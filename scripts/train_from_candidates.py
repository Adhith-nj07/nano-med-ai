"""Train NanoMedAI models directly from audited candidate datasets.

Follows group-aware validation, schema mapping, and independence rules:
- Zeta potential: Uses 288-row candidate (Millipore + PBS media, 32 study groups). Excludes 69-row candidate due to lack of medium, SMILES, and study grouping.
- Cytotoxicity: Uses 666-row MeOx IIIB candidate. Mapped to standard features and binary toxicity target. Excludes cell_viability_pct from features. Grouped by study_pubmed_id.
- Drug release: Uses 115-row longitudinal candidate. Grouped by trajectory_id. Evaluates and reports limitation of 9 trajectories.
"""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import GroupKFold, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.predict import _estimate_mw, _extract_charge

CANDIDATE_DIR = ROOT / "data" / "processed" / "public_data_candidates"
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_stability_from_candidate():
    print("=" * 60)
    print("TASK 1: TRAINING STABILITY (ZETA POTENTIAL) MODEL")
    cand_path = CANDIDATE_DIR / "zeta_potential_288_candidate.csv"
    if not cand_path.exists():
        cand_path = Path(r"C:\Users\User\Downloads\zeta_potential_288_candidate.csv")
    df = pd.read_csv(cand_path)
    print(f"Loaded {len(df)} candidate rows from {cand_path.name}")

    # Feature mapping and transformation
    df["Shape"] = df["shape"].astype(str)
    df["Core"] = df["core_material"].astype(str)
    df["Medium"] = df["measurement_medium"].astype(str)
    df["Coating_Charge"] = df["ligand1_smiles"].apply(_extract_charge)
    df["Estimated_Ligand_MW"] = df["ligand1_smiles"].apply(_estimate_mw)
    df["Log_Size"] = np.log1p(df["core_or_reported_size_nm"].astype(float))
    df["Zeta_mV"] = df["zeta_potential_mv"].astype(float)
    df["study_id"] = df["study_id"].astype(str)

    cat_cols = ["Shape", "Core", "Medium", "Coating_Charge"]
    num_cols = ["Log_Size", "Estimated_Ligand_MW"]
    target_col = "Zeta_mV"
    group_col = "study_id"

    X = df[cat_cols + num_cols]
    y = df[target_col]
    groups = df[group_col]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("model", Ridge(alpha=10.0, random_state=42)),
    ])

    cv = GroupKFold(n_splits=5)
    scoring = ["r2", "neg_mean_absolute_error", "neg_root_mean_squared_error"]
    res = cross_validate(pipe, X, y, groups=groups, cv=cv, scoring=scoring)

    mae = -float(np.mean(res["test_neg_mean_absolute_error"]))
    rmse = -float(np.mean(res["test_neg_root_mean_squared_error"]))
    r2 = float(np.mean(res["test_r2"]))

    print(f"Samples: {len(df)}, Groups ({group_col}): {groups.nunique()}")
    print(f"GroupKFold (5 splits) -> MAE: {mae:.2f} mV, RMSE: {rmse:.2f} mV, R²: {r2:.3f}")

    pipe.fit(X, y)
    out_path = MODELS_DIR / "stability_model_final.joblib"
    joblib.dump(pipe, out_path)
    print(f"Saved stability model to: {out_path}")

    return {
        "task": "zeta_potential",
        "samples": len(df),
        "groups": int(groups.nunique()),
        "metrics": {"MAE_mV": mae, "RMSE_mV": rmse, "R2": r2},
        "model_path": str(out_path),
    }


