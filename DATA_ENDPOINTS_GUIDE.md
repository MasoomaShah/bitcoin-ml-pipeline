# FastAPI Data & File Upload Endpoints

## Data Endpoints Status

Your FastAPI has **3 data-related endpoints** that are fully functional:

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/data/historical` | GET | Retrieve last N records | ✓ Working |
| `/data/latest` | GET | Get latest Bitcoin data | ✓ Working |
| `/predict/file` | POST | Batch predictions from CSV | ✓ Working |

---

## 1. Get Historical Data

### Purpose
Retrieve the last N historical Bitcoin data points with all 49 engineered features.

### Command
```powershell
# Get last 100 records (default)
curl http://localhost:8000/data/historical

# Get last 50 records
curl "http://localhost:8000/data/historical?limit=50"

# Get last 365 records
curl "http://localhost:8000/data/historical?limit=365"
```

### Response Format
```json
[
  {
    "date": "2025-12-16T10:00:00",
    "price": 102500.50,
    "volume": 3500000000,
    "market_cap": 1800000000000,
    "price_smooth": 102000,
    "price_ma7": 101500,
    ...
  },
  {
    "date": "2025-12-17T10:00:00",
    "price": 104315.87,
    "volume": 4331230750,
    "market_cap": 1810758924588,
    ...
  }
]
```

### Parameters
- `limit` (optional): Number of records to return
  - Minimum: 1
  - Maximum: 1000
  - Default: 100

### Python Example
```python
import requests

# Get last 50 records
response = requests.get(
    'http://localhost:8000/data/historical',
    params={'limit': 50}
)

data = response.json()
print(f"Retrieved {len(data)} records")

# Convert to pandas DataFrame
import pandas as pd
df = pd.DataFrame(data)
print(df[['date', 'price', 'volume']].tail(10))
```

---

## 2. Get Latest Data

### Purpose
Get the most recent Bitcoin data point with all 49 features.

### Command
```powershell
curl http://localhost:8000/data/latest
```

### Response Format
```json
{
  "date": "2025-12-17T10:30:00.810156",
  "price": 104315.8739604748,
  "volume": 4331230750.52054,
  "market_cap": 1810758924588.812,
  "price_smooth": 101978.1480338101,
  "price_ma3": 101978.1480338101,
  "price_ma7": 100345.8511346383,
  "price_ma14": 100110.9300198769,
  ...
  "volume_SMA_7": 3485246301.484044
}
```

### Python Example
```python
import requests

response = requests.get('http://localhost:8000/data/latest')
latest = response.json()

print(f"Current Price: ${latest['price']:,.2f}")
print(f"Current Volume: {latest['volume']:,.0f}")
print(f"Market Cap: ${latest['market_cap']:,.0f}")
```

---

## 3. Batch Predictions from CSV File

### Purpose
Upload a CSV file with multiple rows and get predictions for all rows.

### CSV Format Requirements
The CSV must have:
- **Headers** matching the 49 feature names (exact spelling and case)
- **Rows** of data with numeric feature values
- **Optional**: `price` or `current_price` column for reference

### Example CSV Structure
```csv
price,volume,market_cap,price_smooth,price_ma3,price_ma7,...,volume_SMA_7
104315.87,4331230750.52,1810758924588.81,101978.15,101978.15,100345.85,...,3485246301.48
103500.50,4200000000,1800000000000,101500,101500,100000,...,3400000000
...
```

### Command (PowerShell)
```powershell
curl -X POST http://localhost:8000/predict/file `
  -F "file=@batch_predictions.csv"
```

### Command (Bash/Linux)
```bash
curl -X POST http://localhost:8000/predict/file \
  -F "file=@batch_predictions.csv"
```

### Response Format
```json
{
  "predictions": [
    {
      "direction": "UP",
      "direction_confidence": 72.45,
      "price_change_pct": 2.35,
      "current_price": 104315.87,
      "predicted_price": 106763.23,
      "price_change_usd": 2447.36,
      "timestamp": "2025-12-17T10:30:00.123456"
    },
    {
      "direction": "DOWN",
      "direction_confidence": 68.32,
      "price_change_pct": -1.85,
      "current_price": 103500.50,
      "predicted_price": 101583.84,
      "price_change_usd": -1916.66,
      "timestamp": "2025-12-17T10:30:00.234567"
    }
  ],
  "total_records": 2
}
```

### Python Example
```python
import requests
import pandas as pd

