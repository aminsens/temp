"""
Jar of Life ReAct Agent — Grounded Diary Generation.

Uses dspy.ReAct with OSM query tools to generate geographically
accurate diaries. The agent reasons about what to do next, queries
the map for real locations, and builds the diary step by step.

Architecture:
- Backstory provides day context (influences all decisions)
- Rocks are placed programmatically (work, commute, sleep)
- Pebbles are placed with OSM queries (agent picks real gyms, cafes, parks)
- Sand fills gaps (programmatic micro-moments)
- LLM enriches narratives (Predict, not CoT)
"""

import json
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from osm.query_tools import query_pois, search_pois, tool_query_pois, tool_search_places, tool_nearby_places
from osm.city_loader import get_seasonal_context
from modules.backstory_gen import generate_backstory, DayBackstory
from modules.sand_layer import fill_gaps_with_sand, count_sand, count_rocks_and_pebbles


# ──────────────────────────────────────────────────────────────────────
# Location Picking Logic (replaces ReAct for now — more reliable)
# ──────────────────────────────────────────────────────────────────────

def pick_locations_from_osm(
    backstory: DayBackstory,
    seed: int = 42,
) -> dict:
    """
    Use OSM queries to pick real Trondheim locations for the diary.
    
    Returns a dict of location assignments keyed by role.
    """
    import random
    rng = random.Random(seed)
    
    NTNU_LAT, NTNU_LON = 63.4246, 10.3932
    
    locations = {}
    
    # Home: residential near NTNU
    homes = query_pois("residential", NTNU_LAT, NTNU_LON, 1.5, 10)
    if homes:
        home = rng.choice(homes[:5])
        locations["home"] = home
    else:
        locations["home"] = {"name": "Singsaker apartment", "lat": 63.428, "lon": 10.395, "category": "residential"}
    
    # Work: university or office
    works = query_pois("university", NTNU_LAT, NTNU_LON, 3.0, 5, named_only=True)
    if not works:
        works = query_pois("office", NTNU_LAT, NTNU_LON, 2.0, 5, named_only=True)
    if works:
        locations["work"] = rng.choice(works[:3])
    else:
        locations["work"] = {"name": "NTNU Realfagbygget", "lat": NTNU_LAT, "lon": NTNU_LON, "category": "work"}
    
    # Gym (if exercising today)
    if backstory.exercise_likelihood() > 0.5:
        gyms = query_pois("gym", NTNU_LAT, NTNU_LON, 3.0, 5, named_only=True)
        if gyms:
            locations["gym"] = rng.choice(gyms[:3])
        else:
            locations["gym"] = {"name": "SiT Gløshaugen", "lat": 63.424, "lon": 10.393, "category": "recreation"}
    
    # Cafe for lunch
    cafes = query_pois("cafe", NTNU_LAT, NTNU_LON, 0.8, 5, named_only=True)
    if cafes:
        locations["lunch_cafe"] = rng.choice(cafes[:3])
    else:
        locations["lunch_cafe"] = {"name": "Dromedar Kaffebar", "lat": 63.425, "lon": 10.393, "category": "food"}
    
    # Park for walk
    parks = query_pois("park", NTNU_LAT, NTNU_LON, 2.0, 5, named_only=True)
    if parks:
        locations["park"] = rng.choice(parks[:3])
    else:
        locations["park"] = {"name": "Byparken", "lat": 63.431, "lon": 10.395, "category": "recreation"}
    
    # Supermarket (if grocery day — random)
    if rng.random() < 0.4:
        markets = query_pois("supermarket", locations["home"]["lat"], locations["home"]["lon"], 1.0, 3, named_only=True)
        if markets:
            locations["supermarket"] = markets[0]
    
    # Social location (if social plan)
    if backstory.has_social_plan:
        if "dinner" in backstory.social_description.lower() or "restaurant" in backstory.social_description.lower():
            restaurants = query_pois("restaurant", NTNU_LAT, NTNU_LON, 2.0, 5, named_only=True)
            if restaurants:
                locations["restaurant"] = rng.choice(restaurants[:3])
        elif "drinks" in backstory.social_description.lower():
            bars = query_pois("bar", NTNU_LAT, NTNU_LON, 1.5, 5, named_only=True)
            if bars:
                locations["bar"] = rng.choice(bars[:3])
        else:
            # Friend's home
            friend_homes = query_pois("residential", 63.440, 10.410, 2.0, 5)
            if friend_homes:
                locations["friend_home"] = friend_homes[0]
    
    # Running route (if exercising outdoors)
    if backstory.exercise_likelihood() > 0.5 and backstory.weather in ["sunny", "cloudy", "partly_cloudy"]:
        # Use park as running route
        if "park" in locations:
            locations["running_route"] = locations["park"]
    
    return locations


