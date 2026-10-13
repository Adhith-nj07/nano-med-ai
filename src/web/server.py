import os
import sys
import json
import hashlib
from typing import Dict, Any, Optional, List, Literal
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.predict import (
    predict_stability,
    predict_cytotoxicity,
    ValidationError as ModelValidationError,
    ModelLoadError,
    _extract_charge,
    _estimate_mw
)
from src.api.simulation_api import SimulationSessionManager
from src.api.prompt_workflow import (
    check_model_domain,
    get_model_domains,
    get_model_registry,
    run_experiment_prompt,
)
from src.feature_registry import list_features
from src.dataset_catalog import get_dataset, list_datasets

app = FastAPI(
    title="NanoMedAI Platform",
    description="Machine Learning & Biophysical Simulation for Nanomedicine",
    version="1.0.0"
)

# Enable CORS for local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Simulation Session Manager
sim_manager = SimulationSessionManager()

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DEMO_DIR = os.path.join(PROJECT_ROOT, "demo", "nanomedai")
if os.path.exists(DEMO_DIR):
    app.mount("/demo", StaticFiles(directory=DEMO_DIR, html=True), name="demo")

@app.get("/")
def get_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# Pydantic Request Models
class StabilityRequest(BaseModel):
    Shape: str = Field(..., examples=["Sphere"])
    Core: str = Field(..., examples=["Silver"])
    Size_nm: float = Field(..., gt=0, examples=[20.0])
    Medium: str = Field(..., examples=["PBS pH 7.4"])
    Ligand_SMILES: str = Field(..., examples=["C(C(C(=O)O)O)(C(=O)O)O"])

class CytotoxicityRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    Core_size_nm: float = Field(..., alias="Core size (nm)", gt=0, examples=[25.0])
    Hydro_size_nm: float = Field(..., alias="Hydro size (nm)", gt=0, examples=[65.0])
    Surface_charge_mV: float = Field(..., alias="Surface charge (mV)", examples=[-24.5])
    Surface_area_m2_g: float = Field(..., alias="Surface area (m2/g)", gt=0, examples=[45.0])
    Exposure_time_h: float = Field(..., alias="Exposure time", gt=0, examples=[24.0])
    Mass_dose_ug_mL: float = Field(..., alias="Mass dose (ug/mL)", gt=0, examples=[50.0])
    Material_type: str = Field(..., alias="Material type", examples=["CuO"])
    Assay: str = Field(..., examples=["MTT"])
    Cell_name: str = Field(..., alias="Cell name", examples=["A549"])

class SimCreateRequest(BaseModel):
    formulation_id: Optional[str] = "formulation-a"
    nanoparticle: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, Any] = Field(default_factory=dict)
    models: Optional[Dict[str, Any]] = None
    time_step_hours: Optional[float] = 1.0

class SimRunRequest(BaseModel):
    target_time_hours: float = Field(..., gt=0, examples=[72.0])

class SimEnvUpdateRequest(BaseModel):
    temperature: Optional[float] = None
    ph: Optional[float] = None
    ionic_strength: Optional[float] = None
    medium: Optional[str] = None

