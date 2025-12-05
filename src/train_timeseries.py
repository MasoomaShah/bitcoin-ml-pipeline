"""
Training script for time-series GDP growth prediction using World Bank data.
Implements temporal train/test split (no data leakage) and trains regression + classification models.
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

# Import time-series preprocessing
from preprocess_timeseries import (
    preprocess_timeseries_data, 
    get_temporal_train_test_split, 
    create_classification_target
)


def train_regression_model(X_train, y_train, X_test=None, y_test=None):
    """
    Train a RandomForest regression model for GDP growth prediction.
    
    Args:
        X_train, y_train: Training data and target
        X_test, y_test: Optional test data for evaluation
    
    Returns:
        dict: Model and metrics
    """
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = {}
    y_pred_train = model.predict(X_train)
    metrics['train_rmse'] = np.sqrt(mean_squared_error(y_train, y_pred_train))
    metrics['train_mae'] = mean_absolute_error(y_train, y_pred_train)
    metrics['train_r2'] = r2_score(y_train, y_pred_train)
    
    if X_test is not None and y_test is not None:
        y_pred_test = model.predict(X_test)
        metrics['test_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred_test))
        metrics['test_mae'] = mean_absolute_error(y_test, y_pred_test)
        metrics['test_r2'] = r2_score(y_test, y_pred_test)
    
    return model, metrics


def train_classification_model(X_train, y_train_reg, X_test=None, y_test_reg=None, threshold=0.05):
    """
    Train a RandomForest classification model for high/low GDP growth classification.
    
    Args:
        X_train, y_train_reg: Training data and regression target (GDP growth)
        X_test, y_test_reg: Optional test data
        threshold (float): Threshold for 'high growth' classification
    
    Returns:
        dict: Model and metrics
    """
    
    # Convert regression target to binary classification
    y_train = create_classification_target(y_train_reg, threshold=threshold)
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = {}
    y_pred_train = model.predict(X_train)
    metrics['train_accuracy'] = accuracy_score(y_train, y_pred_train)
    metrics['train_precision'] = precision_score(y_train, y_pred_train, zero_division=0)
    metrics['train_recall'] = recall_score(y_train, y_pred_train, zero_division=0)
    
    if X_test is not None and y_test_reg is not None:
        y_test = create_classification_target(y_test_reg, threshold=threshold)
        y_pred_test = model.predict(X_test)
        metrics['test_accuracy'] = accuracy_score(y_test, y_pred_test)
        metrics['test_precision'] = precision_score(y_test, y_pred_test, zero_division=0)
        metrics['test_recall'] = recall_score(y_test, y_pred_test, zero_division=0)
    
    return model, metrics


def train_and_save(data_path, output_dir=None):
    """
    Full training pipeline: load data, preprocess, train, save artifacts.
    
    Args:
        data_path (str): Path to World Bank CSV data
        output_dir (str): Directory to save models and artifacts (default: project root)
    
    Returns:
        dict: Training metrics and metadata
    """
    
    if output_dir is None:
        output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load data
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows")
    
    # Preprocess: fit scaler on all data (since we have limited time-series data)
    print("Preprocessing data...")
    df_processed, scaler, feature_cols = preprocess_timeseries_data(df, scaler=None, drop_date=False)
    
    # Temporal train/test split
    print("Splitting data temporally (last 2 years for test)...")
    X_train, X_test, y_train, y_test, train_dates, test_dates = get_temporal_train_test_split(
        df_processed, test_years=2
    )
    
    print(f"Train set: {len(X_train)} samples ({train_dates.min()} to {train_dates.max()})")
    print(f"Test set: {len(X_test)} samples ({test_dates.min()} to {test_dates.max()})")
    
    # Train regression model
    print("Training regression model...")
    reg_model, reg_metrics = train_regression_model(X_train, y_train, X_test, y_test)
    print(f"Regression metrics: {reg_metrics}")
    
    # Train classification model
    print("Training classification model...")
    clf_model, clf_metrics = train_classification_model(X_train, y_train, X_test, y_test, threshold=0.05)
    print(f"Classification metrics: {clf_metrics}")
    
    # Save models (versioned registry)
    print(f"Saving models and artifacts (versioned) to {output_dir}...")
    models_dir = os.path.join(output_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    # version tag
    version = datetime.utcnow().strftime("v%Y%m%dT%H%M%SZ")

    reg_model_path = os.path.join(models_dir, f"{version}_reg_model.pkl")
    clf_model_path = os.path.join(models_dir, f"{version}_clf_model.pkl")
    scaler_path = os.path.join(models_dir, f"{version}_scaler.pkl")
    features_path = os.path.join(models_dir, f"{version}_feature_columns.json")
    metadata_path_versioned = os.path.join(models_dir, f"{version}_training_metadata.json")

    joblib.dump(reg_model, reg_model_path)
    print(f"✓ Regression model saved to {reg_model_path}")

    joblib.dump(clf_model, clf_model_path)
    print(f"✓ Classification model saved to {clf_model_path}")

    joblib.dump(scaler, scaler_path)
    print(f"✓ Scaler saved to {scaler_path}")

    with open(features_path, 'w', encoding='utf-8') as f:
        json.dump(feature_cols, f, indent=2)
    print(f"✓ Feature columns saved to {features_path}")

    # Save metadata (versioned)
    metadata = {
        "domain": "World Bank - Economic Indicators",
        "target": "GDP_growth (regression)",
        "binary_target": "high_growth (classification, threshold=0.05)",
        "features": feature_cols,
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test),
        "train_date_range": f"{train_dates.min()} to {train_dates.max()}",
        "test_date_range": f"{test_dates.min()} to {test_dates.max()}",
        "regression_metrics": {k: float(v) for k, v in reg_metrics.items()},
        "classification_metrics": {k: float(v) for k, v in clf_metrics.items()},
        "version": version,
        "created_at": datetime.utcnow().isoformat() + 'Z'
    }
    
    with open(metadata_path_versioned, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Versioned metadata saved to {metadata_path_versioned}")

    # Update manifest
    manifest_path = os.path.join(models_dir, "manifest.json")
    manifest = {"active_version": version, "versions": {}}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as mf:
                manifest = json.load(mf)
        except Exception:
            manifest = {"active_version": version, "versions": {}}

    manifest['active_version'] = version
    manifest['versions'][version] = {
        "reg_model": os.path.relpath(reg_model_path, output_dir),
        "clf_model": os.path.relpath(clf_model_path, output_dir),
        "scaler": os.path.relpath(scaler_path, output_dir),
        "feature_columns": os.path.relpath(features_path, output_dir),
        "metadata": os.path.relpath(metadata_path_versioned, output_dir),
        "created_at": metadata['created_at'],
        "regression_metrics": metadata['regression_metrics'],
        "classification_metrics": metadata['classification_metrics']
    }

    with open(manifest_path, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2)
    print(f"✓ Manifest updated at {manifest_path}")

    # Also save non-versioned copies for backward compatibility (optional)
    root_reg = os.path.join(output_dir, "reg_model.pkl")
    root_clf = os.path.join(output_dir, "clf_model.pkl")
    root_scaler = os.path.join(output_dir, "scaler.pkl")
    root_features = os.path.join(output_dir, "feature_columns.json")
    root_metadata = os.path.join(output_dir, "training_metadata.json")

    joblib.dump(reg_model, root_reg)
    joblib.dump(clf_model, root_clf)
    joblib.dump(scaler, root_scaler)
    with open(root_features, 'w', encoding='utf-8') as f:
        json.dump(feature_cols, f, indent=2)
    with open(root_metadata, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Backward-compatible artifacts saved to project root")

    return metadata


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Adjust data path as needed
    data_path = "data/raw/world_bank_gdp.csv"
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        print("Please run untitled1.py first to fetch World Bank data.")
        sys.exit(1)
    
    metadata = train_and_save(data_path)
    print("\nTraining complete!")
    print(json.dumps(metadata, indent=2))
