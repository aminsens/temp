"""Provenance: field-level origin classification and run-level traceability.

Every emitted field is traceable to exactly one origin class
(:class:`paper3_ema.vocab.ProvenanceClass`):

``inherited_context``    copied verbatim from the supplied day (immutable)
``derived_context``      computed from the supplied day by a documented rule
``synthetic_protocol``   produced by the Paper 3 protocol (schedule, response,
                         latency, expiry)
``synthetic_subjective`` produced by the seeded subjective-state generator
``llm_rendered``         produced by the optional LLM note renderer and then
                         closed-world validated (or the offline template)

Run-level provenance records protocol/schema/scheduler/state-generator/auditor/
note-validator versions, LLM provider/model/template/decoding settings, seed,
request hash, context fingerprint, config hash, participant/date, linkage ids,
prompt type, prompt/response times, retry counts and validation state.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date as _date, datetime, timezone
from typing import Any, Iterable, Mapping, Optional, Sequence

from .audit import AUDITOR_VERSION
from .config import ProtocolConfig, default_config
from .context import CONTEXT_BUILDER_VERSION
from .latency import LATENCY_MODEL_VERSION
from .llm import LLM_INTERFACE_VERSION, NoteRenderResult
from .missingness import MISSINGNESS_MODEL_VERSION
from .notes import NOTE_VALIDATOR_VERSION
from .scheduler import SCHEDULER_VERSION
from .state import STATE_GENERATOR_VERSION
from .vocab import SCHEMA_VERSION, ProvenanceClass

PROVENANCE_VERSION = "1.0.0"
PACKAGE_VERSION = "1.0.0"

INHERITED = ProvenanceClass.INHERITED_CONTEXT.value
DERIVED = ProvenanceClass.DERIVED_CONTEXT.value
PROTOCOL = ProvenanceClass.SYNTHETIC_PROTOCOL.value
SUBJECTIVE = ProvenanceClass.SYNTHETIC_SUBJECTIVE.value
LLM = ProvenanceClass.LLM_RENDERED.value

FIELD_PROVENANCE: dict[str, str] = {
    # ---- identity --------------------------------------------------------
    "participant_id": INHERITED,
    "date": INHERITED,
    "day_date": INHERITED,
    "prompt_id": PROTOCOL,
    # ---- timing ----------------------------------------------------------
    "prompt_time": PROTOCOL,
    "prompt_time_min": PROTOCOL,
    "response_time": PROTOCOL,
    "latency_min": PROTOCOL,
    "expiry_minutes": PROTOCOL,
    "expires_at": PROTOCOL,
    "context_reference_time": PROTOCOL,
    "status": PROTOCOL,
    "answered": PROTOCOL,
    "expired": PROTOCOL,
    "usable_for_alignment": PROTOCOL,
    "nonresponse_reason": PROTOCOL,
    "response_probability": PROTOCOL,
    # ---- trigger / schedule ---------------------------------------------
    "trigger": PROTOCOL,
    "is_event_enriched": PROTOCOL,
    "schedule_index": PROTOCOL,
    "window_index": DERIVED,
    "window_label": DERIVED,
    "selection_reason": PROTOCOL,
    "stability_relaxed": PROTOCOL,
    "event_id": DERIVED,
    "event_kind": DERIVED,
    "minutes_after_event": DERIVED,
    "recall_frame": PROTOCOL,
    # ---- linkage (inherited identifiers) --------------------------------
    "episode_id": INHERITED,
    "interval_id": INHERITED,
    "journey_id": INHERITED,
    # ---- current context (inherited facts) ------------------------------
    "activity": INHERITED,
    "activity_label": INHERITED,
    "domain": INHERITED,
    "place_type": INHERITED,
    "social_context": INHERITED,
    "indoor_outdoor": INHERITED,
    "device_wear": INHERITED,
    "preceding_activity": INHERITED,
    "preceding_domain": INHERITED,
    "preceding_place_type": INHERITED,
    "preceding_journey_mode": INHERITED,
    "preceding_journey_duration_min": INHERITED,
    "preceding_journey_delayed": INHERITED,
    "preceding_journey_crowded": INHERITED,
    "current_journey_mode": INHERITED,
    # ---- derived context -------------------------------------------------
    "purpose_category": DERIVED,
    "time_of_day": DERIVED,
    "minutes_since_wake": DERIVED,
    "minutes_in_current_episode": DERIVED,
    "minutes_since_activity_change": DERIVED,
    "minutes_since_journey_end": DERIVED,
    "minutes_since_active_episode_end": DERIVED,
    "recent_exertion_60min": DERIVED,
    "recent_activity_summary": DERIVED,
    "minutes_to_next_commitment": DERIVED,
    "next_commitment_kind": INHERITED,
    "next_commitment_requires_travel": INHERITED,
    "episode_is_unstable": DERIVED,
    "minutes_since_previous_prompt": DERIVED,
    "previous_state": SUBJECTIVE,
    "allowed_entities": DERIVED,
    "allowed_causes": DERIVED,
    "weather_available": INHERITED,
    # ---- synthetic subjective -------------------------------------------
    "valence": SUBJECTIVE,
    "energy": SUBJECTIVE,
    "stress": SUBJECTIVE,
    "latent": SUBJECTIVE,
    "contributions": SUBJECTIVE,
    "noise": SUBJECTIVE,
    "rules_applied": SUBJECTIVE,
    "state_generator_version": SUBJECTIVE,
    # ---- rendered note ---------------------------------------------------
    "context_note": LLM,
    "note_source": LLM,
    "note_validation": LLM,
}


def field_origin(field_name: str) -> Optional[str]:
    return FIELD_PROVENANCE.get(field_name)


def unclassified_fields(field_names: Iterable[str]) -> list[str]:
    """Fields with no declared origin class (validator treats these as errors)."""
    return sorted({name for name in field_names if name not in FIELD_PROVENANCE})


def classify_record(record: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Per-record provenance payload (stored in ``EMAProvenance.record_provenance``)."""
    return {
        "fields_by_origin": {
            origin: sorted(name for name, value in FIELD_PROVENANCE.items() if value == origin)
            for origin in (INHERITED, DERIVED, PROTOCOL, SUBJECTIVE, LLM)
        },
        "record_keys": sorted(record.keys()),
        "unclassified": unclassified_fields(record.keys()),
    }


