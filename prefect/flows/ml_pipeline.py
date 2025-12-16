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

# Deep Learning imports
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False

# Prophet import
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

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
    X_test: pd.DataFrame,
    y_test: pd.Series,
    hyperparameters: Optional[Dict] = None
) -> Tuple:
    """Train multiple regression models and return the best one."""
    print(f"\n{'='*60}")
    print("STEP 4A: TRAIN & SELECT BEST REGRESSION MODEL")
    print(f"{'='*60}")
    
    models_to_test = {}
    results = {}
    
    # Model 1: RandomForest
    print("\n  1. Training RandomForest Regressor...")
    rf_params = {
        'n_estimators': 300,
        'max_depth': 15,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'max_features': 'sqrt',
        'random_state': 42,
        'n_jobs': -1
    }
    rf_model = RandomForestRegressor(**rf_params)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    rf_r2 = r2_score(y_test, rf_pred)
    models_to_test['RandomForest'] = rf_model
    results['RandomForest'] = {'rmse': rf_rmse, 'r2': rf_r2}
    print(f"     ✓ RMSE: {rf_rmse:.4f}, R²: {rf_r2:.4f}")
    
    # Model 2: GradientBoosting
    print("  2. Training GradientBoosting Regressor...")
    gb_params = {
        'n_estimators': 300,
        'max_depth': 8,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'random_state': 42
    }
    gb_model = GradientBoostingRegressor(**gb_params)
    gb_model.fit(X_train, y_train)
    gb_pred = gb_model.predict(X_test)
    gb_rmse = np.sqrt(mean_squared_error(y_test, gb_pred))
    gb_r2 = r2_score(y_test, gb_pred)
    models_to_test['GradientBoosting'] = gb_model
    results['GradientBoosting'] = {'rmse': gb_rmse, 'r2': gb_r2}
    print(f"     ✓ RMSE: {gb_rmse:.4f}, R²: {gb_r2:.4f}")
    
    # Model 3: XGBoost (if available)
    if XGBOOST_AVAILABLE:
        print("  3. Training XGBoost Regressor...")
        xgb_params = {
            'n_estimators': 500,
            'max_depth': 8,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1
        }
        xgb_model = XGBRegressor(**xgb_params)
        xgb_model.fit(X_train, y_train)
        xgb_pred = xgb_model.predict(X_test)
        xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_pred))
        xgb_r2 = r2_score(y_test, xgb_pred)
        models_to_test['XGBoost'] = xgb_model
        results['XGBoost'] = {'rmse': xgb_rmse, 'r2': xgb_r2}
        print(f"     ✓ RMSE: {xgb_rmse:.4f}, R²: {xgb_r2:.4f}")
    
    # Model 4: LSTM (if Keras available)
    if KERAS_AVAILABLE:
        print("  4. Training LSTM Regressor...")
        try:
            from tensorflow.keras.callbacks import EarlyStopping
            
            # Prepare sequences for LSTM (lookback=7 days)
            lookback = 7
            X_train_seq = np.array([X_train.iloc[i:i+lookback].values for i in range(len(X_train)-lookback)])
            y_train_seq = y_train.iloc[lookback:].values
            X_test_seq = np.array([X_test.iloc[i:i+lookback].values for i in range(len(X_test)-lookback)])
            y_test_seq = y_test.iloc[lookback:].values
            
            lstm_model = Sequential([
                LSTM(64, return_sequences=True, input_shape=(lookback, X_train.shape[1])),
                Dropout(0.2),
                LSTM(32),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='linear')
            ])
            lstm_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            lstm_model.fit(X_train_seq, y_train_seq, epochs=50, batch_size=16, 
                          validation_split=0.2, callbacks=[early_stop], verbose=0)
            
            lstm_pred = lstm_model.predict(X_test_seq, verbose=0).flatten()
            lstm_rmse = np.sqrt(mean_squared_error(y_test_seq, lstm_pred))
            lstm_r2 = r2_score(y_test_seq, lstm_pred)
            models_to_test['LSTM'] = lstm_model
            results['LSTM'] = {'rmse': lstm_rmse, 'r2': lstm_r2}
            print(f"     ✓ RMSE: {lstm_rmse:.4f}, R²: {lstm_r2:.4f}")
        except Exception as e:
            print(f"     ✗ LSTM training failed: {e}")
    
    # Model 5: GRU (if Keras available)
    if KERAS_AVAILABLE:
        print("  5. Training GRU Regressor...")
        try:
            from tensorflow.keras.callbacks import EarlyStopping
            
            # Reuse sequences from LSTM
            lookback = 7
            X_train_seq = np.array([X_train.iloc[i:i+lookback].values for i in range(len(X_train)-lookback)])
            y_train_seq = y_train.iloc[lookback:].values
            X_test_seq = np.array([X_test.iloc[i:i+lookback].values for i in range(len(X_test)-lookback)])
            y_test_seq = y_test.iloc[lookback:].values
            
            gru_model = Sequential([
                GRU(64, return_sequences=True, input_shape=(lookback, X_train.shape[1])),
                Dropout(0.2),
                GRU(32),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='linear')
            ])
            gru_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            gru_model.fit(X_train_seq, y_train_seq, epochs=50, batch_size=16, 
                         validation_split=0.2, callbacks=[early_stop], verbose=0)
            
            gru_pred = gru_model.predict(X_test_seq, verbose=0).flatten()
            gru_rmse = np.sqrt(mean_squared_error(y_test_seq, gru_pred))
            gru_r2 = r2_score(y_test_seq, gru_pred)
            models_to_test['GRU'] = gru_model
            results['GRU'] = {'rmse': gru_rmse, 'r2': gru_r2}
            print(f"     ✓ RMSE: {gru_rmse:.4f}, R²: {gru_r2:.4f}")
        except Exception as e:
            print(f"     ✗ GRU training failed: {e}")
    
    # Model 6: Prophet (if available)
    if PROPHET_AVAILABLE:
        print("  6. Training Prophet...")
        try:
            # Prepare data for Prophet
            df_prophet = pd.DataFrame({
                'ds': pd.date_range(end=datetime.now(), periods=len(y_train), freq='D'),
                'y': y_train.values
            })
            
            prophet_model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False, interval_width=0.95)
            prophet_model.fit(df_prophet)
            
            # Forecast for test period
            future = prophet_model.make_future_dataframe(periods=len(y_test))
            forecast = prophet_model.predict(future)
            prophet_pred = forecast['yhat'].tail(len(y_test)).values
            
            prophet_rmse = np.sqrt(mean_squared_error(y_test, prophet_pred))
            prophet_r2 = r2_score(y_test, prophet_pred)
            models_to_test['Prophet'] = prophet_model
            results['Prophet'] = {'rmse': prophet_rmse, 'r2': prophet_r2}
            print(f"     ✓ RMSE: {prophet_rmse:.4f}, R²: {prophet_r2:.4f}")
        except Exception as e:
            print(f"     ✗ Prophet training failed: {e}")
    
    # Select best model (highest R², lower RMSE is secondary criteria)
    print("\n  📊 Model Comparison Results:")
    best_model_name = max(results.keys(), key=lambda x: results[x]['r2'])
    best_model = models_to_test[best_model_name]
    best_metrics = results[best_model_name]
    
    for name, metrics in results.items():
        status = "⭐ BEST" if name == best_model_name else "  "
        print(f"     {status} {name:20} | RMSE: {metrics['rmse']:8.4f} | R²: {metrics['r2']:10.4f}")
    
    print(f"\n  ✓ Selected: {best_model_name} Regressor")
    print(f"    Features used: {X_train.shape[1]}")
    print(f"    Training samples: {len(X_train)}")
    
    return best_model, best_model_name


