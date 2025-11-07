# utils/fetchers/rate_fetcher.py ─────────────────────────────────────────────────────────
"""Fetchers for core interest rates from FRED."""

from __future__ import annotations

# ── Stdlib
import os

# ── Third-party
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

# Cache TTLs (seconds)
TTL_CORE_RATES = 60 * 60 * 6
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Fetch Functions ───────────────────────────╮
@st.cache_data(ttl=TTL_CORE_RATES)
def fetch_core_rates() -> dict[str, tuple[float, float]]:
    """
    Fetch latest core interest rates and their deltas from FRED.
    
    Returns:
        Dictionary mapping rate names to tuples of (current_value, delta)
    """
    latest = {}
    for lbl, sid in SERIES.items():
        ser = fred.get_series(sid).dropna()
        last, prev = ser.iloc[-1], ser.iloc[-2]
        latest[lbl] = (last, last - prev)  # tuple (value, delta)
    return latest
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main entry point for testing rate fetcher."""
    out = fetch_core_rates()  # bypass Streamlit cache
    for k, v in out.items():
        print(k, "→", v, type(v))


if __name__ == "__main__":
    main()

