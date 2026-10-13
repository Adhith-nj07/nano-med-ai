import uuid
from typing import Dict, Any, List, Optional
from src.simulation.engine import SimulationEngine
from src.simulation.models import (
    NanoparticleState, EnvironmentState, SimulationState,
    SimulationStatus, EventType
)
from src.simulation.mechanisms import KorsmeyerPeppasMechanism

class SimulationSessionManager:
    """
    In-memory API layer managing active simulation sessions.
    Routes requests to individual SimulationEngine instances.
    Exposes architecture endpoints including capability tracking.
    """
    def __init__(self):
        self._sessions: Dict[str, SimulationEngine] = {}
        
    def _get_engine(self, simulation_id: str) -> SimulationEngine:
        if simulation_id not in self._sessions:
            raise KeyError(f"Simulation {simulation_id} not found")
        return self._sessions[simulation_id]
        
    def create_simulation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        np_config = request.get('nanoparticle', {})
        env_config = request.get('environment', {})
        
        np_state = NanoparticleState(**np_config)
        env_state = EnvironmentState(**env_config)
        
        # Determine time step and unit (optional overrides)
        time_step = request.get('time_step_hours', 1.0)
        
        engine = SimulationEngine(np_state=np_state, env_state=env_state, time_step=time_step)
        
        # We manually register KorsmeyerPeppas here if params are passed, 
        # since its parameters (k,n) must be known at runtime.
        kp_config = request.get('models', {}).get('korsmeyer_peppas')
        if kp_config:
            engine.active_mechanisms.append(
                KorsmeyerPeppasMechanism(k=kp_config['k'], n=kp_config['n'])
            )
            
        sim_id = engine.state.simulation_id
        self._sessions[sim_id] = engine
        
        return self.get_simulation(sim_id)
        
    def start_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        if engine.state.status != SimulationStatus.INITIALIZED:
            raise ValueError(f"Invalid transition: Cannot start simulation from {engine.state.status.value}")
        engine.state.status = SimulationStatus.RUNNING
        return self.get_simulation(simulation_id)
        
    def step_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        if engine.state.status not in [SimulationStatus.RUNNING, SimulationStatus.INITIALIZED]:
            raise ValueError(f"Invalid transition: Cannot step simulation in {engine.state.status.value} state")
        if engine.state.status == SimulationStatus.INITIALIZED:
            engine.state.status = SimulationStatus.RUNNING
            
        engine.step()
        return self.get_simulation(simulation_id)
        
    def run_simulation(self, simulation_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        target_time = request.get('target_time_hours')
        if target_time is None:
            raise ValueError("target_time_hours is required")
            
        if engine.state.status == SimulationStatus.INITIALIZED:
            engine.state.status = SimulationStatus.RUNNING
            
        if engine.state.status != SimulationStatus.RUNNING:
            raise ValueError(f"Invalid transition: Cannot run simulation in {engine.state.status.value} state")
            
        while engine.time_controller.current_time < target_time:
            engine.step()
            
        return self.get_simulation(simulation_id)
        
    def pause_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        if engine.state.status != SimulationStatus.RUNNING:
            raise ValueError(f"Invalid transition: Cannot pause simulation from {engine.state.status.value}")
        engine.pause()
        return self.get_simulation(simulation_id)
        
    def resume_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        if engine.state.status != SimulationStatus.PAUSED:
            raise ValueError(f"Invalid transition: Cannot resume simulation from {engine.state.status.value}")
        engine.resume()
        return self.get_simulation(simulation_id)
        
    def stop_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        if engine.state.status in [SimulationStatus.STOPPED, SimulationStatus.COMPLETED]:
            raise ValueError(f"Invalid transition: Simulation already {engine.state.status.value.lower()}")
        engine.stop()
        return self.get_simulation(simulation_id)
        
    def reset_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        engine.reset()
        return self.get_simulation(simulation_id)
        
    def update_environment(self, simulation_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        
        # 1. Update environment
        engine.update_environment(**request)
        
        response = {
            "environment_updated": True,
            "current_environment": engine.env_manager.env_state.to_dict(),
            "warnings": engine.state.warnings
        }
            
        return response
        
    def get_simulation(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        st = engine.state
        
        return {
            "simulation_id": st.simulation_id,
            "status": st.status.value,
            "current_time_hours": engine.time_controller.current_time,
            "time_step": st.time_step,
            "nanoparticle_state": st.nanoparticle_state.to_dict(),
            "environment_state": engine.env_manager.env_state.to_dict(),
            "biological_state": st.biological_state.to_dict(),
            "drug_state": st.drug_state.to_dict(),
            "warnings": st.warnings,
            "capabilities": engine.capability_manager.to_dict(),
            "latest_events": [e.__dict__ for e in engine.event_recorder.events[-5:]] if engine.event_recorder.events else []
        }

    def get_capabilities(self, simulation_id: str) -> Dict[str, str]:
        engine = self._get_engine(simulation_id)
        return engine.capability_manager.to_dict()

    def get_mechanisms_status(self, simulation_id: str) -> List[Dict[str, str]]:
        engine = self._get_engine(simulation_id)
        from src.simulation.mechanisms import registry
        
        all_mechs = registry.list_all()
        # include injected runtime ones like K-P
        all_names = {m.name for m in all_mechs}
        for m in engine.active_mechanisms:
            if m.name not in all_names:
                all_mechs.append(m)
                
        return [{
            "name": m.name,
            "version": m.version,
            "status": m.status.value,
            "active": m in engine.active_mechanisms
        } for m in all_mechs]
        
    def get_trajectory(self, simulation_id: str) -> Dict[str, Any]:
        engine = self._get_engine(simulation_id)
        
        time_points = [0.0]
        release_pct = [0.0]
        remaining_pct = [100.0]
        
        current_release = 0.0
        
        for e in engine.event_recorder.events:
            if e.event_type == EventType.DRUG_RELEASE:
                time_points.append(e.timestamp)
                current_release = e.payload.get('new', 0.0)
                release_pct.append(current_release * 100.0)
                remaining_pct.append(max(0.0, (1.0 - current_release)) * 100.0)
                
        # If there are no release events but time advanced, just add current time
        if engine.time_controller.current_time > time_points[-1]:
            time_points.append(engine.time_controller.current_time)
            release_pct.append(engine.state.drug_state.cumulative_released_fraction * 100.0)
            remaining_pct.append(engine.state.drug_state.remaining_drug_amount * 100.0)
            
        return {
            "time_hours": time_points,
            "release_pct": release_pct,
            "remaining_drug_pct": remaining_pct
        }

    def get_events(self, simulation_id: str) -> List[Dict[str, Any]]:
        engine = self._get_engine(simulation_id)
        return [
            {
                "event_type": e.event_type.value,
                "timestamp": e.timestamp,
                "source": e.source,
                "payload": e.payload
            }
            for e in sorted(engine.event_recorder.events, key=lambda x: x.timestamp)
        ]
