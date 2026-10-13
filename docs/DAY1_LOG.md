# Day 1 log

- Repo structure created: data/raw, data/processed, notebooks, models, docs, app.
- SCOPE.md written and checked in.
- Sanity check: ran train_and_export.py against a dummy CSV matching the target
  schema (Material, Size_nm, Shape, Temperature, pH, Salt, Coating, Stability,
  Reactivity, Source), regenerated nanomedai.html, and confirmed in a headless
  browser that Predict returns results with zero JavaScript errors.
  Result: PASS. The pipeline is proven end-to-end before any real data is loaded.
- Baseline synthetic-data accuracy to compare Day 7-8's real-data numbers against:
  see /docs/SCOPE.md success criteria.

## Next (Day 2)
Start sourcing real, immediately-downloadable data (no author-request datasets):
open-access supplementary files from the six papers, S2NANO, eNanoMapper.
Log every source in docs/data-source-log.csv as you go, not at the end of the day.
