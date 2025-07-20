
import os
from datetime import datetime
import pandas as pd
from fredapi import Fred
import yfinance as yf
from dotenv import load_dotenv

# ───────────────────  one-time FRED client  ───────────────────
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise RuntimeError("Missing FRED_API_KEY in .env")
fred = Fred(api_key=FRED_API_KEY)




# ───────────────────  Fetch MOVE from Yahoo ───────────────────
def fetch_move_yahoo_series(start_date: str) -> pd.DataFrame:
    """
    Fetches daily MOVE index from Yahoo Finance (as a fallback),
    returns a DataFrame with a single 'MOVE' column.
    """
    start_date = "max"
    hist = yf.Ticker("^MOVE").history(start_date)
    if hist.empty:
        return pd.DataFrame()
    df = hist["Close"].rename("MOVE").to_frame()
    return df.ffill()

# ───────────────────  Fetch CDS Proxy from Yahoo via CDX ───────────────────
# ETF proxy ticker for CDX NA IG index via X-Trackers ETF
CDS_PROXY_TICKER = "LQD"
def fetch_cds_proxy_series(start_date: str = "2005-01-01") -> pd.DataFrame:
    """
    Fetches the Simplify High Yield ETF (CDX) close prices from Yahoo Finance,
    returns a DataFrame with a 'CDX IG Proxy' column.
    """
    hist = yf.Ticker(CDS_PROXY_TICKER).history(start=start_date)
    if hist.empty:
        return pd.DataFrame()
    df = hist["Close"].rename("CDX IG Proxy").to_frame()
    return df


if __name__ == "__main__":
    

    df_move = fetch_move_yahoo_series()
    print("MOVE tail (FRED):\n", df_move.tail(), "\n")

    df_cds = fetch_cds_proxy_series()
    print("CDS Proxy tail:\n", df_cds.tail())


