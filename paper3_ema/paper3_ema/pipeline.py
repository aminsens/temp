"""Public orchestration: ``generate_ema`` and friends.

Pipeline for one participant-day::

    EMARequest (contextual day + seed + config)
        -> scheduler            (5 opportunities: >=3 semi-random, <=2 event)
        -> context builder      (bounded EMAContextPacket, prompt-time anchored)
        -> state generator      (synthetic valence/energy/stress + full trace)
        -> response model       (Bernoulli non-response, independent of content)
        -> latency model        (right-skewed latency, 10-min expiry)
        -> note renderer        (closed-world, validated, retry, null fallback)
        -> provenance + validation
        -> EMABundle

The LLM is optional and is used **only** for note rendering.  Inherited
contextual facts are never regenerated, never re-reported with noise and never
mutated: the day fingerprint is recomputed at the end of generation and any
change aborts the run.
"""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any, Mapping, Optional, Sequence

from .audit import AUDITOR_VERSION, audit_schedule
from .config import ProtocolConfig, default_config
from .context import CONTEXT_BUILDER_VERSION, build_packet
from .day import ContextualDay, contextual_day_from_mapping, describe_day, validate_day_input
from .eligibility import DayEligibility
from .latency import LATENCY_MODEL_VERSION, draw_latency
from .llm import LLMClient, NoteRenderResult, render_note
from .missingness import MISSINGNESS_MODEL_VERSION, draw_response
from .models import (
    EMABundle,
    EMAContextPacket,
    EMAPrompt,
    EMAResponse,
    EMARequest,
    EMARecord,
    SubjectiveState,
)
from .provenance import build_provenance, build_record_provenance, versions
from .scheduler import SCHEDULER_VERSION, schedule_for_day, stable_seed
from .state import STATE_GENERATOR_VERSION, generate_state, traces_to_dict
from .timeutil import day_datetime
from .vocab import AuditStatus, DeviceWear, ResponseStatus, TriggerType, describe_scales

PIPELINE_VERSION = "1.0.0"


class InheritedContextMutationError(RuntimeError):
    """Raised when the supplied day changed during generation (must never happen)."""


# --------------------------------------------------------------------------
# request helpers
# --------------------------------------------------------------------------

def as_request(
    request: EMARequest | ContextualDay | Mapping[str, Any] | None = None,
    *,
    day: Optional[ContextualDay | Mapping[str, Any]] = None,
    participant_id: Optional[str] = None,
    date: Optional[Any] = None,
    seed: int = 0,
    config: Optional[ProtocolConfig] = None,
    **kwargs: Any,
) -> EMARequest:
    """Coerce whatever the caller supplied into an :class:`EMARequest`."""
    config = config or default_config()
    if isinstance(request, EMARequest):
        return request
    source = request if request is not None else day
    if source is None:
        raise ValueError("generate_ema requires an EMARequest, a ContextualDay or a day mapping")
    contextual = source if isinstance(source, ContextualDay) else contextual_day_from_mapping(source, config)
    return EMARequest(
        day=contextual,
        participant_id=participant_id or contextual.participant_id,
        day_date=date or contextual.day,
        seed=seed,
        protocol_name=config.protocol_name,
        protocol_config_hash=config.hash(),
        **kwargs,
    )


# --------------------------------------------------------------------------
# context packets
# --------------------------------------------------------------------------

def build_context(
    request: EMARequest | ContextualDay | Mapping[str, Any],
    prompts: Sequence[EMAPrompt],
    config: Optional[ProtocolConfig] = None,
    day: Optional[ContextualDay] = None,
    seed: int = 0,
) -> list[EMAContextPacket]:
    """Build the bounded context packet for every prompt of one day."""
    config = config or default_config()
    resolved = as_request(request, day=day, seed=seed, config=config)
    contextual_day = resolved.day
    eligibility = DayEligibility.build(contextual_day, config)
    packets: list[EMAContextPacket] = []
    previous_state: Optional[dict[str, int]] = None
    previous_minute: Optional[float] = None
    for prompt in sorted(prompts, key=lambda item: item.prompt_time_min):
        packet = build_packet(
            contextual_day,
            prompt,
            config=config,
            eligibility=eligibility,
            previous_state=previous_state,
            previous_prompt_minute=previous_minute,
            persona=resolved.persona_context,
        )
        packets.append(packet)
        previous_minute = packet.prompt_time_min
    return packets