@task(name="train_classification_model", retries=2, retry_delay_seconds=10)
def train_classification_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    hyperparameters: Optional[Dict] = None
) -> Tuple:
    """Train multiple classification models and return the best one."""
    print(f"\n{'='*60}")
    print("STEP 4B: TRAIN & SELECT BEST CLASSIFICATION MODEL")
    print(f"{'='*60}")
    
    models_to_test = {}
    results = {}
    
    # Model 1: RandomForest
    print("\n  1. Training RandomForest Classifier...")
    rf_params = {
        'n_estimators': 300,
        'max_depth': 12,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42,
        'n_jobs': -1
    }
    rf_clf = RandomForestClassifier(**rf_params)
    rf_clf.fit(X_train, y_train)
    rf_pred = rf_clf.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_f1 = f1_score(y_test, rf_pred, average='weighted')
    models_to_test['RandomForest'] = rf_clf
    results['RandomForest'] = {'accuracy': rf_acc, 'f1': rf_f1}
    print(f"     ✓ Accuracy: {rf_acc:.4f}, F1: {rf_f1:.4f}")
    
    # Model 2: GradientBoosting
    print("  2. Training GradientBoosting Classifier...")
    gb_params = {
        'n_estimators': 300,
        'max_depth': 8,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'random_state': 42
    }
    gb_clf = GradientBoostingClassifier(**gb_params)
    gb_clf.fit(X_train, y_train)
    gb_pred = gb_clf.predict(X_test)
    gb_acc = accuracy_score(y_test, gb_pred)
    gb_f1 = f1_score(y_test, gb_pred, average='weighted')
    models_to_test['GradientBoosting'] = gb_clf
    results['GradientBoosting'] = {'accuracy': gb_acc, 'f1': gb_f1}
    print(f"     ✓ Accuracy: {gb_acc:.4f}, F1: {gb_f1:.4f}")
    
    # Model 3: XGBoost (if available)
    if XGBOOST_AVAILABLE:
        print("  3. Training XGBoost Classifier...")
        xgb_params = {
            'n_estimators': 500,
            'max_depth': 8,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'eval_metric': 'logloss'
        }
        xgb_clf = XGBClassifier(**xgb_params)
        xgb_clf.fit(X_train, y_train)
        xgb_pred = xgb_clf.predict(X_test)
        xgb_acc = accuracy_score(y_test, xgb_pred)
        xgb_f1 = f1_score(y_test, xgb_pred, average='weighted')
        models_to_test['XGBoost'] = xgb_clf
        results['XGBoost'] = {'accuracy': xgb_acc, 'f1': xgb_f1}
        print(f"     ✓ Accuracy: {xgb_acc:.4f}, F1: {xgb_f1:.4f}")
    
    # Model 4: LSTM Classification (if Keras available)
    if KERAS_AVAILABLE:
        print("  4. Training LSTM Classifier...")
        try:
            from tensorflow.keras.callbacks import EarlyStopping
            
            # Prepare sequences for LSTM (lookback=7 days)
            lookback = 7
            X_train_seq = np.array([X_train.iloc[i:i+lookback].values for i in range(len(X_train)-lookback)])
            y_train_seq = y_train.iloc[lookback:].values
            X_test_seq = np.array([X_test.iloc[i:i+lookback].values for i in range(len(X_test)-lookback)])
            y_test_seq = y_test.iloc[lookback:].values
            
            lstm_clf = Sequential([
                LSTM(64, return_sequences=True, input_shape=(lookback, X_train.shape[1])),
                Dropout(0.2),
                LSTM(32),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='sigmoid')
            ])
            lstm_clf.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            lstm_clf.fit(X_train_seq, y_train_seq, epochs=50, batch_size=16, 
                        validation_split=0.2, callbacks=[early_stop], verbose=0)
            
            lstm_pred = (lstm_clf.predict(X_test_seq, verbose=0) > 0.5).astype(int).flatten()
            lstm_acc = accuracy_score(y_test_seq, lstm_pred)
            lstm_f1 = f1_score(y_test_seq, lstm_pred, average='weighted')
            models_to_test['LSTM'] = lstm_clf
            results['LSTM'] = {'accuracy': lstm_acc, 'f1': lstm_f1}
            print(f"     ✓ Accuracy: {lstm_acc:.4f}, F1: {lstm_f1:.4f}")
        except Exception as e:
            print(f"     ✗ LSTM training failed: {e}")
    
    # Model 5: GRU Classification (if Keras available)
    if KERAS_AVAILABLE:
        print("  5. Training GRU Classifier...")
        try:
            from tensorflow.keras.callbacks import EarlyStopping
            
            lookback = 7
            X_train_seq = np.array([X_train.iloc[i:i+lookback].values for i in range(len(X_train)-lookback)])
            y_train_seq = y_train.iloc[lookback:].values
            X_test_seq = np.array([X_test.iloc[i:i+lookback].values for i in range(len(X_test)-lookback)])
            y_test_seq = y_test.iloc[lookback:].values
            
            gru_clf = Sequential([
                GRU(64, return_sequences=True, input_shape=(lookback, X_train.shape[1])),
                Dropout(0.2),
                GRU(32),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='sigmoid')
            ])
            gru_clf.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            gru_clf.fit(X_train_seq, y_train_seq, epochs=50, batch_size=16, 
                       validation_split=0.2, callbacks=[early_stop], verbose=0)
            
            gru_pred = (gru_clf.predict(X_test_seq, verbose=0) > 0.5).astype(int).flatten()
            gru_acc = accuracy_score(y_test_seq, gru_pred)
            gru_f1 = f1_score(y_test_seq, gru_pred, average='weighted')
            models_to_test['GRU'] = gru_clf
            results['GRU'] = {'accuracy': gru_acc, 'f1': gru_f1}
            print(f"     ✓ Accuracy: {gru_acc:.4f}, F1: {gru_f1:.4f}")
        except Exception as e:
            print(f"     ✗ GRU training failed: {e}")
    
    # Select best model (highest accuracy)
    print("\n  📊 Model Comparison Results:")
    best_model_name = max(results.keys(), key=lambda x: results[x]['accuracy'])
    best_model = models_to_test[best_model_name]
    best_metrics = results[best_model_name]
    
    for name, metrics in results.items():
        status = "⭐ BEST" if name == best_model_name else "  "
        print(f"     {status} {name:20} | Accuracy: {metrics['accuracy']:.4f} | F1: {metrics['f1']:.4f}")
    
    print(f"\n  ✓ Selected: {best_model_name} Classifier")
    print(f"    Features used: {X_train.shape[1]}")
    print(f"    Training samples: {len(X_train)}")
    
    return best_model, best_model_name


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
    reg_model: object,
    clf_model: object,
    reg_model_name: str,
    clf_model_name: str,
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
        'regression_model_type': reg_model_name,
        'classification_model_type': clf_model_name,
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


