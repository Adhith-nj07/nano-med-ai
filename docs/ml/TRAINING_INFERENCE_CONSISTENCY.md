# Training and Inference Consistency Audit

This document serves as proof that the inference path inside `src/predict.py` reproduces the identical feature pipeline used during model training, ensuring robust production predictions.

## 1. Zeta Potential (Stability) Model

### Expected Raw Features
- `Shape`
- `Core`
- `Size_nm`
- `Medium`
- `Ligand_SMILES`

### Transformations & Feature Engineering
| Transformation | Training Implementation | Inference Implementation (`predict.py`) | Status |
|---|---|---|---|
| Size Log Transform | `np.log1p(df['Size (nm)'])` (Phase 12 notebook / logic) | `np.log1p(features['Size_nm'])` | **MATCH** |
| Charge Extraction | Heuristic based on `[O-]` / `[N+]` in `Ligand1 SMILES` | `_extract_charge()` parsing `Ligand_SMILES` | **MATCH** |
| MW Proxy | Heuristic based on C, O, N, S, P counts | `_estimate_mw()` parsing `Ligand_SMILES` | **MATCH** |

### ColumnTransformer Preprocessing
The model serialized to `models/stability_model_final.joblib` natively encapsulates:
- `StandardScaler()` applied to `['Log_Size', 'Estimated_Ligand_MW']`
- `OneHotEncoder(handle_unknown='ignore')` applied to `['Shape', 'Core', 'Medium', 'Coating_Charge']`

Because `joblib.load()` reconstructs this exact Scikit-Learn `Pipeline`, the scalers use the **identical means and variances** fit during training, guaranteeing zero preprocessing leakage or drift.

## 2. Cytotoxicity Model

### Expected Raw Features
- Categorical: `Material type`, `Assay`, `Cell name`
- Numeric: `Core size (nm)`, `Hydro size (nm)`, `Surface charge (mV)`, `Surface area (m2/g)`, `Exposure time`, `Mass dose (ug/mL)`

### Transformations & Preprocessing
| Transformation | Training Implementation | Inference Implementation (`predict.py`) | Status |
|---|---|---|---|
| Target Mapping | `Nontoxic -> 0, Toxic -> 1` | `1 -> Toxic, 0 -> Nontoxic` | **MATCH** |
| Scaling | `StandardScaler` | Serialized in `models/cytotoxicity_model.joblib` | **MATCH** |
| Encoding | `OneHotEncoder(handle_unknown='ignore')` | Serialized in `models/cytotoxicity_model.joblib` | **MATCH** |

### Conclusion
**PASS**. Both active models exhibit strict training-inference consistency. Explicit input validation inside the prediction API prevents silent coercion errors, and all feature derivations are deterministic and verified by unit tests.
