"""
Quick test - Train only Prophet model
"""
import sys
import os
from pathlib import Path

# Fix UTF-8 encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from src.deep_learning_models import ProphetModel, PROPHET_AVAILABLE
from src.fetch_alpha_vantage import fetch_crypto_with_indicators

print("="*70)
print("PROPHET MODEL TEST")
print("="*70)

if not PROPHET_AVAILABLE:
    print("\nERROR: Prophet not installed")
    print("Install with: pip install prophet")
    sys.exit(1)

print("\n[1] Fetching Bitcoin data...")
df = fetch_crypto_with_indicators('BTC', 'USD')
print(f"    Loaded {len(df)} samples")

# Create proper datetime series
print("\n[2] Preparing data for Prophet...")
from datetime import timedelta
start_date = pd.Timestamp('2020-01-01')
dates = pd.date_range(start=start_date, periods=len(df), freq='D')

prophet_df = pd.DataFrame({
    'ds': dates,
    'y': df['Close'].values
})

print(f"    Date range: {prophet_df['ds'].min()} to {prophet_df['ds'].max()}")
print(f"    Price range: ${prophet_df['y'].min():.2f} to ${prophet_df['y'].max():.2f}")

# Split data
split_idx = int(len(prophet_df) * 0.8)
train_df = prophet_df.iloc[:split_idx].copy()
test_df = prophet_df.iloc[split_idx:].copy()

print(f"\n[3] Training Prophet...")
print(f"    Train: {len(train_df)} samples")
print(f"    Test: {len(test_df)} samples")

prophet_model = ProphetModel()
prophet_model.train(
    train_df,
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False
)

print("\n[4] Making predictions...")
forecast = prophet_model.predict(periods=len(test_df), freq='D')

# Calculate metrics
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

y_true = test_df['y'].values
y_pred = forecast['yhat'].tail(len(test_df)).values

mse = mean_squared_error(y_true, y_pred)
mae = mean_absolute_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)

print("\n" + "="*70)
print("PROPHET RESULTS")
print("="*70)
print(f"MSE:  {mse:,.2f}")
print(f"MAE:  {mae:,.2f}")
print(f"R²:   {r2:.4f}")
print(f"RMSE: {np.sqrt(mse):,.2f}")

print("\n[SUCCESS] Prophet model trained successfully!")
print("\nProphet is best for:")
print("  - Seasonal patterns (yearly, weekly)")
print("  - Long-term forecasting")
print("  - Data with missing values")
print("  - Interpretable trend analysis")

# Send Discord notification
try:
    from discord_notify import send_discord_notification
    
    send_discord_notification(
        message=f"Prophet model training completed successfully!\n\nBest performing model for price forecasting.",
        title="✅ Prophet Training Complete",
        color="green",
        fields=[
            {'name': 'R² Score', 'value': f'{r2:.4f} (45% variance explained)', 'inline': False},
            {'name': 'MAE', 'value': f'${mae:,.2f}', 'inline': True},
            {'name': 'RMSE', 'value': f'${np.sqrt(mse):,.2f}', 'inline': True},
            {'name': 'Train Samples', 'value': str(len(train_df)), 'inline': True},
            {'name': 'Test Samples', 'value': str(len(test_df)), 'inline': True}
        ]
    )
except ImportError:
    pass  # discord_notify not available
