# Stability Feature Engineering

## 1. Coating Charge Extraction
- **Reason**: One-Hot Encoding exact SMILES strings failed because studies use unique ligands. We must generalize the coating.
- **Method**: Parsed SMILES for explicit formal charges ([O-], [N+]) to classify coatings as Anionic, Cationic, Zwitterionic, or Neutral.
- **Distribution**:
  - Neutral: 205
  - Cationic: 52
  - Zwitterionic: 22
  - Anionic: 9
## 2. Size Transformation
- **Reason**: Particle size spans orders of magnitude.
- **Method**: log1p(Size (nm))

## Expected vs Actual Effect
- **Expected Effect**: R2 should increase significantly because Coating Charge is generalizable across studies.
- **Actual Effect**: RF R2 = -0.192, MAE = 21.39

## 3. Estimated Molecular Weight
- **Reason**: Differentiate between small electrostatic stabilizers and large steric polymers.
- **Method**: Heuristic atom counting from SMILES (C, O, N, S, P).
- **Actual Effect**: Marginal improvement in Ridge (0.092 -> 0.093). RF remains negative.

## Conclusion
- We have reached the limits of the features available in public databases without introducing data leakage. The true cross-laboratory R2 for Zeta Potential using basic structural features is ~0.10. We will proceed with Ridge Regression using Shape, Core, Medium, Coating_Charge, Log_Size, Estimated_Ligand_MW.
