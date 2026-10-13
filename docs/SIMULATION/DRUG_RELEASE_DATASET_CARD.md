# Drug Release Dataset Card

## Purpose
To provide longitudinal temporal drug-release trajectories for calibrating NanoMedAI Phase S4 simulation models.

## Population & Scope
- **Nanoparticle Scope**: Strictly filtered to spherical polymeric nanoparticles with derived diameters $\le 1000 \text{ nm}$.
- **Drug Scope**: Letrozole (LTZ) and Paclitaxel (PTX) are the only two drugs represented in the final filtered set.
- **Polymer Scope**: PLGA and PLA.

## Sample Count
- **Trajectory count**: 9 unique experimental formulation trajectories.
- **Measurement count**: 115 continuous temporal observations.

## Variables & Units
- `trajectory_id`: String (generated stable ID)
- `nanoparticle_classification`: 'NANOPARTICLE'
- `drug_name`: 'LTZ' or 'PTX'
- `polymer`: 'PLGA' or 'PLA'
- `time_hours`: Elapsed time in hours (normalized from Days).
- `cumulative_release_pct`: % (normalized from fractional release).
- `particle_size_nm`: Derived nanometers from SA/V ratio.

## Inclusion/Exclusion Criteria
- **Included**: `SE == 0` (Spheres) AND $SA-V \ge 6000 \text{ mm}^{-1}$ ($D \le 1000 \text{ nm}$).
- **Excluded**: Cylinders, films, and any spherical formulations with $D > 1000 \text{ nm}$ (which constituted >95% of the raw data).

## Provenance & Licensing
- **Source**: Bannigan et al., Nature Communications, 2022. (DOI: 10.1038/s41467-022-35343-w)
- **Repository**: Zenodo `10.5281/zenodo.7309020`
- **License**: CC-BY 4.0 (as per standard Zenodo / Nature open data policies).

## Limitations & Known Biases
1. **Scope Bias**: The dataset is entirely composed of PLGA/PLA carrying hydrophobic drugs (PTX, LTZ). It cannot be generalized to hydrophilic drugs, liposomes, or lipid nanoparticles.
2. **Missing Environments**: Lack of pH and temperature columns limits the ability to model dynamic environmental interventions.
3. **Low Sample Size**: 9 trajectories is highly restrictive for deep machine learning and barely sufficient for calibrating basic empirical equations (e.g., Korsmeyer-Peppas).

## Validation Considerations
All validation of downstream ML models must utilize `GroupKFold` grouped by `trajectory_id` to strictly prevent temporal data leakage.
