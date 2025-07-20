import yaml
import streamlit as st
import streamlit_authenticator as stauth

# 1) Load your YAML
with open("credentials.yaml") as f:
    config = yaml.safe_load(f)

# 2) Build the authenticator with auto_hash turned on
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    auto_hash=True,      # <— this will SHA-256 your plain passwords on the fly
)

# 3) Show the login form
name, auth_status, username = authenticator.login("Login", "main")
if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Welcome, *{name}*")
    # …rest of your app…
elif auth_status is False:
    st.error("Incorrect username or password")
else:
    st.warning("Please enter your credentials")
