from typing import List, Dict, Any, Optional
import numpy as np

class ValidationFramework:
    """
    Reusable validation infrastructure for data, models, and simulation trajectories.
    """
    
    @staticmethod
    def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(np.abs(y_true - y_pred)))
        
    @staticmethod
    def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        
    @staticmethod
    def calculate_trajectory_rmse(trajectory_true: List[float], trajectory_pred: List[float]) -> float:
        if not trajectory_true or not trajectory_pred or len(trajectory_true) != len(trajectory_pred):
            raise ValueError("Trajectories must have matching non-zero lengths for RMSE calculation.")
        return ValidationFramework.calculate_rmse(np.array(trajectory_true), np.array(trajectory_pred))

    @staticmethod
    def get_grouped_splits(df, group_col: str, n_splits: int = 5):
        """
        Prepare grouped-validation utilities to prevent data leakage.
        group_col can be 'study_id', 'formulation_id', or 'trajectory_id'.
        Requires sklearn.model_selection.GroupKFold in real implementation.
        """
        try:
            from sklearn.model_selection import GroupKFold
            gkf = GroupKFold(n_splits=n_splits)
            return gkf.split(df, groups=df[group_col])
        except ImportError:
            # Stub if sklearn isn't available in some contexts
            return []
