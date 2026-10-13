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
        activeViewMode: 'body', // 'body', 'vessel', 'cellular', 'release'
        selectedRegionId: 'target_tissue',
        regionsData: {},
        stagesData: [],
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
            stageFormula: document.getElementById('hbs-stage-formula'),

            // Domain Warnings & Events
            domainWarningsCard: document.getElementById('hbs-domain-warnings-card'),
            domainWarningsList: document.getElementById('hbs-domain-warnings-list'),
            eventLogContainer: document.getElementById('hbs-event-log')
        };
    }

    // -------------------------------------------------------------
    // Chart.js Kinetics Release Plot
    // -------------------------------------------------------------
    let releaseChart = null;

    function initReleaseChart() {
        const canvas = document.getElementById('hbs-release-chart');
        if (!canvas || !window.Chart) return;

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
                animation: { duration: 400 },
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
                    },
                    tooltip: {
                        backgroundColor: 'rgba(14, 10, 38, 0.95)',
                        borderColor: '#7c3aed',
                        borderWidth: 1,
                        titleColor: '#22d3ee',
                        bodyColor: '#f1efff'
                    }
                }
            }
        });
    }

    function updateReleaseChart(trajectory, currentTime) {
        if (!releaseChart || !trajectory || !trajectory.time_series) return;

        const ts = trajectory.time_series;
        const labels = ts.map(p => p.time_hours);
        const cumData = ts.map(p => p.cumulative_release_pct);
        const rateData = ts.map(p => p.release_rate_pct_hr);

        releaseChart.data.labels = labels;
        releaseChart.data.datasets[0].data = cumData;
        releaseChart.data.datasets[1].data = rateData;
        releaseChart.update('none');
    }

    // -------------------------------------------------------------
    // Three.js Multi-Scale 3D Engine
    // -------------------------------------------------------------
    let renderer = null;
    let scene = null;
    let camera = null;
    let animationFrameId = null;
    let isWebGlAvailable = true;

    // Sub-Scenes / Groups
    let sceneBody = null;
    let sceneVessel = null;
    let sceneCellular = null;
    let sceneRelease = null;

    // Particle & Entity pools
    let rbcParticles = [];
    let nanoParticles = [];
    let drugMolecules = [];
    let organMarkers = {};
    let membraneVesicle = null;
    let coreMesh = null;

    // Mouse / Touch Camera Controller (Pure math, no external CDN dependencies)
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let spherical = { radius: 140, theta: Math.PI / 2, phi: Math.PI / 2 };
    let cameraTarget = { x: 0, y: 0, z: 0 };
    let desiredTarget = { x: 0, y: 0, z: 0 };
    let desiredRadius = 140;

    function initThreeScene() {
        if (!window.THREE) {
            console.warn('Three.js not found, falling back to 2D Canvas');
            initFallbackCanvas();
            return;
        }

        const canvas = elements.threeCanvas;
        if (!canvas) return;

        try {
            renderer = new THREE.WebGLRenderer({
                canvas: canvas,
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance'
            });
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 1, 1000);
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

            // Start Render Loop
            renderLoop();
        } catch (err) {
            console.error('WebGL Initialization Error:', err);
            isWebGlAvailable = false;
            if (elements.threeCanvas) elements.threeCanvas.style.display = 'none';
            if (elements.fallbackCanvas) elements.fallbackCanvas.style.display = 'block';
            initFallbackCanvas();
        }
    }

    function updateCameraPosition() {
        if (!camera) return;
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

        // Touch support
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

    // -------------------------------------------------------------
    // View 1: 3D Human Body & Circulatory System
    // -------------------------------------------------------------
    function buildHumanBodyModel() {
        const matWire = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.16
        });

        // 1. Anatomical Silhouette (Head, Torso, Limbs)
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

        // Arms
        [-1, 1].forEach(side => {
            const armUpper = new THREE.Mesh(new THREE.CylinderGeometry(3, 2.5, 22, 12), matWire);
            armUpper.position.set(side * 18, 25, 0);
            armUpper.rotation.z = side * 0.15;
            sceneBody.add(armUpper);

            const armLower = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2, 22, 12), matWire);
            armLower.position.set(side * 22, 5, 0);
            armLower.rotation.z = side * 0.08;
            sceneBody.add(armLower);
        });

        // Legs
        [-1, 1].forEach(side => {
            const thigh = new THREE.Mesh(new THREE.CylinderGeometry(5.2, 4, 30, 14), matWire);
            thigh.position.set(side * 7, -18, 0);
            sceneBody.add(thigh);

            const calf = new THREE.Mesh(new THREE.CylinderGeometry(3.8, 2.8, 32, 14), matWire);
            calf.position.set(side * 7.5, -48, 0);
            sceneBody.add(calf);
        });

        // 2. Branching Vascular Tree (Arterial Red & Venous Blue Tubes)
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

        // Aorta & Vena Cava Curves
        const createVesselTube = (points, mat, radius) => {
            const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
            const tubeGeo = new THREE.TubeGeometry(curve, 32, radius, 8, false);
            const tubeMesh = new THREE.Mesh(tubeGeo, mat);
            sceneBody.add(tubeMesh);
            return curve;
        };

        // Main vessels
        const vAorta = createVesselTube([
            [0, 26, 2], [1.5, 31, 1.5], [1, 35, 0], [-1.2, 33, -1], [-1, 20, 0],
            [-1, 5, 0], [-2, -5, 0], [-6, -18, 0], [-7, -46, 0]
        ], arteryMat, 1.3);

        const vVenaCava = createVesselTube([
            [1.5, -46, 0], [2, -18, 0], [1, -5, 0], [1, 10, 0], [2, 26, 1],
            [1.8, 38, 0], [0, 47, 0]
        ], veinMat, 1.4);

        // Branching pulmonary & arm vessels
        createVesselTube([[0, 28, 2], [-8, 28, 0]], arteryMat, 0.9); // Left Lung branch
        createVesselTube([[0, 28, 2], [8, 28, 0]], arteryMat, 0.9);  // Right Lung branch
        createVesselTube([[-1, 34, 0], [-18, 26, 0], [-22, 6, 0]], arteryMat, 0.8); // Left Arm
        createVesselTube([[1, 34, 0], [18, 26, 0], [22, 6, 0]], arteryMat, 0.8);   // Right Arm

        // 3. Glowing Organ Nodes / Markers
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

            // Pulsing halo ring
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

        // 4. Circulating Nanoparticle Flow Points in Body
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

    // -------------------------------------------------------------
    // View 2: Microscopic Blood Vessel & Capillary Flow View
    // -------------------------------------------------------------
    function buildBloodVesselModel() {
        // Capillary Wall (Cylinder with translucent endothelial lining)
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

        // Endothelial Cell Mosaic Nodes on wall
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

        // Biconcave Red Blood Cells (RBCs / Erythrocytes)
        const rbcCount = 38;
        const rbcMat = new THREE.MeshStandardMaterial({
            color: 0xdc2626,
            roughness: 0.3,
            metalness: 0.1
        });

        for (let i = 0; i < rbcCount; i++) {
            // Approximating biconcave disc: flattened sphere
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

        // Nanoparticles in vessel lumen (marginating toward wall)
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
                // Margination force pushes particles outward radially
                targetRadius: vesselRadius * (0.6 + Math.random() * 0.35)
            };
            sceneVessel.add(np);
            nanoParticles.push(np);
        }
    }

    // -------------------------------------------------------------
    // View 3: Cellular Uptake & Endocytosis Multi-Step 3D Scene
    // -------------------------------------------------------------
    function buildCellularUptakeModel() {
        // Plasma Membrane (Bilayer plane with undulating waviness)
        const memGeo = new THREE.PlaneGeometry(90, 70, 32, 28);
        const memMat = new THREE.MeshStandardMaterial({
            color: 0x4f46e5,
            emissive: 0x312e81,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.75,
            wireframe: false,
            roughness: 0.5
        });
        const membrane = new THREE.Mesh(memGeo, memMat);
        membrane.rotation.x = -Math.PI / 2.6;
        membrane.position.set(0, -14, 0);
        sceneCellular.add(membrane);

        // Clathrin/Caveolae-Coated Endocytic Invagination Pit
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

        // Intracellular Endosome / Vesicle
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

        // Acidic Lysosome
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

        // Nanoparticle entering the cell
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

    // -------------------------------------------------------------
    // View 4: Nanoparticle Core-Shell Drug Release 3D Scene
    // -------------------------------------------------------------
    function buildNanoparticleReleaseModel() {
        // Polymer / Lipid Core Mesh
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

        // Steric PEG Coating Outer Halo
        const pegHaloGeo = new THREE.SphereGeometry(19.5, 24, 24);
        const pegHaloMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.35
        });
        const pegHalo = new THREE.Mesh(pegHaloGeo, pegHaloMat);
        sceneRelease.add(pegHalo);

        // Encapsulated & Released Drug Molecules (Gold/Orange spheres)
        const drugCount = 120;
        const drugGeo = new THREE.SphereGeometry(0.85, 10, 10);
        const drugMat = new THREE.MeshStandardMaterial({
            color: 0xfbbf24,
            emissive: 0xd97706,
            emissiveIntensity: 0.8
        });

        for (let i = 0; i < drugCount; i++) {
            const mol = new THREE.Mesh(drugGeo, drugMat);
            // Random distribution within and around the nanoparticle core
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
                speed: 0.12 + Math.random() * 0.25,
                released: false
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

        // Adjust camera targets based on active view mode
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

        // Smooth camera lerp
        updateCameraPosition();

        // 1. Body Scene Animation (Vessel tube flow + Organ pulsing)
        if (sceneBody && sceneBody.visible) {
            nanoParticles.forEach(np => {
                if (!np.userData.curve) return;
                np.userData.t = (np.userData.t + np.userData.speed * delta * 12) % 1.0;
                const pt = np.userData.curve.getPointAt(np.userData.t);
                np.position.set(pt.x + np.userData.jitter, pt.y, pt.z + np.userData.jitter);
            });

            // Pulse organ rings
            Object.values(organMarkers).forEach(m => {
                if (m.userData.ring) {
                    const scale = 1.0 + Math.sin(Date.now() * 0.004) * 0.12;
                    m.userData.ring.scale.set(scale, scale, 1);
                }
            });
        }

        // 2. Capillary Vessel Animation (RBC flow + Margination)
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
                // Browninan motion jitter
                np.position.y += (Math.random() - 0.5) * 0.4;
                np.position.z += (Math.random() - 0.5) * 0.4;
                if (np.position.x > 55) np.position.x = -55;
            });
        }

        // 3. Cellular Uptake Animation (5-Stage Endocytosis Loop)
        if (sceneCellular && sceneCellular.visible && sceneCellular.userData.np) {
            const uNp = sceneCellular.userData.np;
            uNp.userData.animPhase = (uNp.userData.animPhase + delta * 0.25) % 1.0;
            const p = uNp.userData.animPhase;

            if (p < 0.2) {
                // Step 1: Approaching plasma membrane
                const subP = p / 0.2;
                uNp.position.set(0, 18 - subP * 14, 0);
                uNp.scale.set(1, 1, 1);
            } else if (p < 0.4) {
                // Step 2: Contacting membrane & receptor binding
                uNp.position.set(0, 4, 0);
            } else if (p < 0.65) {
                // Step 3 & 4: Membrane invaginates into vesicle pit
                const subP = (p - 0.4) / 0.25;
                uNp.position.set(0, 4 - subP * 24, 0);
                if (membraneVesicle) {
                    membraneVesicle.position.set(0, 4 - subP * 24, 0);
                    membraneVesicle.scale.set(1 + subP * 0.2, 1 + subP * 0.2, 1 + subP * 0.2);
                }
            } else {
                // Step 5: Intracellular lysosomal trafficking & drug release
                const subP = (p - 0.65) / 0.35;
                uNp.position.set(subP * 22, -20 - subP * 12, -subP * 8);
                uNp.scale.set(1 - subP * 0.4, 1 - subP * 0.4, 1 - subP * 0.4);
            }
        }

        // 4. Nanoparticle Release Animation
        if (sceneRelease && sceneRelease.visible) {
            if (coreMesh) coreMesh.rotation.y += delta * 0.3;

            // Animate drug molecules diffusing outwards proportionally to release %
            const currentRelFraction = SimState.evaluationResult ?
                (SimState.evaluationResult.model_results.drug_release_kinetics.final_release_pct / 100.0) : 0.4;

            drugMolecules.forEach((mol, idx) => {
                if (idx / drugMolecules.length < currentRelFraction) {
                    // Molecule is diffusing outward
                    mol.position.addScaledVector(mol.userData.dir, mol.userData.speed * delta * 20);
                    if (mol.position.length() > 38) {
                        // Reset to core boundary
                        mol.position.copy(mol.userData.dir).multiplyScalar(mol.userData.origDist);
                    }
                } else {
                    // Retained within core
                    mol.position.copy(mol.userData.dir).multiplyScalar(Math.min(14, mol.userData.origDist));
                }
            });
        }

        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }

    // -------------------------------------------------------------
    // Fallback 2D Canvas Engine (for non-WebGL environments)
    // -------------------------------------------------------------
    let fallbackCtx = null;

    function initFallbackCanvas() {
        const canvas = elements.fallbackCanvas;
        if (!canvas) return;
        canvas.style.display = 'block';
        if (elements.threeCanvas) elements.threeCanvas.style.display = 'none';

        fallbackCtx = canvas.getContext('2d');
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;

        function fallbackLoop() {
            if (!SimState.isRunning && fallbackCtx) {
                drawFallbackFrame();
            }
            requestAnimationFrame(fallbackLoop);
        }
        fallbackLoop();
    }

    function drawFallbackFrame() {
        if (!fallbackCtx || !elements.fallbackCanvas) return;
        const w = elements.fallbackCanvas.width;
        const h = elements.fallbackCanvas.height;

        fallbackCtx.clearRect(0, 0, w, h);
        fallbackCtx.fillStyle = '#06030f';
        fallbackCtx.fillRect(0, 0, w, h);

        // Draw Anatomical Schematic
        fallbackCtx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
        fallbackCtx.lineWidth = 2;
        fallbackCtx.strokeRect(w * 0.35, h * 0.1, w * 0.3, h * 0.8);

        fallbackCtx.fillStyle = '#f1efff';
        fallbackCtx.font = '14px Space Grotesk, sans-serif';
        fallbackCtx.textAlign = 'center';
        fallbackCtx.fillText('ANATOMICAL CIRCULATION SCHEMATIC (FALLBACK)', w / 2, h * 0.08);

        // Draw Organ Nodes
        const nodes = [
            { label: 'Bloodstream', y: 0.25, color: '#ef4444' },
            { label: 'Lungs', y: 0.35, color: '#38bdf8' },
            { label: 'Liver', y: 0.48, color: '#f59e0b' },
            { label: 'Kidneys', y: 0.60, color: '#10b981' },
            { label: 'Target Tissue', y: 0.72, color: '#f43f5e' }
        ];

        nodes.forEach(n => {
            const ny = h * n.y;
            fallbackCtx.fillStyle = n.color;
            fallbackCtx.beginPath();
            fallbackCtx.arc(w / 2, ny, 16, 0, Math.PI * 2);
            fallbackCtx.fill();

            fallbackCtx.fillStyle = '#ffffff';
            fallbackCtx.fillText(n.label, w / 2, ny + 28);
        });
    }

    // -------------------------------------------------------------
    // Simulation Execution Engine & 8-Stage Controller
    // -------------------------------------------------------------
    let simInterval = null;

    function startSimulation() {
        if (!SimState.evaluationResult) {
            evaluateCurrentFormulation().then(() => doStart());
        } else {
            doStart();
        }
    }

    function doStart() {
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

    function simulationTick() {
        if (!SimState.isRunning || SimState.isPaused) return;

        SimState.currentSimTimeHours += SimState.timeStepHours;
        const totalDuration = parseFloat(elements.inputDuration ? elements.inputDuration.value : 48.0);

        // Update stage progression
        const stagesCount = 8;
        const stageDuration = totalDuration / stagesCount;
        const expectedStage = Math.min(stagesCount - 1, Math.floor(SimState.currentSimTimeHours / stageDuration));

        if (expectedStage !== SimState.currentStageIndex) {
            setStage(expectedStage);
        }

        updateTelemetryCards(SimState.currentSimTimeHours);

        // Auto-switch view to align with narrative stage if desired
        if (SimState.autoAdvance) {
            if (SimState.currentStageIndex === 1 && SimState.activeViewMode !== 'vessel') switchViewMode('vessel');
            else if (SimState.currentStageIndex === 4 && SimState.activeViewMode !== 'cellular') switchViewMode('cellular');
            else if (SimState.currentStageIndex === 5 && SimState.activeViewMode !== 'release') switchViewMode('release');
            else if ((SimState.currentStageIndex === 0 || SimState.currentStageIndex === 7) && SimState.activeViewMode !== 'body') switchViewMode('body');
        }

        // Check completion
        if (SimState.currentSimTimeHours >= totalDuration) {
            clearInterval(simInterval);
            SimState.isRunning = false;
            updateControlsUi();
            addEventLog('SIMULATION_COMPLETED', `Completed full journey through human body (${totalDuration.toFixed(1)} hrs).`, 'COMPUTED - ODE');
        }
    }

    function setStage(index) {
        SimState.currentStageIndex = index;
        updateStageDisplay(index);

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

        const stage = SimState.stagesData[index];
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

        if (!SimState.evaluationResult) return;

        const res = SimState.evaluationResult;
        const kinetics = res.model_results.drug_release_kinetics;
        const colloidal = res.model_results.colloidal_index;
        const cytotox = res.model_results.cytotoxicity;

        // Current Korsmeyer-Peppas ODE point: Mt/M_inf = k * t^n
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

        // Particle count indicator
        if (elements.hudParticlesBadge) {
            const activeCount = Math.round(180 * (1.0 - (simTime / SimState.maxDurationHours) * 0.4));
            elements.hudParticlesBadge.textContent = `${activeCount} NPs / mL`;
        }
    }

    function updateControlsUi() {
        if (!elements.btnStart) return;
        elements.btnStart.disabled = SimState.isRunning && !SimState.isPaused;
        elements.btnPause.disabled = !SimState.isRunning || SimState.isPaused;
        elements.btnResume.disabled = !SimState.isPaused;
        elements.btnReset.disabled = !SimState.isRunning && SimState.currentSimTimeHours === 0;
    }

    // -------------------------------------------------------------
    // Region Info Panel Logic
    // -------------------------------------------------------------
    function updateRegionInfoPanel(regionId) {
        const region = SimState.regionsData[regionId];
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

    // -------------------------------------------------------------
    // Formulation Configuration & Backend Evaluation
    // -------------------------------------------------------------
    async function evaluateCurrentFormulation() {
        const payload = {
            material: elements.inputMaterial ? elements.inputMaterial.value : 'PLGA',
            core_size_nm: parseFloat(elements.inputCoreSize ? elements.inputCoreSize.value : 80),
            hydrodynamic_size_nm: parseFloat(elements.inputHydroSize ? elements.inputHydroSize.value : 95),
            surface_coating: elements.inputCoating ? elements.inputCoating.value : 'PEG',
            surface_charge_mv: parseFloat(elements.inputZeta ? elements.inputZeta.value : -24.0),
            drug_name: elements.inputDrug ? elements.inputDrug.value : 'Paclitaxel',
            drug_loading_pct: parseFloat(elements.inputLoading ? elements.inputLoading.value : 12.0),
            k_release: parseFloat(elements.inputK ? elements.inputK.value : 0.18),
            n_release: parseFloat(elements.inputN ? elements.inputN.value : 0.55),
            target_tissue: elements.inputTarget ? elements.inputTarget.value : 'target_tissue',
            administration_route: elements.inputRoute ? elements.inputRoute.value : 'Intravenous',
            initial_concentration_ug_ml: parseFloat(elements.inputDose ? elements.inputDose.value : 50.0),
            temperature_c: parseFloat(elements.inputTemp ? elements.inputTemp.value : 37.0),
            ph: parseFloat(elements.inputPh ? elements.inputPh.value : 7.4),
            ionic_strength_m: parseFloat(elements.inputIonic ? elements.inputIonic.value : 0.154),
            exposure_time_hours: parseFloat(elements.inputDuration ? elements.inputDuration.value : 48.0),
            cell_name: elements.inputCell ? elements.inputCell.value : 'A549',
            assay: elements.inputAssay ? elements.inputAssay.value : 'MTT'
        };

        try {
            if (elements.btnApplyConfig) elements.btnApplyConfig.textContent = 'Evaluating...';
            const res = await fetch('/api/human_body_sim/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            SimState.evaluationResult = data;
            SimState.maxDurationHours = payload.exposure_time_hours;

            // Render warnings
            renderDomainWarnings(data.warnings);

            // Update Chart
            updateReleaseChart(data.model_results.drug_release_kinetics, SimState.currentSimTimeHours);

            // Update Telemetry
            updateTelemetryCards(SimState.currentSimTimeHours);

            addEventLog('CONFIG_EVALUATED', `Formulation evaluated: ${payload.material} (${payload.core_size_nm}nm) loaded with ${payload.drug_name}.`, 'COMPUTED - MODEL');
        } catch (err) {
            console.error('Failed to evaluate formulation:', err);
            addEventLog('EVAL_ERROR', `Evaluation error: ${err.message}. Using client-side biophysical model.`, 'WARNING');
        } finally {
            if (elements.btnApplyConfig) elements.btnApplyConfig.textContent = 'Apply & Evaluate Formulation';
        }
    }

    async function predictZetaPotential() {
        const payload = {
            Shape: 'Sphere',
            Core: elements.inputMaterial ? elements.inputMaterial.value : 'Silver',
            Size_nm: parseFloat(elements.inputCoreSize ? elements.inputCoreSize.value : 80),
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
                addEventLog('ML_PREDICT_ZETA', `Predicted Zeta Potential: ${data.prediction} mV via Ridge model.`, 'COMPUTED - ML');
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

            // Limit DOM log size
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

    // -------------------------------------------------------------
    // Initialization & Data Loading
    // -------------------------------------------------------------
    async function loadRegionsAndStages() {
        try {
            const [regRes, stageRes] = await Promise.all([
                fetch('/api/human_body_sim/regions'),
                fetch('/api/human_body_sim/stages')
            ]);
            if (regRes.ok) {
                const regData = await regRes.json();
                SimState.regionsData = regData.regions || {};
                populateRegionSelect();
            }
            if (stageRes.ok) {
                const sData = await stageRes.json();
                SimState.stagesData = sData.stages || [];
                updateStageDisplay(0);
            }
        } catch (err) {
            console.warn('Backend load error:', err);
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
        // View Switchers
        if (elements.viewModeButtons) {
            elements.viewModeButtons.forEach(btn => {
                btn.addEventListener('click', () => switchViewMode(btn.dataset.view));
            });
        }

        // Stepper Clicks
        if (elements.stageSteps) {
            elements.stageSteps.forEach((st, idx) => {
                st.addEventListener('click', () => setStage(idx));
            });
        }

        // Sim Controls
        if (elements.btnStart) elements.btnStart.addEventListener('click', startSimulation);
        if (elements.btnPause) elements.btnPause.addEventListener('click', pauseSimulation);
        if (elements.btnResume) elements.btnResume.addEventListener('click', resumeSimulation);
        if (elements.btnReset) elements.btnReset.addEventListener('click', resetSimulation);

        // Speed Controls
        if (elements.speedButtons) {
            elements.speedButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    elements.speedButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    SimState.speed = parseFloat(btn.dataset.speed);
                    if (SimState.isRunning && !SimState.isPaused) {
                        clearInterval(simInterval);
                        simInterval = setInterval(simulationTick, 400 / SimState.speed);
                    }
                });
            });
        }

        // Auto Advance Check
        if (elements.autoAdvanceCheck) {
            elements.autoAdvanceCheck.addEventListener('change', e => {
                SimState.autoAdvance = e.target.checked;
            });
        }

        // Region Select
        if (elements.regionSelect) {
            elements.regionSelect.addEventListener('change', e => {
                focusRegion(e.target.value);
            });
        }

        // Preset Select
        if (elements.presetSelect) {
            elements.presetSelect.addEventListener('change', e => {
                applyPreset(e.target.value);
            });
        }

        // Config buttons
        if (elements.btnApplyConfig) elements.btnApplyConfig.addEventListener('click', evaluateCurrentFormulation);
        if (elements.btnPredictZeta) elements.btnPredictZeta.addEventListener('click', predictZetaPotential);

        // Range Sliders display updates
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

        // Window resize
        window.addEventListener('resize', () => {
            if (renderer && elements.threeCanvas) {
                const w = elements.threeCanvas.clientWidth;
                const h = elements.threeCanvas.clientHeight;
                renderer.setSize(w, h);
                if (camera) {
                    camera.aspect = w / h;
                    camera.updateProjectionMatrix();
                }
            }
        });
    }

    // -------------------------------------------------------------
    // Bootstrapper
    // -------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', async () => {
        initDomReferences();
        bindEventListeners();
        initReleaseChart();
        initThreeScene();
        await loadRegionsAndStages();
        await evaluateCurrentFormulation();
    });

    // Expose global controller for tab switching integration
    window.NanoMedHumanBodySim = {
        activate: () => {
            if (renderer && elements.threeCanvas) {
                const w = elements.threeCanvas.clientWidth;
                const h = elements.threeCanvas.clientHeight;
                renderer.setSize(w, h);
                if (camera) {
                    camera.aspect = w / h;
                    camera.updateProjectionMatrix();
                }
            }
            if (releaseChart) releaseChart.resize();
        },
        deactivate: () => {
            // Optional pause/throttle
        }
    };
})();
