"""
Evaluation metrics for synthetic EMA diaries.

These metrics encode everything the EMA literature says makes a good diary,
and can be used as reward signals for optimization or as standalone evaluation.
"""

import json
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# Episode-Level Metrics
# ──────────────────────────────────────────────────────────────────────

REQUIRED_EPISODE_FIELDS = [
    "start_time", "end_time", "primary_activity", "domain",
    "purpose", "specific_location", "location_type",
    "indoor_outdoor", "social_context", "narrative",
]

VALID_ACTIVITIES = {"sitting", "standing", "walking", "running", "cycling", "lying", "transition"}
VALID_DOMAINS = {"work", "leisure", "transport", "household", "exercise", "social", "self_care"}
VALID_LOCATIONS = {
    "home", "work_office", "work_outdoor", "gym", "park", "shopping",
    "restaurant", "transit_vehicle", "transit_stop", "street", "school",
    "medical", "outdoor_general", "indoor_other", "friend_home",
}
VALID_SOCIAL = {
    "alone", "with_partner", "with_family", "with_friends",
    "with_colleagues", "with_strangers", "with_children",
}
VALID_INDOOR_OUTDOOR = {"indoor", "outdoor", "mixed"}


def episode_completeness(episodes: list[dict]) -> dict:
    """What fraction of required fields are present in each episode?"""
    if not episodes:
        return {"score": 0.0, "missing": REQUIRED_EPISODE_FIELDS}

    total_fields = len(REQUIRED_EPISODE_FIELDS) * len(episodes)
    present = 0
    missing_by_field = {f: 0 for f in REQUIRED_EPISODE_FIELDS}

    for ep in episodes:
        for field in REQUIRED_EPISODE_FIELDS:
            if ep.get(field):
                present += 1
            else:
                missing_by_field[field] += 1

    return {
        "score": present / total_fields if total_fields > 0 else 0.0,
        "present": present,
        "total": total_fields,
        "missing_by_field": missing_by_field,
    }


def episode_validity(episodes: list[dict]) -> dict:
    """Are episode field values in valid sets?"""
    if not episodes:
        return {"score": 0.0}

    checks = 0
    passed = 0

    for ep in episodes:
        # Activity
        checks += 1
        if ep.get("primary_activity") in VALID_ACTIVITIES:
            passed += 1

        # Domain
        checks += 1
        if ep.get("domain") in VALID_DOMAINS:
            passed += 1

        # Location
        checks += 1
        if ep.get("location_type") in VALID_LOCATIONS:
            passed += 1

        # Social
        checks += 1
        if ep.get("social_context") in VALID_SOCIAL:
            passed += 1

        # Indoor/outdoor
        checks += 1
        if ep.get("indoor_outdoor") in VALID_INDOOR_OUTDOOR:
            passed += 1

    return {
        "score": passed / checks if checks > 0 else 0.0,
        "passed": passed,
        "total": checks,
    }


# ──────────────────────────────────────────────────────────────────────
# Temporal Metrics
# ──────────────────────────────────────────────────────────────────────

def temporal_continuity(episodes: list[dict], max_gap_min: int = 5) -> dict:
    """Check for gaps and overlaps in the timeline."""
    if len(episodes) < 2:
        return {"score": 1.0, "gaps": [], "overlaps": []}

    sorted_eps = sorted(episodes, key=lambda e: e.get("start_time", "00:00"))
    gaps = []
    overlaps = []

    for i in range(1, len(sorted_eps)):
        prev = sorted_eps[i-1]
        curr = sorted_eps[i]

        prev_end = prev.get("end_time", "00:00")
        curr_start = curr.get("start_time", "00:00")

        diff = _time_diff_min(prev_end, curr_start)

        if diff < 0:
            overlaps.append({
                "episode_1": prev.get("id", i-1),
                "episode_2": curr.get("id", i),
                "overlap_min": abs(diff),
            })
        elif diff > max_gap_min:
            gaps.append({
                "after_episode": prev.get("id", i-1),
                "before_episode": curr.get("id", i),
                "gap_min": diff,
            })

    penalty = (len(gaps) + len(overlaps)) * 0.1
    score = max(0.0, 1.0 - penalty)

    return {
        "score": score,
        "gaps": gaps,
        "overlaps": overlaps,
        "num_episodes": len(sorted_eps),
    }


