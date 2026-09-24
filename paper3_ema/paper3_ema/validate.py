"""Bundle validators.

``validate_bundle(bundle, config, day=...)`` checks a generated (or externally
supplied) :class:`EMABundle` against the Paper 3 contract and returns an
:class:`EMAValidationResult`.  It is read-only: it never repairs a bundle.

Check families
--------------
1. sampling      — exactly five opportunities, >=3 background, <=2 event-enriched
2. placement     — waking-window membership, exclusions, clustering, spread
3. linkage       — episode / interval / journey ids exist in the supplied day
4. inherited     — inherited contextual facts re-derive identically from the day
                   (proof that nothing was altered or hallucinated)
5. subjective    — 1..5 ordinal bounds, documented scale labels, present iff answered
6. missingness   — explicit status/reason for every non-response
7. latency       — dual timestamps, latency arithmetic, expiry semantics
8. note          — closed-world re-validation, source declaration, length limits
9. provenance    — versions, seed, hashes, fingerprint, field-origin classes
10. safeguards   — no demographic / persona attributes anywhere in the record
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Iterable, Mapping, Optional, Sequence

from .audit import audit_schedule
from .config import ProtocolConfig, default_config
from .context import build_packet
from .day import ContextualDay
from .eligibility import DayEligibility
from .models import (
    EMABundle,
    EMAContextPacket,
    EMARecord,
    EMAValidationIssue,
    EMAValidationResult,
)
from .notes import validate_note
from .provenance import FIELD_PROVENANCE, unclassified_fields
from .timeutil import format_hhmm
from .vocab import (
    FORBIDDEN_PERSONA_FACTS,
    SCALE_MAX,
    SCALE_MIN,
    SUBJECTIVE_ITEMS,
    ResponseStatus,
    TriggerType,
)

VALIDATOR_VERSION = "1.0.0"

INHERITED_FIELDS_TO_RECHECK = (
    "activity",
    "domain",
    "place_type",
    "social_context",
    "indoor_outdoor",
    "device_wear",
    "episode_id",
    "interval_id",
    "journey_id",
    "purpose_category",
    "preceding_activity",
    "preceding_journey_mode",
)


def _value(item: Any) -> Any:
    return item.value if hasattr(item, "value") and not isinstance(item, (str, int, float)) else item


# --------------------------------------------------------------------------
# main validator
# --------------------------------------------------------------------------

def validate_bundle(
    bundle: EMABundle | Mapping[str, Any],
    config: Optional[ProtocolConfig] = None,
    day: Optional[ContextualDay] = None,
) -> EMAValidationResult:
    config = config or default_config()
    issues: list[EMAValidationIssue] = []
    checks = 0

    def add(code: str, severity: str, message: str, prompt_id: Optional[str] = None, field_name: Optional[str] = None) -> None:
        issues.append(EMAValidationIssue(code=code, severity=severity, message=message, prompt_id=prompt_id, field=field_name))

    if not isinstance(bundle, EMABundle):
        raise TypeError("validate_bundle expects an EMABundle (build one with paper3_ema.generate_ema)")

    records = list(bundle.records)

    # ---- 1. sampling ----------------------------------------------------
    checks += 1
    expected = int(config.get("validation.expected_opportunities", config.get("sampling.opportunities_per_day", 5)))
    if len(records) != expected:
        add(
            "opportunity_count",
            "error" if len(records) < expected else "warning",
            f"expected exactly {expected} EMA opportunities, found {len(records)}",
        )
    background = [record for record in records if record.prompt.trigger == TriggerType.SEMI_RANDOM]
    event = [record for record in records if record.prompt.trigger != TriggerType.SEMI_RANDOM]
    checks += 1
    if len(background) < int(config.get("validation.min_background", 3)):
        add("background_minimum", "error", f"only {len(background)} semi-random opportunities (minimum 3)")
    checks += 1
    if len(event) > int(config.get("validation.max_event_enriched", 2)):
        add("event_maximum", "error", f"{len(event)} event-enriched opportunities (maximum 2)")

    # ---- 2/3. placement + linkage via the read-only auditor -------------
    if day is not None:
        checks += 1
        audit = audit_schedule(day, [record.prompt for record in records], config)
        for issue in audit.issues:
            if issue.severity == "info":
                continue
            add(
                f"audit.{issue.code}",
                issue.severity,
                issue.message,
                prompt_id=None,
                field_name=issue.prompt_time,
            )

        # ---- 4. inherited facts re-derive identically -------------------
        checks += 1
        eligibility = DayEligibility.build(day, config)
        for record in records:
            prompt = record.prompt
            fresh = build_packet(
                day,
                prompt,
                config=config,
                eligibility=eligibility,
                previous_state=None,
                previous_prompt_minute=None,
            )
            stored = record.packet
            for field_name in INHERITED_FIELDS_TO_RECHECK:
                expected_value = _value(getattr(fresh, field_name))
                actual_value = _value(getattr(stored, field_name))
                if expected_value != actual_value:
                    add(
                        "inherited_context_altered",
                        "error",
                        f"{prompt.prompt_id}: inherited field '{field_name}' is {actual_value!r} in the record "
                        f"but re-derives to {expected_value!r} from the supplied day",
                        prompt_id=prompt.prompt_id,
                        field_name=field_name,
                    )
            declared = prompt.inherited_context or {}
            for key in ("activity", "domain", "place_type", "social_context", "indoor_outdoor", "device_wear"):
                if key in declared and declared[key] != _value(getattr(fresh, key)):
                    add(
                        "inherited_context_altered",
                        "error",
                        f"{prompt.prompt_id}: prompt.inherited_context['{key}'] = {declared[key]!r} "
                        f"but the day yields {_value(getattr(fresh, key))!r}",
                        prompt_id=prompt.prompt_id,
                        field_name=key,
                    )
            if prompt.episode_id and prompt.episode_id not in {ep.episode_id for ep in day.episodes}:
                add("invalid_episode_linkage", "error", f"{prompt.prompt_id}: episode_id {prompt.episode_id!r} not in day", prompt.prompt_id)
            if prompt.interval_id and day.intervals and prompt.interval_id not in {iv.interval_id for iv in day.intervals}:
                add("invalid_interval_linkage", "error", f"{prompt.prompt_id}: interval_id {prompt.interval_id!r} not in day", prompt.prompt_id)
            if prompt.journey_id and prompt.journey_id not in {jn.journey_id for jn in day.journeys}:
                add("invalid_journey_linkage", "error", f"{prompt.prompt_id}: journey_id {prompt.journey_id!r} not in day", prompt.prompt_id)
            episode = day.episode_at(prompt.prompt_time_min)
            if config.get("eligibility.require_episode_coverage", True) and episode is None:
                add("prompt_outside_episode_coverage", "error", f"{prompt.prompt_id}: no episode covers {format_hhmm(prompt.prompt_time_min)}", prompt.prompt_id)
            if getattr(prompt, "stability_relaxed", False):
                exclusion = eligibility.relaxed_exclusion_at(prompt.prompt_time_min)
                add("stability_relaxed", "warning", f"{prompt.prompt_id}: boundary-stability margin relaxed (fragmented day)", prompt.prompt_id)
            else:
                exclusion = eligibility.exclusion_at(prompt.prompt_time_min)
            if exclusion.excluded:
                add("prompt_in_excluded_context", "error", f"{prompt.prompt_id}: {', '.join(exclusion.reasons)} at {format_hhmm(prompt.prompt_time_min)}", prompt.prompt_id)

    # ---- 5. subjective values ------------------------------------------
    checks += 1
    for record in records:
        response = record.response
        state = response.subjective
        if response.answered:
            if state is None:
                add("missing_subjective_state", "error", f"{record.prompt_id}: answered record without subjective state", record.prompt_id)
                continue
            for item in SUBJECTIVE_ITEMS:
                value = getattr(state, item)
                if not isinstance(value, int) or isinstance(value, bool):
                    add("scale_type", "error", f"{record.prompt_id}: {item} must be an int, got {type(value).__name__}", record.prompt_id, item)
                elif not SCALE_MIN <= value <= SCALE_MAX:
                    add("scale_bounds", "error", f"{record.prompt_id}: {item}={value} outside [{SCALE_MIN},{SCALE_MAX}]", record.prompt_id, item)
        else:
            if response.status == ResponseStatus.MISSED and state is not None:
                add("subjective_state_without_response", "error", f"{record.prompt_id}: non-response carries a subjective state", record.prompt_id)
            if response.status == ResponseStatus.EXPIRED and state is None:
                add("expired_without_subjective_state", "error", f"{record.prompt_id}: expired response lost its subjective state", record.prompt_id)

    # ---- 6. missingness -------------------------------------------------
    checks += 1
    for record in records:
        response = record.response
        if response.status == ResponseStatus.MISSED:
            if response.response_time is not None:
                add("missingness_inconsistent", "error", f"{record.prompt_id}: status=missed but a response_time is recorded", record.prompt_id)
            if not response.nonresponse_reason:
                add("missingness_unrecorded", "error", f"{record.prompt_id}: non-response without an explicit reason", record.prompt_id)
            if response.context_note is not None:
                add("note_without_response", "error", f"{record.prompt_id}: non-response carries a context note", record.prompt_id)
        elif response.status == ResponseStatus.EXPIRED:
            if not response.expired:
                add("expiry_flag_missing", "error", f"{record.prompt_id}: status=expired but expired flag is false", record.prompt_id)
            if response.usable_for_alignment:
                add("expired_marked_usable", "error", f"{record.prompt_id}: expired response marked usable_for_alignment", record.prompt_id)
            if response.latency_min is None:
                add("expired_without_latency", "warning", f"{record.prompt_id}: expired response without a latency value", record.prompt_id)
        elif response.status == ResponseStatus.ANSWERED:
            if response.response_time is None:
                add("dual_timestamp_missing", "error", f"{record.prompt_id}: answered record without response_time", record.prompt_id)
            if response.latency_min is None:
                add("dual_timestamp_missing", "error", f"{record.prompt_id}: answered record without latency", record.prompt_id)
            if response.expired:
                add("answered_but_expired", "error", f"{record.prompt_id}: status=answered but latency exceeded expiry", record.prompt_id)
            if not response.usable_for_alignment:
                add("answered_not_usable", "warning", f"{record.prompt_id}: answered record not marked usable_for_alignment", record.prompt_id)

    # ---- 7. latency arithmetic -----------------------------------------
    checks += 1
    expiry = float(config.get("latency.expiry_minutes", 10.0))
    max_latency = float(config.get("validation.max_latency_minutes", 30.0))
    for record in records:
        response = record.response
        if response.response_time is None or response.latency_min is None:
            continue
        expected_time = record.prompt.prompt_time + timedelta(minutes=response.latency_min)
        drift = abs((expected_time - response.response_time).total_seconds())
        if drift > 1.0:
            add("latency_arithmetic", "error", f"{record.prompt_id}: response_time is not prompt_time + latency (drift {drift:.1f}s)", record.prompt_id)
        if response.latency_min <= 0:
            add("latency_nonpositive", "error", f"{record.prompt_id}: latency must be positive", record.prompt_id)
        if response.latency_min > max_latency:
            add("latency_out_of_range", "warning", f"{record.prompt_id}: latency {response.latency_min:.1f} min exceeds {max_latency} min", record.prompt_id)
        if response.latency_min > expiry and not response.expired:
            add("expiry_not_flagged", "error", f"{record.prompt_id}: latency {response.latency_min:.1f} > expiry {expiry} min but not flagged expired", record.prompt_id)
        if response.latency_min <= expiry and response.expired:
            add("expiry_false_positive", "error", f"{record.prompt_id}: flagged expired although latency {response.latency_min:.1f} <= {expiry} min", record.prompt_id)
        if response.expiry_minutes != expiry:
            add("expiry_config_mismatch", "warning", f"{record.prompt_id}: record expiry {response.expiry_minutes} != configured {expiry}", record.prompt_id)
        if record.prompt.recall_frame != "current_at_prompt_time":
            add("recall_frame", "error", f"{record.prompt_id}: recall frame must be 'current_at_prompt_time'", record.prompt_id)
        if response.context_reference_time != "prompt_time":
            add("context_reference_time", "error", f"{record.prompt_id}: context reference must be 'prompt_time'", record.prompt_id)

    # ---- 8. notes -------------------------------------------------------
    checks += 1
    for record in records:
        response = record.response
        note = response.context_note
        if note is None:
            if response.note_source not in (None, "llm", "offline_template"):
                add("note_source_unknown", "warning", f"{record.prompt_id}: null note with source {response.note_source!r}", record.prompt_id)
            continue
        if response.status == ResponseStatus.MISSED:
            # a missed prompt has no response content at all
            add("note_without_response", "error", f"{record.prompt_id}: note present on a non-response", record.prompt_id)
        # EXPIRED responses DO carry (flagged) content, so a note is legitimate:
        validation = validate_note(note, record.packet, config)
        if not validation.valid:
            add(
                "note_closed_world_violation",
                "error",
                f"{record.prompt_id}: stored note fails closed-world validation ({', '.join(validation.codes)}): {note!r}",
                record.prompt_id,
            )
        if response.note_source is None:
            add("note_source_missing", "error", f"{record.prompt_id}: note present without a declared source", record.prompt_id)

    # ---- 9. provenance --------------------------------------------------
    checks += 1
    provenance = bundle.provenance
    required_provenance = {
        "protocol_version": provenance.protocol_version,
        "schema_version": provenance.schema_version,
        "scheduler_version": provenance.scheduler_version,
        "state_generator_version": provenance.state_generator_version,
        "auditor_version": provenance.auditor_version,
        "note_validator_version": provenance.note_validator_version,
        "seed": provenance.seed,
        "request_hash": provenance.request_hash,
        "context_fingerprint": provenance.context_fingerprint,
        "config_hash": provenance.config_hash,
        "participant_id": provenance.participant_id,
        "day_date": provenance.day_date,
        "generated_at": provenance.generated_at,
    }
    if config.get("provenance.record_field_origin", True) and not provenance.field_provenance:
        add("provenance_field_origin_missing", "error", "provenance.field_provenance is empty")
    for name, value in required_provenance.items():
        if value in (None, ""):
            add("provenance_incomplete", "error", f"provenance.{name} is missing")
    if provenance.participant_id and provenance.participant_id != bundle.participant_id:
        add("provenance_participant_mismatch", "error", "provenance participant differs from bundle participant")
    if provenance.config_hash and config.hash() and provenance.config_hash != config.hash():
        add("provenance_config_hash_mismatch", "warning", "bundle was produced with a different configuration hash")
    for record in records:
        trace = provenance.record_provenance.get(record.prompt_id)
        if not trace:
            add("provenance_record_missing", "error", f"{record.prompt_id}: no per-record provenance payload", record.prompt_id)
            continue
        for key in ("prompt_type", "prompt_time", "retry_count", "validation_state", "episode_id"):
            if key not in trace:
                add("provenance_record_incomplete", "error", f"{record.prompt_id}: record provenance lacks '{key}'", record.prompt_id, key)
        if trace.get("prompt_type") != record.prompt.trigger.value:
            add("provenance_trigger_mismatch", "error", f"{record.prompt_id}: provenance prompt_type differs from the record trigger", record.prompt_id)
    unclassified = unclassified_fields(FIELD_PROVENANCE.keys())
    if unclassified:  # pragma: no cover - static self-check
        add("provenance_field_unclassified", "error", f"fields without an origin class: {unclassified}")

    # ---- 10. demographic safeguard -------------------------------------
    checks += 1
    serialized = bundle.canonical_json().lower()
    for term in sorted(FORBIDDEN_PERSONA_FACTS):
        needle = f'"{term}"'
        if needle in serialized:
            add("demographic_leak", "error", f"bundle exposes forbidden persona/demographic field {term!r}")

    # ---- summary consistency -------------------------------------------
    checks += 1
    summary = bundle.summary or {}
    if summary:
        answered = sum(1 for record in records if record.response.answered)
        if summary.get("answered") not in (None, answered):
            add("summary_inconsistent", "warning", f"summary.answered={summary.get('answered')} but {answered} records are answered")
        if summary.get("opportunities") not in (None, len(records)):
            add("summary_inconsistent", "warning", f"summary.opportunities={summary.get('opportunities')} but {len(records)} records exist")
        low, high = (float(value) for value in config.get("missingness.calibration_target_response_rate", [0.85, 0.9]))
        rate = answered / len(records) if records else 0.0
        if records and config.get("validation.warn_when_response_rate_outside_calibration", True) and not (low <= rate <= high):
            add(
                "response_rate_outside_calibration",
                "info",
                f"day-level response rate {rate:.0%} is outside the calibration band [{low:.0%}, {high:.0%}] "
                "(the band is a cohort-level target, single days vary)",
            )

    errors = [issue for issue in issues if issue.severity == "error"]
    result = EMAValidationResult(
        valid=not errors,
        status="PASS" if not errors else "FAIL",
        issues=issues,
        checks_run=checks,
        summary={
            "records": len(records),
            "answered": sum(1 for record in records if record.response.answered),
            "expired": sum(1 for record in records if record.response.expired),
            "missed": sum(1 for record in records if record.response.status == ResponseStatus.MISSED),
            "background": len(background),
            "event_enriched": len(event),
            "errors": len(errors),
            "warnings": sum(1 for issue in issues if issue.severity == "warning"),
            "validator_version": VALIDATOR_VERSION,
        },
    )
    return result


def validate_records(records: Sequence[EMARecord], config: Optional[ProtocolConfig] = None) -> list[EMAValidationIssue]:
    """Lightweight per-record validation without a bundle (used in unit tests)."""
    config = config or default_config()
    issues: list[EMAValidationIssue] = []
    for record in records:
        for item in SUBJECTIVE_ITEMS:
            state = record.response.subjective
            if state is None:
                continue
            value = getattr(state, item)
            if not SCALE_MIN <= int(value) <= SCALE_MAX:
                issues.append(
                    EMAValidationIssue("scale_bounds", "error", f"{record.prompt_id}: {item}={value} out of bounds", record.prompt_id, item)
                )
    return issues


def summarise_validation(result: EMAValidationResult) -> str:
    lines = [f"{result.status}: {result.checks_run} checks, {len(result.errors)} error(s), {len(result.warnings)} warning(s)"]
    lines.extend(f"  - [{issue.severity}] {issue.code}: {issue.message}" for issue in result.issues)
    return "\n".join(lines)
