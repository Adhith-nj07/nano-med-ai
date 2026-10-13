# Scientific Feasibility Audit

## A. What NanoMedAI can scientifically simulate TODAY
NanoMedAI can currently perform **static state re-evaluations (snapshot updates)**. Specifically, if the environmental buffer is changed (e.g., Water to PBS), the platform can utilize the existing ML surrogate (Ridge Regression) to calculate the corresponding shift in Zeta Potential. This is technically an instantaneous event response rather than a continuous mechanistic simulation.

## B. What NanoMedAI can predict TODAY
- **Zeta Potential (mV)**: Using structural features (Core, Shape, Size) and environment (Medium), along with SMILES-derived proxies.
- **Cytotoxicity (Toxic/Nontoxic)**: Using physical features and experimental setup (Cell name, Assay, Exposure time, Mass dose).

## C. What cannot currently be simulated
True **time-dependent mechanistic evolution** cannot be simulated. Phenomena such as:
- Aggregation / Agglomeration
- Dissolution / Degradation
- Drug Release
- Protein Corona formation
These require longitudinal (time-series) data mapping the progression of a *single* nanoparticle sample across time intervals ($t=0, t=1, t=4...$). The current repository contains exclusively static, endpoint measurements.

## D. What data is missing
To perform genuine nanomedicine simulation, we require **longitudinal time-series datasets**. 
Specifically:
- Time-resolved drug release profiles (Cumulative release % vs. Time under varying pH/Temperature).
- Time-resolved dynamic light scattering (DLS) data showing hydrodynamic size change over time in varying ionic strengths (for aggregation models).

## E. Recommended next mechanism
**Drug Release** is the most scientifically defensible and valuable next step. It is well-represented in literature by established empirical models (Higuchi, Korsmeyer-Peppas) and directly links nanoparticle formulation to therapeutic efficacy, bridging the physical and biological domains.

## F. Required dataset for that mechanism
A comprehensive *in vitro* drug release dataset detailing:
- Inputs: Core material, coating, drug MW, drug loading %, temperature, pH.
- Target: Cumulative drug release (%).
- Structure: Repeated measurements of the same sample at $t=1, 2, 4, 8, 24, 48, 72$ hours.

## G. Model recommendation
For Drug Release, the **Korsmeyer-Peppas model** ($M_t/M_\infty = kt^n$) or a hybrid **Mechanistic + ML (Level 4)** approach. The ML model would predict the kinetic rate constant ($k$) and transport exponent ($n$) based on particle features, and the simulation engine would use these parameters to generate the continuous time-series trajectory.

## H. Validation strategy
Future simulation mechanisms must be validated against unseen longitudinal profiles using **Time-Series Error metrics** (e.g., Dynamic Trajectory Similarity, time-integrated RMSE) rather than simple static classification accuracy.

## I. Research limitations
The current framework explicitly prevents fabricating continuous variables from static snapshots. Any correlation inferred from the static Zeta Potential model cannot scientifically predict continuous degradation rates without temporal data.
