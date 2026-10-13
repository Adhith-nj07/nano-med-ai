# Stability Duplicate Audit

- **Exact row duplicates**: 0
- **Nanoparticle duplicates (same core, size, shape, ligand, medium)**: 60 records belong to duplicate groups.
- **Decision**: Exact row duplicates (if any) will be removed during training. Nanoparticle duplicates (different experiments/targets for the exact same NP) will be kept because GroupKFold will group them by study_id. If they belong to the same study, they are valid repeats. If they belong to different studies, GroupKFold ensures they do not leak across the train/test boundary.
