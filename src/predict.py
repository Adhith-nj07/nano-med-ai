import os
import joblib
import pandas as pd
import numpy as np
import re
from typing import Dict, Any

class PredictionError(Exception):
    """Base exception for prediction API errors."""
    pass

class ValidationError(PredictionError):
    """Exception raised for invalid input fields or types."""
    pass

class ModelLoadError(PredictionError):
    """Exception raised when a model file cannot be loaded."""
    pass

# Robust path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STABILITY_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'stability_model_final.joblib')
CYTOTOXICITY_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'cytotoxicity_model.joblib')

_stability_model = None
_cytotoxicity_model = None

def get_stability_model():
    global _stability_model
    if _stability_model is None:
        if not os.path.exists(STABILITY_MODEL_PATH):
            raise ModelLoadError(f"Stability model not found at {STABILITY_MODEL_PATH}")
        try:
            _stability_model = joblib.load(STABILITY_MODEL_PATH)
            _limit_model_parallelism(_stability_model)
        except Exception as e:
            raise ModelLoadError(f"Failed to load stability model: {str(e)}")
    return _stability_model

def get_cytotoxicity_model():
    global _cytotoxicity_model
    if _cytotoxicity_model is None:
        if not os.path.exists(CYTOTOXICITY_MODEL_PATH):
            raise ModelLoadError(f"Cytotoxicity model not found at {CYTOTOXICITY_MODEL_PATH}")
        try:
            _cytotoxicity_model = joblib.load(CYTOTOXICITY_MODEL_PATH)
            _limit_model_parallelism(_cytotoxicity_model)
        except Exception as e:
            raise ModelLoadError(f"Failed to load cytotoxicity model: {str(e)}")
    return _cytotoxicity_model


def _limit_model_parallelism(model):
    """Keep inference compatible with constrained Windows/server workers."""
    if not hasattr(model, "get_params") or not hasattr(model, "set_params"):
        return
    single_worker = {
        name: 1
        for name in model.get_params(deep=True)
        if name == "n_jobs" or name.endswith("__n_jobs")
    }
    if single_worker:
        model.set_params(**single_worker)

def _extract_charge(smiles: str) -> str:
    if not isinstance(smiles, str):
        return 'Neutral'
    s = smiles
    has_anion = '[O-]' in s or '[S-]' in s
    has_cation = '[N+]' in s or '[P+]' in s
    if has_anion and has_cation:
        return 'Zwitterionic'
    elif has_anion:
        return 'Anionic'
    elif has_cation:
        return 'Cationic'
    else:
        return 'Neutral'

def _estimate_mw(smiles: str) -> float:
    if not isinstance(smiles, str):
        return 0.0
    s = smiles.upper()
    c = len(re.findall(r'C', s)) * 12.01
    o = len(re.findall(r'O', s)) * 16.00
    n = len(re.findall(r'N', s)) * 14.01
    s_atom = len(re.findall(r'S', s)) * 32.07
    p = len(re.findall(r'P', s)) * 30.97
    return float(c + o + n + s_atom + p)

def predict_stability(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predicts Zeta Potential (mV) for a nanoparticle.
    """
    required_keys = ['Shape', 'Core', 'Size_nm', 'Medium', 'Ligand_SMILES']
    
    # 1. Validation
    for k in required_keys:
        if k not in features:
            raise ValidationError(f"Missing required feature: '{k}'")
            
    try:
        size_val = float(features['Size_nm'])
        if size_val <= 0:
            raise ValidationError("Size_nm must be strictly positive.")
    except (TypeError, ValueError):
        raise ValidationError("Size_nm must be a valid float.")
        
    for k in ['Shape', 'Core', 'Medium', 'Ligand_SMILES']:
        if not isinstance(features[k], str):
            raise ValidationError(f"Feature '{k}' must be a string.")

    # 2. Model Loading
    model = get_stability_model()
    
    # 3. Preprocessing (Training consistency)
    charge = _extract_charge(features['Ligand_SMILES'])
    mw = _estimate_mw(features['Ligand_SMILES'])
    log_size = np.log1p(size_val)
    
    df = pd.DataFrame([{
        'Shape': features['Shape'],
        'Core': features['Core'],
        'Medium': features['Medium'],
        'Coating_Charge': charge,
        'Log_Size': log_size,
        'Estimated_Ligand_MW': mw
    }])
    
    # 4. Inference
    prediction = model.predict(df)[0]
    
    # 5. Output structure
    return {
        "prediction": float(prediction),
        "unit": "mV",
        "target": "zeta_potential"
    }

def predict_cytotoxicity(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predicts Experimental Cytotoxicity (Toxic / Nontoxic).
    """
    required_num = ['Core size (nm)', 'Hydro size (nm)', 'Surface charge (mV)', 'Surface area (m2/g)', 'Exposure time', 'Mass dose (ug/mL)']
    required_cat = ['Material type', 'Assay', 'Cell name']
    
    # 1. Validation
    for k in required_num + required_cat:
        if k not in features:
            raise ValidationError(f"Missing required feature: '{k}'")
            
    for k in required_num:
        try:
            features[k] = float(features[k])
        except (TypeError, ValueError):
            raise ValidationError(f"Feature '{k}' must be numeric.")
            
    for k in required_cat:
        if not isinstance(features[k], str):
            raise ValidationError(f"Feature '{k}' must be a string.")

    # 2. Model Loading
    model = get_cytotoxicity_model()
    
    # 3. Preprocessing & Inference
    # The ColumnTransformer in the serialized model expects these exact columns.
    df = pd.DataFrame([features])
    prediction = model.predict(df)[0]
    probabilities = np.asarray(model.predict_proba(df)[0], dtype=float).tolist() if hasattr(model, "predict_proba") else None
    classes = list(model.classes_) if probabilities is not None else []
    probability_by_class = dict(zip(classes, probabilities or []))
    probability_toxic = float(probability_by_class[1]) if 1 in probability_by_class else None
    confidence = float(np.max(probabilities)) if probabilities is not None else None
    
    # 4. Output structure
    label = 'Toxic' if prediction == 1 else 'Nontoxic'
    return {
        "prediction": label,
        "target": "cytotoxicity",
        "probability_toxic": probability_toxic,
        "confidence": confidence,
        "probability_calibrated": False
    }
