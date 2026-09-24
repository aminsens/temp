"""
Jar of Life — Staged Pipeline (Rocks → Pebbles → Sand).

Mirrors how a real day unfolds:
1. ROCKS: Fixed anchors placed first (work, commute, sleep, meals)
2. PEBBLES: Variable activities fill some gaps (gym, social, shopping)
3. SAND: Micro-moments fill remaining gaps (check phone, stretch, get water)

Each stage builds on the previous, creating causal texture:
- Sand sees what rocks and pebbles just did
- Narratives can reference previous events
- Emotional arc emerges naturally

Architecture:
- Stage 1: Backstory (LLM) + Locations (OSM) — parallel
- Stage 2: Rocks (LLM) — 8-10 major episodes, leaves gaps
- Stage 3: Pebbles (LLM) — sees rocks, fills some gaps
- Stage 4: Sand (LLM) — sees rocks+pebbles, fills remaining gaps
- Stage 5: QA — programmatic validation
"""

import json
import re
import sys
import os
import random
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from urllib.request import Request, urlopen
from osm.query_tools import query_pois
from modules.ema_generator import generate_ema_probes
from evaluation.qa_validator import validate_diary

LLM_URL = "http://127.0.0.1:8022"


# ──────────────────────────────────────────────────────────────────────
# LLM + Parsing
# ──────────────────────────────────────────────────────────────────────

def call_llm(system: str, user: str, max_tokens: int = 4096) -> str:
    """Call LLM. Returns content only."""
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
        headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"].get("content", "")


def extract_json(text: str):
    """Extract JSON from LLM response using XML tags or bracket matching."""
    # Try <json></json> tags
    m = re.search(r"<json>(.*?)</json>", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except:
            for suffix in ["]", "}"]:
                try:
                    return json.loads(m.group(1) + suffix)
                except:
                    pass

    # Fallback: bracket matching
    text = re.sub(r"```json\s*", "", text).replace("```", "")
    for start, end in [("[", "]"), ("{", "}")]:
        idx = text.find(start)
        if idx >= 0:
            depth = 0
            for i in range(idx, len(text)):
                if text[i] == start:
                    depth += 1
                elif text[i] == end:
                    depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[idx : i + 1])
                    except:
                        break
    return None


def find_gaps(episodes: list[dict]) -> list[dict]:
    """Find gaps between episodes that need filling."""
    if len(episodes) < 2:
        return []

    sorted_eps = sorted(episodes, key=lambda e: e.get("start_time", "00:00"))
    gaps = []

    for i in range(1, len(sorted_eps)):
        ph, pm = map(int, sorted_eps[i - 1]["end_time"].split(":"))
        ch, cm = map(int, sorted_eps[i]["start_time"].split(":"))
        gap_min = (ch * 60 + cm) - (ph * 60 + pm)

        if gap_min >= 3:
            gaps.append({
                "index": i,
                "start": sorted_eps[i - 1]["end_time"],
                "end": sorted_eps[i]["start_time"],
                "gap_min": gap_min,
                "after_purpose": sorted_eps[i - 1].get("purpose", ""),
                "after_location": sorted_eps[i - 1].get("specific_location", ""),
                "before_purpose": sorted_eps[i].get("purpose", ""),
                "before_location": sorted_eps[i].get("specific_location", ""),
            })

    return gaps


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
# EPISODE FORMAT
# ──────────────────────────────────────────────────────────────────────

EPISODE_FIELDS = (
    "start_time,end_time,hetus_code,primary_activity(sitting/standing/walking/running/cycling/lying),"
    "domain(self_care/work/transport/exercise/household/social/leisure),purpose,specific_location,"
    "location_type,indoor_outdoor(indoor/outdoor),social_context(alone/with_partner/with_colleagues),"
    "social_detail,affect_valence(positive/neutral),fatigue(low/mild/moderate/high),narrative"
)

HETUS_GUIDE = (
    "HETUS: 011(sleep),021(eat),031(wash),111(work),311(cook),361(shop),"
    "611(walk),612(run),615(gym),721(computer),821(TV),910(cycling)"
)


# ──────────────────────────────────────────────────────────────────────
# STAGE 1: Backstory + Locations (parallel)
# ──────────────────────────────────────────────────────────────────────

def stage_backstory() -> dict:
    """LLM generates day backstory."""
    print("  Stage 1a: Backstory (LLM)...", flush=True)
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
        print(f"     {result.get('day_archetype', '?')} | {result.get('weather', '?')}", flush=True)
        return result

    print("     [FALLBACK] using defaults", flush=True)
    return {
        "day_archetype": "normal_grind", "weather": "partly cloudy", "temperature_c": 7,
        "mood_baseline": "neutral", "energy_level": 5, "sleep_quality": "okay", "sleep_hours": 7,
        "wake_feeling": "okay", "has_big_event": False, "big_event_description": "",
        "has_social_plan": False, "social_description": "", "physical_carryover": "none",
        "backstory_narrative": "Normal Monday in April.",
    }