# --------------------------------------------------------------------------
# response generation
# --------------------------------------------------------------------------

def generate_responses(
    request: EMARequest | ContextualDay | Mapping[str, Any],
    prompts: Sequence[EMAPrompt],
    config: Optional[ProtocolConfig] = None,
    *,
    packets: Optional[Sequence[EMAContextPacket]] = None,
    seed: Optional[int] = None,
    llm_client: Optional[LLMClient] = None,
    allow_llm: bool = True,
    study_day_index: Optional[int] = None,
) -> tuple[list[EMAResponse], dict[str, Any]]:
    """Simulate response/non-response, latency, subjective state and note.

    Missingness is decided **independently** of subjective content: the
    Bernoulli draw uses only the context packet and the trigger type.
    """
    config = config or default_config()
    resolved = as_request(request, seed=seed or 0, config=config)
    contextual_day = resolved.day
    effective_seed = resolved.seed if seed is None else int(seed)
    if packets is None:
        packets = build_context(resolved, prompts, config)
    if len(packets) != len(prompts):
        raise ValueError("packets and prompts must be aligned one-to-one")

    rng = random.Random(stable_seed(contextual_day.participant_id, contextual_day.day, effective_seed) ^ 0x5EED)
    responses: list[EMAResponse] = []
    render_results: list[Optional[NoteRenderResult]] = []
    states: list[Optional[SubjectiveState]] = []
    traces: list[dict[str, Any]] = []
    llm_calls = 0
    llm_retries = 0
    previous_items: Optional[dict[str, int]] = None
    previous_minute: Optional[float] = None

    order = sorted(range(len(prompts)), key=lambda index: prompts[index].prompt_time_min)
    for index in order:
        prompt = prompts[index]
        packet = packets[index]
        decision = draw_response(prompt, packet, rng, config, study_day_index)
        latency = draw_latency(prompt, packet, rng, config) if decision.responded else None

        state, state_traces = generate_state(
            packet,
            config=config,
            seed=effective_seed,
            participant_id=contextual_day.participant_id,
            day_date=contextual_day.day,
            prompt_id=prompt.prompt_id,
            persona=resolved.persona_context,
            previous_state=previous_items,
            minutes_since_previous_prompt=(
                round(packet.prompt_time_min - previous_minute, 1) if previous_minute is not None else None
            ),
        )
        note_result: Optional[NoteRenderResult] = None
        if decision.responded and latency is not None and latency.status != ResponseStatus.MISSED:
            note_rng = random.Random(
                stable_seed(contextual_day.participant_id, contextual_day.day, effective_seed) + 1000 * (index + 1)
            )
            note_result = render_note(
                packet,
                state.items(),
                config=config,
                client=llm_client,
                rng=note_rng,
                allow_llm=allow_llm and llm_client is not None,
            )
            llm_calls += note_result.attempts
            llm_retries += note_result.retries

        if latency is None:
            status = ResponseStatus.MISSED
            response_time = None
            latency_minutes = None
            expired = False
            answered = False
            nonresponse_reason = "not_answered"
        else:
            status = latency.status
            response_time = prompt.prompt_time + timedelta(minutes=latency.latency_min)
            latency_minutes = latency.latency_min
            expired = latency.expired
            answered = status == ResponseStatus.ANSWERED
            nonresponse_reason = "expired" if status == ResponseStatus.EXPIRED else None

        usable = bool(
            answered and config.get("latency.usable_for_alignment_requires_answered", True)
        )
        # A simulated latent state exists for every opportunity (the response the
        # participant would have given).  It is only *emitted* when the prompt was
        # actually answered; for non-responses the record stays empty and the
        # missingness is explicit.
        keep_subjective = bool(decision.responded and status != ResponseStatus.MISSED)
        response = EMAResponse(
            prompt_id=prompt.prompt_id,
            status=status,
            prompt_time=prompt.prompt_time,
            response_time=response_time,
            latency_min=latency_minutes,
            expiry_minutes=float(config.get("latency.expiry_minutes", 10.0)),
            answered=answered,
            expired=expired,
            usable_for_alignment=usable,
            subjective=state if keep_subjective else None,
            context_note=(note_result.note if note_result else None),
            note_source=(note_result.source if note_result else None),
            note_validation=(note_result.to_dict() if note_result else None),
            device_wear=packet.device_wear,
            nonresponse_reason=nonresponse_reason,
            response_probability=round(decision.probability, 4),
            context_reference_time="prompt_time",
        )
        responses.append(response)
        render_results.append(note_result)
        states.append(state if keep_subjective else None)
        traces.append(traces_to_dict(state_traces))
        if decision.responded and status != ResponseStatus.MISSED:
            previous_items = state.items()
            previous_minute = packet.prompt_time_min

    responses.sort(key=lambda item: item.prompt_time)
    ordered_states = [None] * len(prompts)
    ordered_traces: list[dict[str, Any]] = [{}] * len(prompts)
    ordered_notes: list[Optional[NoteRenderResult]] = [None] * len(prompts)
    for position, index in enumerate(order):
        ordered_states[index] = states[position]
        ordered_traces[index] = traces[position]
        ordered_notes[index] = render_results[position]

    info: dict[str, Any] = {
        "states": ordered_states,
        "traces": ordered_traces,
        "note_results": ordered_notes,
        "llm_calls": llm_calls,
        "llm_retries": llm_retries,
        "response_model_version": MISSINGNESS_MODEL_VERSION,
        "latency_model_version": LATENCY_MODEL_VERSION,
        "pipeline_version": PIPELINE_VERSION,
    }
    return responses, info


