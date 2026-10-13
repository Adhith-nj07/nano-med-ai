# S5 Pre-Integration Architecture & Dry Run

This document captures the current state of NanoMedAI's software architecture as it prepares to ingest the future S5 (Physical Stability) dataset and model.

## 1. Current S5 Status
The `size_stability` and `aggregation` capabilities are currently blocked at `DATA_REQUIRED`. 
* No real scientific S5 models have been implemented. 
* No aggregation predictions are generated.
* No particle size evolution runs in production.

## 2. Data-Provider Boundary
The `PhysicalStabilityDataProvider` strictly enforces the transition from a generic dataset (e.g., CSV) to the unified `Trajectory` schema. It ensures values like `temperature_c`, `pH`, and `particle_size` are appropriately extracted while preserving crucial data integrity attributes like `verification_status` and `provenance`.

## 3. Validation Gate
An internal software checkpoint (`S5ModelReadinessGate`) prevents integration of models lacking a rigorous scientific foundation. Even if an S5 dataset and model arrive, they cannot activate the capability unless:
* `status` is explicitly `"VALIDATED"`.
* Both `validation_method` and `validation_metrics` (e.g. RMSE, MAE, GroupKFold results) are populated.
* The training dataset `verification_status` is `"MODEL_READY"`.
* The `supported_domain` declares valid operating sizes and materials.

## 4. Model Metadata
Future models must attach a `ModelMetadata` schema to track origin, scope, and robustness. Instantiating a `ModelMetadata` object with `status=VALIDATED` will throw an error natively if metric requirements are left blank, blocking accidental capability enablement.

## 5. Mock Integration Path
A `MockSizeStabilityMechanism` was injected in dry-run tests to verify the software layout. It successfully registers with the `MechanismRegistry` and runs under the exact `SimulationEngine` architecture, confirming that once a real mechanism is authored, it will naturally interoperate with the temporal engine.

## 6. Compatibility Checks
Each mechanism exposes a `check_compatibility` function. During the dry-run, testing proved that if an environment variable is pushed outside a mechanism's `supported_domain` (e.g., changing temperature to 45°C when the model only supports up to 40°C), the engine drops the mechanism explicitly rather than producing corrupted extrapolated outputs.

## 7. Environment Changes
When the environment is updated:
1. `EnvironmentChanged` events are recorded.
2. The Engine loops through active mechanisms and queries `check_compatibility()`.
3. Incompatible models are suspended from the execution path.
4. `ValidationFailed` warning events are logged.

## 8. API Behavior
The API exposes `capabilities` with deep context. 
If an unsupported capability is requested or fails to load, structural exceptions like `DataNotValidatedError` or `IncompatibleEnvironmentError` allow frontend clients to display meaningful error reasons instead of generic 500 crashes.

## 9. Checkpoint Behavior
The `CheckpointManager` serializes the deep `SimulationState`, allowing the exact timeline, trajectory events, physical properties, and active mechanisms to be saved. The dry-run proved that state can be snapshotted, the environment modified, the checkpoint restored, and the simulation continued flawlessly.

## 10. Exact future integration steps
When the external Claude process delivers the model-ready S5 data and equations:
1. Load dataset into `data/` and point the `CsvPhysicalStabilityDataProvider` to it, marking records `MODEL_READY`.
2. Generate the mathematical models and export error metrics.
3. Instantiate `ModelMetadata(status=VALIDATED, validation_metrics={...}, ...)`.
4. The `S5ModelReadinessGate` checks the payload.
5. Create `SizeStabilityMechanism` executing the equation inside its `step()` method.
6. Register the mechanism.
7. Change capability `size_stability` to `CapabilityState.SUPPORTED`.
8. The `SimulationEngine` begins generating live physical stability trajectories dynamically.
