from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid

class SimulationStatus(Enum):
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class EventType(Enum):
    SIMULATION_STARTED = "SimulationStarted"
    SIMULATION_PAUSED = "SimulationPaused"
    SIMULATION_RESUMED = "SimulationResumed"
    SIMULATION_STOPPED = "SimulationStopped"
    ENVIRONMENT_CHANGED = "EnvironmentChanged"
    MECHANISM_EXECUTED = "MechanismExecuted"
    PREDICTION_GENERATED = "PredictionGenerated"
    VALIDATION_FAILED = "ValidationFailed"
    
    # Legacy/Granular types
    INITIALIZATION = "INITIALIZATION"
    TIME_STEP = "TIME_STEP"
    AGGREGATION = "AGGREGATION"
    DRUG_RELEASE = "DRUG_RELEASE"
    SIZE_CHANGE = "SIZE_CHANGE"
    CHARGE_CHANGE = "CHARGE_CHANGE"

@dataclass
class TransformationEvent:
    event_id: str
    simulation_id: str
    timestamp: float
    simulation_time: float
    event_type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Legacy fallbacks
    description: Optional[str] = None
    trigger: Optional[str] = None
    previous_state_snapshot: Optional[Dict[str, Any]] = None
    new_state_snapshot: Optional[Dict[str, Any]] = None
    magnitude: Optional[float] = None
    model_source: Optional[str] = None
    uncertainty: Optional[str] = "not_available"

@dataclass
class TrajectoryObservation:
    time: float
    particle_size: Optional[float] = None
    particle_size_type: Optional[str] = None
    pdi: Optional[float] = None
    zeta_potential: Optional[float] = None
    extra_measurements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrajectoryCondition:
    temperature_c: Optional[float] = None
    pH: Optional[float] = None
    ionic_strength: Optional[float] = None
    medium: Optional[str] = None
    buffer: Optional[str] = None

@dataclass
class Trajectory:
    study_id: str
    formulation_id: str
    trajectory_id: str
    environment: TrajectoryCondition
    observations: List[TrajectoryObservation] = field(default_factory=list)
    provenance: Dict[str, str] = field(default_factory=dict)
    verification_status: str = "RAW"

@dataclass
class NanoparticleState:
    core_size_nm: float = 0.0
    hydrodynamic_size_nm: float = 0.0
    pdi: float = 0.0
    zeta_potential_mV: float = 0.0
    aggregation_state: str = "Stable"
    aggregation_index: float = 0.0
    material: str = "Unknown"
    core_composition: str = "Unknown"
    shape: str = "Spherical"
    ligand_smiles: Optional[str] = None
    drug_payload: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}
        
    def copy(self):
        import copy
        return copy.deepcopy(self)

@dataclass
class BiologicalState:
    protein_corona_state: str = "None"
    cellular_association: str = "Unknown"
    uptake_fraction: float = 0.0
    biodistribution: str = "Unknown"
    clearance_fraction: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}
        
    def copy(self):
        import copy
        return copy.deepcopy(self)

@dataclass
class DrugState:
    cumulative_released_fraction: float = 0.0
    remaining_drug_amount: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}
        
    def copy(self):
        import copy
        return copy.deepcopy(self)

@dataclass
class EnvironmentState:
    temperature_c: Optional[float] = None
    pH: Optional[float] = None
    ionic_strength: Optional[float] = None
    buffer: Optional[str] = None
    medium: Optional[str] = None
    solvent_composition: Optional[str] = None
    ROS: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}
    
    def copy(self):
        import copy
        return copy.deepcopy(self)

@dataclass
class SimulationState:
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SimulationStatus = SimulationStatus.INITIALIZED
    current_time: float = 0.0
    time_step: float = 1.0
    time_unit: str = "hours"
    
    nanoparticle_state: NanoparticleState = field(default_factory=NanoparticleState)
    environment_state: EnvironmentState = field(default_factory=EnvironmentState)
    biological_state: BiologicalState = field(default_factory=BiologicalState)
    drug_state: DrugState = field(default_factory=DrugState)
    provenance: Dict[str, Any] = field(default_factory=dict)
    
    events: List[TransformationEvent] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    uncertainty: Dict[str, Any] = field(default_factory=dict)
