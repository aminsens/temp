"""
City Profile for Trondheim.

Encodes geographic, climate, and seasonal characteristics that influence
what activities are realistic and where they happen.

This profile is injected into the diary agent's context so it generates
geographically and seasonally appropriate diaries.
"""

# ──────────────────────────────────────────────────────────────────────
# Geographic Profile
# ──────────────────────────────────────────────────────────────────────

GEOGRAPHY = {
    "city": "Trondheim",
    "country": "Norway",
    "coordinates": {"lat": 63.4305, "lon": 10.3951},
    "elevation_range_m": (0, 400),  # sea level to hilltops
    "terrain": "hilly_coastal",
    "terrain_description": (
        "Trondheim sits along the Trondheimsfjord with hilly terrain. "
        "The city center is relatively flat along the river Nidelva, "
        "but residential areas climb hillsides. Cycling is feasible on "
        "main corridors (Elgeseter gate, Klostergata) but steep in "
        "residential areas (Tyholt, Byåsen). The coastal path (Ladestien) "
        "is flat and popular for walking/running. Kristiansten fortress "
        "hill is a popular running destination with elevation."
    ),
    "coastal": True,
    "fjord_access": True,
    "mountain_proximity_km": 15,  # Bymarka forest/mountain area
    "beaches": [
        {"name": "Korsvika beach", "lat": 63.4450, "lon": 10.4400, "type": "sand"},
        {"name": "Ringvebukta", "lat": 63.4480, "lon": 10.4300, "type": "rocky"},
        {"name": "Rotvoll beach", "lat": 63.4200, "lon": 10.4800, "type": "sand"},
    ],
    "hiking_areas": [
        {"name": "Bymarka forest", "lat": 63.4100, "lon": 10.3200, "difficulty": "easy-moderate"},
        {"name": "Kristiansten fortress", "lat": 63.4300, "lon": 10.4100, "difficulty": "easy"},
        {"name": "Ladestien coastal path", "lat": 63.4500, "lon": 10.4300, "difficulty": "easy"},
        {"name": "Storheia", "lat": 63.4000, "lon": 10.3000, "difficulty": "moderate"},
    ],
    "cycling_feasibility": {
        "main_corridors": "good — flat dedicated bike lanes",
        "residential_hills": "challenging — steep in Tyholt, Byåsen, Saupstad",
        "coastal_paths": "good — Ladestien is flat and scenic",
        "winter": "difficult — snow/ice November-March, many switch to bus",
    },
    "key_landmarks": [
        {"name": "Nidelva river", "type": "river", "activity": "walking, fishing"},
        {"name": "Trondheimsfjord", "type": "fjord", "activity": "swimming, kayaking, walking"},
        {"name": "Nidaros Cathedral", "type": "landmark", "activity": "tourism, walking"},
        {"name": "Bakklandet", "type": "neighborhood", "activity": "cafes, walking, cycling"},
        {"name": "Solsiden", "type": "waterfront", "activity": "dining, entertainment"},
        {"name": "Tyholttårnet", "type": "tower", "activity": "sightseeing, running"},
    ],
}


# ──────────────────────────────────────────────────────────────────────
# Climate Profile
# ──────────────────────────────────────────────────────────────────────

CLIMATE = {
    "climate_zone": "subarctic_oceanic",
    "description": (
        "Trondheim has cool summers and cold winters. "
        "Rain is frequent year-round. Snow covers the ground "
        "from December to March. The Gulf Stream moderates temperatures."
    ),
    "monthly_averages": {
        "jan": {"temp_c": -3, "precipitation_mm": 63, "daylight_hours": 6, "snow": True},
        "feb": {"temp_c": -2, "precipitation_mm": 52, "daylight_hours": 9, "snow": True},
        "mar": {"temp_c": 1, "precipitation_mm": 49, "daylight_hours": 12, "snow": False},
        "apr": {"temp_c": 5, "precipitation_mm": 40, "daylight_hours": 15, "snow": False},
        "may": {"temp_c": 10, "precipitation_mm": 53, "daylight_hours": 18, "snow": False},
        "jun": {"temp_c": 13, "precipitation_mm": 67, "daylight_hours": 20, "snow": False},
        "jul": {"temp_c": 15, "precipitation_mm": 84, "daylight_hours": 19, "snow": False},
        "aug": {"temp_c": 14, "precipitation_mm": 87, "daylight_hours": 16, "snow": False},
        "sep": {"temp_c": 10, "precipitation_mm": 87, "daylight_hours": 13, "snow": False},
        "oct": {"temp_c": 6, "precipitation_mm": 81, "daylight_hours": 10, "snow": False},
        "nov": {"temp_c": 1, "precipitation_mm": 72, "daylight_hours": 7, "snow": True},
        "dec": {"temp_c": -1, "precipitation_mm": 70, "daylight_hours": 5, "snow": True},
    },
    "seasonal_behaviour_patterns": {
        "winter": {
            "months": ["dec", "jan", "feb"],
            "cycling": "reduced — icy roads, dark, many switch to bus/car",
            "outdoor_exercise": "shifts to indoor (gym), skiing if conditions allow",
            "daylight": "very limited (5-9 hours), affects mood and motivation",
            "clothing": "heavy winter gear, layers",
            "typical_indoor_activities": "gym, indoor climbing, swimming pool, home cooking",
        },
        "spring": {
            "months": ["mar", "apr", "may"],
            "cycling": "resumes as roads clear, increasing daylight boosts motivation",
            "outdoor_exercise": "hiking resumes, running increases",
            "daylight": "rapidly increasing (12-18 hours)",
            "mood": "improving, 'spring feeling'",
        },
        "summer": {
            "months": ["jun", "jul", "aug"],
            "cycling": "peak season, long daylight, warm",
            "outdoor_exercise": "beach swimming, hiking, running, kayaking",
            "daylight": "near-constant (19-20 hours), midnight sun effect",
            "special_activities": "BBQ, outdoor dining, beach trips, fishing",
        },
        "autumn": {
            "months": ["sep", "oct", "nov"],
            "cycling": "declining, rain increases, early darkness",
            "outdoor_exercise": "mushroom picking, hiking in colorful forests",
            "daylight": "rapidly decreasing (7-13 hours)",
            "mood": "some seasonal decline as darkness returns",
        },
    },
    "weather_influences": {
        "heavy_rain": {
            "cycling": "switch to bus or work from home",
            "outdoor_exercise": "skip or move to gym",
            "mood": "slightly lower energy",
        },
        "snow": {
            "cycling": "not feasible, bus/car/ski",
            "walking": "slower, need winter boots",
            "exercise": "skiing opportunity, or gym",
        },
        "sunny_warm": {
            "cycling": "preferred, enjoyable",
            "outdoor_exercise": "motivated, longer sessions",
            "social": "outdoor dining, park visits",
            "mood": "positive boost",
        },
        "cold_clear": {
            "cycling": "feasible with proper gear",
            "outdoor_exercise": "invigorating if dressed properly",
            "mood": "energizing",
        },
    },
}