@task(name="upload_models_to_cloud_storage", retries=2, retry_delay_seconds=5)
def upload_models_to_cloud_storage(version_info: Dict) -> bool:
    """
    Upload trained models to Google Cloud Storage for Vertex AI integration.
    
    Models are uploaded to gs://bucket/models/ directory
    so that FastAPI and Streamlit can load them directly from cloud.
    
    Args:
        version_info: Dictionary with version, paths, and metadata
        
    Returns:
        True if successful, False if Cloud Storage unavailable
    """
    try:
        from google.cloud import storage
        
        project_id = os.getenv('GCP_PROJECT_ID', 'ml-project-480417')
        bucket_name = os.getenv('GCP_BUCKET', f"{project_id}-ml-models")
        
        version = version_info['version']
        clf_model_path = version_info['paths']['clf_model']
        reg_model_path = version_info['paths']['reg_model']
        scaler_path = version_info['paths']['scaler']
        features_path = version_info['paths']['features']
        metadata_path = version_info['paths']['metadata']
        
        print(f"\n{'='*60}")
        print("STEP 7A: UPLOAD MODELS TO CLOUD STORAGE")
        print(f"{'='*60}")
        
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        
        # List of files to upload
        files_to_upload = [
            (clf_model_path, f"models/{version}_clf_model.pkl"),
            (reg_model_path, f"models/{version}_reg_model.pkl"),
            (scaler_path, f"models/{version}_scaler.pkl"),
            (features_path, f"models/{version}_feature_columns.json"),
            (metadata_path, f"models/{version}_training_metadata.json"),
        ]
        
        print(f"📤 Uploading models to gs://{bucket_name}/models/")
        
        uploaded_count = 0
        for local_path, cloud_path in files_to_upload:
            try:
                if os.path.exists(local_path):
                    blob = bucket.blob(cloud_path)
                    blob.upload_from_filename(local_path)
                    print(f"  ✓ {Path(cloud_path).name}")
                    uploaded_count += 1
                else:
                    print(f"  ✗ File not found: {local_path}")
            except Exception as e:
                print(f"  ✗ Failed to upload {Path(cloud_path).name}: {e}")
        
        # Upload updated manifest
        try:
            local_manifest = Path(version_info['paths']['manifest'])
            if local_manifest.exists():
                blob = bucket.blob("models/manifest.json")
                blob.upload_from_filename(str(local_manifest))
                print(f"  ✓ manifest.json")
        except Exception as e:
            print(f"  ⚠️ Failed to upload manifest: {e}")
        
        print(f"\n✅ Uploaded {uploaded_count}/{len(files_to_upload)} model files to Cloud Storage")
        print(f"   Cloud location: gs://{bucket_name}/models/{version}_*")
        return True
        
    except ImportError:
        print("⚠️  Google Cloud Storage SDK not installed")
        print("   Install with: pip install google-cloud-storage")
        return False
    except Exception as e:
        print(f"⚠️ Cloud Storage upload failed: {e}")
        print("   Models saved locally but not uploaded to GCP")
        print("   Set GCP_PROJECT_ID and GCP_BUCKET environment variables to enable")
        return False


