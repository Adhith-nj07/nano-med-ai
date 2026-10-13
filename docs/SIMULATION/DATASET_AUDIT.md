# Repository Dataset Audit

## Overview
An exhaustive audit of `data/raw/` and `data/processed/` reveals that all currently integrated datasets are cross-sectional (static) rather than longitudinal (time-series).

## Dataset Details

### 1. `zeta_potential_198_enms_millipore.xlsx` & `zeta_potential_90_enms_phosphate.xlsx`
- **Rows**: 198 & 90 respectively.
- **Inputs**: Shape, Core, Size, Ligand SMILES, Experimental protocol.
- **Target**: Zeta potential (mV).
- **Time Information**: None. Measurements represent a single stabilized endpoint.
- **Suitability**: **C — Suitable only for static ML prediction**.

### 2. `cytotoxicity_meta_analysis.xlsx`
- **Rows**: 666
- **Inputs**: Material, Core size, Surface charge, Cell name, Assay, Exposure time, Mass dose.
- **Target**: Toxicity (Viability %).
- **Time Information**: `Exposure time`. However, this is an independent input feature for a static endpoint classifier, not a longitudinal tracking of a single well plate over time.
- **Suitability**: **C — Suitable only for static ML prediction**.

### 3. Missing Datasets
There are no datasets representing drug release, dissolution, degradation, protein corona, or cell uptake in the repository. These must be acquired externally.
- **Suitability**: **D — Insufficient data**.
