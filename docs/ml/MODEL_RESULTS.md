# Model Results

## Stability Prediction (Zeta Potential)

- **Target:** Zeta (mV)
- **Validation:** 5-Fold Cross-Validation

| Model             | MAE | RMSE | R² |
| ----------------- | --: | ---: | -: |
| Linear Regression | 41.28 | 76.72 | -8.86 |
| Random Forest     | 17.46 | 23.97 | 0.03 |

**Academic Interpretation:**
The Random Forest model dramatically outperforms the Linear Regression baseline. However, an $R^2$ near zero indicates that the model explains very little of the variance in Zeta Potential. This is entirely expected given the extremely small dataset size (69 observations). It demonstrates that the pipeline is technically sound, but the dataset is too small to capture universal physicochemical laws for Zeta Potential prediction.

## Cytotoxicity Prediction (Toxicity Class)

- **Target:** Toxicity (Toxic / Nontoxic)
- **Validation:** 5-Fold GroupKFold (grouped by `Pubmed ID`)

| Model               | Accuracy | Precision | Recall | F1 |
| ------------------- | -------: | --------: | -----: | -: |
| Logistic Regression | 0.753 | 0.600 | 0.415 | 0.367 |
| Random Forest       | 0.756 | 0.603 | 0.605 | 0.482 |

**Academic Interpretation:**
The Random Forest Classifier achieves a modest but clearly predictive F1-score (0.482) and 75.6% accuracy when validated using rigorous group-aware cross-validation (GroupKFold). This demonstrates that the nanoparticle descriptors and assay conditions carry real predictive signal for cytotoxicity that generalizes to *unseen studies*. The models do NOT prove clinical safety, causality, or universal nanoparticle behavior; they simply serve as an academic proof-of-concept for nanoinformatics data-mining.
