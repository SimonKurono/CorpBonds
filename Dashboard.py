# app.py  ─────────────────────────────────────────────────────────
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots



import dashboard_helpers.news_fetcher as nf
import dashboard_helpers.rate_fetcher as rf
import dashboard_helpers.graph_fetcher as gf          # provides YIELD_SERIES_IDS, load_fred_data, fetch_yield_curve
import dashboard_helpers.oas_fetcher as of
import dashboard_helpers.yield_bucket_fetcher as ybf
import dashboard_helpers.cds_move_fetcher as cmf

# ──────────────────  Page config & minimal CSS  ──────────────────
st.set_page_config(page_title="Raffles Bond DB", layout="wide")
st.markdown(
    "<style>.block-container{margin-left:auto;margin-right:auto;}</style>",
    unsafe_allow_html=True,
)

# ──────────────────  Sidebar  ──────────────────
st.sidebar.header("Settings")
st.sidebar.date_input("As of date", value=datetime.today())
st.sidebar.markdown("---")
st.sidebar.write("Built by: Simon Kurono")

# ──────────────────  Cached helpers  ──────────────────
@st.cache_data(ttl=60 * 30)
def get_headlines():
    return nf.fetch_headlines()

@st.cache_data(ttl=60 * 60 * 6)
def get_core_rates():
    return rf.fetch_core_rates()

@st.cache_data(ttl=60*60*60)
def get_yields(start_date,freq="W-FRI"):
    return ybf.fetch_yield_by_rating(start_date)

@st.cache_data(ttl=60 * 60 * 6)
def get_weekly_curve(ids: dict | None = None):
    """Weekly history since 2005 (W-FRI). If ids is None, pull all."""
    if ids is None:
        ids = gf.YIELD_SERIES_IDS
    return gf.load_fred_data("2005-01-01", ids)  # default freq = W-FRI

@st.cache_data(ttl=60*60*60)
def get_move(start_date):
    return cmf.fetch_move_yahoo_series(start_date)

# ──────────────────  Cached treasury yield helpers  ──────────────────
# ─── 1) Define time tabs ────────────────────────────────
PERIODS = {
    "1W":   {"start": (date.today() - relativedelta(weeks=1)).isoformat(), "freq": "D"},
    "1M":   {"start": (date.today() - relativedelta(months=1)).isoformat(), "freq": "D"},
    "6M":  {"start": (date.today() - relativedelta(months=6)).isoformat(), "freq": "D"},
    "1Y":  {"start": (date.today() - relativedelta(years=1)).isoformat(),  "freq": "D"},
    "2Y":  {"start": (date.today() - relativedelta(years=2)).isoformat(),  "freq": "W"},
    "5Y":  {"start": (date.today() - relativedelta(years=5)).isoformat(),  "freq": "W"},
    "10Y": {"start": (date.today() - relativedelta(years=10)).isoformat(), "freq": "W-Fri"},
    "20Y": {"start": (date.today() - relativedelta(years=20)).isoformat(), "freq": "W-Fri"},
    "MAX": {"start": "1900-01-01",                                "freq": "W-Fri"},
    #"YTD": {"start": f"{date.today().year}-01-01",               "freq": "D"},
}

@st.cache_data(ttl=60 * 60 * 6)
def get_curve(start_date: str, ids: dict, freq: str):
    """Unified curve fetcher for any period/frequency."""
    return gf.load_fred_data(start_date, ids, freq=freq)



# ──────────────────  MAIN layout  ──────────────────
st.title("🏦 Raffles Advisors – US Corporate-Bond Dashboard")

headlines   = get_headlines()
core_rates  = get_core_rates()

col_news, col_rates = st.columns([1, 1], gap="large")

# ───────────────  NEWS panel  ───────────────
with col_news:
    st.header("Today’s Headlines")
    if not headlines:
        st.info("No news available.")
    else:
        feature, *others = headlines[:5]

        # featured story
        if feature.get("urlToImage"):
            st.image(feature["urlToImage"], use_container_width=True)
        f_pub = datetime.fromisoformat(feature["publishedAt"].replace("Z", "+00:00"))
        st.markdown(f"**{f_pub:%B %d %Y}** | *{feature['source']['name']}*")
        st.subheader(feature["title"])
        st.write(feature.get("description", ""))
        st.markdown(f"[Read more]({feature['url']})")
        st.markdown("---")

        # 2×2 grid for next 4
        for pair in (others[0:2], others[2:4]):
            
            for art, cell in zip(pair, st.columns(2, gap="small")):
                with cell:
                    if art.get("urlToImage"):
                        st.image(art["urlToImage"], width=160)
                    a_pub = datetime.fromisoformat(art["publishedAt"].replace("Z", "+00:00"))
                    st.markdown(
                        f"<small>{a_pub:%b %d} | {art['source']['name']}</small>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{art['title']}**")
                    st.markdown(f"[Read more]({feature['url']})")
            st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    

