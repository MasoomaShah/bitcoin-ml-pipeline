"""
Populate Vertex AI Feature Store with Bitcoin data
"""

from src.vertex_ai_feature_store import VertexAIFeatureStore
from src.fetch_bitcoin_data import fetch_bitcoin_data
from src.preprocess_bitcoin import preprocess_bitcoin_data

def populate_vertex_ai(days: int = 1095):
    """Populate Vertex AI with Bitcoin features"""
    
    print("=" * 60)
    print("POPULATING VERTEX AI FEATURE STORE")
    print("=" * 60)
    print()
    
    # 1. Connect
    print("1. Connecting to Vertex AI...")
    fs = VertexAIFeatureStore()
    if not fs.connect():
        return False
    print()
    
    # 2. Fetch data
    print(f"2. Fetching {days} days of Bitcoin data from CoinGecko...")
    raw_data = fetch_bitcoin_data(days=days)
    print(f"   ✓ Fetched {len(raw_data)} data points")
    print()
    
    # 3. Preprocess
    print("3. Preprocessing features...")
    processed_data, scaler = preprocess_bitcoin_data(raw_data, drop_date=False)
    processed_data = processed_data.rename(columns={'date': 'timestamp'})
    processed_data.columns = processed_data.columns.str.lower()
    print(f"   ✓ Generated {len(processed_data.columns)} features")
    print()
    
    # 4. Ingest
    print("4. Ingesting into Vertex AI...")
    success = fs.ingest_features(
        features_df=processed_data,
        entity_id_column="timestamp"
    )
    
    if success:
        print()
        print("=" * 60)
        print("✓ VERTEX AI POPULATED SUCCESSFULLY")
        print("=" * 60)
        print(f"  Records: {len(processed_data)}")
        print(f"  Features: {len(processed_data.columns)}")
        return True
    else:
        print()
        print("✗ Failed to populate Vertex AI")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1095, help="Days of data")
    args = parser.parse_args()
    
    populate_vertex_ai(days=args.days)
