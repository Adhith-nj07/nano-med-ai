// demoState.js - Holds the frontend-only mock simulation state

const demoState = {
    status: 'INITIALIZED', // INITIALIZED, RUNNING, PAUSED, STOPPED, COMPLETED
    simulationTime: 0,
    maxTime: 72,
    timeStep: 0, // internal counter
    speedMultiplier: 1, // 1 real sec = 1 sim hour
    intervalId: null,

    config: {
        formulation: 'formulation-a'
    },

    env: {
        temperature: 37.0,
        ph: 7.4,
        ionicStrength: 0.15,
        medium: 'pbs'
    },

    particle: {
        initialSize: 120.0,
        particleSize: 120.0,
        hydrodynamicSize: 128.0,
        pdi: 0.16,
        zetaPotential: -22.0,
        drugRelease: 0.0,
        drugRemaining: 100.0,
        aggregation: false,
        degradation: 0.0,
        dissolution: 0.0
    },
    
    // Configurations mapped for demo
    formulations: {
        'formulation-a': { drug: 'Paclitaxel', material: 'PLGA', size: 120, zeta: -22, load: '8%', coat: 'PEG' },
        'formulation-b': { drug: 'Letrozole', material: 'PLA', size: 145, zeta: -15, load: '5%', coat: 'None' },
        'formulation-c': { drug: 'Letrozole', material: 'PLGA', size: 110, zeta: -28, load: '12%', coat: 'Chitosan' }
    }
};
