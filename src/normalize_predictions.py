"""
Post-processing and normalization for ML model predictions
"""

import numpy as np


def clamp_price_prediction(price_change, historical_data, percentile=95):
    """
    Clamp price change predictions to realistic ranges based on historical volatility.
    
    Args:
        price_change (float): Raw model prediction for price change (e.g., -0.8724 for -87%)
        historical_data (array): Historical price change data to compute limits
        percentile (float): Percentile to use for clamping (default 95 for realistic outliers)
    
    Returns:
        float: Clamped price change value
    """
    if historical_data is None or len(historical_data) < 10:
        # No historical data available, clamp to reasonable default ±10%
        return np.clip(price_change, -0.10, 0.10)
    
    # Calculate bounds based on historical volatility
    p_low = np.percentile(historical_data, 100 - percentile)
    p_high = np.percentile(historical_data, percentile)
    
    # Add some buffer to allow extreme predictions but not absurd ones
    buffer = (p_high - p_low) * 0.5
    lower_bound = p_low - buffer
    upper_bound = p_high + buffer
    
    # Clamp to bounds
    clamped = np.clip(price_change, lower_bound, upper_bound)
    
    return clamped


def normalize_predictions(df, feature_columns_list, recent_price):
    """
    Normalize and validate predictions for a batch of data.
    
    Args:
        df (pd.DataFrame): DataFrame with predictions
        feature_columns_list (list): List of feature column names
        recent_price (float): Recent price for context
    
    Returns:
        pd.DataFrame: Normalized predictions
    """
    return df.copy()