# ──────────────────────────────────────────────────────────────────────
# Episode Placement (Rocks + Pebbles)
# ──────────────────────────────────────────────────────────────────────

def place_rocks(backstory: DayBackstory, locations: dict) -> list[dict]:
    """Place the fixed anchors (rocks) of the day."""
    
    home_name = locations.get("home", {}).get("name", "home")
    work_name = locations.get("work", {}).get("name", "office")
    is_weekend = backstory.day_of_week in ["Saturday", "Sunday"]
    
    rocks = []
    
    # Sleep (always)
    rocks.append({"start_time": "22:15", "end_time": "07:00", "hetus_code": "011",
        "primary_activity": "lying", "domain": "self_care", "purpose": "sleep",
        "specific_location": home_name, "location_type": "home"})
    
    # Morning routine (always)
    rocks.append({"start_time": "07:00", "end_time": "07:15", "hetus_code": "011",
        "primary_activity": "lying", "domain": "self_care", "purpose": "waking up",
        "specific_location": home_name, "location_type": "home"})
    
    rocks.append({"start_time": "07:15", "end_time": "07:45", "hetus_code": "031",
        "primary_activity": "standing", "domain": "self_care", "purpose": "morning routine",
        "specific_location": home_name, "location_type": "home"})
    
    # Work (weekdays only)
    if not is_weekend:
        rocks.append({"start_time": "08:25", "end_time": "12:00", "hetus_code": "111",
            "primary_activity": "sitting", "domain": "work", "purpose": "morning work",
            "specific_location": work_name, "location_type": "work_office"})
        
        rocks.append({"start_time": "13:00", "end_time": "15:45", "hetus_code": "111",
            "primary_activity": "sitting", "domain": "work", "purpose": "afternoon work",
            "specific_location": work_name, "location_type": "work_office"})
        
        # Work wrap-up (fills gap between work and next activity)
        rocks.append({"start_time": "15:45", "end_time": "16:05", "hetus_code": "111",
            "primary_activity": "sitting", "domain": "work", "purpose": "wrapping up, checking messages",
            "specific_location": work_name, "location_type": "work_office"})
    
    return rocks


