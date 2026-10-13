# Public Data Collection and Curation

Collected/staged: 2026-10-10. This is a source inventory and candidate-data bundle, not a model-training run. Raw downloaded workbooks remain unchanged in `data/raw/`; the collection script recreates the candidate CSV exports and QC JSON.

## Candidate data in this project

| Endpoint | Candidate data | Count | Conditions / provenance | Status |
|---|---|---:|---|---|
| Zeta potential | 198 ENMs in Millipore water + 90 gold nanoparticles in PBS | 288 records | Medium is retained; individual paper DOI and source dataset are retained. CC-BY 4.0 is recorded in the project source log. | Curated candidate. Do not collapse the two media into an unconditioned endpoint. |
| Zeta potential | NanoMILE-derived 69 ENMs | 69 records | CC-BY 4.0 Zenodo dataset; descriptors include material/coating, coating charge class, ageing, TEM/STEM size, shape, surface area, and zeta potential. | Separate candidate; do not deduplicate/merge against the 288 records without formulation-level identity review. |
| Cytotoxicity | S2NANO MeOx IIIB subset | 666 measurements / 17 PubMed study IDs | Includes material, sizes, charge, surface area, assay, cell line, exposure time, dose, viability, source toxicity label, PubMed ID. | Candidate only. Confirm exact Zenodo Rights field before redistribution. Group evaluation by PubMed ID. |
| Drug release | Bannigan et al. PLGA/PLA subset | 115 timepoints / 9 formulation trajectories / 1 study | Letrozole and paclitaxel; time 0–723.75 h; release 0–90.11%. | Exploratory kinetic fitting only; too few trajectories and only one study for a general model. |

## Prepared files

- `data/processed/public_data_candidates/zeta_potential_288_candidate.csv`
- `data/processed/public_data_candidates/zeta_potential_69_candidate.csv`
- `data/processed/public_data_candidates/cytotoxicity_meox_iiib_candidate.csv`
- `data/processed/public_data_candidates/drug_release_115_candidate.csv`
- `data/processed/public_data_candidates/collection_quality_summary.json`
- Rebuild with `scripts/collect_public_candidates.py`.

The exports preserve source values and source labels. The cytotoxicity export preserves both continuous viability and the source-derived toxicity class; it does not clip out-of-range control-relative viability values or re-label any samples. Study identifiers are provenance/grouping fields, never model predictors.

## Quality findings and limits

- The zeta 288 table has 288 rows, no exact duplicate rows, no missing values in its selected fields, and two distinct conditions: 198 Millipore-water observations and 90 PBS pH 7.4 observations. Split by study/formulation, and report condition-specific performance.
- The zeta 69 table has 69 rows, no exact duplicates or missing values in its selected fields, and measured zeta spans −57.9 to 64.3 mV. Dataset listing and licensing are documented at [Zenodo DOI 10.5281/zenodo.14864383](https://zenodo.org/records/14864383).
- MeOx IIIB has 666 rows and 17 distinct PubMed IDs in the local subset (not 216 IDs). It contains 487 Nontoxic and 179 Toxic labels. The source classes agree with the 50% viability rule for all 666 rows. 101 viability values are outside 0–100; preserve them as reported until source semantics are checked instead of clipping. The dataset record describes the broader package as compiled from studies and defines Toxic/Nontoxic using a 50% viability threshold. See [Zenodo DOI 10.5281/zenodo.15300193](https://zenodo.org/records/15300193).
- The release table has 115 observations, 9 formulations/trajectories, and one source study. Several environmental/formulation fields are wholly missing (hydrodynamic size, PDI, zeta, encapsulation efficiency, temperature, pH, ionic strength, surfactant percentage). Treat it as a limited kinetic pilot. The Zenodo data DOI is `10.5281/zenodo.7309020`; the prior dataset card contained an incorrect final digit and has been corrected. Nature Communications identifies the dataset as available in Zenodo [10.5281/zenodo.7309020](https://zenodo.org/records/7309141).
- Longitudinal physical-stability data remains unavailable: `data/processed/nanoparticle_physical_stability_longitudinal.csv` contains 0 records. The user-supplied stability track has records, but the prior reconciliation quarantines some for mismatched conditions and unresolved sources. It is not included here.
- The separate 494-row cytotoxicity workbook remains on hold because its first sheet lacks study-group IDs and the second sheet is not a clean observation table.

## Training decision

These collected files are ready for the next curation/validation stage, not for claiming a reliable general model. Before training:

1. Verify the exact license field on the MeOx IIIB Zenodo record and retain attribution/conditions.
2. For cytotoxicity, parse dose and time units, check study-level provenance and duplicates across alternative datasets, then use grouped validation by PubMed ID. Report continuous viability and binary labels as distinct endpoints.
3. For zeta potential, use the 288 water/PBS dataset as an explicitly conditioned target; compare study-grouped holdouts. Keep the 69-row dataset external until identities and overlap are checked.
4. For drug release, keep each complete trajectory in one split; the 9-trajectory one-study dataset only supports exploratory curve fitting.
5. Do not train a longitudinal physical-stability model until verified repeated measurements with explicit medium, temperature, time, size/PDI/aggregation, and study/formulation IDs are collected.

## Source references

- Zeta potential 69 ENMs: [Zenodo 10.5281/zenodo.14864383](https://zenodo.org/records/14864383), CC-BY 4.0 stated on the record.
- Zeta potential 198 water / 90 PBS: records 10.5281/zenodo.14866284 and 10.5281/zenodo.14866297; the project's `docs/data-source-log.csv` records CC-BY 4.0.
- MeOx IIIB: [Zenodo 10.5281/zenodo.15300193](https://zenodo.org/records/15300193); record text confirms data content and open access, but verify the per-record license before redistributing.
- Drug release source: [Bannigan et al., Nature Communications](https://www.nature.com/articles/s41467-022-35343-w), Zenodo data collection DOI 10.5281/zenodo.7309020.
