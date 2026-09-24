"""Context builder: the bounded :class:`EMAContextPacket`.

The packet is the *only* factual material any downstream component (structured
state generator, note renderer, validator) is allowed to see.  It is:

* **bounded** — no full-day narrative dumps, no previous-day narrative, no
  unrestricted free text;
* **name-free** — place *types* rather than proper names, coarse purpose
  categories rather than host purpose strings;
* **demographically blind** — no age, sex, occupation, health, fitness,
  personality or hobby information (see :mod:`paper3_ema.vocab` allowlist);
* **traceable** — every field is either inherited from the supplied day or
  derived by a documented rule (see :mod:`paper3_ema.provenance`).

Context is always resolved at **prompt time**.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from .config import ProtocolConfig, default_config
from .day import ContextualDay
from .eligibility import DayEligibility
from .models import EMAContextPacket, EMAPrompt, EpisodeRef, PersonaContextFacts
from .timeutil import Interval, day_datetime, format_hhmm, parse_hhmm
from .vocab import (
    Activity,
    Domain,
    IndoorOutdoor,
    PlaceType,
    SocialContext,
    TriggerType,
    VIGOROUS_ACTIVITIES,
)

CONTEXT_BUILDER_VERSION = "1.0.0"
DAY_MINUTES = 24 * 60

PURPOSE_CATEGORIES: dict[str, str] = {
    "commute": "commute",
    "commuting": "commute",
    "travel to/from work": "commute",
    "work": "work",
    "working": "work",
    "meeting": "work",
    "study": "study",
    "class": "study",
    "lecture": "study",
    "homework": "study",
    "school": "study",
    "shopping": "shopping",
    "errand": "errands",
    "errands": "errands",
    "childcare": "childcare",
    "child": "childcare",
    "children": "childcare",
    "school run": "childcare",
    "exercise": "exercise",
    "workout": "exercise",
    "gym": "exercise",
    "training": "exercise",
    "run": "exercise",
    "running": "exercise",
    "walk": "leisure_walk",
    "walking": "leisure_walk",
    "hike": "leisure_walk",
    "leisure": "leisure",
    "hobby": "leisure",
    "social": "social",
    "visit": "social",
    "friends": "social",
    "meal": "meal",
    "breakfast": "meal",
    "lunch": "meal",
    "dinner": "meal",
    "eating": "meal",
    "coffee": "meal",
    "self care": "self_care",
    "selfcare": "self_care",
    "shower": "self_care",
    "washing": "self_care",
    "dressing": "self_care",
    "household": "household",
    "chores": "household",
    "cleaning": "household",
    "cooking": "household",
    "laundry": "household",
    "rest": "rest",
    "resting": "rest",
    "relax": "rest",
    "tv": "rest",
    "reading": "rest",
    "sleep": "sleep",
    "appointment": "appointment",
    "medical": "appointment",
    "health": "appointment",
}

SOCIAL_WITH_COMPANY = {
    SocialContext.WITH_PARTNER,
    SocialContext.WITH_FAMILY,
    SocialContext.WITH_CHILDREN,
    SocialContext.WITH_FRIENDS,
    SocialContext.WITH_COLLEAGUES,
    SocialContext.WITH_KNOWN_OTHERS,
    SocialContext.WITH_STRANGERS,
}


# --------------------------------------------------------------------------
# derived helpers
# --------------------------------------------------------------------------

def time_of_day_label(minute: float, config: Optional[ProtocolConfig] = None) -> str:
    """Coarse period of day, from ``state_generator.time_of_day_periods``."""
    config = config or default_config()
    periods = config.get("state_generator.time_of_day_periods") or {}
    for name, span in dict(periods).items():
        if not isinstance(span, (list, tuple)) or len(span) != 2:
            continue
        start, end = float(parse_hhmm(str(span[0]))), float(parse_hhmm(str(span[1])))
        if start <= end:
            if start <= minute < end:
                return str(name)
        elif minute >= start or minute < end:  # wraps midnight
            return str(name)
    return "daytime"


def coarse_purpose(purpose: Optional[str], domain: Optional[Domain]) -> Optional[str]:
    """Map a host purpose string onto a coarse category (no proper names)."""
    if purpose:
        text = purpose.strip().lower()
        if text in PURPOSE_CATEGORIES:
            return PURPOSE_CATEGORIES[text]
        for key, category in PURPOSE_CATEGORIES.items():
            if key in text:
                return category
    if domain is not None:
        return {
            Domain.WORK: "work",
            Domain.STUDY: "study",
            Domain.TRANSPORT: "travel",
            Domain.HOUSEHOLD: "household",
            Domain.CHILDCARE: "childcare",
            Domain.EXERCISE: "exercise",
            Domain.LEISURE: "leisure",
            Domain.SOCIAL: "social",
            Domain.SELF_CARE: "self_care",
            Domain.SHOPPING: "shopping",
        }.get(domain)
    return None


def previous_episode(day: ContextualDay, minute: float) -> Optional[EpisodeRef]:
    """Immediately preceding episode (bounded recent context)."""
    candidates = [ep for ep in day.episodes if ep.end_min <= minute + 1e-9]
    if not candidates:
        return None
    return max(candidates, key=lambda ep: ep.end_min)


def previous_journey(day: ContextualDay, minute: float) -> Optional[Any]:
    candidates = [jn for jn in day.journeys if jn.end_min <= minute + 1e-9]
    if not candidates:
        return None
    return max(candidates, key=lambda jn: jn.end_min)


def last_activity_change(day: ContextualDay, minute: float) -> Optional[float]:
    """Minute of the most recent activity change at or before ``minute``."""
    current = day.episode_at(minute)
    if current is None:
        return None
    preceding = [ep for ep in day.episodes if ep.end_min <= current.start_min + 1e-9]
    if preceding and any(
        ep.activity != current.activity or ep.domain != current.domain for ep in preceding[-1:]
    ):
        return current.start_min
    return current.start_min


def minutes_since_activity_change(day: ContextualDay, minute: float) -> Optional[float]:
    change = last_activity_change(day, minute)
    return round(minute - change, 1) if change is not None else None


def recent_activity_summary(day: ContextualDay, minute: float, lookback_minutes: float = 60.0) -> dict[str, float]:
    """Minutes spent in each activity during the bounded lookback window."""
    window = Interval(max(0.0, minute - lookback_minutes), minute)
    summary: dict[str, float] = {}
    for episode in day.episodes:
        overlap = episode.interval.intersection(window)
        if overlap is None:
            continue
        key = episode.activity.value if episode.activity else "unknown"
        summary[key] = round(summary.get(key, 0.0) + overlap.duration_min, 1)
    return summary


def recent_exertion(day: ContextualDay, minute: float, config: Optional[ProtocolConfig] = None) -> Optional[float]:
    """Bounded 0..1 exertion aggregate over the lookback window.

    Uses host-supplied ``exertion`` when present, otherwise a documented
    fallback mapping from activity class.  Returns ``None`` when the day has no
    episode coverage in the window (no fabrication).
    """
    config = config or default_config()
    half_life = float(
        config.get("state_generator.modifiers.recent_exertion.decay_half_life_minutes", 45)
    )
    window = Interval(max(0.0, minute - 2 * half_life), minute)
    total_weight = 0.0
    total_value = 0.0
    for episode in day.episodes:
        overlap = episode.interval.intersection(window)
        if overlap is None or overlap.duration_min <= 0:
            continue
        value = episode.exertion
        if value is None:
            value = _fallback_exertion(episode.activity)
        if value is None:
            continue
        midpoint = (max(overlap.start, episode.start_min) + min(overlap.end, episode.end_min)) / 2.0
        age = max(0.0, minute - midpoint)
        weight = overlap.duration_min * (0.5 ** (age / half_life) if half_life > 0 else 1.0)
        total_weight += weight
        total_value += weight * float(value)
    if total_weight <= 0:
        return None
    return round(max(0.0, min(1.0, total_value / total_weight)), 4)


def _fallback_exertion(activity: Optional[Activity]) -> Optional[float]:
    """Documented fallback when the host supplies no exertion value."""
    if activity is None:
        return None
    return {
        Activity.SLEEPING: 0.0,
        Activity.LYING_AWAKE: 0.02,
        Activity.SITTING: 0.05,
        Activity.STANDING: 0.15,
        Activity.WALKING: 0.35,
        Activity.RUNNING: 0.85,
        Activity.CYCLING: 0.6,
        Activity.DRIVING: 0.05,
        Activity.PUBLIC_TRANSPORT: 0.05,
        Activity.OTHER_VIGOROUS: 0.75,
        Activity.OTHER_LIGHT: 0.2,
        Activity.UNKNOWN: None,
    }.get(activity)


def next_commitment(day: ContextualDay, minute: float) -> tuple[Optional[Any], Optional[float]]:
    """Next fixed commitment at or after ``minute`` and minutes until it starts."""
    upcoming = [fc for fc in day.fixed_commitments if fc.end_min > minute]
    if not upcoming:
        return None, None
    commitment = min(upcoming, key=lambda fc: fc.start_min)
    lead = max(0.0, commitment.start_min - minute)
    if commitment.requires_travel and commitment.travel_time_min:
        lead = max(0.0, lead - float(commitment.travel_time_min))
    return commitment, round(lead, 1)


def episode_is_unstable(day: ContextualDay, minute: float, eligibility: Optional[DayEligibility] = None) -> bool:
    episode = day.episode_at(minute)
    if episode is not None and (episode.is_unstable or episode.is_unresolved):
        return True
    interval = day.interval_at(minute)
    if interval is not None and interval.is_excluding:
        return True
    return False


# --------------------------------------------------------------------------
# allowed-entity vocabulary for the closed-world note contract
# --------------------------------------------------------------------------

MODE_PHRASES: dict[str, str] = {
    "walk": "the walk",
    "walking": "the walk",
    "foot": "the walk",
    "bike": "the bike ride",
    "bicycle": "the bike ride",
    "cycling": "the bike ride",
    "cycle": "the bike ride",
    "car": "the drive",
    "driving": "the drive",
    "bus": "the bus trip",
    "train": "the train trip",
    "tram": "the tram trip",
    "metro": "the metro trip",
    "subway": "the metro trip",
    "ferry": "the ferry trip",
}

ACTIVITY_PHRASES: dict[Activity, str] = {
    Activity.SITTING: "sitting",
    Activity.STANDING: "standing",
    Activity.WALKING: "the walk",
    Activity.RUNNING: "the run",
    Activity.CYCLING: "the bike ride",
    Activity.DRIVING: "the drive",
    Activity.PUBLIC_TRANSPORT: "the public transport trip",
    Activity.OTHER_VIGOROUS: "the workout",
    Activity.OTHER_LIGHT: "the light activity",
    Activity.LYING_AWAKE: "the rest",
    Activity.SLEEPING: "sleep",
    Activity.UNKNOWN: "the current activity",
}

PLACE_PHRASES: dict[PlaceType, str] = {
    PlaceType.HOME: "at home",
    PlaceType.WORKPLACE: "at work",
    PlaceType.SCHOOL: "at campus",
    PlaceType.SHOP: "at the shop",
    PlaceType.FOOD_VENUE: "at the cafe",
    PlaceType.GYM: "at the gym",
    PlaceType.PARK: "in the park",
    PlaceType.OUTDOOR_GENERIC: "outdoors",
    PlaceType.STREET: "on the street",
    PlaceType.VEHICLE: "in the vehicle",
    PlaceType.TRANSIT_STOP: "at the stop",
    PlaceType.HEALTHCARE: "at the clinic",
    PlaceType.OTHER_BUILDING: "indoors",
    PlaceType.OTHER: "here",
    PlaceType.UNKNOWN: "here",
}

DOMAIN_PHRASES: dict[Domain, str] = {
    Domain.WORK: "work",
    Domain.STUDY: "study",
    Domain.TRANSPORT: "the trip",
    Domain.HOUSEHOLD: "the household tasks",
    Domain.CHILDCARE: "time with the children",
    Domain.EXERCISE: "the exercise session",
    Domain.LEISURE: "the free time",
    Domain.SOCIAL: "the social time",
    Domain.SELF_CARE: "the morning routine",
    Domain.SHOPPING: "the shopping trip",
    Domain.OTHER: "this part of the day",
}


def allowed_entity_vocabulary(
    packet_facts: Mapping[str, Any],
    day: ContextualDay,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Build ``(allowed_entities, allowed_causes)`` from packet facts only."""
    entities: list[str] = []
    causes: list[str] = []

    activity = packet_facts.get("activity")
    if activity:
        phrase = ACTIVITY_PHRASES.get(Activity(activity))
        if phrase:
            entities.append(phrase)
            causes.extend(phrase.split()[-1:] and [phrase])
    preceding = packet_facts.get("preceding_activity")
    if preceding:
        phrase = ACTIVITY_PHRASES.get(Activity(preceding))
        if phrase:
            entities.append(f"the earlier {phrase.strip('the ')}")
            entities.append(phrase)
            causes.append(phrase)
    journey_mode = packet_facts.get("preceding_journey_mode") or packet_facts.get("current_journey_mode")
    if journey_mode:
        phrase = MODE_PHRASES.get(str(journey_mode).lower())
        if phrase:
            entities.append(phrase)
            causes.append(phrase)
    place = packet_facts.get("place_type")
    if place:
        phrase = PLACE_PHRASES.get(PlaceType(place))
        if phrase:
            entities.append(phrase)
    domain = packet_facts.get("domain")
    if domain:
        phrase = DOMAIN_PHRASES.get(Domain(domain))
        if phrase:
            entities.append(phrase)
            causes.append(phrase)
    purpose = packet_facts.get("purpose_category")
    if purpose:
        entities.append(str(purpose).replace("_", " "))
        causes.append(str(purpose).replace("_", " "))
    if packet_facts.get("minutes_since_journey_end") is not None:
        entities.append("the trip just finished")
        causes.append("the trip")
    if packet_facts.get("minutes_since_active_episode_end") is not None:
        entities.append("the activity just finished")
        causes.append("the activity")
    if packet_facts.get("minutes_to_next_commitment") is not None:
        kind = packet_facts.get("next_commitment_kind") or "commitment"
        entities.append(f"the upcoming {str(kind).replace('_', ' ')}")
        causes.append("the schedule")
    time_label = packet_facts.get("time_of_day")
    if time_label:
        entities.append(str(time_label).replace("_", " "))
        causes.append(str(time_label).replace("_", " "))
    if packet_facts.get("weather_available") and day.weather:
        entities.append(str(day.weather))
        causes.append(str(day.weather))
    social = packet_facts.get("social_context")
    if social and SocialContext(social) in SOCIAL_WITH_COMPANY:
        entities.append("the company")
        causes.append("the company")
    elif social == SocialContext.ALONE.value:
        entities.append("the quiet")
        causes.append("the quiet")
    causes.extend(["the day so far", "how the day is going", "the morning", "the evening", "the time of day"])

    unique_entities = tuple(dict.fromkeys(entity for entity in entities if entity))
    unique_causes = tuple(dict.fromkeys(cause for cause in causes if cause))
    return unique_entities, unique_causes


