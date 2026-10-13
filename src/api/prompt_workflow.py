import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.predict import (
    _estimate_mw,
    _extract_charge,
    get_cytotoxicity_model,
    get_stability_model,
    predict_cytotoxicity,
    predict_stability,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STABILITY_PATH = PROJECT_ROOT / "data" / "processed" / "stability_combined_engineered.csv"
CYTOTOXICITY_PATH = PROJECT_ROOT / "data" / "raw" / "cytotoxicity_meta_analysis.xlsx"
RELEASE_PATH = PROJECT_ROOT / "data" / "processed" / "drug_release_longitudinal.csv"

RELEASE_NUMERIC = [
    "particle_size_nm",
    "drug_mw",
    "drug_loading_pct",
    "polymer_mw",
    "la_ga_ratio",
    "time_hours",
]
RELEASE_CATEGORICAL = ["drug_name", "polymer"]
RELEASE_FEATURES = RELEASE_NUMERIC + RELEASE_CATEGORICAL


def _number(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return float(match.group(1).replace(",", "")) if match else None


def _matched_choice(text: str, options: list[str]) -> str | None:
    for option in sorted(options, key=len, reverse=True):
        if re.search(r"(?<![a-z0-9])" + re.escape(option) + r"(?![a-z0-9])", text, re.IGNORECASE):
            return option
    return None


def parse_experiment_prompt(prompt: str) -> dict[str, Any]:
    text = prompt.strip()
    duration_matches = list(re.finditer(
        r"(-?\d+(?:\.\d+)?)\s*(hours?|hrs?|h|days?|d|weeks?|w)\b",
        text,
        flags=re.IGNORECASE,
    ))

    def hours(match: re.Match[str] | None) -> float | None:
        if match is None:
            return None
        amount = float(match.group(1))
        unit = match.group(2).lower()[0]
        return amount * {"h": 1.0, "d": 24.0, "w": 168.0}[unit]

    simulation_match = next(
        (
            match
            for match in duration_matches
            if re.search(r"\b(simulat\w*|run)\b", text[max(0, match.start() - 24):match.start()], re.IGNORECASE)
        ),
        duration_matches[-1] if duration_matches else None,
    )
    exposure_match = next(
        (
            match
            for match in duration_matches
            if re.search(r"\b(exposure|expose)\b", text[max(0, match.start() - 28):match.end() + 20], re.IGNORECASE)
        ),
        None,
    )

    loading_pct = _number(r"(-?\d+(?:\.\d+)?)\s*%\s*(?:drug\s*)?loading", text)
    if loading_pct is None:
        loading_pct = _number(r"(-?\d+(?:\.\d+)?)\s*%", text)
    hydrodynamic_size = _number(r"(?:hydro(?:dynamic)?|dls)\s*(?:size)?\s*[:=]?\s*(-?\d+(?:\.\d+)?)\s*nm\b", text)
    if hydrodynamic_size is None:
        hydrodynamic_size = _number(r"(-?\d+(?:\.\d+)?)\s*nm\s*(?:hydro(?:dynamic)?|dls)(?:\s*size)?\b", text)

    parsed = {
        "size_nm": _number(r"(-?\d+(?:\.\d+)?)\s*nm\b", text),
        "hydrodynamic_size_nm": hydrodynamic_size,
        "surface_area_m2_g": _number(r"surface\s*area\s*[:=]?\s*(-?[\d,]+(?:\.\d+)?)\s*(?:m2/g|m²/g)", text),
        "drug_mw": _number(r"drug\s*(?:mw|molecular\s*weight)\s*[:=]?\s*([\d,]+(?:\.\d+)?)", text),
        "polymer_mw": _number(r"polymer\s*(?:mw|molecular\s*weight)\s*[:=]?\s*([\d,]+(?:\.\d+)?)", text),
        "la_ga_ratio": _number(r"\b(?:la\s*[:/]\s*ga|la\s*[-/]?\s*ga\s+ratio)\s*(?:ratio)?\s*[:=]?\s*([\d,]+(?:\.\d+)?)", text),
        "zeta_mv": _number(r"(-?\d+(?:\.\d+)?)\s*m\s*v\b", text),
        "ph": _number(r"\bp\s*h\s*(-?\d+(?:\.\d+)?)", text),
        "temperature_c": _number(r"(-?\d+(?:\.\d+)?)\s*(?:°\s*c|degrees?\s*c(?:elsius)?|celsius|c)\b", text),
        "dose_ug_ml": _number(r"(-?\d+(?:\.\d+)?)\s*[uµμ]g\s*/\s*ml\b", text),
        "duration_hours": hours(simulation_match),
        "exposure_hours": hours(exposure_match),
        "drug_loading_pct": loading_pct,
        "shape": "rod-like" if re.search(r"\brod(?:-like)?\b", text, re.IGNORECASE) else None,
        "prompt": text,
    }
    if parsed["size_nm"] is not None and parsed["size_nm"] <= 0:
        raise ValueError("Particle size must be greater than zero.")
    if parsed["hydrodynamic_size_nm"] is not None and parsed["hydrodynamic_size_nm"] <= 0:
        raise ValueError("Hydrodynamic size must be greater than zero.")
    if parsed["surface_area_m2_g"] is not None and parsed["surface_area_m2_g"] <= 0:
        raise ValueError("Surface area must be greater than zero.")
    if parsed["drug_mw"] is not None and parsed["drug_mw"] <= 0:
        raise ValueError("Drug molecular weight must be greater than zero.")
    if parsed["polymer_mw"] is not None and parsed["polymer_mw"] <= 0:
        raise ValueError("Polymer molecular weight must be greater than zero.")
    if parsed["la_ga_ratio"] is not None and parsed["la_ga_ratio"] < 0:
        raise ValueError("LA:GA ratio cannot be negative.")
    if parsed["ph"] is not None and not 0 <= parsed["ph"] <= 14:
        raise ValueError("pH must be between 0 and 14.")
    if parsed["temperature_c"] is not None and parsed["temperature_c"] <= -273.15:
        raise ValueError("Temperature cannot be at or below absolute zero.")
    if parsed["dose_ug_ml"] is not None and parsed["dose_ug_ml"] < 0:
        raise ValueError("Dose cannot be negative.")
    if loading_pct is not None and loading_pct < 0:
        raise ValueError("Drug loading cannot be negative.")
    if parsed["duration_hours"] is not None and parsed["duration_hours"] <= 0:
        raise ValueError("Simulation duration must be greater than zero.")
    if parsed["exposure_hours"] is not None and parsed["exposure_hours"] <= 0:
        raise ValueError("Exposure time must be greater than zero.")
    return parsed


def _pipeline(numeric: list[str], categorical: list[str], estimator: Any) -> Pipeline:
    return Pipeline(
        [
            (
                "preprocessor",
                ColumnTransformer(
                    [
                        (
                            "numeric",
                            Pipeline(
                                [
                                    ("imputer", SimpleImputer(strategy="median")),
                                    ("scaler", StandardScaler()),
                                ]
                            ),
                            numeric,
                        ),
                        (
                            "categorical",
                            Pipeline(
                                [
                                    ("imputer", SimpleImputer(strategy="most_frequent")),
                                    ("encoder", OneHotEncoder(handle_unknown="ignore")),
                                ]
                            ),
                            categorical,
                        ),
                    ],
                    sparse_threshold=0,
                ),
            ),
            ("model", estimator),
        ]
    )


def _cv_splitter(groups: pd.Series) -> GroupKFold:
    count = int(groups.nunique())
    if count < 2:
        raise ValueError("At least two independent groups are required for grouped validation.")
    return GroupKFold(n_splits=min(5, count))


@lru_cache(maxsize=2)
def _training_frame(dataset: str) -> pd.DataFrame:
    path = STABILITY_PATH if dataset == "stability" else CYTOTOXICITY_PATH
    return pd.read_csv(path) if path.suffix == ".csv" else pd.read_excel(path)


def get_model_domains() -> dict[str, Any]:
    stability = _training_frame("stability")
    toxicity = _training_frame("cytotoxicity")
    release = pd.read_csv(RELEASE_PATH).dropna(
        subset=RELEASE_FEATURES + ["cumulative_release_pct", "trajectory_id"]
    )
    toxicity_numeric = [
        "Core size (nm)",
        "Hydro size (nm)",
        "Surface charge (mV)",
        "Surface area (m2/g)",
        "Exposure time",
        "Mass dose (ug/mL)",
    ]

    def ranges(frame: pd.DataFrame, columns: list[str]) -> dict[str, list[float]]:
        return {
            column: [float(frame[column].min()), float(frame[column].max())]
            for column in columns
        }

    def categories(frame: pd.DataFrame, columns: list[str]) -> dict[str, list[str]]:
        return {
            column: sorted(frame[column].dropna().astype(str).unique().tolist())
            for column in columns
        }

    def category_modes(frame: pd.DataFrame, columns: list[str]) -> dict[str, str]:
        return {column: str(frame[column].dropna().mode().iloc[0]) for column in columns}

    return {
        "stability": {
            "source": str(STABILITY_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "rows": int(len(stability)),
            "numeric_ranges": {
                "Size_nm": [float(stability["Size (nm)"].min()), float(stability["Size (nm)"].max())],
                "Estimated_Ligand_MW": [float(stability["Estimated_Ligand_MW"].min()), float(stability["Estimated_Ligand_MW"].max())],
            },
            "numeric_medians": {
                "Size_nm": float(stability["Size (nm)"].median()),
                "Estimated_Ligand_MW": float(stability["Estimated_Ligand_MW"].median()),
            },
            "categories": categories(stability, ["Shape", "Core", "Medium", "Coating_Charge"]),
            "category_modes": category_modes(stability, ["Shape", "Core", "Medium", "Coating_Charge"]),
        },
        "cytotoxicity": {
            "source": str(CYTOTOXICITY_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "rows": int(len(toxicity)),
            "numeric_ranges": ranges(toxicity, toxicity_numeric),
            "numeric_medians": {column: float(toxicity[column].median()) for column in toxicity_numeric},
            "categories": categories(toxicity, ["Material type", "Assay", "Cell name"]),
            "category_modes": category_modes(toxicity, ["Material type", "Assay", "Cell name"]),
        },
        "drug_release": {
            "source": str(RELEASE_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "rows": int(len(release)),
            "numeric_ranges": ranges(release, RELEASE_NUMERIC),
            "numeric_medians": {column: float(release[column].median()) for column in RELEASE_NUMERIC},
            "categories": {
                "drug_name": (
                    sorted(list(set(
                        (pd.read_csv(RELEASE_PATH)["drug_name"].dropna().astype(str).str.strip().tolist() if RELEASE_PATH.is_file() else [])
                        + (pd.read_csv(PROJECT_ROOT / "data" / "nano_drug" / "nano_drug_training_dataset.csv")["drug_name"].dropna().astype(str).str.strip().tolist() if (PROJECT_ROOT / "data" / "nano_drug" / "nano_drug_training_dataset.csv").is_file() else [])
                    )))
                ),
                "polymer": categories(release, ["polymer"])["polymer"],
            },
            "drug_mw_map": {
                **({
                    row["drug_name"].strip(): round(float(row["molecular_weight_g_mol"]), 2)
                    for _, row in pd.read_csv(PROJECT_ROOT / "data" / "nano_drug" / "nano_drug_training_dataset.csv").dropna(subset=["drug_name", "molecular_weight_g_mol"]).iterrows()
                    if str(row["drug_name"]).strip()
                } if (PROJECT_ROOT / "data" / "nano_drug" / "nano_drug_training_dataset.csv").is_file() else {}),
                **({
                    row["drug_name"].strip(): round(float(row["drug_mw"]), 2)
                    for _, row in pd.read_csv(RELEASE_PATH).dropna(subset=["drug_name", "drug_mw"]).iterrows()
                    if str(row["drug_name"]).strip()
                } if RELEASE_PATH.is_file() else {}),
            },
            "unsupported_columns": [
                "hydrodynamic_size_nm",
                "pdi",
                "zeta_potential_mv",
                "encapsulation_efficiency_pct",
                "temperature_c",
                "pH",
                "ionic_strength_m",
                "surfactant_pct",
            ],
        },
    }


def check_model_domain(task: str, features: dict[str, Any]) -> list[dict[str, Any]]:
    domain = get_model_domains()[task]
    numeric_values: dict[str, float] = {}
    categorical_values: dict[str, str] = {}
    if task == "stability":
        numeric_values = {
            "Size_nm": float(features["Size_nm"]),
            "Estimated_Ligand_MW": _estimate_mw(features["Ligand_SMILES"]),
        }
        categorical_values = {
            "Shape": str(features["Shape"]),
            "Core": str(features["Core"]),
            "Medium": str(features["Medium"]),
            "Coating_Charge": _extract_charge(features["Ligand_SMILES"]),
        }
    elif task == "cytotoxicity":
        numeric_values = {
            column: float(features[column]) for column in domain["numeric_ranges"]
        }
        categorical_values = {
            column: str(features[column]) for column in domain["categories"]
        }
    else:
        raise ValueError(f"Unknown model domain: {task}")

    warnings = []
    for column, value in numeric_values.items():
        lower, upper = domain["numeric_ranges"][column]
        tolerance = max(1e-9, abs(lower) * 1e-9, abs(upper) * 1e-9)
        if value < lower - tolerance or value > upper + tolerance:
            warnings.append(
                {
                    "field": column,
                    "value": value,
                    "reason": "outside_training_range",
                    "supported_range": [lower, upper],
                }
            )
    for column, value in categorical_values.items():
        supported = domain["categories"][column]
        if value not in supported:
            warnings.append(
                {
                    "field": column,
                    "value": value,
                    "reason": "unsupported_category",
                    "supported_categories": supported,
                }
            )
    return warnings


@lru_cache(maxsize=1)
def get_model_registry() -> dict[str, Any]:
    domains = get_model_domains()
    audits = _model_audits()
    release = _release_bundle()
    return {
        "models": [
            {
                "model_name": "NanoMedAI Stability Model",
                "model_version": "1.0",
                "target": "zeta_potential",
                "training_dataset": domains["stability"]["source"],
                "training_size": domains["stability"]["rows"],
                "features": ["Shape", "Core", "Size_nm", "Medium", "Ligand_SMILES"],
                "validation_method": audits["stability"]["validation"],
                "metrics": audits["stability"]["metrics"],
                "supported_ranges": domains["stability"]["numeric_ranges"],
                "supported_categories": domains["stability"]["categories"],
                "status": "research_prototype",
                "limitations": ["Limited predictive strength; proof-of-concept only.", "Not a clinical prediction."],
            },
            {
                "model_name": "NanoMedAI Cytotoxicity Classifier",
                "model_version": "1.0",
                "target": "toxicity_class",
                "training_dataset": domains["cytotoxicity"]["source"],
                "training_size": domains["cytotoxicity"]["rows"],
                "features": list(domains["cytotoxicity"]["numeric_ranges"]) + list(domains["cytotoxicity"]["categories"]),
                "validation_method": audits["cytotoxicity"]["validation"],
                "metrics": audits["cytotoxicity"]["metrics"],
                "supported_ranges": domains["cytotoxicity"]["numeric_ranges"],
                "supported_categories": domains["cytotoxicity"]["categories"],
                "status": "research_prototype",
                "limitations": ["Moderate cross-study performance; assay-specific classification only.", "Not evidence of clinical safety."],
            },
            {
                "model_name": "NanoMedAI Learned Drug Release Model",
                "model_version": "0.1",
                "target": "cumulative_release_pct",
                "training_dataset": release["source"],
                "training_size": release["metrics"]["rows"],
                "features": RELEASE_FEATURES,
                "validation_method": release["metrics"]["validation"],
                "metrics": {
                    "MAE_release_percentage_points": release["metrics"]["MAE_release_percentage_points"],
                    "R2": release["metrics"]["R2"],
                },
                "supported_ranges": release["ranges"],
                "supported_categories": release["categories"],
                "status": "research_prototype",
                "limitations": ["Environmental response is unsupported.", "Tree spread is not a calibrated confidence interval."],
            },
        ]
    }


@lru_cache(maxsize=1)
def _model_audits() -> dict[str, Any]:
    stability = _training_frame("stability")
    stability = stability.dropna(
        subset=[
            "Shape",
            "Core",
            "Size (nm)",
            "Medium",
            "Coating_Charge",
            "Estimated_Ligand_MW",
            "Zeta_mV",
            "study_id",
        ]
    )
    stability_categorical = ["Shape", "Core", "Medium", "Coating_Charge"]
    stability_numeric = ["Log_Size", "Estimated_Ligand_MW"]
    stability_x = stability[stability_categorical + stability_numeric]
    stability_y = stability["Zeta_mV"]
    stability_pipe = Pipeline(
        [
            (
                "preprocessor",
                ColumnTransformer(
                    [
                        ("numeric", StandardScaler(), stability_numeric),
                        (
                            "categorical",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                            stability_categorical,
                        ),
                    ]
                ),
            ),
            ("model", Ridge(alpha=10.0, random_state=42)),
        ]
    )
    stability_cv = _cv_splitter(stability["study_id"])
    stability_scores = cross_validate(
        stability_pipe,
        stability_x,
        stability_y,
        groups=stability["study_id"],
        cv=stability_cv,
        scoring=["r2", "neg_mean_absolute_error", "neg_root_mean_squared_error"],
    )

    toxicity = _training_frame("cytotoxicity")
    toxicity_categorical = ["Material type", "Assay", "Cell name"]
    toxicity_numeric = [
        "Core size (nm)",
        "Hydro size (nm)",
        "Surface charge (mV)",
        "Surface area (m2/g)",
        "Exposure time",
        "Mass dose (ug/mL)",
    ]
    toxicity_x = toxicity[toxicity_categorical + toxicity_numeric]
    toxicity_y = (toxicity["Toxicity"] == "Toxic").astype(int)
    toxicity_pipe = Pipeline(
        [
            (
                "preprocessor",
                ColumnTransformer(
                    [
                        ("numeric", StandardScaler(), toxicity_numeric),
                        (
                            "categorical",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                            toxicity_categorical,
                        ),
                    ]
                ),
            ),
            ("model", RandomForestClassifier(random_state=42, n_estimators=100)),
        ]
    )
    toxicity_groups = toxicity["Pubmed ID"].astype(str)
    toxicity_cv = _cv_splitter(toxicity_groups)
    toxicity_scores = cross_validate(
        toxicity_pipe,
        toxicity_x,
        toxicity_y,
        groups=toxicity_groups,
        cv=toxicity_cv,
        scoring=["accuracy", "precision", "recall", "f1"],
        error_score="raise",
    )

    return {
        "stability": {
            "validation": "GroupKFold by study_id",
            "groups": int(stability["study_id"].nunique()),
            "rows": len(stability),
            "metrics": {
                "R2": float(np.mean(stability_scores["test_r2"])),
                "MAE_mV": float(-np.mean(stability_scores["test_neg_mean_absolute_error"])),
                "RMSE_mV": float(-np.mean(stability_scores["test_neg_root_mean_squared_error"])),
            },
        },
        "cytotoxicity": {
            "validation": "GroupKFold by Pubmed ID",
            "groups": int(toxicity_groups.nunique()),
            "rows": len(toxicity),
            "metrics": {
                metric.upper(): float(np.mean(toxicity_scores[f"test_{metric}"]))
                for metric in ("accuracy", "precision", "recall", "f1")
            },
        },
    }


@lru_cache(maxsize=1)
def _release_bundle() -> dict[str, Any]:
    frame = pd.read_csv(RELEASE_PATH)
    required = RELEASE_FEATURES + ["cumulative_release_pct", "trajectory_id"]
    frame = frame.dropna(subset=required).copy()
    if frame["trajectory_id"].nunique() < 2:
        raise ValueError("The release dataset needs at least two trajectories for validation.")

    for column in RELEASE_CATEGORICAL:
        frame[column] = frame[column].astype(str)
    x = frame[RELEASE_FEATURES]
    y = frame["cumulative_release_pct"].astype(float)
    groups = frame["trajectory_id"].astype(str)
    cv = _cv_splitter(groups)
    estimator = RandomForestRegressor(
        n_estimators=80,
        min_samples_leaf=2,
        random_state=7,
        # Keep API metrics available in restricted Windows worker processes.
        n_jobs=1,
    )
    pipeline = _pipeline(RELEASE_NUMERIC, RELEASE_CATEGORICAL, estimator)
    out_of_fold = cross_val_predict(pipeline, x, y, groups=groups, cv=cv)
    pipeline.fit(x, y)

    return {
        "frame": frame,
        "pipeline": pipeline,
        "modes": {column: str(frame[column].mode().iloc[0]) for column in RELEASE_CATEGORICAL},
        "medians": {column: float(frame[column].median()) for column in RELEASE_NUMERIC},
        "ranges": {
            column: [float(frame[column].min()), float(frame[column].max())]
            for column in RELEASE_NUMERIC
        },
        "categories": {column: sorted(frame[column].unique().tolist()) for column in RELEASE_CATEGORICAL},
        "metrics": {
            "MAE_release_percentage_points": float(mean_absolute_error(y, out_of_fold)),
            "R2": float(r2_score(y, out_of_fold)),
            "validation": "GroupKFold by trajectory_id",
            "groups": int(groups.nunique()),
            "rows": len(frame),
        },
        "source": str(RELEASE_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }


def _training_baseline(dataset: str, categorical: list[str], numeric: list[str]) -> dict[str, Any]:
    frame = _training_frame(dataset)
    baseline = {column: frame[column].dropna().mode().iloc[0] for column in categorical}
    baseline.update({column: float(frame[column].median()) for column in numeric})
    return baseline


def _feature_drivers(
    model: Any,
    actual: pd.DataFrame,
    baseline: dict[str, Any],
    probability_class: int | None = None,
) -> dict[str, float]:
    def value(frame: pd.DataFrame) -> float:
        if probability_class is None:
            return float(model.predict(frame)[0])
        probabilities = model.predict_proba(frame)[0]
        classes = list(model.named_steps["model"].classes_)
        return float(probabilities[classes.index(probability_class)])

    actual_value = value(actual)
    drivers = {}
    for column in actual.columns:
        occluded = actual.copy()
        occluded.loc[:, column] = baseline[column]
        drivers[column] = actual_value - value(occluded)
    return drivers


def _choice_or_default(prompt: str, options: list[str], default: str) -> tuple[str, bool]:
    selected = _matched_choice(prompt, options)
    return (selected or default, selected is None)


def run_experiment_prompt(prompt: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("Describe an experiment before running the prompt workflow.")

    overrides = overrides or {}
    parsed = parse_experiment_prompt(prompt)
    audits = _model_audits()
    release = _release_bundle()

    stable_baseline = _training_baseline(
        "stability",
        ["Shape", "Core", "Medium", "Coating_Charge"],
        ["Log_Size", "Estimated_Ligand_MW"],
    )
    toxicity_baseline = _training_baseline(
        "cytotoxicity",
        ["Material type", "Assay", "Cell name"],
        [
            "Core size (nm)",
            "Hydro size (nm)",
            "Surface charge (mV)",
            "Surface area (m2/g)",
            "Exposure time",
            "Mass dose (ug/mL)",
        ],
    )

    medium_options = ["PBS pH 7.4", "Millipore Water"]
    override_medium = overrides.get("medium")
    medium_text = str(override_medium or prompt)
    if override_medium is not None and not re.search(r"\bpbs\b|\bwater\b", medium_text, re.IGNORECASE):
        raise ValueError(f"Unsupported medium '{medium_text}'. Supported values: {', '.join(medium_options)}.")
    if re.search(r"\b(biological fluid|biological medium|custom medium)\b", medium_text, re.IGNORECASE):
        raise ValueError(f"Unsupported medium in prompt. Supported values: {', '.join(medium_options)}.")
    if re.search(r"\bpbs\b", medium_text, re.IGNORECASE):
        medium, medium_assumed = "PBS pH 7.4", False
    elif re.search(r"\bwater\b", medium_text, re.IGNORECASE):
        medium, medium_assumed = "Millipore Water", False
    else:
        medium, medium_assumed = _choice_or_default(medium_text, medium_options, "PBS pH 7.4")
    stable_training = _training_frame("stability")
    stable_categories = get_model_domains()["stability"]["categories"]
    shape_value = overrides.get("shape") or parsed["shape"]
    shape = shape_value or str(stable_baseline["Shape"])
    if shape not in stable_categories["Shape"]:
        raise ValueError(f"Unsupported stability shape '{shape}'. Supported: {', '.join(stable_categories['Shape'])}.")
    core_value = overrides.get("core")
    if core_value is not None and core_value not in stable_categories["Core"]:
        raise ValueError(f"Unsupported stability core '{core_value}'. Supported: {', '.join(stable_categories['Core'])}.")
    core, core_assumed = (core_value, False) if core_value else _choice_or_default(
        prompt, stable_categories["Core"], str(stable_baseline["Core"])
    )

    preset_smiles = {
        "citrate": "C(C(C(=O)O)O)(C(=O)O)O",
        "citric": "C(C(C(=O)O)O)(C(=O)O)O",
        "peg": "OCCO",
        "polyethylene glycol": "OCCO",
        "chitosan": "C1C(C(C(C(O1)CO)O)N)O",
        "pvp": "C1CC(=O)N(C1)C=C",
        "oleic": "CCCCCCCC=CCCCCCCCC(=O)O",
        "cysteamine": "C(CS)N",
        "betaine": "C[N+](C)(C)CC(=O)[O-]",
    }
    ligand_smiles = overrides.get("ligand_smiles") or next((smiles for key, smiles in preset_smiles.items() if key in prompt.lower()), None)
    ligand_assumed = ligand_smiles is None
    if ligand_smiles is None:
        ligand_smiles = "C(C(C(=O)O)O)(C(=O)O)O"
    requested_size_nm = overrides.get("core_size_nm", parsed["size_nm"])
    size_nm = float(requested_size_nm) if requested_size_nm is not None else float(stable_training["Size (nm)"].median())
    stability_inputs = {
        "Shape": shape,
        "Core": core,
        "Size_nm": float(size_nm),
        "Medium": medium,
        "Ligand_SMILES": ligand_smiles,
    }
    stability_domain = check_model_domain("stability", stability_inputs)
    stability_result = None
    actual_stability_model_input = pd.DataFrame(
        [
            {
                "Shape": stability_inputs["Shape"],
                "Core": stability_inputs["Core"],
                "Medium": stability_inputs["Medium"],
                "Coating_Charge": _extract_charge(ligand_smiles),
                "Log_Size": float(np.log1p(size_nm)),
                "Estimated_Ligand_MW": _estimate_mw(ligand_smiles),
            }
        ]
    )
    stability_drivers = {}
    if not stability_domain:
        stability_result = predict_stability(stability_inputs)
        absolute_zeta = abs(stability_result["prediction"])
        if absolute_zeta >= 30:
            stability_class = "Highly Stable"
            stability_description = "Strong electrostatic repulsion is predicted (|zeta| >= 30 mV)."
        elif absolute_zeta >= 20:
            stability_class = "Moderately Stable"
            stability_description = "Moderate charge magnitude; aggregation may occur in high ionic strength media."
        else:
            stability_class = "Unstable / Aggregation-Prone"
            stability_description = "Low charge magnitude; aggregation may occur without steric stabilization."
        stability_result.update(
            {
                "stability_class": stability_class,
                "stability_desc": stability_description,
                "engineered_features": {
                    "detected_charge": _extract_charge(ligand_smiles),
                    "estimated_ligand_mw_da": round(_estimate_mw(ligand_smiles), 2),
                    "log_size": round(float(np.log1p(size_nm)), 2),
                },
                "model_metadata": {
                    "model_type": "Ridge / Random Forest Regressor",
                    "validation": "GroupKFold by study_id",
                    "dataset_size": "288 harmonized nanoparticles",
                },
                "applicability": "inside_domain",
                "confidence": "Low" if audits["stability"]["metrics"]["R2"] < .5 else "Moderate",
                "validation_metrics": audits["stability"]["metrics"],
            }
        )
        stability_drivers = _feature_drivers(
            get_stability_model(), actual_stability_model_input, stable_baseline
        )

    toxicity_categories = get_model_domains()["cytotoxicity"]["categories"]
    material = overrides.get("material_type") or _matched_choice(prompt, toxicity_categories["Material type"])
    assay = overrides.get("assay") or _matched_choice(prompt, toxicity_categories["Assay"])
    cell_name = overrides.get("cell_name") or _matched_choice(prompt, toxicity_categories["Cell name"])
    for field_name, value, options in (
        ("material type", material, toxicity_categories["Material type"]),
        ("assay", assay, toxicity_categories["Assay"]),
        ("cell line", cell_name, toxicity_categories["Cell name"]),
    ):
        if value is not None and value not in options:
            raise ValueError(f"Unsupported {field_name} '{value}'. Supported values: {', '.join(options)}.")
    hydrodynamic_size_nm = overrides.get("hydrodynamic_size_nm", parsed["hydrodynamic_size_nm"])
    surface_area_m2_g = overrides.get("surface_area_m2_g", parsed["surface_area_m2_g"])
    surface_charge_mv = overrides.get("surface_charge_mv", parsed["zeta_mv"])
    exposure_time_hours = overrides.get("exposure_time_hours", parsed["exposure_hours"])
    mass_dose_ug_ml = overrides.get("mass_dose_ug_ml", parsed["dose_ug_ml"])
    toxicity_missing = []
    if material is None:
        toxicity_missing.append("supported material type")
    if requested_size_nm is None:
        toxicity_missing.append("core size")
    if hydrodynamic_size_nm is None:
        toxicity_missing.append("hydrodynamic size")
    if surface_area_m2_g is None:
        toxicity_missing.append("surface area")
    if mass_dose_ug_ml is None:
        toxicity_missing.append("dose")
    if exposure_time_hours is None:
        toxicity_missing.append("exposure time")
    if assay is None:
        toxicity_missing.append("assay")
    if cell_name is None:
        toxicity_missing.append("cell line")
    if surface_charge_mv is None and stability_result is None:
        toxicity_missing.append("surface charge (zeta) or in-domain stability result")

    toxicity_inputs = None
    toxicity_result = None
    toxicity_drivers = {}
    toxicity_domain = []
    toxicity_status = "not_run"
    if not toxicity_missing:
        toxicity_inputs = {
            "Material type": material,
            "Core size (nm)": float(requested_size_nm),
            "Hydro size (nm)": float(hydrodynamic_size_nm),
            "Surface charge (mV)": float(surface_charge_mv if surface_charge_mv is not None else stability_result["prediction"]),
            "Surface area (m2/g)": float(surface_area_m2_g),
            "Exposure time": float(exposure_time_hours),
            "Mass dose (ug/mL)": float(mass_dose_ug_ml),
            "Assay": assay,
            "Cell name": cell_name,
        }
        toxicity_domain = check_model_domain("cytotoxicity", toxicity_inputs)
        if toxicity_domain:
            toxicity_status = "outside_domain"
        else:
            toxicity_result = predict_cytotoxicity(dict(toxicity_inputs))
            is_toxic = toxicity_result["prediction"] == "Toxic"
            dose = toxicity_inputs["Mass dose (ug/mL)"]
            toxicity_result.update(
                {
                    "is_toxic": is_toxic,
                    "risk_level": "High Risk" if is_toxic and dose >= 50 else "Moderate Risk" if is_toxic else "Low Risk",
                    "interpretation": (
                        f"Under {toxicity_inputs['Assay']} conditions at {dose:g} ug/mL on "
                        f"{toxicity_inputs['Cell name']}, {toxicity_inputs['Material type']} is classified as "
                        f"{toxicity_result['prediction']}."
                    ),
                    "model_metadata": {
                        "model_type": "Random Forest Classifier",
                        "validation": audits["cytotoxicity"]["validation"],
                    },
                    "validation_metrics": audits["cytotoxicity"]["metrics"],
                    "model_vote_confidence": toxicity_result.get("confidence"),
                    "confidence": "Moderate" if audits["cytotoxicity"]["metrics"]["F1"] >= .4 else "Low",
                    "probability_calibrated": False,
                    "applicability": "inside_domain",
                    "input_provenance": {
                        "Core size (nm)": "user supplied",
                        "Hydro size (nm)": "user supplied",
                        "Surface area (m2/g)": overrides.get("surface_area_source", "user supplied; measurement/estimate source unspecified"),
                        "Surface charge (mV)": "user supplied" if surface_charge_mv is not None else "predicted by in-domain stability model",
                    },
                }
            )
            toxicity_model_input = pd.DataFrame([toxicity_inputs])
            toxicity_drivers = _feature_drivers(
                get_cytotoxicity_model(),
                toxicity_model_input,
                toxicity_baseline,
                probability_class=1,
            )
            toxicity_status = "ready"

    drug_aliases = {
        "PTX": ("paclitaxel", "ptx"),
        "LTZ": ("letrozole", "ltz"),
        "RIF": ("rifampicin", "rifampin", "rif"),
    }
    requested_drug = overrides.get("drug_name")
    drug_name = requested_drug if (requested_drug is not None and str(requested_drug).strip() != "") else release["modes"]["drug_name"]
    drug_assumed = (requested_drug is None or str(requested_drug).strip() == "")

    if drug_assumed:
        for code, aliases in drug_aliases.items():
            if code in release["categories"]["drug_name"] and any(re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", prompt, re.IGNORECASE) for alias in aliases):
                drug_name = code
                drug_assumed = False
                break
        if drug_assumed:
            for code in release["categories"]["drug_name"]:
                if re.search(r"(?<![a-z0-9])" + re.escape(code) + r"(?![a-z0-9])", prompt, re.IGNORECASE):
                    drug_name = code
                    drug_assumed = False
                    break

    if drug_name not in release["categories"]["drug_name"]:
        raise ValueError(f"Unsupported release drug '{drug_name}'. Supported values: {', '.join(release['categories']['drug_name'])}.")
    polymer = overrides.get("release_polymer") or _matched_choice(prompt, release["categories"]["polymer"])
    polymer_assumed = polymer is None
    polymer = polymer or release["modes"]["polymer"]
    if polymer not in release["categories"]["polymer"]:
        raise ValueError(f"Unsupported release polymer '{polymer}'. Supported values: {', '.join(release['categories']['polymer'])}.")

    numeric_ranges = release["ranges"]
    loading_value = overrides.get("drug_loading_pct", parsed["drug_loading_pct"])
    loading_assumed = loading_value is None
    if loading_value is None:
        loading_value = release["medians"]["drug_loading_pct"]

    matching_formulations = release["frame"]
    if drug_name in release["categories"]["drug_name"] and polymer in release["categories"]["polymer"]:
        matching_formulations = matching_formulations[
            (matching_formulations["drug_name"] == drug_name)
            & (matching_formulations["polymer"] == polymer)
        ]
    formulation_pair_supported = not matching_formulations.empty

    def release_feature_value(column: str, prompt_value: float | None) -> float:
        override_value = overrides.get(column)
        if override_value is not None:
            return float(override_value)
        if prompt_value is not None:
            return float(prompt_value)
        if column == "drug_mw" and drug_name in release.get("drug_mw_map", {}):
            return float(release["drug_mw_map"][drug_name])
        source = matching_formulations if formulation_pair_supported else release["frame"]
        return float(source[column].median())

    simulation_features = {
        "particle_size_nm": float(requested_size_nm if requested_size_nm is not None else release["medians"]["particle_size_nm"]),
        "drug_loading_pct": float(loading_value),
        "drug_mw": release_feature_value("drug_mw", parsed["drug_mw"]),
        "polymer_mw": release_feature_value("polymer_mw", parsed["polymer_mw"]),
        "la_ga_ratio": release_feature_value("la_ga_ratio", parsed["la_ga_ratio"]),
        "drug_name": drug_name,
        "polymer": polymer,
    }
    duration_hours = parsed["duration_hours"] or min(72.0, numeric_ranges["time_hours"][1])
    release_warnings = []
    release_missing = []
    if requested_size_nm is None:
        release_missing.append("particle size")
    if drug_assumed:
        release_missing.append("a drug represented in the release dataset")
    if polymer_assumed:
        release_missing.append("a polymer represented in the release dataset")
    if loading_assumed:
        release_missing.append("drug loading")

    for column in RELEASE_NUMERIC:
        value = duration_hours if column == "time_hours" else simulation_features[column]
        lower, upper = numeric_ranges[column]
        # Parsed decimal input and spreadsheet bounds can differ by a few
        # floating-point ulps; treat numerically equal endpoints as in-domain.
        below = value < lower and not np.isclose(value, lower, rtol=1e-9, atol=1e-9)
        above = value > upper and not np.isclose(value, upper, rtol=1e-9, atol=1e-9)
        if below or above:
            release_warnings.append(f"{column}={value:g} is outside the observed range [{lower:g}, {upper:g}].")
    for column in RELEASE_CATEGORICAL:
        value = simulation_features[column]
        if value not in release["categories"][column]:
            release_warnings.append(f"{column}='{value}' was not present in the release dataset.")
    if not formulation_pair_supported:
        release_warnings.append(f"Drug/polymer pair '{drug_name} + {polymer}' was not observed in release training data.")

    times = np.array([], dtype=float)
    predicted_release = np.array([], dtype=float)
    release_sd = np.array([], dtype=float)
    rate = np.array([], dtype=float)
    events = []
    release_drivers = {}
    end_prediction = None
    release_status = "not_run"
    if release_missing:
        release_warnings.append("Release model not run; missing " + ", ".join(release_missing) + ".")
    elif release_warnings:
        release_status = "outside_domain"
    else:
        times = np.linspace(0, duration_hours, 61)
        simulation_frame = pd.DataFrame(
            [{**simulation_features, "time_hours": float(time)} for time in times],
            columns=RELEASE_FEATURES,
        )
        trained_pipeline = release["pipeline"]
        transformed = trained_pipeline.named_steps["preprocessor"].transform(simulation_frame)
        forest = trained_pipeline.named_steps["model"]
        tree_predictions = np.vstack([tree.predict(transformed) for tree in forest.estimators_])
        predicted_release = np.clip(tree_predictions.mean(axis=0), 0, 100)
        predicted_release = np.maximum.accumulate(predicted_release)
        predicted_release[0] = 0.0
        release_sd = tree_predictions.std(axis=0)
        release_sd[0] = 0.0
        rate = np.gradient(predicted_release, times) if len(times) > 1 else np.zeros_like(predicted_release)
        release_status = "ready"
        if len(predicted_release) > 1 and predicted_release[1] >= 20:
            events.append({"time_hours": float(times[1]), "text": f"Early release reaches {predicted_release[1]:.0f}% in the first interval."})
        for threshold in (10, 25, 50, 90):
            crossing = np.flatnonzero(predicted_release >= threshold)
            if crossing.size:
                index = int(crossing[0])
                events.append({"time_hours": float(times[index]), "text": f"{threshold}% cumulative release reached."})

        release_baseline = {**release["modes"], **release["medians"]}
        end_input = pd.DataFrame([{**simulation_features, "time_hours": float(times[-1])}], columns=RELEASE_FEATURES)
        end_prediction = float(trained_pipeline.predict(end_input)[0])
        release_drivers = _feature_drivers(trained_pipeline, end_input, release_baseline)

    environment = {
        "temperature_c": overrides.get("temperature_c", parsed["temperature_c"]),
        "ph": overrides.get("ph", parsed["ph"]),
        "ionic_strength": overrides.get("ionic_strength"),
        "medium": overrides.get("medium") or (
            "PBS" if medium == "PBS pH 7.4" else "Water" if medium == "Millipore Water" else None
        ),
    }
    environment_changed = (
        environment["temperature_c"] is not None and float(environment["temperature_c"]) != 37.0
    ) or (environment["ph"] is not None and float(environment["ph"]) != 7.4) or (
        environment["ionic_strength"] is not None and float(environment["ionic_strength"]) != 0.15
    ) or (environment["medium"] not in (None, "PBS", "PBS pH 7.4"))
    if environment_changed:
        release_warnings.append(
            "Release model has no validated environmental response; changing pH, temperature, ionic strength, or medium does not change this curve."
        )

    assumptions = []
    if medium_assumed:
        assumptions.append(f"Medium defaulted to {medium}.")
    if core_assumed:
        assumptions.append(f"Core defaulted to {core}.")
    if parsed["size_nm"] is None:
        assumptions.append(f"Stability particle size defaulted to the training median ({size_nm:.2f} nm).")
    if parsed["shape"] is None:
        assumptions.append(f"Particle shape defaulted to the observed mode ({shape}).")
    if ligand_assumed:
        assumptions.append("Ligand defaulted to the citrate training-compatible preset.")
    if toxicity_missing:
        assumptions.append("Toxicity model not run; missing " + ", ".join(toxicity_missing) + ".")
    if parsed["zeta_mv"] is None and stability_result is not None and toxicity_result is not None:
        assumptions.append("Toxicity surface charge used the in-domain stability prediction.")
    if toxicity_status == "outside_domain":
        assumptions.append("Toxicity model not run because one or more inputs are outside its training domain.")
    if parsed["duration_hours"] is None:
        assumptions.append(f"Simulation duration defaulted to {duration_hours:g} hours.")
    if release_missing:
        assumptions.append("Drug release model not run; " + ", ".join(release_missing) + " required.")
    if release_status == "outside_domain":
        assumptions.append("Drug release model not run because inputs are outside its training domain.")

    stability_domain_messages = [
        f"{issue['field']}={issue['value']:g} is outside its supported range {issue['supported_range']}."
        if issue["reason"] == "outside_training_range"
        else f"{issue['field']}='{issue['value']}' is unsupported by the stability model."
        for issue in stability_domain
    ]
    toxicity_domain_messages = [
        f"{issue['field']}={issue['value']:g} is outside its supported range {issue['supported_range']}."
        if issue["reason"] == "outside_training_range"
        else f"{issue['field']}='{issue['value']}' is unsupported by the toxicity model."
        for issue in toxicity_domain
    ]

    return {
        "parsed": parsed,
        "environment": environment,
        "assumptions": assumptions,
        "stability": {
            "status": "ready" if stability_result is not None else "outside_domain",
            "inputs": stability_inputs,
            "result": stability_result,
            "drivers": stability_drivers,
            "domain_warnings": stability_domain_messages,
            "domain_issues": stability_domain,
            "cv": audits["stability"],
        },
        "toxicity": {
            "status": toxicity_status,
            "missing_inputs": toxicity_missing,
            "inputs": toxicity_inputs,
            "result": toxicity_result,
            "drivers": toxicity_drivers,
            "domain_warnings": toxicity_domain_messages,
            "domain_issues": toxicity_domain,
            "cv": audits["cytotoxicity"],
        },
        "simulation": {
            "status": release_status,
            "missing_inputs": release_missing,
            "time_hours": times.tolist(),
            "release_pct": predicted_release.tolist(),
            "sd_pct": release_sd.tolist(),
            "rate_pct_per_hour": rate.tolist(),
            "events": events,
            "features": simulation_features,
            "final_release_pct": float(np.clip(end_prediction, 0, 100)) if end_prediction is not None else None,
            "drivers": release_drivers,
            "domain_warnings": release_warnings,
            "cv": release["metrics"],
            "source": release["source"],
            "unit": "hours",
        },
    }
