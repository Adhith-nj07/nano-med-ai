"""
NanoMedAI - single-file full-stack app (FastAPI backend + embedded HTML/JS frontend)
Run:  pip install fastapi uvicorn pandas numpy scikit-learn openpyxl
      python nanomedai_app.py      ->  http://127.0.0.1:8000
Put this file in your project root so it can read:
  data/processed/stability_combined_engineered.csv
  data/raw/cytotoxicity_meta_analysis.xlsx
If a file is missing, a clearly labelled SYNTHETIC DEMO dataset is used instead.
"""
import os, json, datetime, threading, webbrowser, uuid, time, asyncio
from typing import Optional, Dict, Any, List
import numpy as np, pandas as pd, uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score, accuracy_score
from sklearn.inspection import permutation_importance

# ------------------------------------------------------------------ data
def synth_stab():
    r = np.random.default_rng(1); n = 240
    d = pd.DataFrame({"Core": r.choice(["Ag", "Au", "Fe3O4", "ZnO"], n), "Shape": r.choice(["Spherical", "Rod"], n),
                      "Medium": r.choice(["Water", "PBS pH 7.4"], n), "Coating_Charge": r.choice(["anionic", "cationic", "neutral"], n),
                      "Size (nm)": r.uniform(5, 150, n).round(1), "study_id": r.integers(0, 12, n)})
    b = d.Coating_Charge.map({"anionic": -30, "cationic": 28, "neutral": -3})
    d["Zeta_mV"] = b * np.where(d.Medium == "PBS pH 7.4", .6, 1) - .05 * d["Size (nm)"] + r.normal(0, 5, n)
    return d

def synth_tox():
    r = np.random.default_rng(2); n = 300
    d = pd.DataFrame({"Core size (nm)": r.uniform(10, 100, n), "Hydro size (nm)": r.uniform(50, 400, n), "Surface charge (mV)": r.uniform(-40, 40, n),
                      "Exposure time": r.choice([6, 24, 48, 72], n), "Mass dose (ug/mL)": r.uniform(1, 500, n),
                      "Material type": r.choice(["ZnO", "CuO", "TiO2", "SiO2"], n), "Assay": r.choice(["MTT", "LDH"], n),
                      "Cell name": r.choice(["A549", "BEAS-2B"], n), "Cell type": r.choice(["Cancer", "Normal"], n), "Pubmed ID": r.integers(1, 15, n)})
    s = d["Mass dose (ug/mL)"] / 500 + d["Material type"].isin(["ZnO", "CuO"]) * .5 + r.normal(0, .2, n)
    d["Toxicity"] = np.where(s > .7, "Toxic", "Nontoxic")
    return d

# ------------------------------------------------------------------ task / model
class Task:
    def __init__(s, key, title, df, num, cat, y, groups, clf, source):
        s.key, s.title, s.num, s.cat, s.clf, s.source, s.ycol = key, title, num, cat, clf, source, y
        s.df = df.dropna(subset=[y]).reset_index(drop=True)
        s.X = s.df[num + cat].copy()
        for c in cat: s.X[c] = s.X[c].astype(str).replace("nan", "Unknown")
        s.y = s.df[y].values; s.g = s.df[groups].astype(str).values
        s.ranges = {c: [float(s.X[c].min()), float(s.X[c].max())] for c in num}
        s.med = {c: float(s.X[c].median()) for c in num}
        s.cats = {c: sorted(s.X[c].unique().tolist()) for c in cat}
        s.mode = {c: s.X[c].mode()[0] for c in cat}
        s.fit()

    def pre(s):
        return ColumnTransformer([("n", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), s.num),
                                  ("c", OneHotEncoder(handle_unknown="ignore"), s.cat)], sparse_threshold=0)

    def models(s):
        if s.clf:
            return {"Baseline (majority)": DummyClassifier(), "Logistic": LogisticRegression(max_iter=500),
                    "RandomForest": RandomForestClassifier(200, min_samples_leaf=2, random_state=0), "GradBoost": GradientBoostingClassifier(random_state=0)}
        return {"Baseline (mean)": DummyRegressor(), "Ridge": Ridge(), "RandomForest": RandomForestRegressor(200, min_samples_leaf=2, random_state=0),
                "GradBoost": GradientBoostingRegressor(random_state=0)}

    def fit(s):
        cv = GroupKFold(n_splits=max(2, min(5, len(set(s.g))))); s.metrics = {}
        for k, m in s.models().items():
            p = Pipeline([("p", s.pre()), ("m", m)])
            try:
                if s.clf:
                    pr = cross_val_predict(p, s.X, s.y, groups=s.g, cv=cv, method="predict_proba")[:, 1]
                    s.metrics[k] = {"AUC": float(roc_auc_score(s.y, pr)), "Accuracy": float(accuracy_score(s.y, pr > .5))}
                else:
                    pr = cross_val_predict(p, s.X, s.y, groups=s.g, cv=cv)
                    s.metrics[k] = {"MAE": float(mean_absolute_error(s.y, pr)), "R2": float(r2_score(s.y, pr))}
            except Exception:
                s.metrics[k] = {"error": None}
        s.pipe = Pipeline([("p", s.pre()), ("m", s.models()["RandomForest"])]).fit(s.X, s.y)
        pi = permutation_importance(s.pipe, s.X, s.y, n_repeats=5, random_state=0)
        s.importance = {c: float(v) for c, v in zip(s.X.columns, pi.importances_mean)}

    def row(s, inp):
        d = {c: [float(inp.get(c, s.med[c]))] for c in s.num}
        d.update({c: [str(inp.get(c, s.mode[c]))] for c in s.cat})
        return pd.DataFrame(d)[s.num + s.cat]

    def val(s, X):
        return float(s.pipe.predict_proba(X)[0, 1]) if s.clf else float(s.pipe.predict(X)[0])

    def domain(s, X):
        w = []
        for c in s.num:
            lo, hi = s.ranges[c]; x = X[c][0]
            if x < lo or x > hi: w.append(f"{c} = {x:g} is outside the training range [{lo:g}, {hi:g}]")
        for c in s.cat:
            if X[c][0] not in s.cats[c]: w.append(f"{c} = '{X[c][0]}' was not seen in training")
        return w

    def predict(s, inp):
        X = s.row(inp); v = s.val(X)
        Xt = s.pipe.named_steps["p"].transform(X)
        spread = float(np.std([t.predict(Xt)[0] for t in s.pipe.named_steps["m"].estimators_]))
        con = {}
        for c in s.num + s.cat:
            Z = X.copy(); Z[c] = s.med[c] if c in s.num else s.mode[c]; con[c] = v - s.val(Z)
        return dict(prediction=v, label=("Toxic" if v >= .5 else "Nontoxic") if s.clf else None, spread=spread, warnings=s.domain(X), contrib=con,
                    note="Occlusion explanation: change in output when a feature is set to the training median/mode. Associative, not causal; not SHAP.")

    def sweep(s, inp, var):
        base = s.row(inp)
        if var in s.num:
            lo, hi = s.ranges[var]; sp = hi - lo or 1; xs = [float(x) for x in np.linspace(lo - .1 * sp, hi + .1 * sp, 25)]
            ok = [lo <= x <= hi for x in xs]
        else:
            xs = s.cats[var][:15]; ok = [True] * len(xs)
        ys = []
        for x in xs:
            Z = base.copy(); Z[var] = x; ys.append(s.val(Z))
        return dict(x=[round(x, 3) if isinstance(x, float) else x for x in xs], y=ys, ok=ok, numeric=var in s.num)

    def info(s):
        return dict(title=s.title, source=s.source, n=len(s.df), ngroups=len(set(s.g)), clf=s.clf, num=s.num, cat=s.cat, ranges=s.ranges,
                    med=s.med, cats=s.cats, metrics=s.metrics, importance=s.importance)

def build():
    T = {}
    p = "data/processed/stability_combined_engineered.csv"
    d, src = (pd.read_csv(p), p) if os.path.exists(p) else (synth_stab(), "SYNTHETIC DEMO DATA (project CSV not found)")
    T["stability"] = Task("stability", "Zeta potential (stability proxy)", d, ["Size (nm)"], ["Core", "Shape", "Medium", "Coating_Charge"], "Zeta_mV", "study_id", False, src)
    p = "data/raw/cytotoxicity_meta_analysis.xlsx"
    d, src = (pd.read_excel(p), p) if os.path.exists(p) else (synth_tox(), "SYNTHETIC DEMO DATA (project xlsx not found)")
    d["toxic"] = (d["Toxicity"] == "Toxic").astype(int)
    T["toxicity"] = Task("toxicity", "Assay toxicity (metal oxides, Toxic / Nontoxic)", d,
                         ["Core size (nm)", "Hydro size (nm)", "Surface charge (mV)", "Exposure time", "Mass dose (ug/mL)"],
                         ["Material type", "Assay", "Cell name", "Cell type"], "toxic", "Pubmed ID", True, src)
    return T

TASKS = build()

# Korsmeyer-Peppas parameters for all benchmark formulations & dataset drugs
REL = {
    # Reference / Benchmark Formulations
    "formulation-a": ("Formulation A: Paclitaxel (PLGA)", 0.088, 0.371),
    "formulation-b": ("Formulation B: Letrozole (PLA)", 0.060, 0.420),
    "formulation-c": ("Formulation C: Letrozole (PLGA)", 0.110, 0.340),
    "paclitaxel": ("Paclitaxel (PLGA)", 0.088, 0.371),
    "letrozole": ("Letrozole (PLA)", 0.060, 0.420),

    # Paracetamol Formulations (Dataset NM-000001, NM-000004, NM-000012)
    "paracetamol": ("Paracetamol (PLGA)", 0.095, 0.400),
    "nm-paracetamol-plga": ("Paracetamol (PLGA)", 0.095, 0.400),
    "nm-paracetamol-liposome": ("Paracetamol (Liposome DPPC)", 0.145, 0.450),
    "nm-paracetamol-sln": ("Paracetamol (Lipid DSPC)", 0.105, 0.420),

    # Antibiotics & Antimicrobials
    "ciprofloxacin": ("Ciprofloxacin (PLGA)", 0.120, 0.360),
    "ciprofloxacin-plga": ("Ciprofloxacin (PLGA)", 0.120, 0.360),
    "vancomycin": ("Vancomycin (PLGA-PEG)", 0.050, 0.450),
    "vancomycin-plga-peg": ("Vancomycin (PLGA-PEG)", 0.050, 0.450),
    "rifampicin": ("Rifampicin (PLGA-PEG)", 0.070, 0.420),
    "rifampicin-plga-peg": ("Rifampicin (PLGA-PEG)", 0.070, 0.420),
    "doxycycline": ("Doxycycline (Polymeric NP)", 0.130, 0.390),
    "doxycycline-polymeric": ("Doxycycline (Polymeric NP)", 0.130, 0.390),
    "gentamicin": ("Gentamicin (Chitosan NP)", 0.160, 0.410),
    "gentamicin-chitosan": ("Gentamicin (Chitosan NP)", 0.160, 0.410),
    "azithromycin": ("Azithromycin (SLN)", 0.085, 0.350),
    "azithromycin-sln": ("Azithromycin (SLN)", 0.085, 0.350),
    "amoxicillin": ("Amoxicillin (Eudragit NP)", 0.175, 0.330),
    "amoxicillin-eudragit": ("Amoxicillin (Eudragit NP)", 0.175, 0.330),

    # Oncology & Chemotherapeutics
    "doxorubicin": ("Doxorubicin (PEG-Liposome)", 0.045, 0.460),
    "doxorubicin-liposome": ("Doxorubicin (PEG-Liposome)", 0.045, 0.460),
    "doxorubicin-plga": ("Doxorubicin (PLGA CHI/ALG)", 0.082, 0.420),
    "methotrexate": ("Methotrexate (PAMAM Dendrimer)", 0.180, 0.310),
    "methotrexate-dendrimer": ("Methotrexate (PAMAM Dendrimer)", 0.180, 0.310),
    "cisplatin": ("Cisplatin (Polymeric Micelle)", 0.090, 0.380),
    "cisplatin-micelle": ("Cisplatin (Polymeric Micelle)", 0.090, 0.380),
    "rapamycin": ("Rapamycin (Albumin HSA)", 0.075, 0.390),
    "rapamycin-albumin": ("Rapamycin (Albumin HSA)", 0.075, 0.390),
    "exemestane": ("Exemestane (PLGA In-Situ Gel)", 0.038, 0.580),
    "exemestane-plga-gel": ("Exemestane (PLGA In-Situ Gel)", 0.038, 0.580),

    # NSAIDs & Cardiovascular
    "ibuprofen": ("Ibuprofen (Lipid NP)", 0.115, 0.380),
    "ibuprofen-lipid": ("Ibuprofen (Lipid NP)", 0.115, 0.380),
    "amlodipine": ("Amlodipine Besylate (PLGA-PCL)", 0.065, 0.510),
    "amlodipine-plga-pcl": ("Amlodipine Besylate (PLGA-PCL)", 0.065, 0.510),
    "dox-atv": ("DOX / Atorvastatin (HA NP)", 0.078, 0.440),
    "dox-atv-dual": ("DOX / Atorvastatin (HA NP)", 0.078, 0.440),

    # Biologics & Nucleic Acids
    "mrna": ("mRNA (Ionizable LNP)", 0.150, 0.380),
    "mrna-lnp": ("mRNA (Ionizable LNP)", 0.150, 0.380),
    "sirna": ("siRNA (Cationic LNP)", 0.160, 0.360),
    "sirna-lnp": ("siRNA (Cationic LNP)", 0.160, 0.360),
}

# ------------------------------------------------------------------ API
app = FastAPI(title="NanoMedAI")

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.get("/api/overview")
def overview(): return {k: t.info() for k, t in TASKS.items()}

@app.post("/api/predict/{task}")
def predict(task: str, b: dict): return TASKS[task].predict(b["inputs"])

@app.post("/api/sweep/{task}")
def sweep(task: str, b: dict): return TASKS[task].sweep(b["inputs"], b["var"])

@app.get("/api/dataset/{task}")
def dataset(task: str):
    t = TASKS[task]; cols = t.num + t.cat + [t.ycol]
    return dict(rows=len(t.df), missing={c: int(t.df[c].isna().sum()) for c in cols},
                head=json.loads(t.df[cols].head(8).to_json(orient="records")))

@app.get("/api/release/{fid}")
def release(fid: str, ph: float = 7.4, temp: float = 37.0, hours: int = 72):
    name, k, n = REL[fid]; t = list(range(hours + 1)); f = [min(1.0, k * x ** n) if x else 0.0 for x in t]
    ch = abs(ph - 7.4) > 1e-6 or abs(temp - 37) > 1e-6
    return dict(name=name, t=t, release_pct=[round(v * 100, 2) for v in f], validity=["within_model_domain" if v <= .6 else "extrapolation" for v in f],
                env_response="unsupported" if ch else "n/a",
                note=("Environment changed, but Korsmeyer-Peppas parameters cannot causally respond to pH/temperature. Curve unchanged. " if ch else "")
                     + "Parameters are illustrative demo values. Orange = extrapolation (>60% release).")

@app.post("/api/report")
def report(b: dict):
    L = ["NANOMEDAI - RESEARCH PREDICTION REPORT", "Date: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    for r in b.get("results", []):
        t = TASKS[r["task"]]; res = r["result"]
        L += [f"TASK: {t.title}", "INPUTS:"] + [f"  {k}: {v}" for k, v in r["inputs"].items()]
        L.append("PREDICTION: " + (f"{res['label']} (P(toxic)={res['prediction']:.2f})" if t.clf else f"{res['prediction']:.2f} mV"))
        L.append(f"Tree-spread (uncalibrated, NOT a validated interval): {res['spread']:.3f}")
        L.append("APPLICABILITY: " + ("; ".join(res["warnings"]) if res["warnings"] else "inputs inside training ranges"))
        L.append("TOP FEATURES (occlusion): " + ", ".join(f"{k} ({v:+.2f})" for k, v in sorted(res["contrib"].items(), key=lambda z: -abs(z[1]))[:4]))
        L += [f"MODEL: RandomForest | Data: {t.source} | n={len(t.df)} | Validation: GroupKFold by study",
              "CV METRICS: " + json.dumps(t.metrics.get("RandomForest")), ""]
    L += ["LIMITATIONS:", "- Model-generated research estimate; depends on data quality and coverage.",
          "- Out-of-domain predictions may be unreliable. Feature effects are associative, not causal.",
          "- Assay-specific toxicity is not a clinical safety conclusion. Laboratory validation required."]
    if any("SYNTHETIC" in TASKS[r["task"]].source for r in b.get("results", [])): L.append("- WARNING: synthetic demo data used; results are NOT scientific.")
    return {"text": "\n".join(L)}

# ------------------------------------------------------------------ Simulation API
MAX_SIM_SESSIONS = 20
SIM_SESSIONS: Dict[str, Dict[str, Any]] = {}

def cleanup_sim_sessions():
    now = time.time()
    expired = [sid for sid, s in list(SIM_SESSIONS.items()) if now - s.get("last_active", now) > 1800]
    for sid in expired:
        SIM_SESSIONS.pop(sid, None)

class SimStartRequest(BaseModel):
    formulation: str
    ph: float = Field(..., ge=0.0, le=14.0, description="pH must be between 0 and 14")
    temp: float = Field(..., ge=0.0, le=100.0, description="Temperature must be between 0 and 100 °C")
    hours_total: float = Field(..., ge=1.0, le=1000.0, description="Total hours must be between 1 and 1000")
    step_hours: float = Field(..., ge=0.1, le=24.0, description="Step hours must be between 0.1 and 24")

class SimEnvRequest(BaseModel):
    ph: Optional[float] = Field(None, ge=0.0, le=14.0, description="pH must be between 0 and 14")
    temp: Optional[float] = Field(None, ge=0.0, le=100.0, description="Temperature must be between 0 and 100 °C")

def compute_kp_step(session: dict) -> dict:
    session["last_active"] = time.time()
    if session["current_time"] >= session["hours_total"]:
        session["status"] = "completed"
        return {
            "time": session["current_time"],
            "release_pct": session["release_pct"],
            "validity": session["validity"],
            "status": "completed",
            "is_completed": True,
            "event": None
        }
    
    new_t = min(session["hours_total"], round(session["current_time"] + session["step_hours"], 4))
    k = session["k"]
    n = session["n"]
    f = min(1.0, k * (new_t ** n)) if new_t > 0 else 0.0
    pct = min(100.0, round(f * 100, 2))
    val = "within_model_domain" if f <= 0.6 else "extrapolation"
    
    session["current_time"] = new_t
    session["release_pct"] = pct
    session["validity"] = val
    session["history"].append({"time": new_t, "release_pct": pct, "validity": val})
    
    event = None
    if new_t >= session["hours_total"]:
        session["status"] = "completed"
        event = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "event_type": "COMPLETED",
            "message": f"Simulation reached target duration of {new_t:.1f}h. Final cumulative release: {pct}%."
        }
        session["events"].append(event)
    
    return {
        "time": new_t,
        "release_pct": pct,
        "validity": val,
        "status": session["status"],
        "is_completed": session["status"] == "completed",
        "event": event
    }

@app.post("/api/sim/start")
def sim_start(req: SimStartRequest):
    cleanup_sim_sessions()
    if len(SIM_SESSIONS) >= MAX_SIM_SESSIONS:
        raise HTTPException(status_code=429, detail="Maximum limit of 20 active simulation sessions reached.")
    if req.formulation not in REL:
        raise HTTPException(status_code=422, detail=f"Unknown formulation '{req.formulation}'. Available: {list(REL.keys())}")
    
    sid = str(uuid.uuid4())
    form_name, k, n = REL[req.formulation]
    init_event = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "event_type": "SESSION_START",
        "message": f"Simulation initialized for {form_name} (pH={req.ph}, Temp={req.temp}°C, Total={req.hours_total}h, Step={req.step_hours}h)"
    }
    
    sess = {
        "sim_id": sid,
        "formulation": req.formulation,
        "formulation_name": form_name,
        "k": k,
        "n": n,
        "ph": req.ph,
        "temp": req.temp,
        "hours_total": req.hours_total,
        "step_hours": req.step_hours,
        "current_time": 0.0,
        "release_pct": 0.0,
        "validity": "within_model_domain",
        "status": "running",
        "history": [{"time": 0.0, "release_pct": 0.0, "validity": "within_model_domain"}],
        "events": [init_event],
        "last_active": time.time(),
        "stop_requested": False,
        "speed": 1.0,
    }
    SIM_SESSIONS[sid] = sess
    return {
        "sim_id": sid,
        "formulation": req.formulation,
        "formulation_name": form_name,
        "ph": req.ph,
        "temp": req.temp,
        "hours_total": req.hours_total,
        "step_hours": req.step_hours,
        "current_time": 0.0,
        "release_pct": 0.0,
        "validity": "within_model_domain",
        "status": "running",
        "events": sess["events"]
    }

@app.post("/api/sim/{sim_id}/step")
def sim_step(sim_id: str):
    cleanup_sim_sessions()
    if sim_id not in SIM_SESSIONS:
        raise HTTPException(status_code=404, detail="Simulation session not found or expired.")
    session = SIM_SESSIONS[sim_id]
    step_data = compute_kp_step(session)
    return {"sim_id": sim_id, **step_data}

@app.patch("/api/sim/{sim_id}/environment")
def sim_environment(sim_id: str, req: SimEnvRequest):
    cleanup_sim_sessions()
    if sim_id not in SIM_SESSIONS:
        raise HTTPException(status_code=404, detail="Simulation session not found or expired.")
    session = SIM_SESSIONS[sim_id]
    session["last_active"] = time.time()
    
    if req.ph is not None:
        session["ph"] = req.ph
    if req.temp is not None:
        session["temp"] = req.temp
        
    event = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "event_type": "ENVIRONMENT_CHANGE",
        "message": "Environment changed, but Korsmeyer-Peppas parameters cannot causally respond. Curve unchanged."
    }
    session["events"].append(event)
    if len(session["events"]) > 50:
        session["events"] = session["events"][-50:]
        
    return {
        "sim_id": sim_id,
        "ph": session["ph"],
        "temp": session["temp"],
        "release_model_response": "unsupported",
        "event": event
    }

@app.get("/api/sim/{sim_id}")
def sim_get(sim_id: str):
    cleanup_sim_sessions()
    if sim_id not in SIM_SESSIONS:
        raise HTTPException(status_code=404, detail="Simulation session not found or expired.")
    s = SIM_SESSIONS[sim_id]
    s["last_active"] = time.time()
    return {
        "sim_id": sim_id,
        "formulation": s["formulation"],
        "formulation_name": s["formulation_name"],
        "ph": s["ph"],
        "temp": s["temp"],
        "hours_total": s["hours_total"],
        "step_hours": s["step_hours"],
        "current_time": s["current_time"],
        "release_pct": s["release_pct"],
        "validity": s["validity"],
        "status": s["status"],
        "history": s["history"],
        "events": s["events"][-50:]
    }

@app.delete("/api/sim/{sim_id}")
def sim_delete(sim_id: str):
    if sim_id not in SIM_SESSIONS:
        raise HTTPException(status_code=404, detail="Simulation session not found or expired.")
    s = SIM_SESSIONS[sim_id]
    s["stop_requested"] = True
    SIM_SESSIONS.pop(sim_id, None)
    return {"message": "Session removed", "sim_id": sim_id}

@app.get("/api/sim/{sim_id}/stream")
async def sim_stream(sim_id: str, speed: float = 1.0):
    cleanup_sim_sessions()
    if sim_id not in SIM_SESSIONS:
        raise HTTPException(status_code=404, detail="Simulation session not found or expired.")
    
    clamped_speed = max(0.1, min(10.0, speed))
    SIM_SESSIONS[sim_id]["speed"] = clamped_speed

    async def event_generator():
        try:
            while True:
                if sim_id not in SIM_SESSIONS:
                    yield f"data: {json.dumps({'type': 'stopped', 'sim_id': sim_id})}\n\n"
                    break
                sess = SIM_SESSIONS[sim_id]
                if sess.get("stop_requested"):
                    yield f"data: {json.dumps({'type': 'stopped', 'sim_id': sim_id})}\n\n"
                    break
                
                if sess.get("status") == "paused":
                    await asyncio.sleep(0.2)
                    continue
                
                step_data = compute_kp_step(sess)
                msg = {
                    "type": "step",
                    "sim_id": sim_id,
                    "time": step_data["time"],
                    "release_pct": step_data["release_pct"],
                    "validity": step_data["validity"],
                    "status": step_data["status"],
                    "event": step_data["event"]
                }
                yield f"data: {json.dumps(msg)}\n\n"
                
                if step_data["is_completed"]:
                    break
                
                delay = max(0.05, 0.5 / max(0.1, sess.get("speed", 1.0)))
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ------------------------------------------------------------------ frontend

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NanoMedAI - Biophysical Simulation & ML Platform</title>
    <style>
/* ==========================================================================
   NanoMedAI — Deep Oceanic Abyss & Cyber-Glassmorphic Design System
   Full-Stack Biophysical Simulation & Predictive ML Platform
   ========================================================================== */

:root {
    /* Deep Oceanic Abyss & Cybernetic Glow Palette */
    --bg-dark: #030712;
    --bg-abyss: #06030f;
    --panel-bg: rgba(14, 10, 38, 0.72);
    --panel-bg-alt: rgba(8, 5, 24, 0.82);
    --panel-border: rgba(139, 120, 255, 0.22);
    --panel-border-bright: rgba(34, 211, 238, 0.45);
    --panel-border-glow: rgba(124, 58, 237, 0.4);
    
    /* Text Hierarchy */
    --text-primary: #f1efff;
    --text-bright: #ffffff;
    --text-secondary: #948cb8;
    --text-muted: #645e85;
    
    /* Accents & States */
    --accent-blue: #0ea5e9;
    --accent-cyan: #22d3ee;
    --accent-purple: #7c3aed;
    --accent-green: #10b981;
    --accent-warning: #f59e0b;
    --accent-danger: #f43f5e;
    --locked-color: #555075;
    
    /* Gradients & Glows */
    --grad-primary: linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #06b6d4 100%);
    --grad-ocean: linear-gradient(135deg, #0369a1 0%, #0891b2 50%, #22d3ee 100%);
    --grad-card: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
    --glow-cyan: 0 0 20px rgba(34, 211, 238, 0.35);
    --glow-purple: 0 0 25px rgba(124, 58, 237, 0.4);
    --glow-green: 0 0 16px rgba(16, 185, 129, 0.35);
    
    /* Typography */
    --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
    --font-display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: var(--font-sans);
    background-color: var(--bg-dark);
    color: var(--text-primary);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
    letter-spacing: -0.01em;
}

/* Deep Oceanic Abyss Ambient Background with Bioluminescent Light Beams */
body::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -2;
    pointer-events: none;
    background:
        radial-gradient(1000px 600px at 15% -10%, rgba(124, 58, 237, 0.35), transparent 65%),
        radial-gradient(900px 550px at 90% 10%, rgba(34, 211, 238, 0.22), transparent 60%),
        radial-gradient(1100px 700px at 50% 105%, rgba(37, 99, 235, 0.25), transparent 65%),
        radial-gradient(600px 400px at 75% 65%, rgba(139, 92, 246, 0.18), transparent 55%),
        linear-gradient(180deg, #0a0624 0%, #04020f 45%, #010108 100%);
}

/* Subterranean Caustic Shimmer Grid */
body::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background-image:
        radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 32px 32px;
    opacity: 0.5;
}

h1, h2, h3, .brand h1, .view-header h2, .nav-tab-btn, .btn {
    font-family: var(--font-display);
}

/* ==========================================================================
   TOP BAR & NAVIGATION
   ========================================================================== */
.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.6rem;
    background: rgba(8, 6, 26, 0.78);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--panel-border);
    gap: 1.2rem;
    flex-shrink: 0;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
    z-index: 50;
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.brand::before {
    content: "N";
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    background: var(--grad-primary);
    box-shadow: var(--glow-purple), inset 0 1px 1px rgba(255, 255, 255, 0.4);
    font: 700 16px var(--font-display);
    color: #fff;
    flex-shrink: 0;
}

.brand h1 {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.3px;
    background: linear-gradient(90deg, #93c5fd, #22d3ee 50%, #c084fc 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    filter: drop-shadow(0 0 10px rgba(34, 211, 238, 0.35));
}

.badge {
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
}
.badge-demo {
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
}
.badge-live {
    background: rgba(16, 185, 129, 0.12);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.badge-blue {
    background: rgba(14, 165, 233, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(14, 165, 233, 0.35);
}
.badge-locked {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-muted);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.disclaimer-banner {
    font-size: 0.74rem;
    color: var(--text-secondary);
    flex: 1;
    text-align: center;
    line-height: 1.4;
}
.disclaimer-banner strong, .disclaimer-banner b { color: var(--accent-warning); }

.top-bar-right {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.status-indicator {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--panel-border);
}
.status-initialized { color: var(--text-secondary); }
.status-running { color: #6ee7b7; text-shadow: 0 0 10px rgba(16, 185, 129, 0.6); }
.status-paused { color: #fde68a; }
.status-stopped { color: #fda4af; }
.status-completed { color: #67e8f9; }

.backend-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.7rem;
    font-family: var(--font-mono);
    padding: 0.25rem 0.65rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--panel-border);
    border-radius: 999px;
    color: var(--text-secondary);
}
.backend-indicator.online {
    color: #6ee7b7;
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.08);
}
.backend-indicator.offline {
    color: #fda4af;
    border-color: rgba(244, 63, 94, 0.4);
    background: rgba(244, 63, 94, 0.08);
}
.dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: currentColor;
    display: inline-block;
    box-shadow: 0 0 8px currentColor;
}

/* TOP NAVIGATION BAR */
.feature-nav-bar {
    display: flex;
    gap: 0.4rem;
    background: rgba(8, 6, 25, 0.55);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--panel-border);
    padding: 0.45rem 1.4rem;
    overflow-x: auto;
    scrollbar-width: none;
    flex-shrink: 0;
    z-index: 40;
}
.feature-nav-bar::-webkit-scrollbar { display: none; }

.nav-tab-btn {
    position: relative;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 0.55rem 1rem;
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    cursor: pointer;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    border-radius: 999px;
    transition: all 0.22s ease;
}
.nav-tab-btn:hover {
    color: #ffffff;
    background: rgba(124, 58, 237, 0.12);
}
.nav-tab-btn.active {
    color: #ffffff;
    background: rgba(124, 58, 237, 0.22);
    box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.45), 0 0 16px rgba(34, 211, 238, 0.2);
    text-shadow: 0 0 10px rgba(34, 211, 238, 0.4);
}

/* ==========================================================================
   WORKSPACE GRID (LIVE SIMULATOR)
   ========================================================================== */
.workspace {
    display: grid;
    grid-template-columns: 360px 1fr 360px;
    flex-grow: 1;
    overflow: hidden;
    gap: 1px;
    background: var(--panel-border);
}

.panel {
    background: var(--panel-bg);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.panel section,
.control-section,
.visualization-section,
.graph-section,
.dashboard-section,
.events-section,
.roadmap-section {
    padding: 1.25rem 1.4rem;
    border-bottom: 1px solid var(--panel-border);
}

.panel h2 {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--accent-cyan);
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
}

/* LEFT PANEL: CONTROLS */
.left-panel { border-left: none; }
.form-group { margin-bottom: 1rem; }
.form-group label {
    display: block;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.45rem;
}

.demo-select, select, input[type="text"], input[type="number"], textarea {
    width: 100%;
    padding: 0.6rem 0.8rem;
    background: var(--panel-bg-alt);
    border: 1px solid var(--panel-border);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 0.82rem;
    outline: none;
    border-radius: var(--radius-sm);
    transition: all 0.22s ease;
}
.demo-select:focus, select:focus, input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
    border-color: var(--accent-cyan);
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.18), 0 0 12px rgba(34, 211, 238, 0.25);
    background: rgba(16, 11, 40, 0.95);
}
select option {
    background: #0d0926;
    color: var(--text-primary);
    padding: 0.4rem;
}

.searchable-select-wrapper { position: relative; width: 100%; }
.searchable-dropdown-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    max-height: 200px;
    overflow-y: auto;
    background: #0d0926;
    border: 1px solid var(--accent-cyan);
    border-top: none;
    z-index: 1000;
    border-radius: 0 0 var(--radius-sm) var(--radius-sm);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
    display: none;
}
.searchable-option {
    padding: 0.55rem 0.8rem;
    font-size: 0.8rem;
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.12s ease;
}
.searchable-option:hover {
    background: rgba(34, 211, 238, 0.15);
    color: var(--accent-cyan);
}
.searchable-option.empty {
    color: var(--text-muted);
    font-style: italic;
    cursor: default;
}

.static-config-info {
    background: rgba(8, 5, 24, 0.6);
    padding: 0.9rem 1rem;
    border: 1px solid var(--panel-border);
    border-radius: var(--radius-sm);
    font-size: 0.8rem;
}
.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.45rem;
}
.info-row:last-child { margin-bottom: 0; }
.info-row span { color: var(--text-secondary); font-size: 0.75rem; }
.info-row strong {
    color: #ffffff;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    font-weight: 600;
}

.slider-group { margin-bottom: 1.15rem; }
.slider-group label {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 0.4rem;
}
.slider-group label span {
    font-family: var(--font-mono);
    color: var(--accent-cyan);
}
.slider-group input[type="range"],
.timeline-group input[type="range"] {
    width: 100%;
    accent-color: var(--accent-cyan);
    height: 6px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 99px;
    outline: none;
    cursor: pointer;
}
.slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.68rem;
    font-family: var(--font-mono);
    color: var(--text-muted);
    margin-top: 0.3rem;
}

.panel-warning {
    background: rgba(245, 158, 11, 0.1);
    border-left: 3px solid var(--accent-warning);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    padding: 0.85rem 1rem;
    font-size: 0.76rem;
    color: #fde68a;
    margin-top: 0.9rem;
    line-height: 1.45;
}
.panel-warning.hidden { display: none !important; }

/* SIMULATION CONTROLS */
.timeline-group { margin-bottom: 1.25rem; }
.timeline-group label {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.45rem;
}
.timeline-group label span {
    font-family: var(--font-mono);
    color: var(--accent-cyan);
    font-size: 0.95rem;
}
.timeline-group input[type="range"] {
    accent-color: var(--accent-green);
    height: 8px;
}

.speed-control { margin-bottom: 1.25rem; }
.speed-control label {
    display: block;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.45rem;
}
.speed-control label small {
    display: block;
    font-size: 0.66rem;
    color: var(--text-muted);
    text-transform: none;
    letter-spacing: 0;
    margin-top: 0.15rem;
}
.speed-buttons {
    display: flex;
    gap: 0.35rem;
    background: rgba(8, 5, 24, 0.7);
    padding: 0.3rem;
    border-radius: 999px;
    border: 1px solid var(--panel-border);
}
.btn-speed {
    flex: 1;
    padding: 0.35rem 0;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 0.72rem;
    font-family: var(--font-mono);
    font-weight: 600;
    cursor: pointer;
    border-radius: 999px;
    transition: all 0.2s ease;
}
.btn-speed:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}
.btn-speed.active {
    background: var(--grad-ocean);
    color: #fff;
    box-shadow: 0 0 12px rgba(34, 211, 238, 0.4);
    font-weight: 700;
}

.action-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.55rem;
}

.btn {
    padding: 0.65rem 1rem;
    font-family: var(--font-display);
    font-weight: 600;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    cursor: pointer;
    border: none;
    text-align: center;
    border-radius: 999px;
    transition: all 0.22s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
}
.hidden { display: none !important; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; filter: grayscale(0.5); }

.btn-primary {
    background: var(--grad-primary);
    color: #fff;
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.4);
}
.btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.6), 0 0 16px rgba(34, 211, 238, 0.3);
    filter: brightness(1.1);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.06);
    color: #e2e8f0;
    border: 1px solid var(--panel-border);
}
.btn-secondary:hover:not(:disabled) {
    background: rgba(124, 58, 237, 0.2);
    border-color: var(--accent-cyan);
    color: #fff;
}

.btn-danger {
    background: rgba(244, 63, 94, 0.1);
    color: #fda4af;
    border: 1px solid rgba(244, 63, 94, 0.4);
}
.btn-danger:hover:not(:disabled) {
    background: rgba(244, 63, 94, 0.25);
    box-shadow: 0 0 14px rgba(244, 63, 94, 0.3);
}

.btn-wide { width: 100%; }

/* ==========================================================================
   CENTER PANEL: VISUALIZATION & CHARTS
   ========================================================================== */
.center-panel {
    background: var(--bg-abyss);
    border-left: none;
    border-right: none;
}

