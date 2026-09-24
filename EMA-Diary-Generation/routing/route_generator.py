"""
Route Generator — GPS routes from diary locations using OSRM.

Generates actual lat/lon coordinate sequences between diary locations.
No Docker needed — uses OSRM public API.
"""

import json
import time
import sys
import os
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from osm.query_tools import search_pois, query_pois

OSRM_URL = "http://router.project-osrm.org"


def get_route(from_lon, from_lat, to_lon, to_lat, profile="cycling"):
    """Get a route between two points from OSRM."""
    url = f"{OSRM_URL}/route/v1/{profile}/{from_lon},{from_lat};{to_lon},{to_lat}?overview=full&geometries=geojson"
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            return {
                "coordinates": route["geometry"]["coordinates"],
                "distance_m": route["distance"],
                "duration_s": route["duration"],
            }
    except Exception as e:
        print(f"  Route error: {e}")
    return None


def get_location_coords(location_name, lat=None, lon=None):
    """Get coordinates for a location from OSM database."""
    if lat and lon:
        return lat, lon

    # Search OSM
    results = search_pois(location_name, limit=1)
    if results:
        return results[0]["lat"], results[0]["lon"]

    return None, None


def generate_routes_from_diary(diary, locations):
    """Generate GPS routes for all transit episodes in a diary."""
    routes = []
    eps = diary.get("episodes", [])

    for i, ep in enumerate(eps):
        if ep.get("primary_activity") not in ["cycling", "walking", "running"]:
            continue

        # Find previous and next locations
        from_loc = None
        to_loc = None

        # Check transit_from/transit_to
        for role, loc in locations.items():
            name = loc.get("name", "")
            if name and name in ep.get("specific_location", ""):
                to_loc = loc
            if i > 0 and name in eps[i - 1].get("specific_location", ""):
                from_loc = loc

        # Try to infer from surrounding episodes
        if not from_loc and i > 0:
            prev = eps[i - 1]
            for role, loc in locations.items():
                if loc.get("name", "") in prev.get("specific_location", ""):
                    from_loc = loc
                    break

        if not to_loc and i < len(eps) - 1:
            next_ep = eps[i + 1]
            for role, loc in locations.items():
                if loc.get("name", "") in next_ep.get("specific_location", ""):
                    to_loc = loc
                    break

        if from_loc and to_loc:
            profile = "cycling" if ep["primary_activity"] == "cycling" else "foot"
            route = get_route(
                from_loc.get("lon", 10.395), from_loc.get("lat", 63.43),
                to_loc.get("lon", 10.395), to_loc.get("lat", 63.43),
                profile
            )
            if route:
                route["from_name"] = from_loc.get("name", "?")
                route["to_name"] = to_loc.get("name", "?")
                route["episode_purpose"] = ep.get("purpose", "")
                route["start_time"] = ep.get("start_time", "")
                route["end_time"] = ep.get("end_time", "")
                route["activity"] = ep["primary_activity"]
                routes.append(route)
                time.sleep(0.5)

    return routes


def generate_map_html(routes, locations, output_path="output/trondheim_map.html"):
    """Generate an interactive Leaflet map with routes and locations."""
    # Prepare location markers
    markers_js = []
    colors = {"home": "#e74c3c", "work": "#3498db", "gym": "#2ecc71",
              "cafe": "#f39c12", "park": "#27ae60", "supermarket": "#9b59b6"}

    for role, loc in locations.items():
        lat = loc.get("lat", 0)
        lon = loc.get("lon", 0)
        name = loc.get("name", role)
        color = colors.get(role, "#555555")
        markers_js.append(
            f'L.marker([{lat}, {lon}], {{icon: L.divIcon({{className: "custom-icon", '
            f'html: \'<div style="background:{color};width:12px;height:12px;border-radius:50%;'
            f'border:2px solid white;"></div>\', iconSize: [12,12]}})}})'
            f'.bindPopup("<b>{name}</b><br>{role}").addTo(map);'
        )

    # Prepare route polylines
    polylines_js = []
    route_colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
                    "#1abc9c", "#e67e22", "#34495e", "#16a085", "#c0392b"]

    for i, route in enumerate(routes):
        coords = route["coordinates"]
        latlngs = [[c[1], c[0]] for c in coords]
        color = route_colors[i % len(route_colors)]
        dist = route["distance_m"]
        dur = route["duration_s"]
        popup = f"{route['start_time']} {route['activity']}: {route['from_name']} → {route['to_name']}<br>{dist:.0f}m / {dur:.0f}s"
        polylines_js.append(
            f'L.polyline({json.dumps(latlngs)}, {{color: "{color}", weight: 4, opacity: 0.8}})'
            f'.bindPopup("{popup}").addTo(map);'
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Jar of Life — Trondheim Routes</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; font-family: sans-serif; }}
        #map {{ height: 90vh; width: 100%; }}
        #info {{ padding: 10px; background: #f8f9fa; font-size: 13px; }}
    </style>
</head>
<body>
    <div id="info">
        <b>Jar of Life — Trondheim Routes</b> |
        {len(routes)} routes | {len(locations)} locations |
        Click routes for details
    </div>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([63.4305, 10.3951], 14);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
        }}).addTo(map);

        {chr(10).join(markers_js)}

        {chr(10).join(polylines_js)}

        // Fit map to all routes
        var allCoords = [];
        {chr(10).join([f'allCoords.push(...{json.dumps([[c[1],c[0]] for c in r["coordinates"]])});' for r in routes])}
        if (allCoords.length > 0) {{
            map.fitBounds(L.latLngBounds(allCoords).pad(0.1));
        }}
    </script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    return output_path


if __name__ == "__main__":
    # Load last diary
    diary_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "jar_of_life_staged.json")
    with open(diary_path) as f:
        data = json.load(f)

    diary = data["diary"]
    locations = data.get("locations", {})

    # Add coords to locations from OSM
    print("Getting location coordinates...", flush=True)
    for role, loc in locations.items():
        if not loc.get("lat"):
            lat, lon = get_location_coords(loc.get("name", ""))
            if lat:
                loc["lat"] = lat
                loc["lon"] = lon

    print("Generating routes...", flush=True)
    routes = generate_routes_from_diary(diary, locations)
    print(f"  {len(routes)} routes generated", flush=True)

    for r in routes:
        print(f"  {r['start_time']} {r['activity']}: {r['from_name']} → {r['to_name']} ({r['distance_m']:.0f}m)", flush=True)

    print("Generating map...", flush=True)
    map_path = generate_map_html(routes, locations)
    print(f"  Map saved to {map_path}", flush=True)

    # Save routes data
    routes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "routes.json")
    with open(routes_path, "w") as f:
        json.dump(routes, f, indent=2)
    print(f"  Routes saved to {routes_path}", flush=True)