# --------------------------------------------------------------------------
# bundle generation
# --------------------------------------------------------------------------

def generate_bundle(
    request: EMARequest | ContextualDay | Mapping[str, Any] | None = None,
    *,
    day: Optional[ContextualDay | Mapping[str, Any]] = None,
    seed: int = 0,
    config: Optional[ProtocolConfig] = None,
    llm_client: Optional[LLMClient] = None,
    allow_llm: bool = True,
    study_day_index: Optional[int] = None,
    participant_id: Optional[str] = None,
    date: Optional[Any] = None,
    validate: bool = True,
    audit: bool = True,
) -> EMABundle:
    """Generate one complete :class:`EMABundle` for one participant-day."""
    config = config or default_config()
    resolved = as_request(request, day=day, seed=seed, config=config, participant_id=participant_id, date=date)
    contextual_day = resolved.day
    effective_seed = int(resolved.seed)

    fingerprint_before = contextual_day.fingerprint()
    request_hash = resolved.hash()
    day_issues = validate_day_input(contextual_day)

    prompts, schedule_info = schedule_for_day(contextual_day, config, effective_seed)
    packets = build_context(resolved, prompts, config, seed=effective_seed)
    for prompt, packet in zip(prompts, packets):
        prompt.packet = packet
        prompt.inherited_context = {
            "activity": packet.activity.value if packet.activity else None,
            "domain": packet.domain.value if packet.domain else None,
            "place_type": packet.place_type.value if packet.place_type else None,
            "social_context": packet.social_context.value if packet.social_context else None,
            "indoor_outdoor": packet.indoor_outdoor.value if packet.indoor_outdoor else None,
            "device_wear": packet.device_wear.value if packet.device_wear else None,
            "episode_id": packet.episode_id,
            "interval_id": packet.interval_id,
            "journey_id": packet.journey_id,
            "purpose_category": packet.purpose_category,
            "preceding_activity": packet.preceding_activity.value if packet.preceding_activity else None,
            "preceding_journey_mode": packet.preceding_journey_mode,
        }

    responses, response_info = generate_responses(
        resolved,
        prompts,
        config,
        packets=packets,
        seed=effective_seed,
        llm_client=llm_client,
        allow_llm=allow_llm,
        study_day_index=study_day_index,
    )

    fingerprint_after = contextual_day.fingerprint()
    if fingerprint_after != fingerprint_before:  # pragma: no cover - must never happen
        raise InheritedContextMutationError(
            f"inherited context changed during generation: {fingerprint_before} -> {fingerprint_after}"
        )

    records: list[EMARecord] = []
    record_traces: list[dict[str, Any]] = []
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_decoding: dict[str, Any] = {}
    for index, (prompt, packet, response) in enumerate(zip(prompts, packets, responses)):
        note_result: Optional[NoteRenderResult] = response_info["note_results"][index]
        if note_result is not None:
            llm_provider = llm_provider or note_result.provider
            llm_model = llm_model or note_result.model
            llm_decoding = llm_decoding or dict(note_result.decoding)
        record_trace = build_record_provenance(
            prompt.prompt_id,
            trigger=prompt.trigger.value,
            prompt_time=prompt.prompt_time.isoformat(),
            response_time=response.response_time.isoformat() if response.response_time else None,
            episode_id=prompt.episode_id,
            interval_id=prompt.interval_id,
            journey_id=prompt.journey_id,
            validation_state="pending",
            note_result=note_result,
        )
        record_trace["subjective_trace"] = response_info["traces"][index]
        record_trace["context_packet"] = packet.to_dict()
        record_trace["packet_fingerprint"] = packet.fingerprint(12)
        record_trace["selection_reason"] = prompt.selection_reason
        record_trace["validation_state"] = "pending"
        record_traces.append(record_trace)

    provenance = build_provenance(
        participant_id=contextual_day.participant_id,
        day_date=contextual_day.day,
        seed=effective_seed,
        config=config,
        request_hash=request_hash,
        context_fingerprint=fingerprint_before,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_decoding=llm_decoding,
        llm_calls=int(response_info["llm_calls"]),
        llm_retries=int(response_info["llm_retries"]),
        notes=list(schedule_info.get("notes", []))
        + [f"input day diagnostics: {issue}" for issue in day_issues],
    )
    provenance.record_provenance = {
        prompt.prompt_id: trace for prompt, trace in zip(prompts, record_traces)
    }

    records = [
        EMARecord(prompt=prompt, response=response, packet=packet, provenance=provenance)
        for prompt, packet, response in zip(prompts, packets, responses)
    ]

    bundle = EMABundle(
        participant_id=contextual_day.participant_id,
        day_date=contextual_day.day,
        protocol_name=config.protocol_name,
        records=records,
        provenance=provenance,
        scales=describe_scales(),
        summary=_summarise(records, schedule_info, config, contextual_day),
    )
    if audit:
        bundle.audit = audit_schedule(contextual_day, [record.prompt for record in records], config)
        if bundle.audit.status == AuditStatus.NEEDS_REPAIR:
            provenance.notes.append(
                "self-audit reported NEEDS_REPAIR: " + "; ".join(bundle.audit.reasons)
            )
    if validate:
        from .validate import validate_bundle

        bundle.validation = validate_bundle(bundle, config, day=contextual_day)
        state = "pass" if bundle.validation.valid else "fail"
        for trace in provenance.record_provenance.values():
            trace["validation_state"] = state
    return bundle


