# NanoMedAI Master Data Dictionary & Data Schema Reference

## Overview
This document defines the schema, field descriptions, data types, physical units, constraints, and standardized null representation across all structured datasets curated for the NanoMedAI Dataset Curation Framework.

---

## Standardized Null & Missing Value Policy
- Missing or unreported numerical parameters are explicitly preserved as `NA`.
- No synthetic interpolation, default zero-filling, or silent model imputation has been performed.
- Ambiguous records or incomplete kinetic modeling parameters are flagged as `MANUAL_REVIEW`.

---

## Track 1: Zeta Potential Dataset Schema (`NanoMedAI_Zeta_Potential.csv`)

| Field Name | Data Type | Units | Example / Allowed Values | Description & Biophysical Relevance |
| :--- | :--- | :--- | :--- | :--- |
| `study_id` | String | N/A | `STU-001` to `STU-013` | Standardized unique study identifier matching the Study Registry. |
| `doi_pmid` | String | N/A | `10.1039/C3NR05381A` | Digital Object Identifier or PubMed ID for primary source traceability. |
| `formulation_id` | String | N/A | `CLS-NP-01` | Unique formulation identifier within the study. |
| `batch_id` | String | N/A | `BATCH-CLS-0` | Specific experimental batch code or preparation run. |
| `material` | String | N/A | `Poly(cholesteryl silicate) 0%` | Chemical identity of the primary particle core/matrix. |
| `core_size_method` | String | N/A | `49.3 nm (DLS)` | Primary core size and analytical method used for measurement. |
| `hydrodynamic_size_nm` | Float | nm | `49.3` | Intensity-weighted z-average hydrodynamic diameter measured via DLS. |
| `shape` | String | N/A | `Spherical` | Nanoparticle morphology confirmed via TEM/SEM imaging. |
| `coating` | String | N/A | `5% Chol-PEG`, `Chitosan/Alginate` | Surface coating, polymer layer, or surface functionalization moiety. |
| `surface_area` | Float / String | m²/g | `NA` | Specific surface area measured via BET N2 adsorption. |
| `medium` | String | N/A | `Distilled Water`, `PBS Buffer` | Dispersion liquid phase composition. |
| `buffer` | String | N/A | `PBS`, `Phosphate Buffer`, `None` | Chemical buffer species present in the dispersion medium. |
| `pH` | Float / String | pH units | `7.0`, `7.4`, `NA` | Measured pH of the dispersion medium during electrokinetic analysis. |
| `ionic_strength` | String | M or mM | `0.15 M`, `NA` | Calculated or reported ionic strength of the bulk dispersant. |
| `measurement_temp_c` | Float | °C | `25.0` | Cuvette temperature maintained during zeta potential measurement. |
| `measurement_method` | String | N/A | `DLS / ELS` | Electrophoretic Light Scattering or Laser Doppler Electrophoresis. |
| `instrument` | String | N/A | `Zetasizer Nano ZS90` | Make and model of analytical instrumentation. |
| `replicates` | String | N/A | `n=3`, `NA` | Number of independent experimental replicates. |
| `uncertainty_mv` | String | mV | `±0.9` | Reported standard deviation or confidence interval for zeta potential. |
| `measured_zeta_potential_mv` | Float | mV | `-21.4`, `+12.4` | Electrokinetic potential at the slipping plane. |
| `source_location` | String | N/A | `PMC3940272 / Table 1` | Direct citation location (table/figure/paragraph) in primary paper. |
| `provenance` | String | N/A | `Experimental` | Data generation origin (`Experimental`, `Graph-Digitized`). |
| `data_flag` | String | N/A | `raw_table`, `graph_digitized` | Curation flag indicating extraction fidelity and review status. |
| `verification_status` | String | N/A | `Verified`, `Flagged` | Audit verification result following cross-source validation. |

---

## Track 2: Cytotoxicity Dataset Schema (`NanoMedAI_Cytotoxicity.csv`)

