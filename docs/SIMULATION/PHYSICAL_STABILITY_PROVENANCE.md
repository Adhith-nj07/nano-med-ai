# Physical Stability Provenance

## Provenance Tracking
Every record in the target dataset will carry explicit provenance via:
- `measurement_provenance` (e.g., "digitized_from_figure", "machine_readable_supplement")
- `source_publication`
- `source_doi`
- `source_repository`

## Leakage Prevention
Models must be validated using `GroupKFold(groups=study_id)` to prevent formulation leakage. No two trajectories from the same source paper can span the train/test divide.
