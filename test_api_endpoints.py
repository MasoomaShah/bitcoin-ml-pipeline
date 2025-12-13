"""
Test script for the new prediction API endpoints
"""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 60)
print("Testing Bitcoin ML Prediction API Endpoints")
print("=" * 60)

# Test 1: Automatic prediction (original endpoint)
print("\n1. Testing Automatic Prediction (GET /predict)")
print("-" * 60)
try:
    response = requests.get(f"{API_BASE}/predict")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Direction: {data['direction']}")
        print(f"✓ Confidence: {data['direction_confidence']:.2f}%")
        print(f"✓ Current Price: ${data['current_price']:.2f}")
        print(f"✓ Predicted Price: ${data['predicted_price']:.2f}")
        print(f"✓ Input Method: {data.get('input_method', 'N/A')}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: JSON input with custom features
print("\n2. Testing JSON Input (POST /predict/json)")
print("-" * 60)
json_data = {
    "features": {
        "Open": 95000,
        "High": 96500,
        "Low": 94500,
        "Close": 95500,
        "Volume": 25000000,
        "SMA_7": 94500,
        "SMA_14": 93000,
        "SMA_30": 91000,
        "EMA_7": 95000,
        "EMA_14": 94000,
        "momentum_7": 1500,
        "momentum_14": 3000,
        "momentum_30": 5000,
        "volatility_7": 800,
        "volatility_14": 1200,
        "RSI": 65.5,
        "MACD": 250,
        "MACD_signal": 200,
        "BB_middle": 95000,
        "BB_upper": 97000,
        "BB_lower": 93000,
        "BB_width": 4000,
        "volume_SMA_7": 24000000,
        "volume_change": 0.05
    },
    "current_price": 95500
}

try:
    response = requests.post(f"{API_BASE}/predict/json", json=json_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Direction: {data['direction']}")
        print(f"✓ Confidence: {data['direction_confidence']:.2f}%")
        print(f"✓ Current Price: ${data['current_price']:.2f}")
        print(f"✓ Predicted Price: ${data['predicted_price']:.2f}")
        print(f"✓ Input Method: {data.get('input_method', 'N/A')}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Numeric array input
print("\n3. Testing Numeric Array Input (POST /predict/numeric)")
print("-" * 60)
numeric_data = {
    "features": [
        95000, 96500, 94500, 95500, 25000000,  # Open, High, Low, Close, Volume
        94500, 93000, 91000,  # SMA_7, SMA_14, SMA_30
        95000, 94000,  # EMA_7, EMA_14
        1500, 3000, 5000,  # momentum_7, momentum_14, momentum_30
        800, 1200,  # volatility_7, volatility_14
        65.5, 250, 200,  # RSI, MACD, MACD_signal
        95000, 97000, 93000, 4000,  # BB_middle, BB_upper, BB_lower, BB_width
        24000000, 0.05  # volume_SMA_7, volume_change
    ],
    "current_price": 95500
}

try:
    response = requests.post(f"{API_BASE}/predict/numeric", json=numeric_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Direction: {data['direction']}")
        print(f"✓ Confidence: {data['direction_confidence']:.2f}%")
        print(f"✓ Current Price: ${data['current_price']:.2f}")
        print(f"✓ Predicted Price: ${data['predicted_price']:.2f}")
        print(f"✓ Input Method: {data.get('input_method', 'N/A')}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: File upload (CSV)
print("\n4. Testing File Upload (POST /predict/file)")
print("-" * 60)
try:
    with open('test_predict_data.csv', 'rb') as f:
        files = {'file': ('test_predict_data.csv', f, 'text/csv')}
        response = requests.post(f"{API_BASE}/predict/file", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total Records: {data['total_records']}")
        print(f"✓ Predictions:")
        for i, pred in enumerate(data['predictions'][:3]):  # Show first 3
            print(f"   Row {i+1}: {pred['direction']} ({pred['direction_confidence']:.2f}%) - ${pred['predicted_price']:.2f}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Get feature names
print("\n5. Testing Feature Names (GET /model/features)")
print("-" * 60)
try:
    response = requests.get(f"{API_BASE}/model/features")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Feature Count: {data['count']}")
        print(f"✓ Features: {', '.join(data['features'][:5])}...")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("All Tests Completed!")
print("=" * 60)
