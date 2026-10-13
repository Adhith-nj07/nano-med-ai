# Leakage Audit

## Cytotoxicity Dataset

### Excluded Feature: `Viability (%)`
- **Reason:** Direct target leakage. The dataset methodology created the categorical `Toxicity` target directly from the continuous `Viability (%)` column. Including it as a feature would allow the model to achieve 100% accuracy simply by learning the viability threshold, completely ignoring the nanoparticle properties.

### Excluded Features: `Cell species`, `Cell origin`, `Cell type`
- **Reason:** Collinearity/Leakage. These are purely derivative characteristics of the `Cell name`. While not target leakage, including them adds redundant features that artificially inflate the importance of cell line characteristics.

### Group-Aware Validation: `Pubmed ID`
- **Reason:** Data leakage prevention between train and test sets. Multiple rows (e.g., different doses) come from the exact same published experiment (same `Pubmed ID`). If we used random train-test splitting, rows from the same experiment would appear in both partitions. The model could "memorize" the unmeasured idiosyncrasies of that specific lab rather than generalizing to unseen nanoparticles. `GroupKFold` using `Pubmed ID` guarantees that all records from a single study are either entirely in the training set or entirely in the test set.

## Stability Dataset

### Excluded Feature: `Corresponding sphere diameter (nm)`
- **Reason:** Feature collinearity/Leakage. It is a mathematical derivation of `Diameter (TEM-STEM)` and does not provide new physical information.

### Addressed Potential Leakage: `Type of Coating (Anionic, Cationic, Neutral)`
- **Reason for INCLUSION:** While strongly correlated with the sign of the Zeta Potential (the target), it represents an initial synthesis choice by the chemist, not a post-synthesis measurement. It is valid to ask a model "If I synthesize this with an anionic coating, what will the Zeta potential be?" Thus, it is retained.
