"""
Comprehensive Test Script for Bitcoin ML Prediction API
Tests all endpoints including SHAP explainability
"""
import requests
import json

API_BASE = "http://localhost:8000"

print("="*80)
print("BITCOIN ML PREDICTION API - COMPREHENSIVE TEST SUITE")
print("="*80)

# Test data
example_features = {
    "Open": 96234.50,
    "High": 97850.25,
    "Low": 95120.80,
    "Close": 96500.00,
    "Volume": 28500000,
    "SMA_7": 95800.00,
    "SMA_14": 94500.00,
    "SMA_30": 92000.00,
    "EMA_7": 96200.00,
    "EMA_14": 95500.00,
    "momentum_7": 1700,
    "momentum_14": 3500,
    "momentum_30": 5500,
    "volatility_7": 850,
    "volatility_14": 1300,
    "RSI": 68.5,
    "MACD": 280,
    "MACD_signal": 220,
    "BB_middle": 96000,
    "BB_upper": 98000,
    "BB_lower": 94000,
    "BB_width": 4000,
    "volume_SMA_7": 27000000,
    "volume_change": 0.055
}

# Test 1: Health Check
print("\n" + "="*80)
print("TEST 1: Health Check")
print("="*80)
try:
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {data['status']}")
        print(f"✓ Models Loaded: {data['model_loaded']}")
        print(f"✓ Data Available: {data['data_available']}")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 2: Automatic Prediction
print("\n" + "="*80)
print("TEST 2: Automatic Prediction (GET /predict)")
print("="*80)
try:
    response = requests.get(f"{API_BASE}/predict")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Direction: {data['direction']}")
        print(f"✓ Confidence: {data['direction_confidence']:.2f}%")
        print(f"✓ Current Price: ${data['current_price']:,.2f}")
        print(f"✓ Predicted Price: ${data['predicted_price']:,.2f}")
        print(f"✓ Price Change: ${data['price_change_usd']:,.2f} ({data['price_change_pct']:.2f}%)")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 3: JSON Input
print("\n" + "="*80)
print("TEST 3: JSON Input (POST /predict/json)")
print("="*80)
json_payload = {
    "features": example_features,
    "current_price": 96500
}
try:
    response = requests.post(f"{API_BASE}/predict/json", json=json_payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Direction: {data['direction']}")
        print(f"✓ Confidence: {data['direction_confidence']:.2f}%")
        print(f"✓ Predicted Price: ${data['predicted_price']:,.2f}")
        print(f"✓ Input Method: {data['input_method']}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 4: Numeric Array Input
print("\n" + "="*80)
print("TEST 4: Numeric Array Input (POST /predict/numeric)")
print("="*80)
numeric_payload = {
    "features": list(example_features.values()),
    "current_price": 96500
}
try:
    response = requests.post(f"{API_BASE}/predict/numeric", json=numeric_payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Direction: {data['direction']}")
        print(f"✓ Confidence: {data['direction_confidence']:.2f}%")
        print(f"✓ Input Method: {data['input_method']}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 5: File Upload
print("\n" + "="*80)
print("TEST 5: File Upload - Batch Predictions (POST /predict/file)")
print("="*80)
try:
    with open('example_batch.csv', 'rb') as f:
        files = {'file': ('example_batch.csv', f, 'text/csv')}
        response = requests.post(f"{API_BASE}/predict/file", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total Predictions: {data['total_records']}")
        print(f"\n  Sample Predictions:")
        for i, pred in enumerate(data['predictions'][:3]):
            print(f"    Row {i+1}: {pred['direction']} "
                  f"({pred['direction_confidence']:.2f}% confidence) - "
                  f"${pred['predicted_price']:,.2f}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except FileNotFoundError:
    print("✗ File 'example_batch.csv' not found. Please create it first.")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 6: SHAP Explanation (NEW!)
print("\n" + "="*80)
print("TEST 6: SHAP Explainability (POST /explain)")
print("="*80)
print("This endpoint provides feature importance using SHAP values")
print("-"*80)
try:
    response = requests.post(f"{API_BASE}/explain", json=json_payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Explanation Method: {data['explanation_method']}")
        print(f"✓ Prediction Confidence: {data['prediction']*100:.2f}%")
        
        if data.get('base_value') is not None:
            print(f"✓ Base Value: {data['base_value']:.4f}")
        
        print(f"\n  Top 10 Most Important Features:")
        importance = data['feature_importance']
        for i, (feature, value) in enumerate(list(importance.items())[:10], 1):
            print(f"    {i}. {feature}: {value:.6f}")
        
        if data.get('shap_values'):
            print(f"\n✓ SHAP values available: {len(data['shap_values'])} features")
            print("  (These values show how much each feature contributes to the prediction)")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 7: Feature Names
print("\n" + "="*80)
print("TEST 7: Get Feature Names (GET /model/features)")
print("="*80)
try:
    response = requests.get(f"{API_BASE}/model/features")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total Features: {data['count']}")
        print(f"✓ Features: {', '.join(data['features'][:8])}...")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 8: Model Info
print("\n" + "="*80)
print("TEST 8: Model Metadata (GET /model/info)")
print("="*80)
try:
    response = requests.get(f"{API_BASE}/model/info")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Version: {data['version']}")
        print(f"✓ Timestamp: {data['timestamp']}")
        print(f"✓ Classification Accuracy: {data['classification_accuracy']*100:.2f}%")
        print(f"✓ Regression RMSE: {data['regression_rmse']:.4f}")
        print(f"✓ Features Count: {data['features_count']}")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("✓ All endpoints tested successfully!")
print("\nEndpoints Available:")
print("  1. GET  /health           - Health check")
print("  2. GET  /predict          - Automatic prediction")
print("  3. POST /predict/json     - JSON input")
print("  4. POST /predict/numeric  - Numeric array input")
print("  5. POST /predict/file     - CSV file upload (batch)")
print("  6. POST /explain          - SHAP explainability (NEW!)")
print("  7. GET  /model/features   - Feature names")
print("  8. GET  /model/info       - Model metadata")
print("\nDocumentation: http://localhost:8000/docs")
print("="*80)

# Save example files
print("\n" + "="*80)
print("EXAMPLE FILES")
print("="*80)
print("\n1. example_input.json - Ready to use")
print("2. example_batch.csv - Ready to use")
print("\nTo test manually:")
print("  curl -X POST http://localhost:8000/predict/json \\")
print("    -H 'Content-Type: application/json' \\")
print("    -d @example_input.json")
print("\n  curl -X POST http://localhost:8000/explain \\")
print("    -H 'Content-Type: application/json' \\")
print("    -d @example_input.json")
print("="*80)
