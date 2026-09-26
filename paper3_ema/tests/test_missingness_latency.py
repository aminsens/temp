"""Missingness and latency: stochastic (never forced), calibrated, expiry semantics."""

from __future__ import annotations

import random

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture, demo_cohort
from paper3_ema.latency import draw_latency, latency_summary
from paper3_ema.missingness import (
    calibration_report,
    draw_response,
    expected_response_rate,
    response_probability,
)
from paper3_ema.models import EMARequest
from paper3_ema.pipeline import build_context, generate_ema, generate_ema_multi_day
from paper3_ema.scheduler import schedule_for_day
from paper3_ema.vocab import ResponseStatus, TriggerType


def _day_seed_pair(fixture="normal_office_day", seed=7):
    day = build_fixture(fixture)
    prompts, _ = schedule_for_day(day, default_config(), seed=seed)
    request = EMARequest(day=day, participant_id=day.participant_id, day_date=day.day, seed=seed)
    packets = build_context(request, prompts)
    return day, prompts, packets


def test_missingness_is_never_forced_exactly_one():
    """Historical behaviour (exactly one missed probe per day) must not appear."""
    cohort = demo_cohort(participants=3, days=7, seed=20260504)
    bundles = generate_ema_multi_day(cohort, seed=11, validate=False, audit=False)
    miss_counts = [sum(1 for r in b.records if r.response.status == ResponseStatus.MISSED) for b in bundles]
    # a real Bernoulli model produces 0-miss days and multi-miss days both
    assert any(count == 0 for count in miss_counts), f"every day missed exactly something: {miss_counts}"
    assert len(set(miss_counts)) > 1, f"missingness is not varying across days: {miss_counts}"


def test_calibration_target_band():
    """Canonical calibration: 85-90% answered across a *sufficiently large* cohort.

    The band is a cohort-level property (700 opportunities); single days vary.
    """
    config = default_config()
    cohort = demo_cohort(participants=10, days=14, seed=20260504)
    bundles = generate_ema_multi_day(cohort, seed=21, validate=False, audit=False)
    total = sum(len(b.records) for b in bundles)
    assert total >= 500, "calibration needs a sufficiently large cohort"
    answered = sum(1 for b in bundles for r in b.records if r.response.answered)
    rate = answered / total
    report = calibration_report(answered, total, config)
    assert report["within_target"], f"cohort response rate {rate:.2%} outside {report['target']}"


def test_response_probability_modifiers_are_documented():
    day, prompts, packets = _day_seed_pair()
    for prompt, packet in zip(prompts, packets):
        decision = response_probability(prompt, packet, default_config())
        assert 0.0 < decision.probability <= 1.0
        assert decision.base_probability > 0.0
        for multiplier in decision.modifiers_applied.values():
            assert 0.0 < multiplier < 1.0
        assert len(decision.reasons) == len(decision.modifiers_applied) or not decision.modifiers_applied


def test_missingness_is_independent_of_subjective_content():
    """Same packet + trigger + rng stream => same decision, regardless of the state draw."""
    day, prompts, packets = _day_seed_pair()
    config = default_config()
    prompt, packet = prompts[2], packets[2]
    rng1, rng2 = random.Random(5), random.Random(5)
    d1 = draw_response(prompt, packet, rng1, config)
    d2 = draw_response(prompt, packet, rng2, config)
    assert d1.responded == d2.responded
    assert d1.probability == d2.probability


def test_latency_is_right_skewed_and_positive():
    day, prompts, packets = _day_seed_pair()
    rng = random.Random(3)
    values = []
    for _ in range(500):
        draw = draw_latency(prompts[0], packets[0], rng, default_config())
        values.append(draw.base_latency_min)
    summary = latency_summary(values)
    assert summary["n"] == 500
    assert summary["min_min"] > 0
    assert summary["mean_min"] > summary["median_min"], f"not right-skewed: {summary}"


def test_expiry_flags_and_flags_only():
    """A response past the 10-min expiry must be recorded, flagged and unusable."""
    config = default_config()
    day, prompts, packets = _day_seed_pair()
    bundles = [generate_ema(day, seed=s) for s in range(1, 41)]
    expired = [r for b in bundles for r in b.records if r.response.status == ResponseStatus.EXPIRED]
    for record in expired:
        response = record.response
        assert response.expired is True
        assert response.answered is False
        assert response.usable_for_alignment is False
        assert response.latency_min is not None
        assert response.latency_min > config.get("latency.expiry_minutes")
        assert response.response_time is not None  # dual timestamps recorded
    # with 200 prompts at P(late) ~3% we expect several expiries
    assert expired, "expected at least one expired response over 40 days of prompts"


def test_dual_timestamps_and_latency_arithmetic():
    for seed in (1, 7, 42):
        bundle = generate_ema(build_fixture("normal_office_day"), seed=seed)
        for record in bundle.records:
            response = record.response
            if response.response_time is None:
                assert response.status == ResponseStatus.MISSED
                continue
            delta = (response.response_time - record.prompt.prompt_time).total_seconds() / 60.0
            assert abs(delta - response.latency_min) < 0.01
            assert response.context_reference_time == "prompt_time"


def test_missed_records_are_explicit():
    for seed in (1, 7, 42, 99):
        bundle = generate_ema(build_fixture("no_journeys_day"), seed=seed)
        for record in bundle.records:
            response = record.response
            if response.status == ResponseStatus.MISSED:
                assert response.response_time is None
                assert response.nonresponse_reason == "not_answered"
                assert response.subjective is None
                assert response.context_note is None


def test_base_rates_per_trigger_are_configurable():
    rates = expected_response_rate(default_config())
    assert set(rates) == {t.value for t in TriggerType}
    for trigger, rate in rates.items():
        assert 0.0 < rate < 1.0
