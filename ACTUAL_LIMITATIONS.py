"""
ACTUAL LIMITATIONS - Code Evidence

This file documents REAL limitations based on source code analysis.
"""

# ============================================================================
# LIMITATION 1: CSV-Based Feature Storage (Not Real Feature Store)
# ============================================================================
# FROM: api_server.py lines 119-160
# EVIDENCE:
# - Features stored as CSV files in data/features/
# - No integration with Hopsworks, Feast, or other feature stores
# - No versioning, no historical lookup by timestamp
# - Must reload entire CSV on every request

def load_data():
    """Feature loading is CSV-based only"""
    try:
        # Try loading from raw data first (most recent daily run)
        if Path("data/raw/bitcoin_timeseries.csv").exists():
            print("Loading from data/raw/bitcoin_timeseries.csv...")
            df = pd.read_csv("data/raw/bitcoin_timeseries.csv")
        # Try loading from processed data
        elif Path("data/processed").exists():
            data_files = list(Path("data/processed").glob("*.csv"))
            if data_files:
                latest_file = sorted(data_files)[-1]  # Get latest by name
                df = pd.read_csv(latest_file)
        # Try loading from features directory
        elif Path("data/features").exists():
            feature_files = list(Path("data/features").glob("*.csv"))
            if feature_files:
                latest_file = sorted(feature_files)[-1]  # Get latest by name
                df = pd.read_csv(latest_file)
    # LIMITATION: No real-time feature lookup, no point-in-time correctness
    # LIMITATION: Must wait for hourly batch job to update features
    # LIMITATION: No feature versioning or reproducibility


# ============================================================================
# LIMITATION 2: No Concurrent Model Serving / Hot Reloading
# ============================================================================
# FROM: api_server.py lines 85-110
# EVIDENCE:
# - Global variables for models (clf_model, reg_model)
# - No model versioning infrastructure
# - No A/B testing framework
# - Models loaded once at startup, never refreshed

# Global variables - SINGLE VERSION ONLY
clf_model = None
reg_model = None
scaler = None
feature_columns = None
metadata = None

def load_models():
    """Models loaded once at startup - no hot reload"""
    global clf_model, reg_model, scaler, feature_columns, metadata
    try:
        from src.load_models_vertex_ai import load_models_from_vertex_ai
        
        clf_model, reg_model, scaler, feature_columns, metadata = load_models_from_vertex_ai()
        # LIMITATION: Restarting API required to use new models
        # LIMITATION: No gradual rollout or canary deployment
        # LIMITATION: No automatic model performance monitoring


# ============================================================================
# LIMITATION 3: Batch Training Only (No Streaming / Online Learning)
# ============================================================================
# FROM: prefect/flows/ml_pipeline.py lines 1-100
# EVIDENCE:
# - Models trained on full dataset each run (daily)
# - No streaming data ingestion
# - No online/incremental learning
# - No concept drift detection between training runs

@task(name="ingest_data", retries=2, retry_delay_seconds=10)
def ingest_data():
    """
    Ingest Bitcoin time-series data from CSV.
    
    LIMITATION: Only supports daily batch ingestion
    LIMITATION: No real-time streaming from Kafka/Pub-Sub
    LIMITATION: No incremental data loading
    """
    # Must fetch full 365 days each time
    from src.fetch_bitcoin_data import fetch_bitcoin_data
    df = fetch_bitcoin_data(days=365, vs_currency='usd')
    # LIMITATION: Can't incorporate new data without full retraining


# ============================================================================
# LIMITATION 4: No Distributed Training / Model Parallelism
# ============================================================================
# FROM: prefect/flows/ml_pipeline.py lines 301-510
# EVIDENCE:
# - All models trained sequentially
# - Single-machine only (no Spark, Ray, or distributed framework)
# - Limited to available local CPU/GPU
# - Training time increases linearly with data size

