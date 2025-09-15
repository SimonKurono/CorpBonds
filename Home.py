# streamlit_app/Home.py
import streamlit as st
from datetime import date

st.set_page_config(page_title="Raffles Bond Platform", page_icon="🏦", layout="wide")

# ---------- Helpers ----------
def go(page_path: str):
    try:
        st.switch_page(page_path)
    except Exception:
        st.warning(f"Page not found: {page_path}")

def is_signed_in() -> bool:
    return bool(st.session_state.get("access_token"))

# ---------- HERO ----------
st.title("🏦 Raffles Bond Platform")
st.caption("Fixed-income intelligence, unified.")

c1, c2 = st.columns([2, 1], vertical_alignment="center")

with c1:
    # KPIs (placeholders for now)
    k1, k2, k3 = st.columns(3)
    k1.metric("IG OAS", "114 bp")
    k2.metric("2s10s", "-28 bp")
    k3.metric("Sentiment (IG)", "+0.21")

    # Primary actions
    if is_signed_in():
        st.button("→ Go to Dashboard", type="primary", use_container_width=True,
                  on_click=lambda: go("pages/1_📊_Dashboard.py"))
    else:
        st.button("🔐 Sign in to get started", type="primary", use_container_width=True, disabled=True)
        st.caption("Sign-in enables your saved portfolios & preferences. (Wire this after /auth)")

with c2:
    # Interactive teaser (mock yield for selected tenor)
    st.write("**Yield curve teaser**")
    tenor = st.slider("Tenor (months)", 1, 360, 120, label_visibility="collapsed")
    # Simple mock curve
    implied = round(0.8 + 1.2 * (1 - 2 ** (-tenor / 60.0)), 3)
    st.metric("Implied Yield", f"{implied}%")

st.divider()

# ---------- FEATURE GRID (native) ----------
st.subheader("Explore the toolkit")
st.caption("Everything you need for credit & cross-asset workflows.")

features = [
    ("📊 Market Dashboard", "Curves, OAS & sector heatmaps at a glance.", "pages/1_📊_Dashboard.py"),
    ("🧮 Quant / RV", "z-scores, beta/alpha, tracking error, correlations.", "pages/2_🧮_Quant.py"),
    ("💼 Portfolio + Benchmarks", "TWR returns, drawdowns; SPY/LQD/HYG one-click.", "pages/3_💼_Portfolio.py"),
    ("📰 News", "Curated feed with issuer/sector filters + AI summaries.", "pages/4_📰_News.py"),
    ("📈 Stats", "Treasuries, OAS/CDS, curve spreads — CSV downloads.", "pages/5_📈_Stats.py"),
    ("🔎 Search", "Find tickers/CUSIPs; add to portfolio or open in Quant.", "pages/6_🔎_Search.py"),
]

for row in range(0, len(features), 3):
    cols = st.columns(3)
    for i, col in enumerate(cols):
        idx = row + i
        if idx >= len(features): break
        title, desc, target = features[idx]
        with col:
            box = st.container(border=True, height="stretch", vertical_alignment="distribute")
            with box:
                st.markdown(f"### {title}")
                st.caption(desc)
                # A simple open button per card
                st.button("Open", key=f"open_{idx}", use_container_width=True,
                          on_click=lambda t=target: go(t))

st.divider()

# ---------- ABOUT ----------
st.subheader("About")
st.write(
    "Built for analysts and PMs who value speed and consistency. "
    "The platform ingests market data once into a central database, then serves every page "
    "through a unified API so numbers stay consistent across dashboards, quant tools, and portfolios."
)

# ---------- DATA FRESHNESS (placeholders; wire to /stats later) ----------
st.subheader("Data Freshness")
f1, f2, f3 = st.columns(3)
f1.info("Treasuries: EOD • 2025-09-12")
f2.info("IG/HY OAS: EOD • 2025-09-12")
f3.info("News/Sentiment: Hourly • 12:00 PT")
st.caption("Wire these to your freshness table & cached endpoints once the API is live.")

# ---------- FOOTER ----------
st.write("---")
st.caption(f"© Raffles Advisors • For research and education • As-of: {date.today().isoformat()}")
