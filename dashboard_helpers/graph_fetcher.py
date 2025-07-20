# graph_fetcher.py
import os
from datetime import datetime

import yfinance as yf
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from fredapi import Fred

# ───────────────────  one-time FRED client  ───────────────────
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise RuntimeError("Missing FRED_API_KEY in .env")

fred = Fred(api_key=FRED_API_KEY)

# ───────────────────  Static look-up dicts  ───────────────────
YIELD_SERIES_IDS = {
    "3 Month": "DGS3MO",
    "2 Year":  "DGS2",
    "5 Year":  "DGS5",
    "10 Year": "DGS10",
    "30 Year": "DGS30",
}

CURVE_SERIES = YIELD_SERIES_IDS

# ───────────────────  Cached fetchers  ───────────────────

@st.cache_data(ttl=60 * 60 * 6)
def load_fred_data(start_date: str,
                   series_ids: dict,
                   freq: str = "W-FRI") -> pd.DataFrame:
    """
    Fetch daily data from FRED and optionally down-sample.

    freq = "D"      -> keep daily  
    freq = "W-FRI"  -> Friday weekly  
    freq = "M"      -> month-end
    """
    frames = []
    for name, sid in series_ids.items():
        ser = fred.get_series(sid, observation_start=start_date).rename(name)
        if freq != "D":
            ser = ser.resample(freq).last()
        frames.append(ser)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).ffill()



@st.cache_data(ttl=60 * 60 * 6)
def fetch_yield_curve(start_date="2024-01-01",
                      end_date=None,
                      freq="ME") -> pd.DataFrame:
    """Monthly (or custom freq) resample of the on-the-run curve."""
    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")

    df = pd.DataFrame({
        label: fred.get_series(sid,
                               observation_start=start_date,
                               observation_end=end_date)
        for label, sid in CURVE_SERIES.items()
    })
    return df.resample(freq).ffill()



def display_graph(curve):
    
    if not curve.empty:
        curve.index = pd.to_datetime(curve.index)
        st.line_chart(curve)
        st.dataframe(curve.tail())
    else:
        st.warning("No daily data.")


