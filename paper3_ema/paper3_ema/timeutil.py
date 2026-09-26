"""Time helpers for the Paper 3 standalone EMA module.

All times are naive local datetimes anchored to a single calendar day.  The EMA
module never changes time zone and never crosses midnight: an episode that runs
past midnight is clipped to the day and flagged (see
:mod:`paper3_ema.day`).

Design rule (Paper 3): the contextual reference time of an EMA record is always
the *prompt* time, never the response time.  Every helper that resolves context
takes a prompt time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from datetime import datetime, timedelta
from typing import Iterable, Optional, Sequence

MINUTE = timedelta(minutes=1)


# --------------------------------------------------------------------------
# parsing / formatting
# --------------------------------------------------------------------------

def parse_hhmm(value: str) -> int:
    """Parse ``"HH:MM"`` (or ``"HH:MM:SS"``) into minutes after midnight."""
    if value is None:
        raise ValueError("cannot parse None as HH:MM")
    text = str(value).strip()
    parts = text.split(":")
    if len(parts) < 2:
        raise ValueError(f"cannot parse {value!r} as HH:MM")
    hours, minutes = int(parts[0]), int(parts[1])
    seconds = int(parts[2]) if len(parts) > 2 else 0
    total = hours * 60 + minutes + (1 if seconds >= 30 else 0)
    if not 0 <= total <= 24 * 60:
        raise ValueError(f"minute-of-day out of range: {value!r} -> {total}")
    return total


def format_hhmm(minutes: float) -> str:
    """Format minutes after midnight as ``"HH:MM"`` (clamped to the day)."""
    value = int(round(minutes))
    value = max(0, min(24 * 60, value))
    return f"{value // 60:02d}:{value % 60:02d}"


def day_datetime(day: _date | str, minutes: float) -> datetime:
    """Combine a calendar day with minutes-after-midnight."""
    if isinstance(day, str):
        day = _date.fromisoformat(day)
    return datetime(day.year, day.month, day.day) + timedelta(minutes=float(minutes))


def minute_of_day(value: datetime) -> float:
    return value.hour * 60 + value.minute + value.second / 60.0


def to_date(value: _date | str | datetime) -> _date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, _date):
        return value
    return _date.fromisoformat(str(value))


# --------------------------------------------------------------------------
# intervals
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Interval:
    """A half-open interval ``[start, end)`` in minutes after midnight."""

    start: float
    end: float
    label: str = ""

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"interval ends before it starts: {self}")

    @property
    def duration_min(self) -> float:
        return self.end - self.start

    def contains(self, minute: float) -> bool:
        return self.start <= minute < self.end

    def contains_closed(self, minute: float) -> bool:
        return self.start <= minute <= self.end

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end

    def intersection(self, other: "Interval") -> Optional["Interval"]:
        start, end = max(self.start, other.start), min(self.end, other.end)
        if end <= start:
            return None
        return Interval(start, end, self.label or other.label)

    def expanded(self, before: float = 0.0, after: float = 0.0) -> "Interval":
        return Interval(max(0.0, self.start - before), min(24 * 60.0, self.end + after), self.label)

    def as_tuple(self) -> tuple[float, float]:
        return (self.start, self.end)

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.label or 'interval'}[{format_hhmm(self.start)}-{format_hhmm(self.end)}]"


def clip_to_day(start: float, end: float) -> tuple[float, float, bool]:
    """Clip an interval to ``[0, 1440)``.

    Returns ``(start, end, was_clipped)``.  Degenerate results are returned as
    an empty interval at the day boundary.
    """
    clipped = start < 0.0 or end > 24 * 60.0
    start = max(0.0, min(start, 24 * 60.0))
    end = max(0.0, min(end, 24 * 60.0))
    if end < start:
        end = start
    return start, end, clipped


def merge(intervals: Iterable[Interval]) -> list[Interval]:
    """Merge overlapping/adjacent intervals (labels are dropped)."""
    ordered = sorted(intervals, key=lambda iv: (iv.start, iv.end))
    merged: list[Interval] = []
    for iv in ordered:
        if merged and iv.start <= merged[-1].end:
            last = merged[-1]
            merged[-1] = Interval(last.start, max(last.end, iv.end), last.label)
        else:
            merged.append(iv)
    return merged


def total_overlap(intervals: Sequence[Interval], window: Interval) -> float:
    """Minutes of ``window`` covered by any of ``intervals``."""
    inside = [iv for iv in intervals if (part := iv.intersection(window)) is not None]
    if not inside:
        return 0.0
    clipped = [Interval(max(iv.start, window.start), min(iv.end, window.end)) for iv in inside]
    return sum(iv.duration_min for iv in merge(clipped))
