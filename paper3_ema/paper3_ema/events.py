"""Event detection for event-enriched EMA sampling.

Paper 3 event priority:

1. ``post_trip``                  — a journey (or transport episode) has ended
2. ``post_active_episode``        — a bout of exercise / vigorous activity has ended
3. ``context_transition``         — a meaningful contextual transition has settled
4. ``discretionary_fallback``     — a discretionary event (shopping, childcare,
                                    social, self-care) is under way

Events are *detected*, never invented: every :class:`DayEvent` carries the ids
of the episode / interval / journey it came from.  The scheduler is forbidden
from fabricating an event category to satisfy diversity
(``sampling.force_event_diversity: false``).
"""

from __future__ import annotations

from typing import Optional, Sequence

from .config import ProtocolConfig, default_config
from .eligibility import DayEligibility
from .models import ContextualDay, DayEvent, EpisodeRef, JourneyRef
from .timeutil import Interval
from .vocab import EVENT_PRIORITY, Activity, Domain, TriggerType, VIGOROUS_ACTIVITIES

DAY_MINUTES = 24 * 60

ACTIVE_TRANSPORT_MODES = {"walk", "walking", "foot", "bike", "bicycle", "cycling", "cycle"}


def _priority_of(kind: TriggerType, priority_order: Sequence[str]) -> int:
    for index, name in enumerate(priority_order):
        if name == kind.value:
            return index
    return len(priority_order)


def detect_events(
    day: ContextualDay,
    eligibility: DayEligibility,
    config: Optional[ProtocolConfig] = None,
) -> list[DayEvent]:
    """Detect all candidate events in a day (unranked, unfiltered by slots)."""
    config = config or default_config()
    priority_order = [str(item) for item in (config.get("events.priority") or [t.value for t in EVENT_PRIORITY])]
    events: list[DayEvent] = []
    events.extend(_post_trip_events(day, eligibility, config, priority_order))
    events.extend(_post_active_events(day, eligibility, config, priority_order))
    events.extend(_context_transition_events(day, eligibility, config, priority_order))
    events.extend(_discretionary_events(day, eligibility, config, priority_order))
    return _deduplicate(events, config)


# --------------------------------------------------------------------------
# 1. post_trip
# --------------------------------------------------------------------------

def _post_trip_events(
    day: ContextualDay,
    eligibility: DayEligibility,
    config: ProtocolConfig,
    priority_order: Sequence[str],
) -> list[DayEvent]:
    section = config.section("events.post_trip")
    minimum_duration = float(section.get("min_duration_minutes", 5))
    events: list[DayEvent] = []

    if section.get("include_journeys", True):
        for journey in day.journeys:
            if journey.duration_min < minimum_duration:
                continue
            if not _has_stable_opportunity(eligibility, journey.end_min, config):
                continue
            events.append(
                DayEvent(
                    event_id=f"evt-trip-{journey.journey_id}",
                    kind=TriggerType.POST_TRIP,
                    start_min=journey.start_min,
                    end_min=journey.end_min,
                    priority=_priority_of(TriggerType.POST_TRIP, priority_order),
                    score=_score(journey.duration_min, priority_order, TriggerType.POST_TRIP, config),
                    journey_id=journey.journey_id,
                    interval_id=journey.interval_id,
                    episode_id=journey.episode_id,
                    window_index=day.window_of(journey.end_min),
                    label=f"journey by {(journey.mode or 'unknown mode')}",
                    reason=(
                        f"journey {journey.journey_id} ({journey.mode or 'mode unknown'}, "
                        f"{journey.duration_min:.0f} min) ended; prompt after the trip"
                    ),
                )
            )

    if section.get("include_active_transport_episodes", True):
        known_journey_spans = [Interval(jn.start_min, jn.end_min) for jn in day.journeys]
        for episode in day.episodes:
            if episode.domain != Domain.TRANSPORT:
                continue
            if episode.duration_min < minimum_duration:
                continue
            if any(span.overlaps(episode.interval) for span in known_journey_spans):
                continue  # already represented as a journey
            if not _has_stable_opportunity(eligibility, episode.end_min, config):
                continue
            events.append(
                DayEvent(
                    event_id=f"evt-trip-ep-{episode.episode_id}",
                    kind=TriggerType.POST_TRIP,
                    start_min=episode.start_min,
                    end_min=episode.end_min,
                    priority=_priority_of(TriggerType.POST_TRIP, priority_order),
                    score=_score(episode.duration_min, priority_order, TriggerType.POST_TRIP, config),
                    episode_id=episode.episode_id,
                    interval_id=episode.interval_id,
                    window_index=day.window_of(episode.end_min),
                    label=f"transport episode ({(episode.activity.value if episode.activity else 'unknown')})",
                    reason=(
                        f"transport episode {episode.episode_id} "
                        f"({episode.duration_min:.0f} min) ended without a journey record"
                    ),
                )
            )
    return events


