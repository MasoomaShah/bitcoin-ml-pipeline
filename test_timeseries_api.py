"""
Test script for the World Bank GDP Growth Prediction API.
Tests both regression and classification endpoints.
"""

import requests
import json
import pandas as pd
import io

API_BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    response = requests.get(f"{API_BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_model_info():
    """Test getting model information."""
    print("\n" + "="*60)
    print("TEST 2: Get Model Info")
    print("="*60)
    response = requests.get(f"{API_BASE_URL}/model-info")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Domain: {data.get('domain')}")
    print(f"Features: {data.get('features')}")
    print(f"Train samples: {data.get('n_samples_train')}")
    print(f"Test samples: {data.get('n_samples_test')}")
    assert response.status_code == 200


def test_feature_columns():
    """Test getting feature columns."""
    print("\n" + "="*60)
    print("TEST 3: Get Feature Columns")
    print("="*60)
    response = requests.get(f"{API_BASE_URL}/feature-columns")
    print(f"Status: {response.status_code}")
    features = response.json().get("feature_columns")
    print(f"Expected features: {features}")
    assert response.status_code == 200
    assert len(features) == 5


def test_regression_prediction():
    """Test regression prediction endpoint."""
    print("\n" + "="*60)
    print("TEST 4: Regression Prediction")
    print("="*60)
    
    # Use realistic 2024 economic data for Pakistan
    payload = {
        "GDP": 3.73e11,  # ~373 billion USD
        "Population": 251269164,  # ~251 million
        "Inflation": 12.6,  # ~12.6% inflation rate
        "Unemployment": 5.47,  # ~5.47%
        "GDP_rolling3": 3.619492e11  # 3-year rolling average
    }
    
    response = requests.post(
        f"{API_BASE_URL}/predict/regression",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Prediction: {json.dumps(result, indent=2)}")
    
    assert response.status_code == 200
    assert "prediction" in result
    print(f"✓ Predicted GDP growth: {result['prediction']*100:.2f}%")


def test_classification_prediction():
    """Test classification prediction endpoint."""
    print("\n" + "="*60)
    print("TEST 5: Classification Prediction")
    print("="*60)
    
    payload = {
        "GDP": 3.73e11,
        "Population": 251269164,
        "Inflation": 12.6,
        "Unemployment": 5.47,
        "GDP_rolling3": 3.619492e11
    }
    
    response = requests.post(
        f"{API_BASE_URL}/predict/classification",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Classification: {json.dumps(result, indent=2)}")
    
    assert response.status_code == 200
    assert "classification" in result
    print(f"✓ Classification: {result['classification']}")
    print(f"✓ Confidence (High Growth): {result['probability_high_growth']:.2%}")


def test_both_predictions():
    """Test combined regression and classification prediction."""
    print("\n" + "="*60)
    print("TEST 6: Combined Predictions (Regression + Classification)")
    print("="*60)
    
    payload = {
        "GDP": 3.73e11,
        "Population": 251269164,
        "Inflation": 12.6,
        "Unemployment": 5.47,
        "GDP_rolling3": 3.619492e11
    }
    
    response = requests.post(
        f"{API_BASE_URL}/predict/both",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert response.status_code == 200
    assert "regression" in result and "classification" in result
    print(f"✓ Regression prediction: {result['regression']['prediction']*100:.2f}% growth")
    print(f"✓ Classification: {result['classification']['prediction']}")


def test_batch_prediction():
    """Test batch predictions from CSV file."""
    print("\n" + "="*60)
    print("TEST 7: Batch Prediction from CSV")
    print("="*60)
    
    # Create sample CSV data
    data = {
        "date": ["2022-01-01", "2023-01-01", "2024-01-01"],
        "GDP": [3.748903e11, 3.378855e11, 3.730719e11],
        "Population": [243700667, 247504495, 251269164],
        "Inflation": [19.87, 30.77, 12.63],
        "Unemployment": [5.485, 5.408, 5.472],
        "GDP_rolling3": [3.412775e11, 3.537642e11, 3.619492e11]
    }
    
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    # Upload CSV
    files = {"file": ("batch_data.csv", csv_buffer, "text/csv")}
    response = requests.post(
        f"{API_BASE_URL}/predict/batch",
        files=files
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total rows: {result['total_rows']}")
    print(f"Successful predictions: {result['successful_predictions']}")
    print(f"Failed predictions: {result['failed_predictions']}")
    
    for i, pred in enumerate(result['results'][:3]):
        print(f"\nRow {i}:")
        if "error" not in pred:
            print(f"  Regression: {pred['regression_prediction']*100:.2f}% growth")
            print(f"  Classification: {pred['classification_prediction']}")
        else:
            print(f"  Error: {pred['error']}")
    
    assert response.status_code == 200
    assert result['successful_predictions'] > 0


def test_reload_models():
    """Test model reload endpoint."""
    print("\n" + "="*60)
    print("TEST 8: Reload Models")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE_URL}/reload-models"
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert response.status_code == 200
    assert result['models_loaded'] == True
    print("✓ Models reloaded successfully")


if __name__ == "__main__":
    print("\n" + "🚀 "*20)
    print("TESTING WORLD BANK GDP GROWTH PREDICTION API")
    print("🚀 "*20)
    
    try:
        test_health()
        test_model_info()
        test_feature_columns()
        test_regression_prediction()
        test_classification_prediction()
        test_both_predictions()
        test_batch_prediction()
        test_reload_models()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
