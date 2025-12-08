"""
Bitcoin ML Prediction Dashboard - Streamlit App

Features:
- Load trained models and make predictions
- Fetch features from local data/Feature Store
- Interactive dashboard with charts and metrics
- Real-time Bitcoin price prediction
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import joblib
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Page configuration
st.set_page_config(
    page_title="Bitcoin ML Predictions",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .prediction-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .up-prediction {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
    }
    .down-prediction {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_latest_model():
    """Load the latest trained model and metadata"""
    try:
        models_dir = Path("models")
        manifest_path = models_dir / "manifest.json"
        
        if not manifest_path.exists():
            return None, None, None, None, None
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        latest = manifest['models'][0]  # First model is latest
        version = latest['version']
        
        # Load models and metadata
        clf_model = joblib.load(models_dir / f"{version}_clf_model.pkl")
        reg_model = joblib.load(models_dir / f"{version}_reg_model.pkl")
        scaler = joblib.load(models_dir / f"{version}_scaler.pkl")
        
        with open(models_dir / f"{version}_feature_columns.json", 'r') as f:
            feature_columns = json.load(f)
        
        with open(models_dir / f"{version}_training_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        return clf_model, reg_model, scaler, feature_columns, metadata
    
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None, None, None, None


@st.cache_data
def load_bitcoin_data():
    """Load Bitcoin historical data"""
    try:
        # Try to load from API first
        from src.fetch_alpha_vantage import fetch_crypto_with_indicators
        from src.preprocess_bitcoin import preprocess_bitcoin_data
        
        df = fetch_crypto_with_indicators(
            symbol='BTC',
            market='USD',
            api_key=os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        )
        
        if df is not None and not df.empty:
            df_processed = preprocess_bitcoin_data(df)
            return df_processed
        
    except Exception as e:
        st.warning(f"Could not fetch live data: {e}")
    
    # Fallback to stored data
    data_files = list(Path("data/processed").glob("*.csv"))
    if data_files:
        latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
        return pd.read_csv(latest_file)
    
    return None


def create_price_chart(df, predictions=None):
    """Create interactive price chart with predictions"""
    fig = go.Figure()
    
    # Historical prices
    fig.add_trace(go.Scatter(
        x=df['timestamp'] if 'timestamp' in df.columns else df.index,
        y=df['close'],
        mode='lines',
        name='BTC Price',
        line=dict(color='#FF6B35', width=2)
    ))
    
    # Add predictions if available
    if predictions is not None:
        fig.add_trace(go.Scatter(
            x=[df['timestamp'].iloc[-1] if 'timestamp' in df.columns else df.index[-1]],
            y=[predictions['predicted_price']],
            mode='markers',
            name='Predicted Price',
            marker=dict(size=15, color='#4ECDC4', symbol='star')
        ))
    
    fig.update_layout(
        title='Bitcoin Price History',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig


def create_feature_importance_chart(features, values):
    """Create feature importance chart"""
    df = pd.DataFrame({
        'Feature': features[:10],  # Top 10
        'Value': values[:10]
    })
    
    fig = px.bar(
        df,
        x='Value',
        y='Feature',
        orientation='h',
        title='Top 10 Important Features',
        color='Value',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(height=400, template='plotly_white')
    return fig


def make_predictions(clf_model, reg_model, scaler, features, feature_columns):
    """Make predictions using the models"""
    try:
        # Prepare feature vector
        X = features[feature_columns].values.reshape(1, -1)
        X_scaled = scaler.transform(X)
        
        # Classification prediction (Up/Down)
        direction_pred = clf_model.predict(X_scaled)[0]
        direction_proba = clf_model.predict_proba(X_scaled)[0]
        
        # Regression prediction (Price change)
        price_change_pred = reg_model.predict(X_scaled)[0]
        
        # Calculate predicted price
        current_price = features['close'].values[0]
        predicted_price = current_price * (1 + price_change_pred)
        
        return {
            'direction': 'UP ⬆️' if direction_pred == 1 else 'DOWN ⬇️',
            'direction_confidence': float(max(direction_proba)) * 100,
            'price_change_pct': float(price_change_pred) * 100,
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'price_change_usd': float(predicted_price - current_price)
        }
    
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None


def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<div class="main-header">₿ Bitcoin ML Prediction Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=100)
        st.title("Settings")
        
        auto_refresh = st.checkbox("Auto-refresh data", value=False)
        if auto_refresh:
            st.info("Data refreshes every 60 seconds")
        
        show_technical = st.checkbox("Show technical indicators", value=True)
        show_raw_data = st.checkbox("Show raw data", value=False)
        
        st.divider()
        st.markdown("### About")
        st.markdown("""
        This dashboard uses machine learning models trained on historical Bitcoin data 
        to predict future price movements.
        
        **Models:**
        - Classification: Price direction (Up/Down)
        - Regression: Price change prediction
        
        **Features:**
        - 24 technical indicators
        - Real-time predictions
        - Interactive charts
        """)
    
    # Load model and data
    with st.spinner("Loading models and data..."):
        clf_model, reg_model, scaler, feature_columns, metadata = load_latest_model()
        df = load_bitcoin_data()
    
    if clf_model is None or df is None:
        st.error("❌ Could not load models or data. Please train models first.")
        st.code("python src/train_with_feature_store.py")
        return
    
    # Model info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Model Version", metadata.get('version', 'Unknown')[:16])
    with col2:
        st.metric("Training Date", metadata.get('timestamp', 'Unknown')[:10])
    with col3:
        st.metric("Classification Accuracy", f"{metadata.get('classification_accuracy', 0)*100:.1f}%")
    with col4:
        st.metric("Regression RMSE", f"{metadata.get('regression_rmse', 0):.4f}")
    
    st.divider()
    
    # Get latest features for prediction
    latest_features = df.tail(1).copy()
    
    # Make predictions
    predictions = make_predictions(clf_model, reg_model, scaler, latest_features, feature_columns)
    
    if predictions:
        # Prediction display
        st.subheader("🔮 Next Period Prediction")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            direction_class = "up-prediction" if predictions['direction'] == 'UP ⬆️' else "down-prediction"
            st.markdown(f"""
            <div class="prediction-box {direction_class}">
                <div style="font-size: 2.5rem;">{predictions['direction']}</div>
                <div style="font-size: 1rem; opacity: 0.9;">Confidence: {predictions['direction_confidence']:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric(
                "Current Price",
                f"${predictions['current_price']:,.2f}",
                delta=None
            )
            st.metric(
                "Predicted Price",
                f"${predictions['predicted_price']:,.2f}",
                delta=f"${predictions['price_change_usd']:,.2f}"
            )
        
        with col3:
            st.metric(
                "Expected Change",
                f"{predictions['price_change_pct']:.2f}%",
                delta=f"${predictions['price_change_usd']:,.2f}"
            )
            
            # Risk indicator
            risk_level = "High" if abs(predictions['price_change_pct']) > 2 else "Medium" if abs(predictions['price_change_pct']) > 1 else "Low"
            st.metric("Volatility Risk", risk_level)
    
    st.divider()
    
    # Price chart
    st.subheader("📈 Price History & Prediction")
    price_chart = create_price_chart(df.tail(100), predictions)
    st.plotly_chart(price_chart, use_container_width=True)
    
    # Technical indicators
    if show_technical and 'rsi' in df.columns:
        st.subheader("📊 Technical Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rsi_value = df['rsi'].iloc[-1]
            rsi_status = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
            st.metric("RSI", f"{rsi_value:.2f}", delta=rsi_status)
        
        with col2:
            if 'macd' in df.columns:
                st.metric("MACD", f"{df['macd'].iloc[-1]:.2f}")
        
        with col3:
            if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                bb_width = df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]
                st.metric("BB Width", f"{bb_width:.2f}")
        
        with col4:
            if 'volume' in df.columns:
                st.metric("Volume", f"{df['volume'].iloc[-1]:,.0f}")
    
    # Feature importance (if available in metadata)
    if 'feature_importance' in metadata:
        st.subheader("🎯 Feature Importance")
        features = list(metadata['feature_importance'].keys())[:10]
        values = list(metadata['feature_importance'].values())[:10]
        fig = create_feature_importance_chart(features, values)
        st.plotly_chart(fig, use_container_width=True)
    
    # Raw data
    if show_raw_data:
        st.subheader("📋 Raw Data")
        st.dataframe(df.tail(20), use_container_width=True)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>⚠️ <strong>Disclaimer:</strong> This is for educational purposes only. Not financial advice.</p>
        <p>Model trained on historical data. Past performance does not guarantee future results.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
