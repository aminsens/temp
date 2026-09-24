"""Importer for the historical ``EMA-Diary-Generation`` diary format.

This is the *narrow adapter* surface mentioned in the design brief: any host
system (DayForge today, Appa later) supplies a day; the legacy importer proves
the contract by reading the repository's historical generated diaries
(``EMA-Diary-Generation/output/*.json``) without touching anything else in that
historical pipeline.

The historical diary carries: episodes (HETUS-coded), a device-wear schedule,
proper place names and narratives.  The importer

* maps ``primary_activity`` / ``domain`` / ``location_type`` /
  ``social_context`` / ``indoor_outdoor`` onto the Paper 3 vocabularies;
* keeps **place type only** — proper names (streets, buildings, POIs) are
  deliberately dropped from the EMA context packet (privacy + closed world);
* keeps the device-wear schedule (inherited fact, never fabricated);
* ignores the historical ``ema_probes`` blocks entirely — the historical
  corruption layer (standing under-reporting, forced misses, genericised
  locations) is not reused (see ``docs/PHASE0_ARCHAEOLOGY.md`` §2).
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from .context import coarse_purpose
from .day import ContextualDay, contextual_day_from_mapping
from .fixtures import episode, sensor_intervals, wear

LEGACY_ADAPTER_VERSION = "1.0.0"


def _normalise_activity(value: Any) -> str:
    """Historical activities are already close to the Paper 3 vocabulary."""
    text = str(value or "sitting").strip().lower()
    mapping = {
        "lying": "lying_awake",
        "lying_down": "lying_awake",
        "transition": "other_light",
        "public_transit": "public_transport",
        "transit": "public_transport",
        "motorcycle": "driving",
        "car_passenger": "driving",
    }
    if text in mapping:
        return mapping[text]
    if text in {"sleeping", "sleep", "asleep"}:
        return "sleeping"
    return text


def _activity_exertion(activity: str, purpose: Optional[str]) -> Optional[float]:
    """Coarse, documented exertion fallback for historical episodes (class C)."""
    if activity in {"running"}:
        return 0.85
    if activity in {"cycling"}:
        return 0.7
    if activity in {"walking"}:
        return 0.35
    if activity in {"other_vigorous"}:
        return 0.75
    if activity in {"standing"}:
        return 0.15
    if activity in {"sleeping", "lying_awake"}:
        return 0.0
    if purpose and "sleep" in str(purpose).lower():
        return 0.0
    return 0.05


def diary_to_day(
    diary: Mapping[str, Any] | str,
    participant_id: Optional[str] = None,
    day: Any = "2026-04-07",
    keep_wear_schedule: bool = True,
) -> ContextualDay:
    """Convert one historical diary mapping into a :class:`ContextualDay`.

    ``diary`` may be the full output wrapper (``{"persona": ..., "diary": ...}``)
    or the diary object itself.  The wrapper's ``diary`` field may be a JSON
    string (as in the historical test outputs).
    """
    if isinstance(diary, str):
        diary = json.loads(diary)
    wrapper_persona = None
    if isinstance(diary, Mapping):
        if isinstance(diary.get("persona"), Mapping):
            wrapper_persona = diary.get("persona")
        if "week" in diary:  # weekly wrapper: take the first day
            diary = diary["week"][0]
        if "diary" in diary:
            diary = diary["diary"]
    if isinstance(diary, str):
        diary = json.loads(diary)
    if not isinstance(diary, Mapping):
        raise TypeError("diary_to_day expects a mapping (or JSON string) describing a diary")

    persona = wrapper_persona or (diary.get("persona") if isinstance(diary.get("persona"), Mapping) else {}) or {}
    pid = participant_id or str(persona.get("name") or "legacy-participant").replace(" ", "-").lower()

    episodes = []
    for index, item in enumerate(diary.get("episodes", [])):
        # Proper names are never carried into the EMA context: the host
        # free-text purpose is reduced to the coarse purpose category the
        # context builder uses (or dropped when it does not map).
        raw_purpose = str(item.get("purpose") or "").strip() or None
        purpose = coarse_purpose(raw_purpose, None)
        activity = _normalise_activity(item.get("primary_activity"))
        episodes.append(
            episode(
                str(item.get("start_time", "12:00")),
                str(item.get("end_time", "12:30")),
                activity,
                str(item.get("domain", "leisure")),
                place_type=str(item.get("location_type", "home")),
                social=str(item.get("social_context", "alone")),
                indoor_outdoor=str(item.get("indoor_outdoor", "indoor")),
                purpose=purpose,
                exertion=_activity_exertion(activity, purpose),
                episode_id=item.get("id") or f"legacy-ep-{index:03d}",
            )
        )

    wear_periods = []
    if keep_wear_schedule:
        for period in diary.get("device_wear_schedule", []):
            status = str(period.get("status", "worn"))
            if status not in {"worn", "not_worn", "partially_worn"}:
                status = "worn" if "worn" in status else "not_worn"
            wear_periods.append(
                wear(str(period.get("start", "00:00")), str(period.get("end", "00:00")), status)
            )

    wake, sleep = None, None
    for item in diary.get("episodes", []):
        if item.get("primary_activity") in {"sleeping", "sleep", "lying"} and str(
            item.get("purpose") or ""
        ).startswith("sleep"):
            start = item.get("start_time")
            end = item.get("end_time")
            if start and end:
                if str(end) in {"23:59", "24:00"} or str(start) >= "22:00":
                    sleep = end
                elif str(start) <= "09:00":
                    wake = end
    if wake is None:
        for item in diary.get("episodes", []):
            wake = item.get("start_time")
            break

    mapping: dict[str, Any] = {
        "participant_id": pid,
        "date": day,
        "episodes": episodes,
        "intervals": sensor_intervals(episodes),
        "journeys": [],
        "device_wear": wear_periods,
        "source": "legacy:EMA-Diary-Generation",
    }
    if wake is not None:
        mapping["wake_time"] = wake
    if sleep is not None:
        mapping["sleep_time"] = sleep
    return contextual_day_from_mapping(mapping)


def load_historical_diary(path: str, participant_id: Optional[str] = None, day: Any = "2026-04-07") -> ContextualDay:
    """Load one of the repository's historical generated diaries."""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return diary_to_day(data, participant_id=participant_id, day=day)
