# utils/fetchers/yield_bucket_fetcher.py ─────────────────────────────────────────────────────────
"""Fetchers for yield data by rating bucket from FRED."""

from __future__ import annotations

# ── Stdlib
import os

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
YIELD_SERIES = {
    "AAA": "BAMLC0A1CAAAEY",
    "AA": "BAMLC0A2CAAEY",
    "A": "BAMLC0A3CAEY",
    "BBB": "BAMLC0A4CBBBEY",
    "BB": "BAMLH0A1HYBBEY",
    "B": "BAMLH0A2HYBEY",
    "CCC & Below": "BAMLH0A3HYCEY",
}

# Cache TTLs (seconds)
TTL_YIELD_BY_RATING = 60 * 60 * 60

# Defaults
DEFAULT_START_DATE = "2024-01-01"
DEFAULT_FREQ = "W-FRI"
BP_MULTIPLIER = 100  # Convert percentage to basis points
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Fetch Functions ───────────────────────────╮
@st.cache_data(ttl=TTL_YIELD_BY_RATING)
def fetch_yield_by_rating(start_date: str = DEFAULT_START_DATE, freq: str = DEFAULT_FREQ) -> pd.DataFrame:
    """
    Fetch yield data by rating bucket.
    
    Args:
        start_date: Start date for data retrieval
        freq: Resampling frequency (default: "W-FRI" for weekly Friday)
    
    Returns:
        DataFrame with columns = ['AAA', 'AA', ..., 'CCC & Below'],
        indexed by date, all in basis points
    """
    df = pd.DataFrame({
        label: fred.get_series(sid, observation_start=start_date) * BP_MULTIPLIER
        for label, sid in YIELD_SERIES.items()
    })
    return df.resample(freq).ffill()
# ╰─────────────────────────────────────────────────────────────────╯
 
