"""
Prefect ML Pipeline for World Bank GDP Growth Prediction

This flow orchestrates:
- Data ingestion from CSV
- Feature engineering (time-series preprocessing)
- Model training (RandomForest regression + classification)
- Model evaluation
- Model versioning and registry update
- Success/failure notifications (Discord/Slack/Email)
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Optional
import traceback
import requests

try:
    from prefect import flow, task
    from prefect.task_runners import ConcurrentTaskRunner
except ImportError:
    # Fallback for Prefect 3.x
    from prefect import flow, task
    ConcurrentTaskRunner = None
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score, classification_report
try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.preprocess_bitcoin import (
    preprocess_bitcoin_data,
    get_temporal_train_test_split,
    create_classification_target
)
from src.fetch_bitcoin_data import fetch_bitcoin_data, calculate_price_changes, add_technical_indicators


# ============================================================================
# NOTIFICATION TASKS
# ============================================================================

@task(name="send_notification", retries=2, retry_delay_seconds=5)
def send_notification(
    message: str,
    status: str = "info",
    webhook_url: Optional[str] = None,
    notification_type: str = "discord"
) -> bool:
    """
    Send notification via Discord, Slack, or Email.
    
    Set environment variables:
    - DISCORD_WEBHOOK_URL for Discord
    - SLACK_WEBHOOK_URL for Slack
    - EMAIL_WEBHOOK_URL for email service (e.g., Zapier, Make.com)
    """
    if webhook_url is None:
        webhook_url = os.getenv(f"{notification_type.upper()}_WEBHOOK_URL")
    
    if not webhook_url:
        print(f"⚠️  No {notification_type} webhook configured. Skipping notification.")
        return False
    
    try:
        # Emoji based on status
        emoji_map = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        emoji = emoji_map.get(status, "ℹ️")
        
        if notification_type.lower() == "discord":
            payload = {
                "content": f"{emoji} **ML Pipeline Notification**\n\n{message}",
                "username": "Prefect ML Bot"
            }
        elif notification_type.lower() == "slack":
            payload = {
                "text": f"{emoji} *ML Pipeline Notification*\n\n{message}"
            }
        else:  # Generic webhook (email services)
            payload = {
                "subject": f"ML Pipeline: {status.upper()}",
                "message": message,
                "status": status
            }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✓ Notification sent via {notification_type}")
        return True
    
    except Exception as e:
        print(f"✗ Failed to send {notification_type} notification: {e}")
        return False


# ============================================================================
# DATA INGESTION
# ============================================================================

@task(name="ingest_data", retries=3, retry_delay_seconds=10)
def ingest_data(data_path: str) -> pd.DataFrame:
    """
    Ingest Bitcoin time-series data from CSV.
    
    Args:
        data_path: Path to the CSV file
        
    Returns:
        Raw DataFrame
        
    Raises:
        FileNotFoundError: If data file doesn't exist
        ValueError: If required columns are missing
    """
    print(f"\n{'='*60}")
    print("STEP 1: DATA INGESTION")
    print(f"{'='*60}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"✓ Loaded data: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Validate required columns for Bitcoin data
    required_cols = ['date', 'price']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    print(f"✓ Data validation passed")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Features: {', '.join(df.columns.tolist())}")
    
    return df


# ============================================================================
# FEATURE ENGINEERING
# ============================================================================

@task(name="engineer_features", retries=2, retry_delay_seconds=5)
def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, object, list]:
    """
    Apply time-series feature engineering for Bitcoin data.
    
    - Add technical indicators
    - Handle missing values
    - Scale features
    - Create classification target (bull/bear market)
    
    Returns:
        Tuple of (processed_df, scaler, feature_columns)
    """
    print(f"\n{'='*60}")
    print("STEP 2: FEATURE ENGINEERING")
    print(f"{'='*60}")
    
    df_copy = df.copy()
    
    # Add price changes if not already present (predict 1 day ahead for better accuracy)
    if 'future_price_change' not in df_copy.columns:
        df_copy = calculate_price_changes(df_copy, prediction_horizon=1)
    
    # Add technical indicators if not already present
    if 'price_ma7' not in df_copy.columns:
        df_copy = add_technical_indicators(df_copy)
    
    # Create classification target (Bull/Bear market for FUTURE: 1 day ahead)
    # Use future_price_change (not current price_change) for classification
    if 'future_price_change' in df_copy.columns:
        df_copy['market_class'] = create_classification_target(
            df_copy['future_price_change'],
            threshold=0.005  # 0.5% return threshold for 1-day prediction
        )
    
    # Apply preprocessing
    df_processed, scaler = preprocess_bitcoin_data(
        df_copy,
        scaler=None,
        drop_date=False
    )
    
    # Feature columns (exclude date, all target columns)
    feature_cols = [col for col in df_processed.columns 
                   if col not in ['date', 'price_change', 'future_price_change', 'market_class']]
    
    print(f"✓ Feature engineering complete")
    print(f"  Processed shape: {df_processed.shape}")
    print(f"  Feature columns: {feature_cols}")
    print(f"  Scaler fitted: {type(scaler).__name__}")
    
    return df_processed, scaler, feature_cols


# ============================================================================
# TRAIN/TEST SPLIT
# ============================================================================

@task(name="split_data")
def split_data(
    df: pd.DataFrame,
    feature_columns: list,
    test_days: int = 60
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Perform temporal train/test split for Bitcoin data.
    
    Args:
        df: DataFrame with Bitcoin data
        feature_columns: List of feature column names
        test_days: Number of days to use for test set
    
    Returns:
        X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test
    """
    print(f"\n{'='*60}")
    print("STEP 3: TRAIN/TEST SPLIT")
    print(f"{'='*60}")
    
    # Temporal split - returns 6 values: X_train, X_test, y_train, y_test, train_dates, test_dates
    X_train, X_test, y_reg_train, y_reg_test, train_dates, test_dates = get_temporal_train_test_split(
        df, test_days=test_days
    )
    
    # Get classification targets from original dataframe
    df_sorted = df.sort_values('date').reset_index(drop=True)
    split_index = len(df_sorted) - test_days
    
    train_df = df_sorted.iloc[:split_index]
    test_df = df_sorted.iloc[split_index:]
    
    # Extract classification targets and convert to integer type
    y_clf_train = train_df['market_class'].astype(int).values
    y_clf_test = test_df['market_class'].astype(int).values
    
    print(f"✓ Data split complete")
    print(f"  Train size: {len(X_train)} samples")
    print(f"  Test size: {len(X_test)} samples")
    print(f"  Train date range: {pd.to_datetime(train_dates.min())} to {pd.to_datetime(train_dates.max())}")
    print(f"  Test date range: {pd.to_datetime(test_dates.min())} to {pd.to_datetime(test_dates.max())}")
    print(f"  Classification targets - Train unique: {np.unique(y_clf_train)}, Test unique: {np.unique(y_clf_test)}")
    
    return X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test


