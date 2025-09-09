import pandas as pd
import numpy as np

def calculate_moving_averages(data, windows=[20, 50, 200]):
    """
    Calculate moving averages for given windows.
    
    Parameters:
    data (pd.DataFrame): DataFrame with a 'Close' column.
    windows (list): List of window sizes for moving averages.
    
    Returns:
    pd.DataFrame: DataFrame with additional columns for each moving average.
    """
    for window in windows:
        data[f'MA_{window}'] = data['Close'].rolling(window=window).mean()
    return data

def moving_average_strategy(data):
    """
    Simple moving average crossover strategy.
    
    Parameters:
    data (pd.DataFrame): DataFrame with 'Close' and moving average columns.
    
    Returns:
    pd.DataFrame: DataFrame with buy/sell signals.
    """
    data['Signal'] = 0
    data['Signal'][data['MA_20'] > data['MA_50']] = 1
    data['Signal'][data['MA_20'] < data['MA_50']] = -1
    data['Position'] = data['Signal'].diff()
    return data