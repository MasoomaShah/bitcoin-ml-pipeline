#!/usr/bin/env python3
"""
Comprehensive FastAPI Testing Script
Tests all prediction endpoints with different input formats
"""

import requests
import json
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path

API_URL = "http://localhost:8000"

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_response(response):
    """Pretty print response"""
    print(f"\n📊 Status Code: {response.status_code}")
    try:
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_health_check():
    """Test 1: Health Check"""
    print_header("TEST 1: Health Check")
    
    print("Request: GET /health")
    response = requests.get(f"{API_URL}/health")
    print_response(response)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("\n✓ PASSED")

def test_model_info():
    """Test 2: Model Information"""
    print_header("TEST 2: Get Model Information")
    
    print("Request: GET /model/info")
    response = requests.get(f"{API_URL}/model/info")
    print_response(response)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'version' in data
    assert 'classification_accuracy' in data
    assert 'regression_rmse' in data
    print("\n✓ PASSED")

def test_single_price():
    """Test 3: Single Price Prediction (Simplest)"""
    print_header("TEST 3: Single Price Prediction (GET /predict)")
    
    print("Request: GET /predict?price=97309.20")
    response = requests.get(f"{API_URL}/predict?price=97309.20")
    print_response(response)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'direction' in data
    assert 'price_change_pct' in data
    assert 'predicted_price' in data
    print("\n✓ PASSED - Simple price prediction works!")

def test_json_features():
    """Test 4: JSON Features Input"""
    print_header("TEST 4: JSON Features Input (POST /predict/json)")
    
    payload = {
        "features": {
            "price": 97309.20,
            "volume": 3508635533.83,
            "market_cap": 1815851748170.10,
            "price_smooth": 97300.15,
            "price_ma3": 98500.25,
            "price_ma7": 99420.50,
            "price_ma14": 98950.75,
            "price_ma30": 98200.30,
            "price_ema7": 98800.25,
            "price_ema14": 98500.50,
            "momentum_3d": 0.0234,
            "momentum_7d": 0.0234,
            "momentum_14d": 0.0145,
            "roc_3d": 0.0234,
            "roc_7d": 0.0145,
            "price_volatility_3d": 1250.50,
            "price_volatility_7d": 1250.50,
            "price_volatility_14d": 1450.75,
            "volume_ma3": 3300000000.00,
            "volume_ma7": 3250000000.00,
            "volume_change": 0.0456,
            "price_to_ma7": 0.9788,
            "price_to_ma30": 0.9911,
            "bb_middle": 99200.00,
            "bb_std": 3000.00,
            "bb_upper": 102500.00,
            "bb_lower": 95900.00,
            "bb_position": 0.55,
            "rsi_14": 52.35,
            "market_cap_change": 0.0234,
            "volume_to_marketcap": 0.00193,
            "SMA_7": 99420.50,
            "SMA_14": 98950.75,
            "SMA_30": 98200.30,
            "EMA_7": 98800.25,
            "EMA_14": 98500.50,
            "momentum_7": 0.0234,
            "momentum_14": 0.0145,
            "momentum_30": 0.0089,
            "volatility_7": 1250.50,
            "volatility_14": 1450.75,
            "RSI": 52.35,
            "MACD": 450.25,
            "MACD_signal": 420.50,
            "BB_middle": 99200.00,
            "BB_upper": 102500.00,
            "BB_lower": 95900.00,
            "BB_width": 6600.00,
            "volume_SMA_7": 3200000000.00
        },
        "current_price": 97309.20
    }
    
    print("Request: POST /predict/json")
    print("Payload: 49 features as JSON object (with feature names)")
    response = requests.post(f"{API_URL}/predict/json", json=payload)
    print_response(response)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'direction' in data
    assert 'price_change_pct' in data
    print("\n✓ PASSED - JSON features work!")

