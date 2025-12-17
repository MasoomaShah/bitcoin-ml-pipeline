# FastAPI Architecture & Feature Summary

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (8000)                        │
└─────────────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
    │ MODELS      │    │ DATA         │    │ EXPLANATIONS │
    │             │    │              │    │              │
    │ clf_model   │    │ Latest Data  │    │ SHAP Values  │
    │ reg_model   │    │ Historical   │    │ Importance   │
    │ scaler      │    │ Data Upload  │    │ Feature Imp. │
    └─────────────┘    └──────────────┘    └──────────────┘
         │                     │                     │
    [Predictions]          [Access]            [Explain]
    • /predict              • /data/latest      • /explain
    • /predict/json         • /data/historical
    • /predict/numeric      • /predict/file
    • /predict/file
```

---

## Three Main Categories

### 1️⃣ PREDICTIONS (Make Price Forecasts)
**When**: You want to predict Bitcoin price movement
**How**: Send features → Get direction & confidence

```
Input Features (49 features)
         ↓
    [ML Models]
    (Classification + Regression)
         ↓
Output: {
  "direction": "UP/DOWN",
  "confidence": 72.5%,
  "price_change": +2.35%
}
```

**Endpoints**:
- `GET /predict` - Auto-load latest data and predict
- `POST /predict/json` - Send features as dict
- `POST /predict/numeric` - Send features as array
- `POST /predict/file` - Batch predictions from CSV

---

### 2️⃣ DATA ACCESS (Retrieve Bitcoin Data)
**When**: You need Bitcoin price/volume/market data
**How**: Query endpoints → Get data

```
Bitcoin Historical Data (365 days in CSV)
         ↓
API Retrieves Latest/Historical
         ↓
Returns: All 49 engineered features
```

**Endpoints**:
- `GET /data/latest` - Get most recent data point
- `GET /data/historical?limit=100` - Get N recent points
- `POST /predict/file` - Upload CSV for batch processing

**Data Includes**:
- Raw: price, volume, market_cap
- Technical: 46 engineered indicators (moving averages, RSI, MACD, Bollinger Bands, etc.)

---

### 3️⃣ EXPLANATIONS (Understand Model Decisions)
**When**: You want to know WHY the model made that prediction
**How**: Send features → Get SHAP values & feature importance

```
Features (49)
         ↓
    [SHAP Analysis]
    (Permutation-based)
         ↓
Output: {
  "feature_importance": {
    "price_to_ma7": 0.0234,    ← Most important
    "rsi_14": 0.0189,
    ...
  },
  "shap_values": [49 values]  ← Individual contributions
}
```

**Endpoint**:
- `POST /explain` - Get SHAP values and feature importance

**Removed From Streamlit**: SHAP visualization was in Streamlit UI, now purely API-based (better for production)

---

## Feature Generation Pipeline

```
Raw Data (from CoinGecko API)
  ↓
  ├─ price
  ├─ volume
  └─ market_cap
       ↓
[Feature Engineering]
  ↓
  ├─ Moving Averages (MA3, MA7, MA14, MA30, EMA7, EMA14)
  ├─ Momentum (3d, 7d, 14d, momentum_7, momentum_14, momentum_30)
  ├─ Volatility (3d, 7d, 14d, vol_7, vol_14)
  ├─ Technical Indicators (RSI, MACD, Bollinger Bands)
  ├─ Ratios (price_to_ma7, price_to_ma30, volume_to_marketcap)
  └─ Derivatives (volume_change, market_cap_change)
       ↓
49 Total Features
       ↓
[ML Models]
  ├─ Classification (UP/DOWN)
  └─ Regression (% change)
       ↓
Prediction Output
```

---

## Complete Request/Response Flow

### Single Prediction Flow

```
Client Request
  ↓
POST /predict/json {
  "features": {
    "price": 104315.87,
    "volume": 4331230750,
    ...49 features...
  },
  "current_price": 104315.87
}
  ↓
API Server Validates
  ├─ Check all 49 features present
  ├─ Scale features using trained scaler
  └─ Check models loaded
  ↓
ML Models Process
  ├─ Classification: Predict UP/DOWN
  ├─ Classification: Confidence %
  └─ Regression: % price change
  ↓
Server Response
  ↓
{
  "direction": "UP",
  "direction_confidence": 72.45,
  "price_change_pct": 2.35,
  "current_price": 104315.87,
  "predicted_price": 106763.23,
  "price_change_usd": 2447.36,
  "timestamp": "2025-12-17T10:30:00",
  "input_method": "json"
}
```

### Explanation Flow

```
Client Request
  ↓
POST /explain {
  "features": {...49 features...},
  "current_price": 104315.87
}
  ↓
API Server
  ├─ Scale features
  ├─ Get model predictions
  └─ Calculate SHAP values
  ↓
SHAP Analysis
  ├─ Extract feature importance (top 15)
  ├─ Calculate feature contributions
  └─ Create SHAP values array
  ↓
