# Zeta Potential Simulation Validity

## Audit of the Zeta Potential Model

### Training Domain
- **Model**: `models/stability_model_final.joblib` (Ridge Regression, alpha=10).
- **Features**: Log_Size, Estimated_Ligand_MW, Shape, Core, Medium, Coating_Charge.
- **Dataset**: 288 samples synthesized from Millipore/Phosphate data.

### Simulation Compatibility
The model predicts Zeta Potential based strictly on the `Medium` categorical variable (e.g., 'Water' vs. 'PBS pH 7.4'). 
**Limitations:**
- It does **not** take continuous `pH`, `ionic_strength`, or `temperature` as inputs. 
- Therefore, we cannot simulate "pH drops continuously from 7.4 to 6.0". We can only simulate discrete jumps between categorical media present in the training set.
- The model establishes *correlation* between the buffer category and zeta potential, not a *mechanistic causal relationship* across continuous titration gradients.

### Conclusion
The model is valid for sudden, discrete environmental medium swaps (e.g., transferring a particle from water to PBS), but completely invalid for continuous fine-grained pH or temperature simulations.
