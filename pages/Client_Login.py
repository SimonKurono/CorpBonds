import streamlit as st
import yaml
import streamlit_authenticator as stauth

import utils.ui as ui

with open("credentials.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def configure_page():
    ui.configure_page(page_title="Raffles Bond Platform - Login", page_icon="🔐", layout="centered")

def render_sidebar():
    ui.render_sidebar()


# ---------- Page Config ----------



def load_authenticator():
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=True,
    )

    # 1) Render the login form (no unpacking)
    authenticator.login(location="main", key="Client Sign In")

    # 2) Read back from session_state
    name            = st.session_state.get("name")
    auth_status     = st.session_state.get("authentication_status")
    username        = st.session_state.get("username")

    # 3) Handle authentication
    if auth_status:
        authenticator.logout("Log out", "sidebar")
        st.toast(f"Welcome back, {name}!")
    elif auth_status is False:
        st.error("❌ Username/password is incorrect.")
    else:
        st.warning("⚠️ Please enter your credentials.")



def main() -> None:
    configure_page()
    render_sidebar()
    load_authenticator()

if __name__ == "__main__":
    main()
    
