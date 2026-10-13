from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import Trajectory

class PhysicalStabilityDataProvider(ABC):
    """
    Adapter boundary between the processed S5 dataset (CSV/Database) and the simulation domain.
    The simulation engine should NOT read CSV files directly.
    """
    
    @abstractmethod
    def load_validated_trajectories(self) -> List[Trajectory]:
        """Loads all trajectories that have passed rigorous data validation."""
        pass
        
    @abstractmethod
    def get_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        """Retrieves a specific validated trajectory."""
        pass
        
    @abstractmethod
    def get_observations(self, trajectory_id: str) -> List[Dict[str, Any]]:
        """Retrieves the observations array for a trajectory."""
        pass
        
    @abstractmethod
    def get_conditions(self, trajectory_id: str) -> Dict[str, Any]:
        """Retrieves the environmental conditions for a trajectory."""
        pass
        
    @abstractmethod
    def get_provenance(self, trajectory_id: str) -> Dict[str, str]:
        """Retrieves provenance metadata for a trajectory."""
        pass
        
    @abstractmethod
    def get_verification_status(self, trajectory_id: str) -> str:
        """Returns RAW, PROCESSED, VALIDATED, or MODEL_READY."""
        pass

class CsvPhysicalStabilityDataProvider(PhysicalStabilityDataProvider):
    """
    Mock implementation indicating how the CSV data will be bridged once available.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._cache: Dict[str, Trajectory] = {}
        # In a real scenario, this parses the CSV and maps explicitly to the Trajectory schema
        
    def load_validated_trajectories(self) -> List[Trajectory]:
        return list(self._cache.values())
        
    def get_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        return self._cache.get(trajectory_id)
        
    def get_observations(self, trajectory_id: str) -> List[Dict[str, Any]]:
        traj = self.get_trajectory(trajectory_id)
        return [obs.__dict__ for obs in traj.observations] if traj else []
        
    def get_conditions(self, trajectory_id: str) -> Dict[str, Any]:
        traj = self.get_trajectory(trajectory_id)
        return traj.environment.__dict__ if traj else {}
        
    def get_provenance(self, trajectory_id: str) -> Dict[str, str]:
        traj = self.get_trajectory(trajectory_id)
        return traj.provenance if traj else {}
        
    def get_verification_status(self, trajectory_id: str) -> str:
        # For now, S5 is blocked because data is not yet model-ready.
        # This explicitly enforces the RAW -> PROCESSED -> VALIDATED -> MODEL_READY pipeline.
        return "DATA_REQUIRED"
