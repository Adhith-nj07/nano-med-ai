# NanoMedAI Target Selection Recommendation

## Current Problem
The existing NanoMedAI targets ("Stability" and "Reactivity") are synthetic, heuristic-based educational concepts that do not correspond to standardized experimental measurements. Real-world nanoparticle data cannot be mapped to these labels without making scientifically invalid assumptions.

## Stability

### Candidate endpoints
- Zeta potential (mV)
- Hydrodynamic diameter change (DLS, nm)
- Polydispersity Index (PDI)

### Recommended endpoint
Zeta potential (Continuous / Regression)

### Scientific justification
Zeta potential is the most widely reported quantitative measure of electrostatic colloidal stability. While it is not a perfect proxy for sterically stabilized particles (where a near-zero zeta potential can still be stable), treating it as a continuous regression target avoids the flaw of imposing an arbitrary categorical threshold (like ±30 mV) on a heterogeneous dataset.

### Dataset availability
High. Curated nanoinformatics datasets (e.g., S2NANO/Zenodo Metal Oxide datasets) consistently report zeta potential alongside core physical features.

### Remaining uncertainty
Whether the NanoMedAI UI can be gracefully updated from a categorical classification output (High/Medium/Low) to a continuous regression output (mV) without massive architectural changes.

## Reactivity

### Candidate endpoints
- Cell viability (% control)
- IC50 / LC50 (µg/mL)
- ROS generation

### Recommended endpoint
Cytotoxicity (Binary: Toxic / Non-Toxic) derived from Cell Viability.

### Scientific justification
"Reactivity" as a broad concept does not exist in nanoinformatics databases. The standard measurable endpoint for biological response is cytotoxicity, typically measured via cell viability assays (e.g., MTT). Using a literature-standard threshold (e.g., viability < 50% = Toxic) allows for robust, scientifically defensible classification that aligns exactly with how computational nanotoxicology research is conducted.

### Dataset availability
Excellent. Extensive, curated, machine-learning-ready datasets exist (e.g., Kaggle ToxicityAssessment_MeOxNP, Zenodo structured nanotoxicity datasets) that map physicochemical properties and exposure conditions to cell viability outcomes.

### Remaining uncertainty
Predicting cytotoxicity requires input features that describe the biological assay (e.g., Cell Line, Exposure Time, Dose). This necessitates fundamentally changing the NanoMedAI input feature schema.

## Proposed Revised ML Targets

1. Zeta Potential (Regression, in mV)
2. Cytotoxicity (Classification, Toxic / Non-Toxic based on cell viability thresholds)

## Proposed Feature Schema

| Feature | Source | Type | Required |
|---|---|---|---|
| Core Material | Physical Property | Categorical | YES |
| Core Size (nm) | Physical Property | Numeric | YES |
| Surface Coating | Physical Property | Categorical | YES |
| Cell Line | Assay Condition | Categorical | YES (for Cytotoxicity) |
| Exposure Time (h) | Assay Condition | Numeric | YES (for Cytotoxicity) |
| Dose/Concentration | Assay Condition | Numeric | YES (for Cytotoxicity) |
| Source | Dataset Metadata | Group | YES |

*(Note: pH, Temperature, and Salt from the original schema are rarely varied systematically in standard in vitro cytotoxicity datasets, which typically use standard physiological conditions like pH 7.4 and 37°C in cell culture media.)*

## Decision

CONDITIONAL GO

## Reason

Scientifically valid experimental endpoints (Zeta Potential and Cytotoxicity) and their corresponding open-access public datasets are readily available. However, integrating this data requires changing the ML problem definition (from arbitrary classification to regression/classification) and significantly altering the input feature schema to include biological assay conditions (Dose, Exposure Time, Cell Line) while likely dropping physiological constants (pH, Temp, Salt). Implementation can proceed ONLY IF modifying the application schema and UI to support these scientifically necessary changes is approved.
