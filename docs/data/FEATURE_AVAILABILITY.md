# Feature Availability Analysis

## Status: COMPLETE

The following table summarizes the availability of key features across the two selected datasets (`zeta_potential_69_enms.xlsx` for Stability, `cytotoxicity_meta_analysis.xlsx` for Cytotoxicity).

| Feature | Stability | Cytotoxicity | Unit | Data Type | Missingness | Use |
| --- | --- | --- | --- | --- | --- | --- |
| Material | `metal core` | `Material type` | N/A | Categorical | 0 | YES |
| Core Size | `Diameter (TEM-STEM)` | `Core size (nm)` | nm | Numeric | 0 | YES |
| Hydrodynamic Size | N/A | `Hydro size (nm)` | nm | Numeric | 0 | YES (Cytotoxicity only) |
| Surface Coating | `Coating` | N/A | N/A | Categorical | 0 | YES (Stability only) |
| Shape | `Shape group` | N/A | N/A | Categorical | 0 | YES (Stability only) |
| Zeta Potential | TARGET | `Surface charge (mV)` | mV | Numeric | 0 | YES (Input for Cytotox) |
| Cell Line | N/A | `Cell name` | N/A | Categorical | 0 | YES (Cytotoxicity only) |
| Dose | N/A | `Mass dose (ug/mL)`| ug/mL | Numeric | 0 | YES (Cytotoxicity only) |
| Exposure Time | N/A | `Exposure time` | hours | Numeric | 0 | YES (Cytotoxicity only) |
| Assay Type | N/A | `Assay` | N/A | Categorical | 0 | YES (Cytotoxicity only) |
| pH / Salt / Temp | N/A | N/A | N/A | N/A | N/A | EXCLUDED |

*(Note: The original synthetic features pH, Salt, and Temperature do not exist in these curated datasets and must be removed from the UI.)*
