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
    Preprocess Bitcoin time-series data.
    
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
    
    # Handle missing values (forward fill then backward fill)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(method='ffill').fillna(method='bfill')
    
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
