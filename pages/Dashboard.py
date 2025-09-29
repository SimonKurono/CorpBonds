# app.py  ─────────────────────────────────────────────────────────
"""Raffles Advisors – US Corporate-Bond Dashboard (Streamlit)."""

from __future__ import annotations

# ── Stdlib
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, Mapping
from dateutil.relativedelta import relativedelta
from streamlit_extras.add_vertical_space import add_vertical_space
from dateutil.parser import isoparse

# ── Third-party
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Local
import utils.fetchers.news_fetcher as nf
import utils.fetchers.rate_fetcher as rf
import utils.fetchers.graph_fetcher as gf          # provides YIELD_SERIES_IDS, load_fred_data
import utils.fetchers.oas_fetcher as of
import utils.fetchers.yield_bucket_fetcher as ybf
import utils.fetchers.cds_move_fetcher as cmf
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
APP_TITLE = "🏦 Raffles Advisors – US Corporate-Bond Dashboard"
NEWS_MAX = 5
KPI_PER_ROW = 3

# Cache TTLs (seconds)
TTL_NEWS = 60 * 30
TTL_CORE_RATES = 60 * 60 * 6
TTL_WEEKLY_CURVE = 60 * 60 * 6
TTL_YIELD_BY_RATING = 60 * 60 * 60
TTL_MOVE = 60 * 60 * 60

# Plotly defaults
FIG_TEMPLATE = "plotly_white"
FIG_MARGIN = dict(t=50, b=40, l=40, r=40)

# Time tabs
PERIODS: dict[str, dict[str, str]] = {
    "1W":   {"start": (date.today() - relativedelta(weeks=1)).isoformat(), "freq": "D"},
    "1M":   {"start": (date.today() - relativedelta(months=1)).isoformat(), "freq": "D"},
    "6M":   {"start": (date.today() - relativedelta(months=6)).isoformat(), "freq": "D"},
    "1Y":   {"start": (date.today() - relativedelta(years=1)).isoformat(),  "freq": "D"},
    "2Y":   {"start": (date.today() - relativedelta(years=2)).isoformat(),  "freq": "W"},
    "5Y":   {"start": (date.today() - relativedelta(years=5)).isoformat(),  "freq": "W"},
    "10Y":  {"start": (date.today() - relativedelta(years=10)).isoformat(), "freq": "W-Fri"},
    "20Y":  {"start": (date.today() - relativedelta(years=20)).isoformat(), "freq": "W-Fri"},
    "MAX":  {"start": "1900-01-01", "freq": "W-Fri"},
}
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Helpers & caching ──────────────────────╮
def _apply_fig_defaults(fig: go.Figure, *, title: str | None = None,
                        x_title: str | None = None, y_title: str | None = None) -> go.Figure:
    """Apply shared Plotly layout defaults."""
    fig.update_layout(
        template=FIG_TEMPLATE,
        margin=FIG_MARGIN,
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend=dict(x=0, y=1.05, orientation="h"),
    )
    return fig

def _fmt_bp(val: float | int | None) -> str:
    """Format basis points safely."""
    return "—" if val is None else f"{float(val):.1f} bp"

def _fmt_pct_unit(val: float | int | None) -> str:
    """Format value as % (already percent, not bp)."""
    return "—" if val is None else f"{float(val):+.2f} %"

@st.cache_data(ttl=TTL_NEWS)
def get_headlines() -> list[Mapping[str, Any]]:
    return nf.fetch_headlines()

@st.cache_data(ttl=TTL_CORE_RATES)
def get_core_rates() -> Mapping[str, tuple[float, float] | float]:
    return rf.fetch_core_rates()

@st.cache_data(ttl=TTL_YIELD_BY_RATING)
def get_yields(start_date: str, freq: str = "W-FRI") -> pd.DataFrame:
    return ybf.fetch_yield_by_rating(start_date)

@st.cache_data(ttl=TTL_WEEKLY_CURVE)
def get_weekly_curve(ids: dict[str, str] | None = None) -> pd.DataFrame:
    """Weekly history since 2005 (W-FRI). If ids is None, pull all."""
    if ids is None:
        ids = gf.YIELD_SERIES_IDS
    return gf.load_fred_data("2005-01-01", ids)  # default freq = W-FRI

@st.cache_data(ttl=TTL_CORE_RATES)
def get_curve(start_date: str, ids: dict[str, str], freq: str) -> pd.DataFrame:
    """Unified curve fetcher for any period/frequency."""
    return gf.load_fred_data(start_date, ids, freq=freq)