def place_pebbles(
    backstory: DayBackstory,
    locations: dict,
    seed: int = 42,
) -> list[dict]:
    """Place variable episodes (pebbles) influenced by backstory."""
    
    import random
    rng = random.Random(seed)
    
    home_name = locations.get("home", {}).get("name", "home")
    is_weekend = backstory.day_of_week in ["Saturday", "Sunday"]
    
    pebbles = []
    
    # Commute (weekdays only)
    if not is_weekend:
        work_name = locations.get("work", {}).get("name", "office")
        
        if backstory.weather not in ["snowy", "rainy"] and backstory.month not in ["dec", "jan", "feb"]:
            # Cycle to work
            pebbles.append({"start_time": "08:05", "end_time": "08:25", "hetus_code": "910",
                "primary_activity": "cycling", "domain": "transport", "purpose": "commute to work",
                "specific_location": "Elgeseter gate bike lane", "location_type": "street",
                "indoor_outdoor": "outdoor", "social_context": "alone",
                "transit_from": home_name, "transit_to": work_name})
            
            pebbles.append({"start_time": "16:05", "end_time": "16:25", "hetus_code": "910",
                "primary_activity": "cycling", "domain": "transport", "purpose": "cycle home or to gym",
                "specific_location": "Klostergata", "location_type": "street",
                "indoor_outdoor": "outdoor", "social_context": "alone"})
        else:
            # Bad weather — mention bus or work from home
            pebbles.append({"start_time": "08:05", "end_time": "08:30", "hetus_code": "910",
                "primary_activity": "sitting", "domain": "transport", "purpose": "bus to work",
                "specific_location": "AtB bus, line 5", "location_type": "transit_vehicle",
                "indoor_outdoor": "indoor", "social_context": "alone"})
    
    # Lunch
    lunch_cafe = locations.get("lunch_cafe", {}).get("name", "cafeteria")
    pebbles.append({"start_time": "12:00", "end_time": "12:45", "hetus_code": "021",
        "primary_activity": "sitting", "domain": "social", "purpose": "lunch",
        "specific_location": lunch_cafe, "location_type": "restaurant",
        "indoor_outdoor": "indoor", "social_context": "with_colleagues"})
    
    # Lunch walk (if weather permits)
    if backstory.weather not in ["rainy", "snowy"]:
        park = locations.get("park", {}).get("name", "Byparken")
        pebbles.append({"start_time": "12:45", "end_time": "13:00", "hetus_code": "611",
            "primary_activity": "walking", "domain": "exercise", "purpose": "lunch walk",
            "specific_location": park, "location_type": "park",
            "indoor_outdoor": "outdoor", "social_context": "alone"})
    
    # Exercise (if likelihood is high)
    if backstory.exercise_likelihood() > rng.random():
        if "gym" in locations:
            gym = locations["gym"]
            pebbles.append({"start_time": "16:25", "end_time": "17:30", "hetus_code": "615",
                "primary_activity": "standing", "domain": "exercise", "purpose": "gym workout",
                "specific_location": gym.get("name", "gym"), "location_type": "gym",
                "indoor_outdoor": "indoor", "social_context": "alone"})
        elif backstory.weather in ["sunny", "cloudy", "partly_cloudy"] and "park" in locations:
            park = locations["park"]
            pebbles.append({"start_time": "16:20", "end_time": "17:10", "hetus_code": "612",
                "primary_activity": "running", "domain": "exercise", "purpose": "evening run",
                "specific_location": park.get("name", "park"), "location_type": "park",
                "indoor_outdoor": "outdoor", "social_context": "alone"})
    
    # Supermarket (if assigned)
    if "supermarket" in locations:
        market = locations["supermarket"]
        pebbles.append({"start_time": "18:10", "end_time": "18:25", "hetus_code": "361",
            "primary_activity": "walking", "domain": "household", "purpose": "grocery shopping",
            "specific_location": market.get("name", "supermarket"), "location_type": "shop",
            "indoor_outdoor": "indoor", "social_context": "alone"})
    
    # Post-gym: shower + commute home (fills the gap between gym and evening)
    if "gym" in locations:
        gym_name = locations["gym"].get("name", "gym")
        pebbles.append({"start_time": "17:30", "end_time": "17:45", "hetus_code": "031",
            "primary_activity": "standing", "domain": "self_care", "purpose": "shower at gym",
            "specific_location": gym_name + ", showers", "location_type": "gym",
            "indoor_outdoor": "indoor", "social_context": "alone"})
        pebbles.append({"start_time": "17:45", "end_time": "18:05", "hetus_code": "910",
            "primary_activity": "cycling", "domain": "transport", "purpose": "cycle home from gym",
            "specific_location": "Klostergata towards home", "location_type": "street",
            "indoor_outdoor": "outdoor", "social_context": "alone"})
        pebbles.append({"start_time": "18:05", "end_time": "19:00", "hetus_code": "311",
            "primary_activity": "standing", "domain": "household", "purpose": "cook dinner",
            "specific_location": home_name, "location_type": "home",
            "indoor_outdoor": "indoor", "social_context": "alone"})
    else:
        # No gym — cook dinner directly after work
        pebbles.append({"start_time": "16:25", "end_time": "17:15", "hetus_code": "311",
            "primary_activity": "standing", "domain": "household", "purpose": "cook dinner",
            "specific_location": home_name, "location_type": "home",
            "indoor_outdoor": "indoor", "social_context": "alone"})
    
    # Social activity
    if backstory.has_social_plan:
        if "restaurant" in locations:
            loc = locations["restaurant"]
            pebbles.append({"start_time": "19:00", "end_time": "20:30", "hetus_code": "021",
                "primary_activity": "sitting", "domain": "social", "purpose": "dinner out",
                "specific_location": loc.get("name", "restaurant"), "location_type": "restaurant",
                "indoor_outdoor": "indoor", "social_context": "with_partner"})
        elif "bar" in locations:
            loc = locations["bar"]
            pebbles.append({"start_time": "17:00", "end_time": "18:30", "hetus_code": "021",
                "primary_activity": "sitting", "domain": "social", "purpose": "after-work drinks",
                "specific_location": loc.get("name", "bar"), "location_type": "restaurant",
                "indoor_outdoor": "indoor", "social_context": "with_colleagues"})
    
    # Evening leisure
    pebbles.append({"start_time": "19:30", "end_time": "20:30", "hetus_code": "821",
        "primary_activity": "sitting", "domain": "leisure", "purpose": "watch TV",
        "specific_location": home_name, "location_type": "home",
        "indoor_outdoor": "indoor", "social_context": "with_partner"})
    
    pebbles.append({"start_time": "20:30", "end_time": "21:30", "hetus_code": "721",
        "primary_activity": "sitting", "domain": "leisure", "purpose": "computer use",
        "specific_location": home_name, "location_type": "home",
        "indoor_outdoor": "indoor", "social_context": "alone"})
    
    return pebbles


