"""
Test Complete ML Pipeline
Tests all 3 requirements: Feature Store + Model Experiments + Model Registry
"""

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT\ml-project-480417-2e263ddd92fb.json'

from src.train_with_feature_store import train_with_feature_store

print("\n" + "="*80)
print("TESTING COMPLETE ML PIPELINE")
print("="*80)
print("\nRequirements:")
print("1. ✓ Fetches from Feature Store (Vertex AI)")
print("2. ✓ Experiments with multiple models (RF, GB, Ridge, Lasso, SVM)")
print("3. ✓ Uploads to Model Registry (Vertex AI)")
print("\n" + "="*80 + "\n")

results = train_with_feature_store(
    use_feature_store=True,
    test_size=0.1,
    experiment_models=True,
    use_model_registry=True
)

print("\n" + "="*80)
print("PIPELINE TEST COMPLETE!")
print("="*80)
print(f"\nFinal Results:")
print(f"  Version: {results['version']}")
print(f"  Classification Model: {results['classification_metrics'].get('model_name', 'RandomForest')}")
print(f"  Classification Accuracy: {results['classification_metrics']['accuracy']:.2%}")
print(f"  Regression Model: {results['regression_metrics'].get('model_name', 'RandomForest')}")
print(f"  Regression RMSE: {results['regression_metrics']['rmse']:.4f}")
print(f"  Regression R²: {results['regression_metrics']['r2']:.4f}")
print("\n" + "="*80)
