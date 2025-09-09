import os
from dotenv import load_dotenv
from fredapi import Fred
import streamlit as st

load_dotenv()
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

SERIES = {
    "Fed Funds":            "FEDFUNDS",
    "2 Year":               "DGS2",
    "5 Year":               "DGS5",
    "10 Year":              "DGS10",
    "30 Year":              "DGS30",
    "SOFR (O/N)":           "SOFR",
    "SOFR 90-Day Avg":      "SOFR90DAYAVG",
    "5-Year USD Swap Rate": "DSWP5",
    "10-Yr TIPS Breakeven": "T10YIE",
}


@st.cache_data(ttl=60*60*6)
def fetch_core_rates():
    latest = {}
    for lbl, sid in SERIES.items():
        ser = fred.get_series(sid).dropna()
        last, prev = ser.iloc[-1], ser.iloc[-2]
        latest[lbl] = (last, last - prev)   # ← tuple (value, delta)
    return latest


if __name__ == "__main__":
    out = fetch_core_rates()      # bypass Streamlit cache
    for k, v in out.items():
        print(k, "→", v, type(v))
