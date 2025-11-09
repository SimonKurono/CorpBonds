# pages/Portfolio.py ─────────────────────────────────────────────────────────
"""
Portfolio Management & Analysis Page.

Features:
- View current portfolio holdings
- Buy and sell stocks
- Display returns, Sharpe ratios, and return attribution analysis
"""

from __future__ import annotations

# ── Stdlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping

# ── Third-party
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ── Local
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
FIG_TEMPLATE = "plotly_white"
FIG_MARGIN = dict(t=50, b=40, l=40, r=40)
RISK_FREE_RATE = 0.02  # Placeholder: 2% annual risk-free rate
HISTORY_DAYS = 365  # Days of historical data for returns calculation
CHART_HISTORY_DAYS = 180  # Days of historical data for stock charts
ANALYST_BUY_THRESHOLD = 0.10
ANALYST_SELL_THRESHOLD = -0.05
PORTFOLIO_VALUE_CAP = 100_000
BENCHMARK_TICKER = "SPY"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Session State Management ───────────────────────────╮
def init_session_state():
    """Initialize session state for portfolio if not exists."""
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    if "portfolio_value_history" not in st.session_state:
        st.session_state.portfolio_value_history = []


def add_transaction(ticker: str, action: str, quantity: int, price: float):
    """Add a transaction to the history."""
    transaction = {
        "timestamp": datetime.now(),
        "ticker": ticker,
        "action": action,
        "quantity": quantity,
        "price": price,
        "value": quantity * price
    }
    st.session_state.transactions.append(transaction)
    return transaction


def _current_portfolio_value() -> float:
    """Return current portfolio market value."""
    holdings_df = get_current_holdings()
    if holdings_df.empty:
        return 0.0
    return float(holdings_df["Market Value"].sum())


def _aggregate_share_counts(transactions: List[Mapping[str, Any]]) -> dict[str, int]:
    """Return net share counts per ticker from transaction history."""
    holdings: dict[str, int] = {}
    for txn in transactions:
        ticker = txn["ticker"]
        shares = holdings.setdefault(ticker, 0)
        if txn["action"] == "Buy":
            holdings[ticker] = shares + txn["quantity"]
        elif txn["action"] == "Sell":
            holdings[ticker] = shares - txn["quantity"]
    return {ticker: qty for ticker, qty in holdings.items() if qty > 0}


def _fetch_market_snapshot(ticker: str, quantity: int) -> dict[str, Any] | None:
    """Fetch current price data for a ticker and compute market value."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("currentPrice", 0.0)
        market_value = quantity * current_price
        return {
            "Ticker": ticker,
            "Quantity": quantity,
            "Current Price": current_price,
            "Market Value": market_value,
        }
    except Exception as exc:  # pragma: no cover - UI feedback only
        st.warning(f"Could not fetch data for {ticker}: {exc}")
        return None


def get_current_holdings() -> pd.DataFrame:
    """Return current holdings with latest market values."""
    init_session_state()
    holdings_map = _aggregate_share_counts(st.session_state.transactions)
    if not holdings_map:
        return pd.DataFrame()

    snapshots = [_fetch_market_snapshot(ticker, qty) for ticker, qty in holdings_map.items()]
    rows = [snap for snap in snapshots if snap]
    return pd.DataFrame(rows)


def calculate_returns() -> dict:
    """Return portfolio value series, returns, and summary metrics."""
    holdings_df = get_current_holdings()
    if holdings_df.empty:
        return _empty_returns_payload()

    price_history = _download_price_history(holdings_df["Ticker"].tolist())
    if price_history.empty:
        total_value = holdings_df["Market Value"].sum()
        payload = _empty_returns_payload(total_value)
        payload["holdings"] = holdings_df
        payload["price_history"] = price_history
        return payload

    portfolio_values = _build_portfolio_values(holdings_df, price_history)
    if portfolio_values.empty:
        total_value = holdings_df["Market Value"].sum()
        payload = _empty_returns_payload(total_value)
        payload["holdings"] = holdings_df
        payload["price_history"] = price_history
        return payload

    returns_series = portfolio_values.pct_change().fillna(0)
    metrics = calculate_portfolio_metrics(returns_series)

    return {
        "total_value": holdings_df["Market Value"].sum(),
        "returns_series": returns_series,
        "portfolio_values": portfolio_values,
        "metrics": metrics,
        "holdings": holdings_df,
        "price_history": price_history,
    }


def _empty_returns_payload(total_value: float = 0.0) -> dict:
    """Return a standard payload for missing return data."""
    return {
        "total_value": total_value,
        "returns_series": pd.Series(dtype=float),
        "portfolio_values": pd.Series(dtype=float),
        "metrics": {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0},
        "holdings": pd.DataFrame(),
        "price_history": pd.DataFrame(),
    }


def _download_price_history(tickers: List[str]) -> pd.DataFrame:
    """Download and normalise historical close prices for a list of tickers."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=HISTORY_DAYS)
    try:
        raw_prices = yf.download(tickers, start=start_date, end=end_date, progress=False)
    except Exception:  # pragma: no cover - yfinance network issues
        return pd.DataFrame()
    if raw_prices.empty:
        return raw_prices
    return _normalize_price_history(raw_prices, tickers)


