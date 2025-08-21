from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="Quant — Step 1 (Baseline)", layout="wide")
st.title("Quant — Baseline Chart")

# We'll make TZ configurable later; for now fix to PT as your local default
TZ = timezone(timedelta(hours=-7))  # America/Vancouver-ish

# ---------------------------
# Pure helpers (tiny and typed)
# ---------------------------

def default_window() -> Tuple[datetime, datetime, str]:
    """Return the default lookback and interval: ~6 months of daily data."""
    end = datetime.now(tz=TZ)
    start = end - timedelta(days=185)
    return start, end, "1d"



@st.cache_data(ttl=600, show_spinner=False)
def load_history(symbol: str, start: datetime, end: datetime, interval: str) -> pd.DataFrame:
    """Download OHLCV with auto-adjust. Falls back to 1d if intraday fails."""
    if not symbol:
        return pd.DataFrame()
    try:
        df = yf.download(
        symbol,
        start=start,
        end=end + timedelta(days=1),
        interval=interval,
        auto_adjust=True,
        progress=False,
        )
        if df.empty and interval != "1d":
            df = yf.download(symbol, start=start, end=end + timedelta(days=1), interval="1d", auto_adjust=True, progress=False)
    except Exception:
        df = pd.DataFrame()
        if df.empty:
            return df
    df.index = pd.to_datetime(df.index)
    # Normalize columns to Title case (Open, High, Low, Close, Volume)
    df.rename(columns=str.capitalize, inplace=True)
    return df

def plot_line(df: pd.DataFrame, title: str) -> None:
    if df is None or df.empty: 
        st.warning("No data for this ticker/range")
        return
    y = df["Close"] if "Close" in df.columns else df.select_dtypes("number".iloc[:, 0])
    fig = go.Figure(go.Scatter(x = df.index, y=y, mode =- "lines", name = title))
    fig.update_layout(height=460, margin=dict(l=8, r=8, t=40, b=8), title=title)
    st.plotly_chart(fig, use_container_width=True)