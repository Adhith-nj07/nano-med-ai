# NanoMedAI - Academic MVP

NanoMedAI is a machine learning academic mini-project designed to demonstrate the prediction of nanoparticle physicochemical and biological properties from open-access datasets.

## Project Vision

This MVP focuses on:
1. **Zeta Potential Prediction (as a proxy for stability)**
2. **Experimental Cytotoxicity Prediction (Toxic / Nontoxic)**

## Datasets

The project uses real, publicly available data harmonized from Zenodo:
1. **Stability (Zeta Potential):** Combined dataset of 288 nanoparticles from multiple studies (`data/processed/stability_combined_engineered.csv`), grouped by study DOI to prevent data leakage. (Note: The original 69-row dataset is preserved as a historical baseline).
2. **Cytotoxicity:** Meta-analyzed datasets for toxicity classification of metal oxide nanoparticles (DOI: 10.5281/zenodo.15300193), grouped by Pubmed ID.

## Environment Requirements
- Python 3.9+
- `pandas`
- `numpy`
- `scikit-learn`
- `matplotlib`
- `openpyxl`
- `joblib`

Install dependencies:
```bash
pip install pandas numpy scikit-learn matplotlib openpyxl joblib
```

## Reproducibility Workflow

### 1. Model Training
Run the training scripts to preprocess data, perform cross-validation, and save the final models to the `models/` directory.

```bash
python src/train_stability_final.py
python src/train_cytotoxicity.py
```
*Note: Both models use `GroupKFold` (`study_id` or `Pubmed ID`) to rigorously prevent cross-laboratory data leakage.*

### 2. Prediction API
Models are accessed via the unified API in `src/predict.py`, which handles SMILES feature extraction and data preprocessing internally:

```python
from src.predict import predict_stability, predict_cytotoxicity

# Example usage
zeta = predict_stability({
    'Shape': 'Spherical',
    'Core': 'Ag',
    'Size_nm': 20.0,
    'Medium': 'PBS pH 7.4',
    'Ligand_SMILES': 'C(C(C(=O)O)O)(C(=O)O)O'
})
```

## Documentation Map

- `docs/ROADMAP/`: Master roadmap and authoritative current status.
- `docs/data/`: Data selection, feature schemas, and harmonization plans.
- `docs/ml/`: Validation strategies, leakage audits, and training results.
- `docs/UI/`: Requirements for the future UI implementation.

