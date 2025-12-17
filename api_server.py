"""
FastAPI Backend for Bitcoin ML Predictions - SIMPLIFIED

Provides REST API endpoints for:
- Model predictions
- Feature data retrieval
- Model metadata
"""

from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime
import sys
import os
import io

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Initialize FastAPI
app = FastAPI(
    title="Bitcoin ML Prediction API",
    description="REST API for Bitcoin price predictions using ML models",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class FeaturesInput(BaseModel):
    """Input model for custom features (JSON)"""
    features: Dict[str, float] = Field(..., description="Dictionary of feature names and values")
    current_price: Optional[float] = Field(None, description="Current Bitcoin price (optional)")

class NumericFeaturesInput(BaseModel):
    """Input model for numeric feature array"""
    features: List[float] = Field(..., description="Array of 49 feature values in order")
    current_price: Optional[float] = Field(None, description="Current Bitcoin price (optional)")

# Response models
class PredictionResponse(BaseModel):
    direction: str
    direction_confidence: float
    price_change_pct: float
    current_price: float
    predicted_price: float
    price_change_usd: float
    timestamp: str
    input_method: Optional[str] = None

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_records: int

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    data_available: bool
    timestamp: str

class ModelInfo(BaseModel):
    version: str
    timestamp: str
    classification_accuracy: float
    regression_rmse: float
    regression_r2: float
    classification_f1: float
    features_count: int


# Global variables for caching
clf_model = None
reg_model = None
scaler = None
feature_columns = None
metadata = None
bitcoin_data = None


def load_models():
    """Load trained models and metadata (from Vertex AI or local files)"""
    global clf_model, reg_model, scaler, feature_columns, metadata
    
    try:
        from src.load_models_vertex_ai import load_models_from_vertex_ai
        
        clf_model, reg_model, scaler, feature_columns, metadata = load_models_from_vertex_ai()
        
        if clf_model is None:
            return False
        
        return True
    
    except Exception as e:
        print(f"Error loading models: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_data():
    """Load Bitcoin data and generate engineered features"""
    global bitcoin_data
    
    try:
        df = None
        
        # Try loading from raw data first (most recent daily run)
        if Path("data/raw/bitcoin_timeseries.csv").exists():
            print("Loading from data/raw/bitcoin_timeseries.csv...")
            df = pd.read_csv("data/raw/bitcoin_timeseries.csv")
        
        # Try loading from processed data
        if df is None:
            data_files = list(Path("data/processed").glob("*.csv"))
            if data_files:
                print("Loading from data/processed...")
                latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest_file)
        
        # Try loading from features directory
        if df is None:
            feature_files = list(Path("data/features").glob("*.csv"))
            if feature_files:
                print("Loading from data/features...")
                latest_file = max(feature_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest_file)
        
        if df is None:
            print("ERROR: No data files found in data/raw, data/processed, or data/features")
            return False
        
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Check if we need to generate engineered features
        if len(df.columns) < 30:  # Raw data only has 4 columns, need at least 30+ for features
            print("Generating engineered features from raw data...")
            df = generate_engineered_features(df)
        
        if df is None or df.empty:
            print("ERROR: Data is empty after loading")
            return False
        
        bitcoin_data = df
        print(f"Data loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        return True
    
    except Exception as e:
        print(f"ERROR loading data: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_engineered_features(df):
    """Generate 49 engineered features from raw Bitcoin data"""
    try:
        if 'price' not in df.columns:
            print("ERROR: 'price' column not found")
            return None
        
        price_col = 'price'
        
        # Basic moving averages
        df['price_smooth'] = df[price_col].rolling(window=3, min_periods=1).mean()
        df['price_ma3'] = df[price_col].rolling(window=3, min_periods=1).mean()
        df['price_ma7'] = df[price_col].rolling(window=7, min_periods=1).mean()
        df['price_ma14'] = df[price_col].rolling(window=14, min_periods=1).mean()
        df['price_ma30'] = df[price_col].rolling(window=30, min_periods=1).mean()
        
        # Exponential moving averages
        df['price_ema7'] = df[price_col].ewm(span=7, adjust=False).mean()
        df['price_ema14'] = df[price_col].ewm(span=14, adjust=False).mean()
        
        # Momentum
        df['momentum_3d'] = df[price_col].pct_change(periods=3) * 100
        df['momentum_7d'] = df[price_col].pct_change(periods=7) * 100
        df['momentum_14d'] = df[price_col].pct_change(periods=14) * 100
        
        # Rate of change
        df['roc_3d'] = df[price_col].pct_change(periods=3) * 100
        df['roc_7d'] = df[price_col].pct_change(periods=7) * 100
        
        # Volatility
        df['price_volatility_3d'] = df[price_col].rolling(window=3, min_periods=1).std()
        df['price_volatility_7d'] = df[price_col].rolling(window=7, min_periods=1).std()
        df['price_volatility_14d'] = df[price_col].rolling(window=14, min_periods=1).std()
        
        # Volume indicators
        if 'volume' in df.columns:
            df['volume_ma3'] = df['volume'].rolling(window=3, min_periods=1).mean()
            df['volume_ma7'] = df['volume'].rolling(window=7, min_periods=1).mean()
            df['volume_change'] = df['volume'].pct_change(periods=1).fillna(0) * 100
            df['volume_SMA_7'] = df['volume'].rolling(window=7, min_periods=1).mean()
        else:
            df['volume_ma3'] = 0.0
            df['volume_ma7'] = 0.0
            df['volume_change'] = 0.0
            df['volume_SMA_7'] = 0.0
        
        # Price ratios
        df['price_to_ma7'] = df[price_col] / (df['price_ma7'] + 1e-10)
        df['price_to_ma30'] = df[price_col] / (df['price_ma30'] + 1e-10)
        
        # Bollinger Bands
        df['bb_middle'] = df[price_col].rolling(window=20, min_periods=1).mean()
        bb_std = df[price_col].rolling(window=20, min_periods=1).std()
        bb_std = bb_std.fillna(0)
        df['bb_std'] = bb_std
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df[price_col] - df['bb_lower']) / ((df['bb_upper'] - df['bb_lower']) + 1e-10)
        
        # RSI
        delta = df[price_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss + 1e-10)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        df['rsi_14'] = np.clip(df['rsi_14'], 0, 100)
        
        # Market cap indicators
        if 'market_cap' in df.columns:
            df['market_cap_change'] = df['market_cap'].pct_change(periods=1).fillna(0) * df['market_cap']
            df['volume_to_marketcap'] = df['volume'] / (df['market_cap'] + 1e-10) if 'volume' in df.columns else 0.0
        else:
            df['market_cap_change'] = 0.0
            df['volume_to_marketcap'] = 0.0
        
        # Alternative indicators (SMA, EMA, momentum, volatility)
        df['SMA_7'] = df[price_col].rolling(window=7, min_periods=1).mean()
        df['SMA_14'] = df[price_col].rolling(window=14, min_periods=1).mean()
        df['SMA_30'] = df[price_col].rolling(window=30, min_periods=1).mean()
        
        df['EMA_7'] = df[price_col].ewm(span=7, adjust=False).mean()
        df['EMA_14'] = df[price_col].ewm(span=14, adjust=False).mean()
        
        df['momentum_7'] = df[price_col].pct_change(periods=7) * 100
        df['momentum_14'] = df[price_col].pct_change(periods=14) * 100
        df['momentum_30'] = df[price_col].pct_change(periods=30) * 100
        
        df['volatility_7'] = df[price_col].rolling(window=7, min_periods=1).std()
        df['volatility_14'] = df[price_col].rolling(window=14, min_periods=1).std()
        
        df['RSI'] = df['rsi_14'].copy()
        
        # MACD
        ema_12 = df[price_col].ewm(span=12, adjust=False).mean()
        ema_26 = df[price_col].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands alternatives
        df['BB_middle'] = df['bb_middle'].copy()
        df['BB_upper'] = df['bb_upper'].copy()
        df['BB_lower'] = df['bb_lower'].copy()
        df['BB_width'] = df['BB_upper'] - df['BB_lower']
        
        # Clean NaN and infinity values
        for col in df.select_dtypes(include=[np.number]).columns:
            col_median = df[col].replace([np.inf, -np.inf], np.nan).median()
            if pd.isna(col_median):
                col_median = 0.0
            df[col] = df[col].replace([np.inf, -np.inf], col_median)
            df[col] = df[col].fillna(col_median)
        
        print(f"Generated features: {len(df.columns)} total columns")
        return df
        
    except Exception as e:
        print(f"ERROR generating features: {e}")
        import traceback
        traceback.print_exc()
        return None


def scale_features(X, feature_names):
    """Scale features using the loaded scaler"""
    try:
        # Create dataframe with feature columns
        X_df = pd.DataFrame(X, columns=feature_names)
        
        # Add columns expected by scaler (51 columns total)
        X_df['future_price_change'] = 0.0
        X_df['market_class'] = 1
        
        # Get scaler feature names
        scaler_columns = list(scaler.feature_names_in_)
        
        # Reorder and scale
        X_all_scaled = scaler.transform(X_df[scaler_columns].values)
        
        # Extract only the feature columns we care about
        feature_indices = [scaler_columns.index(f) for f in feature_names]
        X_scaled = X_all_scaled[:, feature_indices]
        
        return X_scaled
    
    except Exception as e:
        print(f"Error scaling features: {e}")
        return X


@app.on_event("startup")
def startup_event():
    """Load models on startup"""
    print("Starting FastAPI server...")
    load_models()
    load_data()


@app.get("/", response_model=Dict)
def root():
    """API Root - Available endpoints"""
    return {
        "service": "Bitcoin ML Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health - Health check",
            "predict_price": "/predict?price=XXX - Simple price prediction",
            "predict_json": "/predict/json - Prediction with all 49 features (JSON)",
            "predict_numeric": "/predict/numeric - Prediction with all 49 features (array)",
            "predict_batch": "/predict/file - Batch predictions from CSV file",
            "model_info": "/model/info - Model metadata and metrics",
            "model_features": "/model/features - List of 49 required features",
            "reload_model": "/model/reload - Reload models from disk"
        },
        "models": {
            "classification": "RandomForestClassifier (predicts UP/DOWN)",
            "regression": "RandomForestRegressor (predicts price change %)"
        },
        "features": "49 technical indicators (price, moving averages, volatility, RSI, Bollinger Bands, etc.)"
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if clf_model is not None else "unhealthy",
        model_loaded=clf_model is not None,
        data_available=bitcoin_data is not None,
        timestamp=datetime.now().isoformat()
    )


@app.get("/predict", response_model=PredictionResponse)
def predict():
    """
    Predict tomorrow's Bitcoin price based on today's data
    
    Automatically fetches today's latest Bitcoin data and technical indicators,
    then predicts tomorrow's price direction and change percentage.
    This is equivalent to the Streamlit app prediction.
    """
    if clf_model is None or reg_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    if bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Bitcoin data not loaded")
    
    try:
        # Get latest data point (today's data with all 49 features)
        latest_row = bitcoin_data.iloc[-1].copy()
        
        # Ensure we have the price column
        price_col = next((col for col in ['price', 'Price', 'close', 'Close'] if col in bitcoin_data.columns), None)
        if price_col is None:
            raise ValueError("No price column found in data")
        
        current_price = float(latest_row[price_col])
        
        # Prepare feature vector (same as Streamlit)
        try:
            X_df = latest_row[feature_columns].to_frame().T.copy()
            X_df['future_price_change'] = 0.0
            X_df['market_class'] = 1
            
            # Scale using the loaded scaler
            scaler_columns = list(scaler.feature_names_in_)
            X_all_scaled = scaler.transform(X_df[scaler_columns].values)
            
            # Extract only feature columns
            feature_indices = [scaler_columns.index(f) for f in feature_columns]
            X_scaled = X_all_scaled[:, feature_indices]
            X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Get predictions
            clf_pred = clf_model.predict(X_scaled)[0]
            clf_proba = clf_model.predict_proba(X_scaled)[0]
            reg_pred = reg_model.predict(X_scaled)[0]
            
            # Calculate final values
            price_change_pct = float(reg_pred)
            direction = "UP" if price_change_pct > 0 else "DOWN"
            confidence = float(max(clf_proba)) * 100
            predicted_price = current_price * (1 + price_change_pct / 100)
            price_change_usd = predicted_price - current_price
            
            return PredictionResponse(
                direction=direction,
                direction_confidence=confidence,
                price_change_pct=price_change_pct,
                current_price=current_price,
                predicted_price=predicted_price,
                price_change_usd=price_change_usd,
                timestamp=datetime.now().isoformat(),
                input_method="auto_features"
            )
        
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Feature processing error: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/json", response_model=PredictionResponse)
def predict_json(input_data: FeaturesInput):
    """
    Prediction with all 49 features as JSON dictionary
    
    Requires a JSON object with all 49 feature names.
    Use test_fastapi_json.json as an example.
    """
    if clf_model is None or reg_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Validate all required features are present
        missing_features = set(feature_columns) - set(input_data.features.keys())
        if missing_features:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required features: {list(missing_features)}"
            )
        
        X = np.array([[input_data.features[col] for col in feature_columns]])
        X_scaled = scale_features(X, feature_columns)
        
        # Get predictions
        clf_pred = clf_model.predict(X_scaled)[0]
        clf_proba = clf_model.predict_proba(X_scaled)[0]
        reg_pred = reg_model.predict(X_scaled)[0]
        
        current_price = input_data.current_price or input_data.features.get('price', 0)
        # Use regression prediction for direction (more reliable than classification)
        price_change_pct = float(reg_pred)
        direction = "UP" if price_change_pct > 0 else "DOWN"
        confidence = float(max(clf_proba)) * 100
        predicted_price = current_price * (1 + price_change_pct / 100)
        price_change_usd = predicted_price - current_price
        
        return PredictionResponse(
            direction=direction,
            direction_confidence=confidence,
            price_change_pct=price_change_pct,
            current_price=current_price,
            predicted_price=predicted_price,
            price_change_usd=price_change_usd,
            timestamp=datetime.now().isoformat(),
            input_method="json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/numeric", response_model=PredictionResponse)