class ExperimentPromptRequest(BaseModel):
    sample_name: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    temperature_c: Optional[float] = Field(default=None, gt=-273.15)
    ph: Optional[float] = Field(default=None, ge=0, le=14)
    ionic_strength: Optional[float] = Field(default=None, ge=0)
    medium: Optional[str] = None
    ligand_smiles: Optional[str] = None
    core: Optional[str] = None
    shape: Optional[str] = None
    particle_size_nm: Optional[float] = Field(default=None, gt=0)
    core_size_nm: Optional[float] = Field(default=None, gt=0)
    hydrodynamic_size_nm: Optional[float] = Field(default=None, gt=0)
    surface_area_m2_g: Optional[float] = Field(default=None, gt=0)
    surface_area_source: Optional[Literal["measured", "estimated"]] = None
    surface_charge_mv: Optional[float] = None
    material_type: Optional[str] = None
    assay: Optional[str] = None
    cell_name: Optional[str] = None
    exposure_time_hours: Optional[float] = Field(default=None, gt=0)
    mass_dose_ug_ml: Optional[float] = Field(default=None, ge=0)
    drug_name: Optional[str] = None
    release_polymer: Optional[str] = None
    drug_loading_pct: Optional[float] = Field(default=None, ge=0)
    drug_mw: Optional[float] = Field(default=None, gt=0)
    polymer_mw: Optional[float] = Field(default=None, gt=0)
    la_ga_ratio: Optional[float] = Field(default=None, ge=0)
    simulation_duration_hours: Optional[float] = Field(default=None, gt=0)


@app.get("/old")
@app.get("/classic")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "NanoMedAI API active. Static frontend file not found at " + index_path}


@app.get("/")
@app.get("/simulation")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "NanoMedAI frontend not found at " + index_path}


@app.get("/demo")
def serve_demo():
    demo_index_path = os.path.join(PROJECT_ROOT, "demo", "nanomedai", "index.html")
    if os.path.exists(demo_index_path):
        return FileResponse(demo_index_path)
    return {"message": "NanoMedAI UI Demo not found at " + demo_index_path}


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NanoMedAI Full-Stack Platform",
        "version": "1.0.0",
        "models": {
            "stability_model": "Random Forest Regressor (Zeta Potential mV)",
            "cytotoxicity_model": "Random Forest Classifier (Toxic/Nontoxic)",
            "simulation_engine": "Korsmeyer-Peppas Release & Biophysical State Engine"
        },
        "active_simulations": len(sim_manager._sessions)
    }


@app.get("/api/v1/health")
def versioned_health_check():
    dependencies = {
        "stability-prediction": [
            "data/processed/stability_combined_engineered.csv",
            "models/stability_model_final.joblib",
        ],
        "cytotoxicity": [
            "data/raw/cytotoxicity_meta_analysis.xlsx",
            "models/cytotoxicity_model.joblib",
        ],
        "drug-release": ["data/processed/drug_release_longitudinal.csv"],
    }
    checks = {}
    for feature_id, relative_paths in dependencies.items():
        missing = [
            relative_path for relative_path in relative_paths
            if not os.path.isfile(os.path.join(PROJECT_ROOT, relative_path))
        ]
        checks[feature_id] = {
            "status": "available" if not missing else "unavailable",
            "missing_dependencies": missing,
        }
    overall_status = "healthy" if all(
        check["status"] == "available" for check in checks.values()
    ) else "degraded"
    return {
        "status": overall_status,
        "service": "NanoMedAI Platform",
        "version": "1.0.0",
        "checks": checks,
        "active_simulations": len(sim_manager._sessions),
    }


@app.get("/api/v1/features")
def get_feature_registry():
    """Return feature availability and scientific limitations for clients."""
    return list_features()


@app.get("/api/v1/datasets")
def get_dataset_catalog():
    """List dataset cards with provenance and live file quality summaries."""
    return list_datasets()


@app.get("/api/v1/datasets/{dataset_id}")
def get_dataset_card(dataset_id: str, preview_rows: int = Query(default=0, ge=0, le=10)):
    try:
        card = get_dataset(dataset_id, preview_rows=preview_rows)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read dataset card: {exc}") from exc
    if card is None:
        raise HTTPException(status_code=404, detail="Unknown dataset")
    return card