def stage_locations(seed: int = 42) -> dict:
    """Pick real Trondheim locations from OSM."""
    print("  Stage 1b: Locations (OSM)...", flush=True)
    rng = random.Random(seed)
    NTNU_LAT, NTNU_LON = 63.4246, 10.3932
    locs = {}

    for cat in ["residential", "university", "gym", "cafe", "park"]:
        role = {"residential": "home", "university": "work", "gym": "gym",
                "cafe": "cafe", "park": "park"}[cat]
        r = query_pois(cat, NTNU_LAT, NTNU_LON,
                       1.5 if cat == "residential" else 2.0, 5,
                       named_only=(cat != "residential"))
        locs[role] = rng.choice(r[:5]) if r else {"name": role, "lat": 63.43, "lon": 10.4}

    m = query_pois("supermarket", locs["home"]["lat"], locs["home"]["lon"], 1.0, 3, named_only=True)
    if m:
        locs["supermarket"] = m[0]

    loc_str = " | ".join(f"{k}: {v.get('name', '?')}" for k, v in locs.items())
    print(f"     {loc_str}", flush=True)
    return locs


# ──────────────────────────────────────────────────────────────────────
# STAGE 2: Rocks (8-10 major episodes, leaves gaps)
# ──────────────────────────────────────────────────────────────────────

def stage_rocks(backstory: dict, locations: dict) -> list[dict]:
    """LLM generates ROCKS — the major anchors of the day. Leaves gaps for pebbles and sand."""
    print("  Stage 2: Rocks (LLM)...", flush=True)
    loc_str = " | ".join(f"{k}: {v.get('name', '?')}" for k, v in locations.items())

    text = call_llm(
        "Output JSON array inside <json></json>. No text.",
        f"Generate 10 ROCKS for Monday. Erik, developer, Trondheim.\n"
        f"Backstory: {json.dumps(backstory)[:200]}\n"
        f"Locations: {loc_str}\n\n"
        f"Rocks = MAJOR anchors only: wake up, commute, work block, lunch, commute, gym, dinner, sleep.\n"
        f"Cover 07:00-23:00 but leave GAPS of 15-45min between some rocks (e.g. between work and gym, between gym and dinner).\n"
        f"Generate 10 episodes. DO NOT fill every minute — leave room for intermediate activities.\n"
        f"Each: {EPISODE_FIELDS}\n"
        f"{HETUS_GUIDE}\n"
        f"fatigue: morning=low, midday=mild, afternoon=moderate, evening=high\n"
        f"Narratives 1-2 sentences with Trondheim details.\n<json>",
        max_tokens=4096,
    )

    result = extract_json(text)
    if result and isinstance(result, list):
        print(f"     {len(result)} rocks", flush=True)
        return result

    # Debug
    print(f"     [DEBUG] LLM returned {len(text)} chars", flush=True)
    if text:
        print(f"     [DEBUG] First 300: {text[:300]}", flush=True)

    # Fallback: generate rocks programmatically
    print("     [FALLBACK] generating rocks programmatically", flush=True)
    home = locations.get("home", {}).get("name", "home")
    work = locations.get("work", {}).get("name", "NTNU")
    gym = locations.get("gym", {}).get("name", "gym")
    cafe = locations.get("cafe", {}).get("name", "cafe")

    return [
        {"start_time":"07:00","end_time":"07:15","hetus_code":"011","primary_activity":"lying","domain":"self_care","purpose":"waking up","specific_location":home,"location_type":"home","narrative":"Woke up to the sound of rain on the window."},
        {"start_time":"07:15","end_time":"07:45","hetus_code":"031","primary_activity":"standing","domain":"self_care","purpose":"morning routine","specific_location":home,"location_type":"home","narrative":"Quick shower and got dressed for the day."},
        {"start_time":"07:45","end_time":"08:00","hetus_code":"910","primary_activity":"cycling","domain":"transport","purpose":"commute to work","specific_location":"Elgeseter gate","location_type":"street","narrative":"Cycled to work through the morning drizzle."},
        {"start_time":"08:00","end_time":"12:00","hetus_code":"111","primary_activity":"sitting","domain":"work","purpose":"morning work session","specific_location":work,"location_type":"work_office","narrative":"Deep focus on code. Standup at 10."},
        {"start_time":"12:00","end_time":"12:30","hetus_code":"021","primary_activity":"sitting","domain":"social","purpose":"lunch","specific_location":cafe,"location_type":"restaurant","narrative":"Lunch with colleagues at the cafe."},
        {"start_time":"12:30","end_time":"16:00","hetus_code":"111","primary_activity":"sitting","domain":"work","purpose":"afternoon work","specific_location":work,"location_type":"work_office","narrative":"Afternoon coding and meetings."},
        {"start_time":"16:00","end_time":"16:15","hetus_code":"910","primary_activity":"cycling","domain":"transport","purpose":"commute to gym","specific_location":"Høgskoleringen","location_type":"street","narrative":"Cycled to gym after work."},
        {"start_time":"16:15","end_time":"17:30","hetus_code":"615","primary_activity":"standing","domain":"exercise","purpose":"gym workout","specific_location":gym,"location_type":"gym","narrative":"Weight training session."},
        {"start_time":"17:30","end_time":"17:45","hetus_code":"910","primary_activity":"cycling","domain":"transport","purpose":"commute home","specific_location":"Klostergata","location_type":"street","narrative":"Cycled home, tired but satisfied."},
        {"start_time":"18:00","end_time":"19:00","hetus_code":"311","primary_activity":"standing","domain":"household","purpose":"cook dinner","specific_location":home,"location_type":"home","narrative":"Made pasta with vegetables."},
        {"start_time":"19:00","end_time":"22:00","hetus_code":"021","primary_activity":"sitting","domain":"leisure","purpose":"evening relaxation","specific_location":home,"location_type":"home","narrative":"Relaxed at home after a long day."},
        {"start_time":"22:00","end_time":"23:00","hetus_code":"011","primary_activity":"lying","domain":"self_care","purpose":"sleep","specific_location":home,"location_type":"home","narrative":"Fell asleep quickly."},
    ]


