"""Closed-world note contract: rejection of unsupported facts, retry, null fallback."""

from __future__ import annotations

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture
from paper3_ema.llm import (
    ScriptedLLMClient,
    extract_json,
    offline_note,
    render_note,
)
from paper3_ema.missingness import draw_response
from paper3_ema.models import EMARequest
from paper3_ema.notes import validate_note
from paper3_ema.pipeline import build_context, generate_ema
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.state import generate_state


def _one_answered_record(fixture="public_transport_commuter_day", seed=7):
    day = build_fixture(fixture)
    for s in (seed, seed + 1, seed + 2, seed + 3, seed + 4):
        bundle = generate_ema(day, seed=s)
        answered = [r for r in bundle.records if r.response.answered]
        if answered:
            return day, answered[0]
    raise AssertionError("no answered record found")


def _note_for(packet, state_items, note):
    return validate_note(note, packet, default_config())


def test_valid_grounding_note_passes():
    day, record = _one_answered_record()
    packet = record.packet
    note = "Feeling a bit tired after the train trip."
    if packet.preceding_journey_mode:
        assert _note_for(packet, None, note).valid or any(
            i.code == "unsupported_activity" for i in _note_for(packet, None, note).issues
        )
    # a note only using the time of day and a feeling is always safe
    safe = "Feeling fairly neutral at this point in the day."
    assert _note_for(packet, None, safe).valid


def test_unsupported_delay_is_rejected():
    day, record = _one_answered_record()
    packet = record.packet
    if packet.preceding_journey_delayed:
        pytest.skip("this packet documents a delay; use a non-delayed packet")
    v = _note_for(packet, None, "Stressed because the bus was delayed.")
    assert not v.valid
    assert "unsupported_delay" in v.codes or "unsupported_activity" in v.codes


def test_unsupported_person_is_rejected_when_alone():
    day, record = _one_answered_record()
    packet = record.packet
    if packet.social_context is not None and packet.social_context.value != "alone":
        pytest.skip("packet has company; person reference is supported")
    v = _note_for(packet, None, "Happy because my friend called me.")
    assert not v.valid
    assert "unsupported_person" in v.codes or "unsupported_cause" in v.codes


def test_unsupported_weather_is_rejected():
    day, record = _one_answered_record()
    packet = record.packet
    if packet.weather_available:
        pytest.skip("weather is documented for this packet")
    v = _note_for(packet, None, "Feeling great in the rain.")
    assert not v.valid
    assert "unsupported_weather" in v.codes


def test_unsupported_place_is_rejected():
    day, record = _one_answered_record()
    packet = record.packet
    v = _note_for(packet, None, "Feeling calm at the beach.")
    assert not v.valid
    assert "unsupported_reference" in v.codes or "unsupported_place" in v.codes


def test_unsupported_event_is_rejected():
    day, record = _one_answered_record()
    packet = record.packet
    if packet.minutes_to_next_commitment is not None:
        pytest.skip("packet has a fixed commitment; use one without")
    v = _note_for(packet, None, "Anxious because of the deadline.")
    assert not v.valid
    assert "unsupported_event" in v.codes or "unsupported_cause" in v.codes


def test_medical_and_trait_claims_are_rejected():
    day, record = _one_answered_record()
    packet = record.packet
    v1 = _note_for(packet, None, "I have a headache and a fever.")
    assert not v1.valid and "medical_condition" in v1.codes
    v2 = _note_for(packet, None, "As an introvert I feel calm alone.")
    assert not v2.valid and "psychological_trait_inference" in v2.codes


def test_proper_nouns_are_rejected():
    day, record = _one_answered_record()
    packet = record.packet
    v = _note_for(packet, None, "Feeling fine at the Nidelva riverbank.")
    assert not v.valid and "proper_noun" in v.codes


