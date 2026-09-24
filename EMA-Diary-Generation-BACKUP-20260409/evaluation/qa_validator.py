"""
Diary QA Validator + Self-Correction Loop.

Validates generated diary episodes against:
1. HETUS code validity (must be in allowed set)
2. Activity-domain coherence
3. Temporal continuity
4. Device wear completeness
5. Fatigue trajectory realism
6. Location specificity

Invalid episodes trigger a self-correction loop.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.llm_config import ask
from data.hetus_taxonomy import ACTIVITIES, HETUS_TO_OUR_FORMAT

# ──────────────────────────────────────────────────────────────────────
# Allowed HETUS Level 2 codes (2-digit, simplified)
# ──────────────────────────────────────────────────────────────────────

ALLOWED_HETUS_LEVEL2 = {
    "01", "02", "03",  # Personal care
    "11", "12",        # Employment
    "21", "22",        # Study
    "31", "32", "33", "34", "35", "36", "37", "38", "39",  # Household
    "41", "42", "43",  # Voluntary work
    "51", "52", "53",  # Social life
    "61", "62", "63",  # Sports
    "71", "72", "73",  # Hobbies
    "81", "82", "83",  # Mass media
    "91", "92", "93", "94", "95", "96", "98", "90",  # Travel
}

ALLOWED_HETUS_LEVEL3 = set(ACTIVITIES.keys())

# ──────────────────────────────────────────────────────────────────────
# Activity-Domain Coherence Rules
# ──────────────────────────────────────────────────────────────────────

VALID_ACTIVITY_DOMAIN = {
    "cycling": {"transport", "exercise", "leisure"},
    "running": {"exercise", "leisure"},
    "walking": {"transport", "exercise", "leisure", "household", "social"},
    "sitting": {"work", "leisure", "transport", "household", "self_care", "social"},
    "standing": {"work", "household", "self_care", "leisure"},
    "lying": {"self_care", "leisure"},
}

# ──────────────────────────────────────────────────────────────────────
# Validation Functions
# ──────────────────────────────────────────────────────────────────────

def validate_hetus_code(code: str) -> tuple[bool, str]:
    """Check if a HETUS code is valid."""
    if not code:
        return False, "missing hetus_code"
    
    # Accept Level 2 (2-digit) or Level 3 (3-digit)
    if code in ALLOWED_HETUS_LEVEL3:
        return True, ""
    
    if code[:2] in ALLOWED_HETUS_LEVEL2:
        return True, ""
    
    return False, f"invalid HETUS code: {code}"


def validate_activity_domain(activity: str, domain: str) -> tuple[bool, str]:
    """Check activity-domain coherence."""
    valid = VALID_ACTIVITY_DOMAIN.get(activity, set())
    if domain in valid:
        return True, ""
    return False, f"{activity} + {domain} (valid: {valid})"


def validate_temporal(eps: list) -> list[str]:
    """Check temporal continuity."""
    issues = []
    if not eps:
        return ["no episodes"]
    
    sorted_eps = sorted(eps, key=lambda e: e.get("start_time", "00:00"))
    
    for i in range(1, len(sorted_eps)):
        prev_end = sorted_eps[i-1].get("end_time", "00:00")
        curr_start = sorted_eps[i].get("start_time", "00:00")
        
        try:
            ph, pm = map(int, prev_end.split(":"))
            ch, cm = map(int, curr_start.split(":"))
            diff = (ch * 60 + cm) - (ph * 60 + pm)
            
            if diff < 0:
                issues.append(f"OVERLAP: ep {i-1} ends {prev_end}, ep {i} starts {curr_start}")
            elif diff > 10:
                issues.append(f"GAP: {diff}min between ep {i-1} and ep {i}")
        except ValueError:
            issues.append(f"invalid time format at ep {i}")
    
    return issues


def validate_completeness(ep: dict) -> list[str]:
    """Check if an episode has all required fields."""
    required = [
        "start_time", "end_time", "primary_activity", "domain",
        "purpose", "specific_location", "location_type",
        "indoor_outdoor", "social_context", "hetus_code",
        "affect_valence", "fatigue", "narrative",
    ]
    return [f for f in required if not ep.get(f)]


def validate_device_wear(schedule: list) -> list[str]:
    """Check device wear schedule."""
    issues = []
    if not schedule:
        return ["no device_wear_schedule"]
    
    for i, period in enumerate(schedule):
        if not period.get("start"):
            issues.append(f"wear period {i} missing start time")
        if not period.get("end"):
            issues.append(f"wear period {i} missing end time")
        if not period.get("status"):
            issues.append(f"wear period {i} missing status")
    
    return issues


def validate_fatigue_trajectory(eps: list) -> list[str]:
    """Check that fatigue increases realistically through the day."""
    issues = []
    order = {"none": 0, "low": 1, "mild": 2, "moderate": 3, "high": 4, "exhausted": 5}
    
    fatigues = [order.get(ep.get("fatigue", ""), -1) for ep in eps]
    valid_fatigues = [f for f in fatigues if f >= 0]
    
    if len(valid_fatigues) < 3:
        return ["too few fatigue values to assess trajectory"]
    
    # Check morning vs evening
    third = len(valid_fatigues) // 3
    early_avg = sum(valid_fatigues[:third]) / third if third > 0 else 0
    late_avg = sum(valid_fatigues[2*third:]) / max(1, len(valid_fatigues) - 2*third)
    
    if late_avg < early_avg:
        issues.append(f"fatigue decreases toward evening ({early_avg:.1f} -> {late_avg:.1f})")
    
    return issues


def validate_location_specificity(eps: list) -> list[str]:
    """Check that locations are specific, not generic."""
    generic = {"bedroom", "bathroom", "kitchen", "office", "gym", "park",
               "home", "city streets", "public", "workplace", "outside"}
    issues = []
    
    for i, ep in enumerate(eps):
        loc = ep.get("specific_location", "")
        if loc.lower() in generic:
            issues.append(f"ep {i}: generic location '{loc}'")
        elif len(loc) < 5:
            issues.append(f"ep {i}: location too short '{loc}'")
    
    return issues


def validate_ema_probes(probes: list) -> list[str]:
    """Validate EMA probe realism."""
    issues = []
    
    if not probes:
        return ["no EMA probes"]
    
    # Check missed rate
    answered = [p for p in probes if not p.get("missed")]
    missed = [p for p in probes if p.get("missed")]
    miss_rate = len(missed) / len(probes) if probes else 0
    
    if miss_rate > 0.3:
        issues.append(f"miss rate too high: {miss_rate:.0%}")
    if miss_rate < 0.05 and len(probes) > 4:
        issues.append(f"miss rate too low: {miss_rate:.0%}")
    
    # Check standing underreporting
    gt_standing = [p for p in answered if p.get("gt_activity") == "standing"]
    if gt_standing:
        correctly_reported = sum(
            1 for p in gt_standing if p.get("reported_activity") == "standing"
        )
        report_rate = correctly_reported / len(gt_standing)
        if report_rate > 0.7:
            issues.append(f"standing overreported: {report_rate:.0%} correct (should be ~40%)")
    
    # Check response lags
    lags = [p.get("response_lag_min", 0) for p in answered]
    if lags:
        avg_lag = sum(lags) / len(lags)
        if avg_lag > 10:
            issues.append(f"average lag too high: {avg_lag:.1f}min")
        if avg_lag < 0.5:
            issues.append(f"average lag unrealistically low: {avg_lag:.1f}min")
    
    return issues


# ──────────────────────────────────────────────────────────────────────
# Full Validation
# ──────────────────────────────────────────────────────────────────────

def validate_diary(diary: dict, ema_probes: list = None) -> dict:
    """Full validation of a diary. Returns score and issues."""
    
    eps = diary.get("episodes", [])
    
    results = {
        "hetus_codes": {"issues": [], "score": 1.0},
        "activity_domain": {"issues": [], "score": 1.0},
        "temporal": {"issues": [], "score": 1.0},
        "completeness": {"issues": [], "score": 1.0},
        "device_wear": {"issues": [], "score": 1.0},
        "fatigue_trajectory": {"issues": [], "score": 1.0},
        "location_specificity": {"issues": [], "score": 1.0},
    }
    
    if ema_probes:
        results["ema_probes"] = {"issues": [], "score": 1.0}
    
    # HETUS codes
    for i, ep in enumerate(eps):
        valid, msg = validate_hetus_code(ep.get("hetus_code", ""))
        if not valid:
            results["hetus_codes"]["issues"].append(f"ep {i}: {msg}")
    if results["hetus_codes"]["issues"]:
        results["hetus_codes"]["score"] = 1.0 - len(results["hetus_codes"]["issues"]) / max(1, len(eps))
    
    # Activity-domain
    for i, ep in enumerate(eps):
        valid, msg = validate_activity_domain(
            ep.get("primary_activity", ""), ep.get("domain", "")
        )
        if not valid:
            results["activity_domain"]["issues"].append(f"ep {i}: {msg}")
    if results["activity_domain"]["issues"]:
        results["activity_domain"]["score"] = 1.0 - len(results["activity_domain"]["issues"]) / max(1, len(eps))
    
    # Temporal
    results["temporal"]["issues"] = validate_temporal(eps)
    results["temporal"]["score"] = 1.0 if not results["temporal"]["issues"] else 0.5
    
    # Completeness
    incomplete_episodes = []
    for i, ep in enumerate(eps):
        missing = validate_completeness(ep)
        if missing:
            incomplete_episodes.append(f"ep {i}: missing {missing}")
    results["completeness"]["issues"] = incomplete_episodes
    results["completeness"]["score"] = 1.0 - len(incomplete_episodes) / max(1, len(eps))
    
    # Device wear
    results["device_wear"]["issues"] = validate_device_wear(diary.get("device_wear_schedule", []))
    results["device_wear"]["score"] = 1.0 if not results["device_wear"]["issues"] else 0.5
    
    # Fatigue trajectory
    results["fatigue_trajectory"]["issues"] = validate_fatigue_trajectory(eps)
    results["fatigue_trajectory"]["score"] = 1.0 if not results["fatigue_trajectory"]["issues"] else 0.5
    
    # Location specificity
    results["location_specificity"]["issues"] = validate_location_specificity(eps)
    results["location_specificity"]["score"] = 1.0 - len(results["location_specificity"]["issues"]) / max(1, len(eps))
    
    # EMA probes
    if ema_probes:
        results["ema_probes"]["issues"] = validate_ema_probes(ema_probes)
        results["ema_probes"]["score"] = 1.0 if not results["ema_probes"]["issues"] else 0.5
    
    # Overall score
    scores = [v["score"] for v in results.values()]
    results["overall_score"] = sum(scores) / len(scores) if scores else 0
    
    return results


# ──────────────────────────────────────────────────────────────────────
# Self-Correction Loop
# ──────────────────────────────────────────────────────────────────────

def self_correct_diary(
    diary_json: str,
    validation_results: dict,
    max_iterations: int = 2,
) -> str:
    """
    Use LLM to fix validation issues in the diary.
    
    Sends the diary + issues to the model and asks it to fix them.
    """
    
    issues_text = ""
    for metric, data in validation_results.items():
        if metric == "overall_score":
            continue
        if data.get("issues"):
            issues_text += f"\n{metric} (score: {data['score']:.2f}):\n"
            for issue in data["issues"][:5]:  # limit to 5 issues per category
                issues_text += f"  - {issue}\n"
    
    if not issues_text:
        return diary_json  # nothing to fix
    
    system_prompt = (
        "You fix diary validation issues. Output ONLY valid JSON.\n"
        "Fix the issues listed below while preserving all other valid content.\n"
        "Do not change episodes that are already correct.\n"
        "Do not add new episodes unless temporal gaps need filling.\n"
        "Ensure all HETUS codes are from the valid set:\n"
        "01 02 03 11 12 21 22 31 32 33 34 35 36 37 38 39 "
        "41 42 43 51 52 53 61 62 63 71 72 73 81 82 83 "
        "91 92 93 94 95 96 98 90\n"
        "Or Level 3 codes like: 011 021 031 111 121 311 321 "
        "511 531 611 612 613 615 721 821 910 936 950 960\n"
    )
    
    user_prompt = (
        f"Fix these issues in the diary:\n{issues_text}\n\n"
        f"Diary:\n{diary_json}\n\n"
        "Output the corrected diary as JSON."
    )
    
    result = ask(system_prompt, user_prompt, preset="json_output", max_tokens=8192)
    
    text = result.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
    
    return text.strip()


def generate_with_qa(
    persona_json: str,
    day_of_week: str = "Monday",
    max_qa_iterations: int = 2,
    min_score: float = 0.85,
) -> dict:
    """
    Generate diary with QA validation loop.
    
    Generates -> validates -> corrects -> re-validates until score >= min_score
    or max iterations reached.
    """
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.refined_diary_gen import generate_refined_diary, generate_refined_ema
    
    # Initial generation
    diary = generate_refined_diary(persona_json, day_of_week)
    
    for iteration in range(max_qa_iterations + 1):
        # Validate
        ema = None  # generate EMA only after diary is validated
        validation = validate_diary(diary)
        score = validation["overall_score"]
        
        print(f"  QA iteration {iteration}: score={score:.3f}", flush=True)
        
        if score >= min_score:
            print(f"  PASS (score >= {min_score})", flush=True)
            break
        
        if iteration < max_qa_iterations:
            # Self-correct
            print(f"  Correcting...", flush=True)
            diary_json = json.dumps(diary)
            corrected = self_correct_diary(diary_json, validation)
            try:
                diary = json.loads(corrected)
            except:
                print(f"  Correction failed, keeping original", flush=True)
                break
    
    # Generate EMA after diary is finalized
    ema = generate_refined_ema(json.dumps(diary))
    
    return diary, ema, validation


if __name__ == "__main__":
    print("=== DIARY QA VALIDATOR ===", flush=True)
    
    # Load existing diary for testing
    with open("output/test_run_output.json") as f:
        data = json.load(f)
    
    diary = json.loads(data["diary"])
    ema = json.loads(data["ema_probes"])
    
    results = validate_diary(diary, ema)
    
    print(f"\nOverall score: {results['overall_score']:.3f}", flush=True)
    print(f"\nBreakdown:", flush=True)
    for metric, data in results.items():
        if metric == "overall_score":
            continue
        score = data.get("score", 0)
        n_issues = len(data.get("issues", []))
        status = "PASS" if score >= 0.85 else "FAIL"
        print(f"  {status} {metric}: {score:.3f} ({n_issues} issues)", flush=True)
        for issue in data.get("issues", [])[:3]:
            print(f"    - {issue}", flush=True)