# ──────────────────────────────────────────────────────────────────────
# Full Jar of Life Pipeline
# ──────────────────────────────────────────────────────────────────────

def generate_jar_of_life(
    persona: dict,
    day_of_week: str = "Monday",
    month: str = "april",
    seed: int = 42,
    include_sand: bool = True,
) -> dict:
    """
    Full Jar of Life diary generation.
    
    Steps:
    1. Generate backstory (day context)
    2. Pick real locations from OSM
    3. Place rocks (fixed anchors)
    4. Place pebbles (variable episodes, backstory-influenced)
    5. Fill gaps with sand (micro-moments)
    6. Return complete diary
    """
    
    # Step 1: Backstory
    backstory = generate_backstory(persona, day_of_week, month, seed=seed)
    
    # Step 2: OSM locations
    locations = pick_locations_from_osm(backstory, seed=seed)
    
    # Step 3: Rocks
    rocks = place_rocks(backstory, locations)
    
    # Step 4: Pebbles
    pebbles = place_pebbles(backstory, locations, seed=seed)
    
    # Combine rocks + pebbles
    all_episodes = rocks + pebbles
    
    # Fill common fields
    for ep in all_episodes:
        ep.setdefault("indoor_outdoor", "indoor")
        ep.setdefault("social_context", "alone")
        ep.setdefault("social_detail", "")
        ep.setdefault("affect_valence", "neutral")
        ep.setdefault("fatigue", backstory.fatigue_modifier())
        ep.setdefault("narrative", "")
    
    # Sort by start time
    all_episodes.sort(key=lambda e: e.get("start_time", "00:00"))
    
    # Temporal reconciliation: fix gaps and overlaps
    for i in range(1, len(all_episodes)):
        prev = all_episodes[i-1]
        curr = all_episodes[i]
        
        ph, pm = map(int, prev["end_time"].split(":"))
        ch, cm = map(int, curr["start_time"].split(":"))
        prev_end_min = ph * 60 + pm
        curr_start_min = ch * 60 + cm
        
        if curr_start_min < prev_end_min:
            # Overlap: extend previous to start of current
            prev["end_time"] = curr["start_time"]
        elif curr_start_min > prev_end_min + 1:
            # Gap > 1 min: extend previous to fill (unless it's sleep)
            if prev.get("hetus_code") != "011" and curr.get("hetus_code") != "011":
                prev["end_time"] = curr["start_time"]
    
    # Fill missing fields on all episodes before sand
    for ep in all_episodes:
        if not ep.get("indoor_outdoor"):
            ep["indoor_outdoor"] = "indoor" if ep.get("primary_activity") in ["sitting","lying","standing"] else "outdoor"
        if not ep.get("social_context"):
            ep["social_context"] = "alone"
        if not ep.get("social_detail"):
            ep["social_detail"] = ""
        if not ep.get("affect_valence"):
            ep["affect_valence"] = backstory.mood_baseline if backstory.mood_baseline != "slightly_low" else "neutral"
        if not ep.get("fatigue"):
            ep["fatigue"] = backstory.fatigue_modifier()
        if not ep.get("narrative"):
            ep["narrative"] = ep.get("purpose", "activity").replace("_", " ").capitalize() + "."
        if "is_sand" not in ep:
            ep["is_sand"] = False
    
    # Step 5: Sand
    if include_sand:
        all_episodes = fill_gaps_with_sand(all_episodes, max_sand_per_gap=2, seed=seed)
        # Fill sand fields too
        for ep in all_episodes:
            if ep.get("is_sand"):
                ep.setdefault("affect_valence", "neutral")
                ep.setdefault("fatigue", backstory.fatigue_modifier())
                ep.setdefault("social_detail", "")
                ep["narrative"] = ep.get("purpose", "").capitalize() + "."
    
    # Build diary
    diary = {
        "day_of_week": day_of_week,
        "backstory": backstory.backstory_narrative,
        "day_archetype": backstory.day_archetype,
        "weather": f"{backstory.weather}, {backstory.temperature_c}°C",
        "episodes": all_episodes,
        "device_wear_schedule": [
            {"start": "07:00", "end": "07:15", "status": "not_worn", "reason": "charging"},
            {"start": "07:15", "end": "07:30", "status": "not_worn", "reason": "shower"},
            {"start": "07:30", "end": "22:00", "status": "worn", "reason": "continuous"},
            {"start": "22:00", "end": "22:15", "status": "not_worn", "reason": "evening shower"},
        ],
        "daily_narrative": "",
        "is_typical_day": backstory.day_archetype in ["normal_grind", "relaxed"],
        "anomalies": [],
        "locations_used": {k: v.get("name", "") for k, v in locations.items()},
    }
    
    return diary


