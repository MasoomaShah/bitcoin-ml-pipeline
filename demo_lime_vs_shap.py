"""
Demo: LIME vs SHAP - Understanding Model Explanations

This script demonstrates the difference between LIME and SHAP for
explaining machine learning predictions.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

print("="*70)
print("LIME vs SHAP - Explainability Demo")
print("="*70)

# Check if libraries are available
try:
    from lime.lime_tabular import LimeTabularExplainer
    print("\n✓ LIME is available")
    LIME_OK = True
except ImportError:
    print("\n✗ LIME not installed")
    LIME_OK = False

try:
    import shap
    print("✓ SHAP is available")
    SHAP_OK = True
except ImportError:
    print("✗ SHAP not installed")
    SHAP_OK = False

if not (LIME_OK or SHAP_OK):
    print("\nInstall at least one: pip install lime shap")
    exit(1)

# Create sample data
print("\n" + "-"*70)
print("Creating sample dataset...")
X, y = make_classification(
    n_samples=1000,
    n_features=10,
    n_informative=5,
    n_redundant=2,
    random_state=42
)

feature_names = [f"Feature_{i}" for i in range(10)]
print(f"  Dataset: {X.shape[0]} samples, {X.shape[1]} features")

# Train a model
print("\nTraining RandomForest model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)
print(f"  Model accuracy: {model.score(X, y):.2%}")

# Pick a sample to explain
sample_idx = 0
X_sample = X[sample_idx:sample_idx+1]
prediction = model.predict(X_sample)[0]
proba = model.predict_proba(X_sample)[0]

print(f"\n" + "-"*70)
print(f"Explaining prediction for sample #{sample_idx}")
print(f"  True label: {y[sample_idx]}")
print(f"  Predicted: {prediction}")
print(f"  Confidence: {max(proba):.2%}")

# LIME Explanation
if LIME_OK:
    print("\n" + "="*70)
    print("LIME EXPLANATION")
    print("="*70)
    print("\nWhat LIME does:")
    print("  1. Creates synthetic data by perturbing the input")
    print("  2. Gets predictions for these synthetic samples")
    print("  3. Fits a simple linear model locally")
    print("  4. Shows which features matter for THIS prediction")
    
    lime_explainer = LimeTabularExplainer(
        X,
        feature_names=feature_names,
        class_names=['Class 0', 'Class 1'],
        mode='classification'
    )
    
    lime_exp = lime_explainer.explain_instance(
        X_sample[0],
        model.predict_proba,
        num_features=10
    )
    
    print("\nTop features (LIME):")
    for feature, weight in lime_exp.as_list(label=prediction)[:5]:
        print(f"  {feature}: {weight:+.4f}")
    
    print(f"\nLIME Score: {lime_exp.score:.4f}")
    print("  (Higher score = better local approximation)")

# SHAP Explanation
if SHAP_OK:
    print("\n" + "="*70)
    print("SHAP EXPLANATION")
    print("="*70)
    print("\nWhat SHAP does:")
    print("  1. Uses game theory (Shapley values)")
    print("  2. Considers all possible feature combinations")
    print("  3. Distributes prediction credit fairly among features")
    print("  4. Consistent and theoretically grounded")
    
    try:
        shap_explainer = shap.TreeExplainer(model)
        shap_values = shap_explainer.shap_values(X_sample)
        
        # For binary classification, use positive class
        if isinstance(shap_values, list):
            shap_vals = shap_values[1][0]
        else:
            shap_vals = shap_values[0]
        
        print("\nTop features (SHAP):")
        feature_importance = [(feature_names[i], shap_vals[i]) 
                             for i in range(len(feature_names))]
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
        
        for feature, value in feature_importance[:5]:
            print(f"  {feature}: {value:+.4f}")
        
        print(f"\nBase value: {shap_explainer.expected_value[1]:.4f}")
        print(f"Prediction: {shap_explainer.expected_value[1] + sum(shap_vals):.4f}")
    except Exception as e:
        print(f"\nSHAP error (likely PyTorch issue): {e}")

# Comparison
print("\n" + "="*70)
print("KEY DIFFERENCES")
print("="*70)

print("""
┌─────────────┬──────────────────────────┬──────────────────────────┐
│ Aspect      │ LIME                     │ SHAP                     │
├─────────────┼──────────────────────────┼──────────────────────────┤
│ Method      │ Local linear approx.     │ Game theory (Shapley)    │
│ Speed       │ Fast                     │ Slower                   │
│ Accuracy    │ Approximate              │ Exact (for trees)        │
│ Consistency │ May vary between runs    │ Always consistent        │
│ Scope       │ Model-agnostic           │ Model-specific optimized │
│ Best for    │ Quick explanations       │ Rigorous analysis        │
└─────────────┴──────────────────────────┴──────────────────────────┘

IN YOUR BITCOIN API:
  
  POST /explain      → Uses SHAP (more accurate, slower)
  POST /explain/lime → Uses LIME (faster, approximate)
  
  Use LIME when: You need quick explanations for many predictions
  Use SHAP when: You need accurate, consistent explanations

""")

print("="*70)
print("Demo complete!")
print("="*70)