# ─────────────  CORE-RATE panel  ─────────────
with col_rates:
    st.header("Core Rates")

    #KPI Grid
    core_rates = get_core_rates()        # dict[label] → (val, Δ)
    
    items = list(core_rates.items())
    for row in range(0, len(items), 3):
        for (lbl, data), col in zip(items[row:row+3], st.columns(3, gap="small")):
            # ensure we always have (val, delta)
            if isinstance(data, (list, tuple)) and len(data) == 2:
                val, delta = data
            else:                   # fallback if fetcher gave just a scalar
                val, delta = float(data), 0.0

            # bp vs % formatting
            fmt_val   = f"{val/100:.2%}" if 'Year' in lbl or 'Funds' in lbl else f"{val:.0f} bp"
            fmt_delta = f"{delta:+.2f} %" if 'Year' in lbl or 'Funds' in lbl else f"{delta:+.2f} bp"

            col.metric(lbl, fmt_val, fmt_delta)

    two_rate = core_rates.get("2 Year", (None, None))[1]
    ten_rate = core_rates.get("10 Year", (None, None))[1]

    if two_rate is not None and ten_rate is not None:
        st.caption(f"10y – 2y slope = {ten_rate - two_rate:.2f} bp")


    # ─────────────  Slope Tab  ─────────────
    st.header("Slope")
    wk_curve_all = get_weekly_curve()          # all maturities
    slope_wk = (wk_curve_all["10 Year"] - wk_curve_all["2 Year"]).to_frame("10y–2y")
    yield_curve = get_yields("2000-01-01")

    slope_tab, yield_curve_by_rating = st.tabs(["Slope (10y-2y)", "HY Yield by Rating"])
    
    #2y-10y slope
    with slope_tab:
        fig_s = px.line(
            slope_wk, x=slope_wk.index, y="10y–2y",
            labels={"index": "Date", "10y–2y": "Slope (bp)"},
        )
        st.plotly_chart(fig_s, use_container_width=True,key="slope")
        st.dataframe(slope_wk.tail())
    
    #yield curves by rating bucket
    with yield_curve_by_rating:
        fig_ybf = go.Figure()
        for col in yield_curve.columns:
            fig_ybf.add_trace(go.Scatter(
                x=yield_curve.index,
                y=yield_curve[col],
                name=col,
                line=dict(width=2)
            ))

        fig_ybf.update_layout(
            title="ICE BofA US High Yield Index Effective Yield by Rating Bucket",
            xaxis_title="Date",
            yaxis_title="Index Effective Yield (bp)",
            legend=dict(x=0, y=1.05, orientation="h"),
            margin=dict(t=50, b=40, l=40, r=40)
        )

        st.plotly_chart(fig_ybf, use_container_width=True,key="yield_curves_by_rating")


    st.caption("All news fetched via NewsAPI.")
    st.caption("Finacial data is fetched via FredAPI from the Federal Reserve Bank of St.Louis (FRED).")

        



# ─────────────  CURVE section  ─────────────
st.header("Treasury Curves")
picks = st.multiselect("Select maturities",
                       options=list(gf.YIELD_SERIES_IDS),
                       default=["2 Year","10 Year"])
if not picks:
    st.info("Pick at least one maturity.")
    st.stop()
ids = {p: gf.YIELD_SERIES_IDS[p] for p in picks}

tabs = st.tabs(list(PERIODS.keys()))
for tab, period in zip(tabs, PERIODS.values()):
    start, freq = period["start"], period["freq"]
    df = get_curve(start, ids, freq)
    # … inside your tab loop …
    with tab:
        st.subheader(f"Treasury Yields since {start}")
        if df.empty:
            st.warning("No data.")
        else:
            df.index = pd.to_datetime(df.index)

            # Build a line chart figure from the wide DataFrame
            fig_c = px.line(
                df,
                x=df.index,
                y=df.columns,
                title=f"Treasury Yields ({freq}) since {start}",
                labels={"value": "Yield (%)", "index": "Date"},
            )

            # Show it
            st.plotly_chart(fig_c, use_container_width=True)

            # And your table
            st.dataframe(df.tail())
