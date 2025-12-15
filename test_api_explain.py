"""
Manually test SHAP endpoint by calling the API
"""
import requests
import json

print("Testing API /explain endpoint...")
print("="*60)

# Test data with dummy features (24 features)
test_features = {
    "Open": 97000,
    "High": 98000,
    "Low": 96000,
    "Close": 97500,
    "Volume": 25000000000,
    "SMA_7": 97200,
    "SMA_14": 96800,
    "SMA_30": 95000,
    "EMA_7": 97300,
    "EMA_14": 96900,
    "momentum_7": 500,
    "momentum_14": 700,
    "momentum_30": 2000,
    "volatility_7": 1.2,
    "volatility_14": 1.4,
    "RSI": 55,
    "MACD": 350,
    "MACD_signal": 300,
    "BB_middle": 97000,
    "BB_upper": 98500,
    "BB_lower": 95500,
    "BB_width": 3000,
    "volume_SMA_7": 24000000000,
    "volume_change": 0.05
}

try:
    print(f"Sending request to http://localhost:8000/explain")
    print(f"With {len(test_features)} features...")
    
    response = requests.post(
        "http://localhost:8000/explain",
        json={"features": test_features},
        timeout=120
    )
    
    print(f"\n[OK] Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Successfully got SHAP explanation!")
        
        # Feature importance
        feature_importance = data.get('feature_importance', {})
        if feature_importance:
            print(f"\nTop 10 Features by Importance:")
            print("-" * 60)
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (feat, val) in enumerate(sorted_features, 1):
                print(f"{i:2d}. {feat:20s}: {val:.6f}")
        
        # SHAP values
        shap_vals = data.get('shap_values', [])
        if shap_vals:
            print(f"\nAll SHAP Values for Latest Data:")
            print("-" * 60)
            feature_cols = list(test_features.keys())
            for feat, sv in zip(feature_cols, shap_vals):
                print(f"{feat:20s}: {sv:+.6f}")
        
        print(f"\nBase Value: {data.get('base_value', 'N/A')}")
        print(f"Explanation Method: {data.get('explanation_method', 'N/A')}")
        
    else:
        print(f"[ERROR] API Error: Status {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to API on localhost:8000")
    print("  Make sure API is running:")
    print("  python -m uvicorn api_server:app --host 0.0.0.0 --port 8000")
except requests.exceptions.Timeout:
    print("[ERROR] Request timed out (120+ seconds)")
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
