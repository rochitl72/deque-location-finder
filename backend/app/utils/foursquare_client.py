import os
import requests
from dotenv import load_dotenv

load_dotenv()

FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
BASE_URL = "https://api.foursquare.com/v3/places/search"

HEADERS = {
    "Authorization": FOURSQUARE_API_KEY,
    "accept": "application/json"
}

def search_places(query: str, latitude: float, longitude: float, limit: int = 5):
    try:
        params = {
            "query": query,
            "ll": f"{latitude},{longitude}",
            "limit": limit
        }
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}