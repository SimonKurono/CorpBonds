from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="Quant — Step 1 (Baseline)", layout="wide")
st.title("Quant — Baseline Chart")

# We'll make TZ configurable later; for now fix to PT as your local default
TZ = timezone(timedelta(hours=-7))  # America/Vancouver-ish

# ---------------------------
# Pure helpers (tiny and typed)
# ---------------------------

def default_window() -> Tuple[datetime, datetime, str]:
    """Return the default lookback and interval: ~6 months of daily data."""
    end = datetime.now(tz=TZ)
    start = end - timedelta(days=185)
    return start, end, "1d"