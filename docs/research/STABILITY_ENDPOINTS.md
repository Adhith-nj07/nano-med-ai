# Stability Endpoints

## Candidate Experimental Endpoints

| Endpoint | What it measures | Typical experimental method | Quantitative? | Public datasets available? | Suitable as ML target? |
| -------- | ---------------- | --------------------------- | ------------- | -------------------------- | ---------------------- |
| Zeta potential | Surface charge and electrostatic repulsion | Electrophoretic light scattering (ELS) | YES (mV) | HIGH | YES (as continuous regression, not a binary threshold) |
| Hydrodynamic diameter (size) change | Actual particle aggregation over time | Dynamic Light Scattering (DLS) | YES (nm change) | LOW (time-series data is rare in large aggregations) | YES, but data limited |
| Polydispersity Index (PDI) | Width of particle size distribution | Dynamic Light Scattering (DLS) | YES (0 to 1) | MEDIUM | MARGINAL (usually a secondary indicator) |

## Literature Context

### 1. Zeta Potential
- **Method/Units:** Measured in millivolts (mV).
- **Standard Threshold Assumption:** Historically, values > +30 mV or < -30 mV indicate "stable" electrostatically stabilized colloidal suspensions. 
- **Limitations:** This rule is NOT universal. Sterically stabilized nanoparticles (e.g., those with dense PEG coatings) often have near-zero zeta potentials but exhibit excellent colloidal stability. Forcing a ±30 mV categorical threshold on a heterogeneous dataset will result in scientifically invalid "unstable" labels for perfectly stable polymer-coated particles. 
- **Application for ML:** Must be treated as a continuous regression target, or categorical thresholds must be conditioned on the presence/absence of steric coatings.

### 2. Hydrodynamic Diameter Change
- **Method/Units:** Measured in nanometers (nm) over hours or days.
- **Standard Assumption:** A significant increase in DLS size (e.g., >20% increase) indicates aggregation (instability).
- **Limitations:** Highly accurate for defining stability, but finding large, harmonized, public ML datasets with time-course DLS measurements across varied nanoparticle materials is exceptionally difficult.

## Conclusion
Zeta potential is the most viable, data-rich endpoint for stability prediction. However, to maintain scientific integrity, the model should predict continuous Zeta potential (regression) rather than converting it into a flawed categorical "High/Medium/Low" stability label using rigid thresholds.
