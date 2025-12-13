# Bitcoin ML Prediction API - Complete Guide

## Overview

The Bitcoin ML Prediction API provides multiple endpoints for making Bitcoin price predictions using trained machine learning models. The API supports **three different input types**:

1. **Automatic Prediction** - Uses latest live data
2. **JSON Input** - Custom feature dictionary
3. **Numeric Array Input** - Feature values as array
4. **File Upload** - Batch predictions from CSV files

**Base URL**: `http://localhost:8000`  
**Documentation**: `http://localhost:8000/docs` (Interactive Swagger UI)

---

## Quick Start

### 1. Check API Health
```bash
GET http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "data_available": true,
  "timestamp": "2025-12-09T10:47:00.000000"
}
```

---

## Prediction Endpoints

### Method 1: Automatic Prediction (GET)

**No input required** - Uses latest live Bitcoin data.

```bash
GET http://localhost:8000/predict
```

**Response**:
```json
{
  "direction": "UP",
  "direction_confidence": 59.67,
  "price_change_pct": -3.76,
  "current_price": 95500.00,
  "predicted_price": 96200.50,
  "price_change_usd": 700.50,
  "timestamp": "2025-12-09T10:47:00.000000",
  "input_method": "automatic"
}
```

---

### Method 2: JSON Input (POST)

**Custom feature values** as JSON dictionary.

**Endpoint**: `POST http://localhost:8000/predict/json`

**Request Body**:
```json
{
  "features": {
    "Open": 95000,
    "High": 96500,
    "Low": 94500,
    "Close": 95500,
    "Volume": 25000000,
    "SMA_7": 94500,
    "SMA_14": 93000,
    "SMA_30": 91000,
    "EMA_7": 95000,
    "EMA_14": 94000,
    "momentum_7": 1500,
    "momentum_14": 3000,
    "momentum_30": 5000,
    "volatility_7": 800,
    "volatility_14": 1200,
    "RSI": 65.5,
    "MACD": 250,
    "MACD_signal": 200,
    "BB_middle": 95000,
    "BB_upper": 97000,
    "BB_lower": 93000,
    "BB_width": 4000,
    "volume_SMA_7": 24000000,
    "volume_change": 0.05
  },
  "current_price": 95500
}
```

**Python Example**:
```python
import requests

data = {
    "features": {
        "Open": 95000,
        "High": 96500,
        # ... all 24 features
    },
    "current_price": 95500
}

response = requests.post(
    "http://localhost:8000/predict/json",
    json=data
)
print(response.json())
```

**PowerShell Example**:
```powershell
$body = @{
    features = @{
        Open = 95000
        High = 96500
        # ... all 24 features
    }
    current_price = 95500
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/predict/json" `
    -Method Post -Body $body -ContentType "application/json"
```

---

### Method 3: Numeric Array Input (POST)

**Feature values as array** in specific order.

**Endpoint**: `POST http://localhost:8000/predict/numeric`

**Request Body**:
```json
{
  "features": [
    95000, 96500, 94500, 95500, 25000000,
    94500, 93000, 91000, 95000, 94000,
    1500, 3000, 5000, 800, 1200,
    65.5, 250, 200, 95000, 97000,
    93000, 4000, 24000000, 0.05
  ],
  "current_price": 95500
}
```

**Python Example**:
```python
import requests

data = {
    "features": [
        95000, 96500, 94500, 95500, 25000000,  # OHLCV
        94500, 93000, 91000,  # SMAs
        95000, 94000,  # EMAs
        1500, 3000, 5000,  # Momentum
        800, 1200,  # Volatility
        65.5, 250, 200,  # RSI, MACD, Signal
        95000, 97000, 93000, 4000,  # Bollinger Bands
        24000000, 0.05  # Volume metrics
    ],
    "current_price": 95500
}

response = requests.post(
    "http://localhost:8000/predict/numeric",
    json=data
)
print(response.json())
```

