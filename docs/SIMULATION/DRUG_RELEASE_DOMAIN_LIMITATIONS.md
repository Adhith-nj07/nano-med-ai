# Drug Release Domain Limitations

## Current Supported Nanoparticle Domain
The release engine is ONLY scientifically grounded for:
- **Polymers**: PLGA, PLA
- **Drugs**: Paclitaxel (PTX), Letrozole (LTZ)
- **Particle Size**: $\le 1000$ nm spherical particles
- **Validity region**:  - 60\%$ cumulative release. Time points beyond this are explicitly flagged as extrapolation.

Simulating liposomes, metallic nanoparticles, or other drugs is out-of-domain (OOD).