def train_regression_model(X_train, y_train, X_test, y_test, hyperparameters=None):
    """
    Train multiple regression models sequentially.
    
    LIMITATION: Sequential model training
    LIMITATION: No GPU support for tree models
    LIMITATION: Limited to single machine resources
    """
    models_to_test = {}
    
    # Model 1: Sequential
    print("\n  1. Training RandomForest Regressor...")
    rf_reg = RandomForestRegressor(n_estimators=300, max_depth=15)
    rf_reg.fit(X_train, y_train)  # Blocking - waits for completion
    # LIMITATION: Can't parallelize across clusters
    
    # Model 2: Sequential
    print("  2. Training GradientBoosting Regressor...")
    gb_reg = GradientBoostingRegressor(n_estimators=300, max_depth=8)
    gb_reg.fit(X_train, y_train)  # Blocking - waits for completion
    # LIMITATION: Must wait for each model to finish


# ============================================================================
# LIMITATION 5: Limited Feature Store - No Time Travel / Historical Lookups
# ============================================================================
# FROM: api_server.py lines 330-360
# EVIDENCE:
# - Endpoints only return current/latest data
# - No ability to query features from specific timestamp
# - No historical feature version lookup
# - Hourly snapshot workflow overwrites previous data

@app.get("/data/latest")
def get_latest_data():
    """
    Get latest feature data only.
    
    LIMITATION: Only returns current features
    LIMITATION: No historical lookups possible
    LIMITATION: Can't reconstruct training data point
    """
    df_data = load_data()
    if df_data is not None and not df_data.empty:
        latest = df_data.tail(1)  # ONLY latest row
        # LIMITATION: Can't get features from any other timestamp


# ============================================================================
# LIMITATION 6: Single Prediction Target Per Request
# ============================================================================
# FROM: api_server.py lines 280-300
# EVIDENCE:
# - /predict returns single point forecast
# - No multi-step forecasting endpoint
# - No confidence intervals or prediction intervals
# - Prophet (which supports multi-step) not exposed via API

@app.post("/predict")
def predict(input_data: FeaturesInput):
    """
    Make single prediction only.
    
    LIMITATION: Single point prediction (t+1)
    LIMITATION: No multi-step (t+1, t+2, t+3, ...) forecasting
    LIMITATION: No prediction intervals or uncertainty quantification
    LIMITATION: Prophet's multi-step capability not exposed
    """
    # Returns: {"direction": "Up", "price_change_pct": 1.23, ...}
    # LIMITATION: Only 1-day ahead, no range forecasts


# ============================================================================
# LIMITATION 7: No Model Interpretability / Explanation Cache
# ============================================================================
# FROM: api_server.py lines 515-590 (/explain endpoint)
# EVIDENCE:
# - SHAP values computed on-the-fly (expensive operation)
# - No caching of explanations
# - Slows down prediction with large datasets
# - No async computation for explanations