| Field Name | Data Type | Units | Example / Allowed Values | Description & Biophysical Relevance |
| :--- | :--- | :--- | :--- | :--- |
| `study_id` | String | N/A | `STU-001` | Standardized unique study identifier. |
| `doi_pmid` | String | N/A | `10.1039/C3NR05381A` | Digital Object Identifier or PubMed ID. |
| `formulation_id` | String | N/A | `PHBHHX-SYS-1` | Unique formulation identifier. |
| `batch_id` | String | N/A | `BATCH-PHB-01` | Specific experimental batch code. |
| `material` | String | N/A | `PHBHHx System 1` | Core material composition. |
| `particle_size_nm` | Float / String | nm | `120.5`, `NA` | Mean hydrodynamic particle size. |
| `coating` | String | N/A | `Octadecylamine (High)` | Surface coating or modifying agent. |
| `surface_charge_mv` | Float / String | mV | `-30.0`, `+40.0` | Zeta potential / surface charge metric. |
| `surface_area` | Float / String | m²/g | `NA` | Specific surface area metric. |
| `cell_line` | String | N/A | `L929 Fibroblasts`, `A549` | Biological cell lineage evaluated in cytotoxicity assay. |
| `assay` | String | N/A | `MTT Assay`, `Cell Viability` | Colorimetric or fluorometric cell viability assay protocol. |
| `dose` | String | N/A | `100 ug/mL`, `IC50 ~ 50 ug/mL` | Applied nanoparticle exposure concentration/dose. |
| `exposure_duration_h` | Float | Hours | `24.0`, `48.0` | Duration of nanoparticle incubation prior to viability measurement. |
| `controls` | String | N/A | `Untreated Cells`, `Free Drug` | Negative and positive control systems utilized. |
| `replicates` | String | N/A | `n=3`, `NA` | Experimental sample replicate count. |
| `measured_cell_viability_pct` | Float | % | `88.5`, `18.3` | Quantitative percentage of viable cells relative to negative control. |
| `uncertainty_pct` | String | % | `±3.2` | Reported uncertainty/standard deviation for cell viability. |
| `original_toxicity_label` | String | N/A | `Non-cytotoxic (>85%)` | Original author qualitative classification or threshold definition. |
| `source_location` | String | N/A | `PMC6496505 / Figure 3` | Source table or figure reference. |
| `provenance` | String | N/A | `Experimental` | Data generation methodology. |
| `data_flag` | String | N/A | `raw_table`, `graph_digitized` | Data review classification. |
| `verification_status` | String | N/A | `Verified` | Data verification audit status. |

---

## Track 3: S5 Physical Stability Dataset Schema (`NanoMedAI_S5_Physical_Stability.csv`)

| Field Name | Data Type | Units | Example / Allowed Values | Description & Biophysical Relevance |
| :--- | :--- | :--- | :--- | :--- |
| `study_id` | String | N/A | `STU-006` | Standardized unique study identifier. |
| `doi_pmid` | String | N/A | `10.3390/pharmaceutics` | Digital Object Identifier or PubMed ID. |
| `formulation_id` | String | N/A | `LPNP-TS-DOX-01` | Unique formulation code. |
| `batch_id` | String | N/A | `BATCH-LPNP-01` | Specific experimental batch code. |
| `pharmaceutical_nanocarrier`| String | N/A | `LPNP-TS-DOX Hybrid NP` | Full carrier system descriptor. |
| `encapsulated_drug` | String | N/A | `Doxorubicin`, `Unloaded` | Encapsulated therapeutic active pharmaceutical ingredient. |
| `composition` | String | N/A | `Lipid-TPGS / PLGA` | Complete chemical formulation composition. |
| `storage_conditions` | String | N/A | `4 °C, PBS Buffer, pH 7.4` | Controlled storage temperature and environmental medium. |
| `storage_temp_c` | Float | °C | `4.0`, `37.0` | Environmental storage temperature maintained over time. |
| `measurement_temp_c` | Float | °C | `25.0` | Controlled cuvette temperature during DLS measurement. |
| `dispersion_medium` | String | N/A | `PBS Buffer`, `Hydrogel` | Bulk medium in which particles were stored. |
| `pH` | Float | pH units | `7.0`, `7.4` | Hydrogen ion concentration of storage dispersion medium. |
| `measurement_method` | String | N/A | `DLS / ELS` | Analytical technique used for particle size & zeta tracking. |
| `time_point_days` | Float | Days | `0.0`, `7.0`, `30.0` | Elapsed time from study initiation to measurement point. |
| `mean_particle_size_nm` | Float | nm | `150.0`, `156.0` | Intensity-weighted hydrodynamic particle diameter. |
| `polydispersity_index_pdi` | Float | Dimensionless | `0.250`, `0.264` | Measure of particle size distribution width (monodispersity). |
| `zeta_potential_mv` | Float | mV | `-20.0`, `-18.5` | Surface electrokinetic potential measured at sampling point. |
| `uncertainty` | String | N/A | `NA`, `±1.2` | Reported measurement uncertainty. |
| `replicates` | String | N/A | `n=3` | Sample replicate count. |
| `trajectory_eligibility_status`| String | N/A | `Valid (>=3 Time Points)` | Compliance status with minimum 3 time-point trajectory requirement. |
| `source_location` | String | N/A | `MDPI / Figure 4` | Direct location in publication. |
| `provenance` | String | N/A | `Experimental` | Data provenance. |
| `data_flag` | String | N/A | `raw_table` | Data extraction flag. |

