"""Dataset cards with live file integrity and quality summaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

_DATASETS: dict[str, dict[str, Any]] = {
    "stability": {
        "name": "Engineered nanoparticle zeta potential",
        "path": "data/processed/stability_combined_engineered.csv",
        "status": "ACTIVE",
        "target": {"column": "Zeta_mV", "unit": "mV"},
        "group_column": "study_id",
        "upstream_datasets": [
            {
                "doi": "10.5281/zenodo.14866297",
                "title": "Zeta Potential of 90 GNPs in Phosphate Buffer at pH 7.4",
                "license": "CC BY 4.0",
            },
            {
                "doi": "10.5281/zenodo.18429745",
                "title": "Experimental DLS, zeta potential and TEM-derived size data for nanodiamonds and carbon dots in aqueous environments",
                "license": "CC BY 4.0",
            },
        ],
        "provenance_document": "docs/ml/STABILITY_RECOVERY_REPORT.md",
        "validation": "5-fold GroupKFold grouped by study_id; see docs/ml/FINAL_VALIDATION_STATUS.md",
        "limitations": [
            "The target is zeta potential, which is not a general particle stability endpoint.",
            "Cross-validated MAE is about 18.90 mV and R2 is about 0.108.",
            "Only the active engineered dataset is summarized; older 69-row data are not the active model dataset.",
        ],
    },
    "cytotoxicity": {
        "name": "Metal oxide nanoparticle cytotoxicity meta-analysis",
        "path": "data/raw/cytotoxicity_meta_analysis.xlsx",
        "status": "ACTIVE",
        "target": {"column": "Toxicity", "unit": "Toxic/Nontoxic class"},
        "group_column": "Pubmed ID",
        "upstream_datasets": [
            {
                "doi": "10.5281/zenodo.15300193",
                "title": "Meta-analyzed datasets for toxicity classification of metal oxide nanoparticles",
                "license": "Open Access; specific license not recorded in project documentation",
            }
        ],
        "provenance_document": "docs/data/DATASET_SELECTION.md",
        "validation": "5-fold GroupKFold grouped by Pubmed ID; see docs/ml/FINAL_VALIDATION_STATUS.md",
        "limitations": [
            "The active model is an assay and cell-context-specific research prototype.",
            "Toxicity labels are derived from viability and do not establish clinical safety.",
            "License terms should be checked at the source before redistribution.",
        ],
    },
    "drug-release": {
        "name": "Longitudinal polymeric nanoparticle drug release",
        "path": "data/processed/drug_release_longitudinal.csv",
        "status": "ACTIVE",
        "target": {"column": "cumulative_release_pct", "unit": "%"},
        "group_column": "trajectory_id",
        "upstream_datasets": [
            {
                "doi": "10.1038/s41467-022-35343-w",
                "title": "Machine learning models to accelerate the design of polymeric long-acting injectables",
                "repository": "Zenodo 10.5281/zenodo.7309021",
                "license": "CC BY 4.0 (dataset card)",
            }
        ],
        "provenance_document": "docs/SIMULATION/DRUG_RELEASE_DATASET_CARD.md",
        "validation": "GroupKFold grouped by trajectory_id; see model registry and docs/SIMULATION/DRUG_RELEASE_DATASET_CARD.md",
        "limitations": [
            "Nine trajectories and 115 observations are documented in the dataset card.",
            "Scope is limited to spherical PLGA/PLA particles carrying paclitaxel or letrozole.",
            "pH, temperature, and ionic strength effects are not supported by this dataset.",
        ],
    },
}


def _read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported dataset format: {path.suffix}")


def _dataset_card(
    dataset_id: str,
    definition: dict[str, Any],
    preview_rows: int = 0,
    include_source_identifiers: bool = False,
) -> dict[str, Any]:
    path = PROJECT_ROOT / definition["path"]
    card = {"id": dataset_id, **definition}
    card["source_path"] = card.pop("path")
    card["available"] = path.is_file()
    if not path.is_file():
        card["status"] = "UNAVAILABLE"
        card["availability_reason"] = "Dataset file is missing from this installation."
        return card

    card["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    frame = _read_dataset(path)
    card["statistics"] = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "missing_values_by_column": {
            str(column): int(count)
            for column, count in frame.isna().sum().items()
            if count
        },
        "numeric_ranges": {
            str(column): [float(frame[column].min()), float(frame[column].max())]
            for column in frame.select_dtypes(include="number").columns
            if frame[column].notna().any()
        },
        "group_count": (
            int(frame[definition["group_column"]].nunique(dropna=True))
            if definition["group_column"] in frame.columns
            else None
        ),
        "group_column": definition["group_column"],
    }
    source_column = {
        "stability": "DOI",
        "cytotoxicity": "Pubmed ID",
        "drug-release": "source_doi",
    }[dataset_id]
    source_ids = (
        sorted(frame[source_column].dropna().astype(str).str.strip().loc[lambda values: values.ne("")].unique().tolist())
        if source_column in frame.columns
        else []
    )
    card["statistics"]["source_identifier_column"] = source_column
    card["statistics"]["source_identifier_count"] = len(source_ids)
    if include_source_identifiers:
        card["source_identifiers"] = [
            {"type": source_column, "value": identifier}
            for identifier in source_ids
        ]
    if dataset_id == "drug-release" and "measurement_provenance" in frame.columns:
        card["statistics"]["unknown_measurement_provenance_rows"] = int(
            frame["measurement_provenance"].fillna("UNKNOWN").astype(str).str.upper().eq("UNKNOWN").sum()
        )
    card["columns"] = [str(column) for column in frame.columns]
    if preview_rows:
        card["preview"] = json.loads(frame.head(preview_rows).to_json(orient="records"))
    return card


def list_datasets() -> dict[str, Any]:
    return {
        "catalog_version": "1.0.0",
        "datasets": [_dataset_card(dataset_id, definition) for dataset_id, definition in _DATASETS.items()],
    }


def get_dataset(dataset_id: str, preview_rows: int = 0) -> dict[str, Any] | None:
    definition = _DATASETS.get(dataset_id)
    if definition is None:
        return None
    return _dataset_card(
        dataset_id,
        definition,
        preview_rows=preview_rows,
        include_source_identifiers=True,
    )
