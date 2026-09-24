"""
Quick test run of the EMA Diary Generation Pipeline.
Uses OpenRouter + Gemma 4 31B via DSPy.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dspy
from configs.api_config import OPENROUTER_API_KEY, MODEL_NAME

# ──────────────────────────────────────────────────────────────────────
# Configure DSPy with OpenRouter
# ──────────────────────────────────────────────────────────────────────

lm = dspy.LM(
    model=f"openrouter/{MODEL_NAME}",
    api_key=OPENROUTER_API_KEY,
    api_base="https://openrouter.ai/api/v1",
    temperature=0.7,
    max_tokens=4096,
)
dspy.configure(lm=lm)

print(f"Configured: {MODEL_NAME} via OpenRouter")
print()

# ──────────────────────────────────────────────────────────────────────
# Step 1: Generate a Persona
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STEP 1: Generate Persona")
print("=" * 60)

persona_sig = dspy.Signature(
    "persona_description -> persona_json",
    instructions=(
        "Generate a detailed synthetic persona for a physical activity research study. "
        "Return ONLY valid JSON with these fields: name, age, gender, occupation, city, "
        "living_situation, has_children, has_car, has_bike, fitness_level, work_schedule, "
        "commute_mode, commute_duration_min, hobbies (list), personality_traits (list), "
        "health_notes, typical_sleep_time, typical_wake_time. "
        "Ground the persona in Copenhagen, Denmark with realistic details."
    ),
)
persona_gen = dspy.Predict(persona_sig)

persona_result = persona_gen(
    persona_description="32yo software developer, cycles to work, lives with partner in Nørrebro Copenhagen, moderate fitness, goes to gym 2x/week"
)

print(persona_result.persona_json[:1000])
print()

# ──────────────────────────────────────────────────────────────────────
# Step 2: Generate a Daily Diary (1 day)
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STEP 2: Generate Daily Diary")
print("=" * 60)

diary_sig = dspy.Signature(
    "persona_json, day_info -> daily_diary_json",
    instructions=(
        "Generate a realistic single day diary for this persona. "
        "Return ONLY valid JSON with this structure:\n"
        "{\n"
        '  "day_of_week": "Monday",\n'
        '  "episodes": [\n'
        "    {\n"
        '      "start_time": "07:00",\n'
        '      "end_time": "07:15",\n'
        '      "primary_activity": "sitting",\n'
        '      "domain": "self_care",\n'
        '      "purpose": "eating breakfast",\n'
        '      "specific_location": "home kitchen table",\n'
        '      "location_type": "home",\n'
        '      "indoor_outdoor": "indoor",\n'
        '      "social_context": "with_partner",\n'
        '      "social_detail": "eating with partner Marie",\n'
        '      "affect_valence": "neutral",\n'
        '      "affect_arousal": "low",\n'
        '      "fatigue": "mild",\n'
        '      "narrative": "Had breakfast with Marie, she left early for a meeting"\n'
        "    }\n"
        "  ],\n"
        '  "daily_narrative": "A normal Monday...",\n'
        '  "is_typical_day": true\n'
        "}\n\n"
        "CRITICAL RULES:\n"
        "- Episodes must cover the FULL waking day with NO gaps >5 minutes\n"
        "- Every episode MUST have ALL fields shown above\n"
        "- primary_activity must be one of: sitting, standing, walking, running, cycling, lying\n"
        "- domain must be one of: work, leisure, transport, household, exercise, social, self_care\n"
        "- location_type must be one of: home, work_office, gym, park, street, restaurant, shopping\n"
        "- indoor_outdoor must be: indoor, outdoor, or mixed\n"
        "- social_context must be: alone, with_partner, with_family, with_friends, with_colleagues\n"
        "- Include affect_valence (negative/neutral/positive) and fatigue (none/mild/moderate/high) for every episode\n"
        "- Generate 12-18 episodes covering wake to sleep\n"
        "- Be realistic: include commute, work, lunch, breaks, evening activities"
    ),
)
diary_gen = dspy.Predict(diary_sig)

diary_result = diary_gen(
    persona_json=persona_result.persona_json,
    day_info="Monday, April 7 2026. Normal weekday, weather is 12°C partly cloudy.",
)

print(diary_result.daily_diary_json[:2000])
print()

# ──────────────────────────────────────────────────────────────────────
# Step 3: Generate EMA Probes
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("STEP 3: Generate EMA Probes")
print("=" * 60)

ema_sig = dspy.Signature(
    "daily_diary_json, ema_config -> ema_probes_json",
    instructions=(
        "Given the daily diary, generate 6 EMA prompt responses. "
        "Return ONLY valid JSON array.\n\n"
        "For each probe, simulate:\n"
        "1. A random prompt time between 07:00-23:00 (at least 60min apart)\n"
        "2. Ground truth: what is ACTUALLY happening at that time (from diary)\n"
        "3. What the person REPORTS (subject to recall bias):\n"
        "   - Standing is UNDERREPORTED: only ~40% correctly reported, rest become 'sitting' or 'walking'\n"
        "   - Sedentary is SIMPLIFIED: 'sitting at desk reading email' -> just 'sitting'\n"
        "   - Domain is reported generically: 'work' not 'working on API integration'\n"
        "   - Social context is reported ACCURATELY\n"
        "   - Location is GENERIC: 'work' not '3rd floor meeting room'\n"
        "4. Response lag: 0.5-8 minutes (most responses are quick, some are late)\n"
        "5. One prompt should be MISSED (person ignores notification during activity)\n\n"
        "Each probe format:\n"
        "{\n"
        '  "prompt_time": "10:23",\n'
        '  "response_time": "10:27",\n'
        '  "response_lag_min": 4.0,\n'
        '  "gt_activity": "sitting",\n'
        '  "gt_domain": "work",\n'
        '  "gt_location_type": "work_office",\n'
        '  "gt_social": "with_colleagues",\n'
        '  "reported_activity": "sitting",\n'
        '  "reported_domain": "work",\n'
        '  "reported_location": "office",\n'
        '  "reported_social": "with_colleagues",\n'
        '  "activity_matches_gt": true,\n'
        '  "missed": false\n'
        "}\n"
    ),
)
ema_gen = dspy.Predict(ema_sig)

ema_result = ema_gen(
    daily_diary_json=diary_result.daily_diary_json,
    ema_config="6 prompts per day, current recall window, 15% missing rate, standing underreported",
)

print(ema_result.ema_probes_json[:2000])
print()

# ──────────────────────────────────────────────────────────────────────
# Save everything
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("SAVING RESULTS")
print("=" * 60)

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(output_dir, exist_ok=True)

output = {
    "persona": persona_result.persona_json,
    "diary": diary_result.daily_diary_json,
    "ema_probes": ema_result.ema_probes_json,
}

output_path = os.path.join(output_dir, "test_run_output.json")
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Saved to: {output_path}")
print()

# ──────────────────────────────────────────────────────────────────────
# Quick validation
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("QUICK VALIDATION")
print("=" * 60)

# Parse diary and check episodes
try:
    diary = json.loads(diary_result.daily_diary_json)
    if isinstance(diary, str):
        diary = json.loads(diary)
    
    episodes = diary.get("episodes", [])
    print(f"Episodes generated: {len(episodes)}")
    
    # Check required fields
    required = ["start_time", "end_time", "primary_activity", "domain",
                 "purpose", "specific_location", "location_type",
                 "indoor_outdoor", "social_context"]
    
    complete = 0
    for ep in episodes:
        if all(ep.get(f) for f in required):
            complete += 1
    
    print(f"Episodes with all required fields: {complete}/{len(episodes)}")
    
    # Check temporal coverage
    if episodes:
        sorted_eps = sorted(episodes, key=lambda e: e.get("start_time", "00:00"))
        print(f"Day spans: {sorted_eps[0].get('start_time')} -> {sorted_eps[-1].get('end_time')}")
    
    # Check domains
    domains = set(ep.get("domain", "") for ep in episodes)
    print(f"Domains covered: {domains}")
    
    # Check activities
    activities = set(ep.get("primary_activity", "") for ep in episodes)
    print(f"Activities covered: {activities}")
    
except Exception as e:
    print(f"Parse error: {e}")

# Parse EMA probes
try:
    probes = json.loads(ema_result.ema_probes_json)
    if isinstance(probes, str):
        probes = json.loads(probes)
    print(f"\nEMA probes generated: {len(probes)}")
    
    missed = sum(1 for p in probes if p.get("missed"))
    print(f"Missed prompts: {missed}")
    
    mismatches = sum(1 for p in probes if not p.get("missed") and not p.get("activity_matches_gt", True))
    answered = sum(1 for p in probes if not p.get("missed"))
    if answered:
        print(f"Activity mismatch rate: {mismatches}/{answered} ({mismatches/answered*100:.0f}%)")
except Exception as e:
    print(f"EMA parse error: {e}")

print("\nDone!")
