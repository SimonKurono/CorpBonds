# utils/fetchers/finra_fetcher.py ─────────────────────────────────────────────────────────
"""Lightweight FINRA Query API client with caching and mock support."""

from __future__ import annotations

# ── Stdlib
import base64
import os
from typing import Any, Dict, Optional

# ── Third-party
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

# ── Initialize environment ──
load_dotenv()

# Base URLs
FINRA_BASE_URL = os.getenv("FINRA_BASE_URL", "https://api.finra.org")
FINRA_QA_BASE_URL = os.getenv("FINRA_QA_BASE_URL", "https://api-int.qa.finra.org")
FINRA_TOKEN_URL = os.getenv(
    "FINRA_TOKEN_URL",
    "https://ews.fip.finra.org/fip/rest/ews/oauth2/access_token?grant_type=client_credentials",
)
FINRA_QA_TOKEN_URL = os.getenv(
    "FINRA_QA_TOKEN_URL",
    "https://ews-qaint.fip.qa.finra.org/fip/rest/ews/oauth2/access_token?grant_type=client_credentials",
)

# Credentials
FINRA_CLIENT_ID = os.getenv("FINRA_CLIENT_ID")
FINRA_CLIENT_SECRET = os.getenv("FINRA_CLIENT_SECRET")

# Defaults
DEFAULT_TIMEOUT = 30
TOKEN_TTL = 25 * 60        # 25 minutes
DATA_TTL = 5 * 60          # 5 minutes


# ╭──────────────────────── Helpers ───────────────────────────╮
def _get_secret(key: str) -> Optional[str]:
    """Safe accessor for st.secrets."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def get_credentials() -> Optional[tuple[str, str]]:
    """Return FINRA client credentials from env or Streamlit secrets."""
    client_id = FINRA_CLIENT_ID or _get_secret("FINRA_CLIENT_ID")
    client_secret = FINRA_CLIENT_SECRET or _get_secret("FINRA_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    return client_id, client_secret


def resolve_env(env: str) -> tuple[str, str]:
    """Return (base_url, token_url) for environment."""
    env = (env or "prod").lower()
    if env == "qa":
        return FINRA_QA_BASE_URL, FINRA_QA_TOKEN_URL
    return FINRA_BASE_URL, FINRA_TOKEN_URL


@st.cache_data(ttl=TOKEN_TTL, show_spinner=False)
def fetch_access_token(client_id: str, client_secret: str, token_url: str) -> Optional[str]:
    """Fetch OAuth2 token from FINRA Identity Platform."""
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {"Authorization": f"Basic {basic}"}
    try:
        resp = requests.post(token_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("access_token")
    except Exception as exc:
        st.error(f"FINRA auth failed: {exc}")
        return None


def _auth_header(env: str) -> dict[str, str]:
    """Build Authorization header if credentials are available."""
    creds = get_credentials()
    if not creds:
        return {}
    client_id, client_secret = creds
    _, token_url = resolve_env(env)
    token = fetch_access_token(client_id, client_secret, token_url)
    return {"Authorization": f"Bearer {token}"} if token else {}


@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def fetch_dataset(
    group: str,
    dataset: str,
    *,
    env: str = "prod",
    mock: bool = False,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    method: str = "POST",
    accept: str = "application/json",
) -> Optional[Any]:
    """
    Query a FINRA dataset and return parsed content (JSON or text).

    Args:
        group: FINRA group (e.g., fixedIncomeMarket)
        dataset: Dataset name (without Mock suffix)
        env: 'prod' | 'qa'
        mock: Append 'Mock' to dataset name when True
        payload: POST body (dict) for advanced filters
        params: Query params for GET/POST
        method: 'GET' or 'POST'
        accept: Accept header, defaults to JSON

    Returns:
        Parsed JSON (list/dict) or raw text. None on error.
    """
    base_url, _ = resolve_env(env)
    name = f"{dataset}Mock" if mock and not dataset.lower().endswith("mock") else dataset
    url = f"{base_url}/data/group/{group}/name/{name}"

    headers = {"Accept": accept}
    headers.update(_auth_header(env))

    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        else:
            resp = requests.post(url, headers=headers, params=params, json=payload or {}, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json() if accept == "application/json" else resp.text
    except Exception as exc:
        st.error(f"FINRA request failed: {exc}")
        return None


def to_frame(records: Any) -> Optional[pd.DataFrame]:
    """Convert response records to DataFrame if possible."""
    if records is None:
        return None
    try:
        return pd.DataFrame(records)
    except Exception:
        return None
