# pages/news_search_and_analysis.py
import datetime as dt
import pandas as pd
import streamlit as st

import utils.ui as ui
from utils.fetchers import news_fetcher as nf  # <- use your helper


# --- Page & Sidebar ---
def configure_page():
    ui.render_sidebar()
    st.set_page_config(layout="wide")
    st.title("News Search & Analysis")

# --- Constants / Mappings (labels → slugs) ---
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

# --- Themed default queries (Everything endpoint; no cat/source mixing issues) ---
THEME_QUERIES = {
    "Macro": "interest rates OR inflation OR GDP OR CPI OR unemployment",
    "Technology": "AI OR semiconductors OR cloud OR software OR 'big tech'",
    "Industry": "manufacturing OR industrials OR supply chain",
    "Energy": "oil OR gas OR renewables OR energy transition",
    "Healthcare": "biotech OR pharma OR healthcare policy OR FDA",
    "Entertainment": "streaming OR box office OR gaming industry",
}

# --- UI: Search Parameters ---
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
        value=pd.to_datetime(dt.date.today() - dt.timedelta(days=7)),
    )

with c5:
    end_date = st.date_input(
        "End Date",
        value=pd.to_datetime(dt.date.today()),
    )
with c6:
    run_search = st.button("Search", type="primary", use_container_width=True)

# --- Small render helpers ---
def _source_name(a: dict) -> str:
    src = (a.get("source") or {}).get("name")
    return src or ""

def render_featured_grid(articles: list[dict]):
    """1 Main + 2 side articles."""
    if not articles:
        st.info("No articles found.")
        return
    main, side = articles[0], articles[1:3]  # safe even if less than 3 total

    main_col, side_col = st.columns([2, 1])
    with main_col:
        if (main.get("urlToImage")):
            st.image(main["urlToImage"], use_container_width=True)
        title = main.get("title", "").strip() or "Untitled"
        src = _source_name(main)
        meta = f"{main.get('publishedAt','')[:10]}  ·  {src}" if src else main.get('publishedAt','')[:10]
        st.markdown(f"### {title}")
        if meta:
            st.caption(meta)
        if main.get("description"):
            st.write(main["description"])   
        st.markdown(f"[Read more]({main.get('url')})")
    with side_col:
        for art in side:
            if(art.get("urlToImage")):
                st.image(art["urlToImage"], use_container_width=True)
            title = art.get("title", "").strip() or "Untitled"
            src = _source_name(art)
            meta = f"{art.get('publishedAt','')[:10]}  ·  {src}" if src else art.get('publishedAt','')[:10]
            st.markdown(f"**{title}**")
            if meta:
                st.caption(meta)
            if art.get("description"):
                st.write(art["description"])
            st.markdown(f"[Read more]({art.get('url')})")
            
            

def render_article_card(a: dict):
    """Simple, resilient card layout for one article."""
    if a.get("urlToImage"):
        with st.container(height="stretch"):
            st.image(a["urlToImage"], use_container_width=True)
                
            title = a.get("title", "").strip() or "Untitled"
            src = _source_name(a)
            meta = f"{a.get('publishedAt','')[:10]}  ·  {src}" if src else a.get('publishedAt','')[:10]
            st.markdown(f"**{title}**")
            if meta:
                st.caption(meta)
            if a.get("description"):
                st.write(a["description"])
            st.markdown(f"[Read more]({a.get('url')})")

def render_section(title: str, articles: list[dict]):
    st.subheader(title)
    if not articles:
        st.info("No articles found.")
        return
    # 3-column masonry feel
    
    c1, c2, c3 = st.columns(3)
    for i, art in enumerate(articles):
            with (c1 if i % 3 == 0 else c2 if i % 3 == 1 else c3):
                render_article_card(art)
    
    

    st.markdown("---")


def _labels_to_slug_dict(selected: list[str], mapping: dict[str, str]) -> dict[str, str]:
    """Return {label: slug} for just the selected labels."""
    return {label: mapping[label] for label in selected if label in mapping}

# --- Search behavior ---
def perform_search():
    """
    Uses the Everything endpoint via nf.fetch_all_news.
    - sources: from selection (labels→slugs)
    - domains: None (you can wire this later if desired)
    - query: combine category labels + keyword
    - date window: from UI
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
            page_num=10,
        )
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

    return results

def load_default_dashboard():
    """
    Shows:
    1) Top headlines strip (nf.fetch_headlines) from trusted defaults.
    2) Themed sections using Everything queries.
    """
    # 1) Top headlines (trusted sources via nf.fetch_headlines)
    try:
        top = nf.fetch_headlines(page_size=6)  # cached by helper
    except Exception as e:
        top = []
        st.warning(f"Could not load top headlines: {e}")

    if top:
        st.subheader("Top Headlines")
        render_featured_grid(top)
        st.divider()

    # 2) Themed sections (Everything endpoint)
    # default date window: last 7 days
    to_date = dt.date.today()
    from_date = to_date - dt.timedelta(days=7)

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
                page_num=3,
            )
        except Exception as e:
            arts = []
            st.warning(f"{theme}: failed to load ({e})")

        render_section(theme, arts)

# --- Main: show search results or default dashboard ---
if run_search:
    results = perform_search()
    render_section("Search Results", results)
else:
    load_default_dashboard()


def main():
    configure_page()
    load_default_dashboard()

if __name__ == "main":
    main()
