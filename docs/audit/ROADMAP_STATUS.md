# Roadmap Status

| Roadmap Item | Status | Evidence | Remaining Work | Priority |
|---|---|---|---|---|
| Repository setup | DONE | `app/`, `data/`, `docs/`, `models/`, `notebooks/` directories exist | None | |
| Synthetic baseline | BLOCKED | `train_and_export.py` exists, but `data/raw/` is empty | Locate and commit dummy CSV | HIGH |
| Stability model | BLOCKED | `MODEL_DATA` exists in HTML, but no thresholds for real data | Define scientific thresholds | HIGH |
| Reactivity model | BLOCKED | `MODEL_DATA` exists in HTML, but no thresholds for real data | Define scientific thresholds | HIGH |
| Source-aware validation | DONE | `GroupKFold` implemented in `train_and_export.py` | Ensure real data has `Source` | HIGH |
| Public data acquisition | NOT STARTED | `data-source-log.csv` is empty | Search databases once targets defined | HIGH |
| Data harmonization | NOT STARTED | | Schema mapping and transformations | HIGH |
| Real Stability model | NOT STARTED | | Train on processed real data | MEDIUM |
| Real Reactivity model | NOT STARTED | | Train on processed real data | MEDIUM |
| Cytotoxicity | NOT STARTED | | Assess feasibility during data search | LOW |
| UI integration | PARTIAL | `nanomedai.html` is built but uses synthetic data | Update to real data model | MEDIUM |
| Documentation | PARTIAL | `SCOPE.md` and `DAY1_LOG.md` created | Update Learn page with real info | MEDIUM |
| Final validation | NOT STARTED | | Technical and scientific checks | MEDIUM |
| Drug-release model | OUT OF SCOPE | Documented in `SCOPE.md` | None | |
| Cellular uptake model | OUT OF SCOPE | Documented in `SCOPE.md` | None | |
| NSGA-II optimizer | OUT OF SCOPE | Documented in `SCOPE.md` | None | |
| Bayesian optimizer | OUT OF SCOPE | Documented in `SCOPE.md` | None | |
