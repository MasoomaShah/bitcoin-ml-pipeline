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
import requests
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
    """Load the latest trained model and metadata (from Vertex AI or local files)"""
    try:
        from src.load_models_vertex_ai import load_models_from_vertex_ai
        
        clf_model, reg_model, scaler, feature_columns, metadata = load_models_from_vertex_ai()
        
        if clf_model is None:
            return None, None, None, None, None
        
        return clf_model, reg_model, scaler, feature_columns, metadata
    
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None, None, None, None


@st.cache_data(ttl=3600)  # Cache for 1 hour to prevent constant reloads
def load_bitcoin_data():
    """Load Bitcoin historical data - returns both raw and processed data"""
    try:
        # Use CoinGecko API (same as training pipeline) for consistency
        from src.fetch_bitcoin_data import fetch_bitcoin_data, add_technical_indicators, calculate_price_changes
        
        df_raw = fetch_bitcoin_data(
            days=365,
            vs_currency='usd'
        )
        
        if df_raw is not None and not df_raw.empty:
            # Ensure consistent sorting by date
            if 'date' in df_raw.columns:
                df_raw = df_raw.sort_values('date').reset_index(drop=True)
            
            # CoinGecko already provides lowercase 'price', 'volume', 'market_cap'
            # No need to rename columns - they're already in the right format
            
            # Calculate price changes and add technical indicators (matching training pipeline)
            df_processed = df_raw.copy()
            df_processed = calculate_price_changes(df_processed)
            df_processed = add_technical_indicators(df_processed)
            
            # Add additional technical indicators from preprocessing function
            # This ensures we have all 49 features like the trained model expects
            price_col = 'price'
            
            # SMA (Simple Moving Averages) - with different windows than price_ma*
            df_processed['SMA_7'] = df_processed[price_col].rolling(window=7, min_periods=1).mean()
            df_processed['SMA_14'] = df_processed[price_col].rolling(window=14, min_periods=1).mean()
            df_processed['SMA_30'] = df_processed[price_col].rolling(window=30, min_periods=1).mean()
            
            # EMA (Exponential Moving Averages)
            df_processed['EMA_7'] = df_processed[price_col].ewm(span=7, adjust=False).mean()
            df_processed['EMA_14'] = df_processed[price_col].ewm(span=14, adjust=False).mean()
            
            # Momentum (different calculation than momentum_3d, 7d, 14d)
            df_processed['momentum_7'] = df_processed[price_col].pct_change(periods=7)
            df_processed['momentum_14'] = df_processed[price_col].pct_change(periods=14)
            df_processed['momentum_30'] = df_processed[price_col].pct_change(periods=30)
            
            # Volatility (rolling std with different windows)
            df_processed['volatility_7'] = df_processed[price_col].rolling(window=7, min_periods=1).std()
            df_processed['volatility_14'] = df_processed[price_col].rolling(window=14, min_periods=1).std()
            
            # RSI (Relative Strength Index) - improved calculation
            delta = df_processed[price_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / (loss + 1e-10)
            df_processed['RSI'] = 100 - (100 / (1 + rs))
            df_processed['RSI'] = np.clip(df_processed['RSI'], 0, 100)
            
            # MACD
            ema_12 = df_processed[price_col].ewm(span=12, adjust=False).mean()
            ema_26 = df_processed[price_col].ewm(span=26, adjust=False).mean()
            df_processed['MACD'] = ema_12 - ema_26
            df_processed['MACD_signal'] = df_processed['MACD'].ewm(span=9, adjust=False).mean()
            
            # Bollinger Bands
            df_processed['BB_middle'] = df_processed[price_col].rolling(window=20, min_periods=1).mean()
            bb_std = df_processed[price_col].rolling(window=20, min_periods=1).std()
            bb_std = bb_std.fillna(0)
            df_processed['BB_upper'] = df_processed['BB_middle'] + (bb_std * 2)
            df_processed['BB_lower'] = df_processed['BB_middle'] - (bb_std * 2)
            df_processed['BB_width'] = df_processed['BB_upper'] - df_processed['BB_lower']
            
            # Volume SMA
            df_processed['volume_SMA_7'] = df_processed['volume'].rolling(window=7, min_periods=1).mean()
            
            # Clean infinity and NaN values with consistent median calculation
            for col in df_processed.select_dtypes(include=[np.number]).columns:
                # Calculate median once to ensure consistency
                col_median = df_processed[col].replace([np.inf, -np.inf], np.nan).median()
                df_processed[col] = df_processed[col].replace([np.inf, -np.inf], col_median)
                df_processed[col] = df_processed[col].fillna(col_median)
            
            return df_raw, df_processed
        
    except Exception as e:
        st.warning(f"Could not fetch live data: {e}")
    
    # Fallback to stored data
    data_files = list(Path("data/processed").glob("*.csv"))
    if data_files:
        latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
        df = pd.read_csv(latest_file)
        return df, df  # Return same for both if from file
    
    return None, None


def create_price_chart(df, predictions=None):
    """Create interactive price chart with predictions"""
    fig = go.Figure()
    
    # Determine the price column name
    price_col = None
    for col_name in ['close', 'Close', 'price', 'Price']:
        if col_name in df.columns:
            price_col = col_name
            break
    
    if price_col is None:
        st.error(f"Could not find price column. Available columns: {df.columns.tolist()}")
        return None
    
    # Historical prices
    fig.add_trace(go.Scatter(
        x=df['timestamp'] if 'timestamp' in df.columns else (df['date'] if 'date' in df.columns else df.index),
        y=df[price_col],
        mode='lines',
        name='BTC Price',
        line=dict(color='#FF6B35', width=2)
    ))
    
    # Add predictions if available
    if predictions is not None:
        # Get the correct date/time column
        if 'date' in df.columns:
            last_date = df['date'].iloc[-1]
        elif 'timestamp' in df.columns:
            last_date = df['timestamp'].iloc[-1]
        else:
            last_date = df.index[-1]
        
        # Show both current and predicted price
        fig.add_trace(go.Scatter(
            x=[last_date, last_date],
            y=[predictions['current_price'], predictions['predicted_price']],
            mode='markers+lines',
            name='Prediction',
            line=dict(color='#4ECDC4', width=3, dash='dash'),
            marker=dict(size=12, color=['#FF6B35', '#4ECDC4'], symbol=['circle', 'star'])
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


def make_predictions(clf_model, reg_model, scaler, features, feature_columns, current_price):
    """Make predictions using the models"""
    try:
        import warnings
        from sklearn.utils.validation import check_array
        
        # Suppress sklearn warning about feature names
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='X does not have valid feature names')
            
            # Prepare feature vector with dummy target columns (scaler was fitted with 51 columns: 49 features + 2 targets)
            X_df = features[feature_columns].copy()
            X_df['future_price_change'] = 0.0
            X_df['market_class'] = 1
            
            # Get scaler column order and transform
            scaler_columns = list(scaler.feature_names_in_)
            X_all_scaled = scaler.transform(X_df[scaler_columns].values)
            
            # Extract only the feature columns for model prediction
            feature_indices = [scaler_columns.index(f) for f in feature_columns]
            X_scaled = X_all_scaled[:, feature_indices]
            
            # Clean any remaining infinity or NaN values
            X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Classification prediction (Up/Down)
            direction_pred = clf_model.predict(X_scaled)[0]
            direction_proba = clf_model.predict_proba(X_scaled)[0]
            
            # Regression prediction (Price change)
            price_change_raw = reg_model.predict(X_scaled)[0]
            
            # Clamp price change to realistic range based on recent volatility
            from src.normalize_predictions import clamp_price_prediction
            # Use the features data (which is the processed Bitcoin data) to get recent changes
            recent_changes = features['price'].pct_change().dropna().tail(100).values if 'price' in features.columns else None
            price_change_pred = clamp_price_prediction(price_change_raw, recent_changes, percentile=95)
        
        # Calculate predicted price
        predicted_price = current_price * (1 + price_change_pred)
        
        return {
            'direction': 'UP ⬆️' if direction_pred == 1 else 'DOWN ⬇️',
            'direction_confidence': float(max(direction_proba)) * 100,
            'price_change_pct': float(price_change_pred) * 100,
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'price_change_usd': float(predicted_price - current_price)
        }
    
    except KeyError as e:
        st.error(f"Feature missing: {e}")
        st.write(f"Available features in data: {features.columns.tolist()}")
        st.write(f"Expected features: {feature_columns}")
        return None
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
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
            st.success("✅ Auto-refresh ENABLED - Updates every 60 seconds")
            # Show countdown
            refresh_placeholder = st.empty()
            import time
            current_time = int(time.time()) % 60
            seconds_until_refresh = 60 - current_time
            refresh_placeholder.info(f"⏱️ Next refresh in ~{seconds_until_refresh} seconds")
        else:
            st.warning("⚠️ Auto-refresh DISABLED - Data is cached")
        
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
    try:
        with st.spinner("Loading models and data..."):
            clf_model, reg_model, scaler, feature_columns, metadata = load_latest_model()
            df_raw, df_processed = load_bitcoin_data()
    except Exception as e:
        st.error(f"ERROR during loading: {e}")
        import traceback
        st.write(traceback.format_exc())
        return
    
    if clf_model is None or df_raw is None or df_processed is None:
        st.error("❌ Could not load models or data. Please train models first.")
        st.code("python src/train_with_feature_store.py")
        return
    
    st.success("✅ Models and data loaded successfully")
    
    # Show data timestamp
    from datetime import datetime
    if 'date' in df_raw.columns:
        last_data_time = df_raw['date'].iloc[-1]
        st.info(f"📅 Latest data: {last_data_time} | Loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for missing features
    missing_features = set(feature_columns) - set(df_processed.columns)
    if missing_features:
        st.error(f"Missing features: {missing_features}")
        st.stop()
    
    # Model info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        version = metadata.get('version', metadata.get('model_version', 'Unknown'))
        st.metric("Model Version", version[-16:] if version != 'Unknown' else version)
    with col2:
        created_at = metadata.get('created_at', 'Unknown')
        st.metric("Training Date", created_at[:10] if created_at != 'Unknown' else created_at)
    with col3:
        clf_metrics = metadata.get('classification_metrics', {})
        clf_acc = clf_metrics.get('accuracy', 0)
        st.metric("Classification Accuracy", f"{clf_acc*100:.1f}%")
    with col4:
        reg_metrics = metadata.get('regression_metrics', {})
        reg_rmse = reg_metrics.get('rmse', 0)
        st.metric("Regression RMSE", f"{reg_rmse:.4f}")
    
    st.divider()
    
    # Get latest features for prediction
    latest_features = df_processed.tail(1).copy()
    
    # Get current price from raw data
    price_col = 'Close' if 'Close' in df_raw.columns else 'close' if 'close' in df_raw.columns else 'price'
    current_price = df_raw[price_col].iloc[-1]
    
    # Make predictions
    predictions = make_predictions(clf_model, reg_model, scaler, latest_features, feature_columns, current_price)
    
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
                delta=predictions['price_change_usd']  # Pass as number so Streamlit shows correct color
            )
        
        with col3:
            # Make delta always show the right direction
            delta_val = predictions['price_change_usd']
            st.metric(
                "Expected Change",
                f"{predictions['price_change_pct']:.2f}%",
                delta=delta_val  # Pass as number, Streamlit handles formatting
            )
            
            # Risk indicator
            risk_level = "High" if abs(predictions['price_change_pct']) > 2 else "Medium" if abs(predictions['price_change_pct']) > 1 else "Low"
            st.metric("Volatility Risk", risk_level)
    
    st.divider()
    
    # Price chart
    st.subheader("📈 Price History & Prediction")
    price_chart = create_price_chart(df_raw.tail(100), predictions)
    if price_chart:
        st.plotly_chart(price_chart, use_container_width=True)
    
    # ==================== SHAP EXPLAINABILITY ====================
    if predictions:
        st.divider()
        st.markdown("## 🔍 SHAP Explanation - Why This Prediction?")
        
        try:
            features_dict = dict(zip(feature_columns, latest_features[feature_columns].values[0].tolist()))
            response = requests.post("http://localhost:8000/explain", json={"features": features_dict}, timeout=120)
            
            if response.status_code == 200:
                explanation = response.json()
                
                # Feature importance chart
                feature_importance = explanation.get('feature_importance', {})
                if feature_importance:
                    importance_df = pd.DataFrame({
                        'Feature': list(feature_importance.keys()),
                        'Importance': list(feature_importance.values())
                    }).sort_values('Importance', ascending=True).tail(10)
                    
                    fig = px.bar(importance_df, x='Importance', y='Feature', 
                                 orientation='h',
                                 title="📊 Top 10 Most Important Features",
                                 color='Importance',
                                 color_continuous_scale='Viridis')
                    st.plotly_chart(fig, use_container_width=True)
                
                # SHAP values chart
                shap_vals = explanation.get('shap_values', [])
                if shap_vals:
                    shap_df = pd.DataFrame({
                        'Feature': feature_columns,
                        'SHAP Value': shap_vals
                    }).sort_values('SHAP Value', key=abs, ascending=True).tail(10)
                    
                    fig_shap = px.bar(shap_df, x='SHAP Value', y='Feature', 
                                      orientation='h',
                                      color='SHAP Value', 
                                      color_continuous_scale='RdBu',
                                      title="🎯 SHAP Values (Red=Push UP, Blue=Push DOWN)")
                    st.plotly_chart(fig_shap, use_container_width=True)
            else:
                st.error(f"❌ Cannot generate SHAP explanations. API Error {response.status_code}")
                st.info("Ensure FastAPI is running: `python -m uvicorn api_server:app --host 0.0.0.0 --port 8000`")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Technical indicators
    if show_technical and 'RSI' in df_raw.columns:
        st.subheader("📊 Technical Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rsi_value = df_raw['RSI'].iloc[-1]
            rsi_status = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
            st.metric("RSI", f"{rsi_value:.2f}", delta=rsi_status)
        
        with col2:
            if 'MACD' in df_raw.columns:
                st.metric("MACD", f"{df_raw['MACD'].iloc[-1]:.2f}")
        
        with col3:
            if 'BB_upper' in df_raw.columns and 'BB_lower' in df_raw.columns:
                bb_width = df_raw['BB_upper'].iloc[-1] - df_raw['BB_lower'].iloc[-1]
                st.metric("BB Width", f"{bb_width:.2f}")
        
        with col4:
            if 'Volume' in df_raw.columns:
                st.metric("Volume", f"{df_raw['Volume'].iloc[-1]:,.0f}")
    
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
        st.dataframe(df_raw.tail(20), use_container_width=True)
    
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
        # Clear cache before rerun to fetch fresh data
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"FATAL ERROR: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
