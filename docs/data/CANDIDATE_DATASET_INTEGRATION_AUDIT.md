# Candidate Dataset Integration & Audit Report

**Date:** 2026-10-12  
**Status:** Audit Completed; Candidate Integration & Training Pipeline Implemented  
**Pipeline Script:** `scripts/train_from_candidates.py`

---

## 1. Executive Summary & Audit Findings

Four candidate datasets were audited and evaluated for integration into the NanoMedAI data and modeling pipeline. All files carry explicit candidate status (`training_ready = NO...`), which has been preserved and verified. Original CSVs are preserved in `data/processed/public_data_candidates/` and Downloads.

| Dataset Candidate | Rows | Cols | Missing Values | Duplicate Rows | Target Label / Endpoint | Source License & Metadata | `training_ready` Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `zeta_potential_288_candidate.csv` | 288 | 17 | 0 (0.0%) | 0 | `zeta_potential_mv` (-70.0 to +60.0 mV) | CC-BY-4.0 (Zenodo 10.5281/zenodo.14866284 & 14866297) | `NO: candidate; retain medium as a model condition and evaluate by study/formulation group` |
| `zeta_potential_69_candidate.csv` | 69 | 28 | 0 (0.0%) | 0 | `zeta_potential_mv` (-57.9 to +64.3 mV) | CC-BY-4.0 (Zenodo 10.5281/zenodo.14864383) | `NO: candidate; single dataset and external validation still required` |
| `cytotoxicity_meox_iiib_candidate.csv` | 666 | 20 | 0 (0.0%) | 0 | `source_toxicity_label` (Nontoxic: 487, Toxic: 179) | Confirm exact Zenodo Rights field before redistribution (Zenodo 10.5281/zenodo.15300193) | `NO: candidate; harmonization and grouped validation required` |
| `drug_release_115_candidate.csv` | 115 | 26 | 8 unmeasured metadata cols (100% NaN) | 0 | `cumulative_release_pct` (0.0% to 90.11%) | CC-BY-4.0 (Zenodo 10.5281/zenodo.7309021 / Bannigan et al. 2022) | Evaluated with 9 trajectory groups |

---

## 2. Task 1: Zeta Potential Regression

### 2.1 Compatibility & Duplicate Assessment (288 vs 69)
- **Overlap Check:** 0 overlapping records found. Zenodo DOIs and underlying experimental studies do not share sample identifiers.
- **Measurement Conditions:**
  - **288-row dataset:** Distinctly strata-separated media: 198 records in `Millipore Water` and 90 records in `PBS pH 7.4`. Includes SMILES strings (`ligand1_smiles`, `ligand2_smiles`) enabling chemical charge and MW calculation. Sizes range from 1.5 to 31.5 nm (noble metal cores: Au, Pt, Pd, CdSe, Ag).
  - **69-row dataset:** Measurement medium is recorded as `"not specified in selected table; see primary dataset metadata"`. Zeta potential depends strongly on solution pH and ionic strength. Nanoparticle sizes range up to 1,500 nm (predominantly metal oxides: CeO2, SiO2, TiO2, ZnO). No ligand SMILES are provided.
  - **Study Grouping:** 288-row dataset has 32 distinct literature study DOIs (`study_id`). The 69-row dataset lacks individual study groups.
- **Decision:** **Do NOT concatenate.** Concatenation would contaminate the medium condition feature, introduce missing ligand structures, and break group-aware cross-validation across distinct studies. The 288-row dataset is selected for the active stability pipeline.

### 2.2 Schema Mapping & Feature Preprocessing
- `shape` -> `Shape` (categorical, OHE)
- `core_material` -> `Core` (categorical, OHE)
- `measurement_medium` -> `Medium` (categorical, OHE)
- `ligand1_smiles` -> `_extract_charge()` -> `Coating_Charge` (categorical, OHE)
- `core_or_reported_size_nm` -> $\log(1 + \text{size})$ -> `Log_Size` (numeric, Standardized)
- `ligand1_smiles` -> `_estimate_mw()` -> `Estimated_Ligand_MW` (numeric, Standardized)
- Target: `zeta_potential_mv` -> `Zeta_mV`
- Grouping: `study_id` (32 groups)

### 2.3 Group-Aware Validation Results
- **Model:** Ridge Regression ($\alpha = 10.0$)
- **Validation:** 5-fold `GroupKFold` grouped by `study_id` (32 groups, 288 rows)
- **Metrics:**
  - $R^2$: `0.108`
  - $\text{MAE}$: `18.90 mV`
  - $\text{RMSE}$: `25.91 mV`
- **Model Path:** `models/stability_model_final.joblib`

---

## 3. Task 2: Cytotoxicity Classification

