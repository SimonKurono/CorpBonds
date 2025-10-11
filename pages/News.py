import streamlit as st
import pandas as pd
import utils.ui as ui
import utils.fetchers.news_fetcher

ui.render_sidebar()
st.set_page_config(layout="wide")
st.title("News Search & Analysis")

categories = {"Business": "business", "Entertainment": "entertainment", "General": "general",
              "Health": "health", "Science": "science", "Sports": "sports", "Technology": "technology"}

sources = {"Bloomberg": "bloomberg", "Business Insider": "business-insider", "Financial Post": "financial-post",
           "Fortune": "fortune", "The Wall Street Journal": "the-wall-street-journal", "The Economist": "the-economist",
              "Reuters": "reuters", "CNBC": "cnbc", "TechCrunch": "techcrunch"}

# --- User Inputs in the Sidebar ---
st.header("Search Parameters")
category_col1, source_col2, keywords, col1, col2 = st.columns(5)

with category_col1:
    primary_keyword = st.multiselect("Select News Category", categories.keys(), default=["Business"], width=200)
with source_col2:
    source = st.multiselect("Select News Source", sources.keys(), default=["Bloomberg"],width=200)
with keywords:
    keyword = st.text_input("Additional Keywords", placeholder="e.g., stock market, economy", max_chars=50)
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("today"))

st.header("Filtered News Articles")
news_df = utils.fetchers.news_fetcher.get_headlines(
    categories=[categories[k] for k in primary_keyword],
    sources=[sources[s] for s in source],
    keywords=keyword,
    from_date=start_date,
    to_date=end_date,
    page_size=100,
)

if not news_df.empty:
    for idx, row in news_df.iterrows():
        st.markdown(f"### [{row['title']}]({row['url']})")
        st.markdown(f"*{row['source']}* | {row['publishedAt'].strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"{row['description']}")
        st.markdown("---")


st.header("Today's Top Macroeconomic Headlines")






