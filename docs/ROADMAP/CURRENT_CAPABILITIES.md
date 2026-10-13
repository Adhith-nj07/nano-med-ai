# Current Capabilities (Academic MVP)
- Real datasets for Stability (Zeta Potential) and Cytotoxicity.
- Data preprocessing with structural feature derivation from SMILES strings (Coating Charge, Estimated Ligand MW).
- Group-aware validation using GroupKFold on study DOIs to prevent data leakage.
- Saved ML pipelines (Ridge Regression for Stability, Random Forest for Cytotoxicity).
- Prediction APIs fully decoupling inference logic from dataset logic.
- Scientific validation documentation and reproducible recovery metrics.
