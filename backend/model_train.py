"""
model_train.py
Trening Gradient Boosting modela za predikciju rizika zdravlja trudnice.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib
import os


def load_and_prepare_data(csv_path='data/dataset.csv'):
    """Učitava CSV, čisti podatke i priprema za trening."""
    
    df = pd.read_csv(csv_path)
    
    print(f"Original shape: {df.shape}")
    
    # 1. Konverzija temperature (Fahrenheit → Celsius) - Conversion: C = (F - 32) * 5/9
    if 'tjelesna_temp' in df.columns:
        df['tjelesna_temp'] = ((df['tjelesna_temp'] - 32) * 5/9).round(2)
        print("Temperature converted from Fahrenheit to Celsius")
    
    # 2. Brisanje redova gdje je nivo_rizika NaN - Delete rows where target is NaN
    before = len(df)
    df = df.dropna(subset=['nivo_rizika'])
    print(f"Removed {before - len(df)} rows with NaN in 'nivo_rizika'")
    
    # 3. Izbacivanje outliera (dob = 325) - Remove outlier (age=325)
    before = len(df)
    df = df[df['dob'] != 325]
    print(f"Removed {before - len(df)} row(s) with dob=325 (outlier)")
    
    # 4. Filtriranje dobi (15-50 godina) - Restrict age to 15-50
    before = len(df)
    df = df[(df['dob'] >= 15) & (df['dob'] <= 50)]
    print(f"Removed {before - len(df)} rows with age <15 or >50")
    
    # 5. Popunjavanje numeričkih NaN sa medijanom - Fill numeric NaN with median
    numeric_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak', 
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            missing = df[col].isnull().sum()
            if missing > 0:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"  {col}: filled {missing} NaN with median={median_val:.2f}")
    
    # 6. Popunjavanje kategorickih NaN sa 0 - Fill categorical NaN with 0
    cat_cols = ['komplikacije_u_proslosti', 'dijabetes', 
                'gestacijski_dijabetes', 'mentalno_zdravlje']
    for col in cat_cols:
        if col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                df[col].fillna(0, inplace=True)
                print(f"  {col}: filled {missing} NaN with 0")
    
    print(f"After cleaning shape: {df.shape}")
    print(f"Age range: {df['dob'].min()} - {df['dob'].max()}")
    print(f"Risk distribution:\n{df['nivo_rizika'].value_counts()}")
    
    return df


def encode_target(y):
    """Enkodira target varijablu (Low/High -> 0/1)."""
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    return y_encoded, le


def train_model():
    """Glavna funkcija za trening i cuvanje modela."""
    
    # Ucitavanje podataka - Load and prepare data
    df = load_and_prepare_data()
    
    # Definisanje feature-ova i target-a - Define features and target
    feature_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 
                    'komplikacije_u_proslosti', 'dijabetes', 
                    'gestacijski_dijabetes', 'mentalno_zdravlje', 'otkucaji_srca']
    
    X = df[feature_cols]
    y = df['nivo_rizika']
    
    # Enkodiranje targeta - Encode target
    y_encoded, label_encoder = encode_target(y)
    print(f"\nTarget mapping: {dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))}")
    
    # Podjela na train/test (80/20) - koristi random_state=0 kao u notebooku - Split into train/test (80/20) - use random_state=0 as in notebook
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=0, stratify=y_encoded
    )
    
    print(f"\nTrain size: {X_train.shape[0]} rows")
    print(f"Test size: {X_test.shape[0]} rows")
    print(f"Train class distribution (0=Low, 1=High): {np.bincount(y_train)}")
    print(f"Test class distribution: {np.bincount(y_test)}")
    
    # Treniranje Gradient Boosting modela - Train Gradient Boosting model
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        verbose=1
    )
    
    print("\nTraining Gradient Boosting model...")
    model.fit(X_train, y_train)
    
    # Evaluacija - Evaluation
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n{'='*50}")
    print("MODEL EVALUATION")
    print(f"{'='*50}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    print(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    print(f"\n  True Negatives (Low): {cm[0,0]}")
    print(f"  False Positives: {cm[0,1]}")
    print(f"  False Negatives: {cm[1,0]}")
    print(f"  True Positives (High): {cm[1,1]}")
    
    # Feature importance - Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n{'='*50}")
    print("FEATURE IMPORTANCE")
    print(f"{'='*50}")
    for _, row in feature_importance.iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f} ({row['importance']*100:.1f}%)")
    
    # Cuvanje modela - Save model
    os.makedirs('models', exist_ok=True)
    
    joblib.dump(model, 'models/gb_model.pkl')
    joblib.dump(label_encoder, 'models/label_encoder.pkl')
    joblib.dump(feature_cols, 'models/feature_cols.pkl')
    
    print(f"\n{'='*50}")
    print("MODEL SAVED")
    print(f"{'='*50}")
    print("Files saved in 'models/' directory:")
    print("  - gb_model.pkl")
    print("  - label_encoder.pkl")
    print("  - feature_cols.pkl")
    
    return model, label_encoder, feature_cols, accuracy


if __name__ == '__main__':
    train_model()