# Simulation API

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
