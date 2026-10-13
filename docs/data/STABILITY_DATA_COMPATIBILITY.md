# Stability Data Compatibility Audit

## Original (69 rows)
- Target: Zeta (mV)
- Columns: ['metal core', 'Coating', 'Type of Coating \n(Anionic, Cationic, Neutral)', 'Ageing', 'Diameter  (TEM-STEM)', 'Shape group', 'Geometric Surface Area (nm2)', 'Corresponding sphere diameter (nm)', 'Atomic radius', 'Ionic radius'] ...

## Candidate 7 (198 rows, Millipore pH 7)
- Columns: ['Index', 'Zeta potential in water (mv)', 'Standard deviation (n = 3)', 'Experimental protocol', 'Shape', 'Core', 'Size (nm)', '#Ligand1', 'Ligand1 SMILES', '#Ligand2', 'Ligand2 SMILES', 'Reference', 'DOI']

## Candidate 1 (90 rows, Phosphate buffer pH 7.4)
- Columns: ['Index', 'Zeta potential in PBS (mv)', 'Standard deviation (n = 3)', 'Experimental protocol', 'Shape', 'Core', 'Size (nm)', '#Ligand1', 'Ligand1 SMILES', '#Ligand2', 'Ligand2 SMILES', 'Reference', 'DOI']

## Conclusion
- Both candidate datasets are highly compatible with the original dataset but are MUCH better structured for ML.
- **Target**: Zeta potential in water (mv) and Zeta potential in PBS (mv) are directly comparable to Zeta (mV) from the original (though measured in slightly different media, PBS vs Millipore vs unknown in original, we can use Medium as a new feature or just accept the variance).
- **Features**: Core -> metal core, Shape -> Shape group, Size (nm) -> Diameter  (TEM-STEM).
- **Coating**: The new datasets use explicit Ligand1 SMILES instead of vague string categories like PVP 40k. This is a huge improvement, but we might not have SMILES for the original dataset. However, because the original is so small (N=69), and the two new datasets combined provide 288 records WITH DOI and Reference (study identifiers), the best scientific decision is to **REPLACE** the original 69-row dataset with the combined 288-row dataset. Mixing them without SMILES in the original might just introduce missing data.
- **Study Identifiers**: The new datasets provide DOI and Reference, enabling GroupKFold validation to prevent study-level data leakage, which was a fatal flaw in the original N=69 evaluation.
- **Decision**: ACCEPT both Candidate 7 (198 rows) and Candidate 1 (90 rows) to form a unified 288-row experimental dataset. REJECT the original 69-row dataset as it lacks study identifiers and SMILES strings, making it scientifically incompatible for a rigorous study-aware ML pipeline.
