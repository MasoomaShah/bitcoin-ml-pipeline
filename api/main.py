"""
FastAPI server for Bitcoin price prediction.
Supports both regression (predict price) and classification (predict high/low growth).
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import joblib
import sys
import os
import json
import io
from typing import List, Dict
import traceback
from datetime import datetime

# Ensure the repository root is on sys.path so `import src` resolves
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.preprocess_timeseries import preprocess_timeseries_data

app = FastAPI(title="Bitcoin Price Predictor API", version="1.0")

# Load models and artifacts from project root
model_dir = project_root
reg_model_path = os.path.join(model_dir, "reg_model.pkl")
clf_model_path = os.path.join(model_dir, "clf_model.pkl")
scaler_path = os.path.join(model_dir, "scaler.pkl")
features_path = os.path.join(model_dir, "feature_columns.json")
metadata_path = os.path.join(model_dir, "training_metadata.json")
models_dir = os.path.join(model_dir, "models")
manifest_path = os.path.join(models_dir, "manifest.json")

print(f"\n{'='*60}")
print(f"Model directory: {model_dir}")
print(f"{'='*60}")

# Load models
def load_artifacts_from_manifest(version: str = None):
    """Load artifacts given a version (if manifest exists). Returns dict of paths or None."""
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, 'r', encoding='utf-8') as mf:
            manifest = json.load(mf)
    except Exception:
        return None

    if version is None:
        version = manifest.get('active_version')

    version_info = manifest.get('versions', {}).get(version)
    if not version_info:
        return None

    # resolve relative paths against project root
    resolved = {}
    for k, rel in version_info.items():
        if k == 'created_at' or k.endswith('_metrics'):
            resolved[k] = rel
            continue
        resolved[k] = os.path.join(model_dir, rel)
    return resolved


def read_manifest():
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, 'r', encoding='utf-8') as mf:
            return json.load(mf)
    except Exception:
        return None


def write_manifest(manifest: dict):
    try:
        os.makedirs(models_dir, exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as mf:
            json.dump(manifest, mf, indent=2)
        return True
    except Exception:
        return False


artifacts = load_artifacts_from_manifest()
reg_model = None
clf_model = None
if artifacts is not None:
    try:
        reg_model = joblib.load(artifacts['reg_model'])
        print(f"✓ Regression model loaded from manifest: {artifacts['reg_model']}")
    except Exception as e:
        print(f"✗ Error loading regression model from manifest: {e}")
        reg_model = None

    try:
        clf_model = joblib.load(artifacts['clf_model'])
        print(f"✓ Classification model loaded from manifest: {artifacts['clf_model']}")
    except Exception as e:
        print(f"✗ Error loading classification model from manifest: {e}")
        clf_model = None
else:
    # fall back to legacy single-file artifacts at project root
    try:
        reg_model = joblib.load(reg_model_path)
        print(f"✓ Regression model loaded from {reg_model_path}")
    except Exception as e:
        print(f"✗ Error loading regression model: {e}")
        reg_model = None

    try:
        clf_model = joblib.load(clf_model_path)
        print(f"✓ Classification model loaded from {clf_model_path}")
    except Exception as e:
        print(f"✗ Error loading classification model: {e}")
        clf_model = None

# Load preprocessing artifacts
try:
    if artifacts is not None and os.path.exists(artifacts.get('scaler', '')):
        scaler = joblib.load(artifacts['scaler'])
        print(f"✓ Scaler loaded from manifest: {artifacts['scaler']}")
    else:
        scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        print(f"✓ Scaler loaded: {scaler is not None}")
except Exception as e:
    print(f"✗ Error loading scaler: {e}")
    scaler = None

try:
    if artifacts is not None and os.path.exists(artifacts.get('feature_columns', '')):
        with open(artifacts['feature_columns'], 'r', encoding='utf-8') as f:
            feature_columns = json.load(f)
    elif os.path.exists(features_path):
        with open(features_path, 'r', encoding='utf-8') as f:
            feature_columns = json.load(f)
    else:
        feature_columns = None
    print(f"✓ Feature columns loaded: {len(feature_columns) if feature_columns else 0} features")
except Exception as e:
    print(f"✗ Error loading feature_columns: {e}")
    feature_columns = None

# Load metadata
try:
    if artifacts is not None and os.path.exists(artifacts.get('metadata', '')):
        with open(artifacts['metadata'], 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    elif os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = None
    print(f"✓ Training metadata loaded")
except Exception as e:
    print(f"✗ Error loading metadata: {e}")
    metadata = None

print(f"{'='*60}\n")


# Define input models
class BitcoinFeatures(BaseModel):
    """Input model for Bitcoin technical indicators."""
    price: float
    market_cap: float
    volume: float
    price_smooth: float
    price_ma3: float
    price_ma7: float
    price_ma14: float
    price_ma30: float
    price_ema7: float
    price_ema14: float
    momentum_3d: float
    momentum_7d: float
    momentum_14d: float
    roc_3d: float
    roc_7d: float
    price_volatility_3d: float
    price_volatility_7d: float
    price_volatility_14d: float
    volume_ma3: float
    volume_ma7: float
    volume_change: float
    price_to_ma7: float
    price_to_ma30: float
    bb_middle: float
    bb_std: float
    bb_upper: float
    bb_lower: float
    bb_position: float
    rsi_14: float
    market_cap_change: float
    volume_to_marketcap: float
    SMA_7: float
    SMA_14: float
    SMA_30: float
    EMA_7: float
    EMA_14: float
    momentum_7: float
    momentum_14: float
    momentum_30: float
    volatility_7: float
    volatility_14: float
    RSI: float
    MACD: float
    MACD_signal: float
    BB_middle: float
    BB_upper: float
    BB_lower: float
    BB_width: float
    volume_SMA_7: float


class BatchPredictionInput(BaseModel):
    """Input for batch predictions with historical data."""
    date: str = None  # Optional date string for reference
    indicators: BitcoinFeatures


# Endpoints
@app.get("/")
def home():
    """Health check endpoint."""
    return {
        "message": "Bitcoin Price Predictor API is running!",
        "domain": "Cryptocurrency - Bitcoin Price Prediction",
        "models": "Regression (Price prediction) + Classification (High/Low growth)"
    }


@app.get("/model-info")
def get_model_info():
    """Return information about the trained models and features."""
    if metadata is None:
        raise HTTPException(status_code=500, detail="Model metadata not available")
    
    return metadata


@app.get("/feature-columns")
def get_feature_columns():
    """Return the expected feature columns for predictions."""
    if feature_columns is None:
        raise HTTPException(status_code=500, detail="Feature columns not available")
    
    return {"feature_columns": feature_columns}


@app.post("/predict/regression")
def predict_regression(indicators: BitcoinFeatures):
    """
    Predict Bitcoin price change (normalized) using technical indicators.
    Returns the predicted price change value.
    """
    try:
        if reg_model is None or scaler is None or feature_columns is None:
            raise HTTPException(status_code=500, detail="Models or artifacts not loaded")
        
        # Create DataFrame with provided indicators - use feature_columns to ensure correct order
        data = {}
        for col in feature_columns:
            if hasattr(indicators, col):
                data[col] = [getattr(indicators, col)]
            else:
                raise HTTPException(status_code=400, detail=f"Missing feature: {col}")
        
        df = pd.DataFrame(data)
        
        # Add dummy target columns that scaler was fitted with
        df['future_price_change'] = 0.0
        df['market_class'] = 1
        
        # Get scaler column order
        scaler_columns = list(scaler.feature_names_in_)
        
        # Scale all columns
        X_all = scaler.transform(df[scaler_columns].values)
        
        # Extract only the feature columns for model prediction
        feature_indices = [scaler_columns.index(f) for f in feature_columns]
        X = X_all[:, feature_indices]
        
        # Predict
        prediction = reg_model.predict(X)[0]
        
        return {
            "prediction": float(prediction),
            "interpretation": f"Predicted normalized price change: {float(prediction):.4f}",
            "features_used": feature_columns
        }
    
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in predict_regression:\n{tb}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/classification")
def predict_classification(indicators: BitcoinFeatures):
    """
    Classify Bitcoin price movement as Bullish (≥median) or Bearish (<median).
    Returns classification and probability.
    """
    try:
        if clf_model is None or scaler is None or feature_columns is None:
            raise HTTPException(status_code=500, detail="Models or artifacts not loaded")
        
        # Create DataFrame with provided indicators - use feature_columns to ensure correct order
        data = {}
        for col in feature_columns:
            if hasattr(indicators, col):
                data[col] = [getattr(indicators, col)]
            else:
                raise HTTPException(status_code=400, detail=f"Missing feature: {col}")
        
        df = pd.DataFrame(data)
        
        # Add dummy target columns that scaler was fitted with
        df['future_price_change'] = 0.0
        df['market_class'] = 1
        
        # Get scaler column order
        scaler_columns = list(scaler.feature_names_in_)
        
        # Scale all columns
        X_all = scaler.transform(df[scaler_columns].values)
        
        # Extract only the feature columns for model prediction
        feature_indices = [scaler_columns.index(f) for f in feature_columns]
        X = X_all[:, feature_indices]
        
        # Predict
        prediction = clf_model.predict(X)[0]
        probabilities = clf_model.predict_proba(X)[0]
        
        class_label = "Bullish" if prediction == 1 else "Bearish"
        
        return {
            "classification": class_label,
            "class_value": int(prediction),
            "probability_bearish": float(probabilities[0]),
            "probability_bullish": float(probabilities[1]),
            "features_used": feature_columns
        }
    
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in predict_classification:\n{tb}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/both")
def predict_both(indicators: BitcoinFeatures):
    """
    Simultaneously return both regression and classification predictions for Bitcoin price.
    """
    try:
        if reg_model is None or clf_model is None or scaler is None or feature_columns is None:
            raise HTTPException(status_code=500, detail="Models or artifacts not loaded")
        
        # Create DataFrame with provided indicators - use feature_columns to ensure correct order
        data = {}
        for col in feature_columns:
            if hasattr(indicators, col):
                data[col] = [getattr(indicators, col)]
            else:
                raise HTTPException(status_code=400, detail=f"Missing feature: {col}")
        
        df = pd.DataFrame(data)
        
        # Add dummy target columns that scaler was fitted with
        df['future_price_change'] = 0.0
        df['market_class'] = 1
        
        # Get scaler column order
        scaler_columns = list(scaler.feature_names_in_)
        
        # Scale all columns
        X_all = scaler.transform(df[scaler_columns].values)
        
        # Extract only the feature columns for model prediction
        feature_indices = [scaler_columns.index(f) for f in feature_columns]
        X = X_all[:, feature_indices]
        
        # Predict regression
        regression_pred = float(reg_model.predict(X)[0])
        
        # Predict classification
        classification_pred = int(clf_model.predict(X)[0])
        class_probabilities = [float(p) for p in clf_model.predict_proba(X)[0]]
        
        class_label = "Bullish" if classification_pred == 1 else "Bearish"
        
        return {
            "regression": {
                "prediction": regression_pred,
                "interpretation": f"Predicted normalized price change: {regression_pred:.4f}"
            },
            "classification": {
                "prediction": class_label,
                "class_value": classification_pred,
                "probability_bearish": class_probabilities[0],
                "probability_bullish": class_probabilities[1]
            },
            "features_used": feature_columns
        }
    
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in predict_both:\n{tb}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    """
    Batch prediction from CSV file upload.
    CSV must have all 49 Bitcoin technical indicator columns.
    Optional: date column for reference
    Returns predictions for each row.
    """
    try:
        if reg_model is None or clf_model is None or scaler is None or feature_columns is None:
            raise HTTPException(status_code=500, detail="Models or artifacts not loaded")
        
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error reading CSV in predict_batch:\n{tb}")
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")
    
    # Validate columns
    missing_cols = [c for c in feature_columns if c not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing_cols}. Expected: {feature_columns}"
        )
    
    results = []
    
    for idx, row in df.iterrows():
        try:
            # Extract indicators for required features
            indicators_dict = {col: row[col] for col in feature_columns}
            
            # Create DataFrame
            df_row = pd.DataFrame([indicators_dict])
            
            # Add dummy target columns that scaler was fitted with
            df_row['future_price_change'] = 0.0
            df_row['market_class'] = 1
            
            # Get scaler column order
            scaler_columns = list(scaler.feature_names_in_)
            
            # Scale all columns
            X_all = scaler.transform(df_row[scaler_columns].values)
            
            # Extract only the feature columns for model prediction
            feature_indices = [scaler_columns.index(f) for f in feature_columns]
            X = X_all[:, feature_indices]
            
            # Predict
            reg_pred = float(reg_model.predict(X)[0])
            clf_pred = int(clf_model.predict(X)[0])
            clf_probs = [float(p) for p in clf_model.predict_proba(X)[0]]
            
            class_label = "Bullish" if clf_pred == 1 else "Bearish"
            
            results.append({
                "row_index": idx,
                "date": str(row.get('date', 'N/A')) if 'date' in df.columns else None,
                "regression_prediction": reg_pred,
                "classification_prediction": class_label,
                "classification_value": clf_pred,
                "confidence_bearish": clf_probs[0],
                "confidence_bullish": clf_probs[1]
            })
        
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error predicting row {idx}:\n{tb}")
            results.append({
                "row_index": idx,
                "error": str(e),
                "trace": tb
            })
    
    return {
        "total_rows": len(results),
        "successful_predictions": sum(1 for r in results if "error" not in r),
        "failed_predictions": sum(1 for r in results if "error" in r),
        "results": results
    }


@app.post("/reload-models")
def reload_models(token: str = None, version: str = None):
    """
    Reload models and preprocessing artifacts at runtime.
    Provide a token if you set MODEL_RELOAD_TOKEN env var.
    """
    expected = os.getenv('MODEL_RELOAD_TOKEN')
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid reload token")
    
    global reg_model, clf_model, scaler, feature_columns, metadata
    
    try:
        global reg_model, clf_model, scaler, feature_columns, metadata

        # If a version is provided, try loading from manifest
        artifacts_local = None
        if version:
            artifacts_local = load_artifacts_from_manifest(version)

        # If artifacts_local found, load from those paths, else fall back to project root
        if artifacts_local is not None:
            reg_model = joblib.load(artifacts_local['reg_model'])
            clf_model = joblib.load(artifacts_local['clf_model'])
            scaler = joblib.load(artifacts_local['scaler']) if os.path.exists(artifacts_local.get('scaler','')) else None

            with open(artifacts_local['feature_columns'], 'r', encoding='utf-8') as f:
                feature_columns = json.load(f)

            with open(artifacts_local['metadata'], 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            loaded_from = f"manifest version {version or 'active'}"

        else:
            # legacy fallback
            reg_model = joblib.load(reg_model_path)
            clf_model = joblib.load(clf_model_path)
            scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

            if os.path.exists(features_path):
                with open(features_path, 'r', encoding='utf-8') as f:
                    feature_columns = json.load(f)

            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            loaded_from = 'project root artifacts'

        return {
            "status": "reloaded",
            "timestamp": datetime.now().isoformat(),
            "models_loaded": True,
            "loaded_from": loaded_from
        }

    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error reloading models:\n{tb}")
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")




# Registry endpoints
@app.get("/models")
def list_models():
    """List available model versions from the manifest."""
    manifest = read_manifest()
    if manifest is None:
        return {"models": [], "message": "No manifest found"}
    return {"active_version": manifest.get('active_version'), "versions": list(manifest.get('versions', {}).keys())}


@app.get("/models/{version}")
def get_model_version(version: str):
    manifest = read_manifest()
    if manifest is None:
        raise HTTPException(status_code=404, detail="Manifest not found")
    info = manifest.get('versions', {}).get(version)
    if not info:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")
    return {"version": version, "info": info}


@app.post("/models/activate")
def activate_model_version(version: str, token: str = None, 
                           reload: bool = True):
    """Set a version as active in the manifest. Optionally reload models.
    Provide `MODEL_RELOAD_TOKEN` env var or None if not set.
    """
    expected = os.getenv('MODEL_RELOAD_TOKEN')
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid reload token")

    manifest = read_manifest()
    if manifest is None:
        raise HTTPException(status_code=404, detail="Manifest not found")

    if version not in manifest.get('versions', {}):
        raise HTTPException(status_code=404, detail=f"Version {version} not found in manifest")

    manifest['active_version'] = version
    success = write_manifest(manifest)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write manifest")

    result = {"status": "activated", "active_version": version}
    if reload:
        # reload the artifacts for the new active version
        res = reload_models(token=token, version=version)
        result['reload'] = res

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
