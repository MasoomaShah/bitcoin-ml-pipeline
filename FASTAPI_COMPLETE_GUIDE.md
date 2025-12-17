# FastAPI Testing Complete Guide

## Current Status ✓

- **Models**: Loaded (clf_model.pkl, reg_model.pkl, scaler.pkl)
- **Data**: Available (data/raw/bitcoin_timeseries.csv with 365 days)
- **Test Data**: Generated with real Bitcoin data and 49 engineered features
- **Latest Price**: $104,315.87 (as of 2025-12-17)

---

## What Was Fixed

### Problem 1: `ml_pipeline.py` Not Found
**Error**: `python ml_pipeline.py` returned "No such file or directory"

**Solution**: 
- The ML pipeline is in `prefect/flows/ml_pipeline.py` (Prefect orchestration)
- Models are already trained and saved as pickle files
- No need to retrain; focus on testing the API with existing models

### Problem 2: Test Data Missing Features
**Error**: Test files only had raw data (price, volume, market_cap) but models expect 49 engineered features

**Solution**:
- Created `generate_test_data.py` script
- Generates all 49 technical indicators from raw Bitcoin data
- Produces realistic test data matching what models were trained on

---

## Quick Start (5 minutes)

### Step 1: Start FastAPI Server
```powershell
cd "C:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT"
python api_server.py
```

Output should show:
```
Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Test Health (in another terminal)
```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "model_loaded": true, "data_available": true, "timestamp": "..."}
```

### Step 3: Test JSON Prediction
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```

### Step 4: Test Numeric Prediction
```powershell
curl -X POST http://localhost:8000/predict/numeric `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_numeric.json)
```

### Step 5: Test Auto-Load Prediction
```powershell
curl http://localhost:8000/predict
```

---

## Detailed Endpoint Guide

### Endpoint: `GET /health`
**Purpose**: Check if server and models are healthy

**Command**:
```powershell
curl http://localhost:8000/health
```

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "data_available": true,
  "timestamp": "2025-12-17T10:30:00.123456"
}
```

---

### Endpoint: `GET /model/features`
**Purpose**: Get the list of 49 features in order (important for numeric array)

**Command**:
```powershell
curl http://localhost:8000/model/features
```

**Response (200 OK)**:
```json
{
  "feature_columns": [
    "price", "volume", "market_cap", "price_smooth", ..., "volume_SMA_7"
  ],
  "total_features": 49
}
```

---

### Endpoint: `POST /predict/json`
**Purpose**: Make prediction with 49 features as JSON dictionary

**Test File**: `test_fastapi_json.json`

**Command**:
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```

**Request Format**:
```json
{
  "features": {
    "price": 104315.87,
    "volume": 4331230750.52,
    "market_cap": 1810758924588.81,
    ... (47 more features)
  },
  "current_price": 104315.87
}
```

**Response (200 OK)**:
```json
{
  "direction": "UP",
  "direction_confidence": 72.45,
  "price_change_pct": 2.35,
  "current_price": 104315.87,
  "predicted_price": 106763.23,
  "price_change_usd": 2447.36,
  "timestamp": "2025-12-17T10:30:00.234567",
  "input_method": "json"
}
```

---

### Endpoint: `POST /predict/numeric`
**Purpose**: Make prediction with 49 features as numeric array (must be in correct order)

**Test File**: `test_fastapi_numeric.json`

**Command**:
```powershell
curl -X POST http://localhost:8000/predict/numeric `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_numeric.json)
```

**Request Format**:
```json
{
  "features": [
    104315.87,        // price (index 0)
    4331230750.52,    // volume (index 1)
    1810758924588.81, // market_cap (index 2)
    ... (46 more values in exact feature order)
  ],
  "current_price": 104315.87
}
```

**Response (200 OK)**:
```json
{
  "direction": "DOWN",
  "direction_confidence": 68.32,
  "price_change_pct": -1.85,
  "current_price": 104315.87,
  "predicted_price": 102443.51,
  "price_change_usd": -1872.36,
  "timestamp": "2025-12-17T10:30:00.345678",
  "input_method": "numeric_array"
}
```

---

### Endpoint: `GET /predict`
**Purpose**: Auto-load latest Bitcoin data and make prediction

**Command**:
```powershell
curl http://localhost:8000/predict
```

**Response (200 OK)**:
```json
{
  "direction": "UP",
  "direction_confidence": 71.20,
  "price_change_pct": 1.92,
  "current_price": 104315.87,
  "predicted_price": 106315.47,
  "price_change_usd": 1999.60,
  "timestamp": "2025-12-17T10:30:00.456789",
  "input_method": "auto_features"
}
```

**Note**: This endpoint:
- Auto-loads latest row from `data/raw/bitcoin_timeseries.csv`
- Requires the CSV file to exist and have all 49 feature columns
- Currently: Data file exists with 365 rows ✓

---

### Endpoint: `POST /model/reload`
**Purpose**: Force reload models from disk (if they don't load automatically)

**Command**:
```powershell
curl -X POST http://localhost:8000/model/reload
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "models_loaded": true,
  "data_loaded": true,
  "timestamp": "2025-12-17T10:30:00.567890"
}
```

---

## Python Testing Script

### Run All Tests at Once
```powershell
python test_fastapi.py
```

This will test:
1. Health check
2. Model features endpoint
3. Model info endpoint
4. Auto-load prediction
5. JSON prediction
6. Numeric array prediction
7. Model reload

**Output**:
```
============================================================
TEST SUMMARY
============================================================
✓ PASS    Health Check
✓ PASS    Model Features
✓ PASS    Model Info
✓ PASS    Auto-Load Predict
✓ PASS    JSON Predict
✓ PASS    Numeric Predict
✓ PASS    Model Reload

