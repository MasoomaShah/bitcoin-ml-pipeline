# API Quick Reference - Complete

## Your Question Answered

### ❓ "Where do I get SHAP values now?"
✅ **Answer**: Use the `/explain` endpoint!
- **GET SHAP values**: `POST /explain` with your features
- **Get feature importance**: Same endpoint response
- **See**: [SHAP_GUIDE.md](SHAP_GUIDE.md)

### ❓ "Data historical and data upload don't work - should I remove them?"
✅ **Answer**: They DO work! You just needed documentation
- **Get historical**: `GET /data/historical?limit=100`
- **Get latest**: `GET /data/latest`
- **Upload CSV**: `POST /predict/file` with your CSV
- **See**: [DATA_ENDPOINTS_GUIDE.md](DATA_ENDPOINTS_GUIDE.md)

---

## All FastAPI Endpoints (Complete List)

### Health & Info
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API root with endpoint list |
| `/health` | GET | Health check |
| `/model/info` | GET | Model metadata & metrics |
| `/model/features` | GET | List of 49 required features |
| `/model/reload` | POST | Force reload models |

### Predictions
| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/predict` | GET | Auto-load latest data | Single prediction |
| `/predict/json` | POST | 49 features as dict | Single prediction |
| `/predict/numeric` | POST | 49 features as array | Single prediction |
| `/predict/file` | POST | CSV file upload | Multiple predictions |

### Data Access
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/data/latest` | GET | Latest Bitcoin data point |
| `/data/historical` | GET | Historical data (configurable limit) |

### Explanability (SHAP)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/explain` | POST | Get SHAP values & feature importance |

---

## Quick Test Suite

### Test 1: Health Check
```powershell
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", "model_loaded": true, ...}`

### Test 2: Get Features
```powershell
curl http://localhost:8000/model/features
```
Expected: List of 49 feature names

### Test 3: Latest Data
```powershell
curl http://localhost:8000/data/latest
```
Expected: Latest Bitcoin data with all 49 features

### Test 4: Historical Data
```powershell
curl "http://localhost:8000/data/historical?limit=10"
```
Expected: Array of 10 latest data points

### Test 5: Single Prediction (JSON)
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```
Expected: `{"direction": "UP/DOWN", "price_change_pct": X.XX, ...}`

### Test 6: Single Prediction (Numeric)
```powershell
curl -X POST http://localhost:8000/predict/numeric `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_numeric.json)
```
Expected: Same format as Test 5

### Test 7: Get SHAP Explanations
```powershell
curl -X POST http://localhost:8000/explain `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```
Expected: `{"feature_importance": {...}, "shap_values": [...]}`

### Test 8: Batch Predictions
```powershell
curl -X POST http://localhost:8000/predict/file `
  -F "file=@test_data.csv"
```
Expected: `{"predictions": [...], "total_records": X}`

### Test All
```powershell
python test_fastapi.py
```

---

## Complete Workflow Examples

### Example 1: Get Prediction with Explanation
```powershell
# 1. Get latest data
$latest = curl http://localhost:8000/data/latest | ConvertFrom-Json

# 2. Make prediction
$pred = curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (ConvertTo-Json $latest) | ConvertFrom-Json

# 3. Get explanation
$explain = curl -X POST http://localhost:8000/explain `
  -H "Content-Type: application/json" `
  -d (ConvertTo-Json $latest) | ConvertFrom-Json

# Display results
Write-Host "Prediction: $($pred.direction) ($($pred.direction_confidence)%)"
Write-Host "Price Change: $($pred.price_change_pct)+%"
Write-Host "Top Features: $($explain.feature_importance | ConvertTo-Json)"
```

### Example 2: Historical Analysis
```powershell
# Get 365 days of history
$history = curl "http://localhost:8000/data/historical?limit=365" | ConvertFrom-Json

# Convert to CSV
$history | Export-Csv -Path history.csv -NoTypeInformation

# Batch predict all rows
curl -X POST http://localhost:8000/predict/file `
  -F "file=@history.csv" | ConvertFrom-Json | 
  Select-Object -ExpandProperty predictions |
  Export-Csv -Path predictions.csv -NoTypeInformation
