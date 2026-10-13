# Simulation Limitations

1. **Biological Constraints**: The system tracks biological variables (e.g., cellular uptake) conceptually but lacks the data to predict them.
2. **Mechanistic Constraints**: Time-dependent mechanistic equations (like Higuchi drug release) are absent pending high-quality experimental time-series datasets.
3. **ML Surrogate Accuracy**: The Zeta Potential transformation uses an ML model with an MAE of ~18.9 mV. 
4. **No MD / Quantum Chemistry**: This is a macro-scale surrogate/mechanistic engine, not an atomistic molecular dynamics framework.
