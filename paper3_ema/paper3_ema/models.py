"""Typed public models for the Paper 3 standalone EMA module.

The module boundary is::

    any contextual-day generator  ->  EMARequest  ->  EMA module  ->  EMABundle

Nothing here imports DayForge or Appa.  Every contextual fact carried by a
record is either *inherited* from the supplied day (immutable) or *derived*
from it by a documented rule; the only synthetic content is the protocol
(schedule, missingness, latency) and the subjective state / note.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import date as _date
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from .timeutil import Interval, to_date
from .vocab import (
    SCHEMA_VERSION,
    Activity,
    AuditStatus,
    DeviceWear,
    Domain,
    IndoorOutdoor,
    PlaceType,
    ProvenanceClass,
    ResponseStatus,
    SocialContext,
    TriggerType,
)


# ==========================================================================
# serialisation helpers
# ==========================================================================

def _encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, _date)):
        return value.isoformat()
    if isinstance(value, Interval):
        return {"start_min": value.start, "end_min": value.end, "label": value.label}
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _encode(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, tuple):
        return [_encode(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_encode(v) for v in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


class _ToDictMixin:
    def to_dict(self) -> dict[str, Any]:
        return {f.name: _encode(getattr(self, f.name)) for f in fields(self)}  # type: ignore[arg-type]

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    def canonical_json(self) -> str:
        """Stable serialisation used for hashing."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_encode)

    def fingerprint(self, length: int = 16) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()[:length]


# ==========================================================================
# input contract: a generic contextual day
# ==========================================================================

@dataclass(frozen=True)
class EpisodeRef(_ToDictMixin):
    """One semantic episode of the supplied day (inherited context)."""

    episode_id: str
    start_min: float
    end_min: float
    activity: Optional[Activity] = None
    activity_label: Optional[str] = None          # free-text label from the host
    domain: Optional[Domain] = None
    place_type: Optional[PlaceType] = None
    place_label: Optional[str] = None             # coarse host label; NOT a proper name
    social: Optional[SocialContext] = None
    indoor_outdoor: Optional[IndoorOutdoor] = None
    purpose: Optional[str] = None
    exertion: Optional[float] = None              # 0..1 host-supplied relative exertion
    is_fixed_commitment: bool = False
    discretionary_event: Optional[str] = None     # e.g. "errand", "social_visit"
    interval_id: Optional[str] = None             # sensor interval this episode maps to
    is_realised: bool = True                      # False = planned movement that did not happen
    stability: Optional[str] = None               # "stable" | "unstable" | None (unknown)

    @property
    def interval(self) -> Interval:
        return Interval(self.start_min, self.end_min, self.episode_id)

    @property
    def duration_min(self) -> float:
        return self.end_min - self.start_min

    @property
    def is_unstable(self) -> bool:
        return (self.stability or "").lower() in {"unstable", "micro_transition", "fragmented"}

    @property
    def is_unresolved(self) -> bool:
        return bool((self.stability or "").lower() in {"unresolved", "ambiguous"}) or not self.is_realised


@dataclass(frozen=True)
class IntervalRef(_ToDictMixin):
    """One sensor-derived interval of the supplied day (inherited context).

    Intervals are the movement-sensing layer.  They may be flagged unresolved
    (the interval could not be classified) or non-realised (a planned movement
    that did not materialise).  Prompts never land inside either.
    """

    interval_id: str
    start_min: float
    end_min: float
    kind: Optional[str] = None                    # e.g. "sedentary", "active", "travel"
    resolved: bool = True
    realised: bool = True
    stability: Optional[str] = None
    episode_id: Optional[str] = None

    @property
    def interval(self) -> Interval:
        return Interval(self.start_min, self.end_min, self.interval_id)

    @property
    def is_excluding(self) -> bool:
        return (not self.resolved) or (not self.realised) or self.is_unstable

    @property
    def is_unstable(self) -> bool:
        return (self.stability or "").lower() in {"unstable", "micro_transition", "fragmented"}


