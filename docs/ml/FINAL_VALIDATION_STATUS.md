# Final Validation Status

This document records the exact cross-validation methodology used to evaluate the active predictive models in NanoMedAI.

## 1. Stability Model (Zeta Potential)

- **Dataset Size**: 288 rows (`data/processed/stability_combined_engineered.csv`)
- **Grouping Variable**: `study_id` (representing the source DOI or publication)
- **Unique Studies (Groups)**: 32 unique studies
- **Validation Strategy**: 5-Fold `GroupKFold`
- **Leakage Prevention**: By grouping on `study_id`, no individual study's data appears in both the train and test split of any single fold. This forces the model to generalize across unmeasured intra-lab parameters (like precise pH, ionic strength, or proprietary synthesis quirks) rather than memorizing them.

## 2. Cytotoxicity Model

- **Dataset Size**: 666 rows (`data/raw/cytotoxicity_meta_analysis.xlsx`)
- **Grouping Variable**: `Pubmed ID`
- **Unique Studies (Groups)**: ~70 unique publications
- **Validation Strategy**: 5-Fold `GroupKFold`
- **Leakage Prevention**: Similar to the stability model, evaluating on unseen PubMed IDs guarantees that the RF Classifier is not simply matching identical assay protocols from the same lab.

## Conclusion

Both core models in the current Academic MVP use strict grouped cross-validation strategies, successfully simulating true external dataset evaluation and preventing the data-leakage trap common in nanoinformatics.
