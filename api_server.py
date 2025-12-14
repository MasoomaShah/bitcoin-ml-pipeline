"""
FastAPI Backend for Bitcoin ML Predictions

Provides REST API endpoints for:
- Model predictions
- Feature data retrieval
- Model metadata
- Historical data
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

# Try to import SHAP (optional)
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("[WARNING] SHAP not installed. Explainability features will be limited.")

# Try to import LIME (optional)
try:
    from lime.lime_tabular import LimeTabularExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    print("[WARNING] LIME not installed. Alternative explainability unavailable.")

# Try to import Prophet (optional)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("[WARNING] Prophet not installed. Time series forecasting unavailable.")

# Try to import TensorFlow for deep learning models (optional)
try:
    from tensorflow import keras
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("⚠️  TensorFlow not installed. Deep learning models unavailable.")

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
    features: List[float] = Field(..., description="Array of 24 feature values in order")
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

class ExplanationResponse(BaseModel):
    feature_importance: Dict[str, float]
    shap_values: Optional[List[float]] = None
    base_value: Optional[float] = None
    prediction: float
    explanation_method: str
    timestamp: str

class ProphetForecastResponse(BaseModel):
    forecast_periods: int
    forecasted_prices: List[float]
    forecasted_dates: List[str]
    lower_bound: List[float]
    upper_bound: List[float]
    current_price: float
    model_type: str
    timestamp: str


# Global variables for caching
clf_model = None
reg_model = None
scaler = None
shap_explainer = None
lime_explainer = None
feature_columns = None
metadata = None
bitcoin_data = None
prophet_model = None
lstm_model = None
gru_model = None


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
            
            df = fetch_crypto_with_indicators('BTC', 'USD')
            if df is not None and not df.empty:
                bitcoin_data, _ = preprocess_bitcoin_data(df, scaler=None, drop_date=False)
                # Clean infinity and NaN values immediately
                for col in bitcoin_data.select_dtypes(include=[np.number]).columns:
                    bitcoin_data[col] = bitcoin_data[col].replace([np.inf, -np.inf], np.nan)
                    bitcoin_data[col] = bitcoin_data[col].fillna(bitcoin_data[col].median())
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
        "version": "2.1.0",
        "description": "ML-powered Bitcoin price predictions with multiple models and input methods",
        "endpoints": {
            "health": "/health - Health check",
            "predict_auto": "/predict - Automatic prediction (GET)",
            "predict_json": "/predict/json - Custom features via JSON (POST)",
            "predict_numeric": "/predict/numeric - Numeric feature array (POST)",
            "predict_file": "/predict/file - Batch predictions from CSV (POST)",
            "forecast_prophet": "/forecast/prophet - Time series forecast with Prophet (GET)",
            "forecast_dl": "/forecast/deep-learning - LSTM/GRU predictions (GET)",
            "model_info": "/model/info - Model metadata",
            "model_features": "/model/features - Feature names and order",
            "historical_data": "/data/historical - Historical Bitcoin data",
            "latest_features": "/data/latest - Latest feature values"
        },
        "docs": "/docs - Interactive API documentation",
        "model_types": {
            "traditional_ml": "RandomForest, GradientBoosting (currently deployed)",
            "prophet": "Statistical time series forecasting (R² = 0.4504 - best for forecasting)",
            "deep_learning": "LSTM, GRU (high training accuracy, complex pattern recognition)"
        },
        "input_formats": {
            "json": "Dictionary of feature names and values",
            "numeric": "Array of 24 feature values in order",
            "file": "CSV file with feature columns"
        }
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
        
        # Try both 'Close' and 'close' column names for compatibility
        if 'Close' in latest_features.columns:
            current_price = float(latest_features['Close'].values[0])
        elif 'close' in latest_features.columns:
            current_price = float(latest_features['close'].values[0])
        else:
            raise ValueError("Neither 'Close' nor 'close' column found in data")
        
        predicted_price = current_price * (1 + price_change_pred)
        
        return PredictionResponse(
            direction='UP' if direction_pred == 1 else 'DOWN',
            direction_confidence=float(max(direction_proba)) * 100,
            price_change_pct=float(price_change_pred) * 100,
            current_price=current_price,
            predicted_price=float(predicted_price),
            price_change_usd=float(predicted_price - current_price),
            timestamp=datetime.now().isoformat(),
            input_method="automatic"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/json", response_model=PredictionResponse)
def predict_from_json(input_data: FeaturesInput):
    """
    Get prediction from custom feature values (JSON input)
    
    Accepts a dictionary of feature names and their values.
    Example: {"RSI": 65.5, "MACD": 0.05, "BB_upper": 45000, ...}
    """
    if clf_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Validate all required features are present
        missing_features = set(feature_columns) - set(input_data.features.keys())
        if missing_features:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required features: {list(missing_features)}"
            )
        
        # Create feature array in correct order
        X = np.array([[input_data.features[col] for col in feature_columns]])
        X_scaled = scaler.transform(X)
        
        # Make predictions
        direction_pred = clf_model.predict(X_scaled)[0]
        direction_proba = clf_model.predict_proba(X_scaled)[0]
        price_change_pred = reg_model.predict(X_scaled)[0]
        
        # Use provided price or estimate from data
        if input_data.current_price:
            current_price = input_data.current_price
        elif 'Close' in input_data.features:
            current_price = input_data.features['Close']
        elif bitcoin_data is not None:
            current_price = float(bitcoin_data.tail(1)['Close'].values[0])
        else:
            raise HTTPException(status_code=400, detail="Current price required")
        
        predicted_price = current_price * (1 + price_change_pred)
        
        return PredictionResponse(
            direction='UP' if direction_pred == 1 else 'DOWN',
            direction_confidence=float(max(direction_proba)) * 100,
            price_change_pct=float(price_change_pred) * 100,
            current_price=current_price,
            predicted_price=float(predicted_price),
            price_change_usd=float(predicted_price - current_price),
            timestamp=datetime.now().isoformat(),
            input_method="json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/numeric", response_model=PredictionResponse)
def predict_from_numeric(input_data: NumericFeaturesInput):
    """
    Get prediction from numeric feature array
    
    Accepts an array of 24 feature values in the correct order.
    Use GET /model/features to see the feature order.
    """
    if clf_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Validate feature count
        if len(input_data.features) != len(feature_columns):
            raise HTTPException(
                status_code=400,
                detail=f"Expected {len(feature_columns)} features, got {len(input_data.features)}"
            )
        
        # Prepare features
        X = np.array([input_data.features])
        X_scaled = scaler.transform(X)
        
        # Make predictions
        direction_pred = clf_model.predict(X_scaled)[0]
        direction_proba = clf_model.predict_proba(X_scaled)[0]
        price_change_pred = reg_model.predict(X_scaled)[0]
        
        # Use provided price or estimate from data
        if input_data.current_price:
            current_price = input_data.current_price
        elif bitcoin_data is not None:
            current_price = float(bitcoin_data.tail(1)['Close'].values[0])
        else:
            raise HTTPException(status_code=400, detail="Current price required")
        
        predicted_price = current_price * (1 + price_change_pred)
        
        return PredictionResponse(
            direction='UP' if direction_pred == 1 else 'DOWN',
            direction_confidence=float(max(direction_proba)) * 100,
            price_change_pct=float(price_change_pred) * 100,
            current_price=current_price,
            predicted_price=float(predicted_price),
            price_change_usd=float(predicted_price - current_price),
            timestamp=datetime.now().isoformat(),
            input_method="numeric_array"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/file", response_model=BatchPredictionResponse)
async def predict_from_file(file: UploadFile = File(...)):
    """
    Get batch predictions from CSV file upload
    
    CSV should contain columns matching the feature names.
    Can include 'Close' column for current price.
    Returns predictions for all rows in the file.
    """
    if clf_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        missing_features = set(feature_columns) - set(df.columns)
        if missing_features:
            raise HTTPException(
                status_code=400,
                detail=f"CSV missing required features: {list(missing_features)}"
            )
        
        # Check if Close column exists for price
        has_close = 'Close' in df.columns or 'close' in df.columns
        close_col = 'Close' if 'Close' in df.columns else 'close' if 'close' in df.columns else None
        
        predictions = []
        
        for idx, row in df.iterrows():
            try:
                # Prepare features
                X = np.array([[row[col] for col in feature_columns]])
                X_scaled = scaler.transform(X)
                
                # Make predictions
                direction_pred = clf_model.predict(X_scaled)[0]
                direction_proba = clf_model.predict_proba(X_scaled)[0]
                price_change_pred = reg_model.predict(X_scaled)[0]
                
                # Get current price
                if close_col:
                    current_price = float(row[close_col])
                elif bitcoin_data is not None:
                    current_price = float(bitcoin_data.tail(1)['Close'].values[0])
                else:
                    current_price = 0.0
                
                predicted_price = current_price * (1 + price_change_pred)
                
                predictions.append(PredictionResponse(
                    direction='UP' if direction_pred == 1 else 'DOWN',
                    direction_confidence=float(max(direction_proba)) * 100,
                    price_change_pct=float(price_change_pred) * 100,
                    current_price=current_price,
                    predicted_price=float(predicted_price),
                    price_change_usd=float(predicted_price - current_price),
                    timestamp=datetime.now().isoformat(),
                    input_method="csv_file"
                ))
            except Exception as e:
                # Skip rows with errors but continue processing
                continue
        
        return BatchPredictionResponse(
            predictions=predictions,
            total_records=len(predictions),
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")


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


@app.post("/explain", response_model=ExplanationResponse)
def explain_prediction(input_data: Union[FeaturesInput, NumericFeaturesInput]):
    """
    Get SHAP-based explanation for a prediction
    
    Provides feature importance and SHAP values explaining why the model
    made a particular prediction. Helps understand which features contributed
    most to the prediction.
    """
    if clf_model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Prepare features based on input type
        if isinstance(input_data, FeaturesInput):
            missing_features = set(feature_columns) - set(input_data.features.keys())
            if missing_features:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required features: {list(missing_features)}"
                )
            X = np.array([[input_data.features[col] for col in feature_columns]])
        else:  # NumericFeaturesInput
            if len(input_data.features) != len(feature_columns):
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected {len(feature_columns)} features, got {len(input_data.features)}"
                )
            X = np.array([input_data.features])
        
        X_scaled = scaler.transform(X)
        
        # Get prediction
        direction_pred = clf_model.predict(X_scaled)[0]
        direction_proba = clf_model.predict_proba(X_scaled)[0]
        
        # Calculate feature importance and SHAP values
        feature_importance = {}
        shap_values_list = None
        base_value = None
        
        if SHAP_AVAILABLE:
            try:
                # Create SHAP explainer if not already created
                global shap_explainer
                if shap_explainer is None:
                    # Use a sample of training data as background
                    if bitcoin_data is not None and len(bitcoin_data) > 100:
                        background = bitcoin_data.tail(100)[feature_columns].values
                        background_scaled = scaler.transform(background)
                        shap_explainer = shap.TreeExplainer(clf_model, background_scaled)
                    else:
                        shap_explainer = shap.TreeExplainer(clf_model)
                
                # Calculate SHAP values
                shap_values = shap_explainer.shap_values(X_scaled)
                
                # For binary classification, use values for positive class
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    shap_vals = shap_values[1][0]
                else:
                    shap_vals = shap_values[0]
                
                # Create feature importance dictionary
                for i, feature_name in enumerate(feature_columns):
                    feature_importance[feature_name] = float(abs(shap_vals[i]))
                
                shap_values_list = [float(v) for v in shap_vals]
                base_value = float(shap_explainer.expected_value[1] if isinstance(shap_explainer.expected_value, list) else shap_explainer.expected_value)
                explanation_method = "shap"
                
            except Exception as e:
                print(f"SHAP calculation error: {e}")
                # Fallback to model feature importance
                if hasattr(clf_model, 'feature_importances_'):
                    importances = clf_model.feature_importances_
                    for i, feature_name in enumerate(feature_columns):
                        feature_importance[feature_name] = float(importances[i])
                    explanation_method = "model_feature_importance"
                else:
                    # Use absolute coefficient values
                    for i, feature_name in enumerate(feature_columns):
                        feature_importance[feature_name] = float(abs(X_scaled[0][i]))
                    explanation_method = "scaled_feature_values"
        else:
            # SHAP not available, use model feature importance
            if hasattr(clf_model, 'feature_importances_'):
                importances = clf_model.feature_importances_
                for i, feature_name in enumerate(feature_columns):
                    feature_importance[feature_name] = float(importances[i])
                explanation_method = "model_feature_importance"
            else:
                # Fallback to scaled feature values
                for i, feature_name in enumerate(feature_columns):
                    feature_importance[feature_name] = float(abs(X_scaled[0][i]))
                explanation_method = "scaled_feature_values"
        
        # Sort by importance
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        return ExplanationResponse(
            feature_importance=feature_importance,
            shap_values=shap_values_list,
            base_value=base_value,
            prediction=float(max(direction_proba)),
            explanation_method=explanation_method,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@app.post("/explain/lime", response_model=ExplanationResponse)
def explain_prediction_lime(input_data: Union[FeaturesInput, NumericFeaturesInput]):
    """
    Get LIME-based explanation for a prediction
    
    LIME (Local Interpretable Model-agnostic Explanations) explains predictions
    by fitting a simple interpretable model (like linear regression) locally around
    the prediction point. Unlike SHAP which uses game theory, LIME perturbs the
    input data and observes how predictions change.
    
    **What LIME does:**
    - Creates synthetic data points near your input
    - Gets predictions for these synthetic samples
    - Fits a simple model to approximate the complex model locally
    - Shows which features matter most for THIS specific prediction
    
    **When to use LIME vs SHAP:**
    - LIME: Faster, model-agnostic, good for individual predictions
    - SHAP: More accurate, theoretically grounded, but slower
    """
    if not LIME_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="LIME not installed. Use /explain endpoint for SHAP-based explanations."
        )
    
    if clf_model is None or scaler is None or bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Models or data not loaded")
    
    try:
        # Prepare features
        if isinstance(input_data, FeaturesInput):
            missing_features = set(feature_columns) - set(input_data.features.keys())
            if missing_features:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required features: {list(missing_features)}"
                )
            X = np.array([[input_data.features[col] for col in feature_columns]])
        else:
            if len(input_data.features) != len(feature_columns):
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected {len(feature_columns)} features, got {len(input_data.features)}"
                )
            X = np.array([input_data.features])
        
        X_scaled = scaler.transform(X)
        
        # Get prediction
        direction_pred = clf_model.predict(X_scaled)[0]
        direction_proba = clf_model.predict_proba(X_scaled)[0]
        
        # Create LIME explainer if not already created
        global lime_explainer
        if lime_explainer is None:
            # Use recent data as training data
            training_data = bitcoin_data.tail(500)[feature_columns].values
            training_data_scaled = scaler.transform(training_data)
            
            lime_explainer = LimeTabularExplainer(
                training_data_scaled,
                feature_names=feature_columns,
                class_names=['Down', 'Up'],
                mode='classification',
                discretize_continuous=True
            )
        
        # Get LIME explanation
        exp = lime_explainer.explain_instance(
            X_scaled[0],
            clf_model.predict_proba,
            num_features=len(feature_columns),
            top_labels=1
        )
        
        # Extract feature importance from LIME
        lime_weights = exp.as_list(label=direction_pred)
        feature_importance = {}
        lime_values = []
        
        for feature_desc, weight in lime_weights:
            # Extract feature name from description like "feature_name <= 0.5"
            feature_name = feature_desc.split()[0] if ' ' in feature_desc else feature_desc
            # Find matching column
            for col in feature_columns:
                if col.startswith(feature_name) or feature_name in col:
                    feature_importance[col] = float(abs(weight))
                    lime_values.append(float(weight))
                    break
        
        # Fill in missing features with 0
        for col in feature_columns:
            if col not in feature_importance:
                feature_importance[col] = 0.0
                lime_values.append(0.0)
        
        # Sort by importance
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        return ExplanationResponse(
            feature_importance=feature_importance,
            shap_values=lime_values,  # Using same field but with LIME values
            base_value=float(exp.score),  # LIME's prediction score
            prediction=float(max(direction_proba)),
            explanation_method="lime",
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LIME explanation error: {str(e)}")


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


@app.get("/forecast/prophet", response_model=ProphetForecastResponse)
def forecast_with_prophet(
    periods: int = Query(7, ge=1, le=365, description="Number of days to forecast (1-365)")
):
    """
    Generate time series forecast using Prophet model
    
    Prophet provides statistical forecasting with seasonality and trend analysis.
    This is the best performing model for price forecasting (R² = 0.4504).
    
    Args:
        periods: Number of days to forecast into the future
    
    Returns:
        Forecast with predicted prices, dates, and confidence intervals
    """
    if not PROPHET_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Prophet not installed. Install with: pip install prophet"
        )
    
    if bitcoin_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        # Prepare data for Prophet
        df = bitcoin_data.copy()
        
        # Check if we have date column
        if 'date' not in df.columns:
            if df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
            else:
                raise ValueError("No date column found in data")
        
        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Get current price
        if 'Close' in df.columns:
            current_price = float(df['Close'].iloc[-1])
            value_col = 'Close'
        elif 'close' in df.columns:
            current_price = float(df['close'].iloc[-1])
            value_col = 'close'
        else:
            raise ValueError("No price column (Close/close) found in data")
        
        # Prepare Prophet format (ds, y columns)
        prophet_df = pd.DataFrame({
            'ds': df['date'],
            'y': df[value_col]
        })
        
        # Remove any NaN values
        prophet_df = prophet_df.dropna()
        
        # Train Prophet model
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0
        )
        
        model.fit(prophet_df)
        
        # Make future dataframe and predict
        future = model.make_future_dataframe(periods=periods, freq='D')
        forecast = model.predict(future)
        
        # Extract forecast for future periods only
        forecast_future = forecast.tail(periods)
        
        return ProphetForecastResponse(
            forecast_periods=periods,
            forecasted_prices=[float(x) for x in forecast_future['yhat'].tolist()],
            forecasted_dates=[x.strftime('%Y-%m-%d') for x in forecast_future['ds'].tolist()],
            lower_bound=[float(x) for x in forecast_future['yhat_lower'].tolist()],
            upper_bound=[float(x) for x in forecast_future['yhat_upper'].tolist()],
            current_price=current_price,
            model_type="Prophet (Statistical Time Series)",
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prophet forecast error: {str(e)}")


@app.get("/forecast/deep-learning")
def forecast_with_deep_learning(
    model_type: str = Query("lstm", regex="^(lstm|gru)$", description="Model type: lstm or gru")
):
    """
    Generate prediction using deep learning models (LSTM or GRU)
    
    Deep learning models show high training accuracy and can capture complex patterns.
    Note: Requires TensorFlow and trained .h5 model files.
    
    Args:
        model_type: Type of RNN model to use (lstm or gru)
    
    Returns:
        Direction prediction with confidence from deep learning model
    """
    if not KERAS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="TensorFlow not installed. Install with: pip install tensorflow"
        )
    
    if bitcoin_data is None or feature_columns is None or scaler is None:
        raise HTTPException(status_code=503, detail="Models or data not loaded")
    
    try:
        # Find the latest deep learning model
        models_dir = Path("models")
        model_files = list(models_dir.glob(f"*_{model_type}_classification.h5"))
        
        if not model_files:
            raise HTTPException(
                status_code=404,
                detail=f"No {model_type.upper()} model found. Train with: python src/train_all_models.py"
            )
        
        # Load the latest model
        latest_model_file = max(model_files, key=lambda x: x.stat().st_mtime)
        dl_model = keras.models.load_model(latest_model_file)
        
        # Prepare sequence data (last 30 days)
        sequence_length = 30
        latest_features = bitcoin_data[feature_columns].tail(sequence_length).values
        
        if len(latest_features) < sequence_length:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data. Need {sequence_length} samples, got {len(latest_features)}"
            )
        
        # Scale features
        X_scaled = scaler.transform(latest_features)
        X_seq = X_scaled.reshape(1, sequence_length, len(feature_columns))
        
        # Make prediction
        prediction = dl_model.predict(X_seq, verbose=0)[0][0]
        direction = "UP" if prediction > 0.5 else "DOWN"
        confidence = float(prediction if prediction > 0.5 else 1 - prediction) * 100
        
        # Get current price
        if 'Close' in bitcoin_data.columns:
            current_price = float(bitcoin_data['Close'].iloc[-1])
        elif 'close' in bitcoin_data.columns:
            current_price = float(bitcoin_data['close'].iloc[-1])
        else:
            current_price = 0.0
        
        return {
            "model_type": model_type.upper(),
            "model_file": latest_model_file.name,
            "direction": direction,
            "confidence": confidence,
            "raw_prediction": float(prediction),
            "current_price": current_price,
            "sequence_length": sequence_length,
            "note": f"{model_type.upper()} models achieve high training accuracy and can capture complex temporal patterns",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deep learning prediction error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
