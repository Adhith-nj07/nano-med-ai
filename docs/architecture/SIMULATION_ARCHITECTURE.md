# Simulation Architecture

## 1. Architecture Diagram
```text
SimulationEngine
├── StateManager
├── EnvironmentManager
├── TimeController
├── MechanismRegistry
├── EventRecorder
└── CapabilityManager
```

## 2. SimulationEngine Responsibilities
The `SimulationEngine` is the model-agnostic orchestrator for temporal simulation of nanomedicine systems. It is strictly responsible for managing state progression, advancing time via the `TimeController`, dispatching mechanism steps via the `MechanismRegistry`, and compiling transformation events. It contains NO scientific equations.

## 3. Mechanism Responsibilities
Mechanisms are modular, independent domains of scientific causality implementing the `BaseMechanism` protocol. They read the current state, determine if they are capable of running (`can_run`), execute any scientific transformations (`step`), and emit standard `TransformationEvent` objects. Unsupported mechanisms gracefully return empty events rather than fabricating data.

## 4. State Model
The domain state is segmented into domain-specific records:
- `NanoparticleState`: Physical and chemical properties.
- `EnvironmentState`: The exposure environment (pH, temp, buffers).
- `DrugState`: Drug loading, release fraction, and payload.
- `BiologicalState`: Protein corona, cellular uptake, clearance (Future).
- `Trajectory`: Tracks observations over time with detailed provenance.

## 5. Environment Model
`EnvironmentState` is the central source of truth for the experimental conditions. Fields include `temperature_c`, `pH`, `ionic_strength`, `solvent_composition`, `buffer`, `medium`, and `ROS`. Missing values are natively set to `None` to prevent silent default assumptions. Changes emit explicit `EnvironmentChanged` events.

## 6. Capability System
The `CapabilityManager` centrally tracks the development maturity of simulated behaviors. 
Possible states:
- `SUPPORTED`: Model implemented and validated.
- `DATA_REQUIRED`: Awaiting dataset harvesting.
- `MODEL_REQUIRED`: Data exists, awaiting mathematical model.
- `VALIDATION_REQUIRED`: Model constructed, pending regression.
- `NOT_SUPPORTED`: Beyond current project scope.

## 7. Event Model
All transformations are logged to the `EventRecorder` as explicit events, including `SimulationStarted`, `EnvironmentChanged`, `MechanismExecuted`, and granular updates (e.g., `CHARGE_CHANGE`). This serves as a transparent provenance ledger of *why* a variable changed.

## 8. Prediction vs Simulation
Prediction is distinct from Simulation. 
- **PredictionService**: Single-state, static inference (e.g., initial Zeta Potential classification).
- **SimulationEngine**: Time-dependent state evolution. 
Mechanisms may invoke static predictions (surrogate models) as steps within a time evolution loop, provided the causal triggers are explicitly documented.

## 9. Future Biological Architecture
Future mechanisms (`CellInteractionMechanism`, `CellularUptakeMechanism`, `PharmacokineticMechanism`, etc.) are pre-registered as stubs. Their status defaults to `DATA_REQUIRED`. They are designed to plug directly into the `BiologicalState` payload without architectural refactoring.

## 10. Current Capabilities Status
The system maintains the following definitive capability registry:
*   `zeta_prediction` = SUPPORTED
*   `cytotoxicity_prediction` = SUPPORTED
*   `drug_release` = SUPPORTED_WITH_DOMAIN_LIMITS (Korsmeyer-Peppas implementation is restricted strictly to its validated dataset parameters. It is NOT a generalized drug-release model or a general environmental-response simulator for arbitrary nanoparticles.)
*   `size_stability` = DATA_REQUIRED
*   `aggregation` = DATA_REQUIRED
*   `protein_corona` = DATA_REQUIRED
*   `cellular_uptake` = DATA_REQUIRED
*   `pharmacokinetics` = DATA_REQUIRED
*   `biodistribution` = DATA_REQUIRED
*   `therapeutic_response` = DATA_REQUIRED
*   `toxicity` = DATA_REQUIRED
*   `human_clinical_outcome` = NOT_SUPPORTED

## 11. Architectural Limits
*   **Mechanism interaction**: Future mechanism interaction (e.g., Aggregation slowing Drug Release) is currently stubbed with a `dependencies` array interface in `BaseMechanism`. This requires extending the runtime into a Directed Acyclic Graph (DAG) executor to resolve scientific causal graphs.
