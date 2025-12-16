#!/usr/bin/env python3
"""Debug the extreme predictions issue"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import numpy as np
import pandas as pd
import api_server

print("=" * 70)
print("DEBUGGING EXTREME PREDICTIONS")
print("=" * 70)

# Load data
print("\n1. Loading data and models...")
api_server.load_models()
api_server.load_data()

# Access the global variables
clf_model = api_server.clf_model
reg_model = api_server.reg_model
bitcoin_data = api_server.bitcoin_data
feature_columns = api_server.feature_columns
scaler = api_server.scaler

print(f"[OK] Models loaded")
print(f"[OK] Data loaded: {len(bitcoin_data)} rows")

# Get latest features
print("\n2. Examining latest features...")
latest = bitcoin_data.tail(1)
latest_features = latest[feature_columns].values.reshape(1, -1)

print(f"Latest data row:")
print(f"  Date: {latest['date'].values[0] if 'date' in latest.columns else 'N/A'}")
print(f"  Price: ${latest['price'].values[0] if 'price' in latest.columns else latest['close'].values[0]:,.2f}")
print(f"  Features shape: {latest_features.shape}")

# Show some feature values
print(f"\nFeature values (first 10):")
for i, col in enumerate(feature_columns[:10]):
    val = latest[col].values[0] if col in latest.columns else latest_features[0, i]
    print(f"  {i+1:2d}. {col:25s} = {val:10.6f}")

# Scale the features
print("\n3. Scaling features...")
X_scaled = api_server.scale_features(latest_features, feature_columns)
print(f"Scaled features shape: {X_scaled.shape}")
print(f"Scaled features (first 10): {X_scaled[0, :10]}")

# Make predictions
print("\n4. Making predictions...")
direction_pred = clf_model.predict(X_scaled)[0]
direction_proba = clf_model.predict_proba(X_scaled)[0]
price_change_pred = reg_model.predict(X_scaled)[0]

print(f"Direction prediction: {direction_pred} ({'UP' if direction_pred == 1 else 'DOWN'})")
print(f"Direction probability: {direction_proba}")
print(f"Price change prediction: {price_change_pred:.6f} ({price_change_pred*100:.2f}%)")

# Check against historical data
print("\n5. Historical analysis...")
print(f"Last 5 price changes:")
price_changes = bitcoin_data['price'].pct_change().tail(10).values
for i, pc in enumerate(price_changes[-5:]):
    print(f"  {i+1}. {pc*100:+7.2f}%")

print(f"\nPrice change statistics:")
print(f"  Mean: {price_changes.mean()*100:+.2f}%")
print(f"  Std:  {price_changes.std()*100:+.2f}%")
print(f"  Min:  {price_changes.min()*100:+.2f}%")
print(f"  Max:  {price_changes.max()*100:+.2f}%")
print(f"\nModel predicting: {price_change_pred*100:+.2f}%")

# Test clamping
print("\n6. Testing prediction clamping...")
from src.normalize_predictions import clamp_price_prediction
recent_changes_array = bitcoin_data['price'].pct_change().dropna().tail(100).values
price_change_clamped = clamp_price_prediction(price_change_pred, recent_changes_array, percentile=95)

print(f"Raw model prediction: {price_change_pred:.6f} ({price_change_pred*100:.2f}%)")
print(f"Clamped prediction:  {price_change_clamped:.6f} ({price_change_clamped*100:.2f}%)")
print(f"Improvement: {(abs(price_change_pred) - abs(price_change_clamped))*100:.2f}% reduction in magnitude")
