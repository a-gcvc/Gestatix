"""
app.py
Flask API za predikciju rizika trudnoće koristeći Random Forest model i RAG preporuke.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

from model_utils import predict_risk, get_model_info
from rag_chroma import get_relevant_advice_rag, semantic_search, build_semantic_query_bhs

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint za provjeru statusa API-ja."""
    return jsonify({
        'status': 'ok',
        'message': 'Pregnancy Risk Prediction API (Random Forest) is running',
        'model_info': get_model_info()
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint za predikciju rizika i preporuke.
    """
    try:
        data = request.get_json()
        
        # Validacija osnovnih polja
        required_fields = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak',
                           'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca']
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({
                'error': f'Nedostaju polja: {missing}'
            }), 400
        
        # Predikcija rizika koristeci Random Forest
        prediction_result = predict_risk(data)
        
        # Odgovor bez RAG (samo predikcija)
        response = {
            'risk': prediction_result,
            'input_data': data,
            'model_used': 'RandomForestClassifier'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """
    Endpoint za batch predikciju.
    """
    try:
        data_list = request.get_json()
        
        if not isinstance(data_list, list):
            return jsonify({'error': 'Ocekuje se lista unosa'}), 400
        
        from model_utils import predict_batch
        results = predict_batch(data_list)
        
        return jsonify({'results': results}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/rag/search', methods=['POST'])
def rag_search():
    """
    Endpoint za semantičku pretragu baze znanja.
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query:
            return jsonify({'error': 'Query je obavezan'}), 400
        
        results = semantic_search(query, n_results=n_results)
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/predict_with_rag', methods=['POST'])
def predict_with_rag():
    """
    Kombinovani endpoint: predikcija rizika + RAG preporuke iz PDF baze.
    """
    try:
        data = request.get_json()
        
        # 1. Predikcija rizika (Random Forest)
        prediction_result = predict_risk(data)
        
        # 2. RAG preporuke iz vektorske baze
        advice_text = get_relevant_advice_rag(
            query_context=f"Trudnoća sa nivoom rizika {prediction_result['risk_level']}",
            patient_data=data,
            n_results=4
        )
        
        response = {
            'risk': prediction_result,
            'rag_recommendations': advice_text,
            'input_data': data,
            'model_used': 'RandomForestClassifier'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("="*60)
    print("  PREGNANCY RISK PREDICTION API (Random Forest)")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  GET  /health              - Provjera statusa API-ja")
    print("  POST /predict            - Predikcija rizika")
    print("  POST /predict_batch      - Batch predikcija")
    print("  POST /rag/search         - Semantička pretraga baze")
    print("  POST /predict_with_rag   - Predikcija + RAG preporuke")
    print("\n" + "="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)