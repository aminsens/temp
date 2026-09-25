"""Policy regression tests for two demonstrated defects.

Defect 1 - unknown physical posture excluded EMA.
    ``eligibility.exclude_unknown_activity`` made every episode whose posture
    the host could not resolve unpromptable, even when the episode was stable,
    realised and had fully known behavioural context (domain, place, social
    setting).  The rule is a class-C engineering choice, not part of the
    evidence-documented safety exclusion set.

Defect 2 - event detection disagreed with event placement.
    ``events._has_stable_opportunity`` accepted an event when a stable minute
    existed after it, without requiring that minute to fall inside a
    host-declared waking window.  The scheduler *does* require window
    membership (``sampling.waking_windows.require_prompt_inside_window``), so an
    early-morning event was counted as "eligible" and then silently
    unplaceable.  The auditor reads the same detector and reported
    ``event_enrichment_missing`` for a day on which no legal prompt existed.

Both are written to FAIL against the pre-correction configuration and code.
"""

from __future__ import annotations

import copy

import pytest

from paper3_ema import default_config
from paper3_ema.config import ProtocolConfig
from paper3_ema.day import contextual_day_from_mapping
from paper3_ema.eligibility import DayEligibility
from paper3_ema.events import detect_events
from paper3_ema.fixtures import FIXTURE_BUILDERS, episode, interval, journey
from paper3_ema.pipeline import generate_ema
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.vocab import TriggerType


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _legacy_config() -> ProtocolConfig:
    """The pre-correction policy, reconstructed explicitly."""
    data = copy.deepcopy(default_config().to_dict())
    data["eligibility"]["exclude_unknown_activity"] = True
    return ProtocolConfig.from_dict(data)


