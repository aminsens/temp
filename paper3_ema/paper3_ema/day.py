"""Import and normalisation of an externally supplied contextual day.

The EMA module is host-agnostic: it accepts any mapping that describes a day of
episodes / sensor intervals / journeys / fixed commitments, tolerates several
field-naming conventions, and refuses to invent anything that is absent.

Nothing in this module imports DayForge or Appa.  The legacy importer for the
historical ``EMA-Diary-Generation`` diary format lives in
:mod:`paper3_ema.legacy` and simply produces the same generic mapping.
"""

from __future__ import annotations

from datetime import date as _date
from datetime import datetime
from typing import Any, Iterable, Mapping, Optional, Sequence

from .config import ProtocolConfig, default_config
from .models import (
    ContextualDay,
    EpisodeRef,
    FixedCommitmentRef,
    IntervalRef,
    JourneyRef,
    WearPeriodRef,
)
from .timeutil import Interval, clip_to_day, format_hhmm, parse_hhmm, to_date
from .vocab import (
    DeviceWear,
    normalise_activity,
    normalise_device_wear,
    normalise_domain,
    normalise_indoor_outdoor,
    normalise_place_type,
    normalise_social,
)

DAY_MINUTES = 24 * 60


class DayImportError(ValueError):
    """Raised when a supplied day cannot be interpreted at all."""


# --------------------------------------------------------------------------
# tolerant field access
# --------------------------------------------------------------------------

