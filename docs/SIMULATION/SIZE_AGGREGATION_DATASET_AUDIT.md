# Size & Aggregation Dataset Audit

## Repository Search
- `data/processed/drug_release_longitudinal.csv`: Tracks temporal drug release. Size is a static calculated value ($D = 6 / 	ext{SA-V}$). No DLS/PDI time series.
- `data/raw/zeta_potential_69_enms.xlsx`: Static structural descriptors.
- `data/raw/cytotoxicity_meta_analysis.xlsx`: Static parameters mapped to biological endpoints.

## External Search
- Searches in the NanoSafety Cluster (Zenodo) and general supplemental literature confirmed that DLS/PDI time-series are typically published as isolated figures for 1-2 formulations per study.
- No aggregated, canonical, ML-ready dataset spanning diverse medicinal nanoparticles with proper temporal tracking under controlled environments was found.

## Audit Outcome
Outcome C (Data Insufficient). Longitudinal physical trajectory datasets for medicinal nanoparticles are currently missing.
