# Final Schema Validation

## Stability Features (zeta_potential_69_enms.xlsx)

| Feature | Type | Unique Values | Missing | Range/Categories | Use |
| ------- | ---- | ------------: | ------: | ---------------- | --- |
| `metal core` | Categorical | 14 | 0 | 'Ag', 'Ag2S', 'CeO2', etc. | YES |
| `Coating` | Categorical | 21 | 0 | 'PEG 1500', 'PVP', etc. | YES |
| `Type of Coating \n(Anionic, Cationic, Neutral)` | Categorical | 5 | 0 | 'neutral', 'anionic', 'cationic', etc. | YES (Rename to `Coating_Charge`) |
| `Ageing` | Categorical | 2 | 0 | 'Pristine', 'Aged' | YES |
| `Diameter  (TEM-STEM)` | Numeric | N/A | 0 | 3.0 - 1500.0 | YES (Rename to `Diameter_nm`) |
| `Shape group` | Categorical | 9 | 0 | 'Spherical', 'spherical', 'Nanorods', etc. | YES (Normalize case) |
| `Geometric Surface Area (nm2)` | Numeric | N/A | 0 | 28.27 - 2.82e7 | YES |
| `Zeta (mV)` | Numeric | N/A | 0 | -57.9 - 64.3 | TARGET |

*(All other computational/atomic features are excluded as decided in STABILITY_SCHEMA.md)*

## Cytotoxicity Features (cytotoxicity_meta_analysis.xlsx)

| Feature | Type | Unique Values | Missing | Range/Categories | Use |
| ------- | ---- | ------------: | ------: | ---------------- | --- |
| `Material type` | Categorical | 12 | 0 | 'Al2O3', 'CuO', 'Fe2O3', etc. | YES |
| `Core size (nm)` | Numeric | N/A | 0 | 5.9 - 369.0 | YES |
| `Hydro size (nm)` | Numeric | N/A | 0 | 12.5 - 1457.0 | YES |
| `Surface charge (mV)` | Numeric | N/A | 0 | -47.6 - 42.8 | YES |
| `Surface area (m2/g)` | Numeric | N/A | 0 | 6.0 - 576.23 | YES |
| `Assay` | Categorical | 12 | 0 | 'MTT', 'LDH', 'CCK-8', etc. | YES |
| `Cell name` | Categorical | 16 | 0 | 'A549', 'BEAS-2B', 'HCMEC', etc. | YES |
| `Exposure time` | Numeric | N/A | 0 | 6 - 72 | YES |
| `Mass dose (ug/mL)` | Numeric | N/A | 0 | 0.0 - 1500.0 | YES |
| `Toxicity` | Categorical | 2 | 0 | 'Toxic', 'Nontoxic' | TARGET |
| `Pubmed ID` | Categorical | N/A | 0 | 21255821 - 24983896 | GROUPING ID |
| `Viability (%)` | Numeric | N/A | 0 | -1.43 - 350.9 | EXCLUDED (Leakage) |
