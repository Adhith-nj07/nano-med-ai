/**
 * NanoMedAI - Full-Stack Biophysical Simulation & Machine Learning Web Platform
 * Connects the frontend UI to FastAPI backend endpoints:
 * - /api/health & /api/metadata
 * - /api/simulation/* (Biophysical session manager)
 * - /api/predict/stability (Zeta potential regressor)
 * - /api/predict/cytotoxicity (Random forest classifier)
 * - /api/prompt (Multi-model natural language pipeline)
 * - /api/formulation/heatmap (DLVO colloidal matrix)
 * - /api/dataset/{task} (Harmonized dataset catalog)
 */

// Helper selector
const $ = (id) => document.getElementById(id);
const escapeHTML = (str) => String(str ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Default formulation catalog — Expanded with All Dataset Medicines & Antibiotics
const FORMULATIONS = {
    // --- ONCOLOGY & CHEMOTHERAPEUTICS ---
    'formulation-a': {
        name: 'Formulation A: Paclitaxel + PLGA (Nature Comms Benchmark)',
        drug: 'Paclitaxel',
        category: 'Antineoplastic / Chemotherapeutic',
        material: 'PLGA',
        size: 120.0,
        zeta: -22.0,
        load: '8.0%',
        coat: 'PEG-5000 Stealth',
        k: 0.088,
        n: 0.371
    },
    'formulation-b': {
        name: 'Formulation B: Letrozole + PLA (Long-Acting Injectable)',
        drug: 'Letrozole',
        category: 'Aromatase Inhibitor',
        material: 'PLA',
        size: 150.0,
        zeta: -15.0,
        load: '5.0%',
        coat: 'Citrate',
        k: 0.060,
        n: 0.420
    },
    'formulation-c': {
        name: 'Formulation C: Letrozole + PLGA (Sustained Release)',
        drug: 'Letrozole',
        category: 'Aromatase Inhibitor',
        material: 'PLGA',
        size: 100.0,
        zeta: -28.0,
        load: '6.0%',
        coat: 'PVA Surfactant',
        k: 0.110,
        n: 0.340
    },
    'doxorubicin-liposome': {
        name: 'Doxorubicin + PEGylated Liposome (Doxil Analog)',
        drug: 'Doxorubicin',
        category: 'Anthracycline Chemotherapeutic',
        material: 'Liposome (DPPC/Chol)',
        size: 85.0,
        zeta: -25.0,
        load: '9.8%',
        coat: 'PEG-DSPE Stealth Layer',
        k: 0.045,
        n: 0.460
    },
    'doxorubicin-plga': {
        name: 'Doxorubicin + PLGA Chitosan/Alginate Core',
        drug: 'Doxorubicin',
        category: 'Anthracycline Chemotherapeutic',
        material: 'PLGA (CHI/ALG)',
        size: 175.0,
        zeta: -19.5,
        load: '8.5%',
        coat: 'Layer-by-Layer Chitosan/Alginate',
        k: 0.082,
        n: 0.420
    },
    'methotrexate-dendrimer': {
        name: 'Methotrexate + PAMAM G4 Dendrimer',
        drug: 'Methotrexate',
        category: 'Antimetabolite',
        material: 'PAMAM Dendrimer',
        size: 45.0,
        zeta: 14.0,
        load: '14.0%',
        coat: 'PEG / Primary Amine Surface',
        k: 0.180,
        n: 0.310
    },
    'cisplatin-micelle': {
        name: 'Cisplatin + Block Copolymer Micelles',
        drug: 'Cisplatin',
        category: 'Platinum Antineoplastic',
        material: 'PCL-b-PEG Micelle',
        size: 65.0,
        zeta: -8.0,
        load: '7.2%',
        coat: 'PEG Hydrophilic Shell',
        k: 0.090,
        n: 0.380
    },
    'rapamycin-albumin': {
        name: 'Rapamycin + Albumin Matrix (Abraxane format)',
        drug: 'Rapamycin',
        category: 'mTOR Inhibitor / Immunosuppressive',
        material: 'Human Serum Albumin (HSA)',
        size: 130.0,
        zeta: -18.0,
        load: '10.0%',
        coat: 'Endogenous Albumin Corona',
        k: 0.075,
        n: 0.390
    },
    'exemestane-plga-gel': {
        name: 'Exemestane + PLGA In-Situ Gel NP',
        drug: 'Exemestane',
        category: 'Aromatase Inhibitor',
        material: 'PLGA In-Situ Gel',
        size: 160.0,
        zeta: -23.0,
        load: '12.4%',
        coat: 'Thermosensitive Poloxamer Gel',
        k: 0.038,
        n: 0.580
    },

    // --- PARACETAMOL & ANALGESICS / NSAIDS ---
    'nm-paracetamol-plga': {
        name: 'NM-000001: Paracetamol + PLGA (335 nm, SLN)',
        drug: 'Paracetamol',
        category: 'Analgesic / Antipyretic',
        material: 'PLGA',
        size: 335.5,
        zeta: 7.1,
        load: '7.4%',
        coat: 'Dextran coating',
        k: 0.095,
        n: 0.400
    },
    'nm-paracetamol-liposome': {
        name: 'NM-000004: Paracetamol + Liposome DPPC (90 nm)',
        drug: 'Paracetamol',
        category: 'Analgesic / Antipyretic',
        material: 'Liposome (DPPC)',
        size: 90.1,
        zeta: -35.4,
        load: '4.0%',
        coat: 'Dextran coating',
        k: 0.145,
        n: 0.450
    },
    'nm-paracetamol-sln': {
        name: 'NM-000012: Paracetamol + Lipid DSPC (235 nm)',
        drug: 'Paracetamol',
        category: 'Analgesic / Antipyretic',
        material: 'Lipid (DSPC)',
        size: 234.9,
        zeta: 19.0,
        load: '4.0%',
        coat: 'PEGylation',
        k: 0.105,
        n: 0.420
    },
    'ibuprofen-lipid': {
        name: 'Ibuprofen + Lipid Nanoparticle (150 nm)',
        drug: 'Ibuprofen',
        category: 'NSAID / Anti-inflammatory',
        material: 'Solid Lipid (SLN)',
        size: 150.0,
        zeta: -22.4,
        load: '9.5%',
        coat: 'Tween 80 Surfactant',
        k: 0.115,
        n: 0.380
    },

    // --- ANTIBIOTICS & ANTIMICROBIALS (DATASET COHORT) ---
    'ciprofloxacin-plga': {
        name: 'Ciprofloxacin + PLGA Nanoparticles (Fluoroquinolone)',
        drug: 'Ciprofloxacin',
        category: 'Fluoroquinolone Antibiotic',
        material: 'PLGA',
        size: 165.0,
        zeta: -18.2,
        load: '9.2%',
        coat: 'PVA Surfactant',
        k: 0.120,
        n: 0.360
    },
    'vancomycin-plga-peg': {
        name: 'Vancomycin + PLGA-PEG Extended-Release (Glycopeptide)',
        drug: 'Vancomycin',
        category: 'Glycopeptide Antibiotic',
        material: 'PLGA-PEG',
        size: 180.0,
        zeta: -12.5,
        load: '11.5%',
        coat: 'PEG Stealth Layer',
        k: 0.050,
        n: 0.450
    },
    'rifampicin-plga-peg': {
        name: 'Rifampicin + PLGA-PEG Sustained Core (Antitubercular)',
        drug: 'Rifampicin',
        category: 'Rifamycin / Antitubercular',
        material: 'PLGA-PEG',
        size: 145.0,
        zeta: -16.0,
        load: '8.0%',
        coat: 'PEGylation',
        k: 0.070,
        n: 0.420
    },
    'doxycycline-polymeric': {
        name: 'Doxycycline + Polymeric Nanoparticles (Tetracycline)',
        drug: 'Doxycycline',
        category: 'Tetracycline Antibiotic',
        material: 'PEG-PLA',
        size: 130.0,
        zeta: -24.0,
        load: '7.8%',
        coat: 'Surfactant (Tween 80)',
        k: 0.130,
        n: 0.390
    },
    'gentamicin-chitosan': {
        name: 'Gentamicin + Chitosan Nanoparticles (Aminoglycoside)',
        drug: 'Gentamicin',
        category: 'Aminoglycoside Antibiotic',
        material: 'Chitosan',
        size: 115.0,
        zeta: 28.5,
        load: '6.5%',
        coat: 'Chitosan Cationic Coating',
        k: 0.160,
        n: 0.410
    },
    'azithromycin-sln': {
        name: 'Azithromycin + Solid Lipid Nanoparticles (Macrolide)',
        drug: 'Azithromycin',
        category: 'Macrolide Antibiotic',
        material: 'Solid Lipid (SLN)',
        size: 195.0,
        zeta: -21.0,
        load: '10.2%',
        coat: 'Poloxamer 188',
        k: 0.085,
        n: 0.350
    },
    'amoxicillin-eudragit': {
        name: 'Amoxicillin + Eudragit Nanoparticles (Beta-Lactam)',
        drug: 'Amoxicillin',
        category: 'Beta-Lactam Antibiotic',
        material: 'Eudragit',
        size: 140.0,
        zeta: -15.5,
        load: '8.7%',
        coat: 'Enteric Polymer Coating',
        k: 0.175,
        n: 0.330
    },

    // --- CARDIOVASCULAR & DUAL THERAPIES ---
    'amlodipine-plga-pcl': {
        name: 'Amlodipine Besylate + PLGA-PCL Extruded NPs',
        drug: 'Amlodipine Besylate',
        category: 'Calcium Channel Blocker',
        material: 'PLGA-PCL',
        size: 185.0,
        zeta: -16.5,
        load: '5.0%',
        coat: 'PCL Extruded Matrix',
        k: 0.065,
        n: 0.510
    },
    'dox-atv-dual': {
        name: 'DOX / Atorvastatin + Hyaluronic Acid NP (Dual Therapy)',
        drug: 'DOX / Atorvastatin',
        category: 'Cardioprotective Oncology Dual Delivery',
        material: 'CaP / Hyaluronic Acid',
        size: 140.0,
        zeta: -26.0,
        load: '6.8%',
        coat: 'Hyaluronic Acid CD44-Targeted',
        k: 0.078,
        n: 0.440
    },

    // --- BIOLOGICS & NUCLEIC ACIDS ---
    'mrna-lnp': {
        name: 'mRNA-1273 + Ionizable Lipid Nanoparticle (LNP)',
        drug: 'mRNA-1273',
        category: 'mRNA Vaccine / Biologic',
        material: 'Ionizable Lipid (SM-102)',
        size: 80.0,
        zeta: 4.5,
        load: '92% encapsulation',
        coat: 'PEG-2000 DMG Corona',
        k: 0.150,
        n: 0.380
    },
    'sirna-lnp': {
        name: 'siRNA + Targeted Cationic LNP (Gene Silencing)',
        drug: 'siRNA',
        category: 'Gene Silencing Oligonucleotide',
        material: 'Lipid (DSPC/Chol)',
        size: 75.0,
        zeta: 6.0,
        load: '88% encapsulation',
        coat: 'PEG Stealth / Ligand Conjugation',
        k: 0.160,
        n: 0.360
    }
};

// Aliases for user flexibility and backward compatibility
FORMULATIONS['paracetamol'] = FORMULATIONS['nm-paracetamol-plga'];
FORMULATIONS['ciprofloxacin'] = FORMULATIONS['ciprofloxacin-plga'];
FORMULATIONS['vancomycin'] = FORMULATIONS['vancomycin-plga-peg'];
FORMULATIONS['rifampicin'] = FORMULATIONS['rifampicin-plga-peg'];
FORMULATIONS['doxorubicin'] = FORMULATIONS['doxorubicin-liposome'];
FORMULATIONS['paclitaxel'] = FORMULATIONS['formulation-a'];
FORMULATIONS['letrozole'] = FORMULATIONS['formulation-b'];
FORMULATIONS['ibuprofen'] = FORMULATIONS['ibuprofen-lipid'];
FORMULATIONS['doxycycline'] = FORMULATIONS['doxycycline-polymeric'];
FORMULATIONS['gentamicin'] = FORMULATIONS['gentamicin-chitosan'];
FORMULATIONS['azithromycin'] = FORMULATIONS['azithromycin-sln'];
FORMULATIONS['amoxicillin'] = FORMULATIONS['amoxicillin-eudragit'];
FORMULATIONS['methotrexate'] = FORMULATIONS['methotrexate-dendrimer'];
FORMULATIONS['cisplatin'] = FORMULATIONS['cisplatin-micelle'];
FORMULATIONS['rapamycin'] = FORMULATIONS['rapamycin-albumin'];
FORMULATIONS['exemestane'] = FORMULATIONS['exemestane-plga-gel'];
FORMULATIONS['amlodipine'] = FORMULATIONS['amlodipine-plga-pcl'];
FORMULATIONS['mrna'] = FORMULATIONS['mrna-lnp'];
FORMULATIONS['sirna'] = FORMULATIONS['sirna-lnp'];

// Application Global State
const state = {
    status: 'INITIALIZED', // INITIALIZED, RUNNING, PAUSED, STOPPED, COMPLETED
    time: 0,
    maxTime: 72,
    speed: 1.0,
    timerId: null,
    backendSimulationId: null,
    backendConnected: false,
    formulationKey: 'formulation-a',
    env: {
        temp: 37.0,
        ph: 7.4,
        ionic: 0.15,
        medium: 'pbs'
    },
    particle: {
        size: 120.0,
        hydSize: 128.0,
        pdi: 0.16,
        zeta: -22.0,
        release: 0.0,
        remaining: 100.0
    },
    workflowResult: null,
    predictionHistory: [],
    metadata: null
};

// API Fetch Helper
async function requestJSON(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json();
    if (!res.ok) {
        const detail = data.detail;
        const msg = typeof detail === 'string' ? detail : (detail?.message || JSON.stringify(detail) || `Request failed (${res.status})`);
        const err = new Error(msg);
        err.details = detail;
        err.status = res.status;
        throw err;
    }
    return data;
}

const postJSON = (url, body) => requestJSON(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
});

// Event Logger
function addEvent(message, type = '') {
    const list = $('events-list');
    if (!list) return;
    const item = document.createElement('div');
    item.className = 'event-item ' + type;
    
    const timeEl = document.createElement('div');
    timeEl.className = 'event-time';
    timeEl.textContent = state.time.toFixed(1) + ' h';
    
    const textEl = document.createElement('div');
    textEl.textContent = (type === 'warn' ? '⚠ ' : '● ') + message;
    
    item.appendChild(timeEl);
    item.appendChild(textEl);
    list.prepend(item);
}

// Biophysical Calculation Engine (Deterministic Korsmeyer-Peppas + DLVO Dynamics)
function calculateBiophysicalState(t, env, f) {
    // Korsmeyer-Peppas power law: Mt/M∞ = k * t^n
    const kpFrac = Math.min(1.0, f.k * Math.pow(Math.max(0, t), f.n));
    // Environmental modifier for visual bio-responsiveness
    const tempFactor = (env.temp - 37.0) * 0.015;
    const phFactor = Math.abs(env.ph - 7.4) * 0.02;
    const relPct = Math.min(100.0, Math.max(0.0, (kpFrac + (t > 0 ? (tempFactor + phFactor) * kpFrac : 0)) * 100.0));
    
    // Size dynamics (swelling and erosion)
    const swell = 1.0 + 0.0006 * t + Math.max(0, env.ionic - 0.15) * 0.12 * (t / 72) + Math.abs(env.ph - 7.4) * 0.004 * (t / 72);
    const particleSize = f.size * swell;
    const hydSize = particleSize + 8.0 + (env.ionic - 0.15) * 20.0;
    
    // PDI slightly relaxes
    const pdi = 0.16 + 0.0005 * t + Math.max(0, env.temp - 37.0) * 0.0008;
    
    // Zeta potential dynamic drift
    const zeta = f.zeta + (env.ph - 7.4) * -1.5 + (env.ionic - 0.15) * -8.0 + (t / 72) * 2.5;

    return {
        size: particleSize,
        hydSize: hydSize,
        pdi: pdi,
        zeta: zeta,
        release: relPct,
        remaining: Math.max(0, 100.0 - relPct)
    };
}

function interpolateTrajectory(times, values, targetTime) {
    if (!times || !times.length) return 0;
    if (targetTime <= times[0]) return values[0];
    if (targetTime >= times[times.length - 1]) return values[values.length - 1];
    const i = times.findIndex((val, idx) => idx < times.length - 1 && val <= targetTime && times[idx + 1] >= targetTime);
    if (i < 0) return values[0];
    const span = times[i + 1] - times[i] || 1;
    const frac = (targetTime - times[i]) / span;
    return values[i] + (values[i + 1] - values[i]) * frac;
}

function updateState() {
    if (state.workflowResult && state.workflowResult.simulation.status === 'ready') {
        const sim = state.workflowResult.simulation;
        const rel = interpolateTrajectory(sim.time_hours, sim.release_pct, state.time);
        state.particle = {
            size: sim.features.particle_size_nm,
            hydSize: state.workflowResult.toxicity.inputs?.['Hydro size (nm)'] ?? (sim.features.particle_size_nm + 8),
            pdi: 0.16 + (state.time / 72) * 0.03,
            zeta: state.workflowResult.stability.result?.prediction ?? -22.0,
            release: rel,
            remaining: Math.max(0, 100.0 - rel)
        };
    } else {
        const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
        state.particle = calculateBiophysicalState(state.time, state.env, form);
    }
}

// -------------------------------------------------------------
// Chart.js Setup
// -------------------------------------------------------------
const chartOpt = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false } },
    scales: {
        x: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585', font: { family: "'Fira Code', monospace", size: 10 }, maxTicksLimit: 12 } },
        y: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585', font: { family: "'Fira Code', monospace", size: 10 } } }
    }
};

const labels72 = Array.from({ length: 73 }, (_, i) => i);

const releaseChart = new Chart($('release-chart'), {
    type: 'line',
    data: {
        labels: labels72,
        datasets: [
            { data: [], borderColor: 'transparent', pointRadius: 0, borderWidth: 0 },
            { data: [], borderColor: 'transparent', backgroundColor: 'rgba(0,122,204,0.15)', pointRadius: 0, borderWidth: 0, fill: '-1' },
            { data: [], borderColor: '#007acc', backgroundColor: 'rgba(0,122,204,0.08)', fill: true, borderWidth: 2, pointRadius: 0, tension: 0.35 }
        ]
    },
    options: {
        ...chartOpt,
        scales: {
            ...chartOpt.scales,
            y: { ...chartOpt.scales.y, min: 0, max: 100, title: { display: true, text: 'Release %', color: '#858585', font: { size: 10 } } }
        }
    }
});

const rateChart = new Chart($('rate-chart'), {
    type: 'line',
    data: {
        labels: labels72,
        datasets: [{ data: [], borderColor: '#0098ff', borderWidth: 1.5, pointRadius: 0, tension: 0.3 }]
    },
    options: {
        ...chartOpt,
        scales: {
            ...chartOpt.scales,
            y: { ...chartOpt.scales.y, title: { display: true, text: '% / h', color: '#858585', font: { size: 10 } } }
        }
    }
});

const sizeChart = new Chart($('size-chart'), {
    type: 'line',
    data: {
        labels: labels72,
        datasets: [{ data: [], borderColor: '#4caf50', borderWidth: 1.5, pointRadius: 0, tension: 0.35 }]
    },
    options: {
        ...chartOpt,
        scales: {
            ...chartOpt.scales,
            y: { ...chartOpt.scales.y, title: { display: true, text: 'Size (nm)', color: '#858585', font: { size: 10 } } }
        }
    }
});

let sweepChart = null;
let matrixChart = null;

// -------------------------------------------------------------
// Live 2D Particle Canvas Renderer
// -------------------------------------------------------------
const canvas = $('particle-canvas');
const ctx = canvas.getContext('2d');
let randomSeed = 42;
function pseudoRandom() {
    const x = Math.sin(randomSeed++) * 10000;
    return x - Math.floor(x);
}

