"""Read-only schedule auditor.

``audit_schedule(day, prompt_times, config)`` takes an *existing* schedule —
for example one produced by a host system such as Appa or DayForge — and
reports ``VALID`` or ``NEEDS_REPAIR`` with explicit reasons.

The auditor never alters the schedule.  Repair is the caller's decision: either
re-run :func:`paper3_ema.scheduler.schedule_prompts` or fix the host schedule.

Checks (Paper 3):

* exactly five prompts;
* waking-window membership;
* excluded activities / sleep / unresolved / non-realised / unstable times;
* spread across the day;
* clustering (minimum gap, maximum prompts per window);
* event enrichment (>= 3 background, <= 2 event-enriched, and enrichment when
  eligible events exist);
* valid episode / interval / journey linkage.
"""

from __future__ import annotations

from datetime import date as _date
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from .config import ProtocolConfig, default_config
from .day import ContextualDay, contextual_day_from_mapping
from .eligibility import DayEligibility
from .events import detect_events
from .models import EMAPrompt, ScheduleAuditIssue, ScheduleAuditResult
from .timeutil import format_hhmm, minute_of_day, parse_hhmm, to_date
from .vocab import AuditStatus, TriggerType, normalise_trigger

AUDITOR_VERSION = "1.0.0"


# --------------------------------------------------------------------------
# prompt-time coercion
# --------------------------------------------------------------------------

def _coerce_prompt_times(
    prompt_times: Sequence[Any],
    day: ContextualDay,
) -> list[tuple[float, Optional[str], Optional[TriggerType], Mapping[str, Any]]]:
    """Accept HH:MM strings, datetimes, minute numbers, EMAPrompt or mappings."""
    coerced: list[tuple[float, Optional[str], Optional[TriggerType], Mapping[str, Any]]] = []
    for item in prompt_times:
        trigger: Optional[TriggerType] = None
        raw: Mapping[str, Any] = {}
        prompt_id: Optional[str] = None
        if isinstance(item, EMAPrompt):
            minute = item.prompt_time_min
            trigger = item.trigger
            prompt_id = item.prompt_id
            raw = {"episode_id": item.episode_id, "interval_id": item.interval_id, "journey_id": item.journey_id,
                   "event_id": item.event_id, "window_index": item.window_index,
                   "stability_relaxed": bool(item.stability_relaxed)}
        elif isinstance(item, datetime):
            minute = minute_of_day(item)
        elif isinstance(item, Mapping):
            raw = item
            value = item.get("prompt_time_min")
            if value is None:
                value = item.get("prompt_time") or item.get("time") or item.get("timestamp")
            minute = _minute_from(value, day.day)
            trigger = normalise_trigger(item.get("trigger") or item.get("prompt_type") or item.get("trigger_type"))
            prompt_id = item.get("prompt_id") or item.get("id")
        elif isinstance(item, (int, float)):
            minute = float(item)
        else:
            minute = _minute_from(item, day.day)
        coerced.append((float(minute), prompt_id, trigger, raw))
    return sorted(coerced, key=lambda entry: entry[0])


def _minute_from(value: Any, day: _date) -> float:
    if value is None:
        raise ValueError("prompt time is required for every audited prompt")
    if isinstance(value, datetime):
        return minute_of_day(value)
    if isinstance(value, (int, float)):
        number = float(value)
        return number if number <= 1440 else number % 1440
    text = str(value).strip()
    if "T" in text:
        return minute_of_day(datetime.fromisoformat(text.replace("Z", "+00:00")))
    return float(parse_hhmm(text))


# --------------------------------------------------------------------------
# auditor
# --------------------------------------------------------------------------