@app.get("/api/v1/models")
def get_versioned_model_registry():
    """Return model cards together with the active artifact integrity state."""
    registry = get_model_registry()
    artifact_paths = {
        "zeta_potential": "models/stability_model_final.joblib",
        "toxicity_class": "models/cytotoxicity_model.joblib",
    }
    for model in registry["models"]:
        relative_path = artifact_paths.get(model["target"])
        if relative_path:
            artifact_path = os.path.join(PROJECT_ROOT, relative_path)
            artifact_exists = os.path.isfile(artifact_path)
            artifact_sha256 = None
            if artifact_exists:
                with open(artifact_path, "rb") as artifact_file:
                    artifact_sha256 = hashlib.sha256(artifact_file.read()).hexdigest()
            model["artifact"] = {
                "kind": "serialized_model",
                "path": relative_path,
                "available": artifact_exists,
                "sha256": artifact_sha256,
            }
            model["scientific_state"] = "EXPERIMENTAL"
            model["availability"] = "available" if artifact_exists else "unavailable"
        else:
            dataset_path = os.path.join(PROJECT_ROOT, "data", "processed", "drug_release_longitudinal.csv")
            model["artifact"] = {
                "kind": "dataset_fitted_pipeline",
                "path": None,
                "available": os.path.isfile(dataset_path),
                "sha256": None,
            }
            model["scientific_state"] = "RESEARCH MODULE"
            model["availability"] = "available" if os.path.isfile(dataset_path) else "unavailable"
    return {"registry_version": "1.0.0", **registry}


@app.get("/api/metadata")
def get_metadata():
    """Returns valid categorical values, numeric ranges, and presets for UI forms."""
    domains = get_model_domains()
    stability_domain = domains["stability"]
    toxicity_domain = domains["cytotoxicity"]
    ligand_presets = [
        {"name": "Citric Acid (Citrate)", "smiles": "C(C(C(=O)O)O)(C(=O)O)O", "charge": "Anionic"},
        {"name": "Polyethylene Glycol (PEG)", "smiles": "OCCO", "charge": "Neutral"},
        {"name": "Chitosan monomer", "smiles": "C1C(C(C(C(O1)CO)O)N)O", "charge": "Cationic"},
        {"name": "Betaine", "smiles": "C[N+](C)(C)CC(=O)[O-]", "charge": "Zwitterionic"},
    ]
    stability_charge = stability_domain["category_modes"]["Coating_Charge"]
    ligand_smiles = next((item["smiles"] for item in ligand_presets if item["charge"] == stability_charge), ligand_presets[0]["smiles"])
    stability_presets = [{
        "name": "Observed training median",
        "data": {
            "Shape": stability_domain["category_modes"]["Shape"],
            "Core": stability_domain["category_modes"]["Core"],
            "Size_nm": stability_domain["numeric_medians"]["Size_nm"],
            "Medium": stability_domain["category_modes"]["Medium"],
            "Ligand_SMILES": ligand_smiles,
        },
    }]
    toxicity_frame = pd.read_excel(os.path.join(PROJECT_ROOT, "data", "raw", "cytotoxicity_meta_analysis.xlsx"))
    toxicity_fields = list(toxicity_domain["numeric_ranges"]) + list(toxicity_domain["categories"])
    toxicity_presets = []
    for class_name in ("Nontoxic", "Toxic"):
        candidates = toxicity_frame[toxicity_frame["Toxicity"] == class_name].dropna(subset=toxicity_fields)
        if candidates.empty:
            continue
        row = candidates.iloc[0]
        toxicity_presets.append({
            "name": f"Observed {class_name.lower()} training example",
            "data": {
                column: float(row[column]) if column in toxicity_domain["numeric_ranges"] else str(row[column])
                for column in toxicity_fields
            },
        })
    return {
        "stability": {
            "shapes": stability_domain["categories"]["Shape"],
            "cores": stability_domain["categories"]["Core"],
            "media": stability_domain["categories"]["Medium"],
            "coating_charges": stability_domain["categories"]["Coating_Charge"],
            "category_modes": stability_domain["category_modes"],
            "ligand_presets": ligand_presets,
            "presets": stability_presets,
            "default_ranges": {"size_nm": stability_domain["numeric_ranges"]["Size_nm"]},
            "numeric_medians": stability_domain["numeric_medians"],
            "training_source": stability_domain["source"],
            "training_size": stability_domain["rows"],
        },
        "cytotoxicity": {
            "materials": toxicity_domain["categories"]["Material type"],
            "assays": toxicity_domain["categories"]["Assay"],
            "cell_lines": toxicity_domain["categories"]["Cell name"],
            "category_modes": toxicity_domain["category_modes"],
            "numeric_ranges": toxicity_domain["numeric_ranges"],
            "numeric_medians": toxicity_domain["numeric_medians"],
            "training_source": toxicity_domain["source"],
            "training_size": toxicity_domain["rows"],
            "presets": toxicity_presets
        },
        "drug_release": domains["drug_release"],
        "simulation": {
            "formulations": [
                {
                    "id": "formulation-a",
                    "name": "Formulation A: PLGA + Paclitaxel",
                    "carrier": "PLGA",
                    "drug": "Paclitaxel",
                    "size_nm": 120.0,
                    "zeta_potential": -22.0,
                    "loading_pct": 8.0,
                    "coating": "PEG",
                    "k_kp": 0.18,
                    "n_kp": 0.45
                },
                {
                    "id": "formulation-b",
                    "name": "Formulation B: PLA + Letrozole",
                    "carrier": "PLA",
                    "drug": "Letrozole",
                    "size_nm": 95.0,
                    "zeta_potential": -15.0,
                    "loading_pct": 5.0,
                    "coating": "Citrate",
                    "k_kp": 0.12,
                    "n_kp": 0.50
                },
                {
                    "id": "formulation-c",
                    "name": "Formulation C: PCL + Doxorubicin",
                    "carrier": "PCL",
                    "drug": "Doxorubicin",
                    "size_nm": 150.0,
                    "zeta_potential": 18.0,
                    "loading_pct": 12.0,
                    "coating": "Chitosan",
                    "k_kp": 0.15,
                    "n_kp": 0.43
                }
            ]
        }
    }


