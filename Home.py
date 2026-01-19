# Home.py ─────────────────────────────────────────────────────────
"""Financial Analytics Platform Home Page."""

from __future__ import annotations

# ── Stdlib
from datetime import date, datetime

# ── Third-party
import streamlit as st

# ── Local
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
HERO_KPIS = (
    ("IG OAS", "114 bp"),
    ("2s10s", "-28 bp"),
    ("Sentiment (IG)", "+0.21"),
)

FEATURES = [
    ("📊 Market Dashboard", "Curves, OAS & sector heatmaps at a glance.", "pages/Dashboard.py"),
    ("🧮 AI Credit Memo Generator", "Generate structured buy-side credit analysis.", "pages/Credit_Memo_AI.py"),
    ("💼 Portfolio + Benchmarks", "TWR returns, drawdowns; SPY/LQD/HYG one-click.", "pages/Portfolio.py"),
    ("📰 News", "Curated feed with issuer/sector filters + AI summaries.", "pages/News.py"),
    ("📈 Stats", "Treasuries, OAS/CDS, curve spreads — CSV downloads.", "pages/Relative_Value_Screener.py"),
    ("🔎 Search", "Find tickers/CUSIPs; add to portfolio or open in Quant.", "pages/Stock_Search.py"),
]

FEATURE_GRID_COLUMNS = 3
HERO_KPI_COLUMNS = 3
YIELD_TEASER_MIN_TENOR = 1
YIELD_TEASER_MAX_TENOR = 360
YIELD_TEASER_DEFAULT_TENOR = 120
YIELD_TEASER_BASE = 0.8
YIELD_TEASER_COEFF = 1.2
YIELD_TEASER_DECAY = 60.0

ABOUT_TEXT = (
    "Built for analysts and PMs who value speed and consistency. "
    "The platform ingests market data once into a central database, then serves every page "
    "through a unified API so numbers stay consistent across dashboards, quant tools, and portfolios."
)

COPYRIGHT_TEXT = "© Raffles Advisors • For research and education"
DATA_UPDATE_NOTE = "Data updated daily after market close (4pm ET) unless otherwise noted."
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Helpers and caching ──────────────────────╮
def _calculate_implied_yield(tenor: int) -> float:
    """Calculate implied yield based on tenor using exponential decay model."""
    return round(
        YIELD_TEASER_BASE + YIELD_TEASER_COEFF * (1 - 2 ** (-tenor / YIELD_TEASER_DECAY)),
        3
    )
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Raffles Bond Platform", page_icon="🏦", layout="wide")
    ui.render_sidebar()


def render_hero_section() -> None:
    """Render hero section with KPIs, CTAs, and yield curve teaser."""
    with st.container():
        c1, c2 = st.columns([2, 1], vertical_alignment="center")

        with c1:
            st.caption("Fixed-income intelligence, unified.")

            # Render KPIs
            cols = st.columns(HERO_KPI_COLUMNS)
            for i, (label, value) in enumerate(HERO_KPIS):
                cols[i].metric(label, value)

            # Call-to-action buttons
            if st.button(
                "→ Go to Dashboard",
                type="primary",
                use_container_width=False,
            ):
                ui.go("pages/Dashboard.py")

            # if st.button(
            #     "Learn more",
            #     use_container_width=False,
            # ):
            #     ui.go("pages/Client_Login.py")

        with c2:
            st.write("**Yield curve teaser**")
            tenor = st.slider(
                "Tenor (months)",
                YIELD_TEASER_MIN_TENOR,
                YIELD_TEASER_MAX_TENOR,
                YIELD_TEASER_DEFAULT_TENOR,
                label_visibility="collapsed"
            )
            implied = _calculate_implied_yield(tenor)
            st.metric("Implied Yield", f"{implied}%")


def render_feature_grid() -> None:
    """Render feature grid showcasing platform capabilities."""
    st.subheader("Explore the toolkit")
    st.caption("Everything you need for credit & cross-asset workflows.")
    ui.feature_grid(FEATURES, columns=FEATURE_GRID_COLUMNS)


def render_about_section() -> None:
    """Render about section with platform description."""
    st.subheader("About")
    st.write(ABOUT_TEXT)


def render_data_freshness() -> None:
    """Render data freshness information."""
    st.subheader("Data Freshness")
    today = date.today()
    hour = datetime.now().strftime("%I:%M %p")
    
    f1, f2, f3 = st.columns(3)
    f1.info(f"Treasuries: EOD • {today}")
    f2.info(f"IG/HY OAS: EOD • {today}")
    f3.info(f"News/Sentiment: Hourly • {hour} PT")
    
    st.caption(DATA_UPDATE_NOTE)


def render_footer() -> None:
    """Render footer with copyright and date information."""
    today = date.today()
    st.write("---")
    st.caption(f"{COPYRIGHT_TEXT} • As-of: {today.isoformat()}")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()

    render_hero_section()
    st.divider()

    render_feature_grid()
    st.divider()

    render_about_section()
    render_data_freshness()
    render_footer()


if __name__ == "__main__":
    main()
