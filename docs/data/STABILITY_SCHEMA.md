# Stability Model Schema

## Status: FINALIZED

### Target
**Name:** Zeta (mV)
**Task:** Regression
**Unit:** mV

### Input Features
1. `metal core` (Categorical)
2. `Coating` (Categorical)
3. `Type of Coating (Anionic, Cationic, Neutral)` (Categorical)
4. `Ageing` (Categorical: Pristine / Aged)
5. `Diameter  (TEM-STEM)` (Numeric, nm)
6. `Shape group` (Categorical)
7. `Geometric Surface Area (nm2)` (Numeric, nm2)

### Excluded Features
1. `Corresponding sphere diameter (nm)`
2. `Atomic radius`, `Ionic radius`, `Xox`, `x`, `Nmetal`, `Noxygen`, `Σx`, `Σx/nO`, `MW`, `Group`, `Period`, `Absolute electronegativity`, `Energy Band Gap`

### Reasons for exclusion
- `Corresponding sphere diameter (nm)` is highly collinear with `Diameter (TEM-STEM)`.
- Atomistic and quantum-mechanical descriptors (e.g., `Energy Band Gap`, `Absolute electronegativity`) are excluded to keep the academic MVP model simple and focused on macroscopic physicochemical properties that a user could easily input into the UI.

*(Note: Features like pH, Salt, and Temperature from the original synthetic prototype are excluded because this specific dataset does not capture them—it assumes standard conditions).*
