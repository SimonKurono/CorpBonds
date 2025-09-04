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
        
        if pd.api.types.is_datetime64_any_dtype(data.index):
             data.index = data.index.tz_localize(None)

        return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None

def plot_normalized_data(data, benchmark_data, primary_ticker, benchmark_ticker):
    """
    Creates an interactive Plotly chart showing normalized performance.
    This is better for benchmarking as it shows relative performance instead of absolute price.
    """
    fig = go.Figure()
    
    # reset data to fit plotly
    data.columns = ["Close", "High", "Low", "Open", "Volume"]
    benchmark_data.columns = ["Close", "High", "Low", "Open", "Volume"]
    
    
    # --- Normalize the data ---
    # We divide each closing price by the very first closing price and multiply by 100.
    # This makes both series start at 100, allowing for a fair performance comparison.
    primary_normalized = (data['Close'] / data['Close'].iloc[0]) * 100
    
    # Add primary stock trace
    fig.add_trace(go.Scatter(x=primary_normalized.index, y=primary_normalized, mode='lines', name=primary_ticker))

    # Add benchmark trace if data is available
    if benchmark_data is not None and not benchmark_data.empty:
        benchmark_normalized = (benchmark_data['Close'] / benchmark_data['Close'].iloc[0]) * 100
        fig.add_trace(go.Scatter(x=benchmark_normalized.index, y=benchmark_normalized, mode='lines', name=f"{benchmark_ticker} (Benchmark)", line=dict(dash='dot', color='orange')))

    # Customize layout for the normalized chart
    fig.update_layout(
        title=f'Performance: {primary_ticker} vs. {benchmark_ticker}' if benchmark_ticker else f'{primary_ticker} Performance',
        xaxis_title='Date',
        yaxis_title='Normalized Price (Start = 100)',
        legend_title='Ticker',
        template='plotly_white'
    )
    return fig

#--------- PAGE DISPLAY ------------------------------
st.set_page_config(layout="wide")
st.title("Financial Asset Search & Analysis")

# --- User Inputs in the Sidebar ---
st.header("Search Parameters")
ticker_col1, ticker_col2, col1, col2 = st.columns(4)

with ticker_col1:
    primary_ticker = st.text_input("Enter a Stock or ETF Ticker", "AAPL").upper()
with ticker_col2:
    benchmark_ticker = st.text_input("Enter a Benchmark Ticker (Optional)", "SPY").upper()
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("today"))
    
st.write("---")

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
            #st.markdown(f"**Website:** [{ticker_info.info.get('website', 'N/A')}]({ticker_info.info.get('website', 'N/A')})")
            with st.expander("Business Summary"):
                st.write(ticker_info.info.get('longBusinessSummary', 'No description available.'))
            
            st.markdown("**Run Analysis**")
            monte_carlo, moving_average, relative_value = st.columns(3)
            with monte_carlo:
                st.button(label="Monte Carlo", type="primary", use_container_width=True)
            with moving_average:
                st.button(label="Moving Average",use_container_width=True)
            with relative_value:
                st.button(label="Relative Value", use_container_width=True)

        with chart_col:
            st.subheader("Performance Chart")
            benchmark_data = None
            if benchmark_ticker:
                benchmark_data = get_stock_data(benchmark_ticker, start_date, end_date)
            
            # Use the new normalized plotting function
            if stock_data is not None and not stock_data.empty:
                fig = plot_normalized_data(stock_data, benchmark_data, primary_ticker, benchmark_ticker)
                st.plotly_chart(fig, use_container_width=True)

        # --- Display Raw Data Snapshot ---
        st.subheader("Raw Data Snapshot")
        st.dataframe(stock_data.tail())
        
            

