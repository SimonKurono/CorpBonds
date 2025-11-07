# utils/quant/moving_average_analysis.py ─────────────────────────────────────────────────────────
"""Moving average analysis and strategy backtesting utilities."""

from __future__ import annotations

# ── Third-party
import numpy as np
import pandas as pd


# ╭─────────────────────────── Constants ───────────────────────────╮
DEFAULT_WINDOWS = [20, 50, 200]
DEFAULT_INITIAL_CAPITAL = 10000
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Analysis Functions ───────────────────────────╮
def calculate_moving_averages(
    data: pd.DataFrame,
    windows: list[int] = DEFAULT_WINDOWS
) -> pd.DataFrame:
    """
    Calculate moving averages for given windows.
    
    Args:
        data: DataFrame with a 'Close' column
        windows: List of window sizes for moving averages
    
    Returns:
        DataFrame with additional columns for each moving average
    """
    for window in windows:
        data[f'MA_{window}'] = data['Close'].rolling(window=window).mean()
    return data


def moving_average_strategy(data: pd.DataFrame) -> pd.DataFrame:
    """
    Simple moving average crossover strategy.
    
    Generates buy/sell signals based on MA_20 crossing above/below MA_50.
    
    Args:
        data: DataFrame with 'Close' and moving average columns
    
    Returns:
        DataFrame with 'Signal' and 'Position' columns added
    """
    data = data.copy()
    data['Signal'] = 0
    data.loc[data['MA_20'] > data['MA_50'], 'Signal'] = 1
    data.loc[data['MA_20'] < data['MA_50'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data


def backtest_strategy(
    data: pd.DataFrame,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL
) -> pd.DataFrame:
    """
    Backtest the moving average strategy.
    
    Args:
        data: DataFrame with 'Close' and 'Position' columns
        initial_capital: Starting capital for backtesting
    
    Returns:
        DataFrame with 'Portfolio Value' column added
    """
    data = data.copy()
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
    
    # If holding a position at the end, sell it
    if position > 0:
        data['Portfolio Value'].iloc[-1] = position * data['Close'].iloc[-1]
    
    return data
# ╰─────────────────────────────────────────────────────────────────╯
