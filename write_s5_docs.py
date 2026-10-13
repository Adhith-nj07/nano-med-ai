import os

docs = {
    'docs/SIMULATION/SIZE_DYNAMICS.md': '''# Size Dynamics Model

## Status: S5_DATA_REQUIRED

## Scientific Objective
To model the temporal evolution of primary and hydrodynamic nanoparticle size resulting from storage conditions or environmental exposure.

## Candidate Models Assessed
1. **Smoluchowski Coagulation Equation**: Mechanistic population-balance model. Requires detailed rate constants (attachment efficiencies) dependent on DLVO forces, rarely available in standard nanomedicine datasets.
2. **Empirical Time-Series Plateau**: Exponential convergence mapping initial size to a stable aggregated plateau based on ionic strength and temperature.

## Implementation Status
Not implemented. No longitudinal dataset tracking physical size over time for medicinal nanoparticles (under controlled experimental conditions) is currently available in the repository. Implementing an equation without fitting real trajectories violates the core scientific constraint of NanoMedAI.
''',
    
    'docs/SIMULATION/PDI_DYNAMICS.md': '''# PDI Dynamics Model

## Status: S5_DATA_REQUIRED

## Scientific Objective
To model changes in Polydispersity Index (PDI) as a proxy for physical instability and aggregation over time.

## Candidate Models Assessed
1. **Ostwald Ripening Models (Lifshitz-Slyozov-Wagner)**: Predicts narrowing/widening of size distribution based on dissolution/re-precipitation.
2. **Empirical PDI Broadening**: A statistical broadening model mapping time to PDI increase.

## Implementation Status
Not implemented. PDI time-series data is absent. Interpolating PDI changes from static snapshots or unverified literature claims without a canonical longitudinal dataset is scientifically invalid.
''',
    
    'docs/SIMULATION/AGGREGATION_MODEL.md': '''# Aggregation Kinetics Model

## Status: S5_DATA_REQUIRED

## Scientific Objective
To simulate physical aggregation and agglomeration of nanoparticles in response to environmental conditions (pH, temperature, ionic strength).

## Investigated Dependencies
- **Zeta Potential**: While surface charge acts as a proxy for colloidal stability, inferring *kinetic aggregation rates* strictly from a single static Zeta surrogate prediction without experimental calibration of the Hamaker constant and Debye length is overextrapolation.

## Implementation Status
Not implemented. Environmental variables (temperature, pH) cannot be causally linked to aggregation state updates without experimental trajectory data providing clear evidence for the formulation under test.
''',
    
    'docs/SIMULATION/SIZE_AGGREGATION_DATASET_AUDIT.md': '''# Size & Aggregation Dataset Audit

## Repository Search
- `data/processed/drug_release_longitudinal.csv`: Tracks temporal drug release. Size is a static calculated value ($D = 6 / \text{SA-V}$). No DLS/PDI time series.
- `data/raw/zeta_potential_69_enms.xlsx`: Static structural descriptors.
- `data/raw/cytotoxicity_meta_analysis.xlsx`: Static parameters mapped to biological endpoints.

## External Search
- Searches in the NanoSafety Cluster (Zenodo) and general supplemental literature confirmed that DLS/PDI time-series are typically published as isolated figures for 1-2 formulations per study.
- No aggregated, canonical, ML-ready dataset spanning diverse medicinal nanoparticles with proper temporal tracking under controlled environments was found.

## Audit Outcome
Outcome C (Data Insufficient). Longitudinal physical trajectory datasets for medicinal nanoparticles are currently missing.
''',
    
    'docs/SIMULATION/SIZE_AGGREGATION_VALIDATION.md': '''# Size & Aggregation Validation

## Grouped Validation Strategy (Pending)
When appropriate longitudinal size/aggregation datasets are acquired:
- The data must be strictly grouped by `trajectory_id` and `formulation_id`.
- Data leakage between $t=1$ and $t=24$ for the same physical sample must be blocked using `GroupKFold`.
- Validation metrics will rely on Trajectory RMSE, MAE, and Time-Series similarity.

## Current Validation Status
Not applicable. No models were fitted or implemented due to insufficient data.
''',
    
    'docs/SIMULATION/SIZE_AGGREGATION_LIMITATIONS.md': '''# Size & Aggregation Limitations

## Unverified Causality
NanoMedAI explicitly rejects fabricating causal environmental responses. Because no longitudinal dataset establishes how pH or temperature specifically alters the size of the tracked formulations over time, these interventions remain scientifically unsupported for dynamic aggregation.

## Unlinked Measurements
It is not permissible to mix TEM primary size observations with DLS hydrodynamic size observations as a single longitudinal metric. They measure different physical properties (dry core vs. solvated particle).
''',
    
    'docs/SIMULATION/SIZE_AGGREGATION_DATA_PROVENANCE.md': '''# Size & Aggregation Data Provenance

## Canonical Schema Definition
Future ingested size and aggregation data MUST adhere to the following schema to maintain scientific integrity:
- `study_id`, `experiment_id`, `trajectory_id`, `formulation_id`
- `nanoparticle_classification` (must strictly be medicinal)
- `material`, `core`, `coating`, `drug`
- `primary_particle_size_nm`, `hydrodynamic_size_nm`, `pdi`
- `measurement_method`
- `temperature_c`, `pH`, `ionic_strength_m`, `medium`, `buffer`
- `time`, `time_hours`
- `aggregation_measurement`, `aggregation_index`

## Current Provenance
No external data was acquired in Phase S5 due to the absence of public structured datasets meeting the stringent longitudinal and medicinal-relevance criteria.
'''
}

for path, content in docs.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
