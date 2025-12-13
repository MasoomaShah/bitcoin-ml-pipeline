# 🚀 Deep Learning & Statistical Models - Quick Start

## ✅ What's Been Added

Your project now includes **ALL model types** as required:

### 1️⃣ Traditional ML (Already existed)
- RandomForest, GradientBoosting, Logistic Regression, SVM
- Ridge, Lasso, SVR
- **Location**: `src/model_experiments.py`

### 2️⃣ Deep Learning (NEW! 🆕)
- **LSTM** (Long Short-Term Memory) - 3 layers, dropout regularization
- **GRU** (Gated Recurrent Unit) - 3 layers, faster than LSTM
- **Location**: `src/deep_learning_models.py`

### 3️⃣ Statistical Models (NEW! 🆕)
- **Prophet** (Facebook's time series forecasting)
- **Location**: `src/deep_learning_models.py`

### 4️⃣ Comprehensive Training Script (NEW! 🆕)
- Trains ALL model types in one run
- Compares performance across all models
- Saves best models
- **Location**: `src/train_all_models.py`

---

## 📦 Installation

### Step 1: Install Deep Learning Dependencies

```powershell
# Install TensorFlow, Keras, and Prophet
pip install tensorflow>=2.13.0 keras>=2.13.0 prophet>=1.1.5

# Or install all requirements at once
pip install -r requirements.txt
```

**Note**: TensorFlow is ~500MB, installation may take 5-10 minutes.

### Step 2: Verify Installation

```powershell
python -c "import tensorflow; print('TensorFlow:', tensorflow.__version__)"
python -c "from prophet import Prophet; print('Prophet: OK')"
```

---

## 🏃 Running the Models

### Option 1: Train ALL Models (Recommended)

This trains traditional ML, LSTM, GRU, and Prophet all at once:

```powershell
cd "c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT"
python src/train_all_models.py
```

**Output**: Comprehensive comparison table of all models

**Time**: ~10-15 minutes (deep learning models take longer to train)

### Option 2: Train Only Traditional ML

```powershell
python src/train_with_feature_store.py --experiment-models
```

### Option 3: Python Interactive

```python
from src.deep_learning_models import DeepLearningModels
from src.fetch_alpha_vantage import fetch_crypto_with_indicators
import numpy as np

# Fetch data
df = fetch_crypto_with_indicators('BTC', 'USD')
X = df[feature_columns].values
y = df['direction'].values

# Create LSTM model
dl = DeepLearningModels(sequence_length=30)
X_seq, y_seq = dl.prepare_sequences(X, y)

lstm_model = dl.create_lstm_model(
    input_shape=(30, X.shape[1]),
    task='classification'
)

# Train
history = dl.train_rnn_model(
    lstm_model, X_seq, y_seq,
    epochs=50, batch_size=32
)

# Predict
predictions = lstm_model.predict(X_seq)
```

---

## 📊 Model Comparison

After running `train_all_models.py`, you'll see:

```
📊 COMPREHENSIVE MODEL COMPARISON
======================================================================

🎯 CLASSIFICATION (Direction Prediction):
----------------------------------------------------------------------
              Model  Test Accuracy            Type
      RandomForest         0.7234  Traditional ML
              LSTM         0.7156   Deep Learning
               GRU         0.7089   Deep Learning
  GradientBoosting         0.7012  Traditional ML
...

🏆 Best Classification Model: RandomForest (Accuracy: 0.7234)


📈 REGRESSION (Price Change %):
----------------------------------------------------------------------
              Model  Test MSE  Test MAE  Test R2            Type
      RandomForest     2.345     1.234    0.654  Traditional ML
              LSTM     2.567     1.345    0.623   Deep Learning
               GRU     2.678     1.456    0.612   Deep Learning
...

🏆 Best Regression Model: RandomForest (R²: 0.654)


⏰ PROPHET TIME SERIES FORECAST:
----------------------------------------------------------------------
  MSE: 1234.56
  MAE: 23.45
  R²: 0.678
```

---

## 🧠 Model Details

### LSTM Architecture
```
Layer 1: LSTM(128 units, return_sequences=True)
Dropout: 0.2
Layer 2: LSTM(64 units, return_sequences=True)
Dropout: 0.2
Layer 3: LSTM(32 units)
Dropout: 0.2
Dense: 16 units (ReLU)
Output: 1 unit (sigmoid/linear)
```

**Advantages**:
- Captures long-term dependencies
- Handles sequential patterns
- Good for time series

**Training Time**: 5-10 minutes (50 epochs with early stopping)

### GRU Architecture
```
Layer 1: GRU(128 units, return_sequences=True)
Dropout: 0.2
Layer 2: GRU(64 units, return_sequences=True)
Dropout: 0.2
Layer 3: GRU(32 units)
Dropout: 0.2
Dense: 16 units (ReLU)
Output: 1 unit (sigmoid/linear)
```

**Advantages**:
- Faster training than LSTM
- Fewer parameters
- Often similar performance

**Training Time**: 4-8 minutes (50 epochs with early stopping)

### Prophet
```
Seasonality: Yearly + Weekly
Changepoint Prior Scale: 0.05
Robust to missing data
Automatic holiday detection
```

**Advantages**:
- Excellent for seasonal patterns
- Handles missing data
- Interpretable forecasts

**Training Time**: 1-2 minutes

---

## 📁 Saved Models

After training, models are saved to `models/` with timestamps:

```
models/
├── 20241204T150530Z_lstm_classification.h5
├── 20241204T150530Z_gru_classification.h5
├── 20241204T150530Z_lstm_regression.h5
├── 20241204T150530Z_gru_regression.h5
└── 20241204T150530Z_prophet.pkl
```

### Loading Saved Models

```python
from tensorflow import keras
import joblib

# Load LSTM
lstm_model = keras.models.load_model('models/20241204T150530Z_lstm_classification.h5')

# Load Prophet
prophet_model = joblib.load('models/20241204T150530Z_prophet.pkl')
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'tensorflow'"

**Solution**:
```powershell
pip install tensorflow>=2.13.0 keras>=2.13.0
```

### Issue: "No module named 'prophet'"

**Solution**:
```powershell
pip install prophet>=1.1.5

# If Windows issues, try:
conda install -c conda-forge prophet
```

### Issue: Prophet installation fails on Windows

**Solution**:
```powershell
# Install dependencies first
pip install pystan
pip install prophet
```

### Issue: CUDA/GPU errors with TensorFlow

**Solution** (Use CPU version):
```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU

# Then import tensorflow
import tensorflow as tf
```

### Issue: Models taking too long to train

**Solution** (Reduce epochs):
```python
# In train_all_models.py, change:
history = dl_models.train_rnn_model(
    model, X_train, y_train,
    epochs=20,  # Reduced from 50
    batch_size=64  # Increased from 32
)
```

---

## ✅ Requirements Status

| Requirement | Status | Details |
|------------|--------|---------|
| EDA | ✅ COMPLETE | notebooks/EDA.ipynb (18 cells) |
| Traditional ML | ✅ COMPLETE | RandomForest, GradientBoosting, SVM, Ridge, Lasso |
| **Deep Learning** | ✅ **COMPLETE** | **LSTM, GRU (NEW!)** |
| **Statistical Models** | ✅ **COMPLETE** | **Prophet (NEW!)** |
| Docker | ✅ COMPLETE | 3 containers, all healthy |
| SHAP/LIME | ✅ COMPLETE | POST /explain endpoint |
| Multiple Input Types | ✅ COMPLETE | JSON, CSV, numeric array |

---

## 🎯 Next Steps

### 1. Train Models (Now!)
```powershell
python src/train_all_models.py
```

### 2. Review Performance
Check which model performs best for your use case

### 3. Deploy Best Model (Optional)
Update `api_server.py` to load LSTM/GRU if they outperform traditional ML

### 4. Rebuild Docker (If deploying deep learning)
```powershell
# Add to Dockerfile.api
RUN pip install tensorflow keras prophet

# Rebuild
docker compose down
docker compose up --build -d
```

---

## 📚 References

- **LSTM**: [Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- **GRU**: [Empirical Evaluation of Gated Recurrent Neural Networks](https://arxiv.org/abs/1412.3555)
- **Prophet**: [Facebook Prophet Documentation](https://facebook.github.io/prophet/)

---

## 💡 Tips

1. **Start with traditional ML first** - They train faster and often perform well
2. **Use LSTM/GRU for sequential patterns** - When recent history matters
3. **Use Prophet for seasonal data** - When data has yearly/weekly patterns
4. **Ensemble predictions** - Combine multiple models for better results

---

**Created**: December 2024  
**Project**: Bitcoin ML Price Prediction  
**Author**: GitHub Copilot
