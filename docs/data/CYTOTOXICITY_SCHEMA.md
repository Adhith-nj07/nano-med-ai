# Cytotoxicity Model Schema

## Status: FINALIZED

### Target
**Name:** Toxicity
**Task:** Classification (Toxic / Nontoxic)
**Target Definition:** The dataset explicitly defines the `Toxicity` classification based on the continuous `Viability (%)` endpoint.

### Input Features
1. `Material type` (Categorical)
2. `Core size (nm)` (Numeric)
3. `Hydro size (nm)` (Numeric)
4. `Surface charge (mV)` (Numeric)
5. `Surface area (m2/g)` (Numeric)
6. `Assay` (Categorical)
7. `Cell name` (Categorical)
8. `Exposure time` (Numeric, hours)
9. `Mass dose (ug/mL)` (Numeric)

### Excluded Features
1. `Viability (%)`
2. `Pubmed ID`
3. `Cell species`, `Cell origin`, `Cell type`
4. Computational / Atomistic features (`ΔHsf (eV)`, `Ec (eV)`, `Ev (eV)`, `χMeO (eV)`)
5. Data provenance features (`Core size data`, `Method core size`, etc.)

### Reasons for exclusion
- `Viability (%)`: Direct target leakage (this defines the `Toxicity` label).
- `Pubmed ID`: Should be used strictly as the grouping variable for `GroupKFold` cross-validation, not as a predictive feature.
- `Cell species`, `Cell origin`, `Cell type`: Highly collinear with `Cell name`. `Cell name` is sufficient.
- Computational features: Excluded to keep the academic MVP UI simple. Users are unlikely to know the enthalpy of formation (`ΔHsf`) of their nanoparticle.
- Data provenance features: Not predictive of toxicity.