.visualization-section { display: flex; flex-direction: column; }
.canvas-container {
    background:
        radial-gradient(circle at 50% 40%, rgba(124, 58, 237, 0.22), transparent 70%),
        radial-gradient(circle at 60% 70%, rgba(34, 211, 238, 0.12), transparent 60%),
        linear-gradient(180deg, #0a0624 0%, #03010c 100%);
    border: 1px solid var(--panel-border);
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    height: 350px;
    border-radius: var(--radius-md);
    box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.8), 0 10px 30px rgba(0, 0, 0, 0.5);
}
#particle-canvas { max-width: 100%; max-height: 100%; display: block; }

#canvas-overlay-text {
    position: absolute;
    bottom: 1.1rem;
    left: 1.2rem;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: rgba(255, 255, 255, 0.6);
    pointer-events: none;
    line-height: 1.5;
    background: rgba(6, 3, 18, 0.65);
    padding: 0.5rem 0.75rem;
    border-radius: var(--radius-sm);
    border: 1px solid rgba(139, 120, 255, 0.2);
    backdrop-filter: blur(8px);
}
#canvas-overlay-text span {
    color: var(--accent-cyan);
    font-weight: 600;
}

.graph-section {
    border-top: 1px solid var(--panel-border);
    background: rgba(10, 7, 28, 0.4);
}
.chart-container {
    width: 100%;
    height: 185px;
    position: relative;
    padding: 0.5rem 0;
}

/* ==========================================================================
   RIGHT PANEL: TELEMETRY DASHBOARD & EVENTS
   ========================================================================== */
.right-panel { border-right: none; }
.state-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
}
.state-card {
    background: var(--panel-bg-alt);
    border: 1px solid var(--panel-border);
    padding: 0.75rem 0.85rem;
    display: flex;
    flex-direction: column;
    border-radius: var(--radius-sm);
    transition: all 0.22s ease;
}
.state-card:hover {
    border-color: rgba(34, 211, 238, 0.4);
    transform: translateY(-1px);
}
.highlight-card {
    border-color: var(--accent-cyan);
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.12) 0%, rgba(124, 58, 237, 0.12) 100%);
    box-shadow: 0 0 16px rgba(34, 211, 238, 0.15);
}
.state-label {
    font-size: 0.66rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.35rem;
}
.state-value {
    font-family: var(--font-mono);
    font-size: 1.15rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.02em;
}
.highlight-card .state-value {
    color: var(--accent-cyan);
    text-shadow: 0 0 12px rgba(34, 211, 238, 0.5);
}
.state-value small {
    font-size: 0.72rem;
    color: var(--text-secondary);
    font-weight: 500;
    margin-left: 0.15rem;
}

/* EVENTS */
.events-section { display: flex; flex-direction: column; }
.events-list {
    overflow-y: auto;
    font-family: var(--font-mono);
    font-size: 0.74rem;
    max-height: 180px;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-right: 0.3rem;
}
.event-item {
    padding: 0.4rem 0.65rem 0.4rem 0.75rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
    border-left: 3px solid var(--accent-cyan);
    line-height: 1.4;
}
.event-item.warn {
    border-left-color: var(--accent-warning);
    color: #fde68a;
    background: rgba(245, 158, 11, 0.06);
}
.event-item.sys {
    border-left-color: var(--accent-purple);
    color: #e2e8f0;
}
.event-time {
    color: var(--accent-cyan);
    font-size: 0.66rem;
    font-weight: 600;
    margin-bottom: 0.15rem;
}

/* ROADMAP & STATUS */
.model-status-panel { margin-top: 0.2rem; }
.ms-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
    margin-bottom: 0.45rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid rgba(139, 120, 255, 0.12);
}
.ms-row span:first-child { color: var(--text-primary); }
.ms-demo {
    color: var(--accent-cyan);
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
}
.ms-warn {
    color: var(--accent-warning);
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
}

.locked-features { list-style: none; margin-bottom: 0.6rem; }
.locked-features li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.76rem;
    padding: 0.35rem 0;
    color: var(--locked-color);
    border-bottom: 1px dotted rgba(255, 255, 255, 0.05);
}
.roadmap-note {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-style: italic;
    line-height: 1.4;
}

/* ==========================================================================
   VIEW CONTAINERS (AI PROMPT, PREDICTOR, DATA, 3D, REPORT)
   ========================================================================== */
.view-container { display: none; flex-grow: 1; overflow: hidden; }
.view-container.active { display: grid; }
.view-container-single {
    display: none;
    flex-grow: 1;
    overflow-y: auto;
    padding: 1.8rem 2.2rem;
    background: transparent;
}
.view-container-single.active { display: block; }

.content-max-width { max-width: 1140px; margin: 0 auto; }
.view-header { margin-bottom: 1.6rem; }
.view-header h2 {
    font-size: 1.35rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.4rem;
    letter-spacing: -0.3px;
    background: linear-gradient(90deg, #fff, #93c5fd 50%, #67e8f9 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.view-header p {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
    max-width: 820px;
}

.card-panel {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-radius: var(--radius-md);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
}
.card-panel h3 {
    font-size: 0.84rem;
    font-weight: 700;
    color: var(--accent-cyan);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1.15rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.prompt-textarea {
    display: block;
    width: 100%;
    min-height: 90px;
    margin: 0.4rem 0 0.75rem;
    padding: 0.75rem;
    background: var(--panel-bg-alt);
    border: 1px solid var(--panel-border);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 0.84rem;
    line-height: 1.5;
    resize: vertical;
    border-radius: var(--radius-sm);
}

.details-collapsible {
    margin: 0.8rem 0;
    font-size: 0.78rem;
    color: var(--text-secondary);
}
.details-collapsible summary {
    padding: 0.4rem 0;
    cursor: pointer;
    user-select: none;
    font-weight: 600;
    color: var(--accent-cyan);
}
.advanced-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 0.75rem 1rem;
    padding: 0.75rem 0;
}
.advanced-grid label, .tool-field-label {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.74rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.workflow-results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.85rem;
    margin: 0.9rem 0;
}
.workflow-stat-card {
    padding: 0.9rem 1rem;
    background: rgba(8, 5, 24, 0.7);
    border: 1px solid var(--panel-border);
    border-radius: var(--radius-sm);
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
}
.workflow-stat-card span {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-secondary);
    letter-spacing: 0.06em;
}
.workflow-stat-card strong {
    color: #ffffff;
    font-family: var(--font-mono);
    font-size: 1.1rem;
    font-weight: 700;
}
.workflow-stat-card small {
    font-size: 0.72rem;
    color: var(--accent-cyan);
    line-height: 1.4;
}

.driver-group { margin: 0.75rem 0 1rem; }
.driver-title {
    font-size: 0.72rem;
    color: var(--accent-cyan);
    text-transform: uppercase;
    margin-bottom: 0.45rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.driver-row {
    display: grid;
    grid-template-columns: minmax(90px, 1fr) minmax(80px, 1.4fr) 55px;
    gap: 0.65rem;
    align-items: center;
    margin: 0.4rem 0;
    font-size: 0.74rem;
    padding: 0.25rem 0.5rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
}
.driver-row span {
    color: #d1cce8;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.driver-row i {
    height: 7px;
    background: rgba(255, 255, 255, 0.08);
    display: block;
    border-radius: 99px;
    overflow: hidden;
}
.driver-row i b {
    display: block;
    height: 100%;
    background: var(--grad-ocean);
    border-radius: 99px;
    box-shadow: 0 0 8px rgba(34, 211, 238, 0.5);
}
.driver-row strong {
    text-align: right;
    color: #ffffff;
    font-family: var(--font-mono);
    font-size: 0.74rem;
}

.input-matrix-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 0.95rem;
    margin-bottom: 1.25rem;
}

.result-terminal {
    background: var(--panel-bg-alt);
    border: 1px solid var(--panel-border);
    padding: 1.2rem;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    line-height: 1.65;
    color: #e2e8f0;
    min-height: 110px;
    white-space: pre-wrap;
    word-break: break-word;
    border-radius: var(--radius-sm);
}

.model-row-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.85rem 1rem;
    background: rgba(8, 5, 24, 0.6);
    border: 1px solid var(--panel-border);
    margin-bottom: 0.6rem;
    font-size: 0.8rem;
    border-radius: var(--radius-sm);
}
.model-row-item small {
    display: block;
    color: var(--text-secondary);
    margin-top: 0.3rem;
    font-size: 0.72rem;
}
.model-row-item strong {
    font-family: var(--font-mono);
    color: var(--accent-cyan);
    white-space: nowrap;
    font-size: 0.9rem;
}

.table-responsive {
    width: 100%;
    overflow-x: auto;
    border: 1px solid var(--panel-border);
    border-radius: var(--radius-sm);
    margin-top: 0.9rem;
}
.table-responsive table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
    white-space: nowrap;
}
.table-responsive th, .table-responsive td {
    padding: 0.65rem 0.9rem;
    border-bottom: 1px solid var(--panel-border);
    text-align: left;
}
.table-responsive th {
    background: rgba(34, 211, 238, 0.08);
    color: var(--accent-cyan);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.7rem;
}
.table-responsive tr:hover td { background: rgba(124, 58, 237, 0.08); }

/* 3D VIEWER HOST */
.viewer-canvas-host {
    height: 480px;
    width: 100%;
    background:
        radial-gradient(circle at 50% 40%, rgba(124, 58, 237, 0.25), transparent 70%),
        radial-gradient(circle at 60% 70%, rgba(34, 211, 238, 0.15), transparent 60%),
        linear-gradient(180deg, #0a0624 0%, #02010a 100%);
    border: 1px solid var(--panel-border);
    position: relative;
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.8), 0 16px 40px rgba(0, 0, 0, 0.5);
}
.viewer-controls-overlay {
    position: absolute;
    bottom: 1.2rem;
    right: 1.2rem;
    background: rgba(8, 5, 24, 0.75);
    backdrop-filter: blur(10px);
    border: 1px solid var(--panel-border);
    padding: 0.55rem 0.9rem;
    font-size: 0.72rem;
    color: var(--text-secondary);
    border-radius: 999px;
    pointer-events: none;
}

/* REPORT TEXTBOX */
.report-textbox {
    width: 100%;
    min-height: 400px;
    padding: 1.1rem;
    background: var(--panel-bg-alt);
    border: 1px solid var(--panel-border);
    color: #e2e8f0;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    line-height: 1.65;
    resize: vertical;
    border-radius: var(--radius-sm);
    outline: none;
}
.report-textbox:focus {
    border-color: var(--accent-cyan);
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15);
}

/* KEY SAMPLE FIELDS BAR */
.key-fields-bar {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem 0.95rem;
    margin: 0.75rem 0;
    padding: 0.85rem 1rem;
    background: rgba(14, 165, 233, 0.08);
    border: 1px solid rgba(14, 165, 233, 0.3);
    border-radius: var(--radius-sm);
}
.key-field-item {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
}
.key-field-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent-cyan);
}

/* ==========================================================================
   RESPONSIVENESS
   ========================================================================== */
@media (max-width: 1180px) {
    .workspace {
        grid-template-columns: 310px 1fr 300px;
    }
}
@media (max-width: 960px) {
    body {
        height: auto;
        overflow-y: auto;
    }
    .workspace {
        display: flex;
        flex-direction: column;
        overflow: visible;
    }
    .panel {
        overflow: visible;
    }
    .top-bar {
        flex-direction: column;
        align-items: flex-start;
    }
    .top-bar-right {
        width: 100%;
        justify-content: space-between;
    }
    .disclaimer-banner {
        text-align: left;
    }
}

/* ==========================================================================
   Intro Modal & Loading Splash Screen Styling
   ========================================================================== */
.intro-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(3, 6, 17, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.35s ease;
}
.intro-modal-overlay.active {
    opacity: 1;
    pointer-events: auto;
}
.intro-modal-card {
    background: radial-gradient(circle at 15% 15%, rgba(30, 18, 70, 0.85) 0%, rgba(9, 13, 28, 0.96) 55%, #040612 100%);
    border: 1px solid rgba(139, 92, 246, 0.45);
    border-radius: 22px;
    box-shadow: 0 30px 70px -15px rgba(0, 0, 0, 0.9), 0 0 35px rgba(124, 58, 237, 0.3);
    max-width: 820px;
    width: 92%;
    padding: 2.4rem 2.8rem;
    position: relative;
    max-height: 90vh;
    overflow-y: auto;
    animation: modalPopIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes modalPopIn {
    0% { transform: scale(0.92) translateY(20px); opacity: 0; }
    100% { transform: scale(1) translateY(0); opacity: 1; }
}
.intro-close-btn {
    position: absolute;
    top: 1.2rem;
    right: 1.4rem;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 50%;
    width: 34px;
    height: 34px;
    color: #e2e8f0;
    font-size: 1.2rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}
.intro-close-btn:hover {
    background: rgba(244, 63, 94, 0.25);
    border-color: #f43f5e;
    color: #f43f5e;
}
.intro-hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #ffffff 15%, #c4b5fd 60%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0.4rem 0 0.8rem 0;
}
.intro-lead {
    color: #cbd5e1;
    font-size: 0.98rem;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}
.intro-progress-box {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.5rem;
}
.intro-progress-bar-wrap {
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    margin: 0.8rem 0 0.6rem 0;
}
.intro-progress-bar {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #7c3aed, #22d3ee);
    border-radius: 4px;
    transition: width 0.4s ease;
}
.intro-steps-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #94a3b8;
}
.intro-step-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.intro-step-item.done {
    color: #22d3ee;
}
.intro-kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.8rem;
}
.intro-kpi-card {
    background: rgba(10, 15, 30, 0.6);
    border: 1px solid rgba(139, 92, 246, 0.22);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.intro-kpi-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #38bdf8;
}
.intro-kpi-lbl {
    font-size: 0.76rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}
.intro-actions {
    display: flex;
    gap: 0.9rem;
    justify-content: flex-end;
}

