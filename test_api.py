#!/usr/bin/env python
"""Test script for the pregnancy risk API"""

import requests
import json

API_BASE = 'http://127.0.0.1:5000'

# Test data - valid patient data
test_data = {
    'dob': 28,
    'sistolicki_krvni_tlak': 120,
    'dijastolicki_krvni_tlak': 80,
    'glukoza_u_krvi': 5.2,
    'tjelesna_temp': 36.6,
    'BMI': 22.5,
    'otkucaji_srca': 75,
    'komplikacije_u_proslosti': 0,
    'dijabetes': 0,
    'gestacijski_dijabetes': 0,
    'mentalno_zdravlje': 0
}

print("="*60)
print("Testing Pregnancy Risk Prediction API")
print("="*60)

# Test 1: Health check
print("\n[1] Testing /health endpoint...")
try:
    response = requests.get(f'{API_BASE}/health', timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Predict endpoint
print("\n[2] Testing /predict endpoint...")
try:
    response = requests.post(
        f'{API_BASE}/predict',
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Predict with RAG endpoint
print("\n[3] Testing /predict_with_rag endpoint...")
try:
    response = requests.post(
        f'{API_BASE}/predict_with_rag',
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=15
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")  # First 500 chars
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
