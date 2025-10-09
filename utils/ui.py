# utils/ui.py
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st


# ╭─────────────────────────── Full width container CSS ───────────────────────────╮
st.markdown(
    """
    <style>
    .full-height {
        min-height: 100vh;

        display: flex;
        align-items: center;   /* vertical centering */
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
def configure_page(page_title: str, page_icon: str, layout: str) -> None:
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    if "theme" not in st.session_state:
       st.session_state.theme = "light"
    else:
         st._config.set_option("theme.base", st.session_state.theme)
    

def go(page_path: str):
    """Navigate to a different page in a multipage app."""
    try:
        st.switch_page(page_path)
    except Exception:
        st.warning(f"Page not found: {page_path}")

def is_signed_in() -> bool:
    """Check if user is signed in (mock)."""
    return bool(st.session_state.get("access_token"))

def switch_theme():
    """ Toggle between light and dark themes."""
    
    if st.session_state.theme == "light":
        st._config.set_option("theme.base", "dark")
        st._config.set_option("theme.backgroundColor", "#0E1117")
        st.session_state.theme = "dark"
    else:
        st._config.set_option("theme.base", "light")
        st._config.set_option("theme.backgroundColor", "#FFFFFF")
        st.session_state.theme = "light"
    

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
    st.sidebar.button("Switch Theme", on_click=switch_theme())


def hero_split(
    title: str,
    subtitle: str,
    img_path: str,
    *,
    kpis: Optional[Tuple[Tuple[str,str], ...]] = None,
    primary_label: str = "Get started",
    primary_page: str = "",
    secondary_label: Optional[str] = None,
    secondary_page: Optional[str] = None,
):
    """
    A simple two-column hero.
    - kpis: e.g., (("IG OAS","114 bp"),("2s10s","-28 bp"),("Sentiment","0.21"))
    - *_page: a `pages/...py` path for st.switch_page
    """
    with st.container():
        st.markdown('<div class="full-height">', unsafe_allow_html=True)
        
        c1, c2 = st.columns([2,1], vertical_alignment="center")
        with c1:
            st.title(title)
            st.caption(subtitle)

            if kpis:
                cols = st.columns(len(kpis))
                for (i,(label, value)) in enumerate(kpis):
                    cols[i].metric(label, value)

            # CTAs
            if primary_page:
                st.button(primary_label, type="primary", use_container_width=False,
                        on_click=lambda: go(primary_page))
            else:
                st.button(primary_label, type="primary", disabled=True)

            if secondary_label:
                st.button(secondary_label, use_container_width=False,
                        on_click=(lambda: go(secondary_page)) if secondary_page else None)

        with c2:
            st.image(img_path, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)




        