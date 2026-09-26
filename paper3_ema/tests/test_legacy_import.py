"""Legacy adapter: the historical EMA-Diary-Generation diaries import cleanly."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paper3_ema.legacy import diary_to_day, load_historical_diary
from paper3_ema.pipeline import generate_ema

# Resolved relative to this checkout: tests/ -> paper3_ema/ -> repo root.
# (Was previously a hard-coded sandbox path, which silently skipped these
# tests on any other machine — fixed after the 2026-09-24 live run.)
HISTORICAL_OUTPUTS = Path(__file__).resolve().parents[2] / "EMA-Diary-Generation" / "output"


def test_historical_outputs_path_is_checkout_relative():
    """Regression: the path must be derived from the checkout, never hard-coded
    to a specific machine (the 2026-09-24 live run was skipped on foreign
    checkouts because of a hard-coded /home/user/temp path)."""
    expected = Path(__file__).resolve().parents[2] / "EMA-Diary-Generation" / "output"
    assert HISTORICAL_OUTPUTS == expected
    # the definition itself must not embed a machine-specific absolute path
    definition = [line for line in Path(__file__).read_text(encoding="utf-8").splitlines()
                  if "HISTORICAL_OUTPUTS =" in line]
    assert definition, "HISTORICAL_OUTPUTS definition not found"
    for line in definition:
        assert '"/home/' not in line and "'/home/" not in line, (
            f"machine-specific hard-coded path in definition: {line!r}"
        )
    # in this checkout the historical outputs exist, so the tests below must run
    assert expected.exists(), f"historical outputs missing from checkout: {expected}"


@pytest.mark.skipif(not HISTORICAL_OUTPUTS.exists(), reason="historical outputs not in this checkout")
def test_historical_test_run_diary_imports():
    path = HISTORICAL_OUTPUTS / "test_run_output.json"
    day = load_historical_diary(str(path), participant_id="legacy-erik", day="2026-04-07")
    assert len(day.episodes) > 10
    # proper names must not survive into the day's place labels
    dump = json.dumps(day.to_dict()).lower()
    for name in ("ntnu", "realfagbygget", "singsaker", "nidelva", "byparken", "elgeseter"):
        assert name not in dump, f"proper name {name!r} leaked into imported day"
    # device wear schedule is inherited, not fabricated
    assert len(day.device_wear) == 4
    assert any(wp.status.value == "not_worn" for wp in day.device_wear)


@pytest.mark.skipif(not HISTORICAL_OUTPUTS.exists(), reason="historical outputs not in this checkout")
def test_historical_week_diary_imports_and_generates_ema():
    path = HISTORICAL_OUTPUTS / "week_diary_output.json"
    data = json.loads(path.read_text())
    week = data["week"]
    assert len(week) == 7
    first = week[0]
    day = load_historical_diary(str(path), participant_id="legacy-week")
    # the importer accepts the wrapper shape; the day must be usable end-to-end
    bundle = generate_ema(day, seed=3)
    assert len(bundle.records) == 5
    assert bundle.validation.valid


def test_diary_to_day_tolerates_wrapped_and_bare_shapes():
    bare = {
        "episodes": [
            {"start_time": "07:00", "end_time": "09:00", "primary_activity": "cycling",
             "domain": "transport", "location_type": "street", "social_context": "alone",
             "indoor_outdoor": "outdoor", "purpose": "commute"},
            {"start_time": "09:00", "end_time": "17:00", "primary_activity": "sitting",
             "domain": "work", "location_type": "work_office", "social_context": "with_colleagues",
             "indoor_outdoor": "indoor", "purpose": "work"},
        ],
        "device_wear_schedule": [{"start": "07:00", "end": "17:00", "status": "worn"}],
    }
    day = diary_to_day(bare, participant_id="x", day="2026-05-04")
    assert day.episodes[0].activity.value == "cycling"
    assert day.episodes[0].place_type.value == "street"
    # wrapper shape with JSON-string diary
    wrapper = {"persona": {"name": "Someone"}, "diary": json.dumps(bare)}
    day2 = diary_to_day(wrapper, day="2026-05-04")
    assert day2.participant_id == "someone"
    assert len(day2.episodes) == len(day.episodes)
