// demoTrajectories.js - Handles the deterministic mock calculations for the demo

function calculateDemoState(t, state) {
    // A conceptual Korsmeyer-Peppas-like mock formula for visual demonstration.
    // DOES NOT reflect true physical parameters or backend logic.
    
    // Environmental modifiers for demo response
    const tempEffect = (state.env.temperature - 37) * 1.2;
    const phEffect = (7.4 - state.env.ph) * 2.0; 
    
    // Max release affected by environment purely for visual feedback
    let maxRelease = 85 + tempEffect + phEffect;
    if (maxRelease > 100) maxRelease = 100;
    if (maxRelease < 20) maxRelease = 20;

    // Release curve
    let release = maxRelease * (1 - Math.exp(-0.06 * t));
    
    // Size swelling (concept)
    let sizeDiff = release * 0.15;
    
    // Zeta potential drift
    let zetaDrift = t * 0.08 - (phEffect * 0.5);

    // Ensure realistic visual bounds
    release = Math.max(0, Math.min(100, release));
    
    // Update state particle
    state.particle.drugRelease = release;
    state.particle.drugRemaining = 100 - release;
    state.particle.particleSize = state.particle.initialSize + sizeDiff;
    state.particle.hydrodynamicSize = state.particle.particleSize + 8.0 + (state.env.ionicStrength * 10);
    
    const initialZeta = state.formulations[state.config.formulation].zeta;
    state.particle.zetaPotential = initialZeta + zetaDrift;
    
    // PDI slightly fluctuates
    state.particle.pdi = 0.16 + (Math.sin(t) * 0.02) + (release * 0.001);
}