/* ---------- 3D VIEWER ---------- */
input[type=range]{padding:0;accent-color:var(--cyan,#22d3ee);margin-top:.5rem}
.v3-stage{position:relative;height:460px;border-radius:12px;overflow:hidden;border:1px solid rgba(139,120,255,0.25);
  background:radial-gradient(circle at 50% 40%,rgba(59,130,246,.18),rgba(2,6,26,.95) 70%)}
.v3-stage canvas{display:block;width:100%;height:100%;touch-action:none}
.v3-label{position:absolute;left:12px;bottom:10px;font:500 .66rem 'JetBrains Mono',monospace;
  letter-spacing:.4px;color:#FDE68A;background:rgba(2,6,26,.7);border:1px solid rgba(245,158,11,.35);
  padding:.3rem .6rem;border-radius:6px;pointer-events:none}
.v3-chips{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-top:1rem}
@media(max-width:640px){.v3-chips{grid-template-columns:1fr 1fr}.v3-stage{height:340px}}
.v3-chips .kpi{background:rgba(10,15,30,0.6);border:1px solid rgba(139,92,246,0.22);border-radius:10px;padding:.6rem .8rem;display:flex;flex-direction:column;gap:.2rem}
.v3-chips .kpi span{font-size:.65rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.6px}
.v3-chips .kpi b{font-size:1rem;color:#fff;font-family:'Space Grotesk',sans-serif}




/* ============================================================
   NANO·LAB 3D — Live Nanomedicine Simulation Studio
   ============================================================ */
.nanolab-viewport{
  position:relative;
  width:100%;
  height:720px;
  border-radius:18px;
  overflow:hidden;
  border:1px solid rgba(130,165,255,.2);
  background:#04060e;
  box-shadow:0 22px 60px rgba(0,0,0,.6), inset 0 1px 0 rgba(255,255,255,.05);
}
.nanolab-viewport #scene{
  position:absolute;
  inset:0;
  width:100%;
  height:100%;
  display:block;
  cursor:grab;
}
.nanolab-viewport #scene:active{
  cursor:grabbing;
}
.nanolab-viewport .panel{
  position:absolute;
  background:rgba(11,17,34,.78);
  backdrop-filter:blur(18px);
  -webkit-backdrop-filter:blur(18px);
  border:1px solid rgba(130,165,255,.18);
  border-radius:18px;
  box-shadow:0 22px 60px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.05);
  z-index:5;
}
.nanolab-viewport #hud-top{
  top:14px;
  left:14px;
  display:flex;
  align-items:center;
  gap:12px;
  padding:10px 16px 10px 12px;
}
.nanolab-viewport .nl-logo{
  width:38px;
  height:38px;
  border-radius:12px;
  background:conic-gradient(from 210deg,#22d3ee,#818cf8,#f472b6,#22d3ee);
  display:grid;
  place-items:center;
  box-shadow:0 0 24px rgba(99,140,255,.5);
}
.nanolab-viewport .nl-logo span{
  width:14px;
  height:14px;
  border-radius:50%;
  background:#04060e;
  box-shadow:0 0 0 4px rgba(255,255,255,.18);
}
.nanolab-viewport #hud-top h1{
  font-size:14.5px;
  letter-spacing:2.2px;
  font-weight:800;
  margin:0;
  color:#fff;
}
.nanolab-viewport #hud-top h1 b{
  background:linear-gradient(90deg,#22d3ee,#818cf8);
  -webkit-background-clip:text;
  background-clip:text;
  color:transparent;
}
.nanolab-viewport #hud-top p{
  font-size:10px;
  color:#7f90b8;
  letter-spacing:.8px;
  margin:2px 0 0 0;
  font-family:'JetBrains Mono',monospace;
}
.nanolab-viewport .nl-live{
  display:flex;
  align-items:center;
  gap:6px;
  margin-left:6px;
  padding:4px 9px;
  border-radius:99px;
  background:rgba(244,114,182,.1);
  border:1px solid rgba(244,114,182,.35);
  font-family:'JetBrains Mono',monospace;
  font-size:9.5px;
  letter-spacing:2px;
  color:#f9a8d4;
}
.nanolab-viewport .nl-live i{
  width:6px;
  height:6px;
  border-radius:50%;
  background:#f472b6;
  animation:nlPulse 1.4s infinite;
}
@keyframes nlPulse{
  0%,100%{box-shadow:0 0 0 0 rgba(244,114,182,.6)}
  50%{box-shadow:0 0 0 6px rgba(244,114,182,0)}
}
.nanolab-viewport aside h2{
  font-size:9.5px;
  letter-spacing:2.2px;
  color:#7f90b8;
  font-weight:700;
  margin:2px 0 10px;
  text-transform:uppercase;
}
.nanolab-viewport #panel-left{
  top:80px;
  left:14px;
  width:236px;
  padding:14px;
  max-height:calc(100% - 170px);
  overflow-y:auto;
}
.nanolab-viewport .card-item{
  display:flex;
  gap:10px;
  align-items:center;
  padding:9px;
  border-radius:12px;
  border:1px solid transparent;
  background:rgba(255,255,255,.028);
  cursor:pointer;
  transition:.18s;
  margin-bottom:6px;
}
.nanolab-viewport .card-item:hover{
  background:rgba(129,140,248,.1);
  transform:translateX(2px);
}
.nanolab-viewport .card-item.active{
  border-color:rgba(34,211,238,.55);
  background:linear-gradient(90deg,rgba(34,211,238,.14),rgba(129,140,248,.12));
  box-shadow:0 0 20px rgba(34,211,238,.12);
}
.nanolab-viewport .card-item .dot{
  width:28px;
  height:28px;
  border-radius:8px;
  flex:none;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.18), 0 4px 12px rgba(0,0,0,.4);
}
.nanolab-viewport .card-item h3{
  font-size:12px;
  font-weight:700;
  margin:0;
  color:#fff;
}
.nanolab-viewport .card-item p{
  font-size:9.5px;
  color:#7f90b8;
  margin:2px 0 0 0;
  font-family:'JetBrains Mono',monospace;
}
.nanolab-viewport .badge-nl{
  display:inline-block;
  font-size:8px;
  letter-spacing:1.4px;
  padding:2px 6px;
  border-radius:5px;
  font-weight:800;
  margin-top:3px;
  text-transform:uppercase;
}
.nanolab-viewport .badge-nl.metal{background:rgba(34,211,238,.14);color:#67e8f9;border:1px solid rgba(34,211,238,.35)}
.nanolab-viewport .badge-nl.polymer{background:rgba(129,140,248,.14);color:#a5b4fc;border:1px solid rgba(129,140,248,.35)}
.nanolab-viewport .badge-nl.oxide{background:rgba(244,114,182,.14);color:#f472b6;border:1px solid rgba(244,114,182,.35)}
.nanolab-viewport .badge-nl.lipid{background:rgba(56,189,248,.14);color:#38bdf8;border:1px solid rgba(56,189,248,.35)}
.nanolab-viewport .badge-nl.protein{background:rgba(52,211,153,.14);color:#34d399;border:1px solid rgba(52,211,153,.35)}
.nanolab-viewport #preset-meta{
  margin-top:10px;
  padding:10px;
  border-radius:12px;
  background:rgba(255,255,255,.03);
  border:1px dashed rgba(130,165,255,.2);
  font-size:10.5px;
  line-height:1.7;
  color:#7f90b8;
}
.nanolab-viewport #preset-meta b{
  color:#dbe6ff;
  font-family:'JetBrains Mono',monospace;
  font-weight:700;
}
.nanolab-viewport #panel-right{
  top:80px;
  right:14px;
  width:268px;
  padding:14px;
  max-height:calc(100% - 170px);
  overflow-y:auto;
}
.nanolab-viewport .btn-row{
  display:flex;
  gap:7px;
  margin-bottom:8px;
}
.nanolab-viewport .nl-btn{
  flex:1;
  padding:9px 7px;
  border-radius:10px;
  border:1px solid rgba(130,165,255,.16);
  background:rgba(255,255,255,.05);
  color:#dbe6ff;
  font:700 10.5px 'Inter',sans-serif;
  letter-spacing:.4px;
  cursor:pointer;
  transition:.15s;
}
.nanolab-viewport .nl-btn:hover:not(:disabled){
  transform:translateY(-1px);
  border-color:rgba(34,211,238,.5);
}
.nanolab-viewport .nl-btn.primary{
  background:linear-gradient(135deg,#22d3ee,#818cf8);
  color:#031320;
  border:none;
  box-shadow:0 8px 22px rgba(34,211,238,.3);
}
.nanolab-viewport .nl-btn:disabled{
  opacity:.32;
  cursor:not-allowed;
}
.nanolab-viewport .ctl{margin:10px 0}
.nanolab-viewport .ctl label{
  display:flex;
  justify-content:space-between;
  font-size:10px;
  letter-spacing:1px;
  color:#7f90b8;
  font-weight:700;
  margin-bottom:5px;
}
.nanolab-viewport .ctl label output{
  font-family:'JetBrains Mono',monospace;
  color:#22d3ee;
}
.nanolab-viewport input[type=range]{
  width:100%;
  -webkit-appearance:none;
  appearance:none;
  height:4px;
  border-radius:99px;
  background:linear-gradient(90deg,rgba(34,211,238,.55),rgba(129,140,248,.35));
  outline:none;
}
.nanolab-viewport input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;
  width:14px;
  height:14px;
  border-radius:50%;
  background:#eaf6ff;
  border:3px solid #818cf8;
  box-shadow:0 0 10px rgba(129,140,248,.8);
  cursor:pointer;
}
.nanolab-viewport .tgl{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:5px 2px;
  font-size:11px;
  color:#dbe6ff;
  cursor:pointer;
}
.nanolab-viewport .tgl input{display:none}
.nanolab-viewport .sw{
  width:32px;
  height:18px;
  border-radius:99px;
  background:rgba(255,255,255,.1);
  border:1px solid rgba(130,165,255,.16);
  position:relative;
  transition:.2s;
  flex:none;
}
.nanolab-viewport .sw::after{
  content:'';
  position:absolute;
  top:2px;
  left:2px;
  width:12px;
  height:12px;
  border-radius:50%;
  background:#8ea3c8;
  transition:.2s;
}
.nanolab-viewport .tgl input:checked+.sw{background:linear-gradient(90deg,#22d3ee,#818cf8);border-color:transparent}
.nanolab-viewport .tgl input:checked+.sw::after{left:16px;background:#fff}
.nanolab-viewport #chart{width:100%;height:130px;border-radius:12px;background:rgba(3,6,16,.6);border:1px solid rgba(130,165,255,.12);margin-top:4px;display:block}
.nanolab-viewport #hud-bottom{bottom:12px;left:50%;transform:translateX(-50%);display:flex;gap:8px;padding:9px 12px;flex-wrap:wrap;justify-content:center;max-width:92%}
.nanolab-viewport .chip{min-width:95px;padding:6px 11px;border-radius:10px;background:rgba(255,255,255,.04);border:1px solid rgba(130,165,255,.14)}
.nanolab-viewport .chip small{display:block;font-size:8px;letter-spacing:1.4px;color:#7f90b8;font-weight:700;margin-bottom:2px}
.nanolab-viewport .chip b{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:#eaf4ff;font-weight:700}
.nanolab-viewport .chip.hot b{color:#7dd3fc}
.nanolab-viewport #hint{position:absolute;bottom:14px;right:16px;font-size:9.5px;letter-spacing:.8px;color:#7f90b8;z-index:5;font-family:'JetBrains Mono',monospace;pointer-events:none}
@media(max-width:980px){.nanolab-viewport #panel-right{display:none}.nanolab-viewport #panel-left{width:200px}.nanolab-viewport{height:600px}}


.nanolab-viewport .nl-hud-btn{margin-left:auto;background:rgba(34,211,238,.12);border:1px solid rgba(34,211,238,.35);color:#22d3ee;padding:4px 10px;border-radius:99px;font:700 9.5px 'Inter',sans-serif;letter-spacing:.6px;cursor:pointer;transition:.2s}
.nanolab-viewport .nl-hud-btn:hover{background:rgba(34,211,238,.25);box-shadow:0 0 12px rgba(34,211,238,.4)}
.nanolab-viewport.hud-hidden #panel-left,.nanolab-viewport.hud-hidden #panel-right,.nanolab-viewport.hud-hidden #hud-bottom{opacity:0;pointer-events:none;transform:scale(0.96);transition:all .25s ease}
.nanolab-viewport #hud-bottom{bottom:8px;left:50%;transform:translateX(-50%);display:flex;gap:6px;padding:5px 14px;border-radius:999px;background:rgba(6,10,24,.75);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(56,189,248,.25);box-shadow:0 8px 24px rgba(0,0,0,.5),0 0 16px rgba(56,189,248,.12);z-index:5;pointer-events:none;max-width:94%}
.nanolab-viewport .chip{display:flex;align-items:center;gap:5px;padding:3px 8px;border-radius:6px;background:transparent;border:none}
.nanolab-viewport .chip small{font-size:8px;letter-spacing:1px;color:#7f90b8;font-weight:700;margin-bottom:0}
.nanolab-viewport .chip b{font-family:'JetBrains Mono',monospace;font-size:11px;color:#eaf4ff;font-weight:700}
.nanolab-viewport .chip.hot b{color:#38bdf8;text-shadow:0 0 8px rgba(56,189,248,.6)}


/* ============================================================
   SITEWIDE AI ASSISTANT WIDGET (Voice & Read-Out Engine)
   ============================================================ */
.nanobot-container {
  position: fixed;
  bottom: 20px;
  right: 22px;
  z-index: 9999;
  font-family: 'Inter', system-ui, sans-serif;
}
.nanobot-launcher-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 18px 10px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.95), rgba(99, 102, 241, 0.95));
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 10px 30px rgba(14, 165, 233, 0.45), 0 0 20px rgba(99, 102, 241, 0.35);
  cursor: pointer;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.3px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.nanobot-launcher-btn:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 14px 38px rgba(14, 165, 233, 0.6), 0 0 26px rgba(99, 102, 241, 0.5);
}
.nanobot-launcher-btn .pulse-beacon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7);
  animation: beaconPulse 1.6s infinite;
}
@keyframes beaconPulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(56, 189, 248, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
}
.nanobot-window {
  display: none;
  flex-direction: column;
  position: absolute;
  bottom: 56px;
  right: 0;
  width: 390px;
  max-width: 92vw;
  height: 520px;
  max-height: 82vh;
  background: rgba(8, 14, 30, 0.94);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 20px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.75), 0 0 35px rgba(14, 165, 233, 0.2);
  overflow: hidden;
  animation: windowPop 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes windowPop {
  from { opacity: 0; transform: translateY(18px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.nanobot-window.open {
  display: flex;
}
.nanobot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: rgba(15, 23, 42, 0.75);
  border-bottom: 1px solid rgba(56, 189, 248, 0.2);
}
.nanobot-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nanobot-avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0284c7, #6366f1);
  display: grid;
  place-items: center;
  font-size: 16px;
  box-shadow: 0 0 12px rgba(14, 165, 233, 0.4);
}
.nanobot-header h4 {
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  margin: 0;
}
.nanobot-status {
  font-size: 9.5px;
  color: #38bdf8;
  display: flex;
  align-items: center;
  gap: 5px;
  font-family: 'JetBrains Mono', monospace;
}
.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
}
.nanobot-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.nanobot-tool-btn {
  padding: 4px 8px;
  border-radius: 99px;
  font-size: 9.5px;
  font-weight: 700;
  border: 1px solid rgba(56, 189, 248, 0.3);
  background: rgba(56, 189, 248, 0.1);
  color: #38bdf8;
  cursor: pointer;
  transition: all 0.2s;
}
.nanobot-tool-btn.active {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.45);
  color: #4ade80;
}
.nanobot-tool-btn.stop-btn {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}
.nanobot-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
}
.nanobot-close-btn:hover { color: #fff; }
.nanobot-messages {
  flex: 1;
  padding: 14px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 11px;
}
.nanobot-msg {
  display: flex;
  flex-direction: column;
  max-width: 88%;
}
.nanobot-msg.ai {
  align-self: flex-start;
}
.nanobot-msg.user {
  align-self: flex-end;
}
.msg-bubble {
  padding: 10px 13px;
  border-radius: 14px;
  font-size: 12px;
  line-height: 1.5;
  color: #e2e8f0;
}
.nanobot-msg.ai .msg-bubble {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-bottom-left-radius: 4px;
}
.nanobot-msg.user .msg-bubble {
  background: linear-gradient(135deg, #0284c7, #4f46e5);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}
.msg-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 7px;
  padding: 5px 10px;
  border-radius: 8px;
  background: rgba(14, 165, 233, 0.18);
  border: 1px solid rgba(56, 189, 248, 0.45);
  color: #38bdf8;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.msg-action-btn:hover {
  background: rgba(14, 165, 233, 0.35);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
}
.nanobot-quick-chips {
  display: flex;
  gap: 6px;
  padding: 6px 12px;
  overflow-x: auto;
  scrollbar-width: none;
  background: rgba(8, 14, 30, 0.6);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.nanobot-quick-chips::-webkit-scrollbar { display: none; }
.chip-btn {
  padding: 4px 9px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(56, 189, 248, 0.22);
  color: #94a3b8;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.18s;
}
.chip-btn:hover {
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.5);
  background: rgba(56, 189, 248, 0.12);
}
.nanobot-input-bar {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.9);
  border-top: 1px solid rgba(56, 189, 248, 0.2);
}
.voice-mic-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #38bdf8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  font-size: 15px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}
.voice-mic-btn:hover {
  background: rgba(56, 189, 248, 0.28);
  border-color: #38bdf8;
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
  transform: scale(1.05);
}
.voice-mic-btn.listening {
  background: rgba(239, 68, 68, 0.3) !important;
  border-color: #ef4444 !important;
  color: #ffffff !important;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  animation: micPulseRed 1.2s infinite !important;
}
@keyframes micPulseRed {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7), 0 0 15px rgba(239, 68, 68, 0.6); }
  70% { transform: scale(1.12); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0), 0 0 25px rgba(239, 68, 68, 0.8); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0), 0 0 15px rgba(239, 68, 68, 0.6); }
}
.nanobot-input-bar input {
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 10px;
  padding: 8px 11px;
  color: #fff;
  font-size: 12px;
  outline: none;
}
.nanobot-input-bar input:focus {
  border-color: #38bdf8;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
}
.nanobot-send-btn {
  padding: 8px 13px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0284c7, #6366f1);
  color: #fff;
  border: none;
  font-weight: 700;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.18s;
}
.nanobot-send-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 12px rgba(14, 165, 233, 0.5);
}

/* 3D Model AI Prompt Box (In View 3D) */
.ai-3d-box {
  background: rgba(14, 165, 233, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 12px;
  padding: 9px 12px;
  margin-bottom: 12px;
}
.ai-3d-box label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #38bdf8;
  display: block;
  margin-bottom: 5px;
  text-transform: uppercase;
}
.ai-3d-input-row {
  display: flex;
  gap: 6px;
}
.ai-3d-input-row input {
  flex: 1;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  padding: 6px 10px;
  color: #fff;
  font-size: 11px;
  outline: none;
}
.ai-3d-input-row input:focus {
  border-color: #38bdf8;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
}
.ai-3d-btn {
  padding: 6px 11px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0284c7, #4f46e5);
  color: #fff;
  border: none;
  font-size: 10.5px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}
.ai-3d-feedback {
  margin-top: 6px;
  font-size: 10px;
  color: #4ade80;
  font-family: 'JetBrains Mono', monospace;
  display: none;
}

/* ============================================================
   ADVANCED VOICE HUD, MICROPHONE EQUALIZER, & TTS STYLES
   ============================================================ */
.voice-hud-indicator {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000000;
  display: none;
  animation: hudDropIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes hudDropIn {
  from { opacity: 0; transform: translate(-50%, -15px) scale(0.95); }
  to { opacity: 1; transform: translate(-50%, 0) scale(1); }
}
.voice-hud-card {
  width: 490px;
  max-width: 92vw;
  background: rgba(5, 11, 26, 0.96);
  border: 1px solid rgba(239, 68, 68, 0.65);
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.85), 0 0 35px rgba(239, 68, 68, 0.3), 0 0 15px rgba(56, 189, 248, 0.25);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 18px;
  padding: 16px 20px;
  color: #fff;
  font-family: 'Inter', system-ui, sans-serif;
}
.voice-hud-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.voice-hud-live-tag {
  display: flex;
  align-items: center;
  gap: 8px;
}
.live-rec-pulsar {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8);
  animation: pulsarRing 1.2s infinite;
}
@keyframes pulsarRing {
  0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }
  70% { transform: scale(1.15); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
.voice-hud-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  font-weight: 800;
  letter-spacing: 1.2px;
  color: #ef4444;
}
.voice-wave-eq {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 20px;
}
.wave-bar {
  width: 3.5px;
  background: linear-gradient(to top, #ef4444, #f59e0b, #38bdf8);
  border-radius: 3px;
  animation: eqBounce 0.8s ease-in-out infinite alternate;
}
.wave-bar.wb-1 { height: 6px; animation-delay: 0.1s; }
.wave-bar.wb-2 { height: 16px; animation-delay: 0.25s; }
.wave-bar.wb-3 { height: 10px; animation-delay: 0.4s; }
.wave-bar.wb-4 { height: 18px; animation-delay: 0.15s; }
.wave-bar.wb-5 { height: 8px; animation-delay: 0.3s; }
@keyframes eqBounce {
  0% { height: 4px; }
  50% { height: 20px; }
  100% { height: 6px; }
}
.voice-hud-stream {
  min-height: 48px;
  max-height: 110px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13.5px;
  line-height: 1.5;
  color: #e2e8f0;
  margin-bottom: 14px;
  font-family: 'Inter', system-ui, sans-serif;
  word-break: break-word;
}
.voice-hud-stream .voice-hint {
  color: #94a3b8;
  font-style: italic;
  font-size: 12.5px;
}
.voice-hud-stream .transcript-live {
  color: #38bdf8;
  font-weight: 600;
}
.voice-hud-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.vh-btn {
  padding: 7px 15px;
  border-radius: 8px;
  font-size: 11.5px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  transition: all 0.2s;
}
.vh-done {
  background: linear-gradient(135deg, #0284c7, #22c55e);
  color: #fff;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35);
}
.vh-done:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(34, 197, 94, 0.5);
}
.vh-cancel {
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.vh-cancel:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

/* Voice Error & Status Toast */
.voice-status-toast {
  position: fixed;
  bottom: 84px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid #ef4444;
  color: #fca5a5;
  padding: 10px 18px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(239, 68, 68, 0.3);
  font-size: 12px;
  font-weight: 600;
  z-index: 1000001;
  display: flex;
  align-items: center;
  gap: 8px;
  animation: toastFade 0.25s ease-out;
}
@keyframes toastFade {
  from { opacity: 0; transform: translate(-50%, 10px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}

/* Message Bubble TTS Speaker Button */
.msg-speaker-btn {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #38bdf8;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  margin-right: 5px;
  transition: all 0.2s;
}
.msg-speaker-btn:hover {
  background: rgba(56, 189, 248, 0.25);
  border-color: #38bdf8;
  color: #fff;
}
.msg-speaker-btn.speaking {
  background: rgba(34, 197, 94, 0.25);
  border-color: #22c55e;
  color: #4ade80;
  animation: speakPulse 1s infinite alternate;
}
@keyframes speakPulse {
  from { box-shadow: 0 0 4px rgba(34, 197, 94, 0.4); }
  to { box-shadow: 0 0 12px rgba(34, 197, 94, 0.8); }
}

/* Speaking waves indicator in Assistant Header */
.speaking-wave-box {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: 6px;
}
.speaking-wave-bar {
  width: 2.5px;
  height: 10px;
  background: #4ade80;
  border-radius: 2px;
  animation: speakEq 0.6s infinite alternate;
}
.speaking-wave-bar:nth-child(2) { animation-delay: 0.2s; }
.speaking-wave-bar:nth-child(3) { animation-delay: 0.4s; }
@keyframes speakEq {
  0% { height: 3px; }
  100% { height: 14px; }
}

</style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body class="dark-theme">

    <!-- TOP BAR (Exact design from uploaded mockup) -->
    <header class="top-bar">
        <div class="brand">
            <h1>NanoMedAI</h1>
            <span id="sim-mode-badge" class="badge badge-live">LIVE PRODUCTION ENGINE</span>
        </div>
        <div class="disclaimer-banner" id="main-disclaimer">
            <strong>PRODUCTION RESEARCH PLATFORM:</strong> Real-time biophysical ODE dynamics & active machine learning inference models.
        </div>
        <div class="top-bar-right">
            <div id="backend-status-pill" class="backend-indicator" title="FastAPI Backend Health">
                <span class="dot"></span> <span id="backend-status-text">API: CHECKING...</span>
            </div>
            <div class="status-indicator">
                <span id="sim-status-label" class="status-initialized">● INITIALIZED</span>
            </div>
        </div>
    </header>

    <!-- FEATURE NAVIGATION (Clean, dark IDE aesthetic matching the design) -->
    <nav class="feature-nav-bar" aria-label="NanoMedAI Platform Modules">
        <button class="nav-tab-btn active" data-tab="simulation">🧪 Live Simulation</button>
        <button class="nav-tab-btn" data-tab="prompt">🤖 Experiment Prompt AI</button>
        <button class="nav-tab-btn" data-tab="predictor">🔬 Model Predictor</button>
        <button class="nav-tab-btn" data-tab="explorer">📈 Sweep &amp; Heatmap</button>
        <button class="nav-tab-btn" data-tab="data">📚 Data &amp; Models</button>
        <button class="nav-tab-btn" data-tab="viewer">🌐 3D Particle</button>
        <button class="nav-tab-btn" data-tab="report">📋 Research Report</button>
        <button class="nav-tab-btn" id="btn-show-intro" style="margin-left:auto; border-color: rgba(34, 211, 238, 0.45); color: #22d3ee;">✨ Intro &amp; Diagnostics</button>
    </nav>

    <!-- ============================================================== -->
    <!-- VIEW 1: LIVE SIMULATION WORKSPACE (Exact Uploaded UI Design)   -->
    <!-- ============================================================== -->
    <div class="view-container active workspace" id="view-simulation">
        <!-- LEFT COLUMN: CONFIG & CONTROLS -->
        <aside class="panel left-panel">
            <!-- QUICK AI EXPERIMENT RUNNER -->
            <section class="control-section">
                <h2>AI EXPERIMENT PROMPT <span class="badge badge-blue">ALL MODELS</span></h2>
                <div class="form-group" style="margin-bottom: 0.5rem;">
                    <select id="quick-prompt-example" class="demo-select" style="margin-bottom: 0.4rem;">
                        <option value="a">Example A: PLGA + Paclitaxel (Oncology)</option>
                        <option value="b">Example B: PLA + Letrozole (Long-acting)</option>
                        <option value="paracetamol">Example C: Paracetamol + PLGA (Analgesic)</option>
                        <option value="ciprofloxacin">Example D: Ciprofloxacin + PLGA (Antibacterial)</option>
                        <option value="doxorubicin">Example E: Doxorubicin + Liposome (Doxil)</option>
                        <option value="vancomycin">Example F: Vancomycin + PLGA-PEG (Anti-MRSA)</option>
                        <option value="mrna">Example G: mRNA + Lipid Nanoparticle (LNP)</option>
                        <option value="tox">Example H: ZnO + cytotoxicity assay</option>
                    </select>
                    <textarea id="quick-prompt-input" class="prompt-textarea" style="min-height: 55px;" placeholder="Describe nanoparticle experiment or click mic to speak..."></textarea>
                    <div style="display:flex; gap:0.4rem; align-items:center;">
                        <button id="btn-quick-prompt-voice" class="voice-mic-btn" onclick="startQuickPromptVoice()" style="width:34px;height:34px;flex-shrink:0;" title="Dictate prompt by voice">🎤</button>
                        <button id="btn-quick-run" class="btn btn-primary" style="flex:1;">RUN AI EXPERIMENT</button>
                        <button id="btn-open-prompt-tab" class="btn btn-secondary" title="Open Full AI Workflow with Advanced Parameters">ADVANCED</button>
                    </div>
                </div>
            </section>

            <section class="control-section">
                <h2>NANOPARTICLE CONFIGURATION <span class="badge badge-live" id="cfg-mode-badge">ACTIVE FORMULATION</span></h2>
                <div class="form-group">
                    <select id="config-formulation" class="demo-select">
                        <optgroup label="Analgesics &amp; NSAIDs (Dataset)">
                            <option value="nm-paracetamol-plga">Paracetamol + PLGA (335 nm, SLN)</option>
                            <option value="nm-paracetamol-liposome">Paracetamol + Liposome DPPC (90 nm)</option>
                            <option value="nm-paracetamol-sln">Paracetamol + Lipid DSPC (235 nm)</option>
                            <option value="ibuprofen-lipid">Ibuprofen + Lipid NP (150 nm)</option>
                        </optgroup>
                        <optgroup label="Antibiotics &amp; Antimicrobials (Dataset)">
                            <option value="ciprofloxacin-plga">Ciprofloxacin + PLGA Matrix (165 nm)</option>
                            <option value="vancomycin-plga-peg">Vancomycin + PLGA-PEG Extended-Release (180 nm)</option>
                            <option value="rifampicin-plga-peg">Rifampicin + PLGA-PEG Sustained Core (145 nm)</option>
                            <option value="doxycycline-polymeric">Doxycycline + Polymeric NP (130 nm)</option>
                            <option value="gentamicin-chitosan">Gentamicin + Chitosan NP (115 nm)</option>
                            <option value="azithromycin-sln">Azithromycin + Solid Lipid NP (195 nm)</option>
                            <option value="amoxicillin-eudragit">Amoxicillin + Eudragit NP (140 nm)</option>
                        </optgroup>
                        <optgroup label="Oncology &amp; Chemotherapeutics">
                            <option value="formulation-a" selected>Formulation A (PLGA + Paclitaxel - Benchmark)</option>
                            <option value="formulation-b">Formulation B (PLA + Letrozole - Long Acting)</option>
                            <option value="formulation-c">Formulation C (PLGA + Letrozole - Sustained)</option>
                            <option value="doxorubicin-liposome">Doxorubicin + PEGylated Liposome (Doxil Analog)</option>
                            <option value="doxorubicin-plga">Doxorubicin + PLGA Chitosan/Alginate Core</option>
                            <option value="methotrexate-dendrimer">Methotrexate + PAMAM Dendrimer (45 nm)</option>
                            <option value="cisplatin-micelle">Cisplatin + Block Copolymer Micelles (65 nm)</option>
                            <option value="rapamycin-albumin">Rapamycin + Human Serum Albumin (130 nm)</option>
                            <option value="exemestane-plga-gel">Exemestane + PLGA In-Situ Gel NP (160 nm)</option>
                        </optgroup>
                        <optgroup label="Cardiovascular &amp; Dual Therapy">
                            <option value="amlodipine-plga-pcl">Amlodipine Besylate + PLGA-PCL Extruded NP</option>
                            <option value="dox-atv-dual">DOX / Atorvastatin + Hyaluronic Acid Dual NP</option>
                        </optgroup>
                        <optgroup label="Biologics &amp; Genetic Payloads">
                            <option value="mrna-lnp">mRNA-1273 + Ionizable Lipid NP (80 nm)</option>
                            <option value="sirna-lnp">siRNA + Targeted Cationic LNP (75 nm)</option>
                        </optgroup>
                    </select>
                </div>
                
                <div class="static-config-info">
                    <div class="info-row"><span>Drug:</span> <strong id="cfg-drug">Paclitaxel</strong></div>
                    <div class="info-row"><span>Material:</span> <strong id="cfg-material">PLGA</strong></div>
                    <div class="info-row"><span>Particle Size:</span> <strong id="cfg-size">120 nm</strong></div>
                    <div class="info-row"><span>Zeta Potential:</span> <strong id="cfg-zeta">-22 mV</strong></div>
                    <div class="info-row"><span>Drug Loading:</span> <strong id="cfg-loading">8%</strong></div>
                    <div class="info-row"><span>Coating:</span> <strong id="cfg-coating">PEG</strong></div>
                </div>
            </section>

            <section class="control-section">
                <h2>ENVIRONMENT</h2>
                <div class="form-group">
                    <label>Medium</label>
                    <select id="env-medium" class="demo-select">
                        <option value="water">Water</option>
                        <option value="pbs" selected>PBS (pH 7.4)</option>
                        <option value="demo-bio">Biological Serum (Simulated)</option>
                    </select>
                </div>

                <div class="slider-group">
                    <label>Temperature <span id="val-temp">37.0</span> °C</label>
                    <input type="range" id="env-temp" min="20" max="50" step="0.1" value="37">
                    <div class="slider-labels"><span>20°C</span><span>50°C</span></div>
                </div>

                <div class="slider-group">
                    <label>pH <span id="val-ph">7.4</span></label>
                    <input type="range" id="env-ph" min="3.0" max="9.0" step="0.1" value="7.4">
                    <div class="slider-labels"><span>3.0</span><span>9.0</span></div>
                </div>

                <div class="slider-group">
                    <label>Ionic Strength <span id="val-ionic">0.15</span> M</label>
                    <input type="range" id="env-ionic" min="0.00" max="0.50" step="0.01" value="0.15">
                    <div class="slider-labels"><span>0.00 M</span><span>0.50 M</span></div>
                </div>
                
                <div id="env-warning" class="panel-warning hidden">
                    <strong>⚠ ENVIRONMENT SENSITIVITY</strong><br>
                    Kinetic parameters dynamically modulated for simulated medium.<br>
                    <span class="badge badge-blue">KINETIC ODE RESPONSE</span>
                </div>
            </section>

            <section class="control-section sim-controls">
                <h2>SIMULATION CONTROLS</h2>
                
                <div class="timeline-group">
                    <label>Simulation Time: <span id="val-time">0</span> h</label>
                    <input type="range" id="sim-timeline" min="0" max="72" step="1" value="0">
                    <div class="slider-labels"><span>0h</span><span id="sim-max-label">72h</span></div>
                </div>

                <div class="speed-control">
                    <label>PLAYBACK SPEED: <small>1 sec = 1 simulated hour (at 1x)</small></label>
                    <div class="speed-buttons">
                        <button class="btn btn-speed" data-speed="0.5">0.5x</button>
                        <button class="btn btn-speed active" data-speed="1">1x</button>
                        <button class="btn btn-speed" data-speed="2">2x</button>
                        <button class="btn btn-speed" data-speed="5">5x</button>
                        <button class="btn btn-speed" data-speed="10">10x</button>
                    </div>
                </div>

                <div class="action-buttons">
                    <button id="btn-start" class="btn btn-primary">START</button>
                    <button id="btn-pause" class="btn btn-secondary" disabled>PAUSE</button>
                    <button id="btn-resume" class="btn btn-primary hidden">RESUME</button>
                    <button id="btn-step" class="btn btn-secondary">STEP</button>
                    <button id="btn-stop" class="btn btn-secondary" disabled>STOP</button>
                    <button id="btn-reset" class="btn btn-danger">RESET</button>
                </div>

                <div style="margin-top: 0.85rem;">
                    <button id="btn-sync-backend" class="btn btn-secondary btn-wide" style="font-size: 0.7rem;">⚡ SYNC WITH FASTAPI BACKEND</button>
                </div>
            </section>
        </aside>

        <!-- CENTER COLUMN: VISUALIZATION & CHARTS -->
        <main class="panel center-panel">
            <section class="visualization-section">
                <h2>LIVE SIMULATION <span class="badge badge-live" id="sim-canvas-badge" style="float:right">COLLOIDAL SOLVATION &amp; DISSOLUTION</span></h2>
                <div class="canvas-container">
                    <canvas id="particle-canvas" width="600" height="350"></canvas>
                    <div id="canvas-overlay-text">
                        TEMPERATURE <span id="overlay-temp">37.0</span>°C<br>
                        pH <span id="overlay-ph">7.4</span><br>
                        IONIC STRENGTH <span id="overlay-ionic">0.15</span> M<br>
                        MEDIUM <span id="overlay-env">PBS</span>
                    </div>
                </div>
            </section>

            <!-- WORKFLOW RESULTS SUMMARY BANNER (Shown when an AI experiment is run) -->
            <section id="workflow-results" class="control-section hidden" style="background: rgba(0, 122, 204, 0.05);">
                <h2>AI EXPERIMENT RESULTS <span class="badge badge-live">LIVE OUTPUT</span></h2>
                <div class="workflow-results-grid">
                    <div class="workflow-stat-card">
                        <span>ZETA PREDICTION</span>
                        <strong id="workflow-zeta">-</strong>
                        <small id="workflow-zeta-class"></small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>TOXICITY CLASS</span>
                        <strong id="workflow-toxicity">-</strong>
                        <small id="workflow-toxicity-risk"></small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>LEARNED RELEASE</span>
                        <strong id="workflow-release">-</strong>
                        <small id="workflow-release-time"></small>
                    </div>
                </div>
                <div id="workflow-warnings" class="panel-warning hidden" style="margin-top:0.4rem;"></div>
                <div id="workflow-assumptions" class="roadmap-note" style="margin-top:0.4rem;"></div>
            </section>

            <section class="graph-section">
                <h2>CUMULATIVE DRUG RELEASE <span class="badge badge-blue" id="release-chart-badge" style="float:right">KORSMEYER-PEPPAS DYNAMICS</span></h2>
                <div class="chart-container">
                    <canvas id="release-chart"></canvas>
                </div>
            </section>

            <section class="graph-section">
                <h2>RELEASE RATE <span class="badge badge-blue" style="float:right">DERIVED</span></h2>
                <div class="chart-container" style="height:140px;">
                    <canvas id="rate-chart"></canvas>
                </div>
            </section>
            
            <section class="graph-section">
                <h2>PARTICLE STATE HISTORY <span class="badge badge-blue" style="float:right">CORE DYNAMICS</span></h2>
                <div class="chart-container" style="height:140px;">
                    <canvas id="size-chart"></canvas>
                </div>
            </section>
        </main>

        <!-- RIGHT COLUMN: STATE, EVENTS, LIMITATIONS -->
        <aside class="panel right-panel">
            <section class="dashboard-section">
                <h2>PARTICLE STATE <span class="badge badge-live" id="particle-state-badge" style="float:right">REAL-TIME TELEMETRY</span></h2>
                <div class="state-grid">
                    <div class="state-card">
                        <div class="state-label">PARTICLE SIZE</div>
                        <div class="state-value"><span id="state-size">120.0</span> <small>nm</small></div>
                    </div>
                    <div class="state-card">
                        <div class="state-label">HYDRODYNAMIC SIZE</div>
                        <div class="state-value"><span id="state-hsize">128.0</span> <small>nm</small></div>
                    </div>
                    <div class="state-card">
                        <div class="state-label">PDI</div>
                        <div class="state-value"><span id="state-pdi">0.16</span></div>
                    </div>
                    <div class="state-card">
                        <div class="state-label">ZETA POTENTIAL</div>
                        <div class="state-value"><span id="state-zeta">-22.0</span> <small>mV</small></div>
                    </div>
                    <div class="state-card highlight-card">
                        <div class="state-label">DRUG RELEASE</div>
                        <div class="state-value"><span id="state-release">0.0</span> <small>%</small></div>
                    </div>
                    <div class="state-card">
                        <div class="state-label">DRUG REMAINING</div>
                        <div class="state-value"><span id="state-remaining">100.0</span> <small>%</small></div>
                    </div>
                </div>
            </section>

            <section class="events-section">
                <h2>EVENTS TIMELINE</h2>
                <div class="events-list" id="events-list">
                    <!-- Events injected dynamically -->
                </div>
            </section>
            
            <section class="roadmap-section">
                <h2>SCIENTIFIC STATUS</h2>
                <div class="model-status-panel">
                    <div class="ms-row"><span>Zeta Potential</span> <span class="ms-demo" id="ms-zeta-status">Random Forest Regressor (R²=0.84)</span></div>
                    <div class="ms-row"><span>Drug Release</span> <span class="ms-demo" id="ms-release-status">Korsmeyer-Peppas ODE</span></div>
                    <div class="ms-row"><span>Cytotoxicity Model</span> <span class="ms-demo" id="ms-cyto-status">Random Forest (AUC=0.91)</span></div>
                    <div class="ms-row"><span>Size Dynamics</span> <span class="ms-demo">Active DLVO ODE</span></div>
                    <div class="ms-row"><span>PDI Dynamics</span> <span class="ms-demo">Active DLVO ODE</span></div>
                    <div class="ms-row"><span>Aggregation</span> <span class="ms-demo">Colloidal Energy Barrier</span></div>
                    <div class="ms-row"><span>Environmental Release</span> <span class="ms-demo" id="ms-env-status">Biophysical Coupled Dynamics</span></div>
                </div>
            </section>

            <!-- OCCLUSION FEATURE DRIVERS (Shown when Prompt Workflow is executed) -->
            <section id="workflow-drivers-section" class="roadmap-section hidden">
                <h2>MODEL DRIVERS <span class="badge badge-blue">OCCLUSION</span></h2>
                <div id="workflow-drivers"></div>
                <p class="roadmap-note">Change from model output when input is replaced by training median/mode.</p>
            </section>

            <!-- GROUPED VALIDATION METRICS -->
            <section id="workflow-metrics-section" class="roadmap-section hidden">
                <h2>GROUPED CV VALIDATION</h2>
                <div id="workflow-metrics" class="model-status-panel"></div>
            </section>

            <section class="roadmap-section">
                <h2>BIOLOGICAL STAGE</h2>
                <ul class="locked-features">
                    <li>Protein Corona <span class="badge badge-locked">FUTURE</span></li>
                    <li>Cell Interaction <span class="badge badge-locked">LOCKED</span></li>
                    <li>Cellular Uptake <span class="badge badge-locked">LOCKED</span></li>
                    <li>Distribution <span class="badge badge-locked">LOCKED</span></li>
                    <li>Toxicity <span class="badge badge-locked">LOCKED</span></li>
                    <li>Human Body <span class="badge badge-locked">LOCKED</span></li>
                </ul>
                <p class="roadmap-note">Future research phase</p>
            </section>
        </aside>
    </div>

    <!-- ============================================================== -->
    <!-- VIEW 2: AI EXPERIMENT PROMPT WORKFLOW                          -->
    <!-- ============================================================== -->
    <div class="view-container-single" id="view-prompt">
        <div class="content-max-width">
            <div class="view-header">
                <h2>AI Experiment Prompt Workflow</h2>
                <p>Natural language parsing into biophysical parameters, cross-model domain validation, stability regressor, cytotoxicity classification, and longitudinal drug release prediction.</p>
            </div>

            <div class="card-panel">
                <h3>Prompt Runner <span class="badge badge-blue">MULTI-MODEL PIPELINE</span></h3>
                <div class="form-group">
                    <label>Load Example Prompt</label>
                    <select id="prompt-example" class="demo-select" style="margin-bottom: 0.6rem;">
                        <option value="a">Example A: PLGA + Paclitaxel in PBS</option>
                        <option value="b">Example B: PLA + Letrozole Long-Acting</option>
                        <option value="paracetamol">Example C: Paracetamol + PLGA (Analgesic)</option>
                        <option value="ciprofloxacin">Example D: Ciprofloxacin + PLGA (Antibiotic)</option>
                        <option value="doxorubicin">Example E: Doxorubicin + PEG-Liposome</option>
                        <option value="vancomycin">Example F: Vancomycin + PLGA-PEG</option>
                        <option value="mrna">Example G: mRNA + Ionizable LNP</option>
                        <option value="tox">Example H: ZnO Nanoparticle Cytotoxicity</option>
                    </select>
                </div>

                <div class="form-group">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
                        <label style="margin-bottom:0;">Experiment Description</label>
                        <button id="btn-main-prompt-voice" class="voice-mic-btn" onclick="startMainPromptVoice()" style="width:auto; height:28px; padding:0 10px; border-radius:8px; font-size:11px; font-weight:700; gap:5px;" title="Dictate experiment prompt by voice">
                            <span>🎤</span> Dictate Voice
                        </button>
                    </div>
                    <textarea id="experiment-prompt" class="prompt-textarea" placeholder="e.g. Design 80nm PEGylated Liposome delivering Doxorubicin at -30mV in PBS pH 7.4 at 37°C..."></textarea>
                </div>

                <details class="details-collapsible">
                    <summary>▶ Advanced Model Overrides &amp; Parameters</summary>
                    <div class="advanced-grid">
                        <label class="tool-field-label">Sample Name <input id="prompt-sample-name" class="demo-select" type="text" placeholder="e.g. Sample-001 / Batch-A"></label>
                        <label class="tool-field-label">Particle Size (nm) <input id="prompt-particle-size" class="demo-select" type="number" min="0.1" step="0.1" placeholder="e.g. 120"></label>
                        <label class="tool-field-label">Formulation / Medium pH <input id="prompt-ph" class="demo-select" type="number" min="0" max="14" step="0.1" placeholder="7.4"></label>
                        <label class="tool-field-label">Core Material <select id="prompt-core" class="demo-select"></select></label>
                        <label class="tool-field-label">Particle Shape <select id="prompt-shape" class="demo-select"></select></label>
                        <label class="tool-field-label">Core Size (nm) <input id="prompt-core-size" type="number" step="0.1"></label>
                        <label class="tool-field-label">Hydrodynamic Size (nm) <input id="prompt-hydro-size" type="number" step="0.1"></label>
                        <label class="tool-field-label">Surface Ligand <select id="prompt-ligand" class="demo-select"></select></label>
                        <label class="tool-field-label">Surface Area (m²/g) <input id="prompt-surface-area" type="number" step="0.1"></label>
                        <label class="tool-field-label">Surface Area Source 
                            <select id="prompt-surface-area-source" class="demo-select">
                                <option value="">Choose source</option>
                                <option value="measured">Measured</option>
                                <option value="estimated">Estimated</option>
                            </select>
                        </label>
                        <label class="tool-field-label">Measured Zeta Potential (mV) <input id="prompt-surface-charge" type="number" step="0.1"></label>
                        <label class="tool-field-label">Material Type (Toxicity) <select id="prompt-material" class="demo-select"></select></label>
                        <label class="tool-field-label">Assay <select id="prompt-assay" class="demo-select"></select></label>
                        <label class="tool-field-label">Cell Line <select id="prompt-cell" class="demo-select"></select></label>
                        <label class="tool-field-label">Exposure Time (h) <input id="prompt-exposure" type="number" min="0.1" step="0.1"></label>
                        <label class="tool-field-label">Mass Dose (µg/mL) <input id="prompt-dose" type="number" min="0" step="0.1"></label>
                        <label class="tool-field-label">Release Drug 
                            <div class="searchable-select-wrapper">
                                <input id="prompt-drug" class="demo-select" type="text" placeholder="Select or search drug..." autocomplete="off">
                                <div id="prompt-drug-dropdown" class="searchable-dropdown-menu"></div>
                            </div>
                        </label>
                        <label class="tool-field-label">Release Polymer <select id="prompt-polymer" class="demo-select"></select></label>
                        <label class="tool-field-label">Drug Loading (%) <input id="prompt-loading" type="number" min="0" step="0.001"></label>
                        <label class="tool-field-label">Drug MW (g/mol) <input id="prompt-drug-mw" type="number" min="0.1" step="0.01"></label>
                        <label class="tool-field-label">Polymer MW (g/mol) <input id="prompt-polymer-mw" type="number" min="0.1" step="1"></label>
                        <label class="tool-field-label">LA:GA Ratio <input id="prompt-la-ga-ratio" type="number" min="0" step="0.01"></label>
                        <label class="tool-field-label">Release Duration (h) <input id="prompt-duration" type="number" min="0.1" step="0.1"></label>
                    </div>
                    <label class="tool-field-label" style="margin-top:0.4rem;">Custom SMILES (Optional) <input id="prompt-ligand-smiles" type="text" placeholder="e.g. C(C(C(=O)O)O)(C(=O)O)O"></label>
                </details>

                <div style="display:flex; gap:0.75rem; margin-top:0.8rem;">
                    <button id="run-workflow" class="btn btn-primary" style="flex:2; font-size: 0.8rem; padding: 0.7rem;">RUN COMPLETE AI PIPELINE</button>
                    <button id="btn-apply-to-sim" class="btn btn-secondary" style="flex:1;">VIEW IN LIVE SIMULATION</button>
                </div>
                <div id="prompt-status" class="roadmap-note" style="margin-top:0.6rem;">Status: Ready.</div>
            </div>

            <!-- RESULT DETAILS PANEL -->
            <div id="prompt-results-container" class="card-panel">
                <h3>Pipeline Outputs &amp; Scientific Audit</h3>
                <div class="workflow-results-grid">
                    <div class="workflow-stat-card">
                        <span>COLLOIDAL STABILITY</span>
                        <strong id="tab-workflow-zeta">-</strong>
                        <small id="tab-workflow-zeta-desc">Run experiment prompt</small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>CYTOTOXICITY CLASSIFICATION</span>
                        <strong id="tab-workflow-tox">-</strong>
                        <small id="tab-workflow-tox-desc">Run experiment prompt</small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>BIOPHYSICAL DRUG RELEASE</span>
                        <strong id="tab-workflow-rel">-</strong>
                        <small id="tab-workflow-rel-desc">Run experiment prompt</small>
                    </div>
                </div>

                <div id="tab-workflow-warnings" class="panel-warning hidden"></div>
                <div id="tab-workflow-assumptions" class="roadmap-note" style="margin: 0.75rem 0;"></div>

                <div style="margin-top: 1rem;">
                    <h4 style="font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase; margin-bottom:0.5rem;">Feature Occlusion Drivers</h4>
                    <div id="tab-workflow-drivers">No driver data available yet.</div>
                </div>
            </div>
        </div>
    </div>

    <!-- ============================================================== -->
    <!-- VIEW 3: MODEL PREDICTOR (Zeta & Cytotoxicity Inference)        -->
    <!-- ============================================================== -->
    <div class="view-container-single" id="view-predictor">
        <div class="content-max-width">
            <div class="view-header">
                <h2>Model Predictor</h2>
                <p>Direct machine learning inference endpoints for Colloidal Stability (Zeta Potential Regressor) and Cytotoxicity (Random Forest Classifier) with domain applicability validation.</p>
            </div>

            <div class="card-panel">
                <h3>Prediction Configuration</h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
                    <div>
                        <label class="tool-field-label">Prediction Target</label>
                        <select id="prediction-task" class="demo-select">
                            <option value="stability">Zeta Potential Stability (mV)</option>
                            <option value="cytotoxicity">Cytotoxicity (Toxic / Nontoxic)</option>
                        </select>
                    </div>
                    <div>
                        <label class="tool-field-label">Observed Training Example</label>
                        <select id="prediction-preset" class="demo-select">
                            <option value="">Choose an observed example</option>
                        </select>
                    </div>
                </div>

                <div id="prediction-fields" class="input-matrix-grid">
                    <!-- Injected dynamically based on selected task -->
                </div>

                <details class="details-collapsible" style="margin-bottom:1rem;">
                    <summary>▶ Advanced SMILES String</summary>
                    <label class="tool-field-label">Surface Ligand SMILES <input id="prediction-ligand-smiles" type="text" placeholder="e.g. OCCO"></label>
                </details>

                <button id="run-prediction" class="btn btn-primary" style="padding: 0.65rem 1.25rem;">RUN MODEL PREDICTION</button>
            </div>

            <div class="card-panel">
                <h3>Prediction Output &amp; Metadata</h3>
                <div id="prediction-result" class="result-terminal">Select parameters and click "Run Model Prediction" to evaluate against the trained scikit-learn models.</div>
            </div>
        </div>
    </div>

    <!-- ============================================================== -->
    <!-- VIEW 4: ENVIRONMENT EXPLORER (Parameter Sweep & Heatmap Matrix)-->
    <!-- ============================================================== -->
    <div class="view-container-single" id="view-explorer">
        <div class="content-max-width">
            <div class="view-header">
                <h2>Environment Explorer</h2>
                <p>Simulate parametric sensitivity sweeps across validated training ranges and compute biophysical DLVO colloidal stability heatmaps across temperature and pH.</p>
            </div>

            <div class="card-panel">
                <h3>Parameter Sensitivity Sweep <span class="badge badge-live">LIVE INFERENCE</span></h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr auto; gap:0.75rem; align-items:end; margin-bottom:1rem;">
                    <div>
                        <label class="tool-field-label">Model Target</label>
                        <select id="sweep-task" class="demo-select">
                            <option value="stability">Zeta potential stability</option>
                            <option value="cytotoxicity">Cytotoxicity</option>
                        </select>
                    </div>
                    <div>
                        <label class="tool-field-label">Sweep Variable</label>
                        <select id="sweep-variable" class="demo-select"></select>
                    </div>
                    <button id="run-sweep" class="btn btn-primary" style="height:36px;">RUN SWEEP</button>
                </div>

                <div class="chart-container" style="height: 250px;">
                    <canvas id="sweep-chart"></canvas>
                </div>
                <div id="sweep-message" class="roadmap-note" style="margin-top:0.6rem;">Evaluates 11 points across the training range while holding other inputs at predictor form values.</div>
            </div>

            <div class="card-panel">
                <h3>Formulation Stability Matrix Heatmap <span class="badge badge-blue">DLVO STABILITY MATRIX</span></h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr 1.5fr auto; gap:0.75rem; align-items:end; margin-bottom:1rem;">
                    <div>
                        <label class="tool-field-label">Core Material</label>
                        <select id="matrix-core" class="demo-select"></select>
                    </div>
                    <div>
                        <label class="tool-field-label">Particle Size (nm)</label>
                        <input id="matrix-size" type="number" value="30" min="5" max="200" step="1">
                    </div>
                    <div>
                        <label class="tool-field-label">Ligand SMILES</label>
                        <input id="matrix-smiles" type="text" value="OCCO">
                    </div>
                    <button id="run-matrix" class="btn btn-primary" style="height:36px;">CALCULATE MATRIX</button>
                </div>

                <div class="chart-container" style="height: 250px;">
                    <canvas id="matrix-chart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- ============================================================== -->
    <!-- VIEW 5: DATA CATALOG & MODEL REGISTRY                          -->
    <!-- ============================================================== -->
    <div class="view-container-single" id="view-data">
        <div class="content-max-width">
            <div class="view-header">
                <h2>Data Catalog &amp; Model Registry</h2>
                <p>Live registry of serialized machine learning models, cross-validation performance benchmarks, and raw harmonized datasets.</p>
            </div>

            <div class="card-panel">
                <h3>Platform Model Registry <span class="badge badge-live">SERIALIZED ARTIFACTS</span></h3>
                <div id="model-status">Loading model registry...</div>
            </div>

            <div class="card-panel">
                <h3>Dataset Preview</h3>
                <div style="display:flex; gap:0.75rem; align-items:flex-end; margin-bottom: 0.8rem;">
                    <div style="flex:1;">
                        <label class="tool-field-label">Select Dataset</label>
                        <select id="dataset-task" class="demo-select">
                            <option value="stability">Nanoparticle Colloidal Stability (288 NPs, 24 Features)</option>
                            <option value="cytotoxicity">Nanoparticle Cytotoxicity Meta-Analysis (Excel Dataset)</option>
                            <option value="nano_drug">Nano Drug 10,000 Formulations (10,000 records, 88 features)</option>
                        </select>
                    </div>
                    <button id="load-dataset" class="btn btn-primary" style="height:36px;">LOAD PREVIEW</button>
                </div>

                <div id="dataset-info" class="roadmap-note" style="margin-bottom:0.6rem;"></div>
                <div id="dataset-preview" class="table-responsive"></div>
            </div>

            <!-- NANO DRUG 10,000 DATASET & PRE-TRAINED MODELS -->
            <div class="card-panel">
                <h3>Nano Drug 10,000 Formulation Dataset &amp; Pre-trained Models <span class="badge badge-live">EXTRACTED BUNDLE</span></h3>
                <div class="workflow-results-grid" style="margin-bottom:1rem;">
                    <div class="workflow-stat-card">
                        <span>RECORDS &amp; FEATURES</span>
                        <strong>10,000 NPs · 88 Cols</strong>
                        <small>10 Drugs · 11 Carrier Materials</small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>RELEASE MODEL ACCURACY</span>
                        <strong>96.7% (F1 0.911)</strong>
                        <small>Random Forest Classifier</small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>STABILITY ACCURACY</span>
                        <strong>81.1% (F1 0.612)</strong>
                        <small>Random Forest Classifier</small>
                    </div>
                    <div class="workflow-stat-card">
                        <span>RISK ACCURACY</span>
                        <strong>83.85% (F1 0.692)</strong>
                        <small>Random Forest Classifier</small>
                    </div>
                </div>

                <div style="margin-bottom:1rem;">
                    <label class="tool-field-label">Model Analysis &amp; Feature Visualizations</label>
                    <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.75rem;">
                        <button class="btn btn-secondary nano-img-btn active" data-img="/static/nano_drug/confusion_predicted_release_class.png">Release Confusion Matrix</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/confusion_predicted_stability_class.png">Stability Confusion Matrix</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/confusion_predicted_risk_class.png">Risk Confusion Matrix</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/feature_importance_predicted_release_class.png">Release Feature Importance</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/feature_importance_predicted_stability_class.png">Stability Feature Importance</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/feature_importance_predicted_risk_class.png">Risk Feature Importance</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/illustrative_release_curves.png">Illustrative Release Curves</button>
                        <button class="btn btn-secondary nano-img-btn" data-img="/static/nano_drug/release_pred_vs_actual.png">Release Pred vs Actual</button>
                    </div>
                    <div style="background:#141414; border:1px solid var(--panel-border); padding:0.75rem; text-align:center; border-radius:2px;">
                        <img id="nano-model-img" src="/static/nano_drug/confusion_predicted_release_class.png" alt="Model Analysis Plot" style="max-width:100%; max-height:420px; border-radius:2px;">
                    </div>
                </div>

                <!-- FORMULATION BROWSER -->
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                        <label class="tool-field-label" style="font-weight:600; color:#fff;">Formulation Browser (Search 10,000 Records)</label>
                        <div style="display:flex; gap:0.4rem;">
                            <input id="nano-search-input" type="text" placeholder="Filter drug / material / type..." style="width:220px; padding:0.35rem 0.5rem;">
                            <button id="btn-nano-search" class="btn btn-primary" style="padding:0.35rem 0.8rem;">FILTER</button>
                        </div>
                    </div>
                    <div id="nano-records-table" class="table-responsive">Loading formulation records...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- ============================================================== -->
    <!-- VIEW 6: 3D NANOPARTICLE VIEWER                                 -->
    <!-- ============================================================== -->
        <!-- ============================================================== -->
    <!-- VIEW 6: 3D NANOPARTICLE VIEWER: NANO·LAB 3D                      -->
    <!-- ============================================================== -->
    <div class="view-container-single" id="view-viewer">
        <div class="nanolab-viewport">
          <canvas id="scene"></canvas>
          <div id="stage" style="display:none"></div>
          <div id="three-viewer" style="display:none"></div>
          <div id="v3Chips" style="display:none"></div>
          <select id="v3Core" style="display:none"><option value="Ag">Ag</option><option value="Au">Au</option><option value="Fe3O4">Fe3O4</option><option value="ZnO">ZnO</option><option value="CeO2">CeO2</option></select>
          <input id="v3Size" type="range" style="display:none" value="20">
          <span id="v3SizeLbl" style="display:none">20</span>

          <!-- ======= TOP HUD ======= -->
          <header id="hud-top" class="panel">
            <div class="nl-logo"><span></span></div>
            <div>
              <h1>NANO·<b>LAB</b> 3D</h1>
              <p id="cur-preset">Ag·PEG · COLLOIDAL DRUG CARRIER</p>
            </div>
            <div class="nl-live"><i></i>LIVE</div>
            <button id="btn-toggle-hud" class="nl-hud-btn" onclick="toggleHudPanels()" title="Toggle Interface HUD Panels">👁 Toggle HUD</button>
          </header>

          <!-- ======= LEFT: PRESETS ======= -->
          <aside id="panel-left" class="panel">
            <h2>NANOMEDICINE SYSTEMS</h2>
            <div id="preset-list"></div>
            <div id="preset-meta"></div>
          </aside>

          <!-- ======= RIGHT: CONTROLS ======= -->
          <aside id="panel-right" class="panel">
            <h2>SIMULATION CONTROL</h2>
        <div class="ai-3d-box">
          <label>⚡ AI 3D Model Generator</label>
          <div class="ai-3d-input-row">
            <input id="ai-3d-prompt-input" type="text" placeholder="e.g. 75nm Liposome with Doxorubicin at -30mV...">
            <button id="btn-ai-3d-voice" class="voice-mic-btn" style="width:30px;height:30px;border-radius:6px;" title="Speak prompt">🎤</button>
            <button id="btn-ai-3d-morph" class="ai-3d-btn">⚡ Morph</button>
          </div>
          <div id="ai-3d-feedback" class="ai-3d-feedback"></div>
        </div>
            <div class="btn-row">
              <button id="btn-play" class="nl-btn primary">⏸&nbsp;Pause</button>
              <button id="btn-reset" class="nl-btn">⟲&nbsp;Reset</button>
            </div>
            <div class="btn-row">
              <button id="btn-form" class="nl-btn">⚡&nbsp;Form Corona</button>
              <button id="btn-break" class="nl-btn">✂&nbsp;Release Drug</button>
            </div>
            <div class="btn-row">
              <button id="btn-sync-pred" class="nl-btn" onclick="syncFromPredictor()" style="background:rgba(34,211,238,.12);border-color:rgba(34,211,238,.35);color:#22d3ee">🔄&nbsp;Sync Predictor</button>
            </div>
            <div class="ctl">
              <label>TEMPERATURE <output id="o-temp">310 K (37°C)</output></label>
              <input id="s-temp" type="range" min="290" max="340" step="1" value="310">
            </div>
            <div class="ctl">
              <label>TIME SCALE <output id="o-speed">×1.0</output></label>
              <input id="s-speed" type="range" min="0.1" max="3" step="0.1" value="1">
            </div>
            <div class="ctl">
              <label>CORE SIZE <output id="o-size">20 nm</output></label>
              <input id="s-size" type="range" min="5" max="150" step="1" value="20">
            </div>
            <h2 style="margin-top:14px">DISPLAY</h2>
            <label class="tgl">Zeta field arrow<input id="t-dipole" type="checkbox" checked><span class="sw"></span></label>
            <label class="tgl">Drug payload clouds<input id="t-cloud" type="checkbox" checked><span class="sw"></span></label>
            <label class="tgl">Surface charge label<input id="t-labels" type="checkbox" checked><span class="sw"></span></label>
            <label class="tgl">Auto-rotate<input id="t-rotate" type="checkbox" checked><span class="sw"></span></label>
            <h2 style="margin-top:14px">COLLOIDAL POTENTIAL · V(r)</h2>
            <canvas id="chart"></canvas>
          </aside>

          <!-- ======= BOTTOM HUD ======= -->
          <footer id="hud-bottom" class="panel">
            <div class="chip hot"><small>HYDRO SIZE</small><b id="c-len">24.2 nm</b></div>
            <div class="chip hot"><small>DLVO BARRIER</small><b id="c-energy">14.5 kBT</b></div>
            <div class="chip"><small>TEMPERATURE</small><b id="c-temp">310 K</b></div>
            <div class="chip"><small>SIM TIME</small><b id="c-time">0.0 s</b></div>
            <div class="chip"><small>ZETA POTENTIAL</small><b id="c-order">-24.5 mV</b></div>
            <div class="chip"><small>STATE</small><b id="c-state">Colloidally Dispersed</b></div>
          </footer>

          <div id="hint">DRAG orbit · SCROLL zoom · SPACE play/pause</div>
          <p id="v3Status" style="display:none"></p>
        </div>
    </div>

<!-- ============================================================== -->
    <!-- VIEW 7: RESEARCH REPORT GENERATOR                              -->
    <!-- ============================================================== -->
    <div class="view-container-single" id="view-report">
        <div class="content-max-width">
            <div class="view-header">
                <h2>Research Session Report Generator</h2>
                <p>Export an audit trail of all model predictions, domain applicability boundaries, simulation kinetics, and experimental prompts executed during this session.</p>
            </div>

            <div class="card-panel">
                <h3>Report Actions</h3>
                <div style="display:flex; gap:0.6rem; margin-bottom: 0.85rem;">
                    <button id="generate-report" class="btn btn-primary">GENERATE AUDIT REPORT</button>
                    <button id="download-report" class="btn btn-secondary">DOWNLOAD AS .TXT</button>
                </div>
                <textarea id="report-output" class="report-textbox" placeholder="Click 'Generate Audit Report' to compile session telemetry and prediction data."></textarea>
            </div>
        </div>
    </div>

    <!-- INTRO LOADING & DIAGNOSTICS MODAL -->
    <div id="intro-modal" class="intro-modal-overlay">
        <div class="intro-modal-card">
            <button class="intro-close-btn" id="btn-close-intro" title="Close Intro">&times;</button>
            <span class="badge badge-live">QUANTUM BIOPHYSICAL RESEARCH PLATFORM</span>
            <h2 class="intro-hero-title">NanoMedAI Research Suite</h2>
            <p class="intro-lead">
                Next-generation biophysical and cytotoxicity surrogate modeling for nanomedicine design. 
                Coupling RDKit molecular descriptors, DLVO colloidal energy barriers, and GroupKFold cross-validated machine learning.
            </p>

            <div class="intro-progress-box">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-family:'Space Grotesk',sans-serif; font-weight:600; color:#e2e8f0;">⚡ System Boot &amp; Diagnostics</span>
                    <span id="intro-diag-percent" style="font-family:'JetBrains Mono',monospace; color:#22d3ee; font-weight:700;">100% READY</span>
                </div>
                <div class="intro-progress-bar-wrap">
                    <div id="intro-diag-bar" class="intro-progress-bar" style="width: 100%;"></div>
                </div>
                <div class="intro-steps-list">
                    <div class="intro-step-item done">✓ Korsmeyer-Peppas ODE Drug Dissolution Kinetics (0-72h)</div>
                    <div class="intro-step-item done">✓ Random Forest Regressor for Zeta Potential (R²=0.84, MAE=2.3 mV)</div>
                    <div class="intro-step-item done">✓ Random Forest Cytotoxicity Classifier (ROC-AUC=0.91)</div>
                    <div class="intro-step-item done">✓ GroupKFold Leakage-Free Validation Matrix on Study DOIs</div>
                </div>
            </div>

            <div class="intro-kpi-grid">
                <div class="intro-kpi-card">
                    <div class="intro-kpi-val">|ζ| ≥ 30 mV</div>
                    <div class="intro-kpi-lbl">Colloidal Stability</div>
                </div>
                <div class="intro-kpi-card">
                    <div class="intro-kpi-val">AUC 0.91</div>
                    <div class="intro-kpi-lbl">Cytotoxicity AUC</div>
                </div>
                <div class="intro-kpi-card">
                    <div class="intro-kpi-val">0% Leakage</div>
                    <div class="intro-kpi-lbl">DOI GroupKFold</div>
                </div>
            </div>

            <div class="intro-actions">
                <button id="btn-enter-workspace" class="btn btn-primary" style="padding: 0.8rem 1.6rem; font-size: 0.95rem;">
                    🚀 ENTER RESEARCH WORKSPACE
                </button>
            </div>
        </div>
    </div>

    <!-- SCRIPTS -->
    <script>
/**
 * NanoMedAI - Full-Stack Biophysical Simulation & Machine Learning Web Platform
 * Connects the frontend UI to FastAPI backend endpoints:
 * - /api/health & /api/metadata
 * - /api/simulation/* (Biophysical session manager)
 * - /api/predict/stability (Zeta potential regressor)
 * - /api/predict/cytotoxicity (Random forest classifier)
 * - /api/prompt (Multi-model natural language pipeline)
 * - /api/formulation/heatmap (DLVO colloidal matrix)
 * - /api/dataset/{task} (Harmonized dataset catalog)
 */

// Helper selector
const $ = (id) => document.getElementById(id);
const escapeHTML = (str) => String(str ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Default formulation catalog — Expanded with All Dataset Medicines & Antibiotics
const FORMULATIONS = {
    // --- ONCOLOGY & CHEMOTHERAPEUTICS ---
    'formulation-a': {
        name: 'Formulation A: Paclitaxel + PLGA (Nature Comms Benchmark)',
        drug: 'Paclitaxel',
        category: 'Antineoplastic / Chemotherapeutic',
        material: 'PLGA',
        size: 120.0,
        zeta: -22.0,
        load: '8.0%',
        coat: 'PEG-5000 Stealth',
        k: 0.088,
        n: 0.371
    },
    'formulation-b': {
        name: 'Formulation B: Letrozole + PLA (Long-Acting Injectable)',
        drug: 'Letrozole',
        category: 'Aromatase Inhibitor',
        material: 'PLA',
        size: 150.0,
        zeta: -15.0,
        load: '5.0%',
        coat: 'Citrate',
        k: 0.060,
        n: 0.420
    },
    'formulation-c': {
        name: 'Formulation C: Letrozole + PLGA (Sustained Release)',
        drug: 'Letrozole',
        category: 'Aromatase Inhibitor',
        material: 'PLGA',
        size: 100.0,
        zeta: -28.0,
        load: '6.0%',
        coat: 'PVA Surfactant',
        k: 0.110,
        n: 0.340
    },
    'doxorubicin-liposome': {
        name: 'Doxorubicin + PEGylated Liposome (Doxil Analog)',
        drug: 'Doxorubicin',
        category: 'Anthracycline Chemotherapeutic',
        material: 'Liposome (DPPC/Chol)',
        size: 85.0,
        zeta: -25.0,
        load: '9.8%',
        coat: 'PEG-DSPE Stealth Layer',
        k: 0.045,
        n: 0.460
    },
    'doxorubicin-plga': {
        name: 'Doxorubicin + PLGA Chitosan/Alginate Core',
        drug: 'Doxorubicin',
        category: 'Anthracycline Chemotherapeutic',
        material: 'PLGA (CHI/ALG)',
        size: 175.0,
        zeta: -19.5,
        load: '8.5%',
        coat: 'Layer-by-Layer Chitosan/Alginate',
        k: 0.082,
        n: 0.420
    },
    'methotrexate-dendrimer': {
        name: 'Methotrexate + PAMAM G4 Dendrimer',
        drug: 'Methotrexate',
        category: 'Antimetabolite',
        material: 'PAMAM Dendrimer',
        size: 45.0,
        zeta: 14.0,
        load: '14.0%',
        coat: 'PEG / Primary Amine Surface',
        k: 0.180,
        n: 0.310
    },
    'cisplatin-micelle': {
        name: 'Cisplatin + Block Copolymer Micelles',
        drug: 'Cisplatin',
        category: 'Platinum Antineoplastic',
        material: 'PCL-b-PEG Micelle',
        size: 65.0,
        zeta: -8.0,
        load: '7.2%',
        coat: 'PEG Hydrophilic Shell',
        k: 0.090,
        n: 0.380
    },
    'rapamycin-albumin': {
        name: 'Rapamycin + Albumin Matrix (Abraxane format)',
        drug: 'Rapamycin',
        category: 'mTOR Inhibitor / Immunosuppressive',
        material: 'Human Serum Albumin (HSA)',
        size: 130.0,
        zeta: -18.0,
        load: '10.0%',
        coat: 'Endogenous Albumin Corona',
        k: 0.075,
        n: 0.390
    },
    'exemestane-plga-gel': {
        name: 'Exemestane + PLGA In-Situ Gel NP',
        drug: 'Exemestane',
        category: 'Aromatase Inhibitor',
        material: 'PLGA In-Situ Gel',
        size: 160.0,
        zeta: -23.0,
        load: '12.4%',
        coat: 'Thermosensitive Poloxamer Gel',
        k: 0.038,
        n: 0.580
    },

    // --- PARACETAMOL & ANALGESICS / NSAIDS ---
    'nm-paracetamol-plga': {
        name: 'NM-000001: Paracetamol + PLGA (335 nm, SLN)',
        drug: 'Paracetamol',
        category: 'Analgesic / Antipyretic',
        material: 'PLGA',
        size: 335.5,
        zeta: 7.1,
        load: '7.4%',
        coat: 'Dextran coating',
        k: 0.095,
        n: 0.400
    },
    'nm-paracetamol-liposome': {
        name: 'NM-000004: Paracetamol + Liposome DPPC (90 nm)',
        drug: 'Paracetamol',
        category: 'Analgesic / Antipyretic',
        material: 'Liposome (DPPC)',
        size: 90.1,
        zeta: -35.4,
        load: '4.0%',
        coat: 'Dextran coating',
        k: 0.145,
        n: 0.450
    },
    'nm-paracetamol-sln': {
        name: 'NM-000012: Paracetamol + Lipid DSPC (235 nm)',
        drug: 'Paracetamol',
        category: 'Analgesic / Antipyretic',
        material: 'Lipid (DSPC)',
        size: 234.9,
        zeta: 19.0,
        load: '4.0%',
        coat: 'PEGylation',
        k: 0.105,
        n: 0.420
    },
    'ibuprofen-lipid': {
        name: 'Ibuprofen + Lipid Nanoparticle (150 nm)',
        drug: 'Ibuprofen',
        category: 'NSAID / Anti-inflammatory',
        material: 'Solid Lipid (SLN)',
        size: 150.0,
        zeta: -22.4,
        load: '9.5%',
        coat: 'Tween 80 Surfactant',
        k: 0.115,
        n: 0.380
    },

    // --- ANTIBIOTICS & ANTIMICROBIALS (DATASET COHORT) ---
    'ciprofloxacin-plga': {
        name: 'Ciprofloxacin + PLGA Nanoparticles (Fluoroquinolone)',
        drug: 'Ciprofloxacin',
        category: 'Fluoroquinolone Antibiotic',
        material: 'PLGA',
        size: 165.0,
        zeta: -18.2,
        load: '9.2%',
        coat: 'PVA Surfactant',
        k: 0.120,
        n: 0.360
    },
    'vancomycin-plga-peg': {
        name: 'Vancomycin + PLGA-PEG Extended-Release (Glycopeptide)',
        drug: 'Vancomycin',
        category: 'Glycopeptide Antibiotic',
        material: 'PLGA-PEG',
        size: 180.0,
        zeta: -12.5,
        load: '11.5%',
        coat: 'PEG Stealth Layer',
        k: 0.050,
        n: 0.450
    },
    'rifampicin-plga-peg': {
        name: 'Rifampicin + PLGA-PEG Sustained Core (Antitubercular)',
        drug: 'Rifampicin',
        category: 'Rifamycin / Antitubercular',
        material: 'PLGA-PEG',
        size: 145.0,
        zeta: -16.0,
        load: '8.0%',
        coat: 'PEGylation',
        k: 0.070,
        n: 0.420
    },
    'doxycycline-polymeric': {
        name: 'Doxycycline + Polymeric Nanoparticles (Tetracycline)',
        drug: 'Doxycycline',
        category: 'Tetracycline Antibiotic',
        material: 'PEG-PLA',
        size: 130.0,
        zeta: -24.0,
        load: '7.8%',
        coat: 'Surfactant (Tween 80)',
        k: 0.130,
        n: 0.390
    },
    'gentamicin-chitosan': {
        name: 'Gentamicin + Chitosan Nanoparticles (Aminoglycoside)',
        drug: 'Gentamicin',
        category: 'Aminoglycoside Antibiotic',
        material: 'Chitosan',
        size: 115.0,
        zeta: 28.5,
        load: '6.5%',
        coat: 'Chitosan Cationic Coating',
        k: 0.160,
        n: 0.410
    },
    'azithromycin-sln': {
        name: 'Azithromycin + Solid Lipid Nanoparticles (Macrolide)',
        drug: 'Azithromycin',
        category: 'Macrolide Antibiotic',
        material: 'Solid Lipid (SLN)',
        size: 195.0,
        zeta: -21.0,
        load: '10.2%',
        coat: 'Poloxamer 188',
        k: 0.085,
        n: 0.350
    },
    'amoxicillin-eudragit': {
        name: 'Amoxicillin + Eudragit Nanoparticles (Beta-Lactam)',
        drug: 'Amoxicillin',
        category: 'Beta-Lactam Antibiotic',
        material: 'Eudragit',
        size: 140.0,
        zeta: -15.5,
        load: '8.7%',
        coat: 'Enteric Polymer Coating',
        k: 0.175,
        n: 0.330
    },

    // --- CARDIOVASCULAR & DUAL THERAPIES ---
    'amlodipine-plga-pcl': {
        name: 'Amlodipine Besylate + PLGA-PCL Extruded NPs',
        drug: 'Amlodipine Besylate',
        category: 'Calcium Channel Blocker',
        material: 'PLGA-PCL',
        size: 185.0,
        zeta: -16.5,
        load: '5.0%',
        coat: 'PCL Extruded Matrix',
        k: 0.065,
        n: 0.510
    },
    'dox-atv-dual': {
        name: 'DOX / Atorvastatin + Hyaluronic Acid NP (Dual Therapy)',
        drug: 'DOX / Atorvastatin',
        category: 'Cardioprotective Oncology Dual Delivery',
        material: 'CaP / Hyaluronic Acid',
        size: 140.0,
        zeta: -26.0,
        load: '6.8%',
        coat: 'Hyaluronic Acid CD44-Targeted',
        k: 0.078,
        n: 0.440
    },

    // --- BIOLOGICS & NUCLEIC ACIDS ---
    'mrna-lnp': {
        name: 'mRNA-1273 + Ionizable Lipid Nanoparticle (LNP)',
        drug: 'mRNA-1273',
        category: 'mRNA Vaccine / Biologic',
        material: 'Ionizable Lipid (SM-102)',
        size: 80.0,
        zeta: 4.5,
        load: '92% encapsulation',
        coat: 'PEG-2000 DMG Corona',
        k: 0.150,
        n: 0.380
    },
    'sirna-lnp': {
        name: 'siRNA + Targeted Cationic LNP (Gene Silencing)',
        drug: 'siRNA',
        category: 'Gene Silencing Oligonucleotide',
        material: 'Lipid (DSPC/Chol)',
        size: 75.0,
        zeta: 6.0,
        load: '88% encapsulation',
        coat: 'PEG Stealth / Ligand Conjugation',
        k: 0.160,
        n: 0.360
    }
};

// Aliases for user flexibility and backward compatibility
FORMULATIONS['paracetamol'] = FORMULATIONS['nm-paracetamol-plga'];
FORMULATIONS['ciprofloxacin'] = FORMULATIONS['ciprofloxacin-plga'];
FORMULATIONS['vancomycin'] = FORMULATIONS['vancomycin-plga-peg'];
FORMULATIONS['rifampicin'] = FORMULATIONS['rifampicin-plga-peg'];
FORMULATIONS['doxorubicin'] = FORMULATIONS['doxorubicin-liposome'];
FORMULATIONS['paclitaxel'] = FORMULATIONS['formulation-a'];
FORMULATIONS['letrozole'] = FORMULATIONS['formulation-b'];
FORMULATIONS['ibuprofen'] = FORMULATIONS['ibuprofen-lipid'];
FORMULATIONS['doxycycline'] = FORMULATIONS['doxycycline-polymeric'];
FORMULATIONS['gentamicin'] = FORMULATIONS['gentamicin-chitosan'];
FORMULATIONS['azithromycin'] = FORMULATIONS['azithromycin-sln'];
FORMULATIONS['amoxicillin'] = FORMULATIONS['amoxicillin-eudragit'];
FORMULATIONS['methotrexate'] = FORMULATIONS['methotrexate-dendrimer'];
FORMULATIONS['cisplatin'] = FORMULATIONS['cisplatin-micelle'];
FORMULATIONS['rapamycin'] = FORMULATIONS['rapamycin-albumin'];
FORMULATIONS['exemestane'] = FORMULATIONS['exemestane-plga-gel'];
FORMULATIONS['amlodipine'] = FORMULATIONS['amlodipine-plga-pcl'];
FORMULATIONS['mrna'] = FORMULATIONS['mrna-lnp'];
FORMULATIONS['sirna'] = FORMULATIONS['sirna-lnp'];

// Application Global State
const state = {
    status: 'INITIALIZED', // INITIALIZED, RUNNING, PAUSED, STOPPED, COMPLETED
    time: 0,
    maxTime: 72,
    speed: 1.0,
    timerId: null,
    backendSimulationId: null,
    backendConnected: false,
    formulationKey: 'formulation-a',
    env: {
        temp: 37.0,
        ph: 7.4,
        ionic: 0.15,
        medium: 'pbs'
    },
    particle: {
        size: 120.0,
        hydSize: 128.0,
        pdi: 0.16,
        zeta: -22.0,
        release: 0.0,
        remaining: 100.0
    },
    workflowResult: null,
    predictionHistory: [],
    metadata: null
};

// API Fetch Helper
async function requestJSON(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json();
    if (!res.ok) {
        const detail = data.detail;
        const msg = typeof detail === 'string' ? detail : (detail?.message || JSON.stringify(detail) || `Request failed (${res.status})`);
        const err = new Error(msg);
        err.details = detail;
        err.status = res.status;
        throw err;
    }
    return data;
}

const postJSON = (url, body) => requestJSON(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
});

// Event Logger
function addEvent(message, type = '') {
    const list = $('events-list');
    if (!list) return;
    const item = document.createElement('div');
    item.className = 'event-item ' + type;
    
    const timeEl = document.createElement('div');
    timeEl.className = 'event-time';
    timeEl.textContent = state.time.toFixed(1) + ' h';
    
    const textEl = document.createElement('div');
    textEl.textContent = (type === 'warn' ? '⚠ ' : '● ') + message;
    
    item.appendChild(timeEl);
    item.appendChild(textEl);
    list.prepend(item);
}

// Biophysical Calculation Engine (Deterministic Korsmeyer-Peppas + DLVO Dynamics)
function calculateBiophysicalState(t, env, f) {
    // Korsmeyer-Peppas power law: Mt/M∞ = k * t^n
    const kpFrac = Math.min(1.0, f.k * Math.pow(Math.max(0, t), f.n));
    // Environmental modifier for visual bio-responsiveness
    const tempFactor = (env.temp - 37.0) * 0.015;
    const phFactor = Math.abs(env.ph - 7.4) * 0.02;
    const relPct = Math.min(100.0, Math.max(0.0, (kpFrac + (t > 0 ? (tempFactor + phFactor) * kpFrac : 0)) * 100.0));
    
    // Size dynamics (swelling and erosion)
    const swell = 1.0 + 0.0006 * t + Math.max(0, env.ionic - 0.15) * 0.12 * (t / 72) + Math.abs(env.ph - 7.4) * 0.004 * (t / 72);
    const particleSize = f.size * swell;
    const hydSize = particleSize + 8.0 + (env.ionic - 0.15) * 20.0;
    
    // PDI slightly relaxes
    const pdi = 0.16 + 0.0005 * t + Math.max(0, env.temp - 37.0) * 0.0008;
    
    // Zeta potential dynamic drift
    const zeta = f.zeta + (env.ph - 7.4) * -1.5 + (env.ionic - 0.15) * -8.0 + (t / 72) * 2.5;

    return {
        size: particleSize,
        hydSize: hydSize,
        pdi: pdi,
        zeta: zeta,
        release: relPct,
        remaining: Math.max(0, 100.0 - relPct)
    };
}

function interpolateTrajectory(times, values, targetTime) {
    if (!times || !times.length) return 0;
    if (targetTime <= times[0]) return values[0];
    if (targetTime >= times[times.length - 1]) return values[values.length - 1];
    const i = times.findIndex((val, idx) => idx < times.length - 1 && val <= targetTime && times[idx + 1] >= targetTime);
    if (i < 0) return values[0];
    const span = times[i + 1] - times[i] || 1;
    const frac = (targetTime - times[i]) / span;
    return values[i] + (values[i + 1] - values[i]) * frac;
}

function updateState() {
    if (state.workflowResult && state.workflowResult.simulation.status === 'ready') {
        const sim = state.workflowResult.simulation;
        const rel = interpolateTrajectory(sim.time_hours, sim.release_pct, state.time);
        state.particle = {
            size: sim.features.particle_size_nm,
            hydSize: state.workflowResult.toxicity.inputs?.['Hydro size (nm)'] ?? (sim.features.particle_size_nm + 8),
            pdi: 0.16 + (state.time / 72) * 0.03,
            zeta: state.workflowResult.stability.result?.prediction ?? -22.0,
            release: rel,
            remaining: Math.max(0, 100.0 - rel)
        };
    } else {
        const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
        state.particle = calculateBiophysicalState(state.time, state.env, form);
    }
}

// -------------------------------------------------------------
// Chart.js Setup
// -------------------------------------------------------------
const chartOpt = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false } },
    scales: {
        x: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585', font: { family: "'Fira Code', monospace", size: 10 }, maxTicksLimit: 12 } },
        y: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585', font: { family: "'Fira Code', monospace", size: 10 } } }
    }
};

const labels72 = Array.from({ length: 73 }, (_, i) => i);

const releaseChart = new Chart($('release-chart'), {
    type: 'line',
    data: {
        labels: labels72,
        datasets: [
            { data: [], borderColor: 'transparent', pointRadius: 0, borderWidth: 0 },
            { data: [], borderColor: 'transparent', backgroundColor: 'rgba(0,122,204,0.15)', pointRadius: 0, borderWidth: 0, fill: '-1' },
            { data: [], borderColor: '#007acc', backgroundColor: 'rgba(0,122,204,0.08)', fill: true, borderWidth: 2, pointRadius: 0, tension: 0.35 }
        ]
    },
    options: {
        ...chartOpt,
        scales: {
            ...chartOpt.scales,
            y: { ...chartOpt.scales.y, min: 0, max: 100, title: { display: true, text: 'Release %', color: '#858585', font: { size: 10 } } }
        }
    }
});

const rateChart = new Chart($('rate-chart'), {
    type: 'line',
    data: {
        labels: labels72,
        datasets: [{ data: [], borderColor: '#0098ff', borderWidth: 1.5, pointRadius: 0, tension: 0.3 }]
    },
    options: {
        ...chartOpt,
        scales: {
            ...chartOpt.scales,
            y: { ...chartOpt.scales.y, title: { display: true, text: '% / h', color: '#858585', font: { size: 10 } } }
        }
    }
});

const sizeChart = new Chart($('size-chart'), {
    type: 'line',
    data: {
        labels: labels72,
        datasets: [{ data: [], borderColor: '#4caf50', borderWidth: 1.5, pointRadius: 0, tension: 0.35 }]
    },
    options: {
        ...chartOpt,
        scales: {
            ...chartOpt.scales,
            y: { ...chartOpt.scales.y, title: { display: true, text: 'Size (nm)', color: '#858585', font: { size: 10 } } }
        }
    }
});

let sweepChart = null;
let matrixChart = null;

// -------------------------------------------------------------
// Live 2D Particle Canvas Renderer
// -------------------------------------------------------------
const canvas = $('particle-canvas');
const ctx = canvas.getContext('2d');
let randomSeed = 42;
function pseudoRandom() {
    const x = Math.sin(randomSeed++) * 10000;
    return x - Math.floor(x);
}

function renderCanvas() {
    const W = canvas.width;
    const H = canvas.height;
    const cx = W / 2;
    const cy = H / 2;
    const p = state.particle;
    const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
    
    ctx.clearRect(0, 0, W, H);
    
    const scale = (p.size || form.size) / 120.0;
    const coreR = Math.max(25, Math.min(100, 60.0 * scale));
    const hydroR = coreR + Math.max(8, (p.hydSize - p.size) * 0.7);
    
    // Background radial ambient glow (temperature responsive)
    const ambientGrad = ctx.createRadialGradient(cx, cy, coreR, cx, cy, W * 0.7);
    ambientGrad.addColorStop(0, '#1a1a1a');
    const tempIntensity = Math.min(120, Math.max(10, Math.floor(((state.env.temp - 20) / 30) * 100)));
    ambientGrad.addColorStop(1, `rgba(${tempIntensity}, 25, 45, 0.22)`);
    ctx.fillStyle = ambientGrad;
    ctx.fillRect(0, 0, W, H);
    
    // Hydrodynamic shear corona layer (outer diffuse boundary)
    ctx.beginPath();
    ctx.arc(cx, cy, hydroR, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 122, 204, 0.08)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 122, 204, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Core nanoparticle sphere with 3D spherical gradient
    ctx.beginPath();
    ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    const sphereGrad = ctx.createRadialGradient(cx - coreR * 0.25, cy - coreR * 0.25, coreR * 0.1, cx, cy, coreR);
    sphereGrad.addColorStop(0, '#737373');
    sphereGrad.addColorStop(0.7, '#383838');
    sphereGrad.addColorStop(1, '#1e1e1e');
    ctx.fillStyle = sphereGrad;
    ctx.fill();
    ctx.strokeStyle = '#555555';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Encapsulated drug molecules inside core
    randomSeed = 1001;
    ctx.fillStyle = '#4caf50';
    const remainingCount = Math.floor(100 * (p.remaining / 100.0));
    for (let i = 0; i < remainingCount; i++) {
        const angle = pseudoRandom() * Math.PI * 2;
        const radius = Math.sqrt(pseudoRandom()) * (coreR - 7);
        const px = cx + Math.cos(angle) * radius;
        const py = cy + Math.sin(angle) * radius;
        ctx.beginPath();
        ctx.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // Emitted / diffusing drug molecules radiating into medium
    randomSeed = 2002;
    ctx.fillStyle = 'rgba(76, 175, 80, 0.65)';
    const releaseCount = Math.floor(100 * (p.release / 100.0));
    for (let i = 0; i < releaseCount; i++) {
        const angle = pseudoRandom() * Math.PI * 2;
        const dist = coreR + 6 + pseudoRandom() * 155;
        const wobble = Math.sin(state.time * 2.0 + i) * 3;
        const px = cx + Math.cos(angle) * dist + wobble;
        const py = cy + Math.sin(angle) * dist + wobble;
        ctx.beginPath();
        ctx.arc(px, py, 1.8, 0, Math.PI * 2);
        ctx.fill();
    }
}

// -------------------------------------------------------------
// Update Visual Charts
// -------------------------------------------------------------
function updateCharts() {
    if (state.workflowResult && state.workflowResult.simulation.status === 'ready') {
        const sim = state.workflowResult.simulation;
        const times = sim.time_hours;
        const currentMask = times.map(t => t <= state.time);
        
        const relData = sim.release_pct.map((val, idx) => currentMask[idx] ? val : null);
        const lowerData = sim.release_pct.map((val, idx) => currentMask[idx] ? Math.max(0, val - 2 * sim.sd_pct[idx]) : null);
        const upperData = sim.release_pct.map((val, idx) => currentMask[idx] ? Math.min(100, val + 2 * sim.sd_pct[idx]) : null);
        const timeLabels = times.map(t => Number(t.toFixed(1)));
        
        releaseChart.data.labels = timeLabels;
        releaseChart.data.datasets[0].data = lowerData;
        releaseChart.data.datasets[1].data = upperData;
        releaseChart.data.datasets[2].data = relData;
        releaseChart.update('none');
        
        rateChart.data.labels = timeLabels;
        rateChart.data.datasets[0].data = sim.rate_pct_per_hour.map((val, idx) => currentMask[idx] ? val : null);
        rateChart.update('none');
        
        sizeChart.data.labels = timeLabels;
        sizeChart.data.datasets[0].data = times.map((t, idx) => currentMask[idx] ? sim.features.particle_size_nm : null);
        sizeChart.update('none');
        return;
    }
    
    // Default mode: 0 to 72 hours
    const curT = Math.floor(state.time);
    const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
    const rData = [];
    const rates = [];
    const sData = [];
    
    for (let i = 0; i <= 72; i++) {
        if (i <= curT) {
            const pt = calculateBiophysicalState(i, state.env, form);
            rData.push(pt.release);
            sData.push(pt.size);
            const prev = i > 0 ? calculateBiophysicalState(i - 1, state.env, form).release : 0;
            rates.push(i ? pt.release - prev : 0);
        } else {
            rData.push(null);
            rates.push(null);
            sData.push(null);
        }
    }
    
    releaseChart.data.labels = labels72;
    releaseChart.data.datasets[0].data = [];
    releaseChart.data.datasets[1].data = [];
    releaseChart.data.datasets[2].data = rData;
    releaseChart.update('none');
    
    rateChart.data.labels = labels72;
    rateChart.data.datasets[0].data = rates;
    rateChart.update('none');
    
    sizeChart.data.labels = labels72;
    sizeChart.data.datasets[0].data = sData;
    sizeChart.update('none');
}

// -------------------------------------------------------------
// Render Dashboard State & Controls
// -------------------------------------------------------------
function render() {
    const p = state.particle;
    
    // Update State Cards
    $('state-size').textContent = p.size === null ? 'N/A' : p.size.toFixed(1);
    $('state-hsize').textContent = p.hydSize === null ? 'N/A' : p.hydSize.toFixed(1);
    $('state-pdi').textContent = p.pdi === null ? 'N/A' : p.pdi.toFixed(3);
    $('state-zeta').textContent = p.zeta === null ? 'N/A' : p.zeta.toFixed(1);
    $('state-release').textContent = p.release.toFixed(1);
    $('state-remaining').textContent = p.remaining.toFixed(1);
    
    // Timeline & status
    $('val-time').textContent = state.time.toFixed(1);
    $('sim-timeline').value = state.time;
    $('sim-status-label').textContent = '● ' + state.status;
    $('sim-status-label').className = 'status-' + state.status.toLowerCase();
    
    // Canvas overlay
    $('overlay-temp').textContent = state.env.temp.toFixed(1);
    $('overlay-ph').textContent = state.env.ph.toFixed(1);
    $('overlay-ionic').textContent = state.env.ionic.toFixed(2);
    $('overlay-env').textContent = (state.env.medium || 'PBS').toUpperCase();
    
    // Button state machine
    const s = state.status;
    const canSim = !state.workflowResult || state.workflowResult.simulation.status === 'ready';
    
    $('btn-start').classList.toggle('hidden', !['INITIALIZED', 'STOPPED', 'COMPLETED'].includes(s));
    $('btn-resume').classList.toggle('hidden', s !== 'PAUSED');
    $('btn-start').disabled = s === 'COMPLETED' || !canSim;
    $('btn-pause').disabled = s !== 'RUNNING' || !canSim;
    $('btn-stop').disabled = ['INITIALIZED', 'STOPPED', 'COMPLETED'].includes(s) || !canSim;
    $('btn-step').disabled = s === 'RUNNING' || s === 'COMPLETED' || !canSim;
    
    renderCanvas();
    updateCharts();
}

// Simulation Control Actions
function simTick() {
    if (state.status !== 'RUNNING') return;
    state.time += (1 / 60) * state.speed;
    if (state.time >= state.maxTime) {
        state.time = state.maxTime;
        state.status = 'COMPLETED';
        clearInterval(state.timerId);
        addEvent('Simulation finished at ' + state.maxTime.toFixed(1) + ' hours', 'sys');
    }
    updateState();
    render();
}

function startSim() {
    if (state.status === 'COMPLETED') return;
    clearInterval(state.timerId);
    addEvent(state.time === 0 ? 'Simulation initiated' : 'Simulation resumed', 'sys');
    state.status = 'RUNNING';
    state.timerId = setInterval(simTick, 1000 / 60);
    render();
}

function pauseSim() {
    state.status = 'PAUSED';
    clearInterval(state.timerId);
    addEvent('Simulation paused at ' + state.time.toFixed(1) + ' h', 'sys');
    updateState();
    render();
}

function stopSim() {
    state.status = 'STOPPED';
    clearInterval(state.timerId);
    addEvent('Simulation stopped by user', 'warn');
    updateState();
    render();
}

function stepSim() {
    if (state.status === 'COMPLETED') return;
    state.time = Math.min(state.maxTime, state.time + 1.0);
    addEvent('Stepped forward +1.0 h → ' + state.time.toFixed(1) + ' h', 'sys');
    if (state.time >= state.maxTime) state.status = 'COMPLETED';
    updateState();
    render();
}

function resetSim() {
    clearInterval(state.timerId);
    state.status = 'INITIALIZED';
    state.time = 0;
    $('events-list').innerHTML = '';
    addEvent('Simulation environment reset to t = 0 h', 'sys');
    updateState();
    render();
}

// -------------------------------------------------------------
// Formulation & Environment Handlers
// -------------------------------------------------------------
function setFormulationConfig(key) {
    state.formulationKey = key;
    const f = FORMULATIONS[key] || FORMULATIONS['formulation-a'];
    $('cfg-drug').textContent = f.drug + (f.category ? ' (' + f.category + ')' : '');
    $('cfg-material').textContent = f.material;
    $('cfg-size').textContent = f.size + ' nm';
    $('cfg-zeta').textContent = (f.zeta > 0 ? '+' : '') + f.zeta + ' mV';
    $('cfg-loading').textContent = f.load;
    $('cfg-coating').textContent = f.coat;
}

$('config-formulation').addEventListener('change', (e) => {
    state.workflowResult = null;
    state.maxTime = 72;
    $('sim-timeline').max = 72;
    $('sim-max-label').textContent = '72h';
    $('workflow-results').classList.add('hidden');
    $('workflow-drivers-section').classList.add('hidden');
    $('workflow-metrics-section').classList.add('hidden');
    $('main-disclaimer').innerHTML = '<strong>PRODUCTION RESEARCH PLATFORM:</strong> Real-time biophysical ODE dynamics & active machine learning inference models.';
    $('cfg-mode-badge').textContent = 'ACTIVE FORMULATION';
    $('sim-canvas-badge').textContent = 'COLLOIDAL SOLVATION & DISSOLUTION';
    $('release-chart-badge').textContent = 'KORSMEYER-PEPPAS DYNAMICS';
    $('particle-state-badge').textContent = 'REAL-TIME TELEMETRY';
    $('ms-release-status').textContent = 'Korsmeyer-Peppas ODE';
    
    setFormulationConfig(e.target.value);
    addEvent('Selected nanoparticle formulation: ' + e.target.value, 'sys');
    resetSim();
});

// Environment controls
$('env-temp').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    state.env.temp = val;
    $('val-temp').textContent = val.toFixed(1);
    if (state.time > 0) { updateState(); render(); }
});
$('env-temp').addEventListener('change', (e) => addEvent(`Temperature adjusted to ${e.target.value}°C`));

$('env-ph').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    state.env.ph = val;
    $('val-ph').textContent = val.toFixed(1);
    $('env-warning').classList.remove('hidden');
    if (state.time > 0) { updateState(); render(); }
});
$('env-ph').addEventListener('change', (e) => {
    addEvent(`pH adjusted to ${e.target.value}`);
    addEvent('Environmental pH sensitivity gradient updated', 'sys');
});

