"""LLM interface: DeepSeek note rendering under a closed-world contract.

Role of the LLM in Paper 3 (strictly bounded):

* the LLM **renders** the optional one-sentence context note from a factual
  context packet and the already-decided synthetic subjective values;
* the LLM **never** schedules prompts, **never** alters inherited contextual
  facts, **never** invents events/places/people/journeys, **never** produces
  medical diagnoses and **never** infers psychological traits from demographics;
* by default the LLM does **not** select ``valence``/``energy``/``stress``.
  ``llm.allowed_to_select_subjective_values`` is validated to be ``false`` by
  :class:`paper3_ema.config.ProtocolConfig`; changing that requires the
  justification and comparative evidence described in ``docs/ARCHITECTURE.md``
  §7 and is recorded in ``docs/SCIENTIFIC_ASSUMPTIONS.md`` (item S-14).

Every candidate output is validated by :mod:`paper3_ema.notes`.  On rejection
the renderer retries with the failure reasons attached (up to
``note.max_retries``); if no safe output can be produced it falls back to the
offline template renderer, and finally to ``context_note = null``.
"""

from __future__ import annotations

import json
import os
import random
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence

from .config import ProtocolConfig, default_config
from .models import EMAContextPacket
from .notes import NoteIssue, NoteValidation, rejection_feedback, validate_note
from .vocab import SCALE_LABELS

LLM_INTERFACE_VERSION = "1.0.0"
TEMPLATE_VERSION = "note_v1"

_JSON_TAGS = re.compile(r"<json>\s*(?P<body>.*?)\s*</json>", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"```(?:json)?\s*(?P<body>.*?)```", re.DOTALL)


class LLMUnavailable(RuntimeError):
    """Raised when no credential or no reachable endpoint is available."""


# --------------------------------------------------------------------------
# credential / reachability handling
# --------------------------------------------------------------------------

def resolve_api_key(config: Optional[ProtocolConfig] = None) -> Optional[str]:
    """Resolve the DeepSeek credential from the environment or a key file."""
    config = config or default_config()
    env_name = str(config.get("llm.api_key_env", "DEEPSEEK_API_KEY"))
    value = os.environ.get(env_name) or os.environ.get("DEEPSEEK_API_KEY")
    if value:
        return value.strip()
    for candidate in config.get("llm.api_key_files") or []:
        path = Path(str(candidate)).expanduser()
        try:
            if path.is_file():
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    return text
        except OSError:  # pragma: no cover - defensive
            continue
    return None


def probe_endpoint(config: Optional[ProtocolConfig] = None, timeout: float = 8.0) -> tuple[bool, str]:
    """Best-effort reachability probe (used to SKIP real integration tests)."""
    config = config or default_config()
    url = str(config.get("llm.base_url", "https://api.deepseek.com")).rstrip("/") + str(
        config.get("llm.chat_path", "/chat/completions")
    )
    request = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # pragma: no cover - network
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:  # an HTTP error means we reached the service
        return True, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - network/TLS/DNS failures
        return False, f"{type(exc).__name__}: {exc}"


def llm_available(config: Optional[ProtocolConfig] = None) -> tuple[bool, str]:
    key = resolve_api_key(config)
    if not key:
        return False, "no DeepSeek credential found (set DEEPSEEK_API_KEY)"
    reachable, detail = probe_endpoint(config)
    if not reachable:
        return False, f"credential present but endpoint unreachable ({detail})"
    return True, f"credential present and endpoint reachable ({detail})"


# --------------------------------------------------------------------------
# robust output extraction (salvaged strategy from the historical pipeline)
# --------------------------------------------------------------------------

