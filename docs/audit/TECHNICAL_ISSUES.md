# Technical Issues

| ID | File | Location | Issue | Severity | Evidence | Fix |
|---|---|---|---|---|---|---|
| T-001 | Repository | `data/raw/` | Missing synthetic dataset (dummy CSV). | CRITICAL | `DAY1_LOG.md` mentions running a "dummy CSV", but `data/raw/` is empty. | Locate the original dummy CSV, or construct a synthetic one matching `MODEL_DATA` ranges to allow baseline verification. |
| T-002 | `train_and_export.py` | Line 92-97 | Brittle HTML modification. | MEDIUM | Script uses string matching on `const MODEL_DATA =` to inject JSON. | Use a templating engine (like Jinja2) or externalize `MODEL_DATA.js` to avoid breaking HTML. |
| T-003 | `train_and_export.py` | Line 46 | Missing value handling. | LOW | Uses `dropna(subset=FEATURE_ORDER + TARGETS)`. | Document that rows with any missing required features are discarded, which could drastically reduce real-data sample size. |
| T-004 | `train_and_export.py` | Line 58 | Random state in KFold. | LOW | `KFold(n_splits=5, shuffle=True, random_state=0)`. | GroupKFold does not shuffle by default in older scikit-learn versions, ensure reproducibility across runs if grouping is used. |
