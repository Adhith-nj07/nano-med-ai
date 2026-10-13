import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import GroupKFold, cross_validate, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay

def main():
    os.makedirs('models', exist_ok=True)
    os.makedirs('docs/ml/figures', exist_ok=True)

    # 1. Load Data
    df = pd.read_excel('data/raw/cytotoxicity_meta_analysis.xlsx')
    
    # 2. Inspect Class Distribution
    total = len(df)
    toxic_count = (df['Toxicity'] == 'Toxic').sum()
    nontoxic_count = (df['Toxicity'] == 'Nontoxic').sum()
    
    with open('docs/ml/CYTOTOXICITY_CLASS_BALANCE.md', 'w') as f:
        f.write("# Cytotoxicity Class Balance\n\n")
        f.write(f"Total samples: {total}\n")
        f.write(f"Toxic samples: {toxic_count}\n")
        f.write(f"Nontoxic samples: {nontoxic_count}\n")
        f.write(f"Toxic %: {toxic_count / total * 100:.1f}%\n")
        f.write(f"Nontoxic %: {nontoxic_count / total * 100:.1f}%\n")
    
    # 3. Clean and select columns
    df['Toxicity'] = df['Toxicity'].map({'Nontoxic': 0, 'Toxic': 1})
    
    cat_cols = ['Material type', 'Assay', 'Cell name']
    num_cols = ['Core size (nm)', 'Hydro size (nm)', 'Surface charge (mV)', 
                'Surface area (m2/g)', 'Exposure time', 'Mass dose (ug/mL)']
    target_col = 'Toxicity'
    group_col = 'Pubmed ID'

    X = df[cat_cols + num_cols]
    y = df[target_col]
    groups = df[group_col]

    # 4. Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )

    # 5. Models
    lr_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', LogisticRegression(max_iter=1000, random_state=42))
    ])

    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', RandomForestClassifier(random_state=42, n_estimators=100))
    ])

    # 6. Group-Aware Cross-Validation
    cv = GroupKFold(n_splits=5)

    def evaluate_model(pipeline, name):
        scoring = ['accuracy', 'precision', 'recall', 'f1']
        results = cross_validate(pipeline, X, y, groups=groups, cv=cv, scoring=scoring)
        
        acc = results['test_accuracy'].mean()
        prec = results['test_precision'].mean()
        rec = results['test_recall'].mean()
        f1 = results['test_f1'].mean()
        
        print(f"--- {name} ---")
        print(f"Accuracy:  {acc:.3f}")
        print(f"Precision: {prec:.3f}")
        print(f"Recall:    {rec:.3f}")
        print(f"F1:        {f1:.3f}\n")
        return acc, prec, rec, f1

    print("Evaluating Cytotoxicity Models...")
    evaluate_model(lr_pipeline, "Logistic Regression")
    evaluate_model(rf_pipeline, "Random Forest Classifier")

    # 7. Train Final Model and Save
    rf_pipeline.fit(X, y)
    joblib.dump(rf_pipeline, 'models/cytotoxicity_model.joblib')

    # 8. Generate Plots
    # Confusion Matrix (using CV predictions to prevent overfitting illusion)
    y_pred_cv = cross_val_predict(rf_pipeline, X, y, groups=groups, cv=cv)
    cm = confusion_matrix(y, y_pred_cv)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Nontoxic', 'Toxic'])
    
    fig, ax = plt.subplots(figsize=(6, 6))
    disp.plot(ax=ax, cmap='Blues')
    plt.title('Random Forest: Confusion Matrix (Group CV)')
    plt.tight_layout()
    plt.savefig('docs/ml/figures/cytotoxicity_confusion_matrix.png')
    plt.close()

    # Feature Importance
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
    plt.savefig('docs/ml/figures/cytotoxicity_feature_importance.png')
    plt.close()
    
    print("Cytotoxicity training complete. Model and figures saved.")

if __name__ == "__main__":
    main()
