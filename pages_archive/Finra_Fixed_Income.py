# pages/Finra_Fixed_Income.py ─────────────────────────────────────────────────────────
"""FINRA Fixed Income Metrics."""

from __future__ import annotations

# ── Third-party
import streamlit as st

# ── Local
import utils.fetchers.finra_fetcher as finra
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
ENV_OPTIONS = {
    "Mock": {"env": "prod", "mock": True, "note": "Uses mock datasets; good for testing without data charges."},
    "QA Test": {"env": "qa", "mock": False, "note": "FINRA QA test environment (requires QA token URL)."},
    "Production": {"env": "prod", "mock": False, "note": "Live production datasets; counts toward usage limits."},
}

MARKET_DATASETS = {
    "Corporate Market Sentiment": {
        "group": "fixedIncomeMarket",
        "name": "corporateMarketSentiment",
        "fields": ["tradeReportDate", "tradeType", "totalVolume", "totalTrades", "totalTransactions"],
    },
    "Corporate Market Breadth": {
        "group": "fixedIncomeMarket",
        "name": "corporateMarketBreadth",
        "fields": ["tradeReportDate", "tradeType", "totalVolume", "totalTrades", "totalTransactions"],
    },
    "Corporate 144A Market Sentiment": {
        "group": "fixedIncomeMarket",
        "name": "corporate144AMarketSentiment",
        "fields": ["tradeReportDate", "tradeType", "totalVolume", "totalTrades", "totalTransactions"],
    },
    "Agency Market Sentiment": {
        "group": "fixedIncomeMarket",
        "name": "agencyMarketSentiment",
        "fields": ["tradeReportDate", "tradeType", "totalVolume", "totalTrades", "totalTransactions"],
    },
    "Agency Market Breadth": {
        "group": "fixedIncomeMarket",
        "name": "agencyMarketBreadth",
        "fields": ["tradeReportDate", "tradeType", "totalVolume", "totalTrades", "totalTransactions"],
    },
}

VOLUME_DATASETS = {
    "Corporate & Agency Capped Volume": {
        "group": "fixedIncomeMarket",
        "name": "corporatesAndAgenciesCappedVolume",
        "fields": ["tradeReportDate", "tradeType", "productCategory", "totalVolume", "totalTransactions", "totalTrades"],
    },
    "Securitized Products Capped Volume": {
        "group": "fixedIncomeMarket",
        "name": "securitizedProductsCappedVolume",
        "fields": ["tradeReportDate", "tradeType", "productCategory", "totalVolume", "totalTransactions", "totalTrades"],
    },
}

TREASURY_DATASETS = {
    "Treasury Daily Aggregates": {
        "group": "fixedIncomeMarket",
        "name": "treasuryDailyAggregates",
        "fields": ["tradeDate", "yearsToMaturity", "dealerCustomerVolume", "dealerCustomerCount", "atsInterdealerVolume"],
    },
    "Treasury Monthly Aggregates": {
        "group": "fixedIncomeMarket",
        "name": "treasuryMonthlyAggregates",
        "fields": ["tradeMonth", "yearsToMaturity", "dealerCustomerVolume", "dealerCustomerCount", "atsInterdealerVolume"],
    },
}

TRADE_TYPE_CHOICES = [
    "",
    "all securities",
    "investment grade",
    "high yield",
    "convertible bonds",
    "church bonds",
]
DEFAULT_LIMIT = 50
MAX_LIMIT = 500
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Helpers ─────────────────────────────╮
@st.cache_data(ttl=300, show_spinner=False)
def _load_dataset(group: str, name: str, env: str, mock: bool, payload: dict) -> list | dict | None:
    """Cached FINRA dataset loader."""
    return finra.fetch_dataset(group, name, env=env, mock=mock, payload=payload)


def _require_credentials(env: str, mock: bool) -> bool:
    """Check credentials for non-mock environments."""
    if not mock and (env == "prod" or env == "qa"):
        if finra.get_credentials() is None:
            st.warning("FINRA credentials missing. Set FINRA_CLIENT_ID and FINRA_CLIENT_SECRET in your environment or Streamlit secrets.")
            return False
    return True


def _render_dataset_selector(label: str, datasets: dict[str, dict[str, str]]) -> dict[str, str]:
    choice = st.selectbox(label, list(datasets.keys()))
    return datasets[choice]


