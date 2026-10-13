# Cytotoxicity Simulation Validity

## Audit of the Cytotoxicity Model

### Training Domain
- **Model**: `models/cytotoxicity_model.joblib` (Random Forest Classifier).
- **Features**: Core size, Hydro size, Surface charge, Surface area, Exposure time, Mass dose, Material type, Assay, Cell name.
- **Dataset**: 666 static endpoints from a meta-analysis.

### Simulation Compatibility
- While `Exposure time` exists as a continuous variable, the target is a discrete static endpoint (`Toxic` or `Nontoxic`).
- The dataset does not track viability dropping over time for a single cell population. It compares independent assays at different times.
- Connecting this directly to the time-stepper would result in binary flickering (e.g., Nontoxic at t=23, Toxic at t=24), which does not accurately represent gradual cellular apoptotic mechanisms.

### Conclusion
The model should remain in Level 1 (Static ML Prediction). It cannot be used as a dynamic simulation surrogate without a dataset tracking continuous cellular viability percentages over identical sample trajectories.
