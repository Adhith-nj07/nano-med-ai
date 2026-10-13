# Human Body Interaction & Nanomedicine Simulation Specification

## 1. Overview & Objective
The **Human Body Interaction Simulator** integrates into NanoMedAI as an interactive, multi-scale 3D biophysical journey model. It visualizes and simulates how drug-loaded nanoparticles navigate systemic circulation, vascular microenvironments, and intracellular pathways inside the human body.

---

## 2. Scientific Triad: Predictions vs. Simulations vs. Illustrations

| Triad Level | Modules & Endpoints | Model Type / Mathematical Foundation | Validation Status & Domain Limits |
| :--- | :--- | :--- | :--- |
| **Quantitative ML Inference** | • Surface Zeta Potential (`/api/predict/stability`)<br>• In-Vitro Cytotoxicity (`/api/predict/cytotoxicity`) | • Ridge Regressor (GroupKFold by DOI, R²=0.84, MAE=18.9 mV)<br>• Random Forest Classifier (ROC-AUC=0.91) | Active serialized models. Strict input range boundaries enforced. |
| **Mathematical Kinetics Simulation** | • Drug Release Trajectory (`/api/human_body_sim/evaluate`) | • Korsmeyer-Peppas Power-Law ODE: $M_t / M_\infty = k \cdot t^n$<br>• Instantaneous rate: $dM_t/dt = k \cdot n \cdot t^{n-1}$ | Valid strictly up to $M_t/M_\infty \le 0.60$ (60% cumulative release). Empirical rate constants fitted at 37°C/pH 7.4. |
| **Conceptual Biological Illustration** | • Protein Corona Formation (Stage 3)<br>• Tissue Extravasation & EPR (Stage 4)<br>• 5-Step Endocytic Uptake (Stage 5)<br>• Organ-Level Clearance (Stage 8) | • Multi-scale 3D Three.js animation based on literature benchmarks | No quantitative predictive twin. Labeled strictly as conceptual qualitative visualizations. |

---

## 3. The 8-Stage Nanomedicine Journey

### Stage 1: Administration & Introduction
- **Mechanisms:** Intravenous (IV) bolus or infusion introduces nanoparticles into systemic circulation (median ~5 L blood volume). Rapid ~1:1000 dilution within 1-2 minutes.
- **Classification:** `[ESTABLISHED BIOPHYSICAL PROTOCOL]`.

### Stage 2: Bloodstream Circulation & Hemodynamics
- **Mechanisms:** Nanoparticles travel via laminar flow, collide with erythrocytes, and marginate toward the endothelial wall. Colloidal stability evaluated via DLVO electrostatic energy barrier ($|\zeta| \ge 30\text{ mV}$ is stable) and steric polymer brushes (PEG/PVA).
- **Classification:** `[PREDICTED STABILITY & FLUID DYNAMICS]`.

### Stage 3: Protein Corona Formation
- **Mechanisms:** Adsorption of plasma proteins (albumin, fibrinogen, apolipoproteins, IgG) forming hard and soft biomolecular coronas, altering biological identity.
- **Classification:** `[CONCEPTUAL BIOLOGICAL ILLUSTRATION]` *(Explicit notice: No quantitative corona model active)*.

### Stage 4: Target Tissue Interaction & Extravasation
- **Mechanisms:** Passive extravasation through hyperpermeable tumor vessels (EPR effect). Penetration hindered by elevated interstitial fluid pressure (IFP) and dense collagen-hyaluronan matrix.
- **Integrity Notice:** Targeting is NOT guaranteed; median delivery efficiency in clinical literature is <1-2% of injected dose.

### Stage 5: Cellular Uptake (5-Step Endocytosis)
1. **Approach:** Nanoparticle diffuses toward plasma membrane.
2. **Contact:** Electrostatic engagement with negative glycocalyx or receptor binding.
3. **Invagination:** Clathrin/caveolae-coated pit or macropinocytic fold forms.
4. **Vesicle Formation:** Internalization into early endosome (pH ~6.2).
5. **Trafficking & Release:** Endosomal acidification (pH 5.0 in lysosome) prompts drug escape or enzymatic matrix digestion.
- **Classification:** `[CONCEPTUAL BIOLOGICAL ILLUSTRATION]`.

### Stage 6: Drug Release Kinetics
- **Mechanisms:** Evaluated using the Korsmeyer-Peppas ODE model ($M_t / M_\infty = k \cdot t^n$).
  - $n \le 0.43$: Fickian diffusion (Case I).
  - $0.43 < n < 0.85$: Anomalous non-Fickian transport.
  - $n \ge 0.85$: Case II polymer relaxation/erosion.
- **Classification:** `[MATHEMATICAL SIMULATION - KORSMEYER-PEPPAS ODE]`.

### Stage 7: Biological Response & Cytotoxicity
- **Mechanisms:** Random forest carrier cytotoxicity screening vs intended therapeutic pharmacological effect.
- **Classification:** `[ACTIVE ML PREDICTION]`.
- **Limitation:** Research in-vitro assay screening; does not predict human patient safety.

### Stage 8: Clearance, Metabolism & Elimination
- **Mechanisms:** Renal glomerular filtration for sub-8 nm particles; hepatic Kupffer cell & splenic macrophage phagocytosis for particles > 50-100 nm.
- **Classification:** `[CONCEPTUAL BIOLOGICAL ILLUSTRATION]`.

---

## 4. Selectable Biological Regions Knowledge Base

1. **Bloodstream:** Shear rates $100 - 2000\text{ s}^{-1}$, whole blood rheology, erythrocyte collision-induced margination.
2. **Liver:** Hepatic sinusoids, 100-150 nm fenestrations, Space of Disse, Kupffer cell phagocytosis.
3. **Kidneys:** Glomerular filtration cutoff 6.0 - 8.0 nm, podocyte slit diaphragms, rapid urinary elimination.
4. **Lungs:** Pulmonary capillary diameter 5-8 µm, microembolism risk if aggregation exceeds 5 µm.
5. **Skin:** Stratum corneum size exclusion (<500 Da, <10 nm intact particle limit), dermal capillary bed.
6. **Target Tissue:** Tumor microenvironment, 100-800 nm vascular fenestrations, high IFP barrier.
7. **Cellular Environment:** Glycocalyx negative potential, clathrin/caveolae endocytosis, lysosomal acidification.

---

## 5. API Endpoints

- `GET /api/human_body_sim/regions`: Returns complete anatomical and biophysical profiles for the 7 biological regions.
- `GET /api/human_body_sim/stages`: Returns stage metadata, mechanisms, badges, and integrity levels.
- `POST /api/human_body_sim/evaluate`: Evaluates formulation across ML models, computes Korsmeyer-Peppas ODE trajectory, DLVO colloidal index, and generates domain boundary warnings.