def _normalize_price_history(prices: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    """Return a DataFrame of close prices indexed by date."""
    if isinstance(prices.columns, pd.MultiIndex):
        if "Close" in prices.columns.get_level_values(0):
            close_prices = prices["Close"]
        else:
            close_prices = prices.droplevel(0, axis=1)
    else:
        close_prices = prices["Close"] if "Close" in prices.columns else prices
    if isinstance(close_prices, pd.Series):
        close_prices = close_prices.to_frame(name=tickers[0])
    elif len(close_prices.columns) == 1 and tickers:
        close_prices.columns = [tickers[0]]
    return close_prices.sort_index().dropna(how="all")


def _build_portfolio_values(holdings_df: pd.DataFrame, price_history: pd.DataFrame) -> pd.Series:
    """Aggregate position values across holdings to produce a portfolio series."""
    portfolio_series = pd.Series(dtype=float)
    for _, holding in holdings_df.iterrows():
        ticker = holding["Ticker"]
        quantity = holding["Quantity"]
        if ticker not in price_history.columns:
            continue
        ticker_values = price_history[ticker] * quantity
        portfolio_series = ticker_values if portfolio_series.empty else portfolio_series.add(ticker_values, fill_value=0)
    return portfolio_series.sort_index()


def calculate_portfolio_metrics(returns: pd.Series) -> dict:
    """Calculate portfolio performance metrics."""
    if returns.empty or len(returns) < 2:
        return {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}
    
    ret = returns.dropna()
    
    if ret.empty:
        return {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}
    
    # Annualized metrics
    days = len(ret)
    cagr = (1 + ret).prod() ** (252 / days) - 1 if days > 0 else 0
    vol = ret.std() * np.sqrt(252) if len(ret) > 1 else 0
    sharpe = (cagr - RISK_FREE_RATE) / vol if vol != 0 else 0
    
    # Max drawdown
    curve = (1 + ret).cumprod()
    peak = curve.cummax()
    dd = (curve / peak - 1).min()
    
    return {
        "CAGR": cagr,
        "Vol": vol,
        "Sharpe": sharpe,
        "MaxDD": dd
    }


# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Render Functions ───────────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Portfolio Management", page_icon="💼", layout="wide")
    ui.render_sidebar()


def render_stock_chart(ticker: str) -> None:
    """Render a stock price chart for the given ticker."""
    if not ticker:
        st.info("Enter or select a ticker to view chart")
        return
    close_prices = _load_stock_close_series(ticker)
    if close_prices is None or close_prices.empty:
        st.warning(f"No data available for {ticker}")
        return

    company_name, current_price, analyst_signal, signal_delta = _fetch_stock_metadata(ticker, close_prices)
    figure = _create_stock_chart_figure(ticker, company_name, close_prices, current_price)
    st.plotly_chart(figure, use_container_width=True)

    if current_price > 0:
        st.metric("Current Price", f"${current_price:.2f}")
    st.metric("Analyst Signal", analyst_signal, signal_delta or None)


def _load_stock_close_series(ticker: str) -> pd.Series | None:
    """Download and prepare close price series for a ticker."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=CHART_HISTORY_DAYS)
        raw_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    except Exception as exc:  # pragma: no cover - yfinance network issues
        st.error(f"Error loading chart for {ticker}: {exc}")
        return None

    if raw_data.empty:
        return None

    if isinstance(raw_data.columns, pd.MultiIndex):
        close_prices = raw_data["Close"]
        close_series = close_prices.iloc[:, 0]
    elif "Close" in raw_data.columns:
        close_series = raw_data["Close"]
    else:
        close_series = raw_data.iloc[:, 0]

    close_series = close_series.sort_index().dropna()
    if hasattr(close_series.index, "tz") and close_series.index.tz is not None:
        close_series.index = close_series.index.tz_localize(None)
    return close_series.astype(float)


def _fetch_stock_metadata(ticker: str, close_prices: pd.Series) -> tuple[str, float, str, str]:
    """Return company name, current price, and analyst signal for ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    fallback_price = close_prices.iloc[-1] if not close_prices.empty else 0.0
    current_price = info.get("currentPrice", fallback_price)
    company_name = info.get("longName", ticker)
    try:
        price_targets = stock.analyst_price_targets
    except Exception:  # pragma: no cover - optional data
        price_targets = None
    analyst_signal, signal_delta = _derive_analyst_signal(current_price, price_targets)
    return company_name, current_price, analyst_signal, signal_delta


def _derive_analyst_signal(current_price: float, price_targets: Any) -> tuple[str, str]:
    """Compute Buy/Hold/Sell recommendation based on analyst target mean."""
    if current_price <= 0 or not price_targets:
        return "N/A", ""

    target_mean = None
    if isinstance(price_targets, dict):
        target_mean = price_targets.get("mean") or price_targets.get("targetMean")
    elif hasattr(price_targets, "get"):
        target_mean = price_targets.get("mean") or price_targets.get("targetMean")

    if not target_mean:
        return "N/A", ""

    diff_pct = (target_mean - current_price) / current_price
    if diff_pct >= ANALYST_BUY_THRESHOLD:
        rating = "Buy"
    elif diff_pct <= ANALYST_SELL_THRESHOLD:
        rating = "Sell"
    else:
        rating = "Hold"
    return rating, f"{diff_pct:+.1%}"


def _create_stock_chart_figure(
    ticker: str,
    company_name: str,
    close_prices: pd.Series,
    current_price: float,
) -> go.Figure:
    """Create a Plotly figure for stock price history."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(close_prices.index),
            y=close_prices.values,
            mode="lines",
            name=ticker,
            line=dict(width=2, color="#1f77b4"),
            hovertemplate="<b>%{fullData.name}</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>",
        )
    )

    if current_price > 0 and not close_prices.empty:
        last_date = pd.to_datetime(close_prices.index[-1])
        fig.add_trace(
            go.Scatter(
                x=[last_date],
                y=[float(current_price)],
                mode="markers",
                name="Current Price",
                marker=dict(size=12, color="red", symbol="circle", line=dict(width=2, color="white")),
                hovertemplate="<b>Current Price</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=f"{company_name} ({ticker})",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template=FIG_TEMPLATE,
        margin=FIG_MARGIN,
        height=400,
        showlegend=True,
        hovermode="x unified",
    )
    return fig


def render_trade_panel() -> None:
    """Render buy/sell trading panel."""
    st.header("💰 Trade")
    st.caption("Buy or sell stocks to manage your portfolio")
    
    col_actions, col_chart = st.columns(2, gap="large")

    with col_actions:
        _render_buy_form()
        holdings_df = get_current_holdings()
        _render_sell_form(holdings_df)

    with col_chart:
        st.subheader("📈 Stock Chart")
        display_ticker = _determine_display_ticker()
        render_stock_chart(display_ticker)


def _render_buy_form() -> None:
    """Render form to submit buy orders."""
    st.subheader("Buy Stock")
    buy_ticker = st.text_input("Ticker Symbol", "", key="buy_ticker").upper()
    buy_quantity = st.number_input("Quantity", min_value=1, value=1, key="buy_quantity")

    if st.button("Buy", type="secondary", use_container_width=True):
        if not buy_ticker:
            st.warning("Please enter a ticker symbol.")
            return
        _handle_buy_order(buy_ticker, buy_quantity)


def _handle_buy_order(ticker: str, quantity: int) -> None:
    """Execute a buy order and provide user feedback."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("currentPrice", 0.0)
        if current_price <= 0:
            st.error("Could not fetch current price for this ticker.")
            return
        projected_value = _current_portfolio_value() + current_price * quantity
        if projected_value > PORTFOLIO_VALUE_CAP:
            st.error(f"Trade exceeds portfolio cap of ${PORTFOLIO_VALUE_CAP:,.0f}.")
            return
        add_transaction(ticker, "Buy", quantity, current_price)
        st.success(f"✅ Bought {quantity} shares of {ticker} at ${current_price:.2f}")
    except Exception as exc:  # pragma: no cover - network dependent
        st.error(f"Error fetching data for {ticker}: {exc}")


def _render_sell_form(holdings_df: pd.DataFrame) -> None:
    """Render form to submit sell orders."""
    st.subheader("Sell Stock")
    if holdings_df.empty:
        st.info("No holdings to sell.")
        return

    sell_tickers = holdings_df["Ticker"].tolist()
    sell_ticker = st.selectbox("Select Ticker", sell_tickers, key="sell_ticker")
    if not sell_ticker:
        return

    max_quantity = int(holdings_df.loc[holdings_df["Ticker"] == sell_ticker, "Quantity"].iloc[0])
    sell_quantity = st.number_input(
        "Quantity",
        min_value=1,
        max_value=max_quantity,
        value=1,
        key="sell_quantity",
    )

    if st.button("Sell", type="primary", use_container_width=True):
        _handle_sell_order(sell_ticker, sell_quantity, max_quantity)


def _handle_sell_order(ticker: str, quantity: int, max_quantity: int) -> None:
    """Execute a sell order and provide user feedback."""
    if quantity > max_quantity:
        st.error(f"You only own {max_quantity} shares of {ticker}.")
        return

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("currentPrice", 0.0)
        if current_price <= 0:
            st.error("Could not fetch current price for this ticker.")
            return
        add_transaction(ticker, "Sell", quantity, current_price)
        st.success(f"✅ Sold {quantity} shares of {ticker} at ${current_price:.2f}")
    except Exception as exc:  # pragma: no cover - network dependent
        st.error(f"Error fetching data for {ticker}: {exc}")


def _determine_display_ticker() -> str | None:
    """Return ticker to display in the chart based on recent user actions."""
    buy_ticker = st.session_state.get("buy_ticker")
    if buy_ticker:
        return buy_ticker.upper()
    sell_ticker = st.session_state.get("sell_ticker")
    return sell_ticker


def render_holdings_panel() -> None:
    """Display current portfolio holdings."""
    st.header("📊 Current Holdings")
    
    holdings_df = get_current_holdings()
    
    if holdings_df.empty:
        st.info("📭 Your portfolio is empty. Start by buying some stocks!")
        return
    
    # Display summary metrics
    total_value = holdings_df["Market Value"].sum()
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
    
    # Display holdings table
    st.dataframe(
        holdings_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Pie chart of holdings
    if len(holdings_df) > 0:
        fig_pie = px.pie(
            holdings_df,
            values="Market Value",
            names="Ticker",
            title="Portfolio Allocation by Value"
        )
        fig_pie.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
        st.plotly_chart(fig_pie, use_container_width=True)


def render_performance_panel() -> None:
    """Display portfolio performance metrics and charts."""
    st.header("📈 Performance Analysis")
    
    portfolio_data = calculate_returns()
    
    if portfolio_data["total_value"] == 0:
        st.info("Add holdings to see performance metrics.")
        return
    
    _render_performance_metrics(portfolio_data["metrics"])
    portfolio_values = portfolio_data.get("portfolio_values", pd.Series(dtype=float))
    returns_series = portfolio_data["returns_series"]
    holdings_df = portfolio_data.get("holdings", pd.DataFrame())
    price_history = portfolio_data.get("price_history", pd.DataFrame())

    if not holdings_df.empty:
        _render_share_allocation_chart(holdings_df)

    if not portfolio_values.empty:
        _render_portfolio_value_chart(portfolio_values)

    if not returns_series.empty:
        _render_cumulative_returns_chart(returns_series)

    if not price_history.empty:
        _render_risk_return_chart(price_history)

    if not portfolio_values.empty:
        _render_portfolio_vs_benchmark_chart(portfolio_values)

    st.caption("📝 TODO: Return attribution analysis by sector/asset class will be added here")


def _render_performance_metrics(metrics: Mapping[str, float]) -> None:
    """Render key performance indicators."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CAGR", f"{metrics['CAGR'] * 100:.2f}%")
    with col2:
        st.metric("Volatility", f"{metrics['Vol'] * 100:.2f}%")
    with col3:
        st.metric("Sharpe Ratio", f"{metrics['Sharpe']:.2f}")
    with col4:
        st.metric("Max Drawdown", f"{metrics['MaxDD'] * 100:.2f}%")


def _render_portfolio_value_chart(portfolio_values: pd.Series) -> None:
    """Render time series chart for portfolio value."""
    st.subheader("Portfolio Value Over Time")
    fig_value = px.line(
        x=portfolio_values.index,
        y=portfolio_values.values,
        title="Portfolio Value",
        labels={"x": "Date", "y": "Value ($)"},
    )
    fig_value.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
    st.plotly_chart(fig_value, use_container_width=True)


def _render_cumulative_returns_chart(returns_series: pd.Series) -> None:
    """Render cumulative returns chart."""
    st.subheader("Cumulative Returns")
    cum_returns = (1 + returns_series).cumprod() - 1
    fig_cum = px.line(
        x=cum_returns.index,
        y=cum_returns.values,
        title="Cumulative Returns",
        labels={"x": "Date", "y": "Cumulative Return"},
    )
    fig_cum.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
    fig_cum.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_cum, use_container_width=True)


def _render_share_allocation_chart(holdings_df: pd.DataFrame) -> None:
    """Render holdings allocation by share count."""
    if "Quantity" not in holdings_df.columns or holdings_df.empty:
        return
    st.subheader("Holdings by Shares")
    fig = px.pie(
        holdings_df,
        values="Quantity",
        names="Ticker",
        title="Share Allocation",
    )
    fig.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def _render_risk_return_chart(price_history: pd.DataFrame) -> None:
    """Render risk/return scatter chart for portfolio constituents."""
    returns = price_history.pct_change().dropna(how="all")
    if returns.empty:
        return
    mean_daily = returns.mean()
    annual_return = (1 + mean_daily).pow(252) - 1
    annual_vol = returns.std() * np.sqrt(252)
    scatter_df = pd.DataFrame(
        {
            "Ticker": annual_return.index,
            "Return": annual_return.values,
            "Volatility": annual_vol.reindex_like(annual_return).values,
        }
    ).dropna()
    if scatter_df.empty:
        return
    st.subheader("Risk vs Return")
    fig = px.scatter(
        scatter_df,
        x="Volatility",
        y="Return",
        text="Ticker",
        labels={"Volatility": "Annual Volatility", "Return": "Annual Return"},
        title="Asset Risk/Return Profile",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def _render_portfolio_vs_benchmark_chart(
    portfolio_values: pd.Series,
    benchmark_ticker: str = BENCHMARK_TICKER,
) -> None:
    """Render normalized performance of portfolio versus benchmark."""
    if portfolio_values.empty:
        return
    benchmark_series = _fetch_benchmark_series(benchmark_ticker, portfolio_values.index)
    if benchmark_series.empty or benchmark_series.iloc[0] == 0:
        return
    portfolio_norm = portfolio_values / portfolio_values.iloc[0] * 100
    benchmark_norm = benchmark_series / benchmark_series.iloc[0] * 100
    comparison = pd.DataFrame(
        {
            "Portfolio": portfolio_norm,
            benchmark_ticker: benchmark_norm.reindex(portfolio_norm.index, method="ffill"),
        }
    ).dropna()
    if comparison.empty:
        return
    st.subheader(f"Portfolio vs {benchmark_ticker}")
    fig = px.line(
        comparison,
        x=comparison.index,
        y=comparison.columns,
        labels={"value": "Indexed Performance (100 = start)", "variable": "Series", "x": "Date"},
        title="Portfolio vs Benchmark",
    )
    fig.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def _fetch_benchmark_series(benchmark_ticker: str, index: pd.Index) -> pd.Series:
    """Fetch benchmark close prices aligned with portfolio date range."""
    if index.empty:
        return pd.Series(dtype=float)
    start_date = index.min()
    end_date = index.max() + timedelta(days=1)
    try:
        data = yf.download(benchmark_ticker, start=start_date, end=end_date, progress=False)
    except Exception:  # pragma: no cover - yfinance network issues
        return pd.Series(dtype=float)
    if data.empty:
        return pd.Series(dtype=float)
    if isinstance(data.columns, pd.MultiIndex):
        benchmark = data["Close"].iloc[:, 0]
    elif "Close" in data.columns:
        benchmark = data["Close"]
    else:
        benchmark = data.iloc[:, 0]
    return benchmark.sort_index().dropna()


def render_transaction_history() -> None:
    """Display transaction history."""
    st.header("📜 Transaction History")
    
    if not st.session_state.transactions:
        st.info("No transactions yet.")
        return
    
    transactions_df = pd.DataFrame(st.session_state.transactions)
    transactions_df = transactions_df.sort_values("timestamp", ascending=False)
    
    st.dataframe(
        transactions_df,
        use_container_width=True,
        hide_index=True
    )


# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    init_session_state()
    render_header()

    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Trade", "📊 Holdings", "📈 Performance", "📜 History"])

    with tab1:
        render_trade_panel()

    with tab2:
        render_holdings_panel()

    with tab3:
        render_performance_panel()

    with tab4:
        render_transaction_history()

    # Footer notes
    st.divider()
    st.caption("💡 Note: This is a demo portfolio. All data is stored in session state and will be lost when you refresh the page.")
    st.caption("📝 TODO: Add database persistence, advanced attribution analysis, and integration with Stock Search page")


if __name__ == "__main__":
    main()