@st.cache_data(ttl=TTL_MOVE)
def get_move(start_date: str) -> pd.DataFrame:
    return cmf.fetch_move_yahoo_series(start_date)
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    st.set_page_config(page_title="Raffles Bond DB", page_icon="🏦", layout="wide")
    st.markdown("<style>.block-container{margin-left:auto;margin-right:auto;}</style>", unsafe_allow_html=True)
    st.title(APP_TITLE)

def render_sidebar() -> None:
    ui.render_sidebar()

def render_news_panel(headlines: list[Mapping[str, Any]]) -> None:
    """Top 5 headlines: 1 featured + 4 in grid."""
    st.header("Today’s Headlines")
    if not headlines:
        st.info("No news available.")
        return

    feature, *others = headlines[:NEWS_MAX]
    if feature.get("urlToImage"):
        st.image(feature["urlToImage"], use_container_width=True)
    f_pub = isoparse(feature["publishedAt"]).astimezone(timezone.utc)
    st.markdown(f"**{f_pub:%B %d %Y}** | *{feature['source']['name']}*")
    st.subheader(feature["title"])
    st.write(feature.get("description", ""))
    st.markdown(f"[Read more]({feature['url']})")
    st.markdown("---")

    for pair in (others[0:2], others[2:4]):
        for art, cell in zip(pair, st.columns(2, gap="small")):
            with cell:
                if art.get("urlToImage"):
                    st.image(art["urlToImage"], width=160)
                a_pub = isoparse(art["publishedAt"].replace("Z", "+00:00"))
                st.markdown(
                    f"<small>{a_pub:%b %d} | {art['source']['name']}</small>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{art['title']}**")
                st.markdown(f"[Read more]({feature['url']})")  # kept as-is by request
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

def render_core_rates_panel(core_rates: Mapping[str, tuple[float, float] | float]) -> None:
    """KPI grid + slope caption."""
    st.header("Core Rates")
    items = list(core_rates.items())
    for row in range(0, len(items), KPI_PER_ROW):
        for (lbl, data), col in zip(items[row:row + KPI_PER_ROW], st.columns(KPI_PER_ROW, gap="small")):
            val, delta = (data if isinstance(data, (list, tuple)) and len(data) == 2 else (float(data), 0.0))
            # bp vs % formatting
            is_pct = ('Year' in lbl) or ('Funds' in lbl)
            fmt_val = f"{val/100:.2%}" if is_pct else f"{val:.0f} bp"
            fmt_delta = _fmt_pct_unit(delta) if is_pct else f"{delta:+.2f} bp"
            col.metric(lbl, fmt_val, fmt_delta)

    two_rate = core_rates.get("2 Year", (None, None))[1]
    ten_rate = core_rates.get("10 Year", (None, None))[1]
    if two_rate is not None and ten_rate is not None:
        st.caption(f"10y – 2y slope = {ten_rate - two_rate:.2f} bp")

def render_slope_and_yields() -> None:
    """Slope (10s/2s) + HY yield by rating tabs."""
    st.header("Slope")
    wk_curve_all = get_weekly_curve()
    slope_wk = (wk_curve_all["10 Year"] - wk_curve_all["2 Year"]).to_frame("10y–2y")
    yield_curve = get_yields("2000-01-01")

    slope_tab, yield_curve_by_rating = st.tabs(["Slope (10y-2y)", "HY Yield by Rating"])

    with slope_tab:
        fig_s = px.line(
            slope_wk, x=slope_wk.index, y="10y–2y",
            labels={"index": "Date", "10y–2y": "Slope (bp)"},
        )
        _apply_fig_defaults(fig_s, title="2s10s Slope", x_title="Date", y_title="Basis (bp)")
        st.plotly_chart(fig_s, use_container_width=True, key="slope")
        st.dataframe(slope_wk.tail())

    with yield_curve_by_rating:
        fig_ybf = go.Figure()
        for col in yield_curve.columns:
            fig_ybf.add_trace(go.Scatter(x=yield_curve.index, y=yield_curve[col], name=col, line=dict(width=2)))
        fig_ybf.update_layout(title="ICE BofA US HY Index Effective Yield by Rating Bucket",
                              xaxis_title="Date", yaxis_title="Index Effective Yield (bp)", margin=FIG_MARGIN)
        _apply_fig_defaults(fig_ybf, title="HY Yield by Rating", x_title="Date", y_title="Yield (bp)")
        st.plotly_chart(fig_ybf, use_container_width=True, key="yield_curves_by_rating")
        st.dataframe(yield_curve.tail())

    st.caption("All news fetched via NewsAPI.")
    st.caption("Finacial data is fetched via FredAPI from the Federal Reserve Bank of St.Louis (FRED).")