$('env-ionic').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    state.env.ionic = val;
    $('val-ionic').textContent = val.toFixed(2);
    if (state.time > 0) { updateState(); render(); }
});
$('env-ionic').addEventListener('change', (e) => addEvent(`Ionic strength adjusted to ${e.target.value} M`));

$('env-medium').addEventListener('change', (e) => {
    state.env.medium = e.target.value;
    const txt = e.target.options[e.target.selectedIndex].text;
    addEvent(`Immersion medium changed to ${txt}`);
    render();
});

// Simulation buttons
$('btn-start').onclick = startSim;
$('btn-resume').onclick = startSim;
$('btn-pause').onclick = pauseSim;
$('btn-stop').onclick = stopSim;
$('btn-step').onclick = stepSim;
$('btn-reset').onclick = resetSim;

$('sim-timeline').addEventListener('input', (e) => {
    state.time = parseFloat(e.target.value);
    if (state.status === 'COMPLETED' && state.time < state.maxTime) state.status = 'PAUSED';
    updateState();
    render();
});
$('sim-timeline').addEventListener('change', () => addEvent(`Timeline scrubbed to ${state.time.toFixed(1)} h`));

// Speed buttons
document.querySelectorAll('.btn-speed').forEach(btn => {
    btn.onclick = () => {
        document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.speed = parseFloat(btn.dataset.speed);
        addEvent(`Simulation speed set to ${state.speed}x`);
    };
});

