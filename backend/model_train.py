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

# 1. Data loading and preparation - Učitavanje i priprema podataka
def load_and_prepare_data(csv_path='data/dataset.csv'):
    """Učitava CSV, čisti podatke i priprema za trening."""
    
    df = pd.read_csv(csv_path)
    
    # Print the initial balance - Ispis početnog stanja
    print(f"Original shape: {df.shape}")
    print(f"Missing values:\n{df.isnull().sum()}")
    
    # Delete rows where risk_level is NaN - Brisanje redova gdje je nivo_rizika NaN
    df = df.dropna(subset=['nivo_rizika'])
    
    # Filling numeric NaN values ​​with median - Popunjavanje numeričkih NaN vrijednosti sa medijanom
    numeric_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak', 
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca']
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col].fillna(df[col].median(), inplace=True)
    
    # Filling categorical NaNs with 0 (no complications/diabetes) Popunjavanje kategorickih NaN sa 0 (nema komplikacija/dijabetesa)
    cat_cols = ['komplikacije_u_proslosti', 'dijabetes', 'gestacijski_dijabetes', 'mentalno_zdravlje']
    for col in cat_cols:
        df[col].fillna(0, inplace=True)
    
    # Print after cleaning - Ispis nakon ciscenja
    print(f"After cleaning shape: {df.shape}")
    
    return df


def encode_target(y):
    """Enkodira target varijablu (Low/High -> 0/1)."""
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    return y_encoded, le


def train_model():
    """Glavna funkcija za trening i cuvanje modela."""
    
    # loading data - Ucitavanje podataka
    df = load_and_prepare_data()
    
    # Defining features (x) and target (y) - Definisanje feature-ova (X) i target-a (y)
    feature_cols = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                    'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 
                    'komplikacije_u_proslosti', 'dijabetes', 
                    'gestacijski_dijabetes', 'mentalno_zdravlje', 'otkucaji_srca']
    
    X = df[feature_cols]
    y = df['nivo_rizika']
    
    # Encoding target variable - Enkodiranje targeta
    y_encoded, label_encoder = encode_target(y)
    print(f"\nTarget mapping: {dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))}")
    
    # Division into train/test (80/20) - Podela na train/test (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"\nTrain size: {X_train.shape}")
    print(f"Test size: {X_test.shape}")
    print(f"Train class distribution: {np.bincount(y_train)}")
    print(f"Test class distribution: {np.bincount(y_test)}")
    
    # 2. Training the Gradient Boosting model - Treniranje Gradient Boosting modela
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        verbose=1
    )
    
    print("\nTreniranje modela...")
    model.fit(X_train, y_train)
    
    # 3. Evaluacija modela - Evaluation of the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n=== EVALUACIJA ===")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    print(f"\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance - Važnost feature-ova
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nFEATURE IMPORTANCE:")
    print(feature_importance)
    
    # 4. Cuvanje modela i encodera - Saving the model and encoder    
    os.makedirs('models', exist_ok=True)
    
    joblib.dump(model, 'models/gb_model.pkl')
    joblib.dump(label_encoder, 'models/label_encoder.pkl')
    joblib.dump(feature_cols, 'models/feature_cols.pkl')
    
    print("\nModel i encoder sacuvani u 'models/' direktorijumu.")
    
    return model, label_encoder, feature_cols, accuracy


if __name__ == '__main__':
    train_model()