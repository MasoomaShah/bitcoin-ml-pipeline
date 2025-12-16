# Vertex AI Integration - Complete Architecture

## Overview

Your ML system has been upgraded to use **Google Cloud Vertex AI** for:
1. **Feature Store** - Store and retrieve technical indicators
2. **Model Storage** - Cloud Storage for trained models  
3. **Unified Loading** - Single API for FastAPI, Streamlit, and batch inference

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA & TRAINING                             │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            Bitcoin CSV              Live API (CoinGecko)
            data/raw/                   fetch_bitcoin_data()
                    │                         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────v────────────┐
                    │  Feature Engineering    │
                    │  (Technical Indicators) │
                    │  49 features computed   │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        v                        v                        v
    Local Use          Feature Store              Cloud Storage
   (Training)          (Vertex AI)                (GCS Bucket)
        │           Upload Features                 Upload Models
        │                  │                           │
        v                  v                           v
   ┌─────────────┐  ┌──────────────────┐      ┌──────────────────┐
   │Local Model  │  │Vertex AI Feature │      │Cloud Storage     │
   │Training     │  │Store (BigQuery)  │      │gs://bucket/      │
   │(Local)      │  │- 49 Features     │      │models/v*         │
   │             │  │- Versioned       │      │- Models.pkl      │
   │             │  │- Queryable       │      │- Scaler.pkl      │
   │             │  │- Monitored       │      │- Metadata.json   │
   └─────────────┘  └──────────────────┘      └──────────────────┘
        │                  │                          │
        │        ┌─────────┘                          │
        │        │                                    │
        └────────┼────────────────────────────────────┘
                 │
    ┌────────────v─────────────┐
    │ load_models_from_        │
    │ vertex_ai()              │
    │                          │
    │ 1. Try Feature Store     │────> Read 49 features
    │ 2. Try Cloud Storage     │────> Download models
    │ 3. Fallback Local        │────> Read from disk
    └────────────┬─────────────┘
                 │
        ┌────────v────────┐
        │  Models Loaded  │
        │                 │
        │- clf_model      │
        │- reg_model      │
        │- scaler         │
        │- features (49)  │
        │- metadata       │
        └────────┬────────┘
                 │
    ┌────────────┴───────────────────┐
    │                                │
    v                                v
 FastAPI                         Streamlit
/predict/json              app.py
/predict/numeric           Cache & Serve
/model/features            (Same Models)
```

---

## System Components

### 1. Feature Engineering (`src/fetch_bitcoin_data.py` + `src/preprocess_bitcoin.py`)
- **Input**: Bitcoin daily data (price, market cap, volume)
- **Output**: 49 technical indicators
- **Cached in**: Vertex AI Feature Store (BigQuery)

**49 Features**:
```
Price Indicators:
- price, price_smooth, price_ma3, price_ma7, price_ma14, price_ma30
- price_ema7, price_ema14

Moving Averages:
- SMA_7, SMA_14, SMA_30, EMA_7, EMA_14

Momentum Indicators:
- momentum_3d, momentum_7d, momentum_14d, momentum_7, momentum_14, momentum_30
- roc_3d, roc_7d

Volatility:
- price_volatility_3d, price_volatility_7d, price_volatility_14d
- volatility_7, volatility_14

Bollinger Bands:
- bb_middle, bb_std, bb_upper, bb_lower, bb_position, BB_middle, BB_upper, BB_lower, BB_width

RSI & MACD:
- rsi_14, RSI, MACD, MACD_signal

Market Data:
- market_cap, volume, market_cap_change, volume_to_marketcap, volume_ma3, volume_ma7, volume_change, volume_SMA_7

Price Ratios:
- price_to_ma7, price_to_ma30
```

### 2. Vertex AI Feature Store (`src/vertex_ai_feature_store.py`)

**Setup**:
```python
fs = VertexAIFeatureStore(
    project_id="ml-project-480417",
    region="us-central1",
    featurestore_id="bitcoin_features"
)
```

**Operations**:
```python
# Upload features after computing
fs.ingest_features(features_df, entity_id_column="timestamp")

# Retrieve feature list
features = fs.get_feature_list()  # Returns list of 49 feature names

# Read features via BigQuery
df_features = fs.read_features(
    entity_ids=["entity_1", "entity_2"],
    feature_ids=["price", "rsi_14", "bb_std"]
)
```

**Backing Storage**: BigQuery table
- `ml-project-480417.bitcoin_features_bitcoin`
- Timestamp + 49 columns
- Queryable for analytics/monitoring

### 3. Cloud Storage (`gs://ml-project-480417-ml-models/`)

