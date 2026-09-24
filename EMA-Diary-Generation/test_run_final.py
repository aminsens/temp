"""
EMA Diary Pipeline Test - Step by step with delays.
"""
import os, sys, json, time, requests

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = ["google/gemma-4-31b-it:free", "nvidia/nemotron-3-super-120b-a12b:free"]
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def call_llm(system, user, max_tokens=4096):
    for model in MODELS:
        for attempt in range(4):
            try:
                resp = requests.post(API_URL,
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role":"system","content":system},{"role":"user","content":user}], "max_tokens": max_tokens, "temperature": 0.7},
                    timeout=120)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"], model
                elif resp.status_code == 429:
                    w = min(12*(2**attempt), 60)
                    print(f"    rate-limited, wait {w}s...")
                    time.sleep(w)
                else:
                    print(f"    err {resp.status_code}")
                    time.sleep(5)
            except Exception as e:
                print(f"    exc: {e}")
                time.sleep(5)
        print(f"  {model} failed, trying next...")
    raise Exception("All models failed")

def extract_json(t):
    t = t.strip()
    if t.startswith("```"):
        t = "\n".join(l for l in t.split("\n") if not l.strip().startswith("```"))
    return t.strip()

# ══════════════════════════════════════════
print("STEP 1: Persona")
sys_out, m = call_llm(
    "Return ONLY valid JSON, no markdown.",
    'Generate persona: 32yo male software dev, cycles to work, lives with partner in Nørrebro Copenhagen, moderate fitness. JSON fields: name, age, gender, occupation, city, living_situation, has_children(bool), has_car(bool), has_bike(bool), fitness_level, work_schedule, commute_mode, commute_duration_min, hobbies(array), personality_traits(array), health_notes, typical_sleep_time, typical_wake_time')
persona = extract_json(sys_out)
print(f"  [{m}] {len(persona)} chars")
print(f"  {persona[:300]}")
time.sleep(8)

# ══════════════════════════════════════════
print("\nSTEP 2: Diary")
sys_out, m = call_llm(
    'Generate realistic day diary. Each episode: start_time(HH:MM), end_time(HH:MM), primary_activity(sitting/standing/walking/running/cycling/lying), domain(work/leisure/transport/household/exercise/social/self_care), purpose, specific_location, location_type(home/work_office/gym/park/street/restaurant/shopping), indoor_outdoor(indoor/outdoor/mixed), social_context(alone/with_partner/with_family/with_friends/with_colleagues), social_detail, affect_valence(negative/neutral/positive), fatigue(none/mild/moderate/high), narrative. Cover FULL day 14-18 episodes. ONLY JSON.',
    f'Generate Monday diary for: {persona}\nReturn: {{"day_of_week":"Monday","episodes":[...],"daily_narrative":"...","is_typical_day":true}}')
diary = extract_json(sys_out)
print(f"  [{m}] {len(diary)} chars")
print(f"  {diary[:500]}")
time.sleep(8)

# ══════════════════════════════════════════
print("\nSTEP 3: EMA Probes")
sys_out, m = call_llm(
    'Generate EMA probes from diary. Standing UNDERREPORTED(40% correct). Sedentary SIMPLIFIED. Social ACCURATE. Location GENERIC. Lag 0.5-8min. 1/6 MISSED. ONLY JSON array.',
    f'Generate 6 EMA probes for: {diary}\nEach: prompt_time, response_time, response_lag_min, gt_activity, gt_domain, gt_location_type, gt_social, reported_activity, reported_domain, reported_location, reported_social, activity_matches_gt(bool), missed(bool). Spread 60min+ apart.')
ema = extract_json(sys_out)
print(f"  [{m}] {len(ema)} chars")
print(f"  {ema[:500]}")

# ══════════════════════════════════════════
print("\n" + "="*60)
print("VALIDATION")
print("="*60)

output = {"persona": persona, "diary": diary, "ema_probes": ema}

try:
    d = json.loads(diary)
    eps = d.get("episodes",[])
    print(f"Diary episodes: {len(eps)}")
    req = ["start_time","end_time","primary_activity","domain","purpose","specific_location","location_type","indoor_outdoor","social_context"]
    comp = sum(1 for e in eps if all(e.get(f) for f in req))
    print(f"Complete: {comp}/{len(eps)}")
    if eps:
        s = sorted(eps, key=lambda e: e.get("start_time",""))
        print(f"Day: {s[0].get('start_time')} → {s[-1].get('end_time')}")
        doms = set(e.get("domain","") for e in eps)
        acts = set(e.get("primary_activity","") for e in eps)
        print(f"Domains: {doms}")
        print(f"Activities: {acts}")
        g=o=0
        for i in range(1,len(s)):
            ph,pm=map(int,s[i-1].get("end_time","00:00").split(":"))
            ch,cm=map(int,s[i].get("start_time","00:00").split(":"))
            df=(ch*60+cm)-(ph*60+pm)
            if df<0:o+=1
            elif df>10:g+=1
        print(f"Temporal: {o} overlaps, {g} gaps")
except Exception as e:
    print(f"Diary err: {e}")

try:
    p = json.loads(ema)
    print(f"\nEMA probes: {len(p)}")
    ms = sum(1 for x in p if x.get("missed"))
    print(f"Missed: {ms}")
    an = [x for x in p if not x.get("missed")]
    if an:
        mm = sum(1 for x in an if not x.get("activity_matches_gt",True))
        print(f"Mismatch: {mm}/{len(an)} ({mm/len(an)*100:.0f}%)")
except Exception as e:
    print(f"EMA err: {e}")

path = os.path.join(OUTPUT_DIR, "test_run_output.json")
with open(path,"w") as f: json.dump(output, f, indent=2)
print(f"\nSaved: {path}")
print("Done!")