# ──────────────────────────────────────────────────────────────────────
# Activity Feasibility Matrix
# ──────────────────────────────────────────────────────────────────────

ACTIVITY_FEASIBILITY = {
    "cycling_commute": {
        "feasible_year_round": False,
        "feasible_months": ["apr", "may", "jun", "jul", "aug", "sep", "oct"],
        "reduced_months": ["mar", "nov"],
        "not_feasible_months": ["dec", "jan", "feb"],
        "terrain_note": "Main corridors (Elgeseter, Klostergata) are flat. Residential hills challenging.",
        "alternative_when_not_feasible": "bus or walking",
    },
    "outdoor_running": {
        "feasible_year_round": True,
        "reduced_comfort_months": ["dec", "jan", "feb"],
        "best_months": ["may", "jun", "jul", "aug", "sep"],
        "popular_routes": ["Ladestien coastal path", "Kristiansten fortress", "Nidelva riverside"],
        "terrain_note": "Coastal paths are flat. Hill runs (Kristiansten) are moderate elevation.",
    },
    "outdoor_swimming": {
        "feasible_months": ["jun", "jul", "aug"],
        "locations": ["Korsvika beach", "Ringvebukta", "Rotvoll beach", "Trondheimsfjord"],
        "note": "Water is cold even in summer (14-18C). Many swim year-round as 'vinterbading' (winter swimming).",
    },
    "hiking": {
        "feasible_months": ["may", "jun", "jul", "aug", "sep", "oct"],
        "areas": ["Bymarka forest", "Ladestien", "Kristiansten"],
        "note": "Bymarka has extensive trail networks. Popular weekend activity.",
    },
    "skiing": {
        "feasible_months": ["dec", "jan", "feb", "mar"],
        "locations": ["Bymarka groomed trails", "Granåsen ski center"],
        "note": "Cross-country skiing is very popular in Trondheim winters.",
    },
    "gym_year_round": True,
    "indoor_swimming": True,
}


# ──────────────────────────────────────────────────────────────────────
# Agent Context Builder
# ──────────────────────────────────────────────────────────────────────

def get_city_context(month: str = "april") -> str:
    """Build a city context string for the diary agent."""
    month_key = month.lower()[:3]
    climate = CLIMATE["monthly_averages"].get(month_key, CLIMATE["monthly_averages"]["apr"])

    # Determine season
    season = "spring"
    for s, info in CLIMATE["seasonal_behaviour_patterns"].items():
        if month_key in info["months"]:
            season = s
            break

    season_info = CLIMATE["seasonal_behaviour_patterns"][season]

    context = (
        f"CITY: Trondheim, Norway\n"
        f"MONTH: {month} (season: {season})\n"
        f"WEATHER: avg {climate['temp_c']}C, {climate['precipitation_mm']}mm rain, "
        f"{climate['daylight_hours']}h daylight"
        f"{', snow on ground' if climate.get('snow') else ''}\n"
        f"TERRAIN: {GEOGRAPHY['terrain_description'][:200]}\n"
        f"CYCLING: {ACTIVITY_FEASIBILITY['cycling_commute']['terrain_note']}\n"
        f"SEASONAL: {season_info.get('outdoor_exercise', '')[:150]}\n"
        f"COASTAL: Trondheimsfjord access, beaches at Korsvika and Rotvoll\n"
        f"HIKING: Bymarka forest (15km), Ladestien coastal path, Kristiansten fortress\n"
    )

    return context


def get_feasible_activities(month: str) -> dict:
    """Get what activities are feasible in a given month."""
    month_key = month.lower()[:3]
    result = {}

    for activity, info in ACTIVITY_FEASIBILITY.items():
        if isinstance(info, bool):
            result[activity] = info
            continue

        feasible_months = info.get("feasible_months", info.get("feasible_year_round", False))
        if isinstance(feasible_months, bool):
            result[activity] = feasible_months
        elif isinstance(feasible_months, list):
            result[activity] = month_key in feasible_months

    return result


if __name__ == "__main__":
    print("=== Trondheim City Profile ===\n")

    for month in ["january", "april", "july", "october"]:
        print(f"\n--- {month.upper()} ---")
        print(get_city_context(month))
        activities = get_feasible_activities(month)
        feasible = [k for k, v in activities.items() if v]
        not_feasible = [k for k, v in activities.items() if not v]
        print(f"  Feasible: {', '.join(feasible)}")
        print(f"  Not feasible: {', '.join(not_feasible)}")
