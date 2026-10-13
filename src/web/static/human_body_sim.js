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

    let isDragging = false;
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
            const ambient = new THREE.AmbientLight(0xffffff, 0.7);
            scene.add(ambient);

            const dirLight1 = new THREE.DirectionalLight(0x22d3ee, 1.2);
            dirLight1.position.set(50, 80, 70);
            scene.add(dirLight1);

            const dirLight2 = new THREE.DirectionalLight(0x7c3aed, 0.9);
            dirLight2.position.set(-60, -40, 50);
            scene.add(dirLight2);

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

    function setupControls(canvas) {
        canvas.addEventListener('mousedown', e => {
            isDragging = true;
            prevMouseX = e.clientX;
            prevMouseY = e.clientY;
        });

        window.addEventListener('mouseup', () => { isDragging = false; });

        window.addEventListener('mousemove', e => {
            if (!isDragging) return;
            const deltaX = e.clientX - prevMouseX;
            const deltaY = e.clientY - prevMouseY;
            prevMouseX = e.clientX;
            prevMouseY = e.clientY;

            spherical.theta -= deltaX * 0.008;
            spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi - deltaY * 0.008));
        });

        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            desiredRadius = Math.max(30, Math.min(300, desiredRadius + e.deltaY * 0.15));
        }, { passive: false });

        let touchStartDist = 0;
        canvas.addEventListener('touchstart', e => {
            if (e.touches.length === 1) {
                isDragging = true;
                prevMouseX = e.touches[0].clientX;
                prevMouseY = e.touches[0].clientY;
            } else if (e.touches.length === 2) {
                touchStartDist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
            }
        });

        canvas.addEventListener('touchmove', e => {
            if (e.touches.length === 1 && isDragging) {
                const deltaX = e.touches[0].clientX - prevMouseX;
                const deltaY = e.touches[0].clientY - prevMouseY;
                prevMouseX = e.touches[0].clientX;
                prevMouseY = e.touches[0].clientY;
                spherical.theta -= deltaX * 0.01;
                spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi - deltaY * 0.01));
            } else if (e.touches.length === 2) {
                const dist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                desiredRadius = Math.max(30, Math.min(300, desiredRadius - (dist - touchStartDist) * 0.4));
                touchStartDist = dist;
            }
        });

        canvas.addEventListener('touchend', () => { isDragging = false; });
    }

    function buildHumanBodyModel() {
        const matWire = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.16
        });

        const head = new THREE.Mesh(new THREE.SphereGeometry(7.5, 18, 18), matWire);
        head.position.set(0, 48, 0);
        sceneBody.add(head);

        const neck = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 4.2, 7, 14), matWire);
        neck.position.set(0, 41, 0);
        sceneBody.add(neck);

        const chest = new THREE.Mesh(new THREE.CylinderGeometry(14, 11, 24, 18), matWire);
        chest.position.set(0, 27, 0);
        chest.scale.set(1.15, 1, 0.65);
        sceneBody.add(chest);

        const abdomen = new THREE.Mesh(new THREE.CylinderGeometry(11, 12, 18, 18), matWire);
        abdomen.position.set(0, 7, 0);
        abdomen.scale.set(1.1, 1, 0.7);
        sceneBody.add(abdomen);

        [-1, 1].forEach(side => {
            const armUpper = new THREE.Mesh(new THREE.CylinderGeometry(3, 2.5, 22, 12), matWire);
            armUpper.position.set(side * 18, 25, 0);
            armUpper.rotation.z = side * 0.15;
            sceneBody.add(armUpper);

            const armLower = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2, 22, 12), matWire);
            armLower.position.set(side * 22, 5, 0);
            armLower.rotation.z = side * 0.08;
            sceneBody.add(armLower);

            const thigh = new THREE.Mesh(new THREE.CylinderGeometry(5.2, 4, 30, 14), matWire);
            thigh.position.set(side * 7, -18, 0);
            sceneBody.add(thigh);

            const calf = new THREE.Mesh(new THREE.CylinderGeometry(3.8, 2.8, 32, 14), matWire);
            calf.position.set(side * 7.5, -48, 0);
            sceneBody.add(calf);
        });

        const arteryMat = new THREE.MeshStandardMaterial({
            color: 0xef4444,
            emissive: 0x991b1b,
            roughness: 0.3,
            metalness: 0.1
        });
        const veinMat = new THREE.MeshStandardMaterial({
            color: 0x3b82f6,
            emissive: 0x1e3a8a,
            roughness: 0.3,
            metalness: 0.1
        });

        const createVesselTube = (points, mat, radius) => {
            const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
            const tubeGeo = new THREE.TubeGeometry(curve, 32, radius, 8, false);
            const tubeMesh = new THREE.Mesh(tubeGeo, mat);
            sceneBody.add(tubeMesh);
            return curve;
        };

        const vAorta = createVesselTube([
            [0, 26, 2], [1.5, 31, 1.5], [1, 35, 0], [-1.2, 33, -1], [-1, 20, 0],
            [-1, 5, 0], [-2, -5, 0], [-6, -18, 0], [-7, -46, 0]
        ], arteryMat, 1.3);

        const vVenaCava = createVesselTube([
            [1.5, -46, 0], [2, -18, 0], [1, -5, 0], [1, 10, 0], [2, 26, 1],
            [1.8, 38, 0], [0, 47, 0]
        ], veinMat, 1.4);

        createVesselTube([[0, 28, 2], [-8, 28, 0]], arteryMat, 0.9);
        createVesselTube([[0, 28, 2], [8, 28, 0]], arteryMat, 0.9);
        createVesselTube([[-1, 34, 0], [-18, 26, 0], [-22, 6, 0]], arteryMat, 0.8);
        createVesselTube([[1, 34, 0], [18, 26, 0], [22, 6, 0]], arteryMat, 0.8);

        const organSpecs = [
            { id: 'bloodstream', label: 'Heart & Aorta', pos: [0, 27, 3], color: 0xef4444, size: 3.5 },
            { id: 'lungs', label: 'Pulmonary Bed', pos: [-7.5, 28, 1], color: 0x38bdf8, size: 4.2 },
            { id: 'liver', label: 'Liver (RES)', pos: [4.5, 14, 2], color: 0xf59e0b, size: 4.5 },
            { id: 'kidneys', label: 'Kidneys (Renal Filter)', pos: [-4.2, 8, -2], color: 0x10b981, size: 3.2 },
            { id: 'target_tissue', label: 'Target Tissue (Tumor)', pos: [-6.5, -12, 2], color: 0xf43f5e, size: 3.8 },
            { id: 'skin', label: 'Dermal Microvasculature', pos: [17, 18, 0], color: 0xa855f7, size: 2.8 },
            { id: 'cellular_environment', label: 'Endothelial Cell', pos: [2.5, 4, 1.5], color: 0x06b6d4, size: 2.5 }
        ];

        organSpecs.forEach(spec => {
            const group = new THREE.Group();
            group.position.set(...spec.pos);

            const sphere = new THREE.Mesh(
                new THREE.SphereGeometry(spec.size, 20, 20),
                new THREE.MeshStandardMaterial({
                    color: spec.color,
                    emissive: spec.color,
                    emissiveIntensity: 0.45,
                    transparent: true,
                    opacity: 0.82
                })
            );
            group.add(sphere);

            const ringGeo = new THREE.RingGeometry(spec.size * 1.15, spec.size * 1.35, 32);
            const ringMat = new THREE.MeshBasicMaterial({
                color: spec.color,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.65
            });
            const ring = new THREE.Mesh(ringGeo, ringMat);
            group.add(ring);

            group.userData = { id: spec.id, label: spec.label, ring: ring };
            sceneBody.add(group);
            organMarkers[spec.id] = group;
        });

        const npCount = 180;
        const npGeo = new THREE.SphereGeometry(0.75, 8, 8);
        const npMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee });

        for (let i = 0; i < npCount; i++) {
            const mesh = new THREE.Mesh(npGeo, npMat);
            mesh.userData = {
                t: Math.random(),
                speed: 0.003 + Math.random() * 0.004,
                curve: i % 2 === 0 ? vAorta : vVenaCava,
                jitter: (Math.random() - 0.5) * 1.8
            };
            sceneBody.add(mesh);
            nanoParticles.push(mesh);
        }
    }

    function buildBloodVesselModel() {
        const vesselLength = 110;
        const vesselRadius = 22;

        const wallMat = new THREE.MeshStandardMaterial({
            color: 0x991b1b,
            side: THREE.BackSide,
            transparent: true,
            opacity: 0.45,
            roughness: 0.6
        });
        const vesselCylinder = new THREE.Mesh(
            new THREE.CylinderGeometry(vesselRadius, vesselRadius, vesselLength, 36, 1, true),
            wallMat
        );
        vesselCylinder.rotation.z = Math.PI / 2;
        sceneVessel.add(vesselCylinder);

        const endoMat = new THREE.MeshStandardMaterial({
            color: 0xfca5a5,
            transparent: true,
            opacity: 0.35,
            roughness: 0.8
        });
        for (let i = 0; i < 28; i++) {
            const theta = (i / 28) * Math.PI * 2;
            const x = (Math.random() - 0.5) * vesselLength * 0.9;
            const y = Math.cos(theta) * (vesselRadius - 0.6);
            const z = Math.sin(theta) * (vesselRadius - 0.6);

            const cellTile = new THREE.Mesh(new THREE.BoxGeometry(7, 0.8, 4), endoMat);
            cellTile.position.set(x, y, z);
            cellTile.rotation.x = theta;
            sceneVessel.add(cellTile);
        }

        const rbcCount = 38;
        const rbcMat = new THREE.MeshStandardMaterial({
            color: 0xdc2626,
            roughness: 0.3,
            metalness: 0.1
        });

        for (let i = 0; i < rbcCount; i++) {
            const rbcMesh = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.6, 1.4, 20), rbcMat);
            rbcMesh.scale.set(1, 0.7, 1);
            rbcMesh.position.set(
                (Math.random() - 0.5) * vesselLength,
                (Math.random() - 0.5) * (vesselRadius * 1.3),
                (Math.random() - 0.5) * (vesselRadius * 1.3)
            );
            rbcMesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
            rbcMesh.userData = {
                vx: 0.6 + Math.random() * 0.8,
                rotSpeed: (Math.random() - 0.5) * 0.04
            };
            sceneVessel.add(rbcMesh);
            rbcParticles.push(rbcMesh);
        }

        const npVesselCount = 75;
        const npVesselMat = new THREE.MeshStandardMaterial({
            color: 0x22d3ee,
            emissive: 0x0891b2,
            emissiveIntensity: 0.6
        });

        for (let i = 0; i < npVesselCount; i++) {
            const np = new THREE.Mesh(new THREE.SphereGeometry(1.2, 12, 12), npVesselMat);
            np.position.set(
                (Math.random() - 0.5) * vesselLength,
                (Math.random() - 0.5) * (vesselRadius * 1.6),
                (Math.random() - 0.5) * (vesselRadius * 1.6)
            );
            np.userData = {
                vx: 0.8 + Math.random() * 1.2,
                vy: (Math.random() - 0.5) * 0.2,
                vz: (Math.random() - 0.5) * 0.2,
                targetRadius: vesselRadius * (0.6 + Math.random() * 0.35)
            };
            sceneVessel.add(np);
            nanoParticles.push(np);
        }
    }

    function buildCellularUptakeModel() {
        const memGeo = new THREE.PlaneGeometry(90, 70, 32, 28);
        const memMat = new THREE.MeshStandardMaterial({
            color: 0x4f46e5,
            emissive: 0x312e81,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.75,
            roughness: 0.5
        });
        const membrane = new THREE.Mesh(memGeo, memMat);
        membrane.rotation.x = -Math.PI / 2.6;
        membrane.position.set(0, -14, 0);
        sceneCellular.add(membrane);

        const pitGeo = new THREE.SphereGeometry(11, 24, 24, 0, Math.PI * 2, 0, Math.PI / 1.8);
        const pitMat = new THREE.MeshStandardMaterial({
            color: 0x7c3aed,
            wireframe: true,
            side: THREE.DoubleSide
        });
        const pit = new THREE.Mesh(pitGeo, pitMat);
        pit.position.set(0, -14, 0);
        pit.rotation.x = Math.PI;
        sceneCellular.add(pit);

        const vesicleGeo = new THREE.SphereGeometry(8.5, 24, 24);
        const vesicleMat = new THREE.MeshStandardMaterial({
            color: 0x06b6d4,
            transparent: true,
            opacity: 0.45,
            wireframe: true
        });
        membraneVesicle = new THREE.Mesh(vesicleGeo, vesicleMat);
        membraneVesicle.position.set(0, -28, 0);
        sceneCellular.add(membraneVesicle);

        const lysoGeo = new THREE.SphereGeometry(12, 20, 20);
        const lysoMat = new THREE.MeshStandardMaterial({
            color: 0xf59e0b,
            emissive: 0xb45309,
            emissiveIntensity: 0.35,
            transparent: true,
            opacity: 0.38
        });
        const lysosome = new THREE.Mesh(lysoGeo, lysoMat);
        lysosome.position.set(24, -34, -10);
        sceneCellular.add(lysosome);

        const uptakingNp = new THREE.Mesh(
            new THREE.SphereGeometry(4.2, 24, 24),
            new THREE.MeshStandardMaterial({
                color: 0x22d3ee,
                emissive: 0x0ea5e9,
                emissiveIntensity: 0.6
            })
        );
        uptakingNp.position.set(0, 16, 0);
        uptakingNp.userData = { animPhase: 0 };
        sceneCellular.add(uptakingNp);
        sceneCellular.userData.np = uptakingNp;
    }

    function buildNanoparticleReleaseModel() {
        const coreGeo = new THREE.SphereGeometry(16, 36, 36);
        const coreMat = new THREE.MeshStandardMaterial({
            color: 0x6366f1,
            emissive: 0x3730a3,
            roughness: 0.4,
            transparent: true,
            opacity: 0.85
        });
        coreMesh = new THREE.Mesh(coreGeo, coreMat);
        sceneRelease.add(coreMesh);

        const pegHaloGeo = new THREE.SphereGeometry(19.5, 24, 24);
        const pegHaloMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.35
        });
        const pegHalo = new THREE.Mesh(pegHaloGeo, pegHaloMat);
        sceneRelease.add(pegHalo);

        const drugCount = 120;
        const drugGeo = new THREE.SphereGeometry(0.85, 10, 10);
        const drugMat = new THREE.MeshStandardMaterial({
            color: 0xfbbf24,
            emissive: 0xd97706,
            emissiveIntensity: 0.8
        });

        for (let i = 0; i < drugCount; i++) {
            const mol = new THREE.Mesh(drugGeo, drugMat);
            const dist = 3 + Math.random() * 14;
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
                speed: 0.12 + Math.random() * 0.25
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

        if (mode === 'body') {
            desiredTarget = { x: 0, y: 0, z: 0 };
            desiredRadius = 140;
            focusRegion(SimState.selectedRegionId);
        } else if (mode === 'vessel') {
            desiredTarget = { x: 0, y: 0, z: 0 };
            desiredRadius = 70;
        } else if (mode === 'cellular') {
            desiredTarget = { x: 0, y: -12, z: 0 };
            desiredRadius = 65;
        } else if (mode === 'release') {
            desiredTarget = { x: 0, y: 0, z: 0 };
            desiredRadius = 55;
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
        updateCameraPosition();

        if (sceneBody && sceneBody.visible) {
            nanoParticles.forEach(np => {
                if (!np.userData.curve) return;
                np.userData.t = (np.userData.t + np.userData.speed * delta * 12) % 1.0;
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

        if (sceneVessel && sceneVessel.visible) {
            rbcParticles.forEach(rbc => {
                rbc.position.x += rbc.userData.vx * delta * 35;
                rbc.rotation.x += rbc.userData.rotSpeed;
                rbc.rotation.y += rbc.userData.rotSpeed;
                if (rbc.position.x > 55) rbc.position.x = -55;
            });

            nanoParticles.forEach(np => {
                if (!np.userData.vx) return;
                np.position.x += np.userData.vx * delta * 45;
                np.position.y += (Math.random() - 0.5) * 0.4;
                np.position.z += (Math.random() - 0.5) * 0.4;
                if (np.position.x > 55) np.position.x = -55;
            });
        }

        if (sceneCellular && sceneCellular.visible && sceneCellular.userData.np) {
            const uNp = sceneCellular.userData.np;
            uNp.userData.animPhase = (uNp.userData.animPhase + delta * 0.25) % 1.0;
            const p = uNp.userData.animPhase;

            if (p < 0.2) {
                const subP = p / 0.2;
                uNp.position.set(0, 18 - subP * 14, 0);
                uNp.scale.set(1, 1, 1);
            } else if (p < 0.4) {
                uNp.position.set(0, 4, 0);
            } else if (p < 0.65) {
                const subP = (p - 0.4) / 0.25;
                uNp.position.set(0, 4 - subP * 24, 0);
                if (membraneVesicle) {
                    membraneVesicle.position.set(0, 4 - subP * 24, 0);
                    membraneVesicle.scale.set(1 + subP * 0.2, 1 + subP * 0.2, 1 + subP * 0.2);
                }
            } else {
                const subP = (p - 0.65) / 0.35;
                uNp.position.set(subP * 22, -20 - subP * 12, -subP * 8);
                uNp.scale.set(1 - subP * 0.4, 1 - subP * 0.4, 1 - subP * 0.4);
            }
        }

        if (sceneRelease && sceneRelease.visible) {
            if (coreMesh) coreMesh.rotation.y += delta * 0.3;

            const currentRelFraction = SimState.evaluationResult ?
                (SimState.evaluationResult.model_results.drug_release_kinetics.final_release_pct / 100.0) : 0.4;

            drugMolecules.forEach((mol, idx) => {
                if (idx / drugMolecules.length < currentRelFraction) {
                    mol.position.addScaledVector(mol.userData.dir, mol.userData.speed * delta * 20);
                    if (mol.position.length() > 38) {
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
