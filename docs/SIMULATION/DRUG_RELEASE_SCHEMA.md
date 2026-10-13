# Canonical Drug Release Schema

Based on the required simulation engine constraints and literature availability, the following canonical schema is defined:

```json
{
  "study_id": "string",
  "formulation_id": "string",
  "core_material": "string",
  "particle_size_nm": "float",
  "drug_name": "string",
  "drug_mw": "float",
  "drug_loading_pct": "float",
  "temperature_c": "float",
  "pH": "float",
  "release_medium": "string",
  "time_h": "float",
  "cumulative_release_pct": "float"
}
```
*Optional fields*: `hydrodynamic_size_nm`, `zeta_potential_mv`, `encapsulation_efficiency_pct`, `ionic_strength_m`.