def generate_ema(
    request: EMARequest | ContextualDay | Mapping[str, Any] | None = None,
    *,
    day: Optional[ContextualDay | Mapping[str, Any]] = None,
    seed: int = 0,
    config: Optional[ProtocolConfig] = None,
    llm_client: Optional[LLMClient] = None,
    allow_llm: bool = True,
    study_day_index: Optional[int] = None,
    validate: bool = True,
    audit: bool = True,
    **kwargs: Any,
) -> EMABundle:
    """Public entry point: generate a complete EMA bundle for one day.

    ``request`` may be an :class:`EMARequest`, a :class:`ContextualDay` or a
    generic mapping describing a contextual day (the adapter surface a host
    system such as DayForge/Appa would later use).
    """
    return generate_bundle(
        request,
        day=day,
        seed=seed,
        config=config,
        llm_client=llm_client,
        allow_llm=allow_llm,
        study_day_index=study_day_index,
        validate=validate,
        audit=audit,
        **kwargs,
    )


def generate_ema_multi_day(
    requests: Sequence[EMARequest | ContextualDay | Mapping[str, Any]],
    *,
    seed: int = 0,
    config: Optional[ProtocolConfig] = None,
    llm_client: Optional[LLMClient] = None,
    allow_llm: bool = True,
    validate: bool = True,
    audit: bool = True,
) -> list[EMABundle]:
    """Generate one bundle per supplied day (no cross-day narrative continuity).

    Continuity is limited to *within* a day, as specified.  Study-day index is
    derived from the position in the sequence and only matters when
    ``missingness.modifiers.study_day_decay.enabled`` is true.
    """
    bundles: list[EMABundle] = []
    for index, request in enumerate(requests):
        bundles.append(
            generate_bundle(
                request,
                seed=seed,
                config=config,
                llm_client=llm_client,
                allow_llm=allow_llm,
                study_day_index=index + 1,
                validate=validate,
                audit=audit,
            )
        )
    return bundles


