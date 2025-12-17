# SHAP Explanations via FastAPI

The SHAP values and feature importance are now available via the **`/explain`** endpoint instead of being embedded in Streamlit.

## Quick Test

### 1. Get SHAP Values for Your Prediction

```powershell
curl -X POST http://localhost:8000/explain `
  -H "Content-Type: application/json" `
  -d (Get-Content test_fastapi_json.json)
```

### 2. Response (SHAP + Feature Importance)

```json
{
  "status": "success",
  "explanation_method": "shap_approximation",
  "prediction": {
    "price_change_pct": 2.35,
    "direction": "UP"
  },
  "feature_importance": {
    "price_to_ma7": 0.0234,
    "rsi_14": 0.0189,
    "momentum_14d": 0.0145,
    ...
  },
  "shap_values": [
    -0.15,
    0.42,
    0.03,
    ...
  ],
  "timestamp": "2025-12-17T10:30:00.123456"
}
```

## What Each Field Means

### `feature_importance` (Top 15 Features)
Shows which features had the most influence on the prediction:
- Positive values = feature pushed prediction UP
- Negative values = feature pushed prediction DOWN
- Larger absolute values = more important

Example:
```json
"feature_importance": {
  "price_to_ma7": 0.0234,      // Price ratio to 7-day MA was most important
  "rsi_14": 0.0189,            // RSI indicator was 2nd most important
  "momentum_14d": 0.0145       // 14-day momentum was 3rd most important
}
```

### `shap_values` (All 49 Features)
Approximation of SHAP values for each feature in the model:
- One value per feature in exact order
- Shows individual feature contribution to prediction
- Index matches feature order from `/model/features`

Example interpretation:
```
Feature 0 (price): -0.15      → Pushed price down slightly
Feature 1 (volume): 0.42       → Pushed price up significantly
Feature 2 (market_cap): 0.03   → Minimal effect
...
```

## Python Example

```python
import requests
import json

# Load test data
with open('test_fastapi_json.json') as f:
    test_data = json.load(f)

# Get SHAP explanations
response = requests.post(
    'http://localhost:8000/explain',
    json=test_data
)

explanation = response.json()

# Print prediction
print(f"Predicted Direction: {explanation['prediction']['direction']}")
print(f"Price Change: {explanation['prediction']['price_change_pct']:.2f}%")

# Print top features
print("\nTop 15 Most Important Features:")
for feature, importance in explanation['feature_importance'].items():
    print(f"  {feature}: {importance:.4f}")

# Print SHAP values
print("\nSHAP Values (Feature Contributions):")
features = requests.get('http://localhost:8000/model/features').json()['features']
for feature, shap_val in zip(features, explanation['shap_values']):
    print(f"  {feature}: {shap_val:.4f}")
```

## Comparison: Streamlit vs API

| Aspect | Streamlit (Removed) | FastAPI (Current) |
|--------|-------------------|------------------|
| SHAP Values | Visualized in UI | Available via `/explain` endpoint |
| Feature Importance | Chart displayed | JSON response |
| Predictions | Combined with charts | Separate `/predict` endpoints |
| Explainability | Real-time on-demand | RESTful API call |
| Use Case | Interactive dashboard | Programmatic access |

## Integration Example

### For a Web Dashboard:

```javascript
// Fetch prediction
const predResponse = await fetch('http://localhost:8000/predict/json', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(testData)
});
const prediction = await predResponse.json();

// Fetch explanation (SHAP)
const explResponse = await fetch('http://localhost:8000/explain', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(testData)
});
const explanation = await explResponse.json();

// Display both
console.log('Prediction:', prediction.direction);
console.log('Top Features:', explanation.feature_importance);
console.log('SHAP Values:', explanation.shap_values);
```

## Feature Order (for reference with SHAP values)

The 49 SHAP values correspond to features in this order:

```
Index  Feature              | Index  Feature
-------|---------------------| -------|---------------------
0      price                | 25     bb_upper
1      volume               | 26     bb_lower
2      market_cap           | 27     bb_position
3      price_smooth         | 28     rsi_14
4      price_ma3            | 29     market_cap_change
5      price_ma7            | 30     volume_to_marketcap
6      price_ma14           | 31     SMA_7
7      price_ma30           | 32     SMA_14
8      price_ema7           | 33     SMA_30
9      price_ema14          | 34     EMA_7
10     momentum_3d          | 35     EMA_14
11     momentum_7d          | 36     momentum_7
12     momentum_14d         | 37     momentum_14
13     roc_3d               | 38     momentum_30
14     roc_7d               | 39     volatility_7
15     price_volatility_3d  | 40     volatility_14
16     price_volatility_7d  | 41     RSI
17     price_volatility_14d | 42     MACD
18     volume_ma3           | 43     MACD_signal
19     volume_ma7           | 44     BB_middle
20     volume_change        | 45     BB_upper
21     price_to_ma7         | 46     BB_lower
22     price_to_ma30        | 47     BB_width
23     bb_middle            | 48     volume_SMA_7
24     bb_std               |
```

## Using SHAP for Model Debugging

### Identify Feature Errors:
```python
explanation = requests.post('http://localhost:8000/explain', json=test_data).json()

# Check if a feature has unusually high SHAP value
features = requests.get('http://localhost:8000/model/features').json()['features']
shap_values = explanation['shap_values']

for feature, shap_val in zip(features, shap_values):
    if abs(shap_val) > 10:  # Unusually high
        print(f"⚠ Warning: {feature} has very high SHAP value: {shap_val}")
```

### Verify Feature Impact:
```python
# Features with SHAP value near 0 = not useful
# Features with high SHAP variance = important for predictions
```

---

**Summary**: All SHAP functionality remains available via `/explain` endpoint. This is actually better for production as it separates explainability logic from the UI layer.
