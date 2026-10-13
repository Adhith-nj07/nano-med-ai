# Size & Aggregation Validation

## Grouped Validation Strategy (Pending)
When appropriate longitudinal size/aggregation datasets are acquired:
- The data must be strictly grouped by `trajectory_id` and `formulation_id`.
- Data leakage between $t=1$ and $t=24$ for the same physical sample must be blocked using `GroupKFold`.
- Validation metrics will rely on Trajectory RMSE, MAE, and Time-Series similarity.

## Current Validation Status
Not applicable. No models were fitted or implemented due to insufficient data.
