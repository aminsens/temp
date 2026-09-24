"""
Sand Layer Generator — Micro-moments filling gaps between episodes.

The "sand" in the Jar of Life metaphor:
- Brief, mundane, often forgotten moments
- 2-15 minutes each
- Fill every gap between rocks and pebbles
- Make the diary feel lived-in, not curated

Examples:
- Checked phone, replied to a text
- Got up to refill water bottle
- Brief hallway chat with colleague
- Walked to the printer
- Looked out the window
- Stretched at desk
- Quick bathroom break
- Tied shoelaces before cycling
- Petted the neighbour's cat
- Checked the weather forecast
"""

import random

# ──────────────────────────────────────────────────────────────────────
# Sand grain templates by context
# ──────────────────────────────────────────────────────────────────────

SAND_AT_HOME = [
    {"duration_min": 3, "activity": "sitting", "purpose": "checked phone", "hetus": "721"},
    {"duration_min": 2, "activity": "standing", "purpose": "refilled water glass", "hetus": "039"},
    {"duration_min": 3, "activity": "standing", "purpose": "tidied up kitchen counter", "hetus": "321"},
    {"duration_min": 2, "activity": "sitting", "purpose": "checked weather forecast", "hetus": "721"},
    {"duration_min": 4, "activity": "standing", "purpose": "put away clean dishes", "hetus": "312"},
    {"duration_min": 2, "activity": "sitting", "purpose": "quick phone check, replied to text", "hetus": "515"},
    {"duration_min": 3, "activity": "standing", "purpose": "packed bag for tomorrow", "hetus": "324"},
    {"duration_min": 2, "activity": "standing", "purpose": "locked front door, checked windows", "hetus": "329"},
    {"duration_min": 3, "activity": "sitting", "purpose": "skimmed news on phone", "hetus": "722"},
    {"duration_min": 5, "activity": "sitting", "purpose": "reviewed tomorrow's calendar", "hetus": "721"},
    {"duration_min": 2, "activity": "standing", "purpose": "filled water bottle for gym", "hetus": "039"},
    {"duration_min": 3, "activity": "standing", "purpose": "made a cup of tea", "hetus": "021"},
]

SAND_AT_WORK = [
    {"duration_min": 3, "activity": "sitting", "purpose": "checked Slack messages", "hetus": "111"},
    {"duration_min": 2, "activity": "walking", "purpose": "walked to printer", "hetus": "111"},
    {"duration_min": 4, "activity": "sitting", "purpose": "replied to emails", "hetus": "111"},
    {"duration_min": 2, "activity": "standing", "purpose": "stretched at desk", "hetus": "111"},
    {"duration_min": 3, "activity": "walking", "purpose": "brief hallway chat with colleague", "hetus": "111"},
    {"duration_min": 2, "activity": "standing", "purpose": "refilled water bottle at cooler", "hetus": "111"},
    {"duration_min": 3, "activity": "sitting", "purpose": "quick bathroom break", "hetus": "039"},
    {"duration_min": 4, "activity": "sitting", "purpose": "read internal wiki page", "hetus": "111"},
    {"duration_min": 2, "activity": "standing", "purpose": "stood up to think through a problem", "hetus": "111"},
    {"duration_min": 3, "activity": "sitting", "purpose": "quick personal phone check", "hetus": "515"},
    {"duration_min": 5, "activity": "sitting", "purpose": "waiting for build to compile", "hetus": "111"},
    {"duration_min": 2, "activity": "walking", "purpose": "walked to meeting room", "hetus": "111"},
    {"duration_min": 3, "activity": "standing", "purpose": "whiteboard sketch with colleague", "hetus": "111"},
]

SAND_TRANSIT = [
    {"duration_min": 2, "activity": "standing", "purpose": "waited at traffic light", "hetus": "910"},
    {"duration_min": 3, "activity": "standing", "purpose": "locked bike at destination", "hetus": "910"},
    {"duration_min": 2, "activity": "standing", "purpose": "adjusted backpack straps", "hetus": "910"},
    {"duration_min": 2, "activity": "standing", "purpose": "checked phone for directions", "hetus": "910"},
]

