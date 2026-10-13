# Simulation Architecture

## Concept
The NanoMedAI simulation engine is built as a stateful, time-dependent foundation. It evaluates the interaction between a NanoparticleState and an EnvironmentState over time, generating TransformationEvent records for every change, resulting in a new updated particle state.

## Core Modules
- **StateManager**: Tracks the physical, chemical, and biological attributes of the nanoparticle.
- **EnvironmentManager**: Manages environmental parameters (pH, temperature, ionic strength, buffer).
- **TimeStepper**: Controls the advancement of the simulation.
- **EventRecorder**: Logs every state mutation with its trigger, magnitude, and uncertainty.
- **TransformationEngine**: Connects domain-specific mechanistic models or ML surrogates to evaluate particle evolution.
