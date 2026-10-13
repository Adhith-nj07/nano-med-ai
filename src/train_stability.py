import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold, cross_validate, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def main():
    os.makedirs('models', exist_ok=True)
    os.makedirs('docs/ml/figures', exist_ok=True)

    # 1. Load Data
    df = pd.read_excel('data/raw/zeta_potential_69_enms.xlsx')
    
    # 2. Clean and select columns
    # Rename complex columns for ease of use
    df = df.rename(columns={
        'Type of Coating \n(Anionic, Cationic, Neutral)': 'Coating_Charge',
        'Diameter  (TEM-STEM)': 'Diameter_nm',
        'Geometric Surface Area (nm2)': 'Surface_Area_nm2',
        'Zeta (mV)': 'Zeta_mV'
    })
    
    # Normalize inconsistent capitalization
    df['Shape group'] = df['Shape group'].str.lower()

    cat_cols = ['metal core', 'Coating', 'Coating_Charge', 'Ageing', 'Shape group']
    num_cols = ['Diameter_nm', 'Surface_Area_nm2']
    target_col = 'Zeta_mV'

    X = df[cat_cols + num_cols]
    y = df[target_col]

    # 3. Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )

    # 4. Models
    lr_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', LinearRegression())
    ])

    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(random_state=42, n_estimators=100))
    ])

    # 5. Cross-Validation Strategy
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    def evaluate_model(pipeline, name):
        scoring = ['neg_mean_absolute_error', 'neg_root_mean_squared_error', 'r2']
        results = cross_validate(pipeline, X, y, cv=cv, scoring=scoring)
        
        mae = -results['test_neg_mean_absolute_error'].mean()
        rmse = -results['test_neg_root_mean_squared_error'].mean()
        r2 = results['test_r2'].mean()
        
        print(f"--- {name} ---")
        print(f"MAE:  {mae:.2f}")
        print(f"RMSE: {rmse:.2f}")
        print(f"R²:   {r2:.2f}\n")
        return mae, rmse, r2

    print("Evaluating Stability Models...")
    evaluate_model(lr_pipeline, "Linear Regression")
    evaluate_model(rf_pipeline, "Random Forest Regressor")

    # 6. Train Final Model and Save
    rf_pipeline.fit(X, y)
    joblib.dump(rf_pipeline, 'models/stability_model.joblib')

    # 7. Generate Plots
    # True vs Predicted (using CV predictions for a realistic spread)
    y_pred_cv = cross_val_predict(rf_pipeline, X, y, cv=cv)
    
    plt.figure(figsize=(6, 6))
    plt.scatter(y, y_pred_cv, alpha=0.7)
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
    plt.xlabel('Actual Zeta Potential (mV)')
    plt.ylabel('Predicted Zeta Potential (mV)')
    plt.title('Random Forest: Actual vs Predicted (CV)')
    plt.tight_layout()
    plt.savefig('docs/ml/figures/stability_actual_vs_predicted.png')
    plt.close()

    # Feature Importance
    # Extract feature names from OHE
    ohe = rf_pipeline.named_steps['preprocessor'].named_transformers_['cat']
    cat_feature_names = ohe.get_feature_names_out(cat_cols)
    feature_names = num_cols + list(cat_feature_names)
    
    importances = rf_pipeline.named_steps['model'].feature_importances_
    
    # Sort and plot top 15
    indices = np.argsort(importances)[-15:]
    plt.figure(figsize=(10, 6))
    plt.barh(range(len(indices)), importances[indices], align='center')
    plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
    plt.xlabel('Relative Importance')
    plt.title('Top 15 Feature Importances (Random Forest)')
    plt.tight_layout()
    plt.savefig('docs/ml/figures/stability_feature_importance.png')
    plt.close()
    
    print("Stability training complete. Model and figures saved.")

if __name__ == "__main__":
    main()