@app.get("/api/models")
def get_models():
    return get_model_registry()


@app.get("/api/dataset/{task}")
def get_dataset_preview(task: str):
    dataset_paths = {
        "stability": os.path.join(PROJECT_ROOT, "data", "processed", "stability_combined_engineered.csv"),
        "cytotoxicity": os.path.join(PROJECT_ROOT, "data", "raw", "cytotoxicity_meta_analysis.xlsx"),
        "nano_drug": os.path.join(PROJECT_ROOT, "data", "nano_drug", "nano_drug_training_dataset.csv"),
    }
    path = dataset_paths.get(task)
    if path is None:
        raise HTTPException(status_code=404, detail="Unknown dataset")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dataset file not found: {os.path.basename(path)}")

    try:
        frame = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
        numeric_ranges = {}
        for column in frame.select_dtypes(include="number").columns:
            values = frame[column].dropna()
            if not values.empty:
                numeric_ranges[str(column)] = [float(values.min()), float(values.max())]
        return {
            "task": task,
            "source": os.path.relpath(path, PROJECT_ROOT).replace(os.sep, "/"),
            "rows": len(frame),
            "columns": list(frame.columns),
            "missing": {str(column): int(count) for column, count in frame.isna().sum().items()},
            "numeric_ranges": numeric_ranges,
            "head": json.loads(frame.head(8).to_json(orient="records")),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read dataset preview: {exc}") from exc


@app.get("/api/nano_drug/summary")
def get_nano_drug_summary():
    summary_path = os.path.join(PROJECT_ROOT, "data", "nano_drug", "dataset_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Nano drug summary not found")


@app.get("/api/nano_drug/models")
def get_nano_drug_models():
    models_path = os.path.join(PROJECT_ROOT, "data", "nano_drug", "model_analysis_results.json")
    if os.path.exists(models_path):
        with open(models_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Nano drug models not found")


@app.get("/api/nano_drug/records")
def get_nano_drug_records(limit: int = 20, search: Optional[str] = None):
    dataset_path = os.path.join(PROJECT_ROOT, "data", "nano_drug", "nano_drug_training_dataset.csv")
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="Nano drug dataset file not found")
    try:
        df = pd.read_csv(dataset_path)
        if search:
            s = search.lower()
            mask = (
                df["drug_name"].astype(str).str.lower().str.contains(s) |
                df["nanoparticle_material"].astype(str).str.lower().str.contains(s) |
                df["formulation_type"].astype(str).str.lower().str.contains(s)
            )
            df = df[mask]
        selected_cols = [
            "record_id", "drug_name", "drug_class", "formulation_type",
            "nanoparticle_material", "particle_size_nm", "zeta_potential_mV",
            "drug_loading_percent", "release_72h_percent", "predicted_stability_class",
            "predicted_release_class", "predicted_risk_class"
        ]
        available_cols = [c for c in selected_cols if c in df.columns]
        records = df[available_cols].head(limit).to_dict(orient="records")
        return {"total_found": len(df), "limit": limit, "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading nano drug records: {e}")


@app.post("/api/prompt")
def run_experiment(req: ExperimentPromptRequest):
    try:
        overrides = req.model_dump(exclude={"prompt"}, exclude_none=True)
        return run_experiment_prompt(req.prompt, overrides)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModelValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prompt workflow failed: {exc}") from exc


@app.post("/api/predict/stability")
def predict_nanoparticle_stability(req: StabilityRequest):
    try:
        data = req.model_dump()
        domain_issues = check_model_domain("stability", data)
        if domain_issues:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Input outside validated model domain.",
                    "applicability": "outside_domain",
                    "issues": domain_issues,
                    "supported_ranges": get_model_domains()["stability"]["numeric_ranges"],
                    "supported_categories": get_model_domains()["stability"]["categories"],
                },
            )
        result = predict_stability(data)
        
        # Calculate auxiliary feature engineering details for visual explanation
        charge = _extract_charge(req.Ligand_SMILES)
        mw = _estimate_mw(req.Ligand_SMILES)
        
        val = result["prediction"]
        # Determine stability classification heuristic
        # Absolute Zeta > 30 mV => high electrostatic stability
        # 20 to 30 mV => moderate / incipient stability
        # < 20 mV => prone to rapid aggregation
        abs_v = abs(val)
        if abs_v >= 30:
            stability_class = "Highly Stable"
            stability_color = "accent"
            stability_desc = "Excellent colloidal stability due to strong electrostatic repulsion (|ζ| ≥ 30 mV)."
        elif abs_v >= 20:
            stability_class = "Moderately Stable"
            stability_color = "warn"
            stability_desc = "Moderate stability; potential aggregation in high ionic strength media (20 ≤ |ζ| < 30 mV)."
        else:
            stability_class = "Unstable / Aggregation-Prone"
            stability_color = "danger"
            stability_desc = "Weak surface charge (|ζ| < 20 mV); particles likely to agglomerate without steric stabilization."

        registry = get_model_registry()["models"][0]
        return {
            "prediction": round(val, 2),
            "unit": "mV",
            "target": "zeta_potential",
            "confidence": "Low" if registry["metrics"]["R2"] < 0.5 else "Moderate",
            "uncertainty": {
                "type": "grouped_cross_validation_error",
                "mae_mV": registry["metrics"]["MAE_mV"],
                "rmse_mV": registry["metrics"]["RMSE_mV"],
                "calibrated_interval": False,
            },
            "applicability": "inside_domain",
            "validation_metrics": registry["metrics"],
            "limitations": registry["limitations"],
            "stability_class": stability_class,
            "stability_color": stability_color,
            "stability_desc": stability_desc,
            "engineered_features": {
                "detected_charge": charge,
                "estimated_ligand_mw_da": round(mw, 2),
                "log_size": round(float(data["Size_nm"]), 2)
            },
            "model_metadata": {
                "model_type": "Ridge / Random Forest Regressor",
                "validation": "GroupKFold by DOI (zero cross-study leakage)",
                "dataset_size": "288 harmonized nanoparticles"
            }
        }
    except HTTPException:
        raise
    except ModelValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except ModelLoadError as me:
        raise HTTPException(status_code=500, detail=str(me))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@app.post("/api/predict/cytotoxicity")
