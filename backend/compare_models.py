"""
compare_models.py
Poređenje Random Forest i Gradient Boosting modela.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

# Učitaj podatke (isti preprocessing kao u treningu) - Load data (same preprocessing as in training)
def load_test_data():
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    
    df = pd.read_csv('data/dataset.csv')
    
    # Isti preprocessing - same preprocessing
    df = df.dropna(subset=['nivo_rizika'])
    df = df[df['dob'] != 325]
    df = df[(df['dob'] >= 15) & (df['dob'] <= 50)]
    
    if 'tjelesna_temp' in df.columns:
        df['tjelesna_temp'] = ((df['tjelesna_temp'] - 32) * 5/9).round(2)
    
    numeric_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak', 
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col].fillna(df[col].median(), inplace=True)
    
    cat_cols = ['komplikacije_u_proslosti', 'dijabetes', 'gestacijski_dijabetes', 'mentalno_zdravlje']
    for col in cat_cols:
        if col in df.columns:
            df[col].fillna(0, inplace=True)
    
    feature_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 
                    'komplikacije_u_proslosti', 'dijabetes', 
                    'gestacijski_dijabetes', 'mentalno_zdravlje', 'otkucaji_srca']
    
    X = df[feature_cols]
    y = df['nivo_rizika']
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    _, X_test, _, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=0, stratify=y_encoded
    )
    
    return X_test, y_test, le


def compare_models():
    """Upoređuje Random Forest i Gradient Boosting."""
    
    print("\n" + "="*70)
    print("  POREĐENJE MODELA: RANDOM FOREST vs GRADIENT BOOSTING")
    print("="*70)
    
    # Učitaj test podatke - Load test data
    X_test, y_test, le = load_test_data()
    
    # Učitaj modele - Load models
    rf_model = joblib.load('models/rf_model.pkl')
    gb_model = joblib.load('models/gb_model.pkl')
    
    # Predikcije - Predictions
    rf_pred = rf_model.predict(X_test)
    gb_pred = gb_model.predict(X_test)
    
    rf_proba = rf_model.predict_proba(X_test)[:, 1]
    gb_proba = gb_model.predict_proba(X_test)[:, 1]
    
    # Metrike - Metrics
    rf_acc = accuracy_score(y_test, rf_pred)
    gb_acc = accuracy_score(y_test, gb_pred)
    
    rf_auc = roc_auc_score(y_test, rf_proba)
    gb_auc = roc_auc_score(y_test, gb_proba)
    
    # Confusion matrices - Confusion matrices
    rf_cm = confusion_matrix(y_test, rf_pred)
    gb_cm = confusion_matrix(y_test, gb_pred)
    
    print("\nREZULTATI NA TEST SKUPU:")
    print("-" * 50)
    print(f"{'Metric':<20} {'Random Forest':<20} {'Gradient Boosting':<20}")
    print("-" * 50)
    print(f"{'Accuracy':<20} {rf_acc:.4f} ({rf_acc*100:.2f}%)      {gb_acc:.4f} ({gb_acc*100:.2f}%)")
    print(f"{'AUC-ROC':<20} {rf_auc:.4f}              {gb_auc:.4f}")
    
    print("\nCONFUSION MATRICES:")
    print("-" * 50)
    print("Random Forest:")
    print(f"   TN={rf_cm[0,0]}, FP={rf_cm[0,1]}, FN={rf_cm[1,0]}, TP={rf_cm[1,1]}")
    print("\nGradient Boosting:")
    print(f"   TN={gb_cm[0,0]}, FP={gb_cm[0,1]}, FN={gb_cm[1,0]}, TP={gb_cm[1,1]}")
    
    print("\nClassification Reports:")
    print("\nRandom Forest:")
    print(classification_report(y_test, rf_pred, target_names=['Low', 'High']))
    print("\nGradient Boosting:")
    print(classification_report(y_test, gb_pred, target_names=['Low', 'High']))
    
    # Feature importance poređenje - Feature importance comparison
    rf_features = pd.DataFrame({
        'feature': ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 
                    'komplikacije_u_proslosti', 'dijabetes', 
                    'gestacijski_dijabetes', 'mentalno_zdravlje', 'otkucaji_srca'],
        'importance_rf': rf_model.feature_importances_
    }).sort_values('importance_rf', ascending=False)
    
    gb_features = pd.DataFrame({
        'feature': ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 
                    'komplikacije_u_proslosti', 'dijabetes', 
                    'gestacijski_dijabetes', 'mentalno_zdravlje', 'otkucaji_srca'],
        'importance_gb': gb_model.feature_importances_
    }).sort_values('importance_gb', ascending=False)
    
    print("\nTOP 5 FEATURE IMPORTANCE:")
    print("-" * 50)
    print("\nRandom Forest:")
    for _, row in rf_features.head().iterrows():
        print(f"   {row['feature']:30s}: {row['importance_rf']:.4f}")
    print("\nGradient Boosting:")
    for _, row in gb_features.head().iterrows():
        print(f"   {row['feature']:30s}: {row['importance_gb']:.4f}")
    
    # Zaključak - Conclusion
    print("\n" + "="*70)
    print("  ZAKLJUČAK")
    print("="*70)
    
    if rf_acc > gb_acc:
        print(f"\nRandom Forest je bolji (Accuracy: {rf_acc:.4f} vs {gb_acc:.4f})")
    elif gb_acc > rf_acc:
        print(f"\nGradient Boosting je bolji (Accuracy: {gb_acc:.4f} vs {rf_acc:.4f})")
    else:
        print(f"\nModeli su podjednako dobri")
    
    print(f"\nPreporuka za dalje:")
    if rf_acc >= gb_acc:
        print("   - Random Forest je brži za treniranje i predikciju")
        print("   - Manje je podložan overfitting-u")
    else:
        print("   - Gradient Boosting daje nešto bolje rezultate")
        print("   - Ali je sporiji za treniranje")


if __name__ == '__main__':
    compare_models()