def temporal_coverage(episodes: list[dict], day_start: str = "06:00", day_end: str = "23:30") -> dict:
    """What fraction of the waking day is covered by episodes?"""
    if not episodes:
        return {"score": 0.0, "coverage_pct": 0.0}

    total_day_min = _time_diff_min(day_start, day_end)
    covered_min = 0

    for ep in episodes:
        ep_start = max(ep.get("start_time", day_start), day_start)
        ep_end = min(ep.get("end_time", day_end), day_end)
        covered_min += max(0, _time_diff_min(ep_start, ep_end))

    coverage_pct = covered_min / total_day_min if total_day_min > 0 else 0

    return {
        "score": min(coverage_pct / 0.9, 1.0),  # 90% coverage = perfect score
        "coverage_pct": coverage_pct,
        "covered_min": covered_min,
        "total_day_min": total_day_min,
    }


# ──────────────────────────────────────────────────────────────────────
# Semantic Coherence Metrics
# ──────────────────────────────────────────────────────────────────────

# Activity → valid domains
ACTIVITY_DOMAIN_COMPATIBILITY = {
    "cycling": {"transport", "exercise", "leisure"},
    "running": {"exercise", "leisure"},
    "walking": {"transport", "exercise", "leisure", "household", "social"},
    "sitting": {"work", "leisure", "transport", "household", "self_care", "social"},
    "standing": {"work", "household", "leisure", "social"},
    "lying": {"self_care", "leisure"},
}

# Domain → valid locations
DOMAIN_LOCATION_COMPATIBILITY = {
    "work": {"work_office", "work_outdoor"},
    "transport": {"street", "transit_vehicle", "transit_stop"},
    "exercise": {"gym", "park", "outdoor_general", "street"},
    "leisure": {"home", "park", "restaurant", "shopping", "friend_home", "outdoor_general"},
    "household": {"home"},
    "self_care": {"home", "medical"},
    "social": {"restaurant", "friend_home", "home", "park"},
}


def activity_domain_coherence(episodes: list[dict]) -> dict:
    """Do activity-domain combinations make sense?"""
    if not episodes:
        return {"score": 0.0}

    compatible = 0
    total = 0
    violations = []

    for ep in episodes:
        activity = ep.get("primary_activity", "")
        domain = ep.get("domain", "")
        if activity and domain:
            total += 1
            valid = ACTIVITY_DOMAIN_COMPATIBILITY.get(activity, set())
            if domain in valid:
                compatible += 1
            else:
                violations.append({
                    "episode": ep.get("id", "?"),
                    "activity": activity,
                    "domain": domain,
                    "valid_domains": list(valid),
                })

    return {
        "score": compatible / total if total > 0 else 0.0,
        "compatible": compatible,
        "total": total,
        "violations": violations,
    }


def domain_location_coherence(episodes: list[dict]) -> dict:
    """Do domain-location combinations make sense?"""
    if not episodes:
        return {"score": 0.0}

    compatible = 0
    total = 0
    violations = []

    for ep in episodes:
        domain = ep.get("domain", "")
        location = ep.get("location_type", "")
        if domain and location:
            total += 1
            valid = DOMAIN_LOCATION_COMPATIBILITY.get(domain, set())
            if location in valid:
                compatible += 1
            else:
                violations.append({
                    "episode": ep.get("id", "?"),
                    "domain": domain,
                    "location": location,
                    "valid_locations": list(valid),
                })

    return {
        "score": compatible / total if total > 0 else 0.0,
        "compatible": compatible,
        "total": total,
        "violations": violations,
    }


# ──────────────────────────────────────────────────────────────────────
# EMA Probe Quality Metrics
# ──────────────────────────────────────────────────────────────────────

