"""
Train and Compare ALL Model Types:
- Traditional ML (RandomForest, GradientBoosting, SVM, etc.)
- Deep Learning (LSTM, GRU)
- Statistical (Prophet)
"""

import sys
import os
# Fix Windows UTF-8 encoding issue
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Force stdout encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.model_experiments import ModelExperiments
from src.deep_learning_models import DeepLearningModels, ProphetModel, KERAS_AVAILABLE, PROPHET_AVAILABLE
from src.fetch_alpha_vantage import fetch_crypto_with_indicators
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


def prepare_data(symbol='BTC', currency='USD', test_size=0.2):
    """Fetch and prepare data for all model types"""
    print(f"\n[*] Fetching {symbol}/{currency} data...")
    df = fetch_crypto_with_indicators(symbol, currency)
    
    print(f"✓ Loaded {len(df)} samples")
    print(f"✓ Date range: {df.index[0]} to {df.index[-1]}")
    
    # Sort by date
    df = df.sort_index()
    
    # Ensure we have the basic columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Compute technical indicators locally
    print("[*] Computing technical indicators...")
    
    # Moving averages
    df['SMA_7'] = df['Close'].rolling(window=7).mean()
    df['SMA_14'] = df['Close'].rolling(window=14).mean()
    df['SMA_30'] = df['Close'].rolling(window=30).mean()
    df['EMA_7'] = df['Close'].ewm(span=7).mean()
    df['EMA_14'] = df['Close'].ewm(span=14).mean()
    
    # Momentum
    df['momentum_7'] = df['Close'] - df['Close'].shift(7)
    df['momentum_14'] = df['Close'] - df['Close'].shift(14)
    df['momentum_30'] = df['Close'] - df['Close'].shift(30)
    
    # Volatility
    df['volatility_7'] = df['Close'].rolling(window=7).std()
    df['volatility_14'] = df['Close'].rolling(window=14).std()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    
    # Bollinger Bands
    df['BB_middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    df['BB_width'] = df['BB_upper'] - df['BB_lower']
    
    # Volume indicators
    df['volume_SMA_7'] = df['Volume'].rolling(window=7).mean()
    df['volume_change'] = df['Volume'].pct_change()
    
    print(f"✓ Added {len(df.columns) - len(required_cols)} technical indicators")
    
    # Create targets
    df['direction'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df['price_change_pct'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100
    
    # Remove rows with NaN or inf
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    # Define feature columns (exclude target, date, and non-predictive columns)
    exclude_cols = ['direction', 'price_change_pct', 'date', 'timestamp']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64']]
    
    print(f"✓ Using {len(feature_cols)} features")
    print(f"✓ Final dataset: {len(df)} samples (after removing NaN)")
    
    return df, feature_cols


def train_traditional_models(X_train, y_train_clf, y_train_reg, X_test, y_test_clf, y_test_reg):
    """Train traditional ML models"""
    print("\n" + "="*70)
    print("1️⃣  TRADITIONAL ML MODELS")
    print("="*70)
    
    exp = ModelExperiments(random_state=42)
    
    # Classification
    print("\n[*] Classification (Direction Prediction):")
    best_clf, best_clf_metrics, clf_results = exp.evaluate_classification(
        X_train, X_test,
        y_train_clf, y_test_clf
    )
    
    # Regression
    print("\n[*] Regression (Price Change %):")
    best_reg, best_reg_metrics, reg_results = exp.evaluate_regression(
        X_train, X_test,
        y_train_reg, y_test_reg
    )
    
    return clf_results, reg_results


def train_deep_learning_models(X_train, y_train_clf, y_train_reg, X_test, y_test_clf, y_test_reg, feature_cols):
    """Train LSTM and GRU models"""
    if not KERAS_AVAILABLE:
        print("\n⚠️  Skipping deep learning models (TensorFlow not installed)")
        return None, None
    
    print("\n" + "="*70)
    print("2️⃣  DEEP LEARNING MODELS (LSTM & GRU)")
    print("="*70)
    
    from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error, r2_score
    
    dl_models = DeepLearningModels(sequence_length=30, random_state=42)
    
    # Prepare sequences
    print(f"\n🔄 Preparing sequences (lookback={dl_models.sequence_length} days)...")
    X_train_seq, y_train_clf_seq = dl_models.prepare_sequences(X_train, y_train_clf)
    X_test_seq, y_test_clf_seq = dl_models.prepare_sequences(X_test, y_test_clf)
    
    _, y_train_reg_seq = dl_models.prepare_sequences(X_train, y_train_reg)
    _, y_test_reg_seq = dl_models.prepare_sequences(X_test, y_test_reg)
    
    print(f"✓ Train sequences: {X_train_seq.shape}")
    print(f"✓ Test sequences: {X_test_seq.shape}")
    
    results = {'classification': [], 'regression': []}
    
    # LSTM Classification
    print("\n📊 Training LSTM (Classification)...")
    lstm_clf = dl_models.create_lstm_model(
        input_shape=(dl_models.sequence_length, len(feature_cols)),
        output_dim=1,
        task='classification'
    )
    
    history_lstm_clf = dl_models.train_rnn_model(
        lstm_clf, X_train_seq, y_train_clf_seq,
        X_test_seq, y_test_clf_seq,
        epochs=50, batch_size=32, verbose=1
    )
    
    y_pred_lstm_clf = (lstm_clf.predict(X_test_seq, verbose=0) > 0.5).astype(int).flatten()
    lstm_clf_acc = accuracy_score(y_test_clf_seq, y_pred_lstm_clf)
    
    results['classification'].append({
        'Model': 'LSTM',
        'Test Accuracy': lstm_clf_acc,
        'Type': 'Deep Learning'
    })
    
    print(f"✓ LSTM Classification Accuracy: {lstm_clf_acc:.4f}")
    
    # GRU Classification
    print("\n📊 Training GRU (Classification)...")
    gru_clf = dl_models.create_gru_model(
        input_shape=(dl_models.sequence_length, len(feature_cols)),
        output_dim=1,
        task='classification'
    )
    
    history_gru_clf = dl_models.train_rnn_model(
        gru_clf, X_train_seq, y_train_clf_seq,
        X_test_seq, y_test_clf_seq,
        epochs=50, batch_size=32, verbose=1
    )
    
    y_pred_gru_clf = (gru_clf.predict(X_test_seq, verbose=0) > 0.5).astype(int).flatten()
    gru_clf_acc = accuracy_score(y_test_clf_seq, y_pred_gru_clf)
    
    results['classification'].append({
        'Model': 'GRU',
        'Test Accuracy': gru_clf_acc,
        'Type': 'Deep Learning'
    })
    
    print(f"✓ GRU Classification Accuracy: {gru_clf_acc:.4f}")
    
    # LSTM Regression
    print("\n📊 Training LSTM (Regression)...")
    lstm_reg = dl_models.create_lstm_model(
        input_shape=(dl_models.sequence_length, len(feature_cols)),
        output_dim=1,
        task='regression'
    )
    
    history_lstm_reg = dl_models.train_rnn_model(
        lstm_reg, X_train_seq, y_train_reg_seq,
        X_test_seq, y_test_reg_seq,
        epochs=50, batch_size=32, verbose=1
    )
    
    y_pred_lstm_reg = lstm_reg.predict(X_test_seq, verbose=0).flatten()
    lstm_reg_mse = mean_squared_error(y_test_reg_seq, y_pred_lstm_reg)
    lstm_reg_mae = mean_absolute_error(y_test_reg_seq, y_pred_lstm_reg)
    lstm_reg_r2 = r2_score(y_test_reg_seq, y_pred_lstm_reg)
    
    results['regression'].append({
        'Model': 'LSTM',
        'Test MSE': lstm_reg_mse,
        'Test MAE': lstm_reg_mae,
        'Test R2': lstm_reg_r2,
        'Type': 'Deep Learning'
    })
    
    print(f"✓ LSTM Regression - MSE: {lstm_reg_mse:.4f}, MAE: {lstm_reg_mae:.4f}, R²: {lstm_reg_r2:.4f}")
    
    # GRU Regression
    print("\n📊 Training GRU (Regression)...")
    gru_reg = dl_models.create_gru_model(
        input_shape=(dl_models.sequence_length, len(feature_cols)),
        output_dim=1,
        task='regression'
    )
    
    history_gru_reg = dl_models.train_rnn_model(
        gru_reg, X_train_seq, y_train_reg_seq,
        X_test_seq, y_test_reg_seq,
        epochs=50, batch_size=32, verbose=1
    )
    
    y_pred_gru_reg = gru_reg.predict(X_test_seq, verbose=0).flatten()
    gru_reg_mse = mean_squared_error(y_test_reg_seq, y_pred_gru_reg)
    gru_reg_mae = mean_absolute_error(y_test_reg_seq, y_pred_gru_reg)
    gru_reg_r2 = r2_score(y_test_reg_seq, y_pred_gru_reg)
    
    results['regression'].append({
        'Model': 'GRU',
        'Test MSE': gru_reg_mse,
        'Test MAE': gru_reg_mae,
        'Test R2': gru_reg_r2,
        'Type': 'Deep Learning'
    })
    
    print(f"✓ GRU Regression - MSE: {gru_reg_mse:.4f}, MAE: {gru_reg_mae:.4f}, R²: {gru_reg_r2:.4f}")
    
    # Save models
    models_dir = project_root / 'models'
    models_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    
    lstm_clf.save(models_dir / f'{timestamp}_lstm_classification.h5')
    gru_clf.save(models_dir / f'{timestamp}_gru_classification.h5')
    lstm_reg.save(models_dir / f'{timestamp}_lstm_regression.h5')
    gru_reg.save(models_dir / f'{timestamp}_gru_regression.h5')
    
    print(f"\n✓ Saved deep learning models to {models_dir}/")
    
    return results, (lstm_clf, gru_clf, lstm_reg, gru_reg)


def train_prophet_model(df):
    """Train Facebook Prophet model"""
    if not PROPHET_AVAILABLE:
        print("\n[*] Skipping Prophet (not installed)")
        return None
    
    print("\n" + "="*70)
    print("3. STATISTICAL MODEL (PROPHET)")
    print("="*70)
    
    # Check if we have a 'date' column, otherwise create dates
    if 'date' in df.columns:
        dates = pd.to_datetime(df['date'])
    else:
        # Create synthetic dates starting from a reference point
        # Use daily frequency for Bitcoin data
        from datetime import timedelta
        start_date = pd.Timestamp('2020-01-01')
        dates = pd.date_range(start=start_date, periods=len(df), freq='D')
    
    # Prophet requires datetime index and specific column names
    prophet_df = pd.DataFrame({
        'ds': dates,
        'y': df['Close'].values  # Use .values to avoid index mismatch
    })
    
    # Split: use last 20% for testing
    split_idx = int(len(prophet_df) * 0.8)
    train_df = prophet_df.iloc[:split_idx].copy()
    test_df = prophet_df.iloc[split_idx:].copy()
    
    print(f"\n[*] Training Prophet on {len(train_df)} samples...")
    print(f"    Date range: {train_df['ds'].min()} to {train_df['ds'].max()}")
    
    prophet_model = ProphetModel()
    prophet_model.train(
        train_df,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    
    # Make predictions for test period
    forecast = prophet_model.predict(periods=len(test_df), freq='D')
    
    # Calculate metrics
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    y_true = test_df['y'].values
    y_pred = forecast['yhat'].tail(len(test_df)).values
    
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n✓ Prophet Performance:")
    print(f"  MSE: {mse:.4f}")
    print(f"  MAE: {mae:.4f}")
    print(f"  R²: {r2:.4f}")
    
    # Save model
    models_dir = project_root / 'models'
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    joblib.dump(prophet_model, models_dir / f'{timestamp}_prophet.pkl')
    
    print(f"\n✓ Saved Prophet model to {models_dir}/")
    
    return {
        'MSE': mse,
        'MAE': mae,
        'R2': r2,
        'model': prophet_model
    }


def print_comparison_summary(trad_clf_results, trad_reg_results, dl_results):
    """Print comprehensive comparison of all models"""
    print("\n" + "="*70)
    print("COMPREHENSIVE MODEL COMPARISON")
    print("="*70)
    
    # Classification comparison
    print("\n[CLASSIFICATION] Direction Prediction:")
    print("-" * 70)
    
    # Convert traditional ML results to flat dictionary format
    clf_data = []
    for result in trad_clf_results:
        clf_data.append({
            'Model': result['metrics']['model_name'],
            'Accuracy': result['metrics']['accuracy'],
            'F1-Score': result['metrics']['f1_score'],
            'Type': 'Traditional ML'
        })
    
    # Add deep learning results if available
    if dl_results and 'classification' in dl_results:
        for result in dl_results['classification']:
            clf_data.append(result)
    
    clf_comparison = pd.DataFrame(clf_data)
    if len(clf_comparison) > 0:
        clf_comparison = clf_comparison.sort_values('Accuracy', ascending=False)
        print(clf_comparison.to_string(index=False))
        
        print(f"\n[BEST] Classification: {clf_comparison.iloc[0]['Model']} "
              f"(Accuracy: {clf_comparison.iloc[0]['Accuracy']:.4f})")
    
    # Regression comparison
    print("\n\n[REGRESSION] Price Change %:")
    print("-" * 70)
    
    # Convert traditional ML results to flat dictionary format
    reg_data = []
    for result in trad_reg_results:
        reg_data.append({
            'Model': result['metrics']['model_name'],
            'RMSE': result['metrics']['rmse'],
            'MAE': result['metrics']['mae'],
            'R2': result['metrics']['r2'],
            'Type': 'Traditional ML'
        })
    
    # Add deep learning results if available
    if dl_results and 'regression' in dl_results:
        for result in dl_results['regression']:
            reg_data.append(result)
    
    reg_comparison = pd.DataFrame(reg_data)
    if len(reg_comparison) > 0:
        reg_comparison = reg_comparison.sort_values('R2', ascending=False)
        print(reg_comparison.to_string(index=False))
        
        print(f"\n[BEST] Regression: {reg_comparison.iloc[0]['Model']} "
              f"(R2: {reg_comparison.iloc[0]['R2']:.4f})")


def main():
    """Main training pipeline"""
    print("\n" + "="*70)
    print("BITCOIN PRICE PREDICTION - ALL MODEL TYPES")
    print("="*70)
    print("\nThis script will train and compare:")
    print("  * Traditional ML (RandomForest, GradientBoosting, SVM, etc.)")
    
    if KERAS_AVAILABLE:
        print("  * Deep Learning (LSTM, GRU)")
    else:
        print("  X Deep Learning (TensorFlow not installed)")
    
    if PROPHET_AVAILABLE:
        print("  * Statistical (Prophet)")
    else:
        print("  X Statistical (Prophet not installed)")
    
    # 1. Prepare data
    df, feature_cols = prepare_data()
    
    X = df[feature_cols].values
    y_clf = df['direction'].values
    y_reg = df['price_change_pct'].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train/test split
    X_train, X_test, y_train_clf, y_test_clf = train_test_split(
        X_scaled, y_clf, test_size=0.2, random_state=42, shuffle=False
    )
    
    _, _, y_train_reg, y_test_reg = train_test_split(
        X_scaled, y_reg, test_size=0.2, random_state=42, shuffle=False
    )
    
    print(f"\n✓ Train set: {len(X_train)} samples")
    print(f"✓ Test set: {len(X_test)} samples")
    
    # 2. Train traditional ML
    trad_clf_results, trad_reg_results = train_traditional_models(
        X_train, y_train_clf, y_train_reg,
        X_test, y_test_clf, y_test_reg
    )
    
    # 3. Train deep learning
    dl_results = None
    if KERAS_AVAILABLE:
        dl_results, dl_models = train_deep_learning_models(
            X_train, y_train_clf, y_train_reg,
            X_test, y_test_clf, y_test_reg,
            feature_cols
        )
    
    # 4. Train Prophet
    prophet_results = train_prophet_model(df)
    
    # 5. Print comparison
    print_comparison_summary(trad_clf_results, trad_reg_results, dl_results)
    
    if prophet_results:
        print("\n\n[PROPHET] Time Series Forecast:")
        print("-" * 70)
        print(f"  MSE: {prophet_results['MSE']:.4f}")
        print(f"  MAE: {prophet_results['MAE']:.4f}")
        print(f"  R2: {prophet_results['R2']:.4f}")
    
    print("\n" + "="*70)
    print("[SUCCESS] ALL MODELS TRAINED SUCCESSFULLY!")
    print("="*70)
    
    print("\n[INFO] Models saved to: models/")
    print("\nNext steps:")
    print("  1. Review model comparison above")
    print("  2. Choose best model for deployment")
    print("  3. Update API to use selected model")
    
    # Send Discord notification with all results
    try:
        sys.path.insert(0, str(project_root))
        from discord_notify import send_discord_notification
        
        # Build summary fields
        fields = []
        
        # Traditional ML best results
        if trad_clf_results:
            best_clf = max(trad_clf_results, key=lambda x: x['metrics']['accuracy'])
            fields.append({
                'name': f"🏆 Best Classification: {best_clf['model']}",
                'value': f"Accuracy: {best_clf['metrics']['accuracy']:.2%}",
                'inline': True
            })
        
        # Prophet results
        if prophet_results:
            fields.append({
                'name': '🏆 Best Forecasting: Prophet',
                'value': f"R² = {prophet_results['R2']:.4f}",
                'inline': True
            })
        
        # Deep Learning results
        if dl_results and 'classification' in dl_results:
            lstm_acc = dl_results['classification'][0]['Test Accuracy']
            gru_acc = dl_results['classification'][1]['Test Accuracy']
            fields.extend([
                {'name': 'LSTM Accuracy', 'value': f"{lstm_acc:.2%}", 'inline': True},
                {'name': 'GRU Accuracy', 'value': f"{gru_acc:.2%}", 'inline': True}
            ])
        
        fields.append({'name': 'Models Saved', 'value': 'models/', 'inline': False})
        
        send_discord_notification(
            message="All models trained successfully!\n\n✅ Traditional ML\n✅ Deep Learning (LSTM/GRU)\n✅ Prophet Forecasting",
            title="🎉 Complete ML Training Finished",
            color="green",
            fields=fields
        )
    except Exception as e:
        print(f"\n[NOTE] Could not send Discord notification: {e}")


if __name__ == "__main__":
    main()
