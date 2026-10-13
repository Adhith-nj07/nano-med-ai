/**
 * NanoMedAI — Human Body Interaction and Nanomedicine Simulator
 * =============================================================
 * Scientific 3D simulation of drug-loaded nanoparticles inside the human body.
 * Multi-scale visualization: Macro Body Circulatory, Capillary Flow, Cellular Uptake, Nanoparticle Release.
 * Integrated with active ML models (Zeta stability, Cytotoxicity) and Korsmeyer-Peppas ODE kinetics.
 */

(function () {
    'use strict';

    // -------------------------------------------------------------
    // Formulation Presets
    // -------------------------------------------------------------
    const FORMULATION_PRESETS = {
        'plga-paclitaxel': {
            name: 'PLGA + Paclitaxel (Oncology Benchmark)',
            material: 'PLGA',
            coreSize: 80,
            hydroSize: 95,
            coating: 'PEG',
            smiles: 'OCCO',
            zeta: -24.5,
            drug: 'Paclitaxel',
            loading: 12.0,
            k: 0.18,
            n: 0.55,
            target: 'target_tissue',
            route: 'Intravenous',
            dose: 50.0,
            duration: 48.0,
            cell: 'A549',
            assay: 'MTT',
            desc: 'Biodegradable PLGA core coated with PEG-5000 delivering sustained paclitaxel with anomalous transport kinetics.'
        },
        'doxorubicin-liposome': {
            name: 'PEGylated Liposome + Doxorubicin (Doxil Analog)',
            material: 'Liposome',
            coreSize: 85,
            hydroSize: 100,
            coating: 'PEG',
            smiles: 'OCCO',
            zeta: -28.0,
            drug: 'Doxorubicin',
            loading: 14.5,
            k: 0.12,
            n: 0.42,
            target: 'target_tissue',
            route: 'Intravenous',
            dose: 40.0,
            duration: 72.0,
            cell: 'A549',
            assay: 'MTT',
            desc: 'Long-circulating sterically stabilized liposome with sulfate-crystallized anthracycline chemotherapeutic.'
        },
        'mrna-lnp': {
            name: 'mRNA Lipid Nanoparticle (LNP Formulation)',
            material: 'Liposome',
            coreSize: 75,
            hydroSize: 85,
            coating: 'PEG',
            smiles: 'OCCO',
            zeta: -5.2,
            drug: 'mRNA-1273',
            loading: 10.0,
            k: 0.25,
            n: 0.62,
            target: 'liver',
            route: 'Intravenous',
            dose: 25.0,
            duration: 24.0,
            cell: 'HepG2',
            assay: 'MTT',
            desc: 'Ionizable cationic lipid bilayer carrier with PEG-DMG shield, designed for hepatic delivery and endosomal escape.'
        },
        'paracetamol-sln': {
            name: 'Solid Lipid NP + Paracetamol (Analgesic)',
            material: 'PLGA',
            coreSize: 150,
            hydroSize: 175,
            coating: 'PVA',
            smiles: 'OCC(O)CO',
            zeta: -18.0,
            drug: 'Paracetamol',
            loading: 8.5,
            k: 0.22,
            n: 0.48,
            target: 'bloodstream',
            route: 'Intravenous',
            dose: 60.0,
            duration: 24.0,
            cell: 'HaCaT',
            assay: 'MTT',
            desc: 'Lipid matrix delivering sustained paracetamol release into bloodstream circulation.'
        },
        'vancomycin-plga': {
            name: 'PLGA-PEG + Vancomycin (Anti-MRSA Antibiotic)',
            material: 'PLGA',
            coreSize: 120,
            hydroSize: 140,
            coating: 'PEG',
            smiles: 'OCCO',
            zeta: -15.5,
            drug: 'Vancomycin',
            loading: 15.0,
            k: 0.16,
            n: 0.52,
            target: 'lungs',
            route: 'Intravenous',
            dose: 75.0,
            duration: 48.0,
            cell: 'A549',
            assay: 'MTT',
            desc: 'Polymeric extended-release nanocarrier targeted for systemic pulmonary antibiotic delivery.'
        },
        'cuo-toxicity-model': {
            name: 'Inorganic CuO Nanoparticle (Cytotoxicity Assay)',
            material: 'CuO',
            coreSize: 35,
            hydroSize: 75,
            coating: 'Uncoated',
            smiles: 'O',
            zeta: 12.5,
            drug: 'None (Carrier Study)',
            loading: 0.0,
            k: 0.05,
            n: 0.35,
            target: 'lungs',
            route: 'Intravenous',
            dose: 50.0,
            duration: 24.0,
            cell: 'A549',
            assay: 'MTT',
            desc: 'Inorganic metal oxide nanoparticle demonstrating surface-charge-mediated cellular interaction and cytotoxicity.'
        }
    };

    // -------------------------------------------------------------
    // In-Memory Scientific Knowledge Base (Default Fallback)
    // -------------------------------------------------------------
    const DEFAULT_REGIONS = {
        bloodstream: {
            id: 'bloodstream',
            name: 'Bloodstream & Systemic Circulation',
            category: 'Hemodynamic Transport',
            scientific_classification: 'ESTABLISHED HEMODYNAMIC KNOWLEDGE',
            nanoparticle_interactions: 'Nanoparticles experience shear stress, collisions with erythrocytes driving margination, and immediate plasma protein contact.',
            barrier_description: 'Vascular endothelium with tight junctions (< 2 nm in continuous capillaries).',
            physiological_properties: {
                fluid_type: 'Whole blood (plasma, erythrocytes)',
                pH: '7.35 - 7.45',
                temperature_c: '37.0 °C',
                shear_rate: '100 - 2000 s⁻¹',
                velocity: '0.5 mm/s (capillaries) to 40 cm/s (aorta)'
            }
        },
        liver: {
            id: 'liver',
            name: 'Liver (Hepatic Reticuloendothelial System)',
            category: 'Primary Clearance & Sequestration',
            scientific_classification: 'ESTABLISHED ANATOMICAL KNOWLEDGE',
            nanoparticle_interactions: 'Primary site of nanoparticle uptake for particles > 50-100 nm. Opsonized particles are rapidly phagocytosed by resident Kupffer cells.',
            barrier_description: 'Discontinuous sinusoidal endothelium with 100-150 nm fenestrations.',
            physiological_properties: {
                fenestrations: '100 - 150 nm',
                blood_flow: '1.2 - 1.5 L/min (25% cardiac output)',
                phagocytes: 'Kupffer cells (80-90% of body macrophages)'
            }
        },
        kidneys: {
            id: 'kidneys',
            name: 'Kidneys (Renal Glomerular Filtration)',
            category: 'Size-Selective Elimination',
            scientific_classification: 'ESTABLISHED ANATOMICAL KNOWLEDGE',
            nanoparticle_interactions: 'Nanoparticles with hydrodynamic diameter < 6-8 nm undergo rapid glomerular filtration into urine. Larger particles are retained in circulation.',
            barrier_description: 'Three-layer glomerular filtration barrier with podocyte slit diaphragms (4-10 nm).',
            physiological_properties: {
                filtration_cutoff: '6.0 - 8.0 nm hydrodynamic diameter',
                molecular_weight_cutoff: '~30 - 50 kDa',
                blood_flow: '1.0 - 1.2 L/min'
            }
        },
        lungs: {
            id: 'lungs',
            name: 'Lungs (Pulmonary Capillary Bed)',
            category: 'Microvascular Transit & Inhalation Clearance',
            scientific_classification: 'ESTABLISHED ANATOMICAL KNOWLEDGE',
            nanoparticle_interactions: 'Nanoparticles transit through the dense pulmonary capillary bed. Unstable particles that aggregate into clusters > 5 µm risk micro-embolism.',
            barrier_description: 'Extremely thin alveolar-capillary membrane (0.2 - 0.5 µm).',
            physiological_properties: {
                capillary_diameter: '5 - 8 µm (erythrocyte-sized)',
                transit_time: '0.75 seconds at rest',
                surface_area: '100 - 140 m²'
            }
        },
        skin: {
            id: 'skin',
            name: 'Skin (Dermal Microvasculature)',
            category: 'Peripheral Microvasculature & Barrier Tissue',
            scientific_classification: 'ESTABLISHED ANATOMICAL KNOWLEDGE',
            nanoparticle_interactions: 'For IV delivery, represents a peripheral capillary site. For topical delivery, the stratum corneum provides an impermeable barrier to particles > 10 nm.',
            barrier_description: 'Stratum corneum lipid lamellar matrix.',
            physiological_properties: {
                stratum_corneum_cutoff: '< 500 Da (< 10 nm intact NPs)',
                surface_pH: '4.5 - 5.5',
                dermal_temperature: '32 - 34 °C'
            }
        },
        target_tissue: {
            id: 'target_tissue',
            name: 'Target Tissue (Solid Tumor / Lesion)',
            category: 'Extravasation & Extracellular Penetration',
            scientific_classification: 'ESTABLISHED ONCOLOGY KNOWLEDGE',
            nanoparticle_interactions: 'Nanoparticles may exploit passive EPR extravasation through leaky tumor vessels. Targeting is never guaranteed; clinical delivery efficiency rarely exceeds 1-2% of dose.',
            barrier_description: 'Elevated interstitial fluid pressure (IFP) and dense collagen-hyaluronan matrix.',
            physiological_properties: {
                vascular_pore_cutoff: '100 - 800 nm (EPR effect)',
                interstitial_pressure: '10 - 40 mmHg (elevated IFP)',
                microenvironment_pH: '6.5 - 6.9 (hypoxic/Warburg)'
            }
        },
        cellular_environment: {
            id: 'cellular_environment',
            name: 'Cellular Environment & Endocytic Pathway',
            category: 'Membrane Interaction & Internalization',
            scientific_classification: 'ESTABLISHED CELL BIOLOGY KNOWLEDGE',
            nanoparticle_interactions: 'Membrane contact with anionic glycocalyx followed by clathrin/caveolae-mediated endocytosis, endosomal acidification (pH 5.0), and lysosomal digestion.',
            barrier_description: 'Phospholipid bilayer with fluid mosaic proteins and thick anionic glycocalyx brush.',
            physiological_properties: {
                glycocalyx_charge: 'Net negative',
                early_endosome_pH: '6.0 - 6.5',
                lysosome_pH: '4.5 - 5.0'
            }
        }
    };

    const DEFAULT_STAGES = [
        {
            stage_id: 1, key: 'administration', name: 'Stage 1: Administration & Introduction',
            badge_text: 'ESTABLISHED BIOPHYSICAL PROTOCOL', badge_type: 'live', is_quantitative_prediction: false,
            description: 'Introduction of drug-loaded nanoparticles into the biological system.',
            scientific_mechanisms: 'For IV administration, particles enter systemic circulation via a peripheral vein, undergoing rapid 1:1000 dilution in ~5 L of blood within 1-2 minutes.',
            limitations: 'Route-specific pharmacokinetics for non-IV routes require specialized mucosal models.'
        },
        {
            stage_id: 2, key: 'circulation', name: 'Stage 2: Bloodstream Circulation & Hemodynamics',
            badge_text: 'PREDICTED STABILITY & FLUID DYNAMICS', badge_type: 'live', is_quantitative_prediction: true,
            description: 'Transport through arterial, venous, and capillary vascular networks.',
            scientific_mechanisms: 'Particles circulate with laminar blood flow, marginating toward walls. Colloidal stability evaluated via predicted surface charge (|ζ| potential) and steric PEGylation.',
            limitations: 'In vivo half-life is influenced by multiple unmodeled biological clearance factors beyond surface charge.'
        },
        {
            stage_id: 3, key: 'protein_corona', name: 'Stage 3: Protein Corona Formation',
            badge_text: 'CONCEPTUAL BIOLOGICAL ILLUSTRATION', badge_type: 'purple', is_quantitative_prediction: false,
            description: 'Adsorption of plasma proteins onto nanoparticle surfaces forming a biomolecular corona.',
            scientific_mechanisms: 'Plasma proteins (albumin, fibrinogen, apolipoproteins, IgG) rapidly adsorb forming a hard and soft biomolecular corona that redefines cellular recognition.',
            limitations: 'IMPORTANT: No quantitative protein corona prediction model is active in this platform. Illustrated conceptually.'
        },
        {
            stage_id: 4, key: 'tissue_interaction', name: 'Stage 4: Target Tissue Interaction & Extravasation',
            badge_text: 'PHYSIOLOGICAL INTERACTION MECHANICS', badge_type: 'live', is_quantitative_prediction: false,
            description: 'Approach toward target microvasculature and tissue extravasation.',
            scientific_mechanisms: 'Hyperpermeable tumor vessels may permit passive extravasation (EPR effect). Penetration hindered by high IFP. Targeting is NOT guaranteed (<1-2% median clinical efficiency).',
            limitations: 'Does not guarantee target accumulation; solid tumor delivery is subject to severe physiological barriers.'
        },
        {
            stage_id: 5, key: 'cellular_uptake', name: 'Stage 5: Cellular Uptake & Endocytic Internalization',
            badge_text: 'CONCEPTUAL BIOLOGICAL ILLUSTRATION', badge_type: 'purple', is_quantitative_prediction: false,
            description: 'Membrane contact, invagination, vesicle formation, and intracellular trafficking.',
            scientific_mechanisms: '1. Approach -> 2. Glycocalyx Contact -> 3. Membrane Invagination -> 4. Endosome Vesicle -> 5. Lysosomal Acidification & Drug Escape.',
            limitations: 'Distinguished from quantitative cellular uptake rates. Specific internalization kinetics depend on cell-specific receptor densities.'
        },
        {
            stage_id: 6, key: 'drug_release', name: 'Stage 6: Drug Release Kinetics',
            badge_text: 'MATHEMATICAL SIMULATION (KORSMEYER-PEPPAS ODE)', badge_type: 'live', is_quantitative_prediction: true,
            description: 'Sustained diffusion and dissolution of active pharmaceutical molecules from matrix.',
            scientific_mechanisms: 'Computed via Korsmeyer-Peppas ODE: Mt/M_inf = k * t^n. Classifies Fickian diffusion (n <= 0.43), anomalous transport (0.43 < n < 0.85), or Case II erosion (n >= 0.85).',
            limitations: 'Valid strictly for cumulative release up to 60%. Parameters k, n are empirical constants fitted at 37°C/pH 7.4.'
        },
        {
            stage_id: 7, key: 'toxicity_response', name: 'Stage 7: Biological Response & Cytotoxicity',
            badge_text: 'ACTIVE ML PREDICTION (RANDOM FOREST)', badge_type: 'live', is_quantitative_prediction: true,
            description: 'Assessment of carrier biocompatibility and target cell interaction.',
            scientific_mechanisms: 'Carrier cytotoxicity is predicted via trained Random Forest model. Crucially distinguishes carrier cytotoxicity from intended drug pharmacological action.',
            limitations: 'Research in vitro screening estimate. Does NOT predict human clinical toxicity or patient outcomes.'
        },
        {
            stage_id: 8, key: 'clearance', name: 'Stage 8: Clearance, Metabolism & Elimination',
            badge_text: 'CONCEPTUAL BIOLOGICAL ILLUSTRATION', badge_type: 'purple', is_quantitative_prediction: false,
            description: 'Clearance of carrier fragments and metabolites through renal and hepatobiliary systems.',
            scientific_mechanisms: 'Particles < 6-8 nm undergo renal glomerular filtration into urine. Particles > 50-100 nm are sequestered by hepatic Kupffer cells and splenic macrophages.',
            limitations: 'Quantitative organ clearance curves and elimination half-lives require validated PBPK digital twin models. Illustrated conceptually.'
        }
    ];

    // -------------------------------------------------------------
    // Simulator State
    // -------------------------------------------------------------
    const SimState = {
        isRunning: false,
        isPaused: false,
        speed: 1.0,
        currentStageIndex: 0,
        currentSimTimeHours: 0.0,
        maxDurationHours: 48.0,
        timeStepHours: 0.5,
        activeViewMode: 'body',
        selectedRegionId: 'target_tissue',
        regionsData: DEFAULT_REGIONS,
        stagesData: DEFAULT_STAGES,
        evaluationResult: null,
        autoAdvance: true,
        events: []
    };

    // -------------------------------------------------------------
    // DOM References Cache
    // -------------------------------------------------------------
    let elements = {};

    function initDomReferences() {
        elements = {
            viewContainer: document.getElementById('view-human-body'),
            canvasContainer: document.getElementById('hbs-canvas-container'),
            threeCanvas: document.getElementById('hbs-three-canvas'),
            fallbackCanvas: document.getElementById('hbs-fallback-canvas'),
            viewModeButtons: document.querySelectorAll('.hbs-view-btn'),
            stageSteps: document.querySelectorAll('.hbs-stage-step'),
            btnStart: document.getElementById('hbs-btn-start'),
            btnPause: document.getElementById('hbs-btn-pause'),
            btnResume: document.getElementById('hbs-btn-resume'),
            btnReset: document.getElementById('hbs-btn-reset'),
            speedButtons: document.querySelectorAll('.hbs-speed-btn'),
            autoAdvanceCheck: document.getElementById('hbs-auto-advance'),
            regionSelect: document.getElementById('hbs-region-select'),
            presetSelect: document.getElementById('hbs-preset-select'),
            btnApplyConfig: document.getElementById('hbs-btn-apply-config'),
            btnPredictZeta: document.getElementById('hbs-btn-predict-zeta'),

            // Configuration Inputs
            inputMaterial: document.getElementById('hbs-cfg-material'),
            inputCoreSize: document.getElementById('hbs-cfg-core-size'),
            inputHydroSize: document.getElementById('hbs-cfg-hydro-size'),
            inputCoating: document.getElementById('hbs-cfg-coating'),
            inputZeta: document.getElementById('hbs-cfg-zeta'),
            inputDrug: document.getElementById('hbs-cfg-drug'),
            inputLoading: document.getElementById('hbs-cfg-loading'),
            inputK: document.getElementById('hbs-cfg-k'),
            inputN: document.getElementById('hbs-cfg-n'),
            inputTarget: document.getElementById('hbs-cfg-target'),
            inputRoute: document.getElementById('hbs-cfg-route'),
            inputDose: document.getElementById('hbs-cfg-dose'),
            inputPh: document.getElementById('hbs-cfg-ph'),
            inputPhVal: document.getElementById('hbs-val-ph'),
            inputTemp: document.getElementById('hbs-cfg-temp'),
            inputTempVal: document.getElementById('hbs-val-temp'),
            inputIonic: document.getElementById('hbs-cfg-ionic'),
            inputIonicVal: document.getElementById('hbs-val-ionic'),
            inputDuration: document.getElementById('hbs-cfg-duration'),
            inputDurationVal: document.getElementById('hbs-val-duration'),
            inputCell: document.getElementById('hbs-cfg-cell'),
            inputAssay: document.getElementById('hbs-cfg-assay'),

            // HUD & Telemetry
            hudRegionBadge: document.getElementById('hbs-hud-region-badge'),
            hudStageBadge: document.getElementById('hbs-hud-stage-badge'),
            hudTimeBadge: document.getElementById('hbs-hud-time-badge'),
            hudParticlesBadge: document.getElementById('hbs-hud-particles-badge'),
            progressBar: document.getElementById('hbs-stage-progress-bar'),

            // Metrics
            kpiZeta: document.getElementById('hbs-kpi-zeta'),
            kpiStabilityClass: document.getElementById('hbs-kpi-stability-class'),
            kpiCytotox: document.getElementById('hbs-kpi-cytotox'),
            kpiCytotoxConf: document.getElementById('hbs-kpi-cytotox-conf'),
            kpiReleasePct: document.getElementById('hbs-kpi-release-pct'),
            kpiReleaseMech: document.getElementById('hbs-kpi-release-mech'),
            kpiReleaseRate: document.getElementById('hbs-kpi-release-rate'),
            kpiRemainingPct: document.getElementById('hbs-kpi-remaining-pct'),
            kpiSimTime: document.getElementById('hbs-kpi-sim-time'),

            // Panels
            regionTitle: document.getElementById('hbs-region-title'),
            regionCategory: document.getElementById('hbs-region-category'),
            regionInteractions: document.getElementById('hbs-region-interactions'),
            regionBarrier: document.getElementById('hbs-region-barrier'),
            regionPropertiesList: document.getElementById('hbs-region-properties-list'),
            regionNatureBadge: document.getElementById('hbs-region-nature-badge'),

            stageTitle: document.getElementById('hbs-stage-title'),
            stageBadge: document.getElementById('hbs-stage-badge'),
            stageDesc: document.getElementById('hbs-stage-desc'),
            stageMechanisms: document.getElementById('hbs-stage-mechanisms'),
            stageLimitations: document.getElementById('hbs-stage-limitations'),

            // Domain Warnings & Events
            domainWarningsCard: document.getElementById('hbs-domain-warnings-card'),
            domainWarningsList: document.getElementById('hbs-domain-warnings-list'),
            eventLogContainer: document.getElementById('hbs-event-log')
        };
    }

    // -------------------------------------------------------------
    // Client-side Biophysical Evaluator (Immediate Local Fallback)
    // -------------------------------------------------------------
    function computeLocalEvaluation(cfg) {
        const k = cfg.k_release || 0.18;
        const n = cfg.n_release || 0.55;
        const totalHours = cfg.exposure_time_hours || 48.0;
        const steps = 50;

        let mechanism = 'Anomalous Transport';
        if (n <= 0.43) mechanism = 'Fickian Diffusion (Case I)';
        else if (n >= 0.85) mechanism = 'Case II Polymer Relaxation';

        const timeSeries = [];
        for (let i = 0; i <= steps; i++) {
            const t = (i / steps) * totalHours;
            const fraction = t <= 0 ? 0 : Math.min(1.0, k * Math.pow(t, n));
            const rate = t <= 0 ? 0 : k * n * Math.pow(t, n - 1.0) * 100.0;
            timeSeries.push({
                time_hours: Math.round(t * 10) / 10,
                cumulative_release_pct: Math.round(fraction * 1000) / 10,
                release_rate_pct_hr: Math.round(rate * 100) / 100,
                remaining_drug_pct: Math.round((1.0 - fraction) * 1000) / 10
            });
        }

        const zeta = cfg.surface_charge_mv || -24.5;
        const absZ = Math.abs(zeta);
        const isPeg = (cfg.surface_coating || '').toUpperCase().includes('PEG');
        let stabClass = 'Stable';
        let stabColor = 'accent';
        let aggRisk = 'Low';

        if (isPeg) {
            stabClass = 'Highly Stable (Sterically Shielded)';
            stabColor = 'accent';
            aggRisk = 'Very Low';
        } else if (absZ >= 30) {
            stabClass = 'Electrostatically Stable (|ζ| ≥ 30 mV)';
            stabColor = 'accent';
            aggRisk = 'Low';
        } else if (absZ >= 20) {
            stabClass = 'Moderate Stability (20 ≤ |ζ| < 30 mV)';
            stabColor = 'warn';
            aggRisk = 'Moderate';
        } else {
            stabClass = 'Aggregation Prone (|ζ| < 20 mV)';
            stabColor = 'danger';
            aggRisk = 'High';
        }

        const isToxicCarrier = ['CUO', 'ZNO'].includes((cfg.material || '').toUpperCase());

        return {
            status: 'SUCCESS',
            formulation_summary: cfg,
            model_results: {
                stability: {
                    zeta_mv: zeta,
                    model: 'Ridge Regressor / Configured',
                    confidence: 'Moderate'
                },
                cytotoxicity: {
                    prediction: isToxicCarrier ? 'Toxic' : 'Nontoxic',
                    confidence: 0.91,
                    cell_line: cfg.cell_name || 'A549',
                    assay: cfg.assay || 'MTT'
                },
                colloidal_index: {
                    stability_class: stabClass,
                    color_code: stabColor,
                    aggregation_risk: aggRisk,
                    effective_zeta_mv: zeta,
                    is_sterically_stabilized: isPeg
                },
                drug_release_kinetics: {
                    k: k,
                    n: n,
                    mechanism: mechanism,
                    time_series: timeSeries,
                    final_release_pct: timeSeries[timeSeries.length - 1].cumulative_release_pct,
                    final_release_rate: timeSeries[timeSeries.length - 1].release_rate_pct_hr
                }
            },
            warnings: []
        };
    }

    // -------------------------------------------------------------
    // Chart.js Kinetics Release Plot
    // -------------------------------------------------------------
    let releaseChart = null;

    function initReleaseChart() {
        const canvas = document.getElementById('hbs-release-chart');
        if (!canvas || !window.Chart) return;

        try {
            if (releaseChart) {
                releaseChart.destroy();
                releaseChart = null;
            }

            const ctx = canvas.getContext('2d');
            releaseChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [0],
                    datasets: [
                        {
                            label: 'Cumulative Release Mt/M∞ (%)',
                            data: [0],
                            borderColor: '#22d3ee',
                            backgroundColor: 'rgba(34, 211, 238, 0.12)',
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.25,
                            pointRadius: 1.5,
                            pointHoverRadius: 5
                        },
                        {
                            label: 'Instantaneous Rate (% / hr)',
                            data: [0],
                            borderColor: '#a855f7',
                            borderWidth: 1.8,
                            borderDash: [4, 4],
                            fill: false,
                            yAxisID: 'y1',
                            tension: 0.25,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: {
                        x: {
                            title: { display: true, text: 'Simulation Time (hours)', color: '#948cb8', font: { size: 10 } },
                            grid: { color: 'rgba(139, 120, 255, 0.1)' },
                            ticks: { color: '#948cb8', font: { size: 9 } }
                        },
                        y: {
                            min: 0,
                            max: 100,
                            title: { display: true, text: 'Release %', color: '#22d3ee', font: { size: 10 } },
                            grid: { color: 'rgba(139, 120, 255, 0.1)' },
                            ticks: { color: '#22d3ee', font: { size: 9 }, callback: val => val + '%' }
                        },
                        y1: {
                            position: 'right',
                            min: 0,
                            title: { display: true, text: 'Rate (%/hr)', color: '#a855f7', font: { size: 10 } },
                            grid: { drawOnChartArea: false },
                            ticks: { color: '#a855f7', font: { size: 9 } }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { color: '#f1efff', boxWidth: 12, font: { size: 10 } }
                        }
                    }
                }
            });
        } catch (err) {
            console.warn('Chart.js initialization deferred:', err);
        }
    }

    function updateReleaseChart(trajectory) {
        if (!releaseChart || !trajectory || !trajectory.time_series) return;

        try {
            const ts = trajectory.time_series;
            releaseChart.data.labels = ts.map(p => p.time_hours);
            releaseChart.data.datasets[0].data = ts.map(p => p.cumulative_release_pct);
            releaseChart.data.datasets[1].data = ts.map(p => p.release_rate_pct_hr);
            releaseChart.update('none');
        } catch (e) {
            console.warn('Chart update skipped:', e);
        }
    }

    // -------------------------------------------------------------
    // Three.js Multi-Scale 3D Engine
    // -------------------------------------------------------------
    let renderer = null;
    let scene = null;
    let camera = null;
    let animationFrameId = null;

    let sceneBody = null;
    let sceneVessel = null;
    let sceneCellular = null;
    let sceneRelease = null;

    let rbcParticles = [];
    let nanoParticles = [];
    let drugMolecules = [];
    let organMarkers = {};
    let membraneVesicle = null;
    let coreMesh = null;
    let heartMesh = null;
    let heartPulseTime = 0;
    let clathrinBasket = null;
    let aorticCurve = null;
    let venaCavaCurve = null;

    // -------------------------------------------------------------
    // 3D Camera & Interactive Navigation State
    // -------------------------------------------------------------
    let controlMode = 'orbit'; // 'orbit' or 'pan'
    let autoRotate = false;
    let isDragging = false;
    let isPanning = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let spherical = { radius: 140, theta: Math.PI / 2, phi: Math.PI / 2 };
    let cameraTarget = { x: 0, y: 0, z: 0 };
    let desiredTarget = { x: 0, y: 0, z: 0 };
    let desiredRadius = 140;

    function initThreeScene() {
        if (!window.THREE) {
            console.warn('Three.js not found, enabling 2D fallback');
            initFallbackCanvas();
            return;
        }

        const canvas = elements.threeCanvas;
        if (!canvas) return;

        try {
            // Measure parent viewport or use reliable default to avoid 0x0 / NaN
            const container = elements.canvasContainer || canvas.parentElement;
            let w = canvas.clientWidth || (container ? container.clientWidth : 0) || 800;
            let h = canvas.clientHeight || (container ? container.clientHeight : 0) || 480;
            if (w <= 0) w = 800;
            if (h <= 0) h = 480;

            renderer = new THREE.WebGLRenderer({
                canvas: canvas,
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance'
            });
            renderer.setSize(w, h);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(45, w / h, 1, 1000);
            updateCameraPosition();

            // Lighting Setup
            const ambient = new THREE.AmbientLight(0xffffff, 0.65);
            scene.add(ambient);

            const dirLight1 = new THREE.DirectionalLight(0x22d3ee, 1.3);
            dirLight1.position.set(50, 90, 70);
            scene.add(dirLight1);

            const dirLight2 = new THREE.DirectionalLight(0xa855f7, 0.95);
            dirLight2.position.set(-60, -40, 50);
            scene.add(dirLight2);

            const dirLight3 = new THREE.DirectionalLight(0xf59e0b, 0.5);
            dirLight3.position.set(0, 50, -60);
            scene.add(dirLight3);

            // Ground Holographic Grid for spatial depth
            const grid = new THREE.GridHelper(180, 24, 0x22d3ee, 0x1e1b4b);
            grid.position.y = -62;
            grid.material.opacity = 0.22;
            grid.material.transparent = true;
            scene.add(grid);

            // Sub-Scene Groups
            sceneBody = new THREE.Group();
            sceneVessel = new THREE.Group();
            sceneCellular = new THREE.Group();
            sceneRelease = new THREE.Group();

            scene.add(sceneBody);
            scene.add(sceneVessel);
            scene.add(sceneCellular);
            scene.add(sceneRelease);

            buildHumanBodyModel();
            buildBloodVesselModel();
            buildCellularUptakeModel();
            buildNanoparticleReleaseModel();

            setupControls(canvas);
            switchViewMode('body');

            if (!animationFrameId) {
                renderLoop();
            }
        } catch (err) {
            console.error('WebGL Init Error:', err);
            if (elements.threeCanvas) elements.threeCanvas.style.display = 'none';
            if (elements.fallbackCanvas) elements.fallbackCanvas.style.display = 'block';
            initFallbackCanvas();
        }
    }

    function updateCameraPosition() {
        if (!camera) return;

        // Prevent NaN corruption
        if (isNaN(cameraTarget.x)) cameraTarget.x = 0;
        if (isNaN(cameraTarget.y)) cameraTarget.y = 0;
        if (isNaN(cameraTarget.z)) cameraTarget.z = 0;
        if (isNaN(spherical.radius) || spherical.radius <= 0) spherical.radius = 140;

        cameraTarget.x += (desiredTarget.x - cameraTarget.x) * 0.08;
        cameraTarget.y += (desiredTarget.y - cameraTarget.y) * 0.08;
        cameraTarget.z += (desiredTarget.z - cameraTarget.z) * 0.08;
        spherical.radius += (desiredRadius - spherical.radius) * 0.08;

        const x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
        const y = spherical.radius * Math.cos(spherical.phi);
        const z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);

        camera.position.set(cameraTarget.x + x, cameraTarget.y + y, cameraTarget.z + z);
        camera.lookAt(cameraTarget.x, cameraTarget.y, cameraTarget.z);
    }

    // -------------------------------------------------------------
    // Comprehensive 3D Navigation Controls (Rotate & Move / Pan)
    // -------------------------------------------------------------
    function setupControls(canvas) {
        canvas.style.cursor = 'grab';

        canvas.addEventListener('contextmenu', e => e.preventDefault());

        canvas.addEventListener('mousedown', e => {
            isDragging = true;
            prevMouseX = e.clientX;
            prevMouseY = e.clientY;

            // Pan if right-click, middle-click, Shift key held, or in 'pan' mode
            isPanning = (e.button === 2 || e.button === 1 || e.shiftKey || controlMode === 'pan');
            canvas.style.cursor = 'grabbing';
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
            canvas.style.cursor = controlMode === 'pan' ? 'move' : 'grab';
        });

        window.addEventListener('mousemove', e => {
            if (!isDragging) return;
            const deltaX = e.clientX - prevMouseX;
            const deltaY = e.clientY - prevMouseY;
            prevMouseX = e.clientX;
            prevMouseY = e.clientY;

            if (isPanning) {
                // Pan / Move camera target in local camera plane
                panCameraTarget(-deltaX, deltaY);
            } else {
                // Orbit / Rotate camera horizontally and vertically
                spherical.theta -= deltaX * 0.008;
                spherical.phi = Math.max(0.05, Math.min(Math.PI - 0.05, spherical.phi - deltaY * 0.008));
            }
        });

        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            desiredRadius = Math.max(15, Math.min(320, desiredRadius + e.deltaY * 0.12));
        }, { passive: false });

        // Touch support: 1 finger orbit/pan, 2 fingers pinch-to-zoom & two-finger pan
        let touchStartDist = 0;
        let touchMidX = 0;
        let touchMidY = 0;

        canvas.addEventListener('touchstart', e => {
            if (e.touches.length === 1) {
                isDragging = true;
                isPanning = (controlMode === 'pan');
                prevMouseX = e.touches[0].clientX;
                prevMouseY = e.touches[0].clientY;
            } else if (e.touches.length === 2) {
                isDragging = false;
                touchStartDist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                touchMidX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
                touchMidY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
            }
        }, { passive: false });

        canvas.addEventListener('touchmove', e => {
            if (e.touches.length === 1 && isDragging) {
                e.preventDefault();
                const deltaX = e.touches[0].clientX - prevMouseX;
                const deltaY = e.touches[0].clientY - prevMouseY;
                prevMouseX = e.touches[0].clientX;
                prevMouseY = e.touches[0].clientY;

                if (isPanning) {
                    panCameraTarget(-deltaX, deltaY);
                } else {
                    spherical.theta -= deltaX * 0.01;
                    spherical.phi = Math.max(0.05, Math.min(Math.PI - 0.05, spherical.phi - deltaY * 0.01));
                }
            } else if (e.touches.length === 2) {
                e.preventDefault();
                const dist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                desiredRadius = Math.max(15, Math.min(320, desiredRadius - (dist - touchStartDist) * 0.35));
                touchStartDist = dist;

                const curMidX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
                const curMidY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
                panCameraTarget(curMidX - touchMidX, curMidY - touchMidY);
                touchMidX = curMidX;
                touchMidY = curMidY;
            }
        }, { passive: false });

        canvas.addEventListener('touchend', () => { isDragging = false; });

        // Keyboard navigation
        window.addEventListener('keydown', e => {
            if (document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
            if (e.key === 'ArrowLeft') { nudgeCamera(-1, 0); }
            else if (e.key === 'ArrowRight') { nudgeCamera(1, 0); }
            else if (e.key === 'ArrowUp') { nudgeCamera(0, 1); }
            else if (e.key === 'ArrowDown') { nudgeCamera(0, -1); }
            else if (e.key === '+' || e.key === '=') { zoomCamera(0.85); }
            else if (e.key === '-' || e.key === '_') { zoomCamera(1.18); }
            else if (e.key === 'r' || e.key === 'R') { resetCamera(); }
            else if (e.key === ' ') { e.preventDefault(); toggleAutoRotate(); }
        });
    }

    function panCameraTarget(deltaX, deltaY) {
        if (!camera) return;
        const forward = new THREE.Vector3().subVectors(cameraTarget, camera.position).normalize();
        const right = new THREE.Vector3().crossVectors(forward, camera.up).normalize();
        const up = new THREE.Vector3().crossVectors(right, forward).normalize();
        const panFactor = desiredRadius * 0.0018;

        desiredTarget.x += (right.x * deltaX + up.x * deltaY) * panFactor;
        desiredTarget.y += (right.y * deltaX + up.y * deltaY) * panFactor;
        desiredTarget.z += (right.z * deltaX + up.z * deltaY) * panFactor;
    }

    function setControlMode(mode) {
        controlMode = mode;
        const btnOrbit = document.getElementById('hbs-btn-mode-orbit');
        const btnPan = document.getElementById('hbs-btn-mode-pan');
        if (btnOrbit) btnOrbit.classList.toggle('active', mode === 'orbit');
        if (btnPan) btnPan.classList.toggle('active', mode === 'pan');

        if (elements.threeCanvas) {
            elements.threeCanvas.style.cursor = mode === 'pan' ? 'move' : 'grab';
        }
        const instr = document.getElementById('hbs-hud-instruction');
        if (instr) {
            instr.textContent = mode === 'pan' ?
                '✋ MOVE MODE: Drag to pan camera • Use D-Pad or switch to Rotate' :
                '🔄 ROTATE MODE: Drag to orbit • Right/Shift Drag: Pan • Scroll: Zoom';
        }
    }

    function nudgeCamera(dirX, dirY) {
        if (controlMode === 'pan') {
            panCameraTarget(dirX * 22, dirY * 22);
        } else {
            spherical.theta += dirX * 0.18;
            spherical.phi = Math.max(0.05, Math.min(Math.PI - 0.05, spherical.phi - dirY * 0.18));
        }
    }

    function zoomCamera(factor) {
        desiredRadius = Math.max(15, Math.min(320, desiredRadius * factor));
    }

    function toggleAutoRotate() {
        autoRotate = !autoRotate;
        const btn = document.getElementById('hbs-btn-autorotate');
        if (btn) {
            btn.classList.toggle('active', autoRotate);
            btn.textContent = autoRotate ? '🪐 Auto-Spin: ON' : '🪐 Auto-Spin: OFF';
        }
    }

    function resetCamera() {
        if (SimState.activeViewMode === 'body') {
            desiredTarget = { x: 0, y: 0, z: 0 };
            desiredRadius = 140;
            spherical.theta = Math.PI / 2;
            spherical.phi = Math.PI / 2;
        } else if (SimState.activeViewMode === 'vessel') {
            desiredTarget = { x: 0, y: 0, z: 0 };
            desiredRadius = 70;
            spherical.theta = Math.PI / 2.5;
            spherical.phi = Math.PI / 2.2;
        } else if (SimState.activeViewMode === 'cellular') {
            desiredTarget = { x: 0, y: -12, z: 0 };
            desiredRadius = 65;
            spherical.theta = Math.PI / 2;
            spherical.phi = Math.PI / 2.4;
        } else if (SimState.activeViewMode === 'release') {
            desiredTarget = { x: 0, y: 0, z: 0 };
            desiredRadius = 55;
            spherical.theta = Math.PI / 2;
            spherical.phi = Math.PI / 2;
        }
    }

    // -------------------------------------------------------------
    // Parametric Biconcave Erythrocyte (RBC) Geometry
    // -------------------------------------------------------------
    function createBiconcaveRbcGeometry() {
        const points = [];
        const R = 3.6;
        const segments = 16;
        for (let i = 0; i <= segments; i++) {
            const r = (i / segments) * R;
            const x = r / R;
            // Evans-Fung parametric biconcave thickness equation:
            // h(x) = D * sqrt(1 - x^2) * (c0 + c1 * x^2 + c2 * x^4)
            const h = 1.15 * Math.sqrt(Math.max(0, 1.0 - x * x)) * (0.18 + 1.15 * x * x - 0.42 * x * x * x * x);
            points.push(new THREE.Vector2(r, Math.max(0.15, h)));
        }
        return new THREE.LatheGeometry(points, 22);
    }

    // -------------------------------------------------------------
    // High-Fidelity Anatomical 3D Models (Scientifically Authentic)
    // -------------------------------------------------------------
    function buildHumanBodyModel() {
        // Materials with Cyber-Glass holographic aesthetic
        const matWireCyan = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.22
        });
        const matBone = new THREE.MeshStandardMaterial({
            color: 0xe2e8f0,
            roughness: 0.5,
            metalness: 0.1,
            transparent: true,
            opacity: 0.45
        });
        const matGhost = new THREE.MeshBasicMaterial({
            color: 0x22d3ee,
            transparent: true,
            opacity: 0.08,
            wireframe: false,
            side: THREE.DoubleSide
        });

        // 1. Organic Head & Cranium with Internal Bioluminescent Brain
        const headGroup = new THREE.Group();
        headGroup.position.set(0, 48, 0);

        const cranium = new THREE.Mesh(new THREE.SphereGeometry(7.6, 22, 22), matWireCyan);
        cranium.scale.set(0.95, 1.05, 1.0);
        headGroup.add(cranium);

        const brain = new THREE.Mesh(
            new THREE.SphereGeometry(5.2, 16, 16),
            new THREE.MeshStandardMaterial({
                color: 0xa855f7,
                emissive: 0x7e22ce,
                emissiveIntensity: 0.5,
                roughness: 0.6,
                transparent: true,
                opacity: 0.75
            })
        );
        brain.position.set(0, 1.2, -0.4);
        brain.scale.set(0.9, 0.85, 1.1);
        headGroup.add(brain);

        const jaw = new THREE.Mesh(new THREE.ConeGeometry(3.6, 5.0, 12), matWireCyan);
        jaw.position.set(0, -5.2, 1.4);
        jaw.rotation.x = Math.PI;
        headGroup.add(jaw);

        sceneBody.add(headGroup);

        // 2. Segmented Vertebral Spine (18 Discs from Neck to Pelvis)
        const spineGroup = new THREE.Group();
        for (let i = 0; i < 18; i++) {
            const y = 41 - i * 2.5;
            const disc = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.8, 1.2, 10), matBone);
            disc.position.set(0, y, -1.8 + Math.sin(i * 0.35) * 0.8);
            spineGroup.add(disc);
        }
        sceneBody.add(spineGroup);

        // 3. Anatomical Thoracic Rib Cage (10 Curved Rib Pairs)
        const ribGroup = new THREE.Group();
        for (let i = 0; i < 10; i++) {
            const y = 37 - i * 1.8;
            const spread = 8.5 + Math.sin((i / 10) * Math.PI) * 5.5;
            [-1, 1].forEach(side => {
                const ribCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(0, y, -1.8),
                    new THREE.Vector3(side * (spread * 0.7), y + 0.4, -1.0),
                    new THREE.Vector3(side * spread, y - 0.5, 1.2),
                    new THREE.Vector3(side * (spread * 0.5), y - 1.2, 3.4),
                    new THREE.Vector3(side * 0.8, y - 1.5, 3.8) // sternal junction
                ]);
                const ribTube = new THREE.Mesh(
                    new THREE.TubeGeometry(ribCurve, 16, 0.45, 6, false),
                    matWireCyan
                );
                ribGroup.add(ribTube);
            });
        }

        // Sternum (Chest Bone)
        const sternum = new THREE.Mesh(new THREE.BoxGeometry(1.6, 15, 0.8), matBone);
        sternum.position.set(0, 28, 4.0);
        ribGroup.add(sternum);
        sceneBody.add(ribGroup);

        // 4. Clavicles & Pelvic Girdle
        [-1, 1].forEach(side => {
            const clavicle = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 14, 8), matBone);
            clavicle.position.set(side * 7.5, 38, 1.6);
            clavicle.rotation.z = side * 1.35;
            clavicle.rotation.y = side * 0.25;
            sceneBody.add(clavicle);
        });

        const pelvis = new THREE.Mesh(new THREE.TorusGeometry(8.5, 2.2, 8, 16, Math.PI), matBone);
        pelvis.position.set(0, -6, 0);
        pelvis.rotation.x = Math.PI / 2;
        sceneBody.add(pelvis);

        // 5. Contoured Limbs with Natural Joints
        [-1, 1].forEach(side => {
            // Upper Arm & Forearm
            const armUpper = new THREE.Mesh(new THREE.CylinderGeometry(2.6, 2.1, 20, 12), matWireCyan);
            armUpper.position.set(side * 17.5, 26, 0);
            armUpper.rotation.z = side * 0.16;
            sceneBody.add(armUpper);

            const elbow = new THREE.Mesh(new THREE.SphereGeometry(2.3, 10, 10), matBone);
            elbow.position.set(side * 19.2, 15, 0);
            sceneBody.add(elbow);

            const armLower = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 1.6, 20, 12), matWireCyan);
            armLower.position.set(side * 22, 5, 0);
            armLower.rotation.z = side * 0.08;
            sceneBody.add(armLower);

            // Femur Thigh & Tibia Lower Leg
            const thigh = new THREE.Mesh(new THREE.CylinderGeometry(4.8, 3.6, 28, 14), matWireCyan);
            thigh.position.set(side * 6.8, -18, 0);
            sceneBody.add(thigh);

            const knee = new THREE.Mesh(new THREE.SphereGeometry(3.5, 12, 12), matBone);
            knee.position.set(side * 7.0, -32, 0.4);
            sceneBody.add(knee);

            const calf = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 2.5, 28, 14), matWireCyan);
            calf.position.set(side * 7.2, -47, 0);
            sceneBody.add(calf);
        });

        // Torso Translucent Hull for organic silhouette
        const torsoHull = new THREE.Mesh(new THREE.CylinderGeometry(13.5, 11, 38, 22), matGhost);
        torsoHull.position.set(0, 18, 0);
        torsoHull.scale.set(1.15, 1, 0.65);
        sceneBody.add(torsoHull);

        // 6. Cardiovascular Architecture (Pulsing Heart & Systemic Vessel Trees)
        const arteryMat = new THREE.MeshStandardMaterial({
            color: 0xef4444,
            emissive: 0xdc2626,
            emissiveIntensity: 0.65,
            roughness: 0.3,
            metalness: 0.2
        });
        const veinMat = new THREE.MeshStandardMaterial({
            color: 0x0284c7,
            emissive: 0x0369a1,
            emissiveIntensity: 0.55,
            roughness: 0.3,
            metalness: 0.2
        });

        // 4-Chamber Anatomical Heart Mass
        heartMesh = new THREE.Group();
        heartMesh.position.set(0, 27, 2.6);

        const leftVent = new THREE.Mesh(
            new THREE.SphereGeometry(3.2, 16, 16),
            new THREE.MeshStandardMaterial({ color: 0xb91c1c, emissive: 0x991b1b, emissiveIntensity: 0.7 })
        );
        leftVent.scale.set(1.1, 1.4, 0.9);
        leftVent.position.set(-1.0, -1.0, 0);
        heartMesh.add(leftVent);

        const rightVent = new THREE.Mesh(
            new THREE.SphereGeometry(2.8, 16, 16),
            new THREE.MeshStandardMaterial({ color: 0x991b1b, emissive: 0x7f1d1d, emissiveIntensity: 0.6 })
        );
        rightVent.scale.set(1.0, 1.3, 0.85);
        rightVent.position.set(1.2, -0.6, 0.2);
        heartMesh.add(rightVent);

        const atria = new THREE.Mesh(new THREE.SphereGeometry(2.4, 14, 14), arteryMat);
        atria.position.set(0, 1.8, -0.2);
        heartMesh.add(atria);
        sceneBody.add(heartMesh);

        // Systemic Arterial Highway (Ascending Aorta Arch & Bifurcations)
        const createTube = (pts, mat, r) => {
            const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)));
            const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 36, r, 8, false), mat);
            sceneBody.add(tube);
            return curve;
        };

        aorticCurve = createTube([
            [0, 28, 2.4], [1.8, 33, 1.8], [1.2, 36.5, 0], [-1.4, 34, -1.2],
            [-1.2, 22, -0.8], [-1.0, 8, -0.8], [-1.4, -4, -0.5], [-5.2, -18, 0],
            [-6.8, -32, 0], [-7.2, -50, 0]
        ], arteryMat, 1.35);

        venaCavaCurve = createTube([
            [1.8, -50, 0], [2.2, -32, 0], [1.8, -18, 0], [1.2, -4, 0],
            [1.2, 10, 0], [2.2, 26, 1.2], [2.0, 37, 0], [0, 46, 0]
        ], veinMat, 1.4);

        // Branching Great Vessels: Carotids to brain & Subclavians to arms
        createTube([[-1.2, 36.5, 0], [-3.0, 44, 0.5], [-1.5, 50, 0]], arteryMat, 0.75); // L Carotid
        createTube([[1.2, 36.5, 0], [3.0, 44, 0.5], [1.5, 50, 0]], arteryMat, 0.75);   // R Carotid
        createTube([[-1.2, 35, 0], [-9, 32, 0], [-18, 25, 0], [-22, 6, 0]], arteryMat, 0.7); // L Subclavian
        createTube([[1.2, 35, 0], [9, 32, 0], [18, 25, 0], [22, 6, 0]], arteryMat, 0.7);   // R Subclavian
        createTube([[-1.4, -4, -0.5], [4.8, -18, 0], [6.8, -32, 0], [7.2, -50, 0]], arteryMat, 1.0); // R Iliac/Femoral

        // 7. Anatomical Internal Organs
        // Lungs: Left & Right Lobes with Branching Bronchial Trees
        [-1, 1].forEach(side => {
            const lung = new THREE.Mesh(
                new THREE.SphereGeometry(4.8, 18, 18),
                new THREE.MeshStandardMaterial({
                    color: 0x0284c7,
                    emissive: 0x0369a1,
                    emissiveIntensity: 0.35,
                    transparent: true,
                    opacity: 0.55
                })
            );
            lung.position.set(side * 6.8, 28, 0.8);
            lung.scale.set(0.9, 1.6, 0.85);
            sceneBody.add(lung);
        });

        // Liver (Hepatic Parenchyma Wedge)
        const liverGeo = new THREE.ConeGeometry(5.8, 7.5, 16);
        const liverMesh = new THREE.Mesh(
            liverGeo,
            new THREE.MeshStandardMaterial({
                color: 0xf59e0b,
                emissive: 0xd97706,
                emissiveIntensity: 0.45,
                transparent: true,
                opacity: 0.78
            })
        );
        liverMesh.position.set(4.6, 15, 1.8);
        liverMesh.rotation.z = Math.PI / 1.8;
        liverMesh.scale.set(1.1, 0.9, 0.8);
        sceneBody.add(liverMesh);

        // Kidneys (Bilateral Bean-shaped Renal Cortex)
        [-1, 1].forEach(side => {
            const kidney = new THREE.Mesh(
                new THREE.SphereGeometry(2.5, 16, 16),
                new THREE.MeshStandardMaterial({
                    color: 0x10b981,
                    emissive: 0x059669,
                    emissiveIntensity: 0.45,
                    transparent: true,
                    opacity: 0.82
                })
            );
            kidney.position.set(side * 4.6, 8, -1.8);
            kidney.scale.set(0.75, 1.35, 0.85);
            sceneBody.add(kidney);
        });

        // Target Tissue: Solid Tumor Mass with Angiogenic Neovascularization (EPR Effect)
        const tumorGroup = new THREE.Group();
        tumorGroup.position.set(-6.5, -12, 1.8);

        const tumorCore = new THREE.Mesh(
            new THREE.DodecahedronGeometry(3.6, 2),
            new THREE.MeshStandardMaterial({
                color: 0xf43f5e,
                emissive: 0xbe123c,
                emissiveIntensity: 0.8,
                roughness: 0.6
            })
        );
        tumorGroup.add(tumorCore);

        // Chaotic tortuous tumor microvessels
        for (let i = 0; i < 6; i++) {
            const ang = (i / 6) * Math.PI * 2;
            const neoCurve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(Math.cos(ang) * 4.2, Math.sin(ang) * 3.5, 0),
                new THREE.Vector3(Math.cos(ang + 0.4) * 2.5, Math.sin(ang + 0.4) * 2.2, 1.2),
                new THREE.Vector3(0, 0, 0)
            ]);
            const neoTube = new THREE.Mesh(
                new THREE.TubeGeometry(neoCurve, 12, 0.35, 6, false),
                new THREE.MeshStandardMaterial({ color: 0xfb7185, emissive: 0xe11d48 })
            );
            tumorGroup.add(neoTube);
        }
        sceneBody.add(tumorGroup);

        // Interactive Organ Markers & Click Rings
        const organSpecs = [
            { id: 'bloodstream', label: 'Heart & Aorta', pos: [0, 27, 3.2], color: 0xef4444, size: 3.6 },
            { id: 'lungs', label: 'Pulmonary Bed', pos: [-7.2, 28, 1.2], color: 0x38bdf8, size: 4.2 },
            { id: 'liver', label: 'Liver (RES)', pos: [4.8, 15, 2.0], color: 0xf59e0b, size: 4.5 },
            { id: 'kidneys', label: 'Kidneys (Renal Filter)', pos: [-4.6, 8, -1.8], color: 0x10b981, size: 3.2 },
            { id: 'target_tissue', label: 'Target Tissue (Tumor)', pos: [-6.5, -12, 2.0], color: 0xf43f5e, size: 4.0 },
            { id: 'skin', label: 'Dermal Microvasculature', pos: [18, 18, 0], color: 0xa855f7, size: 2.8 },
            { id: 'cellular_environment', label: 'Endothelial Cell', pos: [2.5, 4, 1.5], color: 0x06b6d4, size: 2.5 }
        ];

        organSpecs.forEach(spec => {
            const group = new THREE.Group();
            group.position.set(...spec.pos);

            const sphere = new THREE.Mesh(
                new THREE.SphereGeometry(spec.size * 0.4, 16, 16),
                new THREE.MeshStandardMaterial({
                    color: spec.color,
                    emissive: spec.color,
                    emissiveIntensity: 0.6,
                    transparent: true,
                    opacity: 0.9
                })
            );
            group.add(sphere);

            const ringGeo = new THREE.RingGeometry(spec.size * 1.1, spec.size * 1.3, 32);
            const ringMat = new THREE.MeshBasicMaterial({
                color: spec.color,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.7
            });
            const ring = new THREE.Mesh(ringGeo, ringMat);
            group.add(ring);

            group.userData = { id: spec.id, label: spec.label, ring: ring };
            sceneBody.add(group);
            organMarkers[spec.id] = group;
        });

        // 8. Dynamic Flowing Nanoparticles Streaming Across Arteries
        const npCount = 200;
        const npGeo = new THREE.SphereGeometry(0.85, 10, 10);
        const npMat = new THREE.MeshStandardMaterial({
            color: 0x22d3ee,
            emissive: 0x06b6d4,
            emissiveIntensity: 0.9
        });

        for (let i = 0; i < npCount; i++) {
            const mesh = new THREE.Mesh(npGeo, npMat);
            const useAorta = (i % 3 !== 0);
            mesh.userData = {
                t: Math.random(),
                speed: 0.003 + Math.random() * 0.005,
                curve: useAorta ? aorticCurve : venaCavaCurve,
                jitter: (Math.random() - 0.5) * 1.5
            };
            sceneBody.add(mesh);
            nanoParticles.push(mesh);
        }
    }

    function buildBloodVesselModel() {
        const vesselLength = 120;
        const vesselRadius = 22;

        // Outer Vascular Tunica Adventitia Wall
        const wallMat = new THREE.MeshStandardMaterial({
            color: 0x881337,
            side: THREE.BackSide,
            transparent: true,
            opacity: 0.42,
            roughness: 0.6
        });
        const vesselCylinder = new THREE.Mesh(
            new THREE.CylinderGeometry(vesselRadius, vesselRadius, vesselLength, 36, 1, true),
            wallMat
        );
        vesselCylinder.rotation.z = Math.PI / 2;
        sceneVessel.add(vesselCylinder);

        // Glycocalyx Layer & Endothelial Cell Monolayer
        const endoMat = new THREE.MeshStandardMaterial({
            color: 0xfca5a5,
            transparent: true,
            opacity: 0.4,
            roughness: 0.8
        });

        for (let i = 0; i < 34; i++) {
            const theta = (i / 34) * Math.PI * 2;
            const x = (Math.random() - 0.5) * vesselLength * 0.9;
            const y = Math.cos(theta) * (vesselRadius - 0.5);
            const z = Math.sin(theta) * (vesselRadius - 0.5);

            const cellTile = new THREE.Mesh(new THREE.BoxGeometry(8, 0.8, 5), endoMat);
            cellTile.position.set(x, y, z);
            cellTile.rotation.x = theta;
            sceneVessel.add(cellTile);
        }

        // Trans-endothelial Fenestrations / EPR Pores (~150nm scaled gaps)
        const poreMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee, wireframe: true });
        for (let i = 0; i < 6; i++) {
            const pore = new THREE.Mesh(new THREE.TorusGeometry(3.2, 0.5, 8, 16), poreMat);
            pore.position.set((i - 2.5) * 14, -vesselRadius + 0.6, 6);
            pore.rotation.x = Math.PI / 2;
            sceneVessel.add(pore);
        }

        // Extravascular Tumor Stroma Collagen Network outside vessel
        const stromaMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e, transparent: true, opacity: 0.2 });
        for (let i = 0; i < 12; i++) {
            const fiber = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 25, 6), stromaMat);
            fiber.position.set((Math.random() - 0.5) * vesselLength * 0.8, -vesselRadius - 8, (Math.random() - 0.5) * 20);
            fiber.rotation.set(Math.random(), Math.random(), Math.random());
            sceneVessel.add(fiber);
        }

        // Parametric Biconcave Erythrocytes (RBCs)
        const rbcGeo = createBiconcaveRbcGeometry();
        const rbcMat = new THREE.MeshStandardMaterial({
            color: 0xdc2626,
            roughness: 0.25,
            metalness: 0.15
        });

        const rbcCount = 42;
        for (let i = 0; i < rbcCount; i++) {
            const rbcMesh = new THREE.Mesh(rbcGeo, rbcMat);
            rbcMesh.position.set(
                (Math.random() - 0.5) * vesselLength,
                (Math.random() - 0.5) * (vesselRadius * 1.3),
                (Math.random() - 0.5) * (vesselRadius * 1.3)
            );
            rbcMesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
            rbcMesh.userData = {
                vx: 0.7 + Math.random() * 0.9,
                rotSpeedX: (Math.random() - 0.5) * 0.04,
                rotSpeedY: (Math.random() - 0.5) * 0.05
            };
            sceneVessel.add(rbcMesh);
            rbcParticles.push(rbcMesh);
        }

        // Circulating Nanoparticles with PEG Corona Halos
        const npVesselCount = 85;
        const npCoreMat = new THREE.MeshStandardMaterial({
            color: 0x22d3ee,
            emissive: 0x0891b2,
            emissiveIntensity: 0.85
        });
        const npCoronaMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.45
        });

        for (let i = 0; i < npVesselCount; i++) {
            const npGroup = new THREE.Group();
            const core = new THREE.Mesh(new THREE.SphereGeometry(1.2, 12, 12), npCoreMat);
            const corona = new THREE.Mesh(new THREE.SphereGeometry(1.8, 8, 8), npCoronaMat);
            npGroup.add(core);
            npGroup.add(corona);

            npGroup.position.set(
                (Math.random() - 0.5) * vesselLength,
                (Math.random() - 0.5) * (vesselRadius * 1.5),
                (Math.random() - 0.5) * (vesselRadius * 1.5)
            );
            npGroup.userData = {
                vx: 0.9 + Math.random() * 1.3,
                vy: (Math.random() - 0.5) * 0.2,
                vz: (Math.random() - 0.5) * 0.2
            };
            sceneVessel.add(npGroup);
            nanoParticles.push(npGroup);
        }
    }

    function buildCellularUptakeModel() {
        // 1. Dual-Layer Phospholipid Bilayer Array
        const bilayerGroup = new THREE.Group();
        const headGeo = new THREE.SphereGeometry(1.2, 8, 8);
        const topHeadMat = new THREE.MeshStandardMaterial({ color: 0x06b6d4, emissive: 0x0891b2, emissiveIntensity: 0.4 });
        const bottomHeadMat = new THREE.MeshStandardMaterial({ color: 0x4f46e5, emissive: 0x3730a3, emissiveIntensity: 0.3 });

        for (let x = -36; x <= 36; x += 3.6) {
            for (let z = -26; z <= 26; z += 3.6) {
                // Outer leaflet (Extracellular)
                const topHead = new THREE.Mesh(headGeo, topHeadMat);
                topHead.position.set(x, -6, z);
                bilayerGroup.add(topHead);

                // Inner leaflet (Cytosolic)
                const bottomHead = new THREE.Mesh(headGeo, bottomHeadMat);
                bottomHead.position.set(x, -11, z);
                bilayerGroup.add(bottomHead);
            }
        }
        sceneCellular.add(bilayerGroup);

        // 2. Transmembrane Receptor Proteins (Integrin / EGFR Dimers)
        const receptorMat = new THREE.MeshStandardMaterial({
            color: 0xf59e0b,
            emissive: 0xd97706,
            emissiveIntensity: 0.6
        });
        for (let i = 0; i < 8; i++) {
            const rx = (i - 3.5) * 9;
            const rGroup = new THREE.Group();
            const stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 8, 8), receptorMat);
            stalk.position.set(rx, -7, 0);
            rGroup.add(stalk);

            const pocket = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.5, 6, 12), receptorMat);
            pocket.position.set(rx, -2.6, 0);
            pocket.rotation.x = Math.PI / 2;
            rGroup.add(pocket);

            sceneCellular.add(rGroup);
            receptorMeshes.push(rGroup);
        }

        // 3. Dynamic Clathrin Geodesic Cage (Invagination Basket)
        const clathrinGeo = new THREE.IcosahedronGeometry(11, 1);
        const clathrinMat = new THREE.MeshStandardMaterial({
            color: 0x8b5cf6,
            wireframe: true,
            side: THREE.DoubleSide
        });
        clathrinBasket = new THREE.Mesh(clathrinGeo, clathrinMat);
        clathrinBasket.position.set(0, -12, 0);
        clathrinBasket.scale.set(1, 0.7, 1);
        sceneCellular.add(clathrinBasket);

        // 4. Budding Endocytic Vesicle
        const vesicleGeo = new THREE.SphereGeometry(8.5, 20, 20);
        const vesicleMat = new THREE.MeshStandardMaterial({
            color: 0x06b6d4,
            transparent: true,
            opacity: 0.5,
            wireframe: true
        });
        membraneVesicle = new THREE.Mesh(vesicleGeo, vesicleMat);
        membraneVesicle.position.set(0, -28, 0);
        sceneCellular.add(membraneVesicle);

        // 5. Intracellular Acidic Lysosome
        const lysoGeo = new THREE.SphereGeometry(13, 20, 20);
        const lysoMat = new THREE.MeshStandardMaterial({
            color: 0xef4444,
            emissive: 0xb91c1c,
            emissiveIntensity: 0.45,
            transparent: true,
            opacity: 0.42
        });
        const lysosome = new THREE.Mesh(lysoGeo, lysoMat);
        lysosome.position.set(26, -34, -10);
        sceneCellular.add(lysosome);

        // 6. Targeted Nanoparticle Docking and Uptake
        const uptakingNp = new THREE.Mesh(
            new THREE.SphereGeometry(4.4, 24, 24),
            new THREE.MeshStandardMaterial({
                color: 0x22d3ee,
                emissive: 0x0891b2,
                emissiveIntensity: 0.75,
                metalness: 0.2
            })
        );
        uptakingNp.position.set(0, 16, 0);
        uptakingNp.userData = { animPhase: 0 };
        sceneCellular.add(uptakingNp);
        sceneCellular.userData.np = uptakingNp;
    }

    function buildNanoparticleReleaseModel() {
        // 1. Degradable Polymeric / Liposomal Core Matrix
        const coreGeo = new THREE.IcosahedronGeometry(16, 3);
        const coreMat = new THREE.MeshStandardMaterial({
            color: 0x6366f1,
            emissive: 0x4338ca,
            emissiveIntensity: 0.5,
            roughness: 0.4,
            transparent: true,
            opacity: 0.82
        });
        coreMesh = new THREE.Mesh(coreGeo, coreMat);
        sceneRelease.add(coreMesh);

        // 2. Exterior PEG Corona Brush Layer (Flexible Radiating Polymer Chains)
        const pegGroup = new THREE.Group();
        const brushMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.4 });
        for (let i = 0; i < 90; i++) {
            const u = Math.random();
            const v = Math.random();
            const theta = u * 2.0 * Math.PI;
            const phi = Math.acos(2.0 * v - 1.0);
            const r1 = 15.8;
            const r2 = 21.5 + Math.random() * 3.5;

            const p1 = new THREE.Vector3(r1 * Math.sin(phi) * Math.cos(theta), r1 * Math.sin(phi) * Math.sin(theta), r1 * Math.cos(phi));
            const p2 = new THREE.Vector3(r2 * Math.sin(phi) * Math.cos(theta), r2 * Math.sin(phi) * Math.sin(theta), r2 * Math.cos(phi));

            const hairCurve = new THREE.CatmullRomCurve3([
                p1,
                new THREE.Vector3().lerpVectors(p1, p2, 0.5).add(new THREE.Vector3((Math.random() - 0.5) * 2, (Math.random() - 0.5) * 2, 0)),
                p2
            ]);
            const hair = new THREE.Mesh(new THREE.TubeGeometry(hairCurve, 8, 0.25, 4, false), brushMat);
            pegGroup.add(hair);
        }
        sceneRelease.add(pegGroup);

        // 3. Encapsulated Drug Payload Crystals & Korsmeyer-Peppas Diffusion Cloud
        const drugCount = 150;
        const drugGeo = new THREE.SphereGeometry(0.95, 10, 10);
        const drugMat = new THREE.MeshStandardMaterial({
            color: 0xfbbf24,
            emissive: 0xd97706,
            emissiveIntensity: 0.95
        });

        for (let i = 0; i < drugCount; i++) {
            const mol = new THREE.Mesh(drugGeo, drugMat);
            const dist = 3.5 + Math.random() * 13.5;
            const u = Math.random();
            const v = Math.random();
            const theta = u * 2.0 * Math.PI;
            const phi = Math.acos(2.0 * v - 1.0);
            const x = dist * Math.sin(phi) * Math.cos(theta);
            const y = dist * Math.sin(phi) * Math.sin(theta);
            const z = dist * Math.cos(phi);

            mol.position.set(x, y, z);
            mol.userData = {
                origDist: dist,
                dir: new THREE.Vector3(x, y, z).normalize(),
                speed: 0.15 + Math.random() * 0.3
            };
            sceneRelease.add(mol);
            drugMolecules.push(mol);
        }
    }

    // -------------------------------------------------------------
    // Multi-View Switcher Logic
    // -------------------------------------------------------------
    function switchViewMode(mode) {
        SimState.activeViewMode = mode;

        if (elements.viewModeButtons) {
            elements.viewModeButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.view === mode);
            });
        }

        if (sceneBody) sceneBody.visible = (mode === 'body');
        if (sceneVessel) sceneVessel.visible = (mode === 'vessel');
        if (sceneCellular) sceneCellular.visible = (mode === 'cellular');
        if (sceneRelease) sceneRelease.visible = (mode === 'release');

        resetCamera();
        if (mode === 'body') {
            focusRegion(SimState.selectedRegionId);
        }
    }

    function focusRegion(regionId) {
        SimState.selectedRegionId = regionId;
        if (elements.regionSelect) elements.regionSelect.value = regionId;

        const marker = organMarkers[regionId];
        if (marker && SimState.activeViewMode === 'body') {
            desiredTarget = {
                x: marker.position.x,
                y: marker.position.y,
                z: marker.position.z
            };
            desiredRadius = 60;
        }
        updateRegionInfoPanel(regionId);
    }

    // -------------------------------------------------------------
    // Render Loop & Physics Animation
    // -------------------------------------------------------------
    function renderLoop() {
        animationFrameId = requestAnimationFrame(renderLoop);

        const delta = 0.016 * SimState.speed;

        // Auto-Spin 360° if active
        if (autoRotate) {
            spherical.theta += 0.006 * SimState.speed;
        }

        updateCameraPosition();

        // 1. Human Body View Dynamics: Heartbeat pulse & vascular flow
        if (sceneBody && sceneBody.visible) {
            heartPulseTime += delta * 6.0;
            if (heartMesh) {
                const s = 1.0 + Math.pow(Math.sin(heartPulseTime), 4) * 0.12;
                heartMesh.scale.set(s, s, s);
            }

            nanoParticles.forEach(np => {
                if (!np.userData.curve) return;
                np.userData.t = (np.userData.t + np.userData.speed * delta * 14) % 1.0;
                const pt = np.userData.curve.getPointAt(np.userData.t);
                np.position.set(pt.x + np.userData.jitter, pt.y, pt.z + np.userData.jitter);
            });

            Object.values(organMarkers).forEach(m => {
                if (m.userData.ring) {
                    const scale = 1.0 + Math.sin(Date.now() * 0.004) * 0.12;
                    m.userData.ring.scale.set(scale, scale, 1);
                }
            });
        }

        // 2. Capillary Vessel Flow: Biconcave RBC tumbling & shear flow
        if (sceneVessel && sceneVessel.visible) {
            rbcParticles.forEach(rbc => {
                rbc.position.x += rbc.userData.vx * delta * 36;
                if (rbc.userData.rotSpeedX) rbc.rotation.x += rbc.userData.rotSpeedX;
                if (rbc.userData.rotSpeedY) rbc.rotation.y += rbc.userData.rotSpeedY;
                if (rbc.position.x > 60) rbc.position.x = -60;
            });

            nanoParticles.forEach(np => {
                if (!np.userData.vx) return;
                np.position.x += np.userData.vx * delta * 46;
                np.position.y += (Math.random() - 0.5) * 0.4;
                np.position.z += (Math.random() - 0.5) * 0.4;
                if (np.position.x > 60) np.position.x = -60;
            });
        }

        // 3. Cellular Uptake: Endocytic invagination & trafficking
        if (sceneCellular && sceneCellular.visible && sceneCellular.userData.np) {
            const uNp = sceneCellular.userData.np;
            uNp.userData.animPhase = (uNp.userData.animPhase + delta * 0.22) % 1.0;
            const p = uNp.userData.animPhase;

            if (p < 0.25) {
                const subP = p / 0.25;
                uNp.position.set(0, 16 - subP * 14, 0);
                uNp.scale.set(1, 1, 1);
                if (clathrinBasket) clathrinBasket.scale.set(1, 0.6 + subP * 0.4, 1);
            } else if (p < 0.45) {
                uNp.position.set(0, 2, 0); // Receptor docked state
            } else if (p < 0.7) {
                const subP = (p - 0.45) / 0.25;
                uNp.position.set(0, 2 - subP * 24, 0);
                if (membraneVesicle) {
                    membraneVesicle.position.set(0, 2 - subP * 24, 0);
                    membraneVesicle.scale.set(1 + subP * 0.2, 1 + subP * 0.2, 1 + subP * 0.2);
                }
            } else {
                const subP = (p - 0.7) / 0.3;
                uNp.position.set(subP * 24, -22 - subP * 12, -subP * 10);
                uNp.scale.set(1 - subP * 0.4, 1 - subP * 0.4, 1 - subP * 0.4);
            }
        }

        // 4. Drug Release: Korsmeyer-Peppas Diffusion plume
        if (sceneRelease && sceneRelease.visible) {
            if (coreMesh) coreMesh.rotation.y += delta * 0.25;

            const currentRelFraction = SimState.evaluationResult ?
                (SimState.evaluationResult.model_results.drug_release_kinetics.final_release_pct / 100.0) : 0.4;

            drugMolecules.forEach((mol, idx) => {
                if (idx / drugMolecules.length < currentRelFraction) {
                    mol.position.addScaledVector(mol.userData.dir, mol.userData.speed * delta * 22);
                    if (mol.position.length() > 42) {
                        mol.position.copy(mol.userData.dir).multiplyScalar(mol.userData.origDist);
                    }
                } else {
                    mol.position.copy(mol.userData.dir).multiplyScalar(Math.min(14, mol.userData.origDist));
                }
            });
        }

        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }
    }

    function initFallbackCanvas() {
        const canvas = elements.fallbackCanvas;
        if (!canvas) return;
        canvas.style.display = 'block';
        if (elements.threeCanvas) elements.threeCanvas.style.display = 'none';

        const ctx = canvas.getContext('2d');
        canvas.width = canvas.clientWidth || 800;
        canvas.height = canvas.clientHeight || 480;

        function fallbackLoop() {
            if (!SimState.isRunning && ctx) {
                const w = canvas.width;
                const h = canvas.height;
                ctx.clearRect(0, 0, w, h);
                ctx.fillStyle = '#06030f';
                ctx.fillRect(0, 0, w, h);

                ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
                ctx.lineWidth = 2;
                ctx.strokeRect(w * 0.35, h * 0.1, w * 0.3, h * 0.8);

                ctx.fillStyle = '#f1efff';
                ctx.font = '14px Space Grotesk, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('ANATOMICAL CIRCULATION SCHEMATIC (FALLBACK)', w / 2, h * 0.08);

                const nodes = [
                    { label: 'Bloodstream', y: 0.25, color: '#ef4444' },
                    { label: 'Lungs', y: 0.35, color: '#38bdf8' },
                    { label: 'Liver', y: 0.48, color: '#f59e0b' },
                    { label: 'Kidneys', y: 0.60, color: '#10b981' },
                    { label: 'Target Tissue', y: 0.72, color: '#f43f5e' }
                ];

                nodes.forEach(n => {
                    const ny = h * n.y;
                    ctx.fillStyle = n.color;
                    ctx.beginPath();
                    ctx.arc(w / 2, ny, 16, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.fillStyle = '#ffffff';
                    ctx.fillText(n.label, w / 2, ny + 28);
                });
            }
            requestAnimationFrame(fallbackLoop);
        }
        fallbackLoop();
    }

    // -------------------------------------------------------------
    // Simulation Execution Engine & 8-Stage Controller
    // -------------------------------------------------------------
    let simInterval = null;

    function startSimulation() {
        if (!elements.btnStart) initDomReferences();
        if (!SimState.evaluationResult) {
            evaluateCurrentFormulation().then(() => doStart());
        } else {
            doStart();
        }
    }

    function doStart() {
        const totalDuration = parseFloat(elements.inputDuration ? elements.inputDuration.value : 48.0) || 48.0;
        if (SimState.currentSimTimeHours >= totalDuration) {
            SimState.currentSimTimeHours = 0.0;
            SimState.currentStageIndex = 0;
            updateStageDisplay(0);
        }
        SimState.isRunning = true;
        SimState.isPaused = false;
        updateControlsUi();
        addEventLog('SIMULATION_STARTED', 'Started Multi-Scale Human Body Nanomedicine Simulation.', 'COMPUTED - ODE');

        if (simInterval) clearInterval(simInterval);
        simInterval = setInterval(simulationTick, 400 / SimState.speed);
    }

    function pauseSimulation() {
        SimState.isPaused = true;
        clearInterval(simInterval);
        updateControlsUi();
        addEventLog('SIMULATION_PAUSED', `Paused at stage ${SimState.currentStageIndex + 1} (${SimState.currentSimTimeHours.toFixed(1)} hrs).`, 'USER');
    }

    function resumeSimulation() {
        SimState.isPaused = false;
        updateControlsUi();
        simInterval = setInterval(simulationTick, 400 / SimState.speed);
        addEventLog('SIMULATION_RESUMED', 'Resumed simulation execution.', 'USER');
    }

    function resetSimulation() {
        clearInterval(simInterval);
        SimState.isRunning = false;
        SimState.isPaused = false;
        SimState.currentStageIndex = 0;
        SimState.currentSimTimeHours = 0.0;
        updateControlsUi();
        updateStageDisplay(0);
        updateTelemetryCards(0);
        addEventLog('SIMULATION_RESET', 'Reset simulation state to baseline t = 0.0 h.', 'USER');
    }

    function setSpeed(speedVal) {
        SimState.speed = parseFloat(speedVal) || 1.0;
        if (elements.speedButtons) {
            elements.speedButtons.forEach(b => {
                b.classList.toggle('active', parseFloat(b.dataset.speed) === SimState.speed);
            });
        }
        if (SimState.isRunning && !SimState.isPaused) {
            clearInterval(simInterval);
            simInterval = setInterval(simulationTick, 400 / SimState.speed);
        }
    }

    function simulationTick() {
        if (!SimState.isRunning || SimState.isPaused) return;

        SimState.currentSimTimeHours += SimState.timeStepHours;
        const totalDuration = parseFloat(elements.inputDuration ? elements.inputDuration.value : 48.0) || 48.0;

        const stagesCount = 8;
        const stageDuration = totalDuration / stagesCount;
        const expectedStage = Math.min(stagesCount - 1, Math.floor(SimState.currentSimTimeHours / stageDuration));

        if (expectedStage !== SimState.currentStageIndex) {
            SimState.currentStageIndex = expectedStage;
            updateStageDisplay(expectedStage);
            const stageData = SimState.stagesData[expectedStage];
            if (stageData) {
                const badgeType = stageData.is_quantitative_prediction ? 'COMPUTED - MODEL' : 'CONCEPTUAL - BIO';
                addEventLog(`STAGE_${expectedStage + 1}_ENTERED`, `Transitioned to: ${stageData.name}`, badgeType);
            }
        }

        updateTelemetryCards(SimState.currentSimTimeHours);

        if (SimState.autoAdvance) {
            if (SimState.currentStageIndex === 1 && SimState.activeViewMode !== 'vessel') switchViewMode('vessel');
            else if (SimState.currentStageIndex === 4 && SimState.activeViewMode !== 'cellular') switchViewMode('cellular');
            else if (SimState.currentStageIndex === 5 && SimState.activeViewMode !== 'release') switchViewMode('release');
            else if ((SimState.currentStageIndex === 0 || SimState.currentStageIndex === 7) && SimState.activeViewMode !== 'body') switchViewMode('body');
        }

        if (SimState.currentSimTimeHours >= totalDuration) {
            clearInterval(simInterval);
            SimState.isRunning = false;
            updateControlsUi();
            addEventLog('SIMULATION_COMPLETED', `Completed full journey through human body (${totalDuration.toFixed(1)} hrs).`, 'COMPUTED - ODE');
        }
    }

    function setStage(index) {
        SimState.currentStageIndex = index;
        const totalDuration = parseFloat(elements.inputDuration ? elements.inputDuration.value : 48.0) || 48.0;
        const stagesCount = 8;
        const stageDuration = totalDuration / stagesCount;
        SimState.currentSimTimeHours = Math.min(totalDuration, index * stageDuration);

        updateStageDisplay(index);
        updateTelemetryCards(SimState.currentSimTimeHours);

        const stageData = SimState.stagesData[index];
        if (stageData) {
            const badgeType = stageData.is_quantitative_prediction ? 'COMPUTED - MODEL' : 'CONCEPTUAL - BIO';
            addEventLog(`STAGE_${index + 1}_ENTERED`, `Transitioned to: ${stageData.name}`, badgeType);
        }
    }

    function updateStageDisplay(index) {
        if (elements.stageSteps) {
            elements.stageSteps.forEach((st, i) => {
                st.classList.toggle('active', i === index);
                st.classList.toggle('completed', i < index);
            });
        }

        if (elements.progressBar) {
            const pct = Math.min(100, (index / 7) * 100);
            elements.progressBar.style.width = pct + '%';
        }

        const stage = SimState.stagesData[index] || DEFAULT_STAGES[index];
        if (!stage) return;

        if (elements.stageTitle) elements.stageTitle.textContent = stage.name;
        if (elements.stageBadge) {
            elements.stageBadge.textContent = stage.badge_text;
            elements.stageBadge.className = `badge badge-${stage.badge_type || 'live'}`;
        }
        if (elements.stageDesc) elements.stageDesc.textContent = stage.description;
        if (elements.stageMechanisms) elements.stageMechanisms.textContent = stage.scientific_mechanisms;
        if (elements.stageLimitations) elements.stageLimitations.textContent = stage.limitations;

        if (elements.hudStageBadge) {
            elements.hudStageBadge.textContent = `STAGE ${index + 1}: ${stage.key.toUpperCase()}`;
        }
    }

    function updateTelemetryCards(simTime) {
        if (elements.hudTimeBadge) elements.hudTimeBadge.textContent = `${simTime.toFixed(1)} hrs`;
        if (elements.kpiSimTime) elements.kpiSimTime.textContent = `${simTime.toFixed(1)} h`;

        const res = SimState.evaluationResult || computeLocalEvaluation(getCurrentFormulationValues());
        const kinetics = res.model_results.drug_release_kinetics;
        const colloidal = res.model_results.colloidal_index;
        const cytotox = res.model_results.cytotoxicity;

        const k = kinetics.k;
        const n = kinetics.n;
        const fraction = simTime <= 0 ? 0 : Math.min(1.0, k * Math.pow(simTime, n));
        const relPct = fraction * 100.0;
        const rate = simTime <= 0 ? 0 : Math.max(0, k * n * Math.pow(simTime, n - 1.0) * 100.0);
        const remPct = Math.max(0, 100.0 - relPct);

        if (elements.kpiReleasePct) elements.kpiReleasePct.textContent = `${relPct.toFixed(1)}%`;
        if (elements.kpiReleaseRate) elements.kpiReleaseRate.textContent = `${rate.toFixed(2)} %/h`;
        if (elements.kpiRemainingPct) elements.kpiRemainingPct.textContent = `${remPct.toFixed(1)}%`;
        if (elements.kpiReleaseMech) elements.kpiReleaseMech.textContent = kinetics.mechanism;

        if (elements.kpiZeta) elements.kpiZeta.textContent = `${colloidal.effective_zeta_mv.toFixed(1)} mV`;
        if (elements.kpiStabilityClass) {
            elements.kpiStabilityClass.textContent = colloidal.stability_class;
            elements.kpiStabilityClass.className = `kpi-sub badge badge-${colloidal.color_code || 'live'}`;
        }

        if (elements.kpiCytotox) {
            elements.kpiCytotox.textContent = cytotox.prediction;
            elements.kpiCytotox.className = `kpi-val ${cytotox.prediction === 'Toxic' ? 'text-danger' : 'text-accent'}`;
        }
        if (elements.kpiCytotoxConf) {
            const conf = cytotox.confidence ? `${(cytotox.confidence * 100).toFixed(0)}% conf` : (cytotox.domain_status || 'Active');
            elements.kpiCytotoxConf.textContent = conf;
        }

        if (elements.hudParticlesBadge) {
            const activeCount = Math.round(180 * (1.0 - (simTime / SimState.maxDurationHours) * 0.4));
            elements.hudParticlesBadge.textContent = `${Math.max(10, activeCount)} NPs / mL`;
        }
    }

    function updateControlsUi() {
        if (!elements.btnStart) return;
        elements.btnStart.disabled = SimState.isRunning && !SimState.isPaused;
        elements.btnPause.disabled = !SimState.isRunning || SimState.isPaused;
        elements.btnResume.disabled = !SimState.isPaused;
        elements.btnReset.disabled = !SimState.isRunning && SimState.currentSimTimeHours === 0;
    }

    function updateRegionInfoPanel(regionId) {
        const region = SimState.regionsData[regionId] || DEFAULT_REGIONS[regionId];
        if (!region) return;

        if (elements.regionTitle) elements.regionTitle.textContent = region.name;
        if (elements.regionCategory) elements.regionCategory.textContent = region.category;
        if (elements.regionInteractions) elements.regionInteractions.textContent = region.nanoparticle_interactions;
        if (elements.regionBarrier) elements.regionBarrier.textContent = region.barrier_description;
        if (elements.regionNatureBadge) elements.regionNatureBadge.textContent = region.scientific_classification;

        if (elements.hudRegionBadge) elements.hudRegionBadge.textContent = region.name.toUpperCase();

        if (elements.regionPropertiesList) {
            elements.regionPropertiesList.innerHTML = '';
            const props = region.physiological_properties || {};
            for (const [key, val] of Object.entries(props)) {
                const li = document.createElement('li');
                const cleanKey = key.replace(/_/g, ' ').toUpperCase();
                li.innerHTML = `<strong>${cleanKey}:</strong> <span>${val}</span>`;
                elements.regionPropertiesList.appendChild(li);
            }
        }
    }

    function getCurrentFormulationValues() {
        return {
            material: elements.inputMaterial ? elements.inputMaterial.value : 'PLGA',
            core_size_nm: parseFloat(elements.inputCoreSize ? elements.inputCoreSize.value : 80) || 80,
            hydrodynamic_size_nm: parseFloat(elements.inputHydroSize ? elements.inputHydroSize.value : 95) || 95,
            surface_coating: elements.inputCoating ? elements.inputCoating.value : 'PEG',
            surface_charge_mv: parseFloat(elements.inputZeta ? elements.inputZeta.value : -24.5) || -24.5,
            drug_name: elements.inputDrug ? elements.inputDrug.value : 'Paclitaxel',
            drug_loading_pct: parseFloat(elements.inputLoading ? elements.inputLoading.value : 12.0) || 12.0,
            k_release: parseFloat(elements.inputK ? elements.inputK.value : 0.18) || 0.18,
            n_release: parseFloat(elements.inputN ? elements.inputN.value : 0.55) || 0.55,
            target_tissue: elements.inputTarget ? elements.inputTarget.value : 'target_tissue',
            administration_route: elements.inputRoute ? elements.inputRoute.value : 'Intravenous',
            initial_concentration_ug_ml: parseFloat(elements.inputDose ? elements.inputDose.value : 50.0) || 50.0,
            temperature_c: parseFloat(elements.inputTemp ? elements.inputTemp.value : 37.0) || 37.0,
            ph: parseFloat(elements.inputPh ? elements.inputPh.value : 7.4) || 7.4,
            ionic_strength_m: parseFloat(elements.inputIonic ? elements.inputIonic.value : 0.154) || 0.154,
            exposure_time_hours: parseFloat(elements.inputDuration ? elements.inputDuration.value : 48.0) || 48.0,
            cell_name: elements.inputCell ? elements.inputCell.value : 'A549',
            assay: elements.inputAssay ? elements.inputAssay.value : 'MTT'
        };
    }

    async function evaluateCurrentFormulation() {
        const payload = getCurrentFormulationValues();
        SimState.maxDurationHours = payload.exposure_time_hours;

        // Apply local calculation immediately
        SimState.evaluationResult = computeLocalEvaluation(payload);
        updateTelemetryCards(SimState.currentSimTimeHours);
        updateReleaseChart(SimState.evaluationResult.model_results.drug_release_kinetics);

        try {
            if (elements.btnApplyConfig) elements.btnApplyConfig.textContent = 'Evaluating...';
            const res = await fetch('/api/human_body_sim/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                SimState.evaluationResult = data;
                renderDomainWarnings(data.warnings);
                updateReleaseChart(data.model_results.drug_release_kinetics);
                updateTelemetryCards(SimState.currentSimTimeHours);
                addEventLog('CONFIG_EVALUATED', `Evaluated: ${payload.material} (${payload.core_size_nm}nm) + ${payload.drug_name}.`, 'COMPUTED - MODEL');
            }
        } catch (err) {
            console.warn('Backend evaluation fallback active:', err);
            addEventLog('LOCAL_EVAL', 'Used client-side biophysical model.', 'OFFLINE');
        } finally {
            if (elements.btnApplyConfig) elements.btnApplyConfig.textContent = 'Apply & Evaluate Formulation';
        }
    }

    async function predictZetaPotential() {
        const payload = {
            Shape: 'Sphere',
            Core: elements.inputMaterial ? elements.inputMaterial.value : 'Silver',
            Size_nm: parseFloat(elements.inputCoreSize ? elements.inputCoreSize.value : 80) || 80,
            Medium: 'PBS pH 7.4',
            Ligand_SMILES: 'OCCO'
        };

        try {
            if (elements.btnPredictZeta) elements.btnPredictZeta.textContent = 'Predicting...';
            const res = await fetch('/api/predict/stability', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const data = await res.json();
                if (elements.inputZeta) elements.inputZeta.value = data.prediction;
                addEventLog('ML_PREDICT_ZETA', `Predicted Zeta: ${data.prediction} mV via Ridge model.`, 'COMPUTED - ML');
                evaluateCurrentFormulation();
            }
        } catch (err) {
            console.warn('ML Predict Zeta error:', err);
        } finally {
            if (elements.btnPredictZeta) elements.btnPredictZeta.textContent = '⚡ Predict via ML';
        }
    }

    function renderDomainWarnings(warnings) {
        if (!elements.domainWarningsCard || !elements.domainWarningsList) return;
        if (!warnings || warnings.length === 0) {
            elements.domainWarningsCard.style.display = 'none';
            return;
        }

        elements.domainWarningsCard.style.display = 'block';
        elements.domainWarningsList.innerHTML = '';
        warnings.forEach(w => {
            const li = document.createElement('li');
            li.className = `alert-item alert-${(w.level || 'info').toLowerCase()}`;
            li.innerHTML = `<strong>[${w.type}]</strong> ${w.message}`;
            elements.domainWarningsList.appendChild(li);
        });
    }

    function addEventLog(type, message, classification) {
        const timeStr = `${SimState.currentSimTimeHours.toFixed(1)}h`;
        SimState.events.unshift({ time: timeStr, type, message, classification });

        if (elements.eventLogContainer) {
            const div = document.createElement('div');
            div.className = 'hbs-event-item';
            div.innerHTML = `
                <div class="hbs-event-meta">
                    <span class="hbs-event-time">${timeStr}</span>
                    <span class="hbs-event-badge badge-small">${classification}</span>
                </div>
                <div class="hbs-event-msg">${message}</div>
            `;
            elements.eventLogContainer.prepend(div);

            while (elements.eventLogContainer.children.length > 30) {
                elements.eventLogContainer.removeChild(elements.eventLogContainer.lastChild);
            }
        }
    }

    function applyPreset(presetKey) {
        const p = FORMULATION_PRESETS[presetKey];
        if (!p) return;

        if (elements.inputMaterial) elements.inputMaterial.value = p.material;
        if (elements.inputCoreSize) elements.inputCoreSize.value = p.coreSize;
        if (elements.inputHydroSize) elements.inputHydroSize.value = p.hydroSize;
        if (elements.inputCoating) elements.inputCoating.value = p.coating;
        if (elements.inputZeta) elements.inputZeta.value = p.zeta;
        if (elements.inputDrug) elements.inputDrug.value = p.drug;
        if (elements.inputLoading) elements.inputLoading.value = p.loading;
        if (elements.inputK) elements.inputK.value = p.k;
        if (elements.inputN) elements.inputN.value = p.n;
        if (elements.inputTarget) elements.inputTarget.value = p.target;
        if (elements.inputRoute) elements.inputRoute.value = p.route;
        if (elements.inputDose) elements.inputDose.value = p.dose;
        if (elements.inputDuration) elements.inputDuration.value = p.duration;
        if (elements.inputCell) elements.inputCell.value = p.cell;
        if (elements.inputAssay) elements.inputAssay.value = p.assay;

        evaluateCurrentFormulation();
    }

    async function loadRegionsAndStages() {
        try {
            const [regRes, stageRes] = await Promise.all([
                fetch('/api/human_body_sim/regions'),
                fetch('/api/human_body_sim/stages')
            ]);
            if (regRes.ok) {
                const regData = await regRes.json();
                if (regData.regions) SimState.regionsData = regData.regions;
                populateRegionSelect();
            }
            if (stageRes.ok) {
                const sData = await stageRes.json();
                if (sData.stages) SimState.stagesData = sData.stages;
                updateStageDisplay(0);
            }
        } catch (err) {
            console.warn('Backend metadata load error:', err);
        }
    }

    function populateRegionSelect() {
        if (!elements.regionSelect) return;
        elements.regionSelect.innerHTML = '';
        for (const [id, reg] of Object.entries(SimState.regionsData)) {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = reg.name;
            elements.regionSelect.appendChild(opt);
        }
        elements.regionSelect.value = SimState.selectedRegionId;
        updateRegionInfoPanel(SimState.selectedRegionId);
    }

    function bindEventListeners() {
        if (elements.viewModeButtons) {
            elements.viewModeButtons.forEach(btn => {
                btn.addEventListener('click', () => switchViewMode(btn.dataset.view));
            });
        }

        if (elements.stageSteps) {
            elements.stageSteps.forEach((st, idx) => {
                st.addEventListener('click', () => setStage(idx));
            });
        }

        if (elements.btnStart) elements.btnStart.addEventListener('click', startSimulation);
        if (elements.btnPause) elements.btnPause.addEventListener('click', pauseSimulation);
        if (elements.btnResume) elements.btnResume.addEventListener('click', resumeSimulation);
        if (elements.btnReset) elements.btnReset.addEventListener('click', resetSimulation);

        if (elements.speedButtons) {
            elements.speedButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    elements.speedButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    SimState.speed = parseFloat(btn.dataset.speed) || 1.0;
                    if (SimState.isRunning && !SimState.isPaused) {
                        clearInterval(simInterval);
                        simInterval = setInterval(simulationTick, 400 / SimState.speed);
                    }
                });
            });
        }

        if (elements.autoAdvanceCheck) {
            elements.autoAdvanceCheck.addEventListener('change', e => {
                SimState.autoAdvance = e.target.checked;
            });
        }

        if (elements.regionSelect) {
            elements.regionSelect.addEventListener('change', e => {
                focusRegion(e.target.value);
            });
        }

        if (elements.presetSelect) {
            elements.presetSelect.addEventListener('change', e => {
                applyPreset(e.target.value);
            });
        }

        if (elements.btnApplyConfig) elements.btnApplyConfig.addEventListener('click', evaluateCurrentFormulation);
        if (elements.btnPredictZeta) elements.btnPredictZeta.addEventListener('click', predictZetaPotential);

        const bindSlider = (slider, display, suffix) => {
            if (slider && display) {
                slider.addEventListener('input', () => {
                    display.textContent = slider.value + suffix;
                });
                slider.addEventListener('change', evaluateCurrentFormulation);
            }
        };
        bindSlider(elements.inputPh, elements.inputPhVal, '');
        bindSlider(elements.inputTemp, elements.inputTempVal, ' °C');
        bindSlider(elements.inputIonic, elements.inputIonicVal, ' M');
        bindSlider(elements.inputDuration, elements.inputDurationVal, ' h');

        window.addEventListener('resize', () => {
            resizeViewport();
        });
    }

    function resizeViewport() {
        if (!elements.threeCanvas) return;
        const container = elements.canvasContainer || elements.threeCanvas.parentElement;
        const w = elements.threeCanvas.clientWidth || (container ? container.clientWidth : 0);
        const h = elements.threeCanvas.clientHeight || (container ? container.clientHeight : 0);

        if (w > 0 && h > 0) {
            if (renderer) renderer.setSize(w, h);
            if (camera) {
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
            }
        }
        if (releaseChart) releaseChart.resize();
    }

    function bootstrap() {
        initDomReferences();
        bindEventListeners();
        populateRegionSelect();
        updateStageDisplay(0);

        // Immediate default evaluation so telemetry cards have data immediately
        SimState.evaluationResult = computeLocalEvaluation(getCurrentFormulationValues());
        updateTelemetryCards(0);

        initReleaseChart();
        initThreeScene();

        // Background sync with API
        loadRegionsAndStages().then(() => {
            evaluateCurrentFormulation();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap);
    } else {
        bootstrap();
    }

    // -------------------------------------------------------------
    // Global API Expose
    // -------------------------------------------------------------
    window.NanoMedHumanBodySim = {
        start: startSimulation,
        pause: pauseSimulation,
        resume: resumeSimulation,
        reset: resetSimulation,
        setStage: setStage,
        setSpeed: setSpeed,
        switchView: switchViewMode,
        focusRegion: focusRegion,
        evaluate: evaluateCurrentFormulation,
        applyPreset: applyPreset,
        predictZeta: predictZetaPotential,
        setControlMode: setControlMode,
        nudgeCamera: nudgeCamera,
        zoomCamera: zoomCamera,
        toggleAutoRotate: toggleAutoRotate,
        resetCamera: resetCamera,
        activate: () => {
            initDomReferences();
            setTimeout(() => {
                resizeViewport();
                if (!releaseChart) initReleaseChart();
                if (SimState.evaluationResult) {
                    updateReleaseChart(SimState.evaluationResult.model_results.drug_release_kinetics);
                }
            }, 60);
        }
    };
})();
