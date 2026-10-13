import unittest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.models import NanoparticleState, EnvironmentState, SimulationStatus, EventType
from src.simulation.engine import SimulationEngine

class TestSimulationEngine(unittest.TestCase):
    
    def setUp(self):
        self.np_state = NanoparticleState(
            material="Gold",
            core_composition="Au",
            core_size_nm=20.0,
            shape="Spherical",
            ligand_smiles="C(C(C(=O)O)O)(C(=O)O)O" # Citrate
        )
        self.env_state = EnvironmentState(
            buffer="PBS pH 7.4",
            temperature_c=25.0
        )
        
    def test_initialization(self):
        engine = SimulationEngine(np_state=self.np_state, env_state=self.env_state, time_step=1.0)
        self.assertEqual(engine.state.status, SimulationStatus.INITIALIZED)
        self.assertEqual(engine.state.current_time, 0.0)
        
        # Verify ML integration immediately populated the zeta potential!
        result = engine.get_result()
        events = result["events"]
        
        # We expect SimulationStarted Event + Charge Change Event (from ML surrogate)
        event_types = [e["event_type"] for e in events]
        self.assertIn(EventType.SIMULATION_STARTED, event_types)
        self.assertIn(EventType.CHARGE_CHANGE, event_types)
        
        # Verify the zeta potential was updated from default 0.0 to the ML prediction
        self.assertNotEqual(result["final_particle_state"]["zeta_potential_mV"], 0.0)
        
    def test_environment_update(self):
        engine = SimulationEngine(np_state=self.np_state, env_state=self.env_state)
        engine.step()
        self.assertEqual(engine.state.current_time, 1.0)
        
        # Update environment
        engine.update_environment(temperature_c=37.0, buffer="Water")
        
        self.assertEqual(engine.env_manager.env_state.temperature_c, 37.0)
        self.assertEqual(engine.env_manager.env_state.buffer, "Water")
        
        # This buffer change should trigger another CHARGE_CHANGE via the ML surrogate
        result = engine.get_result()
        events = result["events"]
        env_change_events = [e for e in events if e["event_type"] == EventType.ENVIRONMENT_CHANGED]
        charge_change_events = [e for e in events if e["event_type"] == EventType.CHARGE_CHANGE]
        
        self.assertEqual(len(env_change_events), 1)
        self.assertTrue(len(charge_change_events) >= 2) # Init + After environment change
        
    def test_run_multiple_steps(self):
        engine = SimulationEngine(np_state=self.np_state, env_state=self.env_state, time_step=0.5)
        engine.run(4) # Should advance by 2.0
        self.assertEqual(engine.state.current_time, 2.0)
        
    def test_pause_stop(self):
        engine = SimulationEngine(np_state=self.np_state, env_state=self.env_state)
        engine.pause()
        self.assertEqual(engine.state.status, SimulationStatus.PAUSED)
        engine.step() # Steps reset status to RUNNING
        self.assertEqual(engine.state.status, SimulationStatus.RUNNING)
        engine.stop()
        self.assertEqual(engine.state.status, SimulationStatus.STOPPED)
        engine.step() # Should not run if stopped
        self.assertEqual(engine.state.current_time, 1.0) # From the first step
        
    def test_reproducibility(self):
        # Two identical engines should produce the exact same final state
        np1 = self.np_state.copy()
        env1 = self.env_state.copy()
        eng1 = SimulationEngine(np1, env1)
        eng1.run(5)
        
        np2 = self.np_state.copy()
        env2 = self.env_state.copy()
        eng2 = SimulationEngine(np2, env2)
        eng2.run(5)
        
        res1 = eng1.get_result()["final_particle_state"]
        res2 = eng2.get_result()["final_particle_state"]
        
        self.assertEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()