# --------------------------------------------------------------------------
# 2. post_active_episode
# --------------------------------------------------------------------------

def _post_active_events(
    day: ContextualDay,
    eligibility: DayEligibility,
    config: ProtocolConfig,
    priority_order: Sequence[str],
) -> list[DayEvent]:
    section = config.section("events.post_active_episode")
    minimum_duration = float(section.get("min_duration_minutes", 10))
    minimum_exertion = float(section.get("min_exertion", 0.4))
    allowed_domains = {str(item) for item in (section.get("domains") or ["exercise"])}
    allowed_activities = {str(item) for item in (section.get("activities") or [])}

    events: list[DayEvent] = []
    for episode in day.episodes:
        if episode.duration_min < minimum_duration:
            continue
        domain_match = episode.domain is not None and episode.domain.value in allowed_domains
        activity_match = episode.activity is not None and episode.activity.value in allowed_activities
        if not (domain_match or activity_match):
            continue
        # cycling only counts as an "active episode" when it is exercise, not transport
        if episode.activity == Activity.CYCLING and not domain_match:
            continue
        if episode.activity in VIGOROUS_ACTIVITIES and episode.exertion is None and not domain_match:
            continue
        if episode.exertion is not None and episode.exertion < minimum_exertion and not domain_match:
            continue
        if not _has_stable_opportunity(eligibility, episode.end_min, config):
            continue
        events.append(
            DayEvent(
                event_id=f"evt-active-{episode.episode_id}",
                kind=TriggerType.POST_ACTIVE_EPISODE,
                start_min=episode.start_min,
                end_min=episode.end_min,
                priority=_priority_of(TriggerType.POST_ACTIVE_EPISODE, priority_order),
                score=_score(episode.duration_min, priority_order, TriggerType.POST_ACTIVE_EPISODE, config),
                episode_id=episode.episode_id,
                interval_id=episode.interval_id,
                window_index=day.window_of(episode.end_min),
                label=(
                    f"active episode "
                    f"({(episode.activity.value if episode.activity else 'unknown')}, "
                    f"{(episode.domain.value if episode.domain else 'domain unknown')})"
                ),
                reason=(
                    f"episode {episode.episode_id} "
                    f"({episode.duration_min:.0f} min, exertion "
                    f"{'n/a' if episode.exertion is None else f'{episode.exertion:.2f}'}) ended"
                ),
            )
        )
    return events


# --------------------------------------------------------------------------
# 3. meaningful_context_transition
# --------------------------------------------------------------------------

def _context_transition_events(
    day: ContextualDay,
    eligibility: DayEligibility,
    config: ProtocolConfig,
    priority_order: Sequence[str],
) -> list[DayEvent]:
    section = config.section("events.context_transition")
    settle = float(section.get("min_stable_minutes_before", 5))
    count_domain = bool(section.get("count_domain_change", True))
    count_place = bool(section.get("count_place_change", True))
    count_social = bool(section.get("count_social_change", False))
    count_environment = bool(section.get("count_indoor_outdoor_change", True))

    events: list[DayEvent] = []
    episodes = sorted(day.episodes, key=lambda ep: ep.start_min)
    for previous, current in zip(episodes, episodes[1:]):
        if abs(current.start_min - previous.end_min) > settle:
            continue  # not contiguous: not a transition we can anchor
        if section.get("exclude_sleep_adjacent", True) and (
            previous.activity == Activity.SLEEPING
            or current.activity == Activity.SLEEPING
            or previous.activity == Activity.LYING_AWAKE
            or current.activity == Activity.LYING_AWAKE
        ):
            continue  # waking up / going to bed is not a Paper 3 enrichment event
        changes = []
        if count_domain and previous.domain is not None and current.domain is not None and previous.domain != current.domain:
            changes.append(f"domain:{previous.domain.value}->{current.domain.value}")
        if count_place and previous.place_type is not None and current.place_type is not None and previous.place_type != current.place_type:
            changes.append(f"place:{previous.place_type.value}->{current.place_type.value}")
        if count_social and previous.social is not None and current.social is not None and previous.social != current.social:
            changes.append(f"social:{previous.social.value}->{current.social.value}")
        if (
            count_environment
            and previous.indoor_outdoor is not None
            and current.indoor_outdoor is not None
            and previous.indoor_outdoor != current.indoor_outdoor
        ):
            changes.append(f"environment:{previous.indoor_outdoor.value}->{current.indoor_outdoor.value}")
        if not changes:
            continue
        anchor = current.start_min + settle
        if anchor >= DAY_MINUTES:
            continue
        if not eligibility.is_stable(anchor):
            continue
        events.append(
            DayEvent(
                event_id=f"evt-transition-{current.episode_id}",
                kind=TriggerType.CONTEXT_TRANSITION,
                start_min=current.start_min,
                end_min=anchor,
                priority=_priority_of(TriggerType.CONTEXT_TRANSITION, priority_order),
                score=_score(1.0, priority_order, TriggerType.CONTEXT_TRANSITION, config),
                episode_id=current.episode_id,
                interval_id=current.interval_id,
                window_index=day.window_of(anchor),
                label="context transition (" + ", ".join(changes) + ")",
                reason=f"transition into {current.episode_id}: " + ", ".join(changes),
            )
        )
    return events


