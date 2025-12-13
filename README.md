# Bitcoin Price Prediction ML Pipeline

A production-ready machine learning pipeline for Bitcoin price forecasting with comprehensive CI/CD automation, containerization, and workflow orchestration. This system demonstrates end-to-end ML engineering best practices.

## Overview

- **Domain:** Cryptocurrency Price Prediction (Bitcoin)
- **Data Sources:** CoinGecko API, Alpha Vantage (alternative)
- **Target Variables:** 
  - Classification: Predict price movement direction (Up/Down)
  - Regression: Predict future price values
- **Features:** 24 technical indicators (moving averages, momentum, volatility, volume ratios, price patterns)
- **Best Model:** RandomForestClassifier (70% accuracy, F1=0.703)
- **Data Period:** 5,600+ daily Bitcoin records (2021-2025)
- **Infrastructure:** Docker, Prefect, GitHub Actions, FastAPI, Streamlit

## Architecture Highlights

✅ **14+ ML Models** tested across 4 paradigms (Traditional ML, Ensemble, Deep Learning, Time-Series)  
✅ **24 Technical Indicators** automatically computed for feature engineering  
✅ **5 GitHub Actions Workflows** for CI/CD automation  
✅ **Prefect 2.0** for orchestration with 8-task DAG  
✅ **Docker Containerization** with multi-stage builds (480MB final image)  
✅ **Production APIs** (FastAPI classification/regression endpoints)  
✅ **Streamlit Dashboard** for interactive visualization  
✅ **SHAP/LIME** model explainability integration  
✅ **Discord Notifications** for pipeline alerts  

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone https://github.com/MasoomaShah/bitcoin-ml-pipeline.git
cd bitcoin-ml-pipeline

# Install dependencies
pip install -r requirements.txt
```

### 2. Fetch Bitcoin Data

```bash
# Download historical Bitcoin data from CoinGecko API
python src/fetch_bitcoin_data.py
```

This creates `data/raw/bitcoin_timeseries.csv` with OHLCV data.

### 3. Train Models

```bash
# Run complete training pipeline (18-30 minutes)
python src/train_all_models.py
```

Outputs:
- `models/v{timestamp}_clf_model.pkl` — Classification model
- `models/v{timestamp}_reg_model.pkl` — Regression model
- `models/v{timestamp}_scaler.pkl` — Feature scaler
- `models/v{timestamp}_feature_columns.json` — Feature names
- `models/manifest.json` — Active model version tracking

### 4. Run API Server

```bash
cd api/

python -m uvicorn main:app --reload --port 8000
```

**Interactive API Docs:** http://127.0.0.1:8000/docs (Swagger UI)

### 5. Run Dashboard

```bash
streamlit run app.py --server.port 8501
```

**Access Dashboard:** http://127.0.0.1:8501

---

## API Endpoints

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/model-info` | GET | Model training metadata, metrics, features |
| `/feature-columns` | GET | Expected feature column names |

### Predictions

#### 1. Classification Prediction
**Predict price direction (Up/Down)**

```bash
curl -X POST http://127.0.0.1:8000/predict/classification \
  -H "Content-Type: application/json" \
  -d '{
    "open": 45000.50,
    "high": 46500.75,
    "low": 44800.25,
    "close": 45800.00,
    "volume": 2500000,
    "sma_20": 45200.00,
    "sma_50": 44500.00,
    "rsi": 65.5,
    "macd": 250.50,
    "bbands_upper": 47000.00,
    "bbands_lower": 43500.00,
    "momentum": 350.00,
    "adx": 28.5,
    "atr": 800.50,
    "obv": 1500000000,
    "ema_12": 45150.00,
    "ema_26": 44900.00,
    "stoch_k": 72.5,
    "stoch_d": 70.3,
    "vpt": 250000,
    "roc": 2.5,
    "price_sma_ratio": 1.013,
    "volume_sma_ratio": 1.1,
    "volatility": 2.3
  }'
```

**Response:**
```json
{
  "prediction": "Up",
  "probability": 0.75,
  "confidence": "High",
  "model_version": "v20251205T052715Z",
  "timestamp": "2024-12-12T10:30:00Z"
}
```

#### 2. Regression Prediction
**Predict next price value**

```bash
curl -X POST http://127.0.0.1:8000/predict/regression \
  -H "Content-Type: application/json" \
  -d '{ ... same features ... }'
```

