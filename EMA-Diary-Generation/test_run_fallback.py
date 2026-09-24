"""
Test run: Gemma 4 → Nemotron 3 fallback with proper retry.
"""

import os, sys, json, time, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = ["google/gemma-4-31b-it:free", "nvidia/nemotron-3-super-120b-a12b:free"]


def call_llm(system: str, user: str, max_retries: int = 3) -> str:
    for model in MODELS:
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "max_tokens": 4096,
                        "temperature": 0.7,
                    },
                    timeout=90,
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    print(f"  [model: {model}]")
                    return content
                elif resp.status_code == 429:
                    wait = min(8 * (2 ** attempt), 45)
                    print(f"  {model} rate-limited, waiting {wait}s (attempt {attempt+1})...")
                    time.sleep(wait)
                else:
                    print(f"  {model} error {resp.status_code}")
                    time.sleep(3)
            except Exception as e:
                print(f"  {model} exception: {e}")
                time.sleep(3)
        print(f"  {model} exhausted, trying next model...")
    raise Exception("All models failed")


def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


# ══════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 1: Generate Persona")
print("=" * 60)
print()

persona_text = call_llm(
    "You generate realistic synthetic personas for physical activity research. Return ONLY valid JSON, no markdown fences.",
    """Generate a persona for: 32yo software developer, cycles to work, lives with partner in Nørrebro Copenhagen, moderate fitness, gym 2x/week.

Return JSON with exactly these fields:
name, age, gender, occupation, city, living_situation, has_children (bool), has_car (bool), has_bike (bool), fitness_level, work_schedule, commute_mode, commute_duration_min, hobbies (array 2-4), personality_traits (array 2-3), health_notes, typical_sleep_time, typical_wake_time"""
)
persona_json = extract_json(persona_text)
print(persona_json[:800])
print()

# ══════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 2: Generate Daily Diary")
print("=" * 60)
print()

diary_text = call_llm(
    """You generate realistic single-day diaries for synthetic personas. Each episode needs ALL fields: start_time (HH:MM), end_time (HH:MM), primary_activity (sitting/standing/walking/running/cycling/lying), domain (work/leisure/transport/household/exercise/social/self_care), purpose (string), specific_location (string), location_type (home/work_office/gym/park/street/restaurant/shopping), indoor_outdoor (indoor/outdoor/mixed), social_context (alone/with_partner/with_family/with_friends/with_colleagues), social_detail (string), affect_valence (negative/neutral/positive), fatigue (none/mild/moderate/high), narrative (1 sentence).

Rules: Cover FULL waking day, no gaps >5 min, 14-18 episodes, be realistic. Return ONLY valid JSON.""",
    f"""Generate a Monday diary for:

{persona_json}

Weather: 12°C partly cloudy.
Return: {{"day_of_week": "Monday", "episodes": [...], "daily_narrative": "...", "is_typical_day": true}}"""
)
diary_json = extract_json(diary_text)
print(diary_json[:2000])
print()

# ══════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 3: Generate EMA Probes")
print("=" * 60)
print()

ema_text = call_llm(
    """You generate EMA prompt responses from a diary. RECALL BIAS: Standing is UNDERREPORTED (~40% correct, rest become sitting/walking). Sedentary SIMPLIFIED. Domain generic. Social ACCURATE. Location GENERIC. Lag: 0.5-8min. 1 of 6 prompts MISSED. Return ONLY valid JSON array.""",
    f"""Generate 6 EMA probes for this diary:

{diary_json}

Each: prompt_time, response_time, response_lag_min, gt_activity, gt_domain, gt_location_type, gt_social, reported_activity, reported_domain, reported_location, reported_social, activity_matches_gt (bool), missed (bool).

Spread across day, 60min+ apart. At least 1 standing→sitting misreport. 1 missed."""
)
ema_json = extract_json(ema_text)
print(ema_json[:2000])
print()

# ══════════════════════════════════════════════════════════════════
print("=" * 60)
print("VALIDATION")
print("=" * 60)

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(output_dir, exist_ok=True)

output = {"persona": persona_json, "diary": diary_json, "ema_probes": ema_json}

try:
    diary = json.loads(diary_json)
    episodes = diary.get("episodes", [])
    print(f"Episodes: {len(episodes)}")
    required = ["start_time","end_time","primary_activity","domain","purpose","specific_location","location_type","indoor_outdoor","social_context"]
    complete = sum(1 for ep in episodes if all(ep.get(f) for f in required))
    print(f"Complete: {complete}/{len(episodes)}")
    if episodes:
        eps = sorted(episodes, key=lambda e: e.get("start_time",""))
        print(f"Day: {eps[0].get('start_time')} → {eps[-1].get('end_time')}")
    domains = set(ep.get("domain","") for ep in episodes)
    activities = set(ep.get("primary_activity","") for ep in episodes)
    print(f"Domains: {domains}")
    print(f"Activities: {activities}")
    eps_s = sorted(episodes, key=lambda e: e.get("start_time",""))
    gaps = overlaps = 0
    for i in range(1, len(eps_s)):
        ph,pm = map(int, eps_s[i-1].get("end_time","00:00").split(":"))
        ch,cm = map(int, eps_s[i].get("start_time","00:00").split(":"))
        diff = (ch*60+cm)-(ph*60+pm)
        if diff < 0: overlaps += 1
        elif diff > 10: gaps += 1
    print(f"Temporal: {overlaps} overlaps, {gaps} gaps")
except Exception as e:
    print(f"Diary error: {e}")

try:
    probes = json.loads(ema_json)
    print(f"\nEMA probes: {len(probes)}")
    missed = sum(1 for p in probes if p.get("missed"))
    print(f"Missed: {missed}")
    answered = [p for p in probes if not p.get("missed")]
    if answered:
        mm = sum(1 for p in answered if not p.get("activity_matches_gt",True))
        print(f"Mismatch: {mm}/{len(answered)} ({mm/len(answered)*100:.0f}%)")
except Exception as e:
    print(f"EMA error: {e}")

output_path = os.path.join(output_dir, "test_run_output.json")
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)
print(f"\nSaved: {output_path}")
print("Done!")
