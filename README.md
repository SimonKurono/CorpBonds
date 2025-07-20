# Raffles Advisors US Corporate‐Bond Dashboard

This Streamlit app provides:
- ☑️ Live news feed
- ☑️ Core rates & yield‐curve charts
- ☑️ Volatility (MOVE & CDS proxy)
- ☑️ OAS metrics & charts
- 🔜 Relative‐value screener, issuance, fund flows, etc.

## Getting started

1. `git clone https://github.com/your-username/corpbonds-dashboard.git`
2. `cd corpbonds-dashboard`
3. `python -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `streamlit run app.py`

## Credentials

- Copy your `credentials.yaml` (with hashed passwords) into the root.
- Create a `.env` file with `FRED_API_KEY=…`