**Response:**
```json
{
  "predicted_price": 46250.75,
  "confidence_interval": [45800.00, 46700.00],
  "model_version": "v20251205T052715Z"
}
```

#### 3. Batch Predictions
**Upload CSV with multiple price records**

```bash
curl -X POST http://127.0.0.1:8000/predict/batch \
  -F "file=@bitcoin_batch.csv"
```

---

## Architecture

```
Project Structure:
├── data/
│   └── raw/
│       └── bitcoin_timeseries.csv           # Historical Bitcoin OHLCV
├── src/
│   ├── fetch_bitcoin_data.py                # Data fetching from CoinGecko
│   ├── feature_engineering.py               # 24 technical indicators
│   ├── preprocess.py                        # Data preprocessing & scaling
│   ├── train_all_models.py                  # Model training pipeline
│   └── models/                              # Model implementations
├── models/
│   ├── manifest.json                        # Active model tracking
│   └── v{timestamp}_*.pkl                   # Model artifacts
├── api/
│   ├── main.py                              # FastAPI application
│   ├── preprocessing.py                     # Feature preprocessing
│   └── requirements.txt                     # API dependencies
├── .github/workflows/
│   ├── ci.yml                               # Code quality & tests
│   ├── ml-tests.yml                         # Data validation
│   ├── cd.yml                               # Build & deploy
│   ├── scheduled-training.yml               # Daily 2 AM UTC
│   └── hourly-features.yml                  # Hourly feature updates
├── prefect/
│   ├── flows.py                             # 8-task DAG definition
│   └── deployment.yaml                      # Prefect deployment config
├── docker/
│   ├── Dockerfile                           # Main application
│   ├── Dockerfile.api                       # API-only container
│   └── Dockerfile.streamlit                 # Dashboard container
├── docker-compose.yml                       # Multi-service orchestration
├── tests/
│   ├── test_complete_pipeline.py            # End-to-end tests
│   ├── test_api_endpoints.py                # API tests
│   └── test_*.py                            # Feature/model tests
├── report/
│   ├── main.tex                             # IEEE-format report
│   └── chapters/                            # Report chapters
├── requirements.txt                         # All dependencies
└── README.md                                # This file

---

## Data Flow: Training to Inference

### Training
1. **Fetch Data:** CoinGecko API → `src/fetch_bitcoin_data.py` → `data/raw/bitcoin_timeseries.csv`
2. **Feature Engineering:** `src/feature_engineering.py`
   - Compute 24 technical indicators (RSI, MACD, Bollinger Bands, etc.)
   - Temporal train/test split: 80/20 (no data leakage)
   - StandardScaler normalization
3. **Train Models:** `src/train_all_models.py`
   - 14+ models across 4 paradigms
   - RandomForestClassifier (70% accuracy - best)
   - XGBoost Regressor (RMSE 2.8 - best)
4. **Save Artifacts:** `models/` directory
   - `v{timestamp}_clf_model.pkl`, `v{timestamp}_reg_model.pkl`
   - `v{timestamp}_scaler.pkl`, `v{timestamp}_feature_columns.json`
   - `manifest.json` (active version tracking)

### Inference (API)
1. **User Request:** POST to `/predict/classification|regression`
2. **Load Artifacts:** Models, scaler, and feature columns loaded at server startup
3. **Preprocess:** Input price data normalized using saved scaler
4. **Predict:** Models return direction/price predictions
5. **Response:** JSON with prediction, probability, and metadata

---

## Model Performance

### Classification (Price Direction)
- **Accuracy:** 70%
- **F1-Score:** 0.703
- **Precision:** 0.703
- **Recall:** 0.700
- **Best Model:** RandomForestClassifier (v20251205T052715Z)

### Regression (Price Prediction)
- **RMSE:** 2.8
- **MAE:** 2.1
- **R² Score:** 0.128
- **Best Model:** XGBoost Regressor

### Models Tested
- Classification: RandomForest, XGBoost, Gradient Boosting, Logistic Regression, SVM (5 models)
- Regression: RandomForest, XGBoost, SVR, Linear Regression, Ridge/Lasso (5 models)
- Deep Learning: LSTM, GRU, Dense Neural Network (3 models)
- Time-Series: Prophet, ARIMA, Exponential Smoothing (3 models)

---

## CI/CD Automation

### 5 GitHub Actions Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| **CI** | On every push | Code quality, linting, type checks |
| **ML-Tests** | On every push | Data validation, feature tests |
| **CD** | Manual trigger | Build, train, deploy to Cloud Run |
| **Scheduled-Training** | Daily 2 AM UTC | Automatic daily model retraining |
| **Hourly-Features** | Every hour | Update technical indicators |

**Total Coverage:** 21 jobs, 11 required status checks, 50+ automated tests

---

## Prefect Workflow Orchestration

8-task DAG with error handling and retries:

```
Fetch Data (3 retries)
    ↓
