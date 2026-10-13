# Blocker Verification

## 1. Synthetic Dataset

Status:
NOT FOUND

Evidence:
A full repository search including hidden files (`Get-ChildItem -Recurse -Force`) confirms there are no data files (`.csv`, `.json`, `.xlsx`, `.parquet`) present other than the empty template `docs/data-source-log.csv`. The `data/raw/` and `data/processed/` directories are completely empty. The dataset generator script or notebook is also missing. The only trace of the synthetic data is the pre-compiled `MODEL_DATA` JSON blob hardcoded into `app/nanomedai.html`.

Impact:
The original synthetic baseline cannot be reproduced or verified. The exact rules used to generate the synthetic labels are lost, meaning we cannot compare the synthetic data distribution to future real data.

## 2. Stability Definition

Current definition:
Defined qualitatively in `app/nanomedai.html` as whether particles "stay evenly spread out (stable) or clump together into larger clusters over time (unstable)."

Synthetic label-generation rule:
The exact mathematical rule is lost with the missing data generator, but the documentation (`nanomedai.html`) states it was generated based on heuristics: PEG protects against clumping; high salt reduces repulsion; pH near isoelectric point encourages clumping; heat speeds collisions.

Scientific basis:
Based loosely on DLVO theory heuristics, but entirely synthetic. It does not map to any single standardized experimental assay.

Real-world endpoint required:
Requires a quantifiable experimental measurement such as Zeta potential (mV), change in hydrodynamic diameter (DLS) over time, or aggregation index.

Status:
NEEDS RESEARCH

## 3. Reactivity Definition

Current definition:
Defined in `app/nanomedai.html` as "An illustrative estimate of how strongly a body's cells or immune system might respond to the particle." It is explicitly labeled as a "teaching signal only."

Synthetic label-generation rule:
The exact rule is lost, but based on: uncoated surfaces attract proteins; smaller particles are more reactive; ion-releasing materials (Ag, ZnO, CuO) are more reactive than inert ones (Au, SiO2).

Scientific basis:
A synthetic amalgamation of general toxicology heuristics. Not a scientifically standardized endpoint.

Real-world endpoint required:
Requires selecting a specific, measurable biological assay (e.g., Reactive Oxygen Species (ROS) generation, IC50, cell viability percentage via MTT assay).

Status:
NEEDS RESEARCH

## 4. Root Cause

The NanoMedAI project was built as an educational/demonstration tool using hardcoded heuristics to generate a "dummy CSV" (which was never checked into source control). Its target variables (`Stability` and `Reactivity`) were conceived as broad concepts for teaching rather than specific, measurable experimental endpoints. Moving to real data requires transforming these broad concepts into exact, measurable experimental proxies.

## 5. Recommended Scope Decision

The current Stability and Reactivity categorical targets (High/Medium/Low) should NOT be assumed as the final schema. Instead, we must research and adopt specific, measurable real-world endpoints (e.g., Zeta potential for stability, cell viability % for reactivity) and clearly define literature-backed thresholds to bin them into categories, or redefine the model as a regression problem. 

## 6. Next Safe Action

Conduct a literature review to determine the most common and standardized experimental endpoints for nanoparticle stability and biological reactivity (e.g., DLS/Zeta for stability; ROS/MTT for reactivity), and establish scientifically defensible thresholds for categorization before acquiring datasets.
