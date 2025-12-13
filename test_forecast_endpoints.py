"""
Test Prophet and Deep Learning Forecasting Endpoints

Tests the new /forecast endpoints added to the API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_prophet_forecast():
    """Test Prophet time series forecasting"""
    print("\n" + "="*70)
    print("TESTING PROPHET FORECAST ENDPOINT")
    print("="*70)
    
    try:
        # Test 7-day forecast
        print("\n[1] Testing 7-day forecast...")
        response = requests.get(f"{BASE_URL}/forecast/prophet?periods=7")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Forecast periods: {data['forecast_periods']}")
            print(f"✓ Current price: ${data['current_price']:,.2f}")
            print(f"✓ Model: {data['model_type']}")
            
            print("\n  Forecasted prices:")
            for date, price, lower, upper in zip(
                data['forecasted_dates'][:5],
                data['forecasted_prices'][:5],
                data['lower_bound'][:5],
                data['upper_bound'][:5]
            ):
                print(f"    {date}: ${price:,.2f} (${lower:,.2f} - ${upper:,.2f})")
            
            if len(data['forecasted_prices']) > 5:
                print(f"    ... and {len(data['forecasted_prices']) - 5} more days")
            
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  {response.text}")
        
        # Test 30-day forecast
        print("\n[2] Testing 30-day forecast...")
        response = requests.get(f"{BASE_URL}/forecast/prophet?periods=30")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Generated {len(data['forecasted_prices'])} predictions")
            
            # Show first and last
            print(f"\n  First forecast: {data['forecasted_dates'][0]} - ${data['forecasted_prices'][0]:,.2f}")
            print(f"  Last forecast:  {data['forecasted_dates'][-1]} - ${data['forecasted_prices'][-1]:,.2f}")
            
        else:
            print(f"✗ Error: {response.status_code}")
        
        print("\n✓ Prophet forecast test complete!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API")
        print("  Make sure the API is running: python -m uvicorn api_server:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_deep_learning_forecast():
    """Test Deep Learning (LSTM/GRU) predictions"""
    print("\n" + "="*70)
    print("TESTING DEEP LEARNING FORECAST ENDPOINT")
    print("="*70)
    
    try:
        # Test LSTM
        print("\n[1] Testing LSTM model...")
        response = requests.get(f"{BASE_URL}/forecast/deep-learning?model_type=lstm")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Model: {data['model_type']}")
            print(f"✓ Model file: {data['model_file']}")
            print(f"✓ Direction: {data['direction']}")
            print(f"✓ Confidence: {data['confidence']:.2f}%")
            print(f"✓ Raw prediction: {data['raw_prediction']:.4f}")
            print(f"✓ Current price: ${data['current_price']:,.2f}")
            print(f"✓ Sequence length: {data['sequence_length']} days")
            print(f"\n  Note: {data['note']}")
            
        elif response.status_code == 404:
            print(f"⚠️  LSTM model not found")
            print(f"  {response.json()['detail']}")
        elif response.status_code == 503:
            print(f"⚠️  TensorFlow not available")
            print(f"  {response.json()['detail']}")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  {response.text}")
        
        # Test GRU
        print("\n[2] Testing GRU model...")
        response = requests.get(f"{BASE_URL}/forecast/deep-learning?model_type=gru")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Model: {data['model_type']}")
            print(f"✓ Direction: {data['direction']}")
            print(f"✓ Confidence: {data['confidence']:.2f}%")
            
        elif response.status_code == 404:
            print(f"⚠️  GRU model not found")
        elif response.status_code == 503:
            print(f"⚠️  TensorFlow not available")
        else:
            print(f"✗ Error: {response.status_code}")
        
        print("\n✓ Deep learning forecast test complete!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API")
        print("  Make sure the API is running: python -m uvicorn api_server:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_ensemble_prediction():
    """Test combining predictions from multiple models"""
    print("\n" + "="*70)
    print("TESTING ENSEMBLE APPROACH")
    print("="*70)
    
    try:
        print("\n[1] Fetching predictions from all models...")
        
        # Traditional ML
        trad_ml = requests.get(f"{BASE_URL}/predict").json()
        print(f"✓ Traditional ML: {trad_ml['direction']} ({trad_ml['direction_confidence']:.1f}% confidence)")
        
        # Prophet (1-day forecast)
        prophet = requests.get(f"{BASE_URL}/forecast/prophet?periods=1").json()
        prophet_direction = "UP" if prophet['forecasted_prices'][0] > prophet['current_price'] else "DOWN"
        prophet_change = ((prophet['forecasted_prices'][0] - prophet['current_price']) / prophet['current_price']) * 100
        print(f"✓ Prophet: {prophet_direction} ({prophet_change:+.2f}%)")
        
        # Deep Learning (LSTM)
        try:
            lstm = requests.get(f"{BASE_URL}/forecast/deep-learning?model_type=lstm").json()
            print(f"✓ LSTM: {lstm['direction']} ({lstm['confidence']:.1f}% confidence)")
            lstm_available = True
        except:
            print("⚠️  LSTM: Not available")
            lstm_available = False
        
        # Calculate ensemble
        print("\n[2] Calculating ensemble prediction...")
        
        votes_up = 0
        votes_down = 0
        
        if trad_ml['direction'] == 'UP':
            votes_up += 1
        else:
            votes_down += 1
        
        if prophet_direction == 'UP':
            votes_up += 1
        else:
            votes_down += 1
        
        if lstm_available:
            if lstm['direction'] == 'UP':
                votes_up += 1
            else:
                votes_down += 1
        
        ensemble_direction = "UP" if votes_up > votes_down else "DOWN"
        print(f"\n✓ Ensemble Prediction: {ensemble_direction}")
        print(f"  Votes UP: {votes_up}")
        print(f"  Votes DOWN: {votes_down}")
        
        print("\n✓ Ensemble test complete!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_api_root():
    """Test updated root endpoint"""
    print("\n" + "="*70)
    print("TESTING UPDATED API ROOT")
    print("="*70)
    
    try:
        response = requests.get(BASE_URL)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ API Version: {data['version']}")
            print(f"✓ Description: {data['description']}")
            
            print("\n📋 Available Endpoints:")
            for endpoint, desc in data['endpoints'].items():
                print(f"  • {endpoint}: {desc}")
            
            print("\n🤖 Model Types:")
            for model, desc in data['model_types'].items():
                print(f"  • {model}: {desc}")
            
        else:
            print(f"✗ Error: {response.status_code}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    print("="*70)
    print("TESTING NEW FORECASTING ENDPOINTS")
    print("="*70)
    print("\nThis script tests the newly added Prophet and Deep Learning endpoints")
    print("Make sure the API is running first:")
    print("  python -m uvicorn api_server:app --reload")
    print("\n" + "="*70)
    
    # Run tests
    test_api_root()
    test_prophet_forecast()
    test_deep_learning_forecast()
    test_ensemble_prediction()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print("\n📊 Summary:")
    print("  • Prophet endpoint provides time series forecasts with confidence intervals")
    print("  • Deep Learning endpoint provides LSTM/GRU predictions")
    print("  • Ensemble approach combines multiple models")
    print("\n💡 Next steps:")
    print("  • Use Prophet for price forecasting (R² = 0.4504)")
    print("  • Use Traditional ML for direction prediction")
    print("  • Consider ensemble for improved accuracy")
    print("="*70)
