"""End-to-end: bundle contract, provenance completeness, immutability of inherited facts."""

from __future__ import annotations

import copy
import json

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import FIXTURE_BUILDERS, build_fixture
from paper3_ema.pipeline import generate_ema
from paper3_ema.validate import validate_bundle
from paper3_ema.vocab import ResponseStatus


def test_all_fixtures_produce_valid_bundles():
    for name in FIXTURE_BUILDERS:
        day = build_fixture(name)
        bundle = generate_ema(day, seed=7)
        assert len(bundle.records) == 5
        assert bundle.validation is not None
        assert bundle.validation.valid, f"{name}: {bundle.validation.issues}"
        assert bundle.audit is not None
        assert bundle.audit.valid, f"{name}: {bundle.audit.reasons}"


def test_bundle_is_json_serialisable():
    bundle = generate_ema(build_fixture("normal_office_day"), seed=7)
    text = bundle.to_json()
    parsed = json.loads(text)
    assert parsed["participant_id"] == bundle.participant_id
    assert len(parsed["records"]) == 5


def test_canonical_json_is_stable():
    a = generate_ema(build_fixture("normal_office_day"), seed=7)
    b = generate_ema(build_fixture("normal_office_day"), seed=7)
    assert a.canonical_json() == b.canonical_json()


def test_provenance_is_complete():
    bundle = generate_ema(build_fixture("normal_office_day"), seed=7)
    prov = bundle.provenance
    assert prov.protocol_version
    assert prov.schema_version
    assert prov.scheduler_version
    assert prov.state_generator_version
    assert prov.auditor_version
    assert prov.note_validator_version
    assert prov.seed == 7
    assert prov.request_hash
    assert prov.context_fingerprint
    assert prov.config_hash == default_config().hash()
    assert prov.participant_id == bundle.participant_id
    assert prov.day_date == bundle.day_date.isoformat()
    assert prov.generated_at
    assert prov.field_provenance, "field-level origin map must be present"
    for record in bundle.records:
        trace = prov.record_provenance[record.prompt_id]
        assert trace["prompt_type"] == record.prompt.trigger.value
        assert trace["prompt_time"]
        assert "retry_count" in trace
        assert "validation_state" in trace
        assert trace["episode_id"] == record.prompt.episode_id
        assert trace["context_packet"], "context packet must be retained for audit"
        assert trace["subjective_trace"], "subjective rule trace must be retained"


def test_field_origin_classes_are_assigned():
    from paper3_ema.provenance import FIELD_PROVENANCE
    from paper3_ema.vocab import ProvenanceClass

    values = set(FIELD_PROVENANCE.values())
    allowed = {c.value for c in ProvenanceClass}
    assert values <= allowed
    # spot checks of the contract
    assert FIELD_PROVENANCE["activity"] == ProvenanceClass.INHERITED_CONTEXT.value
    assert FIELD_PROVENANCE["time_of_day"] == ProvenanceClass.DERIVED_CONTEXT.value
    assert FIELD_PROVENANCE["prompt_time"] == ProvenanceClass.SYNTHETIC_PROTOCOL.value
    assert FIELD_PROVENANCE["valence"] == ProvenanceClass.SYNTHETIC_SUBJECTIVE.value
    assert FIELD_PROVENANCE["context_note"] == ProvenanceClass.LLM_RENDERED.value


def test_inherited_facts_are_detected_as_tampered():
    """Tampering with inherited context must be detected by the validator.

    The packet is a frozen dataclass (inherited facts cannot be mutated in
    place); the tamper here replaces the packet with one whose inherited
    ``domain`` disagrees with the day, which the validator must flag.
    """
    import dataclasses

    from paper3_ema.vocab import Domain

    day = build_fixture("normal_office_day")
    bundle = generate_ema(day, seed=7)
    record = bundle.records[2]
    tampered = dataclasses.replace(record.packet, domain=Domain.EXERCISE)
    bundle.records[2] = dataclasses.replace(record, packet=tampered)
    result = validate_bundle(bundle, default_config(), day=day)
    assert not result.valid
    assert any(i.code == "inherited_context_altered" for i in result.issues)


def test_context_fingerprint_covers_the_day():
    day_a = build_fixture("normal_office_day")
    day_b = build_fixture("normal_office_day")
    bundle_a = generate_ema(day_a, seed=7)
    bundle_b = generate_ema(day_b, seed=7)
    assert bundle_a.provenance.context_fingerprint == day_a.fingerprint()
    assert bundle_a.provenance.context_fingerprint == bundle_b.provenance.context_fingerprint


def test_missing_responses_are_explicit_and_counted():
    bundle = generate_ema(build_fixture("no_journeys_day"), seed=42)
    missed = [r for r in bundle.records if r.response.status == ResponseStatus.MISSED]
    for record in missed:
        assert record.response.nonresponse_reason == "not_answered"
        assert record.response.response_time is None
    summary = bundle.summary
    assert summary["missed"] == len(missed)
    assert summary["answered"] + summary["expired"] + summary["missed"] == len(bundle.records)


def test_note_source_is_declared_for_every_note():
    for name in FIXTURE_BUILDERS:
        bundle = generate_ema(build_fixture(name), seed=7)
        for record in bundle.records:
            if record.response.context_note is not None:
                assert record.response.note_source in ("llm", "offline_template")
                assert record.response.note_validation is not None
                from paper3_ema.notes import validate_note

                assert validate_note(record.response.context_note, record.packet, default_config()).valid


def test_scales_documented_in_bundle():
    bundle = generate_ema(build_fixture("normal_office_day"), seed=7)
    assert set(bundle.scales) == {"valence", "energy", "stress"}
    assert bundle.scales["stress"]["1"] == "none/very low"
    assert bundle.scales["valence"]["5"] == "very positive"
    assert bundle.scales["energy"]["3"] == "moderate"


def test_multi_day_generation_produces_one_bundle_per_day():
    from paper3_ema.fixtures import demo_cohort
    from paper3_ema.pipeline import generate_ema_multi_day

    cohort = demo_cohort(participants=2, days=3, seed=5)
    bundles = generate_ema_multi_day(cohort, seed=5)
    assert len(bundles) == 6
    pairs = {(b.participant_id, b.day_date.isoformat()) for b in bundles}
    assert len(pairs) == 6  # one bundle per (participant, date)
    participants = {b.participant_id for b in bundles}
    assert len(participants) == 2
    for pid in participants:
        assert len([b for b in bundles if b.participant_id == pid]) == 3
