# Simulation Engine

The core SimulationEngine coordinates all simulation logic.

### Capabilities
- **Initialization**: Sets up initial models and logs an INITIALIZATION event.
- **Stepping**: Advances the simulation by a fixed time step (	ime_step), evaluating all applicable transformation models.
- **Live Updates**: The update_environment() method injects environmental changes on the fly, immediately re-applying transformations without requiring a simulation restart.
- **State Control**: pause(), 
un(), and stop() mechanisms are in place.
