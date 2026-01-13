# pages/Dashboard.py ─────────────────────────────────────────────────────────
"""Unified dashboard with flexible layout and sample widgets."""

from __future__ import annotations

# ── Std lib
from datetime import datetime
from typing import Any, Callable, Dict, List, Mapping, Tuple

# ── Third-party
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Local
from utils.dashboard_layout import normalize_width as _normalize_width, pack_rows as _pack_rows
import utils.fetchers.news_fetcher as nf
import utils.fetchers.rate_fetcher as rf
import utils.fetchers.oas_fetcher as of
import utils.fetchers.cds_move_fetcher as cmf
import utils.fetchers.yield_bucket_fetcher as ybf
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
HEADLINE_COUNT = 3
DEFAULT_WIDGETS = (
    "Headlines",
    "Core Rates",
    "OAS (IG vs HY)",
    "Yield by Rating",
    "MOVE Index",
    "CDX IG Proxy",
)
MAX_COLUMNS = 3
MIN_COLUMNS = 1
DEFAULT_COLUMNS = 2
LAYOUT_STATE_KEY = "dashboard_widgets"

TTL_HEADLINES = 60 * 30
TTL_RATES = 60 * 60
TTL_OAS = 60 * 60
TTL_MOVE = 60 * 60
TTL_YIELD_BY_RATING = 60 * 60 * 6
TTL_CDS_PROXY = 60 * 60

YIELD_RATING_POINTS = 52
CDS_TAIL_POINTS = 180
CDS_START_DATE = "2022-01-01"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Helpers and caching ──────────────────────╮
@st.cache_data(ttl=TTL_HEADLINES, show_spinner=False)
def load_headlines() -> List[Dict[str, Any]]:
    """Cached wrapper for NewsAPI headlines. """
    try:
        return nf.fetch_headlines(HEADLINE_COUNT)
    except Exception as exc:
        st.error(f"Headlines failed: {exc}")
        return []


@st.cache_data(ttl=TTL_RATES, show_spinner=False)
def load_core_rates() -> Mapping[str, tuple[float, float]]:
    """Cached wrapper for core rates from FRED."""
    try:
        return rf.fetch_core_rates()
    except Exception as exc:
        st.error(f"Core rates failed: {exc}")
        return {}