# --------------------------------------------------------------------------
# 4. discretionary fallback
# --------------------------------------------------------------------------

def _discretionary_events(
    day: ContextualDay,
    eligibility: DayEligibility,
    config: ProtocolConfig,
    priority_order: Sequence[str],
) -> list[DayEvent]:
    section = config.section("events.discretionary_fallback")
    if not section.get("enabled", True):
        return []
    allowed_domains = {str(item) for item in (section.get("domains") or [])}
    minimum_duration = float(section.get("min_duration_minutes", 15))
    events: list[DayEvent] = []
    for episode in day.episodes:
        explicit = (episode.discretionary_event or "").strip().lower()
        domain_match = episode.domain is not None and episode.domain.value in allowed_domains
        if not explicit and not domain_match:
            continue
        if episode.duration_min < minimum_duration:
            continue
        if episode.is_fixed_commitment:
            continue  # a fixed commitment is not discretionary
        anchor = episode.start_min + min(settle_minutes(config), episode.duration_min / 2.0)
        if not eligibility.is_stable(anchor):
            anchor_minute = eligibility.first_stable_minute(
                episode.start_min, episode.end_min - 1
            )
            if anchor_minute is None:
                continue
            anchor = float(anchor_minute)
        events.append(
            DayEvent(
                event_id=f"evt-disc-{episode.episode_id}",
                kind=TriggerType.DISCRETIONARY_FALLBACK,
                start_min=episode.start_min,
                end_min=episode.end_min,
                priority=_priority_of(TriggerType.DISCRETIONARY_FALLBACK, priority_order),
                score=_score(episode.duration_min, priority_order, TriggerType.DISCRETIONARY_FALLBACK, config),
                episode_id=episode.episode_id,
                interval_id=episode.interval_id,
                window_index=day.window_of(anchor),
                label=f"discretionary event ({explicit or (episode.domain.value if episode.domain else 'unknown')})",
                reason=(
                    f"episode {episode.episode_id} is a discretionary "
                    f"{explicit or (episode.domain.value if episode.domain else 'context')} event"
                ),
            )
        )
    return events


def settle_minutes(config: ProtocolConfig) -> float:
    return float(config.get("sampling.stability_margin_minutes", 5))


# --------------------------------------------------------------------------
# scoring / ranking helpers
# --------------------------------------------------------------------------

def _score(duration_min: float, priority_order: Sequence[str], kind: TriggerType, config: ProtocolConfig) -> float:
    scoring = config.section("events.scoring")
    priority_weight = float(scoring.get("priority_weight", 1.0))
    duration_weight = float(scoring.get("duration_weight", 0.02))
    maximum = float(scoring.get("max_score", 3.0))
    priority_rank = _priority_of(kind, priority_order)
    value = priority_weight * (len(priority_order) - priority_rank) + duration_weight * min(duration_min, 60.0)
    return round(min(value, maximum), 4)


def _has_stable_opportunity(eligibility: DayEligibility, event_end: float, config: ProtocolConfig) -> bool:
    horizon = float(config.get("sampling.max_minutes_after_event", 45))
    minute = eligibility.first_stable_minute(event_end, min(DAY_MINUTES, event_end + horizon))
    return minute is not None


def _deduplicate(events: Sequence[DayEvent], config: ProtocolConfig) -> list[DayEvent]:
    """Rank by priority then time, applying per-kind daily caps."""
    caps = {str(key): int(value) for key, value in dict(config.get("events.per_kind_daily_cap", {}) or {}).items()}
    ordered = sorted(events, key=lambda ev: (ev.priority, -ev.score, ev.end_min))
    kept: list[DayEvent] = []
    per_kind: dict[str, int] = {}
    for event in ordered:
        kind = event.kind.value
        limit = caps.get(kind, 2)
        if per_kind.get(kind, 0) >= limit:
            continue
        if any(
            other.kind == event.kind
            and abs(other.end_min - event.end_min) < float(config.get("sampling.min_gap_minutes", 30))
            for other in kept
        ):
            continue
        per_kind[kind] = per_kind.get(kind, 0) + 1
        kept.append(event)
    return sorted(kept, key=lambda ev: (ev.priority, ev.end_min))


def rank_events(events: Sequence[DayEvent]) -> list[DayEvent]:
    """Paper 3 event ordering: priority first, then recency within priority."""
    return sorted(events, key=lambda ev: (ev.priority, -ev.score, ev.end_min))


def summarise_events(events: Sequence[DayEvent]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for event in events:
        summary[event.kind.value] = summary.get(event.kind.value, 0) + 1
    return summary
