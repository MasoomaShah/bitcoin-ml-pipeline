# FastAPI Quick Test Guide

## Prerequisites
Make sure your FastAPI server is running:
```powershell
python api_server.py
```

## Test the Endpoints

### 1. Health Check
```powershell
curl http://localhost:8000/health
```

### 2. Get Model Features
```powershell
curl http://localhost:8000/model/features
```

### 3. Get Model Info
```powershell
curl http://localhost:8000/model/info
```

### 4. Test JSON Endpoint (with real Bitcoin data)
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```

### 5. Test Numeric Array Endpoint (with real Bitcoin data)
```powershell
curl -X POST http://localhost:8000/predict/numeric `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_numeric.json)
```

### 6. Test Auto-Load Prediction (using latest data from CSV)
```powershell
curl http://localhost:8000/predict
```

### 7. Run Full Test Suite
```powershell
python test_fastapi.py
```

## Expected Results

### Successful JSON/Numeric Response:
```json
{
  "direction": "UP or DOWN",
  "direction_confidence": 65.5,
  "price_change_pct": 2.15,
  "current_price": 104315.87,
  "predicted_price": 106557.01,
  "price_change_usd": 2241.14,
  "timestamp": "2024-12-17T...",
  "input_method": "json or numeric_array"
}
```

## Troubleshooting

If you get "Models not loaded" error:
```powershell
curl -X POST http://localhost:8000/model/reload
```

If you get "Data not loaded" error on `/predict` endpoint:
- Make sure `data/raw/bitcoin_timeseries.csv` exists ✓ (confirmed)
- The API should auto-load it on startup

## Files Generated
- `test_fastapi_json.json` - 49 features as JSON dictionary with real Bitcoin data
- `test_fastapi_numeric.json` - 49 features as numeric array with real Bitcoin data
- `generate_test_data.py` - Script to regenerate test data from CSV
