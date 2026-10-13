"""Create provenance-preserving candidate tables from acquired public datasets.

This is curation only. It does not train models, infer missing values, or
change source files in data/raw.
"""
from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "public_data_candidates"
OUT.mkdir(parents=True, exist_ok=True)

# Zeta potential: NanoMILE-derived curated ENMs, dataset DOI 10.5281/zenodo.14864383
zeta_path = RAW / "zeta_potential_69_enms.xlsx"
zeta = pd.read_excel(zeta_path, sheet_name="default")
zeta.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in zeta.columns]
zeta = zeta.rename(columns={
    "metal core": "core_material",
    "Coating": "surface_coating",
    "Type of Coating (Anionic, Cationic, Neutral)": "coating_charge_class",
    "Ageing": "ageing_status",
    "Diameter (TEM-STEM)": "core_diameter_nm",
    "Shape group": "shape",
    "Geometric Surface Area (nm2)": "geometric_surface_area_nm2",
    "Zeta (mV)": "zeta_potential_mv",
})
zeta.insert(0, "record_id", [f"Z69-{i:03d}" for i in range(1, len(zeta) + 1)])
zeta["source_dataset"] = "NanoMILE 69 ENMs / Zenodo 14864383"
zeta["source_dataset_doi"] = "10.5281/zenodo.14864383"
zeta["source_license"] = "CC-BY-4.0"
zeta["measurement_medium"] = "not specified in selected table; see primary dataset metadata"
zeta["training_ready"] = "NO: candidate; single dataset and external validation still required"
zeta.to_csv(OUT / "zeta_potential_69_candidate.csv", index=False)

# Additional already-acquired CC-BY zeta series, kept in distinct media strata.
zeta288 = pd.read_csv(ROOT / "data" / "processed" / "stability_combined.csv")
zeta288 = zeta288.rename(columns={
    "original_record_id": "record_id",
    "DOI": "study_doi",
    "Reference": "reference",
    "Medium": "measurement_medium",
    "Shape": "shape",
    "Core": "core_material",
    "Size (nm)": "core_or_reported_size_nm",
    "#Ligand1": "ligand1_count_or_label",
    "Ligand1 SMILES": "ligand1_smiles",
    "#Ligand2": "ligand2_count_or_label",
    "Ligand2 SMILES": "ligand2_smiles",
    "Zeta_mV": "zeta_potential_mv",
})
zeta288["source_dataset_doi"] = zeta288["source_dataset"].map({
    "zeta_potential_198_enms_millipore.xlsx": "10.5281/zenodo.14866284",
    "zeta_potential_90_enms_phosphate.xlsx": "10.5281/zenodo.14866297",
})
zeta288["source_license"] = "CC-BY-4.0 per project source log"
zeta288["training_ready"] = "NO: candidate; retain medium as a model condition and evaluate by study/formulation group"
zeta288.to_csv(OUT / "zeta_potential_288_candidate.csv", index=False)

# Cytotoxicity: retain only interpretable, application-relevant predictors,
# continuous endpoint, publisher-defined class, and study grouping/provenance.
tox_path = RAW / "cytotoxicity_meta_analysis.xlsx"
tox = pd.read_excel(tox_path, sheet_name=0)
tox_cols = [
    "Pubmed ID", "Material type", "Core size (nm)", "Hydro size (nm)",
    "Surface charge (mV)", "Surface area (m2/g)", "Assay", "Cell name",
    "Cell species", "Exposure time", "Mass dose (ug/mL)", "Viability (%)",
    "Toxicity", "Average score",
]
tox = tox[tox_cols].copy().rename(columns={
    "Pubmed ID": "study_pubmed_id",
    "Material type": "material_type",
    "Core size (nm)": "core_size_nm",
    "Hydro size (nm)": "hydrodynamic_size_nm",
    "Surface charge (mV)": "surface_charge_mv",
    "Surface area (m2/g)": "surface_area_m2_g",
    "Assay": "assay",
    "Cell name": "cell_line",
    "Cell species": "cell_species",
    "Exposure time": "exposure_time_h_raw",
    "Mass dose (ug/mL)": "mass_dose_ug_ml",
    "Viability (%)": "cell_viability_pct",
    "Toxicity": "source_toxicity_label",
    "Average score": "source_average_quality_score",
})
tox.insert(0, "record_id", [f"MOX-3B-{i:04d}" for i in range(1, len(tox) + 1)])
tox["source_dataset"] = "S2NANO MeOx IIIB / Zenodo 15300193"
tox["source_dataset_doi"] = "10.5281/zenodo.15300193"
tox["source_license"] = "Confirm exact Zenodo Rights field before redistribution"
tox["source_label_rule"] = "Publisher dataset describes Toxicity from 50% cell viability threshold"
tox["training_ready"] = "NO: candidate; harmonization and grouped validation required"
tox.to_csv(OUT / "cytotoxicity_meox_iiib_candidate.csv", index=False)

# Existing longitudinal release source, copied unchanged for the collection bundle.
release = pd.read_csv(ROOT / "data" / "processed" / "drug_release_longitudinal.csv")
release.to_csv(OUT / "drug_release_115_candidate.csv", index=False)

def field_stats(df, fields):
    return {
        col: {
            "missing": int(df[col].isna().sum()),
            "missing_pct": round(float(df[col].isna().mean() * 100), 2),
            "unique_nonmissing": int(df[col].nunique(dropna=True)),
        }
        for col in fields
    }

