"""
Alpha Vantage Data Fetching Module
Fetches cryptocurrency data with technical indicators
"""

import os
import pandas as pd
import numpy as np
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from alpha_vantage.techindicators import TechIndicators
import time


def fetch_crypto_data(symbol='BTC', market='USD', outputsize='full'):
    """
    Fetch cryptocurrency daily data from Alpha Vantage.
    
    Args:
        symbol (str): Cryptocurrency symbol (default: 'BTC')
        market (str): Market currency (default: 'USD')
        outputsize (str): 'compact' (100 days) or 'full' (all available)
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data and date index
    """
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
    
    print(f"Fetching {symbol} data from Alpha Vantage...")
    print(f"  Market: {market}")
    print(f"  Output size: {outputsize}")
    
    try:
        cc = CryptoCurrencies(key=api_key, output_format='pandas')
        data, meta_data = cc.get_digital_currency_daily(
            symbol=symbol, 
            market=market
        )
        
        # Print original columns to debug
        print(f"  Original columns: {list(data.columns)[:5]}...")
        
        # Rename columns for consistency
        column_mapping = {}
        for col in data.columns:
            if 'open' in col.lower():
                column_mapping[col] = 'Open'
            elif 'high' in col.lower():
                column_mapping[col] = 'High'
            elif 'low' in col.lower():
                column_mapping[col] = 'Low'
            elif 'close' in col.lower():
                column_mapping[col] = 'Close'
            elif 'volume' in col.lower():
                column_mapping[col] = 'Volume'
        
        data = data.rename(columns=column_mapping)
        
        # Select only the columns we need
        columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [col for col in columns_to_keep if col in data.columns]
        data = data[available_cols]
        
        # Convert to numeric
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Sort by date (ascending)
        data = data.sort_index()
        
        # Reset index to make date a column
        data = data.reset_index()
        data = data.rename(columns={'index': 'date'})
        
        print(f"✓ Successfully fetched {len(data)} data points")
        print(f"  Date range: {data['date'].min()} to {data['date'].max()}")
        if 'Close' in data.columns:
            print(f"  Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
        
        return data
        
    except Exception as e:
        print(f"✗ Error fetching data from Alpha Vantage: {e}")
        raise


def fetch_technical_indicators(symbol='BTC', market='USD', interval='daily'):
    """
    Fetch pre-calculated technical indicators from Alpha Vantage.
    
    Args:
        symbol (str): Cryptocurrency symbol
        market (str): Market currency
        interval (str): Time interval ('daily', 'weekly', 'monthly')
        
    Returns:
        dict: Dictionary of DataFrames with technical indicators
    """
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
    
    print(f"\nFetching technical indicators for {symbol}...")
    
    ti = TechIndicators(key=api_key, output_format='pandas')
    indicators = {}
    
    try:
        # Fetch RSI
        print("  Fetching RSI...")
        rsi_data, _ = ti.get_rsi(symbol=f'{symbol}{market}', interval=interval, time_period=14)
        indicators['RSI'] = rsi_data['RSI']
        time.sleep(12)  # API rate limit: 5 calls/minute
        
        # Fetch MACD
        print("  Fetching MACD...")
        macd_data, _ = ti.get_macd(symbol=f'{symbol}{market}', interval=interval)
        indicators['MACD'] = macd_data['MACD']
        indicators['MACD_Signal'] = macd_data['MACD_Signal']
        indicators['MACD_Hist'] = macd_data['MACD_Hist']
        time.sleep(12)
        
        # Fetch SMA
        print("  Fetching SMA...")
        sma_data, _ = ti.get_sma(symbol=f'{symbol}{market}', interval=interval, time_period=20)
        indicators['SMA_20'] = sma_data['SMA']
        time.sleep(12)
        
        # Fetch EMA
        print("  Fetching EMA...")
        ema_data, _ = ti.get_ema(symbol=f'{symbol}{market}', interval=interval, time_period=20)
        indicators['EMA_20'] = ema_data['EMA']
        time.sleep(12)
        
        # Fetch Bollinger Bands
        print("  Fetching Bollinger Bands...")
        bbands_data, _ = ti.get_bbands(symbol=f'{symbol}{market}', interval=interval, time_period=20)
        indicators['BB_Upper'] = bbands_data['Real Upper Band']
        indicators['BB_Middle'] = bbands_data['Real Middle Band']
        indicators['BB_Lower'] = bbands_data['Real Lower Band']
        
        print(f"✓ Successfully fetched {len(indicators)} technical indicators")
        
        return indicators
        
    except Exception as e:
        print(f"✗ Error fetching technical indicators: {e}")
        return {}


def fetch_crypto_with_indicators(symbol='BTC', market='USD', days=None):
    """
    Fetch cryptocurrency data with technical indicators combined.
    
    Args:
        symbol (str): Cryptocurrency symbol
        market (str): Market currency
        days (int): Number of recent days to return (None for all)
        
    Returns:
        pd.DataFrame: Combined DataFrame with price data and technical indicators
    """
    # Fetch price data
    price_data = fetch_crypto_data(symbol, market, outputsize='full')
    
    # Note: Technical indicators require separate API calls
    # Due to rate limits (5 calls/min), we'll compute them locally instead
    print("\n⚠️  Technical indicators will be computed locally to avoid API rate limits")
    
    # Limit to recent days if specified
    if days:
        price_data = price_data.tail(days)
    
    return price_data


if __name__ == "__main__":
    # Test the fetcher
    print("Testing Alpha Vantage Bitcoin Data Fetcher\n" + "="*50)
    
    # Fetch Bitcoin data
    df = fetch_crypto_with_indicators(symbol='BTC', market='USD', days=500)
    
    print(f"\nData shape: {df.shape}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nLast 5 rows:")
    print(df.tail())
    print(f"\nColumn names: {list(df.columns)}")
    print(f"\nData types:\n{df.dtypes}")
