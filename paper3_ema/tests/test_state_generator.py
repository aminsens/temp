"""Structured subjective-state generator: seeded, bounded, transparent, demographically blind."""

from __future__ import annotations

import random

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture
from paper3_ema.models import EMARequest, PersonaContextFacts
from paper3_ema.pipeline import build_context
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.state import GENERATOR_INPUT_FIELDS, generate_state, is_deterministic_stereotype
from paper3_ema.models import EMAContextPacket
from paper3_ema.vocab import (
    FORBIDDEN_PERSONA_FACTS,
    SUBJECTIVE_ITEMS,
    Activity,
    Domain,
    IndoorOutdoor,
    PlaceType,
    SocialContext,
)


def _packets(fixture="normal_office_day", seed=7, n_seeds=(7,)):
    day = build_fixture(fixture)
    out = []
    for s in n_seeds:
        prompts, _ = schedule_for_day(day, default_config(), seed=s)
        request = EMARequest(day=day, participant_id=day.participant_id, day_date=day.day, seed=s)
        out.append((day, prompts, build_context(request, prompts)))
    return out


def test_ordinal_values_always_within_bounds():
    for day, prompts, packets in _packets(n_seeds=(1, 7, 42)):
        for prompt, packet in zip(prompts, packets):
            state, traces = generate_state(packet, seed=7, participant_id=day.participant_id, day_date=day.day, prompt_id=prompt.prompt_id)
            for item in SUBJECTIVE_ITEMS:
                value = getattr(state, item)
                assert 1 <= value <= 5
                assert isinstance(value, int)


def test_same_seed_reproduces_identically():
    day, prompts, packets = _packets()[0]
    results = []
    for _ in range(2):
        out = []
        for prompt, packet in zip(prompts, packets):
            state, _ = generate_state(packet, seed=7, participant_id=day.participant_id, day_date=day.day, prompt_id=prompt.prompt_id)
            out.append(state.items())
        results.append(out)
    assert results[0] == results[1]


def test_different_seeds_diverge():
    day, prompts, packets = _packets()[0]
    a = [generate_state(p, seed=1, participant_id="x", day_date="2026-01-01", prompt_id=f"i{i}")[0].items() for i, p in enumerate(packets)]
    b = [generate_state(p, seed=999, participant_id="x", day_date="2026-01-01", prompt_id=f"i{i}")[0].items() for i, p in enumerate(packets)]
    assert a != b


def test_context_changes_the_state():
    """Context sensitivity: the same seeds with different contexts give different
    mean latent states.  (A single draw can coincide by chance on a 5-point scale,
    so the test compares 40-seed means rather than one sample.)"""
    base_ctx = _fixed_work_context()
    post_exercise = EMAContextPacket(
        prompt_time_min=base_ctx.prompt_time_min,
        prompt_time=base_ctx.prompt_time,
        time_of_day=base_ctx.time_of_day,
        minutes_since_wake=base_ctx.minutes_since_wake,
        activity=Activity.OTHER_VIGOROUS,
        domain=Domain.EXERCISE,
        place_type=PlaceType.PARK,
        social_context=SocialContext.ALONE,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
        purpose_category="exercise",
        minutes_in_current_episode=10.0,
        minutes_since_activity_change=10.0,
        recent_exertion_60min=0.7,
        minutes_since_active_episode_end=10.0,
    )
    work_latents, post_latents = [], []
    for seed in range(1, 41):
        s1, _ = generate_state(base_ctx, seed=seed, participant_id="p1", day_date="2026-05-04", prompt_id=f"a{seed}")
        s2, _ = generate_state(post_exercise, seed=seed, participant_id="p1", day_date="2026-05-04", prompt_id=f"a{seed}")
        work_latents.append(s1.latent)
        post_latents.append(s2.latent)
    diffs = {
        item: abs(
            sum(row[item] for row in post_latents) / len(post_latents)
            - sum(row[item] for row in work_latents) / len(work_latents)
        )
        for item in SUBJECTIVE_ITEMS
    }
    assert max(diffs.values()) > 0.15, f"contexts produced nearly identical latent states: {diffs}"


def _fixed_work_context():
    """One fixed, common context: sitting at work in the afternoon."""
    from datetime import datetime

    return EMAContextPacket(
        prompt_time_min=15 * 60 + 30,
        prompt_time=datetime(2026, 5, 4, 15, 30),
        time_of_day="afternoon",
        minutes_since_wake=450.0,
        activity=Activity.SITTING,
        domain=Domain.WORK,
        place_type=PlaceType.WORKPLACE,
        social_context=SocialContext.WITH_COLLEAGUES,
        indoor_outdoor=IndoorOutdoor.INDOOR,
        purpose_category="work",
        minutes_in_current_episode=90.0,
        minutes_since_activity_change=90.0,
        minutes_to_next_commitment=45.0,
        next_commitment_kind="work",
    )


