"""Event-enriched stratified semi-random hybrid scheduler.

Paper 3 sampling design
-----------------------
Exactly ``sampling.opportunities_per_day`` (5) EMA opportunities per
participant-day:

* at least ``sampling.min_background`` (3) **background / semi-random**
  opportunities, drawn at random inside host-supplied daytime windows
  (stratified: each draw prefers a window that is not yet represented);
* at most ``sampling.max_event_enriched`` (2) **event-enriched** opportunities,
  taken in priority order ``post_trip > post_active_episode >
  meaningful_context_transition > discretionary_fallback`` and delivered
  **after** the event, at the first suitable stable opportunity.

When there are not enough eligible events, the remaining slots are filled with
semi-random draws.  Event categories are never fabricated to satisfy diversity
(``sampling.force_event_diversity: false``); if the day genuinely has no
eligible event, all five opportunities are semi-random and the bundle records
that fact.

The scheduler is seed-controlled and reproducible: identical
``(participant, date, seed, day, config)`` always produces an identical
schedule.  It never mutates the supplied day.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional, Sequence

from .audit import audit_schedule
from .config import ProtocolConfig, default_config
from .day import ContextualDay, contextual_day_from_mapping
from .eligibility import DayEligibility, candidate_minutes, relaxed_candidate_minutes
from .events import detect_events, rank_events
from .models import ContextualDay, DayEvent, EMARequest, EMAPrompt
from .timeutil import Interval, day_datetime, format_hhmm
from .vocab import AuditStatus, TriggerType

SCHEDULER_VERSION = "1.0.0"
DAY_MINUTES = 24 * 60


class SchedulingError(RuntimeError):
    """Raised when a day cannot support any legal prompt at all."""


@dataclass
class PromptPlacement:
    """Internal representation of one scheduled opportunity."""

    minute: float
    window_index: Optional[int]
    trigger: TriggerType
    event: Optional[DayEvent] = None
    episode_id: Optional[str] = None
    interval_id: Optional[str] = None
    journey_id: Optional[str] = None
    event_id: Optional[str] = None
    minutes_after_event: Optional[float] = None
    reason: str = ""

    @property
    def is_event_enriched(self) -> bool:
        return self.trigger != TriggerType.SEMI_RANDOM


# --------------------------------------------------------------------------
# seeding
# --------------------------------------------------------------------------

def stable_seed(participant_id: str, day_date: Any, seed: int) -> int:
    """Deterministic, participant/day-specific 64-bit seed (no Python ``hash``)."""
    date_text = day_date.isoformat() if hasattr(day_date, "isoformat") else str(day_date)
    material = f"paper3_ema|{participant_id}|{date_text}|{int(seed)}"
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


# --------------------------------------------------------------------------
# scheduling
# --------------------------------------------------------------------------

def schedule_for_day(
    day: ContextualDay,
    config: Optional[ProtocolConfig] = None,
    seed: int = 0,
) -> tuple[list[EMAPrompt], dict[str, Any]]:
    """Build the Paper 3 prompt schedule for one contextual day.

    Returns ``(prompts, info)`` where ``info`` carries diagnostics: detected
    events, per-window eligibility, unmet targets and the self-audit result.
    """
    config = config or default_config()
    eligibility = DayEligibility.build(day, config)
    events = rank_events(detect_events(day, eligibility, config))
    rng = random.Random(stable_seed(day.participant_id, day.day, seed))

    sampling = config.section("sampling")
    target = int(sampling.get("opportunities_per_day", 5))
    min_background = int(sampling.get("min_background", 3))
    max_event = int(sampling.get("max_event_enriched", 2))
    min_gap = float(sampling.get("min_gap_minutes", 30))
    search_minutes = float(sampling.get("post_event_search_minutes", 45))
    step = int(sampling.get("candidate_step_minutes", 1))
    allow_extra_background = bool(sampling.get("allow_background_to_exceed_min", True))
    prefix = str(sampling.get("prompt_id_prefix", "ema"))
    expiry = float(config.get("latency.expiry_minutes", 10))
    windows = list(day.waking_windows)
    if not windows:
        raise SchedulingError("the supplied day has no waking/daytime windows to stratify over")

    placements: list[PromptPlacement] = []
    notes: list[str] = []

    def gap_ok(minute: float) -> bool:
        return all(abs(minute - placed.minute) >= min_gap for placed in placements)

    def window_of(minute: float) -> Optional[int]:
        """1-based daytime window label (matches auditor and summary reporting)."""
        for index, window in enumerate(windows):
            if window.contains(minute):
                return index + 1
        return None

    # ---- 1. event-enriched slots ----------------------------------------
    event_slots = min(max_event, target - min_background) if allow_extra_background else max_event
    event_slots = max(0, min(event_slots, target))
    used_event_ids: set[str] = set()
    used_windows: set[int] = set()
    for event in events:
        if len([p for p in placements if p.is_event_enriched]) >= event_slots:
            break
        if event.event_id in used_event_ids:
            continue
        horizon = min(DAY_MINUTES, event.end_min + search_minutes)
        minute = eligibility.first_stable_minute(max(event.end_min, 0.0), horizon)
        relaxed_used = False
        if minute is None:
            minute = eligibility.first_relaxed_stable_minute(max(event.end_min, 0.0), horizon)
            relaxed_used = True
        if minute is None:
            continue
        window_label = window_of(float(minute))
        if window_label is None:
            continue
        if not gap_ok(float(minute)):
            continue
        if window_label in used_windows:
            continue  # keep event prompts in distinct daytime windows
        covering_episode = eligibility.episode_at(float(minute))
        covering_interval = eligibility.interval_at(float(minute))
        if relaxed_used:
            event = DayEvent(
                event_id=event.event_id,
                kind=event.kind,
                start_min=event.start_min,
                end_min=event.end_min,
                priority=event.priority,
                score=event.score,
                episode_id=event.episode_id,
                interval_id=event.interval_id,
                journey_id=event.journey_id,
                window_index=event.window_index,
                label=event.label,
                reason=event.reason + " [stability_relaxed]",
            )
        placements.append(
            PromptPlacement(
                minute=float(minute),
                window_index=window_label,
                trigger=event.kind,
                event=event,
                # LINKAGE RULE (Paper 3): episode_id / interval_id always identify
                # the context *at prompt time*; the triggering event keeps its own
                # source ids in event.episode_id / event.journey_id.
                episode_id=(covering_episode.episode_id if covering_episode else event.episode_id),
                interval_id=(covering_interval.interval_id if covering_interval else event.interval_id),
                journey_id=event.journey_id,
                event_id=event.event_id,
                minutes_after_event=round(float(minute) - event.end_min, 1),
                reason=(
                    f"event-enriched {event.kind.value}: {event.reason}; prompt placed at the first "
                    f"stable opportunity {float(minute) - event.end_min:.0f} min after the event "
                    f"(window {window_label}); episode/interval linkage resolved at prompt time"
                    + (" [stability_relaxed: fragmented day, boundary margin dropped]" if relaxed_used else "")
                ),
            )
        )
        used_event_ids.add(event.event_id)
        used_windows.add(window_label)

    # ---- 2. background (semi-random, stratified) slots -------------------
    background_target = max(min_background, target - len([p for p in placements if p.is_event_enriched]))
    background_target = min(background_target, target)
    window_minutes: dict[int, list[int]] = {}
    relaxed_windows: set[int] = set()
    for index, window in enumerate(windows):
        minutes = candidate_minutes(eligibility, window, step=step)
        if not minutes:
            minutes = relaxed_candidate_minutes(eligibility, window, step=step)
            if minutes:
                relaxed_windows.add(index)
        window_minutes[index] = minutes
    if relaxed_windows:
        notes.append(
            "HIGHLY FRAGMENTED DAY: strict boundary stability yields no legal minutes; "
            "relaxed fallback used in window(s) "
            + ", ".join(f"{index + 1} ({windows[index]})" for index in sorted(relaxed_windows))
            + " (all safety exclusions still enforced; boundary margin dropped; marker "
            "'stability_relaxed' recorded on affected prompts)"
        )
    empty_windows = [index for index, minutes in window_minutes.items() if not minutes]
    if empty_windows:
        notes.append(
            "no eligible prompt minute in window(s): "
            + ", ".join(f"{index + 1} ({windows[index]})" for index in sorted(empty_windows))
        )

    ordered = list(range(len(windows)))
    rng.shuffle(ordered)
    # stratification preference: unused windows first, then most eligible minutes
    ordered.sort(key=lambda index: ((index + 1) in used_windows, -len(window_minutes[index])))

    for index in ordered:
        if len([p for p in placements if not p.is_event_enriched]) >= background_target:
            break
        placements.extend(
            _draw_background(index, windows, window_minutes, placements, gap_ok, rng, notes, config, relaxed=index in relaxed_windows)
        )

    # ---- 3. top-up pass (only if the target is still unmet) --------------
    if len(placements) < target:
        notes.append(
            f"stratified pass produced {len(placements)}/{target} opportunities; running top-up pass "
            "over all windows (still semi-random, still exclusion-safe)"
        )
        rng.shuffle(ordered)
        for index in ordered:
            if len(placements) >= target:
                break
            placements.extend(
                _draw_background(
                    index,
                    windows,
                    window_minutes,
                    placements,
                    gap_ok,
                    rng,
                    notes,
                    config,
                    allow_reuse=True,
                    relaxed=index in relaxed_windows,
                )
            )

    if len(placements) < target:
        notes.append(
            f"INFEASIBLE: only {len(placements)} of {target} opportunities could be placed legally on this day "
            "(insufficient eligible, stable, exclusion-free minutes). No artificial event or excluded-context "
            "prompt was fabricated to reach the target."
        )
    if not placements:
        raise SchedulingError(
            "no legal prompt minute exists on this day (every minute is asleep, excluded, unresolved, "
            "non-realised or unstable)"
        )

    # ---- 4. materialise prompts -----------------------------------------
    placements.sort(key=lambda placed: placed.minute)
    prompts: list[EMAPrompt] = []
    for schedule_index, placed in enumerate(placements):
        minute = placed.minute
        episode = day.episode_at(minute)
        interval = day.interval_at(minute)
        prompt_id = _prompt_id(prefix, day, seed, schedule_index)
        prompt_time = day_datetime(day.day, minute)
        prompts.append(
            EMAPrompt(
                prompt_id=prompt_id,
                participant_id=day.participant_id,
                day_date=day.day,
                schedule_index=schedule_index,
                trigger=placed.trigger,
                prompt_time=prompt_time,
                prompt_time_min=minute,
                window_index=placed.window_index,
                window_label=windows[placed.window_index - 1].label if placed.window_index is not None else None,
                episode_id=placed.episode_id or (episode.episode_id if episode else None),
                interval_id=placed.interval_id or (interval.interval_id if interval else (episode.interval_id if episode else None)),
                journey_id=placed.journey_id,
                event_id=placed.event_id,
                event_kind=placed.event.kind.value if placed.event else None,
                minutes_after_event=placed.minutes_after_event,
                selection_reason=placed.reason,
                is_event_enriched=placed.is_event_enriched,
                stability_relaxed="[stability_relaxed" in placed.reason,
                recall_frame="current_at_prompt_time",
                expiry_minutes=expiry,
                expires_at=prompt_time + timedelta(minutes=expiry),
            )
        )

    background_count = sum(1 for prompt in prompts if not prompt.is_event_enriched)
    event_count = sum(1 for prompt in prompts if prompt.is_event_enriched)
    if background_count < min_background:
        notes.append(
            f"only {background_count} background opportunities could be placed "
            f"(protocol minimum {min_background}); remaining minutes were not legally available"
        )

    info: dict[str, Any] = {
        "scheduler_version": SCHEDULER_VERSION,
        "seed": seed,
        "stable_seed": stable_seed(day.participant_id, day.day, seed),
        "target": target,
        "placed": len(prompts),
        "background": background_count,
        "event_enriched": event_count,
        "detected_events": [event.to_dict() for event in events],
        "event_kinds_detected": sorted({event.kind.value for event in events}),
        "notes": notes,
        "excluded_minutes_summary": eligibility.reason_summary(),
        "eligible_minutes_per_window": {index + 1: len(minutes) for index, minutes in window_minutes.items()},
        "relaxed_windows": sorted(index + 1 for index in relaxed_windows),
        "capped_margin_episodes": eligibility.capped_margin_episodes,
        "windows": [f"{format_hhmm(w.start)}-{format_hhmm(w.end)}" for w in windows],
    }
    info["audit"] = audit_schedule(day, prompts, config).to_dict()
    return prompts, info


def _draw_background(
    window_index: int,
    windows: Sequence[Interval],
    window_minutes: Mapping[int, Sequence[int]],
    placements: Sequence[PromptPlacement],
    gap_ok: Any,
    rng: random.Random,
    notes: list[str],
    config: ProtocolConfig,
    allow_reuse: bool = False,
    relaxed: bool = False,
) -> list[PromptPlacement]:
    """Draw one semi-random prompt minute inside a daytime window."""
    minutes = [minute for minute in window_minutes.get(window_index, []) if gap_ok(float(minute))]
    if not minutes:
        return []
    if placements and not allow_reuse:
        # prefer the minute that maximises distance to already-placed prompts
        scored = sorted(
            minutes,
            key=lambda minute: -min(abs(minute - placed.minute) for placed in placements),
        )
        top = min(len(scored), max(1, int(config.get("sampling.candidate_top_k", 15))))
        minute = float(rng.choice(scored[:top]))
    else:
        minute = float(rng.choice(minutes))
    window = windows[window_index]
    return [
        PromptPlacement(
            minute=minute,
            window_index=window_index + 1,
            trigger=TriggerType.SEMI_RANDOM,
            episode_id=None,
            reason=(
                f"semi-random background draw inside daytime window {window_index + 1} "
                f"({format_hhmm(window.start)}-{format_hhmm(window.end)}); "
                f"{len(window_minutes.get(window_index, []))} eligible minutes, exclusion-safe and stable"
                + (" [stability_relaxed: fragmented day, boundary margin dropped]" if relaxed else "")
            ),
        )
    ]


def _prompt_id(prefix: str, day: ContextualDay, seed: int, index: int) -> str:
    material = f"{day.participant_id}|{day.day.isoformat()}|{seed}|{index}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{day.day.isoformat().replace('-', '')}-{index + 1:02d}-{digest}"


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def schedule_prompts(
    request: EMARequest | ContextualDay | Mapping[str, Any],
    config: Optional[ProtocolConfig] = None,
    seed: Optional[int] = None,
    day: Optional[ContextualDay | Mapping[str, Any]] = None,
    with_info: bool = False,
) -> Any:
    """Schedule the five Paper 3 EMA opportunities for one participant-day.

    Accepts an :class:`EMARequest`, a :class:`ContextualDay`, or a generic
    mapping describing a day.  Returns ``list[EMAPrompt]`` (or
    ``(prompts, info)`` when ``with_info=True``).
    """
    config = config or default_config()
    if isinstance(request, EMARequest):
        target_day = request.day
        effective_seed = request.seed if seed is None else seed
    else:
        source = request if request is not None else day
        if source is None:
            raise SchedulingError("schedule_prompts requires a day or an EMARequest")
        target_day = source if isinstance(source, ContextualDay) else contextual_day_from_mapping(source, config)
        effective_seed = 0 if seed is None else seed
    if isinstance(target_day, Mapping):  # pragma: no cover - defensive
        target_day = contextual_day_from_mapping(target_day, config)
    prompts, info = schedule_for_day(target_day, config, int(effective_seed))
    if with_info:
        return prompts, info
    return prompts


__all__ = [
    "SCHEDULER_VERSION",
    "SchedulingError",
    "PromptPlacement",
    "schedule_for_day",
    "schedule_prompts",
    "stable_seed",
    "AuditStatus",
]