@task(name="register_models_to_vertex_ai", retries=2, retry_delay_seconds=5)
def register_models_to_vertex_ai(version_info: Dict) -> bool:
    """
    Register trained models to Google Cloud Vertex AI Model Registry.
    
    Args:
        version_info: Dictionary with version, paths, and metadata
        
    Returns:
        True if successful, False if Vertex AI is unavailable
    """
    try:
        from src.vertex_ai_model_registry import VertexAIModelRegistry
        
        version = version_info['version']
        clf_model_path = version_info['paths']['clf_model']
        reg_model_path = version_info['paths']['reg_model']
        metadata = version_info['metadata']
        
        print(f"\n{'='*60}")
        print("STEP 7B: REGISTER MODELS TO VERTEX AI")
        print(f"{'='*60}")
        
        registry = VertexAIModelRegistry()
        
        # Register classification model
        print(f"\n📤 Uploading classification model to Vertex AI...")
        try:
            clf_model_id = registry.upload_model(
                model_path=clf_model_path,
                display_name=f"bitcoin-classifier-{version}",
                description=f"Bitcoin price direction classifier. Accuracy: {metadata['classification_metrics'].get('accuracy', 0):.4f}",
                metrics=metadata['classification_metrics'],
                model_type="classification"
            )
            print(f"✅ Classification model registered: {clf_model_id}")
        except Exception as e:
            print(f"⚠️ Classification model registration failed: {e}")
        
        # Register regression model
        print(f"\n📤 Uploading regression model to Vertex AI...")
        try:
            reg_model_id = registry.upload_model(
                model_path=reg_model_path,
                display_name=f"bitcoin-regressor-{version}",
                description=f"Bitcoin price regression model. RMSE: {metadata['regression_metrics'].get('rmse', 0):.4f}",
                metrics=metadata['regression_metrics'],
                model_type="regression"
            )
            print(f"✅ Regression model registered: {reg_model_id}")
        except Exception as e:
            print(f"⚠️ Regression model registration failed: {e}")
        
        print(f"\n✅ Models registered to Vertex AI Model Registry")
        return True
        
    except ImportError:
        print("⚠️  Vertex AI SDK not installed. Skipping model registration.")
        print("   Install with: pip install google-cloud-aiplatform")
        return False
    except Exception as e:
        print(f"⚠️ Vertex AI registration failed: {e}")
        print("   Models saved locally but not registered to GCP")
        return False


