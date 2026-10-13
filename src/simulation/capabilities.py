from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class CapabilityState(Enum):
    SUPPORTED = "SUPPORTED"
    SUPPORTED_WITH_DOMAIN_LIMITS = "SUPPORTED_WITH_DOMAIN_LIMITS"
    DATA_REQUIRED = "DATA_REQUIRED"
    MODEL_REQUIRED = "MODEL_REQUIRED"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    NOT_SUPPORTED = "NOT_SUPPORTED"

@dataclass
class CapabilityInfo:
    capability: str
    status: CapabilityState
    reason: str
    required_data: bool = False
    required_model: bool = False
    validation_state: str = "NOT_READY"
    supported_domain: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "status": self.status.value,
            "reason": self.reason,
            "required_data": self.required_data,
            "required_model": self.required_model,
            "validation_state": self.validation_state,
            "supported_domain": self.supported_domain
        }

class CapabilityManager:
    def __init__(self):
        self.capabilities: Dict[str, CapabilityInfo] = {
            "zeta_prediction": CapabilityInfo(
                "zeta_prediction", CapabilityState.SUPPORTED, "Research prototype available within a restricted input domain.", validation_state="EXPERIMENTAL"
            ),
            "cytotoxicity_prediction": CapabilityInfo(
                "cytotoxicity_prediction", CapabilityState.SUPPORTED, "Research prototype available for assay-specific classification.", validation_state="EXPERIMENTAL"
            ),
            "drug_release": CapabilityInfo(
                "drug_release", CapabilityState.SUPPORTED_WITH_DOMAIN_LIMITS, "Research model restricted to observed formulations and fitted conditions; not a general environmental-response simulator.", validation_state="RESEARCH MODULE"
            ),
            "size_stability": CapabilityInfo(
                "size_stability", CapabilityState.DATA_REQUIRED, "No validated S5 model or dataset is currently available.", required_data=True, required_model=True
            ),
            "aggregation": CapabilityInfo(
                "aggregation", CapabilityState.DATA_REQUIRED, "No validated S5 model or dataset is currently available.", required_data=True, required_model=True
            ),
            "protein_corona": CapabilityInfo(
                "protein_corona", CapabilityState.DATA_REQUIRED, "Biological dataset missing.", required_data=True, required_model=True
            ),
            "cellular_uptake": CapabilityInfo(
                "cellular_uptake", CapabilityState.DATA_REQUIRED, "Biological dataset missing.", required_data=True, required_model=True
            ),
            "pharmacokinetics": CapabilityInfo(
                "pharmacokinetics", CapabilityState.DATA_REQUIRED, "In vivo PK dataset missing.", required_data=True, required_model=True
            ),
            "biodistribution": CapabilityInfo(
                "biodistribution", CapabilityState.DATA_REQUIRED, "In vivo biodistribution dataset missing.", required_data=True, required_model=True
            ),
            "therapeutic_response": CapabilityInfo(
                "therapeutic_response", CapabilityState.DATA_REQUIRED, "In vivo efficacy dataset missing.", required_data=True, required_model=True
            ),
            "toxicity": CapabilityInfo(
                "toxicity", CapabilityState.DATA_REQUIRED, "In vivo toxicity dataset missing.", required_data=True, required_model=True
            ),
            "human_clinical_outcome": CapabilityInfo(
                "human_clinical_outcome", CapabilityState.NOT_SUPPORTED, "Out of project scope."
            )
        }
        
    def get_capability(self, name: str) -> CapabilityInfo:
        return self.capabilities.get(name)
        
    def set_capability(self, name: str, info: CapabilityInfo):
        self.capabilities[name] = info

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.to_dict() for k, v in self.capabilities.items()}
