#!/usr/bin/env python3
"""
Jar of Life — LLM-Driven Diary Generation.
Run this on the machine where llama.cpp server is accessible (port 8022).

Usage:
    python3 run_jar_of_life.py
    
Output: jar_of_life_output.json
"""

import json
import sys
import os
import random
import time
from urllib.request import Request, urlopen

# ──────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────

LLM_URL = "http://127.0.0.1:8022"
DB_PATH = os.path.join(os.path.dirname(__file__), "osm", "trondheim_osm.db")

def call_llm(system, user, max_tokens=4096):
    """Call the local LLM."""
    # Discover model
    req = Request(f"{LLM_URL}/v1/models", method="GET")
    with urlopen(req, timeout=10) as resp:
        model = json.loads(resp.read().decode())["data"][0]["id"]
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "top_p": 0.8,
        "top_k": 20,
    }
    
    req = Request(f"{LLM_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST")
    
    with urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]


def parse_json(text):
    """Extract JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
    # Strip preamble
    brace = text.find("{")
    bracket = text.find("[")
    if brace >= 0 and (bracket < 0 or brace < bracket):
        end = text.rfind("}")
        if end > brace:
            try: return json.loads(text[brace:end+1])
            except: pass
    if bracket >= 0:
        end = text.rfind("]")
        if end > bracket:
            try: return json.loads(text[bracket:end+1])
            except: pass
    return None


def query_osm(category, lat=None, lon=None, radius_km=2.0, limit=5, named_only=True):
    """Query the OSM database."""
    import sqlite3, math
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM pois WHERE category = ?", (category,))
    if c.fetchone()[0] > 0:
        where = "category = ?"
    else:
        where = "subcategory = ?"
    
    params = [category]
    if named_only:
        where += " AND name != ''"
    
    c.execute(f"SELECT name, lat, lon, category, subcategory FROM pois WHERE {where}", params)
    rows = c.fetchall()
    conn.close()
    
    results = []
    for name, plat, plon, cat, subcat in rows:
        if lat and lon:
            # Haversine
            R = 6371
            dlat = math.radians(plat - lat)
            dlon = math.radians(plon - lon)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(plat)) * math.sin(dlon/2)**2
            dist = R * 2 * math.asin(math.sqrt(a))
            if dist > radius_km:
                continue
            results.append({"name": name, "lat": plat, "lon": plon, "category": cat, "subcategory": subcat, "distance_km": round(dist, 2)})
        else:
            results.append({"name": name, "lat": plat, "lon": plon, "category": cat, "subcategory": subcat})
    
    if lat and lon:
        results.sort(key=lambda x: x.get("distance_km", 999))
    
    return results[:limit]


# ──────────────────────────────────────────────────────────────────────
# City Context
# ──────────────────────────────────────────────────────────────────────

CITY_CONTEXT = """CITY: Trondheim, Norway (63.43°N, 10.40°E)
TERRAIN: Hilly coastal city along the Trondheimsfjord. City center flat along Nidelva river.
Residential areas climb hillsides (Tyholt, Byåsen). Main bike corridors (Elgeseter gate,
Klostergata, Høgskoleringen) are flat. Residential hills challenging.

KEY LOCATIONS: NTNU Gløshaugen campus, Byparken park, Nidelva river, Trondheimsfjord,
Ladestien coastal path, Bakklandet neighborhood, Solsiden waterfront, Kristiansten fortress.

MONTH: April, Spring. Avg 5°C, 40mm rain, 15h daylight. No snow.
Cycling feasible. Hiking resumes. Running increases. Beach swimming not yet (water too cold)."""

# ──────────────────────────────────────────────────────────────────────
# Few-Shot Examples
# ──────────────────────────────────────────────────────────────────────

EXAMPLES = """
EXAMPLE BACKSTORY:
{"sleep_quality":"okay","sleep_hours":6.5,"wake_feeling":"slightly groggy",
"energy_level":"moderate","mood_baseline":"neutral",
"mood_narrative":"Steady mood, nothing special","day_archetype":"normal_grind",
"weather":"cloudy","temperature_c":8,"has_big_event":false,"has_social_plan":true,
"social_description":"dinner with Marie's friends tonight",
"physical_carryover":"legs slightly sore from yesterday's run",
"backstory_narrative":"Monday morning. Sleep okay — 6.5h. Social dinner tonight. Legs sore from yesterday's run. Cloudy 8°C."}

EXAMPLE EPISODE:
{"start_time":"08:05","end_time":"08:25","hetus_code":"910","primary_activity":"cycling",
"domain":"transport","purpose":"commute to work via Elgeseter gate",
"specific_location":"Elgeseter gate bike lane","location_type":"street",
"indoor_outdoor":"outdoor","social_context":"alone","social_detail":"",
"affect_valence":"positive","fatigue":"low",
"narrative":"Cycles down Elgeseter gate. Cherry blossoms blooming. Light traffic."}

