# streamlit_app/Home.py
import streamlit as st
import utils.ui as ui
from datetime import date
from datetime import datetime

# ---------- Page Config ----------
def configure_page():
    ui.configure_page(page_title="Raffles Bond Platform", page_icon="🏦", layout="wide")
    ui.render_sidebar()

# ---------- HERO ----------
def render_hero():
    with st.container():
        st.markdown('<div class="full-height">', unsafe_allow_html=True)
        
        c1, c2 = st.columns([2,1], vertical_alignment="center")
        with c1:
            st.title("🏦 Raffles Bond Platform")
            st.caption("Fixed-income intelligence, unified.")

            kpis=(("IG OAS","114 bp"),("2s10s","-28 bp"),("Sentiment (IG)","+0.21"))
            cols = st.columns(3)
            for (i,(label, value)) in enumerate(kpis):
                cols[i].metric(label, value)

            # CTAs
            if "pages/Dashboard.py":
                st.button("→ Go to Dashboard", type="primary", use_container_width=False,
                        on_click=lambda: ui.go("pages/Dashboard.py"))
            else:
                st.button("→ Go to Dashboard", type="primary", disabled=True)

            if "Learn more":
                st.button("Learn more", use_container_width=False,
                        on_click=(lambda: ui.go("pages/Client_Login.py")) if "pages/Client_Login.py" else None)

            with c2:
                # Interactive teaser (mock yield for selected tenor)
                st.write("**Yield curve teaser**")
                tenor = st.slider("Tenor (months)", 1, 360, 120, label_visibility="collapsed")
                # Simple mock curve
                implied = round(0.8 + 1.2 * (1 - 2 ** (-tenor / 60.0)), 3)
                st.metric("Implied Yield", f"{implied}%")



# ---------- FEATURE GRID (native) ----------
def render_feature_grid():
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



# ---------- ABOUT ----------
def render_about():
    st.subheader("About")
    st.write(
        "Built for analysts and PMs who value speed and consistency. "
        "The platform ingests market data once into a central database, then serves every page "
        "through a unified API so numbers stay consistent across dashboards, quant tools, and portfolios."
    )

    # ---------- DATA FRESHNESS (placeholders; wire to /stats later) ----------
    st.subheader("Data Freshness")
    today = date.today()
    hour = datetime.now().strftime("%H:%M %p")
    f1, f2, f3 = st.columns(3)
    f1.info(f"Treasuries: EOD • {today}")
    f2.info(f"IG/HY OAS: EOD • {today}")
    f3.info(f"News/Sentiment: Hourly • {hour} PDT")
    st.caption("Data updated daily after market close (4pm ET) unless otherwise noted.")

# ---------- FOOTER ----------
def render_footer():
    st.write("---")
    st.caption(f"© Raffles Advisors • For research and education • As-of: {date.today().isoformat()}")

def main():
    configure_page()
    
    render_hero()
    st.divider()
    
    render_feature_grid()
    st.divider()

    render_about()
    render_footer()

if __name__ == "__main__":
    main()