@st.cache_data(ttl=TTL_OAS, show_spinner=False)
def load_oas_series() -> pd.DataFrame:
    """Cached wrapper for IG/HY OAS."""
    try:
        return of.fetch_index_oas_series("2023-01-01")
    except Exception as exc:
        st.error(f"OAS fetch failed: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=TTL_MOVE, show_spinner=False)
def load_move_series() -> pd.DataFrame:
    """Cached wrapper for MOVE index from Yahoo Finance."""
    try:
        return cmf.fetch_move_yahoo_series("2020-01-01")
    except Exception as exc:
        st.error(f"MOVE fetch failed: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=TTL_YIELD_BY_RATING, show_spinner=False)
def load_yield_by_rating() -> pd.DataFrame:
    """Cached wrapper for yield by rating from FRED."""
    try:
        return ybf.fetch_yield_by_rating()
    except Exception as exc:
        st.error(f"Yield by rating failed: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=TTL_CDS_PROXY, show_spinner=False)
def load_cds_proxy_series() -> pd.DataFrame:
    """Cached wrapper for CDX IG proxy from Yahoo Finance."""
    try:
        return cmf.fetch_cds_proxy_series(CDS_START_DATE)
    except Exception as exc:
        st.error(f"CDX proxy failed: {exc}")
        return pd.DataFrame()
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Widget renderers ──────────────────────╮
def render_widget_headlines(data: List[Dict[str, Any]]) -> None:
    st.markdown("#### Top Headlines")
    if not data:
        st.info("No headlines available.")
        return
    for art in data[:HEADLINE_COUNT]:
        src = (art.get("source") or {}).get("name", "")
        published = art.get("publishedAt") or ""
        caption_bits = " • ".join(filter(None, [src, published[:10]]))
        st.caption(caption_bits)
        st.markdown(f"**{art.get('title', '')}**")
        if art.get("description"):
            st.write(art["description"])
        if art.get("url"):
            st.markdown(f"[Open article]({art['url']})")
        st.divider()


def render_widget_core_rates(data: Mapping[str, tuple[float, float]]) -> None:
    st.markdown("#### Core Rates (latest)")
    if not data:
        st.info("No rate data.")
        return
    items = list(data.items())
    step = min(3, len(items))
    for row in range(0, len(items), step):
        cols = st.columns(step, gap="small")
        for (label, (val, delta)), col in zip(items[row:row + step], cols):
            fmt_val = f"{val/100:.2%}" if "Year" in label or "Funds" in label else f"{val:.0f} bp"
            fmt_delta = f"{delta:+.2f} bp"
            col.metric(label, fmt_val, fmt_delta)


def render_widget_oas(data: pd.DataFrame) -> None:
    st.markdown("#### OAS: IG vs HY")
    if data is None or data.empty:
        st.info("No OAS data.")
        return
    fig = px.line(
        data,
        x=data.index,
        y=list(data.columns),
        labels={"value": "OAS (bp)", "index": "Date"},
        title="IG vs HY OAS",
    )
    fig.update_layout(margin=dict(t=40, b=30, l=40, r=10), template="plotly_white", legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)
    latest = data.tail(1).iloc[0]
    st.caption(f"As of {data.index[-1].date()}: IG {latest['IG OAS']:.1f} bp • HY {latest['HY OAS']:.1f} bp")


def render_widget_move(data: pd.DataFrame) -> None:
    st.markdown("#### MOVE Index")
    if data is None or data.empty:
        st.info("No MOVE data.")
        return
    latest = data["MOVE"].iloc[-1]
    prev = data["MOVE"].iloc[-2] if len(data) >= 2 else latest
    st.metric("Latest MOVE", f"{latest:.1f}", f"{(latest - prev):+.1f}")
    fig = px.area(
        data.tail(180),
        x=data.tail(180).index,
        y="MOVE",
        labels={"index": "Date", "MOVE": "Index"},
        title="MOVE (last 6 months)",
    )
    fig.update_layout(margin=dict(t=40, b=30, l=40, r=10), template="plotly_white", yaxis_title="Index")
    st.plotly_chart(fig, use_container_width=True)


def render_widget_yield_by_rating(data: pd.DataFrame) -> None:
    st.markdown("#### Yield by Rating")
    if data is None or data.empty:
        st.info("No yield data.")
        return
    recent = data.tail(YIELD_RATING_POINTS)
    fig = px.line(
        recent,
        x=recent.index,
        y=list(recent.columns),
        labels={"value": "Yield (bp)", "index": "Date"},
        title="Yield by Rating (weekly)",
    )
    fig.update_layout(
        margin=dict(t=40, b=30, l=40, r=10),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
    latest = data.iloc[-1]
    key_labels = [label for label in ("AAA", "BBB", "BB", "B", "CCC & Below") if label in data.columns]
    if key_labels:
        latest_str = " • ".join(f"{label} {latest[label]:.0f} bp" for label in key_labels)
        st.caption(f"Latest: {latest_str}")


def render_widget_cds_proxy(data: pd.DataFrame) -> None:
    st.markdown("#### CDX IG Proxy (LQD)")
    if data is None or data.empty or "CDX IG Proxy" not in data.columns:
        st.info("No CDX proxy data.")
        return
    series = data["CDX IG Proxy"].dropna()
    if series.empty:
        st.info("No CDX proxy data.")
        return
    latest = series.iloc[-1]
    prev = series.iloc[-2] if len(series) >= 2 else latest
    st.metric("LQD Close", f"{latest:.2f}", f"{(latest - prev):+.2f}")
    recent = series.tail(CDS_TAIL_POINTS)
    fig = px.area(
        recent.to_frame(),
        x=recent.index,
        y="CDX IG Proxy",
        labels={"index": "Date", "CDX IG Proxy": "Price"},
        title="CDX IG Proxy (LQD ETF)",
    )
    fig.update_layout(margin=dict(t=40, b=30, l=40, r=10), template="plotly_white", yaxis_title="Price")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Uses LQD as a proxy for CDX NA IG levels.")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────────── Registry ────────────────────────────╮
WidgetLoader = Callable[[], Any]
WidgetRenderer = Callable[[Any], None]

WIDGETS: Dict[str, Dict[str, Any]] = {
    "Headlines": {
        "loader": load_headlines,
        "renderer": render_widget_headlines,
        "default_width": 1,
        "description": "Top 3 financial headlines.",
    },
    "Core Rates": {
        "loader": load_core_rates,
        "renderer": render_widget_core_rates,
        "default_width": 1,
        "description": "Latest core rates and deltas.",
    },
    "OAS (IG vs HY)": {
        "loader": load_oas_series,
        "renderer": render_widget_oas,
        "default_width": 2,
        "description": "Historical IG/HY OAS chart.",
    },
    "MOVE Index": {
        "loader": load_move_series,
        "renderer": render_widget_move,
        "default_width": 1,
        "description": "MOVE metric and recent trend.",
    },
    "Yield by Rating": {
        "loader": load_yield_by_rating,
        "renderer": render_widget_yield_by_rating,
        "default_width": 2,
        "description": "Weekly yield curves by rating bucket.",
    },
    "CDX IG Proxy": {
        "loader": load_cds_proxy_series,
        "renderer": render_widget_cds_proxy,
        "default_width": 1,
        "description": "LQD proxy for CDX IG levels.",
    },
}
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────────── Layout helpers ──────────────────────╮
def _init_layout() -> None:
    """Initialize dashboard layout in session state if missing."""
    if LAYOUT_STATE_KEY not in st.session_state:
        st.session_state[LAYOUT_STATE_KEY] = [
            {"name": name, "width": WIDGETS[name]["default_width"]} for name in DEFAULT_WIDGETS
        ]


def _reset_layout() -> None:
    st.session_state[LAYOUT_STATE_KEY] = [
        {"name": name, "width": WIDGETS[name]["default_width"]} for name in DEFAULT_WIDGETS
    ]


def _clear_layout() -> None:
    st.session_state[LAYOUT_STATE_KEY] = []


def _append_widget(name: str, width: int, max_columns: int) -> None:
    norm_width = _normalize_width(width, max_columns)
    st.session_state[LAYOUT_STATE_KEY].append({"name": name, "width": norm_width})


def _remove_widget(index: int) -> None:
    if 0 <= index < len(st.session_state.get(LAYOUT_STATE_KEY, [])):
        st.session_state[LAYOUT_STATE_KEY].pop(index)
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Render sections ──────────────────────╮
def _render_sidebar_controls() -> int:
    """Render controls to add/remove widgets and return column count."""
    st.sidebar.header("Dashboard Controls")
    st.sidebar.caption("Pick widgets, set width, then add them to the layout.")

    columns = st.sidebar.slider("Columns per row", MIN_COLUMNS, MAX_COLUMNS, value=DEFAULT_COLUMNS, step=1)

    choices = list(WIDGETS.keys())
    selected_widget = st.sidebar.selectbox("Widget to add", options=choices, index=0)
    width_choice = st.sidebar.select_slider(
        "Widget width (units)",
        options=list(range(1, columns + 1)),
        value=_normalize_width(WIDGETS[selected_widget]["default_width"], columns),
        help="Width units relative to the columns per row.",
    )

    add_col, reset_col = st.sidebar.columns(2)
    with add_col:
        if st.button("Add widget", use_container_width=True):
            _append_widget(selected_widget, width_choice, columns)
            st.rerun()
    with reset_col:
        if st.button("Reset defaults", use_container_width=True):
            _reset_layout()
            st.rerun()

    if st.sidebar.button("Clear dashboard", use_container_width=True):
        _clear_layout()
        st.rerun()

    return columns


def _load_selected_data(selected: List[str]) -> Dict[str, Any]:
    """Load data only for selected widget names (deduped)."""
    data: Dict[str, Any] = {}
    for name in sorted(set(selected)):
        loader: WidgetLoader | None = WIDGETS.get(name, {}).get("loader")  # type: ignore[assignment]
        if loader:
            data[name] = loader()
    return data


def _render_grid(layout: List[Dict[str, Any]], columns: int, data: Dict[str, Any]) -> None:
    """Render widgets in a responsive grid with simple spanning."""
    if not layout:
        st.info("Use the sidebar to add widgets to this dashboard.")
        return

    rows = _pack_rows(layout, columns)
    for row in rows:
        spans = [entry["width"] for _, entry in row]
        cols = st.columns(spans, gap="large")
        for (idx, entry), col in zip(row, cols):
            name = entry.get("name", "")
            renderer: WidgetRenderer | None = WIDGETS.get(name, {}).get("renderer")  # type: ignore[assignment]
            with col:
                block = st.container(border=True)
                with block:
                    st.caption(WIDGETS.get(name, {}).get("description", ""))
                    if st.button("Remove", key=f"rm_{idx}_{name}", use_container_width=True):
                        _remove_widget(idx)
                        st.rerun()
                    if renderer:
                        renderer(data.get(name))
                    else:
                        st.warning("Missing renderer.")


def render_header() -> None:
    """Configure page header and sidebar."""
    ui.configure_page(page_title="Dashboard", page_icon="🧭", layout="wide")
    ui.render_sidebar()
    st.caption("Drag-free but flexible grid: choose columns, widths, and which widgets to show.")


def render_last_refreshed() -> None:
    """Show a lightweight last-refreshed footer."""
    st.write("---")
    st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    render_header()

    _init_layout()
    columns = _render_sidebar_controls()

    layout = st.session_state.get(LAYOUT_STATE_KEY, [])
    names = [item.get("name", "") for item in layout]
    data = _load_selected_data(names)

    _render_grid(layout, columns, data)
    render_last_refreshed()


if __name__ == "__main__":
    main()