HETUS CODES (use ONLY these):
011 Sleep|021 Eat|031 Wash|111 Work|121 Lunch|311 Cook|321 Clean|361 Shop
511 Social|531 Rest|611 Walk(ex)|612 Run|613 Cycle(ex)|615 Gym
721 Computer|812 Read|821 TV|910 TravelWork|936 TravelShop|960 TravelLeisure
"""

# ──────────────────────────────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 60, flush=True)
    print("JAR OF LIFE — LLM-Driven Diary Generation", flush=True)
    print("=" * 60, flush=True)
    
    persona = {
        "name": "Erik Hansen", "age": 32, "gender": "male",
        "occupation": "Software Developer", "city": "Trondheim",
        "living_situation": "Lives with partner Marie",
        "has_bike": True, "fitness_level": "moderate",
        "commute_mode": "bicycle", "commute_duration_min": 18,
        "hobbies": ["cycling", "gym", "hiking"],
    }
    
    # Step 1: Pick real locations
    print("\n1. Picking real locations from OSM...", flush=True)
    NTNU_LAT, NTNU_LON = 63.4246, 10.3932
    rng = random.Random(42)
    
    locations = {}
    homes = query_osm("residential", NTNU_LAT, NTNU_LON, 1.5, 10)
    locations["home"] = rng.choice(homes[:5]) if homes else {"name":"Singsaker","lat":63.428,"lon":10.395}
    
    works = query_osm("university", NTNU_LAT, NTNU_LON, 3.0, 5)
    locations["work"] = rng.choice(works[:3]) if works else {"name":"NTNU","lat":NTNU_LAT,"lon":NTNU_LON}
    
    gyms = query_osm("gym", NTNU_LAT, NTNU_LON, 3.0, 5)
    if gyms: locations["gym"] = rng.choice(gyms[:3])
    
    cafes = query_osm("cafe", NTNU_LAT, NTNU_LON, 0.8, 5)
    locations["cafe"] = rng.choice(cafes[:3]) if cafes else {"name":"Dromedar","lat":63.425,"lon":10.393}
    
    parks = query_osm("park", NTNU_LAT, NTNU_LON, 2.0, 5)
    locations["park"] = rng.choice(parks[:3]) if parks else {"name":"Byparken","lat":63.431,"lon":10.395}
    
    markets = query_osm("supermarket", locations["home"]["lat"], locations["home"]["lon"], 1.0, 3)
    if markets: locations["supermarket"] = markets[0]
    
    loc_str = "\n".join(f"  {k}: {v.get('name','?')} ({v.get('lat',0):.4f}, {v.get('lon',0):.4f})"
                        for k, v in locations.items())
    print(f"   Locations:\n{loc_str}", flush=True)
    
    # Step 2: LLM generates backstory
    print("\n2. Generating backstory (LLM)...", flush=True)
    time.sleep(2)
    
    backstory = call_llm(
        "You generate a day backstory for a synthetic diary. Output ONLY valid JSON.",
        f"Persona: {json.dumps(persona)}\nDay: Monday, Month: April\nCity: {CITY_CONTEXT[:300]}\n\n"
        f"Generate backstory with: sleep_quality, sleep_hours, wake_feeling, energy_level, "
        f"mood_baseline, mood_narrative, day_archetype, weather, temperature_c, "
        f"has_big_event(bool), big_event_description, has_social_plan(bool), social_description, "
        f"physical_carryover, backstory_narrative.\n\n{EXAMPLES[:400]}",
        max_tokens=1024
    )
    
    backstory_obj = parse_json(backstory)
    if backstory_obj:
        print(f"   Archetype: {backstory_obj.get('day_archetype','?')}", flush=True)
        print(f"   Sleep: {backstory_obj.get('sleep_quality','?')} ({backstory_obj.get('sleep_hours','?')}h)", flush=True)
        print(f"   Weather: {backstory_obj.get('weather','?')}, {backstory_obj.get('temperature_c','?')}°C", flush=True)
        print(f"   Narrative: {str(backstory_obj.get('backstory_narrative',''))[:100]}...", flush=True)
    else:
        print("   [WARN] Backstory parse failed, using fallback", flush=True)
        backstory_obj = {"day_archetype":"normal_grind","weather":"cloudy","temperature_c":8,
                        "mood_baseline":"neutral","energy_level":"moderate","sleep_quality":"okay",
                        "sleep_hours":7,"wake_feeling":"okay","backstory_narrative":"Normal Monday."}
    
    # Step 3: LLM generates episodes
    print("\n3. Generating episodes (LLM)...", flush=True)
    time.sleep(2)
    
    episodes_text = call_llm(
        f"You generate a Monday diary. Output ONLY a JSON array of episodes.\n\n{EXAMPLES}\n\n"
        f"RULES: 15-22 episodes covering 07:00-23:00. NO gaps >3min. "
        f"All fields from example. Use REAL locations. Fatigue increases through day. "
        f"Narratives 1-2 sentences with Trondheim street names.",
        f"Persona: {persona['name']}, {persona['age']}, {persona['occupation']}\n\n"
        f"BACKSTORY:\n{json.dumps(backstory_obj, indent=2)}\n\n"
        f"REAL LOCATIONS:\n{loc_str}\n\n"
        f"CITY:\n{CITY_CONTEXT[:500]}\n\n"
        f"Generate the full Monday as a JSON array of episode objects.",
        max_tokens=4096
    )
    
    episodes = parse_json(episodes_text)
    if episodes and isinstance(episodes, list):
        print(f"   Episodes: {len(episodes)}", flush=True)
        for ep in episodes[:5]:
            print(f"     {ep.get('start_time','?')}-{ep.get('end_time','?')} {ep.get('hetus_code','')} {ep.get('purpose','')[:35]}", flush=True)
        if len(episodes) > 5:
            print(f"     ... ({len(episodes)-5} more)", flush=True)
    else:
        print("   [FAIL] Episode generation failed", flush=True)
        print(f"   Raw: {episodes_text[:200]}", flush=True)
        episodes = []
    
    # Step 4: Fill required fields + temporal reconciliation
    print("\n4. Reconciling timeline...", flush=True)
    
    for ep in episodes:
        if not ep.get("indoor_outdoor"):
            ep["indoor_outdoor"] = "indoor" if ep.get("primary_activity") in ["sitting","lying","standing"] else "outdoor"
        if not ep.get("social_context"): ep["social_context"] = "alone"
        if not ep.get("social_detail"): ep["social_detail"] = ""
        if not ep.get("affect_valence"): ep["affect_valence"] = backstory_obj.get("mood_baseline", "neutral")
        if not ep.get("fatigue"): ep["fatigue"] = "mild"
        if not ep.get("narrative"): ep["narrative"] = ep.get("purpose","") + "."
        ep["is_sand"] = False
    
    # Sort and fix gaps
    episodes.sort(key=lambda e: e.get("start_time", "00:00"))
    for i in range(1, len(episodes)):
        ph, pm = map(int, episodes[i-1]["end_time"].split(":"))
        ch, cm = map(int, episodes[i]["start_time"].split(":"))
        prev_end = ph * 60 + pm
        curr_start = ch * 60 + cm
        if curr_start < prev_end:
            episodes[i-1]["end_time"] = episodes[i]["start_time"]
        elif curr_start > prev_end + 1 and episodes[i-1].get("hetus_code") != "011":
            episodes[i-1]["end_time"] = episodes[i]["start_time"]
    
    # Step 5: Build diary
    diary = {
        "day_of_week": "Monday",
        "backstory": backstory_obj.get("backstory_narrative", ""),
        "day_archetype": backstory_obj.get("day_archetype", ""),
        "weather": f"{backstory_obj.get('weather','')}, {backstory_obj.get('temperature_c','')}°C",
        "episodes": episodes,
        "device_wear_schedule": [
            {"start":"07:00","end":"07:30","status":"not_worn","reason":"shower"},
            {"start":"07:30","end":"22:00","status":"worn","reason":"continuous"},
        ],
        "locations_used": {k: v.get("name","") for k, v in locations.items()},
    }
    
    # Step 6: QA (basic checks)
    print("\n5. QA checks...", flush=True)
    non_sand = [ep for ep in episodes if not ep.get("is_sand")]
    
    req = ["start_time","end_time","primary_activity","domain","purpose","specific_location","hetus_code","narrative"]
    comp = sum(1 for ep in non_sand if all(ep.get(f) for f in req))
    print(f"   Completeness: {comp}/{len(non_sand)}", flush=True)
    
    # Temporal
    gaps = 0
    for i in range(1, len(non_sand)):
        ph,pm = map(int, non_sand[i-1]["end_time"].split(":"))
        ch,cm = map(int, non_sand[i]["start_time"].split(":"))
        diff = (ch*60+cm)-(ph*60+pm)
        if diff > 5: gaps += 1
    print(f"   Temporal gaps >5min: {gaps}", flush=True)
    
    domains = set(ep.get("domain","") for ep in non_sand)
    activities = set(ep.get("primary_activity","") for ep in non_sand)
    hetus = set(ep.get("hetus_code","") for ep in non_sand)
    print(f"   Domains: {domains}", flush=True)
    print(f"   Activities: {activities}", flush=True)
    print(f"   HETUS codes: {sorted(hetus)}", flush=True)
    
    # Save
    with open("jar_of_life_output.json", "w") as f:
        json.dump(diary, f, indent=2, default=str)
    
    print(f"\nSaved to jar_of_life_output.json", flush=True)
    print(f"Episodes: {len(episodes)}", flush=True)
    print("DONE!", flush=True)


if __name__ == "__main__":
    run()
