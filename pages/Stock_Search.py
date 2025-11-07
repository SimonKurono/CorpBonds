# pages/Stock_Search.py ─────────────────────────────────────────────────────────
"""Stock Search and Analysis Page.

Features:
- Search for stocks and ETFs
- Compare performance with benchmarks
- View company information and charts
"""

from __future__ import annotations

# ── Stdlib
from datetime import date, datetime
from typing import Optional

# ── Third-party
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ── Local
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
DEFAULT_TICKER = "AAPL"
DEFAULT_BENCHMARK = "SPY"
DEFAULT_START_DATE = "2023-01-01"
FIG_TEMPLATE = "plotly_white"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Helpers and caching ──────────────────────╮
def get_stock_data(ticker_symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
    """
    Fetch historical stock data from Yahoo Finance for a given ticker.
    
    Args:
        ticker_symbol: Stock or ETF ticker symbol
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
    
    Returns:
        DataFrame with stock data or None if error occurs
    """
    try:
        data = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)
        if data.empty:
            st.error(f"No data found for ticker '{ticker_symbol}'. It might be an invalid ticker or delisted.")
            return None

        if pd.api.types.is_datetime64_any_dtype(data.index):
            data.index = data.index.tz_localize(None)

        return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None


def plot_normalized_data(
    data: pd.DataFrame,
    benchmark_data: Optional[pd.DataFrame],
    primary_ticker: str,
    benchmark_ticker: Optional[str],
) -> go.Figure:
    """
    Create an interactive Plotly chart showing normalized performance.
    
    Normalizes both series to start at 100 for fair performance comparison.
    
    Args:
        data: Primary stock data DataFrame
        benchmark_data: Optional benchmark data DataFrame
        primary_ticker: Primary ticker symbol
        benchmark_ticker: Optional benchmark ticker symbol
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Reset data columns to standard format if needed
    if isinstance(data.columns, pd.MultiIndex):
        data = data.droplevel(1, axis=1)
    if benchmark_data is not None and isinstance(benchmark_data.columns, pd.MultiIndex):
        benchmark_data = benchmark_data.droplevel(1, axis=1)

    # Normalize the data: divide each closing price by the first closing price and multiply by 100
    primary_normalized = (data['Close'] / data['Close'].iloc[0]) * 100

    # Add primary stock trace
    fig.add_trace(go.Scatter(
        x=primary_normalized.index,
        y=primary_normalized,
        mode='lines',
        name=primary_ticker
    ))

    # Add benchmark trace if data is available
    if benchmark_data is not None and not benchmark_data.empty:
        benchmark_normalized = (benchmark_data['Close'] / benchmark_data['Close'].iloc[0]) * 100
        fig.add_trace(go.Scatter(
            x=benchmark_normalized.index,
            y=benchmark_normalized,
            mode='lines',
            name=f"{benchmark_ticker} (Benchmark)",
            line=dict(dash='dot', color='orange')
        ))

    # Customize layout for the normalized chart
    title = f'Performance Chart: {primary_ticker} vs. {benchmark_ticker}' if benchmark_ticker else f'{primary_ticker} Performance'
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Normalized Price (Start = 100)',
        legend_title='Ticker',
        template=FIG_TEMPLATE
    )
    return fig
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Financial Asset Search & Analysis", page_icon="📈", layout="wide")
    ui.render_sidebar()


def render_search_parameters() -> tuple[str, Optional[str], date, date]:
    """Render search parameter inputs and return user selections."""
    st.header("Search Parameters")
    ticker_col1, ticker_col2, col1, col2 = st.columns(4)

    with ticker_col1:
        primary_ticker = st.text_input("Enter a Stock or ETF Ticker", DEFAULT_TICKER).upper()
    with ticker_col2:
        benchmark_ticker_input = st.text_input("Enter a Benchmark Ticker (Optional)", DEFAULT_BENCHMARK).upper()
        benchmark_ticker = benchmark_ticker_input if benchmark_ticker_input else None
    with col1:
        start_date = st.date_input("Start Date", pd.to_datetime(DEFAULT_START_DATE))
    with col2:
        end_date = st.date_input("End Date", pd.to_datetime("today"))

    st.write("---")

    return primary_ticker, benchmark_ticker, start_date, end_date


def render_stock_info(ticker: str) -> None:
    """Render company information for the given ticker."""
    ticker_info = yf.Ticker(ticker)

    st.header(f"{ticker_info.info.get('longName', ticker)} ({ticker})")

    sector, industry = st.columns([1, 1])
    with sector:
        st.info(f"**Sector:** {ticker_info.info.get('sector', 'N/A')}")
    with industry:
        st.info(f"**Industry:** {ticker_info.info.get('industry', 'N/A')}")

    with st.expander("Business Summary"):
        st.write(ticker_info.info.get('longBusinessSummary', 'No description available.'))


def render_chart(primary_ticker: str, benchmark_ticker: Optional[str], start_date: date, end_date: date) -> None:
    """Render normalized performance chart."""
    stock_data = get_stock_data(primary_ticker, start_date, end_date)

    if stock_data is None or stock_data.empty:
        return

    render_stock_info(primary_ticker)

    benchmark_data = None
    if benchmark_ticker:
        benchmark_data = get_stock_data(benchmark_ticker, start_date, end_date)

    # Render normalized performance chart
    fig = plot_normalized_data(stock_data, benchmark_data, primary_ticker, benchmark_ticker)
    st.plotly_chart(fig, use_container_width=True)

    # Display raw data snapshot
    st.subheader("Raw Data Snapshot")
    st.dataframe(stock_data.tail())
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()

    # Get search parameters from UI
    primary_ticker, benchmark_ticker, start_date, end_date = render_search_parameters()

    # Render chart if ticker is provided
    if primary_ticker:
        render_chart(primary_ticker, benchmark_ticker, start_date, end_date)


if __name__ == "__main__":
    main()