---

## Track 4: Drug Release Dataset Schema (`NanoMedAI_Drug_Release.csv`)

| Field Name | Data Type | Units | Example / Allowed Values | Description & Biophysical Relevance |
| :--- | :--- | :--- | :--- | :--- |
| `study_id` | String | N/A | `STU-004` | Standardized unique study identifier. |
| `doi_pmid` | String | N/A | `10.2147/IJN.S125431` | Digital Object Identifier or PubMed ID. |
| `formulation_id` | String | N/A | `PLGA-CHI-ALG-3` | Unique formulation identifier. |
| `batch_id` | String | N/A | `BATCH-PLGA-LBL-3` | Specific experimental batch code. |
| `carrier` | String | N/A | `PLGA (CHI/ALG)3 NP` | Nanoparticle or matrix carrier system. |
| `drug` | String | N/A | `Doxorubicin` | Active drug molecule released into medium. |
| `drug_loading_pct` | Float | % | `8.5`, `12.4` | Encapsulated drug mass percentage relative to carrier mass. |
| `particle_size_nm` | Float / String | nm | `189.6`, `NA` | Initial mean hydrodynamic particle size before dissolution. |
| `pdi` | Float / String | Dimensionless | `NA` | Polydispersity index of carrier particles. |
| `zeta_potential_mv` | Float / String | mV | `-48.0`, `NA` | Initial zeta potential of carrier particles. |
| `release_medium` | String | N/A | `Isotonic PBS` | Aqueous or buffered release medium composition. |
| `medium_ph` | Float | pH units | `7.4`, `5.0` | pH of release medium (e.g. physiological vs endosomal). |
| `temperature_c` | Float | °C | `37.0` | Dissolution incubator temperature. |
| `assay` | String | N/A | `UV-Vis Spectroscopy` | Quantification assay method (HPLC, UV-Vis, Fluorescence). |
| `sampling_time_h` | Float | Hours | `1.0`, `4.0`, `24.0` | Elapsed dissolution time at sampling point. |
| `cumulative_release_pct`| Float | % | `8.2`, `54.8`, `92.0` | Total cumulative mass percentage of drug liberated into medium. |
| `uncertainty_pct` | String | % | `±0.8`, `±3.1` | Standard deviation for cumulative release percentage. |
| `korsmeyer_peppas_n` | Float / String | Dimensionless | `0.42`, `0.61`, `NA` | Korsmeyer-Peppas release exponent indicating transport mechanism. |
| `korsmeyer_peppas_k` | Float / String | h^-n | `0.082`, `0.184`, `NA` | Kinetic release rate constant. |
| `model_fit_r2` | Float / String | Dimensionless | `0.9850`, `0.9910`, `NA` | Coefficient of determination for non-linear kinetic model fit. |
| `source_location` | String | N/A | `PMC5344431 / Figure 5` | Direct location in publication. |
| `provenance` | String | N/A | `Experimental` | Data generation methodology. |
| `data_flag` | String | N/A | `raw_table`, `MANUAL_REVIEW` | Review flag (`MANUAL_REVIEW` if missing k/n values in source). |

---

## Study Registry Schema (`NanoMedAI_Study_Registry.csv`)

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `study_id` | String | Standardized unique study identifier (`STU-001` to `STU-099`). |
| `doi_pmid` | String | DOI or PubMed identifier. |
| `publication_year` | Integer | Year of primary publication. |
| `formulation_batch_id` | String | Primary formulation or batch code analyzed. |
| `primary_source_title` | String | Journal name / title descriptor of primary source literature. |
| `inclusion_decision` | String | Curation outcome (`Included` or `Excluded`). |
| `exclusion_inclusion_justification` | String | Detailed rationale for literature inclusion or exclusion. |

---

## Trajectory Audit Schema (`NanoMedAI_Trajectory_Audit.csv`)

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `study_id` | String | Standardized unique study identifier. |
| `formulation_id` | String | Formulation code evaluated for longitudinal tracking. |
| `storage_temp_c` | Float | Storage temperature (°C). |
| `medium_environment` | String | Storage environment/dispersion medium. |
| `total_time_points` | Integer | Total number of actual time-point measurements recorded ($n$). |
| `time_range_span` | String | Full temporal duration of stability monitoring. |
| `trajectory_eligibility_status` | String | Evaluation result (`Eligible (>=3 Points)` or `Ineligible (<3 Points)`). |
| `primary_reason_for_ineligibility` | String | Explanatory notes if rejected for machine learning trajectory modeling. |
