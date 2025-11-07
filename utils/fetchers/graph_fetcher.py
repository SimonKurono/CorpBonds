# utils/fetchers/graph_fetcher.py ─────────────────────────────────────────────────────────
"""Fetchers for yield curve and treasury data from FRED."""

from __future__ import annotations

# ── Stdlib
import os
from datetime import datetime

# ── Third-party
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from fredapi import Fred

# ── Initialize environment ──
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise RuntimeError("Missing FRED_API_KEY in .env")

fred = Fred(api_key=FRED_API_KEY)


# ╭─────────────────────────── Constants ───────────────────────────╮
YIELD_SERIES_IDS = {
    "3 Month": "DGS3MO",
    "2 Year":  "DGS2",
    "5 Year":  "DGS5",
    "10 Year": "DGS10",
    "30 Year": "DGS30",
}

CURVE_SERIES = YIELD_SERIES_IDS

# Cache TTLs (seconds)
TTL_FRED_DATA = 60 * 60 * 6
TTL_YIELD_CURVE = 60 * 60 * 6

# Default frequencies
FREQ_DAILY = "D"
FREQ_WEEKLY_FRI = "W-FRI"
FREQ_MONTH_END = "ME"
DEFAULT_FREQ = FREQ_WEEKLY_FRI
DEFAULT_START_DATE = "2024-01-01"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Fetch Functions ───────────────────────────╮
@st.cache_data(ttl=TTL_FRED_DATA)
def load_fred_data(
    start_date: str,
    series_ids: dict[str, str],
    freq: str = DEFAULT_FREQ
) -> pd.DataFrame:
    """
    Fetch daily data from FRED and optionally down-sample.
    
    Args:
        start_date: Start date for data retrieval
        series_ids: Dictionary mapping series names to FRED series IDs
        freq: Resampling frequency
            - "D"      -> keep daily
            - "W-FRI"  -> Friday weekly
            - "M"      -> month-end
    
    Returns:
        DataFrame with requested series
    """
    frames = []
    for name, sid in series_ids.items():
        ser = fred.get_series(sid, observation_start=start_date).rename(name)
        if freq != FREQ_DAILY:
            ser = ser.resample(freq).last()
        frames.append(ser)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).ffill()


@st.cache_data(ttl=TTL_YIELD_CURVE)
def fetch_yield_curve(
    start_date: str = DEFAULT_START_DATE,
    end_date: str | None = None,
    freq: str = FREQ_MONTH_END
) -> pd.DataFrame:
    """
    Fetch monthly (or custom frequency) resample of the on-the-run curve.
    
    Args:
        start_date: Start date for data retrieval
        end_date: End date for data retrieval (defaults to today)
        freq: Resampling frequency
    
    Returns:
        DataFrame with yield curve data
    """
    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")

    df = pd.DataFrame({
        label: fred.get_series(
            sid,
            observation_start=start_date,
            observation_end=end_date
        )
        for label, sid in CURVE_SERIES.items()
    })
    return df.resample(freq).ffill()


def display_graph(curve: pd.DataFrame) -> None:
    """
    Display a yield curve graph and data table.
    
    Args:
        curve: DataFrame with yield curve data
    """
    if not curve.empty:
        curve.index = pd.to_datetime(curve.index)
        st.line_chart(curve)
        st.dataframe(curve.tail())
    else:
        st.warning("No daily data.")
# ╰─────────────────────────────────────────────────────────────────╯

