# Target Definition Review

This document summarizes the transition from NanoMedAI's original synthetic targets ("Stability" and "Reactivity") to scientifically defensible, experimentally measurable endpoints.

## 1. The Synthetic Problem

The Day-1 audit revealed that:
- **Stability** was defined as a heuristic rule of thumb (e.g., PEG prevents clumping; high salt causes clumping).
- **Reactivity** was defined as a teaching signal for general biological/immune response.
- Neither target corresponded to a specific, standardized experimental assay with quantitative thresholds. 

## 2. Research Objective

To train on real data, these broad concepts must be replaced with exact experimental measurements. The research phase investigated:
1. Which physical assays actually measure colloidal stability (e.g., Zeta potential, DLS size change).
2. Which biological assays actually measure reactivity/toxicity (e.g., Cell viability, ROS generation).
3. Which of these assays have sufficient representation in public machine-learning datasets (e.g., S2NANO, eNanoMapper, Zenodo) to support a 14-day modeling sprint.

## 3. Key Findings

- **Stability:** While Zeta potential is widely reported, the traditional "±30 mV" threshold for stability fails for sterically stabilized (e.g., PEGylated) nanoparticles. A more robust endpoint is the change in hydrodynamic diameter over time, though large-scale time-series datasets are rare. Predicting Zeta potential as a continuous regression variable is the most data-supported approach.
- **Reactivity:** "Reactivity" is too vague for literature curation. The overwhelming majority of nanoinformatics datasets measure **Cytotoxicity** via cell viability assays (e.g., MTT/WST-1) or IC50 values. Cytotoxicity is a distinct and highly standardized endpoint that should entirely replace the "Reactivity" concept.

Detailed analyses are provided in `STABILITY_ENDPOINTS.md`, `REACTIVITY_ENDPOINTS.md`, and `DATASET_AVAILABILITY.md`. The final decision is documented in `TARGET_SELECTION_RECOMMENDATION.md`.
