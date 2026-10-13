# ML Parameter Model Readiness

## Status: NOT READY

## Scientific Justification
There are only **9 independent trajectories** in the strictly validated nanoparticle dataset.
Training an ML model to predict k and 
 from formulation parameters (e.g. drug_mw, la_ga_ratio) with =9$ is statistically invalid and prone to extreme overfitting.

## Grouped Validation Rule
Any future ML model must be validated using GroupKFold split on 	rajectory_id to prevent temporal data leakage. 

Until hundreds of independent trajectories are acquired, the architecture uses per-trajectory static kinetic fits rather than a generalized ML parameter predictor.
