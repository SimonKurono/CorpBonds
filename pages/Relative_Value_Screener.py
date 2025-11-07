# pages/Relative_Value_Screener.py ─────────────────────────────────────────────────────────
"""Relative Value Screener Page.

Features:
- Treasury stats
- Fixed income downloadable metrics
"""

from __future__ import annotations

# ── Third-party
import streamlit as st

# ── Local
import utils.ui as ui


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Relative Value Screener", page_icon="🔍", layout="wide")
    ui.render_sidebar()


def render_placeholder() -> None:
    """Render placeholder content for future implementation."""
    st.header("Coming Soon")
    st.write("TODO: add treasury stats and fixed income downloadable metrics")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()
    render_placeholder()


if __name__ == "__main__":
    main()
