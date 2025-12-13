"""
Test the full training pipeline with reduced data and epochs for faster testing
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Monkey patch the training parameters to make it faster
import src.train_all_models as tam

# Store original function
original_train_dl = tam.train_deep_learning_models

def faster_train_dl(X_train, y_train_clf, y_train_reg, X_test, y_test_clf, y_test_reg, feature_cols):
    """Modified version with fewer epochs"""
    if not tam.KERAS_AVAILABLE:
        print("\n[!] Skipping deep learning models (TensorFlow not installed)")
        return None, None
    
    print("\n" + "="*70)
    print("2. DEEP LEARNING MODELS (LSTM & GRU) - QUICK TEST")
    print("="*70)
    
    from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error, r2_score
    
    dl_models = tam.DeepLearningModels(sequence_length=30, random_state=42)
    
    # Prepare sequences
    print(f"\n[*] Preparing sequences (lookback={dl_models.sequence_length} days)...")
    X_train_seq, y_train_clf_seq = dl_models.prepare_sequences(X_train, y_train_clf)
    X_test_seq, y_test_clf_seq = dl_models.prepare_sequences(X_test, y_test_clf)
    
    _, y_train_reg_seq = dl_models.prepare_sequences(X_train, y_train_reg)
    _, y_test_reg_seq = dl_models.prepare_sequences(X_test, y_test_reg)
    
    print(f"    Train sequences: {X_train_seq.shape}")
    print(f"    Test sequences: {X_test_seq.shape}")
    
    results = {'classification': [], 'regression': []}
    
    # LSTM Classification (reduced epochs)
    print("\n[*] Training LSTM (Classification) - 5 epochs only...")
    lstm_clf = dl_models.create_lstm_model(
        input_shape=(dl_models.sequence_length, len(feature_cols)),
        output_dim=1,
        task='classification'
    )
    
    history_lstm_clf = dl_models.train_rnn_model(
        lstm_clf, X_train_seq, y_train_clf_seq,
        X_test_seq, y_test_clf_seq,
        epochs=5,  # Reduced from 50
        batch_size=32,
        verbose=1
    )
    
    y_pred_lstm_clf = (lstm_clf.predict(X_test_seq, verbose=0) > 0.5).astype(int).flatten()
    lstm_clf_acc = accuracy_score(y_test_clf_seq, y_pred_lstm_clf)
    
    results['classification'].append({
        'Model': 'LSTM',
        'Test Accuracy': lstm_clf_acc,
        'Type': 'Deep Learning'
    })
    
    print(f"    LSTM Classification Accuracy: {lstm_clf_acc:.4f}")
    
    # GRU Classification (reduced epochs)
    print("\n[*] Training GRU (Classification) - 5 epochs only...")
    gru_clf = dl_models.create_gru_model(
        input_shape=(dl_models.sequence_length, len(feature_cols)),
        output_dim=1,
        task='classification'
    )
    
    history_gru_clf = dl_models.train_rnn_model(
        gru_clf, X_train_seq, y_train_clf_seq,
        X_test_seq, y_test_clf_seq,
        epochs=5,  # Reduced from 50
        batch_size=32,
        verbose=1
    )
    
    y_pred_gru_clf = (gru_clf.predict(X_test_seq, verbose=0) > 0.5).astype(int).flatten()
    gru_clf_acc = accuracy_score(y_test_clf_seq, y_pred_gru_clf)
    
    results['classification'].append({
        'Model': 'GRU',
        'Test Accuracy': gru_clf_acc,
        'Type': 'Deep Learning'
    })
    
    print(f"    GRU Classification Accuracy: {gru_clf_acc:.4f}")
    
    print("\n[*] Skipping regression models for quick test...")
    
    return results, (lstm_clf, gru_clf, None, None)

# Replace the function
tam.train_deep_learning_models = faster_train_dl

# Also skip Prophet for speed
original_train_prophet = tam.train_prophet_model
def skip_prophet(df):
    print("\n[*] Skipping Prophet for quick test...")
    return None

tam.train_prophet_model = skip_prophet

# Run main
print("="*70)
print("QUICK TRAINING TEST - Reduced epochs for speed")
print("="*70)
print("\nThis will:")
print("  * Train traditional ML (full)")
print("  * Train LSTM & GRU (5 epochs only)")
print("  * Skip Prophet")
print("  * Use all available data")
print("\n" + "="*70)

tam.main()