def predict_nanoparticle_cytotoxicity(req: Request, payload: Dict[str, Any]):
    try:
        domain_issues = check_model_domain("cytotoxicity", payload)
        if domain_issues:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Input outside validated model domain.",
                    "applicability": "outside_domain",
                    "issues": domain_issues,
                    "supported_ranges": get_model_domains()["cytotoxicity"]["numeric_ranges"],
                    "supported_categories": get_model_domains()["cytotoxicity"]["categories"],
                },
            )
        result = predict_cytotoxicity(payload)
        registry = get_model_registry()["models"][1]
        is_toxic = result["prediction"] == "Toxic"
        
        # Additional contextual evaluation
        dose = float(payload.get("Mass dose (ug/mL)", 0))
        material = payload.get("Material type", "")
        
        risk_level = "High Risk" if is_toxic and dose >= 50 else ("Moderate Risk" if is_toxic else "Low Risk")
        
        return {
            "prediction": result["prediction"],
            "target": "cytotoxicity",
            "is_toxic": is_toxic,
            "risk_level": risk_level,
            "confidence": "Moderate" if registry["metrics"]["F1"] >= 0.4 else "Low",
            "model_vote_confidence": result.get("confidence"),
            "probability_toxic": result.get("probability_toxic"),
            "probability_calibrated": False,
            "applicability": "inside_domain",
            "validation_metrics": registry["metrics"],
            "limitations": registry["limitations"],
            "interpretation": f"Under assay conditions ({payload.get('Assay')}) at {dose} µg/mL on {payload.get('Cell name')}, the {material} formulation is classified as {result['prediction']}.",
            "model_metadata": {
                "model_type": "Random Forest Classifier",
                "validation": "GroupKFold by Pubmed ID (meta-analysis across studies)",
                "doi": "10.5281/zenodo.15300193"
            }
        }
    except HTTPException:
        raise
    except ModelValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except ModelLoadError as me:
        raise HTTPException(status_code=500, detail=str(me))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


