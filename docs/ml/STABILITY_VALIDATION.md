# Stability Validation Design

- **Dataset Size**: 288 rows
- **Grouping Variable**: study_id
- **Number of Unique Studies**: 32
- **Strategy**: 5-Fold GroupKFold.
- **Rationale**: The presence of multiple studies allows us to isolate complete studies in the validation fold. This prevents the model from simply memorizing the specific laboratory protocols of a given publication.
