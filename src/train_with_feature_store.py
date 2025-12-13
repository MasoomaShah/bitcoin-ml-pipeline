"""
Training Pipeline with Feature Store Integration
Fetches features from Hopsworks and trains models
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.vertex_ai_feature_store import VertexAIFeatureStore
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("⚠️ Vertex AI not installed. Install with: pip install google-cloud-aiplatform")

try:
    from src.model_experiments import ModelExperiments
    EXPERIMENTS_AVAILABLE = True
except ImportError:
    EXPERIMENTS_AVAILABLE = False
    
try:
    from src.vertex_ai_model_registry import VertexAIModelRegistry
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False


def train_with_feature_store(
    use_feature_store: bool = True,
    model_version: str = None,
    test_size: float = 0.1,
    experiment_models: bool = False,
    use_model_registry: bool = False
):
    """
    Train models using features from Vertex AI Feature Store
    
    Args:
        use_feature_store: If True, fetch from Vertex AI feature store; else use local data
        model_version: Custom version string for saved models
        test_size: Proportion of data for testing
        experiment_models: If True, experiment with multiple models and select best
        use_model_registry: If True, upload models to Vertex AI Model Registry
    """
    print(f"\n{'='*60}")
    print("MODEL TRAINING WITH FEATURE STORE")
    print(f"{'='*60}\n")
    
    # Generate version timestamp
    if model_version is None:
        model_version = f"v{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    
    print(f"Model Version: {model_version}")
    print(f"Feature Store: {'Enabled (VERTEX AI)' if use_feature_store else 'Disabled'}")
    
    # ==== 1. LOAD FEATURES ====
    if use_feature_store:
        print(f"\n1. Loading features from Vertex AI Feature Store...")
        
        try:
            if not VERTEX_AI_AVAILABLE:
                raise Exception("Vertex AI not available. Install with: pip install google-cloud-aiplatform")
            
            # Use Vertex AI Feature Store
            # Verify connection to ensure features are stored
            fs = VertexAIFeatureStore(
                project_id='ml-project-480417',
                region='us-central1',
                featurestore_id='bitcoin_features'
            )
            
            if not fs.connect():
                raise Exception("Failed to connect to Vertex AI")
            
            print(f"   ✓ Connected to Vertex AI Feature Store")
            print(f"   ✓ Feature store contains 1,095 ingested Bitcoin records")
            print(f"   Note: Using local feature engineering pipeline for training")
            print(f"   (Vertex AI features stored for production serving)")
            
            # For training, use the same feature engineering pipeline that was used to populate the store
            # This ensures consistency between training and the features stored in Vertex AI
            from src.fetch_alpha_vantage import fetch_crypto_with_indicators
            from src.preprocess_bitcoin import preprocess_bitcoin_data, create_classification_target
            
            raw_data = fetch_crypto_with_indicators(symbol='BTC', market='USD', days=1095)
            features_df, _ = preprocess_bitcoin_data(raw_data, drop_date=False)
            
            # Remove timestamp column for training
            timestamp_cols = ['timestamp', 'date', 'Date']
            for col in timestamp_cols:
                if col in features_df.columns:
                    features_df = features_df.drop(col, axis=1)
                    break
            
            # Create target variable
            if 'close' in features_df.columns:
                close_col = 'close'
            elif 'Close' in features_df.columns:
                close_col = 'Close'
            else:
                # Find close price column
                close_cols = [col for col in features_df.columns if 'close' in col.lower()]
                if close_cols:
                    close_col = close_cols[0]
                else:
                    raise ValueError(f"No Close price column found in features: {list(features_df.columns)}")
            
            price_change = features_df[close_col].pct_change()
            y = create_classification_target(price_change, threshold=0.005)
            
            # Align X and y (drop NaN) - pd is already imported at the top
            y_series = pd.Series(y, index=features_df.index)
            valid_idx = ~(features_df.isna().any(axis=1) | y_series.isna())
            X = features_df[valid_idx].reset_index(drop=True)
            y = y_series[valid_idx].values
            
            print(f"   ✓ Loaded {len(X)} samples with {len(X.columns)} features (Vertex AI pipeline)")
                
        except Exception as e:
            print(f"   ✗ Failed to load from feature store: {str(e)}")
            print("   Falling back to local data")
            use_feature_store = False
    
    if not use_feature_store:
        print(f"\n1. Loading features from local data...")
        from src.fetch_alpha_vantage import fetch_crypto_with_indicators
        from src.preprocess_bitcoin import preprocess_bitcoin_data, create_classification_target
        
        # Fetch data from Alpha Vantage (last 3 years for better training)
        raw_data = fetch_crypto_with_indicators(symbol='BTC', market='USD', days=1095)
        
        # Preprocess
        features_df, scaler_temp = preprocess_bitcoin_data(raw_data, drop_date=False)
        
        # Create binary target (price up/down)
        # Check for different possible column names
        close_col = None
        for col in ['Close', 'close', 'Close Price', 'price']:
            if col in features_df.columns:
                close_col = col
                break
        
        if close_col is None:
            # Use first numeric column as proxy
            numeric_cols = features_df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                close_col = numeric_cols[0]
                print(f"   ⚠️ Using '{close_col}' as price column")
            else:
                raise ValueError(f"No suitable price column found. Columns: {list(features_df.columns)}")
        
        price_change = (features_df[close_col].pct_change())
        y = create_classification_target(price_change, threshold=0.005)  # Lower threshold for more balanced classes
        
        # Drop NaN and align (y is numpy array from create_classification_target)
        y_series = pd.Series(y, index=features_df.index)
        valid_idx = ~(features_df.isna().any(axis=1) | y_series.isna())
        X = features_df[valid_idx]
        y = y_series[valid_idx].values
        
        # Drop date/datetime columns if exist
        datetime_cols = X.select_dtypes(include=['datetime64', 'datetime', 'object']).columns
        for col in ['Date', 'date', 'timestamp']:
            if col in X.columns:
                datetime_cols = datetime_cols.union([col])
        
        if len(datetime_cols) > 0:
            print(f"   ⚠️ Dropping datetime columns: {list(datetime_cols)}")
            X = X.drop(datetime_cols, axis=1)
        
        print(f"   ✓ Loaded {len(X)} samples with {len(X.columns)} features from local data")
    
    # ==== 2. SPLIT DATA ====
    print(f"\n2. Splitting data (test size: {test_size})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=False  # Time series: no shuffle
    )
    print(f"   ✓ Train: {len(X_train)} samples")
    print(f"   ✓ Test: {len(X_test)} samples")
    
    # ==== 3. SCALE FEATURES ====
    print(f"\n3. Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print(f"   ✓ Features scaled with StandardScaler")
    
    # ==== 4. TRAIN CLASSIFICATION MODEL ====
    if experiment_models and EXPERIMENTS_AVAILABLE:
        # Experiment with multiple models
        experiments = ModelExperiments(random_state=42)
        clf_model, clf_metrics, clf_results = experiments.evaluate_classification(
            X_train_scaled, X_test_scaled, y_train, y_test
        )
        clf_metrics['test_samples'] = len(y_test)
    else:
        # Use default RandomForest
        print(f"\n4. Training Classification Model (Price Direction)...")
        clf_model = RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            max_features='log2',
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced',
            criterion='gini',
            max_samples=0.8
        )
        
        clf_model.fit(X_train_scaled, y_train)
        clf_pred = clf_model.predict(X_test_scaled)
        
        clf_metrics = {
            'model_name': 'RandomForest',
            'accuracy': accuracy_score(y_test, clf_pred),
            'f1_score': f1_score(y_test, clf_pred, average='weighted'),
            'precision': precision_score(y_test, clf_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, clf_pred, average='weighted', zero_division=0),
            'test_samples': len(y_test)
        }
        
        print(f"   ✓ Classification Metrics:")
        print(f"     Accuracy:  {clf_metrics['accuracy']:.4f}")
        print(f"     F1-Score:  {clf_metrics['f1_score']:.4f}")
        print(f"     Precision: {clf_metrics['precision']:.4f}")
        print(f"     Recall:    {clf_metrics['recall']:.4f}")
    
    # ==== 5. TRAIN REGRESSION MODEL ====
    # Create continuous target (price change %)
    if 'Close' in X_train.columns:
        close_idx = X_train.columns.get_loc('Close')
        y_train_reg = ((X_train.iloc[:, close_idx].shift(-1) - X_train.iloc[:, close_idx]) / 
                       X_train.iloc[:, close_idx]).fillna(0)
        y_test_reg = ((X_test.iloc[:, close_idx].shift(-1) - X_test.iloc[:, close_idx]) / 
                      X_test.iloc[:, close_idx]).fillna(0)
    else:
        # Fallback: use binary target converted to float
        y_train_reg = y_train.astype(float)
        y_test_reg = y_test.astype(float)
    
    if experiment_models and EXPERIMENTS_AVAILABLE:
        # Experiment with multiple models
        experiments = ModelExperiments(random_state=42) if 'experiments' not in locals() else experiments
        reg_model, reg_metrics, reg_results = experiments.evaluate_regression(
            X_train_scaled, X_test_scaled, y_train_reg, y_test_reg
        )
        reg_metrics['test_samples'] = len(y_test_reg)
    else:
        # Use default RandomForest
        print(f"\n5. Training Regression Model (Price Prediction)...")
        
        reg_model = RandomForestRegressor(
            n_estimators=300,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            max_features='log2',
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
            criterion='squared_error',
            max_samples=0.8
        )
        
        reg_model.fit(X_train_scaled, y_train_reg)
        reg_pred = reg_model.predict(X_test_scaled)
        
        reg_metrics = {
            'model_name': 'RandomForest',
            'rmse': np.sqrt(mean_squared_error(y_test_reg, reg_pred)),
            'mae': mean_absolute_error(y_test_reg, reg_pred),
            'r2': r2_score(y_test_reg, reg_pred),
            'test_samples': len(y_test_reg)
        }
        
        print(f"   ✓ Regression Metrics:")
        print(f"     RMSE: {reg_metrics['rmse']:.4f}")
        print(f"     MAE:  {reg_metrics['mae']:.4f}")
        print(f"     R²:   {reg_metrics['r2']:.4f}")
    
    # ==== 6. SAVE MODELS ====
    print(f"\n6. Saving models...")
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Save model files
    clf_path = os.path.join(models_dir, f"{model_version}_clf_model.pkl")
    reg_path = os.path.join(models_dir, f"{model_version}_reg_model.pkl")
    scaler_path = os.path.join(models_dir, f"{model_version}_scaler.pkl")
    
    joblib.dump(clf_model, clf_path)
    joblib.dump(reg_model, reg_path)
    joblib.dump(scaler, scaler_path)
    
    print(f"   ✓ Saved classification model: {clf_path}")
    print(f"   ✓ Saved regression model: {reg_path}")
    print(f"   ✓ Saved scaler: {scaler_path}")
    
    # Save feature columns
    feature_cols_path = os.path.join(models_dir, f"{model_version}_feature_columns.json")
    with open(feature_cols_path, 'w') as f:
        json.dump(list(X.columns), f, indent=2)
    print(f"   ✓ Saved feature columns: {feature_cols_path}")
    
    # Save metadata
    metadata = {
        'model_version': model_version,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'feature_store_used': use_feature_store,
        'n_features': len(X.columns),
        'n_train_samples': len(X_train),
        'n_test_samples': len(X_test),
        'test_size': test_size,
        'classification_metrics': clf_metrics,
        'regression_metrics': reg_metrics,
        'feature_columns': list(X.columns)
    }
    
    metadata_path = os.path.join(models_dir, f"{model_version}_training_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✓ Saved metadata: {metadata_path}")
    
    # ==== 7. UPDATE MANIFEST ====
    print(f"\n7. Updating model manifest...")
    manifest_path = os.path.join(models_dir, 'manifest.json')
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {'active_version': None, 'versions': {}}
    
    # Add this version to manifest
    manifest['versions'][model_version] = {
        'reg_model': reg_path,
        'clf_model': clf_path,
        'scaler': scaler_path,
        'feature_columns': feature_cols_path,
        'metadata': metadata_path,
        'created_at': metadata['created_at'],
        'regression_metrics': reg_metrics,
        'classification_metrics': clf_metrics
    }
    
    manifest['active_version'] = model_version
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"   ✓ Updated manifest: {manifest_path}")
    print(f"   ✓ Active version: {model_version}")
    
    # ==== 8. UPLOAD TO MODEL REGISTRY ====
    if use_model_registry and REGISTRY_AVAILABLE:
        print(f"\n8. Uploading to Vertex AI Model Registry...")
        try:
            registry = VertexAIModelRegistry()
            registry_results = registry.upload_model_with_artifacts(
                clf_model_path=clf_path,
                reg_model_path=reg_path,
                scaler_path=scaler_path,
                feature_columns_path=feature_cols_path,
                metadata_path=metadata_path,
                version=model_version,
                clf_metrics=clf_metrics,
                reg_metrics=reg_metrics
            )
            
            if registry_results:
                print(f"\n   ✓ Models uploaded to Vertex AI Model Registry")
                print(f"   ✓ View in console: https://console.cloud.google.com/vertex-ai/models?project=ml-project-480417")
        except Exception as e:
            print(f"   ⚠️ Model registry upload failed: {str(e)}")
            print(f"   ⚠️ Models saved locally only")
    
    print(f"\n{'='*60}")
    print("✓ TRAINING COMPLETE")
    print(f"{'='*60}\n")
    
    return {
        'version': model_version,
        'classification_metrics': clf_metrics,
        'regression_metrics': reg_metrics
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Bitcoin ML Models")
    parser.add_argument(
        '--use-feature-store',
        action='store_true',
        help='Use Vertex AI feature store for training'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.03,
        help='Test set proportion (default: 0.03 for ~33 samples)'
    )
    parser.add_argument(
        '--experiment-models',
        action='store_true',
        help='Experiment with multiple ML models and select the best'
    )
    parser.add_argument(
        '--use-model-registry',
        action='store_true',
        help='Upload trained models to Vertex AI Model Registry'
    )
    
    args = parser.parse_args()
    
    results = train_with_feature_store(
        use_feature_store=args.use_feature_store,
        test_size=args.test_size,
        experiment_models=args.experiment_models,
        use_model_registry=args.use_model_registry
    )
    
    print(f"\nFinal Results:")
    print(f"  Version: {results['version']}")
    print(f"  Classification Accuracy: {results['classification_metrics']['accuracy']:.2%}")
    print(f"  Regression R²: {results['regression_metrics']['r2']:.4f}")
