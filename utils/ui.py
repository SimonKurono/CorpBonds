# utils/ui.py
from typing import List, Dict, Optional
import streamlit as st

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

def feature_grid(items: List[Dict[str, str]], columns: int = 3) -> None:
    """
    Render a responsive grid of features using native Streamlit columns.
    items: list of dicts like {"icon":"📊", "title":"Dashboard", "desc":"Curves & OAS"}
    """
    for row_start in range(0, len(items), columns):
        cols = st.columns(columns)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(items): 
                break
            
            it = items[idx]
            with col:
                with st.container(border=True, height="stretch"):
                    st.markdown(f"### {it.get('icon','')} {it['title']}")
                    st.caption(it["desc"])

def divider() -> None:
    """Insert a horizontal rule."""
    st.divider()

def verticalSpace(height: int) -> None:
    """Insert vertical space."""
    st.write(f"<div style='height:{height}px'></div>", unsafe_allow_html=True)

def set_page_config(title: str, layout: str) -> None:
    """Set Streamlit page configuration."""
    st.set_page_config(page_title=title, layout=layout)
    