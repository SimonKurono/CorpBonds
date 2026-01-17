# Raffles Advisors Financial Analytics Platform

## Overview
The Raffles Advisors platform is a centralized financial analytics dashboard designed for buy-side investment professionals. It integrates cross-asset market data—spanning US corporate bonds, equities, and derivatives—into a unified interface to streamline decision-making and portfolio management.

The application leverages a modern technology stack to deliver real-time intelligence, ensuring data consistency across various analytical modules, from high-level market dashboards to granular security analysis.

## Key Features

### Market Dashboard
A comprehensive view of market health, featuring:
- **Core Rates**: Real-time Treasury yields and Fed rates.
- **Credit Spreads**: IG (Investment Grade) vs. HY (High Yield) Option-Adjusted Spreads (OAS).
- **Yield Curves**: Interactive visualization of yield curves broken down by credit rating (AAA through CCC).
- **Volatility Monitoring**: Real-time tracking of the MOVE Index and VIX.
- **Liquidity Proxies**: Monitoring of CDX IG levels via LQD proxy data.

### AI Credit Memo Generator
A generative AI module that automates the creation of buy-side credit memos.
- **Engine**: Powered by Google Gemini (Gemini-3-flash-preview).
- **Structure**: Generates strictly formatted JSON outputs compliant with internal schemas.
- **Analysis**: Provides qualitative assessments of issuer solvency, sector risks, and macro-sensitivity.

### Equity & ETF Search
A fundamental analysis tool for global equities and ETFs.
- **Performance**: Normalized return comparisons against major benchmarks (SPY, QQQ, IWM).
- **Fundamentals**: Access to business summaries, sector classifications, and market cap data.
- **Technical**: Historical price data and simple moving average visualization.

### Portfolio Management
An integrated position tracking system.
- **Holdings**: Real-time valuation of tracked assets.
- **Allocations**: Dynamic pie charts and exposure analysis.
- **Performance**: Time-weighted return calculations and drawdown analysis.

## Technical Architecture

The platform follows a modular "fetcher-based" architecture designed for scalability and maintainability.

- **Frontend**: Built with Streamlit, enabling rapid iteration and a responsive web interface.
- **Data Layer**: Centralized `fetcher` modules in the `utils/` directory handle all external API interactions. This ensures that data ingestion logic is decoupled from UI presentation.
- **Caching**: Aggressive server-side caching strategies (using `st.cache_data`) optimize performance and minimize API rate usage.
- **Safety**: Robust error handling ensures stability even during partial upstream API outages.

## Installation

### Prerequisites
- Python 3.11 or higher
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SimonKurono/corpbonds-dashboard.git
   cd corpbonds-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file in the root directory (or configure Streamlit Secrets for cloud deployment) with the following keys:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key
   FRED_API_KEY=your_fred_api_key
   NEWS_API_KEY=your_newsapi_key
   ```

4. **Run the Application**
   ```bash
   streamlit run Home.py
   ```

## Configuration

This application is designed to be cloud-native compatible.
- **Local Development**: Uses `python-dotenv` to read from local `.env` files.
- **Production**: Uses `os.getenv` to transparently read environment variables injected by the hosting provider (e.g., Streamlit Cloud Secrets).

## Data Sources

The platform aggregates data from multiple diverse sources:
- **Federal Reserve Economic Data (FRED)**: User Treasury yields and corporate option-adjusted spreads.
- **Yahoo Finance**: Equity prices, ETF data, and volatility indices (MOVE, VIX).
- **NewsAPI**: Real-time financial headlines and sentiment analysis context.
- **Google GenAI**: Qualitative synthesis for credit memo generation.
