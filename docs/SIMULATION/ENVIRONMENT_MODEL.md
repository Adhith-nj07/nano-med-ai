# Environment Model

The EnvironmentState tracks:
- **Physical**: Temperature, pressure, dissolved oxygen.
- **Chemical**: pH, ionic strength, buffer, solvent composition.
- **Biological**: Serum/plasma indicators.

The engine supports dynamic, live updates to this environment, triggering immediate re-evaluation of transformation models.
