/**
 * NanoMedAI — Demonstration Nanoparticle Database
 * Contains realistic nanoparticle configurations, predictions, and metadata.
 */

window.NMI_PARTICLES = [
  {
    id: "NP-AG-04",
    name: "PLGA-PEG Doxorubicin Nanoparticle",
    shortName: "PLGA-PEG/DOX",
    category: "Polymeric Nanoparticle",
    material: "Poly(lactic-co-glycolic acid) - Polyethylene glycol",
    coreMaterial: "PLGA 50:50 (MW ~30-45 kDa)",
    coating: "PEG 2000 Da (Steric Shield)",
    ligand: "Folate (FA-PEG)",
    ligandSmiles: "C1=CC(=CC=C1C(=O)NC(CCC(=O)O)C(=O)O)NCC2=CN=C3C(=N2)C(=O)NC(=N3)N",
    drug: "Doxorubicin Hydrochloride",
    drugLoadingPct: 8.5,
    drugMwDa: 543.52,
    polymerMwkDa: 45.0,
    laGaRatio: "50:50",
    
    // Physical Properties
    coreSizeNm: 45.0,
    hydroSizeNm: 68.5,
    shape: "Sphere",
    pdi: 0.12,
    surfaceAreaM2g: 52.4,
    zetaPotentialMv: -24.8,
    
    // Chemical Properties
    surfaceCharge: "Anionic",
    ligandChemistry: "Amide linkage via NHS-PEG-Maleimide",
    particleMwDa: 45000.0,
    composition: "PLGA (75%), PEG (15.5%), Doxorubicin (8.5%), Folate (1.0%)",
    solvent: "Water / 10 mM PBS pH 7.4",
    
    // ML Model Predictions
    predictions: {
      zetaPotential: {
        valueMv: -24.8,
        unit: "mV",
        uncertaintyMv: 2.1,
        stabilityClass: "Moderately Stable",
        stabilityColor: "success",
        inTrainingDomain: true,
        domainCoveragePct: 94.2,
        modelType: "Ridge Regressor + SMILES RDKit Features",
        datasetSize: "288 harmonized nanoparticles",
        validationDoi: "10.1021/acs.nanolett.demo101"
      },
      cytotoxicity: {
        result: "Nontoxic",
        isToxic: false,
        toxicProbability: 0.14,
        confidencePct: 86.0,
        riskLevel: "Low Risk",
        cellModel: "A549 (Human Lung Carcinoma)",
        assay: "MTT",
        exposureTimeHours: 24,
        massDoseUgMl: 50.0,
        inTrainingDomain: true,
        modelType: "Random Forest Classifier",
        datasetSize: "1,420 nano-assay data points",
        validationDoi: "10.5281/zenodo.15300193"
      }
    },
    
    // Status
    screeningStatus: "Shortlisted",
    compatibilityScore: 92
  },
  {
    id: "NP-AG-09",
    name: "Citrate-Capped Gold Nanoparticle",
    shortName: "AuNP-Citrate",
    category: "Inorganic Core",
    material: "Colloidal Gold Core + Citrate Ligands",
    coreMaterial: "Metallic Gold (Au0)",
    coating: "Trisodium Citrate Dihydrate",
    ligand: "Citrate",
    ligandSmiles: "C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O",
    drug: "None (Diagnostic/Thermal)",
    drugLoadingPct: 0.0,
    drugMwDa: 0.0,
    polymerMwkDa: 0.0,
    laGaRatio: "N/A",
    
    // Physical Properties
    coreSizeNm: 15.0,
    hydroSizeNm: 18.2,
    shape: "Sphere",
    pdi: 0.08,
    surfaceAreaM2g: 22.1,
    zetaPotentialMv: -38.2,
    
    // Chemical Properties
    surfaceCharge: "Strongly Anionic",
    ligandChemistry: "Electrostatic Adsorption",
    particleMwDa: 196.97,
    composition: "Gold Core (98%), Citrate Shell (2%)",
    solvent: "Ultrapure Water",
    
    // ML Model Predictions
    predictions: {
      zetaPotential: {
        valueMv: -38.2,
        unit: "mV",
        uncertaintyMv: 1.5,
        stabilityClass: "Highly Stable",
        stabilityColor: "success",
        inTrainingDomain: true,
        domainCoveragePct: 98.5,
        modelType: "Ridge Regressor + SMILES RDKit Features",
        datasetSize: "288 harmonized nanoparticles",
        validationDoi: "10.1021/acs.nanolett.demo101"
      },
      cytotoxicity: {
        result: "Nontoxic",
        isToxic: false,
        toxicProbability: 0.22,
        confidencePct: 78.0,
        riskLevel: "Low Risk",
        cellModel: "HeLa (Cervical Cancer)",
        assay: "WST-1",
        exposureTimeHours: 48,
        massDoseUgMl: 20.0,
        inTrainingDomain: true,
        modelType: "Random Forest Classifier",
        datasetSize: "1,420 nano-assay data points",
        validationDoi: "10.5281/zenodo.15300193"
      }
    },
    
    // Status
    screeningStatus: "Model Compatible",
    compatibilityScore: 84
  },
  {
    id: "NP-AG-14",
    name: "Copper Oxide Nanoparticle (Pristine)",
    shortName: "CuO-Pristine",
    category: "Metal Oxide",
    material: "Copper Oxide Core",
    coreMaterial: "Tenorite CuO",
    coating: "Uncoated / Hydroxyl Surface",
    ligand: "Hydroxyl (-OH)",
    ligandSmiles: "[OH-]",
    drug: "None",
    drugLoadingPct: 0.0,
    drugMwDa: 0.0,
    polymerMwkDa: 0.0,
    laGaRatio: "N/A",
    
    // Physical Properties
    coreSizeNm: 32.0,
    hydroSizeNm: 85.0,
    shape: "Irregular Sphere",
    pdi: 0.28,
    surfaceAreaM2g: 45.0,
    zetaPotentialMv: -12.4,
    
    // Chemical Properties
    surfaceCharge: "Weakly Anionic",
    ligandChemistry: "Surface Hydroxylation",
    particleMwDa: 79.55,
    composition: "CuO 100%",
    solvent: "PBS pH 7.4",
    
    // ML Model Predictions
    predictions: {
      zetaPotential: {
        valueMv: -12.4,
        unit: "mV",
        uncertaintyMv: 3.8,
        stabilityClass: "Unstable / Aggregation-Prone",
        stabilityColor: "danger",
        inTrainingDomain: true,
        domainCoveragePct: 88.0,
        modelType: "Ridge Regressor + SMILES RDKit Features",
        datasetSize: "288 harmonized nanoparticles",
        validationDoi: "10.1021/acs.nanolett.demo101"
      },
      cytotoxicity: {
        result: "Toxic",
        isToxic: true,
        toxicProbability: 0.88,
        confidencePct: 91.0,
        riskLevel: "High Risk (ROS-induced membrane damage)",
        cellModel: "A549 (Human Lung Carcinoma)",
        assay: "LDH Release",
        exposureTimeHours: 24,
        massDoseUgMl: 100.0,
        inTrainingDomain: true,
        modelType: "Random Forest Classifier",
        datasetSize: "1,420 nano-assay data points",
        validationDoi: "10.5281/zenodo.15300193"
      }
    },
    
    // Status
    screeningStatus: "Rejected (Toxic)",
    compatibilityScore: 31
  },
  {
    id: "NP-AG-22",
    name: "Chitosan-TPP Insulin Nanoparticle",
    shortName: "CS-TPP/Insulin",
    category: "Biopolymer Hydrogel",
    material: "Chitosan - Tripolyphosphate",
    coreMaterial: "Deacetylated Chitosan Hydrogel",
    coating: "Chitosan Surface Chains",
    ligand: "Amino (-NH2)",
    ligandSmiles: "N",
    drug: "Recombinant Human Insulin",
    drugLoadingPct: 14.2,
    drugMwDa: 5808.0,
    polymerMwkDa: 120.0,
    laGaRatio: "N/A",
    
    // Physical Properties
    coreSizeNm: 110.0,
    hydroSizeNm: 145.0,
    shape: "Sphere",
    pdi: 0.18,
    surfaceAreaM2g: 18.5,
    zetaPotentialMv: +31.5,
    
    // Chemical Properties
    surfaceCharge: "Cationic",
    ligandChemistry: "Protonated Amine Surface",
    particleMwDa: 120000.0,
    composition: "Chitosan (75%), TPP (10.8%), Insulin (14.2%)",
    solvent: "0.1 M Acetate Buffer pH 4.5 / Deionized Water",
    
    // ML Model Predictions
    predictions: {
      zetaPotential: {
        valueMv: 31.5,
        unit: "mV",
        uncertaintyMv: 4.2,
        stabilityClass: "Electrostatically Stable",
        stabilityColor: "success",
        inTrainingDomain: false,
        domainCoveragePct: 62.0,
        modelType: "Ridge Regressor (Out-of-Domain Warning: High Cationic Charge)",
        datasetSize: "288 harmonized nanoparticles",
        validationDoi: "10.1021/acs.nanolett.demo101"
      },
      cytotoxicity: {
        result: "Nontoxic",
        isToxic: false,
        toxicProbability: 0.28,
        confidencePct: 74.0,
        riskLevel: "Low-Moderate Risk",
        cellModel: "Caco-2 (Intestinal Epithelium)",
        assay: "MTT",
        exposureTimeHours: 12,
        massDoseUgMl: 250.0,
        inTrainingDomain: true,
        modelType: "Random Forest Classifier",
        datasetSize: "1,420 nano-assay data points",
        validationDoi: "10.5281/zenodo.15300193"
      }
    },
    
    // Status
    screeningStatus: "Experimental Validation Required",
    compatibilityScore: 78
  }
];
