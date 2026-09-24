"""Response / non-response model (missingness).

Missingness is simulated **separately** from subjective content: the response
decision never looks at valence, energy or stress, and the state generator never
looks at the response decision.

Historical behaviour explicitly rejected here: ``exactly one missed probe per
day`` (``EMA-Diary-Generation/modules/ema_generator.py:44``).  Paper 3 uses a
configurable stochastic Bernoulli response model whose canonical calibration
lands in the ``missingness.calibration_target_response_rate`` band
(≈85-90 % answered across a sufficiently large cohort).  That target is a
*simulation calibration* target, not a claim about true human compliance.

Evidence for the direction of the modifiers (magnitudes are Paper 3 design
choices): ``EMA_Definitive_Synthesis.md`` §7.2 and §13.1,
``Scite_Opus4.6_v2.md`` line 210, ``Gemini.md`` line 118 — responses are less
likely during vigorous activity, driving, intense social/occupational
situations, and when the device is not worn.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

from .config import ProtocolConfig, default_config
from .models import EMAContextPacket, EMAPrompt
from .vocab import TriggerType

MISSINGNESS_MODEL_VERSION = "1.0.0"


@dataclass
class ResponseDecision:
    responded: bool
    probability: float
    base_probability: float
    modifiers_applied: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "responded": self.responded,
            "probability": round(self.probability, 4),
            "base_probability": round(self.base_probability, 4),
            "modifiers_applied": {key: round(value, 4) for key, value in self.modifiers_applied.items()},
            "reasons": list(self.reasons),
        }


def base_probability(trigger: TriggerType, config: ProtocolConfig) -> float:
    table = config.get("missingness.base_response_probability") or {}
    value = dict(table).get(trigger.value)
    if value is None:
        value = dict(table).get(TriggerType.SEMI_RANDOM.value, 0.9)
    return float(value)


def response_probability(
    prompt: EMAPrompt,
    packet: EMAContextPacket,
    config: Optional[ProtocolConfig] = None,
    study_day_index: Optional[int] = None,
) -> ResponseDecision:
    """Compute the (documented) propensity to answer one prompt."""
    config = config or default_config()
    section = config.section("missingness")
    probability = base_probability(prompt.trigger, config)
    decision = ResponseDecision(
        responded=False,
        probability=probability,
        base_probability=probability,
    )

    def apply_modifier(name: str, enabled_section: Any, multiplier_key: str, reason: str) -> None:
        nonlocal probability
        if not enabled_section.get("enabled", False):
            return
        multiplier = float(enabled_section.get(multiplier_key, 1.0))
        if multiplier == 1.0:
            return
        probability *= multiplier
        decision.modifiers_applied[name] = multiplier
        decision.reasons.append(reason)

    exertion = packet.recent_exertion_60min
    high_exertion = section.section("modifiers.high_exertion")
    if exertion is not None and float(exertion) >= float(high_exertion.get("threshold", 0.55)):
        apply_modifier(
            "high_exertion",
            high_exertion,
            "multiplier",
            f"bounded recent exertion {exertion:.2f} >= {high_exertion.get('threshold')} "
            "(evidence: responses are less likely during vigorous activity)",
        )

    engaged = section.section("modifiers.engaged_context")
    engaged_domains = {str(item) for item in (engaged.get("domains") or [])}
    engaged_activities = {str(item) for item in (engaged.get("activities") or [])}
    domain_match = packet.domain is not None and packet.domain.value in engaged_domains
    activity_match = packet.activity is not None and packet.activity.value in engaged_activities
    if domain_match or activity_match:
        why = []
        if domain_match:
            why.append(f"domain '{packet.domain.value}'")
        if activity_match:
            why.append(f"activity '{packet.activity.value}'")
        apply_modifier(
            "engaged_context",
            engaged,
            "multiplier",
            "engaged context: " + " and ".join(why) + " (evidence: intense social/occupational situations)",
        )

    late = section.section("modifiers.late_window")
    threshold = float(late.get("after_minute_of_day", 1260))
    if packet.prompt_time_min >= threshold:
        apply_modifier(
            "late_window",
            late,
            "multiplier",
            f"prompt at minute {packet.prompt_time_min:.0f} >= {threshold:.0f} (late in the day)",
        )

    not_worn = section.section("modifiers.device_not_worn")
    if packet.device_wear is not None and packet.device_wear.value == "not_worn":
        apply_modifier(
            "device_not_worn",
            not_worn,
            "multiplier",
            "host-supplied device-wear status is 'not_worn'",
        )

    decay = section.section("modifiers.study_day_decay")
    if decay.get("enabled", False) and study_day_index is not None:
        start = int(decay.get("start_day_index", 3))
        if study_day_index >= start:
            multiplier = float(decay.get("per_day_multiplier", 0.98)) ** (study_day_index - start + 1)
            probability *= multiplier
            decision.modifiers_applied["study_day_decay"] = multiplier
            decision.reasons.append(
                f"study day {study_day_index} (decay from day {start}; "
                "evidence: compliance drops after the first days in event-triggered setups)"
            )

    minimum = float(section.get("min_probability", 0.05))
    maximum = float(section.get("max_probability", 0.995))
    probability = max(minimum, min(maximum, probability))
    decision.probability = probability
    return decision


def draw_response(
    prompt: EMAPrompt,
    packet: EMAContextPacket,
    rng: random.Random,
    config: Optional[ProtocolConfig] = None,
    study_day_index: Optional[int] = None,
) -> ResponseDecision:
    """Seed-controlled Bernoulli draw.  The decision is independent of content."""
    decision = response_probability(prompt, packet, config, study_day_index)
    decision.responded = rng.random() < decision.probability
    if not decision.responded:
        decision.reasons.append("Bernoulli draw: prompt not answered (recorded as missing)")
    return decision


def expected_response_rate(config: Optional[ProtocolConfig] = None) -> dict[str, float]:
    """Base rates per trigger (used by the calibration test/report)."""
    config = config or default_config()
    return {
        trigger.value: base_probability(trigger, config)
        for trigger in (
            TriggerType.SEMI_RANDOM,
            TriggerType.POST_TRIP,
            TriggerType.POST_ACTIVE_EPISODE,
            TriggerType.CONTEXT_TRANSITION,
            TriggerType.DISCRETIONARY_FALLBACK,
        )
    }


def calibration_report(
    answered: int,
    total: int,
    config: Optional[ProtocolConfig] = None,
) -> dict[str, Any]:
    config = config or default_config()
    low, high = (float(value) for value in config.get("missingness.calibration_target_response_rate", [0.85, 0.9]))
    rate = (answered / total) if total else 0.0
    return {
        "answered": answered,
        "total": total,
        "response_rate": round(rate, 4),
        "target": [low, high],
        "within_target": bool(low - 1e-9 <= rate <= high + 1e-9),
        "base_rates": expected_response_rate(config),
        "note": (
            "calibration target is a simulation property, not a claim about true human compliance; "
            "the literature reports 67-92% depending on burden and trigger type, and event-triggered "
            "compliance can be much lower (Gemini.md line 172 reports a WEALTH median of 34%)"
        ),
    }
