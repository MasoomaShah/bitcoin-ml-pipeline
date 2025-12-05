"""
CoinGecko API Integration for Bitcoin Time-Series Data

Fetches historical Bitcoin price data (hourly) for time-series prediction.
No API key required - completely free!
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time


def fetch_bitcoin_data(days=365, vs_currency='usd'):
    """
    Fetch Bitcoin historical data from CoinGecko API.
    
    Args:
        days (int): Number of days of historical data (1-365 for hourly, max 90 days detailed)
        vs_currency (str): Currency to price Bitcoin in (usd, eur, etc.)
        
    Returns:
        pd.DataFrame: Bitcoin data with columns [timestamp, price, market_cap, volume]
    """
    
    print(f"Fetching Bitcoin data from CoinGecko API...")
    print(f"  Period: Last {days} days")
    print(f"  Currency: {vs_currency.upper()}")
    
    # CoinGecko API endpoint
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily' if days > 90 else 'hourly'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract price, market cap, and volume data
        prices = data['prices']
        market_caps = data['market_caps']
        volumes = data['total_volumes']
        
        # Convert to DataFrame
        df = pd.DataFrame({
            'timestamp': [p[0] for p in prices],
            'price': [p[1] for p in prices],
            'market_cap': [m[1] for m in market_caps],
            'volume': [v[1] for v in volumes]
        })
        
        # Convert timestamp from milliseconds to datetime
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.drop('timestamp', axis=1)
        
        # Reorder columns
        df = df[['date', 'price', 'market_cap', 'volume']]
        
        print(f"✓ Successfully fetched {len(df)} data points")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching data from CoinGecko: {e}")
        raise
    except KeyError as e:
        print(f"✗ Unexpected API response format: {e}")
        raise


def calculate_price_changes(df, prediction_horizon=1):
    """
    Calculate price changes for future prediction.
    Uses multi-day aggregation for more stable predictions.
    
    Args:
        df (pd.DataFrame): Bitcoin data with 'price' column
        prediction_horizon (int): Number of days ahead to predict (default=1)
        
    Returns:
        pd.DataFrame: Data with added 'price_change' and 'future_price_change' columns
    """
    df = df.copy()
    
    # Current day price change (for feature engineering)
    df['price_change'] = df['price'].pct_change()
    
    # Use 3-day rolling average for more stable target
    df['price_smooth'] = df['price'].rolling(window=3, center=True).mean()
    df['price_smooth'] = df['price_smooth'].fillna(df['price'])
    
    # Future price change (TARGET - predict N days ahead)
    # This shifts the target backwards so we predict the future
    df['future_price_change'] = df['price_smooth'].pct_change(periods=prediction_horizon).shift(-prediction_horizon)
    
    # Remove rows with NaN targets (first row and last N rows)
    df = df.dropna(subset=['future_price_change'])
    
    return df


def add_technical_indicators(df):
    """
    Add comprehensive technical indicators for better prediction.
    
    Args:
        df (pd.DataFrame): Bitcoin data
        
    Returns:
        pd.DataFrame: Data with additional features
    """
    df = df.copy()
    
    # Moving averages (multiple timeframes)
    df['price_ma3'] = df['price'].rolling(window=3, min_periods=1).mean()
    df['price_ma7'] = df['price'].rolling(window=7, min_periods=1).mean()
    df['price_ma14'] = df['price'].rolling(window=14, min_periods=1).mean()
    df['price_ma30'] = df['price'].rolling(window=30, min_periods=1).mean()
    
    # Exponential moving averages
    df['price_ema7'] = df['price'].ewm(span=7, adjust=False).mean()
    df['price_ema14'] = df['price'].ewm(span=14, adjust=False).mean()
    
    # Price momentum (multiple periods)
    df['momentum_3d'] = df['price'] - df['price'].shift(3)
    df['momentum_7d'] = df['price'] - df['price'].shift(7)
    df['momentum_14d'] = df['price'] - df['price'].shift(14)
    
    # Rate of change
    df['roc_3d'] = df['price'].pct_change(periods=3)
    df['roc_7d'] = df['price'].pct_change(periods=7)
    
    # Volatility (rolling std, multiple windows)
    df['price_volatility_3d'] = df['price'].rolling(window=3, min_periods=1).std()
    df['price_volatility_7d'] = df['price'].rolling(window=7, min_periods=1).std()
    df['price_volatility_14d'] = df['price'].rolling(window=14, min_periods=1).std()
    
    # Volume indicators
    df['volume_ma3'] = df['volume'].rolling(window=3, min_periods=1).mean()
    df['volume_ma7'] = df['volume'].rolling(window=7, min_periods=1).mean()
    df['volume_change'] = df['volume'].pct_change()
    
    # Price position relative to moving averages
    df['price_to_ma7'] = df['price'] / df['price_ma7']
    df['price_to_ma30'] = df['price'] / df['price_ma30']
    
    # Bollinger Bands
    df['bb_middle'] = df['price_ma7']
    df['bb_std'] = df['price'].rolling(window=7, min_periods=1).std()
    df['bb_upper'] = df['bb_middle'] + (2 * df['bb_std'])
    df['bb_lower'] = df['bb_middle'] - (2 * df['bb_std'])
    df['bb_position'] = (df['price'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # RSI (Relative Strength Index)
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Market cap and volume momentum
    df['market_cap_change'] = df['market_cap'].pct_change()
    df['volume_to_marketcap'] = df['volume'] / df['market_cap']
    
    return df


def save_bitcoin_data(output_path='data/raw/bitcoin_timeseries.csv', days=365):
    """
    Fetch and save Bitcoin data to CSV.
    
    Args:
        output_path (str): Path to save CSV file
        days (int): Number of days of historical data
        
    Returns:
        str: Path to saved file
    """
    import os
    
    # Fetch data
    df = fetch_bitcoin_data(days=days)
    
    # Calculate price changes
    df = calculate_price_changes(df)
    
    # Add technical indicators
    df = add_technical_indicators(df)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\n✓ Data saved to: {output_path}")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    
    return output_path


if __name__ == "__main__":
    # Test the API integration
    print("="*70)
    print("  COINGECKO API TEST - Bitcoin Time-Series Data")
    print("="*70 + "\n")
    
    # Fetch and save 365 days of data
    output_file = save_bitcoin_data(days=365)
    
    # Display sample
    df = pd.read_csv(output_file)
    print("\nFirst 5 rows:")
    print(df.head())
    
    print("\nLast 5 rows:")
    print(df.tail())
    
    print("\nData statistics:")
    print(df.describe())
    
    print("\n" + "="*70)
    print("✓ Bitcoin data ready for ML pipeline!")
    print("="*70)