**Structure**:
```
gs://ml-project-480417-ml-models/
├── models/
│   ├── manifest.json  ← Active version pointer
│   ├── v20251215T121115Z_clf_model.pkl
│   ├── v20251215T121115Z_reg_model.pkl
│   ├── v20251215T121115Z_scaler.pkl
│   ├── v20251215T121115Z_feature_columns.json
│   └── v20251215T121115Z_training_metadata.json
├── features/
│   └── bitcoin_features_2025-12-15.csv
└── logs/
    └── training_logs/
```

### 4. Model Loading (`src/load_models_vertex_ai.py`)

**Three-tier fallback strategy**:

```python
from src.load_models_vertex_ai import load_models_from_vertex_ai

clf, reg, scaler, features, metadata = load_models_from_vertex_ai()

# Tier 1: Vertex AI Feature Store
#   ✓ Retrieve 49 feature names from Feature Store
#   ✓ Returns: ["price", "rsi_14", "bb_std", ...]

# Tier 2: Cloud Storage (gs://)
#   ✓ Download v*.pkl files from Cloud Storage
#   ✓ Load into memory (temporary directory)
#   ✓ Returns: (clf_model, reg_model, scaler, metadata)

# Tier 3: Local Fallback
#   ✓ Read from models/ directory
#   ✓ Use when GCP unavailable
#   ✓ Returns: (same as Tier 2)
```

---

## Training Pipeline (`prefect/flows/ml_pipeline.py`)

### Flow Steps

```
STEP 1: DATA INGESTION
    Input: Bitcoin CSV or live API
    Output: Raw DataFrame (daily price, market cap, volume)

STEP 2: FEATURE ENGINEERING ⭐ NEW
    Compute 49 technical indicators
    Input: Raw DataFrame
    Output: df_processed (with 49 features)

STEP 3: TRAIN/TEST SPLIT
    Temporal split (60 test days, rest training)
    Classification target: UP/DOWN (binary)
    Regression target: % price change

STEP 4A: TRAIN REGRESSION MODEL
    RandomForest, GradientBoosting, XGBoost
    Select best by R²

STEP 4B: TRAIN CLASSIFICATION MODEL
    RandomForest, GradientBoosting, XGBoost
    Select best by Accuracy

STEP 5A: EVALUATE REGRESSION
    RMSE, R², MAE

STEP 5B: EVALUATE CLASSIFICATION
    Accuracy, F1-Score, Precision, Recall

STEP 6: SAVE & VERSION MODELS ⭐ NEW
    Save locally to models/v*.pkl
    Create manifest.json
    Version: v20251215T121115Z

STEP 7A: UPLOAD TO CLOUD STORAGE ⭐ NEW
    Upload models to gs://bucket/models/
    Upload metadata and scaler
    Update manifest in cloud

STEP 7B: REGISTER TO VERTEX AI
    Register models to Model Registry
    Add metadata and metrics

STEP 7C: UPLOAD FEATURES ⭐ NEW
    Upload 49 computed features to Feature Store
    Ingest via BigQuery
    Enable feature monitoring
```

### Prefect Task Configuration

```python
@task(name="upload_models_to_cloud_storage", retries=2, retry_delay_seconds=5)
def upload_models_to_cloud_storage(version_info: Dict) -> bool:
    """Upload trained models to gs://bucket/models/"""

@task(name="upload_features_to_feature_store", retries=2, retry_delay_seconds=5)
def upload_features_to_feature_store(df_features: pd.DataFrame, feature_names: list) -> bool:
    """Upload computed features to Vertex AI Feature Store"""
```

---

## Serving Pipeline (FastAPI & Streamlit)

### FastAPI (`api_server.py`)

```python
@app.on_event("startup")
def startup_event():
    """Load models on startup"""
    global clf_model, reg_model, scaler, feature_columns
    
    clf_model, reg_model, scaler, feature_columns, metadata = \
        load_models_from_vertex_ai()
    
    # Attempts:
    # 1. Load features from Vertex AI Feature Store
    # 2. Load models from Cloud Storage (gs://)
    # 3. Fallback to local models/ directory
```

### Streamlit (`app.py`)

```python
@st.cache_resource
def load_models():
    """Cache models in session state"""
    return load_models_from_vertex_ai()

clf_model, reg_model, scaler, feature_columns, metadata = load_models()
```

---

## Environment Configuration

### Required Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=ml-project-480417
GCP_REGION=us-central1
GCP_BUCKET=ml-project-480417-ml-models

# Authentication
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Feature Store
FEATURESTORE_ID=bitcoin_features
FEATURESTORE_ENTITY_TYPE=bitcoin
```

### Set Locally (Windows PowerShell)

```powershell
$env:GCP_PROJECT_ID = "ml-project-480417"
$env:GCP_REGION = "us-central1"
$env:GCP_BUCKET = "ml-project-480417-ml-models"
$env:GOOGLE_APPLICATION_CREDENTIALS = "./service-account-key.json"
```

### Or in `.env` file

```bash
# Copy to workspace root
cp .env.example .env

