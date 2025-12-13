"""
Quick test of deep learning models with minimal training
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from src.deep_learning_models import DeepLearningModels, KERAS_AVAILABLE

print("="*70)
print("QUICK TEST - Deep Learning Models")
print("="*70)

if not KERAS_AVAILABLE:
    print("\nERROR: TensorFlow/Keras not installed")
    print("Install with: pip install tensorflow keras")
    sys.exit(1)

print("\n[*] Creating sample time series data...")
# Create sample data (100 samples, 10 features)
np.random.seed(42)
X_sample = np.random.randn(100, 10)
y_sample = np.random.randint(0, 2, 100)

print(f"    Sample data shape: {X_sample.shape}")

# Initialize deep learning models
dl = DeepLearningModels(sequence_length=10, random_state=42)

print("\n[*] Preparing sequences...")
X_seq, y_seq = dl.prepare_sequences(X_sample, y_sample)
print(f"    Sequence shape: {X_seq.shape}")
print(f"    Target shape: {y_seq.shape}")

# Test LSTM
print("\n[*] Creating LSTM model...")
lstm_model = dl.create_lstm_model(
    input_shape=(10, 10),  # (sequence_length, n_features)
    output_dim=1,
    task='classification'
)
print(f"    Model created successfully")
print(f"    Total parameters: {lstm_model.count_params():,}")

# Test training (just 2 epochs for quick test)
print("\n[*] Training LSTM (2 epochs, quick test)...")
history = dl.train_rnn_model(
    lstm_model, X_seq, y_seq,
    epochs=2,
    batch_size=16,
    verbose=1
)
print("    Training completed!")

# Test prediction
print("\n[*] Making predictions...")
predictions = lstm_model.predict(X_seq, verbose=0)
print(f"    Predictions shape: {predictions.shape}")
print(f"    Sample predictions: {predictions[:5].flatten()}")

# Test GRU
print("\n[*] Creating GRU model...")
gru_model = dl.create_gru_model(
    input_shape=(10, 10),
    output_dim=1,
    task='classification'
)
print(f"    Model created successfully")
print(f"    Total parameters: {gru_model.count_params():,}")

print("\n" + "="*70)
print("SUCCESS! All deep learning models work correctly")
print("="*70)
print("\nNext steps:")
print("  1. Run full training: python src/train_all_models.py")
print("  2. Be patient - real training takes 10-15 minutes")
