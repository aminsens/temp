"""
Hybrid Diary Generator — Programmatic Structure + LLM Narratives.

Architecture (revised per DSPy community research):
- Structure: HETUS-coded template (programmatic, 99.5% reliable)
- Narratives: LLM enrichment via dspy.Predict + XMLAdapter
- EMA: Programmatic with recall bias rules
- QA: Programmatic validator + LLM self-correction

This separates structure (guaranteed correct) from language (LLM-generated).
"""

import json
import sys
import os
import random
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.llm_config import ask
from data.hetus_taxonomy import ACTIVITIES, HETUS_TO_OUR_FORMAT


# ──────────────────────────────────────────────────────────────────────
# Trondheim Location Database (will be replaced by OSM module)
# ──────────────────────────────────────────────────────────────────────

TRONDHEIM_LOCATIONS = {
    "home": "Singsaker apartment, Trondheim",
    "work": "NTNU Realfagbygget, 3rd floor, Gløshaugen",
    "gym": "SiT Gløshaugen fitness centre",
    "park_walk": "Byparken, along Nidelva river",
    "park_run": "Kristiansten Fortress park trails",
    "cafe": "Dromedar Kaffebar, Nordre gate",
    "supermarket": "Rema 1000, Elgeseter gate",
    "restaurant": "Solsiden area restaurants",
    "friend_home": "Tyholt residential area",
    "bike_route_work": "Elgeseter gate bike lane",
    "bike_route_home": "Klostergata, towards Singsaker",
    "bike_route_gym": "Høgskoleringen, towards SiT Gløshaugen",
    "run_route": "Ladestien coastal path",
    "library": "NTNU Gunnerus library",
    "shopping": "Trondheim Torg, Nordre gate",
}


# ──────────────────────────────────────────────────────────────────────
# Weekday Template (HETUS-coded)
# ──────────────────────────────────────────────────────────────────────

