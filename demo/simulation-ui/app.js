// app.js - Main UI controller for Phase 6 Simulation Demo

document.addEventListener('DOMContentLoaded', () => {

    const UI = {
        statusLabel: document.getElementById('sim-status-label'),
        btnStart: document.getElementById('btn-start'),
        btnPause: document.getElementById('btn-pause'),
        btnResume: document.getElementById('btn-resume'),
        btnStep: document.getElementById('btn-step'),
        btnStop: document.getElementById('btn-stop'),
        btnReset: document.getElementById('btn-reset'),
        
        timeline: document.getElementById('sim-timeline'),
        timeVal: document.getElementById('val-time'),
        
        formulation: document.getElementById('config-formulation'),
        cfgDrug: document.getElementById('cfg-drug'),
        cfgMaterial: document.getElementById('cfg-material'),
        cfgSize: document.getElementById('cfg-size'),
        cfgZeta: document.getElementById('cfg-zeta'),
        cfgLoading: document.getElementById('cfg-loading'),
        cfgCoating: document.getElementById('cfg-coating'),
        
        envTemp: document.getElementById('env-temp'),
        envPh: document.getElementById('env-ph'),
        envIonic: document.getElementById('env-ionic'),
        valTemp: document.getElementById('val-temp'),
        valPh: document.getElementById('val-ph'),
        valIonic: document.getElementById('val-ionic'),
        envWarning: document.getElementById('env-warning'),
        overlayEnv: document.getElementById('overlay-env'),
        overlayTemp: document.getElementById('overlay-temp'),
        overlayPh: document.getElementById('overlay-ph'),
        overlayIonic: document.getElementById('overlay-ionic'),
        
        stateSize: document.getElementById('state-size'),
        stateHsize: document.getElementById('state-hsize'),
        statePdi: document.getElementById('state-pdi'),
        stateZeta: document.getElementById('state-zeta'),
        stateRelease: document.getElementById('state-release'),
        stateRemaining: document.getElementById('state-remaining'),
        
        eventsList: document.getElementById('events-list'),
        speedBtns: document.querySelectorAll('.btn-speed')
    };

    // --- Charts ---
    const ctxRelease = document.getElementById('release-chart').getContext('2d');
    const ctxSize = document.getElementById('size-chart').getContext('2d');
    
    const labels = Array.from({length: 73}, (_, i) => i);
    const releaseData = new Array(73).fill(null);
    const sizeData = new Array(73).fill(null);

    const commonOptions = {
        responsive: true, maintainAspectRatio: false, animation: false,
        scales: {
            x: { grid: { color: '#333' }, ticks: { color: '#858585', maxTicksLimit: 12 } },
            y: { grid: { color: '#333' }, ticks: { color: '#858585' } }
        },
        plugins: { legend: { display: false } }
    };

    const releaseChart = new Chart(ctxRelease, {
        type: 'line',
        data: { labels, datasets: [{ data: releaseData, borderColor: '#007acc', backgroundColor: 'rgba(0,122,204,0.1)', borderWidth: 2, fill: true, pointRadius: 0, tension: 0.4 }] },
        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, min: 0, max: 100 } } }
    });

    const sizeChart = new Chart(ctxSize, {
        type: 'line',
        data: { labels, datasets: [{ data: sizeData, borderColor: '#4caf50', borderWidth: 2, pointRadius: 0, tension: 0.4 }] },
        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, min: 100, max: 160 } } }
    });

    // --- Canvas ---
    const canvas = document.getElementById('particle-canvas');
    const cctx = canvas.getContext('2d');
    let seed = 12345;

    function random() {
        let x = Math.sin(seed++) * 10000;
        return x - Math.floor(x);
    }

    function renderParticle() {
        cctx.clearRect(0, 0, canvas.width, canvas.height);
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        
        const scale = demoState.particle.particleSize / 120;
        const baseRadius = 60 * scale;
        
        // Background Env
        const bgGrad = cctx.createRadialGradient(cx, cy, baseRadius, cx, cy, canvas.width);
        const tempColor = Math.floor(((demoState.env.temperature - 20) / 30) * 100);
        bgGrad.addColorStop(0, '#1a1a1a');
        bgGrad.addColorStop(1, `rgba(${tempColor}, 20, 50, 0.2)`);
        cctx.fillStyle = bgGrad;
        cctx.fillRect(0, 0, canvas.width, canvas.height);

        // Hydrodynamic Corona
        cctx.beginPath();
        const hydroRadius = baseRadius + (demoState.particle.hydrodynamicSize - demoState.particle.particleSize);
        cctx.arc(cx, cy, hydroRadius, 0, Math.PI * 2);
        cctx.fillStyle = 'rgba(0, 122, 204, 0.1)';
        cctx.fill();
        cctx.strokeStyle = 'rgba(0, 122, 204, 0.3)';
        cctx.setLineDash([5, 5]);
        cctx.stroke();
        cctx.setLineDash([]);

        // Particle Core
        cctx.beginPath();
        cctx.arc(cx, cy, baseRadius, 0, Math.PI * 2);
        const coreGrad = cctx.createRadialGradient(cx-15, cy-15, 5, cx, cy, baseRadius);
        coreGrad.addColorStop(0, '#666');
        coreGrad.addColorStop(1, '#222');
        cctx.fillStyle = coreGrad;
        cctx.fill();
        cctx.strokeStyle = '#555';
        cctx.lineWidth = 2;
        cctx.stroke();

        // Payloads
        seed = 42; 
        const remRatio = demoState.particle.drugRemaining / 100;
        const relRatio = demoState.particle.drugRelease / 100;
        
        cctx.fillStyle = '#4caf50';
        for(let i=0; i<Math.floor(120 * remRatio); i++) {
            const angle = random() * Math.PI * 2;
            const r = Math.sqrt(random()) * (baseRadius - 8);
            cctx.beginPath(); cctx.arc(cx + Math.cos(angle)*r, cy + Math.sin(angle)*r, 2.5, 0, Math.PI*2); cctx.fill();
        }

        cctx.fillStyle = 'rgba(76, 175, 80, 0.6)';
        for(let i=0; i<Math.floor(120 * relRatio); i++) {
            const angle = random() * Math.PI * 2;
            const r = baseRadius + 10 + random() * 150;
            const wobble = Math.sin(demoState.simulationTime + i) * (demoState.env.temperature/5);
            cctx.beginPath(); cctx.arc(cx + Math.cos(angle)*r + wobble, cy + Math.sin(angle)*r + wobble, 2, 0, Math.PI*2); cctx.fill();
        }
    }

    // --- Core Logic ---

    function renderEvents(desc, type='normal') {
        const div = document.createElement('div');
        div.className = `event-item ${type}`;
        const prefix = type === 'warn' ? '⚠' : '●';
        div.innerHTML = `<div class="event-time">${demoState.simulationTime.toFixed(1)} h</div><div>${prefix} ${desc}</div>`;
        UI.eventsList.prepend(div);
    }

    function updateCharts() {
        const tFloor = Math.floor(demoState.simulationTime);
        for(let i=0; i<=72; i++) {
            if (i <= tFloor) {
                // Quick deterministic recalc for historical graph consistency
                let mockState = JSON.parse(JSON.stringify(demoState));
                calculateDemoState(i, mockState);
                releaseChart.data.datasets[0].data[i] = mockState.particle.drugRelease;
                sizeChart.data.datasets[0].data[i] = mockState.particle.particleSize;
            } else {
                releaseChart.data.datasets[0].data[i] = null;
                sizeChart.data.datasets[0].data[i] = null;
            }
        }
        releaseChart.update();
        sizeChart.update();
    }

    function updateDashboard() {
        UI.stateSize.innerText = demoState.particle.particleSize.toFixed(1);
        UI.stateHsize.innerText = demoState.particle.hydrodynamicSize.toFixed(1);
        UI.statePdi.innerText = demoState.particle.pdi.toFixed(3);
        UI.stateZeta.innerText = demoState.particle.zetaPotential.toFixed(1);
        UI.stateRelease.innerText = demoState.particle.drugRelease.toFixed(1);
        UI.stateRemaining.innerText = demoState.particle.drugRemaining.toFixed(1);
        
        UI.timeVal.innerText = demoState.simulationTime.toFixed(1);
        UI.timeline.value = demoState.simulationTime;

        UI.statusLabel.innerText = `● ${demoState.status}`;
        UI.statusLabel.className = `status-${demoState.status.toLowerCase()}`;

        renderParticle();
        updateCharts();
    }

    function syncButtons() {
        UI.btnStart.classList.toggle('hidden', demoState.status !== 'INITIALIZED' && demoState.status !== 'STOPPED' && demoState.status !== 'COMPLETED');
        UI.btnResume.classList.toggle('hidden', demoState.status !== 'PAUSED');
        
        UI.btnStart.disabled = (demoState.status === 'COMPLETED');
        UI.btnPause.disabled = (demoState.status !== 'RUNNING');
        UI.btnStop.disabled = (demoState.status === 'INITIALIZED' || demoState.status === 'STOPPED' || demoState.status === 'COMPLETED');
        UI.btnStep.disabled = (demoState.status === 'RUNNING' || demoState.status === 'COMPLETED');
    }

    function tick() {
        if (demoState.status !== 'RUNNING') return;
        
        // Advance time: ~60fps -> 1 frame = 1/60 sec real time
        const deltaHr = (1 / 60) * demoState.speedMultiplier;
        demoState.simulationTime += deltaHr;

        if (demoState.simulationTime >= demoState.maxTime) {
            demoState.simulationTime = demoState.maxTime;
            demoState.status = 'COMPLETED';
            renderEvents('Simulation completed', 'sys');
            clearInterval(demoState.intervalId);
        } else if (Math.random() < 0.005) {
            renderEvents('Particle state updated', 'normal');
        }

        calculateDemoState(demoState.simulationTime, demoState);
        updateDashboard();
        syncButtons();
    }

    // --- Actions ---

    function startDemo() {
        if (demoState.status === 'COMPLETED') return;
        demoState.status = 'RUNNING';
        renderEvents(demoState.simulationTime === 0 ? 'Simulation initialized' : 'Simulation running', 'sys');
        demoState.intervalId = setInterval(tick, 1000/60);
        syncButtons();
    }

    function pauseDemo() {
        demoState.status = 'PAUSED';
        renderEvents('Simulation paused', 'sys');
        clearInterval(demoState.intervalId);
        updateDashboard();
        syncButtons();
    }

    function stopDemo() {
        demoState.status = 'STOPPED';
        renderEvents('Simulation stopped', 'warn');
        clearInterval(demoState.intervalId);
        updateDashboard();
        syncButtons();
    }

    function stepDemo() {
        if (demoState.status === 'COMPLETED') return;
        demoState.simulationTime = Math.min(demoState.maxTime, demoState.simulationTime + 1.0);
        renderEvents(`Stepped to ${demoState.simulationTime.toFixed(1)} h`, 'normal');
        calculateDemoState(demoState.simulationTime, demoState);
        updateDashboard();
        syncButtons();
    }

    function resetDemo() {
        clearInterval(demoState.intervalId);
        demoState.status = 'INITIALIZED';
        demoState.simulationTime = 0;
        
        const f = demoState.formulations[demoState.config.formulation];
        demoState.particle.initialSize = f.size;
        demoState.particle.particleSize = f.size;
        demoState.particle.hydrodynamicSize = f.size + 8;
        demoState.particle.zetaPotential = f.zeta;
        demoState.particle.drugRelease = 0.0;
        demoState.particle.drugRemaining = 100.0;
        demoState.particle.pdi = 0.16;
        
        UI.eventsList.innerHTML = '';
        renderEvents('Workspace reset to initial state', 'sys');
        
        UI.envWarning.classList.add('hidden');
        
        updateDashboard();
        syncButtons();
    }

    // --- Bindings ---

    UI.btnStart.addEventListener('click', startDemo);
    UI.btnResume.addEventListener('click', startDemo);
    UI.btnPause.addEventListener('click', pauseDemo);
    UI.btnStop.addEventListener('click', stopDemo);
    UI.btnStep.addEventListener('click', stepDemo);
    UI.btnReset.addEventListener('click', resetDemo);

    UI.timeline.addEventListener('input', e => {
        demoState.simulationTime = parseFloat(e.target.value);
        if (demoState.status === 'COMPLETED' && demoState.simulationTime < demoState.maxTime) {
            demoState.status = 'PAUSED';
        }
        calculateDemoState(demoState.simulationTime, demoState);
        updateDashboard();
        syncButtons();
    });

    UI.timeline.addEventListener('change', () => {
        renderEvents(`Timeline scrubbed to ${demoState.simulationTime.toFixed(1)} h`, 'normal');
    });

    UI.speedBtns.forEach(btn => btn.addEventListener('click', e => {
        UI.speedBtns.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        demoState.speedMultiplier = parseFloat(e.target.dataset.speed);
    }));

    UI.formulation.addEventListener('change', e => {
        demoState.config.formulation = e.target.value;
        const f = demoState.formulations[e.target.value];
        UI.cfgDrug.innerText = f.drug;
        UI.cfgMaterial.innerText = f.material;
        UI.cfgSize.innerText = `${f.size} nm`;
        UI.cfgZeta.innerText = `${f.zeta} mV`;
        UI.cfgLoading.innerText = f.load;
        UI.cfgCoating.innerText = f.coat;
        if(demoState.status === 'INITIALIZED') resetDemo();
    });

    function bindEnv(input, display, overlay, key, warnOnChange) {
        input.addEventListener('input', e => {
            const v = parseFloat(e.target.value);
            demoState.env[key] = v;
            display.innerText = v.toFixed(key==='ionicStrength'?2:1);
            if(overlay) overlay.innerText = display.innerText;
            
            if(demoState.simulationTime > 0) {
                calculateDemoState(demoState.simulationTime, demoState);
                updateDashboard();
                if(warnOnChange) UI.envWarning.classList.remove('hidden');
            }
        });
        input.addEventListener('change', e => {
            const v = parseFloat(e.target.value);
            renderEvents(`Environment ${key} changed to ${v}`, 'normal');
            if(warnOnChange && demoState.simulationTime > 0) renderEvents('Demo environmental response triggered', 'warn');
        });
    }

    bindEnv(UI.envTemp, UI.valTemp, UI.overlayTemp, 'temperature', false);
    bindEnv(UI.envPh, UI.valPh, UI.overlayPh, 'ph', true);
    bindEnv(UI.envIonic, UI.valIonic, UI.overlayIonic, 'ionicStrength', false);

    document.getElementById('env-medium').addEventListener('change', e => {
        const t = e.target.options[e.target.selectedIndex].text;
        UI.overlayEnv.innerText = t;
        renderEvents(`Medium changed to ${t}`, 'normal');
    });

    // Init
    resetDemo();
});
