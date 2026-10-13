import uuid
from typing import List, Dict, Any

from .models import (
    SimulationState, NanoparticleState, EnvironmentState, 
    SimulationStatus, TransformationEvent, EventType
)
from .mechanisms import registry, BaseMechanism
from .capabilities import CapabilityManager

class StateManager:
    def __init__(self, state: SimulationState):
        self.state = state
        self.np_state = state.nanoparticle_state

class EnvironmentManager:
    def __init__(self, env_state: EnvironmentState):
        self.env_state = env_state

class TimeController:
    def __init__(self, current_time: float = 0.0, time_step: float = 1.0):
        self.current_time = current_time
        self.time_step = time_step
        
    def advance(self):
        self.current_time += self.time_step

class EventRecorder:
    def __init__(self):
        self.events: List[TransformationEvent] = []
        
    def record(self, event: TransformationEvent):
        self.events.append(event)
        
    def record_multiple(self, events: List[TransformationEvent]):
        self.events.extend(events)

class MetricsCalculator:
    def calculate(self, state: SimulationState) -> Dict[str, Any]:
        return {
            "colloidal_stability_proxy": state.nanoparticle_state.zeta_potential_mV,
            "drug_released": state.drug_state.cumulative_released_fraction
        }

class SimulationEngine:
    """
    Model-agnostic engine for simulating nanoparticle transformations over time.
    """
    def __init__(self, np_state: NanoparticleState = None, env_state: EnvironmentState = None, time_step: float = 1.0, time_unit: str = "hours"):
        self.state = SimulationState(
            nanoparticle_state=np_state or NanoparticleState(),
            environment_state=env_state or EnvironmentState(),
            time_step=time_step,
            time_unit=time_unit,
            status=SimulationStatus.INITIALIZED
        )
        self.state_manager = StateManager(self.state)
        self.env_manager = EnvironmentManager(self.state.environment_state)
        self.time_controller = TimeController(current_time=0.0, time_step=time_step)
        self.event_recorder = EventRecorder()
        self.metrics_calculator = MetricsCalculator()
        self.capability_manager = CapabilityManager()
        
        # We hold mechanisms that are active for this specific simulation instance
        self.active_mechanisms: List[BaseMechanism] = []
        
        # Auto-add default supported mechanisms from registry
        for mech in registry.list_all():
            if mech.can_run(self.state):
                self.active_mechanisms.append(mech)
        
        init_event = TransformationEvent(
            event_id=str(uuid.uuid4()),
            simulation_id=self.state.simulation_id,
            timestamp=0.0,
            simulation_time=0.0,
            event_type=EventType.SIMULATION_STARTED,
            source="SimulationEngine",
            payload={"description": "Simulation initialized"}
        )
        self.event_recorder.record(init_event)
        
        self._apply_transformations()
        
    def update_environment(self, **kwargs):
        old_env = self.env_manager.env_state.to_dict()
        changed = False
        
        # Test applying changes on a copy first
        test_env = self.env_manager.env_state.copy()
        for key, value in kwargs.items():
            if hasattr(test_env, key):
                setattr(test_env, key, value)
                changed = True
                
        if changed:
            # We must apply the change to the real state so check_compatibility can evaluate it
            for key, value in kwargs.items():
                if hasattr(self.env_manager.env_state, key):
                    setattr(self.env_manager.env_state, key, value)
            
            # Record the generic change
            event = TransformationEvent(
                event_id=str(uuid.uuid4()),
                simulation_id=self.state.simulation_id,
                timestamp=self.time_controller.current_time,
                simulation_time=self.time_controller.current_time,
                event_type=EventType.ENVIRONMENT_CHANGED,
                source="User or System",
                payload={
                    "description": "Environment parameters updated.",
                    "previous": old_env,
                    "new": self.env_manager.env_state.to_dict()
                }
            )
            self.event_recorder.record(event)
            
            # Check compatibility for all mechanisms and block explicitly if unsupported
            incompatible = []
            for mech in self.active_mechanisms:
                compatible, reason = mech.check_compatibility(self.state)
                if not compatible:
                    incompatible.append(mech)
                    self.event_recorder.record(TransformationEvent(
                        event_id=str(uuid.uuid4()),
                        simulation_id=self.state.simulation_id,
                        timestamp=self.time_controller.current_time,
                        simulation_time=self.time_controller.current_time,
                        event_type=EventType.VALIDATION_FAILED,
                        source="SimulationEngine",
                        payload={
                            "blocked_mechanism": mech.name,
                            "reason": reason,
                            "trigger": "ENVIRONMENT_CHANGE"
                        }
                    ))
                    self.state.warnings.append(f"{mech.name} disabled: {reason}")
            
            # Remove incompatible mechanisms from active pool
            for mech in incompatible:
                self.active_mechanisms.remove(mech)
                
            self._apply_transformations()
            
    def _apply_transformations(self):
        for model in self.active_mechanisms:
            if model.can_run(self.state):
                events = model.step(self.time_controller.current_time, self.state)
                self.event_recorder.record_multiple(events)

    def step(self):
        if self.state.status in [SimulationStatus.COMPLETED, SimulationStatus.STOPPED, SimulationStatus.ERROR]:
            return
            
        self.state.status = SimulationStatus.RUNNING
        self.time_controller.advance()
        self.state.current_time = self.time_controller.current_time
        
        self._apply_transformations()
        
        self.state.metrics = self.metrics_calculator.calculate(self.state)
        self.state.events = self.event_recorder.events
        
    def run(self, steps: int):
        for _ in range(steps):
            self.step()
            
    def pause(self):
        self.state.status = SimulationStatus.PAUSED
        self.event_recorder.record(TransformationEvent(
            event_id=str(uuid.uuid4()),
            simulation_id=self.state.simulation_id,
            timestamp=self.time_controller.current_time,
            simulation_time=self.time_controller.current_time,
            event_type=EventType.SIMULATION_PAUSED,
            source="SimulationEngine"
        ))
        
    def resume(self):
        self.state.status = SimulationStatus.RUNNING
        self.event_recorder.record(TransformationEvent(
            event_id=str(uuid.uuid4()),
            simulation_id=self.state.simulation_id,
            timestamp=self.time_controller.current_time,
            simulation_time=self.time_controller.current_time,
            event_type=EventType.SIMULATION_RESUMED,
            source="SimulationEngine"
        ))

    def stop(self):
        self.state.status = SimulationStatus.STOPPED
        self.event_recorder.record(TransformationEvent(
            event_id=str(uuid.uuid4()),
            simulation_id=self.state.simulation_id,
            timestamp=self.time_controller.current_time,
            simulation_time=self.time_controller.current_time,
            event_type=EventType.SIMULATION_STOPPED,
            source="SimulationEngine"
        ))
        
    def reset(self):
        self.time_controller.current_time = 0.0
        self.state.current_time = 0.0
        self.state.status = SimulationStatus.INITIALIZED
        self.state.events = []
        self.event_recorder.events = []
        
        if hasattr(self.state, 'drug_state'):
            self.state.drug_state.cumulative_released_fraction = 0.0
            self.state.drug_state.remaining_drug_amount = 1.0
        
    def get_result(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.state.simulation_id,
            "status": self.state.status.value,
            "duration": self.time_controller.current_time,
            "time_unit": self.state.time_unit,
            "final_particle_state": self.state.nanoparticle_state.to_dict(),
            "final_environment_state": self.env_manager.env_state.to_dict(),
            "events": [e.__dict__ for e in self.event_recorder.events],
            "metrics": self.state.metrics,
            "capabilities": self.capability_manager.to_dict()
        }