st.markdown("---")


#----------- OAS Section ----------------
st.header("Key OAS Metrics")

col_oas_graph, col_oas_stats = st.columns([2,1],gap="large")

with col_oas_graph:
    oas_tab1, oas_tab_bucket = st.tabs(["HY and IG OAS vs 10-yr Treasury", "OAS by Rating Bucket"])
    fig = go.Figure()
    with oas_tab1:
        df_oas = of.fetch_index_oas_series("2024-01-01")   # IG OAS, HY OAS in bp

        # 2) Treasury history
        treas10 = of.fetch_treasury_series("2024-01-01")    # Series indexed by date

        # IG & HY OAS on primary y
        fig.add_trace(go.Scatter(
            x=df_oas.index, y=df_oas["IG OAS"],
            name="IG OAS", line=dict(color="royalblue")
        ))
        fig.add_trace(go.Scatter(
            x=df_oas.index, y=df_oas["HY OAS"],
            name="HY OAS", line=dict(color="lightpink")
        ))

        # HY–IG Basis on primary y
        fig.add_trace(go.Scatter(
            x=df_oas.index, y=df_oas["HY OAS"] - df_oas["IG OAS"],
            name="HY–IG Basis", line=dict(color="lightgray")
        ))

        # 10-Yr Treasury on secondary y
        fig.add_trace(go.Scatter(
            x=treas10.index, y=treas10,
            name="10-Yr Treasury (bp)",
            line=dict(color="crimson"),
            yaxis="y2"
        ))

        # 4) Layout tweaks
        fig.update_layout(
            title=dict(
                text="IG vs HY OAS & 10-Yr Treasury",
                x=0.15,       # 0 = left, 0.5 = center, 1 = right
                y=1,      # tweak vertical position
                xanchor="center",
                yanchor="top"
            ),
            xaxis_title="Date",
            yaxis_title="OAS (bp) / Basis (bp)",
            legend=dict(x=-0.05, y=1.075, orientation="h"),
            margin=dict(t=50, b=40),
            yaxis2=dict(
                title="10-Yr Treasury (bp)",
                overlaying="y",
                side="right",
                showgrid=False
            )
        )
        st.plotly_chart(fig, use_container_width=True, key = "oas_vs_treasury")

    with oas_tab_bucket:
        st.header("OAS by Rating Bucket")

        rb_df = of.fetch_oas_by_rating("2024-01-01")  # returns columns AAA OAS, AA OAS, … B OAS

        fig_rb = go.Figure()
        for col in rb_df.columns:
            fig_rb.add_trace(go.Scatter(
                x=rb_df.index,
                y=rb_df[col],
                name=col,
                line=dict(width=2)
            ))

        fig_rb.update_layout(
            title="Corporate OAS by Rating Bucket (bp)",
            xaxis_title="Date",
            yaxis_title="OAS (bp)",
            legend=dict(x=0, y=1.05, orientation="h"),
            margin=dict(t=50, b=40, l=40, r=40)
        )

        st.plotly_chart(fig_rb, use_container_width=True,key="oas_by_bucket")

        
        


