/**
 * NanoMedAI — Demonstration Trajectories & Datasets
 * Scientifically structured reference trajectories, heatmap grids, and dataset records.
 */

window.NMI_TRAJECTORIES = {
  // Time points (hours)
  timePointsHours: [0, 1, 2, 4, 6, 8, 12, 16, 24, 32, 40, 48, 60, 72],
  
  // Korsmeyer-Peppas Simulated Trajectory (PLGA-PEG / DOX)
  // n = 0.45 (Fickian diffusion from sphere), K = 0.082 h^-n
  simulatedReleasePct: [0.0, 8.2, 11.2, 15.4, 18.5, 21.0, 25.2, 28.8, 34.2, 38.6, 42.4, 45.8, 50.2, 54.0],

  // Experimental Reference Curve (In Vitro Dissolution in PBS pH 7.4 at 37°C)
  experimentalReleasePct: [0.0, 9.5, 12.8, 16.9, 19.8, 22.5, 26.9, 30.5, 36.0, 40.2, 44.1, 47.5, 52.0, 55.8],

  // Validation boundary threshold index: up to index 11 (48h / 45.8%) is MODEL VALID REGION; index 12+ (60h..72h) is EXTRAPOLATION
  validityBoundaryIndex: 11,
  
  // Heatmap Data Grid: pH vs Temperature (°C) -> Zeta Potential (mV) & Stability Class
  heatmap: {
    phRange: [4.0, 5.0, 6.0, 7.0, 7.4, 8.0, 9.0],
    tempRange: [20.0, 25.0, 30.0, 37.0, 42.0, 45.0],
    
    // Matrix [temp_idx][ph_idx]
    grid: [
      // Temp 20°C
      [
        { ph: 4.0, temp: 20, zeta: -5.2, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 5.0, temp: 20, zeta: -12.4, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 6.0, temp: 20, zeta: -18.8, rating: "Medium", status: "Moderately Stable", color: "#f59e0b" },
        { ph: 7.0, temp: 20, zeta: -25.6, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 7.4, temp: 20, zeta: -27.1, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 8.0, temp: 20, zeta: -29.5, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 9.0, temp: 20, zeta: -32.8, rating: "High", status: "Highly Stable", color: "#10b981" }
      ],
      // Temp 25°C
      [
        { ph: 4.0, temp: 25, zeta: -6.0, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 5.0, temp: 25, zeta: -13.1, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 6.0, temp: 25, zeta: -19.4, rating: "Medium", status: "Moderately Stable", color: "#f59e0b" },
        { ph: 7.0, temp: 25, zeta: -26.2, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 7.4, temp: 25, zeta: -27.8, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 8.0, temp: 25, zeta: -30.1, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 9.0, temp: 25, zeta: -33.5, rating: "High", status: "Highly Stable", color: "#10b981" }
      ],
      // Temp 30°C
      [
        { ph: 4.0, temp: 30, zeta: -6.8, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 5.0, temp: 30, zeta: -13.9, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 6.0, temp: 30, zeta: -20.2, rating: "High", status: "Moderately Stable", color: "#10b981" },
        { ph: 7.0, temp: 30, zeta: -27.0, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 7.4, temp: 30, zeta: -28.5, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 8.0, temp: 30, zeta: -30.9, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 9.0, temp: 30, zeta: -34.2, rating: "High", status: "Highly Stable", color: "#10b981" }
      ],
      // Temp 37°C (Physiological Body Temp)
      [
        { ph: 4.0, temp: 37, zeta: -7.9, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 5.0, temp: 37, zeta: -14.8, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 6.0, temp: 37, zeta: -21.1, rating: "High", status: "Moderately Stable", color: "#10b981" },
        { ph: 7.0, temp: 37, zeta: -27.9, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 7.4, temp: 37, zeta: -29.4, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 8.0, temp: 37, zeta: -31.8, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 9.0, temp: 37, zeta: -35.1, rating: "High", status: "Highly Stable", color: "#10b981" }
      ],
      // Temp 42°C (Hyperthermic Condition)
      [
        { ph: 4.0, temp: 42, zeta: -8.7, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 5.0, temp: 42, zeta: -15.6, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 6.0, temp: 42, zeta: -21.9, rating: "High", status: "Moderately Stable", color: "#10b981" },
        { ph: 7.0, temp: 42, zeta: -28.7, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 7.4, temp: 42, zeta: -30.2, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 8.0, temp: 42, zeta: -32.6, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 9.0, temp: 42, zeta: -36.0, rating: "High", status: "Highly Stable", color: "#10b981" }
      ],
      // Temp 45°C (Thermal Stress)
      [
        { ph: 4.0, temp: 45, zeta: -9.2, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 5.0, temp: 45, zeta: -16.1, rating: "Low", status: "Unstable / Aggregation-Prone", color: "#ef4444" },
        { ph: 6.0, temp: 45, zeta: -22.4, rating: "High", status: "Moderately Stable", color: "#10b981" },
        { ph: 7.0, temp: 45, zeta: -29.2, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 7.4, temp: 45, zeta: -30.7, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 8.0, temp: 45, zeta: -33.1, rating: "High", status: "Electrostatically Stable", color: "#10b981" },
        { ph: 9.0, temp: 45, zeta: -36.5, rating: "High", status: "Highly Stable", color: "#10b981" }
      ]
    ]
  },

  // Research Datasets
  datasets: [
    {
      id: "DS-NANO-ZETA-288",
      name: "Harmonized Nanoparticle Zeta Potential Benchmark",
      source: "ACS Nano / Nanoscale Open Data Consortium",
      doi: "10.1021/acs.nanolett.demo101",
      recordsCount: 288,
      studiesCount: 42,
      variables: "Core material, Core size (nm), Hydrodynamic size (nm), Shape, Ligand SMILES, Medium pH, Ionic Strength, Zeta Potential (mV)",
      targetVariable: "Zeta Potential (mV)",
      experimentalConditions: "DLS / Electrophoretic Light Scattering (ELS) at 25°C & 37°C",
      dataQualityScore: "98.2%",
      missingValuesPct: "0.4%",
      trainingStatus: "Model Trained & Validated (GroupKFold by DOI)"
    },
    {
      id: "DS-CYTO-NANO-1420",
      name: "In Vitro Nanoparticle Cytotoxicity Meta-Dataset",
      source: "Zenodo / Nanotoxicology Literature Curation",
      doi: "10.5281/zenodo.15300193",
      recordsCount: 1420,
      studiesCount: 118,
      variables: "Core size (nm), Hydro size (nm), Surface charge (mV), Surface area (m2/g), Exposure time (h), Mass dose (ug/mL), Material type, Assay type, Cell line",
      targetVariable: "Viability (< 70% = Toxic)",
      experimentalConditions: "MTT, WST-1, LDH, CellTiter-Glo Assays across human/murine cell lines",
      dataQualityScore: "95.6%",
      missingValuesPct: "1.2%",
      trainingStatus: "Model Trained & Validated (GroupKFold by PubMed ID)"
    },
    {
      id: "DS-RELEASE-PLGA-64",
      name: "Polymeric Nanoparticle In Vitro Dissolution Archive",
      source: "Journal of Controlled Release / Pharmaceutics Archive",
      doi: "10.1016/j.jconrel.demo2024",
      recordsCount: 64,
      studiesCount: 16,
      variables: "Polymer MW, LA/GA ratio, Drug loading %, Core size, Medium pH, Temperature, Cumulative release vs Time",
      targetVariable: "Release Trajectory M(t)/M_inf",
      experimentalConditions: "Dialysis Bag & USP Dissolution Apparatus 4 at 37°C in PBS pH 7.4 / pH 5.5",
      dataQualityScore: "92.0%",
      missingValuesPct: "2.8%",
      trainingStatus: "Validation Baseline for Korsmeyer-Peppas Model"
    }
  ]
};
