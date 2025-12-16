# FastAPI JSON Test Examples

## Summary

**Daily Model Training:**
- **Models trained per day**: 1 (RandomForest both classification + regression)
- **Selection method**: Best model based on validation accuracy
- **Schedule**: 2 AM UTC daily via GitHub Actions
- **Artifacts retained**: 60 days

---

## 1️⃣ Simple JSON Test (All 49 Features)

Use this for basic `/predict/json` testing:

```bash
curl -X POST "http://localhost:8000/predict/json" \
  -H "Content-Type: application/json" \
  -d '{
  "features": {
    "price": 95000,
    "volume": 2500000000,
    "market_cap": 1850000000000,
    "price_smooth": 94800,
    "price_ma3": 94500,
    "price_ma7": 94200,
    "price_ma14": 93800,
    "price_ma30": 93000,
    "price_ema7": 94600,
    "price_ema14": 94100,
    "momentum_3d": 0.02,
    "momentum_7d": 0.015,
    "momentum_14d": 0.01,
    "roc_3d": 0.02,
    "roc_7d": 0.015,
    "price_volatility_3d": 1200,
    "price_volatility_7d": 1300,
    "price_volatility_14d": 1400,
    "volume_ma3": 2600000000,
    "volume_ma7": 2550000000,
    "volume_change": 0.05,
    "price_to_ma7": 1.008,
    "price_to_ma30": 1.011,
    "bb_middle": 94000,
    "bb_std": 2800,
    "bb_upper": 99600,
    "bb_lower": 88400,
    "bb_position": 0.45,
    "rsi_14": 55,
    "market_cap_change": 0.02,
    "volume_to_marketcap": 0.00135,
    "SMA_7": 94200,
    "SMA_14": 93800,
    "SMA_30": 93000,
    "EMA_7": 94600,
    "EMA_14": 94100,
    "momentum_7": 0.015,
    "momentum_14": 0.01,
    "momentum_30": 0.008,
    "volatility_7": 1300,
    "volatility_14": 1400,
    "RSI": 55,
    "MACD": 400,
    "MACD_signal": 380,
    "BB_middle": 94000,
    "BB_upper": 99600,
    "BB_lower": 88400,
    "BB_width": 11200,
    "volume_SMA_7": 2550000000
  },
  "current_price": 95000
}'
```

---

## 2️⃣ Bullish Market Test (Expect UP prediction)

```json
{
  "features": {
    "price": 100000,
    "volume": 3500000000,
    "market_cap": 1950000000000,
    "price_smooth": 99500,
    "price_ma3": 98000,
    "price_ma7": 96000,
    "price_ma14": 94000,
    "price_ma30": 92000,
    "price_ema7": 99000,
    "price_ema14": 97000,
    "momentum_3d": 0.05,
    "momentum_7d": 0.04,
    "momentum_14d": 0.03,
    "roc_3d": 0.05,
    "roc_7d": 0.04,
    "price_volatility_3d": 800,
    "price_volatility_7d": 1000,
    "price_volatility_14d": 1200,
    "volume_ma3": 3200000000,
    "volume_ma7": 3100000000,
    "volume_change": 0.15,
    "price_to_ma7": 1.042,
    "price_to_ma30": 1.087,
    "bb_middle": 95000,
    "bb_std": 2500,
    "bb_upper": 100000,
    "bb_lower": 90000,
    "bb_position": 0.8,
    "rsi_14": 72,
    "market_cap_change": 0.05,
    "volume_to_marketcap": 0.0018,
    "SMA_7": 96000,
    "SMA_14": 94000,
    "SMA_30": 92000,
    "EMA_7": 99000,
    "EMA_14": 97000,
    "momentum_7": 0.04,
    "momentum_14": 0.03,
    "momentum_30": 0.02,
    "volatility_7": 1000,
    "volatility_14": 1200,
    "RSI": 72,
    "MACD": 550,
    "MACD_signal": 500,
    "BB_middle": 95000,
    "BB_upper": 100000,
    "BB_lower": 90000,
    "BB_width": 10000,
    "volume_SMA_7": 3100000000
  },
  "current_price": 100000
}
```

---

## 3️⃣ Bearish Market Test (Expect DOWN prediction)

```json
{
  "features": {
    "price": 50000,
    "volume": 1500000000,
    "market_cap": 950000000000,
    "price_smooth": 50500,
    "price_ma3": 55000,
    "price_ma7": 60000,
    "price_ma14": 65000,
    "price_ma30": 70000,
    "price_ema7": 52000,
    "price_ema14": 55000,
    "momentum_3d": -0.08,
    "momentum_7d": -0.06,
    "momentum_14d": -0.04,
    "roc_3d": -0.08,
    "roc_7d": -0.06,
    "price_volatility_3d": 2500,
    "price_volatility_7d": 2300,
    "price_volatility_14d": 2100,
    "volume_ma3": 1400000000,
    "volume_ma7": 1300000000,
    "volume_change": -0.2,
    "price_to_ma7": 0.833,
    "price_to_ma30": 0.714,
    "bb_middle": 60000,
    "bb_std": 5000,
    "bb_upper": 70000,
    "bb_lower": 50000,
    "bb_position": 0.0,
    "rsi_14": 25,
    "market_cap_change": -0.08,
    "volume_to_marketcap": 0.00158,
    "SMA_7": 60000,
    "SMA_14": 65000,
    "SMA_30": 70000,
    "EMA_7": 52000,
    "EMA_14": 55000,
    "momentum_7": -0.06,
    "momentum_14": -0.04,
    "momentum_30": -0.02,
    "volatility_7": 2300,
    "volatility_14": 2100,
    "RSI": 25,
    "MACD": 200,
    "MACD_signal": 250,
    "BB_middle": 60000,
    "BB_upper": 70000,
    "BB_lower": 50000,
    "BB_width": 20000,
    "volume_SMA_7": 1300000000
  },
  "current_price": 50000
}
```

---

## 4️⃣ Test SHAP Explanations

```bash
curl -X POST "http://localhost:8000/explain" \
  -H "Content-Type: application/json" \
  -d '{COPY ANY JSON PAYLOAD FROM ABOVE}'
```

Expected response:
```json
{
  "status": "success",
  "explanation_method": "shap_approximation",
  "prediction": {
    "price_change_pct": 0.02,
    "direction": "UP"
  },
  "feature_importance": {
    "price_to_ma30": 0.145,
    "RSI": 0.089,
    "momentum_7d": 0.076,
    ...
  },
  "shap_values": [0.001, -0.002, 0.015, ...]
}
```

---

## ✅ Updated API Status

- ✅ SHAP endpoint fixed (using RandomForest feature importance)
- ✅ All 49 features working
- ✅ Direction now matches price change % sign
- ✅ Alpha Vantage module deleted
- ✅ FastAPI /docs available at http://localhost:8000/docs
