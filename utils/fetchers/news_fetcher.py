# utils/fetchers/news_fetcher.py ─────────────────────────────────────────────────────────
"""Fetchers for news articles from NewsAPI."""

from __future__ import annotations

# ── Stdlib
import os
from typing import Any, Dict, Iterable, List, Optional, Union

# ── Third-party
import requests
import streamlit as st
from dotenv import load_dotenv
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

# ── Initialize environment ──
load_dotenv()
API_KEY = os.getenv("NEWSAPI_KEY")
if not API_KEY:
    raise RuntimeError("Missing NEWSAPI_KEY in .env")

newsapi = NewsApiClient(API_KEY)


# ╭─────────────────────────── Constants ───────────────────────────╮
URL = "https://newsapi.org/v2/top-headlines"

# Valid default sources (NewsAPI: do NOT mix country/category with 'sources')
_DEFAULT_SOURCES = [
    "bloomberg",
    "the-wall-street-journal",
    "the-economist",
    "reuters",
    "cnbc",
]

# Cache TTLs (seconds)
TTL_HEADLINES = 60 * 30

# Request defaults
DEFAULT_PAGE_SIZE = 5
DEFAULT_LANGUAGE = "en"
REQUEST_TIMEOUT = 12
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Helper Functions ───────────────────────────╮
def _to_sources_csv(sources: Optional[Union[Dict[str, str], Iterable[str]]]) -> Optional[str]:
    """
    Convert sources to CSV string format for NewsAPI.
    
    Accepts:
      - dict like {"Bloomberg":"bloomberg", ...} → join VALUES
      - list/tuple/set of slugs → join directly
      - None → None
    
    Args:
        sources: Sources in various formats
    
    Returns:
        Comma-separated string of source slugs or None
    """
    if not sources:
        return None
    if isinstance(sources, dict):
        # Join VALUES (slugs), not keys (labels)
        vals = [v for v in sources.values() if isinstance(v, str) and v.strip()]
        return ",".join(vals) if vals else None
    # Otherwise assume iterable of strings (slugs)
    vals = [s for s in sources if isinstance(s, str) and s.strip()]
    return ",".join(vals) if vals else None


def _normalize_articles(articles: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Normalize articles to a uniform, resilient shape.
    
    Args:
        articles: List of article dictionaries from NewsAPI
    
    Returns:
        List of normalized article dictionaries
    """
    if not articles:
        return []
    out: List[Dict[str, Any]] = []
    seen = set()
    for a in articles:
        url = a.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({
            "title": (a.get("title") or "").strip(),
            "description": a.get("description") or "",
            "url": url,
            "urlToImage": a.get("urlToImage"),  # keep original key for UI
            "source": a.get("source") or {},
            "publishedAt": a.get("publishedAt") or "",
        })
    return out
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Fetch Functions ───────────────────────────╮
@st.cache_data(ttl=TTL_HEADLINES)
def fetch_headlines(
    page_size: int = DEFAULT_PAGE_SIZE,
    sources: Optional[Union[Dict[str, str], Iterable[str]]] = None,
    *args: Any
) -> List[Dict[str, Any]]:
    """
    Fetch top headlines from NewsAPI.
    
    Uses sources (slugs) only, per NewsAPI rule (no country/category mixed).
    
    Args:
        page_size: Number of articles to fetch
        sources: Optional sources in dict or iterable format
        *args: Additional arguments (for backward compatibility)
    
    Returns:
        List of normalized article dictionaries
    """
    params_local: Dict[str, Any] = {
        "apiKey": API_KEY,
        "language": DEFAULT_LANGUAGE,
        "pageSize": page_size,
    }
    joined = _to_sources_csv(sources) or _to_sources_csv(_DEFAULT_SOURCES)
    if joined:
        params_local["sources"] = joined

    resp = requests.get(URL, params=params_local, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return _normalize_articles(data.get("articles", []))


def fetch_all_news(
    query: str,
    sources: Optional[Union[Dict[str, str], Iterable[str]]],
    domains: Optional[Union[Dict[str, str], Iterable[str]]],
    from_date: str,
    to_date: str,
    language: str = DEFAULT_LANGUAGE,
    sort: str = "relevancy",
    page: int = 2,
    page_num: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch all news articles using NewsAPI Everything endpoint.
    
    Accepts dicts (labels→slugs) or iterables of slugs.
    Returns normalized article dicts.
    
    Args:
        query: Search query string
        sources: Optional sources in dict or iterable format
        domains: Optional domains in dict or iterable format
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        language: Language code (default: "en")
        sort: Sort order (default: "relevancy")
        page: Page number
        page_num: Number of articles per page
    
    Returns:
        List of normalized article dictionaries
    
    Raises:
        RuntimeError: If NewsAPI request fails
    """
    try:
        all_articles = newsapi.get_everything(
            q=query,
            sources=_to_sources_csv(sources),
            domains=_to_sources_csv(domains),
            from_param=from_date,
            to=to_date,
            language=language,
            sort_by=sort,
            page=page,
            page_size=page_num,
        )
    except NewsAPIException as e:
        raise RuntimeError(f"NewsAPI error (everything): {e}") from e

    return _normalize_articles(all_articles.get("articles", []))
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main entry point for testing news fetcher."""
    for art in fetch_headlines():
        src = (art.get("source") or {}).get("name", "")
        print(f"{art.get('publishedAt', '')[:10]} | {src}\n  {art.get('title', '')}\n")


if __name__ == "__main__":
    main()

