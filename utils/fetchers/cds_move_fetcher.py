# utils/fetchers/cds_move_fetcher.py ─────────────────────────────────────────────────────────
"""Fetchers for CDS and MOVE index data."""

from __future__ import annotations

# ── Stdlib
import os

# ── Third-party
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred

# ── Initialize environment ──
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise RuntimeError("Missing FRED_API_KEY in .env")

fred = Fred(api_key=FRED_API_KEY)


# ╭─────────────────────────── Constants ───────────────────────────╮
CDS_PROXY_TICKER = "LQD"  # ETF proxy ticker for CDX NA IG index via X-Trackers ETF
MOVE_TICKER = "^MOVE"
DEFAULT_CDS_START_DATE = "2005-01-01"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Fetch Functions ───────────────────────────╮
def fetch_move_yahoo_series(start_date: str = "max") -> pd.DataFrame:
    """
    Fetch daily MOVE index from Yahoo Finance.
    
    Args:
        start_date: Start date for data retrieval (default: "max" for all history)
    
    Returns:
        DataFrame with a single 'MOVE' column
    """
    # Determine if start_date is a period alias or a date
    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
    if start_date in valid_periods:
        hist = yf.Ticker(MOVE_TICKER).history(period=start_date)
    else:
        # Assume it's a date string
        hist = yf.Ticker(MOVE_TICKER).history(start=start_date)
    if hist.empty:
        return pd.DataFrame()
    df = hist["Close"].rename("MOVE").to_frame()
    return df.ffill()


def fetch_cds_proxy_series(start_date: str = DEFAULT_CDS_START_DATE) -> pd.DataFrame:
    """
    Fetch CDX IG proxy from Yahoo Finance via LQD ETF.
    
    Args:
        start_date: Start date for data retrieval
    
    Returns:
        DataFrame with a 'CDX IG Proxy' column
    """
    hist = yf.Ticker(CDS_PROXY_TICKER).history(start=start_date)
    if hist.empty:
        return pd.DataFrame()
    df = hist["Close"].rename("CDX IG Proxy").to_frame()
    return df
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main entry point for testing fetchers."""
    df_move = fetch_move_yahoo_series()
    print("MOVE tail:\n", df_move.tail(), "\n")

    df_cds = fetch_cds_proxy_series()
    print("CDS Proxy tail:\n", df_cds.tail())


if __name__ == "__main__":
    main()

