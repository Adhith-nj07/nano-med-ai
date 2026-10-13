# Drug Release Dataset Audit

## Quality Audit of Candidate Sources

### Completeness
Both candidate datasets (Nature Comms 2022, Sci Rep 2024) contain comprehensive formulation metadata (PLGA molecular weight, LA ratio, drug properties).

### Experimental Design
Crucially, these datasets contain **true longitudinal trajectories**:
`Formulation A -> t=1h, t=4h, t=24h, t=72h`
This satisfies the requirement that repeated measurements correspond to the same experimental condition across time.

### Data Leakage Risks
Because multiple time points exist for the same formulation, a standard random Train/Test split is **invalid**. If `Formulation A at t=4h` is in the training set and `Formulation A at t=24h` is in the test set, information about the formulation's inherent release kinetics has leaked. Grouped validation (by `formulation_id`) is mandatory.
