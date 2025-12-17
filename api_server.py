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
    """Load Bitcoin data"""
    global bitcoin_data
    
    try:
        # Try loading from raw data first (most recent daily run)
        if Path("data/raw/bitcoin_timeseries.csv").exists():
            bitcoin_data = pd.read_csv("data/raw/bitcoin_timeseries.csv")
            return True
        
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
        
        print("Warning: No data files found in data/raw, data/processed, or data/features")
        return False
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return False


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
def predict(price: float = Query(..., description="Current Bitcoin price")):
    """
    Simple prediction based on price only
    
    This endpoint makes a quick prediction using just the current price.
    For more accurate predictions, use /predict/json with all 49 features.
    """
    if clf_model is None or reg_model is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Create minimal feature vector (use price for all features as placeholder)
        # This is a simplified version - normally you'd use real features
        X = np.full((1, len(feature_columns)), price)
        X_scaled = scale_features(X, feature_columns)
        
        # Get predictions
        clf_pred = clf_model.predict(X_scaled)[0]
        clf_proba = clf_model.predict_proba(X_scaled)[0]
        reg_pred = reg_model.predict(X_scaled)[0]
        
        # Use regression prediction to determine direction (more reliable)
        # Classification can sometimes be off when using placeholder features
        price_change_pct = float(reg_pred)
        direction = "UP" if price_change_pct > 0 else "DOWN"
        confidence = float(max(clf_proba)) * 100
        predicted_price = price * (1 + price_change_pct / 100)
        price_change_usd = predicted_price - price
        
        return PredictionResponse(
            direction=direction,
            direction_confidence=confidence,
            price_change_pct=price_change_pct,
            current_price=price,
            predicted_price=predicted_price,
            price_change_usd=price_change_usd,
            timestamp=datetime.now().isoformat(),
            input_method="price_only"
        )
    
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