# --------------------------------------------------------------------------
# packet construction
# --------------------------------------------------------------------------

def build_packet(
    day: ContextualDay,
    prompt: EMAPrompt,
    config: Optional[ProtocolConfig] = None,
    eligibility: Optional[DayEligibility] = None,
    previous_state: Optional[Mapping[str, int]] = None,
    previous_prompt_minute: Optional[float] = None,
    persona: Optional[PersonaContextFacts] = None,
) -> EMAContextPacket:
    """Resolve the bounded factual context packet for one prompt.

    ``persona`` is accepted only to satisfy the closed allowlist contract; it is
    *not* copied into the packet.  The state generator may consult it through
    the documented contextual rules only.
    """
    config = config or default_config()
    minute = float(prompt.prompt_time_min)
    eligibility = eligibility or DayEligibility.build(day, config)
    lookback = 60.0

    episode = day.episode_at(minute)
    interval = eligibility.interval_at(minute) or (day.interval_at(minute) if day.intervals else None)
    journey = day.journey_at(minute)
    preceding_ep = previous_episode(day, minute)
    preceding_jn = previous_journey(day, minute)
    commitment, minutes_to_commitment = next_commitment(day, minute)

    # journeys that are represented by a transport episode should not be
    # double-counted as "preceding journey"
    if preceding_jn is not None and preceding_ep is not None and preceding_jn.episode_id == preceding_ep.episode_id:
        preceding_jn_is_episode = True
    else:
        preceding_jn_is_episode = False

    facts: dict[str, Any] = {
        "activity": episode.activity.value if episode and episode.activity else None,
        "domain": episode.domain.value if episode and episode.domain else None,
        "place_type": episode.place_type.value if episode and episode.place_type else None,
        "social_context": episode.social.value if episode and episode.social else None,
        "indoor_outdoor": episode.indoor_outdoor.value if episode and episode.indoor_outdoor else None,
        "purpose_category": coarse_purpose(episode.purpose if episode else None, episode.domain if episode else None),
        "preceding_activity": preceding_ep.activity.value if preceding_ep and preceding_ep.activity else None,
        "preceding_journey_mode": (preceding_jn.mode if preceding_jn else None),
        "current_journey_mode": journey.mode if journey else None,
        "minutes_since_journey_end": (
            round(minute - preceding_jn.end_min, 1)
            if preceding_jn is not None and minute - preceding_jn.end_min <= 180
            else None
        ),
        "time_of_day": time_of_day_label(minute, config),
        "weather_available": bool(day.weather),
    }
    allowed_entities, allowed_causes = allowed_entity_vocabulary(facts, day)

    minutes_since_active = _minutes_since_active_episode_end(day, minute, config)

    packet = EMAContextPacket(
        prompt_time_min=minute,
        prompt_time=day_datetime(day.day, minute),
        time_of_day=facts["time_of_day"],
        minutes_since_wake=round(minute - day.wake_min, 1) if day.wake_min is not None else None,
        window_index=prompt.window_index,
        window_label=prompt.window_label,
        activity=episode.activity if episode else None,
        activity_label=(episode.activity_label if episode and episode.activity is None else None),
        domain=episode.domain if episode else None,
        place_type=episode.place_type if episode else None,
        social_context=episode.social if episode else None,
        indoor_outdoor=episode.indoor_outdoor if episode else None,
        purpose_category=facts["purpose_category"],
        device_wear=day.wear_status_at(minute),
        episode_id=(episode.episode_id if episode else None) or prompt.episode_id,
        interval_id=(interval.interval_id if interval else None) or prompt.interval_id,
        journey_id=(journey.journey_id if journey else None) or prompt.journey_id,
        minutes_in_current_episode=round(minute - episode.start_min, 1) if episode else None,
        minutes_since_activity_change=minutes_since_activity_change(day, minute),
        episode_is_unstable=episode_is_unstable(day, minute, eligibility),
        current_journey_mode=journey.mode if journey else None,
        preceding_activity=preceding_ep.activity if preceding_ep else None,
        preceding_domain=preceding_ep.domain if preceding_ep else None,
        preceding_place_type=preceding_ep.place_type if preceding_ep else None,
        preceding_journey_mode=None if preceding_jn is None else preceding_jn.mode,
        preceding_journey_duration_min=None if preceding_jn is None else round(preceding_jn.duration_min, 1),
        preceding_journey_delayed=None if preceding_jn is None else preceding_jn.delayed,
        preceding_journey_crowded=None if preceding_jn is None else preceding_jn.crowded,
        minutes_since_journey_end=facts["minutes_since_journey_end"],
        minutes_since_active_episode_end=minutes_since_active,
        recent_exertion_60min=recent_exertion(day, minute, config),
        recent_activity_summary=recent_activity_summary(day, minute, lookback),
        minutes_to_next_commitment=minutes_to_commitment,
        next_commitment_kind=(commitment.kind or commitment.label) if commitment else None,
        next_commitment_requires_travel=commitment.requires_travel if commitment else None,
        previous_state=dict(previous_state) if previous_state else None,
        minutes_since_previous_prompt=(
            round(minute - float(previous_prompt_minute), 1) if previous_prompt_minute is not None else None
        ),
        allowed_entities=allowed_entities,
        allowed_causes=allowed_causes,
        weather_available=bool(day.weather),
    )
    return packet


