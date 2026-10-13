import json
from typing import Dict, Any
from .models import (
    SimulationState, NanoparticleState, EnvironmentState, 
    DrugState, BiologicalState, SimulationStatus, TransformationEvent, EventType
)

class CheckpointManager:
    """Handles serialization and deserialization of the simulation state."""
    
    @staticmethod
    def save_checkpoint(engine) -> Dict[str, Any]:
        """Serializes the entire SimulationEngine state."""
        state = engine.state
        return {
            "simulation_id": state.simulation_id,
            "status": state.status.value,
            "current_time": engine.time_controller.current_time,
            "time_step": state.time_step,
            "time_unit": state.time_unit,
            "nanoparticle_state": state.nanoparticle_state.to_dict(),
            "environment_state": engine.env_manager.env_state.to_dict(),
            "drug_state": state.drug_state.to_dict(),
            "biological_state": state.biological_state.to_dict(),
            "active_mechanisms": [m.name for m in engine.active_mechanisms],
            "capabilities": engine.capability_manager.to_dict(),
            "events": [
                {
                    "event_id": e.event_id,
                    "simulation_id": e.simulation_id,
                    "timestamp": e.timestamp,
                    "simulation_time": e.simulation_time,
                    "event_type": e.event_type.value,
                    "source": e.source,
                    "payload": e.payload
                } for e in engine.event_recorder.events
            ]
        }
    
    @staticmethod
    def load_checkpoint(engine, checkpoint_data: Dict[str, Any]):
        """Restores the SimulationEngine state from a checkpoint."""
        state = engine.state
        state.simulation_id = checkpoint_data["simulation_id"]
        state.status = SimulationStatus(checkpoint_data["status"])
        
        # Restore time
        engine.time_controller.current_time = checkpoint_data["current_time"]
        state.current_time = checkpoint_data["current_time"]
        state.time_step = checkpoint_data["time_step"]
        state.time_unit = checkpoint_data["time_unit"]
        
        # Restore states
        for k, v in checkpoint_data["nanoparticle_state"].items():
            setattr(state.nanoparticle_state, k, v)
            
        for k, v in checkpoint_data["environment_state"].items():
            setattr(engine.env_manager.env_state, k, v)
            
        for k, v in checkpoint_data["drug_state"].items():
            setattr(state.drug_state, k, v)
            
        for k, v in checkpoint_data["biological_state"].items():
            setattr(state.biological_state, k, v)
            
        # Restore events
        engine.event_recorder.events = []
        for e_data in checkpoint_data["events"]:
            engine.event_recorder.record(TransformationEvent(
                event_id=e_data["event_id"],
                simulation_id=e_data["simulation_id"],
                timestamp=e_data["timestamp"],
                simulation_time=e_data["simulation_time"],
                event_type=EventType(e_data["event_type"]),
                source=e_data["source"],
                payload=e_data["payload"]
            ))
        state.events = engine.event_recorder.events