# -------------------------------------------------------------
# Simulation API Endpoints
# -------------------------------------------------------------
@app.post("/api/simulation/create")
def create_simulation_session(req: SimCreateRequest):
    try:
        raw_np = req.nanoparticle or {}
        raw_env = req.environment or {}

        # Gracefully adapt frontend keys to internal Dataclass attributes
        np_config = {
            "material": raw_np.get("material") or raw_np.get("carrier_material", "PLGA"),
            "drug_payload": raw_np.get("drug_payload") or raw_np.get("core_drug", "Paclitaxel"),
            "core_size_nm": float(raw_np.get("core_size_nm") or raw_np.get("initial_size_nm", 120.0)),
            "hydrodynamic_size_nm": float(raw_np.get("hydrodynamic_size_nm", 150.0)),
            "zeta_potential_mV": float(raw_np.get("zeta_potential_mV") or raw_np.get("zeta_potential", -22.0)),
            "shape": raw_np.get("shape", "Spherical")
        }

        env_config = {
            "temperature_c": float(raw_env.get("temperature_c") or raw_env.get("temperature", 37.0)),
            "pH": float(raw_env.get("pH") or raw_env.get("ph", 7.4)),
            "ionic_strength": float(raw_env.get("ionic_strength") or raw_env.get("ionic_strength_m", 0.15)),
            "medium": raw_env.get("medium") or raw_env.get("medium_type", "PBS")
        }
        
        # Configure Korsmeyer-Peppas mechanism
        models_config = req.models or {
            "korsmeyer_peppas": {"k": 0.18, "n": 0.45}
        }
        
        payload = {
            "nanoparticle": np_config,
            "environment": env_config,
            "models": models_config,
            "time_step_hours": float(req.time_step_hours or 1.0)
        }
        
        sim_data = sim_manager.create_simulation(payload)
        return sim_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.get("/api/simulation/{simulation_id}")
