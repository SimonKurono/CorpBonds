# pages/News.py ─────────────────────────────────────────────────────────
"""News Search and Analysis Page."""

from __future__ import annotations

# ── Stdlib
import datetime as dt
from typing import Any, Dict, List, Mapping

# ── Third-party
import pandas as pd
import streamlit as st

# ── Local
import utils.ui as ui
from utils.fetchers import news_fetcher as nf


# ╭─────────────────────────── Constants ───────────────────────────╮
CATEGORIES = {
    "Business": "business",
    "Entertainment": "entertainment",
    "General": "general",
    "Health": "health",
    "Science": "science",
    "Sports": "sports",
    "Technology": "technology",
}

SOURCES = {
    "Bloomberg": "bloomberg",
    "Business Insider": "business-insider",
    "Financial Post": "financial-post",
    "Fortune": "fortune",
    "The Wall Street Journal": "the-wall-street-journal",
    "The Economist": "the-economist",
    "Reuters": "reuters",
    "CNBC": "cnbc",
    "TechCrunch": "techcrunch",
}

THEME_QUERIES = {
    "Macro": "interest rates OR inflation OR GDP OR CPI OR unemployment",
    "Technology": "AI OR semiconductors OR cloud OR software OR 'big tech'",
    "Industry": "manufacturing OR industrials OR supply chain",
    "Energy": "oil OR gas OR renewables OR energy transition",
    "Healthcare": "biotech OR pharma OR healthcare policy OR FDA",
    "Entertainment": "streaming OR box office OR gaming industry",
}

DEFAULT_HEADLINES_COUNT = 6
DEFAULT_THEME_ARTICLES_COUNT = 3
DEFAULT_SEARCH_ARTICLES_COUNT = 10
DEFAULT_DATE_RANGE_DAYS = 7
# ╰─────────────────────────────────────────────────────────────────╯

# ╭──────────────────────── Helpers and caching ──────────────────────╮
def _source_name(article: Dict[str, Any]) -> str:
    """Extract source name from article dictionary."""
    src = (article.get("source") or {}).get("name")
    return src or ""


def _labels_to_slug_dict(selected: List[str], mapping: Dict[str, str]) -> Dict[str, str]:
    """Return {label: slug} dictionary for just the selected labels."""
    return {label: mapping[label] for label in selected if label in mapping}
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="News Search & Analysis", page_icon="📰", layout="wide")
    ui.render_sidebar()
    #st.title("News Search & Analysis")


def render_search_parameters() -> tuple[List[str], List[str], str, dt.date, dt.date, bool]:
    """Render search parameter inputs and return user selections."""
    st.header("Search Parameters")
    c1, c2, c3, c4, c5, c6 = st.columns([1.25, 1.25, 2.0, 1.25, 1.25, 1.0], vertical_alignment="bottom")

    with c1:
        selected_categories = st.multiselect(
            "Select Category",
            list(CATEGORIES.keys()),
            default=["Business"],
        )

    with c2:
        selected_sources = st.multiselect(
            "Select Sources",
            list(SOURCES.keys()),
            default=["Bloomberg"],
        )

    with c3:
        keyword = st.text_input(
            "Additional Keywords",
            placeholder="e.g., stock market, economy",
            max_chars=80,
        )

    with c4:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime(dt.date.today() - dt.timedelta(days=DEFAULT_DATE_RANGE_DAYS)),
        )

    with c5:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime(dt.date.today()),
        )

    with c6:
        run_search = st.button("Search", type="primary", use_container_width=True)

    return selected_categories, selected_sources, keyword, start_date, end_date, run_search


def render_featured_grid(articles: List[Dict[str, Any]]) -> None:
    """Render featured article grid: 1 main article + 2 side articles."""
    if not articles:
        st.info("No articles found.")
        return

    main, side = articles[0], articles[1:3]  # safe even if less than 3 total

    main_col, side_col = st.columns([2, 1])
    with main_col:
        if main.get("urlToImage"):
            st.image(main["urlToImage"], use_container_width=True)
        title = main.get("title", "").strip() or "Untitled"
        src = _source_name(main)
        meta = f"{main.get('publishedAt', '')[:10]}  ·  {src}" if src else main.get('publishedAt', '')[:10]
        st.markdown(f"### {title}")
        if meta:
            st.caption(meta)
        if main.get("description"):
            st.write(main["description"])
        st.markdown(f"[Read more]({main.get('url')})")

    with side_col:
        for art in side:
            if art.get("urlToImage"):
                st.image(art["urlToImage"], use_container_width=True)
            title = art.get("title", "").strip() or "Untitled"
            src = _source_name(art)
            meta = f"{art.get('publishedAt', '')[:10]}  ·  {src}" if src else art.get('publishedAt', '')[:10]
            st.markdown(f"**{title}**")
            if meta:
                st.caption(meta)
            if art.get("description"):
                st.write(art["description"])
            st.markdown(f"[Read more]({art.get('url')})")


