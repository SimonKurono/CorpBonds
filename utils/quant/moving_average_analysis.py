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

def backtest_strategy(data, initial_capital=10000):
    """
    Backtest the moving average strategy.
    
    Parameters:
    data (pd.DataFrame): DataFrame with 'Close' and 'Position' columns.
    initial_capital (float): Starting capital for backtesting.
    
    Returns:
    pd.DataFrame: DataFrame with portfolio value over time.
    """
    data['Portfolio Value'] = initial_capital
    position = 0
    for i in range(1, len(data)):
        if data['Position'].iloc[i] == 1:  # Buy signal
            position = data['Portfolio Value'].iloc[i-1] / data['Close'].iloc[i]
            data['Portfolio Value'].iloc[i] = 0
        elif data['Position'].iloc[i] == -1 and position > 0:  # Sell signal
            data['Portfolio Value'].iloc[i] = position * data['Close'].iloc[i]
            position = 0
        else:
            data['Portfolio Value'].iloc[i] = data['Portfolio Value'].iloc[i-1]
    
    if position > 0:  # If holding a position at the end, sell it
        data['Portfolio Value'].iloc[-1] = position * data['Close'].iloc[-1]
    
    return data