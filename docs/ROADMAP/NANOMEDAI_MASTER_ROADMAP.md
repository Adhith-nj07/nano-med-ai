# NanoMedAI Master Roadmap

## 1. Current MVP
**Status**: COMPLETE / IN PROGRESS
The current academic MVP provides baseline predictive models (Zeta potential and Cytotoxicity) rigorously validated using GroupKFold to prevent laboratory leakage.

## 2. Current Implemented Features
- Real dataset acquisition.
- Stability/zeta-potential prediction (Ridge Regression).
- Cytotoxicity prediction (Random Forest Classification).
- Data provenance and DOI-grouped validation.
- SMILES-derived stability feature extraction (Charge, Estimated MW).
- Serialized ML pipelines and Decoupled Prediction APIs.
- Foundational feature importance.

## 3. Partial Foundations
- Environment: Medium used as a proxy feature.
- Biology: Cell types used in cytotoxicity meta-analysis.
- Exposure: Dose and Time used in cytotoxicity meta-analysis.
- Data Provenance: DOIs tracked and utilized for data splitting.

## 4. Missing Capabilities
Advanced modules required for a comprehensive digital twin are currently missing (by design): Payload, Formulation ratios, Manufacturing processes, Transformation engine, Protein Corona, Temporal dynamics, Image/Spectral modalities, Physics-informed ML, Uncertainty/OOD, and Active Learning frameworks.

## 5. Future Phases
1. Next Extension (Uncertainty, OOD, SHAP, new targets)
2. Research Platform (Drug release, cellular uptake, transformation, corona, counterfactuals)
3. Advanced AI (Multimodal, GNN, physics-informed, Bayesian)
4. Design / Optimization (Multi-objective, active learning)
5. Full Nano Digital Twin (Knowledge graph, Literature AI, relational DB)

## 6. Dependencies Between Phases
- Advanced AI (Level 4) requires the Research Platform (Level 3) schemas and targets to be active.
- Design / Optimization (Level 5) requires Uncertainty (Level 2) and What-If Simulations (Level 3) to function reliably.

## 7. Dataset Requirements
Future phases will require dense, multi-modal datasets (time-series release profiles, TEM images, full corona proteomics) which currently lack large-scale harmonized public availability.

## 8. Model Requirements
The current ML stack (scikit-learn) is sufficient for the MVP. Future phases will require PyTorch/TensorFlow, graph neural networks (e.g., PyG), and Gaussian Process libraries.

## 9. UI Evolution
The MVP UI is restricted to:
- Dashboard
- Zeta Potential Prediction
- Cytotoxicity Prediction
- Model Information

*Do not add advanced UI tabs until the underlying ML backend matures into Level 3+.*

## 10. Research Direction
NanoMedAI's research differentiation lies in the **integration and system-level workflow**—not in claiming standard algorithms (like RF or Ridge) as novel. By rigorously enforcing OOD detection and preventing leakage, NanoMedAI establishes baseline honesty.

## 11. Long-Term Digital-Twin Architecture
**Vision**: An explainable, physics-aware, multimodal nanoparticle digital twin for transformation, nano-bio interaction, prediction, uncertainty estimation, and optimization.
