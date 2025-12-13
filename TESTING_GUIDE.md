# How to Test the API

## Quick Start

### 1. Ensure Docker Containers are Running
```powershell
docker compose ps
```

All containers should show "Up (healthy)".

### 2. Test Using the Comprehensive Test Script
```powershell
python test_complete_api.py
```

This will test all endpoints including SHAP explainability.

---

## Testing Individual Endpoints

### Example Files Provided
- **example_input.json** - Single prediction with JSON
- **example_batch.csv** - Batch predictions from CSV

### Test 1: JSON Input
```powershell
# PowerShell
$body = Get-Content example_input.json
Invoke-RestMethod -Uri "http://localhost:8000/predict/json" `
    -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json
```

### Test 2: SHAP Explanation (Feature Importance)
```powershell
# PowerShell
$body = Get-Content example_input.json
Invoke-RestMethod -Uri "http://localhost:8000/explain" `
    -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5
```

### Test 3: Batch Predictions from CSV
```python
# Python
import requests

with open('example_batch.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/predict/file', files=files)
    print(response.json())
```

### Test 4: Automatic Prediction
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/predict" | ConvertTo-Json
```

---

## Using Swagger UI (Easiest Method!)

1. Open: **http://localhost:8000/docs**
2. Click any endpoint to expand it
3. Click "Try it out"
4. Enter the example data:
```json
{
  "features": {
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
  },
  "current_price": 96500
}
```
5. Click "Execute"

---

## Expected Output

### Prediction Response
```json
{
  "direction": "UP",
  "direction_confidence": 67.33,
  "price_change_pct": 2.5,
  "current_price": 96500.00,
  "predicted_price": 98912.50,
  "price_change_usd": 2412.50,
  "timestamp": "2025-12-09T10:00:00",
  "input_method": "json"
}
```

### SHAP Explanation Response
```json
{
  "feature_importance": {
    "Close": 0.125,
    "RSI": 0.089,
    "MACD": 0.067,
    ...
  },
  "shap_values": [0.05, -0.02, ...],
  "base_value": 0.5,
  "prediction": 0.6733,
  "explanation_method": "shap",
  "timestamp": "2025-12-09T10:00:00"
}
```

The `feature_importance` shows which features most influenced the prediction!

---

## Troubleshooting

### If SHAP is not installed:
The API will still work but use fallback feature importance:
```json
{
  "explanation_method": "model_feature_importance"
}
```

To enable full SHAP support:
```powershell
# Rebuild containers with SHAP
docker compose down
docker compose up --build
```

### If API is not responding:
```powershell
# Check container status
docker compose ps

# View logs
docker compose logs api

# Restart if needed
docker compose restart api
```

---

## All Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /predict | Automatic prediction |
| POST | /predict/json | Custom JSON input |
| POST | /predict/numeric | Numeric array input |
| POST | /predict/file | Batch CSV upload |
| POST | /explain | SHAP explainability |
| GET | /model/features | Feature names |
| GET | /model/info | Model metadata |
| GET | /health | Health check |
| GET | /docs | Interactive docs |

---

## Quick Commands

```powershell
# Run all tests
python test_complete_api.py

# Test single prediction
python test_api_endpoints.py

# Open interactive docs
start http://localhost:8000/docs

# Open dashboard
start http://localhost:8501
```
