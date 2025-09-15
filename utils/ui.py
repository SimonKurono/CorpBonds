# utils/ui.py
from typing import List, Dict, Optional
from datetime import datetime
import streamlit as st

def go(page_path: str):
    try:
        st.switch_page(page_path)
    except Exception:
        st.warning(f"Page not found: {page_path}")

def is_signed_in() -> bool:
    return bool(st.session_state.get("access_token"))

def section(title: str, subtitle: Optional[str] = None, show_rule: bool = False) -> None:
    """Standard section heading."""
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)
    if show_rule:
        st.divider()

def kpi_chip(label: str, value: str) -> None:
    """Single KPI metric (native st.metric)."""
    st.metric(label, value)

def kpi_group(kpis: List[Dict[str, str]], columns: int = 3) -> None:
    """
    Render KPIs in columns.
    kpis: list of dicts like {"label": "IG OAS", "value": "114 bp"}
    """
    cols = st.columns(len(kpis) if len(kpis) < columns else columns)
    for i, kpi in enumerate(kpis):
        with cols[i % columns]:
            kpi_chip(kpi["label"], kpi["value"])

def feature_grid(features: List[Dict[str, str]], columns: int = 3) -> None:
    """
    Render a responsive grid of features using native Streamlit columns.
    items: list of dicts like {"icon":"📊", "title":"Dashboard", "desc":"Curves & OAS"}
    """
    for row_start in range(0, len(features), columns):
        cols = st.columns(columns)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(features): 
                break
            
            it = features[idx]
            title, desc, target = features[idx]
            with col:
                box = st.container(border=True, height="stretch", vertical_alignment="distribute")
                with box:
                    st.markdown(f"### {title}")
                    st.caption(desc)
                    # A simple open button per card
                    st.button("Open", key=f"open_{idx}", use_container_width=True,
                            on_click=lambda t=target: go(t))


        

def divider() -> None:
    """Insert a horizontal rule."""
    st.divider()

def verticalSpace(height: int) -> None:
    """Insert vertical space."""
    st.write(f"<div style='height:{height}px'></div>", unsafe_allow_html=True)

def render_sidebar() -> None:
    st.sidebar.header("Settings")
    st.sidebar.date_input("As of date", value=datetime.today(), key="as_of_date")
    st.sidebar.markdown("---")
    st.sidebar.write("Built by: Simon Kurono")
    