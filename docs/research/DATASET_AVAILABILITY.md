# Dataset Availability

To support the transition to real-data endpoints (Zeta Potential and Cytotoxicity/Cell Viability), public datasets were assessed based on the requirement of immediate, open-access download (no author requests).

## 1. S2NANO / Zenodo Metal Oxide (MeOx) Datasets
- **Source:** Curated subsets from the S2NANO database, frequently hosted on Zenodo (e.g., "HaHa-Auto", "HaHa-Manual", "MeOX I/II/III") and Kaggle (e.g., "ToxicityAssessment_MeOxNP").
- **Endpoints Available:** 
  - Cytotoxicity (Cell viability % and Binary Toxic/Non-Toxic labels).
  - Zeta potential (mV).
- **Features Available:** Core size, Hydrodynamic size, Surface area, Zeta potential, Cell line, Exposure time, Dose/Concentration.
- **Volume:** Thousands of curated rows derived from literature meta-analyses (e.g., 2,000+ instances across multiple MeOx types like ZnO, CuO, TiO2, SiO2).
- **Usability:** EXCELLENT. These are specifically designed for nanoinformatics (QSAR) machine learning tasks.

## 2. eNanoMapper (eNM) Database
- **Source:** EU Observatory for Nanomaterials / NanoSafety Cluster (data.enanomapper.net).
- **Endpoints Available:** Highly granular physicochemical characterization and in vitro toxicity assays (cell viability, cytotoxicity).
- **Features Available:** Extensive, utilizing the eNanoMapper ontology.
- **Usability:** MODERATE TO HIGH. The data is extremely rich and FAIR-compliant, but downloading and parsing the JSON/RDF API formats into a flat CSV suitable for `train_and_export.py` requires significant data wrangling compared to pre-curated Kaggle/Zenodo CSVs.

## 3. Literature-Derived Supplementary CSVs
- **Source:** Supplementary information files from recent ML nanotoxicity papers (e.g., ACS Nano, Nanotoxicology).
- **Endpoints Available:** Cell viability, Zeta potential, Size.
- **Usability:** HIGH. Often pre-cleaned for random forest or neural network training.

## Conclusion
High-quality, publicly downloadable datasets are readily available, particularly for Metal Oxide nanoparticles (via S2NANO/Zenodo/Kaggle). However, these datasets contain features entirely different from the synthetic NanoMedAI schema (e.g., they include Dose, Exposure Time, Cell Line, and Hydrodynamic Size). The NanoMedAI feature schema must be updated to match the reality of these public datasets.
