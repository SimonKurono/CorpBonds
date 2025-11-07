# utils/fetchers/oas_fetcher.py ─────────────────────────────────────────────────────────
"""Fetchers for OAS (Option-Adjusted Spread) data from FRED."""

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
OAS_SERIES = {
    "IG OAS": "BAMLC0A0CM",
    "HY OAS": "BAMLH0A0HYM2",
}

RATING_OAS_SERIES = {
    "AAA OAS":  "BAMLC0A1CAAA",
    "AA OAS":   "BAMLC0A2CAA",
    "A OAS":    "BAMLC0A3CA",
    "BBB OAS":  "BAMLC0A4CBBB",
    "BB OAS":   "BAMLH0A1HYBB",
    "B OAS":    "BAMLH0A2HYB",
    "CCC OAS": "BAMLH0A3HYC",
}

TREASURY_10Y_SERIES = "DGS10"

# Cache TTLs (seconds)
TTL_OAS = 60 * 60 * 6

# Defaults
DEFAULT_START_DATE = "2024-01-01"
BP_MULTIPLIER = 100  # Convert percentage to basis points
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Fetch Functions ───────────────────────────╮
@st.cache_data(ttl=TTL_OAS)
def fetch_index_oas(start_date: str | None = None) -> pd.DataFrame:
    """
    Fetch index OAS values and deltas from FRED.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD). If None, pulls full history.
    
    Returns:
        DataFrame with columns ['OAS (bp)', 'ΔOAS (bp)']
    """
    out = {}
    for lbl, sid in OAS_SERIES.items():
        ser = fred.get_series(sid, observation_start=start_date).dropna()

        if len(ser) >= 2:
            last, prev = ser.iloc[-1], ser.iloc[-2]
            out[lbl] = (last * BP_MULTIPLIER, (last - prev) * BP_MULTIPLIER)
        elif len(ser) == 1:
            out[lbl] = (ser.iloc[-1] * BP_MULTIPLIER, 0.0)

    return pd.DataFrame.from_dict(
        out, orient="index", columns=["OAS (bp)", "ΔOAS (bp)"]
    )


@st.cache_data(ttl=TTL_OAS)
def fetch_index_oas_series(start_date: str = DEFAULT_START_DATE) -> pd.DataFrame:
    """
    Fetch historical IG & HY index OAS series.
    
    Args:
        start_date: Start date for data retrieval
    
    Returns:
        DataFrame with date index and two columns (IG OAS, HY OAS) in basis points
    """
    df = pd.DataFrame({
        lbl: fred.get_series(sid, observation_start=start_date) * BP_MULTIPLIER
        for lbl, sid in OAS_SERIES.items()
    })
    return df.ffill()


@st.cache_data(ttl=TTL_OAS)
def fetch_treasury_series(start_date: str = DEFAULT_START_DATE) -> pd.Series:
    """
    Fetch 10-year Treasury series from FRED.
    
    Args:
        start_date: Start date for data retrieval
    
    Returns:
        Series with 10-year Treasury yields in basis points
    """
    ser = fred.get_series(TREASURY_10Y_SERIES, observation_start=start_date).dropna() * BP_MULTIPLIER
    return ser


@st.cache_data(ttl=TTL_OAS)
def fetch_oas_by_rating(start_date: str = DEFAULT_START_DATE) -> pd.DataFrame:
    """
    Fetch OAS by rating bucket.
    
    Args:
        start_date: Start date for data retrieval
    
    Returns:
        DataFrame with columns ['AAA OAS', 'AA OAS', ..., 'CCC OAS'],
        indexed by date, all in basis points
    """
    df = pd.DataFrame({
        label: fred.get_series(sid, observation_start=start_date) * BP_MULTIPLIER
        for label, sid in RATING_OAS_SERIES.items()
    })
    return df.ffill()  # forward-fill any missing days
# ╰─────────────────────────────────────────────────────────────────╯