# Prepare CSV
df = pd.read_csv('my_data.csv')
csv_bytes = df.to_csv(index=False).encode()

# Upload and predict
files = {'file': ('data.csv', csv_bytes, 'text/csv')}
response = requests.post(
    'http://localhost:8000/predict/file',
    files=files
)

predictions = response.json()
print(f"Predictions for {predictions['total_records']} records:")
for pred in predictions['predictions']:
    print(f"  {pred['direction']} ({pred['direction_confidence']:.1f}%): "
          f"{pred['price_change_pct']:+.2f}%")
```

---

## Complete Workflow Example

### 1. Get Historical Data
```powershell
$history = curl http://localhost:8000/data/historical?limit=10 | ConvertFrom-Json
$history | Format-Table -Property date, price, volume | Out-String
```

### 2. Get Latest Data Point
```powershell
$latest = curl http://localhost:8000/data/latest | ConvertFrom-Json
Write-Host "Current Price: $($latest.price)"
```

### 3. Make Single Prediction
```powershell
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (ConvertTo-Json $latest)
```

### 4. Batch Predict Multiple Records
```powershell
# Create CSV from historical data
$csv = @"
price,volume,market_cap,price_smooth,price_ma3,price_ma7,price_ma14,price_ma30,price_ema7,price_ema14,momentum_3d,momentum_7d,momentum_14d,roc_3d,roc_7d,price_volatility_3d,price_volatility_7d,price_volatility_14d,volume_ma3,volume_ma7,volume_change,price_to_ma7,price_to_ma30,bb_middle,bb_std,bb_upper,bb_lower,bb_position,rsi_14,market_cap_change,volume_to_marketcap,SMA_7,SMA_14,SMA_30,EMA_7,EMA_14,momentum_7,momentum_14,momentum_30,volatility_7,volatility_14,RSI,MACD,MACD_signal,BB_middle,BB_upper,BB_lower,BB_width,volume_SMA_7
104315.87,4331230750.52,1810758924588,101978.15,101978.15,100345.85,100110.93,100278.84,101073.84,100481.04,4.98,6.90,0.61,4.98,6.90,4599.68,4127.04,3147.33,3757847647,3485246301,8.77,1.04,1.04,100679.28,3091.37,106862.01,94496.55,0.79,50.71,-28894366131,0.0024,100345.85,100110.93,100278.84,101073.84,100481.04,6.90,0.61,8.07,4127.04,3147.33,50.71,310.86,-24.16,100679.28,106862.01,94496.55,12365.46,3485246301
"@

$csv | Out-File batch.csv
curl -X POST http://localhost:8000/predict/file -F "file=@batch.csv"
```

---

## File Upload Troubleshooting

### Error: "CSV missing required features"
```json
{"detail": "CSV missing required features: ['volume_change', ...]"}
```

**Fix**: Check CSV headers match exactly. Run this to verify:
```powershell
curl http://localhost:8000/model/features | ConvertFrom-Json | Select-Object -ExpandProperty features
```

### Error: "File processing error"
**Fix**: Ensure:
- File is valid CSV format
- Headers are in the first row
- All values are numeric
- No blank rows or columns

### Error: "Models not loaded"
**Fix**: Restart API server:
```powershell
python api_server.py
```

---

## Usage Patterns

### Pattern 1: Real-time Single Prediction
```
1. Get latest data: GET /data/latest
2. Make prediction: POST /predict/json or /predict/numeric
```

### Pattern 2: Historical Analysis
```
1. Fetch history: GET /data/historical?limit=365
2. Batch predict: POST /predict/file (convert to CSV)
3. Analyze results
```

### Pattern 3: Continuous Monitoring
```
1. Poll /data/latest every hour
2. Make prediction
3. Store results
4. Track performance
```

### Pattern 4: Full Report
```
1. Get latest: GET /data/latest
2. Make prediction: POST /predict/json
3. Get explanation: POST /explain
4. Get history: GET /data/historical?limit=30
5. Compile report with all data
```

---

## Summary

| Need | Endpoint | Method |
|------|----------|--------|
| See latest Bitcoin data | `/data/latest` | GET |
| See historical data | `/data/historical` | GET |
| Single prediction | `/predict/json` or `/predict/numeric` | POST |
| Multiple predictions | `/predict/file` | POST |
| Explanation (SHAP) | `/explain` | POST |

✓ All endpoints fully functional and ready to use!