### 3.1 Label Rule Verification & Independence Check
- **Label Rule:** `"Publisher dataset describes Toxicity from 50% cell viability threshold"`.
  - Toxic ($n=179$): all `cell_viability_pct` $\le 49.72\%$ (range: $-1.43\%$ to $49.72\%$).
  - Nontoxic ($n=487$): all `cell_viability_pct` $\ge 50.80\%$ (range: $50.80\%$ to $350.90\%$).
  - Exact match: 0 threshold violations.
- **Target Mapping:** `Toxic` $\to 1$, `Nontoxic` $\to 0$.
- **Strict Input Independence:** `cell_viability_pct` is strictly **excluded** from model input features to prevent target leakage.

### 3.2 Schema Mapping & Preprocessing
- `material_type` -> `Material type` (categorical, OHE)
- `assay` -> `Assay` (categorical, OHE)
- `cell_line` -> `Cell name` (categorical, OHE)
- `core_size_nm` -> `Core size (nm)` (numeric, Standardized)
- `hydrodynamic_size_nm` -> `Hydro size (nm)` (numeric, Standardized)
- `surface_charge_mv` -> `Surface charge (mV)` (numeric, Standardized)
- `surface_area_m2_g` -> `Surface area (m2/g)` (numeric, Standardized)
- `exposure_time_h_raw` -> `Exposure time` (numeric, Standardized)
- `mass_dose_ug_ml` -> `Mass dose (ug/mL)` (numeric, Standardized)
- Target: `source_toxicity_label` -> `Toxicity`
- Grouping: `study_pubmed_id` (17 groups)

### 3.3 Group-Aware Validation Results
- **Model:** Random Forest Classifier (100 estimators, random_state=42)
- **Validation:** 5-fold `GroupKFold` grouped by `study_pubmed_id` (17 groups, 666 rows)
- **Metrics:**
  - Accuracy: `0.756`
  - Precision: `0.603`
  - Recall: `0.605`
  - F1 Score: `0.482`
- **Model Path:** `models/cytotoxicity_model.joblib`

---

## 4. Task 3: Drug-Release Regression

### 4.1 Trajectory Sufficiency & Grouping
- **Sample Count:** 115 time-series measurements.
- **Independent Trajectories:** Exactly 9 independent trajectories (`bannigan_2022_38` to `bannigan_2022_51`), all from a single publication (Bannigan et al. 2022).
- **Sufficiency Audit:** 9 independent trajectories is **insufficient** for generalizable machine learning claims. Cross-validation across 9 trajectories leaves only 1–2 formulation trajectories per validation fold, producing high fold-to-fold variance. Scope is strictly restricted to spherical PLGA/PLA particles loaded with paclitaxel or letrozole.
- **Validation Protocol:** Grouped cross-validation keeping all time points of a `trajectory_id` in the same fold. No time points are split across train/test splits.

### 4.2 Schema Mapping & Preprocessing
- `particle_size_nm`, `drug_mw`, `drug_loading_pct`, `polymer_mw`, `la_ga_ratio`, `time_hours` (numeric, Standardized)
- `drug_name`, `polymer` (categorical, OHE)
- Target: `cumulative_release_pct`
- Grouping: `trajectory_id` (9 groups)

### 4.3 Group-Aware Validation Results
- **Model:** Random Forest Regressor (80 estimators, min_samples_leaf=2, random_state=7, n_jobs=1)
- **Validation:** 5-fold `GroupKFold` grouped by `trajectory_id` (9 groups, 115 rows)
- **Metrics:**
  - MAE: `8.32 percentage points`
  - RMSE: `10.36 percentage points`
  - $R^2$: `0.779`
- **Model Path:** `models/drug_release_model.joblib`

---

## 5. Training Commands & Artifact Summary

Execute the end-to-end candidate pipeline:
```bash
py -3.14 scripts/train_from_candidates.py
```

Generated artifacts:
- `models/stability_model_final.joblib`
- `models/cytotoxicity_model.joblib`
- `models/drug_release_model.joblib`
- `data/processed/candidate_training_summary.json`

---

## 6. Blockers & Limitations

1. **Candidate Status & Redistribution:** All candidate datasets remain marked with `training_ready=NO` in source metadata. License rights for `cytotoxicity_meox_iiib_candidate.csv` must be confirmed on Zenodo prior to external redistribution.
2. **69-Row Zeta Potential Incompatibility:** The 69-row candidate lacks medium characterization and ligand SMILES; it remains unmerged pending external pH/ionic strength recovery.
3. **Drug Release Small Sample Size:** With only 9 trajectories from a single paper, the drug release model should be treated as an exploratory research prototype rather than a general formulation predictor.
4. **Generalization:** Metrics reflect group-level cross-validation within the experimental domains and do not guarantee accuracy on untested nanoparticle formulations.