def render_treasury_curves() -> None:
    """Treasury curve multi-tab by period."""
    st.header("Treasury Curves")
    picks = st.multiselect(
        "Select maturities",
        options=list(gf.YIELD_SERIES_IDS),
        default=["2 Year", "10 Year"],
        key="curve_picks",
    )
    if not picks:
        st.info("Pick at least one maturity.")
        st.stop()

    ids = {p: gf.YIELD_SERIES_IDS[p] for p in picks}
    tabs = st.tabs(list(PERIODS.keys()))

    for tab, period in zip(tabs, PERIODS.values()):
        start, freq = period["start"], period["freq"]
        df = get_curve(start, ids, freq)
        with tab:
            st.subheader(f"Treasury Yields since {start}")
            if df.empty:
                st.warning("No data.")
                continue
            df.index = pd.to_datetime(df.index)
            fig_c = px.line(df, x=df.index, y=df.columns,
                            title=f"Treasury Yields ({freq}) since {start}",
                            labels={"value": "Yield (%)", "index": "Date"})
            _apply_fig_defaults(fig_c, title="", x_title="Date", y_title="Yield (%)")
            st.plotly_chart(fig_c, use_container_width=True, key=f"curve_{start}_{freq}")
            st.dataframe(df.tail())

def render_oas_section() -> None:
    """OAS charts + right-hand KPI grid."""
    st.header("Key OAS Metrics")

    
    oas_tab1, oas_tab_bucket = st.tabs(["HY and IG OAS vs 10-yr Treasury", "OAS by Rating Bucket"])

    with oas_tab1:
        fig = go.Figure()
        df_oas = of.fetch_index_oas_series("2024-01-01")
        treas10 = of.fetch_treasury_series("2024-01-01")

        fig.add_trace(go.Scatter(x=df_oas.index, y=df_oas["IG OAS"], name="IG OAS", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=df_oas.index, y=df_oas["HY OAS"], name="HY OAS", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=df_oas.index, y=df_oas["HY OAS"] - df_oas["IG OAS"],
                                    name="HY–IG Basis", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=treas10.index, y=treas10, name="10-Yr Treasury (bp)", yaxis="y2", line=dict(width=2)))

        fig.update_layout(
            title=dict(text="IG vs HY OAS & 10-Yr Treasury", x=0.15, y=1, xanchor="center", yanchor="top"),
            xaxis_title="Date",
            yaxis_title="OAS (bp) / Basis (bp)",
            legend=dict(x=-0.05, y=1.075, orientation="h"),
            margin=dict(t=50, b=40),
            yaxis2=dict(title="10-Yr Treasury (bp)", overlaying="y", side="right", showgrid=False),
            template=FIG_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True, key="oas_vs_treasury")

    with oas_tab_bucket:
        st.header("OAS by Rating Bucket")
        rb_df = of.fetch_oas_by_rating("2024-01-01")
        fig_rb = go.Figure()
        for col in rb_df.columns:
            fig_rb.add_trace(go.Scatter(x=rb_df.index, y=rb_df[col], name=col, line=dict(width=2)))
        fig_rb.update_layout(
            title="Corporate OAS by Rating Bucket (bp)",
            xaxis_title="Date",
            yaxis_title="OAS (bp)",
            margin=FIG_MARGIN,
            template=FIG_TEMPLATE,
        )
        st.plotly_chart(fig_rb, use_container_width=True, key="oas_by_bucket")

    add_vertical_space(2)

    col_table, col_stats = st.columns([1, 2], gap="large")
    with col_table:
        # Latest Rating-Bucket Table
        latest_rb = rb_df.tail(1).T.rename(columns={rb_df.index[-1]: "Latest"})
        latest_rb["Δ (bp)"] = latest_rb["Latest"] - rb_df.tail(2).iloc[0]
        st.table(latest_rb.style.format("{:.1f}"))

    with col_stats:
        # (kept calculations identical)
        df_oas = of.fetch_index_oas_series("2024-01-01")
        rb_df = of.fetch_oas_by_rating("2024-01-01")
        treas10 = of.fetch_treasury_series("2024-01-01")

        ig_now, ig_prev = df_oas["IG OAS"].iloc[-1], df_oas["IG OAS"].iloc[-2]
        hy_now, hy_prev = df_oas["HY OAS"].iloc[-1], df_oas["HY OAS"].iloc[-2]
        vol_3m = df_oas.pct_change().rolling(63).std().iloc[-1] * 100

        ig_disp      = rb_df["BBB OAS"].iloc[-1] - rb_df["AAA OAS"].iloc[-1]
        ig_disp_prev = rb_df["BBB OAS"].iloc[-2] - rb_df["AAA OAS"].iloc[-2]
        hy_disp      = rb_df["B OAS"].iloc[-1]   - rb_df["BB OAS"].iloc[-1]
        hy_disp_prev = rb_df["B OAS"].iloc[-2]   - rb_df["BB OAS"].iloc[-2]

        treas_now, treas_prev = treas10.iloc[-1], treas10.iloc[-2]
        ig_net, ig_net_prev = ig_now - treas_now, ig_prev - treas_prev
        hy_net, hy_net_prev = hy_now - treas_now, hy_prev - treas_prev

        ig_wk = ig_now - df_oas["IG OAS"].shift(5).iloc[-1]
        ig_mn = ig_now - df_oas["IG OAS"].shift(21).iloc[-1]
        hy_wk = hy_now - df_oas["HY OAS"].shift(5).iloc[-1]
        hy_mn = hy_now - df_oas["HY OAS"].shift(21).iloc[-1]

        # Row 1
        c1, c2, c3 = st.columns(3, gap="small")
        with c1: st.metric("IG OAS (bp)", f"{ig_now:.1f}", f"{(ig_now - ig_prev):+.1f}", delta_color="inverse")
        with c2: st.metric("HY OAS (bp)", f"{hy_now:.1f}", f"{(hy_now - hy_prev):+.1f}", delta_color="inverse")
        with c3: st.metric("OAS Vol 3m (σ bp)", f"{vol_3m['IG OAS']:.1f}")

        # Row 2
        c1, c2, c3 = st.columns(3, gap="small")
        with c1: st.metric("IG Dispersion (BBB–AAA)", f"{ig_disp:.1f} bp", f"{(ig_disp - ig_disp_prev):+.1f} bp", delta_color="inverse")
        with c2: st.metric("HY Dispersion (B–BB)", f"{hy_disp:.1f} bp", f"{(hy_disp - hy_disp_prev):+.1f} bp", delta_color="inverse")
        with c3: st.metric("IG OAS–10Y T-Sy", f"{ig_net:.1f} bp", f"{(ig_net - ig_net_prev):+.1f} bp", delta_color="inverse")

        # Row 3
        c1, c2, c3 = st.columns(3, gap="small")
        with c1: st.metric("HY OAS–10Y T-Sy", f"{hy_net:.1f} bp", f"{(hy_net - hy_net_prev):+.1f} bp", delta_color="inverse")
        with c2: st.metric("IG 1M Δ (bp)", f"{ig_mn:+.1f} bp")
        with c3: st.metric("HY 1M Δ (bp)", f"{hy_mn:+.1f} bp")
    

