# Next Actions

## P0 — Blocking

These must be resolved before real-data training.

1. Restore or recreate the synthetic dummy CSV to verify the baseline pipeline.
2. Define exact, literature-backed quantitative thresholds for Stability and Reactivity categories.
3. Clarify feature definitions (e.g., Core vs. Hydrodynamic Size).

## P1 — Critical

These should be completed during Days 1–8.

1. Acquire real dataset from public sources (eNanoMapper, S2NANO) matching the newly defined thresholds.
2. Harmonize dataset (map columns, apply thresholds, filter invalid rows).
3. Train real models using `train_and_export.py`.
4. Document the real-world dataset in the UI Learn page.

## P2 — Important

These should be completed during Days 9–14.

1. Update `MODEL_DATA` in `nanomedai.html` with real model output.
2. Perform technical and scientific sanity checks.
3. Write the final research report comparing real vs synthetic data.

## P3 — Future Work

Not part of the 14-day implementation.

1. Drug-release prediction
2. Cellular uptake prediction
3. NSGA-II optimizer
4. Bayesian optimizer
5. Experimental validation

## Day-by-Day Action Plan

| Day | Task | Deliverable | Dependency | Status |
|---|---|---|---|---|
| 1 | Repository audit | Audit files | None | DONE |
| 2 | Blocker resolution | Thresholds defined, baseline verified | Audit | NOT STARTED |
| 3 | Dataset discovery & feasibility | Feasibility decision, Dataset inventory | Blocker resolution | NOT STARTED |
| 4 | Schema | Final schema | Data feasibility | NOT STARTED |
| 5 | Cleaning | Processed dataset | Schema | NOT STARTED |
| 6 | Labeling | Label specification | Literature/data | NOT STARTED |
| 7 | Training | Real models | Processed data | NOT STARTED |
| 8 | Evaluation | Metrics | Models | NOT STARTED |
| 9 | Buffer/tuning | Improved model if needed | Evaluation | NOT STARTED |
| 10 | Integration | Real MODEL_DATA | Models | NOT STARTED |
| 11 | UI/docs | Updated application | Integration | NOT STARTED |
| 12 | Validation | Validation report | Application | NOT STARTED |
| 13 | Report | Research report | Results | NOT STARTED |
| 14 | Final audit | Release-ready repository | Everything | NOT STARTED |
