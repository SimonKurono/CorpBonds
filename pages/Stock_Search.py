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
import numpy as np

# ── Local
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
DEFAULT_TICKER = "AAPL"
DEFAULT_START_DATE = "2023-01-01"
FIG_TEMPLATE = "plotly_white"
DEFAULT_BENCHMARKS = ["SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "LQD", "JNK", "BIL"]
DEFAULT_BENCHMARK = "SPY"
MAX_BENCHMARKS = 5
ANALYST_BUY_THRESHOLD = 0.10
ANALYST_SELL_THRESHOLD = -0.05
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
        if isinstance(data.columns, pd.MultiIndex):
            data = data.droplevel(1, axis=1)
        return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None


def get_multiple_stock_data(
    tickers: list[str],
    start_date: date,
    end_date: date,
) -> dict[str, pd.DataFrame]:
    """Fetch historical data for multiple tickers (max configured)."""
    datasets: dict[str, pd.DataFrame] = {}
    seen: set[str] = set()
    for ticker in tickers:
        symbol = ticker.upper().strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        if len(datasets) >= MAX_BENCHMARKS:
            break
        data = get_stock_data(symbol, start_date, end_date)
        if data is not None and not data.empty:
            datasets[symbol] = data
    return datasets


def plot_normalized_data(
    data: pd.DataFrame,
    benchmark_data: dict[str, pd.DataFrame],
    primary_ticker: str,
) -> go.Figure:
    """
    Create an interactive Plotly chart showing normalized performance.

    Normalizes all series to start at 100 for fair performance comparison.
    """
    fig = go.Figure()

    primary_close = _closing_price_series(data)
    primary_normalized = _normalize_series(primary_close)

    fig.add_trace(
        go.Scatter(
            x=primary_normalized.index,
            y=primary_normalized,
            mode="lines",
            name=primary_ticker,
        )
    )

    for benchmark_ticker, benchmark_df in benchmark_data.items():
        benchmark_close = _closing_price_series(benchmark_df)
        if benchmark_close.empty:
            continue
        benchmark_normalized = _normalize_series(benchmark_close)
        fig.add_trace(
            go.Scatter(
                x=benchmark_normalized.index,
                y=benchmark_normalized,
                mode="lines",
                name=f"{benchmark_ticker} (Benchmark)",
                line=dict(dash="dot"),
            )
        )

    benchmark_label = ", ".join(benchmark_data.keys())
    title = f"Performance: {primary_ticker} vs. {benchmark_label}" if benchmark_label else f"{primary_ticker} Performance"
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Normalized Price (Start = 100)",
        legend_title="Ticker",
        template=FIG_TEMPLATE,
    )
    return fig


def _closing_price_series(data: pd.DataFrame) -> pd.Series:
    """Extract a clean close-price series from a stock DataFrame."""
    if "Close" in data.columns:
        series = data["Close"]
    elif not data.columns.empty:
        series = data.iloc[:, 0]
    else:
        series = pd.Series(dtype=float)
    series = series.sort_index().dropna()
    if isinstance(series.index, pd.DatetimeIndex) and series.index.tz is not None:
        series.index = series.index.tz_localize(None)
    return series


def _normalize_series(series: pd.Series) -> pd.Series:
    """Normalize price series to start at 100."""
    if series.empty:
        return series
    base_value = series.iloc[0]
    if base_value == 0:
        return series
    return (series / base_value) * 100


def fetch_extended_ticker_data(
    ticker: str,
    start_date: date,
    end_date: date,
) -> dict[str, Optional[pd.DataFrame]]:
    """Fetch supplemental datasets and metadata for a ticker."""
    ticker_obj = yf.Ticker(ticker)
    info = getattr(ticker_obj, "info", {}) or {}
    raw_targets = getattr(ticker_obj, "analyst_price_targets", None)
    price_targets = _to_standard_frame(raw_targets) if raw_targets is not None else None
    calendar = _to_standard_frame(getattr(ticker_obj, "calendar", None))
    income_stmt = _to_standard_frame(getattr(ticker_obj, "quarterly_income_stmt", None))
    history_1mo = _to_standard_frame(ticker_obj.history(period="1mo"))
    option_chain = _fetch_option_chain(ticker_obj)
    benchmark_series = _fetch_benchmark_close_series(start_date, end_date)

    return {
        "info": info,
        "price_targets": price_targets,
        "calendar": calendar,
        "income_stmt": income_stmt,
        "history": history_1mo,
        "option_chain": option_chain,
        "benchmark": benchmark_series,
    }


