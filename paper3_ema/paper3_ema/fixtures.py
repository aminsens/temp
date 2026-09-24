"""Synthetic fixture days used by the test-suite and the demonstration cohort.

These are **test fixtures**, not a second world generator.  They exist to
exercise the EMA protocol against days that are deliberately awkward:
cycling commuters, fragmented days, unresolved movements, evening shifts, days
with no eligible event, and so on.

Nothing here is imported by the production modules; the package itself remains
host-agnostic (see ``docs/ARCHITECTURE.md`` §4 for the adapter contract).
"""

from __future__ import annotations

import random
from datetime import date as _date
from datetime import timedelta
from typing import Any, Mapping, Optional, Sequence

from .day import contextual_day_from_mapping
from .models import ContextualDay
from .timeutil import parse_hhmm

FIXTURE_VERSION = "1.0.0"

# --------------------------------------------------------------------------
# generic builders
# --------------------------------------------------------------------------

def hhmm(value: str) -> float:
    return float(parse_hhmm(value))


def episode(
    start: str,
    end: str,
    activity: str,
    domain: str,
    place_type: str = "home",
    social: str = "alone",
    indoor_outdoor: str = "indoor",
    purpose: Optional[str] = None,
    exertion: Optional[float] = None,
    is_fixed_commitment: bool = False,
    discretionary_event: Optional[str] = None,
    interval_id: Optional[str] = None,
    is_realised: bool = True,
    stability: Optional[str] = None,
    episode_id: Optional[str] = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "start_time": start,
        "end_time": end,
        "activity": activity,
        "domain": domain,
        "place_type": place_type,
        "social_context": social,
        "indoor_outdoor": indoor_outdoor,
        "is_realised": is_realised,
    }
    if episode_id:
        data["episode_id"] = episode_id
    for key, value in (
        ("purpose", purpose),
        ("exertion", exertion),
        ("discretionary_event", discretionary_event),
        ("interval_id", interval_id),
        ("stability", stability),
    ):
        if value is not None:
            data[key] = value
    if is_fixed_commitment:
        data["is_fixed_commitment"] = True
    return data


def journey(
    start: str,
    end: str,
    mode: str,
    purpose: str = "commute",
    origin: str = "home",
    destination: str = "workplace",
    delayed: Optional[bool] = None,
    crowded: Optional[bool] = None,
    distance_km: Optional[float] = None,
    journey_id: Optional[str] = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "start_time": start,
        "end_time": end,
        "mode": mode,
        "purpose": purpose,
        "origin_place_type": origin,
        "destination_place_type": destination,
    }
    if journey_id:
        data["journey_id"] = journey_id
    for key, value in (("delayed", delayed), ("crowded", crowded), ("distance_km", distance_km)):
        if value is not None:
            data[key] = value
    return data


def commitment(
    start: str,
    end: str,
    kind: str = "work",
    requires_travel: bool = False,
    travel_time_min: float = 0.0,
    label: Optional[str] = None,
    commitment_id: Optional[str] = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "start_time": start,
        "end_time": end,
        "kind": kind,
        "requires_travel": requires_travel,
        "travel_time_min": travel_time_min,
    }
    if label:
        data["label"] = label
    if commitment_id:
        data["commitment_id"] = commitment_id
    return data


def interval(
    start: str,
    end: str,
    kind: str = "sedentary",
    resolved: bool = True,
    realised: bool = True,
    stability: Optional[str] = None,
    interval_id: Optional[str] = None,
    episode_id: Optional[str] = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "start_time": start,
        "end_time": end,
        "kind": kind,
        "resolved": resolved,
        "realised": realised,
    }
    for key, value in (("stability", stability), ("interval_id", interval_id), ("episode_id", episode_id)):
        if value is not None:
            data[key] = value
    return data


def wear(start: str, end: str, status: str = "worn", reason: Optional[str] = None) -> dict[str, Any]:
    data: dict[str, Any] = {"start_time": start, "end_time": end, "status": status}
    if reason:
        data["reason"] = reason
    return data