**Feature Order** (24 features):
1. Open
2. High
3. Low
4. Close
5. Volume
6. SMA_7
7. SMA_14
8. SMA_30
9. EMA_7
10. EMA_14
11. momentum_7
12. momentum_14
13. momentum_30
14. volatility_7
15. volatility_14
16. RSI
17. MACD
18. MACD_signal
19. BB_middle
20. BB_upper
21. BB_lower
22. BB_width
23. volume_SMA_7
24. volume_change

---

### Method 4: File Upload (POST)

**Batch predictions** from CSV file.

**Endpoint**: `POST http://localhost:8000/predict/file`

**CSV Format**:
- Must include all 24 feature columns
- Can include `Close` column for current price
- Returns predictions for all rows

**Example CSV** (`test_data.csv`):
```csv
Open,High,Low,Close,Volume,SMA_7,SMA_14,SMA_30,EMA_7,EMA_14,momentum_7,momentum_14,momentum_30,volatility_7,volatility_14,RSI,MACD,MACD_signal,BB_middle,BB_upper,BB_lower,BB_width,volume_SMA_7,volume_change
95000,96500,94500,95500,25000000,94500,93000,91000,95000,94000,1500,3000,5000,800,1200,65.5,250,200,95000,97000,93000,4000,24000000,0.05
96000,97000,95500,96200,26000000,95000,93500,91500,95500,94500,1600,3200,5200,850,1250,67.2,280,220,95500,97500,93500,4000,24500000,0.04
```

**Python Example**:
```python
import requests

with open('test_data.csv', 'rb') as f:
    files = {'file': ('test_data.csv', f, 'text/csv')}
    response = requests.post(
        'http://localhost:8000/predict/file',
        files=files
    )

data = response.json()
print(f"Total predictions: {data['total_records']}")
for pred in data['predictions']:
    print(f"{pred['direction']}: ${pred['predicted_price']:.2f}")
```

**Response**:
```json
{
  "predictions": [
    {
      "direction": "UP",
      "direction_confidence": 67.33,
      "price_change_pct": 2.5,
      "current_price": 95500.00,
      "predicted_price": 97887.50,
      "price_change_usd": 2387.50,
      "timestamp": "2025-12-09T10:47:00.000000",
      "input_method": "csv_file"
    },
    {
      "direction": "UP",
      "direction_confidence": 68.12,
      "price_change_pct": 2.8,
      "current_price": 96200.00,
      "predicted_price": 98894.00,
      "price_change_usd": 2694.00,
      "timestamp": "2025-12-09T10:47:00.000000",
      "input_method": "csv_file"
    }
  ],
  "total_records": 2,
  "timestamp": "2025-12-09T10:47:00.000000"
}
```

---

## Utility Endpoints

### Get Feature Names
Returns list of required features in correct order.

```bash
GET http://localhost:8000/model/features
```

**Response**:
```json
{
  "features": [
    "Open", "High", "Low", "Close", "Volume",
    "SMA_7", "SMA_14", "SMA_30", "EMA_7", "EMA_14",
    "momentum_7", "momentum_14", "momentum_30",
    "volatility_7", "volatility_14",
    "RSI", "MACD", "MACD_signal",
    "BB_middle", "BB_upper", "BB_lower", "BB_width",
    "volume_SMA_7", "volume_change"
  ],
  "count": 24,
  "description": "Features must be provided in this exact order for numeric array input"
}
```

### Get Model Info
Returns model metadata and performance metrics.

```bash
GET http://localhost:8000/model/info
```

**Response**:
```json
{
  "version": "v20251208T075527Z",
  "timestamp": "2025-12-08T07:55:27Z",
  "classification_accuracy": 0.5616,
  "regression_rmse": 0.2358,
  "regression_r2": 0.4523,
  "classification_f1": 0.5789,
  "features_count": 24
}
```

### Get Historical Data
Returns historical Bitcoin data with features.

```bash
GET http://localhost:8000/data/historical?limit=100
```

**Query Parameters**:
- `limit` (optional): Number of records (1-1000, default: 100)