Server Response
  ↓
{
  "status": "success",
  "explanation_method": "shap_approximation",
  "prediction": {
    "price_change_pct": 2.35,
    "direction": "UP"
  },
  "feature_importance": {
    "price_to_ma7": 0.0234,      ← Feature importance
    "rsi_14": 0.0189,
    "momentum_14d": 0.0145
  },
  "shap_values": [
    -0.15, 0.42, 0.03, ..., 0.09  ← 49 SHAP values
  ],
  "timestamp": "2025-12-17T10:30:00"
}
```

### Batch Prediction Flow

```
Client Request
  ↓
POST /predict/file {
  file: data.csv (with 49 columns)
}
  ↓
API Server
  ├─ Parse CSV
  ├─ Validate columns
  └─ Loop through rows
  ↓
For Each Row
  ├─ Extract 49 features
  ├─ Scale features
  ├─ Run ML models
  └─ Store prediction
  ↓
Server Response
  ↓
{
  "predictions": [
    {direction, confidence, price_change_pct, ...},
    {direction, confidence, price_change_pct, ...},
    ...
  ],
  "total_records": 100
}
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Server Startup                      │
└──────────────────────────────────────────────────────────────┘
  ↓
  ├─→ load_models()
  │    ├─ Load clf_model.pkl (classification)
  │    ├─ Load reg_model.pkl (regression)
  │    ├─ Load scaler.pkl (feature scaling)
  │    ├─ Load feature_columns.json (49 feature names)
  │    └─ Load training_metadata.json
  │
  └─→ load_data()
       └─ Load bitcoin_timeseries.csv
            ├─ 365 days of Bitcoin data
            ├─ Raw + 46 engineered features
            └─ Ready for /data/* endpoints


Request Handling:
  ↓
IF /predict* THEN
  ├─ Validate 49 features
  ├─ Scale using scaler
  ├─ Run clf_model (0=DOWN, 1=UP)
  ├─ Run reg_model (% change)
  └─ Return prediction

IF /explain THEN
  ├─ Validate 49 features
  ├─ Scale using scaler
  ├─ Run models
  ├─ Calculate SHAP values
  └─ Return explanation

IF /data/* THEN
  ├─ Return from bitcoin_data
  └─ No model needed

IF /predict/file THEN
  ├─ Parse CSV
  ├─ For each row: /predict/json
  └─ Return array of predictions
```

---

## File Dependencies

```
api_server.py (Main API)
  ├─ clf_model.pkl ←─── Classification model
  ├─ reg_model.pkl ←─── Regression model
  ├─ scaler.pkl ←─── Feature scaler
  ├─ feature_columns.json ←─── Feature names (49)
  ├─ training_metadata.json ←─── Model metrics
  └─ data/raw/bitcoin_timeseries.csv ←─── Historical data

Test Files:
  ├─ test_fastapi_json.json ←─── Test with 49 features (dict format)
  ├─ test_fastapi_numeric.json ←─── Test with 49 features (array format)
  ├─ test_fastapi.py ←─── Automated test suite
  └─ generate_test_data.py ←─── Regenerate test data
```

---

## Current Status ✓

| Component | Status | Details |
|-----------|--------|---------|
| API Server | ✓ Working | FastAPI with 13 endpoints |
| Models | ✓ Loaded | RF Classifier & Regressor |
| Data | ✓ Available | 365 days Bitcoin history |
| Features | ✓ Complete | 49 engineered indicators |
| SHAP | ✓ Available | Via `/explain` endpoint |
| Data Endpoints | ✓ Working | Historical, latest, upload |
| Test Data | ✓ Ready | JSON and numeric formats |
| Predictions | ✓ Functional | Single and batch modes |

---

## Integration Checklist

```
Before Production:
  ☐ Verify all 13 endpoints working: python test_fastapi.py
  ☐ Test SHAP endpoint: POST /explain
  ☐ Test data endpoints: GET /data/latest, /data/historical
  ☐ Test batch predictions: POST /predict/file
  ☐ Verify feature scaling is correct
  ☐ Check model performance metrics
  ☐ Set up monitoring/logging
  ☐ Configure CORS for your frontend
  ☐ Set up authentication (if needed)
  ☐ Deploy to production server

Optional Enhancements:
  ☐ Add API authentication (JWT tokens)
  ☐ Add rate limiting
  ☐ Add logging/monitoring
  ☐ Cache popular predictions
  ☐ Add GraphQL interface
  ☐ Add WebSocket for real-time updates
```

---

## Quick Command Reference

```powershell
# Start server
python api_server.py

# Test health
curl http://localhost:8000/health

# Get latest data
curl http://localhost:8000/data/latest

# Single prediction
curl -X POST http://localhost:8000/predict/json `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)

# Get explanation (SHAP)
curl -X POST http://localhost:8000/explain `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)

# Batch prediction
curl -X POST http://localhost:8000/predict/file `
  -F "file=@batch.csv"

# Run all tests
python test_fastapi.py

# Regenerate test data
python generate_test_data.py

# Check endpoints
curl http://localhost:8000/model/features
```

---

## Summary

✅ **All functionality working**:
- SHAP values → `/explain` endpoint
- Data access → `/data/*` endpoints  
- Predictions → `/predict*` endpoints
- Batch processing → `/predict/file` endpoint

Nothing needs to be removed. Everything is operational and well-documented!