@dataclass(frozen=True)
class JourneyRef(_ToDictMixin):
    """One journey/travel leg of the supplied day (inherited context)."""

    journey_id: str
    start_min: float
    end_min: float
    mode: Optional[str] = None                    # walk / bike / car / bus / train / ...
    purpose: Optional[str] = None
    origin_place_type: Optional[PlaceType] = None
    destination_place_type: Optional[PlaceType] = None
    distance_km: Optional[float] = None
    delayed: Optional[bool] = None                # documented disruption, if the host has one
    crowded: Optional[bool] = None
    episode_id: Optional[str] = None
    interval_id: Optional[str] = None

    @property
    def interval(self) -> Interval:
        return Interval(self.start_min, self.end_min, self.journey_id)

    @property
    def duration_min(self) -> float:
        return self.end_min - self.start_min

    @property
    def is_active(self) -> bool:
        return (self.mode or "").lower() in {"walk", "walking", "bike", "bicycle", "cycling", "cycle", "foot"}


@dataclass(frozen=True)
class FixedCommitmentRef(_ToDictMixin):
    """A fixed appointment used for schedule-pressure context."""

    commitment_id: str
    start_min: float
    end_min: float
    label: Optional[str] = None                   # coarse, e.g. "meeting" - never a person's name
    kind: Optional[str] = None                    # "work" | "care" | "appointment" | "social" | ...
    requires_travel: bool = False
    travel_time_min: float = 0.0

    @property
    def interval(self) -> Interval:
        return Interval(self.start_min, self.end_min, self.commitment_id)


@dataclass(frozen=True)
class WearPeriodRef(_ToDictMixin):
    """Optional device-wear period.  Never fabricated by this module."""

    start_min: float
    end_min: float
    status: DeviceWear
    reason: Optional[str] = None

    @property
    def interval(self) -> Interval:
        return Interval(self.start_min, self.end_min, f"wear:{self.status.value}")


@dataclass(frozen=True)
class ContextualDay(_ToDictMixin):
    """A complete externally supplied contextual day.

    This is the *only* world knowledge the EMA module has.  Fields the host
    cannot supply stay ``None``; the module never invents them.
    """

    participant_id: str
    day: _date
    wake_min: Optional[float] = None
    sleep_min: Optional[float] = None
    episodes: tuple[EpisodeRef, ...] = ()
    intervals: tuple[IntervalRef, ...] = ()
    journeys: tuple[JourneyRef, ...] = ()
    fixed_commitments: tuple[FixedCommitmentRef, ...] = ()
    device_wear: tuple[WearPeriodRef, ...] = ()
    waking_windows: tuple[Interval, ...] = ()     # host-supplied daytime strata
    weather: Optional[str] = None                 # only if the host documents it
    timezone: str = "local"
    source: str = "external"
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "day", to_date(self.day))
        for name in ("episodes", "intervals", "journeys", "fixed_commitments", "device_wear", "waking_windows"):
            value = getattr(self, name)
            if value is None:
                object.__setattr__(self, name, ())
            elif not isinstance(value, tuple):
                object.__setattr__(self, name, tuple(value))

    # -- lookups -----------------------------------------------------------
    def episode_at(self, minute: float) -> Optional[EpisodeRef]:
        for ep in self.episodes:
            if ep.start_min <= minute < ep.end_min:
                return ep
        return None

    def interval_at(self, minute: float) -> Optional[IntervalRef]:
        for iv in self.intervals:
            if iv.start_min <= minute < iv.end_min:
                return iv
        return None

    def journey_at(self, minute: float) -> Optional[JourneyRef]:
        for jn in self.journeys:
            if jn.start_min <= minute < jn.end_min:
                return jn
        return None

    def wear_status_at(self, minute: float) -> Optional[DeviceWear]:
        """Return wear status if - and only if - the host supplied wear data."""
        if not self.device_wear:
            return None
        for wp in self.device_wear:
            if wp.start_min <= minute < wp.end_min:
                return wp.status
        return None

    def window_of(self, minute: float) -> Optional[int]:
        for index, window in enumerate(self.waking_windows):
            if window.contains(minute):
                return index
        return None

    def coverage_minutes(self) -> float:
        return sum(ep.duration_min for ep in self.episodes)


