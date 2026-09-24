"""Context packet tests: bounded, name-free, demographically blind, prompt-time anchored."""

from __future__ import annotations

import json

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture
from paper3_ema.models import EMARequest, PersonaContextFacts
from paper3_ema.pipeline import build_context, generate_ema
from paper3_ema.scheduler import schedule_for_day


def _first_packet(fixture="normal_office_day", seed=7):
    day = build_fixture(fixture)
    prompts, _ = schedule_for_day(day, default_config(), seed=seed)
    packets = build_context(EMARequest(day=day, participant_id=day.participant_id, day_date=day.day, seed=seed), prompts)
    return day, prompts, packets


def test_packet_carries_inherited_facts_verbatim():
    day, prompts, packets = _first_packet()
    for prompt, packet in zip(prompts, packets):
        episode = day.episode_at(prompt.prompt_time_min)
        assert packet.activity == episode.activity
        assert packet.domain == episode.domain
        assert packet.place_type == episode.place_type
        assert packet.social_context == episode.social
        assert packet.indoor_outdoor == episode.indoor_outdoor
        assert packet.episode_id == episode.episode_id


def test_packet_is_bounded_and_name_free():
    for fixture in ("normal_office_day", "public_transport_commuter_day", "exercise_day"):
        day, prompts, packets = _first_packet(fixture)
        for packet in packets:
            text = json.dumps(packet.to_dict()).lower()
            # no proper names / free-text narratives may leak into the packet
            import re as _re

            for banned in ("ntnu", "realfagbygget", "singsaker", "nidelva", "byparken",
                           "sit", "elgeseter", "klostergata", "narrative", "mood"):
                assert not _re.search(rf"(?<![a-z]){_re.escape(banned)}(?![a-z])", text), (
                    f"{fixture}: {banned!r} leaked into context packet"
                )
            if packet.purpose_category is not None:
                assert " " not in packet.purpose_category, "purpose must be a coarse category, not free text"
            assert len(packet.allowed_entities) <= 20


def test_packet_is_demographically_blind():
    day, prompts, packets = _first_packet()
    for packet in packets:
        dump = json.dumps(packet.to_dict())
        for banned in ("age", "gender", "sex", "occupation", "personality", "hobbies",
                       "health", "fitness", "diagnosis"):
            assert f'"{banned}"' not in dump


def test_persona_allowlist_is_closed():
    with pytest.raises(ValueError, match="not permitted"):
        PersonaContextFacts.from_mapping(
            {"childcare_responsibility": True, "age": 41, "personality_traits": ["analytical"]},
            strict=True,
        )
    # non-strict drops, never leaks
    facts = PersonaContextFacts.from_mapping(
        {"childcare_responsibility": True, "age": 41, "personality_traits": ["analytical"]},
        strict=False,
    )
    assert facts.childcare_responsibility is True
    assert not hasattr(facts, "age")


def test_context_is_anchored_to_prompt_time():
    day, prompts, packets = _first_packet(fixture="cycling_commuter_day")
    for prompt, packet in zip(prompts, packets):
        # the packet's time must equal the prompt time (never the response time)
        assert abs(packet.prompt_time_min - prompt.prompt_time_min) < 1e-9
        assert packet.prompt_time == prompt.prompt_time


def test_minutes_since_wake_and_commitments_are_derived():
    day, prompts, packets = _first_packet()
    for packet in packets:
        assert packet.minutes_since_wake == pytest.approx(packet.prompt_time_min - day.wake_min, abs=0.2)
        if day.fixed_commitments:
            upcoming = [fc for fc in day.fixed_commitments if fc.end_min > packet.prompt_time_min]
            if upcoming:
                expected = min(upcoming, key=lambda fc: fc.start_min)
                if expected.end_min > packet.prompt_time_min:
                    assert packet.next_commitment_kind is not None or packet.next_commitment_requires_travel is not None


def test_documented_journey_delay_stays_inherited():
    day, prompts, packets = _first_packet(fixture="public_transport_commuter_day")
    documented = [p for p in packets if p.minutes_since_journey_end is not None]
    assert documented, "expected a post-journey packet"
    am = [p for p in documented if p.minutes_since_journey_end <= 30]
    assert any(p.preceding_journey_delayed for p in am), "documented AM delay should be visible in the packet"


def test_wear_status_is_inherited_when_present():
    day, prompts, packets = _first_packet(fixture="exercise_day")  # has a non-worn morning window
    not_worn = [p for p in packets if p.device_wear is not None and p.device_wear.value == "not_worn"]
    # prompts in 06:45-08:20 would show not_worn; only assert consistency when present
    for packet in packets:
        if packet.device_wear is not None:
            assert packet.device_wear == day.wear_status_at(packet.prompt_time_min)