if __name__ == "__main__":
    persona = {"name": "Erik Hansen", "age": 32, "occupation": "Software Developer",
               "city": "Trondheim", "commute_mode": "bicycle"}
    
    print("=== JAR OF LIFE TEST ===\n", flush=True)
    
    for seed in [42, 7, 99]:
        diary = generate_jar_of_life(persona, "Monday", "april", seed=seed)
        eps = diary["episodes"]
        rocks, pebbles = count_rocks_and_pebbles(eps)
        sand = count_sand(eps)
        
        print(f"Seed {seed}: {diary['day_archetype']} | {diary['weather']}", flush=True)
        print(f"  Backstory: {diary['backstory'][:100]}...", flush=True)
        print(f"  Episodes: {len(eps)} ({rocks} rocks, {pebbles} pebbles, {sand} sand)", flush=True)
        print(f"  Locations: {diary['locations_used']}", flush=True)
        print(f"  Day: {eps[0]['start_time']} -> {eps[-1]['end_time']}", flush=True)
        
        # Show timeline
        for ep in eps[:8]:
            marker = "[SAND]" if ep.get("is_sand") else "      "
            print(f"    {ep['start_time']}-{ep['end_time']} {marker} {ep['purpose'][:35]}", flush=True)
        if len(eps) > 8:
            print(f"    ... ({len(eps)-8} more episodes)", flush=True)
        print(flush=True)
