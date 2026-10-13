# NanoMedAI — Advanced Research Platform UI Demonstration

## Notice & Disclaimers

> [!IMPORTANT]
> **This is a frontend demonstration. It is not connected to the NanoMedAI scientific backend and its values are not scientific predictions.**

---

## Overview

**NanoMedAI** is a computational nanomedicine research platform for studying, predicting, and simulating medicinal nanoparticles.

This interface represents a **research workstation** designed for:
- Nanomedicine researchers
- Pharmaceutical R&D teams
- Drug-delivery researchers
- Computational & Materials scientists

---

## Key Information Architecture

1. **Research Overview**: Platform identity, active model status, capability matrix, dataset provenance.
2. **Nanoparticle Builder**: Workspace for defining physical, chemical, and formulation properties with a conceptual nanoparticle preview canvas.
3. **Environment Builder**: Surroundings configuration with explicit `SUPPORTED` vs `UNSUPPORTED` status tags.
4. **Prediction Workspace**: Static ML endpoint predictions for Zeta Potential (mV) and Cytotoxicity (Toxic/Nontoxic).
5. **Simulation Lab**: Central interactive lab with real-time Korsmeyer-Peppas drug release simulation engine, live controls, time-step controls, and event stream log.
6. **Drug Release Panel**: Cumulative release trajectory chart highlighting Model Valid Region (0-48h) vs Extrapolation Region (>48h).
7. **Particle Stability Panel**: DLVO-based stability matrix across pH and temperature gradients.
8. **Model Transparency**: Open-science validation metrics, GroupKFold cross-validation schemes, and DOI dataset references.
9. **Dataset Explorer**: Open research dataset archive table.
10. **Candidate Screening**: 4-stage translational selection funnel (100 candidates → 10 experimental shortlist).
11. **Candidate Comparison**: Multi-nanoparticle side-by-side comparative table.
12. **Research Report**: Exportable scientific documentation summary.

---

## File Structure

```text
demo/
└── nanomedai/
    ├── index.html          # Main HTML structure with 12 research views
    ├── styles.css          # Deep slate scientific research workstation theme
    ├── app.js              # View navigation, canvas renderers, sim loop, & charts
    ├── data/
    │   ├── demoState.js        # Simulation state & capability boundary matrix
    │   ├── demoParticles.js    # Candidate nanoparticles database
    │   └── demoTrajectories.js # Korsmeyer-Peppas curves, heatmaps & datasets
    └── README.md           # Documentation & disclaimers
```

---

## Visual Design Principles

- **Scientific Research Aesthetic**: Deep graphite and slate background (`#090d14`, `#0f172a`), high information density, thin borders, precise monospace labels for numerical units.
- **Explicit Limitations**: Clear visual badges (`SUPPORTED`, `VALIDATED`, `LIMITED`, `DATA REQUIRED`, `NOT IMPLEMENTED`, `NOT SCIENTIFICALLY SUPPORTED`, `DEMO VALUE`).
- **No Neon Cyberpunk / Gaming Aesthetics**: Restrained, professional biomedical computing aesthetic.