def train_cytotoxicity_from_candidate():
    print("=" * 60)
    print("TASK 2: TRAINING CYTOTOXICITY CLASSIFICATION MODEL")
    cand_path = CANDIDATE_DIR / "cytotoxicity_meox_iiib_candidate.csv"
    if not cand_path.exists():
        cand_path = Path(r"C:\Users\User\Downloads\cytotoxicity_meox_iiib_candidate.csv")
    df = pd.read_csv(cand_path)
    print(f"Loaded {len(df)} candidate rows from {cand_path.name}")

    # Map candidate columns to model expected feature names
    # Note: cell_viability_pct is deliberately NOT included in X!
    df["Toxicity"] = df["source_toxicity_label"].map({"Nontoxic": 0, "Toxic": 1})
    df["Material type"] = df["material_type"].astype(str)
    df["Assay"] = df["assay"].astype(str)
    df["Cell name"] = df["cell_line"].astype(str)
    df["Core size (nm)"] = df["core_size_nm"].astype(float)
    df["Hydro size (nm)"] = df["hydrodynamic_size_nm"].astype(float)
    df["Surface charge (mV)"] = df["surface_charge_mv"].astype(float)
    df["Surface area (m2/g)"] = df["surface_area_m2_g"].astype(float)
    df["Exposure time"] = df["exposure_time_h_raw"].astype(float)
    df["Mass dose (ug/mL)"] = df["mass_dose_ug_ml"].astype(float)
    df["Pubmed ID"] = df["study_pubmed_id"].astype(str)

    cat_cols = ["Material type", "Assay", "Cell name"]
    num_cols = [
        "Core size (nm)",
        "Hydro size (nm)",
        "Surface charge (mV)",
        "Surface area (m2/g)",
        "Exposure time",
        "Mass dose (ug/mL)",
    ]
    target_col = "Toxicity"
    group_col = "Pubmed ID"

    X = df[cat_cols + num_cols]
    y = df[target_col]
    groups = df[group_col]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestClassifier(random_state=42, n_estimators=100)),
    ])

    cv = GroupKFold(n_splits=5)
    scoring = ["accuracy", "precision", "recall", "f1"]
    res = cross_validate(pipe, X, y, groups=groups, cv=cv, scoring=scoring)

    acc = float(np.mean(res["test_accuracy"]))
    prec = float(np.mean(res["test_precision"]))
    rec = float(np.mean(res["test_recall"]))
    f1 = float(np.mean(res["test_f1"]))

    print(f"Samples: {len(df)}, Groups ({group_col}): {groups.nunique()}")
    print(f"GroupKFold (5 splits) -> Accuracy: {acc:.3f}, Precision: {prec:.3f}, Recall: {rec:.3f}, F1: {f1:.3f}")

    pipe.fit(X, y)
    out_path = MODELS_DIR / "cytotoxicity_model.joblib"
    joblib.dump(pipe, out_path)
    print(f"Saved cytotoxicity model to: {out_path}")

    return {
        "task": "cytotoxicity",
        "samples": len(df),
        "groups": int(groups.nunique()),
        "metrics": {"Accuracy": acc, "Precision": prec, "Recall": rec, "F1": f1},
        "model_path": str(out_path),
    }


def train_drug_release_from_candidate():
    print("=" * 60)
    print("TASK 3: TRAINING DRUG RELEASE REGRESSION MODEL")
    cand_path = CANDIDATE_DIR / "drug_release_115_candidate.csv"
    if not cand_path.exists():
        cand_path = Path(r"C:\Users\User\Downloads\drug_release_115_candidate.csv")
    df = pd.read_csv(cand_path)
    print(f"Loaded {len(df)} candidate rows from {cand_path.name}")

    numeric_cols = [
        "particle_size_nm",
        "drug_mw",
        "drug_loading_pct",
        "polymer_mw",
        "la_ga_ratio",
        "time_hours",
    ]
    categorical_cols = ["drug_name", "polymer"]
    features = numeric_cols + categorical_cols
    target_col = "cumulative_release_pct"
    group_col = "trajectory_id"

    # Ensure required columns are present and clean
    df_clean = df.dropna(subset=features + [target_col, group_col]).copy()
    for col in categorical_cols:
        df_clean[col] = df_clean[col].astype(str)

    X = df_clean[features]
    y = df_clean[target_col].astype(float)
    groups = df_clean[group_col].astype(str)

    n_groups = groups.nunique()
    print(f"Samples: {len(df_clean)}, Independent trajectories: {n_groups}")
    if n_groups < 5:
        n_splits = max(2, n_groups)
    else:
        n_splits = 5

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
        ]
    )

    estimator = RandomForestRegressor(
        n_estimators=80,
        min_samples_leaf=2,
        random_state=7,
        n_jobs=1,
    )

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    cv = GroupKFold(n_splits=n_splits)
    scoring = ["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"]
    res = cross_validate(pipe, X, y, groups=groups, cv=cv, scoring=scoring)
    oof_preds = cross_val_predict(pipe, X, y, groups=groups, cv=cv)

    mae = float(mean_absolute_error(y, oof_preds))
    rmse = float(np.sqrt(mean_squared_error(y, oof_preds)))
    r2 = float(r2_score(y, oof_preds))

    print(f"GroupKFold ({n_splits} splits) -> MAE: {mae:.2f} percentage points, RMSE: {rmse:.2f}, R²: {r2:.3f}")
    print("LIMITATION NOTE: 9 trajectories from a single publication (Bannigan et al., 2022) is a very small number")
    print("of independent formulation systems. Held-out trajectory performance exhibits high variance.")

    pipe.fit(X, y)
    out_path = MODELS_DIR / "drug_release_model.joblib"
    joblib.dump(pipe, out_path)
    print(f"Saved drug release model to: {out_path}")

    return {
        "task": "drug_release",
        "samples": len(df_clean),
        "groups": int(n_groups),
        "metrics": {"MAE_pct_points": mae, "RMSE": rmse, "R2": r2},
        "model_path": str(out_path),
    }


def main():
    r1 = train_stability_from_candidate()
    r2 = train_cytotoxicity_from_candidate()
    r3 = train_drug_release_from_candidate()

    summary = {
        "stability": r1,
        "cytotoxicity": r2,
        "drug_release": r3,
    }
    with open(ROOT / "data" / "processed" / "candidate_training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nTraining complete! Summary saved to data/processed/candidate_training_summary.json")


if __name__ == "__main__":
    main()
