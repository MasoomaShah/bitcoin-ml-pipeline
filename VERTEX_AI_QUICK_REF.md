# Vertex AI Quick Reference

## Quick Commands

### Train with Vertex AI
```bash
python src/train_with_feature_store.py --use-feature-store --feature-store-type vertex
```

### Populate Feature Store
```bash
python src/populate_vertex_ai.py
```

### Train without Feature Store (Local)
```bash
python src/train_with_feature_store.py
```

## Environment Setup (One-Time)

```powershell
# Activate environment
conda activate hopsworks-env

# Set Google credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\ml-project-480417-2e263ddd92fb.json"
```

## Feature Store Info

- **Project**: ml-project-480417
- **Region**: us-central1
- **Feature Store**: bitcoin_features
- **Entity Type**: bitcoin
- **Features**: 24 technical indicators
- **Records**: 1,095 (3 years)

## GCP Console Links

- [Vertex AI Feature Store](https://console.cloud.google.com/vertex-ai/feature-store/bitcoin_features?project=ml-project-480417)
- [IAM & Admin](https://console.cloud.google.com/iam-admin?project=ml-project-480417)
- [APIs & Services](https://console.cloud.google.com/apis?project=ml-project-480417)
- [Billing](https://console.cloud.google.com/billing?project=ml-project-480417)

## Troubleshooting

### Check Feature Store Status
```python
from src.vertex_ai_feature_store import VertexAIFeatureStore
fs = VertexAIFeatureStore()
fs.connect()  # Should show ✓ Connected
```

### Verify Credentials
```powershell
Get-Content $env:GOOGLE_APPLICATION_CREDENTIALS | ConvertFrom-Json | Select-Object project_id, client_email
```

### Test Alpha Vantage API
```powershell
curl "https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=USD&apikey=WMK7ADA9G2OXN5DA" | ConvertFrom-Json | Select-Object -First 1
```

## Model Versions

Current active version: **v20251207T161242Z**
- Classification Accuracy: **61.82%**
- Training samples: 985
- Test samples: 110

## Feature List

1. open, high, low, close
2. volume, volume_sma_7, volume_change
3. sma_7, sma_14, sma_30
4. ema_7, ema_14
5. momentum_7, momentum_14, momentum_30
6. volatility_7, volatility_14
7. rsi, macd, macd_signal
8. bb_middle, bb_upper, bb_lower, bb_width

---
*For detailed documentation, see VERTEX_AI_INTEGRATION.md*
