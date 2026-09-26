"""Input day import: tolerance, defaults, and refusal to fabricate."""

from __future__ import annotations

import pytest

from paper3_ema.config import default_config
from paper3_ema.day import (
    ContextualDay,
    DayImportError,
    contextual_day_from_mapping,
    default_waking_windows,
    validate_day_input,
)
from paper3_ema.vocab import DeviceWear


def _minimal_day(**overrides):
    base = {
        "participant_id": "p1",
        "date": "2026-05-04",
        "episodes": [
            {"start": "08:00", "end": "23:00", "activity": "sitting", "domain": "leisure", "location_type": "home"},
        ],
    }
    base.update(overrides)
    return base


def test_minimal_day_imports_with_default_windows():
    day = contextual_day_from_mapping(_minimal_day())
    assert isinstance(day, ContextualDay)
    assert len(day.waking_windows) == 8
    assert day.waking_windows[0].start == 8 * 60
    assert day.waking_windows[-1].end == 23 * 60


def test_host_supplied_windows_are_respected():
    day = contextual_day_from_mapping(
        _minimal_day(
            waking_windows=[
                {"start": "08:00", "end": "12:00", "label": "am"},
                {"start": "13:00", "end": "22:00", "label": "pm"},
            ]
        )
    )
    assert [w.label for w in day.waking_windows] == ["am", "pm"]


def test_alias_field_names_are_accepted():
    day = contextual_day_from_mapping(
        {
            "pid": "alias",
            "day_date": "2026-05-04",
            "activities": [
                {"start_time": "08:00", "end_time": "09:00", "primary_activity": "cycling",
                 "behavioural_domain": "transport", "location": "street", "company": "alone"},
            ],
        }
    )
    assert day.participant_id == "alias"
    assert day.episodes[0].activity.value == "cycling"
    assert day.episodes[0].domain.value == "transport"
    assert day.episodes[0].place_type.value == "street"
    assert day.episodes[0].social.value == "alone"


def test_no_wear_is_never_fabricated():
    day = contextual_day_from_mapping(_minimal_day())
    assert day.device_wear == ()
    assert day.wear_status_at(10 * 60) is None


def test_wear_is_inherited_verbatim():
    day = contextual_day_from_mapping(
        _minimal_day(device_wear=[{"start": "09:00", "end": "10:00", "status": "not_worn", "reason": "shower"}])
    )
    assert day.wear_status_at(9.5 * 60) == DeviceWear.NOT_WORN
    assert day.wear_status_at(12 * 60) is None  # outside any supplied period


def test_empty_day_is_refused():
    with pytest.raises(DayImportError):
        contextual_day_from_mapping({"participant_id": "x", "date": "2026-05-04"})


def test_unknown_activity_becomes_none_not_invented():
    day = contextual_day_from_mapping(
        {"participant_id": "x", "date": "2026-05-04",
         "episodes": [{"start": "08:00", "end": "09:00", "activity": "underwater_basket_weaving"}]}
    )
    assert day.episodes[0].activity is None


def test_overlapping_day_reports_diagnostics():
    day = contextual_day_from_mapping(
        {"participant_id": "x", "date": "2026-05-04",
         "episodes": [
             {"start": "08:00", "end": "10:00", "activity": "sitting", "domain": "leisure"},
             {"start": "09:00", "end": "11:00", "activity": "sitting", "domain": "leisure"},
         ]}
    )
    assert any("overlap" in issue for issue in validate_day_input(day))


def test_default_windows_are_configurable():
    windows = default_waking_windows(default_config())
    assert len(windows) == 8
