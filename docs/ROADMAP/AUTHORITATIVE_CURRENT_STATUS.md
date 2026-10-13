# NanoMedAI — Authoritative Current Status

## Project Type

Academic mini-project with future high-end research expansion.

## Current MVP Status

COMPLETE / IN PROGRESS (ML backend complete, UI integration blocked/pending).

## Active Stability Dataset

`data/processed/stability_combined_engineered.csv` (288 rows)

## Active Stability Model

`models/stability_model_final.joblib` (Ridge Regression, alpha=10)

## Stability Target

Zeta Potential (mV)

## Stability Validation

5-Fold GroupKFold (grouped by `study_id`)

## Stability Metrics

MAE: 18.90 mV
RMSE: (Computed, approx. 23.5)
R²: 0.108

## Active Cytotoxicity Dataset

`data/raw/cytotoxicity_meta_analysis.xlsx` (666 rows)

## Active Cytotoxicity Model

`models/cytotoxicity_model.joblib` (Random Forest Classifier)

## Cytotoxicity Validation

5-Fold GroupKFold (grouped by `Pubmed ID`)

## Cytotoxicity Metrics

Accuracy: 0.756
F1: 0.482
Other: Precision 0.707, Recall 0.366

## Active Prediction APIs

`src/predict.py` (Exposes `predict_stability` and `predict_cytotoxicity`)

## UI Status

NOT STARTED (Original HTML file `app/nanomedai.html` exists but contains hardcoded synthetic logic; integration with the Python API is completely unstarted).

## Current Explainability

CURRENT (Random Forest Feature Importance implemented and saved for cytotoxicity; SHAP/PDP/ICE are FUTURE).

## Current Uncertainty

FUTURE

## Current OOD Detection

FUTURE

## Current Optimization

FUTURE

## Current Digital Twin

FUTURE

## Current Database

FUTURE (Currently uses file-based datasets)

## Current Literature Integration

FUTURE

## Historical Components

- 69-row dataset (`data/raw/zeta_potential_69_enms.xlsx`)
- Original 69-row Random Forest stability model (`models/stability_model.joblib`)
- Synthetic "Reactivity" classification
- Synthetic "Stability" categorical endpoints (High/Medium/Low)

## Future Components

- Transformation Engine
- Protein Corona
- Drug release & Cellular uptake
- Multimodal AI (Images, Spectra)
- Advanced Uncertainty (Conformal prediction)
- Digital Twin Architecture
- Relational Database & Knowledge Graph
- Multi-objective optimization & Active Learning

---

## Component Status Table

| Component              | Current Status | Evidence |
| ---------------------- | -------------- | -------- |
| Real stability dataset | CURRENT | `data/processed/stability_combined_engineered.csv` (288 rows) |
| Stability model        | CURRENT | `models/stability_model_final.joblib` |
| Zeta prediction        | CURRENT | `predict_stability` in `src/predict.py` |
| SMILES features        | FOUNDATION | `_extract_charge`, `_estimate_mw` in `src/predict.py` |
| Cytotoxicity dataset   | CURRENT | `data/raw/cytotoxicity_meta_analysis.xlsx` (666 rows) |
| Cytotoxicity model     | CURRENT | `models/cytotoxicity_model.joblib` |
| GroupKFold             | CURRENT | Used in `train_stability_final.py` & `train_cytotoxicity.py` |
| Prediction API         | CURRENT | `src/predict.py` |
| Basic explainability   | CURRENT | `docs/ml/figures/cytotoxicity_feature_importance.png` |
| SHAP                   | FUTURE | Not implemented |
| Uncertainty            | FUTURE | Not implemented |
| OOD detection          | FUTURE | Not implemented |
| What-if                | FUTURE | Not implemented |
| Counterfactual AI      | FUTURE | Not implemented |
| Drug release           | FUTURE | Not implemented |
| Cellular uptake        | FUTURE | Not implemented |
| Transformation         | FUTURE | Not implemented |
| Protein corona         | FUTURE | Not implemented |
| Time-series            | FUTURE | Not implemented |
| Image AI               | FUTURE | Not implemented |
| Spectral AI            | FUTURE | Not implemented |
| Multimodal AI          | FUTURE | Not implemented |
| Physics-informed ML    | FUTURE | Not implemented |
| Optimization           | FUTURE | Not implemented |
| Active learning        | FUTURE | Not implemented |
| Digital twin           | FUTURE | Not implemented |
| Knowledge graph        | FUTURE | Not implemented |
| Literature-aware AI    | FUTURE | Not implemented |
| Data provenance        | FOUNDATION | Dataset DOIs used for CV grouping |
| Database               | FUTURE | Flat files used for MVP |
