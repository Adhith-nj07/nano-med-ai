# Transformation Models

Transformations represent mechanistic or data-driven equations updating the nanoparticle state.

### Active Models
- **ZetaPotentialUpdateModel**: Acts as an ML Surrogate. It dynamically delegates to predict_stability (Ridge Regression). When physical size or environment buffer changes, the ML model recalculates the Zeta Potential and generates a CHARGE_CHANGE event.

### Future Models
- Aggregation, Dissolution, Drug Release, and Protein Corona are strictly architected but currently unimplemented to prevent fabricating unscientific data.