def extract_json(text: str) -> Optional[Any]:
    """Extract JSON from a model response.

    Handles ``<json>...</json>`` tags, markdown fences and bare JSON.  The
    historical pipeline (``EMA-Diary-Generation/modules/jar_of_life_llm.py:69``)
    showed that reasoning text around JSON is the dominant failure mode; the
    tag/fence strategy is reused here.
    """
    if not text:
        return None
    for pattern in (_JSON_TAGS, _FENCE):
        match = pattern.search(text)
        if match:
            candidate = match.group("body").strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(stripped[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def extract_note_text(payload: Any) -> Optional[str]:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload.strip() or None
    if isinstance(payload, Mapping):
        for key in ("context_note", "note", "sentence", "text", "response"):
            if key in payload:
                value = payload[key]
                if value is None:
                    return None
                if isinstance(value, str):
                    return value.strip() or None
        return None
    return None


# --------------------------------------------------------------------------
# clients
# --------------------------------------------------------------------------

class LLMClient(Protocol):
    """Minimal client protocol: one call, one string."""

    provider: str
    model: str

    def complete(self, system: str, user: str, **kwargs: Any) -> str:  # pragma: no cover - protocol
        ...


@dataclass
class DeepSeekClient:
    """DeepSeek chat-completions client over stdlib ``urllib`` (no dependencies)."""

    api_key: str
    base_url: str = "https://api.deepseek.com"
    chat_path: str = "/chat/completions"
    model: str = "deepseek-chat"
    timeout: float = 30.0
    provider: str = "deepseek"

    @classmethod
    def from_config(cls, config: Optional[ProtocolConfig] = None) -> "DeepSeekClient":
        config = config or default_config()
        key = resolve_api_key(config)
        if not key:
            raise LLMUnavailable("no DeepSeek credential found (set DEEPSEEK_API_KEY)")
        return cls(
            api_key=key,
            base_url=str(config.get("llm.base_url", "https://api.deepseek.com")),
            chat_path=str(config.get("llm.chat_path", "/chat/completions")),
            model=str(config.get("llm.model", "deepseek-chat")),
            timeout=float(config.get("llm.timeout_seconds", 30)),
            provider=str(config.get("llm.provider", "deepseek")),
        )

    def complete(self, system: str, user: str, **decoding: Any) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        for key, value in decoding.items():
            if value is not None:
                payload[key] = value
        request = urllib.request.Request(
            self.base_url.rstrip("/") + self.chat_path,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        try:
            return str(body["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            raise LLMUnavailable(f"unexpected DeepSeek response shape: {body!r}") from exc


@dataclass
class ScriptedLLMClient:
    """Test double: returns a queue of scripted responses (or a callable).

    Used by the offline test-suite to exercise the closed-world validator,
    retry loop and null fallback deterministically, including adversarial
    outputs that invent weather, delays, people, places and diagnoses.
    """

    responses: Sequence[Any] = ()
    provider: str = "scripted"
    model: str = "scripted-test-double"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def complete(self, system: str, user: str, **decoding: Any) -> str:
        self.calls.append({"system": system, "user": user, "decoding": dict(decoding)})
        index = len(self.calls) - 1
        if callable(self.responses):  # type: ignore[union-attr]
            return str(self.responses(system, user, index))  # type: ignore[misc]
        if index < len(self.responses):
            item = self.responses[index]
        else:
            item = self.responses[-1] if self.responses else ""
        if isinstance(item, Exception):
            raise item
        return str(item)


# --------------------------------------------------------------------------
# prompt template (versioned)
# --------------------------------------------------------------------------

SYSTEM_TEMPLATE = """You write ONE optional context sentence for a synthetic EMA (ecological momentary assessment) record in a research simulation.

CLOSED-WORLD CONTRACT - these rules are absolute:
1. You may refer ONLY to facts present in the CONTEXT JSON below. You may not add anything else.
2. You must NOT invent: a person, a place, a proper name, an activity, an event, a journey, a delay, a disruption, weather, a cause, a medical or mental-health condition, a diagnosis, a personality trait, or any demographic characteristic.
3. You must NOT explain the feelings with a cause that is not in the CONTEXT JSON.
4. You must NOT restate the numeric ratings as digits; you may describe them in plain words.
5. Write at most ONE sentence, at most {max_words} words, in plain everyday English, first person.
6. The situation, the person and the feelings are SYNTHETIC simulation data. Do not present them as real clinical information.
7. If you cannot write a sentence that satisfies every rule, reply with {{"context_note": null}}.

Reply with ONLY:
<json>{{"context_note": "<one sentence or null>"}}</json>"""

USER_TEMPLATE = """CONTEXT (closed world - you may only refer to what appears here):
{context_json}

SYNTHETIC SUBJECTIVE STATE ALREADY DECIDED (do not change it, do not output numbers):
{state_json}

Write the single optional context sentence, or null."""


def build_messages(
    packet: EMAContextPacket,
    state: Mapping[str, int],
    config: Optional[ProtocolConfig] = None,
    feedback: str = "",
) -> tuple[str, str]:
    config = config or default_config()
    max_words = int(config.get("note.max_words", 24))
    system = SYSTEM_TEMPLATE.format(max_words=max_words)
    facts = packet.fact_view()
    state_view = {
        item: {"value": int(state[item]), "label": SCALE_LABELS[item][int(state[item])]} for item in ("valence", "energy", "stress")
    }
    context_json = json.dumps(
        {
            "prompt_time": packet.prompt_time.strftime("%H:%M"),
            "time_of_day": facts["time_of_day"],
            "current_activity": facts["activity"],
            "current_domain": facts["domain"],
            "current_place_type": facts["place_type"],
            "current_social_setting": facts["social_context"],
            "indoor_or_outdoor": facts["indoor_outdoor"],
            "purpose_category": facts["purpose_category"],
            "preceding_activity": facts["preceding_activity"],
            "preceding_journey_mode": facts["preceding_journey_mode"],
            "minutes_since_journey_end": facts["minutes_since_journey_end"],
            "journey_delay_documented": bool(facts["preceding_journey_delayed"]),
            "journey_crowding_documented": bool(facts["preceding_journey_crowded"]),
            "minutes_since_active_episode_end": facts["minutes_since_active_episode_end"],
            "minutes_to_next_fixed_commitment": facts["minutes_to_next_commitment"],
            "next_commitment_kind": facts["next_commitment_kind"],
            "weather_documented": bool(facts["weather_available"]),
            "allowed_entities": facts["allowed_entities"],
            "allowed_causes": facts["allowed_causes"],
        },
        indent=2,
        ensure_ascii=False,
    )
    user = USER_TEMPLATE.format(context_json=context_json, state_json=json.dumps(state_view, indent=2))
    if feedback:
        user = f"{user}\n\n{feedback}"
    return system, user


# --------------------------------------------------------------------------
# offline template renderer (deterministic, closed-world by construction)
# --------------------------------------------------------------------------

OFFLINE_TEMPLATES: tuple[str, ...] = (
    "{feeling}{clause}.",
    "{feeling} right now{clause}.",
    "{feeling}, {second_clause}.",
)

# Feeling phrases are keyed by the *dominant* synthetic item so that the note is
# always coherent with the structured state it accompanies.
FEELING_BY_VALENCE: dict[str, tuple[str, ...]] = {
    "high": ("Feeling positive", "In a good mood", "Feeling quite upbeat"),
    "mid": ("Feeling fairly neutral", "Mood is steady", "Feeling okay"),
    "low": ("Feeling a bit low", "Not in a great mood", "Feeling drained"),
}
FEELING_BY_STRESS: dict[str, tuple[str, ...]] = {
    "high": ("Feeling pressured", "Feeling wound up", "Feeling stressed"),
    "low": ("Feeling calm", "Feeling relaxed", "Feeling unrushed"),
}
FEELING_BY_ENERGY: dict[str, tuple[str, ...]] = {
    "high": ("Feeling energetic", "Feeling alert", "Feeling switched on"),
    "low": ("Feeling tired", "Running low on energy", "Feeling drained"),
}
SECOND_CLAUSE_BY_ENERGY: dict[str, tuple[str, ...]] = {
    "high": ("energy is high", "still feeling fresh"),
    "mid": ("energy is steady", "feeling okay overall"),
    "low": ("energy is low", "feeling drained"),
}


def offline_note(
    packet: EMAContextPacket,
    state: Mapping[str, int],
    rng: random.Random,
    config: Optional[ProtocolConfig] = None,
) -> Optional[str]:
    """Deterministic, closed-world-by-construction note (or ``None``).

    The offline renderer exists so that the module is fully usable without an
    LLM and so that integration tests have a bounded reference.  It only ever
    combines (a) a feeling phrase that matches the already-decided synthetic
    state and (b) a grounding clause built from packet facts, so its output
    satisfies the closed-world contract by construction.
    """
    config = config or default_config()
    null_probability = float(config.get("note.null_probability_offline", 0.35))
    if rng.random() < null_probability:
        return None
    from .context import ACTIVITY_PHRASES, DOMAIN_PHRASES, PLACE_PHRASES

    valence, energy, stress = int(state["valence"]), int(state["energy"]), int(state["stress"])
    if stress >= 4:
        feeling = rng.choice(FEELING_BY_STRESS["high"])
    elif valence >= 4:
        feeling = rng.choice(FEELING_BY_VALENCE["high"])
    elif valence <= 2:
        feeling = rng.choice(FEELING_BY_VALENCE["low"])
    elif energy <= 2:
        feeling = rng.choice(FEELING_BY_ENERGY["low"])
    elif energy >= 4:
        feeling = rng.choice(FEELING_BY_ENERGY["high"])
    elif stress <= 2:
        feeling = rng.choice(FEELING_BY_STRESS["low"])
    else:
        feeling = rng.choice(FEELING_BY_VALENCE["mid"])

    grounding: list[str] = []
    if packet.minutes_since_journey_end is not None and packet.preceding_journey_mode:
        mode = str(packet.preceding_journey_mode).lower()
        phrase = {"walk": "the walk", "walking": "the walk", "foot": "the walk",
                  "bike": "the bike ride", "bicycle": "the bike ride", "cycling": "the bike ride",
                  "car": "the drive", "driving": "the drive", "bus": "the bus trip",
                  "train": "the train trip", "tram": "the tram trip"}.get(mode)
        if phrase:
            grounding.append(f"after {phrase}")
    elif packet.minutes_since_active_episode_end is not None:
        grounding.append("after the exercise session")
    elif packet.activity is not None:
        phrase = ACTIVITY_PHRASES.get(packet.activity)
        if phrase and phrase not in {"sleep"}:
            grounding.append(f"while {phrase}" if phrase.startswith("the") is False else f"after {phrase}")
    elif packet.domain is not None:
        grounding.append(f"during {DOMAIN_PHRASES.get(packet.domain, 'this part of the day')}")
    if packet.place_type is not None and rng.random() < 0.5:
        place_phrase = PLACE_PHRASES.get(packet.place_type)
        if place_phrase and place_phrase not in {"here"}:
            grounding.append(place_phrase)
    clause = (" " + ", ".join(grounding[:2])) if grounding else ""

    energy_level = "high" if energy >= 4 else ("low" if energy <= 2 else "mid")
    second_clause = rng.choice(SECOND_CLAUSE_BY_ENERGY[energy_level])
    template = rng.choice(OFFLINE_TEMPLATES)
    note = template.format(feeling=feeling, clause=clause, second_clause=second_clause)
    note = re.sub(r"\s+", " ", note).strip()
    note = re.sub(r"\s+([,.])", r"\1", note)
    note = re.sub(r",\s*\.", ".", note)
    if not note.endswith("."):
        note += "."
    return note


# --------------------------------------------------------------------------
# renderer
# --------------------------------------------------------------------------

@dataclass
class NoteRenderResult:
    note: Optional[str]
    source: Optional[str]                     # "llm" | "offline_template" | None
    attempts: int = 0
    retries: int = 0
    raw_outputs: list[str] = field(default_factory=list)
    validations: list[NoteValidation] = field(default_factory=list)
    fallback_reason: Optional[str] = None
    decoding: dict[str, Any] = field(default_factory=dict)
    provider: Optional[str] = None
    model: Optional[str] = None
    template_version: str = TEMPLATE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "note": self.note,
            "source": self.source,
            "attempts": self.attempts,
            "retries": self.retries,
            "raw_outputs": list(self.raw_outputs),
            "validations": [validation.to_dict() for validation in self.validations],
            "rejected_codes": sorted({code for validation in self.validations for code in validation.codes}),
            "fallback_reason": self.fallback_reason,
            "decoding": dict(self.decoding),
            "provider": self.provider,
            "model": self.model,
            "template_version": self.template_version,
        }


def render_note(
    packet: EMAContextPacket,
    state: Mapping[str, int],
    config: Optional[ProtocolConfig] = None,
    client: Optional[LLMClient] = None,
    rng: Optional[random.Random] = None,
    allow_llm: bool = True,
) -> NoteRenderResult:
    """Render (and validate) the optional context note.

    Order of preference: LLM (validated, retried) -> offline template -> null.
    """
    config = config or default_config()
    rng = rng or random.Random(0)
    enabled = bool(config.get("note.enabled", True))
    result = NoteRenderResult(note=None, source=None)
    if not enabled:
        result.fallback_reason = "note_disabled_by_configuration"
        return result

    max_retries = int(config.get("note.max_retries", 2))
    decoding = {
        "temperature": float(config.get("llm.temperature", 0.4)),
        "top_p": float(config.get("llm.top_p", 0.9)),
        "max_tokens": int(config.get("llm.max_tokens", 120)),
        "seed": config.get("llm.seed"),
    }
    result.decoding = {key: value for key, value in decoding.items() if value is not None}

    if allow_llm and client is not None:
        result.provider = getattr(client, "provider", None)
        result.model = getattr(client, "model", None)
        result.template_version = str(config.get("llm.template_version", TEMPLATE_VERSION))
        feedback = ""
        last_validation: Optional[NoteValidation] = None
        for attempt in range(max_retries + 1):
            result.attempts += 1
            if attempt:
                result.retries += 1
            system, user = build_messages(packet, state, config, feedback)
            try:
                raw = client.complete(system, user, **decoding)
            except Exception as exc:  # noqa: BLE001 - any transport/LLM failure
                result.fallback_reason = f"llm_call_failed:{type(exc).__name__}:{exc}"
                raw = ""
            result.raw_outputs.append(raw)
            payload = extract_json(raw)
            candidate = extract_note_text(payload)
            if payload is None:
                last_validation = NoteValidation(
                    valid=False,
                    issues=[NoteIssue("unparseable_output", "model output was not parseable JSON", None)],
                    normalized=(raw or "").strip()[:200],
                )
                feedback = rejection_feedback(last_validation)
                result.validations.append(last_validation)
                continue
            if candidate is None:
                # the model itself chose null: that is always acceptable
                validation = validate_note(None, packet, config)
                result.validations.append(validation)
                result.note = None
                result.source = "llm"
                result.fallback_reason = "llm_returned_null"
                return result
            validation = validate_note(candidate, packet, config)
            result.validations.append(validation)
            if validation.valid:
                result.note = validation.normalized
                result.source = "llm"
                return result
            last_validation = validation
            feedback = rejection_feedback(validation)
        if last_validation is not None:
            if "llm_call_failed" not in (result.fallback_reason or ""):
                result.fallback_reason = "closed_world_violation:" + ",".join(last_validation.codes)

    if bool(config.get("note.fallback_to_offline_template", True)) and config.get("note.allow_offline_renderer", True):
        template_note = offline_note(packet, state, rng, config)
        if template_note is not None:
            validation = validate_note(template_note, packet, config)
            result.validations.append(validation)
            if validation.valid:
                result.note = validation.normalized
                result.source = "offline_template"
                if result.fallback_reason is None:
                    result.fallback_reason = "llm_not_used"
                return result
            result.fallback_reason = (result.fallback_reason or "") + "|offline_template_rejected:" + ",".join(validation.codes)
        else:
            result.note = None
            result.source = None
            result.fallback_reason = (result.fallback_reason or "llm_not_used") + "|offline_template_returned_null"
            return result

    if bool(config.get("note.fallback_to_null", True)):
        result.note = None
        result.source = None
    return result
