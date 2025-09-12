# 🏦 Raffles Advisors – US Corporate Bond Dashboard

A **Streamlit-powered analytics dashboard** for monitoring **US corporate bond markets**, **Treasury yield curves**, and related fixed-income indicators.

---

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

### 🛠️ In Progress

* **Equity Search & Integration**

  * Stock lookup with charts and key fundamentals.
* **Client Login**

  * Authentication and client-specific dashboards for private access.

---

## 📊 Data Sources

* **[FRED API](https://fred.stlouisfed.org/)** – US Treasury yields & economic data.
* **NewsAPI** – Top financial headlines.
* **Yahoo Finance** – MOVE index & CDS spreads.

---

## 🖥️ Tech Stack

* **Python 3.11+**
* **Streamlit** – dashboard framework
* **Pandas** / **Plotly** – data wrangling & visualization
* **Dateutil** – date handling (rolling periods, deltas)
* **Custom Fetcher Modules**

  * `rate_fetcher` – core Treasury/Fed rates
  * `graph_fetcher` – FRED series (Treasury yields)
  * `oas_fetcher` – OAS and spread data
  * `yield_bucket_fetcher` – HY yields by rating
  * `cds_move_fetcher` – MOVE index

---

## ⚡ Project Status

* **Current Stage:**
  Stable **beta release** – fully interactive fixed-income dashboard with real-time news, rates, and spreads.

* **Next Milestones:**

  * 🔐 Implement client login (secure access).
  * 📈 Add equity search (Yahoo Finance integration).
  * 🗂️ Package helper modules for reusability.
  * ☁️ Deploy on Streamlit Cloud / custom VPS.

---

## 📦 Installation

```bash
# clone repository
git clone https://github.com/SimonKurono/corpbonds-dashboard.git
cd corpbonds-dashboard

# install dependencies
pip install -r requirements.txt

# run locally
streamlit run Dashboard.py
```

-
