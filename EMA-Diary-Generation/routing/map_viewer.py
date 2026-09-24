import json, sys, os, folium, time
from urllib.request import Request, urlopen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from osm.query_tools import search_pois, query_pois

OSRM_URL = "http://router.project-osrm.org"

def get_route(flon, flat, tlon, tlat, profile="cycling"):
    url = f"{OSRM_URL}/route/v1/{profile}/{flon},{flat};{tlon},{tlat}?overview=full&geometries=geojson"
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("code") == "Ok" and data.get("routes"):
            r = data["routes"][0]
            return {"coords": r["geometry"]["coordinates"], "dist": r["distance"], "dur": r["duration"]}
    except: pass
    return None

def get_nearby_road_point(lat, lon, ref_lat, ref_lon):
    """Get a point near the building that's on a road (approximate by offsetting toward the road)."""
    # Simple approximation: move 30m toward the reference road point
    dlat = ref_lat - lat
    dlon = ref_lon - lon
    dist = (dlat**2 + dlon**2) ** 0.5
    if dist < 0.0001:
        return lat, lon
    # Move 60% of the way toward the road
    return lat + dlat * 0.6, lon + dlon * 0.6

def build_map():
    base = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(base, "output", "jar_of_life_staged.json")) as f:
        data = json.load(f)
    diary = data["diary"]
    locs = data.get("locations", {})

    eps = sorted(diary["episodes"], key=lambda e: e.get("start_time", "00:00"))

    # Find ALL transit episodes and build route pairs
    routes_data = []
    for i, ep in enumerate(eps):
        act = ep.get("primary_activity", "")
        if act not in ["cycling", "walking", "running"]:
            continue

        # Find source (where they were before transit)
        from_loc = None
        to_loc = None

        # Check previous episode for source
        if i > 0:
            prev = eps[i - 1]
            for role, loc in locs.items():
                if loc.get("name") and loc["name"] in prev.get("specific_location", ""):
                    from_loc = loc
                    break

        # Check next episode for destination
        if i < len(eps) - 1:
            nxt = eps[i + 1]
            for role, loc in locs.items():
                if loc.get("name") and loc["name"] in nxt.get("specific_location", ""):
                    to_loc = loc
                    break

        # Also check current episode's location
        if not to_loc:
            for role, loc in locs.items():
                if loc.get("name") and loc["name"] in ep.get("specific_location", ""):
                    to_loc = loc
                    break

        # Infer from purpose/domain
        if not from_loc and i > 0:
            prev_purpose = eps[i - 1].get("purpose", "").lower()
            for role in ["gym", "cafe", "park", "supermarket", "work", "home"]:
                if role in prev_purpose and role in locs:
                    from_loc = locs[role]
                    break

        if not to_loc:
            curr_purpose = ep.get("purpose", "").lower()
            for role in ["gym", "cafe", "park", "supermarket", "work", "home"]:
                if role in curr_purpose and role in locs:
                    to_loc = locs[role]
                    break

        if from_loc and to_loc and from_loc.get("lat") and to_loc.get("lat"):
            if from_loc["name"] != to_loc["name"]:
                routes_data.append({
                    "from": from_loc, "to": to_loc,
                    "time": ep.get("start_time", ""),
                    "end_time": ep.get("end_time", ""),
                    "activity": act,
                    "purpose": ep.get("purpose", ""),
                    "domain": ep.get("domain", ""),
                })

    # Auto-detect missing transit between consecutive episodes at different locations
    for i in range(1, len(eps)):
        prev = eps[i - 1]
        curr = eps[i]

        # Skip if already has a transit route
        if curr.get("primary_activity") in ["cycling", "walking", "running"]:
            continue

        # Find locations for prev and curr
        prev_loc = curr_loc = None
        for role, loc in locs.items():
            if loc.get("name"):
                if loc["name"] in prev.get("specific_location", ""):
                    prev_loc = loc
                if loc["name"] in curr.get("specific_location", ""):
                    curr_loc = loc

        if prev_loc and curr_loc and prev_loc["name"] != curr_loc["name"]:
            # Different locations, no transit episode — add implicit route
            profile = "cycling"  # default
            # Guess activity from time and location
            if "gym" in curr.get("purpose", "").lower():
                profile = "cycling"
            elif prev.get("domain") == "work" and "home" in curr.get("specific_location", "").lower():
                profile = "cycling"

            routes_data.append({
                "from": prev_loc, "to": curr_loc,
                "time": prev.get("end_time", ""),
                "end_time": curr.get("start_time", ""),
                "activity": "implied",
                "purpose": f"travel: {prev.get('purpose', '')} → {curr.get('purpose', '')}",
                "domain": "transport",
            })

    # Deduplicate routes (same from/to)
    seen = set()
    unique_routes = []
    for rd in routes_data:
        key = (rd["from"]["name"], rd["to"]["name"])
        if key not in seen:
            seen.add(key)
            unique_routes.append(rd)
    routes_data = unique_routes

    # Create map
    m = folium.Map(location=[63.4305, 10.3951], zoom_start=14, tiles="CartoDB positron")

    # Add location markers with labels
    icons = {"home": "home", "work": "briefcase", "gym": "flag",
             "cafe": "coffee", "park": "tree", "supermarket": "shopping-cart"}
    colors = {"home": "red", "work": "blue", "gym": "green",
              "cafe": "orange", "park": "darkgreen", "supermarket": "purple"}

    for role, loc in locs.items():
        if loc.get("lat") and loc.get("lon"):
            ic = folium.Icon(color=colors.get(role, "gray"), icon=icons.get(role, "info-sign"), prefix="fa")
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=f"<b>{loc.get('name', role)}</b><br>{role}",
                tooltip=f"{loc.get('name', role)} ({role})",
                icon=ic
            ).add_to(m)

    # Generate and draw routes
    route_colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#2c3e50"]

    for i, rd in enumerate(routes_data):
        profile = "cycling" if rd["activity"] == "cycling" else "foot"
        route = get_route(rd["from"]["lon"], rd["from"]["lat"], rd["to"]["lon"], rd["to"]["lat"], profile)

        if route and len(route["coords"]) > 1:
            latlngs = [[c[1], c[0]] for c in route["coords"]]
            color = route_colors[i % len(route_colors)]

            # Main route line (solid for explicit, dashed for implied)
            is_implied = rd["activity"] == "implied"
            weight = 4 if not is_implied else 3
            dash = "5,10" if is_implied else None
            popup_text = (f"<b>{rd['time']} - {rd['end_time']}</b><br>"
                         f"{rd['activity'].title()}: {rd['from']['name']} → {rd['to']['name']}<br>"
                         f"{route['dist']:.0f}m / {route['dur']:.0f}s<br>"
                         f"{rd['purpose']}")
            folium.PolyLine(
                latlngs, color=color, weight=weight, opacity=0.8,
                dash_array=dash,
                popup=popup_text,
                tooltip=f"{rd['time']} {rd['activity']}: {rd['from']['name']} → {rd['to']['name']}"
            ).add_to(m)

            # Dotted line from building entrance to route start
            start_building = rd["from"]
            route_start = route["coords"][0]
            folium.PolyLine(
                [[start_building["lat"], start_building["lon"]],
                 [route_start[1], route_start[0]]],
                color=color, weight=2, opacity=0.5, dash_array="5,10"
            ).add_to(m)

            # Dotted line from route end to building entrance
            end_building = rd["to"]
            route_end = route["coords"][-1]
            folium.PolyLine(
                [[route_end[1], route_end[0]],
                 [end_building["lat"], end_building["lon"]]],
                color=color, weight=2, opacity=0.5, dash_array="5,10"
            ).add_to(m)

            # Entry/exit markers at building doors
            folium.CircleMarker(
                [start_building["lat"], start_building["lon"]],
                radius=6, color=color, fill=True, fill_opacity=0.7,
                popup=f"EXIT: {start_building.get('name', '?')}"
            ).add_to(m)
            folium.CircleMarker(
                [end_building["lat"], end_building["lon"]],
                radius=6, color=color, fill=True, fill_opacity=0.7,
                popup=f"ENTER: {end_building.get('name', '?')}"
            ).add_to(m)

        time.sleep(0.3)

    # Legend
    legend_html = "<div style='position:fixed;bottom:20px;left:20px;background:white;padding:12px;border-radius:5px;z-index:1000;font-size:12px;max-height:300px;overflow-y:auto;box-shadow:0 2px 6px rgba(0,0,0,0.3);'>"
    legend_html += f"<b>Jar of Life — {len(routes_data)} Routes</b><br><br>"
    for rd in routes_data:
        legend_html += f"{rd['time']} {rd['activity']}: {rd['from']['name']} → {rd['to']['name']}<br>"
    legend_html += "<br><i>Solid = route on street<br>Dotted = to/from building entrance<br>Circle = entry/exit point</i>"
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

    out = os.path.join(base, "output", "trondheim_map.html")
    m.save(out)
    print(f"Map saved to {out}")
    print(f"Routes: {len(routes_data)}")
    for rd in routes_data:
        print(f"  {rd['time']}-{rd['end_time']} {rd['activity']}: {rd['from']['name']} → {rd['to']['name']}")

if __name__ == "__main__":
    build_map()