# ==========================================================================
# request
# ==========================================================================

@dataclass(frozen=True)
class PersonaContextFacts(_ToDictMixin):
    """Stable persona attributes with a *direct contextual role* only.

    Closed allowlist (see ``vocab.ALLOWED_PERSONA_FACTS``).  Demographic,
    health, personality and hobby attributes are refused at construction time:
    the subjective-state generator must not be able to see them.
    """

    childcare_responsibility: Optional[bool] = None
    work_schedule_pattern: Optional[str] = None    # "standard" | "shift" | "flexible" | "remote"
    usual_commute_mode: Optional[str] = None       # "walk" | "bike" | "car" | "public_transport"
    usual_sleep_schedule: Optional[str] = None     # "early" | "regular" | "late" | "rotating"

    def __post_init__(self) -> None:
        from .vocab import check_persona_keys

        _allowed, rejected = check_persona_keys(
            [f.name for f in fields(self) if getattr(self, f.name) is not None]
        )
        if rejected:
            raise ValueError(f"refused persona attributes: {rejected}")

    @staticmethod
    def from_mapping(data: Optional[Mapping[str, Any]], strict: bool = True) -> "PersonaContextFacts":
        """Build from a mapping, dropping (strict) or refusing (non-strict) extras.

        ``strict=True`` raises on any non-allowlisted key; ``strict=False``
        drops those keys and is what the day importer uses when a host supplies
        a full persona blob.
        """
        from .vocab import ALLOWED_PERSONA_FACTS, check_persona_keys

        data = dict(data or {})
        keys = list(data.keys())
        allowed, rejected = check_persona_keys(keys)
        if rejected and strict:
            raise ValueError(
                "persona attributes are not permitted in subjective-state generation: "
                f"{sorted(rejected)} (allowed: {sorted(ALLOWED_PERSONA_FACTS)})"
            )
        kwargs = {key: data[key] for key in allowed}
        return PersonaContextFacts(**kwargs)


@dataclass
class EMARequest(_ToDictMixin):
    """Public input to the EMA module."""

    day: ContextualDay
    participant_id: str
    day_date: _date
    seed: int = 0
    protocol_name: str = "paper3_ema_v1"
    protocol_config_hash: Optional[str] = None
    persona_context: Optional[PersonaContextFacts] = None
    request_id: Optional[str] = None
    prior_same_day_state: Optional[dict[str, Any]] = None   # continuity, same day only
    llm: Optional[dict[str, Any]] = None                    # LLMSettings.to_dict() or None

    def __post_init__(self) -> None:
        self.day_date = to_date(self.day_date)
        if self.request_id is None:
            self.request_id = f"req-{self.participant_id}-{self.day_date.isoformat()}-{self.seed}"

    @property
    def participant(self) -> str:
        return self.participant_id

    def context_fingerprint(self) -> str:
        """Hash of the inherited contextual facts only.

        Recorded in provenance at generation time and recomputed by the
        validator: any mutation of inherited context is detected.
        """
        return self.day.fingerprint(16)

    def hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()[:32]


# ==========================================================================
# context packet
# ==========================================================================

