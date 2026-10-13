# Drug Release Validation Plan

## Grouped Validation
Validation must use `GroupKFold` where the grouping key is `formulation_id` (or `study_id`). No formulation can exist in both training and testing.

## Evaluation Metrics
Since the simulation generates a continuous trajectory, validation will use:
1. **MAE / RMSE**: Overall error across all predicted time points vs. experimental time points.
2. **Similarity Factor ($f_2$)**: The FDA standard for comparing dissolution profiles.
   $f_2 = 50 \times \log_{10} \left( \left[ 1 + \frac{1}{n} \sum_{t=1}^n (R_t - T_t)^2 \right]^{-0.5} \times 100 \right)$
   An $f_2$ value $> 50$ indicates equivalence.
