"""
Feature Ingestion Pipeline
Computes and stores features in Hopsworks Feature Store
Run daily to keep features fresh
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_store import BitcoinFeatureStore, prepare_features_for_store
from src.data_ingestion import fetch_bitcoin_data
from src.feature_engineering import engineer_features


def ingest_historical_features(
    days_back: int = 365,
    batch_size: int = 100
) -> None:
    """
    Ingest historical Bitcoin features into feature store
    
    Args:
        days_back: Number of days of historical data to fetch
        batch_size: Number of records per batch
    """
    print(f"\n{'='*60}")
    print("HISTORICAL FEATURE INGESTION")
    print(f"{'='*60}\n")
    
    # Initialize feature store
    fs = BitcoinFeatureStore()
    if not fs.connect():
        print("✗ Cannot proceed without feature store connection")
        sys.exit(1)
    
    # Create feature group
    fg = fs.create_bitcoin_features_fg(
        version=1,
        description=f"Bitcoin OHLCV + Technical Indicators (Last {days_back} days)"
    )
    
    # Fetch raw data
    print(f"\n1. Fetching {days_back} days of Bitcoin data...")
    try:
        raw_data = fetch_bitcoin_data(days=days_back)
        print(f"   ✓ Fetched {len(raw_data)} records")
    except Exception as e:
        print(f"   ✗ Failed to fetch data: {str(e)}")
        sys.exit(1)
    
    # Engineer features
    print(f"\n2. Engineering features...")
    try:
        features_df = prepare_features_for_store(raw_data)
        print(f"   ✓ Computed {len(features_df.columns)} features")
        print(f"   Features: {list(features_df.columns[:10])}...")
    except Exception as e:
        print(f"   ✗ Failed to engineer features: {str(e)}")
        sys.exit(1)
    
    # Ingest in batches
    print(f"\n3. Ingesting features in batches of {batch_size}...")
    total_batches = (len(features_df) + batch_size - 1) // batch_size
    
    for i in range(0, len(features_df), batch_size):
        batch_num = i // batch_size + 1
        batch = features_df.iloc[i:i+batch_size]
        
        try:
            fs.ingest_features(batch, fg)
            print(f"   ✓ Batch {batch_num}/{total_batches} ingested ({len(batch)} records)")
        except Exception as e:
            print(f"   ✗ Batch {batch_num} failed: {str(e)}")
            continue
    
    # Compute statistics
    print(f"\n4. Computing feature statistics...")
    try:
        fs.compute_statistics(fg)
        print(f"   ✓ Statistics computed and stored")
    except Exception as e:
        print(f"   ⚠️ Statistics computation failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print("✓ HISTORICAL FEATURE INGESTION COMPLETE")
    print(f"{'='*60}\n")
    print(f"Total records: {len(features_df)}")
    print(f"Feature group: {fg.name} v{fg.version}")
    print(f"Date range: {features_df['timestamp'].min()} to {features_df['timestamp'].max()}")


def ingest_daily_features() -> None:
    """
    Ingest latest daily features (for scheduled jobs)
    Fetches only new data since last ingestion
    """
    print(f"\n{'='*60}")
    print("DAILY FEATURE INGESTION")
    print(f"{'='*60}\n")
    
    # Initialize feature store
    fs = BitcoinFeatureStore()
    if not fs.connect():
        print("✗ Cannot proceed without feature store connection")
        sys.exit(1)
    
    # Get feature group
    fg = fs.create_bitcoin_features_fg(version=1)
    
    # Fetch last 7 days (ensures overlap for feature computation)
    print(f"\n1. Fetching last 7 days of Bitcoin data...")
    try:
        raw_data = fetch_bitcoin_data(days=7)
        print(f"   ✓ Fetched {len(raw_data)} records")
    except Exception as e:
        print(f"   ✗ Failed to fetch data: {str(e)}")
        sys.exit(1)
    
    # Engineer features
    print(f"\n2. Engineering features...")
    try:
        features_df = prepare_features_for_store(raw_data)
        print(f"   ✓ Computed features for {len(features_df)} records")
    except Exception as e:
        print(f"   ✗ Failed to engineer features: {str(e)}")
        sys.exit(1)
    
    # Ingest features (Hopsworks handles deduplication)
    print(f"\n3. Ingesting features...")
    try:
        fs.ingest_features(features_df, fg)
        print(f"   ✓ Ingested {len(features_df)} records")
    except Exception as e:
        print(f"   ✗ Failed to ingest features: {str(e)}")
        sys.exit(1)
    
    # Update statistics
    print(f"\n4. Updating feature statistics...")
    try:
        fs.compute_statistics(fg)
        print(f"   ✓ Statistics updated")
    except Exception as e:
        print(f"   ⚠️ Statistics update failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print("✓ DAILY FEATURE INGESTION COMPLETE")
    print(f"{'='*60}\n")


def create_feature_view_for_training(
    label_column: str = "target",
    version: int = 1
) -> None:
    """
    Create feature view for model training
    
    Args:
        label_column: Name of target column
        version: Feature view version
    """
    print(f"\n{'='*60}")
    print("CREATING FEATURE VIEW FOR TRAINING")
    print(f"{'='*60}\n")
    
    # Initialize feature store
    fs = BitcoinFeatureStore()
    if not fs.connect():
        print("✗ Cannot proceed without feature store connection")
        sys.exit(1)
    
    # Get feature group
    fg = fs.create_bitcoin_features_fg(version=1)
    
    # Create feature view
    print(f"\nCreating feature view with label: '{label_column}'")
    try:
        fv = fs.create_feature_view(
            name="bitcoin_training_view",
            version=version,
            feature_group=fg,
            label_column=label_column
        )
        print(f"✓ Feature view created: {fv.name} v{fv.version}")
    except Exception as e:
        print(f"✗ Failed to create feature view: {str(e)}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("✓ FEATURE VIEW CREATED")
    print(f"{'='*60}\n")


def verify_feature_store() -> None:
    """
    Verify feature store connection and list available features
    """
    print(f"\n{'='*60}")
    print("FEATURE STORE VERIFICATION")
    print(f"{'='*60}\n")
    
    # Initialize feature store
    fs = BitcoinFeatureStore()
    if not fs.connect():
        print("✗ Feature store connection failed")
        sys.exit(1)
    
    print("\n1. Checking feature groups...")
    try:
        fg = fs.create_bitcoin_features_fg(version=1)
        print(f"   ✓ Feature group found: {fg.name} v{fg.version}")
        print(f"   Description: {fg.description}")
        print(f"   Primary key: {fg.primary_key}")
        print(f"   Event time: {fg.event_time}")
        print(f"   Online enabled: {fg.online_enabled}")
    except Exception as e:
        print(f"   ✗ No feature group found: {str(e)}")
        return
    
    print("\n2. Checking feature views...")
    try:
        fv = fs.create_feature_view(
            name="bitcoin_training_view",
            version=1
        )
        print(f"   ✓ Feature view found: {fv.name} v{fv.version}")
    except Exception as e:
        print(f"   ⚠️ No feature view found: {str(e)}")
    
    print("\n3. Testing feature retrieval...")
    try:
        # Get sample batch data
        sample = fs.get_batch_data(fv, start_time=None, end_time=None)
        print(f"   ✓ Retrieved {len(sample)} sample records")
        print(f"   Features: {list(sample.columns)[:10]}...")
    except Exception as e:
        print(f"   ⚠️ Feature retrieval test failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print("✓ FEATURE STORE VERIFICATION COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bitcoin Feature Store Ingestion")
    parser.add_argument(
        '--mode',
        choices=['historical', 'daily', 'create-view', 'verify'],
        default='daily',
        help='Ingestion mode'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Days of historical data (for historical mode)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for ingestion'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'historical':
        ingest_historical_features(
            days_back=args.days,
            batch_size=args.batch_size
        )
    elif args.mode == 'daily':
        ingest_daily_features()
    elif args.mode == 'create-view':
        create_feature_view_for_training()
    elif args.mode == 'verify':
        verify_feature_store()