tox_study_counts = tox.groupby("study_pubmed_id", dropna=False).size()
tox_viability = pd.to_numeric(tox["cell_viability_pct"], errors="coerce")
tox_label_expected = tox_viability.map(lambda v: "Toxic" if v < 50 else "Nontoxic")
summary = {
    "created_by": "scripts/collect_public_candidates.py",
    "curation_only": True,
    "raw_source_files_unchanged": True,
    "datasets": {
        "zeta_potential_69": {
            "source_file": "data/raw/zeta_potential_69_enms.xlsx",
            "source_doi": "10.5281/zenodo.14864383",
            "license": "CC-BY-4.0 per Zenodo record",
            "rows": int(len(zeta)),
            "duplicate_full_rows": int(zeta.duplicated().sum()),
            "zeta_target_missing": int(zeta["zeta_potential_mv"].isna().sum()),
            "target_min": float(zeta["zeta_potential_mv"].min()),
            "target_max": float(zeta["zeta_potential_mv"].max()),
            "selected_field_quality": field_stats(zeta, [
                "core_material", "surface_coating", "coating_charge_class",
                "ageing_status", "core_diameter_nm", "shape",
                "geometric_surface_area_nm2", "zeta_potential_mv",
            ]),
        },
        "zeta_potential_198_water_plus_90_pbs": {
            "source_file": "data/processed/stability_combined.csv",
            "source_dois": ["10.5281/zenodo.14866284", "10.5281/zenodo.14866297"],
            "license": "CC-BY-4.0 per project source log; preserve medium distinction",
            "rows": int(len(zeta288)),
            "duplicate_full_rows": int(zeta288.duplicated().sum()),
            "target_missing": int(zeta288["zeta_potential_mv"].isna().sum()),
            "medium_counts": {str(k): int(v) for k, v in zeta288["measurement_medium"].value_counts(dropna=False).items()},
            "study_groups": int(zeta288["study_id"].nunique(dropna=True)),
        },
        "cytotoxicity_meox_iiib": {
            "source_file": "data/raw/cytotoxicity_meta_analysis.xlsx",
            "source_doi": "10.5281/zenodo.15300193",
            "license": "Verify exact Rights field on Zenodo before redistribution",
            "rows": int(len(tox)),
            "duplicate_full_rows": int(tox.duplicated().sum()),
            "study_count": int(tox["study_pubmed_id"].nunique(dropna=True)),
            "study_group_sizes": {str(k): int(v) for k, v in tox_study_counts.items()},
            "viability_out_of_0_100": int(((tox["cell_viability_pct"] < 0) | (tox["cell_viability_pct"] > 100)).sum()),
            "source_label_threshold_mismatches_at_50pct": int((tox_label_expected != tox["source_toxicity_label"]).sum()),
            "toxicity_class_counts": {str(k): int(v) for k, v in tox["source_toxicity_label"].value_counts(dropna=False).items()},
            "selected_field_quality": field_stats(tox, [
                "study_pubmed_id", "material_type", "core_size_nm", "hydrodynamic_size_nm",
                "surface_charge_mv", "surface_area_m2_g", "assay", "cell_line",
                "cell_species", "exposure_time_h_raw", "mass_dose_ug_ml",
                "cell_viability_pct", "source_toxicity_label", "source_average_quality_score",
            ]),
            "use_note": "Keep paper/study groups together in evaluation; do not use study_pubmed_id as a model feature. Preserve continuous viability and source class as separate targets. Do not clip observations outside 0-100 without source review; these may be control-relative assay values.",
        },
        "drug_release_bannigan_subset": {
            "source_file": "data/processed/drug_release_longitudinal.csv",
            "source_publication_doi": "10.1038/s41467-022-35343-w",
            "source_data_zenodo_doi": "10.5281/zenodo.7309020",
            "license": "CC-BY-4.0 per existing project dataset card; verify Zenodo record Rights before redistribution",
            "rows": int(len(release)),
            "trajectory_count": int(release["trajectory_id"].nunique()),
            "formulation_count": int(release["formulation_id"].nunique()),
            "study_count": int(release["study_id"].nunique()),
            "duplicate_full_rows": int(release.duplicated().sum()),
            "time_range_hours": [float(release["time_hours"].min()), float(release["time_hours"].max())],
            "release_range_pct": [float(release["cumulative_release_pct"].min()), float(release["cumulative_release_pct"].max())],
            "missing_fields": {str(k): int(v) for k, v in release.isna().sum().items() if v},
            "use_note": "Only 9 trajectories from one study; suitable for exploratory kinetic fitting, not a generalizable multi-study release model. Group by trajectory_id.",
        },
    },
    "not_included_in_candidate_exports": {
        "data/raw/zeta_potential_198_enms_millipore.xlsx": "Included in the separate 288-row candidate export; Millipore-water condition is preserved.",
        "data/raw/zeta_potential_90_enms_phosphate.xlsx": "Included in the separate 288-row candidate export; PBS pH 7.4 condition is preserved.",
        "data/raw/cytotoxicity_14_metal_oxides.xlsx": "494-row source has no PubMed grouping field in its primary sheet and a non-data second sheet; hold pending provenance/grouping audit.",
        "data/raw/user_submitted_20261010/": "Prior reconciliation has unresolved source/value conflicts; do not train from these rows yet.",
        "physical stability longitudinal data": "data/processed/nanoparticle_physical_stability_longitudinal.csv currently has zero rows; no sourced stability trajectories are ready.",
    },
}
(OUT / "collection_quality_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({
    "output_dir": str(OUT),
    "zeta_rows": len(zeta),
    "cytotoxicity_rows": len(tox),
    "zeta_duplicates": int(zeta.duplicated().sum()),
    "cytotoxicity_duplicates": int(tox.duplicated().sum()),
    "cytotoxicity_studies": int(tox["study_pubmed_id"].nunique(dropna=True)),
}, indent=2))
