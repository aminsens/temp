"""Response-latency model and expiry handling.

Both timestamps are always recorded — ``prompt_time`` and ``response_time`` —
because dual-timestamp recording is the strongest alignment practice in the
evidence base and is almost never implemented
(``EMA_Definitive_Synthesis.md`` §7.3, §10.2 UNDERRATED #3).

Latency is drawn from a right-skewed lognormal distribution.  A response that
arrives after ``latency.expiry_minutes`` (default **10 minutes**) is recorded as
``expired``: the response content is kept, the record is flagged, and it is
excluded from accelerometer alignment by default (``Gemini.md`` line 162
recommends a hard maximum latency bound of 5-10 minutes; synthesis §9.1 says
responses with >10-minute lag should be discarded or downweighted).

Contextual interpretation is always aligned to **prompt time**
(``latency.context_reference_time: prompt_time``).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Optional

from .config import ProtocolConfig, default_config
from .models import EMAContextPacket, EMAPrompt
from .vocab import ResponseStatus

LATENCY_MODEL_VERSION = "1.0.0"


@dataclass
class LatencyDraw:
    latency_min: float
    status: ResponseStatus
    expired: bool
    base_latency_min: float
    multipliers: dict[str, float]
    expiry_minutes: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "latency_min": round(self.latency_min, 3),
            "status": self.status.value,
            "expired": self.expired,
            "base_latency_min": round(self.base_latency_min, 3),
            "multipliers": {key: round(value, 3) for key, value in self.multipliers.items()},
            "expiry_minutes": self.expiry_minutes,
        }


def draw_latency(
    prompt: EMAPrompt,
    packet: EMAContextPacket,
    rng: random.Random,
    config: Optional[ProtocolConfig] = None,
) -> LatencyDraw:
    """Draw a right-skewed response latency for one answered prompt."""
    config = config or default_config()
    section = config.section("latency")
    distribution = str(section.get("distribution", "lognormal"))
    mu = float(section.get("mu", -0.35))
    sigma = float(section.get("sigma", 0.85))
    maximum = float(section.get("max_minutes", 30.0))
    expiry = float(section.get("expiry_minutes", 10.0))
    modifiers = section.section("modifiers")

    if distribution == "lognormal":
        base = math.exp(rng.gauss(mu, sigma))
    elif distribution == "exponential":  # pragma: no cover - alternative profile
        base = rng.expovariate(1.0 / max(0.1, math.exp(mu)))
    elif distribution == "uniform":  # pragma: no cover - alternative profile
        base = rng.uniform(0.2, expiry)
    else:
        raise ValueError(f"unsupported latency distribution: {distribution!r}")
    base = max(0.1, min(maximum, base))

    latency = base
    multipliers: dict[str, float] = {}
    exertion = packet.recent_exertion_60min
    if exertion is not None and float(exertion) >= 0.4:
        multiplier = float(modifiers.get("after_exertion_multiplier", 1.0))
        latency *= multiplier
        multipliers["after_exertion"] = multiplier
    late_threshold = float(config.get("missingness.modifiers.late_window.after_minute_of_day", 1260))
    if packet.prompt_time_min >= late_threshold:
        multiplier = float(modifiers.get("late_window_multiplier", 1.0))
        latency *= multiplier
        multipliers["late_window"] = multiplier
    latency = max(0.1, min(maximum, latency))

    expired = latency > expiry
    keep_expired = bool(section.get("keep_expired_response", True))
    policy = str(section.get("expired_policy", "record_and_flag"))
    if not expired:
        status = ResponseStatus.ANSWERED
    elif keep_expired and policy == "record_and_flag":
        status = ResponseStatus.EXPIRED
    else:
        status = ResponseStatus.MISSED

    return LatencyDraw(
        latency_min=round(latency, 3),
        status=status,
        expired=expired,
        base_latency_min=round(base, 3),
        multipliers=multipliers,
        expiry_minutes=expiry,
    )


def expiry_minutes(config: Optional[ProtocolConfig] = None) -> float:
    return float((config or default_config()).get("latency.expiry_minutes", 10.0))


def context_reference_time(config: Optional[ProtocolConfig] = None) -> str:
    value = str((config or default_config()).get("latency.context_reference_time", "prompt_time"))
    if value != "prompt_time":  # pragma: no cover - guarded by config validation
        raise ValueError("Paper 3 aligns context to prompt_time only")
    return value


def latency_summary(values: list[float]) -> dict[str, Any]:
    """Descriptive latency statistics (the reporting the literature omits)."""
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    count = len(ordered)

    def quantile(q: float) -> float:
        position = min(count - 1, max(0, int(round(q * (count - 1)))))
        return round(ordered[position], 2)

    return {
        "n": count,
        "mean_min": round(sum(ordered) / count, 2),
        "median_min": quantile(0.5),
        "p90_min": quantile(0.9),
        "min_min": round(ordered[0], 2),
        "max_min": round(ordered[-1], 2),
        "right_skewed": bool(sum(ordered) / count > quantile(0.5)),
    }
