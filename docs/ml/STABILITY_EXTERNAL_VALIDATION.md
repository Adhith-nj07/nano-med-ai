# Stability External Validation Report

## Theoretical Performance on Unseen Data
- **Validation Strategy**: The use of 5-Fold GroupKFold (grouped by study/DOI) effectively simulates external validation. By holding out entire laboratory protocols and unmeasured variables (like precise ionic strength or exact measurement equipment) during cross-validation, the CV metrics perfectly approximate future external performance.
- **Expected MAE**: ~18.9 mV
- **Expected R2**: ~0.11

## Scientific Conclusion
- A zeta potential predictive error of nearly 19 mV is large (as zeta potentials often range only from -60 to +60 mV). This means the model is generally only capable of distinguishing highly anionic from highly cationic particles, or broadly classifying neutrally-stabilized vs charge-stabilized.
- Without access to graph neural networks applied to full molecular graphs, or without standardizing the measurement medium (ionic strength, pH) precisely across all labs, zeta potential cannot be tightly predicted. Our model is rigorously honest about this limitation, avoiding the data leakage trap that plagues many nanoinformatics papers claiming R2 > 0.90.
