# World Bank GDP Growth Predictor

A production-ready ML API for predicting economic indicators using World Bank data. Provides both **regression** (predict GDP growth %) and **classification** (predict high/low growth periods).

## Overview

- **Domain:** World Bank Economic Indicators (Pakistan)
- **Data Source:** World Bank API (freely available global economic data)
- **Target Variable:** GDP Growth Rate (%) — annual change in GDP
- **Features:** GDP, Population, Inflation Rate, Unemployment Rate, 3-Year Rolling GDP Average
- **Models:** 
  - Regression: RandomForest predicting GDP growth percentage
  - Classification: RandomForest predicting High (≥5%) vs Low (<5%) growth
- **Data Period:** 2010–2024 (15 years)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install python-multipart  # For file upload support
```

### 2. Fetch and Train Models

```bash
# Fetch World Bank data for Pakistan and save to CSV
python untitled1.py

# Train regression and classification models (saves artifacts to project root)
python src/train_timeseries.py
```

This will create:
- `reg_model.pkl` — Trained regression model
- `clf_model.pkl` — Trained classification model
- `scaler.pkl` — StandardScaler for feature normalization
- `feature_columns.json` — Expected feature column names
- `training_metadata.json` — Metrics and training metadata

### 3. Run the API Server

```bash
cd c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT

python -m uvicorn api.main:app --reload --port 8000
```

Server will start at `http://127.0.0.1:8000`

**Interactive API Docs:** http://127.0.0.1:8000/docs (Swagger UI)

---

## API Endpoints

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/model-info` | GET | Model training metadata, metrics, features |
| `/feature-columns` | GET | Expected feature column names |

### Predictions

#### 1. Regression Prediction
**Predict GDP growth percentage**

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
  "interpretation": "Predicted GDP growth: 8.47%",
  "input_indicators": { ... }
}
```

#### 2. Classification Prediction
**Classify as High (≥5%) or Low (<5%) growth**

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
  "probability_high_growth": 0.85,
  "input_indicators": { ... }
}
```

#### 3. Combined Predictions
**Get both regression and classification in one request**

```bash
curl -X POST http://127.0.0.1:8000/predict/both \
  -H "Content-Type: application/json" \
  -d '{ ... same payload ... }'
