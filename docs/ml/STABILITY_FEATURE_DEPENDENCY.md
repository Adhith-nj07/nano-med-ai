# Stability Feature Dependency Audit

## 1. Geometric Surface Area vs Diameter
- Linear Correlation: 0.771
- Log Correlation: 0.966
- The calculated ratio Area / (pi * d^2) shows that for many records, the Area is exactly pi*d^2 (ratio exactly 1.0), meaning it is mathematically derived and redundant for spherical particles. We should likely drop Geometric Surface Area to prevent multicollinearity, or just keep Diameter.

## 2. Coating vs Coating_Charge
- Coating specifies the exact chemical (e.g., PVP, PEG 1500).
- Coating_Charge specifies the functional charge category.
- Since Coating has 21 unique categories for only 69 rows, it is effectively a high-cardinality identifier rather than a learnable feature. Including it will severely overfit the model. Coating_Charge is much more generalizable.

## 3. Ageing
- Ageing is categorical (Pristine vs Aged). It represents an experimental state, which is valid, though limited to 10 aged samples.

## Conclusion
- **Action 1:** Drop Geometric Surface Area (nm2) as it is mathematically derived from Diameter.
- **Action 2:** Drop Coating to prevent high-cardinality overfitting, relying purely on Coating_Charge.