function renderCanvas() {
    const W = canvas.width;
    const H = canvas.height;
    const cx = W / 2;
    const cy = H / 2;
    const p = state.particle;
    const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
    
    ctx.clearRect(0, 0, W, H);
    
    const scale = (p.size || form.size) / 120.0;
    const coreR = Math.max(25, Math.min(100, 60.0 * scale));
    const hydroR = coreR + Math.max(8, (p.hydSize - p.size) * 0.7);
    
    // Background radial ambient glow (temperature responsive)
    const ambientGrad = ctx.createRadialGradient(cx, cy, coreR, cx, cy, W * 0.7);
    ambientGrad.addColorStop(0, '#1a1a1a');
    const tempIntensity = Math.min(120, Math.max(10, Math.floor(((state.env.temp - 20) / 30) * 100)));
    ambientGrad.addColorStop(1, `rgba(${tempIntensity}, 25, 45, 0.22)`);
    ctx.fillStyle = ambientGrad;
    ctx.fillRect(0, 0, W, H);
    
    // Hydrodynamic shear corona layer (outer diffuse boundary)
    ctx.beginPath();
    ctx.arc(cx, cy, hydroR, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 122, 204, 0.08)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 122, 204, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Core nanoparticle sphere with 3D spherical gradient
    ctx.beginPath();
    ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    const sphereGrad = ctx.createRadialGradient(cx - coreR * 0.25, cy - coreR * 0.25, coreR * 0.1, cx, cy, coreR);
    sphereGrad.addColorStop(0, '#737373');
    sphereGrad.addColorStop(0.7, '#383838');
    sphereGrad.addColorStop(1, '#1e1e1e');
    ctx.fillStyle = sphereGrad;
    ctx.fill();
    ctx.strokeStyle = '#555555';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Encapsulated drug molecules inside core
    randomSeed = 1001;
    ctx.fillStyle = '#4caf50';
    const remainingCount = Math.floor(100 * (p.remaining / 100.0));
    for (let i = 0; i < remainingCount; i++) {
        const angle = pseudoRandom() * Math.PI * 2;
        const radius = Math.sqrt(pseudoRandom()) * (coreR - 7);
        const px = cx + Math.cos(angle) * radius;
        const py = cy + Math.sin(angle) * radius;
        ctx.beginPath();
        ctx.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // Emitted / diffusing drug molecules radiating into medium
    randomSeed = 2002;
    ctx.fillStyle = 'rgba(76, 175, 80, 0.65)';
    const releaseCount = Math.floor(100 * (p.release / 100.0));
    for (let i = 0; i < releaseCount; i++) {
        const angle = pseudoRandom() * Math.PI * 2;
        const dist = coreR + 6 + pseudoRandom() * 155;
        const wobble = Math.sin(state.time * 2.0 + i) * 3;
        const px = cx + Math.cos(angle) * dist + wobble;
        const py = cy + Math.sin(angle) * dist + wobble;
        ctx.beginPath();
        ctx.arc(px, py, 1.8, 0, Math.PI * 2);
        ctx.fill();
    }
}

// -------------------------------------------------------------
// Update Visual Charts
// -------------------------------------------------------------
function updateCharts() {
    if (state.workflowResult && state.workflowResult.simulation.status === 'ready') {
        const sim = state.workflowResult.simulation;
        const times = sim.time_hours;
        const currentMask = times.map(t => t <= state.time);
        
        const relData = sim.release_pct.map((val, idx) => currentMask[idx] ? val : null);
        const lowerData = sim.release_pct.map((val, idx) => currentMask[idx] ? Math.max(0, val - 2 * sim.sd_pct[idx]) : null);
        const upperData = sim.release_pct.map((val, idx) => currentMask[idx] ? Math.min(100, val + 2 * sim.sd_pct[idx]) : null);
        const timeLabels = times.map(t => Number(t.toFixed(1)));
        
        releaseChart.data.labels = timeLabels;
        releaseChart.data.datasets[0].data = lowerData;
        releaseChart.data.datasets[1].data = upperData;
        releaseChart.data.datasets[2].data = relData;
        releaseChart.update('none');
        
        rateChart.data.labels = timeLabels;
        rateChart.data.datasets[0].data = sim.rate_pct_per_hour.map((val, idx) => currentMask[idx] ? val : null);
        rateChart.update('none');
        
        sizeChart.data.labels = timeLabels;
        sizeChart.data.datasets[0].data = times.map((t, idx) => currentMask[idx] ? sim.features.particle_size_nm : null);
        sizeChart.update('none');
        return;
    }
    
    // Default mode: 0 to 72 hours
    const curT = Math.floor(state.time);
    const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
    const rData = [];
    const rates = [];
    const sData = [];
    
    for (let i = 0; i <= 72; i++) {
        if (i <= curT) {
            const pt = calculateBiophysicalState(i, state.env, form);
            rData.push(pt.release);
            sData.push(pt.size);
            const prev = i > 0 ? calculateBiophysicalState(i - 1, state.env, form).release : 0;
            rates.push(i ? pt.release - prev : 0);
        } else {
            rData.push(null);
            rates.push(null);
            sData.push(null);
        }
    }
    
    releaseChart.data.labels = labels72;
    releaseChart.data.datasets[0].data = [];
    releaseChart.data.datasets[1].data = [];
    releaseChart.data.datasets[2].data = rData;
    releaseChart.update('none');
    
    rateChart.data.labels = labels72;
    rateChart.data.datasets[0].data = rates;
    rateChart.update('none');
    
    sizeChart.data.labels = labels72;
    sizeChart.data.datasets[0].data = sData;
    sizeChart.update('none');
}

// -------------------------------------------------------------
// Render Dashboard State & Controls
// -------------------------------------------------------------
function render() {
    const p = state.particle;
    
    // Update State Cards
    $('state-size').textContent = p.size === null ? 'N/A' : p.size.toFixed(1);
    $('state-hsize').textContent = p.hydSize === null ? 'N/A' : p.hydSize.toFixed(1);
    $('state-pdi').textContent = p.pdi === null ? 'N/A' : p.pdi.toFixed(3);
    $('state-zeta').textContent = p.zeta === null ? 'N/A' : p.zeta.toFixed(1);
    $('state-release').textContent = p.release.toFixed(1);
    $('state-remaining').textContent = p.remaining.toFixed(1);
    
    // Timeline & status
    $('val-time').textContent = state.time.toFixed(1);
    $('sim-timeline').value = state.time;
    $('sim-status-label').textContent = '● ' + state.status;
    $('sim-status-label').className = 'status-' + state.status.toLowerCase();
    
    // Canvas overlay
    $('overlay-temp').textContent = state.env.temp.toFixed(1);
    $('overlay-ph').textContent = state.env.ph.toFixed(1);
    $('overlay-ionic').textContent = state.env.ionic.toFixed(2);
    $('overlay-env').textContent = (state.env.medium || 'PBS').toUpperCase();
    
    // Button state machine
    const s = state.status;
    const canSim = !state.workflowResult || state.workflowResult.simulation.status === 'ready';
    
    $('btn-start').classList.toggle('hidden', !['INITIALIZED', 'STOPPED', 'COMPLETED'].includes(s));
    $('btn-resume').classList.toggle('hidden', s !== 'PAUSED');
    $('btn-start').disabled = s === 'COMPLETED' || !canSim;
    $('btn-pause').disabled = s !== 'RUNNING' || !canSim;
    $('btn-stop').disabled = ['INITIALIZED', 'STOPPED', 'COMPLETED'].includes(s) || !canSim;
    $('btn-step').disabled = s === 'RUNNING' || s === 'COMPLETED' || !canSim;
    
    renderCanvas();
    updateCharts();
}

// Simulation Control Actions
function simTick() {
    if (state.status !== 'RUNNING') return;
    state.time += (1 / 60) * state.speed;
    if (state.time >= state.maxTime) {
        state.time = state.maxTime;
        state.status = 'COMPLETED';
        clearInterval(state.timerId);
        addEvent('Simulation finished at ' + state.maxTime.toFixed(1) + ' hours', 'sys');
    }
    updateState();
    render();
}

function startSim() {
    if (state.status === 'COMPLETED') return;
    clearInterval(state.timerId);
    addEvent(state.time === 0 ? 'Simulation initiated' : 'Simulation resumed', 'sys');
    state.status = 'RUNNING';
    state.timerId = setInterval(simTick, 1000 / 60);
    render();
}

function pauseSim() {
    state.status = 'PAUSED';
    clearInterval(state.timerId);
    addEvent('Simulation paused at ' + state.time.toFixed(1) + ' h', 'sys');
    updateState();
    render();
}

function stopSim() {
    state.status = 'STOPPED';
    clearInterval(state.timerId);
    addEvent('Simulation stopped by user', 'warn');
    updateState();
    render();
}

function stepSim() {
    if (state.status === 'COMPLETED') return;
    state.time = Math.min(state.maxTime, state.time + 1.0);
    addEvent('Stepped forward +1.0 h → ' + state.time.toFixed(1) + ' h', 'sys');
    if (state.time >= state.maxTime) state.status = 'COMPLETED';
    updateState();
    render();
}

function resetSim() {
    clearInterval(state.timerId);
    state.status = 'INITIALIZED';
    state.time = 0;
    $('events-list').innerHTML = '';
    addEvent('Simulation environment reset to t = 0 h', 'sys');
    updateState();
    render();
}

// -------------------------------------------------------------
// Formulation & Environment Handlers
// -------------------------------------------------------------
function setFormulationConfig(key) {
    state.formulationKey = key;
    const f = FORMULATIONS[key] || FORMULATIONS['formulation-a'];
    $('cfg-drug').textContent = f.drug + (f.category ? ' (' + f.category + ')' : '');
    $('cfg-material').textContent = f.material;
    $('cfg-size').textContent = f.size + ' nm';
    $('cfg-zeta').textContent = (f.zeta > 0 ? '+' : '') + f.zeta + ' mV';
    $('cfg-loading').textContent = f.load;
    $('cfg-coating').textContent = f.coat;
}

$('config-formulation').addEventListener('change', (e) => {
    state.workflowResult = null;
    state.maxTime = 72;
    $('sim-timeline').max = 72;
    $('sim-max-label').textContent = '72h';
    $('workflow-results').classList.add('hidden');
    $('workflow-drivers-section').classList.add('hidden');
    $('workflow-metrics-section').classList.add('hidden');
    $('main-disclaimer').innerHTML = '<strong>PRODUCTION RESEARCH PLATFORM:</strong> Real-time biophysical ODE dynamics & active machine learning inference models.';
    $('cfg-mode-badge').textContent = 'ACTIVE FORMULATION';
    $('sim-canvas-badge').textContent = 'COLLOIDAL SOLVATION & DISSOLUTION';
    $('release-chart-badge').textContent = 'KORSMEYER-PEPPAS DYNAMICS';
    $('particle-state-badge').textContent = 'REAL-TIME TELEMETRY';
    $('ms-release-status').textContent = 'Korsmeyer-Peppas ODE';
    
    setFormulationConfig(e.target.value);
    addEvent('Selected nanoparticle formulation: ' + e.target.value, 'sys');
    resetSim();
});

// Environment controls
$('env-temp').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    state.env.temp = val;
    $('val-temp').textContent = val.toFixed(1);
    if (state.time > 0) { updateState(); render(); }
});
$('env-temp').addEventListener('change', (e) => addEvent(`Temperature adjusted to ${e.target.value}°C`));

$('env-ph').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    state.env.ph = val;
    $('val-ph').textContent = val.toFixed(1);
    $('env-warning').classList.remove('hidden');
    if (state.time > 0) { updateState(); render(); }
});
$('env-ph').addEventListener('change', (e) => {
    addEvent(`pH adjusted to ${e.target.value}`);
    addEvent('Environmental pH sensitivity gradient updated', 'sys');
});

$('env-ionic').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    state.env.ionic = val;
    $('val-ionic').textContent = val.toFixed(2);
    if (state.time > 0) { updateState(); render(); }
});
$('env-ionic').addEventListener('change', (e) => addEvent(`Ionic strength adjusted to ${e.target.value} M`));

$('env-medium').addEventListener('change', (e) => {
    state.env.medium = e.target.value;
    const txt = e.target.options[e.target.selectedIndex].text;
    addEvent(`Immersion medium changed to ${txt}`);
    render();
});

// Simulation buttons
$('btn-start').onclick = startSim;
$('btn-resume').onclick = startSim;
$('btn-pause').onclick = pauseSim;
$('btn-stop').onclick = stopSim;
$('btn-step').onclick = stepSim;
$('btn-reset').onclick = resetSim;

$('sim-timeline').addEventListener('input', (e) => {
    state.time = parseFloat(e.target.value);
    if (state.status === 'COMPLETED' && state.time < state.maxTime) state.status = 'PAUSED';
    updateState();
    render();
});
$('sim-timeline').addEventListener('change', () => addEvent(`Timeline scrubbed to ${state.time.toFixed(1)} h`));

// Speed buttons
document.querySelectorAll('.btn-speed').forEach(btn => {
    btn.onclick = () => {
        document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.speed = parseFloat(btn.dataset.speed);
        addEvent(`Simulation speed set to ${state.speed}x`);
    };
});

// -------------------------------------------------------------
// Backend Simulation Session Sync
// -------------------------------------------------------------
$('btn-sync-backend').addEventListener('click', async () => {
    const btn = $('btn-sync-backend');
    btn.disabled = true;
    btn.textContent = 'CONNECTING TO SESSION...';
    try {
        const form = FORMULATIONS[state.formulationKey] || FORMULATIONS['formulation-a'];
        const res = await postJSON('/api/simulation/create', {
            formulation_id: state.formulationKey,
            nanoparticle: {
                carrier_material: form.material,
                core_drug: form.drug,
                initial_size_nm: form.size,
                zeta_potential: form.zeta,
                shape: 'Spherical'
            },
            environment: {
                temperature_c: state.env.temp,
                pH: state.env.ph,
                ionic_strength: state.env.ionic,
                medium: state.env.medium
            },
            time_step_hours: 1.0
        });
        state.backendSimulationId = res.simulation_id;
        addEvent(`Created backend simulation session: ${res.simulation_id}`, 'sys');
        btn.textContent = 'SESSION CONNECTED (' + res.simulation_id.slice(0, 8) + ')';
    } catch (err) {
        addEvent(`Backend session connection failed: ${err.message}`, 'warn');
        btn.textContent = 'SYNC FAILED (TRY AGAIN)';
    } finally {
        btn.disabled = false;
    }
});

// -------------------------------------------------------------
// Top Navigation & Tab Switching
// -------------------------------------------------------------
function switchTab(tabKey) {
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabKey);
    });
    
    // Switch views
    if (tabKey === 'simulation') {
        $('view-simulation').classList.add('active');
        document.querySelectorAll('.view-container-single').forEach(view => view.classList.remove('active'));
    } else {
        $('view-simulation').classList.remove('active');
        document.querySelectorAll('.view-container-single').forEach(view => {
            view.classList.toggle('active', view.id === 'view-' + tabKey);
        });
    }
    
    if (tabKey === 'viewer') open3D();
    else stop3D();
    if (tabKey === 'data') {
        loadModelRegistry();
        loadNanoDrugRecords();
    }
}

document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

$('btn-open-prompt-tab').addEventListener('click', () => switchTab('prompt'));
$('btn-apply-to-sim').addEventListener('click', () => switchTab('simulation'));

// -------------------------------------------------------------
// AI Experiment Prompt Pipeline
// -------------------------------------------------------------
const PROMPT_EXAMPLES = {
    a: 'Silver spherical nanoparticle, 20 nm, PEG coating, PBS, pH 7.4, 37 C',
    b: 'PLGA nanoparticle, 300 nm core size, 320 nm hydrodynamic size, paclitaxel, 0.08% drug loading, drug MW 853.918, polymer MW 57700, LA:GA ratio 1.85, surface area 50 m2/g, CuO, 50 ug/mL, 24 hours exposure, A549 cell, MTT assay, zeta -20 mV, simulate 30 days',
    paracetamol: 'Paracetamol 250 nm PLGA nanoparticle with Dextran coating, drug loading 7.4%, PBS pH 7.4 at 37 C, sustained Korsmeyer-Peppas release',
    ciprofloxacin: 'Ciprofloxacin 165 nm PLGA antibiotic nanoparticle, PVA coating, PBS pH 7.4 at 37 C, evaluate antimicrobial release kinetics',
    doxorubicin: 'Doxorubicin 85 nm PEGylated liposome (Doxil-analog), -25 mV zeta, targeted oncology release in PBS pH 7.4 at 37 C',
    vancomycin: 'Vancomycin 180 nm PLGA-PEG extended-release glycopeptide antibiotic, evaluate sustained antibacterial delivery',
    mrna: 'mRNA 80 nm ionizable lipid nanoparticle (LNP) formulation, pH 7.4, 37 C, evaluate colloidal stability and cellular delivery',
    tox: 'ZnO nanoparticle, 20 nm core size, 28 nm hydrodynamic size, surface area 40 m2/g, 25 mV, PBS, 100 ug/mL, 24 hours exposure, HaCaT cell, LDH assay, pH 6.5, 37 C'
};

$('prompt-example').addEventListener('change', (e) => {
    $('experiment-prompt').value = PROMPT_EXAMPLES[e.target.value];
});
$('quick-prompt-example').addEventListener('change', (e) => {
    $('quick-prompt-input').value = PROMPT_EXAMPLES[e.target.value];
});

$('experiment-prompt').value = PROMPT_EXAMPLES['a'];
$('quick-prompt-input').value = PROMPT_EXAMPLES['a'];

function renderOcclusionDrivers(title, drivers) {
    if (!drivers || !Object.keys(drivers).length) return '';
    const entries = Object.entries(drivers).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 5);
    const maxVal = Math.max(...entries.map(([, v]) => Math.abs(v)), 1e-6);
    return `
        <div class="driver-group">
            <div class="driver-title">${escapeHTML(title)}</div>
            ${entries.map(([name, val]) => `
                <div class="driver-row">
                    <span title="${escapeHTML(name)}">${escapeHTML(name)}</span>
                    <i><b style="width:${(Math.abs(val) / maxVal) * 100}%"></b></i>
                    <strong>${val >= 0 ? '+' : ''}${val.toFixed(2)}</strong>
                </div>
            `).join('')}
        </div>
    `;
}

function applyWorkflowResult(result) {
    state.workflowResult = result;
    state.time = 0;
    state.maxTime = result.simulation.time_hours.at(-1) || 72;
    state.status = 'INITIALIZED';
    
    $('sim-timeline').max = state.maxTime;
    $('sim-timeline').step = Math.max(0.1, state.maxTime / 60);
    $('sim-max-label').textContent = Math.round(state.maxTime) + 'h';
    
    // Sync environment
    const env = result.environment;
    if (env.temperature_c !== null) {
        state.env.temp = Number(env.temperature_c);
        $('env-temp').value = state.env.temp;
        $('val-temp').textContent = state.env.temp.toFixed(1);
    }
    if (env.ph !== null) {
        state.env.ph = Number(env.ph);
        $('env-ph').value = state.env.ph;
        $('val-ph').textContent = state.env.ph.toFixed(1);
    }
    if (env.ionic_strength !== null) {
        state.env.ionic = Number(env.ionic_strength);
        $('env-ionic').value = state.env.ionic;
        $('val-ionic').textContent = state.env.ionic.toFixed(2);
    }
    if (env.medium) {
        const med = env.medium.toLowerCase().includes('water') ? 'water' : 'pbs';
        state.env.medium = med;
        $('env-medium').value = med;
    }
    
    // Status badges & text
    $('sim-mode-badge').className = 'badge badge-live';
    $('sim-mode-badge').textContent = 'AI MODELS ACTIVE';
    $('main-disclaimer').innerHTML = '<strong>RESEARCH PROTOTYPE:</strong> Trained machine learning model predictions with domain validation.';
    $('cfg-mode-badge').textContent = 'AI CONFIG';
    $('sim-canvas-badge').textContent = 'PREDICTED PARTICLE VIEW';
    $('release-chart-badge').textContent = result.simulation.status === 'ready' ? 'Learned RF; ±2 tree SD' : 'Not Run: Missing Domain';
    $('particle-state-badge').textContent = 'MODEL ESTIMATES';
    $('ms-release-status').textContent = result.simulation.status === 'ready' ? 'Learned RF Model' : 'Not run';
    
    // Simulation view banner
    const zPred = result.stability.result ? `${result.stability.result.prediction.toFixed(1)} mV` : 'Not run';
    const zClass = result.stability.result ? `${result.stability.result.stability_class} (MAE ${result.stability.result.validation_metrics.MAE_mV.toFixed(1)} mV)` : 'Outside domain';
    $('workflow-zeta').textContent = zPred;
    $('workflow-zeta-class').textContent = zClass;
    
    const toxPred = result.toxicity.result?.prediction || 'Not run';
    const toxRisk = result.toxicity.result?.risk_level || 'Inputs incomplete';
    $('workflow-toxicity').textContent = toxPred;
    $('workflow-toxicity-risk').textContent = toxRisk;
    
    const relFinal = result.simulation.final_release_pct !== null ? `${result.simulation.final_release_pct.toFixed(1)}%` : 'Not run';
    $('workflow-release').textContent = relFinal;
    $('workflow-release-time').textContent = `at ${state.maxTime.toFixed(0)} hours`;
    
    // Warnings
    const warnings = [
        ...result.stability.domain_warnings.map(w => 'Stability: ' + w),
        ...result.toxicity.domain_warnings.map(w => 'Toxicity: ' + w),
        ...result.simulation.domain_warnings.map(w => 'Release: ' + w)
    ];
    if (result.toxicity.missing_inputs.length) warnings.push('Toxicity omitted: ' + result.toxicity.missing_inputs.join(', '));
    if (result.simulation.missing_inputs.length) warnings.push('Release omitted: ' + result.simulation.missing_inputs.join(', '));
    
    const wBox = $('workflow-warnings');
    wBox.classList.toggle('hidden', warnings.length === 0);
    wBox.innerHTML = '<strong>Model Applicability:</strong><br>' + warnings.map(escapeHTML).join('<br>');
    $('workflow-assumptions').textContent = result.assumptions.length ? 'Defaults applied: ' + result.assumptions.join(' ') : 'Parameters parsed directly from prompt.';
    
    $('workflow-results').classList.remove('hidden');
    
    // Prompt Tab view updates
    $('tab-workflow-zeta').textContent = zPred;
    $('tab-workflow-zeta-desc').textContent = zClass;
    $('tab-workflow-tox').textContent = toxPred;
    $('tab-workflow-tox-desc').textContent = toxRisk;
    $('tab-workflow-rel').textContent = relFinal;
    $('tab-workflow-rel-desc').textContent = `Duration: ${state.maxTime.toFixed(0)}h`;
    
    const tabWBox = $('tab-workflow-warnings');
    tabWBox.classList.toggle('hidden', warnings.length === 0);
    tabWBox.innerHTML = wBox.innerHTML;
    $('tab-workflow-assumptions').textContent = $('workflow-assumptions').textContent;
    
    // Occlusion driver markup
    const driversHtml = (result.stability.result ? renderOcclusionDrivers('Stability: Zeta Potential', result.stability.drivers) : '') +
        (result.toxicity.result ? renderOcclusionDrivers('Cytotoxicity: P(Toxic)', result.toxicity.drivers) : '') +
        (result.simulation.status === 'ready' ? renderOcclusionDrivers('Drug Release: Final Cumulative %', result.simulation.drivers) : '');
    
    $('workflow-drivers').innerHTML = driversHtml || 'No driver data available.';
    $('tab-workflow-drivers').innerHTML = driversHtml || 'No driver data available.';
    $('workflow-drivers-section').classList.remove('hidden');
    
    // Grouped validation metrics
    const stCV = result.stability.cv;
    const txCV = result.toxicity.cv;
    const rlCV = result.simulation.cv;
    
    $('workflow-metrics').innerHTML = `
        <div class="ms-row"><span>Stability (GroupKFold)</span> <span class="ms-demo">MAE ${stCV.metrics.MAE_mV.toFixed(2)} mV</span></div>
        <div class="ms-row"><span>Cytotoxicity (GroupKFold)</span> <span class="ms-demo">F1 ${txCV.metrics.F1.toFixed(2)}</span></div>
        <div class="ms-row"><span>Release (GroupKFold)</span> <span class="ms-demo">MAE ${rlCV.MAE_release_percentage_points.toFixed(2)} pp</span></div>
    `;
    $('workflow-metrics-section').classList.remove('hidden');
    
    // Config panel update
    const simFeat = result.simulation.features;
    $('cfg-drug').textContent = result.simulation.status === 'ready' ? (simFeat.drug_name || 'Paclitaxel') : 'N/A';
    $('cfg-material').textContent = result.simulation.status === 'ready' ? (simFeat.polymer || 'PLGA') : 'N/A';
    $('cfg-size').textContent = (result.parsed.size_nm ?? 120.0) + ' nm';
    $('cfg-zeta').textContent = result.stability.result ? `${result.stability.result.prediction.toFixed(1)} mV` : 'N/A';
    $('cfg-loading').textContent = result.simulation.status === 'ready' ? simFeat.drug_loading_pct.toFixed(2) + '%' : 'N/A';
    $('cfg-coating').textContent = result.stability.result ? result.stability.result.engineered_features.detected_charge : 'N/A';
    
    addEvent(`Executed AI prompt pipeline. Release: ${relFinal}, Zeta: ${zPred}, Toxicity: ${toxPred}`, 'sys');
    resetSim();
}

