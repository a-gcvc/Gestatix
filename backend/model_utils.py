"""
model_utils.py
Pomocne funkcije za ucitavanje modela i predikciju.
"""

import joblib
import numpy as np
import pandas as pd

# Globalni objekti (ucitavaju se jednom) - Global objects (loaded once)
_model = None
_label_encoder = None
_feature_cols = None

def load_model_artifacts():
    """Ucitava model, label encoder i feature kolone."""
    global _model, _label_encoder, _feature_cols
    
    if _model is None:
        _model = joblib.load('models/gb_model.pkl')
        _label_encoder = joblib.load('models/label_encoder.pkl')
        _feature_cols = joblib.load('models/feature_cols.pkl')
    
    return _model, _label_encoder, _feature_cols


def preprocess_input(data_dict):
    """
    Pretvara input dictionary u DataFrame spreman za predikciju.
    
    Očekivani kljucevi:
    - dob
    - sistolicki_krvni_tlak
    - dijastolicki_krvni_tlak
    - glukoza_u_krvi
    - tjelesna_temp
    - BMI
    - komplikacije_u_proslosti (0/1)
    - dijabetes (0/1)
    - gestacijski_dijabetes (0/1)
    - mentalno_zdravlje (0/1)
    - otkucaji_srca
    """
    
    _, _, feature_cols = load_model_artifacts()
    
    # Provjera da li svi feature-ovi postoje - Check if all features are present
    missing = set(feature_cols) - set(data_dict.keys())
    if missing:
        raise ValueError(f"Nedostajuci feature-ovi: {missing}")
    
    # Kreiranje DataFrame-a - Creating DataFrame
    input_df = pd.DataFrame([{col: data_dict.get(col) for col in feature_cols}])
    
    # Konverzija u numeric - Convert to numeric
    for col in feature_cols:
        input_df[col] = pd.to_numeric(input_df[col], errors='coerce')
    
    return input_df


def predict_risk(data_dict):
    """
    Vraca predikciju rizika za jedan unos.
    Returns: dict sa risk_label i confidence (ako je moguce)
    """
    model, label_encoder, _ = load_model_artifacts()
    
    input_df = preprocess_input(data_dict)
    
    # Predikcija - Prediction
    prediction = model.predict(input_df)[0]
    probabilities = model.predict_proba(input_df)[0]
    
    risk_label = label_encoder.inverse_transform([prediction])[0]
    confidence = float(max(probabilities))
    
    return {
        'risk_level': risk_label,
        'risk_code': int(prediction),
        'confidence': confidence,
        'probabilities': {
            'Low': float(probabilities[0]),
            'High': float(probabilities[1])
        }
    }