def build_record_provenance(
    prompt_id: str,
    *,
    trigger: str,
    prompt_time: str,
    response_time: Optional[str],
    episode_id: Optional[str],
    interval_id: Optional[str],
    journey_id: Optional[str],
    validation_state: str,
    note_result: Optional[NoteRenderResult] = None,
    response_model_version: str = MISSINGNESS_MODEL_VERSION,
    latency_model_version: str = LATENCY_MODEL_VERSION,
) -> dict[str, Any]:
    """Traceability payload for one EMA record."""
    payload: dict[str, Any] = {
        "prompt_id": prompt_id,
        "prompt_type": trigger,
        "prompt_time": prompt_time,
        "response_time": response_time,
        "episode_id": episode_id,
        "interval_id": interval_id,
        "journey_id": journey_id,
        "validation_state": validation_state,
        "retry_count": 0,
        "response_model_version": response_model_version,
        "latency_model_version": latency_model_version,
        "field_origin_classes": {
            origin: sorted(name for name, value in FIELD_PROVENANCE.items() if value == origin)
            for origin in (INHERITED, DERIVED, PROTOCOL, SUBJECTIVE, LLM)
        },
    }
    if note_result is not None:
        payload.update(
            {
                "retry_count": note_result.retries,
                "note_attempts": note_result.attempts,
                "note_source": note_result.source,
                "note_fallback_reason": note_result.fallback_reason,
                "note_rejected_codes": sorted(
                    {code for validation in note_result.validations for code in validation.codes}
                ),
                "note_validator_version": NOTE_VALIDATOR_VERSION,
                "note_template_version": note_result.template_version,
                "llm_provider": note_result.provider,
                "llm_model": note_result.model,
                "llm_decoding": note_result.decoding,
            }
        )
    return payload


def build_provenance(
    *,
    participant_id: str,
    day_date: Any,
    seed: int,
    config: ProtocolConfig,
    request_hash: Optional[str],
    context_fingerprint: Optional[str],
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_decoding: Optional[Mapping[str, Any]] = None,
    llm_calls: int = 0,
    llm_retries: int = 0,
    notes: Optional[Sequence[str]] = None,
    generated_at: Optional[datetime] = None,
) -> Any:
    """Assemble the run-level :class:`paper3_ema.models.EMAProvenance`."""
    from .models import EMAProvenance

    if generated_at is not None:
        timestamp = generated_at.replace(microsecond=0)
    else:
        # Deterministic run anchor: the simulated day at midnight UTC.  The
        # bundle is a pure function of (day, seed, config); wall-clock time is
        # deliberately NOT part of the record so identical inputs always
        # produce byte-identical artifacts (see docs/ARCHITECTURE.md §9).
        day = _date.fromisoformat(str(day_date)[:10]) if not hasattr(day_date, "year") else day_date
        timestamp = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    notes_list = list(notes or [])
    notes_list.append(
        "generated_at is the deterministic run anchor (midnight of the simulated day), not wall-clock time"
    )
    return EMAProvenance(
        protocol_version=str(config.protocol_version),
        schema_version=str(config.get("meta.schema_version", SCHEMA_VERSION)),
        package_version=PACKAGE_VERSION,
        scheduler_version=SCHEDULER_VERSION,
        state_generator_version=STATE_GENERATOR_VERSION,
        auditor_version=AUDITOR_VERSION,
        note_validator_version=NOTE_VALIDATOR_VERSION,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_template_version=str(config.get("llm.template_version", "note_v1")),
        llm_decoding=dict(llm_decoding or {}),
        llm_calls=int(llm_calls),
        llm_retries=int(llm_retries),
        seed=int(seed),
        request_hash=request_hash,
        context_fingerprint=context_fingerprint,
        config_hash=config.hash(),
        config_name=str(config.get("meta.protocol_name", "paper3_ema_v1")),
        participant_id=str(participant_id),
        day_date=day_date.isoformat() if hasattr(day_date, "isoformat") else str(day_date),
        generated_at=timestamp.isoformat(),
        field_provenance=dict(FIELD_PROVENANCE),
        notes=notes_list,
    )


def hash_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()[:16]


def versions(config: Optional[ProtocolConfig] = None) -> dict[str, str]:
    config = config or default_config()
    return {
        "package": PACKAGE_VERSION,
        "protocol": str(config.protocol_version),
        "schema": str(config.get("meta.schema_version", SCHEMA_VERSION)),
        "scheduler": SCHEDULER_VERSION,
        "state_generator": STATE_GENERATOR_VERSION,
        "context_builder": CONTEXT_BUILDER_VERSION,
        "auditor": AUDITOR_VERSION,
        "missingness_model": MISSINGNESS_MODEL_VERSION,
        "latency_model": LATENCY_MODEL_VERSION,
        "note_validator": NOTE_VALIDATOR_VERSION,
        "llm_interface": LLM_INTERFACE_VERSION,
        "provenance": PROVENANCE_VERSION,
        "llm_template": str(config.get("llm.template_version", "note_v1")),
        "note_template": str(config.get("note.template_version", "1.0.0")),
    }
