# utils/auth/generate_hashes.py ─────────────────────────────────────────────────────────
"""Utility script to generate password hashes for authentication."""

from __future__ import annotations

# ── Third-party
import streamlit_authenticator as stauth


# ╭─────────────────────────── Constants ───────────────────────────╮
PLAIN_PASSWORDS = [
    "alice_password",
    "bob_password",
    # Add more passwords as needed
]
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Helper Functions ───────────────────────────╮
def generate_hashed_password(password: str) -> str:
    """Generate a hashed password using streamlit_authenticator."""
    return stauth.Hasher([password]).generate()[0]
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main entry point: generate and print hashed passwords."""
    for pwd in PLAIN_PASSWORDS:
        hashed = generate_hashed_password(pwd)
        print(f"{pwd} → {hashed}")


if __name__ == "__main__":
    main()
