"""
Deep Learning and Statistical Models for Bitcoin Price Prediction

This module implements:
- LSTM (Long Short-Term Memory) neural networks
- GRU (Gated Recurrent Unit) neural networks  
- Prophet (Facebook's time series forecasting)
- Statistical models (ARIMA, SARIMA)
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Try importing deep learning libraries
try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("⚠️  TensorFlow/Keras not installed. Deep learning models unavailable.")

# Try importing Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️  Prophet not installed. Statistical forecasting unavailable.")


class DeepLearningModels:
    """Deep Learning models for time series forecasting"""
    
    def __init__(self, sequence_length=30, random_state=42):
        """
        Initialize deep learning models
        
        Args:
            sequence_length: Number of time steps to look back
            random_state: Random seed for reproducibility
        """
        self.sequence_length = sequence_length
        self.random_state = random_state
        np.random.seed(random_state)
        
        if KERAS_AVAILABLE:
            import tensorflow as tf
            tf.random.set_seed(random_state)
    
    def prepare_sequences(self, data, target=None):
        """
        Prepare sequences for RNN models (LSTM/GRU)
        
        Args:
            data: Input features (2D array: samples x features)
            target: Target values (1D array)
            
        Returns:
            X_seq: 3D array (samples, sequence_length, features)
            y_seq: Target values aligned with sequences
        """
        if len(data) <= self.sequence_length:
            raise ValueError(f"Data length {len(data)} must be > sequence_length {self.sequence_length}")
        
        X_seq = []
        y_seq = [] if target is not None else None
        
        for i in range(len(data) - self.sequence_length):
            X_seq.append(data[i:i + self.sequence_length])
            if target is not None:
                y_seq.append(target[i + self.sequence_length])
        
        X_seq = np.array(X_seq)
        
        if target is not None:
            y_seq = np.array(y_seq)
            return X_seq, y_seq
        
        return X_seq
    
    def create_lstm_model(self, input_shape, output_dim=1, task='regression'):
        """
        Create LSTM model
        
        Args:
            input_shape: (sequence_length, n_features)
            output_dim: Number of output neurons
            task: 'regression' or 'classification'
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras not installed")
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(output_dim, activation='sigmoid' if task == 'classification' else 'linear')
        ])
        
        if task == 'classification':
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
        else:
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
        
        return model
    
    def create_gru_model(self, input_shape, output_dim=1, task='regression'):
        """
        Create GRU model (faster than LSTM, often similar performance)
        
        Args:
            input_shape: (sequence_length, n_features)
            output_dim: Number of output neurons
            task: 'regression' or 'classification'
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras not installed")
        
        model = Sequential([
            GRU(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            GRU(64, return_sequences=True),
            Dropout(0.2),
            GRU(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(output_dim, activation='sigmoid' if task == 'classification' else 'linear')
        ])
        
        if task == 'classification':
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
        else:
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
        
        return model
    
    def train_rnn_model(self, model, X_train, y_train, X_val=None, y_val=None, 
                       epochs=100, batch_size=32, verbose=0):
        """
        Train RNN model (LSTM or GRU) with early stopping
        
        Args:
            model: Keras model (LSTM or GRU)
            X_train, y_train: Training data
            X_val, y_val: Validation data (optional)
            epochs: Maximum training epochs
            batch_size: Batch size
            verbose: Verbosity level (0=silent, 1=progress bar, 2=one line per epoch)
            
        Returns:
            history: Training history
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras not installed")
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=15,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        history = model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        return history


class ProphetModel:
    """Facebook Prophet for time series forecasting"""
    
    def __init__(self):
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet not installed. Install with: pip install prophet")
        
        self.model = None
    
    def prepare_data(self, df, date_col, value_col):
        """
        Prepare data for Prophet (requires 'ds' and 'y' columns)
        
        Args:
            df: DataFrame with time series data
            date_col: Name of date column
            value_col: Name of value column to predict
            
        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df[date_col]),
            'y': df[value_col]
        })
        return prophet_df
    
    def train(self, df, **kwargs):
        """
        Train Prophet model
        
        Args:
            df: DataFrame with 'ds' and 'y' columns
            **kwargs: Additional Prophet parameters
                     (yearly_seasonality, weekly_seasonality, daily_seasonality, etc.)
        """
        default_params = {
            'yearly_seasonality': True,
            'weekly_seasonality': True,
            'daily_seasonality': False,
            'changepoint_prior_scale': 0.05,
            'seasonality_prior_scale': 10.0
        }
        default_params.update(kwargs)
        
        self.model = Prophet(**default_params)
        self.model.fit(df)
        
        return self.model
    
    def predict(self, periods, freq='D'):
        """
        Make future predictions
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'H' for hourly, etc.)
            
        Returns:
            DataFrame with predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)
        
        return forecast


def create_hybrid_ensemble(traditional_pred, lstm_pred, gru_pred, prophet_pred=None, weights=None):
    """
    Create ensemble prediction from multiple model types
    
    Args:
        traditional_pred: Predictions from traditional ML (RandomForest, etc.)
        lstm_pred: Predictions from LSTM
        gru_pred: Predictions from GRU
        prophet_pred: Predictions from Prophet (optional)
        weights: Custom weights for each model (optional)
                If None, uses equal weights
    
    Returns:
        Ensemble prediction
    """
    predictions = [traditional_pred, lstm_pred, gru_pred]
    
    if prophet_pred is not None:
        predictions.append(prophet_pred)
    
    if weights is None:
        # Equal weights
        weights = [1.0 / len(predictions)] * len(predictions)
    
    ensemble = np.zeros_like(predictions[0])
    for pred, weight in zip(predictions, weights):
        ensemble += pred * weight
    
    return ensemble


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("DEEP LEARNING & STATISTICAL MODELS")
    print("="*70)
    
    print(f"\n✓ TensorFlow/Keras available: {KERAS_AVAILABLE}")
    print(f"✓ Prophet available: {PROPHET_AVAILABLE}")
    
    if KERAS_AVAILABLE:
        print("\n📊 Available Deep Learning Models:")
        print("  • LSTM (Long Short-Term Memory)")
        print("  • GRU (Gated Recurrent Unit)")
        print("\n  These models excel at:")
        print("    - Sequential pattern recognition")
        print("    - Long-term dependencies")
        print("    - Time series forecasting")
    
    if PROPHET_AVAILABLE:
        print("\n📊 Available Statistical Models:")
        print("  • Prophet (Facebook's time series model)")
        print("\n  Prophet excels at:")
        print("    - Seasonal patterns")
        print("    - Holiday effects")
        print("    - Robust to missing data")
    
    print("\n" + "="*70)
    print("To enable all models, install dependencies:")
    print("  pip install tensorflow keras prophet")
    print("="*70)
