"""Schedule auditor tests: VALID vs NEEDS_REPAIR with explicit reasons, read-only."""

from __future__ import annotations

import pytest

from paper3_ema.audit import audit_schedule, summarise_audit
from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.vocab import AuditStatus


def _codes(result):
    return [issue.code for issue in result.issues]


def test_generated_schedule_is_valid():
    day = build_fixture("normal_office_day")
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    result = audit_schedule(day, prompts, default_config())
    assert result.status == AuditStatus.VALID
    assert result.valid
    assert result.metrics["prompt_count"] == 5


def test_wrong_count_is_flagged():
    day = build_fixture("normal_office_day")
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    result = audit_schedule(day, prompts[:4], default_config())
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "prompt_count" in _codes(result)


def test_prompt_during_sleep_is_flagged():
    day = build_fixture("normal_office_day")
    # 23:30 is inside the sleep episode 23:00-23:59
    result = audit_schedule(day, ["09:00", "11:00", "13:00", "15:00", "23:30"], default_config())
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "excluded_context" in _codes(result)


def test_prompt_during_cycling_is_flagged():
    day = build_fixture("cycling_commuter_day")
    result = audit_schedule(day, ["08:00", "11:00", "13:00", "16:00", "18:00"], default_config())  # 08:00 is mid-commute cycling
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "excluded_context" in _codes(result)


def test_clustering_is_flagged():
    day = build_fixture("normal_office_day")
    result = audit_schedule(day, ["09:00", "09:10", "12:00", "15:00", "19:00"], default_config())
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "prompt_clustering" in _codes(result)


def test_insufficient_spread_is_flagged():
    # five prompts packed into two daytime windows (30-min gaps respected)
    day = build_fixture("no_eligible_event_day")
    result = audit_schedule(day, ["09:00", "09:40", "10:20", "11:00", "11:40"], default_config())
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "insufficient_spread_windows" in _codes(result)


def test_too_many_event_prompts_is_flagged():
    day = build_fixture("normal_office_day")
    metadata = [
        {"trigger": "post_trip", "event_id": "evt-trip-jn-office-am", "journey_id": "jn-office-am"},
        {"trigger": "post_trip", "event_id": "evt-trip-jn-office-pm", "journey_id": "jn-office-pm"},
        {"trigger": "post_trip", "event_id": "evt-trip-jn-office-am", "journey_id": "jn-office-am"},
        {}, {},
    ]
    result = audit_schedule(day, ["09:00", "11:00", "13:00", "15:00", "19:00"], default_config(),
                            prompt_metadata=metadata)
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "too_many_event_prompts" in _codes(result)


def test_fabricated_event_category_is_flagged():
    """A day with no eligible events may not carry event-enriched prompts."""
    day = build_fixture("no_eligible_event_day")
    metadata = [{"trigger": "post_trip", "journey_id": "jn-office-am"}] + [{}] * 4
    result = audit_schedule(day, ["09:00", "11:00", "13:00", "15:00", "19:00"], default_config(),
                            prompt_metadata=metadata)
    assert result.status == AuditStatus.NEEDS_REPAIR
    codes = _codes(result)
    assert "event_without_detected_event" in codes


def test_invalid_episode_linkage_is_flagged():
    day = build_fixture("normal_office_day")
    metadata = [{}] * 4 + [{"episode_id": "ep-does-not-exist"}]
    result = audit_schedule(day, ["09:00", "11:00", "13:00", "15:00", "19:00"], default_config(),
                            prompt_metadata=metadata)
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "invalid_episode_linkage" in _codes(result)


def test_prompt_before_event_end_is_flagged():
    day = build_fixture("normal_office_day")
    # the AM journey ends 08:20; a post_trip prompt at 08:10 precedes it
    metadata = [{"trigger": "post_trip", "event_id": "evt-trip-jn-office-am", "journey_id": "jn-office-am"}] + [{}] * 4
    result = audit_schedule(day, ["08:10", "11:00", "13:00", "15:00", "19:00"], default_config(),
                            prompt_metadata=metadata)
    assert result.status == AuditStatus.NEEDS_REPAIR
    assert "prompt_before_event_end" in _codes(result)


def test_auditor_is_read_only():
    day = build_fixture("normal_office_day")
    before = day.canonical_json()
    audit_schedule(day, ["09:00", "11:00", "13:00", "15:00", "19:00"], default_config())
    audit_schedule(day, ["23:30", "23:31"], default_config())
    assert day.canonical_json() == before


def test_summarise_audit_contains_reasons():
    day = build_fixture("normal_office_day")
    result = audit_schedule(day, ["09:00", "11:00", "13:00", "15:00", "23:30"], default_config())
    text = summarise_audit(result)
    assert "NEEDS_REPAIR" in text
    assert "excluded_context" in text


def test_generated_schedules_are_audit_valid_across_fixtures():
    for name in ("normal_office_day", "cycling_commuter_day", "public_transport_commuter_day",
                 "no_journeys_day", "exercise_day", "mostly_home_day", "no_eligible_event_day",
                 "evening_shift_day", "unresolved_movement_day", "highly_fragmented_day"):
        day = build_fixture(name)
        prompts, _ = schedule_for_day(day, default_config(), seed=7)
        result = audit_schedule(day, prompts, default_config())
        assert result.valid, f"{name}: {result.reasons}"
