from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ModelStatus(Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    VALIDATED = "VALIDATED"
    DEPRECATED = "DEPRECATED"

@dataclass
class ModelMetadata:
    model_id: str
    model_name: str
    model_version: str
    target: str
    training_data_version: str
    training_studies: List[str] = field(default_factory=list)
    training_trajectories: int = 0
    validation_method: str = "Unknown"
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    supported_domain: Dict[str, Any] = field(default_factory=dict)
    supported_conditions: Dict[str, Any] = field(default_factory=dict)
    measurement_types: List[str] = field(default_factory=list)
    provenance: Dict[str, str] = field(default_factory=dict)
    status: ModelStatus = ModelStatus.EXPERIMENTAL
    
    def __post_init__(self):
        if self.status == ModelStatus.VALIDATED:
            if not self.validation_metrics:
                raise ValueError("status=VALIDATED requires 'validation_metrics'")
            if not self.validation_method or self.validation_method == "Unknown":
                raise ValueError("status=VALIDATED requires 'validation_method'")
            if self.training_trajectories <= 0:
                raise ValueError("status=VALIDATED requires 'training_trajectories' > 0")
            if not self.supported_domain:
                raise ValueError("status=VALIDATED requires 'supported_domain'")
    
    def is_validated(self) -> bool:
        return self.status == ModelStatus.VALIDATED
