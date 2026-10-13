# Particle State Model

The NanoparticleState is a strictly typed data model tracking:
- **Identity**: ID, material, core composition, shape.
- **Physical**: Size, surface area, density.
- **Surface**: Zeta potential, coating integrity, ligand definitions.
- **Payload**: Drug loading, release fractions.
- **Transformations**: Aggregation index, degradation fraction.

*Note: Biological placeholders exist for protein corona and cellular uptake, but are currently untracked/unsupported in Phase S1.*
