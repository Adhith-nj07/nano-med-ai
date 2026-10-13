"""Machine-readable inventory of NanoMedAI capabilities and their limits.

Registry entries describe the state of the code and available evidence. They do
not promote a working interface or model artifact to scientific validation.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


FEATURE_STATES = {
    "ACTIVE",
    "VALIDATED",
    "EXPERIMENTAL",
    "RESEARCH MODULE",
    "COMING SOON",
    "UNAVAILABLE",
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_FEATURE_ASSETS: dict[str, list[str]] = {
    "stability-prediction": [
        "data/processed/stability_combined_engineered.csv",
        "models/stability_model_final.joblib",
    ],
    "drug-release": ["data/processed/drug_release_longitudinal.csv"],
    "cytotoxicity": [
        "data/raw/cytotoxicity_meta_analysis.xlsx",
        "models/cytotoxicity_model.joblib",
    ],
    "research-assistant": [
        "data/processed/stability_combined_engineered.csv",
        "data/raw/cytotoxicity_meta_analysis.xlsx",
        "data/processed/drug_release_longitudinal.csv",
        "models/stability_model_final.joblib",
        "models/cytotoxicity_model.joblib",
    ],
}


_FEATURES: list[dict[str, Any]] = [
    {
        "id": "nanoparticle-design",
        "name": "Nanoparticle design engine",
        "version": "0.1.0",
        "state": "COMING SOON",
        "input_schema": {"type": "object", "fields": ["material", "shape", "size_nm", "surface_functionalization"]},
        "output_schema": {"type": "object", "fields": ["candidate_formulations", "comparison"]},
        "required_datasets": [],
        "model_dependencies": [],
        "api_endpoints": [],
        "supported_ui_components": ["configuration form", "particle state cards"],
        "validation_status": "Not implemented; no candidate rankings are produced.",
        "limitations": ["No formulation-generation model is available."],
        "availability": "unavailable",
    },
    {
        "id": "stability-prediction",
        "name": "Zeta potential and stability research prediction",
        "version": "1.0.0",
        "state": "EXPERIMENTAL",
        "input_schema": {"type": "object", "fields": ["Shape", "Core", "Size_nm", "Medium", "Ligand_SMILES"]},
        "output_schema": {"type": "object", "fields": ["prediction", "applicability", "uncertainty", "model_version"]},
        "required_datasets": ["data/processed/stability_combined_engineered.csv"],
        "model_dependencies": ["models/stability_model_final.joblib"],
        "api_endpoints": ["POST /api/predict/stability", "GET /api/models"],
        "supported_ui_components": ["particle state cards", "scientific status"],
        "validation_status": "Research prototype; grouped cross-validation is documented, but the API does not provide calibrated prediction intervals.",
        "limitations": ["Only predicts zeta potential within the model domain.", "Zeta potential is not a general stability endpoint."],
        "availability": "available",
    },
    {
        "id": "drug-loading",
        "name": "Drug loading and encapsulation",
        "version": "0.1.0",
        "state": "COMING SOON",
        "input_schema": {"type": "object", "fields": ["drug", "carrier", "drug_properties", "formulation"]},
        "output_schema": {"type": "object", "fields": ["loading_pct", "encapsulation_efficiency"]},
        "required_datasets": [],
        "model_dependencies": [],
        "api_endpoints": [],
        "supported_ui_components": ["particle state cards"],
        "validation_status": "No loading or encapsulation prediction model is implemented.",
        "limitations": ["Demo configuration values are illustrative only."],
        "availability": "unavailable",
    },
    {
        "id": "drug-release",
        "name": "Drug release research simulation",
        "version": "0.1.0",
        "state": "RESEARCH MODULE",
        "input_schema": {"type": "object", "fields": ["formulation", "release_model", "duration_hours"]},
        "output_schema": {"type": "object", "fields": ["time_hours", "release_pct", "model_metadata", "warnings"]},
        "required_datasets": ["data/processed/drug_release_longitudinal.csv"],
        "model_dependencies": ["Korsmeyer-Peppas kinetic fit"],
        "api_endpoints": ["POST /api/simulation/create", "GET /api/simulation/{simulation_id}/trajectory", "POST /api/prompt"],
        "supported_ui_components": ["release chart", "simulation timeline", "event timeline"],
        "validation_status": "Research prototype with documented data and model limitations; not a generally validated environmental-response model.",
        "limitations": ["Environmental effects are unsupported unless the selected model documents them.", "Demo UI values are mock values and are not API predictions."],
        "availability": "available_with_domain_limits",
    },
    {
        "id": "particle-transformation",
        "name": "Particle transformation and degradation",
        "version": "0.1.0",
        "state": "COMING SOON",
        "input_schema": {"type": "object", "fields": ["material", "environment", "time"]},
        "output_schema": {"type": "object", "fields": ["transformation_state", "size_evolution"]},
        "required_datasets": ["material-specific longitudinal transformation data"],
        "model_dependencies": [],
        "api_endpoints": [],
        "supported_ui_components": ["particle state history chart", "event timeline"],
        "validation_status": "No transformation predictor is available; the simulation capability is marked unsupported.",
        "limitations": ["Degradation and dissolution are not inferred by the current demo."],
        "availability": "unavailable",
    },
    {
        "id": "biological-interaction",
        "name": "Biological interaction research",
        "version": "0.1.0",
        "state": "COMING SOON",
        "input_schema": {"type": "object", "fields": ["particle", "protein_or_cell", "assay_conditions"]},
        "output_schema": {"type": "object", "fields": ["interaction_endpoint", "uncertainty"]},
        "required_datasets": ["protein corona and cell interaction datasets"],
        "model_dependencies": [],
        "api_endpoints": [],
        "supported_ui_components": ["biological stage panel"],
        "validation_status": "No protein corona or cellular interaction predictor is implemented.",
        "limitations": ["Biological stage labels in the demo are roadmap indicators only."],
        "availability": "unavailable",
    },
    {
        "id": "cytotoxicity",
        "name": "Cytotoxicity research prediction",
        "version": "1.0.0",
        "state": "EXPERIMENTAL",
        "input_schema": {"type": "object", "fields": ["Material type", "Core size (nm)", "Hydro size (nm)", "Surface charge (mV)", "Surface area (m2/g)", "Exposure time", "Mass dose (ug/mL)", "Assay", "Cell name"]},
        "output_schema": {"type": "object", "fields": ["prediction", "probability_toxic", "applicability", "model_version"]},
        "required_datasets": ["data/raw/cytotoxicity_meta_analysis.xlsx"],
        "model_dependencies": ["models/cytotoxicity_model.joblib"],
        "api_endpoints": ["POST /api/predict/cytotoxicity", "POST /api/prompt"],
        "supported_ui_components": ["scientific status", "particle state cards"],
        "validation_status": "Research prototype with study-grouped validation; class probability is not calibrated and outputs are not clinical safety evidence.",
        "limitations": ["Endpoint is assay and cell-context specific.", "Applicability is limited to documented training ranges and categories."],
        "availability": "available",
    },
    {
        "id": "molecular-intelligence",
        "name": "Molecular descriptor utilities",
        "version": "0.1.0",
        "state": "RESEARCH MODULE",
        "input_schema": {"type": "object", "fields": ["SMILES"]},
        "output_schema": {"type": "object", "fields": ["estimated_molecular_weight", "estimated_charge"]},
        "required_datasets": [],
        "model_dependencies": ["SMILES feature extraction in src/predict.py"],
        "api_endpoints": ["POST /api/predict/stability"],
        "supported_ui_components": ["configuration form"],
        "validation_status": "Limited descriptor extraction is implemented; parsing, fingerprints, similarity, and compatibility modeling are not provided.",
        "limitations": ["Estimated descriptors are not a substitute for validated molecular informatics."],
        "availability": "partial",
    },
    {
        "id": "research-assistant",
        "name": "Structured experiment prompt workflow",
        "version": "0.1.0",
        "state": "EXPERIMENTAL",
        "input_schema": {"type": "object", "fields": ["prompt", "optional structured overrides"]},
        "output_schema": {"type": "object", "fields": ["parsed_inputs", "predictions", "simulation", "assumptions", "warnings"]},
        "required_datasets": ["model and simulation datasets declared by invoked modules"],
        "model_dependencies": ["stability", "cytotoxicity", "drug-release workflow"],
        "api_endpoints": ["POST /api/prompt", "GET /api/models", "GET /api/dataset/{task}"],
        "supported_ui_components": ["existing workspace panels"],
        "validation_status": "Structured parsing and model invocation are implemented; this is not an evidence-linked generative scientific assistant.",
        "limitations": ["No claims of literature retrieval, report generation, or experimental design are made."],
        "availability": "partial",
    },
    {
        "id": "candidate-screening",
        "name": "Multi-objective candidate screening",
        "version": "0.1.0",
        "state": "COMING SOON",
        "input_schema": {"type": "object", "fields": ["candidate_formulations", "supported objectives", "constraints"]},
        "output_schema": {"type": "object", "fields": ["ranked_candidates", "pareto_front", "explanations"]},
        "required_datasets": ["task-specific validated datasets"],
        "model_dependencies": [],
        "api_endpoints": [],
        "supported_ui_components": ["existing charts and state cards"],
        "validation_status": "No multi-objective screening implementation is available.",
        "limitations": ["No optimization is run against unsupported or synthetic objectives."],
        "availability": "unavailable",
    },
]


def list_features() -> dict[str, Any]:
    """Return a copy so API consumers cannot mutate the in-process registry."""
    features = deepcopy(_FEATURES)
    for feature in features:
        required_assets = _FEATURE_ASSETS.get(feature["id"], [])
        missing_assets = [
            asset for asset in required_assets
            if not (PROJECT_ROOT / asset).is_file()
        ]
        if missing_assets:
            feature["state"] = "UNAVAILABLE"
            feature["availability"] = "unavailable"
            feature["missing_dependencies"] = missing_assets
    return {
        "registry_version": "1.0.0",
        "feature_states": sorted(FEATURE_STATES),
        "features": features,
    }
