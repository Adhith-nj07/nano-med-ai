# Simulation Session Model

## Storage Design
The MVP backend uses an **in-memory session store** via `SimulationSessionManager`.
Each session is isolated, avoiding concurrency crossover.

## State Transitions
Valid states:
- `INITIALIZED`
- `RUNNING`
- `PAUSED`
- `STOPPED`
- `ERROR`
- `COMPLETED`

## Limitations
- **Persistence**: Sessions are lost if the backend process restarts.
- **Latency**: While the manager executes steps rapidly (sub-millisecond), it does not claim "zero latency" for complex interactive pipelines involving UI network round-trips.
