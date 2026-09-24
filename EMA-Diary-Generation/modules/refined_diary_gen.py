"""
Refined diary generation with academic-grade quality + HETUS taxonomy.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.llm_config import ask
from data.hetus_taxonomy import get_hetus_prompt_section


# ──────────────────────────────────────────────────────────────────────
# System prompt parts (avoiding triple-quote nesting issues)
# ──────────────────────────────────────────────────────────────────────

SYSTEM_PREAMBLE = (
    "You are a precise diary generator for a physical activity research study.\n\n"
    "OUTPUT ONLY A VALID JSON OBJECT. No explanation. No markdown fences.\n\n"
    'The JSON must have this exact structure:\n'
    '{\n'
    '  "day_of_week": "Monday",\n'
    '  "episodes": [...],\n'
    '  "device_wear_schedule": [...],\n'
    '  "daily_narrative": "...",\n'
    '  "is_typical_day": true,\n'
    '  "anomalies": []\n'
    '}\n\n'
    "CRITICAL RULES:\n\n"
    "1. TEMPORAL CONTINUITY\n"
    "- Episodes MUST cover 07:00 to 23:00 with NO gaps >3 minutes\n"
    "- NO overlaps between episodes\n"
    "- Each episode has start_time and end_time in HH:MM format\n\n"
    "2. ACTIVITY-DOMAIN COHERENCE (STRICT)\n"
    "Valid combinations ONLY:\n"
    "- cycling -> transport, exercise, leisure (NEVER work, household, self_care)\n"
    "- running -> exercise, leisure (NEVER work, transport, household)\n"
    "- walking -> transport, exercise, leisure, household (NEVER work)\n"
    "- sitting -> work, leisure, transport, household, self_care, social (NEVER exercise)\n"
    "- standing -> work, household, self_care (NEVER exercise, NEVER transport)\n"
    "- lying -> self_care, leisure (NEVER work, NEVER transport)\n\n"
    "3. LOCATION SPECIFICITY\n"
    "Use SPECIFIC Trondheim locations, NOT generic terms:\n"
    '- NOT "bedroom" -> "master bedroom at Singsaker address"\n'
    '- NOT "office" -> "NTNU campus office, Building A, 3rd floor"\n'
    '- NOT "city streets" -> "Elgeseter gate bike lane"\n'
    '- NOT "kitchen" -> "home kitchen, Singsaker"\n'
    '- NOT "park" -> "Byparken, near Nidelva river"\n'
    '- NOT "gym" -> "SiT Gløshaugen fitness centre"\n'
    '- NOT "cafe" -> "Dromedar Kaffebar, Nordre gate"\n\n'
    "4. DEVICE WEAR SCHEDULE\n"
    "Include device_wear_schedule as array of:\n"
    '{"start": "HH:MM", "end": "HH:MM", "status": "worn/not_worn", "reason": "shower/charging/forgot"}\n'
    "Default: device is worn all waking hours EXCEPT:\n"
    "- Morning shower: 07:15-07:30 not_worn\n"
    "- Evening shower: 22:00-22:15 not_worn\n"
    "- Device put on at 07:00, taken off at 23:00\n\n"
    "5. FATIGUE TRAJECTORY\n"
    "Fatigue MUST increase realistically through the day:\n"
    "- Morning (07:00-09:00): mild or low\n"
    "- Mid-morning (09:00-12:00): low to moderate\n"
    "- Afternoon (12:00-15:00): moderate\n"
    "- Late afternoon (15:00-18:00): moderate to high\n"
    "- Evening (18:00-23:00): high (after exercise) or moderate (rest day)\n\n"
    "6. ACTIVITY DIVERSITY\n"
    "Include at least 5 different primary_activity values.\n"
    "Include standing for cooking, waiting, shopping.\n"
    "Include walking for transport AND exercise (different domains).\n\n"
    "7. NARRATIVES\n"
    "Each episode narrative must be 1-2 sentences, specific, with:\n"
    "- What the person is doing exactly\n"
    "- Where specifically in Trondheim\n"
    "- With whom and what they are discussing/doing\n"
    "- How they feel (for subjective state episodes)\n\n"
    "8. TRANSIT EPISODES\n"
    "For cycling/walking commutes, narrative must include:\n"
    "- Route taken (street names in Trondheim)\n"
    "- Weather/conditions\n"
    "- Traffic/other people\n\n"
    "9. AFFECT VALENCE\n"
    "Must reflect realistic emotional patterns:\n"
    "- Not always positive -- include neutral and occasional negative\n"
    "- Exercise usually positive, work neutral or positive\n"
    "- Commute in bad weather can be negative\n"
    "- Social meals usually positive\n\n"
    "10. HETUS CODES\n"
    'Each episode MUST include a "hetus_code" field with the appropriate HETUS Level 2 or 3 code.\n'
)

SYSTEM_HETUS = get_hetus_prompt_section()

USER_TRONDHEIM = (
    "TRONDHEIM REFERENCE:\n"
    "- NTNU Gløshaugen campus area (university/engineering district)\n"
    "- Singsaker residential area (near campus)\n"
    "- Byparken city park (along Nidelva river)\n"
    "- Nordre gate (main shopping street)\n"
    "- Elgeseter gate (main cycling corridor)\n"
    "- Klostergata (quiet residential street)\n"
    "- SiT Gløshaugen (student gym/fitness)\n"
    "- Lerkendal (football stadium area)\n"
    "- Tyholt (residential area north)\n"
    "- Solsiden (waterfront dining/entertainment)\n"
)


def generate_refined_diary(persona_json: str, day_of_week: str = "Monday") -> dict:
    """Generate a single day diary with academic-grade quality."""

    system_prompt = SYSTEM_PREAMBLE + SYSTEM_HETUS
    user_prompt = (
        f"Generate a {day_of_week} diary for this persona:\n\n"
        f"{persona_json}\n\n"
        f"{USER_TRONDHEIM}\n"
        "Generate 15-20 episodes. JSON ONLY."
    )

    result = ask(system_prompt, user_prompt, preset="json_output", max_tokens=8192)

    # Clean markdown fences
    text = result.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
    text = text.strip()

    # Strip thinking/reasoning blocks that the model adds
    import re
    text = re.sub(r'<analysis>.*?</analysis>', '', text, flags=re.DOTALL).strip()
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL).strip()
    # Strip everything before the first { (model preamble like "Let me analyze...")
    brace_pos = text.find('{')
    if brace_pos > 0:
        text = text[brace_pos:]

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from response (model might add reasoning before)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try fixing truncated JSON
            last_brace = json_str.rfind("}")
            if last_brace > 0:
                fixed = json_str[:last_brace+1]
                opens = fixed.count("[") - fixed.count("]")
                fixed += "]" * opens
                opens2 = fixed.count("{") - fixed.count("}")
                fixed += "}" * opens2
                try:
                    return json.loads(fixed)
                except:
                    pass

    # Debug: show what we got
    print(f"  [DEBUG] Response first 200: {text[:200]}", flush=True)
    print(f"  [DEBUG] Response last 200: {text[-200:]}", flush=True)
    raise ValueError(f"Could not parse diary JSON")


def generate_refined_ema(diary_json: str, num_probes: int = 6) -> list:
    """Generate EMA probes with realistic recall bias."""

    system_prompt = (
        "You generate EMA (Ecological Momentary Assessment) prompt responses.\n\n"
        "OUTPUT ONLY A VALID JSON ARRAY. No explanation.\n\n"
        'Each probe format:\n'
        '{\n'
        '  "prompt_time": "HH:MM",\n'
        '  "response_time": "HH:MM",\n'
        '  "response_lag_min": 0.0,\n'
        '  "gt_activity": "actual activity from diary",\n'
        '  "gt_domain": "actual domain from diary",\n'
        '  "gt_location_type": "actual location type",\n'
        '  "gt_social": "actual social context",\n'
        '  "gt_is_wearing_device": true/false,\n'
        '  "reported_activity": "what person reports (BIASED)",\n'
        '  "reported_domain": "what person reports",\n'
        '  "reported_location": "generic version of location",\n'
        '  "reported_social": "usually accurate",\n'
        '  "activity_matches_gt": true/false,\n'
        '  "missed": false\n'
        '}\n\n'
        "RECALL BIAS RULES (from EMA literature):\n"
        "1. STANDING IS UNDERREPORTED: only 30-40% correctly reported\n"
        '   - Misreported as "sitting" (most common) or "walking"\n'
        "   - People do not notice brief standing transitions\n\n"
        "2. SEDENTARY IS SIMPLIFIED:\n"
        '   - "sitting at desk working on code" -> just "sitting"\n'
        '   - "sitting on couch watching TV" -> just "sitting"\n'
        "   - Domain still reported correctly\n\n"
        "3. LOCATION IS GENERIC:\n"
        '   - "NTNU campus office, Building A, 3rd floor" -> "office"\n'
        '   - "SiT Gløshaugen fitness centre" -> "gym"\n'
        '   - "home kitchen, Singsaker" -> "home"\n'
        '   - "Byparken, near Nidelva river" -> "park"\n\n'
        "4. SOCIAL CONTEXT IS ACCURATE:\n"
        "   - Reported same as ground truth\n\n"
        "5. RESPONSE LAG:\n"
        "   - Most responses: 1-3 minutes\n"
        "   - Some: 5-8 minutes\n"
        "   - If prompted during exercise: longer lag (5-8 min)\n\n"
        "6. MISSED PROMPTS:\n"
        f"   - Exactly 1 of {num_probes} prompts missed\n"
        "   - Missed during: vigorous exercise, social meal, focused work\n"
        "   - Not missed during: passive activities (sitting, lying)\n\n"
        "7. DOMAIN IS USUALLY ACCURATE:\n"
        "   - People know if they are working vs leisure vs commuting\n"
        "   - Domain matches ground truth ~90% of the time"
    )

    user_prompt = (
        f"Generate {num_probes} EMA probes for this diary:\n\n"
        f"{diary_json}\n\n"
        "Spread prompts across 07:00-23:00, at least 60 minutes apart.\n"
        "Include at least 1 probe during a standing episode (should be misreported).\n"
        "Include at least 1 probe during a cycling episode.\n"
        "Exactly 1 probe should be missed.\n"
        "JSON ARRAY ONLY."
    )

    result = ask(system_prompt, user_prompt, preset="json_output", max_tokens=4096)

    text = result.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        last_bracket = text.rfind("]")
        if last_bracket > 0:
            fixed = text[:last_bracket+1]
            try:
                return json.loads(fixed)
            except:
                pass
        raise ValueError(f"Could not parse EMA JSON")


if __name__ == "__main__":
    print("=== GENERATING PERSONA ===", flush=True)
    persona = ask(
        "Output ONLY valid JSON. No explanation.",
        "Generate persona: 32yo male software developer, lives with partner in "
        "Trondheim Norway, bikes to work at NTNU campus, goes to gym 2-3x/week, "
        "runs on weekends.\n\n"
        "JSON fields: name,age,gender,occupation,city,living_situation,"
        "has_children(bool),has_car(bool),has_bike(bool),fitness_level,"
        "work_schedule,commute_mode,commute_duration_min,"
        "hobbies(array of 3-5),personality_traits(array of 3-4),"
        "health_notes,typical_sleep_time,typical_wake_time\n\n"
        "Make it realistic and specific to Trondheim."
    )
    print(f"  Persona: {len(persona)} chars", flush=True)

    print("\n=== GENERATING DIARY ===", flush=True)
    diary = generate_refined_diary(persona)
    eps = diary.get("episodes", [])
    print(f"  Episodes: {len(eps)}", flush=True)

    req = ["start_time","end_time","primary_activity","domain","purpose",
           "specific_location","location_type","indoor_outdoor","social_context",
           "affect_valence","fatigue","narrative"]
    comp = sum(1 for ep in eps if all(ep.get(f) for f in req))
    print(f"  Complete: {comp}/{len(eps)}", flush=True)

    if eps:
        s = sorted(eps, key=lambda e: e.get("start_time",""))
        print(f"  Day: {s[0].get('start_time')} -> {s[-1].get('end_time')}", flush=True)
        print(f"  Domains: {set(ep.get('domain','') for ep in eps)}", flush=True)
        print(f"  Activities: {set(ep.get('primary_activity','') for ep in eps)}", flush=True)

    wear = diary.get("device_wear_schedule", [])
    print(f"  Device wear periods: {len(wear)}", flush=True)

    fatigues = [ep.get("fatigue","") for ep in eps]
    print(f"  Fatigue: {' -> '.join(fatigues)}", flush=True)

    locations = [ep.get("specific_location","") for ep in eps]
    print(f"  Locations: {locations[:5]}...", flush=True)

    hetus_codes = [ep.get("hetus_code","") for ep in eps if ep.get("hetus_code")]
    print(f"  HETUS codes: {len(hetus_codes)} episodes coded", flush=True)

    print("\n=== GENERATING EMA PROBES ===", flush=True)
    ema = generate_refined_ema(json.dumps(diary))
    print(f"  Probes: {len(ema)}", flush=True)
    missed = sum(1 for p in ema if p.get("missed"))
    print(f"  Missed: {missed}", flush=True)

    output = {
        "persona": persona,
        "diary": json.dumps(diary, indent=2),
        "ema_probes": json.dumps(ema, indent=2),
    }
    with open("output/test_run_output.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to output/test_run_output.json", flush=True)
    print("DONE!", flush=True)
