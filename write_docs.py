import os

docs = {
    'docs/API/SIMULATION_API.md': '''# Simulation API

## Overview
The Simulation API orchestrates interaction with the NanoMedAI `SimulationEngine`. It exposes a REST-like abstraction via the `SimulationSessionManager` to create, step, run, and update live simulations without embedding scientific mechanisms directly in the route handlers.

## Endpoints (Conceptual)

### POST /simulation
**Request:**
```json
{
  "nanoparticle_state": {"material": "PLGA", "core_size_nm": 200},
  "environment_state": {"pH": 7.4},
  "release_configuration": {"k": 0.088, "n": 0.371},
  "initial_time": 0.0,
  "time_step": 1.0
}
```
**Response:**
Returns `simulation_id`, `status`, initial states, `supported_mechanisms`, and `warnings` (e.g. out of domain).

### POST /simulation/{id}/start
Transitions state from `INITIALIZED` to `RUNNING`.

### POST /simulation/{id}/step
Advances the simulation by one `time_step` (internal canonical unit: hours).

### POST /simulation/{id}/run
**Request:** `{"target_time_hours": 24}`
Runs deterministic stepping until the target time is reached.

### PATCH /simulation/{id}/environment
**Request:** `{"pH": 5.5}`
Updates the live environment. Returns `environment_updated: true`, and explicit warnings if the active models cannot causally update based on the new conditions (e.g., K-P).

### GET /simulation/{id}
Retrieves current time, states, and the 5 latest events.

### GET /simulation/{id}/trajectory
Returns the simulated temporal curves (e.g., `time_hours`, `release_pct`, `remaining_drug_pct`).

### GET /simulation/{id}/events
Returns all `TransformationEvent` records chronologically.
''',

    'docs/SIMULATION/SIMULATION_SESSION_MODEL.md': '''# Simulation Session Model

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
''',

    'docs/SIMULATION/LIVE_ENVIRONMENT_UPDATES.md': '''# Live Environment Updates

## Behaviour
When a client updates the simulation environment (e.g., modifying `pH` or `temperature_c`), the following strictly occurs:
1. The new values are merged into `EnvironmentState`.
2. A chronological `ENVIRONMENT_CHANGE` event is logged.
3. The engine hashes the environment deterministically (SHA-256) and evaluates all active transformation models.

## Crucial Release Model Handling
Because the Korsmeyer-Peppas model parameters were fitted under static experimental conditions, it **cannot causally respond** to dynamic pH or temperature changes. 

If the environment changes, the K-P model explicitly suppresses any invented acceleration and logs an event stating:
`"Environment changed, but Korsmeyer-Peppas release parameters cannot causally update. Ignoring change."`

The API reflects this in the response:
`"release_model_response": "unsupported"`
''',

    'docs/SIMULATION/SIMULATION_API_LIMITATIONS.md': '''# Simulation API Limitations

## Domain Restrictions
The API strictly exposes domain violations. Requesting a release simulation for a non-PLGA particle, or a particle $>1000$ nm, generates an `unsupported_domain` warning.

## Extrapolation
The API does not hide mathematical limits. If a simulation steps past the $60\%$ valid release fraction of Korsmeyer-Peppas, the associated events explicitly flag the output uncertainty as `extrapolation`.

## Scientific Scope
- No prediction of protein corona, cellular uptake, or human-body transport.
- No generalized ML parameter prediction. Parameters must be explicitly configured or tied to a validated trajectory.
'''
}

os.makedirs('docs/API', exist_ok=True)
for path, content in docs.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
