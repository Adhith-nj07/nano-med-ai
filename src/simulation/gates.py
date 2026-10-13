from typing import Tuple, List, Dict, Any, Optional
from .metadata import ModelMetadata, ModelStatus
from .models import Trajectory

class S5ModelReadinessGate:
    """
    Validation gate to enforce software boundaries before a future scientific 
    S5 mechanism (e.g. SizeStability) can be considered SUPPORTED or active.
    """
    
    @staticmethod
    def evaluate(metadata: ModelMetadata, trajectories: Optional[List[Trajectory]] = None) -> Tuple[str, List[str]]:
        reasons = []
        is_ready = True
        
        # 1. Model Validation Status
        if metadata.status != ModelStatus.VALIDATED:
            reasons.append(f"Model status is {metadata.status.value}, expected VALIDATED.")
            is_ready = False
            
        # 2. Metadata completeness
        try:
            # Re-run post-init validation manually just in case
            metadata.__post_init__()
        except ValueError as e:
            reasons.append(f"Model metadata incomplete: {str(e)}")
            is_ready = False
            
        # 3. Trajectory Data readiness
        if trajectories:
            for t in trajectories:
                if t.verification_status != "MODEL_READY":
                    reasons.append(f"Trajectory {t.trajectory_id} has verification_status='{t.verification_status}', expected 'MODEL_READY'.")
                    is_ready = False
        else:
            if metadata.training_trajectories == 0:
                reasons.append("No training trajectories declared in metadata.")
                is_ready = False
                
        # 4. Required Domains
        if "size_range_nm" not in metadata.supported_domain:
            reasons.append("Missing required domain constraint: size_range_nm.")
            is_ready = False
            
        if "materials" not in metadata.supported_domain:
            reasons.append("Missing required domain constraint: materials.")
            is_ready = False

        if is_ready:
            return "READY", ["All requirements met."]
        else:
            return "NOT_READY", reasons
