import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Type, Any
import uuid

from .models import NanoparticleState, EnvironmentState, SimulationState, TransformationEvent, EventType
from .capabilities import CapabilityState
from src.predict import predict_stability

class BaseMechanism(ABC):
    """Protocol for all independent simulation mechanisms."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        pass
        
    @property
    @abstractmethod
    def status(self) -> CapabilityState:
        pass
        
    @property
    def dependencies(self) -> List[str]:
        """Names of mechanisms this mechanism depends on (for DAG execution)."""
        return []
        
    def check_compatibility(self, state: SimulationState) -> tuple[bool, str]:
        """Checks if the mechanism is mathematically/scientifically compatible with the given state."""
        return True, "Compatible"
        
    def initialize(self, state: SimulationState):
        """Called once when the simulation starts."""
        pass
        
    def can_run(self, state: SimulationState) -> bool:
        """Determines if the mechanism has everything it needs to execute."""
        is_supported = self.status in [CapabilityState.SUPPORTED, CapabilityState.SUPPORTED_WITH_DOMAIN_LIMITS]
        if not is_supported:
            return False
        compatible, _ = self.check_compatibility(state)
        return compatible
        
    @abstractmethod
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]:
        """Executes one time step."""
        pass
        
    def validate(self) -> bool:
        """Internal self-check logic."""
        return True

class MechanismRegistry:
    """Registry allowing mechanisms to be dynamically registered."""
    def __init__(self):
        self._mechanisms: Dict[str, BaseMechanism] = {}
        
    def register(self, mechanism: BaseMechanism):
        self._mechanisms[mechanism.name] = mechanism
        
    def get(self, name: str) -> BaseMechanism:
        return self._mechanisms.get(name)
        
    def list_all(self) -> List[BaseMechanism]:
        return list(self._mechanisms.values())

# Global registry instance
registry = MechanismRegistry()


class ZetaPotentialMechanism(BaseMechanism):
    @property
    def name(self) -> str: return "ZetaPotential"
    @property
    def version(self) -> str: return "1.0.0"
    @property
    def status(self) -> CapabilityState: return CapabilityState.SUPPORTED
    
    def __init__(self):
        self.last_predicted_zeta = None

    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]:
        events = []
        if not self.can_run(state):
            return events
            
        np_state = state.nanoparticle_state
        env_state = state.environment_state
        
        features = {
            "Shape": np_state.shape if hasattr(np_state, "shape") else "Spherical",
            "Core": np_state.core_composition if hasattr(np_state, "core_composition") else "Unknown",
            "Size_nm": np_state.core_size_nm,
            "Medium": env_state.buffer or "Water",
            "Ligand_SMILES": np_state.ligand_smiles if hasattr(np_state, "ligand_smiles") else ""
        }
        
        try:
            if features["Size_nm"] <= 0:
                return events
            
            prediction = predict_stability(features)
            new_zeta = prediction["prediction"]
            
            if self.last_predicted_zeta is None or abs(new_zeta - self.last_predicted_zeta) > 1e-4:
                old_val = np_state.zeta_potential_mV
                np_state.zeta_potential_mV = new_zeta
                self.last_predicted_zeta = new_zeta
                
                events.append(TransformationEvent(
                    event_id=str(uuid.uuid4()),
                    simulation_id=state.simulation_id,
                    timestamp=current_time,
                    simulation_time=current_time,
                    event_type=EventType.CHARGE_CHANGE,
                    source=self.name,
                    payload={
                        "previous": old_val,
                        "new": new_zeta,
                        "unit": "mV",
                        "model_source": "Ridge(alpha=10.0) from src.predict_stability",
                        "uncertainty": "MAE: 18.90 mV",
                        "trigger": "Environment or physical state change"
                    }
                ))
        except Exception:
            pass
        return events


class KorsmeyerPeppasMechanism(BaseMechanism):
    @property
    def name(self) -> str: return "DrugRelease"
    @property
    def version(self) -> str: return "1.0.0"
    @property
    def status(self) -> CapabilityState: return CapabilityState.SUPPORTED_WITH_DOMAIN_LIMITS
    
    @property
    def dependencies(self) -> List[str]:
        # Example of explicit future mechanism dependency
        return ["SizeStability"] 
        
    def check_compatibility(self, state: SimulationState) -> tuple[bool, str]:
        # Simple domain checking mock
        if state.environment_state.temperature_c and state.environment_state.temperature_c > 60:
            return False, "Temperature outside validated Korsmeyer-Peppas domain."
        return True, "Compatible"
    
    def __init__(self, k: float, n: float, max_valid_fraction: float = 0.6):
        self.k = k
        self.n = n
        self.max_valid_fraction = max_valid_fraction
        self.last_env_hash = None
        
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]:
        events = []
        if not self.can_run(state):
            return events
            
        np_state = state.nanoparticle_state
        env_state = state.environment_state
        
        current_env_hash = hashlib.sha256(f"{env_state.pH}_{env_state.temperature_c}_{env_state.buffer}".encode()).hexdigest()
        
        if self.last_env_hash is not None and current_env_hash != self.last_env_hash:
            events.append(TransformationEvent(
                event_id=str(uuid.uuid4()),
                simulation_id=state.simulation_id,
                timestamp=current_time,
                simulation_time=current_time,
                event_type=EventType.ENVIRONMENT_CHANGED,
                source=self.name,
                payload={
                    "warning": "Environment changed, but Korsmeyer-Peppas release parameters cannot causally update. Ignoring change.",
                    "trigger": "unsupported_for_release_model",
                    "uncertainty": "extrapolation"
                }
            ))
        
        self.last_env_hash = current_env_hash

        if current_time <= 0:
            return events
            
        try:
            fractional_release = self.k * (current_time ** self.n)
            fractional_release = min(fractional_release, 1.0)
            
            validity = "within_model_domain" if fractional_release <= self.max_valid_fraction else "extrapolation"
            
            old_val = state.drug_state.cumulative_released_fraction if hasattr(state, 'drug_state') else np_state.cumulative_released_fraction
            
            if abs(fractional_release - old_val) > 1e-6:
                if hasattr(state, 'drug_state'):
                    state.drug_state.cumulative_released_fraction = fractional_release
                    state.drug_state.remaining_drug_amount = max(0.0, 1.0 - fractional_release)
                else:
                    np_state.cumulative_released_fraction = fractional_release
                    np_state.remaining_drug_amount = max(0.0, 1.0 - fractional_release)
                
                events.append(TransformationEvent(
                    event_id=str(uuid.uuid4()),
                    simulation_id=state.simulation_id,
                    timestamp=current_time,
                    simulation_time=current_time,
                    event_type=EventType.DRUG_RELEASE,
                    source=self.name,
                    payload={
                        "previous": old_val,
                        "new": fractional_release,
                        "description": f"Cumulative release updated to {fractional_release*100:.2f}%",
                        "model_source": f"Korsmeyer-Peppas (k={self.k:.4f}, n={self.n:.4f})",
                        "uncertainty": validity
                    }
                ))
        except Exception:
            pass
            
        return events

# ---------------------------------------------------------
# Future Mechanism Stubs
# ---------------------------------------------------------
class SizeStabilityMechanism(BaseMechanism):
    @property
    def name(self) -> str: return "SizeStability"
    @property
    def version(self) -> str: return "0.0.0"
    @property
    def status(self) -> CapabilityState: return CapabilityState.DATA_REQUIRED
    
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]: return []

class AggregationMechanism(BaseMechanism):
    @property
    def name(self) -> str: return "Aggregation"
    @property
    def version(self) -> str: return "0.0.0"
    @property
    def status(self) -> CapabilityState: return CapabilityState.DATA_REQUIRED
    
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]: return []

class ProteinCoronaMechanism(BaseMechanism):
    @property
    def name(self) -> str: return "ProteinCorona"
    @property
    def version(self) -> str: return "0.0.0"
    @property
    def status(self) -> CapabilityState: return CapabilityState.DATA_REQUIRED
    
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]: return []

class CellularUptakeMechanism(BaseMechanism):
    @property
    def name(self) -> str: return "CellularUptake"
    @property
    def version(self) -> str: return "0.0.0"
    @property
    def status(self) -> CapabilityState: return CapabilityState.DATA_REQUIRED
    
    def step(self, current_time: float, state: SimulationState) -> List[TransformationEvent]: return []

# Register existing and planned mechanisms
registry.register(ZetaPotentialMechanism())
registry.register(SizeStabilityMechanism())
registry.register(AggregationMechanism())
registry.register(ProteinCoronaMechanism())
registry.register(CellularUptakeMechanism())

# Note: KorsmeyerPeppasMechanism must be registered at runtime when k, n are known,
# or updated via initialization.

# Backwards compatibility names for existing tests
ZetaPotentialUpdateModel = ZetaPotentialMechanism
KorsmeyerPeppasModel = KorsmeyerPeppasMechanism
