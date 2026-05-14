"""
model_utils.py
Pomocne funkcije za ucitavanje Random Forest modela i predikciju.
"""

import joblib
import numpy as np
import pandas as pd

_model = None
_label_encoder = None
_feature_cols = None


def load_model_artifacts():
    """Ucitava Random Forest model, label encoder i feature kolone. - load random forest model, label encoder and feature columns."""
    global _model, _label_encoder, _feature_cols
    
    if _model is None:
        _model = joblib.load('models/rf_model.pkl')
        _label_encoder = joblib.load('models/label_encoder_rf.pkl')
        _feature_cols = joblib.load('models/feature_cols_rf.pkl')
    
    return _model, _label_encoder, _feature_cols


def preprocess_input(data_dict):
    """Pretvara input dictionary u DataFrame spreman za predikciju. - Convert input dictionary to DataFrame ready for prediction."""
    
    _, _, feature_cols = load_model_artifacts()
    
    missing = set(feature_cols) - set(data_dict.keys())
    if missing:
        raise ValueError(f"Nedostajuci feature-ovi: {missing}")
    
    input_df = pd.DataFrame([{col: data_dict.get(col) for col in feature_cols}])
    
    # Konverzija temperature (Fahrenheit → Celsius) - Convert temperature (Fahrenheit → Celsius)
    if 'tjelesna_temp' in input_df.columns:
        if input_df['tjelesna_temp'].iloc[0] > 50:
            input_df['tjelesna_temp'] = ((input_df['tjelesna_temp'] - 32) * 5/9).round(2)
    
    for col in feature_cols:
        input_df[col] = pd.to_numeric(input_df[col], errors='coerce')
    
    return input_df


def predict_risk(data_dict):
    """Vraca predikciju rizika za jedan unos. - Return risk prediction for a single input."""
    model, label_encoder, _ = load_model_artifacts()
    
    input_df = preprocess_input(data_dict)
    
    prediction = model.predict(input_df)[0]
    probabilities = model.predict_proba(input_df)[0]
    
    # Label encoder ima: 0=High, 1=Low
    if prediction == 0:
        risk_label = 'High'
        risk_code = 1
    else:
        risk_label = 'Low'
        risk_code = 0
    
    high_prob = probabilities[0]
    low_prob = probabilities[1]
    confidence = float(max(probabilities))
    
    result = {
        'risk_level': risk_label,
        'risk_code': risk_code,
        'confidence': confidence,
        'probabilities': {
            'Low': float(low_prob),
            'High': float(high_prob)
        }
    }
    
    print(f"DEBUG predict_risk: {result}")  # Dodajte ovu liniju za debug
    return result


def predict_batch(data_list):
    """Vraca predikcije za vise unosa."""
    results = []
    for data in data_list:
        try:
            results.append(predict_risk(data))
        except Exception as e:
            results.append({'error': str(e), 'input': data})
    return results


def get_model_info():
    """Vraca informacije o ucitanom modelu. - Return information about the loaded model."""
    model, label_encoder, feature_cols = load_model_artifacts()
    
    return {
        'model_type': 'RandomForestClassifier',
        'n_estimators': model.n_estimators,
        'max_depth': model.max_depth,
        'n_features': len(feature_cols),
        'feature_names': feature_cols,
        'encoder_classes': list(label_encoder.classes_)  # ['High', 'Low']
    }