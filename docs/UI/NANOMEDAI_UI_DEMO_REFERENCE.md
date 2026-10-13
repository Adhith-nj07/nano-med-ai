# NanoMedAI UI Demo Reference

## 1. Design Objective
The NanoMedAI UI Demo is a standalone, purely visual frontend prototype. Its primary objective is to facilitate design exploration and UX evaluation for the upcoming NanoMedAI platform. It contains absolutely zero connections to the backend ML models, APIs, or real datasets. All results and interactions are illustrative placeholders intended to demonstrate layout, visual hierarchy, and information density.

## 2. Concept 1: Scientific Research Lab
**Theme**: Academic, clean, data-focused, minimalistic.
**Typography**: Serif headers (Merriweather) with clean sans-serif body (Inter).
**Colors**:
- Primary: Navy Blue (`#1a365d`)
- Secondary: Slate (`#64748b`)
- Background: Pure White (`#ffffff`)
- Surface: Very Light Gray (`#f8fafc`)
**Layout**: High density, sharp corners, distinct table borders, emphasis on textual and numerical data rather than visual flair.

## 3. Concept 2: Modern Scientific Platform
**Theme**: Modern, elegant, SaaS-inspired.
**Typography**: Modern sans-serif throughout (Roboto or SF Pro).
**Colors**:
- Primary: Scientific Teal (`#0d9488`)
- Secondary: Soft Blue (`#3b82f6`)
- Background: Off-white (`#f1f5f9`)
- Surface: White (`#ffffff`) with subtle shadows
**Layout**: Card-based, generous padding, rounded corners, clear visual hierarchy, soft transitions.

## 4. Concept 3: Computational Research Lab
**Theme**: Technical, dense, model-centric, workstation environment (Dark Mode).
**Typography**: Monospace accents (Fira Code) with crisp sans-serif (Inter).
**Colors**:
- Primary: Neon Blue (`#38bdf8`)
- Secondary: Purple (`#c084fc`)
- Background: Deep Dark (`#0f172a`)
- Surface: Dark Gray (`#1e293b`)
- Text: Light Gray (`#cbd5e1`)
**Layout**: High contrast, dense panels, glowing accents, dashboard feel suitable for extended viewing in a lab environment.

## 5. Screen Descriptions
- **Overview**: Dashboard showing available mock models, illustrative metrics, and system status.
- **Zeta Potential**: Interactive form for nanoparticle parameters (Material, Size, Shape, Ligand, Coating) leading to a mock Zeta Potential prediction with an illustrative scale.
- **Cytotoxicity**: Form specifically tailored for toxicity prediction (includes Dose, Exposure Time, Cell Line), yielding a mock classification result.
- **Models**: Detailed tabular view of model architectures (e.g., Ridge Regression, Random Forest), validation methodology, and training set sizes (all placeholders).
- **Research / About**: Explains the platform's focus, separating current tools from future research concepts (e.g., Nano Digital Twin, Protein Corona).

## 6. Component Inventory
- **Concept Selector**: Dropdown or segmented control to switch visual themes dynamically.
- **Navigation Sidebar**: Persistent left-hand menu.
- **Input Cards**: Forms with labels, numerical inputs, and dropdowns.
- **Result Panels**: High-hierarchy displays for prediction outputs.
- **Confidence/Importance Bars**: Illustrative progress bars showing feature importance.
- **Badges**: Small labels for "DEMO MODE", "Available", "Future Concept".
- **Action Buttons**: Primary and secondary buttons.

## 7. Navigation Structure
```text
┌─────────────────────────────┐
│ NanoMedAI                   │
│                             │
│ Overview                    │
│ Zeta Potential              │
│ Cytotoxicity                │
│ Models                      │
│ Research                    │
│                             │
│ ─────────────────────────── │
│                             │
│ DEMO MODE                   │
└─────────────────────────────┘
```

## 8. Color Palettes
Detailed in Concepts 1-3. Managed via CSS variables (`--bg-color`, `--surface-color`, `--text-primary`, `--accent-color`).

## 9. Typography
- Standard Sans: `Inter, system-ui, sans-serif`
- Standard Serif: `Merriweather, Georgia, serif`
- Standard Mono: `Fira Code, Consolas, monospace`

## 10. Interaction States
- **Empty State**: Forms waiting for input.
- **Loading State**: Simulated 1.5s delay showing "Analyzing nanoparticle..."
- **Result State**: Displaying static mock result + feature importance chart.
- **Theme Switching**: Instant application of new CSS variables.

## 11. Future UI Considerations
- Implementing actual SHAP value visualization (currently mocked).
- Connecting to `src/predict.py` via an API layer.
- User authentication and prediction history tracking.
- Interactive 3D molecular viewers (currently outside demo scope).
