# Real-Data Readiness Audit

## 1. Required Training Schema

| Required Field | Required? | Currently Available? | Expected Type | Notes |
|---|---|---|---|---|
| Material | YES | NO | Categorical | CopperOxide, Gold, IronOxide, Silica, Silver, TitaniumDioxide, ZincOxide |
| Size_nm | YES | NO | Numeric | Range 8.0 - 99.9 in synthetic data |
| Shape | YES | NO | Categorical | Cube, Rod, Sheet, Sphere, Star |
| Temperature | YES | NO | Numeric | 20.0 - 64.9 |
| pH | YES | NO | Numeric | 3.52 - 9.5 |
| Salt | YES | NO | Numeric | 0.01 - 0.4 |
| Coating | YES | NO | Categorical | Chitosan, Citrate, PEG, PVP, Uncoated |
| Stability | YES | NO | Target | High, Medium, Low |
| Reactivity | YES | NO | Target | High, Moderate, Low |
| Source | YES | NO | Group (String) | Required for GroupKFold |

## 2. Current Data Inventory

| Dataset | Location | Rows | Columns | Real/Synthetic | Targets | Usable? |
|---|---|---:|---:|---|---|---|
| Synthetic Baseline | MISSING | 0 | 0 | Synthetic | Missing | NOT USABLE |

## 3. Feature Compatibility

No real datasets have been acquired yet because target definitions are undefined. When datasets are acquired, strict attention must be paid to:
- Whether "Size" means core diameter (TEM) or hydrodynamic diameter (DLS).
- Whether pH, Temperature, and Salt are actually reported in the datasets or assumed as physiological (pH 7.4, 37°C).

## 4. Label Compatibility

### Stability

- Current expected label: Categorical (High / Medium / Low)
- Current definition: "stay evenly spread out (stable) or clump together into larger clusters over time (unstable)"
- Real-world measurements available: Unknown until datasets sourced (likely Zeta potential, DLS size change, PDI).
- Possible mapping: Requires literature-backed thresholds (e.g., Zeta potential < -30mV or > +30mV = High Stability).
- Evidence required: Literature citations for thresholds.
- Problems: STOP CONDITION 5 triggered. Labels cannot be defined without scientific justification.

### Reactivity

- Current expected label: Categorical (High / Moderate / Low)
- Current definition: "how strongly a body's cells or immune system might respond"
- Real-world measurements available: Unknown (likely ROS generation, IC50, cell viability).
- Possible mapping: Requires matching a specific assay to this broad concept.
- Evidence required: Literature citations linking the assay to generalized reactivity.
- Problems: STOP CONDITION 6 triggered. Concept is too broad and undefined to map to specific experimental endpoints blindly.

### Cytotoxicity

- Deferred. Do not attempt until Stability/Reactivity are resolved.

## 5. Data Harmonization Problems

- Not yet applicable, as no data has been sourced.

## 6. Data Readiness Verdict

BLOCKED

The repository is not ready for real-data integration. Target endpoints (Stability and Reactivity) lack quantitative definitions, making it impossible to evaluate candidate real-world datasets for compatibility. Additionally, the synthetic baseline data is missing, preventing verification of the existing pipeline.