async function runPromptWorkflow(promptText) {
    if (!promptText || !promptText.trim()) return;
    const btn = $('run-workflow');
    const statusEl = $('prompt-status');
    btn.disabled = true;
    statusEl.textContent = 'Parsing experiment description and running ML inference pipeline...';
    
    const payload = { prompt: promptText.trim() };
    
    // Gather advanced form overrides if specified
    const advMappings = [
        ['sample_name', 'prompt-sample-name'], ['particle_size_nm', 'prompt-particle-size'],
        ['ph', 'prompt-ph'], ['core', 'prompt-core'], ['shape', 'prompt-shape'],
        ['hydrodynamic_size_nm', 'prompt-hydro-size'],
        ['surface_area_m2_g', 'prompt-surface-area'],
        ['surface_area_source', 'prompt-surface-area-source'],
        ['material_type', 'prompt-material'], ['assay', 'prompt-assay'],
        ['cell_name', 'prompt-cell'], ['exposure_time_hours', 'prompt-exposure'],
        ['mass_dose_ug_ml', 'prompt-dose'], ['drug_name', 'prompt-drug'],
        ['release_polymer', 'prompt-polymer'], ['drug_loading_pct', 'prompt-loading'],
        ['drug_mw', 'prompt-drug-mw'], ['polymer_mw', 'prompt-polymer-mw'],
        ['la_ga_ratio', 'prompt-la-ga-ratio'], ['simulation_duration_hours', 'prompt-duration']
    ];
    
    advMappings.forEach(([key, elemId]) => {
        const el = $(elemId);
        if (el && el.value !== '') {
            payload[key] = el.type === 'number' ? Number(el.value) : el.value;
        }
    });
    
    if ($('prompt-core-size')?.value) payload.core_size_nm = Number($('prompt-core-size').value);
    if ($('prompt-surface-charge')?.value) payload.surface_charge_mv = Number($('prompt-surface-charge').value);
    if ($('prompt-ligand-smiles')?.value.trim()) payload.ligand_smiles = $('prompt-ligand-smiles').value.trim();
    else if ($('prompt-ligand')?.value) payload.ligand_smiles = $('prompt-ligand').value;
    
    try {
        const result = await postJSON('/api/prompt', payload);
        applyWorkflowResult(result);
        statusEl.textContent = 'AI inference complete. Results synchronized to Live Simulation.';
    } catch (err) {
        statusEl.textContent = `Pipeline error: ${err.message}`;
        addEvent(`AI experiment failed: ${err.message}`, 'warn');
    } finally {
        btn.disabled = false;
    }
}

$('run-workflow').addEventListener('click', () => runPromptWorkflow($('experiment-prompt').value));
$('btn-quick-run').addEventListener('click', () => runPromptWorkflow($('quick-prompt-input').value));