Total: 7/7 tests passed

✓ All tests passed!
```

---

## Error Handling

### Error: "Models not loaded"
```json
{"detail": "Models not loaded"}
```

**Fix**:
```powershell
curl -X POST http://localhost:8000/model/reload
```

**Check**: Verify pickle files exist:
- `clf_model.pkl` ✓
- `reg_model.pkl` ✓
- `scaler.pkl` ✓

---

### Error: "Bitcoin data not loaded"
```json
{"detail": "Bitcoin data not loaded"}
```

**Fix**: Occurs with `/predict` endpoint when CSV is missing

**Check**: Verify data file:
```powershell
Test-Path "data/raw/bitcoin_timeseries.csv"
```

Currently: ✓ Exists (365 rows)

---

### Error: "Missing required features"
```json
{"detail": "Missing required features: ['volume_change', ...]"}
```

**Cause**: JSON request missing some features

**Fix**: Use the generated test file:
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```

---

### Error: "Expected 49 features, got X"
```json
{"detail": "Expected 49 features, got 48"}
```

**Cause**: Numeric array has wrong number of elements

**Fix**: 
1. Verify test file has exactly 49 numbers
2. Regenerate test data:
   ```powershell
   python generate_test_data.py
   ```

---

## Test Data Files

### `test_fastapi_json.json`
- Contains 49 features as a JSON dictionary
- Generated from real Bitcoin data (365 days)
- Current price: $104,315.87
- Last updated: 2025-12-17

**Sample**:
```json
{
  "features": {
    "price": 104315.8739604748,
    "volume": 4331230750.52054,
    "market_cap": 1810758924588.812,
    ...
  },
  "current_price": 104315.87
}
```

### `test_fastapi_numeric.json`
- Contains 49 features as a numeric array
- Same data as JSON file, different format
- Must maintain exact feature order
- Current price: $104,315.87

**Sample**:
```json
{
  "features": [
    104315.8739604748,
    4331230750.52054,
    1810758924588.812,
    ...
  ],
  "current_price": 104315.87
}
```

---

## Feature Order (for reference)

The 49 features in exact order for numeric array:

1. price
2. volume
3. market_cap
4. price_smooth
5. price_ma3
6. price_ma7
7. price_ma14
8. price_ma30
9. price_ema7
10. price_ema14
11. momentum_3d
12. momentum_7d
13. momentum_14d
14. roc_3d
15. roc_7d
16. price_volatility_3d
17. price_volatility_7d
18. price_volatility_14d
19. volume_ma3
20. volume_ma7
21. volume_change
22. price_to_ma7
23. price_to_ma30
24. bb_middle
25. bb_std
26. bb_upper
27. bb_lower
28. bb_position
29. rsi_14
30. market_cap_change
31. volume_to_marketcap
32. SMA_7
33. SMA_14
34. SMA_30
35. EMA_7
36. EMA_14
37. momentum_7
38. momentum_14
39. momentum_30
40. volatility_7
41. volatility_14
42. RSI
43. MACD
44. MACD_signal
45. BB_middle
46. BB_upper
47. BB_lower
48. BB_width
49. volume_SMA_7

---

## Next Steps

1. ✓ Generate test data: `python generate_test_data.py`
2. **→ Start FastAPI**: `python api_server.py`
3. **→ Test endpoints**: Use curl commands or `python test_fastapi.py`
4. Verify predictions are working correctly
5. Deploy to production as needed

---

## Files Reference

| File | Purpose |
|------|---------|
| `api_server.py` | FastAPI server with endpoints |
| `test_fastapi_json.json` | JSON test data (49 features) |
| `test_fastapi_numeric.json` | Numeric test data (49 features) |
| `test_fastapi.py` | Python test suite |
| `generate_test_data.py` | Generate test data from CSV |
| `data/raw/bitcoin_timeseries.csv` | Historical Bitcoin data (365 days) |
| `clf_model.pkl` | Classification model (pre-trained) |
| `reg_model.pkl` | Regression model (pre-trained) |
| `scaler.pkl` | Feature scaler (pre-trained) |

---

## Questions or Issues?

- **API not responding**: Check if `python api_server.py` is running
- **Wrong predictions**: Verify feature values are realistic
- **Data loading fails**: Ensure CSV file exists with all columns
- **Feature mismatch**: Run `python generate_test_data.py` to regenerate
