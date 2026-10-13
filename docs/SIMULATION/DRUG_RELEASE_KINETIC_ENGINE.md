# Drug Release Kinetic Engine

## Architecture
The release kinetic engine operates as an independent TransformationModel plugged into the core SimulationEngine.
The engine maintains the drug release progression over time and handles validity constraints, updating cumulative_released_fraction and 
emaining_drug_amount.

## Time Integration
The simulator steps forward in time. At each step, the kinetic release model calculates cumulative fractional release:
`	ext
M_t / M_inf = f(t)
`
The model checks environmental hashes to warn of unsupported domain changes and updates the simulation state.

## Current Supported Engine
- **Korsmeyer-Peppas** (Fitted on specific validated trajectories).