def _build_payload(fields: list[str], limit: int, *, trade_type: str = "", product_category: str = "", years_to_maturity: str = "") -> dict:
    payload: dict = {"limit": limit, "fields": fields}
    filters = []
    if trade_type:
        filters.append({"compareType": "equal", "fieldName": "tradeType", "fieldValue": trade_type})
    if product_category:
        filters.append({"compareType": "equal", "fieldName": "productCategory", "fieldValue": product_category})
    if years_to_maturity:
        filters.append({"compareType": "equal", "fieldName": "yearsToMaturity", "fieldValue": years_to_maturity})
    if filters:
        payload["compareFilters"] = filters
    return payload


def _render_table(records: list | dict | None, title: str) -> None:
    if records is None:
        st.error("No data returned.")
        return
    df = finra.to_frame(records)
    if df is None or df.empty:
        st.info("Empty response.")
        return
    st.subheader(title)
    st.dataframe(df, use_container_width=True)
    st.caption(f"Rows: {len(df)}")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    ui.configure_page(page_title="FINRA Fixed Income", page_icon="📊", layout="wide")
    ui.render_sidebar()
    st.caption("FINRA fixed income market aggregates: sentiment, breadth, capped volume, and Treasury aggregates.")


def render_environment_controls() -> tuple[str, bool]:
    cols = st.columns([2, 3])
    with cols[0]:
        env_choice = st.radio("Environment", list(ENV_OPTIONS.keys()), horizontal=True, index=0)
    with cols[1]:
        st.caption(ENV_OPTIONS[env_choice]["note"])
    cfg = ENV_OPTIONS[env_choice]
    return cfg["env"], cfg["mock"]


def render_market_section(env: str, mock: bool) -> None:
    st.header("Market Breadth & Sentiment")
    meta = _render_dataset_selector("Dataset", MARKET_DATASETS)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        trade_type = st.selectbox("Trade type (optional)", TRADE_TYPE_CHOICES, index=0)
    with col2:
        limit = st.slider("Max rows", 5, MAX_LIMIT, DEFAULT_LIMIT, step=5)
    with col3:
        product_category = st.text_input("Product category filter (optional)", placeholder="e.g., affiliate buy")

    payload = _build_payload(meta["fields"], limit, trade_type=trade_type, product_category=product_category)
    if _require_credentials(env, mock):
        records = _load_dataset(meta["group"], meta["name"], env, mock, payload)
        _render_table(records, meta["name"])


def render_volume_section(env: str, mock: bool) -> None:
    st.header("Capped Volume")
    meta = _render_dataset_selector("Dataset", VOLUME_DATASETS)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        trade_type = st.selectbox("Trade type (optional)", TRADE_TYPE_CHOICES, index=0, key="volume_trade_type")
    with col2:
        limit = st.slider("Max rows", 5, MAX_LIMIT, DEFAULT_LIMIT, step=5, key="volume_limit")
    with col3:
        product_category = st.text_input("Product category filter (optional)", placeholder="e.g., high yield", key="volume_product_category")

    payload = _build_payload(meta["fields"], limit, trade_type=trade_type, product_category=product_category)
    if _require_credentials(env, mock):
        records = _load_dataset(meta["group"], meta["name"], env, mock, payload)
        _render_table(records, meta["name"])


def render_treasury_section(env: str, mock: bool) -> None:
    st.header("Treasury Aggregates")
    meta = _render_dataset_selector("Dataset", TREASURY_DATASETS)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        limit = st.slider("Max rows", 5, MAX_LIMIT, DEFAULT_LIMIT, step=5, key="tsy_limit")
    with col2:
        years_to_maturity = st.text_input("Years to maturity filter (optional)", placeholder="<= 2 years", key="tsy_ytm")
    with col3:
        st.caption("Filters use compareType=equal. Leave blank to fetch all rows within the limit.")

    payload = _build_payload(meta["fields"], limit, years_to_maturity=years_to_maturity)
    if _require_credentials(env, mock):
        records = _load_dataset(meta["group"], meta["name"], env, mock, payload)
        _render_table(records, meta["name"])
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    render_header()
    env, mock = render_environment_controls()

    tabs = st.tabs(["Market Breadth / Sentiment", "Capped Volume", "Treasury Aggregates"])
    with tabs[0]:
        render_market_section(env, mock)
    with tabs[1]:
        render_volume_section(env, mock)
    with tabs[2]:
        render_treasury_section(env, mock)


if __name__ == "__main__":
    main()
