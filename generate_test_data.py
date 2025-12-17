#!/usr/bin/env python3
"""
Generate test data from the actual Bitcoin timeseries CSV file
This creates JSON and numeric test data from real historical data
Includes feature engineering to match what the models expect
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def generate_test_data():
    """Load actual Bitcoin data, engineer features, and create test files"""
    
    # Load the actual Bitcoin data
    csv_path = Path("data/raw/bitcoin_timeseries.csv")
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found")
        return False
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")
    print(f"Raw columns: {list(df.columns)}")
    
    # Ensure we have enough data for feature engineering
    if len(df) < 30:
        print("ERROR: Need at least 30 rows for feature engineering")
        return False
    
    # Process dataframe to add all engineered features
    price_col = 'price'
    
    # Basic features
    df['price_smooth'] = df[price_col].rolling(window=3, min_periods=1).mean()
    df['price_ma3'] = df[price_col].rolling(window=3, min_periods=1).mean()
    df['price_ma7'] = df[price_col].rolling(window=7, min_periods=1).mean()
    df['price_ma14'] = df[price_col].rolling(window=14, min_periods=1).mean()
    df['price_ma30'] = df[price_col].rolling(window=30, min_periods=1).mean()
    
    # Exponential Moving Averages
    df['price_ema7'] = df[price_col].ewm(span=7, adjust=False).mean()
    df['price_ema14'] = df[price_col].ewm(span=14, adjust=False).mean()
    
    # Momentum indicators
    df['momentum_3d'] = df[price_col].pct_change(periods=3) * 100
    df['momentum_7d'] = df[price_col].pct_change(periods=7) * 100
    df['momentum_14d'] = df[price_col].pct_change(periods=14) * 100
    
    # Rate of Change
    df['roc_3d'] = df[price_col].pct_change(periods=3) * 100
    df['roc_7d'] = df[price_col].pct_change(periods=7) * 100
    
    # Volatility
    df['price_volatility_3d'] = df[price_col].rolling(window=3, min_periods=1).std()
    df['price_volatility_7d'] = df[price_col].rolling(window=7, min_periods=1).std()
    df['price_volatility_14d'] = df[price_col].rolling(window=14, min_periods=1).std()
    
    # Volume moving averages
    df['volume_ma3'] = df['volume'].rolling(window=3, min_periods=1).mean()
    df['volume_ma7'] = df['volume'].rolling(window=7, min_periods=1).mean()
    df['volume_change'] = df['volume'].pct_change(periods=1).fillna(0) * 100
    
    # Price to moving average ratios
    df['price_to_ma7'] = df[price_col] / (df['price_ma7'] + 1e-10)
    df['price_to_ma30'] = df[price_col] / (df['price_ma30'] + 1e-10)
    
    # Bollinger Bands
    df['bb_middle'] = df[price_col].rolling(window=20, min_periods=1).mean()
    bb_std = df[price_col].rolling(window=20, min_periods=1).std()
    bb_std = bb_std.fillna(0)
    df['bb_std'] = bb_std
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_position'] = (df[price_col] - df['bb_lower']) / ((df['bb_upper'] - df['bb_lower']) + 1e-10)
    
    # RSI - Classic calculation
    delta = df[price_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-10)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    df['rsi_14'] = np.clip(df['rsi_14'], 0, 100)
    
    # Market cap changes
    df['market_cap_change'] = df['market_cap'].pct_change(periods=1).fillna(0) * df['market_cap']
    df['volume_to_marketcap'] = df['volume'] / (df['market_cap'] + 1e-10)
    
    # Alternative SMA values
    df['SMA_7'] = df[price_col].rolling(window=7, min_periods=1).mean()
    df['SMA_14'] = df[price_col].rolling(window=14, min_periods=1).mean()
    df['SMA_30'] = df[price_col].rolling(window=30, min_periods=1).mean()
    
    # Alternative EMA values
    df['EMA_7'] = df[price_col].ewm(span=7, adjust=False).mean()
    df['EMA_14'] = df[price_col].ewm(span=14, adjust=False).mean()
    
    # Alternative momentum
    df['momentum_7'] = df[price_col].pct_change(periods=7) * 100
    df['momentum_14'] = df[price_col].pct_change(periods=14) * 100
    df['momentum_30'] = df[price_col].pct_change(periods=30) * 100
    
    # Alternative volatility
    df['volatility_7'] = df[price_col].rolling(window=7, min_periods=1).std()
    df['volatility_14'] = df[price_col].rolling(window=14, min_periods=1).std()
    
    # RSI alternative name
    df['RSI'] = df['rsi_14'].copy()
    
    # MACD
    ema_12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema_26 = df[price_col].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands alternative names
    df['BB_middle'] = df['bb_middle'].copy()
    df['BB_upper'] = df['bb_upper'].copy()
    df['BB_lower'] = df['bb_lower'].copy()
    df['BB_width'] = df['BB_upper'] - df['BB_lower']
    
    # Volume SMA
    df['volume_SMA_7'] = df['volume'].rolling(window=7, min_periods=1).mean()
    
    # Clean infinity and NaN values
    for col in df.select_dtypes(include=[np.number]).columns:
        col_median = df[col].replace([np.inf, -np.inf], np.nan).median()
        df[col] = df[col].replace([np.inf, -np.inf], col_median)
        df[col] = df[col].fillna(col_median if col_median != 0 else 0)
    
    # Expected 49 features (in order)
    feature_names = [
        "price", "volume", "market_cap", "price_smooth", "price_ma3", "price_ma7",
        "price_ma14", "price_ma30", "price_ema7", "price_ema14", "momentum_3d",
        "momentum_7d", "momentum_14d", "roc_3d", "roc_7d", "price_volatility_3d",
        "price_volatility_7d", "price_volatility_14d", "volume_ma3", "volume_ma7",
        "volume_change", "price_to_ma7", "price_to_ma30", "bb_middle", "bb_std",
        "bb_upper", "bb_lower", "bb_position", "rsi_14", "market_cap_change",
        "volume_to_marketcap", "SMA_7", "SMA_14", "SMA_30", "EMA_7", "EMA_14",
        "momentum_7", "momentum_14", "momentum_30", "volatility_7", "volatility_14",
        "RSI", "MACD", "MACD_signal", "BB_middle", "BB_upper", "BB_lower",
        "BB_width", "volume_SMA_7"
    ]
    
    # Get the latest row with all features
    latest_row = df.iloc[-1]
    print(f"\nUsing latest row (index {len(df)-1})")
    
    # Create JSON test data (dictionary format)
    json_test_data = {
        "features": {},
        "current_price": None
    }
    
    # Create numeric test data (array format)
    numeric_features = []
    
    missing_count = 0
    for feature in feature_names:
        if feature in latest_row.index:
            value = float(latest_row[feature])
            json_test_data["features"][feature] = value
            numeric_features.append(value)
        else:
            print(f"WARNING: Feature '{feature}' not found")
            json_test_data["features"][feature] = 0.0
            numeric_features.append(0.0)
            missing_count += 1
    
    # Set current price
    if "price" in json_test_data["features"]:
        json_test_data["current_price"] = json_test_data["features"]["price"]
    
    numeric_test_data = {
        "features": numeric_features,
        "current_price": json_test_data.get("current_price")
    }
    
    # Save JSON test data
    json_path = Path("test_fastapi_json.json")
    with open(json_path, "w") as f:
        json.dump(json_test_data, f, indent=2)
    print(f"\n✓ Created {json_path}")
    print(f"  Features: {len(json_test_data['features'])}/49")
    print(f"  Current price: ${json_test_data['current_price']:,.2f}")
    
    # Save numeric test data
    numeric_path = Path("test_fastapi_numeric.json")
    with open(numeric_path, "w") as f:
        json.dump(numeric_test_data, f, indent=2)
    print(f"\n✓ Created {numeric_path}")
    print(f"  Features: {len(numeric_test_data['features'])}/49")
    print(f"  Current price: ${numeric_test_data['current_price']:,.2f}")
    
    if missing_count == 0:
        print(f"\n✓ All features successfully generated!")
    else:
        print(f"\n⚠ {missing_count} features had to be filled with 0.0")
    
    return True

if __name__ == "__main__":
    generate_test_data()
