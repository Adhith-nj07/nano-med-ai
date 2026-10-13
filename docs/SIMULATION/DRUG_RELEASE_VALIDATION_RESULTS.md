# Drug Release Validation Results

## Fitting Performance
9 out of 9 validated nanoparticle trajectories were successfully fit using non-linear least squares optimization (scipy.optimize.curve_fit).
- **Log-linear vs Nonlinear**: Nonlinear fitting was strictly preferred to avoid log-transform compression errors near zero.
- **k range**: 0.019 to 0.088
- **n range**: 0.27 to 0.51
- **RMSE**: 0.006 to 0.054 (0.6% to 5.4% error)
- **R²**: 0.84 to 0.99

## Model Adequacy
The Korsmeyer-Peppas model fits the initial 60% of the release curves with extremely high fidelity. No alternative model (Zero-order, First-order) is mathematically required for the initial phase, as K-P cleanly captures the early-time burst and initial diffusion.
