# Feature registry and protected UI baseline

`src/feature_registry.py` is the capability inventory for the platform. The
versioned endpoint `GET /api/v1/features` reports each module's schemas,
datasets, model dependencies, API routes, compatible existing UI areas,
validation status, limitations, and availability.

Dataset provenance and current file-quality summaries are available through
`GET /api/v1/datasets` and `GET /api/v1/datasets/{dataset_id}`. A dataset detail
response includes upstream data sources, license notes, SHA-256, source DOI or
publication identifiers found in the active dataset, row and column counts,
missing values, numeric ranges, and grouped-record counts. Small row
previews are opt-in with `preview_rows` (maximum 10); the catalog list does not
include raw rows. For drug-release data, the response also counts records whose
measurement provenance is recorded as unknown.

`GET /api/v1/health` reports healthy or degraded service status based on the
dataset and model files needed by each currently implemented research workflow.
The legacy `/api/health` route remains available for existing clients.

`GET /api/v1/models` returns the model metadata and validation metrics already
used by the legacy model registry, plus artifact availability and SHA-256 for
serialized models. The release estimator is fitted from the versioned dataset
at runtime, so it is identified as a dataset-fitted pipeline rather than a
serialized model artifact.

Registry states describe implementation and evidence separately. In
particular, the working stability and cytotoxicity endpoints are `EXPERIMENTAL`
research prototypes. Drug release is a `RESEARCH MODULE` with domain limits.
No feature is marked `VALIDATED` by this registry. The demo page continues to
identify its built-in values as mock demonstration values.

## UI baseline

`tests/simulation_ui_baseline.json` versions the `demo/simulation-ui` reference.
It records SHA-256 digests for the markup, styles, interaction code, and demo
data, alongside the protected HTML IDs, classes, and interaction contracts.
`tests/test_simulation_ui_baseline.py` checks those contracts. A future UI
change should update the baseline only after an intentional visual and
functional comparison against the approved reference.

Run the focused checks with:

```text
python -m unittest tests.test_web_server tests.test_simulation_ui_baseline
```
