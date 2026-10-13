/**
 * NanoMedAI — Demo State & Feature Support Registry
 * Scientifically explicit demonstration state & backend boundary definitions.
 */

window.NMI_STATE = {
  isDemo: true,
  demoNotice: "FRONTEND DEMONSTRATION ONLY — NOT CONNECTED TO BACKEND MODEL ENGINE",
  
  activeView: "overview", // overview | builder | environment | prediction | simulation | release | stability | transparency | datasets | screening | comparison | report
  
  // Active selected particle for analysis & simulation
  activeParticleId: "NP-AG-04",
  
  // Simulation Runtime Engine State
  simulation: {
    isRunning: false,
    speedMultiplier: 1.0,
    currentTimeHours: 24.0,
    maxTimeHours: 72.0,
    stepSizeHours: 0.5,
    cumulativeReleasePct: 34.2,
    remainingDrugPct: 65.8,
    releaseRatePctPerHour: 0.85,
    
    // Environment state inside simulation
    environment: {
      temperature_c: 37.0,
      ph: 7.40,
      ionicStrength_M: 0.15,
      buffer: "PBS (Phosphate Buffered Saline)",
      pressure_atm: 1.0,
      viscosity_cP: 0.89,
      ros_uM: 0.0,
      serumConcentration_pct: 10.0
    },
    
    // Timeline events
    events: [
      {
        timeHours: 0.0,
        type: "SIMULATION_START",
        severity: "info",
        trigger: "USER_INIT",
        description: "Simulation initialized for formulation PLGA-PEG / Doxorubicin (NP-AG-04).",
        modelSource: "Korsmeyer-Peppas Engine v1.2",
        uncertainty: "± 2.5%",
        supported: true
      },
      {
        timeHours: 6.0,
        type: "BURST_RELEASE_END",
        severity: "info",
        trigger: "DIFFUSION_TRANSITION",
        description: "Initial surface burst release phase completed. Entering Fickian matrix diffusion regime.",
        modelSource: "Korsmeyer-Peppas Engine v1.2",
        uncertainty: "± 3.1%",
        supported: true
      },
      {
        timeHours: 12.0,
        type: "ENVIRONMENT_CHANGE",
        severity: "warning",
        trigger: "USER_INPUT",
        description: "pH shifted from 7.40 to 5.50 (Simulating endosomal acidification).",
        modelSource: "User Action",
        uncertainty: "N/A",
        supported: true
      },
      {
        timeHours: 12.0,
        type: "MODEL_WARNING",
        severity: "warning",
        trigger: "CAUSAL_LIMIT",
        description: "ENVIRONMENT CHANGED: Current model does not support causal release-parameter updating for pH 5.50. Trajectory continues on baseline curve.",
        modelSource: "Model Boundary Manager",
        uncertainty: "High",
        supported: false
      },
      {
        timeHours: 24.0,
        type: "MODEL_BOUNDARY",
        severity: "info",
        trigger: "VALIDITY_THRESHOLD",
        description: "Cumulative release crossed 30%. Entering empirical validation regime boundary.",
        modelSource: "Korsmeyer-Peppas Engine v1.2",
        uncertainty: "± 4.8%",
        supported: true
      },
      {
        timeHours: 48.0,
        type: "EXTRAPOLATION_WARNING",
        severity: "error",
        trigger: "TIME_LIMIT",
        description: "EXTRAPOLATION: Trajectory beyond 48.0h exceeds Korsmeyer-Peppas validation window (60% release cap).",
        modelSource: "Model Validation Checker",
        uncertainty: "± 14.2%",
        supported: false
      }
    ]
  },
  
  // Scientific Support Matrix (Explicit Scientific Boundaries Rule)
  capabilities: {
    zetaPotentialPrediction: { status: "VERIFIED", label: "SUPPORTED", code: "VALIDATED" },
    cytotoxicityPrediction: { status: "VERIFIED", label: "SUPPORTED", code: "STATIC_ENDPOINT" },
    korsmeyerPeppasRelease: { status: "VERIFIED", label: "SUPPORTED", code: "VALIDATED_DOMAIN" },
    environmentTracking: { status: "VERIFIED", label: "SUPPORTED", code: "STATE_ONLY" },
    modelUncertaintyDisplay: { status: "VERIFIED", label: "SUPPORTED", code: "QUANTIFIED" },
    
    causalPhRelease: { status: "NOT_SUPPORTED", label: "NOT SCIENTIFICALLY SUPPORTED", code: "DATA_REQUIRED" },
    causalTempRelease: { status: "NOT_SUPPORTED", label: "NOT SCIENTIFICALLY SUPPORTED", code: "DATA_REQUIRED" },
    pdiEvolution: { status: "NOT_SUPPORTED", label: "NOT IMPLEMENTED", code: "PLANNED_v2" },
    aggregationDynamics: { status: "NOT_SUPPORTED", label: "NOT IMPLEMENTED", code: "DATA_REQUIRED" },
    proteinCorona: { status: "NOT_SUPPORTED", label: "NOT IMPLEMENTED", code: "DATA_REQUIRED" },
    cellularUptake: { status: "NOT_SUPPORTED", label: "NOT IMPLEMENTED", code: "FUTURE_RESEARCH" },
    humanBiodistribution: { status: "NOT_SUPPORTED", label: "NOT IMPLEMENTED", code: "OUT_OF_SCOPE" }
  },
  
  // Filter settings for dataset explorer & screening
  screening: {
    totalCandidates: 100,
    inDomain: 42,
    constraintMet: 18,
    shortlist: 10,
    maxHydroSizeNm: 100,
    minZetaMv: -40,
    maxZetaMv: -10,
    allowedCytotoxicity: "Nontoxic",
    minDrugLoadingPct: 5.0
  }
};