# ============================================================================
# MODEL TRAINING
# ============================================================================

@task(name="train_regression_model", retries=2, retry_delay_seconds=10)
def train_regression_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    hyperparameters: Optional[Dict] = None
) -> RandomForestRegressor:
    """Train RandomForest regression model."""
    print(f"\n{'='*60}")
    print("STEP 4A: TRAIN REGRESSION MODEL")
    print(f"{'='*60}")
    
    if hyperparameters is None:
        hyperparameters = {
            'n_estimators': 300,
            'max_depth': 15,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1
        }
    
    print(f"  Hyperparameters: {hyperparameters}")
    
    model = RandomForestRegressor(**hyperparameters)
    model.fit(X_train, y_train)
    
    print(f"✓ Regression model trained")
    print(f"  Features used: {X_train.shape[1]}")
    print(f"  Training samples: {len(X_train)}")
    
    return model


@task(name="train_classification_model", retries=2, retry_delay_seconds=10)
def train_classification_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    hyperparameters: Optional[Dict] = None
) -> RandomForestClassifier:
    """Train RandomForest classification model."""
    print(f"\n{'='*60}")
    print("STEP 4B: TRAIN CLASSIFICATION MODEL")
    print(f"{'='*60}")
    
    if hyperparameters is None:
        if XGBOOST_AVAILABLE:
            # XGBoost performs better on time-series
            hyperparameters = {
                'n_estimators': 500,
                'max_depth': 8,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 1,
                'gamma': 0.1,
                'reg_alpha': 0.1,
                'reg_lambda': 1,
                'random_state': 42,
                'n_jobs': -1,
                'eval_metric': 'logloss'
            }
            model = XGBClassifier(**hyperparameters)
        else:
            # Fallback to GradientBoosting
            hyperparameters = {
                'n_estimators': 300,
                'max_depth': 8,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'random_state': 42
            }
            model = GradientBoostingClassifier(**hyperparameters)
    else:
        model = RandomForestClassifier(**hyperparameters)
    
    print(f"  Model: {type(model).__name__}")
    print(f"  Hyperparameters: {hyperparameters}")
    
    model.fit(X_train, y_train)
    
    print(f"✓ Classification model trained")
    print(f"  Features used: {X_train.shape[1]}")
    print(f"  Training samples: {len(X_train)}")
    
    return model


# ============================================================================
# MODEL EVALUATION
# ============================================================================

