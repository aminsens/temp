"""
Test run: raw API calls with retry logic.
Bypasses litellm's aggressive retry to handle free-tier rate limits.
"""

import os
import sys
import json
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemma-4-31b-it:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(system: str, user: str, max_retries: int = 5) -> str:
    """Call the LLM with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.7,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            elif resp.status_code == 429:
                wait = min(10 * (2 ** attempt), 60)  # 10, 20, 40, 60, 60
                err = resp.json().get("error", {}).get("metadata", {}).get("raw", "")
                print(f"  Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s... ({err[:60]})")
                time.sleep(wait)
            else:
                print(f"  Error {resp.status_code}: {resp.text[:200]}")
                time.sleep(5)
        except Exception as e:
            print(f"  Exception: {e}")
            time.sleep(5)
    raise Exception(f"Failed after {max_retries} retries")


def extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last line (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 1: Generate Persona")
print("=" * 60)
print()

persona_system = """You generate realistic synthetic personas for physical activity research.
Return ONLY valid JSON, no markdown fences, no explanation."""

persona_user = """Generate a persona for: 32yo software developer, cycles to work, 
lives with partner in Nørrebro Copenhagen, moderate fitness, gym 2x/week.

Return JSON with exactly these fields:
name, age, gender, occupation, city, living_situation, has_children (bool), 
has_car (bool), has_bike (bool), fitness_level, work_schedule, commute_mode, 
commute_duration_min, hobbies (array of 2-4 strings), personality_traits (array of 2-3 strings),
health_notes, typical_sleep_time, typical_wake_time"""

persona_text = call_llm(persona_system, persona_user)
persona_json = extract_json(persona_text)
print(persona_json[:800])
print()

# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 2: Generate Daily Diary")
print("=" * 60)
print()

diary_system = """You generate realistic single-day diaries for synthetic personas.
Each episode needs ALL these fields: start_time (HH:MM), end_time (HH:MM), 
primary_activity (sitting/standing/walking/running/cycling/lying), 
domain (work/leisure/transport/household/exercise/social/self_care),
purpose (string), specific_location (string), location_type, 
indoor_outdoor (indoor/outdoor/mixed), social_context, social_detail (string),
affect_valence (negative/neutral/positive), fatigue (none/mild/moderate/high),
narrative (1 sentence).

Rules:
- Cover the FULL waking day, no gaps >5 min
- 14-18 episodes from wake to sleep
- Be realistic: include commute, work, lunch, breaks, evening
- Return ONLY valid JSON, no markdown."""

diary_user = f"""Generate a Monday diary for this persona:

{persona_json}

Weather: 12°C partly cloudy.
Return JSON: {{"day_of_week": "Monday", "episodes": [...], "daily_narrative": "...", "is_typical_day": true}}"""

diary_text = call_llm(diary_system, diary_user)
diary_json = extract_json(diary_text)
print(diary_json[:2000])
print()

# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 3: Generate EMA Probes")
print("=" * 60)
print()

ema_system = """You generate EMA (Ecological Momentary Assessment) prompt responses from a diary.

RECALL BIAS RULES:
- Standing is UNDERREPORTED (~40% correct, rest become sitting/walking)
- Sedentary is SIMPLIFIED: "sitting at desk reading email" → just "sitting"
- Domain reported generically: "work" not "working on API integration"
- Social context reported ACCURATELY
- Location GENERIC: "office" not "3rd floor meeting room B"
- Response lag: 0.5-8 minutes
- 1 of 6 prompts should be MISSED (person ignores it)

Return ONLY valid JSON array, no markdown."""

ema_user = f"""Generate 6 EMA probes for this diary:

{diary_json}

Each probe: prompt_time, response_time, response_lag_min, gt_activity, gt_domain, 
gt_location_type, gt_social, reported_activity, reported_domain, reported_location,
reported_social, activity_matches_gt (bool), missed (bool)

Spread prompts across the day (07:00-23:00, at least 60min apart).
Make at least 1 probe where standing is misreported as sitting.
Make 1 probe missed."""

ema_text = call_llm(ema_system, ema_user)
ema_json = extract_json(ema_text)
print(ema_json[:2000])
print()

# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("VALIDATION")
print("=" * 60)

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(output_dir, exist_ok=True)

output = {
    "persona": persona_json,
    "diary": diary_json,
    "ema_probes": ema_json,
}

# Validate diary
try:
    diary = json.loads(diary_json)
    episodes = diary.get("episodes", [])
    print(f"Episodes: {len(episodes)}")

    required = ["start_time", "end_time", "primary_activity", "domain",
                 "purpose", "specific_location", "location_type",
                 "indoor_outdoor", "social_context"]
    complete = sum(1 for ep in episodes if all(ep.get(f) for f in required))
    print(f"Complete episodes: {complete}/{len(episodes)}")

    if episodes:
        eps = sorted(episodes, key=lambda e: e.get("start_time", ""))
        print(f"Day: {eps[0].get('start_time')} → {eps[-1].get('end_time')}")
    
    domains = set(ep.get("domain", "") for ep in episodes)
    activities = set(ep.get("primary_activity", "") for ep in episodes)
    print(f"Domains: {domains}")
    print(f"Activities: {activities}")

    # Temporal check
    eps_sorted = sorted(episodes, key=lambda e: e.get("start_time", ""))
    gaps = 0
    overlaps = 0
    for i in range(1, len(eps_sorted)):
        prev = eps_sorted[i-1].get("end_time", "00:00")
        curr = eps_sorted[i].get("start_time", "00:00")
        ph, pm = map(int, prev.split(":"))
        ch, cm = map(int, curr.split(":"))
        diff = (ch*60+cm) - (ph*60+pm)
        if diff < 0: overlaps += 1
        elif diff > 10: gaps += 1
    print(f"Temporal: {overlaps} overlaps, {gaps} gaps (>10min)")

except Exception as e:
    print(f"Diary parse error: {e}")

# Validate EMA
try:
    probes = json.loads(ema_json)
    print(f"\nEMA probes: {len(probes)}")
    missed = sum(1 for p in probes if p.get("missed"))
    print(f"Missed: {missed}")
    answered = [p for p in probes if not p.get("missed")]
    if answered:
        mismatches = sum(1 for p in answered if not p.get("activity_matches_gt", True))
        print(f"Activity mismatch rate: {mismatches}/{len(answered)} ({mismatches/len(answered)*100:.0f}%)")
except Exception as e:
    print(f"EMA parse error: {e}")

# Save
output_path = os.path.join(output_dir, "test_run_output.json")
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved to: {output_path}")
print("Done!")
