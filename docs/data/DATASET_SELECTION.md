# Dataset Selection

## Status: COMPLETE

Two public datasets from Zenodo were selected to support the Stability and Cytotoxicity prediction tasks.

## Stability Dataset

**Dataset:** Zeta potential dataset for 69 engineered nanomaterials
**Source:** Zenodo
**DOI:** 10.5281/zenodo.14864383
**URL:** https://zenodo.org/records/14864383
**License:** Open Access
**Download date:** 2026-09-26
**File name:** `data/raw/zeta_potential_69_enms.xlsx`
**Number of rows:** 69
**Number of columns:** 22
**Target:** Zeta (mV)
**Target unit:** Millivolts (mV)
**Available features:** `metal core`, `Coating`, `Type of Coating (Anionic, Cationic, Neutral)`, `Ageing`, `Diameter (TEM-STEM)`, `Shape group`, `Geometric Surface Area (nm2)`
**Important experimental conditions:** N/A (represents intrinsic material properties under standard conditions).
**Missingness:** 0 missing values.
**Duplicates:** None (69 unique ENMs).
**Potential leakage:** `Type of Coating` explicitly states charge (Anionic/Cationic/Neutral) which strongly dictates the sign of the Zeta potential. However, this is a legitimate synthesis design choice, not a post-measurement leak.
**Study/source identifiers:** None (single consolidated dataset).
**Reasons for selection:** Contains highly curated physicochemical parameters explicitly designed for Zeta potential modeling.

## Cytotoxicity Dataset

**Dataset:** Meta-analyzed datasets for toxicity classification of metal oxide nanoparticles (Subset: 2017_MeOx_IIIB_HYU)
**Source:** Zenodo
**DOI:** 10.5281/zenodo.15300193
**URL:** https://zenodo.org/records/15300193
**License:** Open Access
**Download date:** 2026-09-26
**File name:** `data/raw/cytotoxicity_meta_analysis.xlsx`
**Number of rows:** 666
**Number of columns:** 32
**Target:** Toxicity (Binary), Viability (%)
**Target unit:** Categorical (Toxic/Nontoxic), %
**Available features:** `Material type`, `Core size (nm)`, `Hydro size (nm)`, `Surface charge (mV)`, `Surface area (m2/g)`, `Assay`, `Cell name`, `Cell species`, `Cell origin`, `Cell type`, `Exposure time`, `Mass dose (ug/mL)`.
**Important experimental conditions:** `Exposure time` (6-72h), `Mass dose (ug/mL)` (0-1500), `Cell name` (16 cell lines), `Assay` (12 types).
**Missingness:** 0 missing values.
**Duplicates:** Multiple measurements per material across different assays/doses.
**Potential leakage:** Derived structural computational features (e.g., ΔHsf) are safe. The target `Toxicity` is directly derived from `Viability (%)`, so we must drop one when training on the other.
**Study/source identifiers:** `Pubmed ID` (crucial for GroupKFold cross-validation).
**Reasons for selection:** Provides a rich set of experimental conditions (dose, time, cell line) and explicitly includes `Pubmed ID` to prevent data leakage during cross-validation via GroupKFold. It also already provides a well-documented Toxic/Nontoxic classification.

## Reasons alternatives were rejected
The "Cytotoxicity data for 14 metal oxide nanoparticles" dataset (`cytotoxicity_14_metal_oxides.xlsx`) lacked varied exposure times (all were 24h) and did not include a clear study identifier (`Pubmed ID`) for robust group-aware cross-validation, making it less suitable for demonstrating generalization to unseen studies.
