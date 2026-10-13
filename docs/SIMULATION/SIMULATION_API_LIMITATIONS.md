# Simulation API Limitations

## Domain Restrictions
The API strictly exposes domain violations. Requesting a release simulation for a non-PLGA particle, or a particle $>1000$ nm, generates an `unsupported_domain` warning.

## Extrapolation
The API does not hide mathematical limits. If a simulation steps past the $60\%$ valid release fraction of Korsmeyer-Peppas, the associated events explicitly flag the output uncertainty as `extrapolation`.

## Scientific Scope
- No prediction of protein corona, cellular uptake, or human-body transport.
- No generalized ML parameter prediction. Parameters must be explicitly configured or tied to a validated trajectory.
