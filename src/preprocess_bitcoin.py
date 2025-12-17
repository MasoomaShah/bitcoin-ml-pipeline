"""
Bitcoin Time-Series Preprocessing Module

Preprocessing functions specifically for Bitcoin price prediction.
Target: Predict price_change (daily returns) and classify as bull/bear market.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def preprocess_bitcoin_data(df, scaler=None, drop_date=True):
    """
    Preprocess Bitcoin time-series data with enhanced technical indicators.
    IMPORTANT: Generate feature names that match what the trained model expects!
    
    Args:
        df (pd.DataFrame): Raw Bitcoin data with columns [date, price, market_cap, volume, ...]
        scaler: Pre-fitted scaler or None to create new
        drop_date (bool): Whether to drop date column
        
    Returns:
        tuple: (processed_df, scaler)
    """
    df = df.copy()
    
    # Ensure date is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Identify price column
    price_col = None
    if 'Close' in df.columns:
        price_col = 'Close'
    elif 'price' in df.columns:
        price_col = 'price'
    elif 'close' in df.columns:
        price_col = 'close'
    
    if price_col:
        # ========== PRICE-BASED FEATURES ==========
        # Smoothing
        df['price_smooth'] = df[price_col].rolling(window=3, min_periods=1).mean()
        
        # Moving averages (BOTH old and new naming to match training data)
        df['price_ma3'] = df[price_col].rolling(window=3, min_periods=1).mean()
        df['SMA_7'] = df[price_col].rolling(window=7, min_periods=1).mean()
        df['price_ma7'] = df['SMA_7']  # Alias for compatibility
        
        df['SMA_14'] = df[price_col].rolling(window=14, min_periods=1).mean()
        df['price_ma14'] = df['SMA_14']  # Alias
        
        df['SMA_30'] = df[price_col].rolling(window=30, min_periods=1).mean()
        df['price_ma30'] = df['SMA_30']  # Alias
        
        # EMA (Exponential Moving Averages)
        df['EMA_7'] = df[price_col].ewm(span=7, adjust=False).mean()
        df['price_ema7'] = df['EMA_7']  # Alias
        
        df['EMA_14'] = df[price_col].ewm(span=14, adjust=False).mean()
        df['price_ema14'] = df['EMA_14']  # Alias
        
        # ========== MOMENTUM ==========
        df['momentum_3d'] = df[price_col].pct_change(periods=3)
        df['momentum_7'] = df[price_col].pct_change(periods=7)
        df['momentum_7d'] = df['momentum_7']
        
        df['momentum_14'] = df[price_col].pct_change(periods=14)
        df['momentum_14d'] = df['momentum_14']
        
        df['momentum_30'] = df[price_col].pct_change(periods=30)
        
        # Rate of Change (ROC)
        df['roc_3d'] = df[price_col].pct_change(periods=3) * 100
        df['roc_7d'] = df[price_col].pct_change(periods=7) * 100
        
        # ========== VOLATILITY ==========
        df['price_volatility_3d'] = df[price_col].rolling(window=3, min_periods=1).std()
        df['price_volatility_7d'] = df[price_col].rolling(window=7, min_periods=1).std()
        df['volatility_7'] = df['price_volatility_7d']
        
        df['price_volatility_14d'] = df[price_col].rolling(window=14, min_periods=1).std()
        df['volatility_14'] = df['price_volatility_14d']
        
        # ========== RSI (Relative Strength Index) ==========
        delta = df[price_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss + 1e-10)
        rs = np.clip(rs, 0, 100)
        rsi = 100 - (100 / (1 + rs))
        df['RSI'] = np.clip(rsi, 0, 100)
        df['rsi_14'] = df['RSI']  # Alias
        
        # ========== MACD ==========
        ema_12 = df[price_col].ewm(span=12, adjust=False).mean()
        ema_26 = df[price_col].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # ========== BOLLINGER BANDS ==========
        df['BB_middle'] = df[price_col].rolling(window=20, min_periods=1).mean()
        df['bb_middle'] = df['BB_middle']  # Alias
        
        bb_std = df[price_col].rolling(window=20, min_periods=1).std()
        bb_std = bb_std.fillna(0)
        df['bb_std'] = bb_std
        
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['bb_upper'] = df['BB_upper']
        
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df['bb_lower'] = df['BB_lower']
        
        df['BB_width'] = df['BB_upper'] - df['BB_lower']
        
        # BB Position (0-1 between lower and upper bands)
        band_range = df['BB_upper'] - df['BB_lower']
        band_range = band_range.replace(0, 1e-10)  # Avoid division by zero
        df['bb_position'] = (df[price_col] - df['BB_lower']) / band_range
        df['bb_position'] = np.clip(df['bb_position'], 0, 1)
        
        # Price ratios to MAs
        df['price_to_ma7'] = df[price_col] / (df['SMA_7'] + 1e-10)
        df['price_to_ma30'] = df[price_col] / (df['SMA_30'] + 1e-10)
    
    # ========== VOLUME FEATURES ==========
    vol_col = None
    if 'Volume' in df.columns:
        vol_col = 'Volume'
    elif 'volume' in df.columns:
        vol_col = 'volume'
    
    if vol_col:
        df['volume_ma3'] = df[vol_col].rolling(window=3, min_periods=1).mean()
        df['volume_SMA_7'] = df[vol_col].rolling(window=7, min_periods=1).mean()
        df['volume_ma7'] = df['volume_SMA_7']  # Alias
        
        df['volume_change'] = df[vol_col].pct_change()
    
    # ========== MARKET CAP FEATURES ==========
    if 'market_cap' in df.columns:
        df['market_cap_change'] = df['market_cap'].pct_change()
        
        if vol_col:
            df['volume_to_marketcap'] = df[vol_col] / (df['market_cap'] + 1e-10)
    
    # ========== HANDLE MISSING VALUES ==========
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].ffill().bfill()
    
    # Clean infinity values
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Fill remaining NaNs with column medians
    for col in numeric_cols:
        if df[col].isna().any():
            median_val = df[col].median()
            if np.isnan(median_val):
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(median_val)
    
    # Drop any remaining NaN rows
    df = df.dropna()
    
    # Identify feature columns (exclude date and target)
    feature_cols = [col for col in df.columns if col not in ['date', 'price_change']]
    
    # Scale features
    if scaler is None:
        scaler = StandardScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
    else:
        df[feature_cols] = scaler.transform(df[feature_cols])
    
    if drop_date and 'date' in df.columns:
        df = df.drop(columns=['date'])
    
    return df, scaler
    if drop_date:
        df = df.drop('date', axis=1)
    
    return df, scaler


def get_temporal_train_test_split(df, test_days=60):
    """
    Split Bitcoin data into train/test by date (no data leakage).
    Uses 'future_price_change' as target (predicting N days ahead).
    
    Args:
        df (pd.DataFrame): DataFrame with 'date' column (datetime)
        test_days (int): Number of days to use for test set
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test, train_dates, test_dates)
    """
    
    if 'date' not in df.columns:
        raise ValueError("DataFrame must have a 'date' column")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Split: last `test_days` for testing
    split_index = len(df) - test_days
    
    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()
    
    # Extract features and target (use future_price_change as target)
    feature_cols = [c for c in df.columns 
                   if c not in ['date', 'price_change', 'future_price_change', 'market_class']]
    
    X_train = train_df[feature_cols].values
    X_test = test_df[feature_cols].values
    y_train = train_df['future_price_change'].values
    y_test = test_df['future_price_change'].values
    
    train_dates = train_df['date'].values
    test_dates = test_df['date'].values
    
    return X_train, X_test, y_train, y_test, train_dates, test_dates


def create_classification_target(price_change_series, threshold=0.01):
    """
    Convert regression target (price_change) to binary classification.
    
    Args:
        price_change_series: Series or array of price changes (returns)
        threshold (float): Positive change threshold for 'bull market' classification
    
    Returns:
        np.array: Binary classification (1 for bull/up, 0 for bear/down)
    """
    return np.where(price_change_series >= threshold, 1, 0)


if __name__ == "__main__":
    # Quick test
    print("Bitcoin time-series preprocessing module ready.")
    print("\nKey functions:")
    print("  - preprocess_bitcoin_data(df, scaler, drop_date)")
    print("  - get_temporal_train_test_split(df, test_days)")
    print("  - create_classification_target(price_change_series, threshold)")
