# Vertex AI Integration Setup Guide

## Overview

Your ML system now uses Vertex AI Feature Store to:
1. **Store computed features** - Upload technical indicators after computation
2. **Read back features during training** - Use Vertex AI features instead of local computation
3. **Load models from Cloud Storage** - Models stored in GCP after training

---

## Prerequisites

### 1. Install Required Packages

```bash
pip install google-cloud-aiplatform google-cloud-storage google-cloud-bigquery
```

### 2. Google Cloud Setup

#### Create GCP Project (if not done)
```bash
gcloud projects create ml-project-480417
gcloud config set project ml-project-480417
```

#### Enable Required APIs
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  compute.googleapis.com
```

#### Create Service Account
```bash
# Create service account
gcloud iam service-accounts create ml-pipeline \
  --display-name="ML Pipeline Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding ml-project-480417 \
  --member=serviceAccount:ml-pipeline@ml-project-480417.iam.gserviceaccount.com \
  --role=roles/aiplatform.admin

gcloud projects add-iam-policy-binding ml-project-480417 \
  --member=serviceAccount:ml-pipeline@ml-project-480417.iam.gserviceaccount.com \
  --role=roles/storage.admin

gcloud projects add-iam-policy-binding ml-project-480417 \
  --member=serviceAccount:ml-pipeline@ml-project-480417.iam.gserviceaccount.com \
  --role=roles/bigquery.admin

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=ml-pipeline@ml-project-480417.iam.gserviceaccount.com
```

---

## Environment Variables Setup

### Option 1: Set via Command Line

```bash
# Set GCP project
export GCP_PROJECT_ID=ml-project-480417
export GCP_REGION=us-central1
export GCP_BUCKET=ml-project-480417-ml-models

# Set authentication
export GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Verify connection
gcloud auth application-default login
```

### Option 2: Create `.env` File

Create `c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT\.env`:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=ml-project-480417
GCP_REGION=us-central1
GCP_BUCKET=ml-project-480417-ml-models
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Feature Store Configuration
FEATURESTORE_ID=bitcoin_features
FEATURESTORE_ENTITY_TYPE=bitcoin

# Model Registry Configuration
MODEL_REGISTRY_BUCKET=ml-project-480417-ml-models
MODEL_REGISTRY_PREFIX=models/
```

Then load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 3: PowerShell Environment (Windows)

```powershell
# Set environment variables
$env:GCP_PROJECT_ID = "ml-project-480417"
$env:GCP_REGION = "us-central1"
$env:GCP_BUCKET = "ml-project-480417-ml-models"
$env:GOOGLE_APPLICATION_CREDENTIALS = "./service-account-key.json"

# Verify
echo $env:GCP_PROJECT_ID
```

---

## Cloud Storage Setup

### Create Bucket for Models
```bash
gsutil mb -p ml-project-480417 -l us-central1 gs://ml-project-480417-ml-models
gsutil versioning set on gs://ml-project-480417-ml-models
```

### Create Bucket Structure
```bash
# Create folders (pseudo-folders in GCS)
gsutil -m cp /dev/null gs://ml-project-480417-ml-models/models/placeholder.txt
gsutil -m cp /dev/null gs://ml-project-480417-ml-models/features/placeholder.txt
gsutil -m cp /dev/null gs://ml-project-480417-ml-models/logs/placeholder.txt
```

---

## Feature Store Setup

### Initialize Feature Store

Run once to create feature store:

```python
from src.vertex_ai_feature_store import VertexAIFeatureStore

fs = VertexAIFeatureStore()
if fs.connect():
    print("✅ Feature Store ready!")
```

### Upload Features (During Training)

This happens automatically in the Prefect pipeline:

```python
# In ml_pipeline.py
upload_features_to_feature_store(df_features, feature_cols)
```

---

## Model Loading Flow

### Training Phase
1. **Compute features locally** → Add technical indicators
2. **Upload to Feature Store** → Save in Vertex AI
3. **Train models** → Use local features
4. **Save models** → Upload to Cloud Storage
5. **Register in Model Registry** → Create manifest