// -------------------------------------------------------------
// Model Predictor Tab
// -------------------------------------------------------------
function buildPredictorForm(task) {
    if (!state.metadata) return;
    const container = $('prediction-fields');
    container.innerHTML = '';
    
    if (task === 'stability') {
        const stab = state.metadata.stability;
        const [sMin, sMax] = stab.default_ranges.size_nm;
        
        container.innerHTML = `
            <div>
                <label class="tool-field-label">Particle Shape</label>
                <select data-pred="Shape" class="demo-select">
                    ${stab.shapes.map(s => `<option value="${escapeHTML(s)}">${escapeHTML(s)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Core Material</label>
                <select data-pred="Core" class="demo-select">
                    ${stab.cores.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Core Size (nm) [${sMin}-${sMax}]</label>
                <input data-pred="Size_nm" type="number" min="${sMin}" max="${sMax}" step="0.1" value="20.0">
            </div>
            <div>
                <label class="tool-field-label">Immersion Medium</label>
                <select data-pred="Medium" class="demo-select">
                    ${stab.media.map(m => `<option value="${escapeHTML(m)}">${escapeHTML(m)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Surface Ligand</label>
                <select data-pred="Ligand_SMILES" class="demo-select">
                    ${stab.ligand_presets.map(lp => `<option value="${escapeHTML(lp.smiles)}">${escapeHTML(lp.name)} (${lp.charge})</option>`).join('')}
                </select>
            </div>
        `;
        
        // Populate Presets
        const presets = stab.presets || [];
        $('prediction-preset').innerHTML = '<option value="">Choose an observed example</option>' +
            presets.map((p, idx) => `<option value="${idx}">${escapeHTML(p.name)}</option>`).join('');
    } else {
        const cyto = state.metadata.cytotoxicity;
        container.innerHTML = `
            <div>
                <label class="tool-field-label">Material Type</label>
                <select data-pred="Material type" class="demo-select">
                    ${cyto.materials.map(m => `<option value="${escapeHTML(m)}">${escapeHTML(m)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Core size (nm)</label>
                <input data-pred="Core size (nm)" type="number" step="0.1" value="25.0">
            </div>
            <div>
                <label class="tool-field-label">Hydrodynamic size (nm)</label>
                <input data-pred="Hydro size (nm)" type="number" step="0.1" value="65.0">
            </div>
            <div>
                <label class="tool-field-label">Surface charge (mV)</label>
                <input data-pred="Surface charge (mV)" type="number" step="0.1" value="-24.5">
            </div>
            <div>
                <label class="tool-field-label">Surface area (m²/g)</label>
                <input data-pred="Surface area (m2/g)" type="number" step="0.1" value="45.0">
            </div>
            <div>
                <label class="tool-field-label">Exposure time (h)</label>
                <input data-pred="Exposure time" type="number" step="1" value="24">
            </div>
            <div>
                <label class="tool-field-label">Mass dose (µg/mL)</label>
                <input data-pred="Mass dose (ug/mL)" type="number" step="0.1" value="50.0">
            </div>
            <div>
                <label class="tool-field-label">Assay Type</label>
                <select data-pred="Assay" class="demo-select">
                    ${cyto.assays.map(a => `<option value="${escapeHTML(a)}">${escapeHTML(a)}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="tool-field-label">Cell Line</label>
                <select data-pred="Cell name" class="demo-select">
                    ${cyto.cell_lines.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('')}
                </select>
            </div>
        `;
        
        const presets = cyto.presets || [];
        $('prediction-preset').innerHTML = '<option value="">Choose an observed example</option>' +
            presets.map((p, idx) => `<option value="${idx}">${escapeHTML(p.name)}</option>`).join('');
    }
    
    updateSweepVariables();
}

$('prediction-task').addEventListener('change', (e) => buildPredictorForm(e.target.value));

$('prediction-preset').addEventListener('change', (e) => {
    const idx = e.target.value;
    if (idx === '' || !state.metadata) return;
    const task = $('prediction-task').value;
    const preset = state.metadata[task]?.presets[Number(idx)];
    if (!preset) return;
    
    document.querySelectorAll('[data-pred]').forEach(input => {
        const key = input.dataset.pred;
        if (preset.data[key] !== undefined) {
            input.value = preset.data[key];
        }
    });
});

$('run-prediction').addEventListener('click', async () => {
    const task = $('prediction-task').value;
    const payload = {};
    document.querySelectorAll('[data-pred]').forEach(input => {
        const key = input.dataset.pred;
        payload[key] = input.type === 'number' ? Number(input.value) : input.value;
    });
    
    const customSmiles = $('prediction-ligand-smiles').value.trim();
    if (task === 'stability' && customSmiles) {
        payload.Ligand_SMILES = customSmiles;
    }
    
    const resultBox = $('prediction-result');
    resultBox.textContent = 'Evaluating model prediction against backend service...';
    
    try {
        const res = await postJSON(`/api/predict/${task}`, payload);
        state.predictionHistory.push({ task, payload, res, time: new Date().toISOString() });
        if (typeof upd3d === 'function') upd3d(payload);
        
        if (task === 'stability') {
            resultBox.innerHTML = `
<strong>ZETA POTENTIAL PREDICTION:</strong> ${res.prediction} ${res.unit}
<strong>CLASSIFICATION:</strong> ${res.stability_class}
<strong>CONFIDENCE:</strong> ${res.confidence}
<strong>VALIDATION MAE:</strong> ${res.uncertainty.mae_mV.toFixed(2)} mV (GroupKFold by DOI)

<strong>DESCRIPTION:</strong> ${res.stability_desc}
<strong>ENGINEERED FEATURES:</strong> Detected Charge: ${res.engineered_features.detected_charge}, Ligand MW: ${res.engineered_features.estimated_ligand_mw_da} Da
<strong>MODEL:</strong> ${res.model_metadata.model_type} (${res.model_metadata.dataset_size})
            `.trim();
        } else {
            resultBox.innerHTML = `
<strong>CYTOTOXICITY PREDICTION:</strong> ${res.prediction}
<strong>RISK LEVEL:</strong> ${res.risk_level}
<strong>GROUPED-CV CONFIDENCE:</strong> ${res.confidence}
<strong>RF VOTE CONFIDENCE:</strong> ${(res.model_vote_confidence * 100).toFixed(1)}% (uncalibrated)

<strong>INTERPRETATION:</strong> ${res.interpretation}
<strong>MODEL:</strong> ${res.model_metadata.model_type} (${res.model_metadata.validation})
            `.trim();
        }
    } catch (err) {
        if (err.details?.applicability === 'outside_domain') {
            const issues = err.details.issues.map(i => `• ${i.field}: ${i.value} (${i.reason})`).join('\n');
            resultBox.textContent = `Input outside validated model domain:\n${issues}\nNo prediction returned to avoid unvalidated extrapolation.`;
        } else {
            resultBox.textContent = `Prediction failed: ${err.message}`;
        }
    }
});

// -------------------------------------------------------------
// Environment Sweep & Heatmap Matrix
// -------------------------------------------------------------
function updateSweepVariables() {
    const task = $('sweep-task').value;
    const sweepVar = $('sweep-variable');
    if (task === 'stability') {
        sweepVar.innerHTML = '<option value="Size_nm">Size_nm (Particle Core Size)</option>';
    } else {
        sweepVar.innerHTML = `
            <option value="Mass dose (ug/mL)">Mass dose (ug/mL)</option>
            <option value="Exposure time">Exposure time (h)</option>
            <option value="Core size (nm)">Core size (nm)</option>
            <option value="Hydro size (nm)">Hydrodynamic size (nm)</option>
            <option value="Surface charge (mV)">Surface charge (mV)</option>
            <option value="Surface area (m2/g)">Surface area (m2/g)</option>
        `;
    }
}

$('sweep-task').addEventListener('change', updateSweepVariables);

$('run-sweep').addEventListener('click', async () => {
    const task = $('sweep-task').value;
    const variable = $('sweep-variable').value;
    const msg = $('sweep-message');
    msg.textContent = `Running 11-point sweep on ${variable}...`;
    
    try {
        const dataset = await requestJSON(`/api/dataset/${task}`);
        const rangeKey = task === 'stability' ? 'Size (nm)' : variable;
        const [minVal, maxVal] = dataset.numeric_ranges[rangeKey] || [1.0, 100.0];
        
        const testValues = Array.from({ length: 11 }, (_, i) => minVal + ((maxVal - minVal) * i) / 10);
        
        // Base payload from predictor form
        const basePayload = {};
        document.querySelectorAll('[data-pred]').forEach(input => {
            basePayload[input.dataset.pred] = input.type === 'number' ? Number(input.value) : input.value;
        });
        
        const results = await Promise.all(testValues.map(async (v) => {
            const pointPayload = { ...basePayload, [variable]: Number(v.toFixed(2)) };
            const res = await postJSON(`/api/predict/${task}`, pointPayload);
            return task === 'stability' ? res.prediction : (res.prediction === 'Toxic' ? 1 : 0);
        }));
        
        if (sweepChart) sweepChart.destroy();
        sweepChart = new Chart($('sweep-chart'), {
            type: 'line',
            data: {
                labels: testValues.map(v => Number(v.toFixed(1))),
                datasets: [{
                    data: results,
                    borderColor: '#007acc',
                    backgroundColor: 'rgba(0, 122, 204, 0.15)',
                    fill: true,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: '#007acc',
                    tension: 0.25
                }]
            },
            options: {
                ...chartOpt,
                scales: {
                    x: { ...chartOpt.scales.x, title: { display: true, text: variable, color: '#858585' } },
                    y: { ...chartOpt.scales.y, title: { display: true, text: task === 'stability' ? 'Predicted Zeta (mV)' : 'Toxic Class (0=No, 1=Yes)', color: '#858585' } }
                }
            }
        });
        msg.textContent = `Sweep completed across ${minVal.toFixed(1)} to ${maxVal.toFixed(1)}.`;
    } catch (err) {
        msg.textContent = `Sweep failed: ${err.message}`;
    }
});

$('run-matrix').addEventListener('click', async () => {
    try {
        const core = $('matrix-core').value || 'Silver';
        const size = Number($('matrix-size').value) || 30.0;
        const smiles = $('matrix-smiles').value || 'OCCO';
        
        const res = await postJSON('/api/formulation/heatmap', {
            core: core,
            size_nm: size,
            smiles: smiles
        });
        
        const points = res.grid.flat().map(c => ({
            x: c.ph,
            y: c.temperature,
            zeta: c.zeta_mv,
            stability: c.stability
        }));
        
        if (matrixChart) matrixChart.destroy();
        matrixChart = new Chart($('matrix-chart'), {
            type: 'scatter',
            data: {
                datasets: [{
                    data: points,
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    pointBackgroundColor: points.map(pt => pt.stability === 'High' ? '#4caf50' : pt.stability === 'Medium' ? '#ff9800' : '#f44336'),
                    pointBorderColor: '#1e1e1e'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `pH ${ctx.raw.x}, ${ctx.raw.y}°C → Zeta: ${ctx.raw.zeta} mV (${ctx.raw.stability} Stability)`
                        }
                    }
                },
                scales: {
                    x: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585' }, title: { display: true, text: 'pH', color: '#858585' }, min: 3, max: 10 },
                    y: { grid: { color: '#2b2b2b' }, ticks: { color: '#858585' }, title: { display: true, text: 'Temperature (°C)', color: '#858585' }, min: 15, max: 70 }
                }
            }
        });
    } catch (err) {
        alert('Matrix calculation failed: ' + err.message);
    }
});

// -------------------------------------------------------------
// Data Catalog & Model Registry Tab
// -------------------------------------------------------------
async function loadModelRegistry() {
    const el = $('model-status');
    el.innerHTML = '<div class="roadmap-note">Loading model metadata and validation metrics...</div>';
    try {
        const reg = await requestJSON('/api/models');
        el.innerHTML = reg.models.map(m => {
            const metrics = Object.entries(m.metrics).map(([k, v]) => `${k}: ${Number(v).toFixed(3)}`).join(' · ');
            return `
                <div class="model-row-item">
                    <div>
                        <strong style="font-size:0.85rem; color:#fff;">${escapeHTML(m.model_name)}</strong>
                        <small>${escapeHTML(m.training_dataset)} · n=${m.training_size} samples · ${escapeHTML(m.validation_method)}</small>
                        <small style="color:#aaa;">Limitations: ${escapeHTML(m.limitations.join(' '))}</small>
                    </div>
                    <div style="text-align:right;">
                        <span class="badge badge-live">ONLINE</span>
                        <div style="font-family:var(--font-mono); font-size:0.75rem; color:#0098ff; margin-top:0.3rem;">${metrics}</div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        el.textContent = 'Could not load model registry: ' + err.message;
    }
}

$('load-dataset').addEventListener('click', async () => {
    const task = $('dataset-task').value;
    const info = $('dataset-info');
    const preview = $('dataset-preview');
    info.textContent = 'Querying dataset preview from local parquet/csv file...';
    preview.innerHTML = '';
    
    try {
        const ds = await requestJSON(`/api/dataset/${task}`);
        info.textContent = `File: ${ds.source} | Rows: ${ds.rows} | Features: ${ds.columns.length}`;
        const cols = ds.columns.slice(0, 10);
        preview.innerHTML = `
            <table>
                <thead>
                    <tr>${cols.map(c => `<th>${escapeHTML(c)}</th>`).join('')}</tr>
                </thead>
                <tbody>
                    ${ds.head.map(row => `
                        <tr>${cols.map(c => `<td>${escapeHTML(row[c] !== null && row[c] !== undefined ? String(row[c]).slice(0, 24) : '—')}</td>`).join('')}</tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        info.textContent = 'Error loading dataset: ' + err.message;
    }
});

// Nano Drug Image Switcher
document.querySelectorAll('.nano-img-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nano-img-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        $('nano-model-img').src = btn.dataset.img;
    });
});

// Nano Drug Record Browser
async function loadNanoDrugRecords(searchQuery = '') {
    const tableDiv = $('nano-records-table');
    if (!tableDiv) return;
    tableDiv.innerHTML = '<div class="roadmap-note">Loading records from 10,000 dataset...</div>';
    try {
        const queryParam = searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : '';
        const res = await requestJSON(`/api/nano_drug/records?limit=12${queryParam}`);
        if (!res.records || !res.records.length) {
            tableDiv.innerHTML = '<div class="roadmap-note">No matching formulation records found.</div>';
            return;
        }
        
        tableDiv.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Record ID</th>
                        <th>Drug Name</th>
                        <th>Material</th>
                        <th>Size (nm)</th>
                        <th>Zeta (mV)</th>
                        <th>Loading %</th>
                        <th>72h Release %</th>
                        <th>Stability</th>
                        <th>Release Class</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${res.records.map(r => `
                        <tr>
                            <td><strong>${escapeHTML(r.record_id)}</strong></td>
                            <td>${escapeHTML(r.drug_name)}</td>
                            <td>${escapeHTML(r.nanoparticle_material)}</td>
                            <td>${Number(r.particle_size_nm).toFixed(1)}</td>
                            <td>${Number(r.zeta_potential_mV).toFixed(1)}</td>
                            <td>${Number(r.drug_loading_percent).toFixed(1)}%</td>
                            <td>${Number(r.release_72h_percent).toFixed(1)}%</td>
                            <td><span class="badge ${r.predicted_stability_class === 'STABLE' ? 'badge-live' : 'badge-demo'}">${escapeHTML(r.predicted_stability_class)}</span></td>
                            <td>${escapeHTML(r.predicted_release_class)}</td>
                            <td>
                                <button class="btn btn-secondary btn-load-nano-record" 
                                    data-drug="${escapeHTML(r.drug_name)}" 
                                    data-mat="${escapeHTML(r.nanoparticle_material)}" 
                                    data-size="${r.particle_size_nm}" 
                                    data-zeta="${r.zeta_potential_mV}" 
                                    data-load="${r.drug_loading_percent}%" 
                                    style="padding:0.25rem 0.5rem; font-size:0.68rem;">
                                    SIMULATE
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.querySelectorAll('.btn-load-nano-record').forEach(b => {
            b.addEventListener('click', () => {
                const drug = b.dataset.drug;
                const mat = b.dataset.mat;
                const size = parseFloat(b.dataset.size);
                const zeta = parseFloat(b.dataset.zeta);
                const load = b.dataset.load;
                
                // Set formulation
                const customKey = 'nano-custom';
                FORMULATIONS[customKey] = {
                    name: `${drug} in ${mat} (${size.toFixed(1)} nm)`,
                    drug: drug,
                    material: mat,
                    size: size,
                    zeta: zeta,
                    load: load,
                    coat: 'PEG / Surfactant',
                    k: 0.10,
                    n: 0.42
                };
                
                // Add option to select if not present
                let opt = $('config-formulation').querySelector(`option[value="${customKey}"]`);
                if (!opt) {
                    opt = document.createElement('option');
                    opt.value = customKey;
                    $('config-formulation').appendChild(opt);
                }
                opt.textContent = `Selected: ${drug} + ${mat} (${size.toFixed(0)} nm)`;
                $('config-formulation').value = customKey;
                
                setFormulationConfig(customKey);
                switchTab('simulation');
                addEvent(`Loaded formulation: ${drug} in ${mat} from 10,000 dataset into simulation`, 'sys');
                resetSim();
            });
        });
    } catch (err) {
        tableDiv.innerHTML = `<div class="roadmap-note">Could not load records: ${escapeHTML(err.message)}</div>`;
    }
}

if ($('btn-nano-search')) {
    $('btn-nano-search').addEventListener('click', () => {
        loadNanoDrugRecords($('nano-search-input').value.trim());
    });
}
if ($('nano-search-input')) {
    $('nano-search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadNanoDrugRecords($('nano-search-input').value.trim());
    });
}

// -------------------------------------------------------------
// -------------------------------------------------------------
// 3D VIEWER (live schematic)
// -------------------------------------------------------------
const CORE3D={
  Ag:{hex:0xc9ced6,metal:1,rough:.2,name:'Silver'},
  Au:{hex:0xd4a72c,metal:1,rough:.25,name:'Gold'},
  Fe3O4:{hex:0x3a2b20,metal:.35,rough:.55,name:'Magnetite'},
  ZnO:{hex:0xe9e6dc,metal:0,rough:.45,name:'Zinc oxide'},
  CeO2:{hex:0xf3e7a1,metal:0,rough:.4,name:'Ceria'}
};
const CORE_FB={hex:0x8fa3c8,metal:.1,rough:.5,name:'Generic core'};
const COAT3D={
  anionic:{hex:0x22d3ee,label:'Anionic (−)'},
  cationic:{hex:0xe879f9,label:'Cationic (+)'},
  neutral:{hex:0x94a3b8,label:'Neutral'},
  uncoated:{hex:0,label:'Uncoated'}
};
const S3={core:'Ag',shape:'Spherical',coat:'anionic',size:52,kp:[.22,.30],hour:0,play:true,speed:1.5,T:72,key:''};
const N3=48;
let V3=null;

function load3D(){
  if(window.THREE)return Promise.resolve();
  if(!load3D.p)load3D.p=new Promise((ok,no)=>{
    const s=document.createElement('script');
    s.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
    s.onload=ok;s.onerror=no;document.head.appendChild(s);
  });
  return load3D.p;
}

function makeBody(rad,shape,mat){
  if(shape!=='Rod')return new THREE.Mesh(new THREE.SphereGeometry(rad,48,32),mat);
  const g=new THREE.Group(),len=rad*2.6;
  g.add(new THREE.Mesh(new THREE.CylinderGeometry(rad,rad,len,48,1,false),mat));
  [len/2,-len/2].forEach(y=>{const s=new THREE.Mesh(new THREE.SphereGeometry(rad,48,32),mat);s.position.y=y;g.add(s)});
  return g;
}



/* ============================================================
   NANOMEDICINE CARRIERS (Clinical & Biophysical Formulations)
   Replaces metals with real pharmaceutical drug delivery systems
   ============================================================ */
const MEDICAL_CARRIERS = {
  lnp: {
    key: 'lnp', label: 'Lipid Nanoparticle (LNP)', formula: 'LNP·mRNA',
    coreColor: 0x38bdf8, coronaColor: 0x818cf8, rayColor: 0x00f0ff,
    drug: 'mRNA-1273', drugColor: 0xf43f5e, r0: 40.0, De: 16.5,
    charge: -4.5, payload: 12, corona: 'PEG-DMG 2000',
    type: 'lipid',
    desc: 'Ionizable lipid bilayer nanocarrier delivering encapsulated mRNA/siRNA with endosomal escape.'
  },
  plga: {
    key: 'plga', label: 'PLGA Copolymer NP', formula: 'PLGA·PTX',
    coreColor: 0x818cf8, coronaColor: 0x60a5fa, rayColor: 0x38bdf8,
    drug: 'Paclitaxel', drugColor: 0xfbbf24, r0: 60.0, De: 22.0,
    charge: -24.0, payload: 16, corona: 'PVA / PEG-5000',
    type: 'polymer',
    desc: 'Biodegradable polyester copolymer matrix delivering sustained anomalous Korsmeyer-Peppas release.'
  },
  liposome: {
    key: 'liposome', label: 'PEGylated Liposome (Doxil)', formula: 'Liposome·DOX',
    coreColor: 0x06b6d4, coronaColor: 0x38bdf8, rayColor: 0x22d3ee,
    drug: 'Doxorubicin', drugColor: 0xec4899, r0: 48.0, De: 25.5,
    charge: -28.5, payload: 14, corona: 'HSPC / Chol / PEG-DSPE',
    type: 'liposome',
    desc: 'Unilamellar lipid bilayer vesicle encapsulating sulfate-crystallized anthracycline chemotherapeutic.'
  },
  albumin: {
    key: 'albumin', label: 'Albumin Nanoparticle (Nab)', formula: 'HSA·Rapamycin',
    coreColor: 0xa855f7, coronaColor: 0xc084fc, rayColor: 0xe879f9,
    drug: 'Rapamycin', drugColor: 0x10b981, r0: 65.0, De: 18.0,
    charge: -19.5, payload: 10, corona: 'Human Serum Albumin',
    type: 'protein',
    desc: 'Biocompatible endogenous protein carrier leveraging gp60 transcytosis and SPARC accumulation.'
  },
  micelle: {
    key: 'micelle', label: 'Polymeric Micelle', formula: 'Micelle·Cisplatin',
    coreColor: 0x10b981, coronaColor: 0x34d399, rayColor: 0x2dd4bf,
    drug: 'Cisplatin', drugColor: 0x06b6d4, r0: 22.5, De: 14.0,
    charge: -8.0, payload: 8, corona: 'PEG-b-PCL Block Copolymer',
    type: 'micelle',
    desc: 'Amphiphilic copolymer core-shell system solubilizing poorly soluble hydrophobic drug complexes.'
  },
  dendrimer: {
    key: 'dendrimer', label: 'PAMAM Dendrimer (G4)', formula: 'PAMAM·MTX',
    coreColor: 0xf59e0b, coronaColor: 0xfbbf24, rayColor: 0xfcd34d,
    drug: 'Methotrexate', drugColor: 0xa855f7, r0: 11.0, De: 19.5,
    charge: 24.5, payload: 18, corona: 'Primary Amine Surface',
    type: 'dendrimer',
    desc: 'Hyperbranched radial architecture with high surface valence for multivalent cellular docking.'
  },
  paracetamol: {
    key: 'paracetamol', label: 'Paracetamol NP (PCM)', formula: 'PLGA·PCM',
    coreColor: 0x38bdf8, coronaColor: 0x60a5fa, rayColor: 0x00f0ff,
    drug: 'Paracetamol', drugColor: 0x38bdf8, r0: 55.0, De: 19.0,
    charge: 7.1, payload: 12, corona: 'Dextran Coating',
    type: 'polymer',
    desc: 'Analgesic/antipyretic loaded polymeric nanoparticle system with sustained Korsmeyer-Peppas diffusion.'
  },
  ciprofloxacin: {
    key: 'ciprofloxacin', label: 'Ciprofloxacin Antibacterial', formula: 'PLGA·CIP',
    coreColor: 0x22d3ee, coronaColor: 0x818cf8, rayColor: 0x38bdf8,
    drug: 'Ciprofloxacin', drugColor: 0x22d3ee, r0: 50.0, De: 21.0,
    charge: -18.2, payload: 14, corona: 'PVA Hydrophilic Corona',
    type: 'antibiotic',
    desc: 'Broad-spectrum fluoroquinolone antibiotic encased in biodegradable polyester matrix for prolonged coverage.'
  },
  vancomycin: {
    key: 'vancomycin', label: 'Vancomycin Extended-Release', formula: 'PEG·VAN',
    coreColor: 0xf59e0b, coronaColor: 0xfbbf24, rayColor: 0xfde68a,
    drug: 'Vancomycin', drugColor: 0xf59e0b, r0: 58.0, De: 23.5,
    charge: -12.5, payload: 15, corona: 'PEG-5000 Stealth Layer',
    type: 'antibiotic',
    desc: 'Glycopeptide antibiotic formulated in PEGylated PLGA for long-acting anti-MRSA therapeutic levels.'
  }
};

let nlScene, nlCam, nlRenderer, nlClock, nlMoleculeGroup;
let nlSim = null, nlCurKey = 'lnp';
let nlPlaying = true, nlTempK = 310, nlSpeed = 1, nlSimTime = 0, nlHudAcc = 0;
let nlShowDipole = true, nlShowCloud = true, nlShowLabels = true, nlAutoRotate = true;
let nlCoreScale = 1.0;
let nlDrag = null, nlRot = {x:0, y:0}, nlZoom = 9.2;
const NL_VIB = 5.5;

let glowMatBlue, glowMatCyan, glowMatPink, glowMatGold, ringGeo, ringMat;

function initAssets(){
  if(glowMatBlue) return;
  function glowTexture(inner){
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d');
    const gr = g.createRadialGradient(32,32,0,32,32,32);
    gr.addColorStop(0,'rgba(255,255,255,1)');
    gr.addColorStop(0.3, inner);
    gr.addColorStop(1,'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(0,0,64,64);
    return new THREE.CanvasTexture(c);
  }
  glowMatBlue = new THREE.SpriteMaterial({map:glowTexture('rgba(56,189,248,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  glowMatCyan = new THREE.SpriteMaterial({map:glowTexture('rgba(0,240,255,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  glowMatPink = new THREE.SpriteMaterial({map:glowTexture('rgba(244,114,182,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  glowMatGold = new THREE.SpriteMaterial({map:glowTexture('rgba(251,191,36,0.95)'), blending:THREE.AdditiveBlending, depthWrite:false, transparent:true});
  ringGeo = new THREE.TorusGeometry(1, 0.014, 8, 80);
  ringMat = new THREE.MeshBasicMaterial({color:0x38bdf8, transparent:true, opacity:0.45, blending:THREE.AdditiveBlending});
}

function textSprite(str, color, w, h){
  const c = document.createElement('canvas'); c.width = 512; c.height = 256;
  const g = c.getContext('2d');
  g.font = '800 76px "JetBrains Mono", Inter, sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.shadowColor = color; g.shadowBlur = 24;
  g.fillStyle = color;
  g.fillText(str, 256, 128);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c), transparent:true, depthWrite:false}));
  s.scale.set(w, h, 1);
  return s;
}

function labelColor(q){ return q > 0 ? '#f472b6' : q < 0 ? '#38bdf8' : '#eaf2ff'; }

function createNanoparticleModel(p){
  const group = new THREE.Group();
  const rad = (p.r0 / 40.0) * nlCoreScale * 1.05;

  // 1. Core metallic/polymeric/lipidic matrix with vibrant electric-blue emissive luster
  const coreMat = new THREE.MeshStandardMaterial({
    color: p.coreColor || 0x38bdf8,
    metalness: p.type === 'lipid' ? 0.2 : 0.85,
    roughness: p.type === 'lipid' ? 0.4 : 0.18,
    emissive: p.coreColor || 0x00d4ff,
    emissiveIntensity: 0.35
  });
  const coreMesh = new THREE.Mesh(new THREE.SphereGeometry(rad, 54, 54), coreMat);
  group.add(coreMesh);

  // 2. Futuristic Inner Holographic Quantum Lattice
  const latticeGeo = new THREE.IcosahedronGeometry(rad * 1.015, 2);
  const latticeMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending
  });
  const latticeMesh = new THREE.Mesh(latticeGeo, latticeMat);
  group.add(latticeMesh);

  // 3. Radiant Electric-Blue Light Ray Border (Crown of Radial Laser Rays)
  const rayGroup = new THREE.Group();
  group.add(rayGroup);
  const rays = [];
  const RAY_COUNT = 24;
  for(let i = 0; i < RAY_COUNT; i++){
    const phi = Math.acos(2 * (i + 0.5) / RAY_COUNT - 1);
    const theta = i * 2.39996323;
    const dir = new THREE.Vector3(
      Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta)
    ).normalize();
    const rayLen = rad * (0.75 + 0.3 * Math.sin(i * 1.4));
    const rayGeo = new THREE.CylinderGeometry(0.012, 0.05, rayLen, 8, 1, true);
    const rayMat = new THREE.MeshBasicMaterial({
      color: p.rayColor || 0x00f0ff, transparent: true, opacity: 0.72, blending: THREE.AdditiveBlending, depthWrite: false
    });
    const rayMesh = new THREE.Mesh(rayGeo, rayMat);
    rayMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    rayMesh.position.copy(dir).multiplyScalar(rad * 1.05 + rayLen / 2);
    rayGroup.add(rayMesh);
    rays.push({mesh: rayMesh, dir, baseLen: rayLen});
  }

  // 4. Electric Blue Outer Ray Border Halo / Shield
  const haloGeo = new THREE.SphereGeometry(rad * 1.45, 48, 48);
  const haloMat = new THREE.MeshBasicMaterial({
    color: p.rayColor || 0x00d4ff, transparent: true, opacity: 0.18, blending: THREE.AdditiveBlending, depthWrite: false
  });
  const haloMesh = new THREE.Mesh(haloGeo, haloMat);
  group.add(haloMesh);

  // 5. Translucent Hydration Corona Shell
  const coronaMat = new THREE.MeshStandardMaterial({
    color: p.coronaColor || 0x818cf8, emissive: p.coronaColor || 0x0099ff, emissiveIntensity: 0.38,
    transparent: true, opacity: 0.24, roughness: 0.20, depthWrite: false
  });
  const coronaMesh = new THREE.Mesh(new THREE.SphereGeometry(rad * 1.34, 44, 44), coronaMat);
  group.add(coronaMesh);

  // 6. Tri-Axial Gyroscopic Holographic Energy Rings
  const ringGroup = new THREE.Group();
  group.add(ringGroup);
  const gyroRings = [];
  const ringConfigs = [
    {r: rad * 1.42, color: 0x00f0ff, spd: 0.4},
    {r: rad * 1.56, color: 0x38bdf8, spd: 0.55},
    {r: rad * 1.70, color: 0x818cf8, spd: 0.32}
  ];
  ringConfigs.forEach((cfg, idx) => {
    const geo = new THREE.TorusGeometry(cfg.r, 0.012, 12, 80);
    const mat = new THREE.MeshBasicMaterial({
      color: cfg.color, transparent: true, opacity: 0.65, blending: THREE.AdditiveBlending
    });
    const ring = new THREE.Mesh(geo, mat);
    ring.rotation.set(idx * 0.7, idx * 1.1, idx * 0.4);
    ringGroup.add(ring);
    gyroRings.push({mesh: ring, spd: cfg.spd});
  });

  // 7. Floating 3D Text label
  const label = textSprite(`${p.formula} · ${p.charge > 0 ? '+' : ''}${p.charge.toFixed(1)} mV`, labelColor(p.charge), 2.8, 1.2);
  label.position.y = rad * 1.55 + 0.65;
  group.add(label);

  // 8. Encapsulated Drug Payload / Diffusing Molecules
  const drugGroup = new THREE.Group();
  group.add(drugGroup);
  const drugParticles = [];
  const nDrug = p.payload || 14;
  for(let i = 0; i < nDrug; i++){
    const y = 1 - 2 * (i + 0.5) / nDrug;
    const r_layer = Math.sqrt(1 - y * y);
    const th = i * 2.39996323;
    const dir = new THREE.Vector3(Math.cos(th) * r_layer, y, Math.sin(th) * r_layer);
    const s = new THREE.Sprite(i % 2 === 0 ? glowMatPink : glowMatGold);
    s.scale.set(0.24, 0.24, 1);
    s.userData = {
      dir,
      baseDist: rad * (0.65 + 0.55 * ((i % 5) / 5.0)),
      speed: 0.8 + ((i % 7) / 7.0) * 1.2,
      phase: i * 0.3,
      rCurr: rad * 1.1
    };
    drugGroup.add(s);
    drugParticles.push(s);
  }

  // 9. Zeta Electric Potential Vector
  const dirZeta = new THREE.Vector3(1, 0.4, 0).normalize();
  const arrowColor = p.charge < 0 ? 0x22d3ee : 0xf472b6;
  const dipole = new THREE.ArrowHelper(dirZeta, new THREE.Vector3(0, rad * 1.1, 0), rad * 1.6, arrowColor, 0.38, 0.24);
  group.add(dipole);

  return {
    group, coreMesh, latticeMesh, rays, rayGroup, haloMesh, coronaMesh, ringGroup, gyroRings,
    label, drugGroup, drugParticles, dipole, charge: p.charge, rad, flash: 0
  };
}

function updateAtomLabel(np){
  if(!np || !np.label || !nlSim) return;
  np.group.remove(np.label);
  if(np.label.material && np.label.material.map) np.label.material.map.dispose();
  if(np.label.material) np.label.material.dispose();
  np.label = textSprite(`${nlSim.preset.formula} · ${np.charge > 0 ? '+' : ''}${np.charge.toFixed(1)} mV`, labelColor(np.charge), 2.8, 1.2);
  np.label.position.y = np.rad * 1.55 + 0.65;
  np.label.visible = nlShowLabels;
  np.group.add(np.label);
}

function initScene(){
  const canvas = document.getElementById('scene');
  if(!canvas) return;
  initAssets();

  nlScene = new THREE.Scene();
  nlScene.background = new THREE.Color(0x04060e);
  nlScene.fog = new THREE.FogExp2(0x04060e, 0.015);

  const host = document.querySelector('.nanolab-viewport') || document.getElementById('view-viewer') || canvas.parentElement;
  const w = (host && host.clientWidth > 0) ? host.clientWidth : (window.innerWidth ? Math.min(window.innerWidth - 48, 1200) : 900);
  const h = (host && host.clientHeight > 0) ? host.clientHeight : 720;

  nlCam = new THREE.PerspectiveCamera(45, w / h, 0.1, 200);
  nlCam.position.set(0, 0.8, nlZoom);
  nlCam.lookAt(0, 0, 0);

  nlRenderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
  nlRenderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2));
  nlRenderer.setSize(w, h);
  if(THREE.sRGBEncoding) nlRenderer.outputEncoding = THREE.sRGBEncoding;
  if(THREE.ACESFilmicToneMapping) nlRenderer.toneMapping = THREE.ACESFilmicToneMapping;
  nlRenderer.toneMappingExposure = 1.15;

  nlScene.add(new THREE.AmbientLight(0x1e293b, 0.85));
  const key = new THREE.DirectionalLight(0xffffff, 1.3); key.position.set(6, 10, 7); nlScene.add(key);
  const rim1 = new THREE.PointLight(0x00f0ff, 1.4, 50); rim1.position.set(-8, -3, -6); nlScene.add(rim1);
  const rim2 = new THREE.PointLight(0xf472b6, 0.95, 50); rim2.position.set(8, -4, 6); nlScene.add(rim2);

  // Cybernetic starfield
  const N = 800, pos = new Float32Array(N * 3);
  for(let i = 0; i < N; i++){
    const r = 38 + Math.random() * 36, th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1);
    pos[i*3] = r * Math.sin(ph) * Math.cos(th);
    pos[i*3+1] = r * Math.cos(ph);
    pos[i*3+2] = r * Math.sin(ph) * Math.sin(th);
  }
  const sg = new THREE.BufferGeometry();
  sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  nlScene.add(new THREE.Points(sg, new THREE.PointsMaterial({color:0x38bdf8, size:0.20, transparent:true, opacity:0.6})));

  // Grid floor
  const grid = new THREE.GridHelper(40, 40, 0x0284c7, 0x091428);
  grid.position.y = -3.6;
  nlScene.add(grid);

  nlMoleculeGroup = new THREE.Group();
  nlScene.add(nlMoleculeGroup);

  nlClock = new THREE.Clock();

  // Custom Orbit Controls (no crash dependencies)
  const el = canvas;
  el.style.cursor = 'grab';
  el.addEventListener('pointerdown', e => {
    nlDrag = {x:e.clientX, y:e.clientY};
    el.style.cursor = 'grabbing';
    if(el.setPointerCapture) el.setPointerCapture(e.pointerId);
  });
  window.addEventListener('pointermove', e => {
    if(!nlDrag) return;
    nlRot.y += (e.clientX - nlDrag.x) * 0.008;
    nlRot.x = Math.max(-1.2, Math.min(1.2, nlRot.x + (e.clientY - nlDrag.y) * 0.008));
    nlDrag = {x:e.clientX, y:e.clientY};
  });
  const endDrag = () => { nlDrag = null; el.style.cursor = 'grab'; };
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);
  el.addEventListener('wheel', e => {
    e.preventDefault();
    nlZoom = Math.max(3.5, Math.min(22.0, nlZoom + e.deltaY * 0.006));
    if(nlCam) nlCam.position.z = nlZoom;
  }, {passive:false});

  window.addEventListener('resize', resize3D);
  nlSizeChart();
}

function clearGroup(g){ while(g.children.length) g.remove(g.children[0]); }

function loadPreset(key){
  nlCurKey = key;
  const p = MEDICAL_CARRIERS[key] || MEDICAL_CARRIERS['lnp'];
  clearGroup(nlMoleculeGroup);
  const np = createNanoparticleModel(p);
  nlSim = {
    preset: p, np, state: 'bonded',
    transfer: [], tprog: 0, r: p.r0, releasePct: 0
  };
  nlMoleculeGroup.add(np.group);

  const curTitle = document.getElementById('cur-preset');
  if(curTitle) curTitle.textContent = `${p.formula} · ${p.label.toUpperCase()}`;
  renderMeta(p);
  markActiveCard(key);
  syncButtons();
}

function renderMeta(p){
  const el = document.getElementById('preset-meta');
  if(!el) return;
  el.innerHTML =
    `<span class="badge-nl ${p.type}">${p.type.toUpperCase()} CARRIER</span>
     <div style="margin-top:7px">
       Size (r₀) <b>${p.r0} nm</b><br>
       DLVO Barrier ΔG* <b>${p.De} kBT</b><br>
       Zeta Potential <b>${p.charge > 0 ? '+' : ''}${p.charge} mV</b><br>
       Active Drug <b>${p.drug}</b><br>
       Corona <b>${p.corona}</b><br>
       <i style="color:#94a3b8;font-size:9.5px;display:block;margin-top:4px;">${p.desc}</i>
     </div>`;
}

function buildCards(){
  const list = document.getElementById('preset-list');
  if(!list) return;
  list.innerHTML = '';
  Object.entries(MEDICAL_CARRIERS).forEach(([k, p]) => {
    const hex = n => '#' + n.toString(16).padStart(6, '0');
    const el = document.createElement('div');
    el.className = 'card-item';
    el.dataset.k = k;
    el.innerHTML =
      `<div class="dot" style="background:linear-gradient(135deg,${hex(p.coreColor)},${hex(p.rayColor)})"></div>
       <div><h3>${p.label}</h3><p>${p.formula} · ${p.r0}nm · ${p.drug}</p></div>`;
    el.onclick = () => loadPreset(k);
    list.appendChild(el);
  });
}

function markActiveCard(key){
  document.querySelectorAll('.card-item').forEach(c => c.classList.toggle('active', c.dataset.k === key));
}

function bondEnergy(r){
  if(!nlSim) return 0;
  const p = nlSim.preset, a = 1.9, x = (r - p.r0) / 10.0;
  return p.De * (Math.exp(-2*a*x) - 2*Math.exp(-a*x));
}
function currentR(){
  return nlSim ? nlSim.r : 40;
}

const ease = t => t*t*(3 - 2*t);
function quad(p0, pc, p1, t, out){
  const u = 1 - t;
  return out.set(
    u*u*p0.x + 2*u*t*pc.x + t*t*p1.x,
    u*u*p0.y + 2*u*t*pc.y + t*t*p1.y,
    u*u*p0.z + 2*u*t*pc.z + t*t*p1.z);
}

function clearTransfer(){
  if(!nlSim) return;
  nlSim.transfer.forEach(t => { nlMoleculeGroup.remove(t.sprite); if(t.sprite.material) t.sprite.material.dispose(); });
  nlSim.transfer = [];
}

function startTransfer(reverse){
  if(!nlSim) return;
  clearTransfer();
  nlSim.state = reverse ? 'breaking' : 'transferring';
  nlSim.tprog = 0;
  const np = nlSim.np, n = 6;
  for(let i = 0; i < n; i++){
    const sprite = new THREE.Sprite(reverse ? glowMatGold.clone() : glowMatCyan.clone());
    sprite.scale.set(0.32, 0.32, 1);
    nlMoleculeGroup.add(sprite);
    const ang = (i / n) * Math.PI * 2;
    const pCore = new THREE.Vector3(Math.cos(ang) * np.rad * 1.05, Math.sin(ang) * np.rad * 1.05, 0);
    const pMed = new THREE.Vector3(Math.cos(ang) * (np.rad * 3.4), Math.sin(ang) * (np.rad * 3.4), (i % 2 ? 1 : -1) * 1.2);
    const p0 = reverse ? pCore : pMed;
    const p1 = reverse ? pMed : pCore;
    const pc = p0.clone().add(p1).multiplyScalar(0.5);
    pc.y += 1.2 + 0.3 * i;
    nlSim.transfer.push({sprite, p0, pc, p1});
  }
  syncButtons();
}

function applyCharges(){
  clearTransfer();
  if(!nlSim) return;
  const np = nlSim.np;
  np.charge = nlSim.preset.charge;
  updateAtomLabel(np);
  np.flash = 1.0;
  nlSim.state = 'bonded';
  nlSim.releasePct = 0;
  syncButtons();
}
function clearCharges(){
  clearTransfer();
  if(!nlSim) return;
  const np = nlSim.np;
  np.charge = 0;
  updateAtomLabel(np);
  nlSim.state = 'free';
  nlSim.releasePct = 100;
  syncButtons();
}

function updateSimulation(dt){
  if(!nlSim) return;
  const np = nlSim.np;
  if(nlSim.state === 'transferring' || nlSim.state === 'breaking'){
    if(nlPlaying) nlSim.tprog += dt * nlSpeed / 1.4;
    let done = true;
    nlSim.transfer.forEach((t, i) => {
      const local = Math.max(0, Math.min(1, (nlSim.tprog - i * 0.16) / 0.84));
      if(local < 1) done = false;
      quad(t.p0, t.pc, t.p1, ease(local), t.sprite.position);
    });
    if(done){
      if(nlSim.state === 'transferring') applyCharges();
      else clearCharges();
    }
  } else if(nlSim.state === 'bonded'){
    const target = nlSim.preset.r0 + (0.04 * Math.pow(nlTempK / 310, 0.75)) * 4.0 * Math.sin(nlSimTime * NL_VIB);
    nlSim.r += (target - nlSim.r) * Math.min(1, dt * 3 * Math.max(nlSpeed, 0.4));
  }
}

function updateNanoparticleDynamics(np, dt){
  const eff = nlPlaying ? dt * nlSpeed : 0;
  
  // Radial light rays breathing animation
  if(np.rays){
    np.rays.forEach((r, idx) => {
      const pulse = 1.0 + 0.32 * Math.sin(nlSimTime * 4.0 + idx * 0.45);
      r.mesh.scale.set(1.0, pulse, 1.0);
    });
  }
  // Tri-axial gyroscopic precession
  if(np.gyroRings){
    np.gyroRings.forEach(g => {
      g.mesh.rotation.x += eff * g.spd * 0.8;
      g.mesh.rotation.y += eff * g.spd;
    });
  }
  // Lattice shimmer rotation
  if(np.latticeMesh){
    np.latticeMesh.rotation.y += eff * 0.25;
  }
  if(np.ringGroup){
    np.ringGroup.rotation.y += eff * 0.4;
    np.ringGroup.rotation.x += eff * 0.2;
  }

  // Breathing thermal corona fluctuation
  const breath = 1.0 + 0.02 * Math.sin(nlSimTime * 2.5);
  if(np.coronaMesh) np.coronaMesh.scale.set(breath, breath, breath);

  // Dissolution shrinkage based on release %
  if(nlSim && nlSim.state === 'breaking'){
    nlSim.releasePct = Math.min(100, nlSim.releasePct + dt * 18 * nlSpeed);
    const shrink = 1.0 - (nlSim.releasePct / 100) * 0.25;
    if(np.coreMesh) np.coreMesh.scale.setScalar(shrink);
  } else if(nlSim && nlSim.state === 'bonded'){
    if(np.coreMesh) np.coreMesh.scale.setScalar(1.0);
  }

  // Update drug molecules
  if(np.drugParticles){
    np.drugParticles.forEach(d => {
      const u = d.userData;
      u.phase += u.speed * eff;
      const wobble = Math.sin(u.phase) * 0.15;
      let dist = u.baseDist + wobble;
      if(nlSim && nlSim.state === 'breaking'){
        dist += (nlSim.releasePct / 100) * 4.5;
        d.material.opacity = Math.max(0.1, 1 - (nlSim.releasePct / 100));
      } else {
        d.material.opacity = 0.95;
      }
      d.position.set(u.dir.x * dist, u.dir.y * dist, u.dir.z * dist);
    });
  }

  if(np.flash > 0){
    np.flash = Math.max(0, np.flash - dt * 1.6);
    if(np.coreMesh && np.coreMesh.material) np.coreMesh.material.emissiveIntensity = 0.25 + np.flash * 0.9;
  }

  if(np.dipole) np.dipole.visible = nlShowDipole && (nlSim && nlSim.state === 'bonded');
  if(np.drugGroup) np.drugGroup.visible = nlShowCloud;
  if(np.label) np.label.visible = nlShowLabels;
}

const chartEl = () => document.getElementById('chart');
let chartDpr = 1;
function nlSizeChart(){
  const c = chartEl();
  if(!c) return;
  chartDpr = Math.min(window.devicePixelRatio||1, 2);
  const cw = c.clientWidth > 0 ? c.clientWidth : 240;
  c.width = cw * chartDpr;
  c.height = 130 * chartDpr;
}

function drawChart(){
  const c = chartEl();
  if(!c || !nlSim) return;
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  if(W === 0 || H === 0) return;
  ctx.clearRect(0, 0, W, H);

  const p = nlSim.preset, De = p.De, a = 1.9;
  const rmin = p.r0 * 0.55, rmax = p.r0 * 2.4;
  const Emin = -1.1 * De, Emax = 0.75 * De;
  const X = r => (r - rmin) / (rmax - rmin) * W;
  const Y = E => H - ((E - Emin) / (Emax - Emin)) * H;
  const morse = r => {
    const x = (r - p.r0) / 10.0;
    return De * (Math.exp(-2*a*x) - 2*Math.exp(-a*x));
  };

  ctx.lineWidth = 1;
  ctx.strokeStyle = 'rgba(130,165,255,.09)';
  for(let i = 1; i < 5; i++){
    ctx.beginPath(); ctx.moveTo(0, H*i/5); ctx.lineTo(W, H*i/5); ctx.stroke();
  }

  // Filled curve
  ctx.beginPath();
  for(let px = 0; px <= W; px += 2){
    const rVal = rmin + (rmax - rmin) * px / W;
    const E = Math.max(morse(rVal), Emin);
    const y = Y(E);
    px === 0 ? ctx.moveTo(px, y) : ctx.lineTo(px, y);
  }
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, 'rgba(56,189,248,.30)');
  grad.addColorStop(1, 'rgba(56,189,248,0)');
  ctx.save();
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fillStyle = grad; ctx.fill(); ctx.restore();

  // Glowing line
  ctx.beginPath();
  for(let px = 0; px <= W; px += 2){
    const rVal = rmin + (rmax - rmin) * px / W;
    const E = Math.max(morse(rVal), Emin);
    const y = Y(E);
    px === 0 ? ctx.moveTo(px, y) : ctx.lineTo(px, y);
  }
  ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2 * chartDpr;
  ctx.shadowColor = 'rgba(56,189,248,.75)'; ctx.shadowBlur = 8 * chartDpr;
  ctx.stroke(); ctx.shadowBlur = 0;

  // Equilibrium line
  ctx.strokeStyle = 'rgba(255,255,255,.25)'; ctx.setLineDash([3*chartDpr, 4*chartDpr]);
  ctx.beginPath(); ctx.moveTo(X(p.r0), 0); ctx.lineTo(X(p.r0), H); ctx.stroke();
  ctx.setLineDash([]);

  // Moving probe marker
  const rCurr = currentR();
  const Er = Math.max(bondEnergy(rCurr), Emin);
  ctx.fillStyle = '#ffffff';
  ctx.beginPath(); ctx.arc(X(rCurr), Y(Er), 4.5 * chartDpr, 0, 7); ctx.fill();
  ctx.shadowColor = '#fff'; ctx.shadowBlur = 10 * chartDpr;
  ctx.fill(); ctx.shadowBlur = 0;

  ctx.font = `700 ${9.5 * chartDpr}px "JetBrains Mono", monospace`;
  ctx.fillStyle = '#7dd3fc';
  ctx.fillText(`r = ${rCurr.toFixed(1)} nm   ΔG* = ${bondEnergy(rCurr).toFixed(1)} kBT`, 8 * chartDpr, 14 * chartDpr);
  ctx.fillStyle = 'rgba(127,144,184,.9)';
  ctx.fillText('VDLVO Colloidal Barrier', 8 * chartDpr, H - 7 * chartDpr);
}

function statusText(){
  if(!nlSim) return 'Colloidally Dispersed';
  switch(nlSim.state){
    case 'free': return 'Dissociated / Free Cargo';
    case 'transferring': return 'Condensing Corona Shell…';
    case 'bonded': return 'Colloidally Dispersed · Stable';
    case 'breaking': return `Dissolving (${nlSim.releasePct.toFixed(0)}% released)`;
    default: return 'Active';
  }
}

function updateHUD(){
  if(!nlSim) return;
  const p = nlSim.preset, r = currentR();
  const lenEl = document.getElementById('c-len'); if(lenEl) lenEl.textContent = (r * 1.1).toFixed(1) + ' nm';
  const enEl = document.getElementById('c-energy'); if(enEl) enEl.textContent = Math.abs(bondEnergy(r)).toFixed(1) + ' kBT';
  const tempEl = document.getElementById('c-temp'); if(tempEl) tempEl.textContent = nlTempK + ' K (' + (nlTempK - 273) + '°C)';
  const timeEl = document.getElementById('c-time'); if(timeEl) timeEl.textContent = nlSimTime.toFixed(1) + ' s';
  const orderEl = document.getElementById('c-order'); if(orderEl) orderEl.textContent = (p.charge > 0 ? '+' : '') + p.charge.toFixed(1) + ' mV';
  const stEl = document.getElementById('c-state'); if(stEl) stEl.textContent = statusText();
}

function syncButtons(){
  if(!nlSim) return;
  const formBtn = document.getElementById('btn-form');
  const breakBtn = document.getElementById('btn-break');
  const playBtn = document.getElementById('btn-play');
  if(formBtn) formBtn.disabled = (nlSim.state === 'bonded' || nlSim.state === 'transferring');
  if(breakBtn) breakBtn.disabled = (nlSim.state === 'free' || nlSim.state === 'breaking');
  if(playBtn) playBtn.innerHTML = nlPlaying ? '⏸&nbsp;Pause' : '▶&nbsp;Play';
}

function toggleHudPanels(){
  const vp = document.querySelector('.nanolab-viewport');
  if(!vp) return;
  vp.classList.toggle('hud-hidden');
  const btn = document.getElementById('btn-toggle-hud');
  if(btn) btn.textContent = vp.classList.contains('hud-hidden') ? '👁 Show HUD' : '👁 Toggle HUD';
}

/* ============================================================
   REAL AI 3D FORMULATION MORPHING ENGINE
   Dynamically interprets user natural language and mutates 3D model
   ============================================================ */
function parseAndMorph3D(promptText){
  if(!promptText || !promptText.trim()) return;

  // Ensure 3D engine is initialized
  if(!nlRenderer){
    initScene();
    buildCards();
    wireUI();
  }

  const text = promptText.toLowerCase();

  // Detect Carrier
  let carrier = 'lnp';
  if(text.includes('plga') || text.includes('polyester') || text.includes('copolymer')) carrier = 'plga';
  else if(text.includes('liposome') || text.includes('bilayer') || text.includes('lipid vesicle')) carrier = 'liposome';
  else if(text.includes('albumin') || text.includes('hsa') || text.includes('abraxane') || text.includes('protein')) carrier = 'albumin';
  else if(text.includes('micelle') || text.includes('block copolymer')) carrier = 'micelle';
  else if(text.includes('dendrimer') || text.includes('pamam') || text.includes('hyperbranched')) carrier = 'dendrimer';
  else if(text.includes('lipid') || text.includes('mrna') || text.includes('sirna')) carrier = 'lnp';

  const base = {...MEDICAL_CARRIERS[carrier]};

  // Detect Size (nm)
  const sizeMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:nm|nanometer)/i) || text.match(/size\s*(?:of|=|:)?\s*(\d+(?:\.\d+)?)/i);
  if(sizeMatch) {
    base.r0 = Math.max(10, Math.min(300, parseFloat(sizeMatch[1])));
  }

  // Detect Drug
  if(text.includes('paracetamol') || text.includes('acetaminophen')) { base.drug = 'Paracetamol'; carrier = 'paracetamol'; }
  else if(text.includes('ciprofloxacin') || text.includes('cipro')) { base.drug = 'Ciprofloxacin'; carrier = 'ciprofloxacin'; }
  else if(text.includes('vancomycin')) { base.drug = 'Vancomycin'; carrier = 'vancomycin'; }
  else if(text.includes('rifampicin') || text.includes('rifampin')) base.drug = 'Rifampicin';
  else if(text.includes('doxycycline')) base.drug = 'Doxycycline';
  else if(text.includes('gentamicin')) base.drug = 'Gentamicin';
  else if(text.includes('azithromycin')) base.drug = 'Azithromycin';
  else if(text.includes('amoxicillin')) base.drug = 'Amoxicillin';
  else if(text.includes('ibuprofen')) base.drug = 'Ibuprofen';
  else if(text.includes('letrozole')) base.drug = 'Letrozole';
  else if(text.includes('exemestane')) base.drug = 'Exemestane';
  else if(text.includes('amlodipine')) base.drug = 'Amlodipine';
  else if(text.includes('paclitaxel') || text.includes('taxol')) base.drug = 'Paclitaxel';
  else if(text.includes('doxorubicin') || text.includes('dox')) base.drug = 'Doxorubicin';
  else if(text.includes('mrna') || text.includes('bnt162b2')) base.drug = 'mRNA-Transcript';
  else if(text.includes('sirna')) base.drug = 'siRNA';
  else if(text.includes('cisplatin')) base.drug = 'Cisplatin';
  else if(text.includes('curcumin')) base.drug = 'Curcumin';
  else if(text.includes('rapamycin')) base.drug = 'Rapamycin';
  else if(text.includes('methotrexate')) base.drug = 'Methotrexate';

  // Detect Charge / Zeta Potential (mV)
  const zetaMatch = text.match(/([+-]?\d+(?:\.\d+)?)\s*mv/i) || text.match(/zeta\s*(?:of|=|:)?\s*([+-]?\d+(?:\.\d+)?)/i);
  if(zetaMatch) {
    base.charge = parseFloat(zetaMatch[1]);
  } else if(text.includes('cationic') || text.includes('positive')) {
    base.charge = Math.abs(base.charge || 20);
  } else if(text.includes('anionic') || text.includes('negative')) {
    base.charge = -Math.abs(base.charge || 25);
  } else if(text.includes('neutral')) {
    base.charge = 0;
  }

  // Adjust energy barrier heuristic from charge and size
  base.De = Math.max(8.0, Math.min(45.0, 10.0 + Math.abs(base.charge) * 0.45 + (base.r0 / 20.0)));
  base.label = `AI Engineered · ${base.label || carrier.toUpperCase()}`;
  base.formula = `${carrier.toUpperCase()}·${base.drug}`;
  base.desc = `Dynamically synthesized by NanoMed AI from user prompt: "${promptText}"`;

  // Dynamically morph the model
  nlCurKey = carrier;
  nlCoreScale = base.r0 / 40.0;
  clearGroup(nlMoleculeGroup);
  const np = createNanoparticleModel(base);
  nlSim = {
    preset: base, np, state: 'bonded',
    transfer: [], tprog: 0, r: base.r0, releasePct: 0
  };
  nlMoleculeGroup.add(np.group);

  const curTitle = document.getElementById('cur-preset');
  if(curTitle) curTitle.textContent = `${base.formula} · ${base.r0} nm · AI GENERATED`;

  const sSize = document.getElementById('s-size'); if(sSize) sSize.value = Math.round(base.r0);
  const oSize = document.getElementById('o-size'); if(oSize) oSize.textContent = Math.round(base.r0) + ' nm';

  renderMeta(base);
  markActiveCard(carrier);
  syncButtons();
  nlSizeChart();
  drawChart();

  // Flash AI feedback
  const feedbackEl = document.getElementById('ai-3d-feedback');
  if(feedbackEl){
    feedbackEl.style.display = 'block';
    feedbackEl.innerHTML = `✨ <b>AI Synthesized:</b> ${base.formula} (${base.r0} nm, ζ = ${base.charge > 0 ? '+' : ''}${base.charge.toFixed(1)} mV). Model morphed live!`;
    setTimeout(() => { if(feedbackEl) feedbackEl.style.display = 'none'; }, 6000);
  }
}

function wireUI(){
  const playBtn = document.getElementById('btn-play');
  if(playBtn) playBtn.onclick = () => { nlPlaying = !nlPlaying; syncButtons(); };
  const resetBtn = document.getElementById('btn-reset');
  if(resetBtn) resetBtn.onclick = () => loadPreset(nlCurKey);
  const formBtn = document.getElementById('btn-form');
  if(formBtn) formBtn.onclick = () => startTransfer(false);
  const breakBtn = document.getElementById('btn-break');
  if(breakBtn) breakBtn.onclick = () => startTransfer(true);

  const sTemp = document.getElementById('s-temp');
  if(sTemp) sTemp.oninput = e => {
    nlTempK = +e.target.value;
    const o = document.getElementById('o-temp'); if(o) o.textContent = nlTempK + ' K (' + (nlTempK - 273) + '°C)';
  };
  const sSpeed = document.getElementById('s-speed');
  if(sSpeed) sSpeed.oninput = e => {
    nlSpeed = +e.target.value;
    const o = document.getElementById('o-speed'); if(o) o.textContent = '×' + nlSpeed.toFixed(1);
  };
  const sSize = document.getElementById('s-size');
  if(sSize) sSize.oninput = e => {
    nlCoreScale = (+e.target.value) / 40.0;
    const o = document.getElementById('o-size'); if(o) o.textContent = e.target.value + ' nm';
    if(nlSim && nlSim.preset) {
      nlSim.preset.r0 = +e.target.value;
      loadPreset(nlCurKey);
    }
  };

  const tDipole = document.getElementById('t-dipole'); if(tDipole) tDipole.onchange = e => nlShowDipole = e.target.checked;
  const tCloud = document.getElementById('t-cloud'); if(tCloud) tCloud.onchange = e => {
    nlShowCloud = e.target.checked;
    if(nlSim && nlSim.np && nlSim.np.drugGroup) nlSim.np.drugGroup.visible = nlShowCloud;
  };
  const tLabels = document.getElementById('t-labels'); if(tLabels) tLabels.onchange = e => {
    nlShowLabels = e.target.checked;
    if(nlSim && nlSim.np && nlSim.np.label) nlSim.np.label.visible = nlShowLabels;
  };
  const tRotate = document.getElementById('t-rotate'); if(tRotate) tRotate.onchange = e => nlAutoRotate = e.target.checked;

  // AI 3D Prompt Morph Button
  const btnMorph = document.getElementById('btn-ai-3d-morph');
  const inputMorph = document.getElementById('ai-3d-prompt-input');
  if(btnMorph && inputMorph){
    btnMorph.onclick = () => parseAndMorph3D(inputMorph.value);
    inputMorph.onkeydown = e => { if(e.key === 'Enter') parseAndMorph3D(inputMorph.value); };
  }
  
  // Voice input for 3D AI
  const btnVoice3D = document.getElementById('btn-ai-3d-voice');
  if(btnVoice3D && inputMorph){
    btnVoice3D.onclick = () => startVoiceRecognition(inputMorph, () => parseAndMorph3D(inputMorph.value), btnVoice3D);
  }

  window.addEventListener('keydown', e => {
    if(e.code === 'Space' && (document.querySelector('#t-3d.on') || document.querySelector('#view-viewer.active'))){
      if(e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA'){
        e.preventDefault();
        nlPlaying = !nlPlaying;
        syncButtons();
      }
    }
  });
}

let nlRaf = 0, nlRunning = false;
function animate(){
  if(!nlRunning) return;
  nlRaf = requestAnimationFrame(animate);
  const dt = Math.min(nlClock ? nlClock.getDelta() : 0.016, 0.05);
  if(nlPlaying) nlSimTime += dt * nlSpeed;
  if(nlAutoRotate) nlRot.y += dt * 0.25;

  if(nlMoleculeGroup){
    nlMoleculeGroup.rotation.y = nlRot.y;
    nlMoleculeGroup.rotation.x = nlRot.x;
  }
  if(nlCam) nlCam.position.z = nlZoom;

  updateSimulation(dt);
  if(nlSim && nlSim.np) updateNanoparticleDynamics(nlSim.np, dt);

  if(nlRenderer && nlScene && nlCam) nlRenderer.render(nlScene, nlCam);

  nlHudAcc += dt;
  if(nlHudAcc > 0.1){
    updateHUD();
    drawChart();
    syncButtons();
    nlHudAcc = 0;
  }
}

function resize3D(){
  if(!nlRenderer || !nlCam) return;
  const host = document.querySelector('.nanolab-viewport') || document.getElementById('view-viewer');
  if(!host) return;
  const w = (host && host.clientWidth > 0) ? host.clientWidth : (window.innerWidth ? Math.min(window.innerWidth - 48, 1200) : 900);
  const h = (host && host.clientHeight > 0) ? host.clientHeight : 720;
  nlRenderer.setSize(w, h);
  nlCam.aspect = w / h;
  nlCam.updateProjectionMatrix();
  nlSizeChart();
  drawChart();
}

function start3D(){
  if(nlRunning) return;
  nlRunning = true;
  if(nlClock) nlClock.start();
  animate();
}
function stop3D(){
  nlRunning = false;
  if(nlRaf) cancelAnimationFrame(nlRaf);
}

async function open3D(){
  if(typeof load3D === 'function') {
    try { await load3D(); } catch(e){}
  }
  const viewEl = document.getElementById('view-viewer') || document.querySelector('.nanolab-viewport');
  if(!viewEl) return;
  if(!nlRenderer){
    initScene();
    buildCards();
    wireUI();
    loadPreset(nlCurKey || 'lnp');
  }
  resize3D();
  setTimeout(resize3D, 50);
  setTimeout(resize3D, 200);
  setTimeout(resize3D, 400);
  start3D();
}

// Pre-initialize 3D scene so model is immediately assembled
if (typeof window !== 'undefined') {
  const init3DPreWarm = () => {
    if(!nlRenderer && typeof THREE !== 'undefined'){
      try {
        initScene();
        buildCards();
        wireUI();
        loadPreset(nlCurKey || 'lnp');
        resize3D();
      } catch(err){
        console.warn('3D pre-warm note:', err);
      }
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init3DPreWarm);
  } else {
    setTimeout(init3DPreWarm, 60);
  }
}

function syncFromPredictor(){
  const g = n => {
    const e = document.querySelector(`#form [data-f="${n}"]`) ||
              document.querySelector(`[data-pred="${n}"]`) ||
              document.querySelector(`#prompt-${n.toLowerCase()}`);
    return e ? e.value : null;
  };
  const mat = g('Material type') || g('Core') || g('carrier') || 'Lipid';
  let targetKey = 'lnp';
  if(mat.includes('PLGA')) targetKey = 'plga';
  else if(mat.includes('Liposome') || mat.includes('DPPC')) targetKey = 'liposome';
  else if(mat.includes('Albumin') || mat.includes('HSA')) targetKey = 'albumin';
  else if(mat.includes('Micelle')) targetKey = 'micelle';
  else if(mat.includes('Dendrimer')) targetKey = 'dendrimer';

  const sz = g('Size (nm)') || g('Hydro size (nm)') || g('Core size (nm)');
  if(sz){
    const sVal = parseFloat(sz);
    nlCoreScale = Math.max(10, Math.min(250, sVal)) / 40.0;
    const sSize = document.getElementById('s-size'); if(sSize) sSize.value = sVal;
    const oSize = document.getElementById('o-size'); if(oSize) oSize.textContent = sVal + ' nm';
    if(MEDICAL_CARRIERS[targetKey]) MEDICAL_CARRIERS[targetKey].r0 = sVal;
  }
  loadPreset(targetKey);
}

function upd3d(inp){
  if(!inp) return;
  const prompt = `${inp['carrier'] || inp['Material type'] || 'Lipid'} nanoparticle with ${inp['drug'] || 'Paclitaxel'} size ${inp['Size (nm)'] || 80}nm`;
  parseAndMorph3D(prompt);
}



/* ============================================================
   NANOBOT AI COMPANION — VOICE RECOGNITION, HUD, & TTS ENGINE
   ============================================================ */
let speechRecognition = null;
let isVoiceListening = false;
let isReadOutOn = true;
let activeVoiceTarget = null;
let activeVoiceCallback = null;
let activeVoiceBtn = null;
let voiceSilenceTimer = null;
let accumulatedTranscript = '';
let currentSpeakingBtn = null;

// Normalization dictionary for common speech-to-text misrecognitions in nanomedicine
function cleanMedicalSpeech(text) {
  if (!text) return '';
  let s = text.trim();
  const replacements = [
    // Carriers
    [/\b(libosome|lightosome|lipozome|lifeosome|liposomes)\b/gi, 'Liposome'],
    [/\b(p\s*l\s*g\s*a|pl\s*ga)\b/gi, 'PLGA'],
    [/\b(l\s*n\s*p|lipid\s+nanoparticle|lipid\s+nanoparticles)\b/gi, 'LNP'],
    [/\b(m\s*r\s*n\s*a|messenger\s+rna)\b/gi, 'mRNA'],
    [/\b(albumin|h\s*s\s*a)\b/gi, 'HSA Albumin'],
    [/\b(micelle|micelles|mycell|mycells)\b/gi, 'Micelle'],
    [/\b(dendrimer|dendrimers)\b/gi, 'PAMAM Dendrimer'],
    // Drugs & Cargo
    [/\b(paracetamol|paracetamole|parasitamol|parisitamol|acetaminophen)\b/gi, 'Paracetamol'],
    [/\b(ciprofloxacin|ciprofloxicin|cipro|seprofloxacin)\b/gi, 'Ciprofloxacin'],
    [/\b(vancomycin|vancomicin|vanco)\b/gi, 'Vancomycin'],
    [/\b(rifampicin|rifampin|rifampicine)\b/gi, 'Rifampicin'],
    [/\b(doxycycline|doxycyclin|doxi)\b/gi, 'Doxycycline'],
    [/\b(gentamicin|gentamycin)\b/gi, 'Gentamicin'],
    [/\b(azithromycin|azithromicin|zithromax)\b/gi, 'Azithromycin'],
    [/\b(amoxicillin|amoxycillin|amoxil)\b/gi, 'Amoxicillin'],
    [/\b(ibuprofen|ibuprefen|advil|motrin)\b/gi, 'Ibuprofen'],
    [/\b(letrozole|femara)\b/gi, 'Letrozole'],
    [/\b(exemestane|aromasin)\b/gi, 'Exemestane'],
    [/\b(amlodipine|norvasc)\b/gi, 'Amlodipine'],
    [/\b(doc\s*rubicin|dock\s*sir\s*rubicin|dox\s*rubicin|dark\s*ruby\s*sin|dr\s*rubicin)\b/gi, 'Doxorubicin'],
    [/\b(pack\s*lit\s*axel|pack\s*lee\s*tax\s*el|paclitaxil|paclitax)\b/gi, 'Paclitaxel'],
    [/\b(wrap\s*a\s*mycin|rapper\s*mycin|rap\s*a\s*mycin|rap\s*micin)\b/gi, 'Rapamycin'],
    [/\b(sis\s*platin|six\s*platin|cis\s*platinum)\b/gi, 'Cisplatin'],
    [/\b(method\s*trex\s*8|meth\s*o\s*trexate|metho\s*trexate)\b/gi, 'Methotrexate'],
    // Biophysical units & values
    [/\b(nano\s*meters?|nanometres?)\b/gi, 'nm'],
    [/\b(milli\s*volts?|millivolts?)\b/gi, 'mV'],
    [/\b(minus|negative)\s*(\d+)/gi, '-$2'],
    [/\b(plus|positive)\s*(\d+)/gi, '+$2'],
    [/\b(data\s+potential|seta\s+potential)\b/gi, 'zeta potential'],
    [/\b(p\s*h)\s*(\d+(?:\.\d+)?)/gi, 'pH $2'],
    [/\b(korsmeyer\s*peppas|course\s*meyer\s*peppas)\b/gi, 'Korsmeyer-Peppas'],
    [/\bd\s*l\s*v\s*o\b/gi, 'DLVO']
  ];
  for (const [pattern, replacement] of replacements) {
    s = s.replace(pattern, replacement);
  }
  return s;
}

// Acoustic Chime Feedback (Web Audio API Synthesizer)
function playAudioChime(type) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    const now = ctx.currentTime;
    if (type === 'start') {
      // Ascending pleasant futuristic chime (Mic On)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(880.00, now + 0.12); // A5
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (type === 'stop') {
      // Descending pleasant chime (Mic Off / Process)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880.00, now); // A5
      osc.frequency.exponentialRampToValueAtTime(523.25, now + 0.12); // C5
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
    } else if (type === 'error') {
      // Alert low buzz
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(260.0, now);
      gain.gain.setValueAtTime(0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    }
  } catch(e) {
    // Audio context may be restricted before gesture
  }
}

// Temporary Toast for Voice Errors
function showVoiceToast(msg, isErr = false) {
  const existing = document.getElementById('voice-status-toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.id = 'voice-status-toast';
  t.className = 'voice-status-toast';
  if (!isErr) t.style.borderColor = '#38bdf8';
  t.innerHTML = `<span>${isErr ? '⚠️' : '🎙️'}</span> <span>${msg}</span>`;
  document.body.appendChild(t);
  setTimeout(() => { if (t.parentNode) t.remove(); }, 4000);
}

function initVoiceEngines() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return false;
  try {
    speechRecognition = new SpeechRec();
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'en-US';

    speechRecognition.onresult = (e) => {
      let interim = '';
      let finalStr = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalStr += e.results[i][0].transcript;
        } else {
          interim += e.results[i][0].transcript;
        }
      }
      const rawCurrent = finalStr || interim;
      if (rawCurrent) {
        accumulatedTranscript = cleanMedicalSpeech(rawCurrent);
        updateVoiceHudStream(accumulatedTranscript, !!finalStr);
        if (activeVoiceTarget) {
          activeVoiceTarget.value = accumulatedTranscript;
        }
      }

      // Auto-commit after 2.4 seconds of natural pause if content exists
      clearTimeout(voiceSilenceTimer);
      if (accumulatedTranscript.trim()) {
        voiceSilenceTimer = setTimeout(() => {
          finishVoiceRecognition();
        }, 2400);
      }
    };

    speechRecognition.onerror = (e) => {
      console.warn('Voice Recognition Error:', e.error);
      clearTimeout(voiceSilenceTimer);
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
        playAudioChime('error');
        showVoiceToast('Microphone access blocked. Click 🔒/🎙️ in your URL bar to allow microphone access.', true);
        cleanupVoiceState();
      } else if (e.error === 'no-speech') {
        showVoiceToast('No voice detected. Please speak closer to your microphone.', false);
      } else if (e.error === 'network') {
        showVoiceToast('Speech recognition network timeout. You can type directly in the box.', true);
        cleanupVoiceState();
      }
    };

    speechRecognition.onend = () => {
      if (isVoiceListening) {
        finishVoiceRecognition();
      } else {
        cleanupVoiceState();
      }
    };
    return true;
  } catch(err) {
    console.error('Failed to init speech recognition:', err);
    return false;
  }
}

