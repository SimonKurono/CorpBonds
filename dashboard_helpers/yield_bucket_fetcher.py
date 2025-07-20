import os
from dotenv import load_dotenv
from fredapi import Fred
import streamlit as st
import pandas as pd

load_dotenv()
fred = Fred(api_key = os.getenv("FRED_API_KEY"))

YIELD_SERIES = {
    "AAA": "BAMLC0A1CAAAEY",
    "AA": "BAMLC0A2CAAEY",
    "A": "BAMLC0A3CAEY",
    "BBB": "BAMLC0A4CBBBEY",
    "BB": "BAMLH0A1HYBBEY",
    "B": "BAMLH0A2HYBEY",
    "CCC & Below": "BAMLH0A3HYCEY",
}

@st.cache_data(ttl=60*60*60)
def fetch_yield_by_rating(start_date: str = "2024-01-01",freq="W-FRI") -> pd.DataFrame:
    """
    Returns a dataframe with columns = ['AAA','AA',...'B'],
    indexed by date, all in basis points
    """

    df = pd.DataFrame({
        label: fred.get_series(sid, observation_start=start_date)*100
        for label, sid in YIELD_SERIES.items()
    })
    return df.resample(freq).ffill() 
