"""Scheduler tests: the event-enriched stratified semi-random hybrid."""

from __future__ import annotations

import pytest

from paper3_ema.config import default_config
from paper3_ema.day import contextual_day_from_mapping
from paper3_ema.eligibility import DayEligibility
from paper3_ema.events import detect_events
from paper3_ema.fixtures import FIXTURE_BUILDERS, build_fixture
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.vocab import TriggerType


def _day(name):
    return build_fixture(name)


def test_exactly_five_opportunities():
    for name in FIXTURE_BUILDERS:
        prompts, info = schedule_for_day(_day(name), default_config(), seed=7)
        assert len(prompts) == 5, f"{name}: {len(prompts)} prompts"
        assert info["target"] == 5


def test_background_and_event_bounds():
    for name in FIXTURE_BUILDERS:
        prompts, _ = schedule_for_day(_day(name), default_config(), seed=7)
        background = [p for p in prompts if p.trigger == TriggerType.SEMI_RANDOM]
        events = [p for p in prompts if p.trigger != TriggerType.SEMI_RANDOM]
        assert len(background) >= 3, f"{name}: only {len(background)} background"
        assert len(events) <= 2, f"{name}: {len(events)} event prompts"
        assert len(background) + len(events) == 5


def test_no_prompt_during_excluded_activities():
    config = default_config()
    for name in ("cycling_commuter_day", "evening_shift_day", "exercise_day", "normal_office_day"):
        day = _day(name)
        eligibility = DayEligibility.build(day, config)
        prompts, _ = schedule_for_day(day, config, seed=7)
        for prompt in prompts:
            episode = day.episode_at(prompt.prompt_time_min)
            assert episode.activity.value not in {"sleeping", "driving", "cycling", "running", "other_vigorous"}, (
                f"{name}: prompt during {episode.activity.value}"
            )


def test_no_prompt_inside_unresolved_or_non_realised_movement():
    day = _day("unresolved_movement_day")
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    for prompt in prompts:
        episode = day.episode_at(prompt.prompt_time_min)
        assert episode.is_realised, f"prompt inside non-realised movement at {prompt.prompt_time_min}"
        assert not episode.is_unresolved, f"prompt inside unresolved interval at {prompt.prompt_time_min}"


def test_no_forced_artificial_event_diversity():
    """A day with no eligible event must produce five semi-random prompts only."""
    day = _day("no_eligible_event_day")
    events = detect_events(day, DayEligibility.build(day, default_config()), default_config())
    assert events == []
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    assert all(p.trigger == TriggerType.SEMI_RANDOM for p in prompts)
    assert all(not p.is_event_enriched for p in prompts)


def test_post_trip_prompt_lands_after_the_trip():
    day = _day("normal_office_day")
    prompts, info = schedule_for_day(day, default_config(), seed=7)
    post_trips = [p for p in prompts if p.trigger == TriggerType.POST_TRIP]
    assert post_trips, "expected at least one post_trip prompt"
    journeys = {j.journey_id: j for j in day.journeys}
    for prompt in post_trips:
        if prompt.journey_id:
            journey = journeys[prompt.journey_id]
            assert prompt.prompt_time_min >= journey.end_min
            assert prompt.minutes_after_event is not None
            assert prompt.minutes_after_event <= 45


def test_event_priority_post_trip_beats_post_active():
    day = _day("exercise_day")  # has a run and a gym session (both post_active) plus a walk journey
    config = default_config()
    prompts, _ = schedule_for_day(day, config, seed=7)
    events = [p for p in prompts if p.is_event_enriched]
    kinds = [p.trigger.value for p in events]
    # when both kinds are present, post_trip must occupy a slot
    if "post_active_episode" in kinds:
        assert "post_trip" in kinds


def test_reproducibility_same_seed():
    day = _day("normal_office_day")
    p1, i1 = schedule_for_day(day, default_config(), seed=123)
    p2, i2 = schedule_for_day(day, default_config(), seed=123)
    assert [p.prompt_time for p in p1] == [p.prompt_time for p in p2]
    assert [p.prompt_id for p in p1] == [p.prompt_id for p in p2]
    assert i1["stable_seed"] == i2["stable_seed"]


def test_different_seeds_diverge():
    day = _day("normal_office_day")
    p1, _ = schedule_for_day(day, default_config(), seed=1)
    p2, _ = schedule_for_day(day, default_config(), seed=2)
    assert [p.prompt_time_min for p in p1] != [p.prompt_time_min for p in p2]


def test_prompts_stay_inside_waking_windows():
    day = _day("evening_shift_day")
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    for prompt in prompts:
        assert day.window_of(prompt.prompt_time_min) is not None, (
            f"prompt at {prompt.prompt_time_min} outside every waking window"
        )


def test_prompts_are_spread_across_windows():
    day = _day("normal_office_day")
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    windows = {p.window_index for p in prompts}
    assert len(windows) >= 3


def test_prompts_min_gap_respected():
    day = _day("normal_office_day")
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    times = sorted(p.prompt_time_min for p in prompts)
    for a, b in zip(times, times[1:]):
        assert b - a >= 30


def test_fragmented_day_uses_documented_relaxation():
    day = _day("highly_fragmented_day")
    prompts, info = schedule_for_day(day, default_config(), seed=7)
    assert len(prompts) == 5
    assert info["relaxed_windows"], "expected the fragmented day to report relaxed windows"
    relaxed = [p for p in prompts if p.stability_relaxed]
    assert relaxed, "expected at least one prompt to carry the stability_relaxed marker"
    for prompt in relaxed:
        assert "[stability_relaxed" in prompt.selection_reason