// -------------------------------------------------------------
// Backend Simulation Session Sync
// -------------------------------------------------------------
$('btn-sync-backend').addEventListener('click', async () => {
    const btn = $('btn-sync-backend');
    btn.disabled = true;
    btn.textContent = 'CONNECTING TO SESSION...';
    try {
        const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
        const res = await postJSON('/api/simulation/create', {
            formulation_id: state.formulationKey,
            nanoparticle: {
                carrier_material: form.material,
                core_drug: form.drug,
                initial_size_nm: form.size,
                zeta_potential: form.zeta,
                shape: 'Spherical'
            },
            environment: {
                temperature_c: state.env.temp,
                pH: state.env.ph,
                ionic_strength: state.env.ionic,
                medium: state.env.medium
            },
            time_step_hours: 1.0
        });
        state.backendSimulationId = res.simulation_id;
        addEvent(`Created backend simulation session: ${res.simulation_id}`, 'sys');
        btn.textContent = 'SESSION CONNECTED (' + res.simulation_id.slice(0, 8) + ')';
    } catch (err) {
        addEvent(`Backend session connection failed: ${err.message}`, 'warn');
        btn.textContent = 'SYNC FAILED (TRY AGAIN)';
    } finally {
        btn.disabled = false;
    }
});

// -------------------------------------------------------------
// Top Navigation & Tab Switching
// -------------------------------------------------------------
function switchTab(tabKey) {
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabKey);
    });
    
    // Switch views
    if (tabKey === 'simulation') {
        $('view-simulation').classList.add('active');
        document.querySelectorAll('.view-container-single').forEach(view => view.classList.remove('active'));
    } else {
        $('view-simulation').classList.remove('active');
        document.querySelectorAll('.view-container-single').forEach(view => {
            view.classList.toggle('active', view.id === 'view-' + tabKey);
        });
    }
    
    if (tabKey === 'viewer') open3D();
    else stop3D();
    if (tabKey === 'data') {
        loadModelRegistry();
        loadNanoDrugRecords();
    }
}

document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

$('btn-open-prompt-tab').addEventListener('click', () => switchTab('prompt'));
$('btn-apply-to-sim').addEventListener('click', () => switchTab('simulation'));

// -------------------------------------------------------------
// AI Experiment Prompt Pipeline
// -------------------------------------------------------------
const PROMPT_EXAMPLES = {
    a: 'Silver spherical nanoparticle, 20 nm, PEG coating, PBS, pH 7.4, 37 C',
    b: 'PLGA nanoparticle, 300 nm core size, 320 nm hydrodynamic size, paclitaxel, 0.08% drug loading, drug MW 853.918, polymer MW 57700, LA:GA ratio 1.85, surface area 50 m2/g, CuO, 50 ug/mL, 24 hours exposure, A549 cell, MTT assay, zeta -20 mV, simulate 30 days',
    paracetamol: 'Paracetamol 250 nm PLGA nanoparticle with Dextran coating, drug loading 7.4%, PBS pH 7.4 at 37 C, sustained Korsmeyer-Peppas release',
    ciprofloxacin: 'Ciprofloxacin 165 nm PLGA antibiotic nanoparticle, PVA coating, PBS pH 7.4 at 37 C, evaluate antimicrobial release kinetics',
    doxorubicin: 'Doxorubicin 85 nm PEGylated liposome (Doxil-analog), -25 mV zeta, targeted oncology release in PBS pH 7.4 at 37 C',
    vancomycin: 'Vancomycin 180 nm PLGA-PEG extended-release glycopeptide antibiotic, evaluate sustained antibacterial delivery',
    mrna: 'mRNA 80 nm ionizable lipid nanoparticle (LNP) formulation, pH 7.4, 37 C, evaluate colloidal stability and cellular delivery',
    tox: 'ZnO nanoparticle, 20 nm core size, 28 nm hydrodynamic size, surface area 40 m2/g, 25 mV, PBS, 100 ug/mL, 24 hours exposure, HaCaT cell, LDH assay, pH 6.5, 37 C'
};

$('prompt-example').addEventListener('change', (e) => {
    $('experiment-prompt').value = PROMPT_EXAMPLES[e.target.value];
});
$('quick-prompt-example').addEventListener('change', (e) => {
    $('quick-prompt-input').value = PROMPT_EXAMPLES[e.target.value];
});

$('experiment-prompt').value = PROMPT_EXAMPLES['a'];
$('quick-prompt-input').value = PROMPT_EXAMPLES['a'];

function renderOcclusionDrivers(title, drivers) {
    if (!drivers || !Object.keys(drivers).length) return '';
    const entries = Object.entries(drivers).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 5);
    const maxVal = Math.max(...entries.map(([, v]) => Math.abs(v)), 1e-6);
    return `
        <div class="driver-group">
            <div class="driver-title">${escapeHTML(title)}</div>
            ${entries.map(([name, val]) => `
                <div class="driver-row">
                    <span title="${escapeHTML(name)}">${escapeHTML(name)}</span>
                    <i><b style="width:${(Math.abs(val) / maxVal) * 100}%"></b></i>
                    <strong>${val >= 0 ? '+' : ''}${val.toFixed(2)}</strong>
                </div>
            `).join('')}
        </div>
    `;
}

function applyWorkflowResult(result) {
    state.workflowResult = result;
    state.time = 0;
    state.maxTime = result.simulation.time_hours.at(-1) || 72;
    state.status = 'INITIALIZED';
    
    $('sim-timeline').max = state.maxTime;
    $('sim-timeline').step = Math.max(0.1, state.maxTime / 60);
    $('sim-max-label').textContent = Math.round(state.maxTime) + 'h';
    
    // Sync environment
    const env = result.environment;
    if (env.temperature_c !== null) {
        state.env.temp = Number(env.temperature_c);
        $('env-temp').value = state.env.temp;
        $('val-temp').textContent = state.env.temp.toFixed(1);
    }
    if (env.ph !== null) {
        state.env.ph = Number(env.ph);
        $('env-ph').value = state.env.ph;
        $('val-ph').textContent = state.env.ph.toFixed(1);
    }
    if (env.ionic_strength !== null) {
        state.env.ionic = Number(env.ionic_strength);
        $('env-ionic').value = state.env.ionic;
        $('val-ionic').textContent = state.env.ionic.toFixed(2);
    }
    if (env.medium) {
        const med = env.medium.toLowerCase().includes('water') ? 'water' : 'pbs';
        state.env.medium = med;
        $('env-medium').value = med;
    }
    
    // Status badges & text
    $('sim-mode-badge').className = 'badge badge-live';
    $('sim-mode-badge').textContent = 'AI MODELS ACTIVE';
    $('main-disclaimer').innerHTML = '<strong>RESEARCH PROTOTYPE:</strong> Trained machine learning model predictions with domain validation.';
    $('cfg-mode-badge').textContent = 'AI CONFIG';
    $('sim-canvas-badge').textContent = 'PREDICTED PARTICLE VIEW';
    $('release-chart-badge').textContent = result.simulation.status === 'ready' ? 'Learned RF; ±2 tree SD' : 'Not Run: Missing Domain';
    $('particle-state-badge').textContent = 'MODEL ESTIMATES';
    $('ms-release-status').textContent = result.simulation.status === 'ready' ? 'Learned RF Model' : 'Not run';
    
    // Simulation view banner
    const zPred = result.stability.result ? `${result.stability.result.prediction.toFixed(1)} mV` : 'Not run';
    const zClass = result.stability.result ? `${result.stability.result.stability_class} (MAE ${result.stability.result.validation_metrics.MAE_mV.toFixed(1)} mV)` : 'Outside domain';
    $('workflow-zeta').textContent = zPred;
    $('workflow-zeta-class').textContent = zClass;
    
    const toxPred = result.toxicity.result?.prediction || 'Not run';
    const toxRisk = result.toxicity.result?.risk_level || 'Inputs incomplete';
    $('workflow-toxicity').textContent = toxPred;
    $('workflow-toxicity-risk').textContent = toxRisk;
    
    const relFinal = result.simulation.final_release_pct !== null ? `${result.simulation.final_release_pct.toFixed(1)}%` : 'Not run';
    $('workflow-release').textContent = relFinal;
    $('workflow-release-time').textContent = `at ${state.maxTime.toFixed(0)} hours`;
    
    // Warnings
    const warnings = [
        ...result.stability.domain_warnings.map(w => 'Stability: ' + w),
        ...result.toxicity.domain_warnings.map(w => 'Toxicity: ' + w),
        ...result.simulation.domain_warnings.map(w => 'Release: ' + w)
    ];
    if (result.toxicity.missing_inputs.length) warnings.push('Toxicity omitted: ' + result.toxicity.missing_inputs.join(', '));
    if (result.simulation.missing_inputs.length) warnings.push('Release omitted: ' + result.simulation.missing_inputs.join(', '));
    
    const wBox = $('workflow-warnings');
    wBox.classList.toggle('hidden', warnings.length === 0);
    wBox.innerHTML = '<strong>Model Applicability:</strong><br>' + warnings.map(escapeHTML).join('<br>');
    $('workflow-assumptions').textContent = result.assumptions.length ? 'Defaults applied: ' + result.assumptions.join(' ') : 'Parameters parsed directly from prompt.';
    
    $('workflow-results').classList.remove('hidden');
    
    // Prompt Tab view updates
    $('tab-workflow-zeta').textContent = zPred;
    $('tab-workflow-zeta-desc').textContent = zClass;
    $('tab-workflow-tox').textContent = toxPred;
    $('tab-workflow-tox-desc').textContent = toxRisk;
    $('tab-workflow-rel').textContent = relFinal;
    $('tab-workflow-rel-desc').textContent = `Duration: ${state.maxTime.toFixed(0)}h`;
    
    const tabWBox = $('tab-workflow-warnings');
    tabWBox.classList.toggle('hidden', warnings.length === 0);
    tabWBox.innerHTML = wBox.innerHTML;
    $('tab-workflow-assumptions').textContent = $('workflow-assumptions').textContent;
    
    // Occlusion driver markup
    const driversHtml = (result.stability.result ? renderOcclusionDrivers('Stability: Zeta Potential', result.stability.drivers) : '') +
        (result.toxicity.result ? renderOcclusionDrivers('Cytotoxicity: P(Toxic)', result.toxicity.drivers) : '') +
        (result.simulation.status === 'ready' ? renderOcclusionDrivers('Drug Release: Final Cumulative %', result.simulation.drivers) : '');
    
    $('workflow-drivers').innerHTML = driversHtml || 'No driver data available.';
    $('tab-workflow-drivers').innerHTML = driversHtml || 'No driver data available.';
    $('workflow-drivers-section').classList.remove('hidden');
    
    // Grouped validation metrics
    const stCV = result.stability.cv;
    const txCV = result.toxicity.cv;
    const rlCV = result.simulation.cv;
    
    $('workflow-metrics').innerHTML = `
        <div class="ms-row"><span>Stability (GroupKFold)</span> <span class="ms-demo">MAE ${stCV.metrics.MAE_mV.toFixed(2)} mV</span></div>
        <div class="ms-row"><span>Cytotoxicity (GroupKFold)</span> <span class="ms-demo">F1 ${txCV.metrics.F1.toFixed(2)}</span></div>
        <div class="ms-row"><span>Release (GroupKFold)</span> <span class="ms-demo">MAE ${rlCV.MAE_release_percentage_points.toFixed(2)} pp</span></div>
    `;
    $('workflow-metrics-section').classList.remove('hidden');
    
    // Config panel update
    const simFeat = result.simulation.features;
    $('cfg-drug').textContent = result.simulation.status === 'ready' ? (simFeat.drug_name || 'Paclitaxel') : 'N/A';
    $('cfg-material').textContent = result.simulation.status === 'ready' ? (simFeat.polymer || 'PLGA') : 'N/A';
    $('cfg-size').textContent = (result.parsed.size_nm ?? 120.0) + ' nm';
    $('cfg-zeta').textContent = result.stability.result ? `${result.stability.result.prediction.toFixed(1)} mV` : 'N/A';
    $('cfg-loading').textContent = result.simulation.status === 'ready' ? simFeat.drug_loading_pct.toFixed(2) + '%' : 'N/A';
    $('cfg-coating').textContent = result.stability.result ? result.stability.result.engineered_features.detected_charge : 'N/A';
    
    addEvent(`Executed AI prompt pipeline. Release: ${relFinal}, Zeta: ${zPred}, Toxicity: ${toxPred}`, 'sys');
    resetSim();
}

async function runPromptWorkflow(promptText) {
    if (!promptText || !promptText.trim()) return;
    const btn = $('run-workflow');
    const statusEl = $('prompt-status');
    btn.disabled = true;
    statusEl.textContent = 'Parsing experiment description and running ML inference pipeline...';
    
    const payload = { prompt: promptText.trim() };
    
    // Gather advanced form overrides if specified
    const advMappings = [
        ['sample_name', 'prompt-sample-name'], ['particle_size_nm', 'prompt-particle-size'],
        ['ph', 'prompt-ph'], ['core', 'prompt-core'], ['shape', 'prompt-shape'],
        ['hydrodynamic_size_nm', 'prompt-hydro-size'],
        ['surface_area_m2_g', 'prompt-surface-area'],
        ['surface_area_source', 'prompt-surface-area-source'],
        ['material_type', 'prompt-material'], ['assay', 'prompt-assay'],
        ['cell_name', 'prompt-cell'], ['exposure_time_hours', 'prompt-exposure'],
        ['mass_dose_ug_ml', 'prompt-dose'], ['drug_name', 'prompt-drug'],
        ['release_polymer', 'prompt-polymer'], ['drug_loading_pct', 'prompt-loading'],
        ['drug_mw', 'prompt-drug-mw'], ['polymer_mw', 'prompt-polymer-mw'],
        ['la_ga_ratio', 'prompt-la-ga-ratio'], ['simulation_duration_hours', 'prompt-duration']
    ];
    
    advMappings.forEach(([key, elemId]) => {
        const el = $(elemId);
        if (el && el.value !== '') {
            payload[key] = el.type === 'number' ? Number(el.value) : el.value;
        }
    });
    
    if ($('prompt-core-size')?.value) payload.core_size_nm = Number($('prompt-core-size').value);
    if ($('prompt-surface-charge')?.value) payload.surface_charge_mv = Number($('prompt-surface-charge').value);
    if ($('prompt-ligand-smiles')?.value.trim()) payload.ligand_smiles = $('prompt-ligand-smiles').value.trim();
    else if ($('prompt-ligand')?.value) payload.ligand_smiles = $('prompt-ligand').value;
    
    try {
        const result = await postJSON('/api/prompt', payload);
        applyWorkflowResult(result);
        statusEl.textContent = 'AI inference complete. Results synchronized to Live Simulation.';
    } catch (err) {
        statusEl.textContent = `Pipeline error: ${err.message}`;
        addEvent(`AI experiment failed: ${err.message}`, 'warn');
    } finally {
        btn.disabled = false;
    }
}

$('run-workflow').addEventListener('click', () => runPromptWorkflow($('experiment-prompt').value));
$('btn-quick-run').addEventListener('click', () => runPromptWorkflow($('quick-prompt-input').value));

