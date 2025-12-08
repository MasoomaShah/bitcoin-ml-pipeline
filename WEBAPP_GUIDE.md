# Bitcoin ML Web App

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-webapp.txt
```

### 2. Run the Streamlit Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

### 3. Run the FastAPI Backend (Optional)

```bash
python api_server.py
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Interactive API: `http://localhost:8000/redoc`

---

## 📊 Features

### Streamlit Dashboard (`app.py`)
- **Real-time Predictions**: Get next-period price direction and change predictions
- **Interactive Charts**: Plotly-powered visualizations
- **Technical Indicators**: RSI, MACD, Bollinger Bands display
- **Model Metrics**: View classification accuracy and regression performance
- **Feature Importance**: See which features drive predictions
- **Auto-refresh**: Optional automatic data updates

### FastAPI Backend (`api_server.py`)
- **REST API**: Standard HTTP endpoints for predictions
- **Model Management**: Load, reload, and query model info
- **Data Access**: Historical data and latest features
- **Health Checks**: Monitor API status
- **OpenAPI Docs**: Auto-generated API documentation

---

## 🎯 API Endpoints

### Core Endpoints

#### `GET /`
Root endpoint with API information

#### `GET /health`
Health check - returns model and data status

#### `GET /predict`
Get prediction for next period
```json
{
  "direction": "UP",
  "direction_confidence": 85.5,
  "price_change_pct": 2.3,
  "current_price": 45000.00,
  "predicted_price": 46035.00,
  "price_change_usd": 1035.00,
  "timestamp": "2025-12-08T10:30:00"
}
```

#### `GET /model/info`
Get model metadata and performance metrics

#### `GET /data/historical?limit=100`
Get historical Bitcoin data (default: 100 records)

#### `GET /data/latest`
Get latest feature values

#### `POST /model/reload`
Reload models and data after training

---

## 📁 Architecture

```
├── app.py                  # Streamlit dashboard (UI)
├── api_server.py           # FastAPI backend (REST API)
├── models/                 # Trained models directory
│   ├── manifest.json
│   ├── v*_classification_model.pkl
│   ├── v*_regression_model.pkl
│   └── v*_*.json
├── data/
│   ├── processed/         # Processed features
│   └── features/          # Latest features
└── src/                   # ML pipeline code
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Alpha Vantage API key for live data
export ALPHA_VANTAGE_API_KEY="your_api_key"
```

### Streamlit Settings

Edit `.streamlit/config.toml` to customize:
- Theme colors
- Server port
- Browser behavior

---

## 💡 Usage Examples

### Example 1: View Dashboard
```bash
streamlit run app.py
```
Navigate to `http://localhost:8501` and explore:
- Current price and prediction
- Historical charts
- Technical indicators
- Model performance metrics

### Example 2: API Request with cURL
```bash
# Get prediction
curl http://localhost:8000/predict

# Get model info
curl http://localhost:8000/model/info

# Get historical data
curl http://localhost:8000/data/historical?limit=50
```

### Example 3: API Request with Python
```python
import requests

# Get prediction
response = requests.get('http://localhost:8000/predict')
prediction = response.json()

print(f"Direction: {prediction['direction']}")
print(f"Confidence: {prediction['direction_confidence']:.1f}%")
print(f"Predicted Price: ${prediction['predicted_price']:,.2f}")
```

### Example 4: Integrate with Your App
```python
import streamlit as st
import requests

# Call API
prediction = requests.get('http://localhost:8000/predict').json()

# Display in Streamlit
st.metric(
    "Predicted Direction",
    prediction['direction'],
    delta=f"{prediction['price_change_pct']:.2f}%"
)
```

---

## 🎨 Customization

### Change Dashboard Theme

Edit the CSS in `app.py`:
```python
st.markdown("""
<style>
    .main-header {
        color: #YOUR_COLOR;
    }
</style>
""", unsafe_allow_html=True)
```

### Add New API Endpoints

In `api_server.py`:
```python
@app.get("/custom/endpoint")
def custom_endpoint():
    return {"message": "Custom response"}
```

### Add New Charts

In `app.py`:
```python
fig = go.Figure()
# Add your chart code
st.plotly_chart(fig)
```

---

## 🚨 Troubleshooting

### Models Not Loading
```bash
# Train models first
python src/train_with_feature_store.py

# Check models directory
ls models/
```

### Data Not Available
```bash
# Fetch fresh data
python src/fetch_alpha_vantage.py

# Or use existing data
ls data/processed/
```

### Port Already in Use
```bash
# Streamlit (default: 8501)
streamlit run app.py --server.port 8502

# FastAPI (default: 8000)
uvicorn api_server:app --port 8001
```

### Import Errors
```bash
# Ensure all dependencies installed
pip install -r requirements-webapp.txt

# Verify Python path
python -c "import sys; print(sys.path)"
```

---

## 📈 Performance Tips

1. **Model Caching**: Models are cached in memory for fast predictions
2. **Data Caching**: Streamlit caches data with `@st.cache_data`
3. **Async API**: FastAPI handles concurrent requests efficiently
4. **Auto-refresh**: Enable in sidebar for live updates (60s interval)

---

## 🔒 Security Notes

⚠️ **For Production Deployment:**
- Add authentication (API keys, OAuth)
- Enable HTTPS/TLS
- Rate limiting for API endpoints
- Input validation and sanitization
- Environment-based configuration
- Secure API key storage

---

## 📝 Disclaimer

This web app is for **educational purposes only**. The predictions are based on historical data and should not be considered financial advice. Always do your own research before making investment decisions.

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API docs at `/docs`
3. Verify models are trained and data is available