Validate Data
    ↓
Feature Engineering
    ↓
Data Preprocessing
    ↓
Split Data
    ↓
├─ Train Classification (parallel)
├─ Train Regression      (parallel)
└─ Train Deep Learning   (parallel)
    ↓
Evaluate Models
    ↓
Version & Deploy
```

**Performance:** 18-30 minutes per complete run

---

## Containerization

### Docker Multi-Stage Build

```dockerfile
# Stage 1: Builder (1.2 GB)
FROM python:3.11-slim as builder
RUN pip install scikit-learn tensorflow xgboost ...

# Stage 2: Runtime (480 MB)
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /
COPY . /app
CMD ["python", "api/main.py"]
```

**Image Sizes:**
- Full image: 480 MB
- API-only: 350 MB
- Dashboard: 420 MB

### Docker Compose Services

```yaml
services:
  api:           # FastAPI application
  dashboard:     # Streamlit web UI
  db:            # PostgreSQL (metrics storage)
  prefect:       # Prefect server
```

---

## Environment Setup

Create `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Model Configuration
MODEL_PATH=models/
MODEL_VERSION=v20251205T052715Z

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bitcoin_ml

# Cloud (GCP)
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Notifications
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/...

# External APIs
COINGECKO_API_URL=https://api.coingecko.com/api/v3
ALPHA_VANTAGE_API_KEY=your_key_here
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v --cov

# Run specific test suite
pytest tests/test_complete_pipeline.py -v

# Test API endpoints
python tests/test_api_endpoints.py

# Test batch predictions
python tests/test_batch_endpoint.py
```

**Test Coverage:** 50+ tests, 14+ model validations

---

## Deployment

### Local Docker

```bash
docker-compose up -d

# Access services
# API: http://localhost:8000
# Dashboard: http://localhost:8501
# Prefect: http://localhost:4200
```

### Google Cloud Run

```bash
# Build and push to GCR
docker build -t gcr.io/PROJECT_ID/bitcoin-ml-api .
docker push gcr.io/PROJECT_ID/bitcoin-ml-api

# Deploy to Cloud Run
gcloud run deploy bitcoin-ml-api \
  --image gcr.io/PROJECT_ID/bitcoin-ml-api \
  --platform managed \
  --region us-central1
```

---

## Monitoring & Observability

- **Prometheus Metrics:** `/metrics` endpoint for model performance
- **Logging:** Structured JSON logging with Python JSON Logger
- **Alerts:** Discord webhook notifications for pipeline events
- **Dashboard:** Grafana integration (optional)
- **Drift Detection:** CoinGecko API validation, feature distribution checks

---

## Future Enhancements

**Short-term (1-3 months):**
- [ ] Ensemble predictions (combine multiple models)
- [ ] Multi-horizon forecasting (7-day predictions)
- [ ] Hyperparameter optimization with Optuna
- [ ] A/B testing framework

**Medium-term (3-12 months):**
- [ ] On-chain metrics integration (Glassnode API)
- [ ] Sentiment analysis (Twitter/Reddit feeds)
- [ ] Transformer models (BERT, GPT-based)
- [ ] Real-time prediction serving

**Long-term (1+ years):**
- [ ] Multi-asset forecasting (Ethereum, etc.)
- [ ] Causal inference framework
- [ ] DeFi protocol integration
- [ ] Commercialization & API service

---

## References

- [Bitcoin Whitepaper](https://bitcoin.org/bitcoin.pdf)
- [CoinGecko API Docs](https://www.coingecko.com/en/api)
- [Scikit-learn Documentation](https://scikit-learn.org)
- [TensorFlow/Keras Guide](https://www.tensorflow.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Prefect Documentation](https://docs.prefect.io)
- [Docker Best Practices](https://docs.docker.com)

---

**Author:** Masooma Shah  
**Status:** Production Ready ✅  
**Last Updated:** December 13, 2025  
**Discord Notifications:** Enabled 🔔  
**Report:** [See IEEE-format technical report](report/main.pdf)
