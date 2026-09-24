"""
OpenStreetMap Trondheim Indexer.

Downloads and indexes POIs from Trondheim for the diary grounding module.
Uses Overpass API to extract categorized locations.
Stores in SQLite for fast local queries.

Run once: python3 osm/trondheim_indexer.py
Creates: osm/trondheim_osm.db
"""

import json
import sqlite3
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# Trondheim bounding box
# Center: 63.4305°N, 10.3951°E
# Radius: ~15km covers city + suburbs
# ──────────────────────────────────────────────────────────────────────

BBOX = {
    "south": 63.3800,
    "west": 10.2500,
    "north": 63.4800,
    "east": 10.5500,
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DB_PATH = Path(__file__).parent / "trondheim_osm.db"

# ──────────────────────────────────────────────────────────────────────
# OSM Tag Categories
# ──────────────────────────────────────────────────────────────────────

CATEGORIES = {
    "residential": {
        "query": """
            way["building"~"apartment|house|residential|detached|terrace|semidetached"]({bbox});
            relation["building"~"apartment|house|residential"]({bbox});
        """,
        "subcategory": "residential",
    },
    "commercial_office": {
        "query": """
            way["building"="office"]({bbox});
            node["office"]({bbox});
            node["amenity"="coworking_space"]({bbox});
        """,
        "subcategory": "office",
    },
    "food_cafe": {
        "query": """
            node["amenity"="cafe"]({bbox});
            node["amenity"="restaurant"]({bbox});
            node["amenity"="fast_food"]({bbox});
            node["amenity"="bakery"]({bbox});
        """,
        "subcategory": "food",
    },
    "food_supermarket": {
        "query": """
            node["shop"="supermarket"]({bbox});
            node["shop"="convenience"]({bbox});
        """,
        "subcategory": "food",
    },
    "recreation_gym": {
        "query": """
            node["leisure"="fitness_centre"]({bbox});
            node["leisure"="sports_centre"]({bbox});
        """,
        "subcategory": "recreation",
    },
    "recreation_park": {
        "query": """
            way["leisure"="park"]({bbox});
            way["leisure"="garden"]({bbox});
            way["natural"="wood"]({bbox});
            node["leisure"="playground"]({bbox});
        """,
        "subcategory": "recreation",
    },
    "recreation_swimming": {
        "query": """
            node["leisure"="swimming_pool"]({bbox});
            node["leisure"="water_park"]({bbox});
        """,
        "subcategory": "recreation",
    },
    "transport_bus": {
        "query": """
            node["highway"="bus_stop"]({bbox});
            node["public_transport"="platform"]({bbox});
        """,
        "subcategory": "transport",
    },
    "transport_train": {
        "query": """
            node["railway"="station"]({bbox});
            node["railway"="halt"]({bbox});
        """,
        "subcategory": "transport",
    },
    "transport_bike_parking": {
        "query": """
            node["amenity"="bicycle_parking"]({bbox});
            node["amenity"="bicycle_rental"]({bbox});
        """,
        "subcategory": "transport",
    },
    "education_university": {
        "query": """
            way["amenity"="university"]({bbox});
            node["amenity"="university"]({bbox});
            way["amenity"="college"]({bbox});
        """,
        "subcategory": "education",
    },
    "education_school": {
        "query": """
            way["amenity"="school"]({bbox});
            node["amenity"="school"]({bbox});
        """,
        "subcategory": "education",
    },
    "education_library": {
        "query": """
            node["amenity"="library"]({bbox});
        """,
        "subcategory": "education",
    },
    "health_clinic": {
        "query": """
            node["amenity"="clinic"]({bbox});
            node["amenity"="doctors"]({bbox});
            node["amenity"="pharmacy"]({bbox});
        """,
        "subcategory": "health",
    },
    "health_hospital": {
        "query": """
            way["amenity"="hospital"]({bbox});
            node["amenity"="hospital"]({bbox});
        """,
        "subcategory": "health",
    },
    "accommodation_hotel": {
        "query": """
            node["tourism"="hotel"]({bbox});
            node["tourism"="hostel"]({bbox});
            node["tourism"="guest_house"]({bbox});
        """,
        "subcategory": "accommodation",
    },
    "bar_nightlife": {
        "query": """
            node["amenity"="bar"]({bbox});
            node["amenity"="pub"]({bbox});
            node["amenity"="nightclub"]({bbox});
        """,
        "subcategory": "social",
    },
    "cinema_entertainment": {
        "query": """
            node["amenity"="cinema"]({bbox});
            node["amenity"="theatre"]({bbox});
            node["amenity"="arts_centre"]({bbox});
        """,
        "subcategory": "entertainment",
    },
    "worship": {
        "query": """
            way["amenity"="place_of_worship"]({bbox});
            node["amenity"="place_of_worship"]({bbox});
        """,
        "subcategory": "community",
    },
}


def build_bbox_str() -> str:
    """Format bounding box for Overpass query."""
    return f"{BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']}"


def query_overpass(query: str, retries: int = 3) -> list[dict]:
    """Execute Overpass API query."""
    bbox = build_bbox_str()
    full_query = f"""
    [out:json][timeout:120];
    (
    {query.format(bbox=bbox)}
    );
    out center;
    """

    for attempt in range(retries):
        try:
            req = Request(
                OVERPASS_URL,
                data=urlencode({"data": full_query}).encode("utf-8"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode())
            return result.get("elements", [])
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
    return []


def extract_poi(element: dict, category: str, subcategory: str) -> dict:
    """Extract POI data from Overpass element."""
    tags = element.get("tags", {})

    # Get coordinates
    if element["type"] == "node":
        lat = element.get("lat")
        lon = element.get("lon")
    elif "center" in element:
        lat = element["center"]["lat"]
        lon = element["center"]["lon"]
    else:
        return None

    if lat is None or lon is None:
        return None

    return {
        "osm_id": f"{element['type']}_{element['id']}",
        "name": tags.get("name", ""),
        "category": category,
        "subcategory": subcategory,
        "lat": lat,
        "lon": lon,
        "tags_json": json.dumps(tags),
    }


def create_database(db_path: Path):
    """Create SQLite database with POI table."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pois (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            osm_id TEXT UNIQUE,
            name TEXT,
            category TEXT,
            subcategory TEXT,
            lat REAL,
            lon REAL,
            tags_json TEXT
        )
    """)

    # Spatial index (simple lat/lon grid for fast nearest-neighbor)
    c.execute("CREATE INDEX IF NOT EXISTS idx_category ON pois(category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_subcategory ON pois(subcategory)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_lat_lon ON pois(lat, lon)")

    # Config table
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    return conn


def index_trondheim():
    """Main indexing function."""
    print("=" * 60)
    print("Trondheim OSM Indexer")
    print("=" * 60)

    # Create database
    db_path = DB_PATH
    print(f"\nDatabase: {db_path}")
    conn = create_database(db_path)

    total_pois = 0

    for category, config in CATEGORIES.items():
        print(f"\nFetching: {category}...", end=" ", flush=True)
        elements = query_overpass(config["query"])

        pois = []
        for el in elements:
            poi = extract_poi(el, category, config["subcategory"])
            if poi:
                pois.append(poi)

        # Insert into database
        c = conn.cursor()
        inserted = 0
        for poi in pois:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO pois (osm_id, name, category, subcategory, lat, lon, tags_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (poi["osm_id"], poi["name"], poi["category"],
                      poi["subcategory"], poi["lat"], poi["lon"], poi["tags_json"]))
                inserted += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        total_pois += inserted
        print(f"{inserted} POIs")

        time.sleep(2)  # rate limit courtesy for Overpass

    # Store metadata
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
              ("bbox", json.dumps(BBOX)))
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
              ("total_pois", str(total_pois)))
    conn.commit()

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Total POIs indexed: {total_pois}")
    print(f"Database: {db_path}")

    # Category breakdown
    c = conn.cursor()
    c.execute("SELECT category, COUNT(*) FROM pois GROUP BY category ORDER BY COUNT(*) DESC")
    print(f"\nBreakdown:")
    for cat, count in c.fetchall():
        print(f"  {cat}: {count}")

    conn.close()
    print(f"\nDone!")


if __name__ == "__main__":
    index_trondheim()