# Edit .env with your values
# Then Python loads: from dotenv import load_dotenv; load_dotenv()
```

---

## Data Flow Example

### Training Day (Prefect Pipeline)

```
1. Fetch Bitcoin data (API or CSV)
   └─> DataFrame: 3000+ rows × 3 columns (date, price, market_cap, volume)

2. Feature Engineering
   └─> DataFrame: 3000+ rows × 49 columns (technical indicators)

3. Split Train/Test
   └─> X_train: 2940 rows, y_test: 60 rows

4. Train Models
   └─> clf_model: RandomForestClassifier (accuracy 70%)
   └─> reg_model: RandomForestRegressor (R² 0.13)

5. Save Locally
   └─> models/v20251215T121115Z_clf_model.pkl (2.5 MB)
   └─> models/v20251215T121115Z_reg_model.pkl (1.8 MB)
   └─> models/v20251215T121115Z_scaler.pkl (0.1 MB)

6. Upload to Cloud
   └─> gs://ml-project-480417-ml-models/models/v20251215T121115Z_*

7. Upload Features
   └─> BigQuery: ml-project-480417.bitcoin_features_bitcoin
       ├─ entity_id: timestamp_unix
       ├─ feature_timestamp: 2025-12-15 12:00:00 UTC
       ├─ price: 97309.20
       ├─ rsi_14: 52.35
       ├─ bb_std: 3400.00
       └─ ... (46 more features)
```

### Inference Day (FastAPI)

```
1. User requests: POST /predict/json
   └─> Features: {"price": 97309.20, "rsi_14": 52.35, ...}

2. Load Models (1x per startup)
   └─> Try Vertex AI Feature Store for feature list
   └─> Try Cloud Storage for model files
   └─> Fallback to local models/

3. Scale Features
   └─> Apply StandardScaler fitted during training

4. Predict
   └─> clf_model.predict(): UP (57% confidence)
   └─> reg_model.predict(): +0.5% price change

5. Return Response
   └─> {"direction": "UP", "confidence": 57%, "predicted_price": 97785.31}
```

---

## Monitoring & Debugging

### Check Vertex AI Setup

```bash
# List feature stores
gcloud ai feature-stores list --region=us-central1

# List entity types
gcloud ai entity-types list --featurestore=bitcoin_features --region=us-central1

# List features
gcloud ai features list --entity-type=bitcoin --featurestore=bitcoin_features --region=us-central1
```

### Query Features in BigQuery

```sql
-- List latest features
SELECT 
  entity_id,
  feature_timestamp,
  price,
  rsi_14,
  bb_std,
  -- ... other 46 features
FROM `ml-project-480417.bitcoin_features_bitcoin`
ORDER BY feature_timestamp DESC
LIMIT 10
```

### Check Model Files

```bash
# List models in Cloud Storage
gsutil ls -r gs://ml-project-480417-ml-models/models/

# Download manifest
gsutil cp gs://ml-project-480417-ml-models/models/manifest.json .

# Check active version
cat models/manifest.json | jq '.active_version'
```

### Test Model Loading

```python
from src.load_models_vertex_ai import load_models_from_vertex_ai

clf, reg, scaler, features, metadata = load_models_from_vertex_ai()

print(f"Features loaded: {len(features)}")
print(f"Model type: {type(clf).__name__}")
print(f"Metadata: {metadata}")
```

---

## Cost Estimation

### Vertex AI Feature Store (Monthly)
- **Storage**: ~50 GB = $1.00 (first 100 GB free tier)
- **Compute**: 1 node (minimum) = $24.00/month
- **API Calls**: 1M queries = $0.04 (first 100M free)

### Cloud Storage
- **Storage**: ~100 MB models = $0.02/month
- **Requests**: 1000 API calls = $0.04

### BigQuery
- **Storage**: ~50 GB features = $0.25/month (first 1 GB free)
- **Queries**: 1M rows scanned = $0.0026

**Total Estimate**: ~$25/month (with free tiers)

### Cost Reduction Tips
1. Use 1 node for Feature Store (not 3-10)
2. Archive old model versions
3. Delete old features (>90 days)
4. Use regional storage (same as compute)

---

## Next Steps

1. **Set up GCP** (see `VERTEX_AI_SETUP.md`)
2. **Configure environment variables**
3. **Test Feature Store connection**
4. **Run Prefect pipeline** (models upload automatically)
5. **Deploy FastAPI** (reads from Vertex AI)
6. **Deploy Streamlit** (reads from Vertex AI)

---

## References

- [Vertex AI Feature Store Docs](https://cloud.google.com/vertex-ai/docs/featurestore)
- [Cloud Storage Python Client](https://cloud.google.com/python/docs/reference/storage)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery)
- [AI Platform Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction)