def render_article_card(article: Dict[str, Any]) -> None:
    """Render a simple, resilient card layout for one article."""
    if article.get("urlToImage"):
        with st.container(height="stretch"):
            st.image(article["urlToImage"], use_container_width=True)

            title = article.get("title", "").strip() or "Untitled"
            src = _source_name(article)
            meta = f"{article.get('publishedAt', '')[:10]}  ·  {src}" if src else article.get('publishedAt', '')[:10]
            st.markdown(f"**{title}**")
            if meta:
                st.caption(meta)
            if article.get("description"):
                st.write(article["description"])
            st.markdown(f"[Read more]({article.get('url')})")


def render_section(title: str, articles: List[Dict[str, Any]]) -> None:
    """Render a section of articles in a 3-column grid layout."""
    st.subheader(title)
    if not articles:
        st.info("No articles found.")
        return

    # 3-column masonry layout
    c1, c2, c3 = st.columns(3)
    for i, art in enumerate(articles):
        with (c1 if i % 3 == 0 else c2 if i % 3 == 1 else c3):
            render_article_card(art)

    st.markdown("---")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Search functions ───────────────────────────╮
def perform_search(
    selected_categories: List[str],
    selected_sources: List[str],
    keyword: str,
    start_date: dt.date,
    end_date: dt.date,
) -> List[Dict[str, Any]]:
    """
    Perform news search using the Everything endpoint via nf.fetch_all_news.
    
    Args:
        selected_categories: List of selected category labels
        selected_sources: List of selected source labels
        keyword: Additional keyword string
        start_date: Start date for search
        end_date: End date for search
    
    Returns:
        List of article dictionaries
    """
    src_dict = _labels_to_slug_dict(selected_sources, SOURCES)

    # Build query: combine selected category labels plus free-text keyword
    cats_query = " OR ".join(selected_categories) if selected_categories else ""
    q_parts = [cats_query.strip(), keyword.strip()]
    query_str = " ".join(p for p in q_parts if p)

    # Ensure valid ISO strings for NewsAPI
    from_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    to_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")

    try:
        results = nf.fetch_all_news(
            query=query_str or "business",  # safe fallback
            sources=src_dict or None,
            domains=None,
            from_date=from_date,
            to_date=to_date,
            language="en",
            sort="relevancy",
            page=1,
            page_num=DEFAULT_SEARCH_ARTICLES_COUNT,
        )
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

    return results


def load_default_dashboard() -> None:
    """
    Load and display default dashboard with top headlines and themed sections.
    
    Shows:
    1) Top headlines strip (nf.fetch_headlines) from trusted defaults
    2) Themed sections using Everything queries
    """
    # Top headlines (trusted sources via nf.fetch_headlines)
    try:
        top = nf.fetch_headlines(page_size=DEFAULT_HEADLINES_COUNT)
    except Exception as e:
        top = []
        st.warning(f"Could not load top headlines: {e}")

    if top:
        st.subheader("Top Headlines")
        render_featured_grid(top)
        st.divider()

    # Themed sections (Everything endpoint)
    # Default date window: last 7 days
    to_date = dt.date.today()
    from_date = to_date - dt.timedelta(days=DEFAULT_DATE_RANGE_DAYS)

    for theme, q in THEME_QUERIES.items():
        try:
            arts = nf.fetch_all_news(
                query=q,
                sources=None,  # let query drive it; you can add source bias later
                domains=None,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
                language="en",
                sort="relevancy",
                page=1,
                page_num=DEFAULT_THEME_ARTICLES_COUNT,
            )
        except Exception as e:
            arts = []
            st.warning(f"{theme}: failed to load ({e})")

        render_section(theme, arts)
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()

    # Get search parameters from UI
    selected_categories, selected_sources, keyword, start_date, end_date, run_search = render_search_parameters()

    # Show search results or default dashboard
    if run_search:
        results = perform_search(selected_categories, selected_sources, keyword, start_date, end_date)
        render_section("Search Results", results)
    else:
        load_default_dashboard()


if __name__ == "__main__":
    main()
