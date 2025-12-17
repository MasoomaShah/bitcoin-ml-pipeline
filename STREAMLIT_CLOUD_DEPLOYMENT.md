# Streamlit Cloud Deployment Guide

## Problem: "Oops, it couldn't be deployed"

This error typically occurs when Streamlit Cloud can't build your environment. Here are the fixes I've made:

## ✅ Fixes Applied

### 1. Updated requirements.txt
- Added **Streamlit** (was missing!)
- Added **Plotly** (for charts)
- Added version pinning for all packages
- Added missing dependencies: joblib, python-dateutil, pytz, six

### 2. Updated .streamlit/config.toml
- Set `headless = true` (required for cloud)
- Added proper server configuration
- Added theme settings

### 3. Created .gitignore entries
- Excludes cache and credential files

## Deployment Steps

### Step 1: Prepare Your Repository
```bash
# Make sure you're in the project directory
cd "5th semester\ML PROJECT"

# Verify requirements.txt is up to date
cat requirements.txt
```

### Step 2: Push to GitHub
```bash
git add requirements.txt .streamlit/config.toml
git commit -m "fix: update requirements for streamlit cloud deployment"
git push
```

### Step 3: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repo
4. Enter:
   - **Repository**: `<your-username>/<repo-name>`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click "Deploy"

### Step 4: Monitor Deployment
- Watch the logs in Streamlit Cloud dashboard
- If it fails, click "Rerun" or check the logs for specific errors

## Common Deployment Issues & Fixes

### ❌ Error: "No module named 'streamlit'"
**Fix**: ✅ Already done - streamlit is now in requirements.txt

### ❌ Error: "No module named 'plotly'"
**Fix**: ✅ Already done - plotly is now in requirements.txt

### ❌ Error: "Cannot connect to feature store"
**Fix**: This is expected - add to app.py:
```python
try:
    df_raw = fetch_bitcoin_data()
except Exception as e:
    st.warning(f"Could not fetch live data: {e}")
    df_raw = pd.read_csv("data/raw/bitcoin_timeseries.csv")
```

### ❌ Error: "ModuleNotFoundError: No module named 'src'"
**Fix**: Already handled in app.py with `sys.path.append()`

### ❌ Build timeout
**Fix**: Remove heavy imports if building takes >15 minutes
- TensorFlow/Keras can be slow
- Prophet can be slow
- Consider lazy loading

## Environment Variables for Cloud

If you need secrets (API keys, credentials):

1. Go to your Streamlit app settings
2. Click "Secrets"
3. Add your secrets in TOML format:
```toml
# .streamlit/secrets.toml (local only - don't commit!)
[gcp]
project_id = "your-project-id"
api_key = "your-key"
```

Then access in app.py:
```python
import streamlit as st
project_id = st.secrets["gcp"]["project_id"]
```

## Streamlit Cloud Limitations

| Feature | Support | Notes |
|---------|---------|-------|
| File Upload | ✓ Yes | Works for CSV predictions |
| API Calls | ✓ Yes | Can call your FastAPI backend |
| External Data | ✓ Yes | Can read CSV, connect to DB |
| TensorFlow | ✓ Yes | But may timeout on deploy |
| Large Files | ✗ No | Keep app.py under 50MB |
| GPU/CUDA | ✗ No | CPU only |
| Background Tasks | ✗ No | Use scheduler services |

## Deployment Architecture Options

### Option 1: Streamlit Cloud (Recommended for MVP)
```
GitHub Repo
    ↓
Streamlit Cloud (runs app.py)
    ↓
FastAPI Backend (your server or Cloud Run)
```

**Pros**: Free tier, easy, automatic deployments on push
**Cons**: Limited compute, no background tasks

### Option 2: Google Cloud Run
```
GitHub Repo
    ↓
Cloud Build (builds Docker)
    ↓
Cloud Run (runs containerized app)
```

**Pros**: More control, can use GPU, scale automatically
**Cons**: Requires setup, costs more

### Option 3: Hybrid (Recommended)
```
Streamlit Cloud (UI)
    ↓ (API calls)
FastAPI on Google Cloud Run (Backend)
    ↓
Vertex AI Feature Store + Models
```

**Pros**: Best of both worlds, scalable, can run heavy ML tasks
**Cons**: More complex setup

## Deployment Steps for Option 3 (Recommended)

### Step 1: Deploy FastAPI to Cloud Run
```bash
# Create Dockerfile for FastAPI
# Push to Container Registry
# Deploy to Cloud Run
```

### Step 2: Update app.py to use Cloud FastAPI
```python
# Instead of local API
API_URL = "https://your-fastapi-backend.run.app"

# Make API calls
response = requests.get(f"{API_URL}/data/latest")
```

### Step 3: Deploy Streamlit to Streamlit Cloud
```bash
# Push app.py to GitHub
# Deploy from Streamlit Cloud dashboard
```

## Quick Checklist Before Deploying

```
□ requirements.txt has all dependencies with versions
□ app.py has no hardcoded paths
□ app.py handles missing files gracefully
□ .streamlit/config.toml has headless = true
□ All imports are in requirements.txt
□ No credential files in repo (use secrets instead)
□ .gitignore excludes __pycache__, .env, .pkl files
□ README.md explains how to run locally
□ No files > 100MB in repo
□ GitHub repo is public (or private with proper access)
```

## Test Deployment Locally Before Cloud

```bash
# Run Streamlit as it would on Cloud (headless mode)
streamlit run app.py --logger.level=debug

# Test with FastAPI running on 8000
# Open http://localhost:8501
```

## Post-Deployment

Once deployed:

1. **Monitor** the app at https://share.streamlit.io/dashboard
2. **Check logs** if there are issues
3. **Set up alerts** for failures
4. **Configure auto-redeploy** on GitHub push
5. **Add custom domain** (premium feature)

## Support

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-cloud
- Troubleshooting: https://docs.streamlit.io/knowledge-base/using-streamlit
- Community: https://discuss.streamlit.io

## Summary

The deployment issues are now fixed:
- ✅ Requirements.txt updated with all packages
- ✅ Streamlit config optimized for cloud
- ✅ Ready to push to GitHub and deploy

**Next step**: Push changes to GitHub and redeploy on Streamlit Cloud!
