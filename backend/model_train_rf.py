"""
model_train_rf.py
Trening Random Forest modela za predikciju rizika zdravlja trudnice.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os


def load_and_prepare_data(csv_path='data/dataset.csv'):
    """Učitava CSV, čisti podatke i priprema za trening."""
    
    df = pd.read_csv(csv_path)
    
    print("="*60)
    print("  KORAK 1: UČITAVANJE I ČIŠĆENJE PODATAKA")
    print("="*60)
    
    print(f"\nOriginal shape: {df.shape}")
    
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
    
    print("\nPopunjavanje numeričkih missing vrijednosti:")
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            missing = df[col].isnull().sum()
            if missing > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                print(f"  {col}: filled {missing} NaN with median={median_val:.2f}")
    
    # 6. Popunjavanje kategorickih NaN sa 0 - Fill categorical NaN with 0
    cat_cols = ['komplikacije_u_proslosti', 'dijabetes', 
                'gestacijski_dijabetes', 'mentalno_zdravlje']
    print("\nPopunjavanje kategorickih missing vrijednosti:")
    for col in cat_cols:
        if col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                df[col] = df[col].fillna(0)
                print(f"  {col}: filled {missing} NaN with 0")
    
    print(f"\nAfter cleaning shape: {df.shape}")
    print(f"Age range: {df['dob'].min()} - {df['dob'].max()}")
    print(f"\nRisk distribution:")
    print(df['nivo_rizika'].value_counts())
    
    return df


def encode_target(y):
    """Enkodira target varijablu (Low/High -> 0/1)."""
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    return y_encoded, le


def train_model():
    """Glavna funkcija za trening i cuvanje Random Forest modela."""
    
    print("\n" + "="*60)
    print("  RANDOM FOREST - TRENING MODELA")
    print("="*60)
    
    # Ucitavanje podataka - Load and prepare data
    df = load_and_prepare_data()
    
    # Definisanje feature-ova i target-a - Define features and target
    feature_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 
                    'komplikacije_u_proslosti', 'dijabetes', 
                    'gestacijski_dijabetes', 'mentalno_zdravlje', 'otkucaji_srca']
    
    print(f"\n📋 Feature-ovi ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols, 1):
        print(f"   {i}. {col}")
    
    X = df[feature_cols]
    y = df['nivo_rizika']
    
    # Enkodiranje targeta - Encode target
    y_encoded, label_encoder = encode_target(y)
    print(f"\n🎯 Target mapping: Low -> 0, High -> 1")
    
    # Podjela na train/test (80/20) - koristi random_state=0 kao u notebooku
    # Split into train/test (80/20) - use random_state=0 as in notebook
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=0, stratify=y_encoded
    )
    
    print(f"\n📊 Podjela podataka:")
    print(f"   Training set: {X_train.shape[0]} rows ({X_train.shape[0]/len(X)*100:.1f}%)")
    print(f"   Test set: {X_test.shape[0]} rows ({X_test.shape[0]/len(X)*100:.1f}%)")
    print(f"\n   Training - Low (0): {sum(y_train == 0)}")
    print(f"   Training - High (1): {sum(y_train == 1)}")
    print(f"   Test - Low (0): {sum(y_test == 0)}")
    print(f"   Test - High (1): {sum(y_test == 1)}")
    
    # Treniranje Random Forest modela - Train Random Forest model
    print("\n🧠 Treniranje Random Forest modela...")
    
    model = RandomForestClassifier(
        n_estimators=100,       # broj stabala (100 je dobar balans)
        max_depth=10,           # maksimalna dubina stabla (sprječava overfitting)
        min_samples_split=5,    # minimalni uzorci za podjelu
        min_samples_leaf=2,     # minimalni uzorci u listu
        max_features='sqrt',    # broj feature-ova za svako stablo
        random_state=42,        # za reprodukciju rezultata
        n_jobs=-1,              # koristi sve dostupne procesore
        verbose=1               # prikazuje progres
    )
    
    model.fit(X_train, y_train)
    
    # Evaluacija - Evaluation
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    print(f"\n{'='*60}")
    print("  REZULTATI EVALUACIJE")
    print('='*60)
    print(f"\n✅ Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"✅ AUC-ROC: {auc:.4f}")
    
    print(f"\n📊 Confusion Matrix:")
    print(f"                 Predicted")
    print(f"               Low      High")
    print(f"   Actual Low    {tn:3d}       {fp:3d}")
    print(f"   Actual High   {fn:3d}       {tp:3d}")
    
    print(f"\n🔢 Detalji:")
    print(f"   True Negatives (Low correctly predicted):   {tn}")
    print(f"   False Positives (Low predicted as High):    {fp}")
    print(f"   False Negatives (High predicted as Low):    {fn}")
    print(f"   True Positives (High correctly predicted):  {tp}")
    
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low', 'High']))
    
    # Feature importance - Važnost feature-ova
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n{'='*60}")
    print("  FEATURE IMPORTANCE (Najvažniji parametri)")
    print('='*60)
    print("\nFeature                    Importance  (%)")
    print("-" * 45)
    for _, row in feature_importance.iterrows():
        bar = "█" * int(row['importance'] * 50)
        print(f"   {row['feature']:30s} {row['importance']:.4f}   ({row['importance']*100:.1f}%) {bar}")

    # Cuvanje modela - Save model
    os.makedirs('models', exist_ok=True)
    
    joblib.dump(model, 'models/rf_model.pkl')
    joblib.dump(label_encoder, 'models/label_encoder_rf.pkl')
    joblib.dump(feature_cols, 'models/feature_cols_rf.pkl')
    
    # Kreiraj feedback CSV fajl ako ne postoji
    feedback_csv_path = 'models/feedback_data.csv'
    if not os.path.exists(feedback_csv_path):
        feedback_df = pd.DataFrame(columns=feature_cols + [
            'feedback_risk', 'original_prediction', 'user_confirmation', 'timestamp', 'trained'
        ])
        feedback_df.to_csv(feedback_csv_path, index=False)
        print(f"\n✅ Kreiran feedback fajl: {feedback_csv_path}")

    # Sačuvaj verziju modela
    with open('models/model_version.txt', 'w') as f:
        f.write(f"Version: 1.0\n")
        f.write(f"Trained: {pd.Timestamp.now()}\n")
        f.write(f"Samples: {len(X_train) + len(X_test)}\n")

    print(f"\n{'='*60}")
    print("  MODEL SAVED")
    print('='*60)
    print("\nFiles saved in 'models/' directory:")
    print("  - rf_model.pkl          (Random Forest model)")
    print("  - label_encoder_rf.pkl  (Label encoder for target)")
    print("  - feature_cols_rf.pkl   (List of feature names)")
    
    print("\n" + "="*60)
    print("  TRENING ZAVRŠEN USPJEŠNO!")
    print("="*60)
    
    return model, label_encoder, feature_cols, accuracy, auc


if __name__ == '__main__':
    model, encoder, features, acc, auc = train_model()