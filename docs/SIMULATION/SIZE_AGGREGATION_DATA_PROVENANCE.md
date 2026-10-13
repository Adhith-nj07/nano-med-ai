# Size & Aggregation Data Provenance

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