@task(name="upload_features_to_feature_store", retries=2, retry_delay_seconds=5)
def upload_features_to_feature_store(df_features: pd.DataFrame, feature_names: list) -> bool:
    """
    Upload computed features to Google Cloud Vertex AI Feature Store.
    
    Args:
        df_features: DataFrame with features
        feature_names: List of feature column names
        
    Returns:
        True if successful, False if Feature Store is unavailable
    """
    try:
        from src.vertex_ai_feature_store import VertexAIFeatureStore
        
        print(f"\n{'='*60}")
        print("STEP 7B: UPLOAD FEATURES TO VERTEX AI FEATURE STORE")
        print(f"{'='*60}")
        
        feature_store = VertexAIFeatureStore()
        
        # Connect to Feature Store (creates if doesn't exist)
        print(f"📤 Connecting to Vertex AI Feature Store...")
        if not feature_store.connect():
            print(f"⚠️  Failed to connect to Feature Store. Skipping upload.")
            return False
        
        # Prepare features for upload
        print(f"📤 Preparing {len(feature_names)} features for upload...")
        
        # Select only the technical indicator features
        feature_df = df_features[feature_names].copy()
        feature_df['timestamp'] = pd.Timestamp.utcnow()
        
        # Upload to Feature Store
        print(f"📤 Uploading features to Vertex AI Feature Store...")
        ingest_success = feature_store.ingest_features(
            features_df=feature_df,
            entity_id_column="timestamp"
        )
        
        if ingest_success:
            print(f"✅ Features uploaded to Vertex AI Feature Store")
            print(f"   Features: {len(feature_names)}")
        else:
            print(f"⚠️  Feature ingestion failed. Check logs above for errors.")
            return False
        print(f"   Records: {len(feature_df)}")
        return True
        
    except ImportError:
        print("⚠️  Vertex AI Feature Store SDK not installed. Skipping feature upload.")
        print("   Install with: pip install google-cloud-aiplatform")
        return False
    except Exception as e:
        print(f"⚠️ Feature Store upload failed: {e}")
        print("   Features computed locally but not uploaded to GCP")
        return False


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
        
        # Step 4: Model Training (select best models)
        reg_model, reg_model_name = train_regression_model(X_train, y_reg_train, X_test, y_reg_test, reg_hyperparams)
        clf_model, clf_model_name = train_classification_model(X_train, y_clf_train, X_test, y_clf_test, clf_hyperparams)
        
        # Step 5: Model Evaluation (concurrent)
        reg_metrics = evaluate_regression_model(reg_model, X_test, y_reg_test)
        clf_metrics = evaluate_classification_model(clf_model, X_test, y_clf_test)
        
        # Step 6: Save and Version Models
        version_info = save_and_version_models(
            reg_model,
            clf_model,
            reg_model_name,
            clf_model_name,
            scaler,
            feature_cols,
            reg_metrics,
            clf_metrics,
            output_dir=output_dir
        )
        
        # Step 7A: Upload models to Cloud Storage (optional - continues if fails)
        cloud_storage_success = upload_models_to_cloud_storage(version_info)
        
        # Step 7B: Register models to Vertex AI (optional - continues if fails)
        vertex_ai_success = register_models_to_vertex_ai(version_info)
        
        # Step 7C: Upload features to Vertex AI Feature Store (optional - continues if fails)
        feature_upload_success = upload_features_to_feature_store(df_processed, feature_cols)
        
        # Calculate pipeline duration
        pipeline_end = datetime.utcnow()
        duration = (pipeline_end - pipeline_start).total_seconds()
        
        # Success notification
        cloud_status = "✅" if cloud_storage_success else "⚠️ (Optional)"
        vertex_status = "✅" if vertex_ai_success else "⚠️ (Optional)"
        feature_status = "✅" if feature_upload_success else "⚠️ (Optional)"
        
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

**Cloud Integration:**
- {cloud_status} Models uploaded to Cloud Storage
- {vertex_status} Vertex AI Model Registry
- {feature_status} Feature Store (Features uploaded)

**Models Location:**
- Local: `{output_dir}/{version_info['version']}_*.pkl`
- Cloud: `gs://YOUR_BUCKET/models/{version_info['version']}_*`
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
            'paths': version_info['paths'],
            'cloud_upload': cloud_storage_success
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
