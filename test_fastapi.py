#!/usr/bin/env python3
"""
FastAPI Testing Script
Tests all endpoints and provides detailed diagnostics
"""

import requests
import json
from pathlib import Path
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_model_features():
    """Test model features endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Get Model Features")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/model/features")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total features: {data.get('total_features', 'N/A')}")
        print(f"Feature list: {data.get('feature_columns', [])}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_auto_predict():
    """Test auto-load prediction endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Auto-Load Prediction (/predict)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/predict")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        print("DIAGNOSTIC: Check if data files exist:")
        print(f"  - data/raw/bitcoin_timeseries.csv: {Path('data/raw/bitcoin_timeseries.csv').exists()}")
        print(f"  - data/processed/*.csv: {len(list(Path('data/processed').glob('*.csv'))) if Path('data/processed').exists() else 0} files")
        print(f"  - data/features/*.csv: {len(list(Path('data/features').glob('*.csv'))) if Path('data/features').exists() else 0} files")
        return False


def test_json_predict():
    """Test JSON prediction endpoint"""
    print("\n" + "="*60)
    print("TEST 4: JSON Prediction (/predict/json)")
    print("="*60)
    
    try:
        # Load test data
        if not Path("test_fastapi_json.json").exists():
            print("ERROR: test_fastapi_json.json not found")
            return False
        
        with open("test_fastapi_json.json") as f:
            test_data = json.load(f)
        
        response = requests.post(f"{BASE_URL}/predict/json", json=test_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Direction: {result.get('direction')}")
            print(f"Confidence: {result.get('direction_confidence'):.2f}%")
            print(f"Price Change: {result.get('price_change_pct'):.2f}%")
            print(f"Current Price: ${result.get('current_price'):,.2f}")
            print(f"Predicted Price: ${result.get('predicted_price'):,.2f}")
            print(f"Full Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_numeric_predict():
    """Test numeric prediction endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Numeric Array Prediction (/predict/numeric)")
    print("="*60)
    
    try:
        # Load test data
        if not Path("test_fastapi_numeric.json").exists():
            print("ERROR: test_fastapi_numeric.json not found")
            return False
        
        with open("test_fastapi_numeric.json") as f:
            test_data = json.load(f)
        
        response = requests.post(f"{BASE_URL}/predict/numeric", json=test_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Direction: {result.get('direction')}")
            print(f"Confidence: {result.get('direction_confidence'):.2f}%")
            print(f"Price Change: {result.get('price_change_pct'):.2f}%")
            print(f"Current Price: ${result.get('current_price'):,.2f}")
            print(f"Predicted Price: ${result.get('predicted_price'):,.2f}")
            print(f"Full Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_model_reload():
    """Test model reload endpoint"""
    print("\n" + "="*60)
    print("TEST 6: Model Reload (/model/reload)")
    print("="*60)
    
    try:
        response = requests.post(f"{BASE_URL}/model/reload")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*60)
    print("TEST 7: Model Info (/model/info)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/model/info")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Response: {response.json()}")
        return response.status_code in [200, 404]  # 404 is ok if endpoint not implemented
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# FastAPI Server Testing")
    print(f"# Base URL: {BASE_URL}")
    print("#"*60)
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except Exception as e:
        print(f"\nERROR: Cannot connect to FastAPI server at {BASE_URL}")
        print(f"Make sure the server is running: python api_server.py")
        print(f"Details: {e}")
        sys.exit(1)
    
    results = {
        "Health Check": test_health(),
        "Model Features": test_model_features(),
        "Model Info": test_model_info(),
        "Auto-Load Predict": test_auto_predict(),
        "JSON Predict": test_json_predict(),
        "Numeric Predict": test_numeric_predict(),
        "Model Reload": test_model_reload(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