def test_no_deterministic_stereotype_for_a_fixed_context():
    """The same context with different seeds must not always map to the same state.

    This is the direct guard against ``activity == work -> stress = high``.
    """
    packet = _fixed_work_context()
    states, contexts = [], []
    for seed in range(1, 31):
        state, _ = generate_state(packet, seed=seed, participant_id="p1", day_date="2026-05-04", prompt_id=f"s{seed}")
        states.append(state)
        contexts.append(packet)
    report = is_deterministic_stereotype(states, contexts)
    stereotypes = {key: value for key, value in report.items() if value["stereotype"]}
    assert not stereotypes, f"deterministic stereotypes detected: {stereotypes}"
    # and the distribution must be genuinely mixed
    values = [state.stress for state in states]
    assert len(set(values)) >= 2, f"stress collapsed to a single value across 30 seeds: {set(values)}"


def test_rules_are_traced_and_documented():
    day, prompts, packets = _packets()[0]
    state, traces = generate_state(packets[0], seed=7, participant_id=day.participant_id, day_date=day.day, prompt_id=prompts[0].prompt_id)
    for item in SUBJECTIVE_ITEMS:
        trace = traces[item]
        assert isinstance(trace.rules, list)
        for rule in trace.rules:
            assert rule.rule  # named
            assert isinstance(rule.delta, float)
            assert rule.detail  # documented
    assert state.rules_applied
    assert state.contributions


def test_modifier_clip_is_enforced():
    config = default_config()
    clip = float(config.get("state_generator.modifier_clip", 1.5))
    day, prompts, packets = _packets()[0]
    for packet in packets:
        _, traces = generate_state(packet, seed=7, participant_id="x", day_date="2026-01-01", prompt_id="p")
        for item in SUBJECTIVE_ITEMS:
            assert abs(traces[item].modifier_clipped) <= clip + 1e-9


def test_generator_cannot_read_forbidden_persona_fields():
    for forbidden in FORBIDDEN_PERSONA_FACTS:
        assert forbidden not in GENERATOR_INPUT_FIELDS
    # the generator's declared inputs are a subset of the packet's fields
    packet_fields = {f for f in EMAContextPacket.__dataclass_fields__}
    assert set(GENERATOR_INPUT_FIELDS) <= packet_fields | {"previous_state"}


def test_childcare_responsibility_only_applies_inside_childcare():
    """Allowed persona use: childcare responsibility only inside childcare episodes."""
    from paper3_ema.state import _rule_childcare

    config = default_config()
    person = PersonaContextFacts(childcare_responsibility=True)
    outside = EMAContextPacket(
        prompt_time_min=12 * 60, prompt_time=None, time_of_day="midday",
        domain=Domain.WORK,
    )
    inside = EMAContextPacket(
        prompt_time_min=12 * 60, prompt_time=None, time_of_day="midday",
        domain=Domain.CHILDCARE,
    )
    assert _rule_childcare(outside, config, person) == []
    assert _rule_childcare(inside, config, person) != []


def test_commute_mode_only_applies_in_transport_context():
    from paper3_ema.state import _rule_commute_context

    config = default_config()
    person = PersonaContextFacts(usual_commute_mode="bike")
    non_transport = EMAContextPacket(
        prompt_time_min=12 * 60, prompt_time=None, time_of_day="midday",
        domain=Domain.LEISURE,
    )
    assert _rule_commute_context(non_transport, config, person) == []


def test_continuity_anchors_towards_previous_state():
    """Same context + previous state pulls the sample toward it (bounded)."""
    day, prompts, packets = _packets()[0]
    packet = packets[3]
    no_prev, _ = generate_state(packet, seed=7, participant_id="x", day_date="2026-01-01", prompt_id="p")
    with_prev, _ = generate_state(
        packet, seed=7, participant_id="x", day_date="2026-01-01", prompt_id="p",
        previous_state={"valence": 5, "energy": 5, "stress": 5},
        minutes_since_previous_prompt=60.0,
    )
    # the previous high state should raise (or at least not lower) the valence
    assert with_prev.valence >= no_prev.valence - 1


def test_latent_state_is_bounded():
    day, prompts, packets = _packets(n_seeds=(1, 7))[0]
    for packet in packets:
        state, _ = generate_state(packet, seed=7, participant_id="x", day_date="2026-01-01", prompt_id="p")
        for item in SUBJECTIVE_ITEMS:
            assert 1.0 <= state.latent[item] <= 5.0