with col_oas_stats:
   # ───────────  Key OAS Stats as a 3×N grid  ───────────
    # Compute all the values first (assuming df_oas, rb_df, and treas10 exist)
    ig_now, ig_prev = df_oas["IG OAS"].iloc[-1], df_oas["IG OAS"].iloc[-2]
    hy_now, hy_prev = df_oas["HY OAS"].iloc[-1], df_oas["HY OAS"].iloc[-2]

    vol_3m = df_oas.pct_change().rolling(63).std().iloc[-1] * 100  # in bp

    ig_disp       = rb_df["BBB OAS"].iloc[-1] - rb_df["AAA OAS"].iloc[-1]
    ig_disp_prev  = rb_df["BBB OAS"].iloc[-2] - rb_df["AAA OAS"].iloc[-2]
    hy_disp       = rb_df["B OAS"].iloc[-1]   - rb_df["BB OAS"].iloc[-1]
    hy_disp_prev  = rb_df["B OAS"].iloc[-2]   - rb_df["BB OAS"].iloc[-2]

    treas_now, treas_prev = treas10.iloc[-1], treas10.iloc[-2]
    ig_net       = ig_now  - treas_now
    ig_net_prev  = ig_prev - treas_prev
    hy_net       = hy_now  - treas_now
    hy_net_prev  = hy_prev - treas_prev

    ig_wk = ig_now - df_oas["IG OAS"].shift(5).iloc[-1]
    ig_mn = ig_now - df_oas["IG OAS"].shift(21).iloc[-1]
    hy_wk = hy_now - df_oas["HY OAS"].shift(5).iloc[-1]
    hy_mn = hy_now - df_oas["HY OAS"].shift(21).iloc[-1]

    # ──────────────────────────────────────────────────────────
    # ROW 1: IG OAS | HY OAS | OAS Vol 3m
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.metric(
            label="IG OAS (bp)",
            value=f"{ig_now:.1f}",
            delta=f"{(ig_now - ig_prev):+.1f}",
            delta_color="inverse",
        )
    with col2:
        st.metric(
            label="HY OAS (bp)",
            value=f"{hy_now:.1f}",
            delta=f"{(hy_now - hy_prev):+.1f}",
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="OAS Vol 3m (σ bp)",
            value=f"{vol_3m['IG OAS']:.1f}",
            delta=None,
        )

    # ROW 2: IG Dispersion | HY Dispersion | IG OAS–10Y T-Sy
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.metric(
            label="IG Dispersion (BBB–AAA)",
            value=f"{ig_disp:.1f} bp",
            delta=f"{(ig_disp - ig_disp_prev):+.1f} bp",
            delta_color="inverse",
        )
    with col2:
        st.metric(
            label="HY Dispersion (B–BB)",
            value=f"{hy_disp:.1f} bp",
            delta=f"{(hy_disp - hy_disp_prev):+.1f} bp",
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="IG OAS–10Y T-Sy",
            value=f"{ig_net:.1f} bp",
            delta=f"{(ig_net - ig_net_prev):+.1f} bp",
            delta_color="inverse",
        )

    # ROW 3: HY OAS–10Y T-Sy | IG 1W Δ | IG 1M Δ
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.metric(
            label="HY OAS–10Y T-Sy",
            value=f"{hy_net:.1f} bp",
            delta=f"{(hy_net - hy_net_prev):+.1f} bp",
            delta_color="inverse",
        )
    with col2:
        st.metric(
            label="IG 1W Δ (bp)",
            value=f"{ig_wk:+.1f} bp",
            delta=None,
        )
    with col3:
        st.metric(
            label="IG 1M Δ (bp)",
            value=f"{ig_mn:+.1f} bp",
            delta=None,
        )

    # ROW 4: HY 1W Δ | HY 1M Δ | (blank)
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.metric(
            label="HY 1W Δ (bp)",
            value=f"{hy_wk:+.1f} bp",
            delta=None,
        )
    with col2:
        st.metric(
            label="HY 1M Δ (bp)",
            value=f"{hy_mn:+.1f} bp",
            delta=None,
        )
    # leave col3 empty to balance the grid


# ───────────  Latest Rating-Bucket Table ───────────
latest_rb = rb_df.tail(1).T.rename(columns={rb_df.index[-1]: "Latest"})
latest_rb["Δ (bp)"] = latest_rb["Latest"] - rb_df.tail(2).iloc[0]
st.table(latest_rb.style.format("{:.1f}"))


# ───────────  Volatility (MOVE, CDS) ───────────
st.header("Volatility (MOVE, CDS)")

df_move = cmf.fetch_move_yahoo_series(start_date="2003-01-01")

st.subheader("CBOE MOVE Index")
if not df_move.empty:
    fig_m = go.Figure()
    fig_m = px.line(
        df_move,
        x = df_move.index,
        y = df_move.columns,
        title = "ICE BofAML MOVE Index (^MOVE)",
        labels={"value": "Move (%)","index": "Date"},
        
    )

    st.plotly_chart(fig_m,use_container_width=True, key="CBOE MOVE")
    st.metric("Latest MOVE", f"{df_move['MOVE'].iloc[-1]:.1f}", delta=None)
else:
    st.warning("No MOVE data.")