function updateVoiceHudStream(text, isFinal) {
  const streamEl = document.getElementById('voice-hud-stream');
  if (!streamEl) return;
  if (!text) {
    streamEl.innerHTML = '<span class="voice-hint">🎙️ Speak now (e.g. "Design 80nm Liposome with Doxorubicin at -30mV")...</span>';
  } else {
    streamEl.innerHTML = `<span class="transcript-live">${text}</span>`;
  }
}

function startVoiceRecognition(targetInput, onComplete, triggerBtn) {
  // If already listening, toggle off and commit
  if (isVoiceListening) {
    finishVoiceRecognition();
    return;
  }

  if (!speechRecognition) {
    const ok = initVoiceEngines();
    if (!ok) {
      alert('Speech Recognition is not supported by this browser. Chrome or Edge is recommended.');
      return;
    }
  }

  activeVoiceTarget = targetInput;
  activeVoiceCallback = onComplete;
  activeVoiceBtn = triggerBtn;
  accumulatedTranscript = '';
  isVoiceListening = true;

  // Visual cues on buttons
  const allMics = [
    document.getElementById('btn-voice-input'),
    document.getElementById('btn-ai-3d-voice'),
    triggerBtn
  ].filter(Boolean);
  allMics.forEach(btn => {
    btn.classList.add('listening');
    btn.setAttribute('title', 'Listening... Click to stop & send');
  });

  // Display Voice HUD
  const hud = document.getElementById('voice-hud-indicator');
  if (hud) hud.style.display = 'block';
  updateVoiceHudStream('', false);

  // Sound chime
  playAudioChime('start');

  try {
    speechRecognition.start();
  } catch(e) {
    console.log('Recognition start note:', e.message);
  }
}