### Serving Phase (FastAPI/Streamlit)
1. **`load_models_from_vertex_ai()` called**
2. **Attempt 1**: Read features from Feature Store
3. **Attempt 2**: Load models from Cloud Storage via `gs://` path
4. **Fallback**: Read from local `models/` directory
5. **Return**: (clf_model, reg_model, scaler, features, metadata)

---

## Verification Steps

### 1. Check GCP Authentication
```bash
gcloud auth list
gcloud config list
```

### 2. Test Feature Store Connection
```bash
cd "c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT"
python -c "from src.vertex_ai_feature_store import VertexAIFeatureStore; fs = VertexAIFeatureStore(); fs.connect()"
```

### 3. Test Model Loading
```bash
python -c "from src.load_models_vertex_ai import load_models_from_vertex_ai; clf, reg, scaler, features, metadata = load_models_from_vertex_ai(); print(f'✅ Loaded {len(features)} features')"
```

### 4. Check Cloud Storage
```bash
gsutil ls -r gs://ml-project-480417-ml-models/
```

### 5. Check Feature Store
```bash
gcloud ai feature-stores list --region=us-central1
gcloud ai entity-types list --featurestore=bitcoin_features --region=us-central1
```

---

## Troubleshooting

### Issue: "Authentication failed"
```bash
# Fix: Re-authenticate
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

### Issue: "Bucket not found"
```bash
# Create bucket
gsutil mb -l us-central1 gs://ml-project-480417-ml-models
```

### Issue: "Feature Store API not enabled"
```bash
# Enable it
gcloud services enable aiplatform.googleapis.com
```

### Issue: "Permission denied"
```bash
# Check service account permissions
gcloud projects get-iam-policy ml-project-480417 \
  --flatten="bindings[].members" \
  --filter="bindings.members:ml-pipeline*"
```

---

## Production Checklist

- [ ] GCP project created and configured
- [ ] Service account created with correct roles
- [ ] `service-account-key.json` downloaded
- [ ] Environment variables set (`GCP_PROJECT_ID`, `GCP_REGION`, `GCP_BUCKET`)
- [ ] Cloud Storage bucket created
- [ ] Feature Store initialized
- [ ] Models uploaded to Cloud Storage
- [ ] `load_models_from_vertex_ai()` tested
- [ ] FastAPI uses Vertex AI loading
- [ ] Streamlit uses Vertex AI loading
- [ ] Prefect pipeline uploads features after training

---

## Data Flow Diagram

```
Training Pipeline:
┌──────────────────┐
│ Fetch Bitcoin    │
│ Data (CSV/API)   │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ Compute Features │
│ (Technical Indicators)
└────────┬─────────┘
         │
         ├──> Upload to Vertex AI Feature Store
         │
         v
┌──────────────────┐
│ Train Models     │
│ (RandomForest)   │
└────────┬─────────┘
         │
         ├──> Save to Cloud Storage
         │    (models/*.pkl)
         │
         v
┌──────────────────┐
│ Update Manifest  │
│ manifest.json    │
└──────────────────┘


Serving Pipeline:
┌──────────────────────────────┐
│ API Request (FastAPI/Streamlit)
└────────┬─────────────────────┘
         │
         v
┌──────────────────────────────┐
│ load_models_from_vertex_ai()  │
└────────┬─────────────────────┘
         │
         ├─> Try Feature Store for features
         │
         ├─> Try Cloud Storage for models
         │   (gs://bucket/models/v*.pkl)
         │
         └─> Fallback to local models/
             (if GCP unavailable)
         │
         v
┌──────────────────┐
│ Make Prediction  │
│ (clf + reg)      │
└──────────────────┘
```

---

## Cost Optimization

### To reduce costs:
1. Use `--online_store_fixed_node_count=1` (minimum)
2. Archive old model versions
3. Set up data lifecycle policies
4. Use regional storage (closer to compute)

### Example lifecycle policy:
```bash
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://ml-project-480417-ml-models
```

---

## Documentation Links

- [Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore/overview)
- [Cloud Storage Python Client](https://cloud.google.com/python/docs/reference/storage/latest)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [Service Account Setup](https://cloud.google.com/docs/authentication/getting-started)