def ema_recall_realism(probes: list[dict]) -> dict:
    """
    Do EMA probes show realistic recall patterns?

    Based on EMA literature:
    - Standing should be underreported
    - Sedentary should be simplified
    - Response lag should be right-skewed
    - Some prompts should be missed
    """
    if not probes:
        return {"score": 0.0}

    metrics = {}

    # Mismatch rate
    answered = [p for p in probes if not p.get("missed")]
    if answered:
        mismatch_count = sum(
            1 for p in answered if not p.get("activity_matches_gt", True)
        )
        mismatch_rate = mismatch_count / len(answered)
        # 5-35% mismatch is realistic
        metrics["mismatch_rate"] = mismatch_rate
        metrics["mismatch_realistic"] = 0.05 <= mismatch_rate <= 0.35

    # Missing rate
    missed = [p for p in probes if p.get("missed")]
    miss_rate = len(missed) / len(probes) if probes else 0
    metrics["miss_rate"] = miss_rate
    metrics["miss_realistic"] = 0.05 <= miss_rate <= 0.25

    # Lag distribution
    lags = [p.get("response_lag_min", 0) for p in answered]
    if lags:
        avg_lag = sum(lags) / len(lags)
        metrics["avg_lag_min"] = avg_lag
        metrics["lag_realistic"] = 0.5 <= avg_lag <= 10

    # Standing underreporting
    gt_standing = [p for p in answered if p.get("gt_activity") == "standing"]
    if gt_standing:
        reported_standing = sum(
            1 for p in gt_standing if p.get("reported_activity") == "standing"
        )
        standing_report_rate = reported_standing / len(gt_standing)
        metrics["standing_report_rate"] = standing_report_rate
        metrics["standing_underreported"] = standing_report_rate < 0.7

    # Compute overall score
    realism_checks = [
        metrics.get("mismatch_realistic", False),
        metrics.get("miss_realistic", False),
        metrics.get("lag_realistic", False),
    ]
    metrics["score"] = sum(realism_checks) / len(realism_checks)

    return metrics


# ──────────────────────────────────────────────────────────────────────
# Cross-Day Consistency
# ──────────────────────────────────────────────────────────────────────

def cross_day_consistency(day_diaries: list[dict]) -> dict:
    """Check that multi-day diaries are internally consistent."""
    if len(day_diaries) < 2:
        return {"score": 1.0, "issues": []}

    issues = []

    # Check wake/sleep consistency
    wake_times = []
    for day in day_diaries:
        episodes = day.get("episodes", [])
        if episodes:
            first_activity = episodes[0].get("primary_activity", "")
            if first_activity in ["sitting", "standing"]:  # waking activity
                wake_times.append(episodes[0].get("start_time", ""))

    if len(wake_times) >= 2:
        wake_minutes = [_parse_time(t) for t in wake_times if t]
        if wake_minutes:
            variance = max(wake_minutes) - min(wake_minutes)
            if variance > 180:  # >3hr variance in wake time
                issues.append(f"Wake time variance too high: {variance}min")

    # Check for narrative thread continuity
    # (This would need the full narrative texts to check properly)

    return {
        "score": max(0.0, 1.0 - len(issues) * 0.2),
        "issues": issues,
        "num_days": len(day_diaries),
    }


# ──────────────────────────────────────────────────────────────────────
# Comprehensive Evaluation
# ──────────────────────────────────────────────────────────────────────

def evaluate_diary(
    day_diaries: list[dict],
    ema_probes: Optional[list[list[dict]]] = None,
) -> dict:
    """
    Full evaluation of a generated diary suite.

    Returns scores across all dimensions the EMA literature cares about.
    """
    all_episodes = []
    for day in day_diaries:
        all_episodes.extend(day.get("episodes", []))

    results = {
        "episode_completeness": episode_completeness(all_episodes),
        "episode_validity": episode_validity(all_episodes),
        "temporal_continuity": temporal_continuity(all_episodes),
        "temporal_coverage": temporal_coverage(all_episodes),
        "activity_domain_coherence": activity_domain_coherence(all_episodes),
        "domain_location_coherence": domain_location_coherence(all_episodes),
        "cross_day_consistency": cross_day_consistency(day_diaries),
    }

    if ema_probes:
        all_probes = [p for day_probes in ema_probes for p in day_probes]
        results["ema_recall_realism"] = ema_recall_realism(all_probes)

    # Overall score (weighted average)
    weights = {
        "episode_completeness": 0.20,
        "episode_validity": 0.10,
        "temporal_continuity": 0.20,
        "temporal_coverage": 0.10,
        "activity_domain_coherence": 0.15,
        "domain_location_coherence": 0.10,
        "cross_day_consistency": 0.10,
        "ema_recall_realism": 0.05,
    }

    weighted_sum = 0
    total_weight = 0
    for key, weight in weights.items():
        if key in results:
            weighted_sum += results[key].get("score", 0) * weight
            total_weight += weight

    results["overall_score"] = weighted_sum / total_weight if total_weight > 0 else 0

    return results


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _time_diff_min(t1: str, t2: str) -> float:
    """Minutes from t1 to t2."""
    h1, m1 = map(int, t1.split(":"))
    h2, m2 = map(int, t2.split(":"))
    return (h2 * 60 + m2) - (h1 * 60 + m1)


def _parse_time(t: str) -> int:
    """Parse HH:MM to minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m
