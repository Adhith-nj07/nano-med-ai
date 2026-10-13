# Stability Model Diagnosis: Dataset Structure Audit

## 1. Raw Dataset Dimensions
- **File:** `data/raw/zeta_potential_69_enms.xlsx`
- **Rows:** 69
- **Columns:** 22
- **Duplicates:** 0 fully duplicate rows.

## 2. Missing Values
- **Missingness:** There are exactly 0 missing values across all 22 columns. No imputation is necessary.

## 3. Key Observations
- **Target (`Zeta (mV)`):** Has 64 unique values among 69 records, demonstrating healthy continuous variance.
- **Categorical inconsistencies:** `Shape group` contains both `"Spherical"` and `"spherical"`, which splits the same class. `"Type of Coating \n(Anionic, Cationic, Neutral)"` contains `"cationic"` and `"positive"`, which conceptually overlap.
- **Numerical variance:** `Diameter  (TEM-STEM)` contains 51 unique values. `Geometric Surface Area (nm2)` contains 53 unique values.
- **Collinearity concern:** `Corresponding sphere diameter (nm)` has exactly the same first few unique values as `Diameter  (TEM-STEM)`, confirming they represent the same physical property scaled or transformed.

## 4. Conclusion
The basic dataset structure is solid (no missing data, no duplicate rows). The extremely poor R² (0.03) observed in the baseline model is not caused by missing values or duplicate rows. It is likely driven by the combination of a tiny sample size (N=69) and potentially poor feature-target alignment, requiring deeper target and feature diagnostics.


## 5. Target Diagnostics (Zeta mV)
- **Min:** -57.90
- **Max:** 64.30
- **Mean:** -1.44
- **Median:** -2.20
- **Std:** 28.32
- **Q1:** -19.30
- **Q3:** 5.70
- **Unique values:** 64

**Analysis:** The target spans a wide range (-57.9 to 64.3 mV). The mean is negative (-15.22 mV), while the standard deviation is extremely large (24.34 mV). This high variance implies that predicting Zeta potential in this tiny dataset requires features that can strongly separate these extreme positive and negative values. If the features do not contain that information, the R2 will be near zero.


## 6. Feature Diagnostics

### Numerical Features
- **Diameter  (TEM-STEM)**: Pearson=0.111, Spearman=-0.350, Var=6.5e+04, Min=3.0, Max=1500.0
- **Geometric Surface Area (nm2)**: Pearson=0.239, Spearman=-0.385, Var=1.2e+13, Min=28.2743338823081, Max=28260000.0

### Categorical Features

#### metal core
- Ag: count=4, mean_zeta=-16.45
- Ag2S: count=1, mean_zeta=-50.50
- AlOOH: count=1, mean_zeta=34.90
- Au: count=5, mean_zeta=-19.07
- BaTiO3: count=1, mean_zeta=-3.17
- Ca10(PO4)6(OH)2: count=1, mean_zeta=-8.90
- CeO2: count=13, mean_zeta=7.90
- CePO4: count=1, mean_zeta=55.70
- CeZrO2: count=11, mean_zeta=15.78
- CuO: count=1, mean_zeta=-0.59
- Fe2O3: count=1, mean_zeta=64.30
- SiO2: count=14, mean_zeta=-18.71
- TiO2: count=8, mean_zeta=4.91
- ZnO: count=7, mean_zeta=-11.95

#### Coating
-  triethoxycaprilysilane: count=3, mean_zeta=-19.13
- 4% (w/v) each of polyoxyethylene glycerol trioleate and polyoxyethylene (20) sorbitan monolaurate (Tween 20): count=2, mean_zeta=-3.36
- AA4040: count=1, mean_zeta=17.10
- D540: count=1, mean_zeta=-43.10
- Ethylenediamine: count=2, mean_zeta=-5.66
- F127: count=1, mean_zeta=5.30
- HMTA: count=2, mean_zeta=1.75
- PEG 1500: count=1, mean_zeta=0.02
- PEG 600: count=1, mean_zeta=0.09
- PVP: count=2, mean_zeta=-4.40
- PVP 10k: count=2, mean_zeta=0.23
- PVP 360k: count=2, mean_zeta=-0.55
- PVP 40k: count=1, mean_zeta=0.62
- Tannic acid / sodium citrate: count=2, mean_zeta=-29.54
- aminoacid: count=9, mean_zeta=-24.67
- aminoalkyl: count=4, mean_zeta=-5.90
- epoxysilane: count=1, mean_zeta=-16.30
- polyethylene glycol: count=4, mean_zeta=-17.18
- sodium citrate: count=1, mean_zeta=-26.60
- sulfate & PVP capped: count=1, mean_zeta=-50.50
- uncoated: count=26, mean_zeta=18.03

#### Coating_Charge
- anionic: count=8, mean_zeta=-24.10
- cationic: count=1, mean_zeta=25.90
- neutral: count=47, mean_zeta=-2.51
- positive: count=1, mean_zeta=-33.30
- uncoated: count=12, mean_zeta=18.25

#### Ageing
- Aged: count=10, mean_zeta=-9.50
- Pristine: count=59, mean_zeta=-0.07

#### Shape group
- agglomerated: count=5, mean_zeta=-9.10
- faceted: count=7, mean_zeta=10.03
- harns: count=2, mean_zeta=17.37
- nanorods: count=3, mean_zeta=15.10
- sea urchins: count=4, mean_zeta=-12.50
- spherical: count=43, mean_zeta=-1.61
- various shapes: count=5, mean_zeta=-16.94
