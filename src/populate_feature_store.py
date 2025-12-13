"""
Populate Hopsworks Feature Store with Bitcoin data
Run this to upload features to Hopsworks for the first time or to update
"""

import pandas as pd
from datetime import datetime
from src.feature_store import BitcoinFeatureStore
from src.fetch_alpha_vantage import fetch_crypto_with_indicators
from src.preprocess_bitcoin import preprocess_bitcoin_data

def populate_features(days: int = 1095):
    """
    Fetch Bitcoin data and upload to Hopsworks Feature Store
    
    Args:
        days: Number of days of historical data to fetch
    """
    print("=" * 60)
    print("POPULATING HOPSWORKS FEATURE STORE")
    print("=" * 60)
    print()
    
    # 1. Connect to feature store
    print("1. Connecting to Hopsworks...")
    fs = BitcoinFeatureStore()
    if not fs.connect():
        print("✗ Failed to connect to Hopsworks")
        return False
    print()
    
    # 2. Fetch raw data
    print(f"2. Fetching {days} days of Bitcoin data from Alpha Vantage...")
    raw_data = fetch_crypto_with_indicators(symbol='BTC', market='USD', days=days)
    print(f"   ✓ Fetched {len(raw_data)} data points")
    print()
    
    # 3. Preprocess data
    print("3. Preprocessing features...")
    processed_data, scaler = preprocess_bitcoin_data(raw_data, drop_date=False)
    feature_cols = [col for col in processed_data.columns if col != 'date']
    print(f"   ✓ Generated {len(feature_cols)} features")
    print(f"   Features: {', '.join(feature_cols[:10])}...")
    print()
    
    # 4. Create or get feature group
    print("4. Creating/updating feature group...")
    fg = fs.create_bitcoin_features_fg(version=1)
    print()
    
    # 5. Rename date to timestamp for Hopsworks
    print("5. Preparing data for ingestion...")
    processed_data = processed_data.rename(columns={'date': 'timestamp'})
    print(f"   ✓ Renamed 'date' to 'timestamp'")
    print()
    
    # 6. Insert features
    print("6. Inserting features into Hopsworks...")
    try:
        fs.ingest_features(
            features_df=processed_data,
            feature_group=fg
        )
        success = True
    except Exception as e:
        print(f"   ✗ Failed to ingest: {e}")
        success = False
    
    if success:
        print()
        print("=" * 60)
        print("✓ FEATURE STORE POPULATED SUCCESSFULLY")
        print("=" * 60)
        print(f"  Total samples: {len(processed_data)}")
        print(f"  Features: {len(processed_data.columns)}")
        print(f"  Date range: {processed_data.index.min()} to {processed_data.index.max()}")
        return True
    else:
        print()
        print("=" * 60)
        print("✗ FAILED TO POPULATE FEATURE STORE")
        print("=" * 60)
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate Hopsworks with Bitcoin features")
    parser.add_argument(
        "--days",
        type=int,
        default=1095,
        help="Number of days of historical data (default: 1095 = 3 years)"
    )
    
    args = parser.parse_args()
    
    populate_features(days=args.days)
