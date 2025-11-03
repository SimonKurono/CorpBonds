# pages/Portfolio.py
"""
Portfolio Management & Analysis Page

Features:
- View current portfolio holdings
- Buy and sell stocks
- Display returns, Sharpe ratios, and return attribution analysis
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import utils.ui as ui


# ╭─────────────────────────── Constants & Configuration ───────────────────────────╮
FIG_TEMPLATE = "plotly_white"
FIG_MARGIN = dict(t=50, b=40, l=40, r=40)
RISK_FREE_RATE = 0.02  # Placeholder: 2% annual risk-free rate


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


def get_current_holdings() -> pd.DataFrame:
    """Get current portfolio holdings from transaction history."""
    init_session_state()
    
    holdings = {}
    for txn in st.session_state.transactions:
        ticker = txn["ticker"]
        if ticker not in holdings:
            holdings[ticker] = 0
        
        if txn["action"] == "Buy":
            holdings[ticker] += txn["quantity"]
        elif txn["action"] == "Sell":
            holdings[ticker] -= txn["quantity"]
    
    # Remove zero holdings
    holdings = {k: v for k, v in holdings.items() if v > 0}
    
    if not holdings:
        return pd.DataFrame()
    
    # Create DataFrame with current market prices
    data = []
    for ticker, quantity in holdings.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_price = info.get('currentPrice', 0)
            market_value = quantity * current_price
            data.append({
                "Ticker": ticker,
                "Quantity": quantity,
                "Current Price": current_price,
                "Market Value": market_value
            })
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {e}")
            continue
    
    return pd.DataFrame(data)


def calculate_returns() -> dict:
    """
    Calculate portfolio returns and metrics.
    Returns portfolio statistics including CAGR, Vol, Sharpe ratio.
    """
    holdings_df = get_current_holdings()
    
    if holdings_df.empty or len(holdings_df) == 0:
        return {
            "total_value": 0,
            "returns_series": pd.Series(),
            "metrics": {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}
        }
    
    # Get historical prices for all holdings
    tickers = holdings_df["Ticker"].tolist()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of history
    
    try:
        prices_df = yf.download(tickers, start=start_date, end=end_date, progress=False)
        if prices_df.empty:
            return {
                "total_value": holdings_df["Market Value"].sum(),
                "returns_series": pd.Series(),
                "metrics": {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}
            }
    except Exception:
        return {
            "total_value": holdings_df["Market Value"].sum(),
            "returns_series": pd.Series(),
            "metrics": {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}
        }
    
    # Handle MultiIndex columns (yfinance returns MultiIndex)
    if isinstance(prices_df.columns, pd.MultiIndex):
        prices_df.columns = prices_df.columns.droplevel(1)
    
    # Calculate portfolio returns
    portfolio_returns = pd.Series(dtype=float)
    portfolio_values = pd.Series(dtype=float)
    
    for _, holding in holdings_df.iterrows():
        ticker = holding["Ticker"]
        quantity = holding["Quantity"]
        
        if ticker in prices_df.columns:
            ticker_prices = prices_df[ticker]["Close"] if "Close" in prices_df.columns else prices_df[ticker]
            ticker_values = ticker_prices * quantity
            
            if portfolio_values.empty:
                portfolio_values = ticker_values
            else:
                portfolio_values = portfolio_values.add(ticker_values, fill_value=0)
    
    if not portfolio_values.empty:
        portfolio_returns = portfolio_values.pct_change().fillna(0)
    
    # Calculate metrics
    metrics = calculate_portfolio_metrics(portfolio_returns)
    
    return {
        "total_value": holdings_df["Market Value"].sum(),
        "returns_series": portfolio_returns,
        "portfolio_values": portfolio_values,
        "metrics": metrics
    }


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
def render_header():
    """Configure page header."""
    ui.configure_page(page_title="Portfolio Management", page_icon="💼", layout="wide")
    ui.render_sidebar()


def render_stock_chart(ticker: str):
    """Render a stock price chart for the given ticker."""
    if not ticker:
        st.info("Enter or select a ticker to view chart")
        return
    
    try:
        # Get historical data (last 6 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if stock_data.empty:
            st.warning(f"No data available for {ticker}")
            return
        
        # Handle MultiIndex columns from yfinance
        # yfinance returns DataFrame with MultiIndex columns like ('Close', 'TICKER')
        if isinstance(stock_data.columns, pd.MultiIndex):
            # Flatten MultiIndex by selecting 'Close' level
            try:
                # Method 1: Use xs to cross-section
                close_prices = stock_data.xs('Close', axis=1, level=0)
                # If multiple columns, take first
                if isinstance(close_prices, pd.DataFrame):
                    close_prices = close_prices.iloc[:, 0]
            except:
                # Method 2: Direct column access
                try:
                    close_prices = stock_data[('Close', ticker)]
                except:
                    # Method 3: Get first Close column
                    close_cols = [col for col in stock_data.columns if col[0] == 'Close']
                    if close_cols:
                        close_prices = stock_data[close_cols[0]]
                    else:
                        close_prices = stock_data.iloc[:, 0]
        else:
            # Single ticker case - just get Close column
            if 'Close' in stock_data.columns:
                close_prices = stock_data['Close']
            else:
                close_prices = stock_data.iloc[:, 0]
        
        # Ensure we have a Series (not DataFrame)
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]
        
        # Convert to Series if needed
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices.values, index=close_prices.index)
        
        # Remove timezone info if present
        if hasattr(close_prices.index, 'tz') and close_prices.index.tz is not None:
            close_prices.index = close_prices.index.tz_localize(None)
        
        # Ensure data is sorted by date and remove any NaN values
        close_prices = close_prices.sort_index().dropna()
        
        # Debug: Check if we have data
        if len(close_prices) == 0:
            st.warning(f"No price data available for {ticker}")
            return
        
        # Get current price info
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice', close_prices.iloc[-1] if not close_prices.empty else 0)
        company_name = info.get('longName', ticker)
        
        # Create chart
        fig = go.Figure()
        
        # Ensure we have valid numeric data
        close_prices = close_prices.astype(float)
        
        # Add price line
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(close_prices.index),
            y=close_prices.values,
            mode='lines',
            name=ticker,
            line=dict(width=2, color='#1f77b4'),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
        ))
        
        # Add current price marker
        if current_price > 0 and not close_prices.empty:
            last_date = pd.to_datetime(close_prices.index[-1])
            fig.add_trace(go.Scatter(
                x=[last_date],
                y=[float(current_price)],
                mode='markers',
                name='Current Price',
                marker=dict(size=12, color='red', symbol='circle', line=dict(width=2, color='white')),
                hovertemplate='<b>Current Price</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title=f"{company_name} ({ticker})",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template=FIG_TEMPLATE,
            margin=FIG_MARGIN,
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display current price info
        if current_price > 0:
            st.metric("Current Price", f"${current_price:.2f}")
        
    except Exception as e:
        st.error(f"Error loading chart for {ticker}: {e}")
        st.exception(e)


def render_trade_panel():
    """Render buy/sell trading panel."""
    st.header("💰 Trade")
    st.caption("Buy or sell stocks to manage your portfolio")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.subheader("Buy Stock")
        buy_ticker = st.text_input("Ticker Symbol", "", key="buy_ticker").upper()
        buy_quantity = st.number_input("Quantity", min_value=1, value=1, key="buy_quantity")
        
        if st.button("Buy", type="secondary", use_container_width=True):
            if buy_ticker:
                try:
                    stock = yf.Ticker(buy_ticker)
                    info = stock.info
                    current_price = info.get('currentPrice', 0)
                    
                    if current_price > 0:
                        add_transaction(buy_ticker, "Buy", buy_quantity, current_price)
                        st.success(f"✅ Bought {buy_quantity} shares of {buy_ticker} at ${current_price:.2f}")
                    else:
                        st.error("Could not fetch current price for this ticker.")
                except Exception as e:
                    st.error(f"Error fetching data for {buy_ticker}: {e}")
            else:
                st.warning("Please enter a ticker symbol.")
        
        st.subheader("Sell Stock")
        holdings_df = get_current_holdings()
        
        if holdings_df.empty:
            st.info("No holdings to sell.")
        else:
            sell_tickers = holdings_df["Ticker"].tolist()
            sell_ticker = st.selectbox("Select Ticker", sell_tickers, key="sell_ticker")
            
            if sell_ticker:
                max_quantity = int(holdings_df[holdings_df["Ticker"] == sell_ticker]["Quantity"].iloc[0])
                sell_quantity = st.number_input("Quantity", min_value=1, max_value=max_quantity, value=1, key="sell_quantity")
                
                if st.button("Sell", type="primary", use_container_width=True):
                    try:
                        stock = yf.Ticker(sell_ticker)
                        info = stock.info
                        current_price = info.get('currentPrice', 0)
                        
                        if current_price > 0:
                            if sell_quantity <= max_quantity:
                                add_transaction(sell_ticker, "Sell", sell_quantity, current_price)
                                st.success(f"✅ Sold {sell_quantity} shares of {sell_ticker} at ${current_price:.2f}")
                            else:
                                st.error(f"You only own {max_quantity} shares of {sell_ticker}.")
                        else:
                            st.error("Could not fetch current price for this ticker.")
                    except Exception as e:
                        st.error(f"Error fetching data for {sell_ticker}: {e}")
    
    with col2:
        st.subheader("📈 Stock Chart")
        
        # Determine which ticker to display (prioritize buy ticker if entered)
        display_ticker = None
        
        # Check if user is entering a buy ticker (access from session state)
        if 'buy_ticker' in st.session_state and st.session_state.get('buy_ticker'):
            display_ticker = st.session_state.get('buy_ticker').upper()
        # Otherwise check if user selected a sell ticker
        elif 'sell_ticker' in st.session_state and st.session_state.get('sell_ticker'):
            display_ticker = st.session_state.get('sell_ticker')
        
        # Render chart for the active ticker
        render_stock_chart(display_ticker)    


def render_holdings_panel():
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


def render_performance_panel():
    """Display portfolio performance metrics and charts."""
    st.header("📈 Performance Analysis")
    
    portfolio_data = calculate_returns()
    
    if portfolio_data["total_value"] == 0:
        st.info("Add holdings to see performance metrics.")
        return
    
    # Display metrics
    metrics = portfolio_data["metrics"]
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CAGR", f"{metrics['CAGR']*100:.2f}%")
    with col2:
        st.metric("Volatility", f"{metrics['Vol']*100:.2f}%")
    with col3:
        st.metric("Sharpe Ratio", f"{metrics['Sharpe']:.2f}")
    with col4:
        st.metric("Max Drawdown", f"{metrics['MaxDD']*100:.2f}%")
    
    # Portfolio value chart
    portfolio_values = portfolio_data.get("portfolio_values", pd.Series())
    returns_series = portfolio_data["returns_series"]
    
    if not portfolio_values.empty:
        st.subheader("Portfolio Value Over Time")
        fig_value = px.line(
            x=portfolio_values.index,
            y=portfolio_values.values,
            title="Portfolio Value",
            labels={"x": "Date", "y": "Value ($)"}
        )
        fig_value.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
        st.plotly_chart(fig_value, use_container_width=True)
    
    if not returns_series.empty:
        st.subheader("Cumulative Returns")
        cum_returns = (1 + returns_series).cumprod() - 1
        fig_cum = px.line(
            x=cum_returns.index,
            y=cum_returns.values,
            title="Cumulative Returns",
            labels={"x": "Date", "y": "Cumulative Return"}
        )
        fig_cum.update_layout(template=FIG_TEMPLATE, margin=FIG_MARGIN)
        fig_cum.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_cum, use_container_width=True)
    
    # TODO: Placeholder for return attribution analysis
    st.caption("📝 TODO: Return attribution analysis by sector/asset class will be added here")


def render_transaction_history():
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


# ╭─────────────────────────── Main Page Logic ───────────────────────────╮
def main():
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

