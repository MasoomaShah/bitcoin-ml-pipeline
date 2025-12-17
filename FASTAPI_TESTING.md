# FastAPI Testing Guide

## Quick Start - Test Commands

### 1. Check Server Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-01-15T10:30:00"}
```

---

## JSON Endpoint - `/predict/json`

### Test Data File: `test_fastapi_json.json`
Contains all 49 features as a dictionary with realistic Bitcoin values.

### Command:
```bash
curl -X POST http://localhost:8000/predict/json \
  -H "Content-Type: application/json" \
  -d @test_fastapi_json.json
```

### Response Example:
```json
{
  "direction": "UP",
  "direction_confidence": 72.5,
  "price_change_pct": 2.35,
  "current_price": 97650.50,
  "predicted_price": 99943.06,
  "price_change_usd": 2292.56,
  "timestamp": "2024-01-15T10:30:00.123456",
  "input_method": "json"
}
```

### Using Python:
```python
import requests
import json

with open('test_fastapi_json.json') as f:
    data = json.load(f)

response = requests.post('http://localhost:8000/predict/json', json=data)
print(response.json())
```

---

## Numeric Array Endpoint - `/predict/numeric`

### Test Data File: `test_fastapi_numeric.json`
Contains 49 features as a numeric array in the exact order from `/model/features`.

### Command:
```bash
curl -X POST http://localhost:8000/predict/numeric \
  -H "Content-Type: application/json" \
  -d @test_fastapi_numeric.json
```

### Response Example:
```json
{
  "direction": "DOWN",
  "direction_confidence": 68.3,
  "price_change_pct": -1.85,
  "current_price": 97650.50,
  "predicted_price": 95945.68,
  "price_change_usd": -1704.82,
  "timestamp": "2024-01-15T10:30:00.234567",
  "input_method": "numeric_array"
}
```

### Using Python:
```python
import requests
import json

with open('test_fastapi_numeric.json') as f:
    data = json.load(f)

response = requests.post('http://localhost:8000/predict/numeric', json=data)
print(response.json())
```

---

## Auto-Load Latest Data Endpoint - `/predict`

### Issue: Data Loading
This endpoint tries to load the latest Bitcoin features from:
1. `data/raw/bitcoin_timeseries.csv`
2. `data/processed/*.csv`
3. `data/features/*.csv`

If these files don't exist, the endpoint will fail.

### Command:
```bash
curl http://localhost:8000/predict
```

### Expected Response (if data found):
```json
{
  "direction": "UP",
  "direction_confidence": 71.2,
  "price_change_pct": 1.92,
  "current_price": 97650.50,
  "predicted_price": 99522.45,
  "price_change_usd": 1871.95,
  "timestamp": "2024-01-15T10:30:00.345678",
  "input_method": "auto_load"
}
```

### Error (if data not found):
```json
{"detail": "Data loading error: No data files found"}
```

### Fix:
Run the training pipeline first to generate data files:
```bash
python ml_pipeline.py
```

Or ensure hourly workflow has run to create `data/features/btc_features_*.csv`

---

## Get Model Metadata

### Get Feature Names and Order:
```bash
curl http://localhost:8000/model/features
```

Response:
```json
{
  "feature_columns": [
    "price",
    "volume",
    "market_cap",
    "price_smooth",
    ...
  ],
  "total_features": 49
}
```

### Get Model Info:
```bash
curl http://localhost:8000/model/info
```

---

## Troubleshooting

### Error: "Models not loaded"
```
Server response: {"detail": "Models not loaded"}
```
**Fix**: Call `/model/reload` to force reload:
```bash
curl -X POST http://localhost:8000/model/reload
```

### Error: "Missing required features"
```
Server response: {"detail": "Missing required features: ['volume_change', ...]"}
```
**Fix**: Ensure all 49 features are in JSON object. Check `/model/features` endpoint.

### Error: "Expected 49 features, got X"
```
Server response: {"detail": "Expected 49 features, got 48"}
```
**Fix**: Numeric array must have exactly 49 elements in the correct order. Use `/model/features` to verify.

### Error: "Data loading error"
```
Server response: {"detail": "Data loading error: No data files found"}
```
**Fix**: 
1. Run training pipeline: `python ml_pipeline.py`
2. Or run hourly workflow to generate features: `.github/workflows/hourly-features.yml`
3. Or place Bitcoin data in `data/raw/bitcoin_timeseries.csv`

---

## Feature Order (for numeric array)

The 49 features in order (for `/predict/numeric`):

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

1. **Test JSON endpoint**:
   ```bash
   curl -X POST http://localhost:8000/predict/json -H "Content-Type: application/json" -d @test_fastapi_json.json
   ```

2. **Test numeric endpoint**:
   ```bash
   curl -X POST http://localhost:8000/predict/numeric -H "Content-Type: application/json" -d @test_fastapi_numeric.json
   ```

3. **Fix data loading for `/predict` endpoint**:
   - Run `python ml_pipeline.py` to generate training data
   - Or configure data file location in `api_server.py`

4. **Optional: Add `/latest` endpoint**:
   - Currently not implemented
   - Would fetch the most recent Bitcoin data from CoinGecko
   - Request feature if needed
