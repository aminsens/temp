"""Adversarial fixture-day tests: the protocol's documented behaviour under strain."""

from __future__ import annotations

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import (
    FIXTURE_BUILDERS,
    FIXTURE_EXPECTATIONS,
    build_fixture,
)
from paper3_ema.pipeline import generate_ema
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.vocab import TriggerType


def _prompts(name, seed=7):
    day = build_fixture(name)
    prompts, info = schedule_for_day(day, default_config(), seed=seed)
    return day, prompts, info


# ---------------------------------------------------------------- 1. normal office day
def test_normal_office_day_post_trip_triggers():
    day, prompts, _ = _prompts("normal_office_day")
    triggers = [p.trigger for p in prompts]
    assert TriggerType.POST_TRIP in triggers
    for p in prompts:
        if p.trigger == TriggerType.POST_TRIP:
            assert p.journey_id is not None
            assert p.prompt_time_min >= next(j.end_min for j in day.journeys if j.journey_id == p.journey_id)


# ---------------------------------------------------------------- 2. cycling commuter
def test_cycling_commuter_no_prompt_during_cycling():
    day, prompts, _ = _prompts("cycling_commuter_day")
    for p in prompts:
        ep = day.episode_at(p.prompt_time_min)
        assert ep.activity.value not in ("cycling", "running"), f"prompt at {p.prompt_time_min} during {ep.activity.value}"


def test_cycling_commuter_post_trip_after_ride():
    day, prompts, _ = _prompts("cycling_commuter_day")
    post_trip = [p for p in prompts if p.trigger == TriggerType.POST_TRIP]
    assert post_trip
    for p in post_trip:
        journey = next(j for j in day.journeys if j.journey_id == p.journey_id)
        assert p.prompt_time_min > journey.end_min


# ---------------------------------------------------------------- 3. public-transport commuter
def test_public_transport_commuter_no_prompt_inside_vehicle():
    day, prompts, _ = _prompts("public_transport_commuter_day")
    for p in prompts:
        ep = day.episode_at(p.prompt_time_min)
        assert ep.activity.value != "public_transport"


# ---------------------------------------------------------------- 4. no journeys
def test_no_journeys_day_has_no_post_trip():
    day, prompts, _ = _prompts("no_journeys_day")
    assert not any(p.trigger == TriggerType.POST_TRIP for p in prompts)
    assert all(p.journey_id is None for p in prompts)


# ---------------------------------------------------------------- 5. exercise day
def test_exercise_day_no_prompt_during_vigorous():
    day, prompts, _ = _prompts("exercise_day")
    for p in prompts:
        ep = day.episode_at(p.prompt_time_min)
        assert ep.activity.value not in ("running", "other_vigorous"), f"prompt during {ep.activity.value}"


def test_exercise_day_post_active_after_bout():
    day, prompts, _ = _prompts("exercise_day")
    post_active = [p for p in prompts if p.trigger == TriggerType.POST_ACTIVE_EPISODE]
    assert post_active, "expected at least one post_active_episode prompt"
    run_end = 8 * 60 + 20  # the morning run ends at 08:20 in the fixture
    for p in post_active:
        assert p.prompt_time_min >= run_end, (
            f"post-active prompt at {p.prompt_time_min} precedes the end of the run"
        )


# ---------------------------------------------------------------- 6. highly fragmented day
def test_highly_fragmented_day_places_five_or_reports_relaxation():
    day, prompts, info = _prompts("highly_fragmented_day")
    assert len(prompts) == 5
    # every prompt must be either strictly stable or explicitly flagged relaxed
    for p in prompts:
        if p.stability_relaxed:
            assert "[stability_relaxed" in p.selection_reason
    assert all(p.trigger == TriggerType.SEMI_RANDOM for p in prompts)


# ---------------------------------------------------------------- 7. mostly home day
def test_mostly_home_day_place_is_home():
    day, prompts, _ = _prompts("mostly_home_day")
    for p in prompts:
        ep = day.episode_at(p.prompt_time_min)
        assert ep.place_type.value in ("home", "outdoor_generic"), f"place {ep.place_type.value}"


# ---------------------------------------------------------------- 8. no eligible event
def test_no_eligible_event_day_all_semi_random():
    day, prompts, info = _prompts("no_eligible_event_day")
    assert all(p.trigger == TriggerType.SEMI_RANDOM for p in prompts)
    assert info["event_kinds_detected"] == []


# ---------------------------------------------------------------- 9. evening shift day
def test_evening_shift_day_no_prompt_while_driving_or_asleep():
    day, prompts, _ = _prompts("evening_shift_day")
    for p in prompts:
        ep = day.episode_at(p.prompt_time_min)
        assert ep.activity.value not in ("driving", "sleeping", "lying_awake")
    # the day wakes at 10:15; the first prompt must be after wake
    first = min(p.prompt_time_min for p in prompts)
    assert first >= day.wake_min


# ------------------------------------------------------- 10. unresolved movement day
def test_unresolved_movement_day_avoids_bad_intervals():
    day, prompts, _ = _prompts("unresolved_movement_day")
    for p in prompts:
        ep = day.episode_at(p.prompt_time_min)
        assert ep.is_realised, f"prompt inside non-realised movement at {p.prompt_time_min}"
        assert not ep.is_unresolved, f"prompt inside unresolved interval at {p.prompt_time_min}"
        # the cancelled cycling commute is 08:30-09:00; nothing may prompt there
        assert not (8 * 60 + 30 <= p.prompt_time_min < 9 * 60)


def test_all_fixtures_documented_expectations_present():
    for name in FIXTURE_BUILDERS:
        assert name in FIXTURE_EXPECTATIONS
        assert len(FIXTURE_EXPECTATIONS[name]) > 10


# ---------------------------------------------------------------- cross-cutting
@pytest.mark.parametrize("name", sorted(FIXTURE_BUILDERS))
def test_every_fixture_valid_and_audit_clean(name):
    day = build_fixture(name)
    bundle = generate_ema(day, seed=7)
    assert bundle.validation.valid, f"{name}: {[i.message for i in bundle.validation.issues]}"
    assert bundle.audit.valid, f"{name}: {bundle.audit.reasons}"


@pytest.mark.parametrize("seed", [1, 7, 42, 1234, 99999])
def test_scheduler_deterministic_across_seeds_and_runs(seed):
    day = build_fixture("normal_office_day")
    p1, _ = schedule_for_day(day, default_config(), seed=seed)
    p2, _ = schedule_for_day(day, default_config(), seed=seed)
    assert [p.prompt_time for p in p1] == [p.prompt_time for p in p2]
    assert [p.prompt_id for p in p1] == [p.prompt_id for p in p2]
