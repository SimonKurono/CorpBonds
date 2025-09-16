# streamlit_app/Home.py
import streamlit as st
import utils.ui as ui
from datetime import date

# ---------- Page Config ----------
st.set_page_config(page_title="Raffles Bond Platform", page_icon="🏦", layout="wide")
ui.render_sidebar()

# ---------- HERO ----------

ui.hero_split(
    title="🏦 Raffles Bond Platform",
    subtitle="Fixed-income intelligence, unified.",
    img_path="assets/hero_banner_dark.png",      # put your banner here
    kpis=(("IG OAS","114 bp"),("2s10s","-28 bp"),("Sentiment (IG)","+0.21")),
    primary_label="→ Go to Dashboard",
    primary_page="pages/1_📊_Dashboard.py",
    secondary_label="Learn more",
    secondary_page=None,  # you can wire later
)
st.divider()


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
    if ui.is_signed_in():
        st.button("→ Go to Dashboard", type="primary", use_container_width=True,
                  on_click=lambda: ui.go("pages/1_📊_Dashboard.py"))
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

ui.feature_grid(features, columns=3)

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