@dataclass(frozen=True)
class EMAContextPacket(_ToDictMixin):
    """Minimal bounded factual context handed to the state generator / renderer.

    Contains *no* proper names, *no* narrative text and *no* demographic
    attributes.  Every field is inherited from the day or derived from it by a
    documented rule.
    """

    prompt_time_min: float
    prompt_time: datetime
    time_of_day: str                                   # "early_morning"|"morning"|"midday"|"afternoon"|"evening"|"late_evening"|"night"
    minutes_since_wake: Optional[float] = None
    window_index: Optional[int] = None
    window_label: Optional[str] = None

    # current context (inherited)
    activity: Optional[Activity] = None
    activity_label: Optional[str] = None
    domain: Optional[Domain] = None
    place_type: Optional[PlaceType] = None
    social_context: Optional[SocialContext] = None
    indoor_outdoor: Optional[IndoorOutdoor] = None
    purpose_category: Optional[str] = None
    device_wear: Optional[DeviceWear] = None

    # linkage (inherited ids)
    episode_id: Optional[str] = None
    interval_id: Optional[str] = None
    journey_id: Optional[str] = None

    # derived current-context quantities
    minutes_in_current_episode: Optional[float] = None
    minutes_since_activity_change: Optional[float] = None
    episode_is_unstable: bool = False
    current_journey_mode: Optional[str] = None

    # recent context (derived, bounded)
    preceding_activity: Optional[Activity] = None
    preceding_domain: Optional[Domain] = None
    preceding_place_type: Optional[PlaceType] = None
    preceding_journey_mode: Optional[str] = None
    preceding_journey_duration_min: Optional[float] = None
    preceding_journey_delayed: Optional[bool] = None
    preceding_journey_crowded: Optional[bool] = None
    minutes_since_journey_end: Optional[float] = None
    minutes_since_active_episode_end: Optional[float] = None
    recent_exertion_60min: Optional[float] = None      # 0..1 bounded aggregate
    recent_activity_summary: Optional[dict[str, float]] = None  # {"sitting": 34.0, ...} minutes in last 60

    # schedule pressure (derived)
    minutes_to_next_commitment: Optional[float] = None
    next_commitment_kind: Optional[str] = None
    next_commitment_requires_travel: Optional[bool] = None

    # optional, only when continuity is enabled
    previous_state: Optional[dict[str, int]] = None
    minutes_since_previous_prompt: Optional[float] = None

    # closed-world vocabulary handed to the renderer
    allowed_entities: tuple[str, ...] = ()
    allowed_causes: tuple[str, ...] = ()
    weather_available: bool = False

    def fact_view(self) -> dict[str, Any]:
        """Subset used for closed-world checking and grounding tests."""
        return {
            "activity": self.activity.value if self.activity else None,
            "activity_label": self.activity_label,
            "domain": self.domain.value if self.domain else None,
            "place_type": self.place_type.value if self.place_type else None,
            "social_context": self.social_context.value if self.social_context else None,
            "indoor_outdoor": self.indoor_outdoor.value if self.indoor_outdoor else None,
            "purpose_category": self.purpose_category,
            "preceding_activity": self.preceding_activity.value if self.preceding_activity else None,
            "preceding_domain": self.preceding_domain.value if self.preceding_domain else None,
            "preceding_journey_mode": self.preceding_journey_mode,
            "preceding_journey_delayed": self.preceding_journey_delayed,
            "preceding_journey_crowded": self.preceding_journey_crowded,
            "current_journey_mode": self.current_journey_mode,
            "minutes_since_journey_end": self.minutes_since_journey_end,
            "minutes_since_active_episode_end": self.minutes_since_active_episode_end,
            "minutes_to_next_commitment": self.minutes_to_next_commitment,
            "next_commitment_kind": self.next_commitment_kind,
            "time_of_day": self.time_of_day,
            "weather_available": self.weather_available,
            "allowed_entities": list(self.allowed_entities),
            "allowed_causes": list(self.allowed_causes),
        }


# ==========================================================================
# prompt / response
# ==========================================================================

@dataclass
class EMAPrompt(_ToDictMixin):
    """One EMA opportunity (scheduled, before any response exists)."""

    prompt_id: str
    participant_id: str
    day_date: _date
    schedule_index: int
    trigger: TriggerType
    prompt_time: datetime
    prompt_time_min: float
    window_index: Optional[int] = None
    window_label: Optional[str] = None
    episode_id: Optional[str] = None
    interval_id: Optional[str] = None
    journey_id: Optional[str] = None
    event_id: Optional[str] = None
    event_kind: Optional[str] = None
    minutes_after_event: Optional[float] = None
    selection_reason: str = ""
    is_event_enriched: bool = False
    stability_relaxed: bool = False
    recall_frame: str = "current_at_prompt_time"
    expiry_minutes: float = 10.0
    expires_at: Optional[datetime] = None
    inherited_context: dict[str, Any] = field(default_factory=dict)
    packet: Optional[EMAContextPacket] = None

    def __post_init__(self) -> None:
        self.day_date = to_date(self.day_date)
        self.is_event_enriched = self.trigger != TriggerType.SEMI_RANDOM