@app.post("/explain")
def explain(input_data: FeaturesInput):
    """
    Generate SHAP explanations on every request.
    
    LIMITATION: SHAP computed on-demand (slow)
    LIMITATION: No explanation caching
    LIMITATION: Blocking request - increases latency
    LIMITATION: Not suitable for high-throughput serving
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)  # Expensive computation
    # LIMITATION: Each request pays the SHAP cost


# ============================================================================
# LIMITATION 8: No Feature Validation / Data Quality Checks
# ============================================================================
# FROM: api_server.py - Missing validation
# EVIDENCE:
# - No schema validation for features
# - No data quality tests
# - No drift detection between training and serving
# - No alerting on anomalous feature values

class FeaturesInput(BaseModel):
    """Input model for custom features (JSON)"""
    features: Dict[str, float]  # LIMITATION: Any dict accepted
    current_price: Optional[float] = None
    # LIMITATION: No type checking beyond float
    # LIMITATION: No range validation (e.g., prices can't be negative)
    # LIMITATION: No schema version tracking


# ============================================================================
# LIMITATION 9: No Automated Retraining Trigger
# ============================================================================
# FROM: .github/workflows/scheduled-training.yml
# EVIDENCE:
# - Training runs on fixed schedule (daily)
# - No performance degradation detection
# - No automatic trigger on data drift
# - No automated model evaluation before deployment

# LIMITATION: Fixed daily schedule regardless of data quality
# LIMITATION: No "if model performance drops > X%, retrain" logic
# LIMITATION: No concept drift detection between training runs
# LIMITATION: Models deployed even if performance degraded


# ============================================================================
# LIMITATION 10: Memory Constraints for Large Batch Predictions
# ============================================================================
# FROM: api_server.py lines 620-670 (/predict/file endpoint)
# EVIDENCE:
# - Entire CSV loaded into memory
# - No streaming/chunked processing
# - Will fail for large files (GBs+)
# - No pagination or streaming response

@app.post("/predict/file")
async def predict_batch_file(file: UploadFile = File(...)):
    """
    Batch predictions - loads entire file into memory.
    
    LIMITATION: Full file loaded before processing
    LIMITATION: No streaming/chunked processing
    LIMITATION: Memory-bound (will crash on large files)
    LIMITATION: No progress tracking for long operations
    """
    contents = await file.read()  # LIMITATION: Entire file in memory
    df = pd.read_csv(io.StringIO(contents.decode()))  # All rows at once
    # LIMITATION: File size limited by available RAM


# ============================================================================
# LIMITATION 11: No Real-Time Predictions (Inference Only)
# ============================================================================
# FROM: Streamlit app.py - No streaming integration
# EVIDENCE:
# - Predictions only on manual input
# - No WebSocket support
# - No streaming predictions (e.g., every minute)
# - No integration with real-time data sources

# LIMITATION: Pull-based predictions only (user triggers)
# LIMITATION: No WebSocket for live updates
# LIMITATION: No Kafka/Pub-Sub consumer for auto-predictions
# LIMITATION: No scheduled prediction publishing


# ============================================================================
# LIMITATION 12: Classification/Regression Ensembles Not Combined
# ============================================================================
# FROM: api_server.py - /predict endpoint
# EVIDENCE:
# - Classification and regression models used independently
# - No ensemble meta-learner
# - No weighted combination of predictions
# - Predictions returned separately, not fused

@app.post("/predict")
def predict(input_data: FeaturesInput):
    """
    Separate classification and regression predictions.
    
    LIMITATION: Models not ensembled together
    LIMITATION: No meta-learner to combine predictions
    LIMITATION: No cross-model consistency checks
    LIMITATION: Could make contradictory predictions
        (e.g., "Up" direction but -5% price change)
    """
    # Returns classification AND regression separately
    # LIMITATION: No guarantee they agree on prediction direction


# ============================================================================
# SUMMARY OF ACTUAL LIMITATIONS
# ============================================================================
"""
1. CSV-Based Features (Not Real Feature Store)
   - No point-in-time feature lookups
   - No versioning or audit trail
   - Manual hourly batch jobs required

2. No Hot Model Reloading
   - Single model version at a time
   - API restart required to deploy new models
   - No A/B testing or canary deployments

3. Batch-Only Training (No Streaming)
   - Full dataset retrained daily
   - No online/incremental learning
   - No real-time model updates

4. No Distributed Training
   - Single-machine only
   - Sequential model training
   - Linear scaling with data size

5. No Feature Time Travel
   - Only current features accessible
   - Can't replay historical predictions
   - No reproducibility of past training data

6. Single-Step Forecasting Only
   - Returns 1-day ahead prediction
   - No multi-step forecasting
   - No prediction intervals

7. No Explanation Caching
   - SHAP values computed on-demand
   - Expensive per-request computation
   - High latency for interpretability

8. No Data Quality Framework
   - No feature validation
   - No drift detection
   - No data schema enforcement

9. No Automated Retraining Triggers
   - Fixed daily schedule only
   - No performance-based retraining
   - No concept drift detection

10. Memory-Bound Batch Processing
    - Entire files loaded into memory
    - No chunked/streaming processing
    - Limited by available RAM

11. No Real-Time Inference
    - Pull-based predictions only
    - No WebSocket or streaming
    - No scheduled prediction publishing

12. Models Not Ensembled
    - Classification and regression separate
    - No meta-learner combining predictions
    - Possible prediction contradictions
"""
