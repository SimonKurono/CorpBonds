# generate_hashes.py
import streamlit_authenticator

# 1) List your plaintext passwords
plain_pwds = [
    "alice_password",
    "bob_password",
    # …etc
]

# 2) Hash & print
for pwd in plain_pwds:
    print(f"{pwd} → {generate_hashed_password(pwd)}")