```

#### 4. Batch Predictions (CSV Upload)
**Upload CSV file with multiple economic indicators**

CSV format (required columns):
```csv
date,GDP,Population,Inflation,Unemployment,GDP_rolling3
2022-01-01,3.748903e+11,243700667,19.87,5.485,3.412775e+11
2023-01-01,3.378855e+11,247504495,30.77,5.408,3.537642e+11
2024-01-01,3.730719e+11,251269164,12.63,5.472,3.619492e+11
```

```bash
curl -X POST http://127.0.0.1:8000/predict/batch \
  -F "file=@batch_data.csv"
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
    },
    ...
  ]
}
```

#### 5. Reload Models (Runtime)
**Reload trained models and preprocessing artifacts without restarting the API**

```bash
curl -X POST http://127.0.0.1:8000/reload-models
```

**Optional Token Protection:**
```bash
# Set env var: MODEL_RELOAD_TOKEN=my_secret_token
curl -X POST "http://127.0.0.1:8000/reload-models?token=my_secret_token"
```

---

## Architecture

```
Project Structure:
├── untitled1.py                          # World Bank data fetching script
├── data/
│   └── raw/
│       └── world_bank_gdp.csv           # Raw data (fetched from World Bank API)
├── src/
│   ├── preprocess_timeseries.py         # Time-series preprocessing (scaling, temporal splits)
│   ├── train_timeseries.py              # Training pipeline (regression + classification)
│   ├── models/
│   │   ├── regression.py                # Regression model training logic
│   │   └── classification.py            # Classification model training logic
├── api/
│   └── main.py                          # FastAPI application (all endpoints)
├── tests/
│   └── test_timeseries_api.py           # API endpoint tests
├── reg_model.pkl                        # Trained regression model
├── clf_model.pkl                        # Trained classification model
├── scaler.pkl                           # StandardScaler (feature normalization)
├── feature_columns.json                 # Feature column names (for alignment)
└── training_metadata.json               # Training metrics and metadata
```

---

## Data Flow: Training to Inference

### Training
1. **Fetch Data:** World Bank API → `untitled1.py` → `data/raw/world_bank_gdp.csv`
2. **Preprocess:** `src/preprocess_timeseries.py`
   - Temporal train/test split (no data leakage): 2010–2022 (train), 2023–2024 (test)
   - StandardScaler normalization
   - Forward/backward fill for missing values
3. **Train Models:** `src/train_timeseries.py`
   - RandomForestRegressor (GDP growth %)
   - RandomForestClassifier (High/Low growth)
4. **Save Artifacts:** Project root
   - `reg_model.pkl`, `clf_model.pkl`, `scaler.pkl`, `feature_columns.json`, `training_metadata.json`

### Inference (API)
1. **User Request:** POST to `/predict/regression|classification|both`
2. **Load Artifacts:** Models, scaler, and feature columns loaded at server startup
3. **Preprocess:** Input indicators normalized using saved scaler
4. **Predict:** Models return predictions
5. **Response:** JSON with prediction, confidence, and metadata

---

## Model Performance

**Regression (GDP Growth Prediction):**
- Train RMSE: 0.054 (5.4 percentage points)
- Train R²: 0.444
- Test RMSE: 0.102 (10.2 percentage points)
- Test R²: -0.018 (limited test data: 2 years)

**Classification (High vs Low Growth):**
- Train Accuracy: 100%
- Train Precision: 100%
- Train Recall: 100%
- Test Accuracy: 50% (due to small test set)

*Note: Test set is small (2 years) due to limited historical data. Model improves with more historical data.*

---

## Environment Variables (Optional)

Create a `.env` file at project root:

```env
# MODEL RELOAD PROTECTION
MODEL_RELOAD_TOKEN=your_secret_token_here

# WORLD BANK API (if used for live data fetching)
# (World Bank API is free and does not require authentication)

# DATABASE (future use)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
```

Load via `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Testing

Run the comprehensive test suite:

```bash
# Start API server first (in one terminal)
python -m uvicorn api.main:app --reload --port 8000

# In another terminal, run tests
python test_timeseries_api.py
```

Tests cover:
- Health check
- Model info retrieval
- Regression prediction
- Classification prediction
- Combined predictions
- Batch predictions (CSV upload)
- Model reload endpoint

---

## Future Enhancements

- [ ] **Prefect Orchestration:** Automate data fetch → train → validate → deploy
- [ ] **DeepChecks Integration:** Monitor data drift, feature distribution, model performance
- [ ] **GitHub Actions CI/CD:** Auto-run tests, DeepChecks, build & push Docker image
- [ ] **Model Versioning:** Save timestamped model versions, compare metrics
- [ ] **Caching:** Redis cache for TMDB responses and predictions
- [ ] **Monitoring:** Prometheus metrics, Grafana dashboards
- [ ] **Containerization:** Docker & docker-compose for local dev and production

---

## Troubleshooting

**"Models not loaded" error:**
- Ensure `train_timeseries.py` was run successfully
- Check that model files exist in project root: `reg_model.pkl`, `clf_model.pkl`

**"python-multipart not installed":**
```bash
pip install python-multipart
```

**"No module named 'src'":**
- Run API from project root: `cd c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT`
- Run: `python -m uvicorn api.main:app --port 8000`

**Test dataset too small:**
- Currently using 15 years of data (2010–2024)
- For better models, expand to more countries or longer historical periods

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [scikit-learn RandomForest](https://scikit-learn.org/stable/modules/ensemble.html#forests)
- [World Bank API](https://data.worldbank.org)

---

**Author:** ML Project Team  
**Last Updated:** December 2024
