# NanoMedAI Prediction API

The authoritative backend entry point for ML inference is `src/predict.py`.

It provides two core prediction functions wrapped with strict validation and robust model path resolution.

## 1. Zeta Potential (Stability) Prediction

Predicts the Zeta Potential (mV) based on structural features.

### Function
`predict_stability(features: dict) -> dict`

### Input Schema
```python
{
    "Shape": str,           # e.g., "Spherical"
    "Core": str,            # e.g., "Ag", "Au", "TiO2"
    "Size_nm": float,       # Core diameter in nm (must be > 0)
    "Medium": str,          # e.g., "Water", "PBS pH 7.4"
    "Ligand_SMILES": str    # Canonical SMILES (e.g., "C(C(C(=O)O)O)(C(=O)O)O")
}
```

### Output Schema
```python
{
    "prediction": float,    # e.g., -23.7
    "unit": "mV",
    "target": "zeta_potential"
}
```

### Example Usage
```python
from src.predict import predict_stability

output = predict_stability({
    "Shape": "Spherical",
    "Core": "Ag",
    "Size_nm": 20.0,
    "Medium": "PBS pH 7.4",
    "Ligand_SMILES": "C(C(C(=O)O)O)(C(=O)O)O"
})

print(output)
# {"prediction": 1.662648, "unit": "mV", "target": "zeta_potential"}
```

---

## 2. Cytotoxicity Prediction

Predicts experimental toxicity (Toxic vs Nontoxic) based on nanomaterial and assay features.

### Function
`predict_cytotoxicity(features: dict) -> dict`

### Input Schema
```python
{
    "Material type": str,        # e.g., "CuO"
    "Core size (nm)": float,
    "Hydro size (nm)": float,
    "Surface charge (mV)": float,
    "Surface area (m2/g)": float,
    "Assay": str,                # e.g., "MTT"
    "Cell name": str,            # e.g., "A549"
    "Exposure time": float,      # in hours
    "Mass dose (ug/mL)": float
}
```

### Output Schema
```python
{
    "prediction": str,           # "Toxic" or "Nontoxic"
    "target": "cytotoxicity"
}
```

### Example Usage
```python
from src.predict import predict_cytotoxicity

output = predict_cytotoxicity({
    "Material type": "CuO",
    "Core size (nm)": 20.0,
    "Hydro size (nm)": 30.0,
    "Surface charge (mV)": -15.0,
    "Surface area (m2/g)": 50.0,
    "Assay": "MTT",
    "Cell name": "A549",
    "Exposure time": 24.0,
    "Mass dose (ug/mL)": 10.0
})

print(output)
# {"prediction": "Nontoxic", "target": "cytotoxicity"}
```

---

## Error Handling

The API natively raises the following exceptions upon failure:

- `ValidationError`: Raised if a required key is missing, or if a field cannot be safely cast to the required numerical type (e.g., negative sizes).
- `ModelLoadError`: Raised if the underlying serialized `.joblib` model file cannot be located or is corrupted.

Internal Python stack traces are intercepted at the boundary to prevent spilling filesystem/library errors to the eventual UI layer.
