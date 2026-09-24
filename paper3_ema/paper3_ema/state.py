"""Structured, seeded, context-conditioned synthetic subjective-state generator.

This module produces the Paper 3 synthetic subjective values (``valence``,
``energy``, ``stress``) on a documented five-point ordinal scale.

Design contract
---------------
* **seed-controlled and reproducible** — identical ``(participant, date, seed,
  packet, config)`` always yields identical values;
* **context-sensitive but stochastic** — contextual variables *modestly* shift a
  latent value; the ordinal response is then sampled around that latent value.
  Neither extreme is allowed: not ``activity == work -> stress = high`` and not
  ``stress = random.choice(1..5)``;
* **bounded** — modifiers are individually documented, summed, hard-clipped
  (``modifier_clip``) and the latent value is clipped to ``hard_clip``;
* **transparent** — every applied rule is returned by name with its numeric
  contribution, and is registered in ``docs/SCIENTIFIC_ASSUMPTIONS.md``;
* **demographically blind** — the generator reads only the packet plus a closed
  allowlist of persona facts (childcare responsibility, work-schedule pattern,
  usual commute mode, usual sleep schedule).  Age, sex/gender, occupation,
  health, fitness, personality and hobbies are refused
  (:class:`paper3_ema.models.PersonaContextFacts`).

These are simulation rules, **not** claims about human psychology, and the
outputs are **not** observed human measurements.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from .config import ProtocolConfig, default_config
from .context import CONTEXT_BUILDER_VERSION
from .models import EMAContextPacket, PersonaContextFacts, SubjectiveState
from .vocab import (
    SCALE_MAX,
    SCALE_MIN,
    SUBJECTIVE_ITEMS,
    Activity,
    Domain,
    IndoorOutdoor,
    SocialContext,
    clamp_scale,
)

STATE_GENERATOR_VERSION = "1.0.0"

GENERATOR_INPUT_FIELDS: tuple[str, ...] = (
    "prompt_time_min",
    "time_of_day",
    "minutes_since_wake",
    "activity",
    "domain",
    "place_type",
    "social_context",
    "indoor_outdoor",
    "purpose_category",
    "minutes_since_journey_end",
    "preceding_journey_mode",
    "preceding_journey_delayed",
    "preceding_journey_crowded",
    "minutes_since_active_episode_end",
    "recent_exertion_60min",
    "minutes_to_next_commitment",
    "next_commitment_kind",
    "next_commitment_requires_travel",
    "minutes_since_activity_change",
    "previous_state",
    "minutes_since_previous_prompt",
)
"""Exhaustive list of packet fields the generator may read.  Enforced by a
test (``tests/test_state_generator.py``) so that no demographic or narrative
field can be added silently."""


@dataclass
class RuleApplication:
    rule: str
    item: str
    delta: float
    detail: str = ""


@dataclass
class StateTrace:
    """Full audit trail of one state draw."""

    item: str
    baseline: float
    day_effect: float
    rules: list[RuleApplication] = field(default_factory=list)
    modifier_total: float = 0.0
    modifier_clipped: float = 0.0
    continuity_anchor: Optional[float] = None
    continuity_weight: float = 0.0
    latent_pre_noise: float = 0.0
    noise: float = 0.0
    latent: float = 0.0
    sampled: float = 0.0
    ordinal: int = 3

    def contributions(self) -> dict[str, float]:
        values = {rule.rule: round(rule.delta, 4) for rule in self.rules}
        values["_baseline"] = round(self.baseline, 4)
        values["_day_effect"] = round(self.day_effect, 4)
        if self.continuity_anchor is not None:
            values["_continuity"] = round(self.continuity_anchor - self.latent_pre_noise, 4)
        values["_modifier_clip"] = round(self.modifier_clipped - self.modifier_total, 4)
        return values


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _gaussian(rng: random.Random) -> float:
    """Standard normal draw from ``random.Random`` only (no numpy)."""
    return rng.gauss(0.0, 1.0)


def _day_effects(participant_id: str, day_date: Any, seed: int, sd: float) -> dict[str, float]:
    """Person-day level offsets: make days differ without stereotyping."""
    rng = random.Random(f"paper3_ema|day|{participant_id}|{day_date}|{seed}")
    return {item: rng.gauss(0.0, sd) for item in SUBJECTIVE_ITEMS}


def _float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# rule implementations
# --------------------------------------------------------------------------

def _rule_circadian(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.circadian")
    if not section.get("enabled", True):
        return []
    period = packet.time_of_day
    rules: list[RuleApplication] = []
    for item, key in (("energy", "energy_by_period"), ("valence", "valence_by_period"), ("stress", "stress_by_period")):
        table = section.get(key) or {}
        delta = _float(dict(table).get(period))
        if delta:
            rules.append(RuleApplication(f"circadian.{period}", item, delta, f"time-of-day period '{period}'"))
    return rules


def _rule_minutes_since_wake(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.minutes_since_wake")
    if not section.get("enabled", True):
        return []
    minutes = _float(packet.minutes_since_wake)
    if minutes is None:
        return []
    ramp = float(section.get("energy_ramp_minutes", 60))
    boost = float(section.get("energy_max_boost", 0.5))
    if ramp <= 0 or minutes >= ramp:
        return []
    delta = boost * (minutes / ramp)
    return [RuleApplication("wake_ramp", "energy", round(delta, 4), f"{minutes:.0f} min since waking (ramp {ramp:.0f} min)")]


def _rule_recent_exertion(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.recent_exertion")
    if not section.get("enabled", True):
        return []
    exertion = _float(packet.recent_exertion_60min)
    if exertion is None or exertion <= 0.02:
        return []
    rules = [
        RuleApplication("recent_exertion.energy", "energy", round(float(section.get("energy_effect", -0.9)) * exertion, 4),
                        f"bounded recent exertion {exertion:.2f}"),
        RuleApplication("recent_exertion.valence", "valence", round(float(section.get("valence_effect", 0.35)) * exertion, 4),
                        f"bounded recent exertion {exertion:.2f}"),
        RuleApplication("recent_exertion.stress", "stress", round(float(section.get("stress_effect", -0.15)) * exertion, 4),
                        f"bounded recent exertion {exertion:.2f}"),
    ]
    return rules


def _rule_post_journey(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.post_journey")
    if not section.get("enabled", True):
        return []
    elapsed = _float(packet.minutes_since_journey_end)
    mode = (packet.preceding_journey_mode or "").lower()
    if elapsed is None or not mode:
        return []
    window = float(section.get("window_minutes", 30))
    if elapsed > window:
        return []
    active = {str(item).lower() for item in (section.get("active_modes") or [])}
    public = {str(item).lower() for item in (section.get("public_modes") or [])}
    car = {str(item).lower() for item in (section.get("car_modes") or [])}
    if mode in active:
        kind, table = "active", section.get("active") or {}
    elif mode in public:
        kind, table = "public", section.get("public") or {}
    elif mode in car:
        kind, table = "car", section.get("car") or {}
    else:
        return []
    decay = max(0.0, 1.0 - (elapsed / window) * 0.5)
    rules = [
        RuleApplication(f"post_journey.{kind}.{item}", item, round(_float(value) * decay, 4),
                        f"{mode} journey ended {elapsed:.0f} min ago")
        for item, value in dict(table).items()
        if _float(value)
    ]
    if packet.preceding_journey_delayed:
        rules.extend(
            RuleApplication(f"journey_delayed.{item}", item, _float(value), "host-documented journey delay")
            for item, value in dict(section.get("delayed_journey") or {}).items()
            if _float(value)
        )
    if packet.preceding_journey_crowded:
        rules.extend(
            RuleApplication(f"journey_crowded.{item}", item, _float(value), "host-documented crowding")
            for item, value in dict(section.get("crowded_journey") or {}).items()
            if _float(value)
        )
    return rules


def _rule_schedule_pressure(
    packet: EMAContextPacket,
    config: ProtocolConfig,
    persona: Optional[PersonaContextFacts],
) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.schedule_pressure")
    if not section.get("enabled", True):
        return []
    minutes = _float(packet.minutes_to_next_commitment)
    if minutes is None:
        return []
    horizons = [float(value) for value in (section.get("horizons_minutes") or [30, 60, 120])]
    table = {float(key): _float(value) or 0.0 for key, value in dict(section.get("pressure_by_horizon") or {}).items()}
    pressure = 0.0
    matched: Optional[float] = None
    for horizon in sorted(horizons):
        if minutes <= horizon:
            pressure = table.get(horizon, 0.0)
            matched = horizon
            break
    if pressure <= 0:
        return []
    if packet.next_commitment_requires_travel:
        pressure += float(section.get("extra_when_travel_required", 0.0))
    detail = f"next fixed commitment in {minutes:.0f} min (horizon {matched:.0f} min)"
    if persona and persona.work_schedule_pattern == "shift":
        pressure += float(config.get("persona.shift_work_extra_pressure", 0.0))
        detail += "; host-declared shift-work schedule pattern"
    rules = [
        RuleApplication("schedule_pressure.stress", "stress", round(float(section.get("stress_effect", 1.0)) * pressure, 4), detail),
        RuleApplication("schedule_pressure.energy", "energy", round(float(section.get("energy_effect", -0.25)) * pressure, 4), detail),
        RuleApplication("schedule_pressure.valence", "valence", round(float(section.get("valence_effect", -0.2)) * pressure, 4), detail),
    ]
    return rules


def _rule_post_transition(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.post_transition")
    if not section.get("enabled", True):
        return []
    change = _float(packet.minutes_since_activity_change)
    if change is None:
        return []
    window = float(section.get("window_minutes", 20))
    if change > window:
        return []
    detail = f"activity changed {change:.0f} min ago"
    rules: list[RuleApplication] = []
    for item in SUBJECTIVE_ITEMS:
        value = _float(section.get(item))
        if value:
            rules.append(RuleApplication(f"post_transition.{item}", item, value, detail))
    return rules


def _rule_social_company(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.social_company")
    if not section.get("enabled", True) or packet.social_context is None:
        return []
    from .context import SOCIAL_WITH_COMPANY

    table = section.get("with_company") if packet.social_context in SOCIAL_WITH_COMPANY else section.get("alone")
    if not table:
        return []
    detail = f"social setting '{packet.social_context.value}'"
    return [
        RuleApplication(f"social_company.{item}", item, _float(value), detail)
        for item, value in dict(table).items()
        if _float(value)
    ]


def _rule_domain(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.domain")
    if not section.get("enabled", True) or packet.domain is None:
        return []
    cap = float(section.get("max_abs_total", 0.3))
    rules: list[RuleApplication] = []
    for item in SUBJECTIVE_ITEMS:
        table = {str(key): _float(value) for key, value in dict(section.get(item) or {}).items()}
        delta = table.get(packet.domain.value)
        if delta is None:
            continue
        delta = max(-cap, min(cap, delta))
        if delta:
            rules.append(
                RuleApplication(
                    f"domain.{packet.domain.value}.{item}",
                    item,
                    round(delta, 4),
                    f"behavioural domain '{packet.domain.value}' (bounded small effect, capped at +/-{cap})",
                )
            )
    return rules


def _rule_outdoor(packet: EMAContextPacket, config: ProtocolConfig) -> list[RuleApplication]:
    section = config.section("state_generator.modifiers.outdoor")
    if not section.get("enabled", True) or packet.indoor_outdoor is None:
        return []
    table = section.get("outdoor") if packet.indoor_outdoor == IndoorOutdoor.OUTDOOR else section.get("indoor")
    if not table:
        return []
    detail = f"environment '{packet.indoor_outdoor.value}'"
    return [
        RuleApplication(f"outdoor.{item}", item, _float(value), detail)
        for item, value in dict(table).items()
        if _float(value)
    ]


def _rule_childcare(
    packet: EMAContextPacket,
    config: ProtocolConfig,
    persona: Optional[PersonaContextFacts],
) -> list[RuleApplication]:
    """Allowed persona use: childcare responsibility *inside* a childcare episode."""
    if not config.get("persona.use_childcare_responsibility", True):
        return []
    if persona is None or not persona.childcare_responsibility:
        return []
    if packet.domain != Domain.CHILDCARE:
        return []
    table = config.get("persona.childcare_effect") or {}
    detail = "host-declared childcare responsibility during a childcare episode"
    return [
        RuleApplication(f"childcare_responsibility.{item}", item, _float(value), detail)
        for item, value in dict(table).items()
        if _float(value)
    ]


def _rule_commute_context(packet: EMAContextPacket, config: ProtocolConfig, persona: Optional[PersonaContextFacts]) -> list[RuleApplication]:
    """Allowed persona use: usual commute mode, only in a transport context."""
    if persona is None or not persona.usual_commute_mode:
        return []
    if packet.domain != Domain.TRANSPORT:
        return []
    mode = str(persona.usual_commute_mode).lower()
    usual_is_active = mode in {"walk", "walking", "bike", "bicycle", "cycling", "foot"}
    current_mode = (packet.current_journey_mode or packet.preceding_journey_mode or "").lower()
    if not current_mode:
        return []
    current_is_active = current_mode in {"walk", "walking", "bike", "bicycle", "cycling", "foot"}
    if usual_is_active == current_is_active:
        return []  # expected mode: no extra synthetic effect
    delta_valence = -0.10 if usual_is_active else 0.05
    delta_stress = 0.15 if usual_is_active else -0.05
    detail = f"host-declared usual commute mode '{mode}' vs current transport mode '{current_mode}'"
    return [
        RuleApplication("commute_mode_mismatch.valence", "valence", delta_valence, detail),
        RuleApplication("commute_mode_mismatch.stress", "stress", delta_stress, detail),
    ]


ALL_RULES = (
    "circadian",
    "minutes_since_wake",
    "recent_exertion",
    "post_journey",
    "schedule_pressure",
    "post_transition",
    "social_company",
    "domain",
    "outdoor",
    "childcare_responsibility",
    "commute_mode_mismatch",
)


# --------------------------------------------------------------------------
# main entry point
# --------------------------------------------------------------------------

def collect_rules(
    packet: EMAContextPacket,
    config: ProtocolConfig,
    persona: Optional[PersonaContextFacts] = None,
) -> list[RuleApplication]:
    rules: list[RuleApplication] = []
    rules += _rule_circadian(packet, config)
    rules += _rule_minutes_since_wake(packet, config)
    rules += _rule_recent_exertion(packet, config)
    rules += _rule_post_journey(packet, config)
    rules += _rule_schedule_pressure(packet, config, persona)
    rules += _rule_post_transition(packet, config)
    rules += _rule_social_company(packet, config)
    rules += _rule_domain(packet, config)
    rules += _rule_outdoor(packet, config)
    rules += _rule_childcare(packet, config, persona)
    rules += _rule_commute_context(packet, config, persona)
    return rules


def generate_state(
    packet: EMAContextPacket,
    config: Optional[ProtocolConfig] = None,
    seed: int = 0,
    participant_id: str = "participant",
    day_date: Any = None,
    prompt_id: str = "",
    persona: Optional[PersonaContextFacts] = None,
    previous_state: Optional[Mapping[str, int]] = None,
    minutes_since_previous_prompt: Optional[float] = None,
) -> tuple[SubjectiveState, dict[str, StateTrace]]:
    """Generate the synthetic subjective state for one EMA opportunity.

    Returns ``(SubjectiveState, traces)`` where ``traces`` documents every rule
    contribution per item (serialised into provenance).
    """
    config = config or default_config()
    section = config.section("state_generator")
    baseline = {item: float((section.get("baseline") or {}).get(item, 3.0)) for item in SUBJECTIVE_ITEMS}
    day_sd = float(section.get("day_effect_sd", 0.45))
    noise_sd = {item: float((section.get("noise_sd") or {}).get(item, 0.45)) for item in SUBJECTIVE_ITEMS}
    modifier_clip = float(section.get("modifier_clip", 1.5))
    hard_clip = [float(value) for value in (section.get("hard_clip") or [SCALE_MIN, SCALE_MAX])]
    sampling_sd = float(section.get("sampling.sd", 0.6))

    continuity = section.section("continuity")
    continuity_enabled = bool(continuity.get("enabled", True))
    continuity_weight = float(continuity.get("weight", 0.35))
    continuity_max_interval = float(continuity.get("max_interval_minutes", 240))

    previous = dict(previous_state or packet.previous_state or {})
    minutes_since_previous = (
        minutes_since_previous_prompt
        if minutes_since_previous_prompt is not None
        else packet.minutes_since_previous_prompt
    )
    continuity_usable = bool(
        continuity_enabled
        and previous
        and (minutes_since_previous is None or float(minutes_since_previous) <= continuity_max_interval)
    )

    day_effects = _day_effects(participant_id, day_date, seed, day_sd)
    rules = collect_rules(packet, config, persona)

    rng = random.Random(f"paper3_ema|state|{participant_id}|{day_date}|{seed}|{prompt_id}")
    traces: dict[str, StateTrace] = {}
    values: dict[str, int] = {}
    latents: dict[str, float] = {}
    noise_draws: dict[str, float] = {}
    contributions: dict[str, dict[str, float]] = {}
    applied: list[str] = []

    for item in SUBJECTIVE_ITEMS:  # fixed order => reproducible
        item_rules = [rule for rule in rules if rule.item == item]
        trace = StateTrace(item=item, baseline=baseline[item], day_effect=round(day_effects[item], 4))
        trace.rules = item_rules
        modifier_total = sum(rule.delta for rule in item_rules)
        modifier_clipped = max(-modifier_clip, min(modifier_clip, modifier_total))
        trace.modifier_total = round(modifier_total, 4)
        trace.modifier_clipped = round(modifier_clipped, 4)
        latent = baseline[item] + day_effects[item] + modifier_clipped
        if continuity_usable and item in previous:
            anchor = float(previous[item])
            trace.continuity_anchor = anchor
            trace.continuity_weight = continuity_weight
            latent = (1.0 - continuity_weight) * latent + continuity_weight * anchor
        trace.latent_pre_noise = round(latent, 4)
        noise = rng.gauss(0.0, noise_sd[item])
        trace.noise = round(noise, 4)
        latent += noise
        latent = max(hard_clip[0], min(hard_clip[1], latent))
        trace.latent = round(latent, 4)
        sampled = latent + rng.gauss(0.0, sampling_sd)
        trace.sampled = round(sampled, 4)
        ordinal = clamp_scale(sampled)
        trace.ordinal = ordinal
        values[item] = ordinal
        latents[item] = trace.latent
        noise_draws[item] = trace.noise
        contributions[item] = trace.contributions()
        applied.extend(sorted({rule.rule for rule in item_rules}))
        traces[item] = trace

    state = SubjectiveState(
        valence=values["valence"],
        energy=values["energy"],
        stress=values["stress"],
        latent={item: round(value, 4) for item, value in latents.items()},
        contributions={item: contributions[item] for item in SUBJECTIVE_ITEMS},
        noise={item: round(value, 4) for item, value in noise_draws.items()},
        rules_applied=tuple(sorted(set(applied))),
        generator_version=f"{STATE_GENERATOR_VERSION}+ctx{CONTEXT_BUILDER_VERSION}",
    )
    return state, traces


def traces_to_dict(traces: Mapping[str, StateTrace]) -> dict[str, Any]:
    return {
        item: {
            "baseline": trace.baseline,
            "day_effect": trace.day_effect,
            "modifier_total": trace.modifier_total,
            "modifier_clipped": trace.modifier_clipped,
            "continuity_anchor": trace.continuity_anchor,
            "continuity_weight": trace.continuity_weight,
            "latent_pre_noise": trace.latent_pre_noise,
            "noise": trace.noise,
            "latent": trace.latent,
            "sampled": trace.sampled,
            "ordinal": trace.ordinal,
            "rules": [
                {"rule": rule.rule, "item": rule.item, "delta": round(rule.delta, 4), "detail": rule.detail}
                for rule in trace.rules
            ],
        }
        for item, trace in traces.items()
    }


def explain_state(state: SubjectiveState, traces: Mapping[str, StateTrace]) -> str:
    """Human-readable explanation of one draw (used in demo reports)."""
    lines = [
        f"valence={state.valence} energy={state.energy} stress={state.stress} "
        f"(latent {state.latent}) generator={state.generator_version}"
    ]
    for item, trace in traces.items():
        parts = ", ".join(f"{rule.rule}:{rule.delta:+.2f}" for rule in trace.rules) or "no contextual rule fired"
        lines.append(
            f"  {item}: baseline {trace.baseline:+.2f} | day {trace.day_effect:+.2f} | {parts} "
            f"| clipped {trace.modifier_clipped:+.2f} | continuity "
            f"{'n/a' if trace.continuity_anchor is None else f'{trace.continuity_anchor:.0f}@w={trace.continuity_weight:.2f}'} "
            f"| noise {trace.noise:+.2f} -> latent {trace.latent:.2f} -> sampled {trace.sampled:.2f} -> {trace.ordinal}"
        )
    return "\n".join(lines)


def is_deterministic_stereotype(
    states: Sequence[SubjectiveState],
    contexts: Sequence[EMAContextPacket],
) -> dict[str, Any]:
    """Diagnostic used by tests/demo: does one context value always map to one state?

    Returns per-(context field, value, item) concentration statistics.  A
    deterministic stereotype shows up as ``distinct == 1`` with ``n >= 5``.
    """
    buckets: dict[tuple[str, Any, str], list[int]] = {}
    for state, packet in zip(states, contexts):
        for field_name in ("activity", "domain", "place_type", "social_context"):
            value = getattr(packet, field_name)
            key_value = value.value if value is not None else None
            for item in SUBJECTIVE_ITEMS:
                buckets.setdefault((field_name, key_value, item), []).append(getattr(state, item))
    report: dict[str, Any] = {}
    for (field_name, key_value, item), values in sorted(buckets.items()):
        if len(values) < 5:
            continue
        distinct = len(set(values))
        report[f"{field_name}={key_value}:{item}"] = {
            "n": len(values),
            "distinct": distinct,
            "values": sorted(set(values)),
            "stereotype": distinct == 1,
        }
    return report