def render_vol_section() -> None:
    """MOVE index + metric."""
    st.header("Volatility (MOVE, CDS)")
    df_move = get_move(start_date="2003-01-01")

    st.subheader("CBOE MOVE Index")
    if df_move.empty:
        st.warning("No MOVE data.")
        return

    fig_m = px.line(df_move, x=df_move.index, y=df_move.columns,
                    title="ICE BofAML MOVE Index (^MOVE)",
                    labels={"value": "Move (%)", "index": "Date"})
    _apply_fig_defaults(fig_m, title="", x_title="Date", y_title="Index Value")
    st.plotly_chart(fig_m, use_container_width=True, key="CBOE_MOVE")
    st.metric("Latest MOVE", f"{df_move['MOVE'].iloc[-1]:.1f}")
# ╰─────────────────────────────────────────────────────────────────╯


def main() -> None:
    render_header()
    render_sidebar()

    headlines = get_headlines()
    core_rates = get_core_rates()

    col_news, col_rates = st.columns([1, 1], gap="large")
    with col_news:
        render_news_panel(headlines)
    with col_rates:
        render_core_rates_panel(core_rates)
        render_slope_and_yields()

    st.markdown("---")
    render_treasury_curves()
    st.markdown("---")
    render_oas_section()
    st.markdown("---")
    render_vol_section()


if __name__ == "__main__":
    main()