```

### Example 3: Monitoring Loop
```powershell
for ($i = 0; $i -lt 24; $i++) {
    # Get latest
    $data = curl http://localhost:8000/data/latest | ConvertFrom-Json
    
    # Predict
    $pred = curl -X POST http://localhost:8000/predict/json `
      -H "Content-Type: application/json" `
      -d (ConvertTo-Json $data) | ConvertFrom-Json
    
    # Log
    Add-Content log.txt "$(Get-Date): $($pred.direction) - $($pred.price_change_pct)%"
    
    # Wait 1 hour
    Start-Sleep -Seconds 3600
}
```

---

## Test Files Available

| File | Contents | Use |
|------|----------|-----|
| `test_fastapi_json.json` | 49 features as JSON dict | Test `/predict/json` |
| `test_fastapi_numeric.json` | 49 features as array | Test `/predict/numeric` |
| `test_fastapi.py` | Full test suite | Run all tests at once |
| `generate_test_data.py` | Generate new test data | Recreate test files from CSV |

---

## Regenerate Test Data

If you need fresh test data from your Bitcoin CSV:

```powershell
python generate_test_data.py
```

This updates `test_fastapi_json.json` and `test_fastapi_numeric.json` with the latest Bitcoin data from `data/raw/bitcoin_timeseries.csv`.

---

## Common Issues & Fixes

### Issue: "Models not loaded"
```
Server Response: {"detail": "Models not loaded"}
```
**Fix**: 
```powershell
curl -X POST http://localhost:8000/model/reload
```

### Issue: "Data not loaded"
```
Server Response: {"detail": "Data not loaded"}
```
**Fix**: 
1. Ensure `data/raw/bitcoin_timeseries.csv` exists
2. Restart API: `python api_server.py`

### Issue: "Missing required features"
```
Server Response: {"detail": "Missing required features: [...]"}
```
**Fix**: Use the generated test files:
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```

### Issue: "CSV missing required features"
```
Server Response: {"detail": "CSV missing required features: [...]"}
```
**Fix**: Check CSV headers:
```powershell
curl http://localhost:8000/model/features | ConvertFrom-Json | Select-Object -ExpandProperty features
```

---

## Response Format Reference

### Prediction Response
```json
{
  "direction": "UP" | "DOWN",
  "direction_confidence": 0.0-100.0,
  "price_change_pct": -99.0 to 99.0,
  "current_price": 100000.50,
  "predicted_price": 102000.50,
  "price_change_usd": 2000.00,
  "timestamp": "2025-12-17T10:30:00.123456",
  "input_method": "json" | "numeric_array" | "auto_features"
}
```

### Explanation Response
```json
{
  "status": "success",
  "explanation_method": "shap_approximation",
  "prediction": {
    "price_change_pct": 2.35,
    "direction": "UP"
  },
  "feature_importance": {
    "price_to_ma7": 0.0234,
    "rsi_14": 0.0189,
    "momentum_14d": 0.0145
  },
  "shap_values": [array of 49 floats],
  "timestamp": "2025-12-17T10:30:00.123456"
}
```

### Historical Data Response
```json
[
  {
    "date": "2025-12-17T10:30:00.810156",
    "price": 104315.87,
    "volume": 4331230750.52,
    "market_cap": 1810758924588.81,
    ...
  }
]
```

---

## Next Steps

1. ✅ Read [SHAP_GUIDE.md](SHAP_GUIDE.md) - Get SHAP values
2. ✅ Read [DATA_ENDPOINTS_GUIDE.md](DATA_ENDPOINTS_GUIDE.md) - Use data endpoints
3. ✅ Read [FASTAPI_COMPLETE_GUIDE.md](FASTAPI_COMPLETE_GUIDE.md) - Full details
4. ✅ Run `python test_fastapi.py` - Test everything
5. ✅ Try the examples above - Integrate into your workflow

---

**Bottom Line**: Everything works! SHAP, data endpoints, predictions - all functional via FastAPI REST endpoints.
