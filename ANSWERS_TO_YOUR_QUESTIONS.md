# Answers to Your Questions

## ❓ Question 1: "How do I locate my Feature Store and Registry on Google Cloud Services?"

### Feature Store Location
1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Make sure you're in project **ml-project-480417**
3. Navigate to **Vertex AI** → **Feature Store** (in left sidebar)
4. Your feature store **bitcoin_features** will be listed there
5. This is where all your technical indicator data (SMA_7, RSI, MACD, etc.) is stored

### Model Registry Location
1. In **Google Cloud Console**: https://console.cloud.google.com/
2. Project: **ml-project-480417**
3. Navigate to **Vertex AI** → **Model Registry** (in left sidebar)
4. All your trained models are registered here with metadata
5. You can see version history, metrics, and deployment status

---

## ❓ Question 2: "Why is the predicted price GREEN when it should show direction?"

**FIXED!** ✅ 

**The Problem**: The delta was being formatted as a string (`f"${value:,.2f}"`), and Streamlit couldn't parse the direction from text.

**The Solution**: Changed it to pass the numeric value directly:
```python
# Before (WRONG - formatted string):
st.metric("Predicted Price", f"${predicted_price:,.2f}", 
          delta=f"${price_change_usd:,.2f}")

# After (CORRECT - numeric value):
st.metric("Predicted Price", f"${predicted_price:,.2f}", 
          delta=price_change_usd)  # Let Streamlit handle the formatting
```

**How Streamlit handles it now**:
- ✅ **GREEN ⬆️** when `delta` is **positive** (price going up)
- ✅ **RED ⬇️** when `delta` is **negative** (price going down)

**Status**: The fix has been applied to app.py (line 398). Restart Streamlit to see the change:
```bash
streamlit run app.py
```

---

## ❓ Question 3: "Models train everyday, so shouldn't the accuracy change?"

**The Issue**: Your classification accuracy stays at **56.2%** but should update daily because the daily training workflow runs every day at 2 AM UTC.

**Why It's Static**: 
1. The GitHub Actions workflow **scheduled-training.yml** is configured to run daily
2. It trains new models and saves them to `models/v20251208T075527Z_training_metadata.json`
3. **BUT** the latest model was created on **Dec 8** (6 days ago) - not yesterday
4. **The workflow hasn't actually run since Dec 8!**

**Possible Reasons for No Recent Training**:
1. GitHub Actions workflow might be **disabled** on the repository
2. The **cron schedule** might not be triggering (check GitHub Actions tab)
3. Training might be **failing silently** - check the workflow logs
4. API keys might have **expired** (Alpha Vantage API key)

**How to Fix**:
1. Go to your GitHub repository
2. Click **Actions** tab
3. Look for **"Scheduled - Daily Model Training"** workflow
4. Check recent runs - are there any from today or yesterday?
5. If no recent runs, the workflow is disabled. Click **"Enable workflow"**

**Manual Trigger** (to test if it works):
```bash
# In your repository, you can manually trigger training:
# Or from CLI:
gh workflow run scheduled-training.yml
```

**When It Runs Correctly**, the dashboard will show:
- ✅ New accuracy values daily
- ✅ New model versions like `v20251210T020000Z` (date of training)
- ✅ Updated metrics in `models/manifest.json`

---

## ✅ Question 4: "Can you fix the errors in EDA.ipynb?"

**ALREADY FIXED!** ✅

**The Problem**: Cell 7 was trying to plot moving averages (SMA_7, SMA_14, SMA_30) but these columns didn't exist in the raw Bitcoin data.

**The Solution**: Added a check to compute them if missing:
```python
# Compute technical indicators if missing
if 'SMA_7' not in df_sorted.columns:
    df_sorted['SMA_7'] = df_sorted['Close'].rolling(window=7).mean()
if 'SMA_14' not in df_sorted.columns:
    df_sorted['SMA_14'] = df_sorted['Close'].rolling(window=14).mean()
if 'SMA_30' not in df_sorted.columns:
    df_sorted['SMA_30'] = df_sorted['Close'].rolling(window=30).mean()
```

**Status**: ✅ Fix has been applied. When you run Cell 7 in EDA.ipynb:
- It will auto-compute any missing technical indicators
- Charts will display correctly
- No errors!

---

## 📋 Summary of Changes

| Issue | Status | What Changed |
|-------|--------|--------------|
| Predicted price color (GREEN) | ✅ FIXED | Changed delta from formatted string to numeric value |
| Model accuracy not updating | ⏳ NEEDS ACTION | Check if GitHub Actions workflow is enabled & running |
| Feature Store location | ✅ ANSWERED | Vertex AI → Feature Store in GCP Console |
| Model Registry location | ✅ ANSWERED | Vertex AI → Model Registry in GCP Console |
| EDA.ipynb errors | ✅ FIXED | Added checks to compute missing technical indicators |

---

## 🔍 Next Steps

1. **Verify the color fix**: Refresh Streamlit dashboard at http://localhost:8501
   - Look at "Predicted Price" metric - should now show correct direction color

2. **Enable daily training**: 
   - Check GitHub Actions workflow status
   - Ensure the scheduled-training.yml is **enabled**
   - Verify it runs tomorrow at 2 AM UTC

3. **Test EDA.ipynb**:
   - Open notebooks/EDA.ipynb in VS Code
   - Run Cell 7 (should plot without errors now)

---

**Questions? Let me know!** 🚀