def audit_schedule(
    day: ContextualDay | Mapping[str, Any],
    prompt_times: Sequence[Any],
    config: Optional[ProtocolConfig] = None,
    prompt_metadata: Optional[Sequence[Mapping[str, Any]]] = None,
) -> ScheduleAuditResult:
    """Audit an existing schedule.  Read-only: returns a verdict, never a fix."""
    config = config or default_config()
    if not isinstance(day, ContextualDay):
        day = contextual_day_from_mapping(day, config)

    entries = _coerce_prompt_times(prompt_times, day)
    if prompt_metadata:
        merged: list[tuple[float, Optional[str], Optional[TriggerType], Mapping[str, Any]]] = []
        for index, entry in enumerate(entries):
            extra = prompt_metadata[index] if index < len(prompt_metadata) else {}
            combined = dict(entry[3])
            combined.update({k: v for k, v in dict(extra).items() if v is not None})
            trigger = entry[2] or normalise_trigger(extra.get("trigger") or extra.get("prompt_type"))
            merged.append((entry[0], entry[1] or extra.get("prompt_id"), trigger, combined))
        entries = merged

    eligibility = DayEligibility.build(day, config)
    events = detect_events(day, eligibility, config)

    expected = int(config.get("sampling.opportunities_per_day", 5))
    min_background = int(config.get("sampling.min_background", 3))
    max_event = int(config.get("sampling.max_event_enriched", 2))
    min_gap = float(config.get("sampling.min_gap_minutes", 30))
    coverage = config.section("sampling.coverage")
    min_distinct_windows = int(coverage.get("min_distinct_windows", 3))
    max_per_window = int(coverage.get("max_prompts_per_window", 2))
    min_spread = float(coverage.get("min_spread_minutes", 210))
    require_window = bool(config.get("sampling.waking_windows.require_prompt_inside_window", True))

    issues: list[ScheduleAuditIssue] = []

    def add(code: str, severity: str, message: str, minute: Optional[float] = None) -> None:
        issues.append(
            ScheduleAuditIssue(
                code=code,
                severity=severity,
                message=message,
                prompt_time=format_hhmm(minute) if minute is not None else None,
            )
        )

    # ---- 1. count --------------------------------------------------------
    if len(entries) != expected:
        add(
            "prompt_count",
            "error",
            f"expected exactly {expected} EMA opportunities, found {len(entries)}",
        )

    windows = list(day.waking_windows)
    window_indices: list[Optional[int]] = []
    minutes: list[float] = []
    triggers: list[TriggerType] = []
    event_count = 0
    background_count = 0

    for index, (minute, prompt_id, trigger, meta) in enumerate(entries):
        minutes.append(minute)
        label = prompt_id or f"#{index + 1}"

        # ---- 2. waking-window membership --------------------------------
        window_index = day.window_of(minute)          # 0-based lookup index
        window_label = None if window_index is None else window_index + 1
        declared = meta.get("window_index")
        if declared is not None and window_label is not None and int(declared) != int(window_label):
            add(
                "window_linkage_mismatch",
                "error",
                f"{label}: declares window {declared} but {format_hhmm(minute)} falls in window {window_label}",
                minute,
            )
        window_indices.append(window_label)
        if require_window and window_label is None:
            spans = ", ".join(f"{format_hhmm(w.start)}-{format_hhmm(w.end)}" for w in windows) or "none supplied"
            add(
                "outside_waking_window",
                "error",
                f"{label}: {format_hhmm(minute)} is outside every daytime window ({spans})",
                minute,
            )

        # ---- 3. exclusions ----------------------------------------------
        relaxed = bool(meta.get("stability_relaxed"))
        if relaxed:
            exclusion = eligibility.relaxed_exclusion_at(minute)
            add(
                "stability_relaxed",
                "warning",
                f"{label}: boundary-stability margin relaxed for this prompt (highly fragmented day); "
                "all safety exclusions were still enforced",
                minute,
            )
        else:
            exclusion = eligibility.exclusion_at(minute)
        if exclusion.excluded:
            add(
                "excluded_context",
                "error",
                f"{label}: prompt at {format_hhmm(minute)} falls in an excluded context ({', '.join(exclusion.reasons)})",
                minute,
            )

        # ---- 4. trigger classification ----------------------------------
        resolved_trigger = trigger or TriggerType.SEMI_RANDOM
        if trigger is None:
            add(
                "trigger_unspecified",
                "warning",
                f"{label}: no trigger supplied; counted as semi_random for the balance checks",
                minute,
            )
        triggers.append(resolved_trigger)
        if resolved_trigger == TriggerType.SEMI_RANDOM:
            background_count += 1
        else:
            event_count += 1

        # ---- 5. linkage validity ----------------------------------------
        episode = day.episode_at(minute)
        episode_id = meta.get("episode_id")
        if episode_id is not None:
            known = {ep.episode_id for ep in day.episodes}
            if episode_id not in known:
                add("invalid_episode_linkage", "error", f"{label}: episode_id {episode_id!r} is not in the supplied day", minute)
            elif episode is not None and episode.episode_id != episode_id:
                add(
                    "episode_linkage_mismatch",
                    "error",
                    f"{label}: links episode {episode_id!r} but {format_hhmm(minute)} falls inside {episode.episode_id!r}",
                    minute,
                )
        interval_id = meta.get("interval_id")
        if interval_id is not None:
            known_intervals = {iv.interval_id for iv in day.intervals}
            if day.intervals and interval_id not in known_intervals:
                add("invalid_interval_linkage", "error", f"{label}: interval_id {interval_id!r} is not in the supplied day", minute)
            if episode is not None and episode.interval_id and episode.interval_id != interval_id:
                add(
                    "interval_linkage_mismatch",
                    "warning",
                    f"{label}: interval_id {interval_id!r} differs from the covering episode's interval {episode.interval_id!r}",
                    minute,
                )
        journey_id = meta.get("journey_id")
        if journey_id is not None:
            known_journeys = {jn.journey_id for jn in day.journeys}
            if journey_id not in known_journeys:
                add("invalid_journey_linkage", "error", f"{label}: journey_id {journey_id!r} is not in the supplied day", minute)
        event_id = meta.get("event_id")
        if event_id is not None:
            known_events = {ev.event_id for ev in events}
            if event_id not in known_events:
                add(
                    "unknown_event_linkage",
                    "warning",
                    f"{label}: event_id {event_id!r} is not reproducible from the supplied day",
                    minute,
                )
        if resolved_trigger != TriggerType.SEMI_RANDOM and not any(
            meta.get(key) for key in ("event_id", "journey_id", "episode_id")
        ):
            add(
                "event_linkage_missing",
                "error",
                f"{label}: event-enriched trigger {resolved_trigger.value} without episode/interval/journey linkage",
                minute,
            )

    # ---- 6. clustering ---------------------------------------------------
    for (left_minute, *_), (right_minute, *_) in zip(entries, entries[1:]):
        gap = right_minute - left_minute
        if gap <= 0:
            add("duplicate_prompt_time", "error", f"two prompts share the time {format_hhmm(left_minute)}", left_minute)
        elif gap < min_gap:
            add(
                "prompt_clustering",
                "error",
                f"only {gap:.0f} min between {format_hhmm(left_minute)} and {format_hhmm(right_minute)} "
                f"(minimum {min_gap:.0f} min)",
                right_minute,
            )

    # ---- 7. spread -------------------------------------------------------
    distinct_windows = {index for index in window_indices if index is not None}
    if len(distinct_windows) < min_distinct_windows:
        add(
            "insufficient_spread_windows",
            "error",
            f"prompts cover {len(distinct_windows)} daytime window(s); protocol requires at least {min_distinct_windows}",
        )
    if minutes:
        spread = minutes[-1] - minutes[0]
        if spread < min_spread:
            add(
                "insufficient_spread_minutes",
                "warning",
                f"first-to-last prompt span is {spread:.0f} min; protocol target is at least {min_spread:.0f} min",
            )
    for window_index in sorted(distinct_windows):
        count = sum(1 for index in window_indices if index == window_index)
        if count > max_per_window:
            add(
                "window_overload",
                "error",
                f"window {window_index} ({windows[window_index - 1]}) carries {count} prompts; maximum is {max_per_window}",
            )

    # ---- 8. event / background balance -----------------------------------
    if background_count < min_background:
        add(
            "insufficient_background",
            "error",
            f"only {background_count} semi-random (background) opportunity(ies); protocol requires at least {min_background}",
        )
    if event_count > max_event:
        add(
            "too_many_event_prompts",
            "error",
            f"{event_count} event-enriched opportunities; protocol allows at most {max_event}",
        )
    if events and event_count == 0:
        kinds = sorted({ev.kind.value for ev in events})
        add(
            "event_enrichment_missing",
            "error",
            f"the day contains {len(events)} eligible event(s) ({', '.join(kinds)}) but no event-enriched prompt was scheduled",
        )
    if not events and event_count > 0:
        add(
            "event_without_detected_event",
            "error",
            f"{event_count} prompt(s) claim an event trigger but no eligible event exists in the supplied day "
            "(fabricated event category)",
        )
    if not events:
        add(
            "no_eligible_events",
            "info",
            "no eligible event opportunities in this day; all five opportunities are semi-random (protocol-compliant)",
        )

    # ---- 9. post-event timing (when linkage is declared) -----------------
    horizon = float(config.get("sampling.max_minutes_after_event", 45))
    for (minute, prompt_id, trigger, meta) in entries:
        if not trigger or trigger == TriggerType.SEMI_RANDOM:
            continue
        event = next((ev for ev in events if ev.event_id == meta.get("event_id")), None)
        if event is None:
            continue
        delta = minute - event.end_min
        if delta < 0:
            add(
                "prompt_before_event_end",
                "error",
                f"{prompt_id or format_hhmm(minute)}: prompt precedes the end of its event {event.event_id}",
                minute,
            )
        elif delta > horizon:
            add(
                "prompt_too_far_after_event",
                "warning",
                f"{prompt_id or format_hhmm(minute)}: {delta:.0f} min after event {event.event_id} "
                f"(horizon {horizon:.0f} min)",
                minute,
            )

    status = AuditStatus.NEEDS_REPAIR if any(issue.severity == "error" for issue in issues) else AuditStatus.VALID
    metrics: dict[str, Any] = {
        "prompt_count": len(entries),
        "expected_prompt_count": expected,
        "background_count": background_count,
        "event_enriched_count": event_count,
        "distinct_windows": len(distinct_windows),
        "windows_used": sorted(distinct_windows),
        "spread_minutes": round(minutes[-1] - minutes[0], 1) if minutes else 0.0,
        "min_gap_minutes": round(min((b[0] - a[0] for a, b in zip(entries, entries[1:])), default=0.0), 1),
        "detected_events": len(events),
        "detected_event_kinds": sorted({ev.kind.value for ev in events}),
        "triggers": [trigger.value for trigger in triggers],
        "errors": sum(1 for issue in issues if issue.severity == "error"),
        "warnings": sum(1 for issue in issues if issue.severity == "warning"),
    }
    return ScheduleAuditResult(
        status=status,
        valid=status == AuditStatus.VALID,
        issues=issues,
        metrics=metrics,
        prompt_times=[format_hhmm(minute) for minute in minutes],
        auditor_version=AUDITOR_VERSION,
    )


def audit_bundle_prompts(
    day: ContextualDay | Mapping[str, Any],
    prompts: Sequence[EMAPrompt],
    config: Optional[ProtocolConfig] = None,
) -> ScheduleAuditResult:
    """Convenience wrapper: audit the prompts of a generated bundle."""
    return audit_schedule(day, list(prompts), config)


def summarise_audit(result: ScheduleAuditResult) -> str:
    """One-paragraph human-readable audit summary."""
    lines = [
        f"status={result.status.value} prompts={result.metrics.get('prompt_count')} "
        f"background={result.metrics.get('background_count')} event={result.metrics.get('event_enriched_count')} "
        f"windows={result.metrics.get('distinct_windows')} spread={result.metrics.get('spread_minutes')}min "
        f"errors={result.metrics.get('errors')} warnings={result.metrics.get('warnings')}"
    ]
    lines.extend(f"  - {reason}" for reason in result.reasons)
    return "\n".join(lines)
