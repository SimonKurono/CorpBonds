# utils/ui.py
from __future__ import annotations
from typing import List, Optional, Dict
import streamlit as st

# --- 1) Base CSS injector (call once per page) ---
def inject_base_css() -> None:
    """
    Injects global CSS for consistent styling (cards, sections, KPI chips, grid).
    Safe to call multiple times; only injects once per page render.
    """
    if st.session_state.get("_ui_base_css_injected"):
        return
    st.session_state["_ui_base_css_injected"] = True

    st.markdown("""
    <style>
      /* Container width + typography polish */
      .block-container {max-width: 1150px; padding-top: 1.5rem; padding-bottom: 3rem;}
      h1,h2,h3 {letter-spacing: .2px;}

      /* Section + divider */
      .ui-section {margin-top: 2rem; margin-bottom: .5rem;}
      .ui-hr {height:1px; background: linear-gradient(to right, rgba(255,255,255,0.12), rgba(255,255,255,0.02)); margin:.5rem 0 1rem 0;}

      /* KPI chips */
      .ui-kpis {display:flex; gap:.6rem; flex-wrap: wrap; margin:.25rem 0 .25rem 0;}
      .ui-kpi {
        padding:.38rem .6rem; border-radius:.7rem;
        border:1px solid rgba(255,255,255,.08);
        background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
        font-size:.92rem; white-space: nowrap;
      }
      .ui-kpi .l {opacity:.82; margin-right:.35rem;}
      .ui-kpi .v {font-weight:600;}

      /* Feature grid + cards */
      .ui-grid {display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1rem;}
      @media (max-width:1100px){ .ui-grid{grid-template-columns: repeat(2, minmax(0,1fr));} }
      @media (max-width:700px){ .ui-grid{grid-template-columns: 1fr;} }

      .ui-card {
        padding: 1rem; border-radius: 1rem;
        background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));
        border: 1px solid rgba(255,255,255,.06);
        transition: transform .12s ease, background .15s ease, border-color .15s ease;
      }
      .ui-card:hover { transform: translateY(-2px); border-color: rgba(110,231,183,.35); }
      .ui-card .t {font-weight: 600; margin-bottom: .15rem;}
      .ui-card .d {opacity:.86; font-size:.95rem;}
      .ui-card a {text-decoration: none;}
    </style>
    """, unsafe_allow_html=True)

# --- 2) Section helper ---
def section(title: str, subtitle: Optional[str] = None, *, show_rule: bool = False) -> None:
    """Render a standard section heading with optional subtitle and horizontal rule."""
    st.markdown('<div class="ui-section"></div>', unsafe_allow_html=True)
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)
    if show_rule:
        st.markdown('<div class="ui-hr"></div>', unsafe_allow_html=True)

# --- 3) KPI chips ---
def kpi_chip(label: str, value: str) -> str:
    """
    Returns HTML for a single KPI chip (use inside kpi_group).
    Usage: ui.kpi_group([ui.kpi_chip("IG OAS","114 bp"), ...])
    """
    return f'<div class="ui-kpi"><span class="l">{label}:</span><span class="v">{value}</span></div>'

def kpi_group(kpis: List[str]) -> None:
    """Render a row of KPI chips produced by kpi_chip()."""
    st.markdown('<div class="ui-kpis">' + "".join(kpis) + '</div>', unsafe_allow_html=True)

# --- 4) Feature cards (static) ---
def feature_card(title: str, desc: str, icon: str = "", href: Optional[str] = None) -> str:
    """
    Returns HTML for a feature card. Use inside feature_grid().
    - icon: emoji or small text icon, optional
    - href: if provided, card title becomes a link (Streamlit link_button is separate)
    """
    tt = f"{icon} {title}".strip()
    title_html = f'<a href="{href}" target="_blank" rel="noopener" class="t">{tt}</a>' if href else f'<div class="t">{tt}</div>'
    return f'''
      <div class="ui-card">
        {title_html}
        <div class="d">{desc}</div>
      </div>
    '''

def feature_grid(items: List[Dict[str, Optional[str]]], columns: int = 3) -> None:
    """
    Render a responsive grid of feature cards.
    items: list of dicts with keys: icon, title, desc, href
    """
    # We don't need 'columns' arg for CSS grid, but kept for API symmetry if you switch layouts later.
    html = '<div class="ui-grid">' + "".join(
        feature_card(i.get("title",""), i.get("desc",""), icon=i.get("icon",""), href=i.get("href"))
        for i in items
    ) + '</div>'
    st.markdown(html, unsafe_allow_html=True)
