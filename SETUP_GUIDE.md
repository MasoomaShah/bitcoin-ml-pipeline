# Bitcoin ML Pipeline - Quick Setup Guide

## Installation (Choose One Option)

### Option 1: Minimal Setup (Local Training Only)
```bash
pip install -r requirements-minimal.txt
```

This installs:
- scikit-learn, pandas, numpy (ML basics)
- alpha-vantage (data fetching)
- joblib (model saving)

### Option 2: Full Setup (With Vertex AI)
```bash
pip install -r requirements.txt
```

This includes everything from Option 1 plus:
- google-cloud-aiplatform (Feature Store & Model Registry)
- google-cloud-storage (GCS bucket access)

## Usage

### 1. Train Locally (No Feature Store)
```bash
python src/train_with_feature_store.py --test-size 0.1
```

### 2. Train with Vertex AI Feature Store
```bash
# Set credentials first
$env:GOOGLE_APPLICATION_CREDENTIALS="ml-project-480417-2e263ddd92fb.json"

# Train with feature store
python src/train_with_feature_store.py --use-feature-store --test-size 0.1
```

### 3. Train with Model Experiments
```bash
python src/train_with_feature_store.py --experiment-models --test-size 0.1
```

### 4. Full Pipeline (Feature Store + Experiments + Registry)
```bash
python src/train_with_feature_store.py --use-feature-store --experiment-models --use-model-registry --test-size 0.1
```

## Environment Variables

```bash
# Alpha Vantage API Key (Required)
$env:ALPHA_VANTAGE_API_KEY="WMK7ADA9G2OXN5DA"

# Google Cloud Credentials (Optional - only for Vertex AI)
$env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\ml-project-480417-2e263ddd92fb.json"
```

## Quick Test

```bash
# Test if packages are installed
python -c "import sklearn; import pandas; import alpha_vantage; print('✓ Core packages installed')"

# Test if Google Cloud is available (optional)
python -c "try: import google.cloud.aiplatform; print('✓ Vertex AI available')\nexcept: print('⚠️ Vertex AI not installed')"
```

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'alpha_vantage'`  
**Fix**: `pip install alpha-vantage`

**Issue**: `ModuleNotFoundError: No module named 'google'`  
**Fix**: `pip install google-cloud-aiplatform google-cloud-storage`

**Issue**: `ModuleNotFoundError: No module named 'sklearn'`  
**Fix**: `pip install scikit-learn`

## File Structure
```
ML PROJECT/
├── src/
│   ├── train_with_feature_store.py  ← Main training script
│   ├── fetch_alpha_vantage.py       ← Data fetching
│   ├── preprocess_bitcoin.py        ← Feature engineering
│   ├── model_experiments.py         ← Multi-model testing
│   ├── vertex_ai_feature_store.py   ← Feature Store (optional)
│   └── vertex_ai_model_registry.py  ← Model Registry (optional)
│
├── models/                           ← Saved models
├── requirements-minimal.txt          ← Core dependencies
└── requirements.txt                  ← Full dependencies
```

## What Works Without Vertex AI

✅ **Local Training**: Full ML pipeline with Alpha Vantage data  
✅ **Model Experiments**: Test multiple models (RF, GB, Ridge, Lasso, SVM)  
✅ **Model Saving**: Save trained models locally  
✅ **Feature Engineering**: 24 technical indicators  

❌ **Feature Store**: Requires Vertex AI  
❌ **Model Registry**: Requires Vertex AI  

## Recommended Workflow

1. **Start Simple**: Train locally without Vertex AI
   ```bash
   pip install -r requirements-minimal.txt
   python src/train_with_feature_store.py --experiment-models --test-size 0.1
   ```

2. **Add Vertex AI Later** (if needed):
   ```bash
   pip install google-cloud-aiplatform google-cloud-storage
   python src/train_with_feature_store.py --use-feature-store --experiment-models --use-model-registry
   ```
