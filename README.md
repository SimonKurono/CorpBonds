# 🏦 Raffles Advisors – Financial Analytics Platform

A **Streamlit-powered analytics dashboard** for monitoring **US corporate bond markets**, **equity analysis**, **portfolio management**, and quantitative research tools. Features real-time market data, news aggregation, and interactive visualizations.


## 🚀 Features

### ✅ Current Functionality

* **Market Headlines**

  * Top 5 news articles fetched via NewsAPI (with images, metadata, and links).
* **Core Rates**

  * Key Treasury and Fed rates with real-time metrics (Δ in bp/%).
  * Automatic calculation of **10y–2y slope**.
* **Treasury Curves**

  * Multi-tab yield curves from 1W to 20Y history.
  * Flexible maturity selection (2Y, 10Y, etc.).
* **Slope & Yields**

  * Interactive line chart for **2s10s slope**.
  * **ICE BofA US HY Index yields** by rating bucket.
* **Option-Adjusted Spread (OAS)**

  * IG vs HY OAS against 10Y Treasury.
  * Rating bucket OAS curves (AAA–CCC).
  * Live KPI grid (dispersion, vol, OAS–Treasury spreads, 1M/1W changes).
* **Volatility**

  * **CBOE MOVE Index** time series.
  * Latest MOVE metrics.

* **News**

  * View top headlines across 5 sectors
  * Search for news based on criteria and source

* **Stock Search & Analysis** 📈
  * Search any stock or ETF ticker with real-time Yahoo Finance data
  * Normalized performance charts with benchmark comparison
  * View sector, industry, and business information
  * Historical price data visualization

* **Quant Playground** 🧮
  * Monte Carlo simulations (Geometric Brownian Motion)
  * Moving average analysis with customizable windows
  * Relative value z-score calculations
  * Strategy prototyping with performance backtesting
  * Performance metrics: CAGR, Volatility, Sharpe Ratio, Max Drawdown

* **Portfolio Management** 💼
  * Buy and sell stocks directly in the interface
  * Real-time portfolio holdings with current market prices
  * Portfolio allocation pie charts
  * Performance metrics: CAGR, Volatility, Sharpe Ratio, Max Drawdown
  * Portfolio value and cumulative returns charts
  * Complete transaction history tracking
  * *Placeholder: Return attribution analysis and database persistence*

* **Credit Memo AI** 🤖
  * Generate buy-side credit memos using Gemini LLM with qualitative analysis, risk assessment, and scenario planning


### 🛠️ In Progress

* **Client Login**

  * Authentication and client-specific dashboards for private access.



## 📊 Data Sources

* **[FRED API](https://fred.stlouisfed.org/)** – US Treasury yields & economic data.
* **NewsAPI** – Top financial headlines.
* **Yahoo Finance** – MOVE index, CDS spreads, stock prices, and market data.



## 🖥️ Tech Stack

* **Python 3.11+**
* **Streamlit** – dashboard framework
* **Pandas** / **Plotly** – data wrangling & visualization
* **NumPy** – numerical computations and statistical analysis
* **Yahoo Finance** – real-time market data and stock information
* **Dateutil** – date handling (rolling periods, deltas)
* **Custom Fetcher Modules**

  * `rate_fetcher` – core Treasury/Fed rates
  * `graph_fetcher` – FRED series (Treasury yields)
  * `oas_fetcher` – OAS and spread data
  * `yield_bucket_fetcher` – HY yields by rating
  * `cds_move_fetcher` – MOVE index
  * `news_fetcher` – financial news aggregation



## ⚡ Project Status

* **Current Stage:**
  Stable **beta release** – fully interactive financial analytics platform with:
  - Fixed-income market monitoring (Treasury curves, OAS, spreads)
  - Real-time news aggregation and search
  - Stock search and analysis
  - Quantitative tools and strategy backtesting
  - Portfolio management and tracking

* **Next Milestones:**

  * 🔐 Implement client login (secure access).
  * 💾 Add database persistence for portfolio data.
  * 📊 Enhance return attribution analysis.
  * 🔗 Improve integration between pages.
  * ☁️ Deploy on Streamlit Cloud / custom VPS.



## 📦 Installation

```bash
# clone repository
git clone https://github.com/SimonKurono/corpbonds-dashboard.git
cd corpbonds

# install dependencies
pip install -r requirements.txt

# run locally
streamlit run Home.py
```