# --------------------------------------------------------------------------
# summaries
# --------------------------------------------------------------------------

def _summarise(
    records: Sequence[EMARecord],
    schedule_info: Mapping[str, Any],
    config: ProtocolConfig,
    day: ContextualDay,
) -> dict[str, Any]:
    from .latency import latency_summary
    from .missingness import calibration_report

    answered = [record for record in records if record.response.answered]
    expired = [record for record in records if record.response.expired]
    missed = [record for record in records if record.response.status == ResponseStatus.MISSED]
    latencies = [record.response.latency_min for record in records if record.response.latency_min is not None]
    triggers: dict[str, int] = {}
    windows: dict[str, int] = {}
    for record in records:
        triggers[record.prompt.trigger.value] = triggers.get(record.prompt.trigger.value, 0) + 1
        label = str(record.prompt.window_index or 0)
        windows[label] = windows.get(label, 0) + 1
    items = [record.subjective_items() for record in records if record.subjective_items()]
    distribution = {
        item: {str(value): sum(1 for row in items if row and row.get(item) == value) for value in range(1, 6)}
        for item in ("valence", "energy", "stress")
    }
    means = {
        item: round(sum(row[item] for row in items) / len(items), 3) if items else None
        for item in ("valence", "energy", "stress")
    }
    notes = [record.response.context_note for record in records if record.response.context_note]
    return {
        "opportunities": len(records),
        "target_opportunities": int(config.get("sampling.opportunities_per_day", 5)),
        "background": int(schedule_info.get("background", 0)),
        "event_enriched": int(schedule_info.get("event_enriched", 0)),
        "trigger_counts": triggers,
        "windows_used": windows,
        "answered": len(answered),
        "expired": len(expired),
        "missed": len(missed),
        "response_rate": round(len(answered) / len(records), 4) if records else None,
        "calibration": calibration_report(len(answered), len(records), config),
        "latency": latency_summary(latencies),
        "subjective_distribution": distribution,
        "subjective_means": means,
        "notes_rendered": len(notes),
        "notes_null": sum(1 for record in records if record.response.answered and not record.response.context_note),
        "note_sources": {
            source: sum(1 for record in records if record.response.note_source == source)
            for source in ("llm", "offline_template")
        },
        "device_wear_available": bool(day.device_wear),
        "detected_event_kinds": schedule_info.get("event_kinds_detected", []),
        "scheduler_notes": schedule_info.get("notes", []),
        "eligible_minutes_per_window": schedule_info.get("eligible_minutes_per_window", {}),
        "capped_stability_margin_episodes": schedule_info.get("capped_margin_episodes", []),
        "versions": versions(config),
    }


__all__ = [
    "PIPELINE_VERSION",
    "InheritedContextMutationError",
    "as_request",
    "build_context",
    "generate_responses",
    "generate_bundle",
    "generate_ema",
    "generate_ema_multi_day",
    "describe_day",
]
