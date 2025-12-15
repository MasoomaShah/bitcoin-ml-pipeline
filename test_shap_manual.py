import joblib
import json
import pandas as pd
import numpy as np

# Load models and data
print("Loading models...")
clf = joblib.load("models/v20251208T075527Z_clf_model.pkl")
reg = joblib.load("models/v20251208T075527Z_reg_model.pkl")
scaler = joblib.load("models/v20251208T075527Z_scaler.pkl")

with open("models/v20251208T075527Z_feature_columns.json") as f:
    feature_columns = json.load(f)

# Load data
df = pd.read_csv("data/raw/bitcoin_timeseries.csv", index_col=0, parse_dates=True)
print(f"Data shape: {df.shape}")
print(f"Feature columns: {len(feature_columns)}")

# Get latest features
latest_features = df[feature_columns].iloc[[-1]]
print(f"\nLatest features shape: {latest_features.shape}")

# Try SHAP
print("\n" + "="*50)
print("Testing SHAP...")
print("="*50)

try:
    import shap
    print(f"✓ SHAP version: {shap.__version__}")
    
    # Create explainer
    print("\nCreating SHAP TreeExplainer (this may take 10-30 seconds)...")
    explainer = shap.TreeExplainer(reg)
    
    # Get background data
    background = df[feature_columns].tail(100).values
    print(f"Background data shape: {background.shape}")
    
    # Calculate SHAP values
    print("Calculating SHAP values...")
    shap_values = explainer.shap_values(latest_features[feature_columns].values)
    
    print(f"\n✓ SHAP values calculated!")
    print(f"✓ SHAP values shape: {np.array(shap_values).shape}")
    print(f"✓ Base value (expected model output): {explainer.expected_value}")
    
    # Top features
    feature_importance = dict(zip(feature_columns, np.abs(shap_values[0]).tolist()))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print(f"\n{'='*50}")
    print("Top 10 features by SHAP impact:")
    print(f"{'='*50}")
    for i, (feat, val) in enumerate(top_features, 1):
        print(f"{i:2d}. {feat:20s}: {val:.6f}")
    
    print(f"\n{'='*50}")
    print("All SHAP values for latest data:")
    print(f"{'='*50}")
    for feat, shap_val in zip(feature_columns, shap_values[0]):
        print(f"{feat:20s}: {shap_val:+.6f}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
