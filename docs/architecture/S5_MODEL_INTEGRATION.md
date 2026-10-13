# S5 Model Integration Path

This document outlines the software infrastructure and the future integration sequence for the Phase S5 (Physical Stability) dataset and models.

## 1. Objective
To allow physical transformation mechanisms (like nanoparticle size evolution and aggregation) to be plugged into the `SimulationEngine` immediately upon scientific validation, without requiring architectural rewrites. 

## 2. Dataset to Domain Adapter (Data Provider Interface)
The `PhysicalStabilityDataProvider` abstract base class isolates the Simulation Engine from raw dataset structures (e.g., CSV, SQL, data lakes).
* **Location**: `src/simulation/data_providers.py`
* **Responsibilities**:
  * Loads parsed and validated data.
  * Explicitly maps dataset fields to the standardized `Trajectory` domain schema.
  * Supplies time-series `observations` and `conditions`.
  * Preserves `provenance`.
  * Enforces the `verification_status` of the trajectory (e.g., `PROCESSED`, `VALIDATED`, `MODEL_READY`).

## 3. Validated Data Boundary & Capabilities
The simulation engine distinguishes between RAW, PROCESSED, and VALIDATED data via strict verification status. 
The system enforces capability limits via `CapabilityState`:
* Currently, S5 capabilities (`size_stability`, `aggregation`) return `DATA_REQUIRED`. 
* Simply adding a CSV file to the repository does not enable the capability.
* Mechanisms track their own `status` and refuse to `can_run()` unless it is explicitly altered to `SUPPORTED` following rigorous validation.

## 4. Model Metadata Structure
When the S5 model is trained, it must be accompanied by an explicit metadata payload reflecting the `ModelMetadata` schema (`src/simulation/metadata.py`):
* `model_id` / `model_version`
* `target`
* `training_data_version`
* `validation_method` / `validation_metrics` (e.g., `GroupKFold`, `RMSE`)
* `supported_domain` & `supported_conditions`
* `status` (`EXPERIMENTAL`, `VALIDATED`, etc.)

## 5. Mechanism Integration Contract
Future S5 models will implement the `BaseMechanism` interface (`src/simulation/mechanisms.py`):
* **Inputs**: Inherits `SimulationState` containing physical/environment domains and the current time.
* **Outputs**: Updated properties directly within `NanoparticleState` (e.g., size, PDI) and `TransformationEvent` records.
* **Dependencies**: Explicitly declared via `dependencies` property (e.g., Aggregation depends on Zeta Potential).
* **Compatibility Check**: Implement `check_compatibility(state) -> (bool, str)` using `supported_domain` metadata to gracefully block out-of-domain inputs without hallucinating endpoints.
* **Provenance**: Events carry `uncertainty`, `model_source`, and `validity` in their `payload`.

## 6. Simulation Checkpoints
Long-running trajectories with environment changes require state preservation. `SimulationEngine` now natively supports checkpointing:
* **Serialization**: `CheckpointManager.save_checkpoint(engine)`
* **Deserialization**: `CheckpointManager.load_checkpoint(engine, data)`
* Checkpoints preserve all physical parameters, events, and capabilities allowing pauses/resumes across environments.

## 7. Dynamic Environment Updates
Environment changes update the `EnvironmentState`. The engine executes a real-time capability re-evaluation:
1. Validates the new environment (`EnvironmentChanged` event).
2. Probes `mech.check_compatibility()` for all active mechanisms.
3. Automatically explicitly blocks/disables any incompatible mechanism, attaching `VALIDATION_FAILED` warning events.

## 8. Exact Integration Sequence (When S5 Model Arrives)
1. **S5 Dataset Arrival**: Raw data ingested via separate extraction pipeline.
2. **Data Validation**: Curated into `MODEL_READY` trajectories via the `PhysicalStabilityDataProvider`.
3. **Model Development**: Separate ML process builds/fits equations.
4. **Grouped Validation**: ML process logs `ModelMetadata` including strict `supported_domain` constraints and MAE/RMSE metrics.
5. **Mechanism Registration**: Create `SizeStabilityMechanism(BaseMechanism)` in `mechanisms.py`, implementing `step()` and `check_compatibility()`.
6. **Capability Change**: Update `CapabilityManager` to change `size_stability` status to `SUPPORTED`.
7. **Simulation**: Future API requests dynamically pick up the capability and execute the S5 transformation step over time.