# ──────────────────────────────────────────────────────────────────────
# STAGE 3: Pebbles (fills some gaps, leaves room for sand)
# ──────────────────────────────────────────────────────────────────────

def stage_pebbles(rocks: list[dict], backstory: dict, locations: dict) -> list[dict]:
    """LLM generates PEBBLES — variable activities that fill some gaps between rocks."""
    print("  Stage 3: Pebbles (LLM)...", flush=True)

    gaps = find_gaps(rocks)
    if not gaps:
        print("     No gaps to fill", flush=True)
        return []

    # Only fill gaps >= 15 min with pebbles (leave gaps < 15 for sand)
    pebble_gaps = [g for g in gaps if g["gap_min"] >= 15]
    if not pebble_gaps:
        print("     No gaps >= 8min for pebbles", flush=True)
        return []

    loc_str = " | ".join(f"{k}: {v.get('name', '?')}" for k, v in locations.items())

    text = call_llm(
        "Output JSON array inside <json></json>. No text.",
        f"Fill gaps between major episodes with PEBBLES (variable activities).\n\n"
        f"Gaps to fill:\n{json.dumps(pebble_gaps, indent=2)[:800]}\n\n"
        f"Backstory: {json.dumps(backstory)[:150]}\n"
        f"Locations: {loc_str}\\n\\n"
        f"Generate 1 pebble per gap. Activities: coffee break, walk, quick shopping, chat.\n"
        f"Each: {EPISODE_FIELDS}\n"
        f"{HETUS_GUIDE}\n"
        f"fatigue: match time of day\n"
        f"Narratives reference what just happened or what's coming next.\n<json>",
        max_tokens=4096,
    )

    result = extract_json(text)
    if result and isinstance(result, list):
        print(f"     {len(result)} pebbles", flush=True)
        return result

    print("     [FALLBACK] no pebbles generated", flush=True)
    return []


# ──────────────────────────────────────────────────────────────────────
# STAGE 4: Sand (fills remaining small gaps with micro-moments)
# ──────────────────────────────────────────────────────────────────────

