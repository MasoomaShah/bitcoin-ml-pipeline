"""
Time-series preprocessing for World Bank economic indicators.
Handles date-indexed data with features like GDP, Population, Inflation, Unemployment, and rolling aggregates.
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler
import json
import numpy as np


def preprocess_timeseries_data(df, scaler=None, drop_date=True):
    """
    Preprocess time-series economic data for training or inference.
    
    Args:
        df (pd.DataFrame): Input data with columns: date, GDP, GDP_growth, Population, Inflation, Unemployment, GDP_rolling3
        scaler (StandardScaler): Optional fitted scaler for inference. If None, a new one is fit.
        drop_date (bool): Whether to drop the 'date' column from features (keep for validation).
    
    Returns:
        tuple: (df_processed, scaler_used, feature_columns)
            - df_processed: Preprocessed DataFrame with scaled features
            - scaler_used: The fitted (or provided) StandardScaler
            - feature_columns: List of feature column names (excluding target and date)
    """
    
    # Ensure date column is datetime
    if 'date' in df.columns and df['date'].dtype != 'datetime64[ns]':
        df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date to preserve temporal order
    if 'date' in df.columns:
        df = df.sort_values('date').reset_index(drop=True)
    
    # Handle missing values (forward fill for time-series)
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    df.fillna(0, inplace=True)
    
    # Extract feature columns (exclude date and target)
    feature_cols = [c for c in df.columns if c not in ['date', 'GDP_growth']]
    
    # Scale features
    if scaler is None:
        scaler = StandardScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
    else:
        # Use provided scaler (for inference)
        df[feature_cols] = scaler.transform(df[feature_cols])
    
    # Drop date from features if requested (but keep for reference)
    if drop_date and 'date' in df.columns:
        df_processed = df.drop(columns=['date'])
    else:
        df_processed = df
    
    # Return processed data, scaler, and feature list
    return df_processed, scaler, feature_cols


def get_temporal_train_test_split(df, test_years=2):
    """
    Split time-series data into train/test by date (no data leakage).
    
    Args:
        df (pd.DataFrame): DataFrame with 'date' column (datetime)
        test_years (int): Number of years to use for test set
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test, train_dates, test_dates)
    """
    
    if 'date' not in df.columns:
        raise ValueError("DataFrame must have a 'date' column")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Get unique years
    df['year'] = df['date'].dt.year
    unique_years = sorted(df['year'].unique())
    
    # Split: last `test_years` years for testing
    test_threshold_year = unique_years[-test_years]
    
    train_mask = df['year'] < test_threshold_year
    test_mask = df['year'] >= test_threshold_year
    
    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()
    
    # Extract features and target
    feature_cols = [c for c in df.columns if c not in ['date', 'GDP_growth', 'year']]
    
    X_train = train_df[feature_cols].values
    X_test = test_df[feature_cols].values
    y_train = train_df['GDP_growth'].values
    y_test = test_df['GDP_growth'].values
    
    train_dates = train_df['date'].values
    test_dates = test_df['date'].values
    
    return X_train, X_test, y_train, y_test, train_dates, test_dates


def create_classification_target(gdp_growth_series, threshold=0.05):
    """
    Convert regression target (GDP growth) to binary classification.
    
    Args:
        gdp_growth_series: Series or array of GDP growth rates
        threshold (float): Growth rate threshold for 'high growth' classification
    
    Returns:
        np.array: Binary classification (1 for high growth, 0 for low/negative growth)
    """
    return np.where(gdp_growth_series >= threshold, 1, 0)


if __name__ == "__main__":
    # Quick test
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    print("Time-series preprocessing module ready.")
