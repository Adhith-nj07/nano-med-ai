# Data Harmonization Plan

## Status: COMPLETE

### 1. Stability Dataset Preprocessing
- **Source:** `data/raw/zeta_potential_69_enms.xlsx`
- **Target Cleaning:** The target `Zeta (mV)` is numeric and clean.
- **Categorical Normalization:** 
  - `Shape group`: Needs capitalization normalization (e.g., 'spherical' vs 'Spherical').
  - `Type of Coating (Anionic, Cationic, Neutral)`: Rename column to `Coating Charge` for programmatic ease.
- **Feature Encoding:** One-Hot Encoding (OHE) for `metal core`, `Coating`, `Type of Coating`, `Ageing`, and `Shape group`.
- **Scaling Requirements:** Standardize continuous features (`Diameter (TEM-STEM)`, `Geometric Surface Area (nm2)`).
- **Validation Strategy:** Standard K-Fold or Train/Test split (no study IDs are present to group by).

### 2. Cytotoxicity Dataset Preprocessing
- **Source:** `data/raw/cytotoxicity_meta_analysis.xlsx`
- **Target Cleaning:** Use `Toxicity`. Encode 'Nontoxic' -> 0, 'Toxic' -> 1. Drop `Viability (%)` to prevent target leakage.
- **Categorical Normalization:**
  - `Material type`, `Cell name`, `Assay` will be One-Hot Encoded.
- **Scaling Requirements:** Standardize `Core size (nm)`, `Hydro size (nm)`, `Surface charge (mV)`, `Surface area (m2/g)`, `Exposure time`, and `Mass dose (ug/mL)`.
- **Validation Strategy:** `GroupKFold` cross-validation using `Pubmed ID` as the grouping variable. This prevents data leakage where rows from the same published study end up in both the training and test sets.
- **Missing Data:** Dataset has 0 missing values for the selected features.

### 3. File Outputs
Processed datasets will be saved to:
- `data/processed/stability_processed.csv`
- `data/processed/cytotoxicity_processed.csv`