@task(name="evaluate_regression_model")
def evaluate_regression_model(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict:
    """Evaluate regression model and return metrics."""
    print(f"\n{'='*60}")
    print("STEP 5A: EVALUATE REGRESSION MODEL")
    print(f"{'='*60}")
    
    y_pred = model.predict(X_test)
    
    # Calculate RMSE using sqrt(MSE) for compatibility
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    
    metrics = {
        'rmse': float(rmse),
        'r2': float(r2_score(y_test, y_pred)),
        'test_samples': len(y_test)
    }
    
    print(f"✓ Regression evaluation complete")
    print(f"  RMSE: {metrics['rmse']:.4f}")
    print(f"  R²: {metrics['r2']:.4f}")
    
    return metrics


@task(name="evaluate_classification_model")
def evaluate_classification_model(
    model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict:
    """Evaluate classification model and return metrics."""
    print(f"\n{'='*60}")
    print("STEP 5B: EVALUATE CLASSIFICATION MODEL")
    print(f"{'='*60}")
    
    y_pred = model.predict(X_test)
    
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'f1_score': float(f1_score(y_test, y_pred, average='weighted')),
        'test_samples': len(y_test)
    }
    
    print(f"✓ Classification evaluation complete")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")
    
    # Print classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low Growth', 'High Growth']))
    
    return metrics


# ============================================================================
# MODEL VERSIONING & SAVING
# ============================================================================

@task(name="save_and_version_models", retries=2, retry_delay_seconds=5)
def save_and_version_models(
    reg_model: RandomForestRegressor,
    clf_model: RandomForestClassifier,
    scaler: object,
    feature_columns: list,
    reg_metrics: Dict,
    clf_metrics: Dict,
    output_dir: str = "models"
) -> Dict:
    """
    Save models with versioning and update manifest.
    
    Returns:
        Dictionary with version info and paths
    """
    print(f"\n{'='*60}")
    print("STEP 6: SAVE AND VERSION MODELS")
    print(f"{'='*60}")
    
    # Create version timestamp
    version = datetime.utcnow().strftime("v%Y%m%dT%H%M%SZ")
    
    # Ensure output directory exists
    output_path = Path(project_root) / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define file paths
    reg_model_path = output_path / f"{version}_reg_model.pkl"
    clf_model_path = output_path / f"{version}_clf_model.pkl"
    scaler_path = output_path / f"{version}_scaler.pkl"
    features_path = output_path / f"{version}_feature_columns.json"
    metadata_path = output_path / f"{version}_training_metadata.json"
    manifest_path = output_path / "manifest.json"
    
    # Save models
    joblib.dump(reg_model, reg_model_path)
    joblib.dump(clf_model, clf_model_path)
    joblib.dump(scaler, scaler_path)
    
    # Save feature columns
    with open(features_path, 'w') as f:
        json.dump(feature_columns, f, indent=2)
    
    # Save metadata
    metadata = {
        'version': version,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'regression_metrics': reg_metrics,
        'classification_metrics': clf_metrics,
        'feature_count': len(feature_columns),
        'model_type': 'RandomForest'
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Update manifest
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {'versions': {}}
    
    manifest['active_version'] = version
    manifest['versions'][version] = {
        'reg_model': f"{output_dir}/{version}_reg_model.pkl",
        'clf_model': f"{output_dir}/{version}_clf_model.pkl",
        'scaler': f"{output_dir}/{version}_scaler.pkl",
        'feature_columns': f"{output_dir}/{version}_feature_columns.json",
        'metadata': f"{output_dir}/{version}_training_metadata.json",
        'created_at': metadata['created_at'],
        'regression_metrics': reg_metrics,
        'classification_metrics': clf_metrics
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✓ Models saved and versioned")
    print(f"  Version: {version}")
    print(f"  Directory: {output_path}")
    print(f"  Manifest updated: {manifest_path}")
    
    return {
        'version': version,
        'paths': {
            'reg_model': str(reg_model_path),
            'clf_model': str(clf_model_path),
            'scaler': str(scaler_path),
            'features': str(features_path),
            'metadata': str(metadata_path),
            'manifest': str(manifest_path)
        },
        'metadata': metadata
    }


# ============================================================================
# MAIN FLOW
# ============================================================================
 
@flow(
    name="ml-training-pipeline",
    description="End-to-end ML pipeline for GDP growth prediction",
    retries=1,
    retry_delay_seconds=30
)
def ml_training_pipeline(
    data_path: str = "data/raw/bitcoin_timeseries.csv",
    test_days: int = 30,
    output_dir: str = "models",
    notification_type: str = "discord",  # discord, slack, or email
    reg_hyperparams: Optional[Dict] = None,
    clf_hyperparams: Optional[Dict] = None,
    fetch_live_data: bool = False
) -> Dict:
    """
    Complete ML training pipeline with orchestration for Bitcoin price prediction.
    
    Args:
        data_path: Path to Bitcoin CSV data (if fetch_live_data=False)
        test_days: Number of days to use for test set
        output_dir: Directory to save models
        notification_type: Type of notification (discord/slack/email)
        reg_hyperparams: Hyperparameters for regression model
        clf_hyperparams: Hyperparameters for classification model
        fetch_live_data: If True, fetch fresh data from CoinGecko API instead of using CSV
        
    Returns:
        Dictionary with version info and metrics
    """
    pipeline_start = datetime.utcnow()
    
    try:
        # Resolve data path
        if not os.path.isabs(data_path):
            data_path = str(project_root / data_path)
        
        print(f"\n{'='*70}")
        print(f"  ML TRAINING PIPELINE STARTED")
        print(f"  Time: {pipeline_start.isoformat()}")
        print(f"{'='*70}\n")
        
        # Step 1: Data Ingestion
        if fetch_live_data:
            print("Fetching live Bitcoin data from CoinGecko API...")
            df_raw = fetch_bitcoin_data(days=365)
            df_raw = calculate_price_changes(df_raw, prediction_horizon=1)
            df_raw = add_technical_indicators(df_raw)
        else:
            df_raw = ingest_data(data_path)
        
        # Step 2: Feature Engineering
        df_processed, scaler, feature_cols = engineer_features(df_raw)
        
        # Step 3: Train/Test Split
        X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = split_data(
            df_processed,
            feature_cols,
            test_days=test_days
        )
        
        # Step 4: Model Training (concurrent)
        reg_model = train_regression_model(X_train, y_reg_train, reg_hyperparams)
        clf_model = train_classification_model(X_train, y_clf_train, clf_hyperparams)
        
        # Step 5: Model Evaluation (concurrent)
        reg_metrics = evaluate_regression_model(reg_model, X_test, y_reg_test)
        clf_metrics = evaluate_classification_model(clf_model, X_test, y_clf_test)
        
        # Step 6: Save and Version Models
        version_info = save_and_version_models(
            reg_model,
            clf_model,
            scaler,
            feature_cols,
            reg_metrics,
            clf_metrics,
            output_dir=output_dir
        )
        
        # Calculate pipeline duration
        pipeline_end = datetime.utcnow()
        duration = (pipeline_end - pipeline_start).total_seconds()
        
        # Success notification
        success_message = f"""
**ML Pipeline Completed Successfully! 🎉**

**Version:** {version_info['version']}
**Duration:** {duration:.2f}s

**Regression Metrics:**
- RMSE: {reg_metrics['rmse']:.4f}
- R²: {reg_metrics['r2']:.4f}

**Classification Metrics:**
- Accuracy: {clf_metrics['accuracy']:.4f}
- F1 Score: {clf_metrics['f1_score']:.4f}

**Models saved to:** `{output_dir}/`
"""
        
        send_notification(success_message, status="success", notification_type=notification_type)
        
        print(f"\n{'='*70}")
        print(f"  ✅ PIPELINE COMPLETED SUCCESSFULLY")
        print(f"  Duration: {duration:.2f}s")
        print(f"{'='*70}\n")
        
        return {
            'status': 'success',
            'version': version_info['version'],
            'duration_seconds': duration,
            'regression_metrics': reg_metrics,
            'classification_metrics': clf_metrics,
            'paths': version_info['paths']
        }
    
    except Exception as e:
        # Calculate pipeline duration
        pipeline_end = datetime.utcnow()
        duration = (pipeline_end - pipeline_start).total_seconds()
        
        # Error notification
        error_trace = traceback.format_exc()
        error_message = f"""
**ML Pipeline Failed! ❌**

**Error:** {str(e)}
**Duration:** {duration:.2f}s
**Time:** {pipeline_end.isoformat()}

**Traceback:**
```
{error_trace[-1000:]}  # Last 1000 chars
```
"""
        
        send_notification(error_message, status="error", notification_type=notification_type)
        
        print(f"\n{'='*70}")
        print(f"  ❌ PIPELINE FAILED")
        print(f"  Error: {str(e)}")
        print(f"  Duration: {duration:.2f}s")
        print(f"{'='*70}\n")
        print(error_trace)
        
        raise  # Re-raise to let Prefect handle it


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the pipeline locally
    result = ml_training_pipeline(
        data_path="data/raw/world_bank_gdp.csv",
        notification_type="discord"  # Change to slack or email as needed
    )
    
    print("\n" + "="*70)
    print("FINAL RESULT:")
    print(json.dumps(result, indent=2))
    print("="*70)
