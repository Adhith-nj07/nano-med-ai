# User-Downloaded NanoMedAI Data Reconciliation

Reviewed: 2026-10-10. The original downloads are preserved without edits under
`data/raw/user_submitted_20261010/`. Reviewed companion files are under
`data/processed/user_submission_reviewed/`.

## Reconciled inventory

| Track/file | CSV rows | Unique study IDs | Readiness |
|---|---:|---:|---|
| Zeta potential | 12 | 6 | Candidate only; corrected DOI metadata supplied, most values still need row-level checking |
| Cytotoxicity | 11 | 4 | Candidate only; one source unresolved and one dose category corrected from the primary abstract |
| Physical stability | 20 | 5 | Four reported trajectories meet the point-count rule; source verification and study-level validation still needed |
| Drug release | 19 | 4 | Candidate only; sparse curves, two manual-review records, and source/value conflicts |
| **Total across four track CSVs** | **62** | **13** | Not a training-ready dataset |

The extraction audit's per-track row counts (12, 11, 20, 19) sum to 62, not
the reported 142 observations. Its “14 studies” wording comprises 13 included
IDs (`STU-001`–`STU-013`) plus the excluded `STU-099`; `STU-014` appears only
in the trajectory audit and is now recorded as an unresolved hold in the
reviewed registry. The trajectory audit also labels the `STU-004` drug-release
curve as a stability trajectory; it is excluded from the physical-stability
trajectory count.

## Source corrections and verification

The reviewed registry adds `reviewed_doi`, `reviewed_title`, and
`review_status`; it preserves every submitted identifier in `doi_pmid`.

| Study | Submitted source | Reviewed source / disposition |
|---|---|---|
| STU-001 | `10.1039/C3NR05381A` | Correct DOI: `10.1039/c3nr05961h`. Zeta values/sizes match primary Table 1. Cytotoxicity values match Figure 3 after correcting assay to MTS and dose to 5 µM wortmannin. |
| STU-002 | `10.1002/term.2890` | Correct DOI: `10.1111/cpr.12192`. Source identity confirmed; individual values remain to be checked. |
| STU-003 | `PMC12655768`, a review/editorial | Underlying primary experiment identified: De Capua et al., `10.3390/pharmaceutics16081010` (PMC11360396). The 137 nm and −30 mV values match its Table 1. Reviewed zeta copy points to this primary source. |
| STU-004 | `10.2147/IJN.S125431` | Correct DOI: `10.2147/IJN.S130404`. Source identity confirmed; individual values remain to be checked. |
| STU-005 | `10.3390/pharmaceutics` | Correct paper DOI: `10.3389/fonc.2026.1905253`. The paper abstract reports about 80% release by 24 h, while the submitted curve says 22.4% at 24 h. The submitted release rows remain on hold until the curve/formulation is reconciled. The 257.6 nm and −15.3 mV summary values agree with the abstract. |
| STU-006 | `10.3390/pharmaceutics14112394` | DOI confirmed. The submitted physical-stability series claims storage at 4 °C for 30 days; the cited paper's Figure 4 describes measurements in PBS/RPMI/MEM up to 24 h at 37 °C. The entire STU-006 physical-stability series is quarantined for this condition/timepoint mismatch. |
| STU-007 | `10.3390/nano17050207` | Underlying primary study identified: Narmani et al., `10.1016/j.ijbiomac.2023.125554`. The abstract reports a sorafenib-loaded chitosan-PLGA-folic-acid CPSF formulation, 400 nM, 24 h, and viability of 13% (A549) and 78% (MSC). The reviewed cytotoxicity copy corrects dose, assay, material/coating, and surface charge. |
| STU-008 | `10.1039/D4RA00000X` | Quarantined: source could not be matched, and one row combines HepG2 and MCF-7 while giving one outcome. Its “IC50 ~ 50 ug/mL” is retained as an IC50 summary, not treated as administered dose. |
| STU-009, STU-010, STU-012, STU-013 | Incomplete DOI strings | Quarantined pending a resolvable primary citation and source-level check. |
| STU-011 | `10.1021/acs.molpharmaceut.0c00321` | DOI/source confirmed; two time points only, so not eligible for longitudinal trajectory modeling. |
| STU-014 | No registry citation | Quarantined; source and registry details are missing. |

Primary source checks: [STU-001 article with Table 1 and Figure 3 results](https://pmc.ncbi.nlm.nih.gov/articles/PMC3940272/),
[STU-002 PubMed record](https://pubmed.ncbi.nlm.nih.gov/26017818/),
[STU-003 primary paper and table](https://pmc.ncbi.nlm.nih.gov/articles/PMC11360396/),
[STU-004 PubMed record](https://pubmed.ncbi.nlm.nih.gov/28424550/),
[STU-005 PubMed record](https://pubmed.ncbi.nlm.nih.gov/42564046/),
[STU-006 PubMed record](https://pubmed.ncbi.nlm.nih.gov/36365212/),
[STU-007 primary paper](https://www.sciencedirect.com/science/article/abs/pii/S0141813023024480),
and [STU-011 PubMed record](https://pubmed.ncbi.nlm.nih.gov/32515968/).

“Source confirmed” does not mean every numeric value was independently
verified. Only the explicitly stated table/abstract matches above have been
checked at value level. The submitted `verification_status=Verified` fields
are retained in raw files but are not accepted as independent verification.

## Cytotoxicity normalization

`NanoMedAI_Cytotoxicity_normalized_review.csv` preserves the original
`measured_cell_viability_pct` as the continuous endpoint and adds:

- `dose_numeric`, `dose_unit`, and `dose_kind`;
- `reviewed_doi`, `review_status`, and `training_ready`;
- an empty `toxicity_class_derived` column.

Exact administered concentrations are parsed as numeric. STU-001's assay and
5 µM wortmannin dose and STU-007's 400 nM concentration are corrected from
their primary sources. “Sub-therapeutic
Dose” and “Standard Dose” remain missing numeric concentrations. The STU-008
IC50 summary remains tagged as `IC50_summary_not_administered_dose`, so it must
not be used as an exposure-dose feature. No cross-study toxicity class was
invented: the original labels use incompatible criteria, and viability in
cancer cell lines is not the same endpoint as general material safety.

`NanoMedAI_Trajectory_Audit_reviewed.csv` reclassifies STU-004 as a drug-release
trajectory, excludes STU-011 for having only two points, and marks STU-014 as
unresolved. The submitted STU-006 physical-stability rows are quarantined
because their stated 4 °C/30-day conditions do not match the cited paper's
37 °C/up-to-24-hour series.

## Training decision

All reviewed track copies have `training_ready=NO`. This is intentional:
there are only 13 study IDs across 62 observations, source IDs are unresolved
for several tracks, and correlated rows within formulations/curves must stay
together in grouped validation. These files can support a carefully cited
pilot or curation exercise after the remaining holds are resolved, but not a
credible general-purpose fit or performance claim.
