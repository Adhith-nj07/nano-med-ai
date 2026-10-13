# Time-Series Data Requirements

For NanoMedAI to transition from a Level 1 (Static ML Prediction) to a Level 3/4 (Mechanistic Simulation) platform, specific time-series data structures are required.

## The Problem with Current Data
Current data links Formulation $F$ to Endpoint $E$ directly ($F \rightarrow E$).
Simulation requires Formulation $F$ transitioning through State $S_t$ over time ($F \rightarrow S_{t_1} \rightarrow S_{t_2} \rightarrow S_{t_n}$).

## Required Structure (Example: Drug Release)
To model cumulative release, the acquired dataset must contain long-format trajectories:
| Particle_ID | pH | Temp | Time_h | Cumulative_Release_% |
|-------------|----|------|--------|----------------------|
| NP_001      | 7.4| 37   | 1      | 15.2                 |
| NP_001      | 7.4| 37   | 4      | 35.8                 |
| NP_001      | 7.4| 37   | 24     | 72.1                 |

Without this structure, differential equations cannot be calibrated, and the simulation time-stepper cannot be scientifically validated.
