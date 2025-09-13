import os
from dotenv import load_dotenv
from fredapi import Fred
import streamlit as st
import pandas as pd

load_dotenv()
fred = Fred(api_key = os.getenv("FRED_API_KEY"))

OAS_SERIES = {
    "IG OAS": "BAMLC0A0CM",
    
    "HY OAS": "BAMLH0A0HYM2",
}

@st.cache_data(ttl=60*60*6)
def fetch_index_oas(start_date: str = None):
    """
    Fetches index OAS values and deltas from FRED,
    but only as far back as `start_date` (ISO 'YYYY-MM-DD').
    If start_date is None, pulls the full history.
    Returns a DataFrame with columns ['OAS (bp)', 'ΔOAS (bp)'].
    """
    out = {}
    for lbl, sid in OAS_SERIES.items():
        
        ser = fred.get_series(sid,
                              observation_start=start_date).dropna()

        
        if len(ser) >= 2:
            last, prev = ser.iloc[-1], ser.iloc[-2]
            out[lbl] = (last * 100, (last - prev) * 100)
        elif len(ser) == 1:
           
            out[lbl] = (ser.iloc[-1] * 100, 0.0)

    
    return pd.DataFrame.from_dict(
        out, orient="index", columns=["OAS (bp)", "ΔOAS (bp)"]
    )

@st.cache_data(ttl=60*60*6)
def fetch_index_oas_series(start_date: str = "2024-01-01") -> pd.DataFrame:
    """
    Fetches historical IG & HY index OAS (in basis points),
    returns a DataFrame with date index and two columns.
    """
    df = pd.DataFrame({
        lbl: fred.get_series(sid, observation_start=start_date) * 100
        for lbl, sid in OAS_SERIES.items()
    })
    return df.ffill()

@st.cache_data(ttl=60*60*6)
def fetch_treasury_series(start_date: str = "2024-01-01") -> pd.Series:
    # Pull DGS10 from FRED, convert % → bp
    ser = fred.get_series("DGS10", observation_start=start_date).dropna() * 100
    return ser


#oas by rating bucket:
RATING_OAS_SERIES = {
    "AAA OAS":  "BAMLC0A1CAAA",
    "AA OAS":   "BAMLC0A2CAA",
    "A OAS":    "BAMLC0A3CA",
    "BBB OAS":  "BAMLC0A4CBBB",
    "BB OAS":   "BAMLH0A1HYBB",
    "B OAS":    "BAMLH0A2HYB",
    "CCC OAS": "BAMLH0A3HYC",
    
}

@st.cache_data(ttl=60 * 60 * 6)
def fetch_oas_by_rating(start_date: str = "2024-01-01") -> pd.DataFrame:
    """
    Returns a DataFrame with columns = ['AAA OAS','AA OAS',...,'B OAS'],
    indexed by date, all in basis points.
    """
    df = pd.DataFrame({
        label: fred.get_series(sid, observation_start=start_date) * 100
        for label, sid in RATING_OAS_SERIES.items()
    })
    return df.ffill()   # forward-fill any missing days