def _unknown_posture_work_day() -> dict:
    """A stable, realised, fully contextualised weekday with unknown posture.

    ``activity="work"`` deliberately does not resolve to a physical behaviour
    (the vocabulary has no such activity), which is exactly what the Appa
    adapter produces when the frozen physical-state layer refuses a class.
    Domain, place type, social setting and boundaries are all known.
    """
    episodes = [
        episode("00:00", "07:00", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("07:00", "08:00", "sitting", "self_care", "home", "alone", "indoor", purpose="self_care"),
        episode("08:00", "12:00", "work", "work", "workplace", "with_colleagues", "indoor", purpose="work"),
        episode("12:00", "16:00", "work", "work", "workplace", "with_colleagues", "indoor", purpose="work"),
        episode("16:30", "18:00", "sitting", "leisure", "home", "with_family", "indoor", purpose="leisure"),
        episode("18:00", "22:00", "sitting", "leisure", "home", "with_family", "indoor", purpose="leisure"),
        episode("22:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    return {
        "participant_id": "fixture-unknown-posture",
        "date": "2026-06-15",
        "wake_time": "07:00",
        "sleep_time": "22:00",
        "episodes": episodes,
        "intervals": [
            interval("00:00", "07:00", kind="rest"),
            interval("07:00", "08:00", kind="sedentary"),
            interval("08:00", "12:00", kind="sedentary"),
            interval("12:00", "16:00", kind="sedentary"),
            interval("16:30", "18:00", kind="sedentary"),
            interval("18:00", "22:00", kind="sedentary"),
            interval("22:00", "23:59", kind="rest"),
        ],
        "journeys": [journey("16:00", "16:30", "walk", journey_id="j-walk")],
        "fixed_commitments": [],
    }


def _early_journey_day() -> dict:
    """A day whose only journey ends well before the first waking window.

    With the default 08:00-23:00 strata a journey ending 06:40 has no legal
    post-event prompt minute: the 45-minute horizon expires at 07:25, before
    any window opens.  A single stable cushion episode spans 06:40-08:00 so the
    minutes after the journey ARE stable -- which is exactly why the old
    stability-only screen accepted the event.

    Every waking episode is deliberately identical in domain, place, social
    setting and environment, so no *late* transition event is generated that
    would mask the defect by being legally placeable.
    """
    episodes = [
        episode("00:00", "06:00", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("06:20", "06:40", "walking", "transport", "street", "alone", "outdoor", purpose="commute"),
        episode("06:40", "08:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure"),
        episode("08:00", "12:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure"),
        episode("12:00", "22:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure"),
        episode("22:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    return {
        "participant_id": "fixture-early-journey",
        "date": "2026-06-16",
        "wake_time": "06:00",
        "sleep_time": "22:00",
        "episodes": episodes,
        "intervals": [
            interval("00:00", "06:00", kind="rest"),
            interval("06:20", "06:40", kind="active"),
            interval("06:40", "08:00", kind="sedentary"),
            interval("08:00", "12:00", kind="sedentary"),
            interval("12:00", "22:00", kind="sedentary"),
            interval("22:00", "23:59", kind="rest"),
        ],
        "journeys": [journey("06:20", "06:40", "walk", journey_id="j-early")],
        "fixed_commitments": [],
    }


# ==========================================================================
# DEFECT 1 - unknown physical posture must not, by itself, exclude a prompt
# ==========================================================================

def test_unknown_posture_is_not_excluded_by_default():
    config = default_config()
    day = contextual_day_from_mapping(_unknown_posture_work_day(), config)
    eligibility = DayEligibility.build(day, config)

    assert day.episode_at(600).activity is None, "fixture must have an unknown posture"
    assert day.episode_at(600).domain is not None, "fixture must have a known domain"

    exclusion = eligibility.exclusion_at(600)
    assert not exclusion.excluded, f"unknown posture alone must not exclude: {exclusion.reasons}"
    assert "activity:unknown" not in exclusion.reasons


def test_legacy_unknown_posture_rule_is_reproducible_but_non_default():
    legacy = _legacy_config()
    assert legacy.get("eligibility.exclude_unknown_activity") is True
    day = contextual_day_from_mapping(_unknown_posture_work_day(), legacy)
    eligibility = DayEligibility.build(day, legacy)
    assert eligibility.exclusion_at(600).excluded
    assert "activity:unknown" in eligibility.exclusion_at(600).reasons


def test_prompts_may_land_in_an_unknown_posture_episode():
    config = default_config()
    day = contextual_day_from_mapping(_unknown_posture_work_day(), config)
    bundle = generate_ema(day, seed=3, llm_client=None, allow_llm=False)

    assert bundle.validation.status == "PASS"
    assert len(bundle.records) == config.get("sampling.opportunities_per_day")
    unknown = [r for r in bundle.records if r.packet.activity is None]
    assert unknown, "at least one prompt must sit in an unknown-posture episode"
    for record in unknown:
        assert record.prompt.inherited_context["activity"] is None


def test_unknown_posture_does_not_fabricate_a_physical_state():
    config = default_config()
    day = contextual_day_from_mapping(_unknown_posture_work_day(), config)
    bundle = generate_ema(day, seed=3, llm_client=None, allow_llm=False)
    for record in bundle.records:
        assert record.packet.activity is None or record.packet.activity.value != "unknown"
        assert record.prompt.inherited_context["domain"] in {"work", "leisure", "self_care"}


def test_sleep_is_still_excluded():
    config = default_config()
    day = contextual_day_from_mapping(_unknown_posture_work_day(), config)
    eligibility = DayEligibility.build(day, config)
    exclusion = eligibility.exclusion_at(120)
    assert exclusion.excluded
    assert any("sleep" in r for r in exclusion.reasons)


def test_all_safety_exclusions_are_still_enforced():
    """Cycling, driving, running, sleep, unresolved, non-realised, unstable.

    Each sensitive episode is separated from the next by a gap so that adjacent
    exclusion periods are not merged (a merge keeps the first period's label,
    which would make the reported reason imprecise).  Each probe minute sits
    mid-episode, clear of the +/-5 minute boundary margins.
    """
    episodes = [
        episode("00:00", "06:30", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
        episode("06:40", "07:00", "cycling", "transport", "street", "alone", "outdoor", purpose="commute"),
        episode("07:10", "07:30", "driving", "transport", "street", "alone", "vehicle", purpose="commute"),
        episode("07:40", "08:10", "running", "exercise", "park", "alone", "outdoor", purpose="exercise"),
        episode("08:20", "08:50", "walking", "transport", "street", "alone", "outdoor", is_realised=False),
        episode("09:00", "09:30", "work", "work", "workplace", "alone", "indoor", stability="unresolved"),
        episode("09:40", "10:10", "sitting", "leisure", "home", "alone", "indoor", stability="unstable"),
        episode("10:20", "22:00", "sitting", "leisure", "home", "alone", "indoor", purpose="leisure"),
        episode("22:00", "23:59", "sleeping", "self_care", "home", "alone", "indoor", purpose="sleep"),
    ]
    mapping = {
        "participant_id": "fixture-safety",
        "date": "2026-06-17",
        "wake_time": "06:30",
        "sleep_time": "22:00",
        "episodes": episodes,
        "intervals": [interval(str(e["start_time"]), str(e["end_time"])) for e in episodes],
        "journeys": [
            journey("06:40", "07:00", "bike", journey_id="j-bike"),
            journey("07:10", "07:30", "car", journey_id="j-car"),
        ],
        "fixed_commitments": [],
    }
    config = default_config()
    day = contextual_day_from_mapping(mapping, config)
    eligibility = DayEligibility.build(day, config)

    checks = {
        60: "sleep",
        410: "activity:cycling",
        440: "driving",
        470: "running",
        510: "non_realised",
        550: "unresolved",
        590: "unstable",
    }
    for minute, expected in checks.items():
        exclusion = eligibility.exclusion_at(minute)
        assert exclusion.excluded, f"minute {minute} must stay excluded"
        assert any(expected in reason for reason in exclusion.reasons), (
            f"minute {minute}: expected {expected!r} in {exclusion.reasons}"
        )


# ==========================================================================
# DEFECT 2 - detection must agree with placement about "eligible"
# ==========================================================================

def test_an_event_before_the_first_window_is_not_reported_as_eligible():
    config = default_config()
    day = contextual_day_from_mapping(_early_journey_day(), config)
    eligibility = DayEligibility.build(day, config)

    window_start = min(w.start for w in day.waking_windows)
    horizon = float(config.get("sampling.max_minutes_after_event", 45))
    assert 40 + horizon < window_start, "fixture must place the journey outside every window"

    events = detect_events(day, eligibility, config)
    assert not [e for e in events if e.journey_id == "j-early"], (
        "a journey with no window-legal post-event minute must not be reported as eligible"
    )


def test_early_event_does_not_trigger_a_false_audit_error():
    config = default_config()
    day = contextual_day_from_mapping(_early_journey_day(), config)
    bundle = generate_ema(day, seed=1, llm_client=None, allow_llm=False)
    codes = {i.code for i in bundle.validation.issues}
    assert "audit.event_enrichment_missing" not in codes
    assert "audit.event_without_detected_event" not in codes


def test_every_detected_event_has_a_window_legal_stable_minute():
    """The invariant whose violation caused the false audit error."""
    config = default_config()
    horizon = float(config.get("sampling.max_minutes_after_event", 45))

    days = [(name, builder()) for name, builder in sorted(FIXTURE_BUILDERS.items())]
    days.append(("unknown_posture_work_day", _unknown_posture_work_day()))
    days.append(("early_journey_day", _early_journey_day()))

    checked = 0
    for name, mapping in days:
        day = contextual_day_from_mapping(mapping, config)
        eligibility = DayEligibility.build(day, config)
        for event in detect_events(day, eligibility, config):
            checked += 1
            deadline = min(1440.0, event.end_min + horizon)
            legal = [
                minute
                for window in day.waking_windows
                for minute in range(
                    int(round(max(event.end_min, window.start))),
                    int(round(min(deadline, window.end - 1))) + 1,
                )
                if window.contains(float(minute)) and eligibility.is_stable(minute)
            ]
            assert legal, (
                f"{name}: event {event.event_id} ({event.kind.value}) is reported as "
                f"eligible but has no stable minute inside a waking window within "
                f"{horizon:.0f} min of its end ({event.end_min:.0f})"
            )
    assert checked > 0, "the invariant must be exercised against real fixture events"


def test_the_first_detected_event_is_always_placeable():
    """Detection accepted implies the scheduler places at least one event prompt."""
    config = default_config()
    for name, builder in sorted(FIXTURE_BUILDERS.items()):
        day = contextual_day_from_mapping(builder(), config)
        eligibility = DayEligibility.build(day, config)
        events = detect_events(day, eligibility, config)
        if not events:
            continue
        prompts, _info = schedule_for_day(day, config, 7)
        enriched = [p for p in prompts if p.trigger != TriggerType.SEMI_RANDOM]
        assert enriched, f"{name}: {len(events)} eligible event(s) but nothing was placed"