def _to_standard_frame(data: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Return a dataframe with a clean index, or None."""
    if data is None or isinstance(data, dict):
        return pd.DataFrame(data) if data else None
    if isinstance(data, pd.DataFrame):
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    return None


def _fetch_option_chain(ticker_obj: yf.Ticker) -> Optional[pd.DataFrame]:
    """Return option chain dataframe for the nearest expiry."""
    try:
        expiries = getattr(ticker_obj, "options", [])
        if not expiries:
            return None
        chain = ticker_obj.option_chain(expiries[0])
        return chain.calls
    except Exception:
        return None


def _fetch_benchmark_close_series(start_date: date, end_date: date) -> pd.Series:
    """Fetch SPY close prices for beta calculation."""
    spy_data = get_stock_data(DEFAULT_BENCHMARK, start_date, end_date)
    if spy_data is None or spy_data.empty:
        return pd.Series(dtype=float)
    return _closing_price_series(spy_data)


def compute_price_statistics(
    close_series: pd.Series,
    benchmark_series: pd.Series,
    price_targets: Optional[dict],
) -> dict[str, Optional[float]]:
    """Compute descriptive statistics, beta, and analyst recommendation."""
    stats = {
        "mean": None,
        "std": None,
        "var": None,
        "beta": None,
        "market_cap": None,
        "analyst_mean": None,
        "analyst_rating": "N/A",
        "analyst_diff": None,
    }
    if close_series.empty:
        return stats

    stats["mean"] = float(close_series.mean())
    stats["std"] = float(close_series.std())
    stats["var"] = float(close_series.var())

    if not benchmark_series.empty:
        stats["beta"] = _compute_beta(close_series, benchmark_series)

    stats["analyst_mean"], stats["analyst_rating"], stats["analyst_diff"] = _summarize_price_targets(
        close_series.iloc[-1], price_targets
    )
    return stats


def _compute_beta(close_series: pd.Series, benchmark_series: pd.Series) -> Optional[float]:
    """Compute beta of the asset versus benchmark."""
    returns = close_series.pct_change().dropna()
    benchmark_returns = benchmark_series.reindex(returns.index).pct_change().dropna()
    if returns.empty or benchmark_returns.empty:
        return None
    aligned = pd.concat([returns, benchmark_returns], axis=1, join="inner").dropna()
    if aligned.empty:
        return None
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1]
    var = np.var(aligned.iloc[:, 1])
    if var == 0:
        return None
    return float(cov / var)


def _summarize_price_targets(
    current_price: float,
    price_targets: Optional[pd.DataFrame],
) -> tuple[Optional[float], str, Optional[str]]:
    """Summarize analyst price targets into a rating."""
    if current_price <= 0 or not price_targets:
        return None, "N/A", None

    mean_target = None
    if isinstance(price_targets, pd.DataFrame):
        first_row = price_targets.iloc[0] if not price_targets.empty else None
        if first_row is not None:
            mean_target = first_row.get("targetMean") or first_row.get("mean")
    elif isinstance(price_targets, dict):
        mean_target = price_targets.get("mean") or price_targets.get("targetMean")

    if not mean_target:
        return None, "N/A", None

    diff_pct = (mean_target - current_price) / current_price
    if diff_pct >= ANALYST_BUY_THRESHOLD:
        rating = "Buy"
    elif diff_pct <= ANALYST_SELL_THRESHOLD:
        rating = "Sell"
    else:
        rating = "Hold"

    return float(mean_target), rating, f"{diff_pct:+.1%}"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Financial Asset Search & Analysis", page_icon="📈", layout="wide")
    ui.render_sidebar()


def render_search_parameters() -> tuple[str, list[str], date, date]:
    """Render search parameter inputs and return user selections."""
    st.header("Search Parameters")
    ticker_col1, ticker_col2, col1, col2 = st.columns(4)

    with ticker_col1:
        primary_ticker = st.text_input("Enter a Stock or ETF Ticker", DEFAULT_TICKER).upper()
    with ticker_col2:
        benchmark_ticker_inputs = st.multiselect(
            "Select Benchmark Tickers (Optional)",
            options=DEFAULT_BENCHMARKS,
            default=[DEFAULT_BENCHMARK],
            key="benchmark_ticker_input",
            max_selections=MAX_BENCHMARKS,
        )
    with col1:
        start_date = st.date_input("Start Date", pd.to_datetime(DEFAULT_START_DATE))
    with col2:
        end_date = st.date_input("End Date", pd.to_datetime("today"))

    st.write("---")

    return primary_ticker, benchmark_ticker_inputs, start_date, end_date


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


def render_extended_sections(
    ticker: str,
    market_cap: Optional[float],
    stats: dict[str, Optional[float]],
    extended_data: dict[str, Optional[pd.DataFrame]],
) -> None:
    """Render additional analytics, analyst targets, and reference tables."""
    st.subheader("Analyst & Market Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Market Cap", _format_currency(market_cap))
    with col2:
        st.metric("Daily Std Dev", _format_number(stats.get("std")))
    with col3:
        st.metric("Daily Mean", _format_number(stats.get("mean")))
    with col4:
        st.metric("Daily Variance", _format_number(stats.get("var")))

    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("Beta vs SPY", _format_number(stats.get("beta")))
    with col6:
        st.metric(
            "Analyst Target",
            _format_currency(stats.get("analyst_mean")),
            stats.get("analyst_diff"),
        )
    with col7:
        st.metric("Analyst Rating", stats.get("analyst_rating", "N/A"))

    st.subheader("Reference Materials")
    with st.expander("Analyst Price Targets"):
        targets = extended_data.get("price_targets")
        if targets:
            st.dataframe(pd.DataFrame([targets]))
        else:
            st.info("No analyst price target data available.")

    with st.expander("Upcoming Events (Calendar)"):
        calendar_df = extended_data.get("calendar")
        if isinstance(calendar_df, pd.DataFrame) and not calendar_df.empty:
            st.dataframe(calendar_df)
        else:
            st.info("No calendar data available.")

    with st.expander("Quarterly Income Statement"):
        income_stmt = extended_data.get("income_stmt")
        if isinstance(income_stmt, pd.DataFrame) and not income_stmt.empty:
            st.dataframe(income_stmt)
        else:
            st.info("No quarterly income statement data available.")

    with st.expander("Recent Trading History (1 month)"):
        history_df = extended_data.get("history")
        if isinstance(history_df, pd.DataFrame) and not history_df.empty:
            st.dataframe(history_df.tail())
        else:
            st.info("No recent history available.")

    with st.expander("Nearest Option Chain (Calls)"):
        option_chain = extended_data.get("option_chain")
        if isinstance(option_chain, pd.DataFrame) and not option_chain.empty:
            st.dataframe(option_chain)
        else:
            st.info("No option chain data available.")


def render_chart(
    primary_ticker: str,
    benchmark_ticker_inputs: list[str],
    start_date: date,
    end_date: date,
) -> None:
    """Render normalized performance chart."""
    stock_data = get_stock_data(primary_ticker, start_date, end_date)

    if stock_data is None or stock_data.empty:
        return

    render_stock_info(primary_ticker)

    extended_data = fetch_extended_ticker_data(primary_ticker, start_date, end_date)
    benchmark_data: dict[str, pd.DataFrame] = {}
    if benchmark_ticker_inputs:
        benchmark_data = get_multiple_stock_data(benchmark_ticker_inputs, start_date, end_date)

    stats = compute_price_statistics(
        _closing_price_series(stock_data),
        extended_data.get("benchmark", pd.Series(dtype=float)),
        extended_data.get("price_targets"),
    )
    market_cap = extended_data.get("info", {}).get("marketCap")
    render_extended_sections(primary_ticker, market_cap, stats, extended_data)

    # Render normalized performance chart
    fig = plot_normalized_data(stock_data, benchmark_data, primary_ticker)
    st.plotly_chart(fig, use_container_width=True)

    # Display raw data snapshot
    st.subheader("Raw Data Snapshot")
    st.dataframe(stock_data.tail())
# ╰─────────────────────────────────────────────────────────────────╯


def _format_currency(value: Optional[float]) -> str:
    """Format numeric value as currency string."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def _format_number(value: Optional[float]) -> str:
    """Format numeric value with reasonable precision."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.4f}"


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()

    # Get search parameters from UI
    primary_ticker, benchmark_ticker_inputs, start_date, end_date = render_search_parameters()

    # Render chart if ticker is provided
    if primary_ticker:
        render_chart(primary_ticker, benchmark_ticker_inputs, start_date, end_date)


if __name__ == "__main__":
    main()