def test_length_limits_are_enforced():
    day, record = _one_answered_record()
    packet = record.packet
    long_note = "Feeling fine. " * 10
    v = _note_for(packet, None, long_note.strip())
    assert not v.valid
    assert "multiple_sentences" in v.codes or "too_long" in v.codes


def test_null_is_always_valid():
    day, record = _one_answered_record()
    packet = record.packet
    assert validate_note(None, packet, default_config()).valid


def test_offline_template_output_always_passes_closed_world():
    """The deterministic renderer must only ever emit contract-compliant notes."""
    for fixture in ("normal_office_day", "public_transport_commuter_day", "exercise_day", "mostly_home_day"):
        day = build_fixture(fixture)
        bundle = generate_ema(day, seed=7)
        for record in bundle.records:
            if not record.response.answered:
                continue
            # re-render offline notes across many rng seeds and validate each
            for rng_seed in range(30):
                import random as _random

                note = offline_note(
                    record.packet,
                    record.response.subjective.items() if record.response.subjective else {"valence": 3, "energy": 3, "stress": 3},
                    _random.Random(rng_seed),
                    default_config(),
                )
                if note is None:
                    continue
                assert validate_note(note, record.packet, default_config()).valid, note


def test_llm_retry_then_success():
    day, record = _one_answered_record()
    packet = record.packet
    state = {"valence": 3, "energy": 3, "stress": 3}
    client = ScriptedLLMClient(responses=[
        'thinking... <json>{"context_note": "It is raining heavily and my friend is here."}</json>',
        '<json>{"context_note": "Feeling fairly neutral right now."}</json>',
    ])
    result = render_note(packet, state, default_config(), client=client, rng=None, allow_llm=True)
    assert result.source == "llm"
    assert result.note is not None
    assert result.retries == 1
    assert result.attempts == 2
    assert validate_note(result.note, packet, default_config()).valid


def test_llm_persistently_unsafe_falls_back_to_null_or_template():
    day, record = _one_answered_record()
    packet = record.packet
    state = {"valence": 3, "energy": 3, "stress": 3}
    # every attempt invents a delay
    client = ScriptedLLMClient(responses=[
        '<json>{"context_note": "Stressed because the train was delayed again."}</json>',
    ])
    result = render_note(packet, state, default_config(), client=client, rng=None, allow_llm=True)
    # it must not emit the unsafe note verbatim
    assert result.note is None or "delayed" not in (result.note or "").lower()
    if result.note is not None:
        assert result.source == "offline_template"
        assert validate_note(result.note, packet, default_config()).valid
    else:
        assert result.fallback_reason is not None


def test_llm_chosing_null_is_accepted():
    day, record = _one_answered_record()
    packet = record.packet
    state = {"valence": 3, "energy": 3, "stress": 3}
    client = ScriptedLLMClient(responses=['<json>{"context_note": null}</json>'])
    result = render_note(packet, state, default_config(), client=client, rng=None, allow_llm=True)
    assert result.note is None
    assert result.source == "llm"


def test_llm_never_used_to_pick_subjective_values():
    config = default_config()
    assert bool(config.get("llm.allowed_to_select_subjective_values")) is False


def test_extract_json_handles_reasoning_wraparound():
    assert extract_json('blah blah <json>{"a": 1}</json> blah') == {"a": 1}
    assert extract_json('```json\n{"b": 2}\n```') == {"b": 2}
    assert extract_json('{"c": 3}') == {"c": 3}
    assert extract_json('no json here') is None


def test_closed_world_blocks_invented_journey():
    day = build_fixture("no_journeys_day")
    bundle = generate_ema(day, seed=7)
    record = next(r for r in bundle.records if r.response.answered)
    packet = record.packet
    if packet.minutes_since_journey_end is not None or packet.preceding_journey_mode:
        pytest.skip("packet has a journey")
    v = _note_for(packet, None, "Feeling great after the long bus ride.")
    assert not v.valid
    assert "unsupported_journey" in v.codes or "unsupported_activity" in v.codes or "unsupported_reference" in v.codes