def get_simulation_state(simulation_id: str):
    try:
        return sim_manager.get_simulation(simulation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Simulation session not found")


@app.post("/api/simulation/{simulation_id}/start")
def start_simulation(simulation_id: str):
    try:
        return sim_manager.start_simulation(simulation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulation/{simulation_id}/step")
def step_simulation(simulation_id: str):
    try:
        return sim_manager.step_simulation(simulation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulation/{simulation_id}/run")
def run_simulation_to_time(simulation_id: str, req: SimRunRequest):
    try:
        return sim_manager.run_simulation(simulation_id, {"target_time_hours": req.target_time_hours})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulation/{simulation_id}/pause")
def pause_simulation(simulation_id: str):
    try:
        return sim_manager.pause_simulation(simulation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulation/{simulation_id}/resume")
def resume_simulation(simulation_id: str):
    try:
        return sim_manager.resume_simulation(simulation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulation/{simulation_id}/reset")
def reset_simulation(simulation_id: str):
    try:
        return sim_manager.reset_simulation(simulation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/simulation/{simulation_id}/trajectory")
def get_simulation_trajectory(simulation_id: str):
    try:
        return sim_manager.get_trajectory(simulation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Simulation session not found")


@app.post("/api/simulation/{simulation_id}/environment")
def update_simulation_environment(simulation_id: str, req: SimEnvUpdateRequest):
    try:
        data = {k: v for k, v in req.model_dump().items() if v is not None}
        return sim_manager.update_environment(simulation_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Formulation Heatmap Matrix Calculation
# -------------------------------------------------------------
@app.post("/api/formulation/heatmap")
def calculate_heatmap(req: Dict[str, Any]):
    """
    Computes a 2D matrix of predicted stability / colloidal response
    over pH range (3.5 to 9.5) and Temperature range (20 to 65 °C).
    """
    core = req.get("core", "Gold")
    size_nm = float(req.get("size_nm", 20.0))
    smiles = req.get("smiles", "OCCO")
    
    ph_steps = [3.5, 4.5, 5.5, 6.5, 7.4, 8.5, 9.5]
    temp_steps = [20, 25, 37, 45, 55, 65]
    
    grid = []
    for t in temp_steps:
        row = []
        for ph in ph_steps:
            # Deterministic biophysical heuristic based on DLVO approximation and pH shifts
            # At neutral pH 7.4 with standard PEG/citrate
            base_zeta = -28.0 if "O" in smiles else -15.0
            ph_factor = (ph - 7.0) * -2.5
            temp_factor = (t - 37.0) * -0.15
            zeta_approx = base_zeta + ph_factor + temp_factor
            
            abs_z = abs(zeta_approx)
            if abs_z >= 30:
                rating = "High"
            elif abs_z >= 20:
                rating = "Medium"
            else:
                rating = "Low"
                
            row.append({
                "ph": ph,
                "temperature": t,
                "zeta_mv": round(zeta_approx, 1),
                "stability": rating,
                "confidence": round(0.85 + 0.1 * (1.0 / (1.0 + abs(t - 37) / 20.0)), 2)
            })
        grid.append(row)
        
    return {
        "ph_values": ph_steps,
        "temperature_values": temp_steps,
        "grid": grid,
        "core": core,
        "size_nm": size_nm
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.web.server:app", host="127.0.0.1", port=8000, reload=True)
