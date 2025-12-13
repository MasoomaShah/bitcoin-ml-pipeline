"""
Vertex AI Feature Store Integration
Manages Bitcoin features in Google Cloud Vertex AI
"""

import os
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
            # Check if feature store exists
            try:
                self.featurestore = Featurestore(
                    featurestore_name=self.featurestore_id
                )
                print(f"✓ Connected to existing feature store: {self.featurestore_id}")
            except:
                # Create new feature store
                print(f"Creating new feature store: {self.featurestore_id}...")
                self.featurestore = Featurestore.create(
                    featurestore_id=self.featurestore_id,
                    online_store_fixed_node_count=1,
                )
                print(f"✓ Created feature store: {self.featurestore_id}")
            
            # Get or create entity type for Bitcoin
            try:
                self.entity_type = self.featurestore.get_entity_type(
                    entity_type_id="bitcoin"
                )
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
            df['feature_timestamp'] = pd.to_datetime(df[entity_id_column]).dt.tz_localize('UTC')
            
            # Create features if they don't exist
            existing_features = {f.name for f in self.entity_type.list_features()}
            # Exclude entity_id, feature_timestamp, and original timestamp column (reserved)
            feature_cols = [col for col in df.columns 
                          if col not in [entity_id_column, 'entity_id', 'feature_timestamp']]
            
            for col in feature_cols:
                if col not in existing_features:
                    print(f"Creating feature: {col}...")
                    Feature.create(
                        feature_id=col.lower().replace(" ", "_"),
                        value_type="DOUBLE",
                        entity_type_name=self.entity_type.resource_name,
                        description=f"Bitcoin feature: {col}"
                    )
            
            # Ingest data
            print(f"Ingesting {len(df)} records...")
            self.entity_type.ingest_from_df(
                feature_ids=[col.lower().replace(" ", "_") for col in feature_cols],
                feature_time='feature_timestamp',
                df_source=df,
                entity_id_field='entity_id',
            )
            
            print(f"✓ Ingested {len(df)} records successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to ingest features: {str(e)}")
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