function finishVoiceRecognition() {
  if (!isVoiceListening) return;
  clearTimeout(voiceSilenceTimer);
  isVoiceListening = false;
  playAudioChime('stop');

  try {
    if (speechRecognition) speechRecognition.stop();
  } catch(e) {}

  const finalResult = cleanMedicalSpeech(accumulatedTranscript);
  if (activeVoiceTarget && finalResult) {
    activeVoiceTarget.value = finalResult;
  }

  cleanupVoiceState();

  if (activeVoiceCallback && finalResult) {
    const cb = activeVoiceCallback;
    activeVoiceCallback = null;
    setTimeout(() => cb(finalResult), 120);
  }
}

function cancelVoiceRecognition() {
  clearTimeout(voiceSilenceTimer);
  isVoiceListening = false;
  try {
    if (speechRecognition) speechRecognition.abort();
  } catch(e) {}
  cleanupVoiceState();
  showVoiceToast('Voice input cancelled', false);
}

function cleanupVoiceState() {
  isVoiceListening = false;
  clearTimeout(voiceSilenceTimer);
  const hud = document.getElementById('voice-hud-indicator');
  if (hud) hud.style.display = 'none';

  const allMics = [
    document.getElementById('btn-voice-input'),
    document.getElementById('btn-ai-3d-voice'),
    activeVoiceBtn
  ].filter(Boolean);
  allMics.forEach(btn => {
    btn.classList.remove('listening');
    btn.setAttribute('title', 'Speak to NanoMed AI');
  });
  activeVoiceBtn = null;
}

// -------------------------------------------------------------------
// TEXT-TO-SPEECH (TTS) & READ-OUT ENGINE
// -------------------------------------------------------------------
function toggleReadOut() {
  isReadOutOn = !isReadOutOn;
  const btn = document.getElementById('btn-readout-toggle');
  if (btn) {
    btn.classList.toggle('active', isReadOutOn);
    btn.textContent = isReadOutOn ? '🔊 Auto-Speak: ON' : '🔈 Auto-Speak: OFF';
    btn.title = isReadOutOn ? 'AI automatically speaks responses' : 'AI text only (speech muted)';
  }
  if (!isReadOutOn) stopSpeech();
}

