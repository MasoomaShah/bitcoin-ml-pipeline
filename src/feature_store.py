"""
Feature Store Integration with Hopsworks
Manages feature storage, versioning, and retrieval for ML pipeline
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hopsworks
import hsfs
from hsfs.feature_group import FeatureGroup
from hsfs.feature_view import FeatureView


class BitcoinFeatureStore:
    """
    Manages Bitcoin ML features in Hopsworks Feature Store
    
    Features:
    - Feature ingestion with validation
    - Version control and lineage tracking
    - Online/offline feature serving
    - Feature monitoring and statistics
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_name: str = "bitcoin_ml_pipeline"
    ):
        """
        Initialize connection to Hopsworks Feature Store
        
        Args:
            api_key: Hopsworks API key (or set HOPSWORKS_API_KEY env var)
            project_name: Name of Hopsworks project
        """
        self.api_key = api_key or os.getenv('HOPSWORKS_API_KEY')
        self.project_name = project_name
        self.project = None
        self.fs = None
        self._feature_groups = {}
        
    def connect(self) -> bool:
        """
        Establish connection to Hopsworks
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.project = hopsworks.login(
                api_key_value=self.api_key,
                project=self.project_name
            )
            self.fs = self.project.get_feature_store()
            print(f"✓ Connected to Hopsworks project: {self.project_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Hopsworks: {str(e)}")
            print("  Make sure HOPSWORKS_API_KEY is set in environment")
            return False
    
    def create_bitcoin_features_fg(
        self,
        version: int = 1,
        description: str = "Bitcoin OHLCV and technical indicators"
    ) -> FeatureGroup:
        """
        Create or get Bitcoin features feature group
        
        Args:
            version: Feature group version
            description: Description of feature group
            
        Returns:
            FeatureGroup: Hopsworks feature group object
        """
        fg_name = "bitcoin_features"
        
        try:
            # Try to get existing feature group
            fg = self.fs.get_feature_group(fg_name, version=version)
            print(f"✓ Retrieved existing feature group: {fg_name} v{version}")
        except Exception:
            # Create new feature group
            fg = self.fs.create_feature_group(
                name=fg_name,
                version=version,
                description=description,
                primary_key=["timestamp"],
                event_time="timestamp",
                online_enabled=True,  # Enable online serving
                statistics_config={
                    "enabled": True,
                    "histograms": True,
                    "correlations": True
                }
            )
            print(f"✓ Created new feature group: {fg_name} v{version}")
        
        self._feature_groups[fg_name] = fg
        return fg
    
    def ingest_features(
        self,
        features_df: pd.DataFrame,
        feature_group: Optional[FeatureGroup] = None,
        write_options: Dict = None
    ) -> None:
        """
        Ingest features into feature store
        
        Args:
            features_df: DataFrame with features (must include timestamp)
            feature_group: Target feature group (or uses default)
            write_options: Additional write options for Hopsworks
        """
        if feature_group is None:
            feature_group = self.create_bitcoin_features_fg()
        
        # Ensure timestamp column exists
        if 'timestamp' not in features_df.columns:
            features_df['timestamp'] = pd.Timestamp.now()
        
        # Convert timestamp to proper format
        if features_df['timestamp'].dtype == 'object':
            features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
        
        # Default write options
        if write_options is None:
            write_options = {"wait_for_job": True}
        
        try:
            feature_group.insert(features_df, write_options=write_options)
            print(f"✓ Ingested {len(features_df)} feature records")
            print(f"  Columns: {list(features_df.columns)}")
            print(f"  Date range: {features_df['timestamp'].min()} to {features_df['timestamp'].max()}")
        except Exception as e:
            print(f"✗ Failed to ingest features: {str(e)}")
            raise
    
    def create_feature_view(
        self,
        name: str = "bitcoin_training_view",
        version: int = 1,
        feature_group: Optional[FeatureGroup] = None,
        label_column: Optional[str] = None
    ) -> FeatureView:
        """
        Create feature view for training/inference
        
        Args:
            name: Name of feature view
            version: Version number
            feature_group: Source feature group
            label_column: Optional label column for training
            
        Returns:
            FeatureView: Hopsworks feature view object
        """
        if feature_group is None:
            feature_group = self._feature_groups.get("bitcoin_features")
            if feature_group is None:
                feature_group = self.create_bitcoin_features_fg()
        
        try:
            # Try to get existing feature view
            fv = self.fs.get_feature_view(name, version=version)
            print(f"✓ Retrieved existing feature view: {name} v{version}")
        except Exception:
            # Create new feature view
            query = feature_group.select_all()
            
            fv = self.fs.create_feature_view(
                name=name,
                version=version,
                query=query,
                labels=[label_column] if label_column else []
            )
            print(f"✓ Created new feature view: {name} v{version}")
        
        return fv
    
    def get_training_data(
        self,
        feature_view: Optional[FeatureView] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        training_dataset_version: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Retrieve training data from feature store
        
        Args:
            feature_view: Feature view to query
            start_time: Start timestamp for filtering
            end_time: End timestamp for filtering
            training_dataset_version: Specific version to retrieve
            
        Returns:
            Tuple of (features_df, labels_series)
        """
        if feature_view is None:
            feature_view = self.create_feature_view()
        
        try:
            if training_dataset_version:
                # Get specific version
                X, y = feature_view.get_training_data(training_dataset_version)
            else:
                # Create new training dataset
                X, y = feature_view.get_training_data(
                    start_time=start_time,
                    end_time=end_time
                )
            
            print(f"✓ Retrieved training data: {X.shape[0]} samples, {X.shape[1]} features")
            return X, y
        except Exception as e:
            print(f"✗ Failed to get training data: {str(e)}")
            raise
    
    def get_batch_data(
        self,
        feature_view: Optional[FeatureView] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get batch features for inference
        
        Args:
            feature_view: Feature view to query
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            DataFrame with features
        """
        if feature_view is None:
            feature_view = self.create_feature_view()
        
        try:
            batch_data = feature_view.get_batch_data(
                start_time=start_time,
                end_time=end_time
            )
            print(f"✓ Retrieved batch data: {batch_data.shape[0]} samples")
            return batch_data
        except Exception as e:
            print(f"✗ Failed to get batch data: {str(e)}")
            raise
    
    def get_online_features(
        self,
        feature_view: Optional[FeatureView] = None,
        entry: Dict = None
    ) -> Dict:
        """
        Get online features for real-time inference
        
        Args:
            feature_view: Feature view configured for online serving
            entry: Primary key values to lookup
            
        Returns:
            Dictionary with feature values
        """
        if feature_view is None:
            feature_view = self.create_feature_view()
        
        try:
            # Initialize online serving if not already done
            if not hasattr(feature_view, '_vector_server'):
                feature_view.init_serving()
            
            # Get feature vector
            features = feature_view.get_feature_vector(entry)
            return features
        except Exception as e:
            print(f"✗ Failed to get online features: {str(e)}")
            raise
    
    def compute_statistics(
        self,
        feature_group: Optional[FeatureGroup] = None
    ) -> Dict:
        """
        Compute and store feature statistics
        
        Args:
            feature_group: Feature group to analyze
            
        Returns:
            Dictionary with statistics
        """
        if feature_group is None:
            feature_group = self._feature_groups.get("bitcoin_features")
        
        try:
            stats = feature_group.compute_statistics()
            print(f"✓ Computed statistics for {feature_group.name}")
            return stats
        except Exception as e:
            print(f"✗ Failed to compute statistics: {str(e)}")
            raise
    
    def get_feature_monitoring(
        self,
        feature_group_name: str = "bitcoin_features",
        version: int = 1
    ) -> pd.DataFrame:
        """
        Get feature monitoring data (drift, quality metrics)
        
        Args:
            feature_group_name: Name of feature group
            version: Version number
            
        Returns:
            DataFrame with monitoring metrics
        """
        try:
            fg = self.fs.get_feature_group(feature_group_name, version=version)
            
            # Get feature statistics over time
            stats = fg.get_statistics()
            
            print(f"✓ Retrieved monitoring data for {feature_group_name}")
            return stats
        except Exception as e:
            print(f"✗ Failed to get monitoring data: {str(e)}")
            raise
    
    def delete_feature_group(
        self,
        name: str,
        version: Optional[int] = None
    ) -> None:
        """
        Delete a feature group (use with caution!)
        
        Args:
            name: Feature group name
            version: Specific version to delete (None = all versions)
        """
        try:
            if version:
                fg = self.fs.get_feature_group(name, version=version)
                fg.delete()
                print(f"✓ Deleted feature group: {name} v{version}")
            else:
                # Delete all versions
                all_fgs = self.fs.get_feature_groups(name)
                for fg in all_fgs:
                    fg.delete()
                print(f"✓ Deleted all versions of feature group: {name}")
        except Exception as e:
            print(f"✗ Failed to delete feature group: {str(e)}")
            raise


def prepare_features_for_store(raw_data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare raw Bitcoin data for feature store ingestion
    Computes technical indicators and formats for storage
    
    Args:
        raw_data: DataFrame with OHLCV data
        
    Returns:
        DataFrame ready for feature store ingestion
    """
    from src.feature_engineering import engineer_features
    
    # Compute features using existing pipeline
    features_df = engineer_features(raw_data)
    
    # Ensure timestamp column
    if 'Date' in features_df.columns:
        features_df['timestamp'] = pd.to_datetime(features_df['Date'])
        features_df = features_df.drop('Date', axis=1)
    elif features_df.index.name == 'Date' or features_df.index.dtype == 'datetime64[ns]':
        features_df['timestamp'] = features_df.index
        features_df = features_df.reset_index(drop=True)
    
    # Add metadata
    features_df['ingestion_time'] = pd.Timestamp.now()
    features_df['pipeline_version'] = '1.0'
    
    return features_df


# Example usage
if __name__ == "__main__":
    # Initialize feature store
    fs = BitcoinFeatureStore()
    
    if fs.connect():
        print("\n=== Feature Store Setup ===")
        
        # Create feature group
        fg = fs.create_bitcoin_features_fg(version=1)
        
        # Example: Load and ingest features
        # features_df = prepare_features_for_store(raw_bitcoin_data)
        # fs.ingest_features(features_df, fg)
        
        # Create feature view for training
        fv = fs.create_feature_view(
            name="bitcoin_training_view",
            version=1,
            label_column="target"
        )
        
        print("\n✓ Feature store setup complete!")
        print(f"  Feature Group: {fg.name} v{fg.version}")
        print(f"  Feature View: {fv.name} v{fv.version}")
    else:
        print("\n✗ Feature store setup failed")
        print("  Set HOPSWORKS_API_KEY environment variable")
        print("  Get API key from: https://app.hopsworks.ai/")
