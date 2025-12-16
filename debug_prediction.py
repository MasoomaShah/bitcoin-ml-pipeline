#!/usr/bin/env python
"""Debug prediction with cached data"""
import os
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from pathlib import Path
import joblib
import json
import pandas as pd
import numpy as np

print("=" * 80)
print("DEBUGGING BITCOIN PREDICTION (WITH CACHED DATA)")
print("=" * 80)

# Load models and scaler
models_dir = Path("models")
version = "v20251215T121115Z"

print(f"\n1. Loading models from {models_dir}...")
clf_model = joblib.load(models_dir / f"{version}_clf_model.pkl")
reg_model = joblib.load(models_dir / f"{version}_reg_model.pkl")
scaler = joblib.load(models_dir / f"{version}_scaler.pkl")

print(f"   ✓ Classification model loaded")
print(f"   ✓ Regression model loaded")
print(f"   ✓ Scaler loaded")

# Load feature columns
with open(models_dir / f"{version}_feature_columns.json") as f:
    feature_columns = json.load(f)

print(f"\n2. Features expected: {len(feature_columns)}")

# Load cached data
print(f"\n3. Loading cached Bitcoin data...")
data_files = sorted(Path("data/processed").glob("*.csv"))
if data_files:
    latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
    print(f"   Loading: {latest_file.name}")
    df = pd.read_csv(latest_file)
    print(f"   ✓ Loaded {len(df)} rows")
else:
    print(f"   No cached data found!")
    exit(1)

# Check feature availability
missing_features = [f for f in feature_columns if f not in df.columns]
if missing_features:
    print(f"   ⚠️  Missing features: {missing_features[:10]}...")
else:
    print(f"   ✓ All {len(feature_columns)} features available")

# Get latest row
latest_row = df.iloc[-1]
print(f"\n4. Latest data point:")
if 'date' in df.columns:
    print(f"   Date: {latest_row['date']}")
print(f"   Price: ${latest_row['price']:.2f}")

# Prepare features for prediction
X_df = latest_row[feature_columns].to_frame().T
X_df['future_price_change'] = 0.0
X_df['market_class'] = 1

scaler_columns = list(scaler.feature_names_in_)
print(f"\n5. Scaling...")

X_all_scaled = scaler.transform(X_df[scaler_columns].values)

# Extract features
feature_indices = [scaler_columns.index(f) for f in feature_columns]
X_scaled = X_all_scaled[:, feature_indices]
print(f"   ✓ X_scaled shape (for model): {X_scaled.shape}")

# Make predictions
print(f"\n6. Making predictions...")

regression_output = reg_model.predict(X_scaled)[0]
classification_output = clf_model.predict(X_scaled)[0]
classification_proba = clf_model.predict_proba(X_scaled)[0]

print(f"\n7. RAW MODEL OUTPUTS:")
print(f"   Regression output: {regression_output:.6f}")
print(f"   Classification: {'UP' if classification_output == 1 else 'DOWN'}")
print(f"   Classification confidence: {max(classification_proba)*100:.2f}%")

# Calculate predicted price
current_price = latest_row['price']
predicted_price = current_price * (1 + regression_output)

print(f"\n8. FINAL PREDICTION:")
print(f"   Current price: ${current_price:.2f}")
print(f"   Regression predicts change: {regression_output*100:.4f}%")
print(f"   Predicted price: ${predicted_price:.2f}")
print(f"   Price change: ${predicted_price - current_price:.2f}")

# Check if this seems reasonable
if abs(regression_output) > 0.5:
    print(f"\n❌ PROBLEM: Regression predicting {regression_output*100:.1f}% change!")
    print(f"   This seems unrealistic for daily Bitcoin prediction")
elif abs(regression_output) < 0.01:
    print(f"\n⚠️  Model output very small: {regression_output:.6f}")
    print(f"   This might indicate features are outside training distribution")
else:
    print(f"\n✓ Prediction seems reasonable")
