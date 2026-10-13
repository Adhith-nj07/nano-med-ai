# Simulation Validation

Validation suite exists in 	ests/test_simulation.py and strictly checks:
- **Initialization**: Ensures correct SimulationStatus and ML surrogate startup.
- **Environment Update**: Ensures that dynamic parameter changes successfully trigger ML surrogate updates.
- **Event Tracking**: Confirms that state mutations record a TransformationEvent containing historical snapshots.
- **Reproducibility**: Guarantees identical simulation outputs for identical initial conditions.
