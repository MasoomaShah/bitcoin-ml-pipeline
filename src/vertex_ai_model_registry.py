"""
Vertex AI Model Registry Integration
Uploads and manages models in Google Cloud Vertex AI Model Registry
"""

import os
import joblib
import json
from datetime import datetime
from typing import Dict, Optional
from google.cloud import aiplatform
from google.cloud.aiplatform import Model


class VertexAIModelRegistry:
    """Manages models in Vertex AI Model Registry"""
    
    def __init__(
        self,
        project_id: str = "ml-project-480417",
        region: str = "us-central1",
        staging_bucket: Optional[str] = None
    ):
        """
        Initialize Vertex AI Model Registry
        
        Args:
            project_id: GCP project ID
            region: GCP region
            staging_bucket: GCS bucket for model artifacts (optional)
        """
        self.project_id = project_id
        self.region = region
        self.staging_bucket = staging_bucket or f"gs://{project_id}-models"
        
        # Initialize Vertex AI
        aiplatform.init(
            project=project_id,
            location=region,
            staging_bucket=self.staging_bucket
        )
        
        print(f"✓ Initialized Vertex AI Model Registry")
        print(f"  Project: {project_id}")
        print(f"  Region: {region}")
    
    def upload_model(
        self,
        model_path: str,
        display_name: str,
        description: str,
        metrics: Dict,
        labels: Optional[Dict] = None,
        model_type: str = "classification"
    ) -> Model:
        """
        Upload a model to Vertex AI Model Registry
        
        Args:
            model_path: Local path to pickled model file
            display_name: Display name in Model Registry
            description: Model description
            metrics: Dictionary of model metrics
            labels: Optional labels for the model
            model_type: Type of model (classification or regression)
            
        Returns:
            Uploaded Model object
        """
        try:
            print(f"\nUploading model to Vertex AI Model Registry...")
            print(f"  Display Name: {display_name}")
            print(f"  Type: {model_type}")
            
            # Create labels with metrics
            model_labels = labels or {}
            model_labels.update({
                'model_type': model_type.lower(),
                'framework': 'scikit_learn',
                'uploaded_at': datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            })
            
            # Format metrics for description
            metrics_str = "\n".join([f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}" 
                                    for k, v in metrics.items()])
            full_description = f"{description}\n\nMetrics:\n{metrics_str}"
            
            # Vertex AI requires artifact_uri to be a directory containing model.pkl or model.joblib
            # Create a model directory and copy the model file with correct name
            import shutil
            model_dir = model_path.replace('.pkl', '_artifacts')
            os.makedirs(model_dir, exist_ok=True)
            
            # Copy model file to artifacts directory with standard name
            model_artifact_path = os.path.join(model_dir, 'model.pkl')
            shutil.copy2(model_path, model_artifact_path)
            
            print(f"  Created artifacts directory: {model_dir}")
            
            # Upload model
            model = aiplatform.Model.upload(
                display_name=display_name,
                artifact_uri=model_dir,  # Directory containing model artifacts
                serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
                description=full_description,
                labels=model_labels
            )
            
            print(f"✓ Model uploaded successfully")
            print(f"  Model ID: {model.name}")
            print(f"  Resource Name: {model.resource_name}")
            
            return model
            
        except Exception as e:
            print(f"✗ Failed to upload model: {str(e)}")
            raise
    
    def upload_model_with_artifacts(
        self,
        clf_model_path: str,
        reg_model_path: str,
        scaler_path: str,
        feature_columns_path: str,
        metadata_path: str,
        version: str,
        clf_metrics: Dict,
        reg_metrics: Dict
    ) -> Dict:
        """
        Upload complete model package with all artifacts
        
        Args:
            clf_model_path: Path to classification model
            reg_model_path: Path to regression model
            scaler_path: Path to scaler
            feature_columns_path: Path to feature columns JSON
            metadata_path: Path to metadata JSON
            version: Model version string
            clf_metrics: Classification metrics
            reg_metrics: Regression metrics
            
        Returns:
            Dictionary with upload results
        """
        results = {}
        
        try:
            # Upload classification model
            print("\n" + "="*60)
            print("UPLOADING CLASSIFICATION MODEL")
            print("="*60)
            
            clf_display_name = f"bitcoin_price_classifier_{version}"
            clf_description = f"Bitcoin price direction classifier (version {version})"
            
            clf_model = self.upload_model(
                model_path=clf_model_path,
                display_name=clf_display_name,
                description=clf_description,
                metrics=clf_metrics,
                model_type="classification",
                labels={'version': version.replace('v', '').replace('T', '_').replace('Z', '')}
            )
            
            results['classification'] = {
                'model': clf_model,
                'model_id': clf_model.name,
                'resource_name': clf_model.resource_name
            }
            
            # Upload regression model
            print("\n" + "="*60)
            print("UPLOADING REGRESSION MODEL")
            print("="*60)
            
            reg_display_name = f"bitcoin_price_regressor_{version}"
            reg_description = f"Bitcoin price regressor (version {version})"
            
            reg_model = self.upload_model(
                model_path=reg_model_path,
                display_name=reg_display_name,
                description=reg_description,
                metrics=reg_metrics,
                model_type="regression",
                labels={'version': version.replace('v', '').replace('T', '_').replace('Z', '')}
            )
            
            results['regression'] = {
                'model': reg_model,
                'model_id': reg_model.name,
                'resource_name': reg_model.resource_name
            }
            
            print("\n" + "="*60)
            print("✓ ALL MODELS UPLOADED TO VERTEX AI MODEL REGISTRY")
            print("="*60)
            
            # Print summary
            print(f"\nClassification Model: {clf_display_name}")
            print(f"  Accuracy: {clf_metrics.get('accuracy', 0):.4f}")
            print(f"  Model ID: {results['classification']['model_id']}")
            
            print(f"\nRegression Model: {reg_display_name}")
            print(f"  R²: {reg_metrics.get('r2', 0):.4f}")
            print(f"  Model ID: {results['regression']['model_id']}")
            
            # Save registry info to local file
            registry_info_path = metadata_path.replace('_training_metadata.json', '_registry_info.json')
            registry_info = {
                'classification': {
                    'model_id': results['classification']['model_id'],
                    'resource_name': results['classification']['resource_name'],
                    'display_name': clf_display_name,
                    'metrics': clf_metrics
                },
                'regression': {
                    'model_id': results['regression']['model_id'],
                    'resource_name': results['regression']['resource_name'],
                    'display_name': reg_display_name,
                    'metrics': reg_metrics
                },
                'uploaded_at': datetime.utcnow().isoformat(),
                'version': version
            }
            
            with open(registry_info_path, 'w') as f:
                json.dump(registry_info, f, indent=2)
            
            print(f"\n✓ Registry info saved: {registry_info_path}")
            
            return results
            
        except Exception as e:
            print(f"\n✗ Failed to upload models to registry: {str(e)}")
            import traceback
            traceback.print_exc()
            return results
    
    def list_models(self, filter_str: Optional[str] = None):
        """List models in the registry"""
        try:
            models = aiplatform.Model.list(filter=filter_str)
            
            print(f"\nModels in Registry:")
            print("="*60)
            
            for model in models:
                print(f"\n{model.display_name}")
                print(f"  ID: {model.name}")
                print(f"  Created: {model.create_time}")
                print(f"  Labels: {model.labels}")
            
            return models
            
        except Exception as e:
            print(f"✗ Failed to list models: {str(e)}")
            return []
    
    def get_model(self, model_id: str) -> Optional[Model]:
        """Get a specific model from the registry"""
        try:
            model = aiplatform.Model(model_id)
            print(f"✓ Retrieved model: {model.display_name}")
            return model
        except Exception as e:
            print(f"✗ Failed to get model: {str(e)}")
            return None
    
    def delete_model(self, model_id: str):
        """Delete a model from the registry"""
        try:
            model = aiplatform.Model(model_id)
            model.delete()
            print(f"✓ Deleted model: {model_id}")
        except Exception as e:
            print(f"✗ Failed to delete model: {str(e)}")


def test_model_registry():
    """Test the model registry integration"""
    print("Testing Vertex AI Model Registry...")
    print()
    
    try:
        registry = VertexAIModelRegistry()
        
        # List models
        registry.list_models(filter_str="labels.model_type:classification")
        
        print("\n✓ Model Registry Working!")
        
    except Exception as e:
        print(f"✗ Model Registry Test Failed: {str(e)}")


if __name__ == "__main__":
    test_model_registry()
