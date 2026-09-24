"""
Jar of Life — LLM-Driven Diary Generation with XML Output.

Uses XML tags (<json></json>) for reliable JSON extraction from
reasoning-enabled LLMs. The model thinks freely outside the tags
and puts structured data inside them.

Architecture:
- LLM generates all content (backstory, episodes, narratives)
- Programmatic code: OSM locations, temporal reconciliation, QA validation
- XML tags solve JSON corruption from thinking text
"""

import json
import re
import sys
import os
import random
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from urllib.request import Request, urlopen
from osm.query_tools import query_pois
from modules.ema_generator import generate_ema_probes
from evaluation.qa_validator import validate_diary


# ──────────────────────────────────────────────────────────────────────
# LLM Client (XML-based output)
# ──────────────────────────────────────────────────────────────────────

LLM_URL = "http://127.0.0.1:8022"


def call_llm(system: str, user: str, max_tokens: int = 4096) -> str:
    """Call the local LLM. Returns content only (ignores reasoning_content)."""
    # Get model name
    try:
        req = Request(f"{LLM_URL}/v1/models", method="GET")
        with urlopen(req, timeout=10) as resp:
            model = json.loads(resp.read().decode())["data"][0]["id"]
    except Exception as e:
        raise ConnectionError(f"LLM server not reachable at {LLM_URL}: {e}")

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

    req = Request(
        f"{LLM_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=300) as resp:
        msg = json.loads(resp.read().decode())["choices"][0]["message"]
        return msg.get("content", "")


def extract_json(text: str):
    """Extract JSON from LLM response. Handles <json></json> tags and markdown fences."""
    # Try <json></json> tags first (XML approach)
    m = re.search(r"<json>(.*?)</json>", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except:
            # Try adding closing brackets
            for suffix in ["</json>", "]", "}"]:
                try:
                    return json.loads(m.group(1) + suffix)
                except:
                    pass

    # Fallback: strip markdown fences and find JSON
    text = re.sub(r"```json\s*", "", text).replace("```", "")

    for start_char, end_char in [("{", "}"), ("[", "]")]:
        idx = text.find(start_char)
        if idx >= 0:
            depth = 0
            for i in range(idx, len(text)):
                if text[i] == start_char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[idx : i + 1])
                    except:
                        break

    return None


# ──────────────────────────────────────────────────────────────────────
# OSM Location Picker
# ──────────────────────────────────────────────────────────────────────

def pick_locations(seed: int = 42) -> dict:
    """Pick real Trondheim locations from OSM database."""
    rng = random.Random(seed)
    NTNU_LAT, NTNU_LON = 63.4246, 10.3932
    locs = {}

    for cat in ["residential", "university", "gym", "cafe", "park"]:
        role = {"residential": "home", "university": "work", "gym": "gym", "cafe": "cafe", "park": "park"}[cat]
        r = query_pois(cat, NTNU_LAT, NTNU_LON, 1.5 if cat == "residential" else 2.0, 5, named_only=(cat != "residential"))
        locs[role] = rng.choice(r[:5]) if r else {"name": role, "lat": 63.43, "lon": 10.4}

    m = query_pois("supermarket", locs["home"]["lat"], locs["home"]["lon"], 1.0, 3, named_only=True)
    if m:
        locs["supermarket"] = m[0]

    return locs


# ──────────────────────────────────────────────────────────────────────
# Generation Steps
# ──────────────────────────────────────────────────────────────────────

def generate_backstory(city_context: str = "") -> dict:
    """LLM generates day backstory."""
    text = call_llm(
        "Output JSON inside <json></json> tags.",
        "Monday backstory for Erik, 32, developer, Trondheim. April, spring. "
        "JSON: sleep_quality,sleep_hours,wake_feeling,energy_level(1-10),mood_baseline,"
        "mood_narrative,day_archetype(normal_grind/deadline_pressure/relaxed/social_heavy),"
        "weather,temperature_c,has_big_event(bool),big_event_description,"
        "has_social_plan(bool),social_description,physical_carryover,backstory_narrative. <json>",
        max_tokens=2048,
    )

    result = extract_json(text)
    if result:
        return result

    # Fallback
    return {
        "day_archetype": "normal_grind", "weather": "partly cloudy", "temperature_c": 7,
        "mood_baseline": "neutral", "energy_level": 5, "sleep_quality": "okay", "sleep_hours": 7,
        "wake_feeling": "okay", "has_big_event": False, "big_event_description": "",
        "has_social_plan": False, "social_description": "", "physical_carryover": "none",
        "backstory_narrative": "Normal Monday in April.",
    }


def generate_episodes(backstory: dict, locations: dict) -> list[dict]:
    """LLM generates diary episodes using XML output."""
    loc_str = " | ".join(f"{k}: {v.get('name', '?')}" for k, v in locations.items())

    text = call_llm(
        "Output ONLY JSON array inside <json></json>. No text.",
        f"20 episodes for Monday diary. Erik, developer, Trondheim.\n"
        f"Backstory: {json.dumps(backstory)[:250]}\n"
        f"Locations: {loc_str}\n\n"
        f"Fields: start_time,end_time,hetus_code,primary_activity,domain,purpose,"
        f"specific_location,location_type,indoor_outdoor,social_context,social_detail,"
        f"affect_valence,fatigue,narrative\n\n"
        f"CRITICAL:\n"
        f"- primary_activity: sitting,standing,walking,running,cycling,lying ONLY\n"
        f"- domain: self_care,work,transport,exercise,household,social,leisure ONLY\n"
        f"- fatigue MUST INCREASE: morning=low, midday=mild, afternoon=moderate, evening=high\n"
        f"- HETUS: 011(sleep),021(eat),031(wash),111(work),311(cook),361(shop),"
        f"611(walk),615(gym),721(computer),821(TV),910(cycling)\n"
        f"- Cover 07:00-23:00, NO gaps >3min\n"
        f"- Narratives 1-2 sentences with Trondheim street names\n<json>",
        max_tokens=8192,
    )

    result = extract_json(text)
    if result and isinstance(result, list):
        return result
    return []


def generate_sand_grains(episodes: list[dict]) -> list[dict]:
    """LLM generates micro-moments (sand) for gaps > 5 min."""
    # Find gaps
    gaps = []
    sorted_eps = sorted(episodes, key=lambda e: e.get("start_time", "00:00"))
    for i in range(1, len(sorted_eps)):
        ph, pm = map(int, sorted_eps[i - 1]["end_time"].split(":"))
        ch, cm = map(int, sorted_eps[i]["start_time"].split(":"))
        gap = (ch * 60 + cm) - (ph * 60 + pm)
        if gap >= 5:
            gaps.append({
                "after": sorted_eps[i - 1].get("purpose", ""),
                "before": sorted_eps[i].get("purpose", ""),
                "location": sorted_eps[i - 1].get("specific_location", ""),
                "start": sorted_eps[i - 1]["end_time"],
                "end": sorted_eps[i]["start_time"],
            })

    if not gaps:
        return []

    text = call_llm(
        "Output JSON array inside <json></json>. Sand grains = micro-moments (2-8 min).",
        f"Fill gaps with 1-2 micro-moments each.\n"
        f"Gaps: {json.dumps(gaps)[:500]}\n\n"
        f"Each grain: start_time,end_time,hetus_code(039),primary_activity(sitting/standing/walking),"
        f"domain(self_care),purpose,specific_location,location_type,indoor_outdoor,social_context(alone),"
        f"social_detail,affect_valence(neutral),fatigue,micro_narrative\n<json>",
        max_tokens=2048,
    )

    result = extract_json(text)
    if result and isinstance(result, list):
        for ep in result:
            ep["is_sand"] = True
        return result
    return []


# ──────────────────────────────────────────────────────────────────────
# Post-Processing
# ──────────────────────────────────────────────────────────────────────

def enforce_fatigue(episodes: list[dict]) -> list[dict]:
    """Force fatigue to increase through the day."""
    for ep in episodes:
        sh, _ = map(int, ep.get("start_time", "00:00").split(":"))
        if sh < 9:
            ep["fatigue"] = "low"
        elif sh < 12:
            ep["fatigue"] = "mild"
        elif sh < 16:
            ep["fatigue"] = "moderate"
        else:
            ep["fatigue"] = "high"
    return episodes


def fill_fields(episodes: list[dict], backstory: dict) -> list[dict]:
    """Ensure all episodes have required fields."""
    for ep in episodes:
        if not ep.get("indoor_outdoor"):
            ep["indoor_outdoor"] = "indoor" if ep.get("primary_activity") in ["sitting", "lying", "standing"] else "outdoor"
        if not ep.get("social_context"):
            ep["social_context"] = "alone"
        if not ep.get("social_detail"):
            ep["social_detail"] = ""
        if not ep.get("affect_valence"):
            ep["affect_valence"] = backstory.get("mood_baseline", "neutral")
        if not ep.get("fatigue"):
            ep["fatigue"] = "moderate"
        if not ep.get("narrative"):
            ep["narrative"] = ep.get("purpose", "activity") + "."
        if "is_sand" not in ep:
            ep["is_sand"] = False
    return episodes


def reconcile_timeline(episodes: list[dict]) -> list[dict]:
    """Fix gaps and overlaps."""
    if len(episodes) < 2:
        return episodes

    episodes.sort(key=lambda e: e.get("start_time", "00:00"))
    for i in range(1, len(episodes)):
        ph, pm = map(int, episodes[i - 1]["end_time"].split(":"))
        ch, cm = map(int, episodes[i]["start_time"].split(":"))
        prev_end = ph * 60 + pm
        curr_start = ch * 60 + cm

        if curr_start < prev_end:
            episodes[i - 1]["end_time"] = episodes[i]["start_time"]
        elif curr_start > prev_end + 1 and episodes[i - 1].get("hetus_code") != "011":
            episodes[i - 1]["end_time"] = episodes[i]["start_time"]

    return episodes


# ──────────────────────────────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────────────────────────────

def generate_jar_of_life(
    persona: dict,
    day_of_week: str = "Monday",
    month: str = "april",
    seed: int = 42,
) -> dict:
    """
    Full LLM-driven Jar of Life diary generation.
    
    Returns a complete diary dict with:
    - backstory (day context from LLM)
    - episodes (20+ from LLM, grounded in real OSM locations)
    - ema_probes (programmatic with recall bias)
    - qa_validation (7 metrics)
    """
    
    print("  1. Backstory (LLM)...", flush=True)
    backstory = generate_backstory()
    print(f"     {backstory.get('day_archetype', '?')} | {backstory.get('weather', '?')}", flush=True)
    time.sleep(2)

    print("  2. Locations (OSM)...", flush=True)
    locations = pick_locations(seed)
    loc_str = " | ".join(f"{k}: {v.get('name', '?')}" for k, v in locations.items())
    print(f"     {loc_str}", flush=True)

    print("  3. Episodes (LLM)...", flush=True)
    episodes = generate_episodes(backstory, locations)
    print(f"     {len(episodes)} episodes", flush=True)
    time.sleep(2)

    print("  4. Sand grains (LLM)...", flush=True)
    sand = generate_sand_grains(episodes) if episodes else []
    print(f"     {len(sand)} sand grains", flush=True)
    time.sleep(2)

    # Combine + process
    all_episodes = episodes + sand
    all_episodes = enforce_fatigue(all_episodes)
    all_episodes = fill_fields(all_episodes, backstory)
    all_episodes = reconcile_timeline(all_episodes)
    all_episodes.sort(key=lambda e: e.get("start_time", "00:00"))

    # Build diary
    diary = {
        "day_of_week": day_of_week,
        "backstory": backstory.get("backstory_narrative", ""),
        "day_archetype": backstory.get("day_archetype", ""),
        "weather": f"{backstory.get('weather', '')}, {backstory.get('temperature_c', '')}°C",
        "episodes": all_episodes,
        "device_wear_schedule": [
            {"start": "07:00", "end": "07:30", "status": "not_worn", "reason": "shower"},
            {"start": "07:30", "end": "22:00", "status": "worn", "reason": "continuous"},
            {"start": "22:00", "end": "22:15", "status": "not_worn", "reason": "evening shower"},
        ],
        "daily_narrative": "",
        "is_typical_day": backstory.get("day_archetype", "") in ["normal_grind", "relaxed"],
        "anomalies": [],
        "locations_used": {k: v.get("name", "") for k, v in locations.items()},
    }

    return diary


# ──────────────────────────────────────────────────────────────────────
# CLI Test
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    persona = {
        "name": "Erik Hansen", "age": 32, "gender": "male",
        "occupation": "Software Developer", "city": "Trondheim",
        "has_bike": True, "fitness_level": "moderate",
    }

    print("=== JAR OF LIFE: LLM + XML ===\n", flush=True)

    diary = generate_jar_of_life(persona, "Monday", "april", seed=42)

    eps = diary["episodes"]
    non_sand = [ep for ep in eps if not ep.get("is_sand")]
    sand = sum(1 for ep in eps if ep.get("is_sand"))

    print(f"\n  Episodes: {len(eps)} ({len(non_sand)} main + {sand} sand)", flush=True)

    # EMA + QA
    ema = generate_ema_probes(diary, seed=42)
    validation = validate_diary(diary, ema)

    print(f"\n  QA: {validation['overall_score']:.3f}", flush=True)
    for metric, data in validation.items():
        if metric == "overall_score":
            continue
        s = data.get("score", 0)
        n = len(data.get("issues", []))
        if n > 0:
            st = "PASS" if s >= 0.85 else "FAIL"
            print(f"    {st} {metric}: {s:.3f} ({n})", flush=True)

    # Save
    output = {
        "backstory": diary.get("backstory"),
        "diary": diary,
        "ema_probes": ema,
        "validation": validation,
    }
    with open("output/jar_of_life_llm_output.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n  Saved!", flush=True)