SAND_AT_GYM = [
    {"duration_min": 3, "activity": "standing", "purpose": "checked workout plan on phone", "hetus": "615"},
    {"duration_min": 2, "activity": "standing", "purpose": "filled water bottle at fountain", "hetus": "615"},
    {"duration_min": 4, "activity": "sitting", "purpose": "rested between sets", "hetus": "615"},
    {"duration_min": 2, "activity": "walking", "purpose": "walked to different equipment", "hetus": "615"},
    {"duration_min": 3, "activity": "sitting", "purpose": "towel break, checked phone", "hetus": "615"},
]

SAND_SOCIAL = [
    {"duration_min": 3, "activity": "sitting", "purpose": "waited for friend to arrive", "hetus": "511"},
    {"duration_min": 5, "activity": "sitting", "purpose": "chatting while waiting for food", "hetus": "511"},
    {"duration_min": 2, "activity": "standing", "purpose": "looked at menu", "hetus": "511"},
    {"duration_min": 3, "activity": "sitting", "purpose": "showed something on phone to friend", "hetus": "511"},
]

SAND_OUTDOOR = [
    {"duration_min": 2, "activity": "standing", "purpose": "stopped to admire the view", "hetus": "611"},
    {"duration_min": 3, "activity": "standing", "purpose": "took a photo on phone", "hetus": "611"},
    {"duration_min": 2, "activity": "standing", "purpose": "tied shoelaces", "hetus": "611"},
    {"duration_min": 3, "activity": "sitting", "purpose": "sat on bench to rest", "hetus": "531"},
    {"duration_min": 2, "activity": "standing", "purpose": "checked map on phone", "hetus": "611"},
]


def get_sand_pool(location_type: str, activity: str) -> list[dict]:
    """Get appropriate sand grains for a given context."""
    if location_type == "home":
        return SAND_AT_HOME
    elif location_type in ["work_office", "work"]:
        return SAND_AT_WORK
    elif location_type == "gym":
        return SAND_AT_GYM
    elif location_type in ["restaurant", "bar"]:
        return SAND_SOCIAL
    elif location_type in ["park", "street"] and activity in ["walking", "running", "cycling"]:
        return SAND_OUTDOOR
    elif activity == "cycling":
        return SAND_TRANSIT
    else:
        return SAND_AT_HOME


def fill_gaps_with_sand(
    episodes: list[dict],
    max_sand_per_gap: int = 2,
    min_gap_for_sand_min: int = 3,
    seed: int = 42,
) -> list[dict]:
    """
    Fill gaps between episodes with micro-moments (sand grains).
    
    Args:
        episodes: List of episode dicts (rocks and pebbles)
        max_sand_per_gap: Maximum sand grains to insert per gap
        min_gap_for_sand_min: Minimum gap size (minutes) to fill with sand
        seed: Random seed for reproducibility
    
    Returns:
        Extended list of episodes with sand grains inserted
    """
    rng = random.Random(seed)
    
    if len(episodes) < 2:
        return episodes
    
    # Sort by start time
    sorted_eps = sorted(episodes, key=lambda e: e.get("start_time", "00:00"))
    
    result = []
    
    for i in range(len(sorted_eps)):
        result.append(sorted_eps[i])
        
        if i < len(sorted_eps) - 1:
            curr_end = sorted_eps[i].get("end_time", "00:00")
            next_start = sorted_eps[i + 1].get("start_time", "00:00")
            
            # Calculate gap
            eh, em = map(int, curr_end.split(":"))
            ns_h, ns_m = map(int, next_start.split(":"))
            gap_min = (ns_h * 60 + ns_m) - (eh * 60 + em)
            
            if gap_min >= min_gap_for_sand_min:
                # Get context from surrounding episode
                context_ep = sorted_eps[i]
                location_type = context_ep.get("location_type", "home")
                activity = context_ep.get("primary_activity", "sitting")
                
                # Get sand pool for this context
                sand_pool = get_sand_pool(location_type, activity)
                
                # Fill the gap
                gap_remaining = gap_min
                sand_count = 0
                
                while gap_remaining >= 2 and sand_count < max_sand_per_gap:
                    # Pick a sand grain that fits
                    fitting = [s for s in sand_pool if s["duration_min"] <= gap_remaining]
                    if not fitting:
                        break
                    
                    grain = rng.choice(fitting)
                    
                    # Calculate timing
                    grain_start_min = (eh * 60 + em) + (gap_min - gap_remaining)
                    grain_h, grain_m = divmod(grain_start_min, 60)
                    grain_end_min = grain_start_min + grain["duration_min"]
                    grain_eh, grain_em = divmod(grain_end_min, 60)
                    
                    sand_episode = {
                        "start_time": f"{grain_h:02d}:{grain_m:02d}",
                        "end_time": f"{grain_eh:02d}:{grain_em:02d}",
                        "hetus_code": grain["hetus"],
                        "primary_activity": grain["activity"],
                        "domain": context_ep.get("domain", "self_care"),
                        "purpose": grain["purpose"],
                        "specific_location": context_ep.get("specific_location", "home"),
                        "location_type": location_type,
                        "indoor_outdoor": context_ep.get("indoor_outdoor", "indoor"),
                        "social_context": context_ep.get("social_context", "alone"),
                        "social_detail": "",
                        "affect_valence": context_ep.get("affect_valence", "neutral"),
                        "fatigue": context_ep.get("fatigue", "mild"),
                        "narrative": grain["purpose"].capitalize() + ".",
                        "is_sand": True,  # Mark as micro-moment
                    }
                    
                    result.append(sand_episode)
                    gap_remaining -= grain["duration_min"]
                    sand_count += 1
                    
                    # Remove used grain to avoid repetition
                    sand_pool = [s for s in sand_pool if s["purpose"] != grain["purpose"]]
                    if not sand_pool:
                        break
    
    # Re-sort by start time
    result.sort(key=lambda e: e.get("start_time", "00:00"))
    
    return result


