"""Prompt-time eligibility: exclusions, stability and candidate minutes.

Paper 3 exclusion rule (evidence: ``Gemini.md`` line 158 — delivery must be
delayed during high-intensity exercise, cycling or driving; synthesis §7.2 on
non-random missingness; §10.2 UNDERRATED #4 on demarcation uncertainty):

a prompt may never be delivered while the synthetic participant is

* asleep (or in a sleep period),
* driving,
* cycling,
* running / actively exercising,
* inside a non-realised movement,
* inside an unresolved interval,
* inside an unstable micro-transition,

and — as a Paper 3 engineering rule — within ``stability_margin_minutes`` of an
episode boundary, so that the contextual reference time is unambiguous.

For an eligible event (travel, exercise) the prompt is placed **after** the
event at the first suitable stable opportunity, and context is always resolved
at the **prompt** time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from .config import ProtocolConfig, default_config
from .models import ContextualDay, EpisodeRef, IntervalRef
from .timeutil import Interval, format_hhmm, merge
from .vocab import Activity, VIGOROUS_ACTIVITIES

DAY_MINUTES = 24 * 60


@dataclass(frozen=True)
class Exclusion:
    """Why a minute is not a legal prompt time."""

    excluded: bool
    reasons: tuple[str, ...] = ()

    def __bool__(self) -> bool:  # pragma: no cover - convenience
        return self.excluded


NO_EXCLUSION = Exclusion(False, ())


@dataclass
class DayEligibility:
    """Pre-computed minute-level eligibility for one supplied day."""

    day: ContextualDay
    config: ProtocolConfig
    sleep_periods: tuple[Interval, ...] = ()
    blocked_periods: tuple[Interval, ...] = ()
    unstable_periods: tuple[Interval, ...] = ()
    _exclusion_reasons: list[tuple[str, ...]] = field(default_factory=list)
    _stable: list[bool] = field(default_factory=list)
    _relaxed_stable: list[bool] = field(default_factory=list)
    _relaxed_reasons: list[tuple[str, ...]] = field(default_factory=list)
    capped_margin_episodes: list[tuple[str, float, float]] = field(default_factory=list)

    # -- construction ------------------------------------------------------
    @classmethod
    def build(cls, day: ContextualDay, config: Optional[ProtocolConfig] = None) -> "DayEligibility":
        config = config or default_config()
        eligibility = cls(day=day, config=config)
        eligibility.sleep_periods = eligibility._resolve_sleep_periods()
        eligibility.blocked_periods = eligibility._resolve_blocked_periods()
        eligibility.unstable_periods = eligibility._resolve_unstable_periods()
        eligibility._precompute()
        return eligibility

    # -- rule sources ------------------------------------------------------
    def _excluded_activities(self) -> set[Activity]:
        raw = self.config.get("eligibility.exclude_activities", []) or []
        activities: set[Activity] = set()
        for item in raw:
            try:
                activities.add(Activity(str(item)))
            except ValueError:
                continue
        # Paper 3 hard exclusions, always present regardless of configuration
        activities |= {Activity.SLEEPING, Activity.DRIVING, Activity.CYCLING, Activity.RUNNING}
        activities |= set(VIGOROUS_ACTIVITIES)
        return activities

    def _resolve_sleep_periods(self) -> tuple[Interval, ...]:
        periods: list[Interval] = []
        if self.config.get("eligibility.exclude_during_sleep_period", True):
            wake, sleep = self.day.wake_min, self.day.sleep_min
            if sleep is not None:
                periods.append(Interval(float(sleep), float(DAY_MINUTES), "sleep_period_evening"))
            if wake is not None and wake > 0:
                periods.append(Interval(0.0, float(wake), "sleep_period_morning"))
        periods.extend(
            ep.interval for ep in self.day.episodes if ep.activity == Activity.SLEEPING
        )
        return tuple(merge(periods))

    def _resolve_blocked_periods(self) -> tuple[Interval, ...]:
        """Periods in which a prompt is excluded by activity or interval state."""
        excluded_activities = self._excluded_activities()
        periods: list[Interval] = []
        for episode in self.day.episodes:
            if episode.activity in excluded_activities:
                periods.append(Interval(episode.start_min, episode.end_min, f"activity:{episode.activity.value if episode.activity else 'unknown'}"))
            elif episode.activity is None and self.config.get("eligibility.exclude_unknown_activity", True):
                periods.append(Interval(episode.start_min, episode.end_min, "activity:unknown"))
            if not episode.is_realised and self.config.get("eligibility.exclude_non_realised_movements", True):
                periods.append(Interval(episode.start_min, episode.end_min, "non_realised_movement"))
            if episode.is_unstable and self.config.get("eligibility.exclude_unstable_micro_transitions", True):
                periods.append(Interval(episode.start_min, episode.end_min, "unstable_micro_transition"))
            if episode.is_unresolved and self.config.get("eligibility.exclude_unresolved_intervals", True):
                periods.append(Interval(episode.start_min, episode.end_min, "unresolved_episode"))
        for interval in self.day.intervals:
            if not interval.resolved and self.config.get("eligibility.exclude_unresolved_intervals", True):
                periods.append(Interval(interval.start_min, interval.end_min, "unresolved_interval"))
            if not interval.realised and self.config.get("eligibility.exclude_non_realised_movements", True):
                periods.append(Interval(interval.start_min, interval.end_min, "non_realised_interval"))
            if interval.is_unstable and self.config.get("eligibility.exclude_unstable_micro_transitions", True):
                periods.append(Interval(interval.start_min, interval.end_min, "unstable_interval"))
        for journey in self.day.journeys:
            mode = (journey.mode or "").lower()
            if mode in {"car", "driving", "drive", "motorbike", "motorcycle", "bus", "train", "tram", "metro", "subway", "bike", "bicycle", "cycling"}:
                periods.append(Interval(journey.start_min, journey.end_min, f"journey_mode:{mode or 'unknown'}"))
        return tuple(merge(periods))

    def _resolve_unstable_periods(self) -> tuple[Interval, ...]:
        """Periods too close to a contextual transition to be a stable prompt time.

        Paper 3 rule: a prompt must sit at least ``stability_margin_minutes``
        away from an episode boundary, so that the contextual reference time is
        unambiguous.  For episodes shorter than twice the margin the *effective*
        margin is capped at half the episode length (a bounded micro-transition
        is still protected, but a short episode does not become unpromptable).
        This is a Paper 3 engineering rule (class C).
        """
        margin = float(self.config.get("sampling.stability_margin_minutes", 5))
        adaptive = bool(self.config.get("sampling.adaptive_stability_margin", True))
        periods: list[Interval] = []
        self.capped_margin_episodes = []
        if margin <= 0:
            return ()
        for episode in self.day.episodes:
            effective = margin
            if adaptive and episode.duration_min < 2 * margin:
                effective = episode.duration_min / 2.0
                self.capped_margin_episodes.append(
                    (episode.episode_id, round(episode.duration_min, 1), round(effective, 1))
                )
            if effective <= 0:
                continue
            periods.append(
                Interval(max(0.0, episode.start_min - effective), episode.start_min + effective, "episode_start_margin")
            )
            periods.append(
                Interval(max(0.0, episode.end_min - effective), min(float(DAY_MINUTES), episode.end_min + effective), "episode_end_margin")
            )
        for interval in self.day.intervals:
            if interval.is_unstable:
                periods.append(Interval(interval.start_min, interval.end_min, "interval_unstable"))
        return tuple(merge(periods))

    def _hard_blocked_periods(self) -> tuple[Interval, ...]:
        """Blocked periods that hold under the *relaxed* stability rule too:
        excluded activities, unknown activity, non-realised movements,
        unresolved intervals/episodes and unstable micro-transitions.  Boundary
        margins are the only thing the relaxed path drops."""
        excluded_activities = self._excluded_activities()
        periods: list[Interval] = []
        for episode in self.day.episodes:
            if episode.activity in excluded_activities:
                periods.append(Interval(episode.start_min, episode.end_min, f"activity:{episode.activity.value if episode.activity else 'unknown'}"))
            elif episode.activity is None and self.config.get("eligibility.exclude_unknown_activity", True):
                periods.append(Interval(episode.start_min, episode.end_min, "activity:unknown"))
            if not episode.is_realised and self.config.get("eligibility.exclude_non_realised_movements", True):
                periods.append(Interval(episode.start_min, episode.end_min, "non_realised_movement"))
            if episode.is_unstable and self.config.get("eligibility.exclude_unstable_micro_transitions", True):
                periods.append(Interval(episode.start_min, episode.end_min, "unstable_micro_transition"))
            if episode.is_unresolved and self.config.get("eligibility.exclude_unresolved_intervals", True):
                periods.append(Interval(episode.start_min, episode.end_min, "unresolved_episode"))
        for interval in self.day.intervals:
            if not interval.resolved and self.config.get("eligibility.exclude_unresolved_intervals", True):
                periods.append(Interval(interval.start_min, interval.end_min, "unresolved_interval"))
            if not interval.realised and self.config.get("eligibility.exclude_non_realised_movements", True):
                periods.append(Interval(interval.start_min, interval.end_min, "non_realised_interval"))
            if interval.is_unstable and self.config.get("eligibility.exclude_unstable_micro_transitions", True):
                periods.append(Interval(interval.start_min, interval.end_min, "unstable_interval"))
        for journey in self.day.journeys:
            mode = (journey.mode or "").lower()
            if mode in {"car", "driving", "drive", "motorbike", "motorcycle", "bus", "train", "tram", "metro", "subway", "bike", "bicycle", "cycling"}:
                periods.append(Interval(journey.start_min, journey.end_min, f"journey_mode:{mode or 'unknown'}"))
        return tuple(merge(periods))

    # -- minute level ------------------------------------------------------
    def _precompute(self) -> None:
        excluded_activities = self._excluded_activities()
        require_coverage = bool(self.config.get("eligibility.require_episode_coverage", True))
        reasons: list[tuple[str, ...]] = []
        stable: list[bool] = []
        episodes = self.day.episodes
        for minute in range(DAY_MINUTES + 1):
            found: list[str] = []
            for period in self.sleep_periods:
                if period.contains(minute):
                    found.append("asleep")
                    break
            if not found:
                for period in self.blocked_periods:
                    if period.contains(minute):
                        found.append(period.label or "blocked")
                        break
            if not found and require_coverage:
                episode = _episode_at(episodes, minute)
                if episode is None:
                    found.append("uncovered_time")
                elif episode.activity in excluded_activities:
                    found.append(f"activity:{episode.activity.value if episode.activity else 'unknown'}")
                elif episode.activity is None and self.config.get("eligibility.exclude_unknown_activity", True):
                    found.append("activity:unknown")
            if not found:
                for period in self.unstable_periods:
                    if period.contains(minute):
                        found.append("unstable_micro_transition")
                        break
            reasons.append(tuple(found))
            stable.append(not found)
        relaxed: list[bool] = []
        relaxed_reasons: list[tuple[str, ...]] = []
        for minute in range(DAY_MINUTES + 1):
            found: list[str] = []
            for period in self.sleep_periods:
                if period.contains(minute):
                    found.append("asleep")
                    break
            if not found:
                for period in self._hard_blocked_periods():
                    if period.contains(minute):
                        found.append(period.label or "blocked")
                        break
            if not found and require_coverage:
                episode = _episode_at(episodes, minute)
                if episode is None:
                    found.append("uncovered_time")
                elif episode.activity in excluded_activities:
                    found.append(f"activity:{episode.activity.value if episode.activity else 'unknown'}")
                elif episode.activity is None and self.config.get("eligibility.exclude_unknown_activity", True):
                    found.append("activity:unknown")
                elif episode.is_unstable or episode.is_unresolved or not episode.is_realised:
                    found.append("episode_unstable_or_unresolved")
            if not found:
                for interval in self.day.intervals:
                    if interval.start_min <= minute < interval.end_min:
                        if not interval.resolved or not interval.realised or interval.is_unstable:
                            found.append("interval_unstable_or_unresolved")
                        break
            relaxed_reasons.append(tuple(found))
            relaxed.append(not found)
        self._exclusion_reasons = reasons
        self._stable = stable
        self._relaxed_stable = relaxed
        self._relaxed_reasons = relaxed_reasons

    # -- queries -----------------------------------------------------------
    def exclusion_at(self, minute: float) -> Exclusion:
        index = int(minute)
        index = max(0, min(DAY_MINUTES, index))
        reasons = self._exclusion_reasons[index]
        return Exclusion(bool(reasons), reasons)

    def is_excluded(self, minute: float) -> bool:
        return bool(self.exclusion_at(minute).reasons)

    def is_stable(self, minute: float) -> bool:
        index = max(0, min(DAY_MINUTES, int(minute)))
        return self._stable[index]

    def first_stable_minute(
        self,
        earliest: float,
        latest: Optional[float] = None,
        window: Optional[Interval] = None,
    ) -> Optional[int]:
        """First eligible, stable minute at or after ``earliest``."""
        start = max(0, int(round(earliest)))
        end = DAY_MINUTES if latest is None else min(DAY_MINUTES, int(round(latest)))
        if window is not None:
            start = max(start, int(round(window.start)))
            end = min(end, int(round(window.end)))
        for minute in range(start, end + 1):
            if self._stable[minute]:
                return minute
        return None

    def relaxed_exclusion_at(self, minute: float) -> Exclusion:
        index = max(0, min(DAY_MINUTES, int(minute)))
        reasons = self._relaxed_reasons[index]
        return Exclusion(bool(reasons), reasons)

    def is_relaxed_stable(self, minute: float) -> bool:
        index = max(0, min(DAY_MINUTES, int(minute)))
        return self._relaxed_stable[index]

    def first_relaxed_stable_minute(
        self,
        earliest: float,
        latest: Optional[float] = None,
    ) -> Optional[int]:
        start = max(0, int(round(earliest)))
        end = DAY_MINUTES if latest is None else min(DAY_MINUTES, int(round(latest)))
        for minute in range(start, end + 1):
            if self._relaxed_stable[minute]:
                return minute
        return None

    def relaxed_stable_minutes(self, window: Interval, step: int = 1) -> list[int]:
        start = max(0, int(window.start))
        end = min(DAY_MINUTES, int(window.end) + 1)
        return [
            minute
            for minute in range(start, end, max(1, step))
            if window.contains(minute) and self._relaxed_stable[minute]
        ]

    def stable_minutes(self, window: Interval, step: int = 1) -> list[int]:
        start = max(0, int(window.start))
        end = min(DAY_MINUTES, int(window.end) + 1)
        return [
            minute
            for minute in range(start, end, max(1, step))
            if window.contains(minute) and self._stable[minute]
        ]

    def episode_at(self, minute: float) -> Optional[EpisodeRef]:
        return _episode_at(self.day.episodes, minute)

    def interval_at(self, minute: float) -> Optional[IntervalRef]:
        return self.day.interval_at(minute)

    def reason_summary(self) -> dict[str, float]:
        """Minutes of the day excluded by each reason (diagnostics)."""
        summary: dict[str, float] = {}
        for reasons in self._exclusion_reasons:
            for reason in reasons:
                summary[reason] = summary.get(reason, 0.0) + 1.0
        return {key: value for key, value in sorted(summary.items(), key=lambda kv: -kv[1])}


def _episode_at(episodes: Sequence[EpisodeRef], minute: float) -> Optional[EpisodeRef]:
    for episode in episodes:
        if episode.start_min <= minute < episode.end_min:
            return episode
    if episodes:
        last = episodes[-1]
        if minute >= last.end_min and minute - last.end_min < 1e-9:
            return last
    return None


def candidate_minutes(
    eligibility: DayEligibility,
    window: Interval,
    step: Optional[int] = None,
) -> list[int]:
    """All legal prompt minutes inside ``window``."""
    step = int(step or eligibility.config.get("sampling.candidate_step_minutes", 1))
    limit = int(eligibility.config.get("sampling.max_candidates_per_window", 400))
    minutes = eligibility.stable_minutes(window, step=step)
    if len(minutes) > limit:
        stride = -(-len(minutes) // limit)
        minutes = minutes[::stride][:limit]
    return minutes


def describe_exclusion(exclusion: Exclusion, minute: float) -> str:
    if not exclusion.excluded:
        return f"{format_hhmm(minute)}: eligible"
    return f"{format_hhmm(minute)}: excluded ({', '.join(exclusion.reasons)})"


def relaxed_candidate_minutes(
    eligibility: DayEligibility,
    window: Interval,
    step: Optional[int] = None,
) -> list[int]:
    """Fallback candidates for fragmented days: boundary-margin relaxed.

    Only used when the strict rule yields no legal minutes at all.  All
    safety-critical exclusions (sleep, driving/cycling/vigorous activity,
    non-realised movement, unresolved intervals, unstable micro-transitions)
    still apply; only the episode-boundary stability margin is dropped.
    """
    step = int(step or eligibility.config.get("sampling.candidate_step_minutes", 1))
    limit = int(eligibility.config.get("sampling.max_candidates_per_window", 400))
    minutes = eligibility.relaxed_stable_minutes(window, step=step)
    if len(minutes) > limit:
        stride = -(-len(minutes) // limit)
        minutes = minutes[::stride][:limit]
    return minutes