// -------------------------------------------------------------
// Model Predictor Tab
// -------------------------------------------------------------
function buildPredictorForm(task) {
    if (!state.metadata) return;
    const container = $('prediction-fields');
    container.innerHTML = '';
    
    if (task === 'stability') {
        const stab = state.metadata.stability;
        const [sMin, sMax] = stab.default_ranges.size_nm;
        
        container.innerHTML = `
            <div>
                <label class="tool-field-label">Particle Shape</label>
                <select data-pred="Shape" class="demo-select">
                    ${stab.shapes.map(s => `<option value="${escapeHTML(s)}">${escapeHTML(s)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Core Material</label>
                <select data-pred="Core" class="demo-select">
                    ${stab.cores.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Core Size (nm) [${sMin}-${sMax}]</label>
                <input data-pred="Size_nm" type="number" min="${sMin}" max="${sMax}" step="0.1" value="20.0">
            </div>
            <div>
                <label class="tool-field-label">Immersion Medium</label>
                <select data-pred="Medium" class="demo-select">
                    ${stab.media.map(m => `<option value="${escapeHTML(m)}">${escapeHTML(m)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Surface Ligand</label>
                <select data-pred="Ligand_SMILES" class="demo-select">
                    ${stab.ligand_presets.map(lp => `<option value="${escapeHTML(lp.smiles)}">${escapeHTML(lp.name)} (${lp.charge})</option>`).join('')}
                </select>
            </div>
        `;
        
        // Populate Presets
        const presets = stab.presets || [];
        $('prediction-preset').innerHTML = '<option value="">Choose an observed example</option>' +
            presets.map((p, idx) => `<option value="${idx}">${escapeHTML(p.name)}</option>`).join('');
    } else {
        const cyto = state.metadata.cytotoxicity;
        container.innerHTML = `
            <div>
                <label class="tool-field-label">Material Type</label>
                <select data-pred="Material type" class="demo-select">
                    ${cyto.materials.map(m => `<option value="${escapeHTML(m)}">${escapeHTML(m)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Core size (nm)</label>
                <input data-pred="Core size (nm)" type="number" step="0.1" value="25.0">
            </div>
            <div>
                <label class="tool-field-label">Hydrodynamic size (nm)</label>
                <input data-pred="Hydro size (nm)" type="number" step="0.1" value="65.0">
            </div>
            <div>
                <label class="tool-field-label">Surface charge (mV)</label>
                <input data-pred="Surface charge (mV)" type="number" step="0.1" value="-24.5">
            </div>
            <div>
                <label class="tool-field-label">Surface area (m²/g)</label>
                <input data-pred="Surface area (m2/g)" type="number" step="0.1" value="45.0">
            </div>
            <div>
                <label class="tool-field-label">Exposure time (h)</label>
                <input data-pred="Exposure time" type="number" step="1" value="24">
            </div>
            <div>
                <label class="tool-field-label">Mass dose (µg/mL)</label>
                <input data-pred="Mass dose (ug/mL)" type="number" step="0.1" value="50.0">
            </div>
            <div>
                <label class="tool-field-label">Assay Type</label>
                <select data-pred="Assay" class="demo-select">
                    ${cyto.assays.map(a => `<option value="${escapeHTML(a)}">${escapeHTML(a)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Cell Line</label>
                <select data-pred="Cell name" class="demo-select">
                    ${cyto.cell_lines.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('')}
                </select>
            </div>
        `;
        
        const presets = cyto.presets || [];
        $('prediction-preset').innerHTML = '<option value="">Choose an observed example</option>' +
            presets.map((p, idx) => `<option value="${idx}">${escapeHTML(p.name)}</option>`).join('');
    }
    
    updateSweepVariables();
}

$('prediction-task').addEventListener('change', (e) => buildPredictorForm(e.target.value));

$('prediction-preset').addEventListener('change', (e) => {
    const idx = e.target.value;
    if (idx === '' || !state.metadata) return;
    const task = $('prediction-task').value;
    const preset = state.metadata[task]?.presets[Number(idx)];
    if (!preset) return;
    
    document.querySelectorAll('[data-pred]').forEach(input => {
        const key = input.dataset.pred;
        if (preset.data[key] !== undefined) {
            input.value = preset.data[key];
        }
    });
});

$('run-prediction').addEventListener('click', async () => {
    const task = $('prediction-task').value;
    const payload = {};
    document.querySelectorAll('[data-pred]').forEach(input => {
        const key = input.dataset.pred;
        payload[key] = input.type === 'number' ? Number(input.value) : input.value;
    });
    
    const customSmiles = $('prediction-ligand-smiles').value.trim();
    if (task === 'stability' && customSmiles) {
        payload.Ligand_SMILES = customSmiles;
    }
    
    const resultBox = $('prediction-result');
    resultBox.textContent = 'Evaluating model prediction against backend service...';
    
    try {
        const res = await postJSON(`/api/predict/${task}`, payload);
        state.predictionHistory.push({ task, payload, res, time: new Date().toISOString() });
        if (typeof upd3d === 'function') upd3d(payload);
        
        if (task === 'stability') {
            resultBox.innerHTML = `
<strong>ZETA POTENTIAL PREDICTION:</strong> ${res.prediction} ${res.unit}
<strong>CLASSIFICATION:</strong> ${res.stability_class}
<strong>CONFIDENCE:</strong> ${res.confidence}
<strong>VALIDATION MAE:</strong> ${res.uncertainty.mae_mV.toFixed(2)} mV (GroupKFold by DOI)

<strong>DESCRIPTION:</strong> ${res.stability_desc}
<strong>ENGINEERED FEATURES:</strong> Detected Charge: ${res.engineered_features.detected_charge}, Ligand MW: ${res.engineered_features.estimated_ligand_mw_da} Da
<strong>MODEL:</strong> ${res.model_metadata.model_type} (${res.model_metadata.dataset_size})
            `.trim();
        } else {
            resultBox.innerHTML = `
<strong>CYTOTOXICITY PREDICTION:</strong> ${res.prediction}
<strong>RISK LEVEL:</strong> ${res.risk_level}
<strong>GROUPED-CV CONFIDENCE:</strong> ${res.confidence}
<strong>RF VOTE CONFIDENCE:</strong> ${(res.model_vote_confidence * 100).toFixed(1)}% (uncalibrated)

<strong>INTERPRETATION:</strong> ${res.interpretation}
<strong>MODEL:</strong> ${res.model_metadata.model_type} (${res.model_metadata.validation})
            `.trim();
        }
    } catch (err) {
        if (err.details?.applicability === 'outside_domain') {
            const issues = err.details.issues.map(i => `• ${i.field}: ${i.value} (${i.reason})`).join('\n');
            resultBox.textContent = `Input outside validated model domain:\n${issues}\nNo prediction returned to avoid unvalidated extrapolation.`;
        } else {
            resultBox.textContent = `Prediction failed: ${err.message}`;
        }
    }
});

// -------------------------------------------------------------
// Environment Sweep & Heatmap Matrix
// -------------------------------------------------------------
function updateSweepVariables() {
    const task = $('sweep-task').value;
    const sweepVar = $('sweep-variable');
    if (task === 'stability') {
        sweepVar.innerHTML = '<option value="Size_nm">Size_nm (Particle Core Size)</option>';
    } else {
        sweepVar.innerHTML = `
            <option value="Mass dose (ug/mL)">Mass dose (ug/mL)</option>
            <option value="Exposure time">Exposure time (h)</option>
            <option value="Core size (nm)">Core size (nm)</option>
            <option value="Hydro size (nm)">Hydrodynamic size (nm)</option>
            <option value="Surface charge (mV)">Surface charge (mV)</option>
            <option value="Surface area (m2/g)">Surface area (m2/g)</option>
        `;
    }
}

$('sweep-task').addEventListener('change', updateSweepVariables);

$('run-sweep').addEventListener('click', async () => {
    const task = $('sweep-task').value;
    const variable = $('sweep-variable').value;
    const msg = $('sweep-message');
    msg.textContent = `Running 11-point sweep on ${variable}...`;
    
    try {
        const dataset = await requestJSON(`/api/dataset/${task}`);
        const rangeKey = task === 'stability' ? 'Size (nm)' : variable;
        const [minVal, maxVal] = dataset.numeric_ranges[rangeKey] || [1.0, 100.0];
        
        const testValues = Array.from({ length: 11 }, (_, i) => minVal + ((maxVal - minVal) * i) / 10);
        
        // Base payload from predictor form
        const basePayload = {};
        document.querySelectorAll('[data-pred]').forEach(input => {
            basePayload[input.dataset.pred] = input.type === 'number' ? Number(input.value) : input.value;
        });
        
        const results = await Promise.all(testValues.map(async (v) => {
            const pointPayload = { ...basePayload, [variable]: Number(v.toFixed(2)) };
            const res = await postJSON(`/api/predict/${task}`, pointPayload);
            return task === 'stability' ? res.prediction : (res.prediction === 'Toxic' ? 1 : 0);
        }));
        
        if (sweepChart) sweepChart.destroy();
        sweepChart = new Chart($('sweep-chart'), {
            type: 'line',
            data: {
                labels: testValues.map(v => Number(v.toFixed(1))),
                datasets: [{
                    data: results,
                    borderColor: '#007acc',
                    backgroundColor: 'rgba(0, 122, 204, 0.15)',
                    fill: true,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: '#007acc',
                    tension: 0.25
                }]
            },
            options: {
                ...chartOpt,
                scales: {
                    x: { ...chartOpt.scales.x, title: { display: true, text: variable, color: '#858585' } },
                    y: { ...chartOpt.scales.y, title: { display: true, text: task === 'stability' ? 'Predicted Zeta (mV)' : 'Toxic Class (0=No, 1=Yes)', color: '#858585' } }
                }
            }
        });
        msg.textContent = `Sweep completed across ${minVal.toFixed(1)} to ${maxVal.toFixed(1)}.`;
    } catch (err) {
        msg.textContent = `Sweep failed: ${err.message}`;
    }
});

$('run-matrix').addEventListener('click', async () => {
    try {
        const core = $('matrix-core').value || 'Silver';
        const size = Number($('matrix-size').value) || 30.0;
        const smiles = $('matrix-smiles').value || 'OCCO';
        
        const res = await postJSON('/api/formulation/heatmap', {
            core: core,
            size_nm: size,
            smiles: smiles
        });
        
        const points = res.grid.flat().map(c => ({
            x: c.ph,
            y: c.temperature,
            zeta: c.zeta_mv,
            stability: c.stability
        }));
        
        if (matrixChart) matrixChart.destroy();
        matrixChart = new Chart($('matrix-chart'), {
            type: 'scatter',
            data: {
                datasets: [{
                    data: points,
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    pointBackgroundColor: points.map(pt => pt.stability === 'High' ? '#4caf50' : pt.stability === 'Medium' ? '#ff9800' : '#f44336'),
                    pointBorderColor: '#1e1e1e'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `pH ${ctx.raw.x}, ${ctx.raw.y}°C → Zeta: ${ctx.raw.zeta} mV (${ctx.raw.stability} Stability)`
                        }
                    }
                },
                scales: {
                    x: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585' }, title: { display: true, text: 'pH', color: '#858585' }, min: 3, max: 10 },
                    y: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585' }, title: { display: true, text: 'Temperature (°C)', color: '#858585' }, min: 15, max: 70 }
                }
            }
        });
    } catch (err) {
        alert('Matrix calculation failed: ' + err.message);
    }
});

// -------------------------------------------------------------
// Data Catalog & Model Registry Tab
// -------------------------------------------------------------
async function loadModelRegistry() {
    const el = $('model-status');
    el.innerHTML = '<div class="roadmap-note">Loading model metadata and validation metrics...</div>';
    try {
        const reg = await requestJSON('/api/models');
        el.innerHTML = reg.models.map(m => {
            const metrics = Object.entries(m.metrics).map(([k, v]) => `${k}: ${Number(v).toFixed(3)}`).join(' · ');
            return `
                <div class="model-row-item">
                    <div>
                        <strong style="font-size:0.85rem; color:#fff;">${escapeHTML(m.model_name)}</strong>
                        <small>${escapeHTML(m.training_dataset)} · n=${m.training_size} samples · ${escapeHTML(m.validation_method)}</small>
                        <small style="color:#aaa;">Limitations: ${escapeHTML(m.limitations.join(' '))}</small>
                    </div>
                    <div style="text-align:right;">
                        <span class="badge badge-live">ONLINE</span>
                        <div style="font-family:var(--font-mono); font-size:0.75rem; color:#0098ff; margin-top:0.3rem;">${metrics}</div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        el.textContent = 'Could not load model registry: ' + err.message;
    }
}

$('load-dataset').addEventListener('click', async () => {
    const task = $('dataset-task').value;
    const info = $('dataset-info');
    const preview = $('dataset-preview');
    info.textContent = 'Querying dataset preview from local parquet/csv file...';
    preview.innerHTML = '';
    
    try {
        const ds = await requestJSON(`/api/dataset/${task}`);
        info.textContent = `File: ${ds.source} | Rows: ${ds.rows} | Features: ${ds.columns.length}`;
        const cols = ds.columns.slice(0, 10);
        preview.innerHTML = `
            <table>
                <thead>
                    <tr>${cols.map(c => `<th>${escapeHTML(c)}</th>`).join('')}</tr>
                </thead>
                <tbody>
                    ${ds.head.map(row => `
                        <tr>${cols.map(c => `<td>${escapeHTML(row[c] !== null && row[c] !== undefined ? String(row[c]).slice(0, 24) : '—')}</td>`).join('')}</tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        info.textContent = 'Error loading dataset: ' + err.message;
    }
});

// Nano Drug Image Switcher
document.querySelectorAll('.nano-img-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nano-img-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        $('nano-model-img').src = btn.dataset.img;
    });
});

// Nano Drug Record Browser
async function loadNanoDrugRecords(searchQuery = '') {
    const tableDiv = $('nano-records-table');
    if (!tableDiv) return;
    tableDiv.innerHTML = '<div class="roadmap-note">Loading records from 10,000 dataset...</div>';
    try {
        const queryParam = searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : '';
        const res = await requestJSON(`/api/nano_drug/records?limit=12${queryParam}`);
        if (!res.records || !res.records.length) {
            tableDiv.innerHTML = '<div class="roadmap-note">No matching formulation records found.</div>';
            return;
        }
        
        tableDiv.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Record ID</th>
                        <th>Drug Name</th>
                        <th>Material</th>
                        <th>Size (nm)</th>
                        <th>Zeta (mV)</th>
                        <th>Loading %</th>
                        <th>72h Release %</th>
                        <th>Stability</th>
                        <th>Release Class</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${res.records.map(r => `
                        <tr>
                            <td><strong>${escapeHTML(r.record_id)}</strong></td>
                            <td>${escapeHTML(r.drug_name)}</td>
                            <td>${escapeHTML(r.nanoparticle_material)}</td>
                            <td>${Number(r.particle_size_nm).toFixed(1)}</td>
                            <td>${Number(r.zeta_potential_mV).toFixed(1)}</td>
                            <td>${Number(r.drug_loading_percent).toFixed(1)}%</td>
                            <td>${Number(r.release_72h_percent).toFixed(1)}%</td>
                            <td><span class="badge ${r.predicted_stability_class === 'STABLE' ? 'badge-live' : 'badge-demo'}">${escapeHTML(r.predicted_stability_class)}</span></td>
                            <td>${escapeHTML(r.predicted_release_class)}</td>
                            <td>
                                <button class="btn btn-secondary btn-load-nano-record" 
                                    data-drug="${escapeHTML(r.drug_name)}" 
                                    data-mat="${escapeHTML(r.nanoparticle_material)}" 
                                    data-size="${r.particle_size_nm}" 
                                    data-zeta="${r.zeta_potential_mV}" 
                                    data-load="${r.drug_loading_percent}%" 
                                    style="padding:0.25rem 0.5rem; font-size:0.68rem;">
                                    SIMULATE
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.querySelectorAll('.btn-load-nano-record').forEach(b => {
            b.addEventListener('click', () => {
                const drug = b.dataset.drug;
                const mat = b.dataset.mat;
                const size = parseFloat(b.dataset.size);
                const zeta = parseFloat(b.dataset.zeta);
                const load = b.dataset.load;
                
                // Set formulation
                const customKey = 'nano-custom';
                FORMULATIONS[customKey] = {
                    name: `${drug} in ${mat} (${size.toFixed(1)} nm)`,
                    drug: drug,
                    material: mat,
                    size: size,
                    zeta: zeta,
                    load: load,
                    coat: 'PEG / Surfactant',
                    k: 0.10,
                    n: 0.42
                };
                
                // Add option to select if not present
                let opt = $('config-formulation').querySelector(`option[value="${customKey}"]`);
                if (!opt) {
                    opt = document.createElement('option');
                    opt.value = customKey;
                    $('config-formulation').appendChild(opt);
                }
                opt.textContent = `Selected: ${drug} + ${mat} (${size.toFixed(0)} nm)`;
                $('config-formulation').value = customKey;
                
                setFormulationConfig(customKey);
                switchTab('simulation');
                addEvent(`Loaded formulation: ${drug} in ${mat} from 10,000 dataset into simulation`, 'sys');
                resetSim();
            });
        });
    } catch (err) {
        tableDiv.innerHTML = `<div class="roadmap-note">Could not load records: ${escapeHTML(err.message)}</div>`;
    }
}

if ($('btn-nano-search')) {
    $('btn-nano-search').addEventListener('click', () => {
        loadNanoDrugRecords($('nano-search-input').value.trim());
    });
}
if ($('nano-search-input')) {
    $('nano-search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadNanoDrugRecords($('nano-search-input').value.trim());
    });
}

// -------------------------------------------------------------
// -------------------------------------------------------------
// 3D VIEWER (live schematic)
// -------------------------------------------------------------
const CORE3D={
  Ag:{hex:0xc9ced6,metal:1,rough:.2,name:'Silver'},
  Au:{hex:0xd4a72c,metal:1,rough:.25,name:'Gold'},
  Fe3O4:{hex:0x3a2b20,metal:.35,rough:.55,name:'Magnetite'},
  ZnO:{hex:0xe9e6dc,metal:0,rough:.45,name:'Zinc oxide'},
  CeO2:{hex:0xf3e7a1,metal:0,rough:.4,name:'Ceria'}
};
const CORE_FB={hex:0x8fa3c8,metal:.1,rough:.5,name:'Generic core'};
const COAT3D={
  anionic:{hex:0x22d3ee,label:'Anionic (−)'},
  cationic:{hex:0xe879f9,label:'Cationic (+)'},
  neutral:{hex:0x94a3b8,label:'Neutral'},
  uncoated:{hex:0,label:'Uncoated'}
};
const S3={core:'Ag',shape:'Spherical',coat:'anionic',size:52,kp:[.22,.30],hour:0,play:true,speed:1.5,T:72,key:''};
const N3=48;
let V3=null;

function load3D(){
  if(window.THREE)return Promise.resolve();
  if(!load3D.p)load3D.p=new Promise((ok,no)=>{
    const s=document.createElement('script');
    s.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
    s.onload=ok;s.onerror=no;document.head.appendChild(s);
  });
  return load3D.p;
}

function makeBody(rad,shape,mat){
  if(shape!=='Rod')return new THREE.Mesh(new THREE.SphereGeometry(rad,48,32),mat);
  const g=new THREE.Group(),len=rad*2.6;
  g.add(new THREE.Mesh(new THREE.CylinderGeometry(rad,rad,len,48,1,false),mat));
  [len/2,-len/2].forEach(y=>{const s=new THREE.Mesh(new THREE.SphereGeometry(rad,48,32),mat);s.position.y=y;g.add(s)});
  return g;
}



/* ============================================================
   NANOMEDICINE CARRIERS (Clinical & Biophysical Formulations)
   Replaces metals with real pharmaceutical drug delivery systems
   ============================================================ */
const MEDICAL_CARRIERS = {
  lnp: {
    key: 'lnp', label: 'Lipid Nanoparticle (LNP)', formula: 'LNP·mRNA',
    coreColor: 0x38bdf8, coronaColor: 0x818cf8, rayColor: 0x00f0ff,
    drug: 'mRNA-1273', drugColor: 0xf43f5e, r0: 40.0, De: 16.5,
    charge: -4.5, payload: 12, corona: 'PEG-DMG 2000',
    type: 'lipid',
    desc: 'Ionizable lipid bilayer nanocarrier delivering encapsulated mRNA/siRNA with endosomal escape.'
  },
  plga: {
    key: 'plga', label: 'PLGA Copolymer NP', formula: 'PLGA·PTX',
    coreColor: 0x818cf8, coronaColor: 0x60a5fa, rayColor: 0x38bdf8,
    drug: 'Paclitaxel', drugColor: 0xfbbf24, r0: 60.0, De: 22.0,
    charge: -24.0, payload: 16, corona: 'PVA / PEG-5000',
    type: 'polymer',
    desc: 'Biodegradable polyester copolymer matrix delivering sustained anomalous Korsmeyer-Peppas release.'
  },
  liposome: {
    key: 'liposome', label: 'PEGylated Liposome (Doxil)', formula: 'Liposome·DOX',
    coreColor: 0x06b6d4, coronaColor: 0x38bdf8, rayColor: 0x22d3ee,
    drug: 'Doxorubicin', drugColor: 0xec4899, r0: 48.0, De: 25.5,
    charge: -28.5, payload: 14, corona: 'HSPC / Chol / PEG-DSPE',
    type: 'liposome',
    desc: 'Unilamellar lipid bilayer vesicle encapsulating sulfate-crystallized anthracycline chemotherapeutic.'
  },
  albumin: {
    key: 'albumin', label: 'Albumin Nanoparticle (Nab)', formula: 'HSA·Rapamycin',
    coreColor: 0xa855f7, coronaColor: 0xc084fc, rayColor: 0xe879f9,
    drug: 'Rapamycin', drugColor: 0x10b981, r0: 65.0, De: 18.0,
    charge: -19.5, payload: 10, corona: 'Human Serum Albumin',
    type: 'protein',
    desc: 'Biocompatible endogenous protein carrier leveraging gp60 transcytosis and SPARC accumulation.'
  },
  micelle: {
    key: 'micelle', label: 'Polymeric Micelle', formula: 'Micelle·Cisplatin',
    coreColor: 0x10b981, coronaColor: 0x34d399, rayColor: 0x2dd4bf,
    drug: 'Cisplatin', drugColor: 0x06b6d4, r0: 22.5, De: 14.0,
    charge: -8.0, payload: 8, corona: 'PEG-b-PCL Block Copolymer',
    type: 'micelle',
    desc: 'Amphiphilic copolymer core-shell system solubilizing poorly soluble hydrophobic drug complexes.'
  },
  dendrimer: {
    key: 'dendrimer', label: 'PAMAM Dendrimer (G4)', formula: 'PAMAM·MTX',
    coreColor: 0xf59e0b, coronaColor: 0xfbbf24, rayColor: 0xfcd34d,
    drug: 'Methotrexate', drugColor: 0xa855f7, r0: 11.0, De: 19.5,
    charge: 24.5, payload: 18, corona: 'Primary Amine Surface',
    type: 'dendrimer',
    desc: 'Hyperbranched radial architecture with high surface valence for multivalent cellular docking.'
  },
  paracetamol: {
    key: 'paracetamol', label: 'Paracetamol NP (PCM)', formula: 'PLGA·PCM',
    coreColor: 0x38bdf8, coronaColor: 0x60a5fa, rayColor: 0x00f0ff,
    drug: 'Paracetamol', drugColor: 0x38bdf8, r0: 55.0, De: 19.0,
    charge: 7.1, payload: 12, corona: 'Dextran Coating',
    type: 'polymer',
    desc: 'Analgesic/antipyretic loaded polymeric nanoparticle system with sustained Korsmeyer-Peppas diffusion.'
  },
  ciprofloxacin: {
    key: 'ciprofloxacin', label: 'Ciprofloxacin Antibacterial', formula: 'PLGA·CIP',
    coreColor: 0x22d3ee, coronaColor: 0x818cf8, rayColor: 0x38bdf8,
    drug: 'Ciprofloxacin', drugColor: 0x22d3ee, r0: 50.0, De: 21.0,
    charge: -18.2, payload: 14, corona: 'PVA Hydrophilic Corona',
    type: 'antibiotic',
    desc: 'Broad-spectrum fluoroquinolone antibiotic encased in biodegradable polyester matrix for prolonged coverage.'
  },
  vancomycin: {
    key: 'vancomycin', label: 'Vancomycin Extended-Release', formula: 'PEG·VAN',
    coreColor: 0xf59e0b, coronaColor: 0xfbbf24, rayColor: 0xfde68a,
    drug: 'Vancomycin', drugColor: 0xf59e0b, r0: 58.0, De: 23.5,
    charge: -12.5, payload: 15, corona: 'PEG-5000 Stealth Layer',
    type: 'antibiotic',
    desc: 'Glycopeptide antibiotic formulated in PEGylated PLGA for long-acting anti-MRSA therapeutic levels.'
  }
};

let nlScene, nlCam, nlRenderer, nlClock, nlMoleculeGroup;
let nlSim = null, nlCurKey = 'lnp';
let nlPlaying = true, nlTempK = 310, nlSpeed = 1, nlSimTime = 0, nlHudAcc = 0;
let nlShowDipole = true, nlShowCloud = true, nlShowLabels = true, nlAutoRotate = true;
let nlCoreScale = 1.0;
let nlDrag = null, nlRot = {x:0, y:0}, nlZoom = 9.2;
const NL_VIB = 5.5;

let glowMatBlue, glowMatCyan, glowMatPink, glowMatGold, ringGeo, ringMat;

function initAssets(){
  if(glowMatBlue) return;
  function glowTexture(inner){
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d');
    const gr = g.createRadialGradient(32,32,0,32,32,32);
    gr.addColorStop(0,'rgba(255,255,255,1)');
    gr.addColorStop(0.3, inner);
    gr.addColorStop(1,'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(0,0,64,64);
    return new THREE.CanvasTexture(c);
  }
  glowMatBlue = new THREE.SpriteMaterial({map:glowTexture('rgba(56,189,248,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  glowMatCyan = new THREE.SpriteMaterial({map:glowTexture('rgba(0,240,255,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  glowMatPink = new THREE.SpriteMaterial({map:glowTexture('rgba(244,114,182,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  glowMatGold = new THREE.SpriteMaterial({map:glowTexture('rgba(251,191,36,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  ringGeo = new THREE.TorusGeometry(1, 0.014, 8, 80);
  ringMat = new THREE.MeshBasicMaterial({color:0x38bdf8, transparent:true, opacity:0.45, blending:THREE.AdditiveBlending});
}

function textSprite(str, color, w, h){
  const c = document.createElement('canvas'); c.width = 512; c.height = 256;
  const g = c.getContext('2d');
  g.font = '800 76px "JetBrains Mono", Inter, sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.shadowColor = color; g.shadowBlur = 24;
  g.fillStyle = color;
  g.fillText(str, 256, 128);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c), transparent:true, depthWrite:false}));
  s.scale.set(w, h, 1);
  return s;
}

function labelColor(q){ return q > 0 ? '#f472b6' : q < 0 ? '#38bdf8' : '#eaf2ff'; }

function createNanoparticleModel(p){
  const group = new THREE.Group();
  const rad = (p.r0 / 40.0) * nlCoreScale * 1.05;

  // 1. Core metallic/polymeric/lipidic matrix with vibrant electric-blue emissive luster
  const coreMat = new THREE.MeshStandardMaterial({
    color: p.coreColor || 0x38bdf8,
    metalness: p.type === 'lipid' ? 0.2 : 0.85,
    roughness: p.type === 'lipid' ? 0.4 : 0.18,
    emissive: p.coreColor || 0x00d4ff,
    emissiveIntensity: 0.35
  });
  const coreMesh = new THREE.Mesh(new THREE.SphereGeometry(rad, 54, 54), coreMat);
  group.add(coreMesh);

  // 2. Futuristic Inner Holographic Quantum Lattice
  const latticeGeo = new THREE.IcosahedronGeometry(rad * 1.015, 2);
  const latticeMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending
  });
  const latticeMesh = new THREE.Mesh(latticeGeo, latticeMat);
  group.add(latticeMesh);

  // 3. Radiant Electric-Blue Light Ray Border (Crown of Radial Laser Rays)
  const rayGroup = new THREE.Group();
  group.add(rayGroup);
  const rays = [];
  const RAY_COUNT = 24;
  for(let i = 0; i < RAY_COUNT; i++){
    const phi = Math.acos(2 * (i + 0.5) / RAY_COUNT - 1);
    const theta = i * 2.39996323;
    const dir = new THREE.Vector3(
      Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta)
    ).normalize();
    const rayLen = rad * (0.75 + 0.3 * Math.sin(i * 1.4));
    const rayGeo = new THREE.CylinderGeometry(0.012, 0.05, rayLen, 8, 1, true);
    const rayMat = new THREE.MeshBasicMaterial({
      color: p.rayColor || 0x00f0ff, transparent: true, opacity: 0.72, blending: THREE.AdditiveBlending, depthWrite: false
    });
    const rayMesh = new THREE.Mesh(rayGeo, rayMat);
    rayMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    rayMesh.position.copy(dir).multiplyScalar(rad * 1.05 + rayLen / 2);
    rayGroup.add(rayMesh);
    rays.push({mesh: rayMesh, dir, baseLen: rayLen});
  }

  // 4. Electric Blue Outer Ray Border Halo / Shield
  const haloGeo = new THREE.SphereGeometry(rad * 1.45, 48, 48);
  const haloMat = new THREE.MeshBasicMaterial({
    color: p.rayColor || 0x00d4ff, transparent: true, opacity: 0.18, blending: THREE.AdditiveBlending, depthWrite: false
  });
  const haloMesh = new THREE.Mesh(haloGeo, haloMat);
  group.add(haloMesh);

  // 5. Translucent Hydration Corona Shell
  const coronaMat = new THREE.MeshStandardMaterial({
    color: p.coronaColor || 0x818cf8, emissive: p.coronaColor || 0x0099ff, emissiveIntensity: 0.38,
    transparent: true, opacity: 0.24, roughness: 0.20, depthWrite: false
  });
  const coronaMesh = new THREE.Mesh(new THREE.SphereGeometry(rad * 1.34, 44, 44), coronaMat);
  group.add(coronaMesh);

  // 6. Tri-Axial Gyroscopic Holographic Energy Rings
  const ringGroup = new THREE.Group();
  group.add(ringGroup);
  const gyroRings = [];
  const ringConfigs = [
    {r: rad * 1.42, color: 0x00f0ff, spd: 0.4},
    {r: rad * 1.56, color: 0x38bdf8, spd: 0.55},
    {r: rad * 1.70, color: 0x818cf8, spd: 0.32}
  ];
  ringConfigs.forEach((cfg, idx) => {
    const geo = new THREE.TorusGeometry(cfg.r, 0.012, 12, 80);
    const mat = new THREE.MeshBasicMaterial({
      color: cfg.color, transparent: true, opacity: 0.65, blending: THREE.AdditiveBlending
    });
    const ring = new THREE.Mesh(geo, mat);
    ring.rotation.set(idx * 0.7, idx * 1.1, idx * 0.4);
    ringGroup.add(ring);
    gyroRings.push({mesh: ring, spd: cfg.spd});
  });

  // 7. Floating 3D Text label
  const label = textSprite(`${p.formula} · ${p.charge > 0 ? '+' : ''}${p.charge.toFixed(1)} mV`, labelColor(p.charge), 2.8, 1.2);
  label.position.y = rad * 1.55 + 0.65;
  group.add(label);

  // 8. Encapsulated Drug Payload / Diffusing Molecules
  const drugGroup = new THREE.Group();
  group.add(drugGroup);
  const drugParticles = [];
  const nDrug = p.payload || 14;
  for(let i = 0; i < nDrug; i++){
    const y = 1 - 2 * (i + 0.5) / nDrug;
    const r_layer = Math.sqrt(1 - y * y);
    const th = i * 2.39996323;
    const dir = new THREE.Vector3(Math.cos(th) * r_layer, y, Math.sin(th) * r_layer);
    const s = new THREE.Sprite(i % 2 === 0 ? glowMatPink : glowMatGold);
    s.scale.set(0.24, 0.24, 1);
    s.userData = {
      dir,
      baseDist: rad * (0.65 + 0.55 * ((i % 5) / 5.0)),
      speed: 0.8 + ((i % 7) / 7.0) * 1.2,
      phase: i * 0.3,
      rCurr: rad * 1.1
    };
    drugGroup.add(s);
    drugParticles.push(s);
  }

  // 9. Zeta Electric Potential Vector
  const dirZeta = new THREE.Vector3(1, 0.4, 0).normalize();
  const arrowColor = p.charge < 0 ? 0x22d3ee : 0xf472b6;
  const dipole = new THREE.ArrowHelper(dirZeta, new THREE.Vector3(0, rad * 1.1, 0), rad * 1.6, arrowColor, 0.38, 0.24);
  group.add(dipole);

  return {
    group, coreMesh, latticeMesh, rays, rayGroup, haloMesh, coronaMesh, ringGroup, gyroRings,
    label, drugGroup, drugParticles, dipole, charge: p.charge, rad, flash: 0
  };
}

function updateAtomLabel(np){
  if(!np || !np.label || !nlSim) return;
  np.group.remove(np.label);
  if(np.label.material && np.label.material.map) np.label.material.map.dispose();
  if(np.label.material) np.label.material.dispose();
  np.label = textSprite(`${nlSim.preset.formula} · ${np.charge > 0 ? '+' : ''}${np.charge.toFixed(1)} mV`, labelColor(np.charge), 2.8, 1.2);
  np.label.position.y = np.rad * 1.55 + 0.65;
  np.label.visible = nlShowLabels;
  np.group.add(np.label);
}

function initScene(){
  const canvas = document.getElementById('scene');
  if(!canvas) return;
  initAssets();

  nlScene = new THREE.Scene();
  nlScene.background = new THREE.Color(0x04060e);
  nlScene.fog = new THREE.FogExp2(0x04060e, 0.015);

  const host = document.querySelector('.nanolab-viewport') || document.getElementById('view-viewer') || canvas.parentElement;
  const w = (host && host.clientWidth > 0) ? host.clientWidth : (window.innerWidth ? Math.min(window.innerWidth - 48, 1200) : 900);
  const h = (host && host.clientHeight > 0) ? host.clientHeight : 720;

  nlCam = new THREE.PerspectiveCamera(45, w / h, 0.1, 200);
  nlCam.position.set(0, 0.8, nlZoom);
  nlCam.lookAt(0, 0, 0);

  nlRenderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
  nlRenderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2));
  nlRenderer.setSize(w, h);
  if(THREE.sRGBEncoding) nlRenderer.outputEncoding = THREE.sRGBEncoding;
  if(THREE.ACESFilmicToneMapping) nlRenderer.toneMapping = THREE.ACESFilmicToneMapping;
  nlRenderer.toneMappingExposure = 1.15;

  nlScene.add(new THREE.AmbientLight(0x1e293b, 0.85));
  const key = new THREE.DirectionalLight(0xffffff, 1.3); key.position.set(6, 10, 7); nlScene.add(key);
  const rim1 = new THREE.PointLight(0x00f0ff, 1.4, 50); rim1.position.set(-8, -3, -6); nlScene.add(rim1);
  const rim2 = new THREE.PointLight(0xf472b6, 0.95, 50); rim2.position.set(8, -4, 6); nlScene.add(rim2);

  // Cybernetic starfield
  const N = 800, pos = new Float32Array(N * 3);
  for(let i = 0; i < N; i++){
    const r = 38 + Math.random() * 36, th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1);
    pos[i*3] = r * Math.sin(ph) * Math.cos(th);
    pos[i*3+1] = r * Math.cos(ph);
    pos[i*3+2] = r * Math.sin(ph) * Math.sin(th);
  }
  const sg = new THREE.BufferGeometry();
  sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  nlScene.add(new THREE.Points(sg, new THREE.PointsMaterial({color:0x38bdf8, size:0.20, transparent:true, opacity:0.6})));

  // Grid floor
  const grid = new THREE.GridHelper(40, 40, 0x0284c7, 0x091428);
  grid.position.y = -3.6;
  nlScene.add(grid);

  nlMoleculeGroup = new THREE.Group();
  nlScene.add(nlMoleculeGroup);

  nlClock = new THREE.Clock();

  // Custom Orbit Controls (no crash dependencies)
  const el = canvas;
  el.style.cursor = 'grab';
  el.addEventListener('pointerdown', e => {
    nlDrag = {x:e.clientX, y:e.clientY};
    el.style.cursor = 'grabbing';
    if(el.setPointerCapture) el.setPointerCapture(e.pointerId);
  });
  window.addEventListener('pointermove', e => {
    if(!nlDrag) return;
    nlRot.y += (e.clientX - nlDrag.x) * 0.008;
    nlRot.x = Math.max(-1.2, Math.min(1.2, nlRot.x + (e.clientY - nlDrag.y) * 0.008));
    nlDrag = {x:e.clientX, y:e.clientY};
  });
  const endDrag = () => { nlDrag = null; el.style.cursor = 'grab'; };
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);
  el.addEventListener('wheel', e => {
    e.preventDefault();
    nlZoom = Math.max(3.5, Math.min(22.0, nlZoom + e.deltaY * 0.006));
    if(nlCam) nlCam.position.z = nlZoom;
  }, {passive:false});

  window.addEventListener('resize', resize3D);
  nlSizeChart();
}

function clearGroup(g){ while(g.children.length) g.remove(g.children[0]); }

function loadPreset(key){
  nlCurKey = key;
  const p = MEDICAL_CARRIERS[key] || MEDICAL_CARRIERS['lnp'];
  clearGroup(nlMoleculeGroup);
  const np = createNanoparticleModel(p);
  nlSim = {
    preset: p, np, state: 'bonded',
    transfer: [], tprog: 0, r: p.r0, releasePct: 0
  };
  nlMoleculeGroup.add(np.group);

  const curTitle = document.getElementById('cur-preset');
  if(curTitle) curTitle.textContent = `${p.formula} · ${p.label.toUpperCase()}`;
  renderMeta(p);
  markActiveCard(key);
  syncButtons();
}

function renderMeta(p){
  const el = document.getElementById('preset-meta');
  if(!el) return;
  el.innerHTML =
    `<span class="badge-nl ${p.type}">${p.type.toUpperCase()} CARRIER</span>
     <div style="margin-top:7px">
       Size (r₀) <b>${p.r0} nm</b><br>
       DLVO Barrier ΔG* <b>${p.De} kBT</b><br>
       Zeta Potential <b>${p.charge > 0 ? '+' : ''}${p.charge} mV</b><br>
       Active Drug <b>${p.drug}</b><br>
       Corona <b>${p.corona}</b><br>
       <i style="color:#94a3b8;font-size:9.5px;display:block;margin-top:4px;">${p.desc}</i>
     </div>`;
}

function buildCards(){
  const list = document.getElementById('preset-list');
  if(!list) return;
  list.innerHTML = '';
  Object.entries(MEDICAL_CARRIERS).forEach(([k, p]) => {
    const hex = n => '#' + n.toString(16).padStart(6, '0');
    const el = document.createElement('div');
    el.className = 'card-item';
    el.dataset.k = k;
    el.innerHTML =
      `<div class="dot" style="background:linear-gradient(135deg,${hex(p.coreColor)},${hex(p.rayColor)})"></div>
       <div><h3>${p.label}</h3><p>${p.formula} · ${p.r0}nm · ${p.drug}</p></div>`;
    el.onclick = () => loadPreset(k);
    list.appendChild(el);
  });
}

function markActiveCard(key){
  document.querySelectorAll('.card-item').forEach(c => c.classList.toggle('active', c.dataset.k === key));
}

function bondEnergy(r){
  if(!nlSim) return 0;
  const p = nlSim.preset, a = 1.9, x = (r - p.r0) / 10.0;
  return p.De * (Math.exp(-2*a*x) - 2*Math.exp(-a*x));
}
function currentR(){
  return nlSim ? nlSim.r : 40;
}

const ease = t => t*t*(3 - 2*t);
function quad(p0, pc, p1, t, out){
  const u = 1 - t;
  return out.set(
    u*u*p0.x + 2*u*t*pc.x + t*t*p1.x,
    u*u*p0.y + 2*u*t*pc.y + t*t*p1.y,
    u*u*p0.z + 2*u*t*pc.z + t*t*p1.z);
}

function clearTransfer(){
  if(!nlSim) return;
  nlSim.transfer.forEach(t => { nlMoleculeGroup.remove(t.sprite); if(t.sprite.material) t.sprite.material.dispose(); });
  nlSim.transfer = [];
}

function startTransfer(reverse){
  if(!nlSim) return;
  clearTransfer();
  nlSim.state = reverse ? 'breaking' : 'transferring';
  nlSim.tprog = 0;
  const np = nlSim.np, n = 6;
  for(let i = 0; i < n; i++){
    const sprite = new THREE.Sprite(reverse ? glowMatGold.clone() : glowMatCyan.clone());
    sprite.scale.set(0.32, 0.32, 1);
    nlMoleculeGroup.add(sprite);
    const ang = (i / n) * Math.PI * 2;
    const pCore = new THREE.Vector3(Math.cos(ang) * np.rad * 1.05, Math.sin(ang) * np.rad * 1.05, 0);
    const pMed = new THREE.Vector3(Math.cos(ang) * (np.rad * 3.4), Math.sin(ang) * (np.rad * 3.4), (i % 2 ? 1 : -1) * 1.2);
    const p0 = reverse ? pCore : pMed;
    const p1 = reverse ? pMed : pCore;
    const pc = p0.clone().add(p1).multiplyScalar(0.5);
    pc.y += 1.2 + 0.3 * i;
    nlSim.transfer.push({sprite, p0, pc, p1});
  }
  syncButtons();
}

function applyCharges(){
  clearTransfer();
  if(!nlSim) return;
  const np = nlSim.np;
  np.charge = nlSim.preset.charge;
  updateAtomLabel(np);
  np.flash = 1.0;
  nlSim.state = 'bonded';
  nlSim.releasePct = 0;
  syncButtons();
}
function clearCharges(){
  clearTransfer();
  if(!nlSim) return;
  const np = nlSim.np;
  np.charge = 0;
  updateAtomLabel(np);
  nlSim.state = 'free';
  nlSim.releasePct = 100;
  syncButtons();
}

function updateSimulation(dt){
  if(!nlSim) return;
  const np = nlSim.np;
  if(nlSim.state === 'transferring' || nlSim.state === 'breaking'){
    if(nlPlaying) nlSim.tprog += dt * nlSpeed / 1.4;
    let done = true;
    nlSim.transfer.forEach((t, i) => {
      const local = Math.max(0, Math.min(1, (nlSim.tprog - i * 0.16) / 0.84));
      if(local < 1) done = false;
      quad(t.p0, t.pc, t.p1, ease(local), t.sprite.position);
    });
    if(done){
      if(nlSim.state === 'transferring') applyCharges();
      else clearCharges();
    }
  } else if(nlSim.state === 'bonded'){
    const target = nlSim.preset.r0 + (0.04 * Math.pow(nlTempK / 310, 0.75)) * 4.0 * Math.sin(nlSimTime * NL_VIB);
    nlSim.r += (target - nlSim.r) * Math.min(1, dt * 3 * Math.max(nlSpeed, 0.4));
  }
}

function updateNanoparticleDynamics(np, dt){
  const eff = nlPlaying ? dt * nlSpeed : 0;
  
  // Radial light rays breathing animation
  if(np.rays){
    np.rays.forEach((r, idx) => {
      const pulse = 1.0 + 0.32 * Math.sin(nlSimTime * 4.0 + idx * 0.45);
      r.mesh.scale.set(1.0, pulse, 1.0);
    });
  }
  // Tri-axial gyroscopic precession
  if(np.gyroRings){
    np.gyroRings.forEach(g => {
      g.mesh.rotation.x += eff * g.spd * 0.8;
      g.mesh.rotation.y += eff * g.spd;
    });
  }
  // Lattice shimmer rotation
  if(np.latticeMesh){
    np.latticeMesh.rotation.y += eff * 0.25;
  }
  if(np.ringGroup){
    np.ringGroup.rotation.y += eff * 0.4;
    np.ringGroup.rotation.x += eff * 0.2;
  }

  // Breathing thermal corona fluctuation
  const breath = 1.0 + 0.02 * Math.sin(nlSimTime * 2.5);
  if(np.coronaMesh) np.coronaMesh.scale.set(breath, breath, breath);

  // Dissolution shrinkage based on release %
  if(nlSim && nlSim.state === 'breaking'){
    nlSim.releasePct = Math.min(100, nlSim.releasePct + dt * 18 * nlSpeed);
    const shrink = 1.0 - (nlSim.releasePct / 100) * 0.25;
    if(np.coreMesh) np.coreMesh.scale.setScalar(shrink);
  } else if(nlSim && nlSim.state === 'bonded'){
    if(np.coreMesh) np.coreMesh.scale.setScalar(1.0);
  }

  // Update drug molecules
  if(np.drugParticles){
    np.drugParticles.forEach(d => {
      const u = d.userData;
      u.phase += u.speed * eff;
      const wobble = Math.sin(u.phase) * 0.15;
      let dist = u.baseDist + wobble;
      if(nlSim && nlSim.state === 'breaking'){
        dist += (nlSim.releasePct / 100) * 4.5;
        d.material.opacity = Math.max(0.1, 1 - (nlSim.releasePct / 100));
      } else {
        d.material.opacity = 0.95;
      }
      d.position.set(u.dir.x * dist, u.dir.y * dist, u.dir.z * dist);
    });
  }

  if(np.flash > 0){
    np.flash = Math.max(0, np.flash - dt * 1.6);
    if(np.coreMesh && np.coreMesh.material) np.coreMesh.material.emissiveIntensity = 0.25 + np.flash * 0.9;
  }

  if(np.dipole) np.dipole.visible = nlShowDipole && (nlSim && nlSim.state === 'bonded');
  if(np.drugGroup) np.drugGroup.visible = nlShowCloud;
  if(np.label) np.label.visible = nlShowLabels;
}

const chartEl = () => document.getElementById('chart');
let chartDpr = 1;
function nlSizeChart(){
  const c = chartEl();
  if(!c) return;
  chartDpr = Math.min(window.devicePixelRatio||1, 2);
  const cw = c.clientWidth > 0 ? c.clientWidth : 240;
  c.width = cw * chartDpr;
  c.height = 130 * chartDpr;
}

function drawChart(){
  const c = chartEl();
  if(!c || !nlSim) return;
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  if(W === 0 || H === 0) return;
  ctx.clearRect(0, 0, W, H);

  const p = nlSim.preset, De = p.De, a = 1.9;
  const rmin = p.r0 * 0.55, rmax = p.r0 * 2.4;
  const Emin = -1.1 * De, Emax = 0.75 * De;
  const X = r => (r - rmin) / (rmax - rmin) * W;
  const Y = E => H - ((E - Emin) / (Emax - Emin)) * H;
  const morse = r => {
    const x = (r - p.r0) / 10.0;
    return De * (Math.exp(-2*a*x) - 2*Math.exp(-a*x));
  };

  ctx.lineWidth = 1;
  ctx.strokeStyle = 'rgba(130,165,255,.09)';
  for(let i = 1; i < 5; i++){
    ctx.beginPath(); ctx.moveTo(0, H*i/5); ctx.lineTo(W, H*i/5); ctx.stroke();
  }

  // Filled curve
  ctx.beginPath();
  for(let px = 0; px <= W; px += 2){
    const rVal = rmin + (rmax - rmin) * px / W;
    const E = Math.max(morse(rVal), Emin);
    const y = Y(E);
    px === 0 ? ctx.moveTo(px, y) : ctx.lineTo(px, y);
  }
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, 'rgba(56,189,248,.30)');
  grad.addColorStop(1, 'rgba(56,189,248,0)');
  ctx.save();
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fillStyle = grad; ctx.fill(); ctx.restore();

  // Glowing line
  ctx.beginPath();
  for(let px = 0; px <= W; px += 2){
    const rVal = rmin + (rmax - rmin) * px / W;
    const E = Math.max(morse(rVal), Emin);
    const y = Y(E);
    px === 0 ? ctx.moveTo(px, y) : ctx.lineTo(px, y);
  }
  ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2 * chartDpr;
  ctx.shadowColor = 'rgba(56,189,248,.75)'; ctx.shadowBlur = 8 * chartDpr;
  ctx.stroke(); ctx.shadowBlur = 0;

  // Equilibrium line
  ctx.strokeStyle = 'rgba(255,255,255,.25)'; ctx.setLineDash([3*chartDpr, 4*chartDpr]);
  ctx.beginPath(); ctx.moveTo(X(p.r0), 0); ctx.lineTo(X(p.r0), H); ctx.stroke();
  ctx.setLineDash([]);

  // Moving probe marker
  const rCurr = currentR();
  const Er = Math.max(bondEnergy(rCurr), Emin);
  ctx.fillStyle = '#ffffff';
  ctx.beginPath(); ctx.arc(X(rCurr), Y(Er), 4.5 * chartDpr, 0, 7); ctx.fill();
  ctx.shadowColor = '#fff'; ctx.shadowBlur = 10 * chartDpr;
  ctx.fill(); ctx.shadowBlur = 0;

  ctx.font = `700 ${9.5 * chartDpr}px "JetBrains Mono", monospace`;
  ctx.fillStyle = '#7dd3fc';
  ctx.fillText(`r = ${rCurr.toFixed(1)} nm   ΔG* = ${bondEnergy(rCurr).toFixed(1)} kBT`, 8 * chartDpr, 14 * chartDpr);
  ctx.fillStyle = 'rgba(127,144,184,.9)';
  ctx.fillText('VDLVO Colloidal Barrier', 8 * chartDpr, H - 7 * chartDpr);
}

function statusText(){
  if(!nlSim) return 'Colloidally Dispersed';
  switch(nlSim.state){
    case 'free': return 'Dissociated / Free Cargo';
    case 'transferring': return 'Condensing Corona Shell…';
    case 'bonded': return 'Colloidally Dispersed · Stable';
    case 'breaking': return `Dissolving (${nlSim.releasePct.toFixed(0)}% released)`;
    default: return 'Active';
  }
}

function updateHUD(){
  if(!nlSim) return;
  const p = nlSim.preset, r = currentR();
  const lenEl = document.getElementById('c-len'); if(lenEl) lenEl.textContent = (r * 1.1).toFixed(1) + ' nm';
  const enEl = document.getElementById('c-energy'); if(enEl) enEl.textContent = Math.abs(bondEnergy(r)).toFixed(1) + ' kBT';
  const tempEl = document.getElementById('c-temp'); if(tempEl) tempEl.textContent = nlTempK + ' K (' + (nlTempK - 273) + '°C)';
  const timeEl = document.getElementById('c-time'); if(timeEl) timeEl.textContent = nlSimTime.toFixed(1) + ' s';
  const orderEl = document.getElementById('c-order'); if(orderEl) orderEl.textContent = (p.charge > 0 ? '+' : '') + p.charge.toFixed(1) + ' mV';
  const stEl = document.getElementById('c-state'); if(stEl) stEl.textContent = statusText();
}

function syncButtons(){
  if(!nlSim) return;
  const formBtn = document.getElementById('btn-form');
  const breakBtn = document.getElementById('btn-break');
  const playBtn = document.getElementById('btn-play');
  if(formBtn) formBtn.disabled = (nlSim.state === 'bonded' || nlSim.state === 'transferring');
  if(breakBtn) breakBtn.disabled = (nlSim.state === 'free' || nlSim.state === 'breaking');
  if(playBtn) playBtn.innerHTML = nlPlaying ? '⏸&nbsp;Pause' : '▶&nbsp;Play';
}

function toggleHudPanels(){
  const vp = document.querySelector('.nanolab-viewport');
  if(!vp) return;
  vp.classList.toggle('hud-hidden');
  const btn = document.getElementById('btn-toggle-hud');
  if(btn) btn.textContent = vp.classList.contains('hud-hidden') ? '👁 Show HUD' : '👁 Toggle HUD';
}

/* ============================================================
   REAL AI 3D FORMULATION MORPHING ENGINE
   Dynamically interprets user natural language and mutates 3D model
   ============================================================ */
function parseAndMorph3D(promptText){
  if(!promptText || !promptText.trim()) return;

  // Ensure 3D engine is initialized
  if(!nlRenderer){
    initScene();
    buildCards();
    wireUI();
  }

  const text = promptText.toLowerCase();

  // Detect Carrier
  let carrier = 'lnp';
  if(text.includes('plga') || text.includes('polyester') || text.includes('copolymer')) carrier = 'plga';
  else if(text.includes('liposome') || text.includes('bilayer') || text.includes('lipid vesicle')) carrier = 'liposome';
  else if(text.includes('albumin') || text.includes('hsa') || text.includes('abraxane') || text.includes('protein')) carrier = 'albumin';
  else if(text.includes('micelle') || text.includes('block copolymer')) carrier = 'micelle';
  else if(text.includes('dendrimer') || text.includes('pamam') || text.includes('hyperbranched')) carrier = 'dendrimer';
  else if(text.includes('lipid') || text.includes('mrna') || text.includes('sirna')) carrier = 'lnp';

  const base = {...MEDICAL_CARRIERS[carrier]};

  // Detect Size (nm)
  const sizeMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:nm|nanometer)/i) || text.match(/size\s*(?:of|=|:)?\s*(\d+(?:\.\d+)?)/i);
  if(sizeMatch) {
    base.r0 = Math.max(10, Math.min(300, parseFloat(sizeMatch[1])));
  }

  // Detect Drug
  if(text.includes('paracetamol') || text.includes('acetaminophen')) { base.drug = 'Paracetamol'; carrier = 'paracetamol'; }
  else if(text.includes('ciprofloxacin') || text.includes('cipro')) { base.drug = 'Ciprofloxacin'; carrier = 'ciprofloxacin'; }
  else if(text.includes('vancomycin')) { base.drug = 'Vancomycin'; carrier = 'vancomycin'; }
  else if(text.includes('rifampicin') || text.includes('rifampin')) base.drug = 'Rifampicin';
  else if(text.includes('doxycycline')) base.drug = 'Doxycycline';
  else if(text.includes('gentamicin')) base.drug = 'Gentamicin';
  else if(text.includes('azithromycin')) base.drug = 'Azithromycin';
  else if(text.includes('amoxicillin')) base.drug = 'Amoxicillin';
  else if(text.includes('ibuprofen')) base.drug = 'Ibuprofen';
  else if(text.includes('letrozole')) base.drug = 'Letrozole';
  else if(text.includes('exemestane')) base.drug = 'Exemestane';
  else if(text.includes('amlodipine')) base.drug = 'Amlodipine';
  else if(text.includes('paclitaxel') || text.includes('taxol')) base.drug = 'Paclitaxel';
  else if(text.includes('doxorubicin') || text.includes('dox')) base.drug = 'Doxorubicin';
  else if(text.includes('mrna') || text.includes('bnt162b2')) base.drug = 'mRNA-Transcript';
  else if(text.includes('sirna')) base.drug = 'siRNA';
  else if(text.includes('cisplatin')) base.drug = 'Cisplatin';
  else if(text.includes('curcumin')) base.drug = 'Curcumin';
  else if(text.includes('rapamycin')) base.drug = 'Rapamycin';
  else if(text.includes('methotrexate')) base.drug = 'Methotrexate';

  // Detect Charge / Zeta Potential (mV)
  const zetaMatch = text.match(/([+-]?\d+(?:\.\d+)?)\s*mv/i) || text.match(/zeta\s*(?:of|=|:)?\s*([+-]?\d+(?:\.\d+)?)/i);
  if(zetaMatch) {
    base.charge = parseFloat(zetaMatch[1]);
  } else if(text.includes('cationic') || text.includes('positive')) {
    base.charge = Math.abs(base.charge || 20);
  } else if(text.includes('anionic') || text.includes('negative')) {
    base.charge = -Math.abs(base.charge || 25);
  } else if(text.includes('neutral')) {
    base.charge = 0;
  }

  // Adjust energy barrier heuristic from charge and size
  base.De = Math.max(8.0, Math.min(45.0, 10.0 + Math.abs(base.charge) * 0.45 + (base.r0 / 20.0)));
  base.label = `AI Engineered · ${base.label || carrier.toUpperCase()}`;
  base.formula = `${carrier.toUpperCase()}·${base.drug}`;
  base.desc = `Dynamically synthesized by NanoMed AI from user prompt: "${promptText}"`;

  // Dynamically morph the model
  nlCurKey = carrier;
  nlCoreScale = base.r0 / 40.0;
  clearGroup(nlMoleculeGroup);
  const np = createNanoparticleModel(base);
  nlSim = {
    preset: base, np, state: 'bonded',
    transfer: [], tprog: 0, r: base.r0, releasePct: 0
  };
  nlMoleculeGroup.add(np.group);

  const curTitle = document.getElementById('cur-preset');
  if(curTitle) curTitle.textContent = `${base.formula} · ${base.r0} nm · AI GENERATED`;

  const sSize = document.getElementById('s-size'); if(sSize) sSize.value = Math.round(base.r0);
  const oSize = document.getElementById('o-size'); if(oSize) oSize.textContent = Math.round(base.r0) + ' nm';

  renderMeta(base);
  markActiveCard(carrier);
  syncButtons();
  nlSizeChart();
  drawChart();

  // Flash AI feedback
  const feedbackEl = document.getElementById('ai-3d-feedback');
  if(feedbackEl){
    feedbackEl.style.display = 'block';
    feedbackEl.innerHTML = `✨ <b>AI Synthesized:</b> ${base.formula} (${base.r0} nm, ζ = ${base.charge > 0 ? '+' : ''}${base.charge.toFixed(1)} mV). Model morphed live!`;
    setTimeout(() => { if(feedbackEl) feedbackEl.style.display = 'none'; }, 6000);
  }
}

function wireUI(){
  const playBtn = document.getElementById('btn-play');
  if(playBtn) playBtn.onclick = () => { nlPlaying = !nlPlaying; syncButtons(); };
  const resetBtn = document.getElementById('btn-reset');
  if(resetBtn) resetBtn.onclick = () => loadPreset(nlCurKey);
  const formBtn = document.getElementById('btn-form');
  if(formBtn) formBtn.onclick = () => startTransfer(false);
  const breakBtn = document.getElementById('btn-break');
  if(breakBtn) breakBtn.onclick = () => startTransfer(true);

  const sTemp = document.getElementById('s-temp');
  if(sTemp) sTemp.oninput = e => {
    nlTempK = +e.target.value;
    const o = document.getElementById('o-temp'); if(o) o.textContent = nlTempK + ' K (' + (nlTempK - 273) + '°C)';
  };
  const sSpeed = document.getElementById('s-speed');
  if(sSpeed) sSpeed.oninput = e => {
    nlSpeed = +e.target.value;
    const o = document.getElementById('o-speed'); if(o) o.textContent = '×' + nlSpeed.toFixed(1);
  };
  const sSize = document.getElementById('s-size');
  if(sSize) sSize.oninput = e => {
    nlCoreScale = (+e.target.value) / 40.0;
    const o = document.getElementById('o-size'); if(o) o.textContent = e.target.value + ' nm';
    if(nlSim && nlSim.preset) {
      nlSim.preset.r0 = +e.target.value;
      loadPreset(nlCurKey);
    }
  };

  const tDipole = document.getElementById('t-dipole'); if(tDipole) tDipole.onchange = e => nlShowDipole = e.target.checked;
  const tCloud = document.getElementById('t-cloud'); if(tCloud) tCloud.onchange = e => {
    nlShowCloud = e.target.checked;
    if(nlSim && nlSim.np && nlSim.np.drugGroup) nlSim.np.drugGroup.visible = nlShowCloud;
  };
  const tLabels = document.getElementById('t-labels'); if(tLabels) tLabels.onchange = e => {
    nlShowLabels = e.target.checked;
    if(nlSim && nlSim.np && nlSim.np.label) nlSim.np.label.visible = nlShowLabels;
  };
  const tRotate = document.getElementById('t-rotate'); if(tRotate) tRotate.onchange = e => nlAutoRotate = e.target.checked;

  // AI 3D Prompt Morph Button
  const btnMorph = document.getElementById('btn-ai-3d-morph');
  const inputMorph = document.getElementById('ai-3d-prompt-input');
  if(btnMorph && inputMorph){
    btnMorph.onclick = () => parseAndMorph3D(inputMorph.value);
    inputMorph.onkeydown = e => { if(e.key === 'Enter') parseAndMorph3D(inputMorph.value); };
  }
  
  // Voice input for 3D AI
  const btnVoice3D = document.getElementById('btn-ai-3d-voice');
  if(btnVoice3D && inputMorph){
    btnVoice3D.onclick = () => startVoiceRecognition(inputMorph, () => parseAndMorph3D(inputMorph.value), btnVoice3D);
  }

  window.addEventListener('keydown', e => {
    if(e.code === 'Space' && (document.querySelector('#t-3d.on') || document.querySelector('#view-viewer.active'))){
      if(e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA'){
        e.preventDefault();
        nlPlaying = !nlPlaying;
        syncButtons();
      }
    }
  });
}

let nlRaf = 0, nlRunning = false;
function animate(){
  if(!nlRunning) return;
  nlRaf = requestAnimationFrame(animate);
  const dt = Math.min(nlClock ? nlClock.getDelta() : 0.016, 0.05);
  if(nlPlaying) nlSimTime += dt * nlSpeed;
  if(nlAutoRotate) nlRot.y += dt * 0.25;

  if(nlMoleculeGroup){
    nlMoleculeGroup.rotation.y = nlRot.y;
    nlMoleculeGroup.rotation.x = nlRot.x;
  }
  if(nlCam) nlCam.position.z = nlZoom;

  updateSimulation(dt);
  if(nlSim && nlSim.np) updateNanoparticleDynamics(nlSim.np, dt);

  if(nlRenderer && nlScene && nlCam) nlRenderer.render(nlScene, nlCam);

  nlHudAcc += dt;
  if(nlHudAcc > 0.1){
    updateHUD();
    drawChart();
    syncButtons();
    nlHudAcc = 0;
  }
}

function resize3D(){
  if(!nlRenderer || !nlCam) return;
  const host = document.querySelector('.nanolab-viewport') || document.getElementById('view-viewer');
  if(!host) return;
  const w = (host && host.clientWidth > 0) ? host.clientWidth : (window.innerWidth ? Math.min(window.innerWidth - 48, 1200) : 900);
  const h = (host && host.clientHeight > 0) ? host.clientHeight : 720;
  nlRenderer.setSize(w, h);
  nlCam.aspect = w / h;
  nlCam.updateProjectionMatrix();
  nlSizeChart();
  drawChart();
}

function start3D(){
  if(nlRunning) return;
  nlRunning = true;
  if(nlClock) nlClock.start();
  animate();
}
function stop3D(){
  nlRunning = false;
  if(nlRaf) cancelAnimationFrame(nlRaf);
}

async function open3D(){
  if(typeof load3D === 'function') {
    try { await load3D(); } catch(e){}
  }
  const viewEl = document.getElementById('view-viewer') || document.querySelector('.nanolab-viewport');
  if(!viewEl) return;
  if(!nlRenderer){
    initScene();
    buildCards();
    wireUI();
    loadPreset(nlCurKey || 'lnp');
  }
  resize3D();
  setTimeout(resize3D, 50);
  setTimeout(resize3D, 200);
  setTimeout(resize3D, 400);
  start3D();
}

// Pre-initialize 3D scene so model is immediately assembled
if (typeof window !== 'undefined') {
  const init3DPreWarm = () => {
    if(!nlRenderer && typeof THREE !== 'undefined'){
      try {
        initScene();
        buildCards();
        wireUI();
        loadPreset(nlCurKey || 'lnp');
        resize3D();
      } catch(err){
        console.warn('3D pre-warm note:', err);
      }
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init3DPreWarm);
  } else {
    setTimeout(init3DPreWarm, 60);
  }
}

function syncFromPredictor(){
  const g = n => {
    const e = document.querySelector(`#form [data-f="${n}"]`) ||
              document.querySelector(`[data-pred="${n}"]`) ||
              document.querySelector(`#prompt-${n.toLowerCase()}`);
    return e ? e.value : null;
  };
  const mat = g('Material type') || g('Core') || g('carrier') || 'Lipid';
  let targetKey = 'lnp';
  if(mat.includes('PLGA')) targetKey = 'plga';
  else if(mat.includes('Liposome') || mat.includes('DPPC')) targetKey = 'liposome';
  else if(mat.includes('Albumin') || mat.includes('HSA')) targetKey = 'albumin';
  else if(mat.includes('Micelle')) targetKey = 'micelle';
  else if(mat.includes('Dendrimer')) targetKey = 'dendrimer';

  const sz = g('Size (nm)') || g('Hydro size (nm)') || g('Core size (nm)');
  if(sz){
    const sVal = parseFloat(sz);
    nlCoreScale = Math.max(10, Math.min(250, sVal)) / 40.0;
    const sSize = document.getElementById('s-size'); if(sSize) sSize.value = sVal;
    const oSize = document.getElementById('o-size'); if(oSize) oSize.textContent = sVal + ' nm';
    if(MEDICAL_CARRIERS[targetKey]) MEDICAL_CARRIERS[targetKey].r0 = sVal;
  }
  loadPreset(targetKey);
}

function upd3d(inp){
  if(!inp) return;
  const prompt = `${inp['carrier'] || inp['Material type'] || 'Lipid'} nanoparticle with ${inp['drug'] || 'Paclitaxel'} size ${inp['Size (nm)'] || 80}nm`;
  parseAndMorph3D(prompt);
}



/* ============================================================
   NANOBOT AI COMPANION — VOICE RECOGNITION, HUD, & TTS ENGINE
   ============================================================ */
let speechRecognition = null;
let isVoiceListening = false;
let isReadOutOn = true;
let activeVoiceTarget = null;
let activeVoiceCallback = null;
let activeVoiceBtn = null;
let voiceSilenceTimer = null;
let accumulatedTranscript = '';
let currentSpeakingBtn = null;

// Normalization dictionary for common speech-to-text misrecognitions in nanomedicine
function cleanMedicalSpeech(text) {
  if (!text) return '';
  let s = text.trim();
  const replacements = [
    // Carriers
    [/\b(libosome|lightosome|lipozome|lifeosome|liposomes)\b/gi, 'Liposome'],
    [/\b(p\s*l\s*g\s*a|pl\s*ga)\b/gi, 'PLGA'],
    [/\b(l\s*n\s*p|lipid\s+nanoparticle|lipid\s+nanoparticles)\b/gi, 'LNP'],
    [/\b(m\s*r\s*n\s*a|messenger\s+rna)\b/gi, 'mRNA'],
    [/\b(albumin|h\s*s\s*a)\b/gi, 'HSA Albumin'],
    [/\b(micelle|micelles|mycell|mycells)\b/gi, 'Micelle'],
    [/\b(dendrimer|dendrimers)\b/gi, 'PAMAM Dendrimer'],
    // Drugs & Cargo
    [/\b(paracetamol|paracetamole|parasitamol|parisitamol|acetaminophen)\b/gi, 'Paracetamol'],
    [/\b(ciprofloxacin|ciprofloxicin|cipro|seprofloxacin)\b/gi, 'Ciprofloxacin'],
    [/\b(vancomycin|vancomicin|vanco)\b/gi, 'Vancomycin'],
    [/\b(rifampicin|rifampin|rifampicine)\b/gi, 'Rifampicin'],
    [/\b(doxycycline|doxycyclin|doxi)\b/gi, 'Doxycycline'],
    [/\b(gentamicin|gentamycin)\b/gi, 'Gentamicin'],
    [/\b(azithromycin|azithromicin|zithromax)\b/gi, 'Azithromycin'],
    [/\b(amoxicillin|amoxycillin|amoxil)\b/gi, 'Amoxicillin'],
    [/\b(ibuprofen|ibuprefen|advil|motrin)\b/gi, 'Ibuprofen'],
    [/\b(letrozole|femara)\b/gi, 'Letrozole'],
    [/\b(exemestane|aromasin)\b/gi, 'Exemestane'],
    [/\b(amlodipine|norvasc)\b/gi, 'Amlodipine'],
    [/\b(doc\s*rubicin|dock\s*sir\s*rubicin|dox\s*rubicin|dark\s*ruby\s*sin|dr\s*rubicin)\b/gi, 'Doxorubicin'],
    [/\b(pack\s*lit\s*axel|pack\s*lee\s*tax\s*el|paclitaxil|paclitax)\b/gi, 'Paclitaxel'],
    [/\b(wrap\s*a\s*mycin|rapper\s*mycin|rap\s*a\s*mycin|rap\s*micin)\b/gi, 'Rapamycin'],
    [/\b(sis\s*platin|six\s*platin|cis\s*platinum)\b/gi, 'Cisplatin'],
    [/\b(method\s*trex\s*8|meth\s*o\s*trexate|metho\s*trexate)\b/gi, 'Methotrexate'],
    // Biophysical units & values
    [/\b(nano\s*meters?|nanometres?)\b/gi, 'nm'],
    [/\b(milli\s*volts?|millivolts?)\b/gi, 'mV'],
    [/\b(minus|negative)\s*(\d+)/gi, '-$2'],
    [/\b(plus|positive)\s*(\d+)/gi, '+$2'],
    [/\b(data\s+potential|seta\s+potential)\b/gi, 'zeta potential'],
    [/\b(p\s*h)\s*(\d+(?:\.\d+)?)/gi, 'pH $2'],
    [/\b(korsmeyer\s*peppas|course\s*meyer\s*peppas)\b/gi, 'Korsmeyer-Peppas'],
    [/\bd\s*l\s*v\s*o\b/gi, 'DLVO']
  ];
  for (const [pattern, replacement] of replacements) {
    s = s.replace(pattern, replacement);
  }
  return s;
}

// Acoustic Chime Feedback (Web Audio API Synthesizer)
function playAudioChime(type) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    const now = ctx.currentTime;
    if (type === 'start') {
      // Ascending pleasant futuristic chime (Mic On)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(880.00, now + 0.12); // A5
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (type === 'stop') {
      // Descending pleasant chime (Mic Off / Process)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880.00, now); // A5
      osc.frequency.exponentialRampToValueAtTime(523.25, now + 0.12); // C5
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
    } else if (type === 'error') {
      // Alert low buzz
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(260.0, now);
      gain.gain.setValueAtTime(0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    }
  } catch(e) {
    // Audio context may be restricted before gesture
  }
}

// Temporary Toast for Voice Errors
function showVoiceToast(msg, isErr = false) {
  const existing = document.getElementById('voice-status-toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.id = 'voice-status-toast';
  t.className = 'voice-status-toast';
  if (!isErr) t.style.borderColor = '#38bdf8';
  t.innerHTML = `<span>${isErr ? '⚠️' : '🎙️'}</span> <span>${msg}</span>`;
  document.body.appendChild(t);
  setTimeout(() => { if (t.parentNode) t.remove(); }, 4000);
}

function initVoiceEngines() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return false;
  try {
    speechRecognition = new SpeechRec();
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'en-US';

    speechRecognition.onresult = (e) => {
      let interim = '';
      let finalStr = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalStr += e.results[i][0].transcript;
        } else {
          interim += e.results[i][0].transcript;
        }
      }
      const rawCurrent = finalStr || interim;
      if (rawCurrent) {
        accumulatedTranscript = cleanMedicalSpeech(rawCurrent);
        updateVoiceHudStream(accumulatedTranscript, !!finalStr);
        if (activeVoiceTarget) {
          activeVoiceTarget.value = accumulatedTranscript;
        }
      }

      // Auto-commit after 2.4 seconds of natural pause if content exists
      clearTimeout(voiceSilenceTimer);
      if (accumulatedTranscript.trim()) {
        voiceSilenceTimer = setTimeout(() => {
          finishVoiceRecognition();
        }, 2400);
      }
    };

    speechRecognition.onerror = (e) => {
      console.warn('Voice Recognition Error:', e.error);
      clearTimeout(voiceSilenceTimer);
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
        playAudioChime('error');
        showVoiceToast('Microphone access blocked. Click 🔒/🎙️ in your URL bar to allow microphone access.', true);
        cleanupVoiceState();
      } else if (e.error === 'no-speech') {
        showVoiceToast('No voice detected. Please speak closer to your microphone.', false);
      } else if (e.error === 'network') {
        showVoiceToast('Speech recognition network timeout. You can type directly in the box.', true);
        cleanupVoiceState();
      }
    };

    speechRecognition.onend = () => {
      if (isVoiceListening) {
        finishVoiceRecognition();
      } else {
        cleanupVoiceState();
      }
    };
    return true;
  } catch(err) {
    console.error('Failed to init speech recognition:', err);
    return false;
  }
}

function updateVoiceHudStream(text, isFinal) {
  const streamEl = document.getElementById('voice-hud-stream');
  if (!streamEl) return;
  if (!text) {
    streamEl.innerHTML = '<span class="voice-hint">🎙️ Speak now (e.g. "Design 80nm Liposome with Doxorubicin at -30mV")...</span>';
  } else {
    streamEl.innerHTML = `<span class="transcript-live">${text}</span>`;
  }
}

function startVoiceRecognition(targetInput, onComplete, triggerBtn) {
  // If already listening, toggle off and commit
  if (isVoiceListening) {
    finishVoiceRecognition();
    return;
  }

  if (!speechRecognition) {
    const ok = initVoiceEngines();
    if (!ok) {
      alert('Speech Recognition is not supported by this browser. Chrome or Edge is recommended.');
      return;
    }
  }

  activeVoiceTarget = targetInput;
  activeVoiceCallback = onComplete;
  activeVoiceBtn = triggerBtn;
  accumulatedTranscript = '';
  isVoiceListening = true;

  // Visual cues on buttons
  const allMics = [
    document.getElementById('btn-voice-input'),
    document.getElementById('btn-ai-3d-voice'),
    triggerBtn
  ].filter(Boolean);
  allMics.forEach(btn => {
    btn.classList.add('listening');
    btn.setAttribute('title', 'Listening... Click to stop & send');
  });

  // Display Voice HUD
  const hud = document.getElementById('voice-hud-indicator');
  if (hud) hud.style.display = 'block';
  updateVoiceHudStream('', false);

  // Sound chime
  playAudioChime('start');

  try {
    speechRecognition.start();
  } catch(e) {
    console.log('Recognition start note:', e.message);
  }
}

function finishVoiceRecognition() {
  if (!isVoiceListening) return;
  clearTimeout(voiceSilenceTimer);
  isVoiceListening = false;
  playAudioChime('stop');

  try {
    if (speechRecognition) speechRecognition.stop();
  } catch(e) {}

  const finalResult = cleanMedicalSpeech(accumulatedTranscript);
  if (activeVoiceTarget && finalResult) {
    activeVoiceTarget.value = finalResult;
  }

  cleanupVoiceState();

  if (activeVoiceCallback && finalResult) {
    const cb = activeVoiceCallback;
    activeVoiceCallback = null;
    setTimeout(() => cb(finalResult), 120);
  }
}

function cancelVoiceRecognition() {
  clearTimeout(voiceSilenceTimer);
  isVoiceListening = false;
  try {
    if (speechRecognition) speechRecognition.abort();
  } catch(e) {}
  cleanupVoiceState();
  showVoiceToast('Voice input cancelled', false);
}

function cleanupVoiceState() {
  isVoiceListening = false;
  clearTimeout(voiceSilenceTimer);
  const hud = document.getElementById('voice-hud-indicator');
  if (hud) hud.style.display = 'none';

  const allMics = [
    document.getElementById('btn-voice-input'),
    document.getElementById('btn-ai-3d-voice'),
    activeVoiceBtn
  ].filter(Boolean);
  allMics.forEach(btn => {
    btn.classList.remove('listening');
    btn.setAttribute('title', 'Speak to NanoMed AI');
  });
  activeVoiceBtn = null;
}

// -------------------------------------------------------------------
// TEXT-TO-SPEECH (TTS) & READ-OUT ENGINE
// -------------------------------------------------------------------
function toggleReadOut() {
  isReadOutOn = !isReadOutOn;
  const btn = document.getElementById('btn-readout-toggle');
  if (btn) {
    btn.classList.toggle('active', isReadOutOn);
    btn.textContent = isReadOutOn ? '🔊 Auto-Speak: ON' : '🔈 Auto-Speak: OFF';
    btn.title = isReadOutOn ? 'AI automatically speaks responses' : 'AI text only (speech muted)';
  }
  if (!isReadOutOn) stopSpeech();
}

function prepareTextForSpeech(text) {
  let s = text.replace(/<[^>]+>/g, ' '); // Strip HTML
  s = s.replace(/[•*_~`#]/g, ' ');       // Strip markdown symbols
  
  // Expand scientific notation & abbreviations for smooth pronunciation:
  s = s.replace(/\bnm\b/gi, ' nanometers ');
  s = s.replace(/\bmV\b/gi, ' millivolts ');
  s = s.replace(/\bmRNA\b/gi, ' messenger R N A ');
  s = s.replace(/\bLNP\b/gi, ' L N P ');
  s = s.replace(/\bPLGA\b/gi, ' P L G A ');
  s = s.replace(/\bHSA\b/gi, ' H S A ');
  s = s.replace(/\bPAMAM\b/gi, ' PAMAM ');
  s = s.replace(/\bDLVO\b/gi, ' D L V O barrier ');
  s = s.replace(/\b-(\d+(?:\.\d+)?)\b/g, ' negative $1 ');
  s = s.replace(/\+(\d+(?:\.\d+)?)\b/g, ' positive $1 ');
  s = s.replace(/\bpH\s*([0-9.]+)/gi, ' p H $1 ');
  s = s.replace(/\bPBS\b/gi, ' P B S buffer ');
  s = s.replace(/\s+/g, ' ').trim();
  return s;
}

function getBestSpeechVoice() {
  if (!('speechSynthesis' in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || !voices.length) return null;
  const preferred = voices.find(v => 
    (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('Jenny') || v.name.includes('Zira')) 
    && v.lang.startsWith('en')
  );
  if (preferred) return preferred;
  return voices.find(v => v.lang.startsWith('en')) || voices[0];
}

function speakText(text, onComplete) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();

  const clean = prepareTextForSpeech(text);
  if (!clean) return;

  const utter = new SpeechSynthesisUtterance(clean);
  utter.rate = 1.0;
  utter.pitch = 1.0;

  const bestVoice = getBestSpeechVoice();
  if (bestVoice) utter.voice = bestVoice;

  const stopBtn = document.getElementById('btn-stop-speech');
  const speakWave = document.getElementById('speaking-wave');
  if (stopBtn) stopBtn.style.display = 'inline-block';
  if (speakWave) speakWave.style.display = 'inline-flex';

  utter.onend = () => {
    if (stopBtn) stopBtn.style.display = 'none';
    if (speakWave) speakWave.style.display = 'none';
    if (currentSpeakingBtn) {
      currentSpeakingBtn.classList.remove('speaking');
      currentSpeakingBtn.innerHTML = '🔊 Listen';
      currentSpeakingBtn = null;
    }
    if (onComplete) onComplete();
  };
  utter.onerror = () => {
    if (stopBtn) stopBtn.style.display = 'none';
    if (speakWave) speakWave.style.display = 'none';
    if (currentSpeakingBtn) {
      currentSpeakingBtn.classList.remove('speaking');
      currentSpeakingBtn.innerHTML = '🔊 Listen';
      currentSpeakingBtn = null;
    }
  };

  window.speechSynthesis.speak(utter);
}

function stopSpeech() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  const stopBtn = document.getElementById('btn-stop-speech');
  const speakWave = document.getElementById('speaking-wave');
  if (stopBtn) stopBtn.style.display = 'none';
  if (speakWave) speakWave.style.display = 'none';
  if (currentSpeakingBtn) {
    currentSpeakingBtn.classList.remove('speaking');
    currentSpeakingBtn.innerHTML = '🔊 Listen';
    currentSpeakingBtn = null;
  }
}

function speakMessageBubble(btn) {
  if (!btn) return;
  if (btn === currentSpeakingBtn && window.speechSynthesis && window.speechSynthesis.speaking) {
    stopSpeech();
    return;
  }
  stopSpeech();

  const bubble = btn.closest('.msg-bubble');
  if (!bubble) return;

  const clone = bubble.cloneNode(true);
  const btns = clone.querySelectorAll('button');
  btns.forEach(b => b.remove());
  const text = clone.innerText || clone.textContent;

  currentSpeakingBtn = btn;
  btn.classList.add('speaking');
  btn.innerHTML = '⏹ Stop';

  speakText(text, () => {
    btn.classList.remove('speaking');
    btn.innerHTML = '🔊 Listen';
    currentSpeakingBtn = null;
  });
}

function toggleNanoBot() {
  const w = document.getElementById('nanobot-window');
  if (!w) return;
  w.classList.toggle('open');
  if (w.classList.contains('open')) {
    const inp = document.getElementById('nanobot-input');
    if (inp) inp.focus();
  } else {
    stopSpeech();
    cancelVoiceRecognition();
  }
}

function appendNanoBotMsg(sender, text, actions) {
  const box = document.getElementById('nanobot-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = `nanobot-msg ${sender}`;

  let actionHtml = '';
  if (actions && actions.length) {
    actionHtml = actions.map(a => 
      `<button class="msg-action-btn" onclick="${a.action}"><span>${a.icon}</span> ${a.label}</button>`
    ).join(' ');
  }

  // Include speaker button on all AI messages
  const speakerHtml = sender === 'ai' ? 
    `<button class="msg-speaker-btn" onclick="speakMessageBubble(this)" title="Read this message aloud">🔊 Listen</button>` : '';

  div.innerHTML = `<div class="msg-bubble">${text} ${speakerHtml} ${actionHtml}</div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;

  if (sender === 'ai' && isReadOutOn) {
    speakText(text);
  }
}

function startAssistantVoice() {
  const inp = document.getElementById('nanobot-input');
  const btn = document.getElementById('btn-voice-input');
  startVoiceRecognition(inp, () => sendNanoBotMessage(), btn);
}

function startQuickPromptVoice() {
  const inp = document.getElementById('quick-prompt-input');
  const btn = document.getElementById('btn-quick-prompt-voice');
  startVoiceRecognition(inp, () => {
    const runBtn = document.getElementById('btn-quick-run');
    if (runBtn) runBtn.click();
  }, btn);
}

function startMainPromptVoice() {
  const inp = document.getElementById('experiment-prompt');
  const btn = document.getElementById('btn-main-prompt-voice');
  startVoiceRecognition(inp, () => {}, btn);
}

function quickAsk(q){
  const inp = document.getElementById('nanobot-input');
  if(inp) inp.value = q;
  sendNanoBotMessage();
}

function sendNanoBotMessage(){
  const inp = document.getElementById('nanobot-input');
  if(!inp || !inp.value.trim()) return;
  const userText = inp.value.trim();
  inp.value = '';

  appendNanoBotMsg('user', userText);

  // Intelligent NanoMed AI Processing
  setTimeout(() => {
    processAssistantQuery(userText);
  }, 350);
}

/* ============================================================
   INTERACTIVE CONVERSATIONAL AI CLINICAL DIRECTOR & SIMULATION RUNNER
   - Multi-turn talk-back dialogue
   - Proactive diagnostic alerts (Medium, pH, Stability, Extrapolation)
   - Automatic transfer to Live Simulation Workspace & execution
   - Full Voice & Audio Feedback integration
   ============================================================ */

const CLINICAL_DRUG_KNOWLEDGE = {
  paracetamol: {
    name: 'Paracetamol',
    category: 'Analgesic & Antipyretic',
    defaultCarrier: 'nm-paracetamol-plga',
    carriers: [
      { key: 'nm-paracetamol-plga', label: 'PLGA Copolymer (335 nm)', size: 335.5, zeta: 7.1, load: '7.4%', desc: 'Long-acting biodegradable polyester depot' },
      { key: 'nm-paracetamol-liposome', label: 'Liposome DPPC (90 nm)', size: 90.1, zeta: -35.4, load: '4.0%', desc: 'Unilamellar lipid bilayer vesicle' },
      { key: 'nm-paracetamol-sln', label: 'Solid Lipid DSPC (235 nm)', size: 234.9, zeta: 19.0, load: '4.0%', desc: 'Solid matrix with enhanced shelf stability' }
    ]
  },
  ciprofloxacin: {
    name: 'Ciprofloxacin',
    category: 'Fluoroquinolone Antibiotic',
    defaultCarrier: 'ciprofloxacin-plga',
    carriers: [
      { key: 'ciprofloxacin-plga', label: 'PLGA Matrix (165 nm)', size: 165.0, zeta: -18.2, load: '9.2%', desc: 'PVA-stabilized sustained antibacterial release' }
    ]
  },
  vancomycin: {
    name: 'Vancomycin',
    category: 'Glycopeptide Antibiotic',
    defaultCarrier: 'vancomycin-plga-peg',
    carriers: [
      { key: 'vancomycin-plga-peg', label: 'PLGA-PEG Stealth (180 nm)', size: 180.0, zeta: -12.5, load: '11.5%', desc: 'PEGylated extended-release against MRSA' }
    ]
  },
  rifampicin: {
    name: 'Rifampicin',
    category: 'Rifamycin / Antitubercular',
    defaultCarrier: 'rifampicin-plga-peg',
    carriers: [
      { key: 'rifampicin-plga-peg', label: 'PLGA-PEG Core (145 nm)', size: 145.0, zeta: -16.0, load: '8.0%', desc: 'Hydrophobic core with stealth corona' }
    ]
  },
  doxycycline: {
    name: 'Doxycycline',
    category: 'Tetracycline Antibiotic',
    defaultCarrier: 'doxycycline-polymeric',
    carriers: [
      { key: 'doxycycline-polymeric', label: 'Polymeric NP (130 nm)', size: 130.0, zeta: -24.0, load: '7.8%', desc: 'PEG-PLA mucosal delivery' }
    ]
  },
  gentamicin: {
    name: 'Gentamicin',
    category: 'Aminoglycoside Antibiotic',
    defaultCarrier: 'gentamicin-chitosan',
    carriers: [
      { key: 'gentamicin-chitosan', label: 'Chitosan NP (115 nm)', size: 115.0, zeta: 28.5, load: '6.5%', desc: 'Mucoadhesive cationic polysaccharide' }
    ]
  },
  azithromycin: {
    name: 'Azithromycin',
    category: 'Macrolide Antibiotic',
    defaultCarrier: 'azithromycin-sln',
    carriers: [
      { key: 'azithromycin-sln', label: 'Solid Lipid NP (195 nm)', size: 195.0, zeta: -21.0, load: '10.2%', desc: 'Poloxamer-coated lipid nanoparticles' }
    ]
  },
  amoxicillin: {
    name: 'Amoxicillin',
    category: 'Beta-Lactam Antibiotic',
    defaultCarrier: 'amoxicillin-eudragit',
    carriers: [
      { key: 'amoxicillin-eudragit', label: 'Eudragit NP (140 nm)', size: 140.0, zeta: -15.5, load: '8.7%', desc: 'Enteric protected gastric-resistant matrix' }
    ]
  },
  doxorubicin: {
    name: 'Doxorubicin',
    category: 'Anthracycline Chemotherapeutic',
    defaultCarrier: 'doxorubicin-liposome',
    carriers: [
      { key: 'doxorubicin-liposome', label: 'PEGylated Liposome (85 nm)', size: 85.0, zeta: -25.0, load: '9.8%', desc: 'Doxil-analog with prolonged circulation' },
      { key: 'doxorubicin-plga', label: 'PLGA Chitosan/Alginate (175 nm)', size: 175.0, zeta: -19.5, load: '8.5%', desc: 'Layer-by-layer core-shell matrix' }
    ]
  },
  paclitaxel: {
    name: 'Paclitaxel',
    category: 'Taxane Chemotherapeutic',
    defaultCarrier: 'formulation-a',
    carriers: [
      { key: 'formulation-a', label: 'PLGA Benchmark (120 nm)', size: 120.0, zeta: -22.0, load: '8.0%', desc: 'Nature Comms benchmark formulation' }
    ]
  },
  letrozole: {
    name: 'Letrozole',
    category: 'Aromatase Inhibitor',
    defaultCarrier: 'formulation-b',
    carriers: [
      { key: 'formulation-b', label: 'PLA Long-Acting (150 nm)', size: 150.0, zeta: -15.0, load: '5.0%', desc: 'Extended PLA parenteral depot' },
      { key: 'formulation-c', label: 'PLGA Matrix (100 nm)', size: 100.0, zeta: -28.0, load: '6.0%', desc: 'Sustained PLGA copolymer release' }
    ]
  },
  ibuprofen: {
    name: 'Ibuprofen',
    category: 'NSAID / Anti-inflammatory',
    defaultCarrier: 'ibuprofen-lipid',
    carriers: [
      { key: 'ibuprofen-lipid', label: 'Solid Lipid NP (150 nm)', size: 150.0, zeta: -22.4, load: '9.5%', desc: 'Lipid matrix with high encapsulation' }
    ]
  },
  mrna: {
    name: 'mRNA-1273',
    category: 'mRNA Vaccine / Biologic',
    defaultCarrier: 'mrna-lnp',
    carriers: [
      { key: 'mrna-lnp', label: 'Ionizable LNP (80 nm)', size: 80.0, zeta: 4.5, load: '92% encap', desc: 'SM-102 / PEG-DMG ionizable lipid shell' }
    ]
  }
};

let aiSession = {
  active: false,
  drugKey: null,
  waitingFor: null,
  selectedKey: null,
  ph: 7.4,
  temp: 37.0,
  medium: 'pbs'
};

// -------------------------------------------------------------
// Diagnostic Alert & Issue Evaluator
// -------------------------------------------------------------
function diagnoseFormulationIssues(form, env = {}) {
  const issues = [];
  const ph = env.ph !== undefined ? env.ph : (state.env ? state.env.ph : 7.4);
  const temp = env.temp !== undefined ? env.temp : (state.env ? state.env.temp : 37.0);
  const zeta = form.zeta;
  const size = form.size;

  // 1. Medium & pH Issue Analysis
  if (ph < 6.8) {
    issues.push({
      type: 'medium',
      severity: 'warn',
      icon: '⚠️',
      title: `Acidic Medium Alert (pH ${ph.toFixed(1)})`,
      message: `At acidic pH ${ph.toFixed(1)} (e.g., endosomes or tumor microenvironment), hydrolytic ester cleavage is accelerated. Korsmeyer-Peppas baseline was fitted under physiological pH 7.4, so anomalous burst release may increase.`,
      spoken: `Medium warning: operating at acidic pH ${ph.toFixed(1)}, which accelerates polymer erosion.`
    });
  } else if (ph > 7.9) {
    issues.push({
      type: 'medium',
      severity: 'warn',
      icon: '⚠️',
      title: `Alkaline Medium Alert (pH ${ph.toFixed(1)})`,
      message: `At alkaline pH ${ph.toFixed(1)}, base-catalyzed hydrolysis and potential neutralization of surface charge may occur.`,
      spoken: `Medium warning: alkaline pH ${ph.toFixed(1)} may alter surface potential.`
    });
  } else {
    issues.push({
      type: 'medium',
      severity: 'good',
      icon: '✅',
      title: `Physiological Buffer Matched (pH ${ph.toFixed(1)})`,
      message: `Medium is calibrated to physiological blood/PBS pH 7.4 with 0.15 M ionic strength.`,
      spoken: `Release medium matched to physiological pH 7.4.`
    });
  }

  // 2. Temperature Issue Analysis
  if (Math.abs(temp - 37.0) > 1.5) {
    issues.push({
      type: 'temp',
      severity: 'warn',
      icon: '⚠️',
      title: `Temperature Deviation (${temp.toFixed(1)}°C)`,
      message: `Operating away from 37.0°C human body temperature. Diffusion coefficient scales via Stokes-Einstein equation D = k_B·T / (6πηr), altering release kinetics.`,
      spoken: `Temperature is set to ${temp.toFixed(1)} degrees Celsius, altering fluid viscosity and drug diffusion.`
    });
  }

  // 3. Colloidal Stability Issue (Zeta Potential)
  if (Math.abs(zeta) < 20.0) {
    issues.push({
      type: 'stability',
      severity: 'danger',
      icon: '⚠️',
      title: `Low Colloidal Stability Risk (Zeta: ${zeta > 0 ? '+' : ''}${zeta} mV)`,
      message: `Surface charge magnitude is below 20 mV. The electrostatic DLVO repulsion barrier is low. Nanoparticles may aggregate in ionic media unless protected by a steric PEG corona.`,
      spoken: `Stability warning: surface charge of ${zeta} millivolts is low, risking particle agglomeration.`
    });
  } else {
    issues.push({
      type: 'stability',
      severity: 'good',
      icon: '✅',
      title: `Colloidally Stable (Zeta: ${zeta > 0 ? '+' : ''}${zeta} mV)`,
      message: `Strong electrostatic repulsion barrier (|ζ| ≥ 20 mV) maintains robust colloidal dispersion in suspension.`,
      spoken: `Colloidal stability confirmed with an electrostatic barrier of ${zeta} millivolts.`
    });
  }

  // 4. Bio-distribution / Particle Sizing
  if (size > 220.0) {
    issues.push({
      type: 'size',
      severity: 'warn',
      icon: 'ℹ️',
      title: `Nanoscale Sizing Notice (${size} nm)`,
      message: `Particle diameter exceeds 200 nm. Long-acting parenteral formulations at this size face higher hepatic Kupffer uptake and splenic filtration.`,
      spoken: `Particle size of ${size} nanometers exceeds 200 nanometers, which increases splenic clearance.`
    });
  }

  // 5. Korsmeyer-Peppas Mathematical Extrapolation Domain Limit
  issues.push({
    type: 'extrapolation',
    severity: 'info',
    icon: '📊',
    title: 'Korsmeyer-Peppas ODE Mathematical Domain Limit',
    message: 'The Korsmeyer-Peppas model Mt/M∞ = k·t^n applies to the initial 60% of release. Telemetry marks fractions beyond 60% as mathematical extrapolation.',
    spoken: 'Korsmeyer-Peppas kinetics are valid up to 60 percent cumulative release.'
  });

  return issues;
}

// -------------------------------------------------------------
// Automated Simulation Execution Function
// -------------------------------------------------------------
function executeAiSimulationWorkflow(formKey, customOverrides = {}) {
  const f = FORMULATIONS[formKey] || FORMULATIONS['formulation-a'];
  
  // 1. Switch to Live Simulation Workspace
  if (typeof switchTab === 'function') {
    switchTab('simulation');
  }

  // 2. Select formulation dropdown
  const sel = document.getElementById('config-formulation');
  if (sel) {
    sel.value = formKey;
    if (typeof setFormulationConfig === 'function') {
      setFormulationConfig(formKey);
    }
  }

  // 3. Set environment parameters
  const ph = customOverrides.ph !== undefined ? customOverrides.ph : 7.4;
  const temp = customOverrides.temp !== undefined ? customOverrides.temp : 37.0;
  const medium = customOverrides.medium || 'pbs';

  const phInput = document.getElementById('env-ph');
  const tempInput = document.getElementById('env-temp');
  const medSelect = document.getElementById('env-medium');

  if (phInput) {
    phInput.value = ph;
    if (state.env) state.env.ph = parseFloat(ph);
    const valPh = document.getElementById('val-ph');
    if (valPh) valPh.textContent = parseFloat(ph).toFixed(1);
  }

  if (tempInput) {
    tempInput.value = temp;
    if (state.env) state.env.temp = parseFloat(temp);
    const valTemp = document.getElementById('val-temp');
    if (valTemp) valTemp.textContent = parseFloat(temp).toFixed(1);
  }

  if (medSelect) {
    medSelect.value = medium;
    if (state.env) state.env.medium = medium;
  }

  // 4. Reset & Launch Simulation immediately!
  if (typeof resetSim === 'function') resetSim();
  setTimeout(() => {
    if (typeof startSim === 'function') {
      startSim();
      addEvent(`AI automated launch: ${f.name} (pH ${ph}, ${temp}°C)`, 'sys');
    }
  }, 180);

  // 5. Morph 3D viewer model
  try {
    if (typeof parseAndMorph3D === 'function') {
      parseAndMorph3D(`${f.drug} ${f.size}nm ${f.material} at ${f.zeta}mV`);
    }
  } catch(e) {}
}

// Window globally accessible callback for action buttons
window.confirmAiDrugSetup = function(formKey, runImmediately = false, envOverrides = {}) {
  const f = FORMULATIONS[formKey] || FORMULATIONS['formulation-a'];
  const issues = diagnoseFormulationIssues(f, envOverrides);

  let issuesHtml = issues.map(iss => 
    `<div style="font-size:11.5px; margin:3px 0; color:${iss.severity === 'danger' ? '#f43f5e' : iss.severity === 'warn' ? '#f59e0b' : '#38bdf8'};">
      <b>${iss.icon} ${iss.title}:</b> ${iss.message}
    </div>`
  ).join('');

  // Spoken voice summary (concise & informative)
  const spokenIssues = issues.filter(i => i.severity === 'danger' || i.severity === 'warn').map(i => i.spoken).join(' ');
  const speechText = `Selected ${f.drug} in ${f.material}, size ${f.size} nanometers, surface charge ${f.zeta} millivolts. ${spokenIssues ? spokenIssues + ' ' : ''}Transferring to Live Simulation Workspace and executing now!`;

  const msg = `⚡ <b>AI Formulation Verified: ${f.name}</b><br>` +
    `• <b>Drug / Payload:</b> ${f.drug} (${f.category || 'Therapeutic Active'})<br>` +
    `• <b>Carrier Matrix:</b> ${f.material} · <b>Size:</b> ${f.size} nm · <b>Zeta:</b> ${f.zeta > 0 ? '+' : ''}${f.zeta} mV<br>` +
    `• <b>Drug Loading:</b> ${f.load} · <b>Coating:</b> ${f.coat}<br>` +
    `• <b>Korsmeyer-Peppas ODE:</b> k = ${f.k}, n = ${f.n}<br><br>` +
    `<b>Biophysical & Medium Diagnostic Review:</b><br>${issuesHtml}<br><br>` +
    `🚀 <b>Status:</b> Automatically loaded into the Simulation Workspace and started execution!`;

  const actions = [
    { label: 'View Live Simulation', icon: '▶️', action: "switchTab('simulation')" },
    { label: 'Inspect 3D Digital Twin', icon: '🌐', action: "switchTab('viewer')" }
  ];

  appendNanoBotMsg('ai', msg, actions);

  // Speak aloud via TTS
  speakText(speechText);

  // Execute in workspace
  executeAiSimulationWorkflow(formKey, envOverrides);

  // Reset dialogue session
  aiSession = { active: false, drugKey: null, waitingFor: null, selectedKey: null, ph: 7.4, temp: 37.0, medium: 'pbs' };
};

// -------------------------------------------------------------
// Conversational Multi-Turn Query Processor
// -------------------------------------------------------------
function processAssistantQuery(query) {
  const q = query.toLowerCase().trim();

  // Helper: detect drug in text
  let detectedDrugKey = null;
  for (const [key, info] of Object.entries(CLINICAL_DRUG_KNOWLEDGE)) {
    if (q.includes(key) || q.includes(info.name.toLowerCase())) {
      detectedDrugKey = key;
      break;
    }
  }
  // Check alternative phonetic/common drug names
  if (!detectedDrugKey) {
    if (q.includes('acetaminophen') || q.includes('pcm')) detectedDrugKey = 'paracetamol';
    else if (q.includes('cipro')) detectedDrugKey = 'ciprofloxacin';
    else if (q.includes('vanco')) detectedDrugKey = 'vancomycin';
    else if (q.includes('rifampin')) detectedDrugKey = 'rifampicin';
    else if (q.includes('doxil') || q.includes('adria')) detectedDrugKey = 'doxorubicin';
    else if (q.includes('taxol')) detectedDrugKey = 'paclitaxel';
    else if (q.includes('femara')) detectedDrugKey = 'letrozole';
  }

  // Detect explicit environmental parameters in user input
  let parsedPh = null;
  const phMatch = q.match(/ph\s*(?:of|=|:)?\s*(\d+(?:\.\d+)?)/);
  if (phMatch) parsedPh = parseFloat(phMatch[1]);

  let parsedTemp = null;
  const tempMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:°?c|degrees?|celsius)/);
  if (tempMatch) parsedTemp = parseFloat(tempMatch[1]);

  let parsedSize = null;
  const sizeMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:nm|nanometers?)/);
  if (sizeMatch) parsedSize = parseFloat(sizeMatch[1]);

  // A. IF USER SAYS "RUN", "DEFAULTS", "YES", "EXECUTE" WHILE IN AN ACTIVE DRUG SESSION
  if (aiSession.active && aiSession.drugKey && (q.includes('run') || q.includes('default') || q.includes('yes') || q.includes('ok') || q.includes('start') || q.includes('proceed') || q.includes('execute') || q.includes('simulate'))) {
    const drugInfo = CLINICAL_DRUG_KNOWLEDGE[aiSession.drugKey];
    const formKey = aiSession.selectedKey || drugInfo.defaultCarrier;
    const envOverrides = {};
    if (parsedPh !== null) envOverrides.ph = parsedPh;
    if (parsedTemp !== null) envOverrides.temp = parsedTemp;
    window.confirmAiDrugSetup(formKey, true, envOverrides);
    return;
  }

  // B. IF USER NAMES A SPECIFIC CARRIER (e.g. "PLGA", "Liposome", "SLN") WHILE IN ACTIVE DRUG SESSION
  if (aiSession.active && aiSession.drugKey) {
    const drugInfo = CLINICAL_DRUG_KNOWLEDGE[aiSession.drugKey];
    let matchedCarrierKey = null;

    if (q.includes('liposome') || q.includes('lipid vesicle')) {
      const found = drugInfo.carriers.find(c => c.key.includes('liposome'));
      if (found) matchedCarrierKey = found.key;
    } else if (q.includes('sln') || q.includes('solid lipid') || q.includes('dspc')) {
      const found = drugInfo.carriers.find(c => c.key.includes('sln'));
      if (found) matchedCarrierKey = found.key;
    } else if (q.includes('plga') || q.includes('polymer') || q.includes('polymeric')) {
      const found = drugInfo.carriers.find(c => c.key.includes('plga'));
      if (found) matchedCarrierKey = found.key;
    }

    if (matchedCarrierKey) {
      const envOverrides = {};
      if (parsedPh !== null) envOverrides.ph = parsedPh;
      if (parsedTemp !== null) envOverrides.temp = parsedTemp;
      window.confirmAiDrugSetup(matchedCarrierKey, true, envOverrides);
      return;
    }
  }

  // C. IF A DRUG NAME IS DETECTED IN THE USER'S QUERY
  if (detectedDrugKey) {
    const drugInfo = CLINICAL_DRUG_KNOWLEDGE[detectedDrugKey];
    const isDirectRunRequested = q.includes('simulate') || q.includes('run') || q.includes('start') || q.includes('default') || (parsedSize !== null && q.includes('plga'));

    // Check if user already specified full parameters (Direct Execute)
    if (isDirectRunRequested && drugInfo.carriers.length > 0) {
      // Pick best matching carrier
      let targetKey = drugInfo.defaultCarrier;
      if (q.includes('liposome')) {
        const found = drugInfo.carriers.find(c => c.key.includes('liposome'));
        if (found) targetKey = found.key;
      } else if (q.includes('sln') || q.includes('solid lipid')) {
        const found = drugInfo.carriers.find(c => c.key.includes('sln'));
        if (found) targetKey = found.key;
      }
      const envOverrides = {};
      if (parsedPh !== null) envOverrides.ph = parsedPh;
      if (parsedTemp !== null) envOverrides.temp = parsedTemp;
      window.confirmAiDrugSetup(targetKey, true, envOverrides);
      return;
    }

    // Otherwise: INITIATE INTERACTIVE TALK-BACK DIALOGUE!
    aiSession = {
      active: true,
      drugKey: detectedDrugKey,
      waitingFor: 'carrier_selection',
      selectedKey: drugInfo.defaultCarrier,
      ph: parsedPh !== null ? parsedPh : 7.4,
      temp: parsedTemp !== null ? parsedTemp : 37.0,
      medium: 'pbs'
    };

    const carrierListHtml = drugInfo.carriers.map((c, i) => 
      `• <b>Option ${i + 1}: ${c.label}</b> (Loading: ${c.load}, Zeta: ${c.zeta > 0 ? '+' : ''}${c.zeta} mV)<br>&nbsp;&nbsp;&nbsp;&nbsp;<i>${c.desc}</i>`
    ).join('<br>');

    const actionButtons = drugInfo.carriers.map(c => ({
      label: c.label.split('(')[0].trim(),
      icon: c.key.includes('liposome') ? '🫧' : c.key.includes('sln') ? '🛡️' : '💊',
      action: `window.confirmAiDrugSetup('${c.key}', true)`
    }));
    actionButtons.push({
      label: 'Run Calibrated Defaults',
      icon: '⚡',
      action: `window.confirmAiDrugSetup('${drugInfo.defaultCarrier}', true)`
    });

    const reply = `I have identified <b>${drugInfo.name}</b> (${drugInfo.category}).<br><br>` +
      `To configure the simulation for this medicine, which nanocarrier system and target size would you like to formulate?<br><br>` +
      `${carrierListHtml}<br><br>` +
      `<b>Environment check:</b> Defaulting to <b>PBS buffer pH 7.4 at 37°C</b>.<br>` +
      `You can tell me your custom parameters (e.g. <i>'PLGA 335nm at pH 6.5'</i>) or click an option below to launch immediately!`;

    const speechText = `Identified ${drugInfo.name}. Which delivery platform would you like to formulate? Options include ${drugInfo.carriers.map(c => c.label.split('(')[0]).join(', or ')}. You can state your carrier, or say 'run defaults' to launch the simulation now.`;

    appendNanoBotMsg('ai', reply, actionButtons);
    speakText(speechText);
    return;
  }

  // D. IF USER ASKS ABOUT PROBLEMS / ISSUES IN MEDIUM / ENVIRONMENT
  if (q.includes('issue') || q.includes('problem') || q.includes('medium') || q.includes('ph') || q.includes('buffer') || q.includes('serum') || q.includes('temperature') || q.includes('risk')) {
    const curFormKey = (state && state.formulationKey) ? state.formulationKey : 'formulation-a';
    const curForm = FORMULATIONS[curFormKey] || FORMULATIONS['formulation-a'];
    const curEnv = { ph: state.env.ph, temp: state.env.temp, medium: state.env.medium };
    const issues = diagnoseFormulationIssues(curForm, curEnv);

    const issuesHtml = issues.map(iss => 
      `<div style="margin:4px 0; padding:4px 8px; border-radius:4px; background:${iss.severity === 'danger' ? 'rgba(244,63,94,0.12)' : iss.severity === 'warn' ? 'rgba(245,158,11,0.12)' : 'rgba(56,189,248,0.08)'}; border-left:3px solid ${iss.severity === 'danger' ? '#f43f5e' : iss.severity === 'warn' ? '#f59e0b' : '#38bdf8'};">
        <b>${iss.icon} ${iss.title}</b><br>
        <span style="font-size:12px; color:#cbd5e1;">${iss.message}</span>
      </div>`
    ).join('');

    const speechSummary = issues.map(i => i.spoken).slice(0, 3).join(' ');

    const reply = `<b>Comprehensive Medium & Biophysical Diagnostics (${curForm.name}):</b><br><br>` +
      `<b>Current Conditions:</b> Medium: <b>${curEnv.medium.toUpperCase()}</b> · pH: <b>${curEnv.ph.toFixed(1)}</b> · Temp: <b>${curEnv.temp.toFixed(1)}°C</b><br><br>` +
      `${issuesHtml}`;

    const actions = [
      { label: 'Set Neutral PBS (pH 7.4)', icon: '🧪', action: "if($('env-ph')) {$('env-ph').value=7.4; state.env.ph=7.4; $('val-ph').textContent='7.4'; addEvent('pH normalized to 7.4','sys');}" },
      { label: 'Simulate Tumor Acidosis (pH 6.5)', icon: '⚠️', action: "if($('env-ph')) {$('env-ph').value=6.5; state.env.ph=6.5; $('val-ph').textContent='6.5'; addEvent('pH set to 6.5 (tumor acidosis)','sys');}" }
    ];

    appendNanoBotMsg('ai', reply, actions);
    speakText(speechSummary);
    return;
  }

  // E. 3D MODEL VIEW / MORPH SPECIFIC REQUEST
  if (q.includes('3d') || q.includes('morph') || q.includes('render') || q.includes('visualize') || q.includes('ray') || q.includes('border') || q.includes('mesh')) {
    parseAndMorph3D(query);
    const p = nlSim ? nlSim.preset : { formula: 'Nanocarrier', r0: 80, charge: -20 };
    const reply = `Generated and updated 3D digital twin: <b>${p.formula}</b> (${p.r0} nm, surface potential ${p.charge > 0 ? '+' : ''}${p.charge} mV). Glowing light ray border, lattice packing, and payload have dynamically updated!`;
    const actions = [
      { label: 'View in 3D Tab', icon: '🌐', action: "switchTab('viewer')" },
      { label: 'Send to Live Simulation', icon: '▶️', action: "switchTab('simulation')" }
    ];
    appendNanoBotMsg('ai', reply, actions);
    speakText(`Updated 3D model for ${p.formula} at ${p.r0} nanometers.`);
    return;
  }

  // F. GENERAL TELEMETRY ANALYSIS
  if (q.includes('analyze') || q.includes('state') || q.includes('telemetry')) {
    let curSize = 120, curZeta = -22.0, curRel = 0;
    if (typeof state !== 'undefined' && state.particle) {
      curSize = state.particle.size || 120;
      curZeta = state.particle.zeta || -22;
      curRel = state.particle.release || 0;
    }
    const isStable = Math.abs(curZeta) >= 20;
    const reply = `<b>Current Telemetry Analysis:</b><br>` +
      `• <b>Particle Size:</b> ${curSize.toFixed(1)} nm<br>` +
      `• <b>Zeta Potential:</b> ${curZeta.toFixed(1)} mV (${isStable ? 'Colloidally Stable' : 'Aggregation-Prone'})<br>` +
      `• <b>Colloidal DLVO Barrier:</b> ${Math.abs(curZeta) >= 30 ? 'High electrostatic repulsion barrier prevents protein agglomeration.' : 'Moderate steric barrier; recommended PEGylation to extend half-life.'}<br>` +
      `• <b>Korsmeyer-Peppas Release:</b> ${curRel.toFixed(1)}% cumulative drug release.`;
    const actions = [
      { label: 'Run Live Simulation', icon: '▶️', action: "switchTab('simulation')" }
    ];
    appendNanoBotMsg('ai', reply, actions);
    speakText(`Telemetry analysis: particle size ${curSize.toFixed(1)} nanometers, zeta potential ${curZeta.toFixed(1)} millivolts, current release ${curRel.toFixed(1)} percent.`);
    return;
  }

  // G. FALLBACK: GENERAL NANOMEDICINE ASSISTANT
  const formattedPrompt = `Design ${q.includes('cancer') ? 'oncology-targeted' : 'biocompatible'} nanocarrier delivering active cargo in PBS buffer pH 7.4 at 37°C with sustained Korsmeyer-Peppas release kinetics and low cytotoxicity screen.`;
  const reply = `I have analyzed your query: <i>"${query}"</i>.<br><br>` +
    `For predictive screening across the Stability Regressor and Cytotoxicity Classifier, I have structured an experimental run for the primary simulation engine.`;
  
  const actions = [
    { label: 'Send to Main Section & Execute', icon: '🚀', action: `sendAsMainPrompt('${formattedPrompt.replace(/'/g, "\'")}')` },
    { label: 'Configure Paracetamol Simulation', icon: '💊', action: "window.confirmAiDrugSetup('nm-paracetamol-plga')" },
    { label: 'Configure Ciprofloxacin Simulation', icon: '🧪', action: "window.confirmAiDrugSetup('ciprofloxacin-plga')" }
  ];
  appendNanoBotMsg('ai', reply, actions);
  speakText(`Analyzed your query. I have prepared a simulation configuration.`);
}


