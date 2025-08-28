import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

def get_stock_data(ticker_symbol, start_date, end_date):
    """
    Fetches historical stock data from Yahoo Finance for a given ticker.
    Includes error handling for invalid tickers or data fetching issues.
    """
    try:
        data = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)
        if data.empty:
            st.error(f"No data found for ticker '{ticker_symbol}'. It might be an invalid ticker or delisted.")
            return None
        return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None

def plot_stock_data(data, benchmark_data, primary_ticker, benchmark_ticker):
    """
    Creates an interactive Plotly chart with the stock's closing price.
    Optionally overlays a benchmark's closing price.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=primary_ticker))

    if benchmark_data is not None and not benchmark_data.empty:
        fig.add_trace(go.Scatter(x=benchmark_data.index, y=benchmark_data['Close'], mode='lines', name=f"{benchmark_ticker} (Benchmark)", line=dict(dash='dot', color='orange')))

    fig.update_layout(
        title=f'{primary_ticker} vs. {benchmark_ticker}' if benchmark_ticker else f'{primary_ticker} Stock Price',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        legend_title='Ticker',
        template='plotly_white'
    )
    return fig


st.set_page_config(layout="wide")
st.title("Financial Asset Search & Analysis")

# --- User Inputs in the Sidebar ---
st.header("Search Parameters")
primary_ticker = st.text_input("Enter a Stock or ETF Ticker", "AAPL").upper()
benchmark_ticker = st.text_input("Enter a Benchmark Ticker (Optional)", "SPY").upper()

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("today"))

# --- Main Page Logic ---
if primary_ticker:
    stock_data = get_stock_data(primary_ticker, start_date, end_date)

    if stock_data is not None:
        ticker_info = yf.Ticker(primary_ticker)
        
        st.header(f"{ticker_info.info.get('longName', primary_ticker)} ({primary_ticker})")
        
        # --- Display Company Info and Price Chart in columns ---
        info_col, chart_col = st.columns([1, 2]) # Give more space to the chart

        with info_col:
            st.subheader("Company Profile")
            st.markdown(f"**Sector:** {ticker_info.info.get('sector', 'N/A')}")
            st.markdown(f"**Industry:** {ticker_info.info.get('industry', 'N/A')}")
            st.markdown(f"**Website:** [{ticker_info.info.get('website', 'N/A')}]({ticker_info.info.get('website', 'N/A')})")
            with st.expander("Business Summary"):
                st.write(ticker_info.info.get('longBusinessSummary', 'No description available.'))

        with chart_col:
            st.subheader("Price Chart")
            benchmark_data = None
            if benchmark_ticker:
                benchmark_data = get_stock_data(benchmark_ticker, start_date, end_date)
            
            fig = plot_stock_data(stock_data, benchmark_data, primary_ticker, benchmark_ticker)
            st.plotly_chart(fig, use_container_width=True)

        # --- Display Raw Data Snapshot ---
        st.subheader("Raw Data Snapshot")
        st.dataframe(stock_data.tail())
