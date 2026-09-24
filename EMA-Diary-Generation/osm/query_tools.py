"""
OSM Query Tools for the Jar of Life diary agent.

Provides query functions that the ReAct agent can call to:
- Find POIs by category near a location
- Find routes between two points
- Find residential areas for persona home assignment
- Look up specific places by name
"""

import sqlite3
import json
import math
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "trondheim_osm.db"


def get_connection():
    """Get database connection."""
    return sqlite3.connect(str(DB_PATH))


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def query_pois(category: str, near_lat: float = None, near_lon: float = None,
               radius_km: float = 3.0, limit: int = 10, named_only: bool = False) -> list[dict]:
    """
    Query POIs by category, optionally filtered by proximity.

    Args:
        category: POI category (residential, food, recreation, etc.) or subcategory
        near_lat: Center latitude for proximity search
        near_lon: Center longitude for proximity search
        radius_km: Search radius in km
        limit: Max results
        named_only: Only return POIs with names

    Returns:
        List of POI dicts with name, lat, lon, category, subcategory, distance
    """
    conn = get_connection()
    c = conn.cursor()

    # Try as category first, then subcategory
    c.execute("SELECT COUNT(*) FROM pois WHERE category = ?", (category,))
    if c.fetchone()[0] > 0:
        where = "category = ?"
        params = [category]
    else:
        where = "subcategory = ?"
        params = [category]

    if named_only:
        where += " AND name != ''"

    c.execute(f"SELECT name, lat, lon, category, subcategory, street, housenumber FROM pois WHERE {where}", params)
    rows = c.fetchall()
    conn.close()

    results = []
    for name, lat, lon, cat, subcat, street, housenumber in rows:
        dist = None
        if near_lat and near_lon:
            dist = haversine(near_lat, near_lon, lat, lon)
            if dist > radius_km:
                continue

        address = ""
        if street:
            address = street
            if housenumber:
                address += f" {housenumber}"

        results.append({
            "name": name or f"Unnamed {subcat}",
            "lat": lat,
            "lon": lon,
            "category": cat,
            "subcategory": subcat,
            "address": address,
            "distance_km": round(dist, 2) if dist else None,
        })

    # Sort by distance if available
    if near_lat and near_lon:
        results.sort(key=lambda x: x["distance_km"] or 999)

    return results[:limit]


def query_nearby(lat: float, lon: float, radius_km: float = 0.5, limit: int = 20) -> list[dict]:
    """
    Find all POIs near a coordinate, regardless of category.

    Useful for understanding what's around a specific location.
    """
    conn = get_connection()
    c = conn.cursor()

    # Use bounding box for speed
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))

    c.execute("""SELECT name, lat, lon, category, subcategory, street
        FROM pois
        WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?""",
        (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta))
    rows = c.fetchall()
    conn.close()

    results = []
    for name, plat, plon, cat, subcat, street in rows:
        dist = haversine(lat, lon, plat, plon)
        if dist <= radius_km:
            results.append({
                "name": name or f"Unnamed {subcat}",
                "lat": plat,
                "lon": plon,
                "category": cat,
                "subcategory": subcat,
                "address": street or "",
                "distance_km": round(dist, 3),
            })

    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]


def search_pois(query: str, category: str = None, limit: int = 10) -> list[dict]:
    """
    Search POIs by name (partial match).

    Useful for finding specific places like "Dromedar" or "SiT".
    """
    conn = get_connection()
    c = conn.cursor()

    where = "name LIKE ?"
    params = [f"%{query}%"]

    if category:
        where += " AND category = ?"
        params.append(category)

    c.execute(f"SELECT name, lat, lon, category, subcategory, street FROM pois WHERE {where} LIMIT ?", params + [limit])
    rows = c.fetchall()
    conn.close()

    return [{"name": n or "Unnamed", "lat": la, "lon": lo, "category": cat,
             "subcategory": sub, "address": st or ""} for n, la, lo, cat, sub, st in rows]