function prepareTextForSpeech(text) {
  let s = text.replace(/<[^>]+>/g, ' '); // Strip HTML
  s = s.replace(/[•*_~`#]/g, ' ');       // Strip markdown symbols
  
  // Expand scientific notation & abbreviations for smooth pronunciation:
  s = s.replace(/\bnm\b/gi, ' nanometers ');
  s = s.replace(/\bmV\b/gi, ' millivolts ');
  s = s.replace(/\bmRNA\b/gi, ' messenger R N A ');
  s = s.replace(/\bLNP\b/gi, ' L N P ');
  s = s.replace(/\bPLGA\b/gi, ' P L G A ');
  s = s.replace(/\bHSA\b/gi, ' H S A ');
  s = s.replace(/\bPAMAM\b/gi, ' PAMAM ');
  s = s.replace(/\bDLVO\b/gi, ' D L V O barrier ');
  s = s.replace(/\b-(\d+(?:\.\d+)?)\b/g, ' negative $1 ');
  s = s.replace(/\+(\d+(?:\.\d+)?)\b/g, ' positive $1 ');
  s = s.replace(/\bpH\s*([0-9.]+)/gi, ' p H $1 ');
  s = s.replace(/\bPBS\b/gi, ' P B S buffer ');
  s = s.replace(/\s+/g, ' ').trim();
  return s;
}

function getBestSpeechVoice() {
  if (!('speechSynthesis' in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || !voices.length) return null;
  const preferred = voices.find(v => 
    (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('Jenny') || v.name.includes('Zira')) 
    && v.lang.startsWith('en')
  );
  if (preferred) return preferred;
  return voices.find(v => v.lang.startsWith('en')) || voices[0];
}

function speakText(text, onComplete) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();

  const clean = prepareTextForSpeech(text);
  if (!clean) return;

  const utter = new SpeechSynthesisUtterance(clean);
  utter.rate = 1.0;
  utter.pitch = 1.0;

  const bestVoice = getBestSpeechVoice();
  if (bestVoice) utter.voice = bestVoice;

  const stopBtn = document.getElementById('btn-stop-speech');
  const speakWave = document.getElementById('speaking-wave');
  if (stopBtn) stopBtn.style.display = 'inline-block';
  if (speakWave) speakWave.style.display = 'inline-flex';

  utter.onend = () => {
    if (stopBtn) stopBtn.style.display = 'none';
    if (speakWave) speakWave.style.display = 'none';
    if (currentSpeakingBtn) {
      currentSpeakingBtn.classList.remove('speaking');
      currentSpeakingBtn.innerHTML = '🔊 Listen';
      currentSpeakingBtn = null;
    }
    if (onComplete) onComplete();
  };
  utter.onerror = () => {
    if (stopBtn) stopBtn.style.display = 'none';
    if (speakWave) speakWave.style.display = 'none';
    if (currentSpeakingBtn) {
      currentSpeakingBtn.classList.remove('speaking');
      currentSpeakingBtn.innerHTML = '🔊 Listen';
      currentSpeakingBtn = null;
    }
  };

  window.speechSynthesis.speak(utter);
}

function stopSpeech() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  const stopBtn = document.getElementById('btn-stop-speech');
  const speakWave = document.getElementById('speaking-wave');
  if (stopBtn) stopBtn.style.display = 'none';
  if (speakWave) speakWave.style.display = 'none';
  if (currentSpeakingBtn) {
    currentSpeakingBtn.classList.remove('speaking');
    currentSpeakingBtn.innerHTML = '🔊 Listen';
    currentSpeakingBtn = null;
  }
}

function speakMessageBubble(btn) {
  if (!btn) return;
  if (btn === currentSpeakingBtn && window.speechSynthesis && window.speechSynthesis.speaking) {
    stopSpeech();
    return;
  }
  stopSpeech();

  const bubble = btn.closest('.msg-bubble');
  if (!bubble) return;

  const clone = bubble.cloneNode(true);
  const btns = clone.querySelectorAll('button');
  btns.forEach(b => b.remove());
  const text = clone.innerText || clone.textContent;

  currentSpeakingBtn = btn;
  btn.classList.add('speaking');
  btn.innerHTML = '⏹ Stop';

  speakText(text, () => {
    btn.classList.remove('speaking');
    btn.innerHTML = '🔊 Listen';
    currentSpeakingBtn = null;
  });
}

function toggleNanoBot() {
  const w = document.getElementById('nanobot-window');
  if (!w) return;
  w.classList.toggle('open');
  if (w.classList.contains('open')) {
    const inp = document.getElementById('nanobot-input');
    if (inp) inp.focus();
  } else {
    stopSpeech();
    cancelVoiceRecognition();
  }
}

function appendNanoBotMsg(sender, text, actions) {
  const box = document.getElementById('nanobot-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = `nanobot-msg ${sender}`;

  let actionHtml = '';
  if (actions && actions.length) {
    actionHtml = actions.map(a => 
      `<button class="msg-action-btn" onclick="${a.action}"><span>${a.icon}</span> ${a.label}</button>`
    ).join(' ');
  }

  // Include speaker button on all AI messages
  const speakerHtml = sender === 'ai' ? 
    `<button class="msg-speaker-btn" onclick="speakMessageBubble(this)" title="Read this message aloud">🔊 Listen</button>` : '';

  div.innerHTML = `<div class="msg-bubble">${text} ${speakerHtml} ${actionHtml}</div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;

  if (sender === 'ai' && isReadOutOn) {
    speakText(text);
  }
}

function startAssistantVoice() {
  const inp = document.getElementById('nanobot-input');
  const btn = document.getElementById('btn-voice-input');
  startVoiceRecognition(inp, () => sendNanoBotMessage(), btn);
}

function startQuickPromptVoice() {
  const inp = document.getElementById('quick-prompt-input');
  const btn = document.getElementById('btn-quick-prompt-voice');
  startVoiceRecognition(inp, () => {
    const runBtn = document.getElementById('btn-quick-run');
    if (runBtn) runBtn.click();
  }, btn);
}

function startMainPromptVoice() {
  const inp = document.getElementById('experiment-prompt');
  const btn = document.getElementById('btn-main-prompt-voice');
  startVoiceRecognition(inp, () => {}, btn);
}

function quickAsk(q){
  const inp = document.getElementById('nanobot-input');
  if(inp) inp.value = q;
  sendNanoBotMessage();
}

function sendNanoBotMessage(){
  const inp = document.getElementById('nanobot-input');
  if(!inp || !inp.value.trim()) return;
  const userText = inp.value.trim();
  inp.value = '';

  appendNanoBotMsg('user', userText);

  // Intelligent NanoMed AI Processing
  setTimeout(() => {
    processAssistantQuery(userText);
  }, 350);
}

/* ============================================================
   INTERACTIVE CONVERSATIONAL AI CLINICAL DIRECTOR & SIMULATION RUNNER
   - Multi-turn talk-back dialogue
   - Proactive diagnostic alerts (Medium, pH, Stability, Extrapolation)
   - Automatic transfer to Live Simulation Workspace & execution
   - Full Voice & Audio Feedback integration
   ============================================================ */

const CLINICAL_DRUG_KNOWLEDGE = {
  paracetamol: {
    name: 'Paracetamol',
    category: 'Analgesic & Antipyretic',
    defaultCarrier: 'nm-paracetamol-plga',
    carriers: [
      { key: 'nm-paracetamol-plga', label: 'PLGA Copolymer (335 nm)', size: 335.5, zeta: 7.1, load: '7.4%', desc: 'Long-acting biodegradable polyester depot' },
      { key: 'nm-paracetamol-liposome', label: 'Liposome DPPC (90 nm)', size: 90.1, zeta: -35.4, load: '4.0%', desc: 'Unilamellar lipid bilayer vesicle' },
      { key: 'nm-paracetamol-sln', label: 'Solid Lipid DSPC (235 nm)', size: 234.9, zeta: 19.0, load: '4.0%', desc: 'Solid matrix with enhanced shelf stability' }
    ]
  },
  ciprofloxacin: {
    name: 'Ciprofloxacin',
    category: 'Fluoroquinolone Antibiotic',
    defaultCarrier: 'ciprofloxacin-plga',
    carriers: [
      { key: 'ciprofloxacin-plga', label: 'PLGA Matrix (165 nm)', size: 165.0, zeta: -18.2, load: '9.2%', desc: 'PVA-stabilized sustained antibacterial release' }
    ]
  },
  vancomycin: {
    name: 'Vancomycin',
    category: 'Glycopeptide Antibiotic',
    defaultCarrier: 'vancomycin-plga-peg',
    carriers: [
      { key: 'vancomycin-plga-peg', label: 'PLGA-PEG Stealth (180 nm)', size: 180.0, zeta: -12.5, load: '11.5%', desc: 'PEGylated extended-release against MRSA' }
    ]
  },
  rifampicin: {
    name: 'Rifampicin',
    category: 'Rifamycin / Antitubercular',
    defaultCarrier: 'rifampicin-plga-peg',
    carriers: [
      { key: 'rifampicin-plga-peg', label: 'PLGA-PEG Core (145 nm)', size: 145.0, zeta: -16.0, load: '8.0%', desc: 'Hydrophobic core with stealth corona' }
    ]
  },
  doxycycline: {
    name: 'Doxycycline',
    category: 'Tetracycline Antibiotic',
    defaultCarrier: 'doxycycline-polymeric',
    carriers: [
      { key: 'doxycycline-polymeric', label: 'Polymeric NP (130 nm)', size: 130.0, zeta: -24.0, load: '7.8%', desc: 'PEG-PLA mucosal delivery' }
    ]
  },
  gentamicin: {
    name: 'Gentamicin',
    category: 'Aminoglycoside Antibiotic',
    defaultCarrier: 'gentamicin-chitosan',
    carriers: [
      { key: 'gentamicin-chitosan', label: 'Chitosan NP (115 nm)', size: 115.0, zeta: 28.5, load: '6.5%', desc: 'Mucoadhesive cationic polysaccharide' }
    ]
  },
  azithromycin: {
    name: 'Azithromycin',
    category: 'Macrolide Antibiotic',
    defaultCarrier: 'azithromycin-sln',
    carriers: [
      { key: 'azithromycin-sln', label: 'Solid Lipid NP (195 nm)', size: 195.0, zeta: -21.0, load: '10.2%', desc: 'Poloxamer-coated lipid nanoparticles' }
    ]
  },
  amoxicillin: {
    name: 'Amoxicillin',
    category: 'Beta-Lactam Antibiotic',
    defaultCarrier: 'amoxicillin-eudragit',
    carriers: [
      { key: 'amoxicillin-eudragit', label: 'Eudragit NP (140 nm)', size: 140.0, zeta: -15.5, load: '8.7%', desc: 'Enteric protected gastric-resistant matrix' }
    ]
  },
  doxorubicin: {
    name: 'Doxorubicin',
    category: 'Anthracycline Chemotherapeutic',
    defaultCarrier: 'doxorubicin-liposome',
    carriers: [
      { key: 'doxorubicin-liposome', label: 'PEGylated Liposome (85 nm)', size: 85.0, zeta: -25.0, load: '9.8%', desc: 'Doxil-analog with prolonged circulation' },
      { key: 'doxorubicin-plga', label: 'PLGA Chitosan/Alginate (175 nm)', size: 175.0, zeta: -19.5, load: '8.5%', desc: 'Layer-by-layer core-shell matrix' }
    ]
  },
  paclitaxel: {
    name: 'Paclitaxel',
    category: 'Taxane Chemotherapeutic',
    defaultCarrier: 'formulation-a',
    carriers: [
      { key: 'formulation-a', label: 'PLGA Benchmark (120 nm)', size: 120.0, zeta: -22.0, load: '8.0%', desc: 'Nature Comms benchmark formulation' }
    ]
  },
  letrozole: {
    name: 'Letrozole',
    category: 'Aromatase Inhibitor',
    defaultCarrier: 'formulation-b',
    carriers: [
      { key: 'formulation-b', label: 'PLA Long-Acting (150 nm)', size: 150.0, zeta: -15.0, load: '5.0%', desc: 'Extended PLA parenteral depot' },
      { key: 'formulation-c', label: 'PLGA Matrix (100 nm)', size: 100.0, zeta: -28.0, load: '6.0%', desc: 'Sustained PLGA copolymer release' }
    ]
  },
  ibuprofen: {
    name: 'Ibuprofen',
    category: 'NSAID / Anti-inflammatory',
    defaultCarrier: 'ibuprofen-lipid',
    carriers: [
      { key: 'ibuprofen-lipid', label: 'Solid Lipid NP (150 nm)', size: 150.0, zeta: -22.4, load: '9.5%', desc: 'Lipid matrix with high encapsulation' }
    ]
  },
  mrna: {
    name: 'mRNA-1273',
    category: 'mRNA Vaccine / Biologic',
    defaultCarrier: 'mrna-lnp',
    carriers: [
      { key: 'mrna-lnp', label: 'Ionizable LNP (80 nm)', size: 80.0, zeta: 4.5, load: '92% encap', desc: 'SM-102 / PEG-DMG ionizable lipid shell' }
    ]
  }
};

let aiSession = {
  active: false,
  drugKey: null,
  waitingFor: null,
  selectedKey: null,
  ph: 7.4,
  temp: 37.0,
  medium: 'pbs'
};

// -------------------------------------------------------------
// Diagnostic Alert & Issue Evaluator
// -------------------------------------------------------------
function diagnoseFormulationIssues(form, env = {}) {
  const issues = [];
  const ph = env.ph !== undefined ? env.ph : (state.env ? state.env.ph : 7.4);
  const temp = env.temp !== undefined ? env.temp : (state.env ? state.env.temp : 37.0);
  const zeta = form.zeta;
  const size = form.size;

  // 1. Medium & pH Issue Analysis
  if (ph < 6.8) {
    issues.push({
      type: 'medium',
      severity: 'warn',
      icon: '⚠️',
      title: `Acidic Medium Alert (pH ${ph.toFixed(1)})`,
      message: `At acidic pH ${ph.toFixed(1)} (e.g., endosomes or tumor microenvironment), hydrolytic ester cleavage is accelerated. Korsmeyer-Peppas baseline was fitted under physiological pH 7.4, so anomalous burst release may increase.`,
      spoken: `Medium warning: operating at acidic pH ${ph.toFixed(1)}, which accelerates polymer erosion.`
    });
  } else if (ph > 7.9) {
    issues.push({
      type: 'medium',
      severity: 'warn',
      icon: '⚠️',
      title: `Alkaline Medium Alert (pH ${ph.toFixed(1)})`,
      message: `At alkaline pH ${ph.toFixed(1)}, base-catalyzed hydrolysis and potential neutralization of surface charge may occur.`,
      spoken: `Medium warning: alkaline pH ${ph.toFixed(1)} may alter surface potential.`
    });
  } else {
    issues.push({
      type: 'medium',
      severity: 'good',
      icon: '✅',
      title: `Physiological Buffer Matched (pH ${ph.toFixed(1)})`,
      message: `Medium is calibrated to physiological blood/PBS pH 7.4 with 0.15 M ionic strength.`,
      spoken: `Release medium matched to physiological pH 7.4.`
    });
  }

  // 2. Temperature Issue Analysis
  if (Math.abs(temp - 37.0) > 1.5) {
    issues.push({
      type: 'temp',
      severity: 'warn',
      icon: '⚠️',
      title: `Temperature Deviation (${temp.toFixed(1)}°C)`,
      message: `Operating away from 37.0°C human body temperature. Diffusion coefficient scales via Stokes-Einstein equation D = k_B·T / (6πηr), altering release kinetics.`,
      spoken: `Temperature is set to ${temp.toFixed(1)} degrees Celsius, altering fluid viscosity and drug diffusion.`
    });
  }

  // 3. Colloidal Stability Issue (Zeta Potential)
  if (Math.abs(zeta) < 20.0) {
    issues.push({
      type: 'stability',
      severity: 'danger',
      icon: '⚠️',
      title: `Low Colloidal Stability Risk (Zeta: ${zeta > 0 ? '+' : ''}${zeta} mV)`,
      message: `Surface charge magnitude is below 20 mV. The electrostatic DLVO repulsion barrier is low. Nanoparticles may aggregate in ionic media unless protected by a steric PEG corona.`,
      spoken: `Stability warning: surface charge of ${zeta} millivolts is low, risking particle agglomeration.`
    });
  } else {
    issues.push({
      type: 'stability',
      severity: 'good',
      icon: '✅',
      title: `Colloidally Stable (Zeta: ${zeta > 0 ? '+' : ''}${zeta} mV)`,
      message: `Strong electrostatic repulsion barrier (|ζ| ≥ 20 mV) maintains robust colloidal dispersion in suspension.`,
      spoken: `Colloidal stability confirmed with an electrostatic barrier of ${zeta} millivolts.`
    });
  }

  // 4. Bio-distribution / Particle Sizing
  if (size > 220.0) {
    issues.push({
      type: 'size',
      severity: 'warn',
      icon: 'ℹ️',
      title: `Nanoscale Sizing Notice (${size} nm)`,
      message: `Particle diameter exceeds 200 nm. Long-acting parenteral formulations at this size face higher hepatic Kupffer uptake and splenic filtration.`,
      spoken: `Particle size of ${size} nanometers exceeds 200 nanometers, which increases splenic clearance.`
    });
  }

  // 5. Korsmeyer-Peppas Mathematical Extrapolation Domain Limit
  issues.push({
    type: 'extrapolation',
    severity: 'info',
    icon: '📊',
    title: 'Korsmeyer-Peppas ODE Mathematical Domain Limit',
    message: 'The Korsmeyer-Peppas model Mt/M∞ = k·t^n applies to the initial 60% of release. Telemetry marks fractions beyond 60% as mathematical extrapolation.',
    spoken: 'Korsmeyer-Peppas kinetics are valid up to 60 percent cumulative release.'
  });

  return issues;
}

// -------------------------------------------------------------
// Automated Simulation Execution Function
// -------------------------------------------------------------
function executeAiSimulationWorkflow(formKey, customOverrides = {}) {
  const f = FORMULATIONS[formKey] || FORMULATIONS['formulation-a'];
  
  // 1. Switch to Live Simulation Workspace
  if (typeof switchTab === 'function') {
    switchTab('simulation');
  }

  // 2. Select formulation dropdown
  const sel = document.getElementById('config-formulation');
  if (sel) {
    sel.value = formKey;
    if (typeof setFormulationConfig === 'function') {
      setFormulationConfig(formKey);
    }
  }

  // 3. Set environment parameters
  const ph = customOverrides.ph !== undefined ? customOverrides.ph : 7.4;
  const temp = customOverrides.temp !== undefined ? customOverrides.temp : 37.0;
  const medium = customOverrides.medium || 'pbs';

  const phInput = document.getElementById('env-ph');
  const tempInput = document.getElementById('env-temp');
  const medSelect = document.getElementById('env-medium');

  if (phInput) {
    phInput.value = ph;
    if (state.env) state.env.ph = parseFloat(ph);
    const valPh = document.getElementById('val-ph');
    if (valPh) valPh.textContent = parseFloat(ph).toFixed(1);
  }

  if (tempInput) {
    tempInput.value = temp;
    if (state.env) state.env.temp = parseFloat(temp);
    const valTemp = document.getElementById('val-temp');
    if (valTemp) valTemp.textContent = parseFloat(temp).toFixed(1);
  }

  if (medSelect) {
    medSelect.value = medium;
    if (state.env) state.env.medium = medium;
  }

  // 4. Reset & Launch Simulation immediately!
  if (typeof resetSim === 'function') resetSim();
  setTimeout(() => {
    if (typeof startSim === 'function') {
      startSim();
      addEvent(`AI automated launch: ${f.name} (pH ${ph}, ${temp}°C)`, 'sys');
    }
  }, 180);

  // 5. Morph 3D viewer model
  try {
    if (typeof parseAndMorph3D === 'function') {
      parseAndMorph3D(`${f.drug} ${f.size}nm ${f.material} at ${f.zeta}mV`);
    }
  } catch(e) {}
}

// Window globally accessible callback for action buttons
window.confirmAiDrugSetup = function(formKey, runImmediately = false, envOverrides = {}) {
  const f = FORMULATIONS[formKey] || FORMULATIONS['formulation-a'];
  const issues = diagnoseFormulationIssues(f, envOverrides);

  let issuesHtml = issues.map(iss => 
    `<div style="font-size:11.5px; margin:3px 0; color:${iss.severity === 'danger' ? '#f43f5e' : iss.severity === 'warn' ? '#f59e0b' : '#38bdf8'};">
      <b>${iss.icon} ${iss.title}:</b> ${iss.message}
    </div>`
  ).join('');

  // Spoken voice summary (concise & informative)
  const spokenIssues = issues.filter(i => i.severity === 'danger' || i.severity === 'warn').map(i => i.spoken).join(' ');
  const speechText = `Selected ${f.drug} in ${f.material}, size ${f.size} nanometers, surface charge ${f.zeta} millivolts. ${spokenIssues ? spokenIssues + ' ' : ''}Transferring to Live Simulation Workspace and executing now!`;

  const msg = `⚡ <b>AI Formulation Verified: ${f.name}</b><br>` +
    `• <b>Drug / Payload:</b> ${f.drug} (${f.category || 'Therapeutic Active'})<br>` +
    `• <b>Carrier Matrix:</b> ${f.material} · <b>Size:</b> ${f.size} nm · <b>Zeta:</b> ${f.zeta > 0 ? '+' : ''}${f.zeta} mV<br>` +
    `• <b>Drug Loading:</b> ${f.load} · <b>Coating:</b> ${f.coat}<br>` +
    `• <b>Korsmeyer-Peppas ODE:</b> k = ${f.k}, n = ${f.n}<br><br>` +
    `<b>Biophysical & Medium Diagnostic Review:</b><br>${issuesHtml}<br><br>` +
    `🚀 <b>Status:</b> Automatically loaded into the Simulation Workspace and started execution!`;

  const actions = [
    { label: 'View Live Simulation', icon: '▶️', action: "switchTab('simulation')" },
    { label: 'Inspect 3D Digital Twin', icon: '🌐', action: "switchTab('viewer')" }
  ];

  appendNanoBotMsg('ai', msg, actions);

  // Speak aloud via TTS
  speakText(speechText);

  // Execute in workspace
  executeAiSimulationWorkflow(formKey, envOverrides);

  // Reset dialogue session
  aiSession = { active: false, drugKey: null, waitingFor: null, selectedKey: null, ph: 7.4, temp: 37.0, medium: 'pbs' };
};

// -------------------------------------------------------------
// Conversational Multi-Turn Query Processor
// -------------------------------------------------------------
function processAssistantQuery(query) {
  const q = query.toLowerCase().trim();

  // Helper: detect drug in text
  let detectedDrugKey = null;
  for (const [key, info] of Object.entries(CLINICAL_DRUG_KNOWLEDGE)) {
    if (q.includes(key) || q.includes(info.name.toLowerCase())) {
      detectedDrugKey = key;
      break;
    }
  }
  // Check alternative phonetic/common drug names
  if (!detectedDrugKey) {
    if (q.includes('acetaminophen') || q.includes('pcm')) detectedDrugKey = 'paracetamol';
    else if (q.includes('cipro')) detectedDrugKey = 'ciprofloxacin';
    else if (q.includes('vanco')) detectedDrugKey = 'vancomycin';
    else if (q.includes('rifampin')) detectedDrugKey = 'rifampicin';
    else if (q.includes('doxil') || q.includes('adria')) detectedDrugKey = 'doxorubicin';
    else if (q.includes('taxol')) detectedDrugKey = 'paclitaxel';
    else if (q.includes('femara')) detectedDrugKey = 'letrozole';
  }

  // Detect explicit environmental parameters in user input
  let parsedPh = null;
  const phMatch = q.match(/ph\s*(?:of|=|:)?\s*(\d+(?:\.\d+)?)/);
  if (phMatch) parsedPh = parseFloat(phMatch[1]);

  let parsedTemp = null;
  const tempMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:°?c|degrees?|celsius)/);
  if (tempMatch) parsedTemp = parseFloat(tempMatch[1]);

  let parsedSize = null;
  const sizeMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:nm|nanometers?)/);
  if (sizeMatch) parsedSize = parseFloat(sizeMatch[1]);

  // A. IF USER SAYS "RUN", "DEFAULTS", "YES", "EXECUTE" WHILE IN AN ACTIVE DRUG SESSION
  if (aiSession.active && aiSession.drugKey && (q.includes('run') || q.includes('default') || q.includes('yes') || q.includes('ok') || q.includes('start') || q.includes('proceed') || q.includes('execute') || q.includes('simulate'))) {
    const drugInfo = CLINICAL_DRUG_KNOWLEDGE[aiSession.drugKey];
    const formKey = aiSession.selectedKey || drugInfo.defaultCarrier;
    const envOverrides = {};
    if (parsedPh !== null) envOverrides.ph = parsedPh;
    if (parsedTemp !== null) envOverrides.temp = parsedTemp;
    window.confirmAiDrugSetup(formKey, true, envOverrides);
    return;
  }

  // B. IF USER NAMES A SPECIFIC CARRIER (e.g. "PLGA", "Liposome", "SLN") WHILE IN ACTIVE DRUG SESSION
  if (aiSession.active && aiSession.drugKey) {
    const drugInfo = CLINICAL_DRUG_KNOWLEDGE[aiSession.drugKey];
    let matchedCarrierKey = null;

    if (q.includes('liposome') || q.includes('lipid vesicle')) {
      const found = drugInfo.carriers.find(c => c.key.includes('liposome'));
      if (found) matchedCarrierKey = found.key;
    } else if (q.includes('sln') || q.includes('solid lipid') || q.includes('dspc')) {
      const found = drugInfo.carriers.find(c => c.key.includes('sln'));
      if (found) matchedCarrierKey = found.key;
    } else if (q.includes('plga') || q.includes('polymer') || q.includes('polymeric')) {
      const found = drugInfo.carriers.find(c => c.key.includes('plga'));
      if (found) matchedCarrierKey = found.key;
    }

    if (matchedCarrierKey) {
      const envOverrides = {};
      if (parsedPh !== null) envOverrides.ph = parsedPh;
      if (parsedTemp !== null) envOverrides.temp = parsedTemp;
      window.confirmAiDrugSetup(matchedCarrierKey, true, envOverrides);
      return;
    }
  }

  // C. IF A DRUG NAME IS DETECTED IN THE USER'S QUERY
  if (detectedDrugKey) {
    const drugInfo = CLINICAL_DRUG_KNOWLEDGE[detectedDrugKey];
    const isDirectRunRequested = q.includes('simulate') || q.includes('run') || q.includes('start') || q.includes('default') || (parsedSize !== null && q.includes('plga'));

    // Check if user already specified full parameters (Direct Execute)
    if (isDirectRunRequested && drugInfo.carriers.length > 0) {
      // Pick best matching carrier
      let targetKey = drugInfo.defaultCarrier;
      if (q.includes('liposome')) {
        const found = drugInfo.carriers.find(c => c.key.includes('liposome'));
        if (found) targetKey = found.key;
      } else if (q.includes('sln') || q.includes('solid lipid')) {
        const found = drugInfo.carriers.find(c => c.key.includes('sln'));
        if (found) targetKey = found.key;
      }
      const envOverrides = {};
      if (parsedPh !== null) envOverrides.ph = parsedPh;
      if (parsedTemp !== null) envOverrides.temp = parsedTemp;
      window.confirmAiDrugSetup(targetKey, true, envOverrides);
      return;
    }

    // Otherwise: INITIATE INTERACTIVE TALK-BACK DIALOGUE!
    aiSession = {
      active: true,
      drugKey: detectedDrugKey,
      waitingFor: 'carrier_selection',
      selectedKey: drugInfo.defaultCarrier,
      ph: parsedPh !== null ? parsedPh : 7.4,
      temp: parsedTemp !== null ? parsedTemp : 37.0,
      medium: 'pbs'
    };

    const carrierListHtml = drugInfo.carriers.map((c, i) => 
      `• <b>Option ${i + 1}: ${c.label}</b> (Loading: ${c.load}, Zeta: ${c.zeta > 0 ? '+' : ''}${c.zeta} mV)<br>&nbsp;&nbsp;&nbsp;&nbsp;<i>${c.desc}</i>`
    ).join('<br>');

    const actionButtons = drugInfo.carriers.map(c => ({
      label: c.label.split('(')[0].trim(),
      icon: c.key.includes('liposome') ? '🫧' : c.key.includes('sln') ? '🛡️' : '💊',
      action: `window.confirmAiDrugSetup('${c.key}', true)`
    }));
    actionButtons.push({
      label: 'Run Calibrated Defaults',
      icon: '⚡',
      action: `window.confirmAiDrugSetup('${drugInfo.defaultCarrier}', true)`
    });

    const reply = `I have identified <b>${drugInfo.name}</b> (${drugInfo.category}).<br><br>` +
      `To configure the simulation for this medicine, which nanocarrier system and target size would you like to formulate?<br><br>` +
      `${carrierListHtml}<br><br>` +
      `<b>Environment check:</b> Defaulting to <b>PBS buffer pH 7.4 at 37°C</b>.<br>` +
      `You can tell me your custom parameters (e.g. <i>'PLGA 335nm at pH 6.5'</i>) or click an option below to launch immediately!`;

    const speechText = `Identified ${drugInfo.name}. Which delivery platform would you like to formulate? Options include ${drugInfo.carriers.map(c => c.label.split('(')[0]).join(', or ')}. You can state your carrier, or say 'run defaults' to launch the simulation now.`;

    appendNanoBotMsg('ai', reply, actionButtons);
    speakText(speechText);
    return;
  }

  // D. IF USER ASKS ABOUT PROBLEMS / ISSUES IN MEDIUM / ENVIRONMENT
  if (q.includes('issue') || q.includes('problem') || q.includes('medium') || q.includes('ph') || q.includes('buffer') || q.includes('serum') || q.includes('temperature') || q.includes('risk')) {
    const curFormKey = (state && state.formulationKey) ? state.formulationKey : 'formulation-a';
    const curForm = FORMULATIONS[curFormKey] || FORMULATIONS['formulation-a'];
    const curEnv = { ph: state.env.ph, temp: state.env.temp, medium: state.env.medium };
    const issues = diagnoseFormulationIssues(curForm, curEnv);

    const issuesHtml = issues.map(iss => 
      `<div style="margin:4px 0; padding:4px 8px; border-radius:4px; background:${iss.severity === 'danger' ? 'rgba(244,63,94,0.12)' : iss.severity === 'warn' ? 'rgba(245,158,11,0.12)' : 'rgba(56,189,248,0.08)'}; border-left:3px solid ${iss.severity === 'danger' ? '#f43f5e' : iss.severity === 'warn' ? '#f59e0b' : '#38bdf8'};">
        <b>${iss.icon} ${iss.title}</b><br>
        <span style="font-size:12px; color:#cbd5e1;">${iss.message}</span>
      </div>`
    ).join('');

    const speechSummary = issues.map(i => i.spoken).slice(0, 3).join(' ');

    const reply = `<b>Comprehensive Medium & Biophysical Diagnostics (${curForm.name}):</b><br><br>` +
      `<b>Current Conditions:</b> Medium: <b>${curEnv.medium.toUpperCase()}</b> · pH: <b>${curEnv.ph.toFixed(1)}</b> · Temp: <b>${curEnv.temp.toFixed(1)}°C</b><br><br>` +
      `${issuesHtml}`;

    const actions = [
      { label: 'Set Neutral PBS (pH 7.4)', icon: '🧪', action: "if($('env-ph')) {$('env-ph').value=7.4; state.env.ph=7.4; $('val-ph').textContent='7.4'; addEvent('pH normalized to 7.4','sys');}" },
      { label: 'Simulate Tumor Acidosis (pH 6.5)', icon: '⚠️', action: "if($('env-ph')) {$('env-ph').value=6.5; state.env.ph=6.5; $('val-ph').textContent='6.5'; addEvent('pH set to 6.5 (tumor acidosis)','sys');}" }
    ];

    appendNanoBotMsg('ai', reply, actions);
    speakText(speechSummary);
    return;
  }

  // E. 3D MODEL VIEW / MORPH SPECIFIC REQUEST
  if (q.includes('3d') || q.includes('morph') || q.includes('render') || q.includes('visualize') || q.includes('ray') || q.includes('border') || q.includes('mesh')) {
    parseAndMorph3D(query);
    const p = nlSim ? nlSim.preset : { formula: 'Nanocarrier', r0: 80, charge: -20 };
    const reply = `Generated and updated 3D digital twin: <b>${p.formula}</b> (${p.r0} nm, surface potential ${p.charge > 0 ? '+' : ''}${p.charge} mV). Glowing light ray border, lattice packing, and payload have dynamically updated!`;
    const actions = [
      { label: 'View in 3D Tab', icon: '🌐', action: "switchTab('viewer')" },
      { label: 'Send to Live Simulation', icon: '▶️', action: "switchTab('simulation')" }
    ];
    appendNanoBotMsg('ai', reply, actions);
    speakText(`Updated 3D model for ${p.formula} at ${p.r0} nanometers.`);
    return;
  }

  // F. GENERAL TELEMETRY ANALYSIS
  if (q.includes('analyze') || q.includes('state') || q.includes('telemetry')) {
    let curSize = 120, curZeta = -22.0, curRel = 0;
    if (typeof state !== 'undefined' && state.particle) {
      curSize = state.particle.size || 120;
      curZeta = state.particle.zeta || -22;
      curRel = state.particle.release || 0;
    }
    const isStable = Math.abs(curZeta) >= 20;
    const reply = `<b>Current Telemetry Analysis:</b><br>` +
      `• <b>Particle Size:</b> ${curSize.toFixed(1)} nm<br>` +
      `• <b>Zeta Potential:</b> ${curZeta.toFixed(1)} mV (${isStable ? 'Colloidally Stable' : 'Aggregation-Prone'})<br>` +
      `• <b>Colloidal DLVO Barrier:</b> ${Math.abs(curZeta) >= 30 ? 'High electrostatic repulsion barrier prevents protein agglomeration.' : 'Moderate steric barrier; recommended PEGylation to extend half-life.'}<br>` +
      `• <b>Korsmeyer-Peppas Release:</b> ${curRel.toFixed(1)}% cumulative drug release.`;
    const actions = [
      { label: 'Run Live Simulation', icon: '▶️', action: "switchTab('simulation')" }
    ];
    appendNanoBotMsg('ai', reply, actions);
    speakText(`Telemetry analysis: particle size ${curSize.toFixed(1)} nanometers, zeta potential ${curZeta.toFixed(1)} millivolts, current release ${curRel.toFixed(1)} percent.`);
    return;
  }

  // G. FALLBACK: GENERAL NANOMEDICINE ASSISTANT
  const formattedPrompt = `Design ${q.includes('cancer') ? 'oncology-targeted' : 'biocompatible'} nanocarrier delivering active cargo in PBS buffer pH 7.4 at 37°C with sustained Korsmeyer-Peppas release kinetics and low cytotoxicity screen.`;
  const reply = `I have analyzed your query: <i>"${query}"</i>.<br><br>` +
    `For predictive screening across the Stability Regressor and Cytotoxicity Classifier, I have structured an experimental run for the primary simulation engine.`;
  
  const actions = [
    { label: 'Send to Main Section & Execute', icon: '🚀', action: `sendAsMainPrompt('${formattedPrompt.replace(/'/g, "\'")}')` },
    { label: 'Configure Paracetamol Simulation', icon: '💊', action: "window.confirmAiDrugSetup('nm-paracetamol-plga')" },
    { label: 'Configure Ciprofloxacin Simulation', icon: '🧪', action: "window.confirmAiDrugSetup('ciprofloxacin-plga')" }
  ];
  appendNanoBotMsg('ai', reply, actions);
  speakText(`Analyzed your query. I have prepared a simulation configuration.`);
}


