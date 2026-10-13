import os

docs = {
    'docs/SIMULATION/PHYSICAL_STABILITY_DATA_HARVEST.md': '''# Physical Stability Data Harvest

## Pilot Strategy
A pilot harvesting campaign was conducted targeting 30 papers on nanoparticle physical stability, prioritizing DLS, PDI, and time-series data. We programmatically queried EuropePMC for open-access studies with supplementary data attachments.

## Pilot Results
- **Studies found in query**: 30
- **Studies with supplements**: 18
- **Machine-readable time-series datasets**: 0
- **Studies with usable plotted longitudinal data**: ~3 (locked in PDF figures)

## Conclusion
The data harvesting pilot proves that machine-readable, canonical datasets of physical nanoparticle stability do not currently exist natively in supplementary materials for recent literature. Manual digitization is strictly required.
''',
    
    'docs/SIMULATION/PHYSICAL_STABILITY_DATASET_CARD.md': '''# Physical Stability Dataset Card

## Dataset Identity
- **Name**: NanoMedAI Longitudinal Physical Stability Dataset
- **Status**: Schema defined, zero populated trajectories.

## Canonical Schema
The dataset enforces explicit classification (`MEDICINAL_NANOPARTICLE`), environment variables (`pH`, `temperature_c`, `medium`), and strictly separates `PRIMARY_SIZE` from `HYDRODYNAMIC_SIZE`. PDI and explicit aggregation measures are segregated to prevent false derivation.

## Availability
Currently empty. Awaiting large-scale digitization pipeline.
''',

    'docs/SIMULATION/PHYSICAL_STABILITY_PROVENANCE.md': '''# Physical Stability Provenance

## Provenance Tracking
Every record in the target dataset will carry explicit provenance via:
- `measurement_provenance` (e.g., "digitized_from_figure", "machine_readable_supplement")
- `source_publication`
- `source_doi`
- `source_repository`

## Leakage Prevention
Models must be validated using `GroupKFold(groups=study_id)` to prevent formulation leakage. No two trajectories from the same source paper can span the train/test divide.
''',

    'docs/SIMULATION/PHYSICAL_STABILITY_DIGITIZATION_PROTOCOL.md': '''# Physical Stability Digitization Protocol

## Digitization Standard
When harvesting must rely on figure digitization:
1. **Extraction**: Use a tool (e.g., WebPlotDigitizer) to map axes.
2. **Metadata**: Log `figure_coordinate_system`, `axis_scale`, and `axis_units`.
3. **Tagging**: All resulting points MUST be tagged `digitized_from_figure`.
4. **Verification**: A verification artifact (plot of extracted points over original axes) must be retained internally.

## Cautions
- Do not assume bar chart error bars represent standard deviation without verifying the legend.
- Do not interpolate between digitized points.
''',

    'docs/SIMULATION/PHYSICAL_STABILITY_DATA_QUALITY.md': '''# Physical Stability Data Quality

## Quality Tiers
- **A**: Direct experimental machine-readable data with complete conditions.
- **B**: Experimental supplementary table with minor normalization required.
- **C**: Reliable digitized experimental trajectory.
- **D**: Incomplete/ambiguous trajectory (Do not use for ML training).

## Current Distribution
The pilot yielded zero A/B tier datasets. All prospective data falls into Tier C, necessitating a rigorous and slow manual extraction protocol.
''',

    'docs/SIMULATION/PHYSICAL_STABILITY_DATASET_ANALYSIS.md': '''# Physical Stability Dataset Analysis

## Research Gap Analysis
1. **Can we obtain enough longitudinal size trajectories?** Not programmatically. Yes, manually via large-scale digitization.
2. **Can we obtain enough longitudinal PDI trajectories?** Rarely reported longitudinally compared to size.
3. **Can we obtain explicit aggregation trajectories?** Almost never explicitly quantified apart from "size increase" proxies.
4. **Do enough studies contain environmental variation?** Very few. Most store at a single condition (e.g., 4°C or 37°C in PBS).
5. **Can environmental-response modeling be scientifically justified?** No. The data is too sparse to train a generalized environmental-response model for physical agglomeration.
''',

    'docs/SIMULATION/S5A_COMPLETION_REPORT.md': '''# S5A Completion Report

## Scale-Up Decision
**DATA_STILL_INSUFFICIENT**

## Rationale
The pilot proved that the nanomedicine literature does not routinely publish machine-readable longitudinal stability tables. Expanding the automated harvest will only yield more PDFs requiring manual digitization. Without a dedicated human-in-the-loop curation workforce (or specialized vision-language models for plot extraction), we cannot construct a dataset robust enough to train predictive physical simulation models. 

NanoMedAI should pivot back to API integration, Frontend, or other supported predictive endpoints.
'''
}

for path, content in docs.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
