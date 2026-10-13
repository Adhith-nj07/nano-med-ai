# Drug Release Data Validation Report

## Source
- **Publication**: Bannigan et al., "Machine learning models to accelerate the design of polymeric long-acting injectables", Nature Communications (2022).
- **DOI**: `10.1038/s41467-022-35343-w`
- **Repository**: Zenodo record `10.5281/zenodo.7309021`

## Raw dataset
- **Files**: `Dataset_14_feat.tsv` (actually formatted as an Excel / ZIP archive)
- **Rows**: 3,783 experimental measurements
- **Columns**: 17 formulation and experimental features, mostly focused on dimensionless ML input features.

## Nanoparticle filtering
We strictly enforced the NanoMedAI mandate: the data must reflect *nanoparticle* medicines.
Using the `SA-V` (Surface Area to Volume) ratio and `SE` (Shape encoding where 0 = sphere) columns, the particle diameter $D$ was derived ($D = 6 / \text{SA-V}$). The inclusion criteria required $D \le 1000 \text{ nm}$.
- **Total records**: 3,783
- **Included nanoparticle records**: 115
- **Excluded microparticle/implant records**: 3,598
- **Ambiguous/Other records**: 70

## Longitudinal structure
The filtered dataset comprises true longitudinal trajectories.
- **Unique nanoparticle trajectories**: 9
- **Median time points per trajectory**: 12
- **Min/Max time**: ~0 to 30 days.

## Environmental coverage
**CRITICAL LIMITATION**: The ML-optimized dataset provided by the authors stripped out all environmental variables (`pH`, `temperature`, `buffer`, `agitation`). As a result, the current dataset has 100% missingness for the precise simulation control parameters needed for dynamic NanoMedAI interventions. 
- **Temperature coverage**: 100% missing (assumed 37°C in vitro, but unrecorded).
- **pH coverage**: 100% missing (assumed 7.4, but unrecorded).
- **Medium coverage**: 100% missing.

## Data quality
- **Duplicates**: None found at identical trajectory/time intersections.
- **Impossible values**: Release is bounded cleanly between 0.0 and 1.0 (normalized to 0-100%).
- **Monotonicity**: Time points are strictly monotonically increasing. Small deviations in cumulative release are within experimental noise margins.

## Provenance
- **Digitized vs Direct**: The Zenodo dataset aggregates both digitized literature graphs and raw experimental tables, but does not provide a row-level flag distinguishing them. Measurement provenance is marked `UNKNOWN`.

## Final dataset
- **Scientifically usable trajectories**: 9
- **Scientifically usable measurements**: 115