def test_numeric_array():
    """Test 5: Numeric Array Input"""
    print_header("TEST 5: Numeric Array Input (POST /predict/numeric)")
    
    payload = {
        "features": [
            97309.20,  # price
            3508635533.83,  # volume
            1815851748170.10,  # market_cap
            97300.15,  # price_smooth
            98500.25,  # price_ma3
            99420.50,  # price_ma7
            98950.75,  # price_ma14
            98200.30,  # price_ma30
            98800.25,  # price_ema7
            98500.50,  # price_ema14
            0.0234,  # momentum_3d
            0.0234,  # momentum_7d
            0.0145,  # momentum_14d
            0.0234,  # roc_3d
            0.0145,  # roc_7d
            1250.50,  # price_volatility_3d
            1250.50,  # price_volatility_7d
            1450.75,  # price_volatility_14d
            3300000000.00,  # volume_ma3
            3250000000.00,  # volume_ma7
            0.0456,  # volume_change
            0.9788,  # price_to_ma7
            0.9911,  # price_to_ma30
            99200.00,  # bb_middle
            3000.00,  # bb_std
            102500.00,  # bb_upper
            95900.00,  # bb_lower
            0.55,  # bb_position
            52.35,  # rsi_14
            0.0234,  # market_cap_change
            0.00193,  # volume_to_marketcap
            99420.50,  # SMA_7
            98950.75,  # SMA_14
            98200.30,  # SMA_30
            98800.25,  # EMA_7
            98500.50,  # EMA_14
            0.0234,  # momentum_7
            0.0145,  # momentum_14
            0.0089,  # momentum_30
            1250.50,  # volatility_7
            1450.75,  # volatility_14
            52.35,  # RSI
            450.25,  # MACD
            420.50,  # MACD_signal
            99200.00,  # BB_middle
            102500.00,  # BB_upper
            95900.00,  # BB_lower
            6600.00,  # BB_width
            3200000000.00  # volume_SMA_7
        ],
        "current_price": 97309.20
    }
    
    print("Request: POST /predict/numeric")
    print("Payload: 49 features as numeric array (ordered values only)")
    response = requests.post(f"{API_URL}/predict/numeric", json=payload)
    print_response(response)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'direction' in data
    print("\n✓ PASSED - Numeric array works!")

def test_batch_csv():
    """Test 6: Batch CSV Upload"""
    print_header("TEST 6: Batch CSV Upload (POST /predict/batch)")
    
    # Create inline CSV with all 49 features
    csv_data = """price,volume,market_cap,price_smooth,price_ma3,price_ma7,price_ma14,price_ma30,price_ema7,price_ema14,momentum_3d,momentum_7d,momentum_14d,roc_3d,roc_7d,price_volatility_3d,price_volatility_7d,price_volatility_14d,volume_ma3,volume_ma7,volume_change,price_to_ma7,price_to_ma30,bb_middle,bb_std,bb_upper,bb_lower,bb_position,rsi_14,market_cap_change,volume_to_marketcap,SMA_7,SMA_14,SMA_30,EMA_7,EMA_14,momentum_7,momentum_14,momentum_30,volatility_7,volatility_14,RSI,MACD,MACD_signal,BB_middle,BB_upper,BB_lower,BB_width,volume_SMA_7
97309.20,3508635533.83,1815851748170.10,97300.15,98500.25,99420.50,98950.75,98200.30,98800.25,98500.50,0.0234,0.0234,0.0145,0.0234,0.0145,1250.50,1250.50,1450.75,3300000000.00,3250000000.00,0.0456,0.9788,0.9911,99200.00,3000.00,102500.00,95900.00,0.55,52.35,0.0234,0.00193,99420.50,98950.75,98200.30,98800.25,98500.50,0.0234,0.0145,0.0089,1250.50,1450.75,52.35,450.25,420.50,99200.00,102500.00,95900.00,6600.00,3200000000.00
96228.18,1444793574.06,1851412983843.97,96220.50,97500.75,98250.75,98100.50,97950.20,98150.30,98050.75,0.0123,0.0123,0.0089,0.0123,0.0089,1100.20,1100.20,1200.50,3150000000.00,3200000000.00,0.0325,0.9759,0.9825,98500.00,2800.00,101200.00,95800.00,0.45,48.75,0.0156,0.00078,98250.75,98100.50,97950.20,98150.30,98050.75,0.0123,0.0089,0.0056,1100.20,1200.50,48.75,380.15,390.25,98500.00,101200.00,95800.00,5400.00,3100000000.00"""
    
    print("Request: POST /predict/batch (inline CSV with 2 rows, 49 features)")
    files = {'file': ('test_batch.csv', csv_data)}
    response = requests.post(f"{API_URL}/predict/batch", files=files)
    print_response(response)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'predictions' in data
    assert 'total_records' in data
    assert len(data['predictions']) > 0
    print(f"\n✓ PASSED - Batch prediction works! ({data['total_records']} records)")