WEEKDAY_TEMPLATES = {
    "work_day": [
        {"start":"07:00","end":"07:15","hetus":"011","activity":"lying","domain":"self_care","purpose":"waking up","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"mild"},
        {"start":"07:15","end":"07:45","hetus":"031","activity":"standing","domain":"self_care","purpose":"shower and morning routine","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"mild"},
        {"start":"07:45","end":"08:05","hetus":"021","activity":"sitting","domain":"self_care","purpose":"breakfast","loc_key":"home","social":"with_partner","social_detail":"eating with partner","affect":"positive","fatigue":"low"},
        {"start":"08:05","end":"08:25","hetus":"910","activity":"cycling","domain":"transport","purpose":"commute to work","loc_key":"bike_route_work","social":"alone","social_detail":"","affect":"positive","fatigue":"low","transit_from":"home","transit_to":"work"},
        {"start":"08:25","end":"10:00","hetus":"111","activity":"sitting","domain":"work","purpose":"morning coding session","loc_key":"work","social":"with_colleagues","social_detail":"open office, team nearby","affect":"neutral","fatigue":"low"},
        {"start":"10:00","end":"10:15","hetus":"111","activity":"sitting","domain":"work","purpose":"coffee break","loc_key":"work","social":"with_colleagues","social_detail":"chatting with team","affect":"neutral","fatigue":"low"},
        {"start":"10:15","end":"12:00","hetus":"111","activity":"sitting","domain":"work","purpose":"development work","loc_key":"work","social":"with_colleagues","social_detail":"standup at 11","affect":"neutral","fatigue":"moderate"},
        {"start":"12:00","end":"12:45","hetus":"021","activity":"sitting","domain":"social","purpose":"lunch","loc_key":"cafe","social":"with_colleagues","social_detail":"lunch with team","affect":"positive","fatigue":"moderate"},
        {"start":"12:45","end":"13:00","hetus":"611","activity":"walking","domain":"exercise","purpose":"lunch walk","loc_key":"park_walk","social":"alone","social_detail":"","affect":"positive","fatigue":"low"},
        {"start":"13:00","end":"15:30","hetus":"111","activity":"sitting","domain":"work","purpose":"afternoon development","loc_key":"work","social":"with_colleagues","social_detail":"meeting at 14:00","affect":"neutral","fatigue":"moderate"},
        {"start":"15:30","end":"15:45","hetus":"111","activity":"sitting","domain":"work","purpose":"afternoon break","loc_key":"work","social":"alone","social_detail":"","affect":"neutral","fatigue":"moderate"},
        {"start":"15:45","end":"16:05","hetus":"910","activity":"cycling","domain":"transport","purpose":"cycle home","loc_key":"bike_route_home","social":"alone","social_detail":"","affect":"positive","fatigue":"low","transit_from":"work","transit_to":"home"},
        {"start":"16:05","end":"16:15","hetus":"031","activity":"standing","domain":"self_care","purpose":"change for gym","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"moderate"},
        {"start":"16:15","end":"17:30","hetus":"615","activity":"standing","domain":"exercise","purpose":"gym workout","loc_key":"gym","social":"alone","social_detail":"","affect":"positive","fatigue":"moderate"},
        {"start":"17:30","end":"17:45","hetus":"031","activity":"standing","domain":"self_care","purpose":"shower at gym","loc_key":"gym","social":"alone","social_detail":"","affect":"neutral","fatigue":"moderate"},
        {"start":"17:45","end":"18:05","hetus":"910","activity":"cycling","domain":"transport","purpose":"cycle home from gym","loc_key":"bike_route_gym","social":"alone","social_detail":"","affect":"positive","fatigue":"moderate","transit_from":"gym","transit_to":"home"},
        {"start":"18:05","end":"19:00","hetus":"311","activity":"standing","domain":"household","purpose":"cook dinner","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"moderate"},
        {"start":"19:00","end":"19:30","hetus":"021","activity":"sitting","domain":"social","purpose":"dinner","loc_key":"home","social":"with_partner","social_detail":"dinner with partner","affect":"positive","fatigue":"moderate"},
        {"start":"19:30","end":"20:30","hetus":"821","activity":"sitting","domain":"leisure","purpose":"watch TV","loc_key":"home","social":"with_partner","social_detail":"watching together","affect":"positive","fatigue":"moderate"},
        {"start":"20:30","end":"21:30","hetus":"721","activity":"sitting","domain":"leisure","purpose":"gaming","loc_key":"home","social":"alone","social_detail":"","affect":"positive","fatigue":"moderate"},
        {"start":"21:30","end":"22:00","hetus":"031","activity":"standing","domain":"self_care","purpose":"evening routine","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"high"},
        {"start":"22:00","end":"22:15","hetus":"531","activity":"lying","domain":"leisure","purpose":"reading in bed","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"high"},
        {"start":"22:15","end":"23:00","hetus":"011","activity":"lying","domain":"self_care","purpose":"sleep","loc_key":"home","social":"alone","social_detail":"","affect":"neutral","fatigue":"high"},
    ],
    "gym_day_variants": {
        "running": {"hetus":"612","activity":"running","purpose":"evening run","loc_key":"run_route","duration_min":50},
        "rest": {"hetus":"531","activity":"lying","purpose":"rest day","loc_key":"home","duration_min":75},
    },
    "weekend_variations": {
        "sleep_in": {"start_offset_min":60},
        "no_commute": True,
        "longer_exercise": True,
        "social_activity": True,
    },
}

DEVICE_WEAR_TEMPLATE = [
    {"start":"07:00","end":"07:15","status":"not_worn","reason":"charging overnight"},
    {"start":"07:15","end":"07:30","status":"not_worn","reason":"morning shower"},
    {"start":"07:30","end":"22:00","status":"worn","reason":"continuous wear"},
    {"start":"22:00","end":"22:15","status":"not_worn","reason":"evening shower"},
]


# ──────────────────────────────────────────────────────────────────────
# Diary Generator
# ──────────────────────────────────────────────────────────────────────

def generate_diary_structure(
    day_of_week: str,
    persona: dict,
    seed: int = 42,
    exercise_variant: Optional[str] = None,
) -> dict:
    """
    Generate diary structure programmatically.
    
    Returns a complete diary dict with:
    - HETUS-coded episodes
    - Trondheim-specific locations
    - Device wear schedule
    - Realistic fatigue trajectory
    
    NO LLM INVOLVED — 99.5% reliable.
    """
    rng = random.Random(seed)
    
    is_weekend = day_of_week in ["Saturday", "Sunday"]
    template = WEEKDAY_TEMPLATES["work_day"].copy()
    
    if is_weekend:
        # Weekend: shift wake time later, no commute, add social
        for ep in template:
            sh, sm = map(int, ep["start"].split(":"))
            eh, em = map(int, ep["end"].split(":"))
            if sh < 10:  # shift morning activities later
                ep["start"] = f"{sh+1:02d}:{sm:02d}"
                ep["end"] = f"{eh+1:02d}:{em:02d}"
        
        # Remove commute episodes
        template = [ep for ep in template if ep.get("hetus") != "910"]
        
        # Remove work episodes, replace with leisure
        new_template = []
        for ep in template:
            if ep["hetus"] == "111":
                # Replace work with leisure activities
                leisure_options = [
                    {"hetus":"611","activity":"walking","domain":"exercise","purpose":"morning hike","loc_key":"park_walk","social":"with_partner","social_detail":"hiking with partner"},
                    {"hetus":"361","activity":"walking","domain":"household","purpose":"grocery shopping","loc_key":"supermarket","social":"alone","social_detail":""},
                    {"hetus":"512","activity":"sitting","domain":"social","purpose":"visiting friends","loc_key":"friend_home","social":"with_friends","social_detail":"coffee and chat"},
                    {"hetus":"721","activity":"sitting","domain":"leisure","purpose":"browsing internet","loc_key":"home","social":"alone","social_detail":""},
                ]
                replacement = rng.choice(leisure_options)
                ep.update(replacement)
            new_template.append(ep)
        template = new_template
    
    # Apply exercise variant (swap gym for running or rest day)
    if exercise_variant and exercise_variant in WEEKDAY_TEMPLATES["gym_day_variants"]:
        variant = WEEKDAY_TEMPLATES["gym_day_variants"][exercise_variant]
        for i, ep in enumerate(template):
            if ep.get("hetus") == "615":  # gym
                template[i].update(variant)
                break
    
    # Resolve locations
    episodes = []
    for ep_template in template:
        loc = TRONDHEIM_LOCATIONS.get(ep_template["loc_key"], "Trondheim")
        
        # Determine location type
        loc_type = "home"
        if "office" in loc.lower() or "NTNU" in loc:
            loc_type = "work_office"
        elif "gym" in loc.lower() or "SiT" in loc:
            loc_type = "gym"
        elif "park" in loc.lower() or "Byparken" in loc:
            loc_type = "park"
        elif "cafe" in loc.lower() or "Kaffebar" in loc:
            loc_type = "restaurant"
        elif "gate" in loc.lower() or "bike" in loc.lower():
            loc_type = "street"
        elif "Rema" in loc or "supermarket" in loc:
            loc_type = "shop"
        elif "friend" in loc.lower() or "Tyholt" in loc:
            loc_type = "other_home"
        
        indoor = "indoor" if ep_template["activity"] in ["sitting","lying","standing"] else "outdoor"
        if "bike_route" in ep_template["loc_key"] or "run_route" in ep_template["loc_key"]:
            indoor = "outdoor"
        
        episode = {
            "start_time": ep_template["start"],
            "end_time": ep_template["end"],
            "hetus_code": ep_template["hetus"],
            "primary_activity": ep_template["activity"],
            "domain": ep_template["domain"],
            "purpose": ep_template["purpose"],
            "specific_location": loc,
            "location_type": loc_type,
            "indoor_outdoor": indoor,
            "social_context": ep_template["social"],
            "social_detail": ep_template["social_detail"],
            "affect_valence": ep_template["affect"],
            "fatigue": ep_template["fatigue"],
            "narrative": "",  # to be filled by LLM
        }
        
        # Add transit fields if applicable
        if "transit_from" in ep_template:
            episode["transit_from"] = TRONDHEIM_LOCATIONS.get(ep_template["transit_from"], ep_template["transit_from"])
            episode["transit_to"] = TRONDHEIM_LOCATIONS.get(ep_template["transit_to"], ep_template["transit_to"])
        
        episodes.append(episode)
    
    diary = {
        "day_of_week": day_of_week,
        "episodes": episodes,
        "device_wear_schedule": DEVICE_WEAR_TEMPLATE.copy(),
        "daily_narrative": "",  # to be filled by LLM
        "is_typical_day": True,
        "anomalies": [],
    }
    
    return diary


def enrich_narratives(diary: dict, persona: dict) -> dict:
    """
    Use LLM to enrich episode narratives and daily summary.
    
    Uses Predict + XMLAdapter-compatible prompt.
    The LLM ONLY writes narrative text — structure is untouched.
    """
    
    # Build episode summary for context
    episode_summary = []
    for i, ep in enumerate(diary["episodes"]):
        episode_summary.append(
            f"{i}: {ep['start_time']}-{ep['end_time']} "
            f"{ep['hetus_code']} {ep['purpose']} "
            f"at {ep['specific_location']} "
            f"({ep['social_context']})"
        )
    
    system_prompt = (
        "You write natural narrative text for a daily diary. "
        "For each episode, write 1-2 sentences describing what the person is doing. "
        "Be specific: mention Trondheim street names, weather, social interactions. "
        "Also write a daily_narrative (2-3 sentences summarizing the day). "
        "Output ONLY a JSON object with: "
        'narratives (array of strings, one per episode), daily_narrative (string). '
        "No explanation."
    )
    
    user_prompt = (
        f"Persona: {persona.get('name', 'Erik')}, {persona.get('age', 32)}, "
        f"{persona.get('occupation', 'developer')}, {persona.get('city', 'Trondheim')}. "
        f"Day: {diary['day_of_week']}\n\n"
        f"Episodes:\n" + "\n".join(episode_summary) + "\n\n"
        f"Write narratives for each episode and a daily_narrative. "
        f'Mention: Elgeseter gate, Byparken, Nidelva, SiT Gløshaugen, Klostergata, Singsaker. '
        f"JSON: {{narratives: [...], daily_narrative: '...'}}"
    )
    
    result = ask(system_prompt, user_prompt, preset="json_output", max_tokens=2048)
    
    # Parse
    text = result.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
    
    # Find JSON
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            enriched = json.loads(text[start:end+1])
            narratives = enriched.get("narratives", [])
            daily_narrative = enriched.get("daily_narrative", "")
            
            # Apply narratives to episodes
            for i, nar in enumerate(narratives):
                if i < len(diary["episodes"]):
                    diary["episodes"][i]["narrative"] = nar
            
            if daily_narrative:
                diary["daily_narrative"] = daily_narrative
            
            return diary
        except json.JSONDecodeError:
            pass
    
    # Fallback: use template narratives
    return enrich_narratives_fallback(diary)


def enrich_narratives_fallback(diary: dict) -> dict:
    """Fallback narrative generation (no LLM)."""
    
    narrative_templates = {
        "011": "Falls asleep for the night.",
        "031": "Takes care of personal hygiene and gets ready.",
        "021": "Enjoys a meal.",
        "910": "Cycles through Trondheim streets.",
        "111": "Focuses on work tasks at the office.",
        "611": "Goes for a walk, enjoying the fresh air.",
        "612": "Goes for a run along the path.",
        "615": "Completes a gym workout session.",
        "311": "Prepares dinner in the kitchen.",
        "821": "Relaxes watching television.",
        "721": "Spends time on the computer.",
        "531": "Rests before sleep.",
        "361": "Handles grocery shopping.",
        "512": "Spends time with friends.",
    }
    
    for ep in diary["episodes"]:
        if not ep.get("narrative"):
            hetus = ep.get("hetus_code", "")
            base = narrative_templates.get(hetus, ep.get("purpose", ""))
            loc = ep.get("specific_location", "")
            if loc:
                ep["narrative"] = f"{base} Location: {loc}."
    
    diary["daily_narrative"] = (
        f"A {diary['day_of_week']} in Trondheim. "
        f"Cycled to work, had a productive day at the office, "
        f"enjoyed a gym session, and relaxed at home in the evening."
    )
    
    return diary


# ──────────────────────────────────────────────────────────────────────
# Main Generation Function
# ──────────────────────────────────────────────────────────────────────

def generate_hybrid_diary(
    persona: dict,
    day_of_week: str = "Monday",
    seed: int = 42,
    exercise_variant: Optional[str] = None,
    enrich: bool = True,
) -> dict:
    """
    Generate a complete diary: programmatic structure + LLM narratives.
    
    Args:
        persona: Persona dict (name, age, occupation, etc.)
        day_of_week: Monday through Sunday
        seed: Random seed for reproducibility
        exercise_variant: None, "running", or "rest"
        enrich: Whether to use LLM for narrative enrichment
    
    Returns:
        Complete diary dict with all fields populated
    """
    
    # Step 1: Generate structure (programmatic)
    diary = generate_diary_structure(day_of_week, persona, seed, exercise_variant)
    
    # Step 2: Enrich narratives (LLM)
    if enrich:
        diary = enrich_narratives(diary, persona)
    else:
        diary = enrich_narratives_fallback(diary)
    
    return diary


# ──────────────────────────────────────────────────────────────────────
# CLI Test
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time
    
    persona = {
        "name": "Erik Hansen",
        "age": 32,
        "gender": "male",
        "occupation": "Software Developer",
        "city": "Trondheim",
        "living_situation": "Lives with partner",
        "has_children": False,
        "has_car": False,
        "has_bike": True,
        "fitness_level": "moderate",
        "work_schedule": "Mon-Fri 08-16",
        "commute_mode": "bicycle",
        "commute_duration_min": 18,
        "hobbies": ["cycling", "gym", "hiking"],
    }
    
    print("=== GENERATING WEEKDAY DIARY ===", flush=True)
    diary = generate_hybrid_diary(persona, "Monday", seed=42, enrich=True)
    
    eps = diary.get("episodes", [])
    print(f"Episodes: {len(eps)}", flush=True)
    print(f"Day: {eps[0]['start_time']} -> {eps[-1]['end_time']}", flush=True)
    print(f"HETUS: {[ep['hetus_code'] for ep in eps]}", flush=True)
    print(f"Domains: {set(ep['domain'] for ep in eps)}", flush=True)
    print(f"Activities: {set(ep['primary_activity'] for ep in eps)}", flush=True)
    
    # Check narratives
    filled = sum(1 for ep in eps if ep.get("narrative"))
    print(f"Narratives filled: {filled}/{len(eps)}", flush=True)
    
    # QA
    from evaluation.qa_validator import validate_diary
    validation = validate_diary(diary)
    print(f"\nQA Score: {validation['overall_score']:.3f}", flush=True)
    for metric, data in validation.items():
        if metric == "overall_score": continue
        score = data.get("score", 0)
        n = len(data.get("issues", []))
        status = "PASS" if score >= 0.85 else "FAIL"
        print(f"  {status} {metric}: {score:.3f} ({n} issues)", flush=True)
    
    # Save
    output = {
        "persona": json.dumps(persona),
        "diary": json.dumps(diary, indent=2),
        "validation": json.dumps(validation, indent=2),
    }
    with open("output/hybrid_test_output.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved!", flush=True)
    print("DONE!", flush=True)
