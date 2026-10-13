import unittest
import sys
import os
import uuid
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from simulation.models import SimulationState, NanoparticleState, EnvironmentState, TransformationEvent, EventType, Trajectory, TrajectoryObservation, TrajectoryCondition
from simulation.mechanisms import BaseMechanism, registry, CapabilityState
from simulation.engine import SimulationEngine
from simulation.data_providers import CsvPhysicalStabilityDataProvider
from simulation.metadata import ModelMetadata, ModelStatus
from simulation.gates import S5ModelReadinessGate
from api.simulation_api import SimulationSessionManager

class MockSizeStabilityMechanism(BaseMechanism):
    """
    TEST ONLY MOCK.
    DO NOT EXPOSE AS PRODUCTION SCIENTIFIC CAPABILITY.
    """
    @property
    def name(self) -> str: return "SizeStabilityMock"
    @property
    def version(self) -> str: return "0.0.0-mock"
    @property
    def status(self) -> CapabilityState: return CapabilityState.SUPPORTED
    
    @property
    def dependencies(self) -> List[str]:
        return ["ZetaPotential"]
        
    def check_compatibility(self, state: SimulationState) -> Tuple[bool, str]:
        if state.environment_state.temperature_c and state.environment_state.temperature_c > 40:
            return False, "Temperature > 40C is out of domain for S5 mock."
        if state.nanoparticle_state.material == "Liposome":
            return False, "Liposome unsupported by S5 mock."
        return True, "Compatible"
        
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]:
        events = []
        if not self.can_run(state):
            return events
            
        old_size = state.nanoparticle_state.core_size_nm
        new_size = old_size + (current_time * 0.1) # Dummy operation
        
        if new_size != old_size:
            state.nanoparticle_state.core_size_nm = new_size
            events.append(TransformationEvent(
                event_id=str(uuid.uuid4()),
                simulation_id=state.simulation_id,
                timestamp=current_time,
                simulation_time=current_time,
                event_type=EventType.SIZE_CHANGE,
                source=self.name,
                payload={
                    "previous": old_size,
                    "new": new_size,
                    "mock": True, # CLEARLY IDENTIFIED TEST RESULT
                    "model_source": "MockSizeStabilityMechanism",
                    "uncertainty": "synthetic_mock_value"
                }
            ))
        return events