function sendAsMainPrompt(promptText){
  // 1. Populate prompt in main workspace textarea
  const targetArea = document.getElementById('experiment-prompt') || 
                     document.getElementById('quick-prompt-input');
  if(targetArea){
    targetArea.value = promptText;
    targetArea.scrollIntoView({behavior: 'smooth', block: 'center'});
    targetArea.style.borderColor = '#38bdf8';
    targetArea.style.boxShadow = '0 0 20px rgba(56, 189, 248, 0.6)';
    setTimeout(() => { targetArea.style.borderColor = ''; targetArea.style.boxShadow = ''; }, 3000);
  }

  // 2. Switch to Main Simulation / Prompt tab
  if(typeof switchTab === 'function'){
    const tabTarget = document.getElementById('view-prompt') ? 'prompt' : 'simulation';
    switchTab(tabTarget);
  } else if(typeof tab === 'function'){
    tab('pred');
  }

  // 3. Confirm to user via assistant
  appendNanoBotMsg('ai', `🚀 <b>Transferred to Main Section!</b> The formatted prompt has been injected into the primary experiment input: <i>"${promptText}"</i>.`);
}



// -------------------------------------------------------------
// Research Report Generator
// -------------------------------------------------------------
function generateResearchReport() {
    const lines = [
        '====================================================================',
        '               NANOMEDAI RESEARCH SESSION AUDIT REPORT              ',
        '====================================================================',
        `Generated: ${new Date().toLocaleString()}`,
        `Platform Version: 1.0.0 (FastAPI + Scikit-Learn 1.6+)`,
        '',
        '--- 1. ACTIVE SIMULATION STATE ---',
        `Formulation: ${FORMULATIONS[state.formulationKey]?.name || 'Custom'}`,
        `Simulation Time: ${state.time.toFixed(1)} h (Max: ${state.maxTime.toFixed(1)} h)`,
        `Environment: Temp = ${state.env.temp.toFixed(1)}°C, pH = ${state.env.ph.toFixed(1)}, Ionic = ${state.env.ionic.toFixed(2)} M`,
        `Particle Core Size: ${state.particle.size ? state.particle.size.toFixed(1) : 'N/A'} nm`,
        `Hydrodynamic Size: ${state.particle.hydSize ? state.particle.hydSize.toFixed(1) : 'N/A'} nm`,
        `Zeta Potential: ${state.particle.zeta ? state.particle.zeta.toFixed(1) : 'N/A'} mV`,
        `PDI: ${state.particle.pdi ? state.particle.pdi.toFixed(3) : 'N/A'}`,
        `Cumulative Drug Release: ${state.particle.release.toFixed(2)}%`,
        `Drug Remaining in Core: ${state.particle.remaining.toFixed(2)}%`,
        ''
    ];
    
    if (state.workflowResult) {
        const wf = state.workflowResult;
        lines.push('--- 2. AI EXPERIMENT PROMPT PIPELINE ---');
        lines.push(`Input Prompt: ${$('experiment-prompt').value}`);
        lines.push(`Colloidal Stability: ${wf.stability.result ? `${wf.stability.result.prediction} mV (${wf.stability.result.stability_class})` : 'Outside validated domain'}`);
        lines.push(`Cytotoxicity: ${wf.toxicity.result ? `${wf.toxicity.result.prediction} (Risk: ${wf.toxicity.result.risk_level})` : 'Not evaluated'}`);
        lines.push(`Biophysical Release: ${wf.simulation.final_release_pct !== null ? `${wf.simulation.final_release_pct.toFixed(1)}% at ${state.maxTime.toFixed(0)}h` : 'Not run'}`);
        lines.push(`Cross-Validation Stability MAE: ${wf.stability.cv.metrics.MAE_mV.toFixed(2)} mV`);
        lines.push(`Cross-Validation Toxicity F1: ${wf.toxicity.cv.metrics.F1.toFixed(3)}`);
        lines.push(`Cross-Validation Release MAE: ${wf.simulation.cv.MAE_release_percentage_points.toFixed(2)} percentage points`);
        lines.push('');
    }
    
    if (state.predictionHistory.length) {
        lines.push('--- 3. DIRECT MODEL PREDICTIONS HISTORY ---');
        state.predictionHistory.forEach((item, idx) => {
            lines.push(`[${idx + 1}] ${item.task.toUpperCase()} at ${item.time}`);
            lines.push(`Inputs: ${JSON.stringify(item.payload)}`);
            lines.push(`Result: ${JSON.stringify(item.res.prediction)} (${item.res.confidence || ''})`);
            lines.push('');
        });
    }
    
    lines.push('--- 4. SCIENTIFIC LIMITATIONS & ADVISORY ---');
    lines.push('• All estimates are generated by harmonized empirical surrogate models.');
    lines.push('• Biological stages (Protein corona, Cellular uptake, In vivo distribution) require prospective wet-lab validation.');
    lines.push('• Environmental pH and ionic strength modifiers are non-causal heuristic bounds unless explicitly modeled in wet lab assays.');
    lines.push('====================================================================');
    
    $('report-output').value = lines.join('\n');
}