@dataclass
class SubjectiveState(_ToDictMixin):
    """Synthetic subjective values.  NOT observed human measurements."""

    valence: int
    energy: int
    stress: int
    latent: dict[str, float] = field(default_factory=dict)
    contributions: dict[str, dict[str, float]] = field(default_factory=dict)
    noise: dict[str, float] = field(default_factory=dict)
    rules_applied: tuple[str, ...] = ()
    generator_version: str = ""

    def items(self) -> dict[str, int]:
        return {"valence": self.valence, "energy": self.energy, "stress": self.stress}


@dataclass
class EMAResponse(_ToDictMixin):
    """Outcome of one EMA opportunity."""

    prompt_id: str
    status: ResponseStatus
    prompt_time: datetime
    response_time: Optional[datetime] = None
    latency_min: Optional[float] = None
    expiry_minutes: float = 10.0
    answered: bool = False
    expired: bool = False
    usable_for_alignment: bool = False
    subjective: Optional[SubjectiveState] = None
    context_note: Optional[str] = None
    note_source: Optional[str] = None                # "llm" | "offline_template" | None
    note_validation: Optional[dict[str, Any]] = None
    device_wear: Optional[DeviceWear] = None         # inherited, optional
    nonresponse_reason: Optional[str] = None         # "not_answered" | "expired"
    response_probability: Optional[float] = None     # simulated propensity (for audit)
    context_reference_time: str = "prompt_time"


@dataclass
class EMARecord(_ToDictMixin):
    """One complete EMA opportunity: prompt + response + context + provenance.

    ``provenance`` is the run-level :class:`EMAProvenance`; the per-record
    traceability payload lives in ``provenance.record_provenance[prompt_id]``.
    """

    prompt: EMAPrompt
    response: EMAResponse
    packet: EMAContextPacket
    provenance: "EMAProvenance"

    @property
    def prompt_id(self) -> str:
        return self.prompt.prompt_id

    @property
    def record_provenance(self) -> dict[str, Any]:
        return dict(self.provenance.record_provenance.get(self.prompt_id, {}))

    @property
    def trigger(self) -> TriggerType:
        return self.prompt.trigger

    def subjective_items(self) -> Optional[dict[str, int]]:
        return self.response.subjective.items() if self.response.subjective else None

    def flat_row(self) -> dict[str, Any]:
        """Flat, analysis-friendly row (used by the demo report)."""
        row: dict[str, Any] = {
            "participant_id": self.prompt.participant_id,
            "date": self.prompt.day_date.isoformat(),
            "prompt_id": self.prompt.prompt_id,
            "schedule_index": self.prompt.schedule_index,
            "trigger": self.prompt.trigger.value,
            "is_event_enriched": self.prompt.is_event_enriched,
            "prompt_time": self.prompt.prompt_time.strftime("%H:%M"),
            "prompt_time_min": round(self.prompt.prompt_time_min, 1),
            "window_index": self.prompt.window_index,
            "episode_id": self.prompt.episode_id,
            "interval_id": self.prompt.interval_id,
            "journey_id": self.prompt.journey_id,
            "event_id": self.prompt.event_id,
            "minutes_after_event": self.prompt.minutes_after_event,
            "status": self.response.status.value,
            "response_time": self.response.response_time.strftime("%H:%M") if self.response.response_time else None,
            "latency_min": round(self.response.latency_min, 2) if self.response.latency_min is not None else None,
            "expired": self.response.expired,
            "device_wear": self.response.device_wear.value if self.response.device_wear else None,
            "context_note": self.response.context_note,
            "note_source": self.response.note_source,
        }
        ctx = self.prompt.inherited_context
        for key in ("activity", "domain", "place_type", "social_context", "indoor_outdoor"):
            row[f"ctx_{key}"] = ctx.get(key)
        for key in ("preceding_activity", "preceding_journey_mode", "minutes_since_journey_end",
                    "minutes_since_active_episode_end", "minutes_to_next_commitment",
                    "minutes_since_wake", "recent_exertion_60min"):
            row[key] = self.packet.to_dict().get(key)
        items = self.subjective_items() or {}
        for key in ("valence", "energy", "stress"):
            row[key] = items.get(key)
        return row


