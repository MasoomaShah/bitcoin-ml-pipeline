# 🎯 Quick Reference: World Bank GDP Prediction API

## Start the Server

```bash
cd "c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT"
python -m uvicorn api.main:app --reload --port 8000
```

**API URL:** http://127.0.0.1:8000  
**Swagger Docs:** http://127.0.0.1:8000/docs

---

## API Endpoints Quick Reference

### 1️⃣ Regression: Predict GDP Growth %

```bash
curl -X POST http://127.0.0.1:8000/predict/regression \
  -H "Content-Type: application/json" \
  -d '{
    "GDP": 3.73e11,
    "Population": 251269164,
    "Inflation": 12.6,
    "Unemployment": 5.47,
    "GDP_rolling3": 3.619e11
  }'
```

**Response:**
```json
{
  "prediction": 0.0847,
  "interpretation": "Predicted GDP growth: 8.47%"
}
```

---

### 2️⃣ Classification: High or Low Growth?

```bash
curl -X POST http://127.0.0.1:8000/predict/classification \
  -H "Content-Type: application/json" \
  -d '{
    "GDP": 3.73e11,
    "Population": 251269164,
    "Inflation": 12.6,
    "Unemployment": 5.47,
    "GDP_rolling3": 3.619e11
  }'
```

**Response:**
```json
{
  "classification": "High Growth (≥5%)",
  "class_value": 1,
  "probability_low_growth": 0.15,
  "probability_high_growth": 0.85
}
```

---

### 3️⃣ Both: Get Predictions in One Request

```bash
curl -X POST http://127.0.0.1:8000/predict/both \
  -H "Content-Type: application/json" \
  -d '{
    "GDP": 3.73e11,
    "Population": 251269164,
    "Inflation": 12.6,
    "Unemployment": 5.47,
    "GDP_rolling3": 3.619e11
  }'
```

**Response:** Contains both `regression` and `classification` predictions

---

### 4️⃣ Batch: Predict from CSV File

**Create CSV file `data.csv`:**
```csv
date,GDP,Population,Inflation,Unemployment,GDP_rolling3
2022-01-01,3.748903e+11,243700667,19.87,5.485,3.412775e+11
2023-01-01,3.378855e+11,247504495,30.77,5.408,3.537642e+11
2024-01-01,3.730719e+11,251269164,12.63,5.472,3.619492e+11
```

```bash
curl -X POST http://127.0.0.1:8000/predict/batch \
  -F "file=@data.csv"
```

**Response:**
```json
{
  "total_rows": 3,
  "successful_predictions": 3,
  "failed_predictions": 0,
  "results": [
    {
      "row_index": 0,
      "date": "2022-01-01",
      "regression_prediction": 0.0757,
      "classification_prediction": "High Growth (≥5%)",
      "confidence_high_growth": 0.82
    }
  ]
}
```

---

### 5️⃣ Get Model Info

```bash
curl http://127.0.0.1:8000/model-info | python -m json.tool
```

Shows: features, training dates, model metrics

---

### 6️⃣ Get Feature Names

```bash
curl http://127.0.0.1:8000/feature-columns
```

Returns: `["GDP", "Population", "Inflation", "Unemployment", "GDP_rolling3"]`

---

### 7️⃣ Reload Models

```bash
curl -X POST http://127.0.0.1:8000/reload-models
```

Reloads `reg_model.pkl`, `clf_model.pkl`, `scaler.pkl` without restarting API

---

## Python Examples

### Using requests library

```python
import requests
import json

API_URL = "http://127.0.0.1:8000"

# Predict regression
payload = {
    "GDP": 3.73e11,
    "Population": 251269164,
    "Inflation": 12.6,
    "Unemployment": 5.47,
    "GDP_rolling3": 3.619e11
}

response = requests.post(f"{API_URL}/predict/regression", json=payload)
result = response.json()
print(f"GDP Growth Prediction: {result['prediction']*100:.2f}%")

# Batch predictions
import pandas as pd
df = pd.read_csv("batch_data.csv")
with open("batch_data.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{API_URL}/predict/batch", files=files)
    
results = response.json()
print(f"Predictions: {results['successful_predictions']}/{results['total_rows']} successful")
```

---

## Feature Ranges (Pakistan Data)

Based on training data (2010–2024):

| Feature | Min | Max | Unit |
|---------|-----|-----|------|
| GDP | 1.97e11 | 3.75e11 | USD |
| Population | 199M | 251M | Count |
| Inflation | 2.5% | 30.8% | % |
| Unemployment | 0.65% | 6.3% | % |
| GDP_rolling3 | 1.95e11 | 3.62e11 | USD |

*Values outside these ranges may produce unreliable predictions.*

---

## Common Responses

### Success (200 OK)
```json
{
  "prediction": 0.0847,
  "interpretation": "..."
}
```

### Error (500 Internal Server Error)
```json
{
  "detail": "Models or artifacts not loaded"
}
```

**Fix:** Ensure `train_timeseries.py` was run and model files exist in project root

### Error (400 Bad Request)
```json
{
  "detail": "Missing required columns: ['GDP', 'Population', ...]"
}
```

**Fix:** Check CSV column names

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server won't start | Run from project root, check port 8000 not in use |
| "Models not loaded" | Run `python src/train_timeseries.py` first |
| "python-multipart not installed" | `pip install python-multipart` |
| CORS errors | Use Swagger docs instead of cross-origin requests |
| CSV upload fails | Check column names and data types (must be numeric) |

---

## Test All Endpoints

Run comprehensive tests:
```bash
python test_timeseries_api.py
```

---

## Performance Expectations

| Endpoint | Latency | Notes |
|----------|---------|-------|
| Regression | <50ms | Single prediction |
| Classification | <50ms | Single prediction |
| Batch (10 rows) | <500ms | Depends on CSV size |
| Model reload | <1s | Loads all artifacts from disk |

---

## Example Use Cases

### 1. Forecast Next Year's GDP Growth
```python
# Use latest available data
recent_indicators = {
    "GDP": 3.73e11,
    "Population": 251.3e6,
    "Inflation": 12.6,
    "Unemployment": 5.47,
    "GDP_rolling3": 3.62e11
}

response = requests.post("http://127.0.0.1:8000/predict/regression", json=recent_indicators)
growth_forecast = response.json()["prediction"]
print(f"Expected GDP growth: {growth_forecast*100:.1f}%")
```

### 2. Batch Scenario Analysis
```python
# Create 3 scenarios (optimistic, base, pessimistic)
scenarios = pd.DataFrame({
    "GDP": [3.8e11, 3.73e11, 3.65e11],  # Optimistic, base, pessimistic
    "Population": [251.3e6, 251.3e6, 251.3e6],
    "Inflation": [10.0, 12.6, 15.0],
    "Unemployment": [5.0, 5.47, 6.0],
    "GDP_rolling3": [3.62e11, 3.62e11, 3.62e11]
})

scenarios.to_csv("scenarios.csv", index=False)

# Batch predict all scenarios
with open("scenarios.csv", "rb") as f:
    response = requests.post("http://127.0.0.1:8000/predict/batch", files={"file": f})
    
results = response.json()
for scenario, pred in zip(["Optimistic", "Base", "Pessimistic"], results["results"]):
    growth = pred["regression_prediction"]
    print(f"{scenario}: {growth*100:.1f}% growth")
```

---

**Last Updated:** December 2024  
**Status:** Production Ready ✅
