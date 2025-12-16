"""
Load models and data from Vertex AI Feature Store and Model Registry
"""

import os
import json
import joblib
import warnings
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# Suppress warnings
warnings.filterwarnings('ignore')


def load_models_from_vertex_ai(version: str = None) -> Tuple[object, object, object, List[str], Dict]:
    """
    Load models and features from Vertex AI (Feature Store + Model Registry)
    
    Args:
        version: Model version string (e.g., 'v20251215T121115Z')
        
    Returns:
        Tuple of (clf_model, reg_model, scaler, feature_columns, metadata)
    """
    
    try:
        from google.cloud import aiplatform, storage
        from src.vertex_ai_feature_store import VertexAIFeatureStore
        
        # Initialize Vertex AI
        project_id = os.getenv('GCP_PROJECT_ID', 'ml-project-480417')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        print(f"🔄 Loading from Vertex AI Feature Store and Model Registry...")
        print(f"   Project: {project_id} | Region: {region}")
        
        aiplatform.init(project=project_id, location=region)
        
        # Step 1: Load features from Feature Store
        print(f"\n📥 STEP 1: Retrieving features from Vertex AI Feature Store")
        feature_store = VertexAIFeatureStore()
        
        if feature_store.connect():
            feature_columns = feature_store.get_feature_list()
            if feature_columns:
                print(f"✅ Retrieved {len(feature_columns)} features from Feature Store")
                print(f"   Features: {feature_columns[:5]}... (showing first 5)")
            else:
                print(f"⚠️  No features found in Feature Store. Using local.")
                return load_models_from_local(version)
        else:
            print(f"⚠️  Could not connect to Feature Store. Using local fallback.")
            return load_models_from_local(version)
        
        # Step 2: Load models from Cloud Storage (via Model Registry)
        print(f"\n📥 STEP 2: Loading models from Vertex AI Model Registry")
        
        # Get model directory from Cloud Storage
        storage_client = storage.Client(project=project_id)
        bucket_name = os.getenv('GCP_BUCKET', f"{project_id}-ml-models")
        
        try:
            bucket = storage_client.bucket(bucket_name)
            
            # Get latest version if not specified
            if not version:
                blobs = list(bucket.list_blobs(prefix="models/"))
                manifest_blob = bucket.blob("models/manifest.json")
                
                if manifest_blob.exists():
                    manifest_json = manifest_blob.download_as_string()
                    manifest = json.loads(manifest_json)
                    version = manifest.get('active_version')
                    print(f"📌 Found active version from Cloud Storage: {version}")
            
            if not version:
                print(f"⚠️  No model version found. Using local fallback.")
                return load_models_from_local(version)
            
            # Download models from Cloud Storage
            print(f"   Downloading models version: {version}")
            
            clf_blob = bucket.blob(f"models/{version}_clf_model.pkl")
            reg_blob = bucket.blob(f"models/{version}_reg_model.pkl")
            scaler_blob = bucket.blob(f"models/{version}_scaler.pkl")
            metadata_blob = bucket.blob(f"models/{version}_training_metadata.json")
            
            if clf_blob.exists() and reg_blob.exists() and scaler_blob.exists():
                # Download to temporary location
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    clf_path = Path(tmpdir) / "clf_model.pkl"
                    reg_path = Path(tmpdir) / "reg_model.pkl"
                    scaler_path = Path(tmpdir) / "scaler.pkl"
                    metadata_path = Path(tmpdir) / "metadata.json"
                    
                    clf_blob.download_to_filename(str(clf_path))
                    reg_blob.download_to_filename(str(reg_path))
                    scaler_blob.download_to_filename(str(scaler_path))
                    
                    # Load into memory
                    clf_model = joblib.load(str(clf_path))
                    reg_model = joblib.load(str(reg_path))
                    scaler = joblib.load(str(scaler_path))
                    
                    # Load metadata
                    if metadata_blob.exists():
                        metadata_json = metadata_blob.download_as_string()
                        metadata = json.loads(metadata_json)
                    else:
                        metadata = {'version': version}
                    
                    print(f"✅ Models loaded from Cloud Storage")
                    print(f"   Classification: {type(clf_model).__name__}")
                    print(f"   Regression: {type(reg_model).__name__}")
                    print(f"   Features: {len(feature_columns)}")
                    
                    return clf_model, reg_model, scaler, feature_columns, metadata
            else:
                print(f"⚠️  Model files not found in Cloud Storage. Using local fallback.")
                return load_models_from_local(version)
                
        except Exception as e:
            print(f"⚠️  Could not load from Cloud Storage: {e}")
            print(f"   Falling back to local files...")
            return load_models_from_local(version)
        
    except ImportError as e:
        print(f"⚠️  Required packages not installed: {e}")
        print(f"   Install with: pip install google-cloud-aiplatform google-cloud-storage")
        print(f"   Falling back to local model files...")
        return load_models_from_local(version)
    except Exception as e:
        print(f"⚠️  Could not load from Vertex AI: {e}")
        print(f"   Falling back to local model files...")
        return load_models_from_local(version)


def load_models_from_local(version: str = None) -> Tuple[object, object, object, List[str], Dict]:
    """
    Load models from local files
    
    Args:
        version: Model version string
        
    Returns:
        Tuple of (clf_model, reg_model, scaler, feature_columns, metadata)
    """
    
    try:
        models_dir = Path("models")
        
        # If no version specified, read from manifest
        if version is None:
            manifest_path = models_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                if 'active_version' in manifest:
                    version = manifest['active_version']
                elif 'models' in manifest and manifest['models']:
                    version = manifest['models'][0]['version']
                else:
                    raise ValueError("Could not determine active model version from manifest")
            else:
                raise FileNotFoundError(f"Manifest not found at {manifest_path}")
        
        print(f"Loading models from local files (version: {version})...")
        
        # Load models
        clf_model = joblib.load(models_dir / f"{version}_clf_model.pkl")
        reg_model = joblib.load(models_dir / f"{version}_reg_model.pkl")
        scaler = joblib.load(models_dir / f"{version}_scaler.pkl")
        
        with open(models_dir / f"{version}_feature_columns.json", 'r') as f:
            feature_columns = json.load(f)
        
        with open(models_dir / f"{version}_training_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        print(f"[OK] Loaded {version}")
        print(f"  Classification model: {type(clf_model).__name__}")
        print(f"  Regression model: {type(reg_model).__name__}")
        print(f"  Features: {len(feature_columns)}")
        
        return clf_model, reg_model, scaler, feature_columns, metadata
        
    except Exception as e:
        print(f"[ERROR] Failed to load models: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None


if __name__ == "__main__":
    # Test
    print("=" * 60)
    print("Testing model loading...")
    print("=" * 60)
    
    clf, reg, scaler, features, metadata = load_models_from_vertex_ai()
    
    if clf is not None:
        print(f"\n[OK] Successfully loaded models")
        print(f"  Classification: {type(clf)}")
        print(f"  Regression: {type(reg)}")
    else:
        print(f"\n[ERROR] Failed to load models")
