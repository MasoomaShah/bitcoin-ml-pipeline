"""
LIME Explainability Demo with Bitcoin Prediction Model
Shows how LIME explains individual predictions
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from lime.lime_tabular import LimeTabularExplainer
import joblib

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.fetch_alpha_vantage import fetch_crypto_with_indicators
from sklearn.preprocessing import StandardScaler

print("="*70)
print("LIME EXPLAINABILITY DEMO - Bitcoin Price Prediction")
print("="*70)

# 1. Load a trained model
print("\n[1] Loading trained model...")
models_dir = project_root / 'models'
model_files = list(models_dir.glob('v*_clf_model.pkl'))

if not model_files:
    print("  No trained models found. Train a model first:")
    print("  python src/train_all_models.py")
    sys.exit(1)

# Use the most recent model
latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
model = joblib.load(latest_model)
print(f"  ✓ Loaded: {latest_model.name}")

# Load the scaler and feature columns
timestamp = latest_model.name.split('_')[0]
scaler_file = models_dir / f"{timestamp}_scaler.pkl"
features_file = models_dir / f"{timestamp}_feature_columns.json"

import json
with open(features_file, 'r') as f:
    feature_cols = json.load(f)
    
print(f"  ✓ Loaded {len(feature_cols)} feature columns")

# 2. Get data
print("\n[2] Fetching Bitcoin data...")
df = fetch_crypto_with_indicators('BTC', 'USD')

# Add technical indicators
df['SMA_7'] = df['Close'].rolling(window=7).mean()
df['SMA_14'] = df['Close'].rolling(window=14).mean()
df['SMA_30'] = df['Close'].rolling(window=30).mean()
df['EMA_7'] = df['Close'].ewm(span=7).mean()
df['EMA_14'] = df['Close'].ewm(span=14).mean()
df['momentum_7'] = df['Close'] - df['Close'].shift(7)
df['momentum_14'] = df['Close'] - df['Close'].shift(14)
df['momentum_30'] = df['Close'] - df['Close'].shift(30)
df['volatility_7'] = df['Close'].rolling(window=7).std()
df['volatility_14'] = df['Close'].rolling(window=14).std()

delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

exp1 = df['Close'].ewm(span=12).mean()
exp2 = df['Close'].ewm(span=26).mean()
df['MACD'] = exp1 - exp2
df['MACD_signal'] = df['MACD'].ewm(span=9).mean()

df['BB_middle'] = df['Close'].rolling(window=20).mean()
bb_std = df['Close'].rolling(window=20).std()
df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
df['BB_width'] = df['BB_upper'] - df['BB_lower']

df['volume_SMA_7'] = df['Volume'].rolling(window=7).mean()
df['volume_change'] = df['Volume'].pct_change()

df['direction'] = (df['Close'].shift(-1) > df['Close']).astype(int)

df = df.replace([np.inf, -np.inf], np.nan).dropna()

# Use only the features the model was trained on
X = df[feature_cols].values
y = df['direction'].values

print(f"  ✓ Data shape: {X.shape}")

# 3. Scale data using the loaded scaler
loaded_scaler = joblib.load(scaler_file)
X_scaled = loaded_scaler.transform(X)

# 4. Create LIME explainer
print("\n[3] Creating LIME explainer...")
explainer = LimeTabularExplainer(
    X_scaled,
    feature_names=feature_cols,
    class_names=['Down', 'Up'],
    mode='classification',
    random_state=42
)
print("  ✓ LIME explainer created")

# 5. Explain a few predictions
print("\n[4] Explaining predictions...")
print("-" * 70)

num_samples = 3
for i in range(num_samples):
    idx = -(i+1)  # Last 3 samples
    instance = X_scaled[idx]
    
    # Get prediction
    prediction = model.predict([instance])[0]
    proba = model.predict_proba([instance])[0]
    
    print(f"\nSample {i+1} (index {len(X) + idx}):")
    print(f"  Prediction: {'UP' if prediction == 1 else 'DOWN'}")
    print(f"  Confidence: {max(proba)*100:.1f}%")
    
    # Get LIME explanation
    exp = explainer.explain_instance(
        instance,
        model.predict_proba,
        num_features=5
    )
    
    print(f"  Top 5 feature importances (LIME):")
    for feature, weight in exp.as_list():
        direction = "pushes UP" if weight > 0 else "pushes DOWN"
        print(f"    • {feature} ({direction}, weight={weight:.4f})")

print("\n" + "="*70)
print("LIME EXPLANATION COMPLETE")
print("="*70)
print("\nWhat LIME shows:")
print("  • Which features contributed to each prediction")
print("  • How much each feature influenced the decision")
print("  • Direction of influence (positive or negative)")
print("\nThis helps you understand:")
print("  • Why the model made a specific prediction")
print("  • Which technical indicators were most important")
print("  • If the model is using reasonable patterns")
print("="*70)
