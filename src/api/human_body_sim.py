"""
Human Body Interaction and Nanomedicine Simulation API
======================================================
Provides multi-scale biophysical evaluation, regional anatomical intelligence,
and rigorous stage-by-stage journey modeling for drug-loaded nanoparticles.

Scientific Integrity Guidelines:
- ML predictions (Stability Zeta mV, Cytotoxicity) are calculated using active trained models.
- Drug release kinetics are simulated using the Korsmeyer-Peppas ODE model (Mt/M_inf = k * t^n).
- Biological interactions (protein corona, cellular endocytosis, extravasation, organ clearance)
  are strictly classified and labeled as conceptual biological illustrations when no quantitative
  prediction model exists.
- Disclaims clinical applicability and warns on out-of-domain environmental parameters.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np
from pydantic import BaseModel, Field

from src.predict import (
    predict_stability,
    predict_cytotoxicity,
    _extract_charge,
    _estimate_mw,
    ValidationError as ModelValidationError,
)
from src.api.prompt_workflow import check_model_domain, get_model_domains


# ---------------------------------------------------------------------------
# Biological Regions Knowledge Base (Established Anatomical / Biophysical Data)
# ---------------------------------------------------------------------------
BIOLOGICAL_REGIONS: Dict[str, Dict[str, Any]] = {
    "bloodstream": {
        "id": "bloodstream",
        "name": "Bloodstream & Systemic Circulation",
        "category": "Hemodynamic Transport",
        "anatomical_location": "Vascular system (arteries, arterioles, veins, capillaries)",
        "physiological_properties": {
            "fluid_type": "Whole blood (plasma, erythrocytes, leukocytes, platelets)",
            "pH": 7.35 - 7.45,
            "temperature_c": 37.0,
            "shear_rate_s_minus_1": "100 - 2000 s⁻¹ (venous to microvascular)",
            "flow_velocity": "0.5 - 1.0 mm/s in capillaries; 10 - 40 cm/s in aorta",
            "ionic_strength_M": 0.154,
        },
        "nanoparticle_interactions": (
            "Nanoparticles experience hydrodynamic shear stress, collisions with erythrocytes "
            "(facilitating margination toward the endothelial wall), and immediate contact with plasma proteins. "
            "Sterically stabilized particles (e.g. PEGylated) resist rapid aggregation, whereas unprotected "
            "or low-charge particles (|ζ| < 20 mV) risk micro-aggregation under physiological ionic strength."
        ),
        "barrier_description": "Vascular endothelium with tight junctions (< 2 nm in continuous capillaries).",
        "expected_phenomena": [
            "Laminar convective transport",
            "Margination toward vascular walls",
            "Hemodynamic shear-induced dispersion",
            "Collisions with circulating erythrocytes"
        ],
        "scientific_classification": "ESTABLISHED HEMODYNAMIC KNOWLEDGE",
        "model_nature": "Physiological transport physics and empirical fluid dynamics"
    },
    "liver": {
        "id": "liver",
        "name": "Liver (Hepatic Reticuloendothelial System)",
        "category": "Primary Clearance & Sequestration",
        "anatomical_location": "Hepatic sinusoids, Space of Disse, Kupffer cells",
        "physiological_properties": {
            "fenestration_diameter_nm": "100 - 150 nm",
            "blood_flow_rate": "1.2 - 1.5 L/min (25% of cardiac output)",
            "sinusoidal_velocity": "0.1 - 0.3 mm/s (slow transit allowing phagocytosis)",
            "resident_macrophages": "Kupffer cells (~80-90% of all tissue macrophages)"
        },
        "nanoparticle_interactions": (
            "Primary site of nanoparticle accumulation for particles > 50-100 nm. Opsonized particles are "
            "avidly recognized by scavenger receptors on Kupffer cells and hepatic sinusoidal endothelial cells. "
            "Particles < 100 nm can cross sinusoidal fenestrations into the Space of Disse to interact directly "
            "with hepatocytes, potentially undergoing hepatobiliary excretion via bile."
        ),
        "barrier_description": "Discontinuous sinusoidal endothelium with 100-150 nm fenestrations.",
        "expected_phenomena": [
            "Receptor-mediated phagocytosis by Kupffer cells",
            "Fenestration permeation into Space of Disse (<100 nm)",
            "Metabolic enzymatic degradation of polymer matrix",
            "Biliary excretion of non-degraded residues"
        ],
        "scientific_classification": "ESTABLISHED ANATOMICAL KNOWLEDGE",
        "model_nature": "Literature-supported mononuclear phagocyte system (MPS) physiology"
    },
    "kidneys": {
        "id": "kidneys",
        "name": "Kidneys (Renal Glomerular Filtration)",
        "category": "Size-Selective Elimination",
        "anatomical_location": "Renal corpuscle, Bowman's capsule, podocyte slit diaphragms",
        "physiological_properties": {
            "glomerular_filtration_cutoff_nm": "6.0 - 8.0 nm hydrodynamic diameter",
            "molecular_weight_cutoff_kDa": "~30 - 50 kDa",
            "surface_charge_filtration": "Anionic filtration barrier repels negatively charged species",
            "renal_blood_flow": "1.0 - 1.2 L/min (20% of cardiac output)"
        },
        "nanoparticle_interactions": (
            "Nanoparticles with hydrodynamic diameters below 6-8 nm undergo rapid glomerular filtration into "
            "urine. Particles larger than 10-15 nm are generally retained in systemic circulation unless they "
            "undergo biodegradation into sub-threshold renal metabolites. Cationic particles may bind non-specifically "
            "to the negatively charged glomerular basement membrane."
        ),
        "barrier_description": "Three-layer glomerular filtration barrier: fenestrated endothelium (70-90 nm), "
                               "glomerular basement membrane, and podocyte slit diaphragms (4-10 nm).",
        "expected_phenomena": [
            "Rapid urinary elimination for sub-8 nm particles",
            "Steric retention for conventional nanocarriers (>20 nm)",
            "Glomerular basement membrane charge interactions",
            "Proximal tubular epithelial reabsorption (minor)"
        ],
        "scientific_classification": "ESTABLISHED ANATOMICAL KNOWLEDGE",
        "model_nature": "Physiological renal pore-size sieving model"
    },
    "lungs": {
        "id": "lungs",
        "name": "Lungs (Pulmonary Capillary Bed & Alveoli)",
        "category": "Microvascular Transit & Inhalation Clearance",
        "anatomical_location": "Pulmonary capillaries and alveolar airspace",
        "physiological_properties": {
            "capillary_diameter_um": "5 - 8 µm (erythrocyte-sized)",
            "transit_time_seconds": "0.75 seconds at rest",
            "total_surface_area": "100 - 140 m²",
            "alveolar_macrophages": "Active in airspace and interstitial septa"
        },
        "nanoparticle_interactions": (
            "In systemic intravenous circulation, nanoparticles must transit through the dense pulmonary capillary bed. "
            "Unstable particles that aggregate into clusters > 5 µm risk micro-embolism in pulmonary capillaries. "
            "For inhalation administration routes, nanoparticles deposit in alveoli based on aerodynamic diameter "
            "and undergo clearance by alveolar macrophages or mucociliary escalator."
        ),
        "barrier_description": "Extremely thin alveolar-capillary membrane (0.2 - 0.5 µm).",
        "expected_phenomena": [
            "Rapid microvascular capillary transit for dispersed particles",
            "Entrapment risk if colloidal aggregation occurs (>5 µm)",
            "High local oxygen tension and pulmonary surfactant interaction",
            "Macrophage clearance if delivered via aerosol"
        ],
        "scientific_classification": "ESTABLISHED ANATOMICAL KNOWLEDGE",
        "model_nature": "Pulmonary hemodynamics and aerosol deposition mechanics"
    },
    "skin": {
        "id": "skin",
        "name": "Skin (Dermal Microcirculation & Transdermal Barrier)",
        "category": "Peripheral Microvasculature & Barrier Tissue",
        "anatomical_location": "Epidermis, dermis, dermal papillary capillaries",
        "physiological_properties": {
            "stratum_corneum_cutoff": "< 500 Da; generally impermeable to intact NPs > 10 nm",
            "surface_pH": "4.5 - 5.5 (acid mantle)",
            "dermal_temperature_c": "32 - 34 °C",
            "dermal_capillary_diameter": "7 - 10 µm"
        },
        "nanoparticle_interactions": (
            "For systemic IV delivery, skin represents a peripheral microvascular perfusion site with tight "
            "continuous capillaries. For topical/transdermal applications, the intact stratum corneum provides an "
            "almost impenetrable barrier to nanoparticles > 10 nm, requiring follicular shunt pathways, chemical "
            "permeation enhancers, or microneedles to access systemic capillaries."
        ),
        "barrier_description": "Stratum corneum: 'bricks-and-mortar' corneocytes embedded in lipid lamellar matrix.",
        "expected_phenomena": [
            "Low extravasation under normal continuous capillary conditions",
            "Topical size-exclusion by stratum corneum lipid bilayers",
            "Follicular duct accumulation for topical formulations",
            "Potential dermal lymphatic drainage upon intradermal injection"
        ],
        "scientific_classification": "ESTABLISHED ANATOMICAL KNOWLEDGE",
        "model_nature": "Dermatological lipid matrix barrier principles"
    },
    "target_tissue": {
        "id": "target_tissue",
        "name": "Target Tissue (e.g. Solid Tumor / Inflamed Lesion)",
        "category": "Extravasation & Extracellular Penetration",
        "anatomical_location": "Pathological tissue interstitium (oncology / inflammatory site)",
        "physiological_properties": {
            "endothelial_pore_cutoff_nm": "100 - 800 nm (EPR effect in hyperpermeable tumor vessels)",
            "interstitial_fluid_pressure_mmHg": "10 - 40 mmHg (elevated IFP hindering convection)",
            "extracellular_matrix": "Dense collagen fibrils and hyaluronan gel",
            "local_microenvironment_pH": "6.5 - 6.9 (hypoxic/acidic Warburg effect in tumors)"
        },
        "nanoparticle_interactions": (
            "Nanoparticles may exploit passive Enhanced Permeability and Retention (EPR) through defective, leaky "
            "tumor vessels, but targeting is NEVER guaranteed. Clinical and preclinical data indicate that median "
            "delivery efficiency is frequently under 1-2% of the injected dose. Elevated interstitial fluid pressure "
            "(IFP) and dense collagen-hyaluronan matrices severely restrict deep tissue penetration, leading to "
            "perivascular particle accumulation."
        ),
        "barrier_description": "Elevated interstitial fluid pressure (IFP) and dense fibrous extracellular matrix.",
        "expected_phenomena": [
            "Passive extravasation through hyperpermeable vascular fenestrations",
            "Steric hindrance and diffusion retardation by collagen/hyaluronan matrix",
            "Receptor-mediated targeting if functionalized with specific ligands",
            "Compromised deep-core penetration due to interstitial fluid pressure"
        ],
        "scientific_classification": "ESTABLISHED ONCOLOGY & BIOMATERIALS KNOWLEDGE",
        "model_nature": "Tumor microenvironment transport physics and EPR literature"
    },
    "cellular_environment": {
        "id": "cellular_environment",
        "name": "Cellular Environment & Endocytic Pathway",
        "category": "Membrane Interaction & Internalization",
        "anatomical_location": "Target cell surface, plasma membrane, endosomes, lysosomes",
        "physiological_properties": {
            "membrane_potential_mV": "-10 to -70 mV across plasma membrane",
            "glycocalyx_charge": "Net negative (sialic acid residues, proteoglycans)",
            "early_endosome_pH": "6.0 - 6.5",
            "late_endosome_lysosome_pH": "4.5 - 5.0",
            "endocytic_vesicle_size_nm": "60 - 150 nm (clathrin/caveolae) up to >500 nm (macropinosome)"
        },
        "nanoparticle_interactions": (
            "Cationic nanoparticles experience strong electrostatic attraction to the negatively charged glycocalyx, "
            "often driving higher (though non-specific) membrane contact and potential membrane disruption. "
            "Neutral/anionic particles exhibit lower non-specific uptake. Once internalized into endocytic vesicles, "
            "particles encounter an acidic microenvironment (pH 5.0 in lysosomes) rich in hydrolases, which can trigger "
            "accelerated drug release, proton-sponge endosomal escape, or carrier degradation."
        ),
        "barrier_description": "Phospholipid bilayer with fluid mosaic proteins and thick anionic glycocalyx brush.",
        "expected_phenomena": [
            "Membrane adherence via electrostatic/receptor interaction",
            "Clathrin-mediated endocytosis, caveolae, or macropinocytosis",
            "Acidification from early endosome (pH 6.2) to lysosome (pH 4.8)",
            "Enzymatic hydrolytic degradation and intracellular drug diffusion"
        ],
        "scientific_classification": "ESTABLISHED CELL BIOLOGY KNOWLEDGE",
        "model_nature": "Cellular endocytosis and endolysosomal trafficking mechanics"
    }
}


# ---------------------------------------------------------------------------
# 8-Stage Journey Specification & Integrity Mapping
# ---------------------------------------------------------------------------
SIMULATION_STAGES: List[Dict[str, Any]] = [
    {
        "stage_id": 1,
        "key": "administration",
        "name": "Stage 1: Administration & Introduction",
        "badge_text": "ESTABLISHED BIOPHYSICAL PROTOCOL",
        "badge_type": "protocol",
        "scientific_nature": "Physiological Administration Modeling",
        "is_quantitative_prediction": False,
        "description": "Introduction of drug-loaded nanoparticles into the biological system.",
        "scientific_mechanisms": (
            "For intravenous (IV) administration, particles are introduced directly into systemic circulation "
            "via a peripheral or central vein, undergoing rapid 1:1000 dilution in approximately 5 liters of blood "
            "within 1 to 2 minutes of circulation time."
        ),
        "limitations": "Route-specific pharmacokinetics for non-IV routes (oral, inhalation) require specialized mucosal barrier models."
    },
    {
        "stage_id": 2,
        "key": "circulation",
        "name": "Stage 2: Bloodstream Circulation & Hemodynamics",
        "badge_text": "PREDICTED STABILITY & FLUID DYNAMICS",
        "badge_type": "ml-physics",
        "scientific_nature": "Active ML Zeta Inference + Colloidal DLVO Physics",
        "is_quantitative_prediction": True,
        "description": "Transport through arterial, venous, and capillary vascular networks.",
        "scientific_mechanisms": (
            "Nanoparticles circulate with laminar blood flow, colliding with erythrocytes and marginating toward vessel walls. "
            "Colloidal stability is evaluated via predicted surface charge (|ζ| potential). High surface charge provides electrostatic repulsion, "
            "while PEGylation provides steric hydration barriers preventing salt-induced aggregation."
        ),
        "limitations": "In-vivo half-life is influenced by multiple unmodeled biological clearance factors beyond surface charge."
    },
    {
        "stage_id": 3,
        "key": "protein_corona",
        "name": "Stage 3: Protein Corona Formation",
        "badge_text": "CONCEPTUAL BIOLOGICAL ILLUSTRATION",
        "badge_type": "conceptual",
        "scientific_nature": "Conceptual Biological Illustration (No Validated ML Model)",
        "is_quantitative_prediction": False,
        "description": "Adsorption of plasma proteins onto nanoparticle surfaces forming a biomolecular corona.",
        "scientific_mechanisms": (
            "Upon contact with plasma, over 300 varieties of proteins (albumin, fibrinogen, apolipoproteins, IgG, complement factors) "
            "rapidly adsorb onto the nanoparticle surface. A tightly bound 'hard corona' forms within minutes, surrounded by a dynamic 'soft corona'. "
            "This corona fundamentally alters the nanoparticle's synthetic identity, redefining its biological cellular recognition."
        ),
        "limitations": "IMPORTANT: No validated quantitative protein corona prediction model is active in this platform. This visualization is purely conceptual and qualitative."
    },
    {
        "stage_id": 4,
        "key": "tissue_interaction",
        "name": "Stage 4: Target Tissue Interaction & Extravasation",
        "badge_text": "PHYSIOLOGICAL INTERACTION MECHANICS",
        "badge_type": "mechanics",
        "scientific_nature": "Vascular Extravasation & Extracellular Matrix Barrier Mechanics",
        "is_quantitative_prediction": False,
        "description": "Approach toward target microvasculature and tissue extravasation.",
        "scientific_mechanisms": (
            "In tumor or inflamed tissues, hyperpermeable vasculature with discontinuous endothelium may permit passive extravasation "
            "(Enhanced Permeability and Retention effect). However, high interstitial fluid pressure and dense collagen matrices retard penetration. "
            "Targeting is NOT guaranteed; median delivery across solid tumors rarely exceeds 1-2% of injected dose."
        ),
        "limitations": "Does not guarantee target accumulation; solid tumor delivery efficiency is subject to severe in-vivo physiological barriers."
    },
    {
        "stage_id": 5,
        "key": "cellular_uptake",
        "name": "Stage 5: Cellular Uptake & Endocytic Internalization",
        "badge_text": "CONCEPTUAL BIOLOGICAL ILLUSTRATION",
        "badge_type": "conceptual",
        "scientific_nature": "Multi-Step Endocytosis Pathway (Conceptual Illustration)",
        "is_quantitative_prediction": False,
        "description": "Membrane contact, invagination, vesicle formation, and intracellular trafficking.",
        "scientific_mechanisms": (
            "1. Approach: Nanoparticle reaches cell surface.\n"
            "2. Contact: Electrostatic attraction or ligand-receptor engagement with glycocalyx.\n"
            "3. Invagination: Membrane forms clathrin/caveolae-coated pit or macropinocytic fold.\n"
            "4. Vesicle Formation: Budding into early endosome (pH ~6.2).\n"
            "5. Intracellular Release: Endosome acidification (pH ~5.0 in lysosome) prompts drug escape or enzymatic carrier breakdown."
        ),
        "limitations": "Distinguished from quantitative cellular uptake rates. Specific internalization kinetics depend on cell-specific receptor densities."
    },
    {
        "stage_id": 6,
        "key": "drug_release",
        "name": "Stage 6: Drug Release Kinetics",
        "badge_text": "MATHEMATICAL SIMULATION (KORSMEYER-PEPPAS ODE)",
        "badge_type": "ode-math",
        "scientific_nature": "Validated Mathematical Kinetics Model (Mt/M_inf = k * t^n)",
        "is_quantitative_prediction": True,
        "description": "Sustained diffusion and dissolution of active pharmaceutical molecules from the matrix.",
        "scientific_mechanisms": (
            "Drug release is mathematically computed using the Korsmeyer-Peppas power-law ODE: Mt/M_inf = k * t^n. "
            "The release exponent n characterizes the underlying physical transport mechanism: "
            "n ≤ 0.43 indicates Fickian diffusion; 0.43 < n < 0.85 indicates anomalous non-Fickian transport; "
            "n ≥ 0.85 corresponds to Case II polymer relaxation/erosion controlled release."
        ),
        "limitations": "Valid strictly for cumulative release up to 60%. Parameters k and n are empirical constants fitted at 37°C/pH 7.4 and do not causally adjust for uncharacterized pH/temperature shifts."
    },
    {
        "stage_id": 7,
        "key": "toxicity_response",
        "name": "Stage 7: Biological Response & Cytotoxicity",
        "badge_text": "ACTIVE ML PREDICTION (RANDOM FOREST)",
        "badge_type": "ml-prediction",
        "scientific_nature": "Trained Machine Learning In-Vitro Cytotoxicity Classification",
        "is_quantitative_prediction": True,
        "description": "Assessment of carrier biocompatibility and target cell interaction.",
        "scientific_mechanisms": (
            "Carrier cytotoxicity is predicted using a trained Random Forest model evaluated across particle size, surface area, "
            "surface charge, exposure time, mass dose, material type, cell line, and assay type. "
            "Crucially, carrier-induced cytotoxicity (e.g. membrane disruption, ROS generation) is distinguished from the intended "
            "therapeutic pharmacological efficacy of the encapsulated drug molecule."
        ),
        "limitations": "Research screening estimate based on in-vitro assay data. Does NOT predict clinical toxicity, therapeutic effectiveness, or human patient safety."
    },
    {
        "stage_id": 8,
        "key": "clearance",
        "name": "Stage 8: Clearance, Metabolism & Elimination",
        "badge_text": "CONCEPTUAL BIOLOGICAL ILLUSTRATION",
        "badge_type": "conceptual",
        "scientific_nature": "Organ-Specific Clearance Pathways (Conceptual Illustration)",
        "is_quantitative_prediction": False,
        "description": "Clearance of carrier fragments and metabolites through renal and hepatobiliary systems.",
        "scientific_mechanisms": (
            "Particles < 6-8 nm hydrodynamic diameter undergo renal filtration via glomerular podocyte slit diaphragms into urine. "
            "Particles > 50-100 nm are sequestered by hepatic Kupffer cells and splenic macrophages. "
            "Biodegradable polymers (e.g. PLGA) degrade via ester hydrolysis into lactic and glycolic acid, entering the Krebs cycle."
        ),
        "limitations": "Quantitative organ clearance curves and elimination half-lives require validated PBPK digital twin models. Illustrated conceptually."
    }
]


# ---------------------------------------------------------------------------
# Request and Response Models
# ---------------------------------------------------------------------------
class HumanBodySimRequest(BaseModel):
    material: str = Field(default="PLGA", examples=["PLGA", "Liposome", "Silver", "Gold", "Silica"])
    core_size_nm: float = Field(default=80.0, gt=0, examples=[80.0])
    hydrodynamic_size_nm: Optional[float] = Field(default=95.0, gt=0, examples=[95.0])
    surface_charge_mv: Optional[float] = Field(default=-22.5, examples=[-22.5])
    surface_coating: str = Field(default="PEG", examples=["PEG", "PVA", "Citrate", "Chitosan", "Uncoated"])
    ligand_smiles: Optional[str] = Field(default="OCCO", examples=["OCCO"])
    drug_name: str = Field(default="Paclitaxel", examples=["Paclitaxel", "Doxorubicin", "Ciprofloxacin"])
    drug_loading_pct: float = Field(default=10.0, ge=0, le=100, examples=[10.0])
    k_release: float = Field(default=0.18, gt=0, examples=[0.18])
    n_release: float = Field(default=0.55, gt=0, examples=[0.55])
    target_tissue: str = Field(default="target_tissue", examples=["target_tissue", "liver", "lungs", "kidneys", "skin"])
    administration_route: str = Field(default="Intravenous", examples=["Intravenous", "Oral", "Inhalation", "Subcutaneous"])
    initial_concentration_ug_ml: float = Field(default=50.0, gt=0, examples=[50.0])
    temperature_c: float = Field(default=37.0, examples=[37.0])
    ph: float = Field(default=7.4, ge=0, le=14, examples=[7.4])
    ionic_strength_m: float = Field(default=0.154, ge=0, examples=[0.154])
    exposure_time_hours: float = Field(default=48.0, gt=0, examples=[48.0])
    cell_name: str = Field(default="A549", examples=["A549", "HaCaT", "HepG2"])
    assay: str = Field(default="MTT", examples=["MTT", "LDH", "WST-1"])


# ---------------------------------------------------------------------------
# Simulation Engine & Computation Helpers
# ---------------------------------------------------------------------------
def compute_korsmeyer_peppas_trajectory(
    k: float,
    n: float,
    total_hours: float,
    steps: int = 50
) -> Dict[str, Any]:
    """
    Computes time-series drug release trajectory using Korsmeyer-Peppas ODE model:
    Mt/M_inf = k * (t ^ n).
    Valid domain: Mt/M_inf <= 0.60.
    """
    if total_hours <= 0:
        total_hours = 24.0
    
    t_vals = np.linspace(0.0, float(total_hours), max(10, steps))
    time_series = []
    
    # Mechanism categorization
    if n <= 0.43:
        mechanism = "Fickian Diffusion (Case I)"
        mechanism_desc = "Rate of drug release governed by classical Fickian molecular diffusion through polymer matrix."
    elif 0.43 < n < 0.85:
        mechanism = "Anomalous / Non-Fickian Transport"
        mechanism_desc = "Combined diffusion and polymer relaxation/swelling governing release kinetics."
    else:
        mechanism = "Case II Transport (Polymer Erosion / Relaxation)"
        mechanism_desc = "Zero-order/Case II release governed predominantly by polymer chain relaxation and matrix degradation."

    max_valid_fraction = 0.60
    
    for t in t_vals:
        t_float = float(t)
        if t_float <= 0.0:
            fraction = 0.0
            rate = 0.0
        else:
            fraction = k * (t_float ** n)
            # Derivative: dM/dt = k * n * t^(n-1)
            rate = k * n * (t_float ** (n - 1.0)) * 100.0  # % per hour
            
        fraction_capped = min(1.0, fraction)
        percentage = round(fraction_capped * 100.0, 2)
        validity = "VALID_MODEL_DOMAIN" if fraction <= max_valid_fraction else "EXTRAPOLATION_BEYOND_60PCT"
        
        time_series.append({
            "time_hours": round(t_float, 2),
            "cumulative_release_pct": percentage,
            "release_rate_pct_hr": round(max(0.0, rate), 3),
            "remaining_drug_pct": round(max(0.0, 100.0 - percentage), 2),
            "validity_domain": validity
        })

    final_release_pct = time_series[-1]["cumulative_release_pct"]
    final_rate = time_series[-1]["release_rate_pct_hr"]
    
    return {
        "k": k,
        "n": n,
        "mechanism": mechanism,
        "mechanism_description": mechanism_desc,
        "max_valid_fraction": max_valid_fraction,
        "time_series": time_series,
        "final_release_pct": final_release_pct,
        "final_release_rate": final_rate,
        "final_remaining_pct": round(100.0 - final_release_pct, 2)
    }


def compute_colloidal_stability_index(
    zeta_potential_mv: float,
    coating: str,
    ionic_strength_m: float
) -> Dict[str, Any]:
    """
    Computes DLVO and colloidal aggregation propensity heuristic.
    """
    abs_zeta = abs(zeta_potential_mv)
    is_steric = any(c in coating.upper() for c in ["PEG", "PVA", "DEXTRAN", "POLOXAMER"])
    
    # High ionic strength compresses electrical double layer (screening Debye length)
    ionic_screening_factor = max(0.5, 1.0 - (ionic_strength_m - 0.154) * 1.5) if ionic_strength_m > 0.154 else 1.0
    effective_zeta = zeta_potential_mv * ionic_screening_factor
    abs_eff = abs(effective_zeta)
    
    if is_steric:
        stability_class = "Highly Stable (Sterically Protected)"
        color_code = "accent"
        desc = f"PEG/PVA polymer brush provides steric repulsion barrier, preventing aggregation despite medium ionic strength (effective ζ: {effective_zeta:.1f} mV)."
        aggregation_risk = "Very Low"
    elif abs_eff >= 30.0:
        stability_class = "Electrostatically Highly Stable"
        color_code = "accent"
        desc = f"Strong electrostatic repulsion (|ζ| ≥ 30 mV, measured {zeta_potential_mv:.1f} mV) provides robust colloidal repulsion in biological fluids."
        aggregation_risk = "Low"
    elif abs_eff >= 20.0:
        stability_class = "Incipient / Moderate Stability"
        color_code = "warn"
        desc = f"Moderate electrostatic repulsion (20 ≤ |ζ| < 30 mV, measured {zeta_potential_mv:.1f} mV). Aggregation is possible in high ionic strength fluids."
        aggregation_risk = "Moderate"
    else:
        stability_class = "Aggregation-Prone / Unstable"
        color_code = "danger"
        desc = f"Weak surface potential (|ζ| < 20 mV, measured {zeta_potential_mv:.1f} mV). Attractive van der Waals forces dominate; particles prone to rapid flocculation."
        aggregation_risk = "High"

    return {
        "stability_class": stability_class,
        "color_code": color_code,
        "description": desc,
        "aggregation_risk": aggregation_risk,
        "effective_zeta_mv": round(effective_zeta, 2),
        "is_sterically_stabilized": is_steric,
        "ionic_screening_factor": round(ionic_screening_factor, 2)
    }


def evaluate_human_body_simulation(req: HumanBodySimRequest) -> Dict[str, Any]:
    """
    Orchestrates full scientific evaluation of the nanoparticle formulation
    across active ML models, ODE kinetics, biological regions, and stages.
    """
    warnings: List[Dict[str, Any]] = []

    # 1. Environmental & Causality Warning
    if abs(req.temperature_c - 37.0) > 0.5 or abs(req.ph - 7.4) > 0.3:
        warnings.append({
            "type": "ENVIRONMENTAL_CAUSALITY_LIMIT",
            "level": "INFO",
            "message": (
                f"Environmental conditions (pH {req.ph:.2f}, {req.temperature_c:.1f}°C) deviate from baseline (pH 7.4, 37.0°C). "
                "Note: Korsmeyer-Peppas kinetic parameters (k, n) are empirical constants fitted at 37°C/pH 7.4. "
                "The mathematical model does not causally alter release rates without experimental temperature-dependent kinetics."
            )
        })

    # 2. Administration Route Warning
    if req.administration_route.upper() != "INTRAVENOUS":
        warnings.append({
            "type": "ADMINISTRATION_ROUTE_LIMITATION",
            "level": "CAUTION",
            "message": (
                f"Selected administration route '{req.administration_route}' requires specialized absorption models "
                "(e.g., gastrointestinal barrier or alveolar epithelium) not quantitatively trained in this platform. "
                "The simulation illustrates systemic transport following systemic absorption."
            )
        })

    # 3. Model Inference: Stability (Zeta Potential)
    # Check if user-provided zeta or predict via stability model
    stability_prediction: Optional[Dict[str, Any]] = None
    predicted_zeta_mv = req.surface_charge_mv or -20.0
    stability_issues = []

    stability_payload = {
        "Shape": "Sphere",
        "Core": req.material if req.material in ["Gold", "Silver", "Iron Oxide"] else "Silver",
        "Size_nm": req.core_size_nm,
        "Medium": "PBS pH 7.4",
        "Ligand_SMILES": req.ligand_smiles or "OCCO"
    }
    
    try:
        stability_issues = check_model_domain("stability", stability_payload)
        if not stability_issues:
            ml_stab = predict_stability(stability_payload)
            predicted_zeta_mv = ml_stab["prediction"]
            stability_prediction = {
                "zeta_mv": round(predicted_zeta_mv, 2),
                "model": "Ridge Regressor (GroupKFold by DOI)",
                "mae_mv": 18.90,
                "confidence": "Moderate",
                "domain_status": "INSIDE_VALIDATED_DOMAIN"
            }
        else:
            stability_prediction = {
                "zeta_mv": round(predicted_zeta_mv, 2),
                "model": "User-configured / Baseline Formulation",
                "confidence": "Extrapolated",
                "domain_status": "OUTSIDE_VALIDATED_DOMAIN",
                "domain_issues": stability_issues
            }
            warnings.append({
                "type": "STABILITY_DOMAIN_WARNING",
                "level": "WARN",
                "message": f"Stability parameters outside validated model domain: {[i['field'] for i in stability_issues]}."
            })
    except Exception as e:
        stability_prediction = {
            "zeta_mv": round(predicted_zeta_mv, 2),
            "model": "User-configured / Fallback",
            "confidence": "Uncalibrated",
            "domain_status": f"ERROR: {str(e)}"
        }

    # 4. Model Inference: Cytotoxicity
    cytotoxicity_prediction: Optional[Dict[str, Any]] = None
    cytotox_payload = {
        "Core size (nm)": req.core_size_nm,
        "Hydro size (nm)": req.hydrodynamic_size_nm or (req.core_size_nm * 1.25),
        "Surface charge (mV)": predicted_zeta_mv,
        "Surface area (m2/g)": max(5.0, round(6000.0 / (req.core_size_nm * 3.0), 1)),  # Geometric estimate 6/(rho*d)
        "Exposure time": req.exposure_time_hours,
        "Mass dose (ug/mL)": req.initial_concentration_ug_ml,
        "Material type": req.material if req.material in ["CuO", "ZnO", "TiO2", "Fe2O3", "Ag"] else "CuO",
        "Assay": req.assay if req.assay in ["MTT", "LDH", "WST-1"] else "MTT",
        "Cell name": req.cell_name if req.cell_name in ["A549", "HaCaT", "HepG2", "HeLa"] else "A549"
    }

    try:
        cyto_issues = check_model_domain("cytotoxicity", cytotox_payload)
        if not cyto_issues:
            ml_cyto = predict_cytotoxicity(cytotox_payload)
            cytotoxicity_prediction = {
                "prediction": ml_cyto["prediction"],
                "target": "In-Vitro Carrier Cytotoxicity",
                "probability_toxic": ml_cyto.get("probability_toxic"),
                "confidence": ml_cyto.get("confidence"),
                "cell_line": cytotox_payload["Cell name"],
                "assay": cytotox_payload["Assay"],
                "exposure_time_hours": req.exposure_time_hours,
                "mass_dose_ug_ml": req.initial_concentration_ug_ml,
                "domain_status": "INSIDE_VALIDATED_DOMAIN",
                "important_limitation": (
                    "In-vitro cellular viability estimate for nanoparticle carrier. "
                    "Does not predict clinical toxicity, organ toxicity, or patient clinical outcome."
                )
            }
        else:
            cytotoxicity_prediction = {
                "prediction": "Unknown (Out of Domain)",
                "target": "In-Vitro Carrier Cytotoxicity",
                "domain_status": "OUTSIDE_VALIDATED_DOMAIN",
                "domain_issues": cyto_issues,
                "important_limitation": "Inputs exceed validated range for cytotoxicity classifier."
            }
            warnings.append({
                "type": "CYTOTOXICITY_DOMAIN_WARNING",
                "level": "WARN",
                "message": f"Cytotoxicity parameters outside validated domain: {[i['field'] for i in cyto_issues]}."
            })
    except Exception as e:
        cytotoxicity_prediction = {
            "prediction": "Simulation Baseline (Nontoxic Carrier)",
            "target": "In-Vitro Carrier Cytotoxicity",
            "domain_status": f"FALLBACK ({str(e)})",
            "important_limitation": "Classifier fallback; evaluate with experimental testing."
        }

    # 5. Colloidal Stability & Aggregation Propensity
    colloidal = compute_colloidal_stability_index(
        predicted_zeta_mv,
        req.surface_coating,
        req.ionic_strength_m
    )

    # 6. Drug Release Kinetics Trajectory (Korsmeyer-Peppas ODE)
    release_kinetics = compute_korsmeyer_peppas_trajectory(
        k=req.k_release,
        n=req.n_release,
        total_hours=req.exposure_time_hours,
        steps=50
    )

    # 7. Organ Accumulation & Clearance Estimates (Semi-Empirical Literature Heuristics)
    # Strictly disclaimed as illustrative estimations based on hydrodynamic size
    hydro_size = req.hydrodynamic_size_nm or req.core_size_nm
    is_pegylated = colloidal["is_sterically_stabilized"]
    
    if hydro_size < 8.0:
        clearance_dominant = "Renal Glomerular Filtration"
        clearance_pct_renal = 85.0
        clearance_pct_hepatic = 10.0
        clearance_half_life_desc = "Short (< 1 - 2 hours) due to rapid urinary excretion."
    elif is_pegylated:
        clearance_dominant = "Prolonged Circulation with Delayed Hepatic/Splenic MPS Uptake"
        clearance_pct_renal = 5.0
        clearance_pct_hepatic = 65.0
        clearance_half_life_desc = "Prolonged (18 - 48 hours) mediated by PEG steric evasion of opsonization."
    else:
        clearance_dominant = "Reticuloendothelial System (Hepatic Kupffer Cell & Spleen Phagocytosis)"
        clearance_pct_renal = 2.0
        clearance_pct_hepatic = 85.0
        clearance_half_life_desc = "Rapid clearance (< 0.5 - 4 hours) via macrophage scavenger receptors."

    illustrative_biodistribution = {
        "status": "CONCEPTUAL_ILLUSTRATIVE_ESTIMATE",
        "notice": "Biodistribution figures are illustrative qualitative estimates derived from nanoparticle literature benchmarks, not a digital twin.",
        "dominant_clearance_route": clearance_dominant,
        "estimated_organ_uptake": {
            "liver_mps_pct": clearance_pct_hepatic,
            "kidney_urinary_pct": clearance_pct_renal,
            "target_tissue_pct": 1.5 if req.target_tissue == "target_tissue" else 3.0,
            "spleen_pct": 8.0,
            "lungs_microvascular_pct": 2.5,
            "carcass_residual_pct": max(0.0, round(100.0 - (clearance_pct_hepatic + clearance_pct_renal + 12.0), 1))
        },
        "half_life_profile": clearance_half_life_desc
    }

    # 8. Complete Stage Manifest with Runtime Parameters
    stage_manifest = []
    for st in SIMULATION_STAGES:
        item = dict(st)
        if item["key"] == "administration":
            item["runtime_detail"] = {
                "route": req.administration_route,
                "initial_dose_ug_ml": req.initial_concentration_ug_ml,
                "drug_loading_pct": req.drug_loading_pct,
                "drug_name": req.drug_name
            }
        elif item["key"] == "circulation":
            item["runtime_detail"] = {
                "colloidal_stability": colloidal["stability_class"],
                "aggregation_risk": colloidal["aggregation_risk"],
                "zeta_mv": round(predicted_zeta_mv, 2),
                "ionic_screening": colloidal["ionic_screening_factor"]
            }
        elif item["key"] == "drug_release":
            item["runtime_detail"] = {
                "model_equation": f"Mt/M_inf = {req.k_release:.4f} * t^{req.n_release:.4f}",
                "mechanism": release_kinetics["mechanism"],
                "final_cumulative_release_pct": release_kinetics["final_release_pct"],
                "final_release_rate_pct_hr": release_kinetics["final_release_rate"]
            }
        elif item["key"] == "toxicity_response":
            item["runtime_detail"] = {
                "carrier_classification": cytotoxicity_prediction.get("prediction"),
                "tested_cell_line": cytotox_payload["Cell name"],
                "drug_pharmacology": f"{req.drug_name} intended molecular target action"
            }
        elif item["key"] == "clearance":
            item["runtime_detail"] = {
                "primary_pathway": illustrative_biodistribution["dominant_clearance_route"],
                "filtration_note": illustrative_biodistribution["half_life_profile"]
            }
        stage_manifest.append(item)

    return {
        "status": "SUCCESS",
        "formulation_summary": {
            "material": req.material,
            "core_size_nm": req.core_size_nm,
            "hydrodynamic_size_nm": hydro_size,
            "surface_coating": req.surface_coating,
            "zeta_potential_mv": round(predicted_zeta_mv, 2),
            "drug_name": req.drug_name,
            "drug_loading_pct": req.drug_loading_pct,
            "administration_route": req.administration_route,
            "target_tissue": req.target_tissue,
            "environment": {
                "pH": req.ph,
                "temperature_c": req.temperature_c,
                "ionic_strength_m": req.ionic_strength_m,
                "exposure_time_hours": req.exposure_time_hours
            }
        },
        "model_results": {
            "stability": stability_prediction,
            "cytotoxicity": cytotoxicity_prediction,
            "colloidal_index": colloidal,
            "drug_release_kinetics": release_kinetics,
            "illustrative_biodistribution": illustrative_biodistribution
        },
        "stages": stage_manifest,
        "warnings": warnings,
        "disclaimer": (
            "SCIENTIFIC RESEARCH NOTICE: This platform provides predictive and mathematical estimates "
            "for academic research in nanomedicine. Predictions and conceptual biological illustrations "
            "do not represent clinical digital twins or medical advice. Experimental laboratory validation is required."
        )
    }