class TestS5DryRun(unittest.TestCase):
    
    def test_gate_blocks_unvalidated_model(self):
        # Missing validation metrics & method
        meta = ModelMetadata(
            model_id="s5_size_01",
            model_name="S5 Size Stability",
            model_version="0.1",
            target="core_size_nm",
            training_data_version="v1"
        )
        # Cannot even construct with VALIDATED without crashing now
        with self.assertRaises(ValueError):
            meta.status = ModelStatus.VALIDATED
            meta.__post_init__()
            
    def test_gate_allows_validated_model(self):
        meta = ModelMetadata(
            model_id="s5_size_01",
            model_name="S5 Size Stability",
            model_version="0.1",
            target="core_size_nm",
            training_data_version="v1",
            status=ModelStatus.VALIDATED,
            validation_method="GroupKFold",
            validation_metrics={"RMSE": 5.2},
            training_trajectories=10,
            supported_domain={"size_range_nm": [10, 200], "materials": ["PLGA"]}
        )
        status, reasons = S5ModelReadinessGate.evaluate(meta)
        self.assertEqual(status, "READY")
        
    def test_provider_trajectory_flow(self):
        provider = CsvPhysicalStabilityDataProvider("dummy.csv")
        traj = Trajectory(
            study_id="S_01", formulation_id="F_01", trajectory_id="T_01",
            environment=TrajectoryCondition(temperature_c=25.0),
            verification_status="PROCESSED" # Not MODEL_READY
        )
        provider._cache["T_01"] = traj
        
        meta = ModelMetadata(
            model_id="s5", model_name="s5", model_version="1", target="size",
            training_data_version="1", status=ModelStatus.VALIDATED,
            validation_method="CrossVal", validation_metrics={"MAE": 1.0},
            training_trajectories=1, supported_domain={"size_range_nm": [1], "materials": ["A"]}
        )
        
        status, reasons = S5ModelReadinessGate.evaluate(meta, [traj])
        self.assertEqual(status, "NOT_READY")
        self.assertTrue(any("expected 'MODEL_READY'" in r for r in reasons))
        
    def test_mock_mechanism_in_engine(self):
        registry.register(MockSizeStabilityMechanism())
        
        engine = SimulationEngine(
            np_state=NanoparticleState(material="PLGA", core_size_nm=100.0),
            env_state=EnvironmentState(temperature_c=25.0)
        )
        
        # Step
        engine.run(1)
        # Should have updated size: 100 + 0.1 = 100.1
        self.assertAlmostEqual(engine.state.nanoparticle_state.core_size_nm, 100.1)
        
        # Events should contain mock payload
        size_events = [e for e in engine.state.events if e.event_type == EventType.SIZE_CHANGE]
        self.assertTrue(len(size_events) > 0)
        self.assertTrue(size_events[-1].payload.get("mock"))

    def test_environment_compatibility_dry_run(self):
        registry.register(MockSizeStabilityMechanism())
        engine = SimulationEngine(
            np_state=NanoparticleState(material="PLGA", core_size_nm=100.0),
            env_state=EnvironmentState(temperature_c=25.0)
        )
        
        engine.run(1)
        self.assertAlmostEqual(engine.state.nanoparticle_state.core_size_nm, 100.1)
        
        # Change to out-of-domain temperature
        engine.update_environment(temperature_c=45.0)
        
        # Mechanism should have been dropped and warning recorded
        self.assertFalse(any(isinstance(m, MockSizeStabilityMechanism) for m in engine.active_mechanisms))
        
        val_failed = [e for e in engine.state.events if e.event_type == EventType.VALIDATION_FAILED]
        self.assertTrue(len(val_failed) > 0)
        self.assertEqual(val_failed[-1].payload["blocked_mechanism"], "SizeStabilityMock")
        
        # Run again, size should NOT increase
        engine.run(1)
        self.assertAlmostEqual(engine.state.nanoparticle_state.core_size_nm, 100.1)
        
    def test_checkpoint_dry_run_with_environment_change(self):
        from simulation.checkpoint import CheckpointManager
        
        engine = SimulationEngine(
            np_state=NanoparticleState(material="PLGA", core_size_nm=100.0),
            env_state=EnvironmentState(temperature_c=25.0)
        )
        # Ensure mock is there
        if not any(isinstance(m, MockSizeStabilityMechanism) for m in engine.active_mechanisms):
            engine.active_mechanisms.append(MockSizeStabilityMechanism())
            
        engine.run(2)
        self.assertAlmostEqual(engine.state.nanoparticle_state.core_size_nm, 100.3) # 100 + 0.1 (t=1) + 0.2 (t=2)
        
        ckpt = CheckpointManager.save_checkpoint(engine)
        
        engine2 = SimulationEngine()
        CheckpointManager.load_checkpoint(engine2, ckpt)
        # Re-attach mock since load_checkpoint currently just restores names in active_mechanisms?
        # Actually load_checkpoint doesn't reload the object references. We'll need to manually re-add.
        engine2.active_mechanisms = [m for m in registry.list_all() if m.name in ckpt["active_mechanisms"]]
        if not any(isinstance(m, MockSizeStabilityMechanism) for m in engine2.active_mechanisms):
            engine2.active_mechanisms.append(MockSizeStabilityMechanism())
        
        self.assertEqual(engine2.state.current_time, 2.0)
        
        # Step again
        engine2.run(1) # current_time becomes 3.0
        self.assertAlmostEqual(engine2.state.nanoparticle_state.core_size_nm, 100.6) # 100.3 + 0.3
        
    def test_api_capability_reporting(self):
        api = SimulationSessionManager()
        req = {
            "nanoparticle": {"material": "PLGA"},
            "environment": {"temperature_c": 25.0}
        }
        res = api.create_simulation(req)
        sim_id = res['simulation_id']
        caps = api.get_capabilities(sim_id)
        
        size_cap = caps["size_stability"]
        self.assertEqual(size_cap["status"], "DATA_REQUIRED")
        self.assertEqual(size_cap["validation_state"], "NOT_READY")

if __name__ == '__main__':
    unittest.main()
