# NanoMedAI — Two-Week Real-Data Retraining: Scope Statement

**Date:** Day 1
**Status:** Locked for the two-week sprint. Anything not listed under "In scope" is deliberately excluded — see "Deferred to future work."

## Objective

Retrain NanoMedAI's existing colloidal-stability and biological-reactivity models on
real, published nanoparticle data in place of the current synthetic training set,
and ship the retrained model inside the existing NanoMedAI web app. If a suitable
public cytotoxicity dataset can be assembled within the first two days, add
cytotoxicity as a third predicted target under the same process.

## In scope

- Sourcing nanoparticle data from **already-downloadable public sources only**
  (open-access supplementary files, S2NANO, eNanoMapper). No dataset that requires
  emailing an author and waiting for a reply.
- Reusing NanoMedAI's existing 7-field schema (Material, Size, Shape, Coating,
  Temperature, pH, Ionic strength) without adding new input fields.
- Reusing the existing `train_and_export.py` retraining pipeline without
  architectural changes.
- Re-labeling Stability and Reactivity from whatever real, continuous measurements
  the sourced data provides (e.g. aggregation measurements, viability assays),
  with the threshold for each label documented and cited.
- A stretch target: **Cytotoxicity**, added the same way, only if a usable public
  dataset is in hand by the end of Day 3.
- Updating the app's Learn page to describe the real dataset(s) used, in place of
  the current synthetic-data disclosure.
- A short written report: data sources and limits, real-data accuracy vs. the old
  synthetic-data accuracy, and an explicit "next steps" section.

## Explicitly out of scope for this sprint (deferred to future work)

- Drug-release prediction and cellular-uptake prediction as modeled targets.
- Any new input feature (zeta potential, drug loading, exposure time, cell line).
- The multi-objective optimizer (NSGA-II / Bayesian optimization) — the existing
  brute-force Compare search stays as-is.
- Any dataset that requires a data-access request or author correspondence.
- A backend/server architecture — the app stays a single client-side HTML file.

These are not abandoned — they are the next phase of the 24-week roadmap this
sprint is a compressed first slice of, and the final report should say so
explicitly rather than imply the project is "done."

## Success criteria

1. `train_and_export.py` runs end-to-end on a real CSV and produces a working
   `nanomedai_real.html`.
2. Cross-validated balanced accuracy for Stability and Reactivity is reported and
   compared honestly against the synthetic-data baseline, whatever the result.
3. The published app reflects the real-data model, not the synthetic one, and its
   Learn page accurately describes what it was trained on.

## Day 1 checklist

- [x] Repo structure created (`data/raw`, `data/processed`, `notebooks`, `models`,
      `docs`, `app`)
- [x] This scope statement written
- [ ] Sanity check: confirm the existing pipeline (`train_and_export.py` +
      `nanomedai.html`) runs end-to-end on the current synthetic data, so Day 2
      starts from a known-working baseline
