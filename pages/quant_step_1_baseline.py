# quant_step1_baseline.py
# -------------------------------------------------------------
# STEP 1 — the smallest vertical slice:
# Input a ticker → fetch 6M daily prices via yfinance → plot a clean line chart.
# Keep it tiny, typed, and testable. We'll add timeframes/search/providers next.
# -------------------------------------------------------------

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


st.set_page_config(page_title="Quant — Step 1 (Baseline)", layout="wide")
st.title("Quant — Baseline Chart")

TZ = ZoneInfo("America/Vancouver")


def default_window() -> Tuple[datetime, datetime, str]:
    """Return the default lookback and interval: ~6 months of daily data."""
    end = datetime.now(TZ)
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
            start=start.replace(tzinfo=None),
            end=(end + timedelta(days=1)).replace(tzinfo=None),  # ensure naive datetimes
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
        if df.empty and interval != "1d":
            df = yf.download(
                symbol,
                start=start.replace(tzinfo=None),
                end=(end + timedelta(days=1)).replace(tzinfo=None),
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
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
        st.warning("No data for this ticker/range.")
        return
    # Prefer Close if present; else first numeric column
    y_col = "Close" if "Close" in df.columns else df.select_dtypes(include=["number"]).columns[0]
    fig = go.Figure(go.Scatter(x=df.index, y=df[y_col], mode="lines", name=title))
    
    # Add template="plotly_dark" to make the line visible on dark backgrounds
    fig.update_layout(
        template="plotly_dark",
        height=460, 
        margin=dict(l=8, r=8, t=40, b=8), 
        title=title
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# UI (intentionally minimal for Step 1)
# ---------------------------

symbol = st.text_input("Ticker", placeholder="e.g., LQD, IEF, TLT, AAPL").strip().upper()

if symbol:
    start, end, interval = default_window()
    df = load_history(symbol, start, end, interval)

    col_plot, col_meta = st.columns([3, 2])
    with col_plot:
        plot_line(df, symbol)
    with col_meta:
        st.subheader("Snapshot (raw)")
        # Keep this very light for now; we'll replace with a proper meta card later
        if not df.empty:
            st.caption("Last 5 rows")
            st.dataframe(df.tail(5))
        else:
            st.info("No data downloaded yet.")
else:
    st.info("Enter a ticker to start. We'll add search & timeframes in Step 2.")