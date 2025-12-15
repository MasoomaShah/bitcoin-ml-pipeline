# How to Locate Your Vertex AI Feature Store & Model Registry on Google Cloud

## 📍 QUICK LINKS (Your Project)

Your Google Cloud Project ID: **ml-project-480417**

### Direct Links:
1. **Vertex AI Feature Store**: https://console.cloud.google.com/vertex-ai/feature-store/bitcoin_features?project=ml-project-480417
2. **Vertex AI Model Registry**: https://console.cloud.google.com/vertex-ai/model-registry?project=ml-project-480417
3. **Google Cloud Console (Main)**: https://console.cloud.google.com/?project=ml-project-480417

---

## 🔍 HOW TO NAVIGATE MANUALLY (If links don't work)

### **Step 1: Go to Google Cloud Console**
- Visit: https://console.cloud.google.com
- Select project **ml-project-480417** from dropdown (top left)

### **Step 2: Access Vertex AI**
- In left sidebar, click **Vertex AI**
- Or search "Vertex AI" in the search bar

### **Step 3: Find Feature Store**
**Path:** Vertex AI → Feature Store
- Click **Feature Store** in left menu
- You should see: **bitcoin_features** (your feature store)
- Click on it to see:
  - Feature tables: `bitcoin_technical_indicators`, `bitcoin_price_data`
  - Entity type: `bitcoin`
  - Feature definitions (24 technical indicators)

### **Step 4: Find Model Registry**
**Path:** Vertex AI → Model Registry
- Click **Model Registry** in left menu
- You should see all registered models
- Filter by: `bitcoin_ml`, `btc_prediction`, or date **2025-12**
- Each model shows:
  - Version history
  - Training metrics (accuracy, RMSE)
  - Deployment status
  - Creation date

### **Step 5: Find Trained Models**
**Path:** Vertex AI → Models
- Shows all your trained models
- Can see:
  - Model name
  - Training date
  - Performance metrics
  - Endpoints (if deployed)

### **Step 6: View Training Jobs**
**Path:** Vertex AI → Training
- Shows all completed/running training jobs
- Can see training history and logs
- Useful for debugging training failures

---

## 📊 WHAT TO LOOK FOR IN FEATURE STORE

```
Feature Store: bitcoin_features
├── Entity Type: bitcoin
│   └── Bitcoin price and technical indicators
│
├── Feature Tables:
│   ├── bitcoin_technical_indicators
│   │   ├── sma_7 (7-day simple moving average)
│   │   ├── sma_14 (14-day simple moving average)
│   │   ├── sma_30 (30-day simple moving average)
│   │   ├── rsi (Relative Strength Index)
│   │   ├── macd (Moving Average Convergence)
│   │   ├── bollinger_bands_width
│   │   ├── momentum_7, momentum_14, momentum_30
│   │   ├── volatility_7, volatility_14
│   │   └── volume_sma_7
│   │
│   └── bitcoin_price_data
│       ├── open
│       ├── high
│       ├── low
│       ├── close
│       ├── volume
│       └── timestamp
```

---

## 🤖 WHAT TO LOOK FOR IN MODEL REGISTRY

```
Model Registry
├── bitcoin_price_classifier
│   ├── Version 1 (2025-12-08)
│   │   ├── Input: 24 technical indicators
│   │   ├── Output: UP/DOWN direction
│   │   ├── Accuracy: 56.2%
│   │   └── Status: Ready
│   │
│   └── Version 2 (2025-12-15)
│       └── [Latest training run]
│
└── bitcoin_price_regressor
    ├── Version 1 (2025-12-08)
    │   ├── Input: 24 technical indicators
    │   ├── Output: Price change %
    │   ├── RMSE: 0.2358
    │   └── Status: Ready
    │
    └── Version 2 (2025-12-15)
        └── [Latest training run]
```

---

## 🔐 AUTHENTICATION SETUP

If you get permission errors:

1. **Enable Vertex AI API**
   - Go to Console → APIs & Services → Library
   - Search "Vertex AI API"
   - Click "Enable"

2. **Set up Service Account** (for local training)
   ```bash
   # Create service account key
   gcloud iam service-accounts keys create ~/vertex-ai-key.json \
     --iam-account=vertex-ai-sa@ml-project-480417.iam.gserviceaccount.com
   
   # Set environment variable
   export GOOGLE_APPLICATION_CREDENTIALS="~/vertex-ai-key.json"
   ```

3. **Permissions Needed**
   - Vertex AI Admin
   - Storage Admin (for Feature Store)
   - ML Engine Admin

---

## 📈 MONITORING YOUR FEATURES & MODELS

### **Feature Store Monitoring:**
- Click Feature Store → Select table → Monitor
- View:
  - Data freshness (last update timestamp)
  - Feature statistics
  - Data skew detection
  - Missing values

### **Model Performance Monitoring:**
- Click Model Registry → Select model → Evaluate
- View:
  - Accuracy, precision, recall
  - Confusion matrix
  - Training time
  - Inference latency

---

## 🔄 COMMON TASKS

### **Retrain Model Using Latest Features**
```bash
cd src
python train_with_feature_store.py \
  --use-feature-store \
  --feature-store-type vertex \
  --project-id ml-project-480417 \
  --region us-central1
```

### **Register Model Manually**
```bash
python src/vertex_ai_model_registry.py \
  --model-path models/v20251208T075527Z_clf_model.pkl \
  --model-name bitcoin_price_classifier \
  --accuracy 0.562
```

### **Check Feature Store Connection**
```bash
python -c "from src.vertex_ai_feature_store import VertexAIFeatureStore; fs = VertexAIFeatureStore(); print(fs.list_features())"
```

---

## 📞 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| "Permission denied" | Check IAM roles, enable Vertex AI API |
| Features not showing | Ensure features were ingested with `src/populate_vertex_ai.py` |
| Models not visible | Check project ID (ml-project-480417) is selected |
| Can't connect from code | Set GOOGLE_APPLICATION_CREDENTIALS env var |
| Feature Store empty | Run: `python src/populate_vertex_ai.py` |

---

## 🎯 SUMMARY

Your Vertex AI Setup:
- **Project ID**: ml-project-480417
- **Region**: us-central1
- **Feature Store**: bitcoin_features (bitcoin entity type)
- **Models**: bitcoin_price_classifier (UP/DOWN), bitcoin_price_regressor (price change)
- **Training Script**: `src/train_with_feature_store.py`
- **Registry Script**: `src/vertex_ai_model_registry.py`

Everything is integrated! Just use the links above to monitor your features and models in real-time on Google Cloud. ☁️