def count_sand(episodes: list[dict]) -> int:
    """Count sand grains in an episode list."""
    return sum(1 for ep in episodes if ep.get("is_sand", False))


def count_rocks_and_pebbles(episodes: list[dict]) -> tuple[int, int]:
    """Count rocks (HETUS 011/111/910) and pebbles (everything else non-sand)."""
    rocks = 0
    pebbles = 0
    for ep in episodes:
        if ep.get("is_sand", False):
            continue
        hetus = ep.get("hetus_code", "")
        if hetus in ["011", "111", "910"]:  # sleep, work, commute
            rocks += 1
        else:
            pebbles += 1
    return rocks, pebbles


if __name__ == "__main__":
    # Test with a simple episode list
    test_episodes = [
        {"start_time": "07:00", "end_time": "07:15", "hetus_code": "011", "primary_activity": "lying", "domain": "self_care", "purpose": "waking up", "location_type": "home", "specific_location": "bedroom", "indoor_outdoor": "indoor", "social_context": "alone", "affect_valence": "neutral", "fatigue": "mild", "narrative": "Wakes up."},
        {"start_time": "07:45", "end_time": "08:05", "hetus_code": "021", "primary_activity": "sitting", "domain": "self_care", "purpose": "breakfast", "location_type": "home", "specific_location": "kitchen", "indoor_outdoor": "indoor", "social_context": "with_partner", "affect_valence": "positive", "fatigue": "low", "narrative": "Breakfast."},
        {"start_time": "08:25", "end_time": "12:00", "hetus_code": "111", "primary_activity": "sitting", "domain": "work", "purpose": "coding", "location_type": "work_office", "specific_location": "office", "indoor_outdoor": "indoor", "social_context": "with_colleagues", "affect_valence": "neutral", "fatigue": "moderate", "narrative": "Working."},
    ]
    
    filled = fill_gaps_with_sand(test_episodes, seed=42)
    
    print(f"Original episodes: {len(test_episodes)}")
    print(f"After sand: {len(filled)}")
    print(f"Sand grains: {count_sand(filled)}")
    rocks, pebbles = count_rocks_and_pebbles(filled)
    print(f"Rocks: {rocks}, Pebbles: {pebbles}")
    
    print("\nTimeline:")
    for ep in filled:
        marker = "[SAND]" if ep.get("is_sand") else "[ROCK]"
        print(f"  {ep['start_time']}-{ep['end_time']} {marker:7s} {ep['purpose']}")