def stage_sand(all_episodes: list[dict], backstory: dict) -> list[dict]:
    """LLM generates SAND — micro-moments within long episodes."""
    print("  Stage 4: Sand (LLM)...", flush=True)

    # Find long episodes (> 30 min) that could have micro-moments
    long_episodes = []
    for ep in all_episodes:
        sh, sm = map(int, ep.get("start_time", "00:00").split(":"))
        eh, em = map(int, ep.get("end_time", "00:00").split(":"))
        duration = (eh * 60 + em) - (sh * 60 + sm)
        if duration >= 45:
            long_episodes.append({
                "purpose": ep.get("purpose", ""),
                "location": ep.get("specific_location", ""),
                "start": ep.get("start_time", ""),
                "end": ep.get("end_time", ""),
                "duration_min": duration,
                "domain": ep.get("domain", ""),
                "social": ep.get("social_context", "alone"),
            })

    if not long_episodes:
        print("     No long episodes for sand", flush=True)
        return []

    text = call_llm(
        "Output JSON array inside <json></json>. No text.",
        f"Add SAND (micro-moments) that happen DURING long activities.\n\n"
        f"Long episodes:\n{json.dumps(long_episodes, indent=2)[:600]}\n\n"
        f"Generate 2-3 sand grains per long episode. These are brief interruptions "
        f"that happen during the activity: checked phone, got water, stretched, "
        f"brief chat, walked to printer, bathroom break.\n\n"
        f"Each grain must be WITHIN the episode time range (start_time and end_time "
        f"must be between the episode's start and end).\n\n"
        f"Each: start_time,end_time,hetus_code(039),primary_activity(sitting/standing/walking),"
        f"domain(match parent episode),purpose,specific_location(same as parent),location_type,"
        f"indoor_outdoor,social_context(alone),social_detail,affect_valence(neutral),"
        f"fatigue,narrative\n\n"
        f"Narrative: reference what just happened in the main activity.\n"
        f"Example: 'Checked Slack — three messages from Morten about the weekend hike.'\n<json>",
        max_tokens=2048,
    )

    result = extract_json(text)
    if result and isinstance(result, list):
        for ep in result:
            ep["is_sand"] = True
        print(f"     {len(result)} sand grains", flush=True)
        return result

    print(f"     [FALLBACK] no sand generated ({len(text)} chars)", flush=True)
    return []


# ──────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────────────

def generate_jar_of_life_staged(
    persona: dict = None,
    day_of_week: str = "Monday",
    month: str = "april",
    seed: int = 42,
) -> dict:
    """
    Full staged Jar of Life pipeline.
    
    Rocks → Pebbles → Sand. Each stage builds on the previous.
    """
    if persona is None:
        persona = {"name": "Erik Hansen", "age": 32, "occupation": "Software Developer",
                   "city": "Trondheim", "has_bike": True}

    print("=" * 60, flush=True)
    print("JAR OF LIFE — Staged Pipeline", flush=True)
    print("=" * 60, flush=True)

    # Stage 1: Backstory + Locations
    backstory = stage_backstory()
    time.sleep(2)
    locations = stage_locations(seed)

    # Stage 2: Rocks
    time.sleep(2)
    rocks = stage_rocks(backstory, locations)
    if not rocks:
        print("  [FATAL] No rocks generated", flush=True)
        return None

    # Stage 3: Pebbles
    time.sleep(2)
    pebbles = stage_pebbles(rocks, backstory, locations)

    # Combine rocks + pebbles for sand stage
    all_episodes = rocks + pebbles
    all_episodes.sort(key=lambda e: e.get("start_time", "00:00"))

    # Stage 4: Sand
    time.sleep(2)
    sand = stage_sand(all_episodes, backstory)

    # Combine all
    all_episodes = rocks + pebbles + sand
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
        "locations_used": {k: v.get("name", "") for k, v in locations.items()},
    }

    # QA
    ema = generate_ema_probes(diary, seed=seed)
    validation = validate_diary(diary, ema)

    print(f"\n{'=' * 60}", flush=True)
    non_sand = [ep for ep in all_episodes if not ep.get("is_sand")]
    sand_count = sum(1 for ep in all_episodes if ep.get("is_sand"))
    print(f"  RESULTS: {len(all_episodes)} episodes ({len(non_sand)} main + {sand_count} sand)", flush=True)
    print(f"  QA: {validation['overall_score']:.3f}", flush=True)
    for metric, data in validation.items():
        if metric == "overall_score":
            continue
        s = data.get("score", 0)
        n = len(data.get("issues", []))
        if n > 0:
            st = "PASS" if s >= 0.85 else "FAIL"
            print(f"    {st} {metric}: {s:.3f} ({n})", flush=True)

    missed = sum(1 for p in ema if p.get("missed"))
    ans = [p for p in ema if not p.get("missed")]
    mm = sum(1 for p in ans if not p.get("activity_matches_gt", True))
    print(f"  EMA: {missed} missed, {mm}/{len(ans)} standing misreported", flush=True)

    # Save
    output = {"backstory": backstory, "locations": locations,
              "diary": diary, "ema_probes": ema, "validation": validation}
    with open("output/jar_of_life_staged.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"  Saved to output/jar_of_life_staged.json", flush=True)

    return diary


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    generate_jar_of_life_staged()
