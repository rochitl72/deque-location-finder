from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, requests, json
from datetime import datetime
from difflib import get_close_matches

# ------------------ FastAPI Setup ------------------
app = FastAPI(title="De-Que Backend", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ API Keys ------------------
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
FOURSQUARE_API_BASE = "https://api.foursquare.com/v3"

# ------------------ Dynamic Categories ------------------
CATEGORY_MAP = {}

def fetch_foursquare_categories():
    """Fetch categories from Foursquare and build a CATEGORY_MAP."""
    global CATEGORY_MAP
    url = f"{FOURSQUARE_API_BASE}/places/categories"
    headers = {"Authorization": FOURSQUARE_API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch categories:", response.text)
        CATEGORY_MAP = {}
        return

    categories_data = response.json()

    def process_category(cat):
        CATEGORY_MAP[cat["name"].lower()] = [cat["id"]]
        for subcat in cat.get("categories", []):
            process_category(subcat)

    for category in categories_data:
        process_category(category)

    print(f"[INFO] Loaded {len(CATEGORY_MAP)} categories from Foursquare.")

def find_category(query):
    """Find closest category ID(s) based on query."""
    if not CATEGORY_MAP:
        return None
    query_lower = query.lower()
    match = get_close_matches(query_lower, list(CATEGORY_MAP.keys()), n=1, cutoff=0.5)
    return CATEGORY_MAP[match[0]] if match else None

# ------------------ Foursquare API ------------------
def fetch_foursquare_places(query, latitude, longitude, limit=5):
    category_ids = find_category(query)
    url = f"{FOURSQUARE_API_BASE}/places/search"
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {"ll": f"{latitude},{longitude}", "limit": limit}

    if category_ids:
        params["categories"] = ",".join(category_ids)
    else:
        params["query"] = query

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # Save log
    os.makedirs("logs", exist_ok=True)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "latitude": latitude,
        "longitude": longitude,
        "results": data.get("results", [])
    }
    with open(f"logs/foursquare_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json", "w") as log_file:
        json.dump(log_data, log_file, indent=2)

    return {"results": data.get("results", [])}

# ------------------ Pydantic Models ------------------
class ChatbotQuery(BaseModel):
    query: str
    latitude: float
    longitude: float
    limit: int = 5

# ------------------ Root Endpoint ------------------
@app.get("/")
def root():
    return {"message": "De-Que Backend is running with dynamic category mapping!"}

# ------------------ Foursquare Endpoint ------------------
@app.get("/chatbot/foursquare")
def foursquare_search(query: str, latitude: float, longitude: float, limit: int = 5):
    return fetch_foursquare_places(query, latitude, longitude, limit)

# ------------------ Chatbot Query Endpoint ------------------
@app.post("/chatbot/query")
async def chatbot_query(payload: ChatbotQuery):
    query = payload.query
    latitude = payload.latitude
    longitude = payload.longitude
    limit = payload.limit

    places = fetch_foursquare_places(query, latitude, longitude, limit)
    results = places.get("results", [])

    if not results:
        return {"reply": "No relevant places found nearby.", "places": {"results": []}}

    ranked_results = sorted(results, key=lambda p: p.get("distance", 10000))
    top_places = "\n".join(
        [f"- {p['name']} ({p['location'].get('formatted_address', 'Address N/A')})" for p in ranked_results[:3]]
    )
    reply = f"Based on your query '{query}', here are some recommended places:\n{top_places}"

    return {"reply": reply, "places": {"results": ranked_results}}

# ------------------ App Startup ------------------
@app.on_event("startup")
def on_startup():
    print("[INFO] Fetching categories from Foursquare...")
    fetch_foursquare_categories()
# ------------------ Fetch All Categories ------------------
@app.get("/chatbot/categories")
def get_all_categories_fallback():
    """Fetch categories by using a dummy search query as fallback."""
    url = "https://api.foursquare.com/v3/places/search"
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {"query": "restaurant", "limit": 50, "ll": "13.0067,80.2570"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch categories", "status": response.status_code}

    data = response.json()
    categories = []

    for place in data.get("results", []):
        for cat in place.get("categories", []):
            if cat not in categories:
                categories.append({
                    "id": cat.get("id"),
                    "name": cat.get("name")
                })

    return {"categories": categories}