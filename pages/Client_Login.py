import streamlit as st
import yaml
import streamlit_authenticator as stauth

import utils.ui as ui

with open("credentials.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

ui.render_sidebar()



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
    st.sidebar.success(f"Welcome back, {name}!")
elif auth_status is False:
    st.error("❌ Username/password is incorrect.")
else:
    st.warning("⚠️ Please enter your credentials.")
