"""
EMA Probe Generator — Programmatic (no LLM).

Generates realistic EMA probes with:
- Response lag (1-8 minutes, right-skewed)
- Standing underreporting (40% correct)
- Sedentary simplification
- Generic location reporting
- Accurate social context
- 1 missed probe per 6
"""

import json
import random

def generate_ema_probes(diary: dict, num_probes: int = 6, seed: int = 42) -> list:
    """Generate EMA probes from a diary with realistic recall bias."""
    rng = random.Random(seed)
    
    episodes = diary.get("episodes", [])
    if not episodes:
        return []
    
    # Select prompt times spread across waking hours
    waking_eps = [ep for ep in episodes if ep.get("hetus_code") != "011"]
    if len(waking_eps) < num_probes:
        waking_eps = episodes
    
    # Pick evenly spaced episodes as prompt targets
    step = max(1, len(waking_eps) // num_probes)
    target_eps = [waking_eps[i * step] for i in range(min(num_probes, len(waking_eps)))]
    
    # Ensure at least 1 standing episode (for underreporting)
    standing_eps = [ep for ep in waking_eps if ep.get("primary_activity") == "standing"]
    if standing_eps and not any(ep.get("primary_activity") == "standing" for ep in target_eps):
        target_eps[0] = rng.choice(standing_eps)
    
    # Ensure at least 1 cycling episode
    cycling_eps = [ep for ep in waking_eps if ep.get("primary_activity") == "cycling"]
    if cycling_eps and not any(ep.get("primary_activity") == "cycling" for ep in target_eps):
        target_eps[min(1, len(target_eps)-1)] = rng.choice(cycling_eps)
    
    probes = []
    
    # Pick which probe to miss (not first, not last)
    miss_idx = rng.randint(1, len(target_eps) - 2) if len(target_eps) > 2 else 0
    
    for i, ep in enumerate(target_eps):
        gt_activity = ep.get("primary_activity", "sitting")
        gt_domain = ep.get("domain", "leisure")
        gt_location_type = ep.get("location_type", "home")
        gt_social = ep.get("social_context", "alone")
        gt_location = ep.get("specific_location", "home")
        
        # Prompt time: random within the episode
        start_parts = ep.get("start_time", "12:00").split(":")
        end_parts = ep.get("end_time", "12:30").split(":")
        start_min = int(start_parts[0]) * 60 + int(start_parts[1])
        end_min = int(end_parts[0]) * 60 + int(end_parts[1])
        prompt_min = rng.randint(start_min, max(start_min, end_min - 1))
        prompt_h, prompt_m = divmod(prompt_min, 60)
        prompt_time = f"{prompt_h:02d}:{prompt_m:02d}"
        
        # Response lag: right-skewed (most quick, some slow)
        if gt_activity in ["running", "cycling"]:
            lag = rng.uniform(4.0, 8.0)  # slower during exercise
        else:
            lag = rng.uniform(0.5, 4.0)  # quick otherwise
        lag = round(lag, 1)
        
        response_min = prompt_min + int(lag)
        resp_h, resp_m = divmod(response_min, 60)
        response_time = f"{resp_h:02d}:{resp_m:02d}"
        
        # Missed?
        if i == miss_idx:
            probes.append({
                "prompt_time": prompt_time,
                "response_time": None,
                "response_lag_min": None,
                "gt_activity": gt_activity,
                "gt_domain": gt_domain,
                "gt_location_type": gt_location_type,
                "gt_social": gt_social,
                "gt_is_wearing_device": True,
                "reported_activity": None,
                "reported_domain": None,
                "reported_location": None,
                "reported_social": None,
                "activity_matches_gt": None,
                "missed": True,
            })
            continue
        
        # Apply recall bias
        reported_activity = gt_activity
        reported_domain = gt_domain  # usually accurate
        reported_social = gt_social  # always accurate
        activity_matches = True
        
        # STANDING UNDERREPORTING (30-40% correct, rest misreported)
        if gt_activity == "standing":
            if rng.random() > 0.35:  # 65% chance of misreport
                reported_activity = rng.choice(["sitting", "walking"])
                activity_matches = False
        
        # CYCLING can be misreported during commute
        if gt_activity == "cycling" and rng.random() < 0.15:
            reported_activity = "cycling"  # usually accurate for cycling
            # but domain is simplified
        
        # SEDENTARY SIMPLIFICATION (remove detail from purpose)
        reported_location = genericize_location(gt_location)
        
        # DEVICE WEAR
        wear_schedule = diary.get("device_wear_schedule", [])
        is_wearing = True
        for period in wear_schedule:
            if period.get("status") == "not_worn":
                ws = period.get("start", "00:00")
                we = period.get("end", "00:00")
                if ws <= prompt_time <= we:
                    is_wearing = False
                    break
        
        probes.append({
            "prompt_time": prompt_time,
            "response_time": response_time,
            "response_lag_min": lag,
            "gt_activity": gt_activity,
            "gt_domain": gt_domain,
            "gt_location_type": gt_location_type,
            "gt_social": gt_social,
            "gt_is_wearing_device": is_wearing,
            "reported_activity": reported_activity,
            "reported_domain": reported_domain,
            "reported_location": reported_location,
            "reported_social": reported_social,
            "activity_matches_gt": activity_matches,
            "missed": False,
        })
    
    return probes


def genericize_location(specific_location: str) -> str:
    """Convert specific Trondheim location to generic EMA response."""
    mapping = {
        "NTNU": "office",
        "Realfagbygget": "office",
        "campus": "office",
        "office": "office",
        "Singsaker": "home",
        "apartment": "home",
        "kitchen": "home",
        "bedroom": "home",
        "bathroom": "home",
        "living room": "home",
        "Byparken": "park",
        "Nidelva": "park",
        "river": "park",
        "SiT": "gym",
        "fitness": "gym",
        "Gløshaugen": "gym",
        "Elgeseter": "outside",
        "Klostergata": "outside",
        "Høgskoleringen": "outside",
        "bike lane": "outside",
        "street": "outside",
        "Samfundet": "restaurant",
        "cafeteria": "restaurant",
    }
    
    for key, generic in mapping.items():
        if key.lower() in specific_location.lower():
            return generic
    
    return "other"


if __name__ == "__main__":
    # Test with existing diary
    with open("output/test_run_output.json") as f:
        data = json.load(f)
    
    diary = json.loads(data["diary"])
    probes = generate_ema_probes(diary, num_probes=6)
    
    print(f"Generated {len(probes)} probes:")
    for p in probes:
        if p["missed"]:
            print(f"  {p['prompt_time']} MISSED (gt: {p['gt_activity']})")
        else:
            match = "==" if p["activity_matches_gt"] else "!="
            print(f"  {p['prompt_time']} gt={p['gt_activity']} {match} reported={p['reported_activity']} lag={p['response_lag_min']}min")
    
    missed = sum(1 for p in probes if p["missed"])
    answered = [p for p in probes if not p["missed"]]
    mismatches = sum(1 for p in answered if not p.get("activity_matches_gt", True))
    print(f"\nMissed: {missed}/{len(probes)}")
    print(f"Mismatch: {mismatches}/{len(answered)} ({mismatches/len(answered)*100:.0f}%)")
