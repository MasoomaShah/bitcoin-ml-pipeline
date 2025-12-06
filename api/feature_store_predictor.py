"""
API Enhancement: Feature Store Integration for Real-time Inference
Fetches features from Hopsworks for low-latency predictions
"""

import os
import sys
from typing import Dict, Optional
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_store import BitcoinFeatureStore


class FeatureStorePredictor:
    """
    Prediction service with feature store integration
    """
    
    def __init__(self, use_feature_store: bool = True):
        """
        Initialize predictor with optional feature store
        
        Args:
            use_feature_store: If True, use Hopsworks; else compute features locally
        """
        self.use_feature_store = use_feature_store
        self.fs = None
        self.feature_view = None
        
        if use_feature_store:
            self._initialize_feature_store()
    
    def _initialize_feature_store(self):
        """Initialize connection to Hopsworks feature store"""
        try:
            self.fs = BitcoinFeatureStore()
            if self.fs.connect():
                self.feature_view = self.fs.create_feature_view(
                    name="bitcoin_training_view",
                    version=1
                )
                # Initialize online serving
                self.feature_view.init_serving()
                print("✓ Feature store initialized for online serving")
            else:
                print("⚠️ Feature store connection failed, will compute features locally")
                self.use_feature_store = False
        except Exception as e:
            print(f"⚠️ Feature store initialization failed: {str(e)}")
            self.use_feature_store = False
    
    def get_features_for_prediction(
        self,
        input_data: Dict
    ) -> pd.DataFrame:
        """
        Get features for prediction (from feature store or local computation)
        
        Args:
            input_data: Input data dictionary with OHLCV values
            
        Returns:
            DataFrame with features ready for model inference
        """
        if self.use_feature_store and self.feature_view:
            return self._get_online_features(input_data)
        else:
            return self._compute_features_locally(input_data)
    
    def _get_online_features(self, input_data: Dict) -> pd.DataFrame:
        """
        Fetch features from Hopsworks online feature store
        
        Args:
            input_data: Primary key values to lookup features
            
        Returns:
            DataFrame with features from feature store
        """
        try:
            # Extract timestamp or use current time
            timestamp = input_data.get('timestamp', pd.Timestamp.now())
            
            # Get feature vector from online store
            features = self.feature_view.get_feature_vector(
                {'timestamp': timestamp}
            )
            
            # Convert to DataFrame
            features_df = pd.DataFrame([features])
            
            # Remove metadata columns
            drop_cols = ['timestamp', 'ingestion_time', 'pipeline_version', 'target']
            features_df = features_df.drop(
                [c for c in drop_cols if c in features_df.columns],
                axis=1
            )
            
            return features_df
            
        except Exception as e:
            print(f"⚠️ Online feature retrieval failed: {str(e)}")
            print("   Falling back to local computation")
            return self._compute_features_locally(input_data)
    
    def _compute_features_locally(self, input_data: Dict) -> pd.DataFrame:
        """
        Compute features locally from raw input
        
        Args:
            input_data: Dictionary with OHLCV values
            
        Returns:
            DataFrame with computed features
        """
        from src.feature_engineering import engineer_features
        
        # Convert input to DataFrame
        if isinstance(input_data, dict):
            input_df = pd.DataFrame([input_data])
        else:
            input_df = input_data
        
        # Compute features
        features_df = engineer_features(input_df)
        
        # Remove target column if exists
        if 'target' in features_df.columns:
            features_df = features_df.drop('target', axis=1)
        
        return features_df


# Integration with existing API
def enhance_api_with_feature_store():
    """
    Update FastAPI endpoints to use feature store
    Add this to api/main.py
    """
    enhancement_code = '''
# Add to api/main.py imports:
from api.feature_store_predictor import FeatureStorePredictor

# Initialize at startup:
feature_store_predictor = FeatureStorePredictor(
    use_feature_store=os.getenv('USE_FEATURE_STORE', 'false').lower() == 'true'
)

# Update predict endpoint:
@app.post("/predict")
async def predict(input_data: PredictionInput):
    """Predict Bitcoin price direction with feature store integration"""
    try:
        # Get features from feature store or compute locally
        features_df = feature_store_predictor.get_features_for_prediction(
            input_data.dict()
        )
        
        # Scale features
        features_scaled = scaler.transform(features_df)
        
        # Make predictions
        clf_pred = clf_model.predict(features_scaled)[0]
        reg_pred = reg_model.predict(features_scaled)[0]
        
        return {
            "classification": {
                "prediction": int(clf_pred),
                "direction": "UP" if clf_pred == 1 else "DOWN"
            },
            "regression": {
                "price_change_pct": float(reg_pred)
            },
            "feature_source": "feature_store" if feature_store_predictor.use_feature_store else "computed",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
    return enhancement_code


if __name__ == "__main__":
    # Test feature store predictor
    print("Testing Feature Store Predictor...\n")
    
    predictor = FeatureStorePredictor(use_feature_store=True)
    
    # Test input
    test_input = {
        'open': 50000.0,
        'high': 51000.0,
        'low': 49500.0,
        'close': 50500.0,
        'volume': 1000000.0,
        'timestamp': pd.Timestamp.now()
    }
    
    print("Test Input:")
    print(test_input)
    print()
    
    try:
        features = predictor.get_features_for_prediction(test_input)
        print(f"✓ Retrieved {len(features.columns)} features")
        print(f"  Feature names: {list(features.columns)[:10]}...")
        print(f"  Feature source: {'Hopsworks' if predictor.use_feature_store else 'Local'}")
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