def _pick(data: Mapping[str, Any], names: Sequence[str], default: Any = None) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def _to_minutes(value: Any, day: Optional[_date] = None) -> Optional[float]:
    """Convert a time representation to minutes after midnight of ``day``."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        # a value > 1440 is assumed to be an ISO-ish minute count or epoch-free
        return number if number <= DAY_MINUTES else number % DAY_MINUTES
    if isinstance(value, datetime):
        return value.hour * 60 + value.minute + value.second / 60.0
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:  # ISO datetime
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.hour * 60 + parsed.minute + parsed.second / 60.0
    if ":" in text:
        return float(parse_hhmm(text))
    try:
        return float(text)
    except ValueError as exc:  # pragma: no cover - defensive
        raise DayImportError(f"cannot interpret time value {value!r}") from exc


def _to_span(data: Mapping[str, Any], day: Optional[_date]) -> tuple[Optional[float], Optional[float]]:
    start = _to_minutes(_pick(data, ("start_min", "start_minute", "start", "start_time", "begin", "from", "onset")), day)
    end = _to_minutes(_pick(data, ("end_min", "end_minute", "end", "end_time", "stop", "to", "offset")), day)
    if start is None and end is None:
        return None, None
    if start is None:
        start = max(0.0, (end or 0.0))
    if end is None:
        duration = _pick(data, ("duration_min", "duration_minutes", "duration"))
        end = start + float(duration) if duration is not None else start
    start, end, _ = clip_to_day(float(start), float(end))
    return start, end


def _optional_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "1", "y", "on"}:
        return True
    if text in {"false", "no", "0", "n", "off"}:
        return False
    return None


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# --------------------------------------------------------------------------
# element importers
# --------------------------------------------------------------------------

def _import_episode(raw: Mapping[str, Any], index: int, day: Optional[_date]) -> Optional[EpisodeRef]:
    start, end = _to_span(raw, day)
    if start is None or end is None or end <= start:
        return None
    episode_id = _optional_str(_pick(raw, ("episode_id", "id", "eid", "uid"))) or f"ep-{index:03d}"
    activity_raw = _pick(raw, ("activity", "primary_activity", "activity_type", "behaviour", "movement"))
    activity = normalise_activity(activity_raw)
    exertion = _optional_float(_pick(raw, ("exertion", "intensity_norm", "relative_exertion", "met_norm")))
    if exertion is None:
        intensity = _optional_str(_pick(raw, ("intensity", "intensity_level")))
        exertion = {"sedentary": 0.05, "light": 0.25, "moderate": 0.55, "vigorous": 0.85}.get((intensity or "").lower())
    realised = _optional_bool(_pick(raw, ("is_realised", "realised", "realized", "occurred", "completed")))
    stability = _optional_str(_pick(raw, ("stability", "interval_stability", "transition_state", "state")))
    return EpisodeRef(
        episode_id=episode_id,
        start_min=start,
        end_min=end,
        activity=activity,
        activity_label=_optional_str(activity_raw) if activity is None else None,
        domain=normalise_domain(_pick(raw, ("domain", "behavioural_domain", "behavioral_domain", "purpose_domain"))),
        place_type=normalise_place_type(_pick(raw, ("place_type", "location_type", "place", "location", "setting"))),
        place_label=_optional_str(_pick(raw, ("place_label", "location_label"))),
        social=normalise_social(_pick(raw, ("social", "social_context", "company", "with_whom"))),
        indoor_outdoor=normalise_indoor_outdoor(_pick(raw, ("indoor_outdoor", "indoors_outdoors", "environment"))),
        purpose=_optional_str(_pick(raw, ("purpose", "purpose_category", "activity_purpose"))),
        exertion=exertion,
        is_fixed_commitment=bool(_optional_bool(_pick(raw, ("is_fixed_commitment", "fixed_commitment", "is_fixed", "scheduled")))),
        discretionary_event=_optional_str(_pick(raw, ("discretionary_event", "event_type", "discretionary"))),
        interval_id=_optional_str(_pick(raw, ("interval_id", "sensor_interval_id", "interval"))),
        is_realised=True if realised is None else realised,
        stability=stability,
    )


def _import_interval(raw: Mapping[str, Any], index: int, day: Optional[_date]) -> Optional[IntervalRef]:
    start, end = _to_span(raw, day)
    if start is None or end is None or end <= start:
        return None
    resolved = _optional_bool(_pick(raw, ("resolved", "is_resolved", "classified", "labelled", "labeled")))
    realised = _optional_bool(_pick(raw, ("realised", "is_realised", "realized", "occurred")))
    stability = _optional_str(_pick(raw, ("stability", "transition_state", "state")))
    return IntervalRef(
        interval_id=_optional_str(_pick(raw, ("interval_id", "id", "iid"))) or f"iv-{index:03d}",
        start_min=start,
        end_min=end,
        kind=_optional_str(_pick(raw, ("kind", "interval_kind", "type", "category"))),
        resolved=True if resolved is None else resolved,
        realised=True if realised is None else realised,
        stability=stability,
        episode_id=_optional_str(_pick(raw, ("episode_id", "episode"))),
    )


def _import_journey(raw: Mapping[str, Any], index: int, day: Optional[_date]) -> Optional[JourneyRef]:
    start, end = _to_span(raw, day)
    if start is None or end is None or end <= start:
        return None
    return JourneyRef(
        journey_id=_optional_str(_pick(raw, ("journey_id", "id", "trip_id", "leg_id"))) or f"jn-{index:03d}",
        start_min=start,
        end_min=end,
        mode=_optional_str(_pick(raw, ("mode", "transport_mode", "travel_mode", "modality"))),
        purpose=_optional_str(_pick(raw, ("purpose", "trip_purpose"))),
        origin_place_type=normalise_place_type(_pick(raw, ("origin_place_type", "from_place_type", "origin_type"))),
        destination_place_type=normalise_place_type(
            _pick(raw, ("destination_place_type", "to_place_type", "destination_type"))
        ),
        distance_km=_optional_float(_pick(raw, ("distance_km", "distance", "length_km"))),
        delayed=_optional_bool(_pick(raw, ("delayed", "is_delayed", "disrupted", "late"))),
        crowded=_optional_bool(_pick(raw, ("crowded", "is_crowded", "overcrowded"))),
        episode_id=_optional_str(_pick(raw, ("episode_id", "episode"))),
        interval_id=_optional_str(_pick(raw, ("interval_id", "interval"))),
    )


def _import_commitment(raw: Mapping[str, Any], index: int, day: Optional[_date]) -> Optional[FixedCommitmentRef]:
    start, end = _to_span(raw, day)
    if start is None:
        return None
    if end is None or end <= start:
        duration = _optional_float(_pick(raw, ("duration_min", "duration_minutes", "duration")))
        end = start + (duration if duration else 30.0)
    end = min(end, float(DAY_MINUTES))
    return FixedCommitmentRef(
        commitment_id=_optional_str(_pick(raw, ("commitment_id", "id", "anchor_id"))) or f"fc-{index:03d}",
        start_min=start,
        end_min=end,
        label=_optional_str(_pick(raw, ("label", "kind", "type", "category"))),
        kind=_optional_str(_pick(raw, ("kind", "type", "category", "domain"))),
        requires_travel=bool(_optional_bool(_pick(raw, ("requires_travel", "needs_travel", "travel_required")))),
        travel_time_min=float(_optional_float(_pick(raw, ("travel_time_min", "travel_minutes"))) or 0.0),
    )


def _import_wear(raw: Mapping[str, Any], index: int, day: Optional[_date]) -> Optional[WearPeriodRef]:
    start, end = _to_span(raw, day)
    if start is None or end is None or end <= start:
        return None
    status = normalise_device_wear(_pick(raw, ("status", "wear_status", "state", "worn")))
    if status is None:
        return None
    return WearPeriodRef(
        start_min=start,
        end_min=end,
        status=status,
        reason=_optional_str(_pick(raw, ("reason", "note"))),
    )


def _import_windows(raw: Any, day: Optional[_date]) -> tuple[Interval, ...]:
    if not raw:
        return ()
    windows: list[Interval] = []
    for index, item in enumerate(raw):
        if isinstance(item, Mapping):
            start, end = _to_span(item, day)
            label = _optional_str(_pick(item, ("label", "name", "window_id", "id")))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            start, end = _to_minutes(item[0], day), _to_minutes(item[1], day)
            label = None
        else:  # pragma: no cover - defensive
            continue
        if start is None or end is None or end <= start:
            continue
        windows.append(Interval(float(start), float(end), label or f"w{index + 1}"))
    return tuple(windows)


# --------------------------------------------------------------------------
# public importer
# --------------------------------------------------------------------------

def contextual_day_from_mapping(
    data: Mapping[str, Any],
    config: Optional[ProtocolConfig] = None,
) -> ContextualDay:
    """Build a :class:`ContextualDay` from a generic mapping.

    Accepts (at minimum) ``participant_id``/``date`` plus one of ``episodes``,
    ``intervals`` or ``journeys``.  Missing elements stay empty; the module
    never fabricates them.
    """
    config = config or default_config()
    data = dict(data)
    day_value = _pick(data, ("date", "day", "day_date", "calendar_date"))
    try:
        day = to_date(day_value) if day_value is not None else _date(2026, 1, 1)
    except (TypeError, ValueError) as exc:
        raise DayImportError(f"cannot interpret date {day_value!r}") from exc

    participant_id = str(_pick(data, ("participant_id", "participant", "person_id", "pid", "id"), "participant"))

    episodes = [
        ep
        for ep in (
            _import_episode(raw, index, day)
            for index, raw in enumerate(_pick(data, ("episodes", "activities", "episode_list"), []) or [])
        )
        if ep is not None
    ]
    intervals = [
        iv
        for iv in (
            _import_interval(raw, index, day)
            for index, raw in enumerate(_pick(data, ("intervals", "sensor_intervals", "accel_intervals"), []) or [])
        )
        if iv is not None
    ]
    journeys = [
        jn
        for jn in (
            _import_journey(raw, index, day)
            for index, raw in enumerate(_pick(data, ("journeys", "trips", "legs", "travel"), []) or [])
        )
        if jn is not None
    ]
    commitments = [
        fc
        for fc in (
            _import_commitment(raw, index, day)
            for index, raw in enumerate(
                _pick(data, ("fixed_commitments", "commitments", "anchors", "appointments", "schedule"), []) or []
            )
        )
        if fc is not None
    ]
    wear = [
        wp
        for wp in (
            _import_wear(raw, index, day)
            for index, raw in enumerate(_pick(data, ("device_wear", "wear_periods", "wear_schedule"), []) or [])
        )
        if wp is not None
    ]
    windows = _import_windows(_pick(data, ("waking_windows", "daytime_windows", "windows", "strata")), day)

    if not episodes and not intervals and not journeys:
        raise DayImportError(
            "supplied day contains no episodes, intervals or journeys: the EMA module has no context to annotate"
        )

    wake = _to_minutes(_pick(data, ("wake_min", "wake_time", "waking_time", "woke_at", "wake")), day)
    sleep = _to_minutes(_pick(data, ("sleep_min", "sleep_time", "bed_time", "bedtime", "sleep_onset")), day)
    if wake is None:
        wake = _infer_wake(episodes)
    if sleep is None:
        sleep = _infer_sleep(episodes)

    if not windows:
        windows = default_waking_windows(config)

    return ContextualDay(
        participant_id=participant_id,
        day=day,
        wake_min=wake,
        sleep_min=sleep,
        episodes=tuple(sorted(episodes, key=lambda ep: (ep.start_min, ep.end_min))),
        intervals=tuple(sorted(intervals, key=lambda iv: (iv.start_min, iv.end_min))),
        journeys=tuple(sorted(journeys, key=lambda jn: (jn.start_min, jn.end_min))),
        fixed_commitments=tuple(sorted(commitments, key=lambda fc: fc.start_min)),
        device_wear=tuple(sorted(wear, key=lambda wp: wp.start_min)),
        waking_windows=windows,
        weather=_optional_str(_pick(data, ("weather", "weather_summary"))),
        timezone=str(_pick(data, ("timezone", "tz"), "local")),
        source=str(_pick(data, ("source", "generator"), "external")),
        notes=_optional_str(_pick(data, ("notes", "day_notes"))),
    )


def _infer_wake(episodes: Sequence[EpisodeRef]) -> Optional[float]:
    from .vocab import Activity

    sleeping = [ep for ep in episodes if ep.activity == Activity.SLEEPING]
    morning = [ep for ep in sleeping if ep.end_min <= 12 * 60]
    if morning:
        return min(ep.end_min for ep in morning)
    if episodes:
        return min(ep.start_min for ep in episodes)
    return None


def _infer_sleep(episodes: Sequence[EpisodeRef]) -> Optional[float]:
    from .vocab import Activity

    sleeping = [ep for ep in episodes if ep.activity == Activity.SLEEPING]
    evening = [ep for ep in sleeping if ep.start_min >= 12 * 60]
    if evening:
        return max(ep.start_min for ep in evening)
    if episodes:
        return max(ep.end_min for ep in episodes)
    return None


def default_waking_windows(config: Optional[ProtocolConfig] = None) -> tuple[Interval, ...]:
    """Eight equal daytime strata spanning the configured span (default 08:00-23:00).

    The window set is *host-supplied when available*; this default exists so the
    standalone module can run on a day that does not carry stratification.
    """
    config = config or default_config()
    start = float(parse_hhmm(str(config.get("sampling.waking_windows.default_start", "08:00"))))
    end = float(parse_hhmm(str(config.get("sampling.waking_windows.default_end", "23:00"))))
    count = max(1, int(config.get("sampling.waking_windows.default_count", 8)))
    if end <= start:
        raise DayImportError("waking window span must be positive")
    width = (end - start) / count
    return tuple(
        Interval(start + i * width, start + (i + 1) * width, f"w{i + 1}") for i in range(count)
    )


def describe_day(day: ContextualDay) -> dict[str, Any]:
    """Compact human-readable summary of an imported day (diagnostics only)."""
    return {
        "participant_id": day.participant_id,
        "date": day.day.isoformat(),
        "episodes": len(day.episodes),
        "intervals": len(day.intervals),
        "journeys": len(day.journeys),
        "fixed_commitments": len(day.fixed_commitments),
        "device_wear_periods": len(day.device_wear),
        "waking_windows": [f"{format_hhmm(w.start)}-{format_hhmm(w.end)}" for w in day.waking_windows],
        "wake": format_hhmm(day.wake_min) if day.wake_min is not None else None,
        "sleep": format_hhmm(day.sleep_min) if day.sleep_min is not None else None,
        "episode_coverage_min": round(day.coverage_minutes(), 1),
        "unresolved_intervals": [iv.interval_id for iv in day.intervals if not iv.resolved],
        "non_realised": [ep.episode_id for ep in day.episodes if not ep.is_realised],
        "unstable_episodes": [ep.episode_id for ep in day.episodes if ep.is_unstable],
        "fingerprint": day.fingerprint(),
    }


def day_to_mapping(day: ContextualDay) -> dict[str, Any]:
    """Round-trip representation (used by examples and tests)."""
    return {
        "participant_id": day.participant_id,
        "date": day.day.isoformat(),
        "wake_time": format_hhmm(day.wake_min) if day.wake_min is not None else None,
        "sleep_time": format_hhmm(day.sleep_min) if day.sleep_min is not None else None,
        "weather": day.weather,
        "waking_windows": [
            {"start_time": format_hhmm(w.start), "end_time": format_hhmm(w.end), "label": w.label}
            for w in day.waking_windows
        ],
        "episodes": [ep.to_dict() for ep in day.episodes],
        "intervals": [iv.to_dict() for iv in day.intervals],
        "journeys": [jn.to_dict() for jn in day.journeys],
        "fixed_commitments": [fc.to_dict() for fc in day.fixed_commitments],
        "device_wear": [wp.to_dict() for wp in day.device_wear],
    }


def validate_day_input(day: ContextualDay) -> list[str]:
    """Read-only diagnostics about a supplied day (never repairs it)."""
    issues: list[str] = []
    ordered = sorted(day.episodes, key=lambda ep: ep.start_min)
    for previous, current in zip(ordered, ordered[1:]):
        if current.start_min < previous.end_min:
            issues.append(
                f"overlap: {previous.episode_id} [{format_hhmm(previous.start_min)}-{format_hhmm(previous.end_min)}] "
                f"overlaps {current.episode_id} [{format_hhmm(current.start_min)}-{format_hhmm(current.end_min)}]"
            )
        elif current.start_min - previous.end_min > 30:
            issues.append(
                f"gap: {current.start_min - previous.end_min:.0f} min uncovered before {current.episode_id}"
            )
    unknown_activity = [ep.episode_id for ep in day.episodes if ep.activity is None]
    if unknown_activity:
        issues.append(f"episodes with unmappable activity: {unknown_activity}")
    if not day.waking_windows:
        issues.append("no waking windows supplied or derivable")
    if day.wake_min is None:
        issues.append("wake time not supplied and not derivable")
    return issues
