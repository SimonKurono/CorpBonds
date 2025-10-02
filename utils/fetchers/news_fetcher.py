import os
from dotenv import load_dotenv
import requests
from fredapi import Fred
import streamlit as st

# 1) Load key from .env
load_dotenv()
API_KEY = os.getenv("NEWSAPI_KEY")
if not API_KEY:
    raise RuntimeError("Missing NEWSAPI_KEY in .env")

# 2) Define endpoint & params
URL = "https://newsapi.org/v2/top-headlines"
params = {
    "apiKey": API_KEY,
    "language": "en",
    "pageSize": 5,
    "sources": "bloomberg, the-wall-street-journal, the-economist, us, business"    
}

@st.cache_data(ttl=60*30) 
def fetch_headlines(page_size: int, sources: dict, *args) -> list[dict]:
    paarams = {
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": page_size,
        "sources": ",".join(sources)
    }
    resp = requests.get(URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("articles", [])




if __name__ == "__main__":
    for art in fetch_headlines():
        print(f"{art['publishedAt'][:10]} | {art['source']['name']}\n  {art['title']}\n")
