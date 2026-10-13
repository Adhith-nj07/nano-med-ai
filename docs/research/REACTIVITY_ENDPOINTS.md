# Reactivity Endpoints

## Candidate Experimental Endpoints

| Endpoint | What it measures | Typical experimental method | Quantitative? | Public datasets available? | Suitable as ML target? |
| -------- | ---------------- | --------------------------- | ------------- | -------------------------- | ---------------------- |
| Cell viability | Percentage of living cells post-exposure | MTT, WST-1, Alamar Blue assays | YES (% control) | HIGH | YES |
| IC50 / LC50 | Concentration required to kill 50% of cells | Dose-response viability assays | YES (µg/mL) | HIGH | YES |
| ROS generation | Reactive Oxygen Species production (oxidative stress) | DCFDA assay | YES (Fluorescence) | LOW | NO (Insufficient data scale) |

## Literature Context

### 1. Why "Reactivity" is Problematic
"Reactivity" in nanoparticle literature can refer to surface chemical reactivity, catalytic activity, or biological response. The existing NanoMedAI prototype used it as a proxy for "how strongly a body's cells or immune system might respond." In nanoinformatics literature, this broad concept does not exist as a single target. It is almost universally replaced by **Cytotoxicity**.

### 2. Cell Viability (% Control)
- **Method/Units:** Often measured via MTT assay; reported as a percentage of viable cells compared to an unexposed control.
- **Thresholds:** A common literature threshold for categorical ML models is classifying viability < 50% as "Toxic" and > 50% as "Non-Toxic" (equivalent to the IC50 point). Sometimes a three-tier system is used (e.g., >80% = Low Toxicity, 50-80% = Moderate, <50% = High Toxicity).
- **Limitations:** Viability is deeply dependent on the specific cell line used (e.g., A549 lung cells vs. HepG2 liver cells), the exposure time (e.g., 24h vs. 48h), and the nanoparticle concentration (dose). An ML model predicting viability MUST include Dose, Exposure Time, and Cell Line as input features.

### 3. IC50
- **Method/Units:** The interpolated concentration (e.g., µg/mL) where cell viability drops to 50%. 
- **Application for ML:** Excellent continuous regression target, but requires that the dataset curated it explicitly, rather than just providing single-dose viability scores.

## Conclusion
The vague concept of "Reactivity" must be formally abandoned and replaced with **Cytotoxicity**. Cell viability (% of control) or binary toxicity (Toxic vs. Non-Toxic based on a 50% or 80% viability threshold) are the most defensible and data-rich endpoints.
