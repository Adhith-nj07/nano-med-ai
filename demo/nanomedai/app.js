/**
 * NanoMedAI — Research Platform Demonstration Application Controller
 * Handles navigation, interactive scientific visualizations, simulation loop,
 * environment tracking, event logging, and candidate screening.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Application State
  const state = window.NMI_STATE;
  const particles = window.NMI_PARTICLES;
  const trajectories = window.NMI_TRAJECTORIES;

  // Active state holders
  let selectedParticle = particles[0];
  let simAnimFrame = null;
  let lastFrameTimestamp = 0;

  // DOM Elements Initialization
  initNavigation();
  initParticleBuilder();
  initEnvironmentBuilder();
  initPredictionWorkspace();
  initSimulationLab();
  initDrugReleasePanel();
  initParticleStabilityPanel();
  initModelTransparency();
  initDatasetExplorer();
  initCandidateScreening();
  initComparisonMode();
  initResearchReport();

  // Draw initial canvases
  drawConceptualParticle("particleCanvas", selectedParticle);
  drawConceptualParticle("builderParticleCanvas", selectedParticle);
  drawSimulationCanvas();
  drawReleaseChartCanvas();
  renderHeatmapGrid();
  renderEventLog();

  // =========================================================================
  // 1. NAVIGATION SYSTEM
  // =========================================================================
  function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const viewSections = document.querySelectorAll(".view-section");

    navItems.forEach(item => {
      item.addEventListener("click", () => {
        const targetView = item.getAttribute("data-view");
        if (!targetView) return;

        // Update nav UI
        navItems.forEach(n => n.classList.remove("active"));
        item.classList.add("active");

        // Update view sections
        viewSections.forEach(v => {
          v.classList.remove("active");
          if (v.id === `view-${targetView}`) {
            v.classList.add("active");
          }
        });

        state.activeView = targetView;

        // Redraw active visualizations if needed
        if (targetView === "simulation") {
          drawSimulationCanvas();
        } else if (targetView === "release") {
          drawReleaseChartCanvas();
        } else if (targetView === "builder") {
          drawConceptualParticle("builderParticleCanvas", selectedParticle);
        }
      });
    });

    // Particle selector change handlers
    const particleSelect = document.getElementById("activeParticleSelect");
    if (particleSelect) {
      particleSelect.addEventListener("change", (e) => {
        const found = particles.find(p => p.id === e.target.value);
        if (found) {
          selectedParticle = found;
          state.activeParticleId = found.id;
          updateParticleDisplays();
        }
      });
    }
  }

  function updateParticleDisplays() {
    drawConceptualParticle("particleCanvas", selectedParticle);
    drawConceptualParticle("builderParticleCanvas", selectedParticle);
    updatePredictionDisplay();
    updateReportView();
  }

  // =========================================================================
  // 2. CONCEPTUAL PARTICLE CANVAS RENDERER
  // =========================================================================
  function drawConceptualParticle(canvasId, particle) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const cx = width / 2;
    const cy = height / 2;

    ctx.clearRect(0, 0, width, height);

    // Dark Background Grid
    ctx.strokeStyle = "rgba(51, 65, 85, 0.3)";
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 20) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (let y = 0; y < height; y += 20) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }

    // 1. Hydrodynamic Boundary Layer (Outer dashed circle)
    const hydroRadius = Math.min(width, height) * 0.38;
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, hydroRadius, 0, Math.PI * 2);
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(56, 189, 248, 0.5)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = "rgba(56, 189, 248, 0.04)";
    ctx.fill();
    ctx.restore();

    // 2. Polymer / Coating Shell
    const coatingRadius = hydroRadius * 0.75;
    ctx.beginPath();
    ctx.arc(cx, cy, coatingRadius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(192, 132, 252, 0.25)";
    ctx.fill();
    ctx.strokeStyle = "rgba(192, 132, 252, 0.6)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // 3. Nanoparticle Core
    const coreRadius = coatingRadius * 0.6;
    ctx.beginPath();
    ctx.arc(cx, cy, coreRadius, 0, Math.PI * 2);
    const grad = ctx.createRadialGradient(cx - 5, cy - 5, 2, cx, cy, coreRadius);
    grad.addColorStop(0, "#475569");
    grad.addColorStop(1, "#1e293b");
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 2;
    ctx.stroke();

    // 4. Encapsulated Drug Payload Molecules inside Core/Shell
    const drugCount = 12;
    for (let i = 0; i < drugCount; i++) {
      const angle = (i / drugCount) * Math.PI * 2 + 0.3;
      const r = coreRadius * 0.55 * (0.3 + 0.7 * Math.sin(i * 3));
      const dx = cx + r * Math.cos(angle);
      const dy = cy + r * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(dx, dy, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#f87171"; // Red drug molecule
      ctx.fill();
    }

    // 5. Surface Ligands (Folate / PEG chains emanating outwards)
    const ligandCount = 16;
    for (let i = 0; i < ligandCount; i++) {
      const angle = (i / ligandCount) * Math.PI * 2;
      const x1 = cx + coatingRadius * Math.cos(angle);
      const y1 = cy + coatingRadius * Math.sin(angle);
      const x2 = cx + (hydroRadius - 4) * Math.cos(angle);
      const y2 = cy + (hydroRadius - 4) * Math.sin(angle);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.quadraticCurveTo(
        cx + (coatingRadius + 12) * Math.cos(angle + 0.2),
        cy + (coatingRadius + 12) * Math.sin(angle + 0.2),
        x2, y2
      );
      ctx.strokeStyle = "#34d399"; // Green ligand chain
      ctx.lineWidth = 1.8;
      ctx.stroke();

      // Ligand terminal head group
      ctx.beginPath();
      ctx.arc(x2, y2, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = "#34d399";
      ctx.fill();
    }

    // Overlay Annotation Labels
    ctx.font = "10px monospace";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`Core: ${particle.coreSizeNm} nm`, 10, height - 28);
    ctx.fillText(`Hydro: ${particle.hydroSizeNm} nm`, 10, height - 12);

    ctx.fillStyle = "#34d399";
    ctx.fillText("CONCEPTUAL PARTICLE VIEW", width - 160, 18);
  }

  // =========================================================================
  // 3. LIVE SIMULATION CANVAS & TIME LOOP
  // =========================================================================
  function initSimulationLab() {
    const btnStart = document.getElementById("simBtnStart");
    const btnPause = document.getElementById("simBtnPause");
    const btnStep = document.getElementById("simBtnStep");
    const btnReset = document.getElementById("simBtnReset");
    const speedSelect = document.getElementById("simSpeedSelect");

    if (btnStart) {
      btnStart.addEventListener("click", () => {
        state.simulation.isRunning = true;
        btnStart.style.display = "none";
        btnPause.style.display = "inline-flex";
        pushEvent("SIMULATION_RESUMED", "USER_INPUT", "Simulation playback resumed.", "User Action", "N/A", true);
        startSimLoop();
      });
    }

    if (btnPause) {
      btnPause.addEventListener("click", () => {
        state.simulation.isRunning = false;
        btnPause.style.display = "none";
        btnStart.style.display = "inline-flex";
        pushEvent("SIMULATION_PAUSED", "USER_INPUT", "Simulation playback paused.", "User Action", "N/A", true);
      });
    }

    if (btnStep) {
      btnStep.addEventListener("click", () => {
        stepSimulation(state.simulation.stepSizeHours);
      });
    }

    if (btnReset) {
      btnReset.addEventListener("click", () => {
        state.simulation.isRunning = false;
        state.simulation.currentTimeHours = 0.0;
        state.simulation.cumulativeReleasePct = 0.0;
        state.simulation.remainingDrugPct = 100.0;
        if (btnStart) btnStart.style.display = "inline-flex";
        if (btnPause) btnPause.style.display = "none";
        pushEvent("SIMULATION_RESET", "USER_INPUT", "Simulation reset to T = 0.0 h.", "User Action", "N/A", true);
        updateSimUI();
        drawSimulationCanvas();
        drawReleaseChartCanvas();
      });
    }

    if (speedSelect) {
      speedSelect.addEventListener("change", (e) => {
        state.simulation.speedMultiplier = parseFloat(e.target.value);
      });
    }
  }

  function startSimLoop() {
    if (!state.simulation.isRunning) return;
    const now = performance.now();
    if (lastFrameTimestamp > 0) {
      const deltaSec = (now - lastFrameTimestamp) / 1000;
      const hoursAdvance = deltaSec * 1.5 * state.simulation.speedMultiplier;
      stepSimulation(hoursAdvance);
    }
    lastFrameTimestamp = now;

    if (state.simulation.currentTimeHours < state.simulation.maxTimeHours) {
      simAnimFrame = requestAnimationFrame(startSimLoop);
    } else {
      state.simulation.isRunning = false;
      const btnStart = document.getElementById("simBtnStart");
      const btnPause = document.getElementById("simBtnPause");
      if (btnStart) btnStart.style.display = "inline-flex";
      if (btnPause) btnPause.style.display = "none";
      pushEvent("SIMULATION_END", "MAX_TIME_REACHED", "Simulation reached end time limit (72.0 h).", "Korsmeyer-Peppas Engine", "± 5.0%", true);
    }
  }

  function stepSimulation(deltaHours) {
    state.simulation.currentTimeHours = Math.min(
      state.simulation.maxTimeHours,
      state.simulation.currentTimeHours + deltaHours
    );

    // Korsmeyer-Peppas calculation: M_t / M_inf = K * t^n (K=0.082, n=0.45)
    const t = state.simulation.currentTimeHours;
    if (t <= 0) {
      state.simulation.cumulativeReleasePct = 0.0;
    } else {
      const releaseFrac = 0.082 * Math.pow(t, 0.45);
      state.simulation.cumulativeReleasePct = Math.min(100.0, +(releaseFrac * 100).toFixed(1));
    }
    state.simulation.remainingDrugPct = +(100.0 - state.simulation.cumulativeReleasePct).toFixed(1);

    // Trigger warning when crossing 48h (extrapolation threshold)
    if (t >= 48.0 && !state.simulation._warned48) {
      state.simulation._warned48 = true;
      pushEvent("EXTRAPOLATION_STARTED", "VALIDITY_BOUNDARY", "EXTRAPOLATION: Trajectory beyond 48.0h exceeds Korsmeyer-Peppas validation window.", "Model Validation Checker", "± 14.2%", false);
    }

    updateSimUI();
    drawSimulationCanvas();
    drawReleaseChartCanvas();
  }

  function updateSimUI() {
    const timeDisplay = document.getElementById("simTimerDisplay");
    const releaseDisplay = document.getElementById("simReleaseVal");
    const remainingDisplay = document.getElementById("simRemainingVal");
    const timelineScrubber = document.getElementById("simTimelineRange");

    if (timeDisplay) timeDisplay.textContent = `T = ${state.simulation.currentTimeHours.toFixed(1)} h`;
    if (releaseDisplay) releaseDisplay.textContent = `${state.simulation.cumulativeReleasePct.toFixed(1)} %`;
    if (remainingDisplay) remainingDisplay.textContent = `${state.simulation.remainingDrugPct.toFixed(1)} %`;
    if (timelineScrubber) timelineScrubber.value = state.simulation.currentTimeHours;
  }

  function drawSimulationCanvas() {
    const canvas = document.getElementById("simCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const cx = width / 2;
    const cy = height / 2;

    ctx.clearRect(0, 0, width, height);

    // Ambient Medium / Solvent background
    ctx.fillStyle = "#05080e";
    ctx.fillRect(0, 0, width, height);

    // Medium grid
    ctx.strokeStyle = "rgba(30, 41, 59, 0.5)";
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 30) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (let y = 0; y < height; y += 30) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }

    // Nanoparticle Core & Shell
    const hydroRadius = 90;
    const coreRadius = 55;

    // Hydrodynamic boundary
    ctx.beginPath();
    ctx.arc(cx, cy, hydroRadius, 0, Math.PI * 2);
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]);

    // Core
    ctx.beginPath();
    ctx.arc(cx, cy, coreRadius, 0, Math.PI * 2);
    ctx.fillStyle = "#1e293b";
    ctx.fill();
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Released Drug Molecules Diffusing Outward into Medium
    const releaseFrac = state.simulation.cumulativeReleasePct / 100.0;
    const totalMolecules = 40;
    const releasedCount = Math.floor(totalMolecules * releaseFrac);
    const internalCount = totalMolecules - releasedCount;

    // Internal molecules inside core
    for (let i = 0; i < internalCount; i++) {
      const angle = (i / totalMolecules) * Math.PI * 2 * 3.1;
      const r = coreRadius * 0.7 * (0.2 + 0.8 * (i / totalMolecules));
      const mx = cx + r * Math.cos(angle);
      const my = cy + r * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(mx, my, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#f87171";
      ctx.fill();
    }

    // Released molecules diffusing into surrounding environment
    for (let i = 0; i < releasedCount; i++) {
      const angle = (i / totalMolecules) * Math.PI * 2 * 2.7 + 0.5;
      const r = hydroRadius + 15 + (i * 3.5) % 110;
      const mx = cx + r * Math.cos(angle);
      const my = cy + r * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(mx, my, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#fbbf24"; // Released payload in amber gold
      ctx.fill();

      // Diffusion vector arrow
      ctx.beginPath();
      ctx.moveTo(mx, my);
      ctx.lineTo(mx + 6 * Math.cos(angle), my + 6 * Math.sin(angle));
      ctx.strokeStyle = "rgba(251, 191, 36, 0.4)";
      ctx.stroke();
    }
  }

  // =========================================================================
  // 4. ENVIRONMENT CONTROLS & EVENT LOGGING
  // =========================================================================
  function initEnvironmentBuilder() {
    const phInput = document.getElementById("envPhInput");
    const tempInput = document.getElementById("envTempInput");

    if (phInput) {
      phInput.addEventListener("change", (e) => {
        const val = parseFloat(e.target.value);
        state.simulation.environment.ph = val;
        pushEvent("ENVIRONMENT_CHANGE", "USER_INPUT", `pH shifted to ${val.toFixed(2)}`, "User Action", "N/A", true);
        pushEvent("MODEL_WARNING", "CAUSAL_LIMIT", "ENVIRONMENT CHANGED: Current model does not support causal release-parameter updating for this condition.", "Model Boundary Manager", "High", false);
      });
    }

    if (tempInput) {
      tempInput.addEventListener("change", (e) => {
        const val = parseFloat(e.target.value);
        state.simulation.environment.temperature_c = val;
        pushEvent("ENVIRONMENT_CHANGE", "USER_INPUT", `Temperature shifted to ${val.toFixed(1)} °C`, "User Action", "N/A", true);
        pushEvent("MODEL_WARNING", "CAUSAL_LIMIT", "ENVIRONMENT CHANGED: Current model does not support causal release-parameter updating for temperature.", "Model Boundary Manager", "High", false);
      });
    }
  }

  function pushEvent(type, trigger, desc, source, uncertainty, supported) {
    const evt = {
      timeHours: state.simulation.currentTimeHours,
      type: type,
      severity: supported ? "info" : "warning",
      trigger: trigger,
      description: desc,
      modelSource: source,
      uncertainty: uncertainty,
      supported: supported
    };
    state.simulation.events.unshift(evt);
    renderEventLog();
  }

  function renderEventLog() {
    const container = document.getElementById("eventLogContainer");
    if (!container) return;
    container.innerHTML = "";

    state.simulation.events.slice(0, 15).forEach(evt => {
      const row = document.createElement("div");
      row.className = `event-row ${evt.severity}`;
      row.innerHTML = `
        <span style="font-weight:700; color:var(--accent-purple);">${evt.timeHours.toFixed(1)} h</span>
        <span class="badge ${evt.supported ? 'badge-blue' : 'badge-amber'}">${evt.type}</span>
        <span style="color:var(--text-primary);">${evt.description}</span>
        <span style="color:var(--text-muted); text-align:right;">${evt.uncertainty}</span>
      `;
      container.appendChild(row);
    });
  }

  // =========================================================================
  // 5. DRUG RELEASE CHART RENDERER (Canvas)
  // =========================================================================
  function drawReleaseChartCanvas() {
    const canvas = document.getElementById("releaseChartCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    const padL = 55;
    const padR = 25;
    const padT = 30;
    const padB = 40;

    const graphW = width - padL - padR;
    const graphH = height - padT - padB;

    ctx.clearRect(0, 0, width, height);

    // 1. Shaded Extrapolation Region (Time > 48h)
    const x48 = padL + (48.0 / 72.0) * graphW;
    ctx.fillStyle = "rgba(248, 113, 113, 0.08)";
    ctx.fillRect(x48, padT, width - padR - x48, graphH);

    // Label for Extrapolation
    ctx.font = "10px monospace";
    ctx.fillStyle = "#f87171";
    ctx.fillText("EXTRAPOLATION REGION (>48h)", x48 + 10, padT + 20);

    // 2. Axes & Grid
    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 1;

    // Y Grid lines (0% to 100%)
    for (let pct = 0; pct <= 100; pct += 20) {
      const y = padT + graphH - (pct / 100.0) * graphH;
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(width - padR, y); ctx.stroke();
      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px monospace";
      ctx.fillText(`${pct}%`, 15, y + 3);
    }

    // X Grid lines (0h to 72h)
    const tPoints = [0, 12, 24, 36, 48, 60, 72];
    tPoints.forEach(t => {
      const x = padL + (t / 72.0) * graphW;
      ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, padT + graphH); ctx.stroke();
      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px monospace";
      ctx.fillText(`${t}h`, x - 8, height - 15);
    } );

    // 3. Experimental Reference Trajectory (Dashed Green)
    const expTimes = trajectories.timePointsHours;
    const expVals = trajectories.experimentalReleasePct;

    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "#34d399";
    ctx.lineWidth = 1.8;
    for (let i = 0; i < expTimes.length; i++) {
      const x = padL + (expTimes[i] / 72.0) * graphW;
      const y = padT + graphH - (expVals[i] / 100.0) * graphH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // 4. Korsmeyer-Peppas Simulated Trajectory (Solid Blue)
    const simVals = trajectories.simulatedReleasePct;
    ctx.beginPath();
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 2.5;
    for (let i = 0; i < expTimes.length; i++) {
      const x = padL + (expTimes[i] / 72.0) * graphW;
      const y = padT + graphH - (simVals[i] / 100.0) * graphH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // 5. Current Simulation Time Indicator Point
    const curT = state.simulation.currentTimeHours;
    const curPct = state.simulation.cumulativeReleasePct;
    const curX = padL + (curT / 72.0) * graphW;
    const curY = padT + graphH - (curPct / 100.0) * graphH;

    ctx.beginPath();
    ctx.arc(curX, curY, 6, 0, Math.PI * 2);
    ctx.fillStyle = "#c084fc";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Vertical line indicator
    ctx.beginPath();
    ctx.setLineDash([2, 2]);
    ctx.moveTo(curX, padT);
    ctx.lineTo(curX, padT + graphH);
    ctx.strokeStyle = "rgba(192, 132, 252, 0.6)";
    ctx.stroke();
    ctx.setLineDash([]);

    // Legend
    ctx.font = "11px sans-serif";
    ctx.fillStyle = "#38bdf8"; ctx.fillText("— Simulated (Korsmeyer-Peppas)", padL + 20, padT + 40);
    ctx.fillStyle = "#34d399"; ctx.fillText("- - Experimental In-Vitro", padL + 240, padT + 40);
  }

  // =========================================================================
  // 6. STABILITY HEATMAP GRID RENDERER
  // =========================================================================
  function renderHeatmapGrid() {
    const table = document.getElementById("heatmapGridTable");
    if (!table) return;
    table.innerHTML = "";

    const phs = trajectories.heatmap.phRange;
    const temps = trajectories.heatmap.tempRange;
    const grid = trajectories.heatmap.grid;

    // Header Row (pH)
    const headRow = document.createElement("tr");
    headRow.innerHTML = `<th>Temp \\ pH</th>` + phs.map(p => `<th>pH ${p.toFixed(1)}</th>`).join("");
    table.appendChild(headRow);

    // Rows (Temperatures)
    temps.forEach((t, rIdx) => {
      const tr = document.createElement("tr");
      let html = `<th style="color:var(--text-secondary);">${t.toFixed(0)} °C</th>`;
      grid[rIdx].forEach(cell => {
        html += `
          <td class="heatmap-cell" style="background-color:${cell.color};" title="Zeta: ${cell.zeta} mV (${cell.status})">
            <div>${cell.zeta}</div>
            <div style="font-size:8px; opacity:0.8;">${cell.rating}</div>
          </td>
        `;
      });
      tr.innerHTML = html;
      table.appendChild(tr);
    });
  }

  // =========================================================================
  // 7. PREDICTION & OTHER WORKSPACE INITIALIZERS
  // =========================================================================
  function initParticleBuilder() {}
  function initPredictionWorkspace() {}
  function initParticleStabilityPanel() {}
  function initModelTransparency() {}
  function initDatasetExplorer() {}
  function initCandidateScreening() {}
  function initComparisonMode() {}
  function initResearchReport() {}

  function updatePredictionDisplay() {
    const p = selectedParticle;
    const zVal = document.getElementById("predZetaVal");
    const cVal = document.getElementById("predCytoVal");

    if (zVal && p.predictions.zetaPotential) {
      zVal.textContent = `${p.predictions.zetaPotential.valueMv} mV`;
    }
    if (cVal && p.predictions.cytotoxicity) {
      cVal.textContent = `${p.predictions.cytotoxicity.result}`;
    }
  }

  function updateReportView() {
    const rPartId = document.getElementById("reportParticleId");
    if (rPartId) rPartId.textContent = selectedParticle.name;
  }
});