def sensor_intervals(episodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Derive coarse sensor intervals from fixture episodes (all resolved/realised)."""
    intervals: list[dict[str, Any]] = []
    for index, item in enumerate(episodes):
        activity = str(item.get("activity", "sitting"))
        if activity in {"driving", "public_transport", "cycling"}:
            kind = "travel"
        elif activity in {"walking", "running", "other_vigorous"}:
            kind = "active"
        elif activity in {"sleeping", "lying_awake"}:
            kind = "rest"
        else:
            kind = "sedentary"
        intervals.append(
            interval(
                str(item["start_time"]),
                str(item["end_time"]),
                kind=kind,
                interval_id=f"iv-{index + 1:03d}",
            )
        )
    return intervals


# --------------------------------------------------------------------------
# the ten adversarial fixture days
# --------------------------------------------------------------------------

def normal_office_day(participant_id: str = "fixture-office", day: Any = "2026-05-04", weather: Optional[str] = None) -> dict[str, Any]:
    episodes = [
        episode("06:45", "07:00", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("07:00", "07:30", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("07:30", "07:50", "sitting", "self_care", "home", "with_partner", "indoor", purpose="breakfast", exertion=0.05),
        episode("07:50", "08:20", "public_transport", "transport", "vehicle", "with_strangers", "indoor", purpose="commute", exertion=0.05),
        episode("08:20", "08:30", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("08:30", "10:30", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05, is_fixed_commitment=True),
        episode("10:30", "10:45", "standing", "work", "workplace", "with_colleagues", "indoor", purpose="meeting", exertion=0.15),
        episode("10:45", "12:15", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("12:15", "12:45", "sitting", "social", "food_venue", "with_colleagues", "indoor", purpose="lunch", exertion=0.05),
        episode("12:45", "13:05", "walking", "leisure", "park", "alone", "outdoor", purpose="walk", exertion=0.35),
        episode("13:05", "15:30", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("15:30", "16:00", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="meeting", exertion=0.05),
        episode("16:00", "16:30", "public_transport", "transport", "vehicle", "with_strangers", "indoor", purpose="commute", exertion=0.05),
        episode("16:30", "17:00", "walking", "shopping", "shop", "alone", "indoor", purpose="shopping", exertion=0.3, discretionary_event="errand"),
        episode("17:00", "18:00", "standing", "household", "home", "alone", "indoor", purpose="cooking", exertion=0.25),
        episode("18:00", "18:40", "sitting", "social", "home", "with_partner", "indoor", purpose="dinner", exertion=0.05),
        episode("18:40", "20:10", "sitting", "leisure", "home", "with_partner", "indoor", purpose="leisure", exertion=0.05),
        episode("20:10", "21:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("21:00", "21:30", "standing", "self_care", "home", "alone", "indoor", purpose="self care", exertion=0.15),
        episode("21:30", "23:00", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("23:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    journeys = [
        journey("07:50", "08:20", "bus", "commute", "home", "workplace", journey_id="jn-office-am"),
        journey("16:00", "16:30", "bus", "commute", "workplace", "home", journey_id="jn-office-pm"),
    ]
    commitments = [
        commitment("08:30", "10:30", "work", requires_travel=True, travel_time_min=30, commitment_id="fc-morning-block"),
        commitment("10:30", "10:45", "work", label="meeting", commitment_id="fc-standup"),
        commitment("15:30", "16:00", "work", label="meeting", commitment_id="fc-review"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "07:00",
        "sleep_time": "23:00",
        "weather": weather,
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": journeys,
        "fixed_commitments": commitments,
        "device_wear": [wear("07:00", "23:00", "worn", "continuous wear")],
        "fixture": "normal_office_day",
        "expectation": "two post_trip events available; meeting commitments create schedule pressure",
    }


def cycling_commuter_day(participant_id: str = "fixture-cyclist", day: Any = "2026-05-05") -> dict[str, Any]:
    episodes = [
        episode("06:30", "07:00", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("07:00", "07:25", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("07:25", "07:45", "sitting", "self_care", "home", "with_family", "indoor", purpose="breakfast", exertion=0.05),
        episode("07:45", "08:15", "cycling", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.7),
        episode("08:15", "10:15", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("10:15", "10:30", "walking", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.3),
        episode("10:30", "12:30", "sitting", "work", "workplace", "alone", "indoor", purpose="work", exertion=0.05),
        episode("12:30", "13:00", "sitting", "self_care", "food_venue", "with_colleagues", "indoor", purpose="lunch", exertion=0.05),
        episode("13:00", "15:45", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("15:45", "16:15", "cycling", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.7),
        episode("16:15", "17:15", "running", "exercise", "park", "alone", "outdoor", purpose="exercise", exertion=0.85),
        episode("17:15", "17:45", "standing", "self_care", "home", "alone", "indoor", purpose="shower", exertion=0.2),
        episode("17:45", "18:30", "sitting", "household", "home", "with_family", "indoor", purpose="dinner", exertion=0.05),
        episode("18:30", "20:00", "sitting", "leisure", "home", "with_family", "indoor", purpose="leisure", exertion=0.05),
        episode("20:00", "21:30", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("21:30", "22:30", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("22:30", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    journeys = [
        journey("07:45", "08:15", "bike", "commute", "home", "workplace", journey_id="jn-bike-am"),
        journey("15:45", "16:15", "bike", "commute", "workplace", "home", journey_id="jn-bike-pm"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "07:00",
        "sleep_time": "22:30",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": journeys,
        "fixed_commitments": [commitment("08:15", "15:45", "work", requires_travel=True, travel_time_min=30, commitment_id="fc-workday")],
        "device_wear": [wear("07:00", "22:30", "worn")],
        "fixture": "cycling_commuter_day",
        "expectation": "no prompt may land inside cycling or running; post_trip and post_active_episode events both exist",
    }


def public_transport_commuter_day(participant_id: str = "fixture-transit", day: Any = "2026-05-06") -> dict[str, Any]:
    episodes = [
        episode("06:15", "06:45", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("06:45", "07:10", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("07:10", "07:25", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("07:25", "07:40", "standing", "transport", "transit_stop", "with_strangers", "outdoor", purpose="commute", exertion=0.15),
        episode("07:40", "08:25", "public_transport", "transport", "vehicle", "with_strangers", "indoor", purpose="commute", exertion=0.05),
        episode("08:25", "08:40", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("08:40", "12:00", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("12:00", "12:40", "sitting", "social", "food_venue", "with_colleagues", "indoor", purpose="lunch", exertion=0.05),
        episode("12:40", "16:10", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("16:10", "16:25", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("16:25", "17:10", "public_transport", "transport", "vehicle", "with_strangers", "indoor", purpose="commute", exertion=0.05),
        episode("17:10", "17:35", "walking", "shopping", "shop", "alone", "indoor", purpose="shopping", exertion=0.3, discretionary_event="errand"),
        episode("17:35", "18:30", "standing", "household", "home", "alone", "indoor", purpose="cooking", exertion=0.25),
        episode("18:30", "19:10", "sitting", "self_care", "home", "alone", "indoor", purpose="dinner", exertion=0.05),
        episode("19:10", "21:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("21:00", "22:00", "sitting", "social", "home", "with_friends", "indoor", purpose="social", exertion=0.05),
        episode("22:00", "23:00", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("23:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    journeys = [
        journey("07:10", "08:40", "train", "commute", "home", "workplace", delayed=True, crowded=True, journey_id="jn-train-am"),
        journey("16:10", "17:10", "train", "commute", "workplace", "home", journey_id="jn-train-pm"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "06:45",
        "sleep_time": "23:00",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": journeys,
        "fixed_commitments": [commitment("08:40", "16:10", "work", requires_travel=True, travel_time_min=75, commitment_id="fc-workday")],
        "device_wear": [wear("06:45", "23:00", "worn")],
        "fixture": "public_transport_commuter_day",
        "expectation": "documented delay/crowding may be referenced in a note; undocumented delays must be rejected",
    }


def no_journeys_day(participant_id: str = "fixture-nojourney", day: Any = "2026-05-07") -> dict[str, Any]:
    episodes = [
        episode("07:30", "08:00", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("08:00", "08:30", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("08:30", "09:00", "sitting", "self_care", "home", "alone", "indoor", purpose="breakfast", exertion=0.05),
        episode("09:00", "11:30", "sitting", "work", "home", "alone", "indoor", purpose="work", exertion=0.05),
        episode("11:30", "12:00", "standing", "household", "home", "alone", "indoor", purpose="chores", exertion=0.25),
        episode("12:00", "12:40", "sitting", "self_care", "home", "alone", "indoor", purpose="lunch", exertion=0.05),
        episode("12:40", "15:30", "sitting", "work", "home", "alone", "indoor", purpose="work", exertion=0.05),
        episode("15:30", "16:10", "walking", "exercise", "park", "alone", "outdoor", purpose="walk", exertion=0.4),
        episode("16:10", "17:30", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("17:30", "18:20", "standing", "household", "home", "alone", "indoor", purpose="cooking", exertion=0.25),
        episode("18:20", "19:00", "sitting", "self_care", "home", "alone", "indoor", purpose="dinner", exertion=0.05),
        episode("19:00", "21:30", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("21:30", "22:30", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("22:30", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "08:00",
        "sleep_time": "22:30",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": [],
        "fixed_commitments": [],
        "fixture": "no_journeys_day",
        "expectation": "no post_trip event; enrichment must come from the walk or a transition, never fabricated",
    }


def exercise_day(participant_id: str = "fixture-exercise", day: Any = "2026-05-08") -> dict[str, Any]:
    episodes = [
        episode("06:00", "06:45", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("06:45", "07:05", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("07:05", "07:20", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("07:20", "08:20", "running", "exercise", "park", "alone", "outdoor", purpose="exercise", exertion=0.9),
        episode("08:20", "08:50", "standing", "self_care", "gym", "with_strangers", "indoor", purpose="shower", exertion=0.2),
        episode("08:50", "09:20", "sitting", "self_care", "food_venue", "alone", "indoor", purpose="breakfast", exertion=0.05),
        episode("09:20", "12:00", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("12:00", "12:35", "sitting", "social", "food_venue", "with_colleagues", "indoor", purpose="lunch", exertion=0.05),
        episode("12:35", "16:00", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("16:00", "16:20", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("16:20", "17:30", "other_vigorous", "exercise", "gym", "with_strangers", "indoor", purpose="exercise", exertion=0.8),
        episode("17:30", "18:00", "standing", "self_care", "gym", "alone", "indoor", purpose="shower", exertion=0.2),
        episode("18:00", "18:30", "walking", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.3),
        episode("18:30", "19:15", "sitting", "household", "home", "with_partner", "indoor", purpose="dinner", exertion=0.05),
        episode("19:15", "21:00", "sitting", "leisure", "home", "with_partner", "indoor", purpose="leisure", exertion=0.05),
        episode("21:00", "22:00", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("22:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    journeys = [journey("07:05", "07:20", "walk", "exercise", "home", "park", journey_id="jn-run-out")]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "06:45",
        "sleep_time": "22:00",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": journeys,
        "fixed_commitments": [commitment("09:20", "16:00", "work", requires_travel=True, travel_time_min=20, commitment_id="fc-workday")],
        "device_wear": [wear("06:45", "08:20", "not_worn", "charging"), wear("08:20", "22:00", "worn")],
        "fixture": "exercise_day",
        "expectation": "post_active_episode events after the run and the gym session; no prompt inside running/vigorous activity",
    }


def highly_fragmented_day(participant_id: str = "fixture-fragmented", day: Any = "2026-05-09") -> dict[str, Any]:
    episodes = [
        episode("06:30", "07:00", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("07:00", "07:10", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
    ]
    minute = hhmm("07:10")
    activities = [
        ("walking", "household", "home", "indoor", 0.3),
        ("sitting", "work", "home", "indoor", 0.05),
        ("standing", "household", "home", "indoor", 0.2),
        ("walking", "childcare", "home", "indoor", 0.3),
        ("sitting", "leisure", "home", "indoor", 0.05),
        ("standing", "self_care", "home", "indoor", 0.15),
    ]
    index = 0
    while minute < hhmm("21:00"):
        activity, domain, place, environment, exertion = activities[index % len(activities)]
        duration = 6.0 + (index % 3) * 2.0  # 6-10 minute fragments
        end = min(minute + duration, hhmm("21:00"))
        if end - minute < 2:
            break
        stability = "unstable" if index % 5 == 4 else None
        episodes.append(
            episode(
                f"{int(minute // 60):02d}:{int(minute % 60):02d}",
                f"{int(end // 60):02d}:{int(end % 60):02d}",
                activity,
                domain,
                place,
                "with_children" if domain == "childcare" else "alone",
                environment,
                purpose=domain,
                exertion=exertion,
                stability=stability,
                discretionary_event="errand" if index % 7 == 3 else None,
            )
        )
        minute = end
        index += 1
    episodes.append(episode("21:00", "22:30", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02))
    episodes.append(episode("22:30", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"))
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "07:00",
        "sleep_time": "22:30",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": [],
        "fixed_commitments": [],
        "fixture": "highly_fragmented_day",
        "expectation": "stability margins remove many minutes; the scheduler must still place 5 legal opportunities or report infeasibility explicitly",
    }


def mostly_home_day(participant_id: str = "fixture-home", day: Any = "2026-05-10") -> dict[str, Any]:
    episodes = [
        episode("08:00", "08:40", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("08:40", "09:10", "standing", "self_care", "home", "with_family", "indoor", purpose="morning routine", exertion=0.2),
        episode("09:10", "09:50", "sitting", "self_care", "home", "with_family", "indoor", purpose="breakfast", exertion=0.05),
        episode("09:50", "11:30", "standing", "household", "home", "with_children", "indoor", purpose="chores", exertion=0.3, discretionary_event="household"),
        episode("11:30", "12:20", "sitting", "leisure", "home", "with_children", "indoor", purpose="leisure", exertion=0.05),
        episode("12:20", "13:00", "sitting", "household", "home", "with_family", "indoor", purpose="lunch", exertion=0.05),
        episode("13:00", "14:30", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("14:30", "16:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("16:00", "17:00", "walking", "leisure", "outdoor_generic", "with_children", "outdoor", purpose="walk", exertion=0.35),
        episode("17:00", "18:00", "standing", "household", "home", "with_family", "indoor", purpose="cooking", exertion=0.25),
        episode("18:00", "19:00", "sitting", "social", "home", "with_family", "indoor", purpose="dinner", exertion=0.05),
        episode("19:00", "21:00", "sitting", "leisure", "home", "with_family", "indoor", purpose="leisure", exertion=0.05),
        episode("21:00", "22:00", "standing", "self_care", "home", "alone", "indoor", purpose="self care", exertion=0.15),
        episode("22:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "08:40",
        "sleep_time": "22:00",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": [],
        "fixed_commitments": [],
        "device_wear": [wear("08:40", "22:00", "worn")],
        "fixture": "mostly_home_day",
        "expectation": "place type stays 'home'; enrichment can only come from the walk or a transition, never from an invented outing",
    }


def no_eligible_event_day(participant_id: str = "fixture-noevent", day: Any = "2026-05-11") -> dict[str, Any]:
    """A day with no journeys, no exercise bout and no meaningful transition.

    Every waking episode shares the same activity, domain, place type, social
    setting and environment, so the event detector finds nothing to enrich with.
    This is the fixture that proves the protocol does not fabricate an event
    category in order to look diverse.
    """
    episodes = [
        episode("07:45", "08:15", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("08:15", "10:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("10:00", "12:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("12:00", "14:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("14:00", "16:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("16:00", "18:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("18:00", "20:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("20:00", "22:30", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("22:30", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "08:15",
        "sleep_time": "22:30",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": [],
        "fixed_commitments": [],
        "fixture": "no_eligible_event_day",
        "expectation": "all five opportunities must be semi_random; no artificial event category may be invented",
    }


def evening_shift_day(participant_id: str = "fixture-eveningshift", day: Any = "2026-05-12") -> dict[str, Any]:
    episodes = [
        episode("09:30", "10:15", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("10:15", "10:45", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("10:45", "11:20", "sitting", "self_care", "home", "alone", "indoor", purpose="breakfast", exertion=0.05),
        episode("11:20", "13:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure", exertion=0.05),
        episode("13:00", "13:40", "sitting", "household", "home", "alone", "indoor", purpose="lunch", exertion=0.05),
        episode("13:40", "15:00", "walking", "leisure", "park", "alone", "outdoor", purpose="walk", exertion=0.35),
        episode("15:00", "15:40", "standing", "self_care", "home", "alone", "indoor", purpose="self care", exertion=0.15),
        episode("15:40", "16:10", "driving", "transport", "vehicle", "alone", "indoor", purpose="commute", exertion=0.1),
        episode("16:10", "16:30", "standing", "work", "healthcare", "with_colleagues", "indoor", purpose="work", exertion=0.2),
        episode("16:30", "19:00", "standing", "work", "healthcare", "with_colleagues", "indoor", purpose="shift", exertion=0.35, is_fixed_commitment=True),
        episode("19:00", "19:30", "sitting", "work", "healthcare", "with_colleagues", "indoor", purpose="break", exertion=0.05),
        episode("19:30", "22:30", "standing", "work", "healthcare", "with_colleagues", "indoor", purpose="shift", exertion=0.35, is_fixed_commitment=True),
        episode("22:30", "23:00", "driving", "transport", "vehicle", "alone", "indoor", purpose="commute", exertion=0.1),
        episode("23:00", "23:20", "sitting", "self_care", "home", "alone", "indoor", purpose="dinner", exertion=0.05),
        episode("23:20", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    journeys = [
        journey("15:40", "16:10", "car", "commute", "home", "healthcare", journey_id="jn-shift-am"),
        journey("22:30", "23:00", "car", "commute", "healthcare", "home", journey_id="jn-shift-pm"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "10:15",
        "sleep_time": "23:20",
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": journeys,
        "fixed_commitments": [commitment("16:30", "22:30", "work", requires_travel=True, travel_time_min=30, commitment_id="fc-shift")],
        "device_wear": [wear("10:15", "23:20", "worn")],
        "persona_context": {"work_schedule_pattern": "shift"},
        "fixture": "evening_shift_day",
        "expectation": "late waking window use; no prompt while driving; shift-work persona fact may only affect schedule pressure",
    }


def unresolved_movement_day(participant_id: str = "fixture-unresolved", day: Any = "2026-05-13") -> dict[str, Any]:
    episodes = [
        episode("07:00", "07:30", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("07:30", "08:00", "standing", "self_care", "home", "alone", "indoor", purpose="morning routine", exertion=0.2),
        episode("08:00", "08:30", "sitting", "self_care", "home", "with_partner", "indoor", purpose="breakfast", exertion=0.05),
        # planned cycling commute that did not happen (non-realised movement)
        episode("08:30", "09:00", "cycling", "transport", "street", "alone", "outdoor", purpose="commute", exertion=0.7, is_realised=False, stability="non_realised", episode_id="ep-cancelled-ride"),
        episode("09:00", "09:20", "sitting", "transport", "vehicle", "with_strangers", "indoor", purpose="commute", exertion=0.05),
        # unresolved interval: sensor could not classify this segment
        episode("09:20", "09:50", "unknown", "other", "other_building", "unknown", "indoor", purpose=None, stability="unresolved", episode_id="ep-unresolved-segment"),
        episode("09:50", "12:00", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("12:00", "12:35", "sitting", "social", "food_venue", "with_colleagues", "indoor", purpose="lunch", exertion=0.05),
        episode("12:35", "13:05", "walking", "leisure", "park", "alone", "outdoor", purpose="walk", exertion=0.35),
        episode("13:05", "16:30", "sitting", "work", "workplace", "with_colleagues", "indoor", purpose="work", exertion=0.05),
        episode("16:30", "17:00", "public_transport", "transport", "vehicle", "with_strangers", "indoor", purpose="commute", exertion=0.05),
        episode("17:00", "18:00", "standing", "household", "home", "alone", "indoor", purpose="cooking", exertion=0.25),
        episode("18:00", "19:00", "sitting", "social", "home", "with_partner", "indoor", purpose="dinner", exertion=0.05),
        episode("19:00", "21:30", "sitting", "leisure", "home", "with_partner", "indoor", purpose="leisure", exertion=0.05),
        episode("21:30", "22:30", "lying_awake", "leisure", "home", "alone", "indoor", purpose="rest", exertion=0.02),
        episode("22:30", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    intervals = sensor_intervals(episodes)
    intervals.append(interval("09:20", "09:50", kind="unclassified", resolved=False, realised=True, stability="unstable", interval_id="iv-unresolved-1"))
    intervals.append(interval("08:30", "09:00", kind="travel", resolved=True, realised=False, interval_id="iv-nonrealised-1"))
    journeys = [
        journey("09:00", "09:20", "bus", "commute", "home", "workplace", journey_id="jn-bus-am"),
        journey("16:30", "17:00", "bus", "commute", "workplace", "home", journey_id="jn-bus-pm"),
    ]
    return {
        "participant_id": participant_id,
        "date": day,
        "wake_time": "07:30",
        "sleep_time": "22:30",
        "episodes": episodes,
        "intervals": intervals,
        "journeys": journeys,
        "fixed_commitments": [commitment("09:50", "16:30", "work", requires_travel=True, travel_time_min=40, commitment_id="fc-workday")],
        "fixture": "unresolved_movement_day",
        "expectation": "no prompt inside the non-realised ride or the unresolved interval; both must be reported as excluded minutes",
    }


FIXTURE_BUILDERS: dict[str, Any] = {
    "normal_office_day": normal_office_day,
    "cycling_commuter_day": cycling_commuter_day,
    "public_transport_commuter_day": public_transport_commuter_day,
    "no_journeys_day": no_journeys_day,
    "exercise_day": exercise_day,
    "highly_fragmented_day": highly_fragmented_day,
    "mostly_home_day": mostly_home_day,
    "no_eligible_event_day": no_eligible_event_day,
    "evening_shift_day": evening_shift_day,
    "unresolved_movement_day": unresolved_movement_day,
}

FIXTURE_EXPECTATIONS: dict[str, str] = {name: builder()["expectation"] for name, builder in FIXTURE_BUILDERS.items()}


def build_fixture(name: str, participant_id: Optional[str] = None, day: Any = None) -> ContextualDay:
    if name not in FIXTURE_BUILDERS:
        raise KeyError(f"unknown fixture {name!r}; available: {sorted(FIXTURE_BUILDERS)}")
    kwargs: dict[str, Any] = {}
    if participant_id:
        kwargs["participant_id"] = participant_id
    if day:
        kwargs["day"] = day
    mapping = FIXTURE_BUILDERS[name](**kwargs)
    return contextual_day_from_mapping(mapping)


def fixture_mapping(name: str, **kwargs: Any) -> dict[str, Any]:
    if name not in FIXTURE_BUILDERS:
        raise KeyError(f"unknown fixture {name!r}")
    return FIXTURE_BUILDERS[name](**kwargs)


def all_fixtures(**kwargs: Any) -> dict[str, ContextualDay]:
    return {name: build_fixture(name, **kwargs) for name in FIXTURE_BUILDERS}


def legacy_diary_to_day(diary: Any, participant_id: str = "legacy", day: Any = "2026-04-07") -> ContextualDay:
    """Import a historical ``EMA-Diary-Generation`` diary (regression fixture).

    Provided so the historical output in ``EMA-Diary-Generation/output/`` can be
    fed through the new pipeline; the historical EMA probe blocks are ignored.
    """
    import json as _json

    if isinstance(diary, str):
        diary = _json.loads(diary)
    episodes = []
    for index, item in enumerate(diary.get("episodes", [])):
        episodes.append(
            episode(
                str(item.get("start_time", "12:00")),
                str(item.get("end_time", "12:30")),
                str(item.get("primary_activity", "sitting")),
                str(item.get("domain", "leisure")),
                place_type=str(item.get("location_type", "home")),
                social=str(item.get("social_context", "alone")),
                indoor_outdoor=str(item.get("indoor_outdoor", "indoor")),
                purpose=str(item.get("purpose") or "")[:40] or None,
                episode_id=item.get("id") or f"legacy-ep-{index:03d}",
            )
        )
    wear_periods = [
        wear(str(period.get("start", "00:00")), str(period.get("end", "00:00")), str(period.get("status", "worn")))
        for period in diary.get("device_wear_schedule", [])
    ]
    mapping = {
        "participant_id": participant_id,
        "date": day,
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": [],
        "device_wear": wear_periods,
        "source": "legacy:EMA-Diary-Generation",
    }
    return contextual_day_from_mapping(mapping)


# --------------------------------------------------------------------------
# demonstration cohort (multi-day)
# --------------------------------------------------------------------------

DEMO_ARCHETYPES: tuple[str, ...] = (
    "normal_office_day",
    "cycling_commuter_day",
    "public_transport_commuter_day",
    "mostly_home_day",
    "evening_shift_day",
)


def demo_day_mapping(
    archetype: str,
    participant_id: str,
    day: Any,
    seed: int = 0,
) -> dict[str, Any]:
    """Produce a day for the demonstration cohort from an archetype.

    The point of the cohort is **not** behavioural realism: it is to inspect
    sampling distribution, event/background balance, response rate, latency,
    subjective-state variation, continuity, note grounding, missingness and
    provenance across a contained multi-day run.
    """
    if archetype not in FIXTURE_BUILDERS:
        raise KeyError(f"unknown archetype {archetype!r}")
    rng = random.Random(f"paper3_ema|demo|{participant_id}|{day}|{seed}")
    mapping = FIXTURE_BUILDERS[archetype](participant_id=participant_id, day=day)
    episodes = list(mapping["episodes"])
    jittered: list[dict[str, Any]] = []
    for index, item in enumerate(episodes):
        item = dict(item)
        shift = rng.choice([-6, -3, 0, 0, 0, 3, 6]) if index else 0
        item["start_time"] = _shift_hhmm(item["start_time"], shift)
        item["end_time"] = _shift_hhmm(item["end_time"], shift if index < len(episodes) - 1 else 0)
        if rng.random() < 0.25 and index not in (0, len(episodes) - 1):
            item["social_context"] = rng.choice(["alone", "with_partner", "with_colleagues", "with_friends"])
        jittered.append(item)
    mapping["episodes"] = _resequence(jittered)
    mapping["intervals"] = sensor_intervals(mapping["episodes"])
    for journey_item in mapping.get("journeys", []):
        journey_item["delayed"] = rng.random() < 0.12
        journey_item["crowded"] = rng.random() < 0.18
    mapping["weather"] = rng.choice([None, None, "light rain", "cold and clear", "mild and overcast"])
    mapping["source"] = f"paper3_ema.fixtures:demo/{archetype}"
    return mapping


def _shift_hhmm(value: str, minutes: float) -> str:
    total = max(0.0, min(1439.0, hhmm(value) + minutes))
    return f"{int(total // 60):02d}:{int(total % 60):02d}"


def _resequence(episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Repair ordering/overlap introduced by jitter (fixtures only)."""
    ordered: list[dict[str, Any]] = []
    previous_end = 0.0
    for item in episodes:
        start = max(hhmm(item["start_time"]), previous_end)
        end = max(hhmm(item["end_time"]), start + 1)
        item["start_time"] = f"{int(start // 60):02d}:{int(start % 60):02d}"
        item["end_time"] = f"{int(min(end, 1439) // 60):02d}:{int(min(end, 1439) % 60):02d}"
        previous_end = min(end, 1439.0)
        ordered.append(item)
    return ordered


def demo_cohort(
    participants: int = 4,
    days: int = 7,
    start_date: Any = "2026-05-04",
    seed: int = 20260504,
    archetypes: Sequence[str] = DEMO_ARCHETYPES,
) -> list[dict[str, Any]]:
    """Return ``participants x days`` day mappings for the demonstration run."""
    start = start_date if isinstance(start_date, _date) else _date.fromisoformat(str(start_date))
    cohort: list[dict[str, Any]] = []
    for person_index in range(participants):
        archetype = archetypes[person_index % len(archetypes)]
        participant_id = f"demo-p{person_index + 1:02d}"
        for day_index in range(days):
            current = start + timedelta(days=day_index)
            cohort.append(
                demo_day_mapping(
                    archetype,
                    participant_id,
                    current.isoformat(),
                    seed=seed + person_index * 100 + day_index,
                )
            )
    return cohort