@dataclass
class EMAProvenance(_ToDictMixin):
    """Full traceability record for one participant-day."""

    protocol_version: str
    schema_version: str = SCHEMA_VERSION
    package_version: str = ""
    scheduler_version: str = ""
    state_generator_version: str = ""
    auditor_version: str = ""
    note_validator_version: str = ""
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_template_version: Optional[str] = None
    llm_decoding: Optional[dict[str, Any]] = None
    llm_calls: int = 0
    llm_retries: int = 0
    seed: Optional[int] = None
    request_hash: Optional[str] = None
    context_fingerprint: Optional[str] = None
    config_hash: Optional[str] = None
    config_name: Optional[str] = None
    participant_id: Optional[str] = None
    day_date: Optional[str] = None
    generated_at: Optional[str] = None
    field_provenance: dict[str, str] = field(default_factory=dict)
    record_provenance: dict[str, dict[str, Any]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class EMAValidationIssue(_ToDictMixin):
    code: str
    severity: str                       # "error" | "warning" | "info"
    message: str
    prompt_id: Optional[str] = None
    field: Optional[str] = None


@dataclass
class EMAValidationResult(_ToDictMixin):
    valid: bool
    status: str                         # "PASS" | "FAIL"
    issues: list[EMAValidationIssue] = field(default_factory=list)
    checks_run: int = 0
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[EMAValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[EMAValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


@dataclass
class ScheduleAuditIssue(_ToDictMixin):
    code: str
    severity: str
    message: str
    prompt_time: Optional[str] = None


@dataclass
class ScheduleAuditResult(_ToDictMixin):
    """Read-only verdict about an existing schedule.  Never repairs anything."""

    status: AuditStatus
    valid: bool
    issues: list[ScheduleAuditIssue] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    prompt_times: list[str] = field(default_factory=list)
    auditor_version: str = ""

    @property
    def reasons(self) -> list[str]:
        return [f"[{i.severity}] {i.code}: {i.message}" for i in self.issues]


@dataclass
class EMABundle(_ToDictMixin):
    """Public output: one participant-day of EMA opportunities."""

    participant_id: str
    day_date: _date
    protocol_name: str
    records: list[EMARecord] = field(default_factory=list)
    provenance: EMAProvenance = field(default_factory=lambda: EMAProvenance(protocol_version="paper3_ema_v1"))
    validation: Optional[EMAValidationResult] = None
    scales: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    audit: Optional[ScheduleAuditResult] = None

    def __post_init__(self) -> None:
        self.day_date = to_date(self.day_date)

    @property
    def prompts(self) -> list[EMAPrompt]:
        return [r.prompt for r in self.records]

    @property
    def responses(self) -> list[EMAResponse]:
        return [r.response for r in self.records]

    def answered(self) -> list[EMARecord]:
        return [r for r in self.records if r.response.answered]

    def rows(self) -> list[dict[str, Any]]:
        return [r.flat_row() for r in self.records]


# ==========================================================================
# events (internal, but serialised for auditability)
# ==========================================================================

@dataclass(frozen=True)
class DayEvent(_ToDictMixin):
    """A detected candidate event for event-enriched sampling."""

    event_id: str
    kind: TriggerType
    end_min: float
    start_min: float
    priority: int
    score: float
    episode_id: Optional[str] = None
    interval_id: Optional[str] = None
    journey_id: Optional[str] = None
    window_index: Optional[int] = None
    label: Optional[str] = None
    reason: str = ""

    @property
    def duration_min(self) -> float:
        return self.end_min - self.start_min


@dataclass(frozen=True)
class PromptCandidate(_ToDictMixin):
    """A legal minute at which a prompt could be delivered."""

    minute: float
    window_index: Optional[int]
    episode_id: Optional[str]
    interval_id: Optional[str]
    journey_id: Optional[str]
    reason: str = ""
