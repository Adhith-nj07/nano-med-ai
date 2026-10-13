# Drug Release Model Readiness

## Candidate: Korsmeyer-Peppas Model
Equation: $M_t / M_\infty = k t^n$

### Assumptions
- Applicable to polymeric systems (like PLGA).
- Generally valid only for the first ~60% of fractional release.

### Parameter Identifiability
To fit $k$ (release rate constant) and $n$ (release exponent), the dataset must have multiple time points in the initial burst and swelling phases (t < 24h). The identified datasets contain sufficient sampling resolution.

### ML Hybrid Integration (Level 4)
Because environmental parameters (pH, Temperature) and formulation parameters (Size, Loading) determine $k$ and $n$, an ML model can be trained to predict $k$ and $n$. The simulation engine will then use these predicted constants to solve the Korsmeyer-Peppas equation continuously over time $t$.

### Live Parameter Change
If pH changes at $t=10$, the engine must recalculate $k$ and $n$ for the new state, and integrate the release curve forward from the remaining drug mass. This is mathematically feasible but requires careful state management.
