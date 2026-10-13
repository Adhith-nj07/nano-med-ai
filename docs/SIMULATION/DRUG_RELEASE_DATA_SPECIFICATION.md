# Drug Release Data Specification

## Ideal Dataset Structure
To transition NanoMedAI to Phase S4 (Dynamic Mechanistic Simulation), a longitudinal dataset is required.

### 1. Nanoparticle Information
- **formulation_id**: Unique identifier for the specific particle.
- **core_material**: Material (e.g., PLGA, Liposome).
- **particle_size_nm**: Initial size.

### 2. Drug Information
- **drug_name**: Name of encapsulated API.
- **drug_mw**: Molecular weight of the drug.
- **drug_loading_pct**: Mass percentage of drug.

### 3. Experimental Environment
- **temperature_c**: Incubation temperature.
- **pH**: Acidity of the release medium.
- **release_medium**: Solvent / buffer used (e.g., PBS).

### 4. Time
- **time_h**: Time elapsed since initiation of the release study.

### 5. Target
- **cumulative_release_pct**: Percentage of encapsulated drug released by `time_h`.
