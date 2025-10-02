import os
import requests

def get_treasury_freshness() -> str:
    # Example: Query the FRED API for the most recent data date for Treasury rates.
    fred_key = os.getenv("FRED_API_KEY")
    # Replace with a real endpoint and parameter setup; this is just a demonstration.
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={fred_key}&file_type=json"
    try:
        response = requests.get(url)
        data = response.json()
        # Assume the last observation date is in data["observations"][-1]["date"]
        last_date = data["observations"][-1]["date"]
        return f"EOD • {last_date}"
    except Exception as e:
        return "Unavailable"
    

def get_oas_freshness() -> str:
    # Replace with your real API endpoint for OAS data.
    url = "https://api.example.com/oas/latest"
    try:
        response = requests.get(url)
        data = response.json()
        # Assume the API returns a date field
        last_date = data.get("last_date", "N/A")
        return f"EOD • {last_date}"
    except Exception as e:
        return "Unavailable"
    

def get_news_freshness() -> str:
    # Example: Query the News API for the timestamp of the latest article.
    news_key = os.getenv("NEWSAPI_KEY")
    url = f"https://newsapi.org/v2/top-headlines?apiKey={news_key}&q=finance"
    try:
        response = requests.get(url)
        data = response.json()
        # Assume the first article's publishedAt gives us a timestamp
        published = data["articles"][0]["publishedAt"]
        # You might want to format the timestamp as needed
        return published.replace("T", " ").split("Z")[0]  # very basic formatting
    except Exception as e:
        return "Unavailable"