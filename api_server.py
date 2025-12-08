"""
FastAPI Backend for Bitcoin ML Predictions

Provides REST API endpoints for:
- Model predictions
- Feature data retrieval
- Model metadata
- Historical data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime
import sys
import os

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

# Response models
class PredictionResponse(BaseModel):
    direction: str
    direction_confidence: float
    price_change_pct: float
    current_price: float
    predicted_price: float
    price_change_usd: float
    timestamp: str

class ModelInfo(BaseModel):
    version: str
    timestamp: str
    classification_accuracy: float
    regression_rmse: float
    regression_r2: float
    classification_f1: float
    features_count: int

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    data_available: bool
    timestamp: str


# Global variables for caching
clf_model = None
reg_model = None
scaler = None
feature_columns = None
metadata = None
bitcoin_data = None


def load_models():
    """Load trained models and metadata"""
    global clf_model, reg_model, scaler, feature_columns, metadata
    
    try:
        models_dir = Path("models")
        manifest_path = models_dir / "manifest.json"
        
        if not manifest_path.exists():
            return False
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Handle both old and new manifest formats
        if 'models' in manifest:
            # Old format
            latest = manifest['models'][0]
            version = latest['version']
        elif 'active_version' in manifest:
            # New format
            version = manifest['active_version']
        else:
            return False
        
        clf_model = joblib.load(models_dir / f"{version}_clf_model.pkl")
        reg_model = joblib.load(models_dir / f"{version}_reg_model.pkl")
        scaler = joblib.load(models_dir / f"{version}_scaler.pkl")
        
        with open(models_dir / f"{version}_feature_columns.json", 'r') as f:
            feature_columns = json.load(f)
        
        with open(models_dir / f"{version}_training_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        return True
    
    except Exception as e:
        print(f"Error loading models: {e}")
        return False


def load_data():
    """Load Bitcoin data"""
    global bitcoin_data
    
    try:
        # Try loading from processed data
        data_files = list(Path("data/processed").glob("*.csv"))
        if data_files:
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            bitcoin_data = pd.read_csv(latest_file)
            return True
        
        # Try loading from features directory
        feature_files = list(Path("data/features").glob("*.csv"))
        if feature_files:
            latest_file = max(feature_files, key=lambda x: x.stat().st_mtime)
            bitcoin_data = pd.read_csv(latest_file)
            return True
        
        # Try fetching fresh data if no files exist
        print("  No data files found, fetching fresh data...")
        try:
            from src.fetch_alpha_vantage import fetch_crypto_with_indicators
            from src.preprocess_bitcoin import preprocess_bitcoin_data
            
            df = fetch_crypto_with_indicators('BTC', 'USD', api_key=os.getenv('ALPHA_VANTAGE_API_KEY', 'demo'))
            if df is not None and not df.empty:
                bitcoin_data = preprocess_bitcoin_data(df)
                return True
        except:
            pass
        
        return False
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize models and data on startup"""
    print("Loading models and data...")
    models_loaded = load_models()
    data_loaded = load_data()
    
    if models_loaded:
        print("✓ Models loaded successfully")
    else:
        print("✗ Failed to load models")
    
    if data_loaded:
        print("✓ Data loaded successfully")
    else:
        print("✗ Failed to load data")


@app.get("/", response_model=Dict)
def root():
    """Root endpoint with API information"""
    return {
        "message": "Bitcoin ML Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "model_info": "/model/info",
            "historical_data": "/data/historical",
            "latest_features": "/data/latest"
        },
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if clf_model and bitcoin_data is not None else "unhealthy",
        model_loaded=clf_model is not None,
        data_available=bitcoin_data is not None,
        timestamp=datetime.now().isoformat()
    )


@app.get("/predict", response_model=PredictionResponse)
def predict():
    """Get prediction for next period"""
    if clf_model is None or bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Models or data not loaded")
    
    try:
        # Get latest features
        latest_features = bitcoin_data.tail(1).copy()
        
        # Prepare features
        X = latest_features[feature_columns].values.reshape(1, -1)
        X_scaled = scaler.transform(X)
        
        # Make predictions
        direction_pred = clf_model.predict(X_scaled)[0]
        direction_proba = clf_model.predict_proba(X_scaled)[0]
        price_change_pred = reg_model.predict(X_scaled)[0]
        
        current_price = float(latest_features['close'].values[0])
        predicted_price = current_price * (1 + price_change_pred)
        
        return PredictionResponse(
            direction='UP' if direction_pred == 1 else 'DOWN',
            direction_confidence=float(max(direction_proba)) * 100,
            price_change_pct=float(price_change_pred) * 100,
            current_price=current_price,
            predicted_price=float(predicted_price),
            price_change_usd=float(predicted_price - current_price),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


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
        df = bitcoin_data.tail(limit)
        return {
            "count": len(df),
            "data": df.to_dict(orient='records')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data retrieval error: {str(e)}")


@app.get("/data/latest")
def get_latest_features():
    """Get latest feature values"""
    if bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        latest = bitcoin_data.tail(1).to_dict(orient='records')[0]
        return {
            "timestamp": latest.get('timestamp', datetime.now().isoformat()),
            "features": latest
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature retrieval error: {str(e)}")


@app.post("/model/reload")
def reload_models():
    """Reload models and data (useful after training)"""
    try:
        models_loaded = load_models()
        data_loaded = load_data()
        
        return {
            "status": "success" if models_loaded and data_loaded else "partial",
            "models_loaded": models_loaded,
            "data_loaded": data_loaded,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
