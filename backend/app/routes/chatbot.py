import os
import json
import requests
from datetime import datetime
from openai import OpenAI

# ------------------ API Keys ------------------
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "your_foursquare_api_key_here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------ Logging ------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def save_log(filename, data):
    """Save data into logs folder."""
    path = os.path.join(LOG_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return path

# ------------------ Foursquare ------------------
CAFE_CATEGORIES = {13032, 13034, 13035, 13036, 13065}  # Allowed category IDs

def fetch_foursquare_places(query: str, latitude: float, longitude: float, limit: int = 5):
    url = "https://api.foursquare.com/v3/places/search"
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {"query": query, "ll": f"{latitude},{longitude}", "limit": limit}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # Filter only cafes/restaurants
    filtered = []
    for place in data.get("results", []):
        category_ids = {c.get("id") for c in place.get("categories", [])}
        if category_ids & CAFE_CATEGORIES:
            filtered.append(place)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_log(f"foursquare_{timestamp}.json", {"query": query, "results": filtered})
    return filtered

# ------------------ OpenAI Reasoning ------------------
def get_openai_reasoning(query: str, places: list):
    """
    Generate reasoning and ranking using OpenAI.
    """
    place_summary = "\n".join(
        [f"{idx+1}. {p['name']} - {p['location'].get('formatted_address', 'Address unknown')}"
         for idx, p in enumerate(places)]
    )
    prompt = f"You are a location assistant. Based on the following places:\n{place_summary}\nRank and describe them in relation to '{query}' focusing on coziness and relevance."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert assistant for location recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print("OpenAI Exception:", e)
        return None

# ------------------ Local Ranking ------------------
def rank_places_locally(query: str, places: list):
    def score_place(place):
        score = 0
        name = place.get("name", "").lower()
        category = place["categories"][0]["name"].lower() if place.get("categories") else ""
        distance = place.get("distance", 10000)

        if "cafe" in category or "coffee" in category or "tea" in category:
            score += 10
        if "cozy" in query.lower() and ("cafe" in name or "coffee" in category):
            score += 5
        score += max(0, (2000 - distance) // 100)
        return score

    return sorted(places, key=score_place, reverse=True)

# ------------------ Main Handler ------------------
def handle_chatbot_query(query: str, latitude: float, longitude: float, limit: int = 5):
    places = fetch_foursquare_places(query, latitude, longitude, limit)
    if not places:
        return {"reply": "No relevant places found nearby.", "places": []}

    reasoning = get_openai_reasoning(query, places)
    if not reasoning:
        ranked_places = rank_places_locally(query, places)
        reasoning = "Based on local analysis, here are the top suggested places:\n" + \
                    "\n".join([f"- {p['name']}" for p in ranked_places[:3]])
        return {"reply": reasoning, "places": ranked_places}

    return {"reply": reasoning, "places": places}