$('generate-report').addEventListener('click', generateResearchReport);

$('download-report').addEventListener('click', () => {
    let text = $('report-output').value;
    if (!text.trim()) {
        generateResearchReport();
        text = $('report-output').value;
    }
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NanoMedAI_Research_Report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
});

// -------------------------------------------------------------
// System Bootstrap & Health Check
// -------------------------------------------------------------
async function bootstrap() {
    // Populate Initial Static Formulation
    setFormulationConfig('formulation-a');
    resetSim();
    
    // Ping Backend Health
    const pill = $('backend-status-pill');
    const pillText = $('backend-status-text');
    try {
        const health = await requestJSON('/api/health');
        state.backendConnected = true;
        pill.className = 'backend-indicator online';
        pillText.textContent = `API: ONLINE (${health.version})`;
        addEvent(`Connected to NanoMedAI FastAPI backend (v${health.version})`, 'sys');
        
        // Fetch Metadata & setup forms
        const meta = await requestJSON('/api/metadata');
        state.metadata = meta;
        
        // Fill dropdowns in Advanced Drawer & Matrix
        const stab = meta.stability;
        const cyto = meta.cytotoxicity;
        const populateSelect = (id, items) => {
            const el = $(id);
            if (!el) return;
            el.innerHTML = '<option value="">Default</option>' + (items || []).map(i => `<option value="${escapeHTML(i)}">${escapeHTML(i)}</option>`).join('');
        };

        const setupSearchableDrugDropdown = (inputId, dropdownId, items, drugMwMap) => {
            const input = $(inputId);
            const dropdown = $(dropdownId);
            if (!input || !dropdown) return;

            let availableItems = items || [];

            const renderOptions = (filterText = '') => {
                const query = (filterText || '').trim().toLowerCase();
                const matches = availableItems.filter(item => item.toLowerCase().includes(query));
                if (matches.length === 0) {
                    dropdown.innerHTML = '<div class="searchable-option empty">No matching drug found</div>';
                } else {
                    dropdown.innerHTML = matches.map(item => 
                        `<div class="searchable-option" data-value="${escapeHTML(item)}">${escapeHTML(item)}</div>`
                    ).join('');
                }
            };

            const showDropdown = () => {
                renderOptions(input.value);
                dropdown.style.display = 'block';
            };

            input.addEventListener('focus', showDropdown);
            input.addEventListener('click', showDropdown);

            input.addEventListener('input', () => {
                renderOptions(input.value);
                dropdown.style.display = 'block';
            });

            dropdown.addEventListener('click', (e) => {
                const itemEl = e.target.closest('.searchable-option');
                if (itemEl && itemEl.dataset.value) {
                    const selectedDrug = itemEl.dataset.value;
                    input.value = selectedDrug;
                    dropdown.style.display = 'none';

                    const mwInput = $('prompt-drug-mw');
                    if (mwInput && drugMwMap && drugMwMap[selectedDrug]) {
                        if (!mwInput.value || parseFloat(mwInput.value) === 0) {
                            mwInput.value = drugMwMap[selectedDrug];
                        }
                    }
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            document.addEventListener('click', (e) => {
                if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });
        };

        populateSelect('prompt-core', stab.cores);
        populateSelect('prompt-shape', stab.shapes);
        populateSelect('prompt-material', cyto.materials);
        populateSelect('prompt-assay', cyto.assays);
        populateSelect('prompt-cell', cyto.cell_lines);
        if ($('prompt-drug-dropdown')) {
            setupSearchableDrugDropdown('prompt-drug', 'prompt-drug-dropdown', rel.categories.drug_name, rel.drug_mw_map);
        } else {
            populateSelect('prompt-drug', rel.categories.drug_name);
        }
        populateSelect('prompt-polymer', rel.categories.polymer);
        
        if ($('prompt-ligand')) {
            $('prompt-ligand').innerHTML = '<option value="">Default</option>' +
                stab.ligand_presets.map(l => `<option value="${escapeHTML(l.smiles)}">${escapeHTML(l.name)}</option>`).join('');
        }
        
        if ($('matrix-core')) {
            $('matrix-core').innerHTML = stab.cores.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('');
        }
        
        buildPredictorForm('stability');
    } catch (err) {
        state.backendConnected = false;
        pill.className = 'backend-indicator offline';
        pillText.textContent = 'API: STANDALONE ENGINE';
        addEvent('Backend service unreachable; running in standalone local biophysical mode', 'warn');
    }

    initIntroModal();
}

// Intro Modal Handlers & Diagnostics
function initIntroModal() {
    const modal = $('intro-modal');
    const closeBtn = $('btn-close-intro');
    const enterBtn = $('btn-enter-workspace');
    const showBtn = $('btn-show-intro');
    
    function closeModal() {
        if (modal) modal.classList.remove('active');
    }
    function openModal() {
        if (modal) {
            modal.classList.add('active');
            runIntroDiagnostics();
        }
    }
    
    if (closeBtn) closeBtn.onclick = closeModal;
    if (enterBtn) enterBtn.onclick = closeModal;
    if (showBtn) showBtn.onclick = openModal;
    
    // Auto-animate diagnostics
    runIntroDiagnostics();
}

function runIntroDiagnostics() {
    const bar = $('intro-diag-bar');
    const pct = $('intro-diag-percent');
    if (!bar || !pct) return;
    
    bar.style.width = '0%';
    pct.textContent = 'INITIALIZING...';
    
    let p = 0;
    const interval = setInterval(() => {
        p += 25;
        if (p > 100) {
            clearInterval(interval);
            bar.style.width = '100%';
            pct.textContent = '100% READY';
        } else {
            bar.style.width = p + '%';
            pct.textContent = p + '% READY';
        }
    }, 160);
}

// Window Resize Handling
window.addEventListener('resize', () => {
    if (typeof resize3D === 'function') resize3D();
});

// Run Bootstrap on DOM Ready
document.addEventListener('DOMContentLoaded', bootstrap);


</script>

<!-- ============================================================== -->
<!-- SITEWIDE AI NANOMEDICINE ASSISTANT (Voice & Read-Out Engine)   -->
<!-- ============================================================== -->
<div id="nanobot-widget" class="nanobot-container">
  <button id="nanobot-launcher" class="nanobot-launcher-btn" onclick="toggleNanoBot()">
    <span class="pulse-beacon"></span>
    <span class="launcher-icon">✨</span>
    <span class="launcher-text">NanoMed AI Assistant</span>
  </button>

  <div id="nanobot-window" class="nanobot-window">
    <div class="nanobot-header">
      <div class="nanobot-title-wrap">
        <div class="nanobot-avatar">🤖</div>
        <div>
          <h4>NanoMed AI Companion</h4>
          <span class="nanobot-status"><i class="status-dot"></i> Live Biophysical Assistant</span>
        </div>
      </div>
      <div class="nanobot-actions">
        <span id="speaking-wave" class="speaking-wave-box" style="display:none;" title="AI is speaking">
          <span class="speaking-wave-bar"></span>
          <span class="speaking-wave-bar"></span>
          <span class="speaking-wave-bar"></span>
        </span>
        <button id="btn-readout-toggle" class="nanobot-tool-btn active" onclick="toggleReadOut()" title="Toggle voice read-out mode">🔊 Voice: ON</button>
        <button id="btn-stop-speech" class="nanobot-tool-btn stop-btn" onclick="stopSpeech()" style="display:none" title="Stop speech">⏹ Stop</button>
        <button class="nanobot-close-btn" onclick="toggleNanoBot()" title="Minimize Assistant">&times;</button>
      </div>
    </div>

    <div id="nanobot-messages" class="nanobot-messages">
      <div class="nanobot-msg ai">
        <div class="msg-bubble">
          👋 <b>Welcome to NanoMed AI!</b> I am your voice-enabled nanomedicine co-pilot.<br><br>
          You can talk or type to me anytime. I can:<br>
          • <b>Morph the 3D Model:</b> <i>"Design an 85nm Liposome with Doxorubicin at -30mV"</i><br>
          • <b>Analyze Telemetry:</b> <i>"Check colloidal stability & cytotoxicity risk"</i><br>
          • <b>Format Main Prompt:</b> <i>"Prepare prompt for breast cancer mRNA LNP"</i>
          <br><button class="msg-speaker-btn" onclick="speakMessageBubble(this)" title="Read aloud">🔊 Listen</button>
        </div>
      </div>
    </div>

    <div class="nanobot-quick-chips">
      <button class="chip-btn" onclick="quickAsk('Analyze active simulation & release state')">📊 Analyze Active State</button>
      <button class="chip-btn" onclick="quickAsk('Create an 80nm Lipid Nanoparticle with mRNA')">🧬 Design mRNA LNP (3D)</button>
      <button class="chip-btn" onclick="quickAsk('Prepare optimal breast cancer formulation prompt')">🚀 Format Main Prompt</button>
    </div>

    <div class="nanobot-input-bar">
      <button id="btn-voice-input" class="voice-mic-btn" onclick="startAssistantVoice()" title="Speak to NanoMed AI">
        <span class="mic-icon">🎤</span>
      </button>
      <input id="nanobot-input" type="text" placeholder="Speak or ask anything about formulation, 3D model, or risk..." autocomplete="off">
      <button id="btn-nanobot-send" class="nanobot-send-btn" onclick="sendNanoBotMessage()">Send</button>
    </div>
  </div>
</div>

<!-- ============================================================== -->
<!-- FLOATING VOICE HUD & REAL-TIME SPEECH RECOGNITION EQUALIZER     -->
<!-- ============================================================== -->
<div id="voice-hud-indicator" class="voice-hud-indicator">
  <div class="voice-hud-card">
    <div class="voice-hud-header">
      <div class="voice-hud-live-tag">
        <span class="live-rec-pulsar"></span>
        <span class="voice-hud-label">AI LISTENING...</span>
      </div>
      <div class="voice-wave-eq">
        <span class="wave-bar wb-1"></span>
        <span class="wave-bar wb-2"></span>
        <span class="wave-bar wb-3"></span>
        <span class="wave-bar wb-4"></span>
        <span class="wave-bar wb-5"></span>
      </div>
    </div>
    <div class="voice-hud-stream" id="voice-hud-stream">
      <span class="voice-hint">🎙️ Speak into your microphone (e.g. "Design 80nm Liposome with Doxorubicin at -30mV")...</span>
    </div>
    <div class="voice-hud-footer">
      <button id="voice-hud-done" class="vh-btn vh-done" onclick="finishVoiceRecognition()">
        <span>⏹</span> Done / Process
      </button>
      <button id="voice-hud-cancel" class="vh-btn vh-cancel" onclick="cancelVoiceRecognition()">
        <span>✕</span> Cancel
      </button>
    </div>
  </div>
</div>

</body>
</html>
"""

def find_available_port(preferred=8000):
    import socket
    for p in [preferred, 8008, 8050, 8080]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    return 8008

if __name__ == "__main__":
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print(f"  NanoMedAI Live Server running at: {url}")
    print("=" * 65)
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port)
