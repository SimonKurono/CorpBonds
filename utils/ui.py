# utils/ui.py ─────────────────────────────────────────────────────────
"""UI utility functions for Streamlit pages."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st


# ╭─────────────────────────── Constants ───────────────────────────╮
DEFAULT_KPI_COLUMNS = 3
DEFAULT_FEATURE_COLUMNS = 3
BUILT_BY = "Simon Kurono"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── UI Functions ───────────────────────────╮
def configure_page(page_title: str, page_icon: str, layout: str = "wide") -> None:
    """Configure Streamlit page (theme now comes from config.toml)."""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    st.title(f"{page_icon} {page_title}")


def go(page_path: str) -> None:
    """Navigate to a different page."""
    try:
        st.switch_page(page_path)
    except Exception:
        st.warning(f"Page not found: {page_path}")


def is_signed_in() -> bool:
    """Check if user is signed in based on session state."""
    return bool(st.session_state.get("access_token"))


def section(title: str, subtitle: Optional[str] = None, show_rule: bool = False) -> None:
    """Render a section header with optional subtitle and divider."""
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)
    if show_rule:
        st.divider()


def kpi_chip(label: str, value: str) -> None:
    """Render a single KPI metric."""
    st.metric(label, value)


def kpi_group(kpis: List[Dict[str, str]], columns: int = DEFAULT_KPI_COLUMNS) -> None:
    """Render a group of KPI metrics in a grid layout."""
    cols = st.columns(min(columns, len(kpis)))
    for i, kpi in enumerate(kpis):
        with cols[i % columns]:
            kpi_chip(kpi["label"], kpi["value"])


def feature_grid(features: List[Tuple[str, str, str]], columns: int = DEFAULT_FEATURE_COLUMNS) -> None:
    """Render a grid of feature cards with navigation buttons."""
    for row_start in range(0, len(features), columns):
        cols = st.columns(columns)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(features):
                break
            title, desc, target = features[idx]
            with col:
                box = st.container(border=True, height="stretch", vertical_alignment="distribute")
                with box:
                    st.markdown(f"### {title}")
                    st.caption(desc)
                    st.button(
                        "Open",
                        key=f"open_{idx}",
                        use_container_width=True,
                        on_click=lambda t=target: go(t)
                    )


def divider() -> None:
    """Render a horizontal divider."""
    st.divider()


def verticalSpace(height: int) -> None:
    """Add vertical space of specified height in pixels."""
    st.write(f"<div style='height:{height}px'></div>", unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render the sidebar with settings and metadata."""
    st.sidebar.header("Settings")
    st.sidebar.date_input("As of date", value=datetime.today(), key="as_of_date")
    st.sidebar.markdown("---")
    st.sidebar.write(f"Built by: {BUILT_BY}")
# ╰─────────────────────────────────────────────────────────────────╯
