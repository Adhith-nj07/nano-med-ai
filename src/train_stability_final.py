import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge

def main():
    os.makedirs('models', exist_ok=True)
    df = pd.read_csv('data/processed/stability_combined_engineered.csv')
    df = df.dropna(subset=['Shape', 'Core', 'Size (nm)', 'Medium', 'Coating_Charge', 'Estimated_Ligand_MW', 'Zeta_mV', 'study_id'])

    cat_cols = ['Shape', 'Core', 'Medium', 'Coating_Charge']
    num_cols = ['Log_Size', 'Estimated_Ligand_MW']
    X = df[cat_cols + num_cols]
    y = df['Zeta_mV']
    groups = df['study_id']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )

    pipe = Pipeline([('preprocessor', preprocessor), ('model', Ridge(alpha=10.0, random_state=42))])
    cv = GroupKFold(n_splits=5)
    res = cross_validate(pipe, X, y, groups=groups, cv=cv, scoring=['r2', 'neg_mean_absolute_error', 'neg_root_mean_squared_error'])

    print(f"Final CV R2: {res['test_r2'].mean():.3f}")
    print(f"Final CV MAE: {-res['test_neg_mean_absolute_error'].mean():.2f}")

    pipe.fit(X, y)
    joblib.dump(pipe, 'models/stability_model_final.joblib')
    print('Model saved to models/stability_model_final.joblib')

if __name__ == '__main__':
    main()
