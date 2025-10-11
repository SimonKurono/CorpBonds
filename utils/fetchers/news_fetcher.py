# utils/fetchers/news_fetcher.py
import os
from typing import Iterable, Optional, Union, List, Dict, Any
from dotenv import load_dotenv
import requests
from fredapi import Fred  # kept to avoid breaking imports elsewhere
import streamlit as st
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

# 1) Load key from .env
load_dotenv()
API_KEY = os.getenv("NEWSAPI_KEY")
if not API_KEY:
    raise RuntimeError("Missing NEWSAPI_KEY in .env")

newsapi = NewsApiClient(API_KEY)

# 2) Endpoints
URL = "https://newsapi.org/v2/top-headlines"

# Valid default sources (NewsAPI: do NOT mix country/category with 'sources')
_DEFAULT_SOURCES = [
    "bloomberg",
    "the-wall-street-journal",
    "the-economist",
    "reuters",
    "cnbc",
]

def _to_sources_csv(sources: Optional[Union[Dict[str, str], Iterable[str]]]) -> Optional[str]:
    """
    Accepts:
      - dict like {"Bloomberg":"bloomberg", ...} → join VALUES
      - list/tuple/set of slugs → join directly
      - None → None
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
    """Uniform, resilient shape."""
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
            "urlToImage": a.get("urlToImage"),  # keep original key for your UI
            "source": a.get("source") or {},
            "publishedAt": a.get("publishedAt") or "",
        })
    return out

@st.cache_data(ttl=60 * 30)
def fetch_headlines(page_size: int = 5,
                    sources: Optional[Union[Dict[str, str], Iterable[str]]] = None,
                    *args) -> List[Dict[str, Any]]:
    """
    Minimal, backward-compatible fix:
    - Makes params optional (so __main__ smoke test works).
    - Uses sources (slugs) only, per NewsAPI rule (no country/category mixed in this helper).
    - Fixes the old 'paarams' typo; actually uses local params.
    - Adds timeout and normalization.
    """
    params_local: Dict[str, Any] = {
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": page_size,
    }
    joined = _to_sources_csv(sources) or _to_sources_csv(_DEFAULT_SOURCES)
    if joined:
        params_local["sources"] = joined

    resp = requests.get(URL, params=params_local, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    return _normalize_articles(data.get("articles", []))

def fetch_all_news(query: str,
                   sources: Optional[Union[Dict[str, str], Iterable[str]]],
                   domains: Optional[Union[Dict[str, str], Iterable[str]]],
                   from_date: str,
                   to_date: str,
                   language: str = "en",
                   sort: str = "relevancy",
                   page: int = 2) -> List[Dict[str, Any]]:
    """
    Keeps your signature. Accepts dicts (labels→slugs) or iterables of slugs.
    Returns normalized article dicts.
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
            page_size=50,  
        )
    except NewsAPIException as e:
        raise RuntimeError(f"NewsAPI error (everything): {e}") from e

    return _normalize_articles(all_articles.get("articles", []))

if __name__ == "__main__":
    for art in fetch_headlines():
        src = (art.get("source") or {}).get("name", "")
        print(f"{art.get('publishedAt','')[:10]} | {src}\n  {art.get('title','')}\n")
