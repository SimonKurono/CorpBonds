# streamlit_app/Home.py
import streamlit as st
import utils.ui as ui
from datetime import date, datetime

def main() -> None:
    # 1) Page config FIRST
    ui.configure_page(page_title="Raffles Bond Platform", page_icon="🏦", layout="wide")

    # 2) Sidebar next
    ui.render_sidebar()

    # ---------- HERO ----------
    with st.container():
        c1, c2 = st.columns([2, 1], vertical_alignment="center")

        with c1:
            st.caption("Fixed-income intelligence, unified.")

            kpis = (("IG OAS", "114 bp"), ("2s10s", "-28 bp"), ("Sentiment (IG)", "+0.21"))
            cols = st.columns(3)
            for i, (label, value) in enumerate(kpis):
                cols[i].metric(label, value)

            # CTAs (no always-true ifs)
            st.button(
                "→ Go to Dashboard",
                type="primary",
                use_container_width=False,
                on_click=lambda: ui.go("pages/Dashboard.py"),
            )
            st.button(
                "Learn more",
                use_container_width=False,
                on_click=lambda: ui.go("pages/Client_Login.py"),
            )

        # IMPORTANT: same indentation level as c1
        with c2:
            st.write("**Yield curve teaser**")
            tenor = st.slider("Tenor (months)", 1, 360, 120, label_visibility="collapsed")
            implied = round(0.8 + 1.2 * (1 - 2 ** (-tenor / 60.0)), 3)
            st.metric("Implied Yield", f"{implied}%")

    st.divider()

    # ---------- FEATURE GRID ----------
    st.subheader("Explore the toolkit")
    st.caption("Everything you need for credit & cross-asset workflows.")
    features = [
        ("📊 Market Dashboard", "Curves, OAS & sector heatmaps at a glance.", "pages/Dashboard.py"),
        ("🧮 Quant / RV", "z-scores, beta/alpha, tracking error, correlations.", "pages/Quant_Playground.py"),
        ("💼 Portfolio + Benchmarks", "TWR returns, drawdowns; SPY/LQD/HYG one-click.", "pages/Portfolio.py"),
        ("📰 News", "Curated feed with issuer/sector filters + AI summaries.", "pages/News.py"),
        ("📈 Stats", "Treasuries, OAS/CDS, curve spreads — CSV downloads.", "pages/Relative_Value_Screener.py"),
        ("🔎 Search", "Find tickers/CUSIPs; add to portfolio or open in Quant.", "pages/Stock_Search.py"),
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

    st.subheader("Data Freshness")
    today = date.today()
    hour = datetime.now().strftime("%I:%M %p")
    f1, f2, f3 = st.columns(3)
    f1.info(f"Treasuries: EOD • {today}")
    f2.info(f"IG/HY OAS: EOD • {today}")
    f3.info(f"News/Sentiment: Hourly • {hour} PT")
    st.caption("Data updated daily after market close (4pm ET) unless otherwise noted.")

    st.write("---")
    st.caption(f"© Raffles Advisors • For research and education • As-of: {today.isoformat()}")

if __name__ == "__main__":
    main()