def predict_numeric(input_data: NumericFeaturesInput):
    """
    Prediction with 49 features as numeric array
    
    Features must be provided in the exact order matching /model/features endpoint.
    Use test_fastapi_numeric.json as an example.
    """
    if clf_model is None or reg_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        if len(input_data.features) != len(feature_columns):
            raise HTTPException(
                status_code=400,
                detail=f"Expected {len(feature_columns)} features, got {len(input_data.features)}"
            )
        
        X = np.array([input_data.features])
        X_scaled = scale_features(X, feature_columns)
        
        # Get predictions
        clf_pred = clf_model.predict(X_scaled)[0]
        clf_proba = clf_model.predict_proba(X_scaled)[0]
        reg_pred = reg_model.predict(X_scaled)[0]
        
        current_price = input_data.current_price or input_data.features[0]
        # Use regression prediction for direction (more reliable than classification)
        price_change_pct = float(reg_pred)
        direction = "UP" if price_change_pct > 0 else "DOWN"
        confidence = float(max(clf_proba)) * 100
        predicted_price = current_price * (1 + price_change_pct / 100)
        price_change_usd = predicted_price - current_price
        
        return PredictionResponse(
            direction=direction,
            direction_confidence=confidence,
            price_change_pct=price_change_pct,
            current_price=current_price,
            predicted_price=predicted_price,
            price_change_usd=price_change_usd,
            timestamp=datetime.now().isoformat(),
            input_method="numeric_array"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/file", response_model=BatchPredictionResponse)
def predict_batch(file: UploadFile = File(...)):
    """
    Batch predictions from CSV file
    
    CSV file must have 49 columns with headers matching the feature names.
    Use test_fastapi_batch.csv as an example.
    """
    if clf_model is None or reg_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate columns
        missing_features = set(feature_columns) - set(df.columns)
        if missing_features:
            raise HTTPException(
                status_code=400,
                detail=f"CSV missing required features: {list(missing_features)}"
            )
        
        predictions = []
        
        for idx, row in df.iterrows():
            try:
                X = np.array([[row[col] for col in feature_columns]])
                X_scaled = scale_features(X, feature_columns)
                
                clf_pred = clf_model.predict(X_scaled)[0]
                clf_proba = clf_model.predict_proba(X_scaled)[0]
                reg_pred = reg_model.predict(X_scaled)[0]
                
                current_price = row.get('price', row.get('current_price', 0))
                # Use regression prediction for direction (more reliable than classification)
                price_change_pct = float(reg_pred)
                direction = "UP" if price_change_pct > 0 else "DOWN"
                confidence = float(max(clf_proba)) * 100
                predicted_price = current_price * (1 + price_change_pct / 100)
                price_change_usd = predicted_price - current_price
                
                predictions.append(PredictionResponse(
                    direction=direction,
                    direction_confidence=confidence,
                    price_change_pct=price_change_pct,
                    current_price=current_price,
                    predicted_price=predicted_price,
                    price_change_usd=price_change_usd,
                    timestamp=datetime.now().isoformat()
                ))
            except Exception as e:
                print(f"Error predicting row {idx}: {e}")
                continue
        
        return BatchPredictionResponse(
            predictions=predictions,
            total_records=len(predictions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File processing error: {str(e)}")


@app.get("/model/features")
def get_feature_names():
    """Get list of required feature names in order"""
    if feature_columns is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    return {
        "features": feature_columns,
        "count": len(feature_columns),
        "description": "Features must be provided in this exact order for numeric array input"
    }


@app.get("/model/info", response_model=ModelInfo)
def get_model_info():
    """Get model metadata and performance metrics"""
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model metadata not loaded")
    
    return ModelInfo(
        version=metadata.get('version', 'unknown'),
        timestamp=metadata.get('timestamp', 'unknown'),
        classification_accuracy=metadata.get('classification_accuracy', 0.0),
        regression_rmse=metadata.get('regression_rmse', 0.0),
        regression_r2=metadata.get('regression_r2', 0.0),
        classification_f1=metadata.get('classification_f1', 0.0),
        features_count=len(feature_columns) if feature_columns else 0
    )


@app.get("/data/historical")
def get_historical_data(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """Get historical Bitcoin data"""
    if bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        return bitcoin_data.tail(limit).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


@app.get("/data/latest")
def get_latest_data():
    """Get the latest Bitcoin data point"""
    if bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        latest = bitcoin_data.iloc[-1].to_dict()
        return latest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


@app.post("/explain")
def explain_prediction(input_data: FeaturesInput):
    """Generate SHAP-like explanations for prediction (Streamlit integration)"""
    global clf_model, reg_model, scaler, feature_columns
    
    if clf_model is None or reg_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    try:
        # Extract features from input dict, maintaining feature_columns order
        X_list = []
        for feat in feature_columns:
            if feat in input_data.features:
                X_list.append(input_data.features[feat])
            else:
                X_list.append(0.0)  # Default if missing
        
        X = np.array([X_list])  # Shape: (1, 49)
        
        # Scale features
        X_df = pd.DataFrame(X, columns=feature_columns)
        X_df['future_price_change'] = 0.0
        X_df['market_class'] = 1
        scaler_columns = list(scaler.feature_names_in_)
        X_all_scaled = scaler.transform(X_df[scaler_columns].values)
        feature_indices = [scaler_columns.index(f) for f in feature_columns]
        X_scaled = X_all_scaled[:, feature_indices]
        
        # Get model predictions
        reg_pred = float(reg_model.predict(X_scaled)[0])
        
        # Get feature importance from regression model
        if hasattr(reg_model, 'feature_importances_'):
            importances = reg_model.feature_importances_
            feature_importance = {
                name: float(imp) 
                for name, imp in zip(feature_columns, importances)
            }
            # Sort and get top 15
            top_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:15]
            feature_importance = dict(top_features)
        else:
            feature_importance = {}
        
        # Compute SHAP-like values (feature contribution)
        shap_values = []
        predictions_baseline = reg_model.predict(X_scaled)[0]
        
        for i in range(len(feature_columns)):
            X_permuted = X_scaled.copy()
            noise = np.random.normal(0, 0.01, 1)
            X_permuted[0, i] += noise[0]
            prediction_permuted = reg_model.predict(X_permuted)[0]
            contribution = (prediction_permuted - predictions_baseline) / (noise[0] + 1e-10)
            shap_values.append(float(contribution))
        
        return {
            "status": "success",
            "explanation_method": "shap_approximation",
            "prediction": {
                "price_change_pct": reg_pred,
                "direction": "UP" if reg_pred > 0 else "DOWN"
            },
            "feature_importance": feature_importance,
            "shap_values": shap_values,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@app.post("/model/reload")
def reload_models():
    """Manually reload models from disk"""
    global clf_model, reg_model, scaler, feature_columns, metadata, bitcoin_data
    
    try:
        models_loaded = load_models()
        data_loaded = load_data()
        
        return {
            "status": "success",
            "models_loaded": models_loaded,
            "data_loaded": data_loaded,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