def get_residential_areas(limit: int = 20) -> list[dict]:
    """
    Get named residential buildings for persona home assignment.

    Returns residential POIs that have names (apartment buildings, etc.)
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("""SELECT name, lat, lon, street, housenumber
        FROM pois
        WHERE category = 'residential' AND name != ''
        LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()

    return [{"name": n, "lat": la, "lon": lo,
             "address": f"{st} {hn}".strip() if st else ""}
            for n, la, lo, st, hn in rows]


def get_stats() -> dict:
    """Get database statistics."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM pois")
    total = c.fetchone()[0]

    c.execute("SELECT category, COUNT(*) FROM pois GROUP BY category ORDER BY COUNT(*) DESC")
    by_category = {row[0]: row[1] for row in c.fetchall()}

    c.execute("SELECT subcategory, COUNT(*) FROM pois GROUP BY subcategory ORDER BY COUNT(*) DESC")
    by_subcategory = {row[0]: row[1] for row in c.fetchall()}

    conn.close()

    return {
        "total_pois": total,
        "by_category": by_category,
        "by_subcategory": by_subcategory,
    }


# ──────────────────────────────────────────────────────────────────────
# Tool functions for the ReAct agent (string-based interface)
# ──────────────────────────────────────────────────────────────────────

def tool_query_pois(category: str, near: str = "", radius_km: float = 3.0, limit: int = 5) -> str:
    """
    Find places by category. Optionally near a coordinate.

    Args:
        category: One of: residential, food, recreation, work, education, social, transport, health
                  Or subcategory: cafe, restaurant, gym, park, supermarket, etc.
        near: "lat,lon" string like "63.4305,10.3951" or empty for all
        radius_km: Search radius in km
        limit: Max results

    Returns:
        JSON string of matching POIs
    """
    near_lat, near_lon = None, None
    if near and "," in near:
        parts = near.split(",")
        near_lat = float(parts[0].strip())
        near_lon = float(parts[1].strip())

    results = query_pois(category, near_lat, near_lon, radius_km, limit, named_only=True)
    return json.dumps(results, indent=2)


def tool_search_places(query: str, category: str = "", limit: int = 5) -> str:
    """
    Search for places by name.

    Args:
        query: Name or partial name to search (e.g., "Dromedar", "SiT", "NTNU")
        category: Optional category filter
        limit: Max results

    Returns:
        JSON string of matching POIs
    """
    results = search_pois(query, category or None, limit)
    return json.dumps(results, indent=2)


def tool_nearby_places(lat: float, lon: float, radius_km: float = 0.3) -> str:
    """
    List all places near a coordinate.

    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius

    Returns:
        JSON string of nearby POIs sorted by distance
    """
    results = query_nearby(lat, lon, radius_km, limit=15)
    return json.dumps(results, indent=2)


if __name__ == "__main__":
    print("=== OSM Query Tools Test ===\n")

    stats = get_stats()
    print(f"Database: {stats['total_pois']} POIs\n")
    print("By category:")
    for cat, count in stats["by_category"].items():
        print(f"  {cat}: {count}")

    print("\n--- Test: cafes near NTNU (63.4246, 10.3932) ---")
    cafes = query_pois("cafe", 63.4246, 10.3932, 2.0, 5, named_only=True)
    for c in cafes:
        print(f"  {c['name']:30s} {c['distance_km']}km {c['address']}")

    print("\n--- Test: search 'SiT' ---")
    results = search_pois("SiT")
    for r in results:
        print(f"  {r['name']:30s} {r['category']}/{r['subcategory']}")

    print("\n--- Test: parks near Byparken (63.4305, 10.3951) ---")
    parks = query_pois("park", 63.4305, 10.3951, 3.0, 5, named_only=True)
    for p in parks:
        print(f"  {p['name']:30s} {p['distance_km']}km")