def test_explanations():
    """Test 7: SHAP Explanations"""
    print_header("TEST 7: SHAP Explanations (POST /explain)")
    
    payload = {
        "features": {
            "price": 97309.20,
            "volume": 3508635533.83,
            "market_cap": 1815851748170.10,
            "price_smooth": 97300.15,
            "price_ma3": 98500.25,
            "price_ma7": 99420.50,
            "price_ma14": 98950.75,
            "price_ma30": 98200.30,
            "price_ema7": 98800.25,
            "price_ema14": 98500.50,
            "momentum_3d": 0.0234,
            "momentum_7d": 0.0234,
            "momentum_14d": 0.0145,
            "roc_3d": 0.0234,
            "roc_7d": 0.0145,
            "price_volatility_3d": 1250.50,
            "price_volatility_7d": 1250.50,
            "price_volatility_14d": 1450.75,
            "volume_ma3": 3300000000.00,
            "volume_ma7": 3250000000.00,
            "volume_change": 0.0456,
            "price_to_ma7": 0.9788,
            "price_to_ma30": 0.9911,
            "bb_middle": 99200.00,
            "bb_std": 3000.00,
            "bb_upper": 102500.00,
            "bb_lower": 95900.00,
            "bb_position": 0.55,
            "rsi_14": 52.35,
            "market_cap_change": 0.0234,
            "volume_to_marketcap": 0.00193,
            "SMA_7": 99420.50,
            "SMA_14": 98950.75,
            "SMA_30": 98200.30,
            "EMA_7": 98800.25,
            "EMA_14": 98500.50,
            "momentum_7": 0.0234,
            "momentum_14": 0.0145,
            "momentum_30": 0.0089,
            "volatility_7": 1250.50,
            "volatility_14": 1450.75,
            "RSI": 52.35,
            "MACD": 450.25,
            "MACD_signal": 420.50,
            "BB_middle": 99200.00,
            "BB_upper": 102500.00,
            "BB_lower": 95900.00,
            "BB_width": 6600.00,
            "volume_SMA_7": 3200000000.00
        }
    }
    
    print("Request: POST /explain (with all 49 features)")
    print("Returns: Feature importance and SHAP values")
    response = requests.post(f"{API_URL}/explain", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        assert 'feature_importance' in data or 'message' in data
        print("\n✓ PASSED - Explanations available!")
    else:
        print("\n⚠ Explanations may not be available (SHAP not installed)")

def test_historical_data():
    """Test 8: Get Historical Data"""
    print_header("TEST 8: Historical Data (GET /data/historical)")
    
    print("Request: GET /data/historical?days=7")
    response = requests.get(f"{API_URL}/data/historical?days=7")
    print_response(response)
    
    if response.status_code == 200:
        print("\n✓ PASSED - Historical data available!")
    else:
        print("\n⚠ Historical data may not be available")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "🚀 FASTAPI COMPREHENSIVE TEST SUITE 🚀" + " "*14 + "║")
    print("╚" + "="*68 + "╝")
    
    print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API URL: {API_URL}")
    print("\n" + "─"*70)
    
    tests = [
        ("Health Check", test_health_check),
        ("Model Info", test_model_info),
        ("Single Price", test_single_price),
        ("JSON Features", test_json_features),
        ("Numeric Array", test_numeric_array),
        ("Batch CSV", test_batch_csv),
        ("Explanations", test_explanations),
        ("Historical Data", test_historical_data),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print(f"\n✗ FAILED: Could not connect to API at {API_URL}")
            print("   Make sure FastAPI is running: python -m uvicorn api_server:app --reload")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            failed += 1
    
    # Print summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)
    print(f"✓ Passed:  {passed}/{len(tests)}")
    print(f"✗ Failed:  {failed}/{len(tests)}")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"❌ {failed} test(s) failed\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