---

## Response Fields

All prediction responses include:

| Field | Type | Description |
|-------|------|-------------|
| `direction` | string | "UP" or "DOWN" |
| `direction_confidence` | float | Confidence percentage (0-100) |
| `price_change_pct` | float | Predicted price change % |
| `current_price` | float | Current Bitcoin price ($) |
| `predicted_price` | float | Predicted Bitcoin price ($) |
| `price_change_usd` | float | Predicted change in USD |
| `timestamp` | string | ISO 8601 timestamp |
| `input_method` | string | "automatic", "json", "numeric_array", or "csv_file" |

---

## Error Responses

### 400 Bad Request
Missing or invalid input data.

```json
{
  "detail": "Missing required features: ['RSI', 'MACD']"
}
```

### 500 Internal Server Error
Prediction processing error.

```json
{
  "detail": "Prediction error: 'close'"
}
```

### 503 Service Unavailable
Models or data not loaded.

```json
{
  "detail": "Models or data not loaded"
}
```

---

## Testing

### Using Python
Run the included test script:
```bash
python test_api_endpoints.py
```

### Using Swagger UI
Open interactive documentation:
```
http://localhost:8000/docs
```

- Try all endpoints interactively
- See request/response schemas
- Download OpenAPI specification

### Using cURL
```bash
# Automatic prediction
curl http://localhost:8000/predict

# JSON input
curl -X POST http://localhost:8000/predict/json \
  -H "Content-Type: application/json" \
  -d @request.json

# File upload
curl -X POST http://localhost:8000/predict/file \
  -F "file=@test_data.csv"
```

---

## Feature Descriptions

| Feature | Description |
|---------|-------------|
| **OHLCV** | |
| Open | Opening price |
| High | Highest price |
| Low | Lowest price |
| Close | Closing price |
| Volume | Trading volume |
| **Moving Averages** | |
| SMA_7 | 7-day Simple Moving Average |
| SMA_14 | 14-day Simple Moving Average |
| SMA_30 | 30-day Simple Moving Average |
| EMA_7 | 7-day Exponential Moving Average |
| EMA_14 | 14-day Exponential Moving Average |
| **Momentum** | |
| momentum_7 | 7-day momentum |
| momentum_14 | 14-day momentum |
| momentum_30 | 30-day momentum |
| **Volatility** | |
| volatility_7 | 7-day volatility |
| volatility_14 | 14-day volatility |
| **Technical Indicators** | |
| RSI | Relative Strength Index |
| MACD | Moving Average Convergence Divergence |
| MACD_signal | MACD signal line |
| **Bollinger Bands** | |
| BB_middle | Middle band |
| BB_upper | Upper band |
| BB_lower | Lower band |
| BB_width | Band width |
| **Volume Metrics** | |
| volume_SMA_7 | 7-day volume moving average |
| volume_change | Volume change rate |

---

## Best Practices

1. **Use appropriate input method**:
   - Automatic: Quick predictions with live data
   - JSON: Custom scenarios with specific features
   - Numeric: Integration with numerical systems
   - File: Batch processing multiple predictions

2. **Validate inputs**:
   - All 24 features are required
   - Check feature order for numeric arrays
   - Ensure CSV has proper column names

3. **Handle errors gracefully**:
   - Check HTTP status codes
   - Parse error messages
   - Retry on 503 (service unavailable)

4. **Optimize performance**:
   - Use batch predictions for multiple records
   - Cache feature list to avoid repeated calls
   - Reuse connections for multiple requests

---

## Docker Deployment

The API runs in a Docker container:

```bash
# Start services
docker compose up -d

# Check API status
docker compose ps api

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

**Ports**:
- API: `8000`
- Dashboard: `8501`
- Database: `5432`

---

## Support

For issues or questions:
1. Check `/docs` for interactive API documentation
2. Review error messages in response
3. Check container logs: `docker compose logs api`
4. Verify models are loaded: `GET /health`