def _minutes_since_active_episode_end(
    day: ContextualDay,
    minute: float,
    config: ProtocolConfig,
) -> Optional[float]:
    """Elapsed time since the most recent qualifying active episode ended."""
    section = config.section("events.post_active_episode")
    minimum_duration = float(section.get("min_duration_minutes", 10))
    allowed_domains = {str(item) for item in (section.get("domains") or ["exercise"])}
    allowed_activities = {str(item) for item in (section.get("activities") or [])}
    horizon = 180.0
    best: Optional[float] = None
    for episode in day.episodes:
        if episode.end_min > minute or minute - episode.end_min > horizon:
            continue
        if episode.duration_min < minimum_duration:
            continue
        domain_match = episode.domain is not None and episode.domain.value in allowed_domains
        activity_match = episode.activity is not None and episode.activity.value in allowed_activities
        if not (domain_match or activity_match):
            continue
        if episode.activity == Activity.CYCLING and not domain_match:
            continue
        elapsed = minute - episode.end_min
        if best is None or elapsed < best:
            best = elapsed
    return round(best, 1) if best is not None else None


def packet_facts_view(packet: EMAContextPacket) -> dict[str, Any]:
    """The closed-world fact view (used by the note renderer and validators)."""
    return packet.fact_view()


def describe_packet(packet: EMAContextPacket) -> str:
    """One-line human-readable rendering (debug / demo reports)."""
    return (
        f"{format_hhmm(packet.prompt_time_min)} "
        f"{packet.activity.value if packet.activity else 'activity?'} / "
        f"{packet.domain.value if packet.domain else 'domain?'} / "
        f"{packet.place_type.value if packet.place_type else 'place?'} / "
        f"{packet.social_context.value if packet.social_context else 'social?'} / "
        f"{packet.indoor_outdoor.value if packet.indoor_outdoor else 'env?'}"
    )
