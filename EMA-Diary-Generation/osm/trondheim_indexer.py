"""
Trondheim OSM POI Indexer.

Downloads and indexes Points of Interest from OpenStreetMap for Trondheim.
Uses Overpass API to extract categorized locations.
Stores in SQLite for fast queries by the Jar of Life diary agent.

Run: python3 osm/trondheim_indexer.py
Creates: osm/trondheim_osm.db
"""

import json
import sqlite3
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DB_PATH = Path(__file__).parent / "trondheim_osm.db"

# Trondheim bounding box: ~15km radius from center
BBOX = (63.3800, 10.2500, 63.4800, 10.5500)  # south, west, north, east

# ──────────────────────────────────────────────────────────────────────
# OSM Tag Queries
# ──────────────────────────────────────────────────────────────────────

QUERIES = {
    "residential": 'way["building"~"apartment|house|residential|detached"]({b});',
    "office": 'node["office"]({b});way["building"="office"]({b});node["amenity"="coworking_space"]({b});',
    "university": 'way["amenity"="university"]({b});node["amenity"="university"]({b});',
    "school": 'way["amenity"="school"]({b});node["amenity"="school"]({b});',
    "cafe": 'node["amenity"="cafe"]({b});',
    "restaurant": 'node["amenity"="restaurant"]({b});',
    "fast_food": 'node["amenity"="fast_food"]({b});',
    "bakery": 'node["amenity"="bakery"]({b});',
    "bar": 'node["amenity"="bar"]({b});node["amenity"="pub"]({b});',
    "supermarket": 'node["shop"="supermarket"]({b});',
    "convenience": 'node["shop"="convenience"]({b});',
    "gym": 'node["leisure"="fitness_centre"]({b});node["leisure"="sports_centre"]({b});',
    "swimming": 'node["leisure"="swimming_pool"]({b});',
    "park": 'way["leisure"="park"]({b});way["leisure"="garden"]({b});',
    "playground": 'node["leisure"="playground"]({b});',
    "cinema": 'node["amenity"="cinema"]({b});',
    "theatre": 'node["amenity"="theatre"]({b});',
    "library": 'node["amenity"="library"]({b});',
    "hospital": 'way["amenity"="hospital"]({b});node["amenity"="hospital"]({b});',
    "clinic": 'node["amenity"="clinic"]({b});node["amenity"="doctors"]({b});',
    "pharmacy": 'node["amenity"="pharmacy"]({b});',
    "bus_stop": 'node["highway"="bus_stop"]({b});',
    "train_station": 'node["railway"="station"]({b});node["railway"="halt"]({b});',
    "bicycle_parking": 'node["amenity"="bicycle_parking"]({b});',
    "bicycle_rental": 'node["amenity"="bicycle_rental"]({b});',
    "hotel": 'node["tourism"="hotel"]({b});node["tourism"="hostel"]({b});',
    "place_of_worship": 'way["amenity"="place_of_worship"]({b});node["amenity"="place_of_worship"]({b});',
}

# Category grouping for the diary agent
CATEGORY_GROUPS = {
    "residential": ["residential"],
    "work": ["office", "university"],
    "food": ["cafe", "restaurant", "fast_food", "bakery", "supermarket", "convenience"],
    "recreation": ["gym", "swimming", "park", "playground", "cinema", "theatre"],
    "transport": ["bus_stop", "train_station", "bicycle_parking", "bicycle_rental"],
    "health": ["hospital", "clinic", "pharmacy"],
    "education": ["university", "school", "library"],
    "social": ["bar", "restaurant", "cafe"],
    "accommodation": ["hotel"],
}


def build_bbox_str():
    return f"{BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]}"


def query_overpass(query_str, retries=3):
    """Execute Overpass API query."""
    bbox = build_bbox_str()
    full_query = f"[out:json][timeout:180];({query_str.format(b=bbox)});out center;"

    for attempt in range(retries):
        try:
            req = Request(
                OVERPASS_URL,
                data=urlencode({"data": full_query}).encode("utf-8"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urlopen(req, timeout=240) as resp:
                return json.loads(resp.read().decode()).get("elements", [])
        except Exception as e:
            print(f"    attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(15 * (attempt + 1))
    return []


def extract_poi(element, subcategory):
    """Extract POI from Overpass element."""
    tags = element.get("tags", {})

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

    # Find parent category
    parent_cat = "other"
    for cat, subs in CATEGORY_GROUPS.items():
        if subcategory in subs:
            parent_cat = cat
            break

    return {
        "osm_id": f"{element['type']}_{element['id']}",
        "name": tags.get("name", ""),
        "category": parent_cat,
        "subcategory": subcategory,
        "lat": lat,
        "lon": lon,
        "street": tags.get("addr:street", ""),
        "housenumber": tags.get("addr:housenumber", ""),
        "city": tags.get("addr:city", "Trondheim"),
        "tags_json": json.dumps(tags),
    }


def create_database(db_path):
    """Create SQLite database."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS pois (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        osm_id TEXT UNIQUE,
        name TEXT,
        category TEXT,
        subcategory TEXT,
        lat REAL,
        lon REAL,
        street TEXT,
        housenumber TEXT,
        city TEXT,
        tags_json TEXT
    )""")

    c.execute("CREATE INDEX IF NOT EXISTS idx_cat ON pois(category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_subcat ON pois(subcategory)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_latlon ON pois(lat, lon)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_name ON pois(name)")

    c.execute("""CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")

    conn.commit()
    return conn


def index_trondheim():
    """Main indexing function."""
    print("=" * 60)
    print("Trondheim OSM POI Indexer")
    print("=" * 60)

    conn = create_database(DB_PATH)
    total = 0

    for subcategory, query in QUERIES.items():
        print(f"\n  Fetching {subcategory}...", end=" ", flush=True)
        elements = query_overpass(query)

        c = conn.cursor()
        inserted = 0
        for el in elements:
            poi = extract_poi(el, subcategory)
            if poi:
                try:
                    c.execute("""INSERT OR IGNORE INTO pois
                        (osm_id, name, category, subcategory, lat, lon, street, housenumber, city, tags_json)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (poi["osm_id"], poi["name"], poi["category"], poi["subcategory"],
                         poi["lat"], poi["lon"], poi["street"], poi["housenumber"],
                         poi["city"], poi["tags_json"]))
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass

        conn.commit()
        total += inserted
        print(f"{inserted} POIs")
        time.sleep(3)  # rate limit courtesy

    # Store metadata
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", ("bbox", json.dumps(BBOX)))
    c.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", ("total_pois", str(total)))
    c.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", ("indexed_at", time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Total POIs: {total}")

    c = conn.cursor()
    c.execute("SELECT category, subcategory, COUNT(*) FROM pois GROUP BY category, subcategory ORDER BY category, COUNT(*) DESC")
    print(f"\nBreakdown:")
    current_cat = ""
    for cat, subcat, count in c.fetchall():
        if cat != current_cat:
            print(f"\n  {cat.upper()}:")
            current_cat = cat
        print(f"    {subcat}: {count}")

    conn.close()
    print(f"\nDatabase: {DB_PATH}")
    print("Done!")


if __name__ == "__main__":
    index_trondheim()