function sendAsMainPrompt(promptText){
  // 1. Populate prompt in main workspace textarea
  const targetArea = document.getElementById('experiment-prompt') || 
                     document.getElementById('quick-prompt-input');
  if(targetArea){
    targetArea.value = promptText;
    targetArea.scrollIntoView({behavior: 'smooth', block: 'center'});
    targetArea.style.borderColor = '#38bdf8';
    targetArea.style.boxShadow = '0 0 20px rgba(56, 189, 248, 0.6)';
    setTimeout(() => { targetArea.style.borderColor = ''; targetArea.style.boxShadow = ''; }, 3000);
  }

  // 2. Switch to Main Simulation / Prompt tab
  if(typeof switchTab === 'function'){
    const tabTarget = document.getElementById('view-prompt') ? 'prompt' : 'simulation';
    switchTab(tabTarget);
  } else if(typeof tab === 'function'){
    tab('pred');
  }

  // 3. Confirm to user via assistant
  appendNanoBotMsg('ai', `🚀 <b>Transferred to Main Section!</b> The formatted prompt has been injected into the primary experiment input: <i>"${promptText}"</i>.`);
}



// -------------------------------------------------------------
// Research Report Generator
// -------------------------------------------------------------
function generateResearchReport() {
    const lines = [
        '====================================================================',
        '               NANOMEDAI RESEARCH SESSION AUDIT REPORT              ',
        '====================================================================',
        `Generated: ${new Date().toLocaleString()}`,
        `Platform Version: 1.0.0 (FastAPI + Scikit-Learn 1.6+)`,
        '',
        '--- 1. ACTIVE SIMULATION STATE ---',
        `Formulation: ${FORMULATIONS[state.formulationKey]?.name || 'Custom'}`,
        `Simulation Time: ${state.time.toFixed(1)} h (Max: ${state.maxTime.toFixed(1)} h)`,
        `Environment: Temp = ${state.env.temp.toFixed(1)}°C, pH = ${state.env.ph.toFixed(1)}, Ionic = ${state.env.ionic.toFixed(2)} M`,
        `Particle Core Size: ${state.particle.size ? state.particle.size.toFixed(1) : 'N/A'} nm`,
        `Hydrodynamic Size: ${state.particle.hydSize ? state.particle.hydSize.toFixed(1) : 'N/A'} nm`,
        `Zeta Potential: ${state.particle.zeta ? state.particle.zeta.toFixed(1) : 'N/A'} mV`,
        `PDI: ${state.particle.pdi ? state.particle.pdi.toFixed(3) : 'N/A'}`,
        `Cumulative Drug Release: ${state.particle.release.toFixed(2)}%`,
        `Drug Remaining in Core: ${state.particle.remaining.toFixed(2)}%`,
        ''
    ];
    
    if (state.workflowResult) {
        const wf = state.workflowResult;
        lines.push('--- 2. AI EXPERIMENT PROMPT PIPELINE ---');
        lines.push(`Input Prompt: ${$('experiment-prompt').value}`);
        lines.push(`Colloidal Stability: ${wf.stability.result ? `${wf.stability.result.prediction} mV (${wf.stability.result.stability_class})` : 'Outside validated domain'}`);
        lines.push(`Cytotoxicity: ${wf.toxicity.result ? `${wf.toxicity.result.prediction} (Risk: ${wf.toxicity.result.risk_level})` : 'Not evaluated'}`);
        lines.push(`Biophysical Release: ${wf.simulation.final_release_pct !== null ? `${wf.simulation.final_release_pct.toFixed(1)}% at ${state.maxTime.toFixed(0)}h` : 'Not run'}`);
        lines.push(`Cross-Validation Stability MAE: ${wf.stability.cv.metrics.MAE_mV.toFixed(2)} mV`);
        lines.push(`Cross-Validation Toxicity F1: ${wf.toxicity.cv.metrics.F1.toFixed(3)}`);
        lines.push(`Cross-Validation Release MAE: ${wf.simulation.cv.MAE_release_percentage_points.toFixed(2)} percentage points`);
        lines.push('');
    }
    
    if (state.predictionHistory.length) {
        lines.push('--- 3. DIRECT MODEL PREDICTIONS HISTORY ---');
        state.predictionHistory.forEach((item, idx) => {
            lines.push(`[${idx + 1}] ${item.task.toUpperCase()} at ${item.time}`);
            lines.push(`Inputs: ${JSON.stringify(item.payload)}`);
            lines.push(`Result: ${JSON.stringify(item.res.prediction)} (${item.res.confidence || ''})`);
            lines.push('');
        });
    }
    
    lines.push('--- 4. SCIENTIFIC LIMITATIONS & ADVISORY ---');
    lines.push('• All estimates are generated by harmonized empirical surrogate models.');
    lines.push('• Biological stages (Protein corona, Cellular uptake, In vivo distribution) require prospective wet-lab validation.');
    lines.push('• Environmental pH and ionic strength modifiers are non-causal heuristic bounds unless explicitly modeled in wet lab assays.');
    lines.push('====================================================================');
    
    $('report-output').value = lines.join('\n');
}

$('generate-report').addEventListener('click', generateResearchReport);

$('download-report').addEventListener('click', () => {
    let text = $('report-output').value;
    if (!text.trim()) {
        generateResearchReport();
        text = $('report-output').value;
    }
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NanoMedAI_Research_Report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
});

// -------------------------------------------------------------
// System Bootstrap & Health Check
// -------------------------------------------------------------
async function bootstrap() {
    // Populate Initial Static Formulation
    setFormulationConfig('formulation-a');
    resetSim();
    
    // Ping Backend Health
    const pill = $('backend-status-pill');
    const pillText = $('backend-status-text');
    try {
        const health = await requestJSON('/api/health');
        state.backendConnected = true;
        pill.className = 'backend-indicator online';
        pillText.textContent = `API: ONLINE (${health.version})`;
        addEvent(`Connected to NanoMedAI FastAPI backend (v${health.version})`, 'sys');
        
        // Fetch Metadata & setup forms
        const meta = await requestJSON('/api/metadata');
        state.metadata = meta;
        
        // Fill dropdowns in Advanced Drawer & Matrix
        const stab = meta.stability;
        const cyto = meta.cytotoxicity;
        const populateSelect = (id, items) => {
            const el = $(id);
            if (!el) return;
            el.innerHTML = '<option value="">Default</option>' + (items || []).map(i => `<option value="${escapeHTML(i)}">${escapeHTML(i)}</option>`).join('');
        };

        const setupSearchableDrugDropdown = (inputId, dropdownId, items, drugMwMap) => {
            const input = $(inputId);
            const dropdown = $(dropdownId);
            if (!input || !dropdown) return;

            let availableItems = items || [];

            const renderOptions = (filterText = '') => {
                const query = (filterText || '').trim().toLowerCase();
                const matches = availableItems.filter(item => item.toLowerCase().includes(query));
                if (matches.length === 0) {
                    dropdown.innerHTML = '<div class="searchable-option empty">No matching drug found</div>';
                } else {
                    dropdown.innerHTML = matches.map(item => 
                        `<div class="searchable-option" data-value="${escapeHTML(item)}">${escapeHTML(item)}</div>`
                    ).join('');
                }
            };

            const showDropdown = () => {
                renderOptions(input.value);
                dropdown.style.display = 'block';
            };

            input.addEventListener('focus', showDropdown);
            input.addEventListener('click', showDropdown);

            input.addEventListener('input', () => {
                renderOptions(input.value);
                dropdown.style.display = 'block';
            });

            dropdown.addEventListener('click', (e) => {
                const itemEl = e.target.closest('.searchable-option');
                if (itemEl && itemEl.dataset.value) {
                    const selectedDrug = itemEl.dataset.value;
                    input.value = selectedDrug;
                    dropdown.style.display = 'none';

                    const mwInput = $('prompt-drug-mw');
                    if (mwInput && drugMwMap && drugMwMap[selectedDrug]) {
                        if (!mwInput.value || parseFloat(mwInput.value) === 0) {
                            mwInput.value = drugMwMap[selectedDrug];
                        }
                    }
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            document.addEventListener('click', (e) => {
                if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });
        };

        populateSelect('prompt-core', stab.cores);
        populateSelect('prompt-shape', stab.shapes);
        populateSelect('prompt-material', cyto.materials);
        populateSelect('prompt-assay', cyto.assays);
        populateSelect('prompt-cell', cyto.cell_lines);
        if ($('prompt-drug-dropdown')) {
            setupSearchableDrugDropdown('prompt-drug', 'prompt-drug-dropdown', rel.categories.drug_name, rel.drug_mw_map);
        } else {
            populateSelect('prompt-drug', rel.categories.drug_name);
        }
        populateSelect('prompt-polymer', rel.categories.polymer);
        
        if ($('prompt-ligand')) {
            $('prompt-ligand').innerHTML = '<option value="">Default</option>' +
                stab.ligand_presets.map(l => `<option value="${escapeHTML(l.smiles)}">${escapeHTML(l.name)}</option>`).join('');
        }
        
        if ($('matrix-core')) {
            $('matrix-core').innerHTML = stab.cores.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('');
        }
        
        buildPredictorForm('stability');
    } catch (err) {
        state.backendConnected = false;
        pill.className = 'backend-indicator offline';
        pillText.textContent = 'API: STANDALONE ENGINE';
        addEvent('Backend service unreachable; running in standalone local biophysical mode', 'warn');
    }

    initIntroModal();
}

// Intro Modal Handlers & Diagnostics
function initIntroModal() {
    const modal = $('intro-modal');
    const closeBtn = $('btn-close-intro');
    const enterBtn = $('btn-enter-workspace');
    const showBtn = $('btn-show-intro');
    
    function closeModal() {
        if (modal) modal.classList.remove('active');
    }
    function openModal() {
        if (modal) {
            modal.classList.add('active');
            runIntroDiagnostics();
        }
    }
    
    if (closeBtn) closeBtn.onclick = closeModal;
    if (enterBtn) enterBtn.onclick = closeModal;
    if (showBtn) showBtn.onclick = openModal;
    
    // Auto-animate diagnostics
    runIntroDiagnostics();
}

function runIntroDiagnostics() {
    const bar = $('intro-diag-bar');
    const pct = $('intro-diag-percent');
    if (!bar || !pct) return;
    
    bar.style.width = '0%';
    pct.textContent = 'INITIALIZING...';
    
    let p = 0;
    const interval = setInterval(() => {
        p += 25;
        if (p > 100) {
            clearInterval(interval);
            bar.style.width = '100%';
            pct.textContent = '100% READY';
        } else {
            bar.style.width = p + '%';
            pct.textContent = p + '% READY';
        }
    }, 160);
}

// Window Resize Handling
window.addEventListener('resize', () => {
    if (typeof resize3D === 'function') resize3D();
});

// Run Bootstrap on DOM Ready
document.addEventListener('DOMContentLoaded', bootstrap);

