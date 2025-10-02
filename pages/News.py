import streamlit as st
import pandas as pd
import utils.ui as ui

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
category_col1, source_col2, col1, col2 = st.columns(4)

with category_col1:
    primary_keyword = st.multiselect("Select News Category", categories.keys(), default=["Business"])
with source_col2:
    source = st.multiselect("Select News Source", sources.keys(), default=["Bloomberg"])
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("today"))



