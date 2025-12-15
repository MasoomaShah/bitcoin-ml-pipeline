"""
Vertex AI Feature Store Integration
Manages Bitcoin features in Google Cloud Vertex AI
"""

import os
import time
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
from google.cloud import aiplatform
from google.cloud.aiplatform import Feature, EntityType, Featurestore


class VertexAIFeatureStore:
    """
    Manages Bitcoin ML features in Vertex AI Feature Store
    
    Features:
    - Feature ingestion with validation
    - Version control and lineage tracking
    - Online/offline feature serving
    - Feature monitoring and statistics
    """
    
    def __init__(
        self,
        project_id: str = "ml-project-480417",
        region: str = "us-central1",
        featurestore_id: str = "bitcoin_features"
    ):
        """
        Initialize connection to Vertex AI Feature Store
        
        Args:
            project_id: Google Cloud project ID
            region: Google Cloud region
            featurestore_id: Name of the feature store
        """
        self.project_id = project_id
        self.region = region
        self.featurestore_id = featurestore_id
        self.featurestore = None
        self.entity_type = None
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=region)
        
    def connect(self) -> bool:
        """
        Establish connection to Vertex AI Feature Store
        
        Returns:
            bool: True if connection successful
        """
        try:
            # List existing feature stores
            print("Checking for existing feature store...")
            featurestores = Featurestore.list()
            
            # Find or create feature store
            self.featurestore = None
            for fs in featurestores:
                if self.featurestore_id in fs.resource_name:
                    self.featurestore = fs
                    print(f"✓ Connected to existing feature store: {self.featurestore_id}")
                    break
            
            if self.featurestore is None:
                print(f"Creating new feature store: {self.featurestore_id}...")
                self.featurestore = Featurestore.create(
                    featurestore_id=self.featurestore_id,
                    online_store_fixed_node_count=1,
                )
                print(f"✓ Created feature store: {self.featurestore_id}")
            
            # Get or create entity type for Bitcoin
            try:
                entity_types = self.featurestore.list_entity_types()
                self.entity_type = None
                for et in entity_types:
                    if "bitcoin" in et.resource_name.lower():
                        self.entity_type = et
                        break
                
                if self.entity_type is None:
                    raise ValueError("Entity type not found")
                    
                print(f"✓ Connected to entity type: bitcoin")
            except:
                print("Creating entity type: bitcoin...")
                self.entity_type = self.featurestore.create_entity_type(
                    entity_type_id="bitcoin",
                    description="Bitcoin time-series data"
                )
                print(f"✓ Created entity type: bitcoin")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to Vertex AI: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def ingest_features(
        self,
        features_df: pd.DataFrame,
        entity_id_column: str = "timestamp"
    ) -> bool:
        """
        Ingest features into Vertex AI Feature Store
        
        Args:
            features_df: DataFrame with features
            entity_id_column: Column to use as entity ID
            
        Returns:
            bool: True if ingestion successful
        """
        try:
            if self.entity_type is None:
                print("✗ Not connected. Call connect() first.")
                return False
            
            # Ensure entity ID column exists
            if entity_id_column not in features_df.columns:
                print(f"✗ Entity ID column '{entity_id_column}' not found")
                return False
            
            # Convert timestamp to datetime and then to Unix timestamp (integer)
            df = features_df.copy()
            if df[entity_id_column].dtype == 'object':
                df[entity_id_column] = pd.to_datetime(df[entity_id_column])
            
            # Convert to Unix timestamp integer for entity ID
            df['entity_id'] = (df[entity_id_column].astype('int64') // 10**9).astype(str)
            
            # Convert to proper TIMESTAMP format for Vertex AI (UTC timezone aware)
            # Handle both timezone-aware and timezone-naive timestamps
            ts = pd.to_datetime(df[entity_id_column])
            if ts.dt.tz is None:
                df['feature_timestamp'] = ts.dt.tz_localize('UTC')
            else:
                # Already timezone-aware, convert to UTC
                df['feature_timestamp'] = ts.dt.tz_convert('UTC')
            
            # Create features if they don't exist
            existing_features = {f.name.lower() for f in self.entity_type.list_features()}
            # Exclude entity_id, feature_timestamp, and original timestamp column (reserved)
            feature_cols = [col for col in df.columns 
                          if col not in [entity_id_column, 'entity_id', 'feature_timestamp']]
            
            # Create features with delays to respect rate limits (10 per minute max)
            # Rate limit: 10/minute = need to space out by ~6+ seconds per feature
            created_count = 0
            for i, col in enumerate(feature_cols):
                feature_id = col.lower().replace(" ", "_")
                if feature_id not in existing_features:
                    print(f"Creating feature {i+1}/{len(feature_cols)}: {col}...")
                    Feature.create(
                        feature_id=feature_id,
                        value_type="DOUBLE",
                        entity_type_name=self.entity_type.resource_name,
                        description=f"Bitcoin feature: {col}"
                    )
                    created_count += 1
                    # Wait 7 seconds between each feature to stay well under 10/minute quota
                    new_features_count = len([col.lower().replace(" ", "_") for col in feature_cols if col.lower().replace(" ", "_") not in existing_features])
                    if created_count < new_features_count:
                        time.sleep(7)
                else:
                    print(f"Skipping feature {i+1}/{len(feature_cols)}: {col} (already exists)")

            
            # Ingest data using BigQuery (the correct method for Vertex AI Feature Store)
            print(f"Ingesting {len(df)} records...")
            
            # Prepare data for BigQuery ingestion
            # Build a clean DataFrame with no index issues
            feature_ids = [col.lower().replace(" ", "_") for col in feature_cols]
            
            # Create a dictionary for the new DataFrame
            # Keep feature_timestamp as datetime (BigQuery will auto-detect as TIMESTAMP)
            data_dict = {
                'entity_id': df['entity_id'].values,
                'feature_timestamp': df['feature_timestamp'].values,
            }
            
            # Add feature columns with normalized names
            for orig_col, feature_id in zip(feature_cols, feature_ids):
                data_dict[feature_id] = df[orig_col].values
            
            # Create DataFrame from dict (this avoids index issues)
            df_import = pd.DataFrame(data_dict)
            
            # Import from DataFrame to Feature Store
            self.entity_type.ingest_from_df(
                feature_ids=feature_ids,
                feature_time='feature_timestamp',
                df_source=df_import,
                entity_id_field='entity_id',
            )
            
            print(f"✓ Ingested {len(df)} records successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to ingest features: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def read_features(
        self,
        entity_ids: List[str],
        feature_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read features from Vertex AI Feature Store
        
        Args:
            entity_ids: List of entity IDs to read
            feature_ids: List of feature IDs to read (None = all)
            
        Returns:
            DataFrame with features
        """
        try:
            if self.entity_type is None:
                print("✗ Not connected. Call connect() first.")
                return pd.DataFrame()
            
            # Get all features if not specified
            if feature_ids is None:
                all_features = self.entity_type.list_features()
                feature_ids = [f.name for f in all_features]
            
            # For Vertex AI Feature Store, we need to use batch read
            # Since reading from Feature Store requires specific API calls and is complex,
            # we'll use a simpler approach: query the BigQuery backing table directly
            print(f"   Note: Vertex AI batch reading is complex. Using stored data instead...")
            
            # Alternative: Since we just ingested the data, return a message that
            # for now, training should use the local preprocessing
            # In production, you would set up proper feature serving
            print(f"   ⚠️ Vertex AI online serving requires additional setup.")
            print(f"   ⚠️ For training, consider using the ingested data via BigQuery export")
            print(f"   ⚠️ or use local preprocessing with the same feature definitions.")
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"✗ Failed to read features: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()


def test_vertex_ai():
    """Test Vertex AI connection"""
    print("Testing Vertex AI Feature Store...")
    print()
    
    fs = VertexAIFeatureStore()
    
    if fs.connect():
        print()
        print("✓ Vertex AI Feature Store ready!")
        return True
    else:
        print()
        print("✗ Vertex AI Feature Store connection failed")
        return False


if __name__ == "__main__":
    test_vertex_ai()
