# pages/Client_Login.py ─────────────────────────────────────────────────────────
"""Client Login and Authentication Page."""

from __future__ import annotations

# ── Stdlib
from typing import Any, Mapping

# ── Third-party
import streamlit as st
import streamlit_authenticator as stauth
import yaml

# ── Local
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
CREDENTIALS_FILE = "credentials.yaml"
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Helpers and caching ──────────────────────╮
def _load_config() -> Mapping[str, Any]:
    """Load authentication configuration from YAML file."""
    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Raffles Bond Platform - Login", page_icon="🔐", layout="centered")


def render_sidebar() -> None:
    """Render the sidebar navigation."""
    ui.render_sidebar()


def render_login_panel() -> None:
    """Render authentication login form and handle user authentication."""
    config = _load_config()
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=True,
    )

    # Render the login form
    authenticator.login(location="main", key="Client Sign In")

    # Read authentication status from session state
    name = st.session_state.get("name")
    auth_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

    # Handle authentication states
    if auth_status:
        authenticator.logout("Log out", "sidebar")
        st.toast(f"Welcome back, {name}!")
    elif auth_status is False:
        st.error("❌ Username/password is incorrect.")
    else:
        st.warning("⚠️ Please enter your credentials.")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()
    render_sidebar()
    render_login_panel()


if __name__ == "__main__":
    main()

