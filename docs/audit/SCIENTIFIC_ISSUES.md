# Scientific Issues

| ID | Issue | Severity | Evidence | Why It Matters | Recommendation |
|---|---|---|---|---|---|
| S-001 | Undefined Stability thresholds | CRITICAL | No quantitative definition of High/Medium/Low stability in code or docs. | Cannot map real continuous data (like Zeta potential or size change) to categories defensibly. | Define literature-backed thresholds (e.g. Zeta potential > 30mV or < -30mV = High). REQUIRES LITERATURE VERIFICATION. |
| S-002 | Undefined Reactivity endpoint | CRITICAL | Reactivity is vaguely defined as biological response in `nanomedai.html`. | Toxicity has many distinct assays (ROS, IC50, viability). Mixing them blindly invalidates the model. | Identify one specific assay to represent Reactivity, and define thresholds for High/Moderate/Low. REQUIRES LITERATURE VERIFICATION. |
| S-003 | Size definition ambiguity | HIGH | Model expects `Size_nm`, but doesn't specify if it's core size (TEM) or hydrodynamic size (DLS). | Real datasets report both; they are physically different and cannot be mixed silently. | Specify which size measurement the model accepts and enforce it during data harmonization. |
| S-004 | Categorical mapping ambiguity | HIGH | Coating and Material lists are specific (e.g., "PEG", "Gold"). | Real datasets contain complex variations (e.g., "PEG-5000", "AuNR"). Naive string matching will fail. | Establish clear rules for binning real-world material/coating variants into the allowed categories. |
