# UI Requirements

## Overall Architecture
The UI will be a single-page HTML application (`index.html` + `style.css` + `script.js` or combined into one simple file if it remains small). It will strictly separate presentation logic from prediction logic. The actual model inference will occur in a separate prediction layer.

## Pages / Views

### 1. Dashboard (Home)
- **Content:** Title ("NanoMedAI - Machine Learning for Nanoparticle Analysis"), brief description of the academic MVP scope.
- **Actions:** Buttons to navigate to "Stability Prediction" and "Cytotoxicity Prediction".

### 2. Stability Prediction View
- **Description:** Form for inputting nanoparticle physicochemical properties to predict Zeta Potential.
- **Inputs:** Dynamic based on final `STABILITY_SCHEMA.md` (e.g., Material, Size, Coating, pH).
- **Outputs:** Predicted Zeta Potential (mV) (Regression output).
- **Model Information:** Name of the model used (e.g., Random Forest Regressor), MAE/RMSE/R² metrics obtained during testing, and feature importance (if applicable).

### 3. Cytotoxicity Prediction View
- **Description:** Form for inputting nanoparticle properties and assay conditions to predict toxicity.
- **Inputs:** Dynamic based on final `CYTOTOXICITY_SCHEMA.md` (e.g., Material, Size, Coating, Dose, Exposure Time, Cell Line).
- **Outputs:** Cytotoxicity Class (e.g., Toxic / Non-Toxic) or Viability %, depending on final schema.
- **Model Information:** Name of the model used, Accuracy/F1-score, and any data limitations (e.g., applicable only to specific cell lines).

## UI State Considerations

### Validation Requirements
- All numeric inputs must have `min` and `max` constraints corresponding directly to the ranges in the training dataset.
- Categorical inputs must use dropdowns (`<select>`) populated exclusively with the exact categories present in the training data (after harmonization).
- Prevent prediction submission if any required field is empty or out of bounds.

### Error States
- Display clear, inline error messages if input values exceed the model's valid boundaries.
- If the prediction function fails (e.g., due to an unexpected input type), show a user-friendly error alert without breaking the UI.

### Loading States
- While the prediction is running, the "Predict" button should show a spinner or a "Calculating..." state and become disabled to prevent double submissions.
- (Even if the browser-side inference is nearly instantaneous, providing visual feedback confirms the action).

## Future Extensibility Considerations
- **Navigation:** The navigation bar should be designed to easily add future tabs (e.g., "Drug Release", "Cellular Uptake") without redesigning the layout.
- **Modularity:** The prediction views should be encapsulated so that future developers can swap out the simple client-side model logic for an API fetch call to a backend server (e.g., FastAPI) without rewriting the DOM manipulation code.
- **Clean Separation:** Do not hard-code model weights or JSON blobs directly into the HTML structure. They should be loaded dynamically via JS or an external file, preserving the boundary between DATA/MODEL and UI.

*(Note: The actual UI implementation will NOT begin until the dataset is downloaded and the ML feature schemas are definitively locked in).*
