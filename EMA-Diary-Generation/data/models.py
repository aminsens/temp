"""
Core data models for synthetic EMA diary generation.

These models encode everything the EMA literature says a good diary should contain,
structured so that DSPy can reason about them as typed inputs/outputs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Optional
import json
import uuid


# ──────────────────────────────────────────────────────────────────────
# Enumerations (constrained vocabularies from EMA literature)
# ──────────────────────────────────────────────────────────────────────

class ActivityType(str, Enum):
    """What the person is physically doing."""
    SITTING = "sitting"
    STANDING = "standing"
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    LYING = "lying"
    TRANSITION = "transition"  # brief posture change


class Domain(str, Enum):
    """Why the behaviour is happening - the single most undercollected EMA variable."""
    WORK = "work"
    LEISURE = "leisure"
    TRANSPORT = "transport"
    HOUSEHOLD = "household"
    SELF_CARE = "self_care"
    SOCIAL = "social"
    EXERCISE = "exercise"


class LocationType(str, Enum):
    """Where the behaviour occurs."""
    HOME = "home"
    WORK_OFFICE = "work_office"
    WORK_OUTDOOR = "work_outdoor"
    GYM = "gym"
    PARK = "park"
    SHOPPING = "shopping"
    RESTAURANT = "restaurant"
    TRANSIT_VEHICLE = "transit_vehicle"
    TRANSIT_STOP = "transit_stop"
    STREET = "street"
    SCHOOL = "school"
    MEDICAL = "medical"
    OUTDOOR_GENERAL = "outdoor_general"
    INDOOR_OTHER = "indoor_other"
    FRIEND_HOME = "friend_home"


class SocialContext(str, Enum):
    """Who the person is with."""
    ALONE = "alone"
    WITH_PARTNER = "with_partner"
    WITH_FAMILY = "with_family"
    WITH_FRIENDS = "with_friends"
    WITH_COLLEAGUES = "with_colleagues"
    WITH_STRANGERS = "with_strangers"
    WITH_CHILDREN = "with_children"


class AffectValence(str, Enum):
    """Positive/negative emotional valence."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class AffectArousal(str, Enum):
    """High/low energy arousal."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FatigueLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"
    EXHAUSTED = "exhausted"


class DeviceWearStatus(str, Enum):
    """Whether the accelerometer is being worn - shockingly undercollected in real EMA."""
    WORN = "worn"
    NOT_WORN = "not_worn"
    PARTIALLY_WORN = "partially_worn"  # e.g., removed for shower then put back


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class EMAPromptType(str, Enum):
    """How the EMA prompt was triggered."""
    RANDOM_SIGNAL = "random_signal"           # time-based random
    EVENT_TRIGGERED = "event_triggered"        # sensor-informed
    HYBRID_RANDOM = "hybrid_random"            # part of hybrid design
    HYBRID_EVENT = "hybrid_event"              # part of hybrid design
    END_OF_DAY = "end_of_day"                  # retrospective


class IndoorOutdoor(str, Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIXED = "mixed"  # e.g., market with open air section


# ──────────────────────────────────────────────────────────────────────
# Core Data Models
# ──────────────────────────────────────────────────────────────────────

@dataclass
class Persona:
    """A synthetic person with stable characteristics that shape their diary."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    age: int = 30
    gender: str = ""
    occupation: str = ""
    city: str = "Copenhagen"
    living_situation: str = ""          # "lives alone", "with partner", "with family"
    has_children: bool = False
    has_car: bool = False
    has_bike: bool = True
    fitness_level: str = "moderate"     # low, moderate, high
    work_schedule: str = "standard"     # standard, flexible, shift, remote
    commute_mode: str = "cycling"       # walking, cycling, driving, transit, mixed
    commute_duration_min: int = 20
    hobbies: list[str] = field(default_factory=list)
    personality_traits: list[str] = field(default_factory=list)
    health_notes: str = ""              # "mild knee pain", "healthy", etc.
    typical_sleep_time: str = "23:00"
    typical_wake_time: str = "07:00"

    def to_prompt_context(self) -> str:
        """Condensed persona for LLM prompting."""
        return (
            f"{self.name}, {self.age}yo {self.gender}, {self.occupation}. "
            f"Lives: {self.living_situation}. City: {self.city}. "
            f"Commute: {self.commute_mode} ({self.commute_duration_min}min). "
            f"Fitness: {self.fitness_level}. Work: {self.work_schedule}. "
            f"Bike: {self.has_bike}, Car: {self.has_car}. "
            f"Health: {self.health_notes or 'healthy'}. "
            f"Sleep: {self.typical_sleep_time}-{self.typical_wake_time}. "
            f"Hobbies: {', '.join(self.hobbies) if self.hobbies else 'none specified'}. "
            f"Personality: {', '.join(self.personality_traits) if self.personality_traits else 'none specified'}."
        )


@dataclass
class Episode:
    """
    A single behavioural episode in the diary.
    
    This is the atomic unit of the diary. Each episode has:
    - Temporal boundaries (when it starts/ends)
    - Physical behaviour (what activity, what intensity)
    - Semantic meaning (why, where, with whom)
    - Subjective state (how the person feels)
    
    The EMA literature says these are the variables that matter most,
    ordered by scientific value:
    1. Activity type
    2. Domain (work/leisure/transport/household)
    3. Location
    4. Social context
    5. Purpose/intention
    6. Affect
    7. Fatigue
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    start_time: str = ""            # "08:15"
    end_time: str = ""              # "08:35"
    duration_min: float = 0.0

    # Physical behaviour
    primary_activity: ActivityType = ActivityType.SITTING
    secondary_activities: list[ActivityType] = field(default_factory=list)
    activity_description: str = ""  # "cycling to work along the harbour"

    # Semantic meaning (the gap accelerometers cannot fill)
    domain: Domain = Domain.TRANSPORT
    purpose: str = ""               # "commute to office", "recreational exercise"
    specific_location: str = ""     # "Nørrebrogade bike lane", "home desk"
    location_type: LocationType = LocationType.HOME
    indoor_outdoor: IndoorOutdoor = IndoorOutdoor.INDOOR

    # Social
    social_context: SocialContext = SocialContext.ALONE
    social_detail: str = ""         # "cycling with colleague Morten"

    # Subjective state (configurable - some studies want this, some don't)
    affect_valence: Optional[AffectValence] = None
    affect_arousal: Optional[AffectArousal] = None
    fatigue: Optional[FatigueLevel] = None
    pain_level: Optional[int] = None  # 0-10

    # Narrative (for memory-consistent recall generation)
    narrative: str = ""             # "Woke up a bit groggy, made coffee, checked email"
    mood_narrative: str = ""        # "Feeling okay but slightly anxious about the 10am meeting"

    # Memory anchors (for cross-day consistency)
    references_previous: list[str] = field(default_factory=list)  # episode IDs from past days
    is_routine: bool = True         # habitual vs unusual episode

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_min": self.duration_min,
            "primary_activity": self.primary_activity.value,
            "domain": self.domain.value,
            "purpose": self.purpose,
            "specific_location": self.specific_location,
            "location_type": self.location_type.value,
            "indoor_outdoor": self.indoor_outdoor.value,
            "social_context": self.social_context.value,
            "social_detail": self.social_detail,
            "activity_description": self.activity_description,
            "narrative": self.narrative,
            "is_routine": self.is_routine,
        }
        if self.affect_valence:
            d["affect_valence"] = self.affect_valence.value
        if self.affect_arousal:
            d["affect_arousal"] = self.affect_arousal.value
        if self.fatigue:
            d["fatigue"] = self.fatigue.value
        if self.pain_level is not None:
            d["pain_level"] = self.pain_level
        if self.secondary_activities:
            d["secondary_activities"] = [a.value for a in self.secondary_activities]
        return d


@dataclass
class DailyDiary:
    """A complete day of episodes for one persona."""
    persona_id: str = ""
    date: str = ""                  # "2026-04-07"
    day_of_week: DayOfWeek = DayOfWeek.MONDAY
    episodes: list[Episode] = field(default_factory=list)
    device_wear_schedule: list[dict] = field(default_factory=list)
    # e.g., [{"start": "07:00", "end": "07:15", "status": "not_worn"}, ...]
    daily_narrative: str = ""       # "A fairly normal Monday. Had a busy morning at work..."
    is_typical_day: bool = True
    anomalies: list[str] = field(default_factory=list)
    # e.g., ["left phone at home 10-12", "gym session skipped due to rain"]

    def get_episode_at(self, time_str: str) -> Optional[Episode]:
        """Find which episode is active at a given time."""
        for ep in self.episodes:
            if ep.start_time <= time_str < ep.end_time:
                return ep
        return None

    def validate_temporal_coverage(self) -> list[str]:
        """Check for gaps or overlaps in the timeline."""
        issues = []
        sorted_eps = sorted(self.episodes, key=lambda e: e.start_time)
        for i in range(1, len(sorted_eps)):
            prev_end = sorted_eps[i-1].end_time
            curr_start = sorted_eps[i].start_time
            if curr_start < prev_end:
                issues.append(
                    f"OVERLAP: {sorted_eps[i-1].activity_description} "
                    f"(ends {prev_end}) overlaps with "
                    f"{sorted_eps[i].activity_description} (starts {curr_start})"
                )
            gap = self._time_diff_min(prev_end, curr_start)
            if gap > 5:
                issues.append(
                    f"GAP: {gap}min gap between "
                    f"{sorted_eps[i-1].activity_description} and "
                    f"{sorted_eps[i].activity_description}"
                )
        return issues

    @staticmethod
    def _time_diff_min(t1: str, t2: str) -> float:
        h1, m1 = map(int, t1.split(":"))
        h2, m2 = map(int, t2.split(":"))
        return (h2 * 60 + m2) - (h1 * 60 + m1)


@dataclass
class EMAProbe:
    """
    A single EMA prompt and its response.
    
    This captures:
    - When the prompt was sent (prompt_time)
    - When the person responded (response_time) 
    - The lag between them (response_lag_min)
    - What was actually happening at prompt time (ground truth)
    - What the person reported (self-report, subject to recall/demarcation)
    - Whether the response matches ground truth (for quality analysis)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    prompt_time: str = ""           # "10:23"
    response_time: str = ""         # "10:27"
    response_lag_min: float = 0.0
    prompt_type: EMAPromptType = EMAPromptType.RANDOM_SIGNAL

    # Ground truth (from diary) at prompt_time
    gt_activity: ActivityType = ActivityType.SITTING
    gt_domain: Domain = Domain.WORK
    gt_location_type: LocationType = LocationType.WORK_OFFICE
    gt_social: SocialContext = SocialContext.ALONE
    gt_specific_location: str = ""
    gt_is_wearing_device: bool = True

    # What the person self-reports (may differ due to recall, lag, demarcation)
    reported_activity: ActivityType = ActivityType.SITTING
    reported_domain: Domain = Domain.WORK
    reported_location: str = ""
    reported_social: SocialContext = SocialContext.ALONE
    reported_affect_valence: Optional[AffectValence] = None
    reported_affect_arousal: Optional[AffectArousal] = None
    reported_fatigue: Optional[FatigueLevel] = None

    # Recall window used (what the EMA question asked about)
    recall_window: str = "current"  # "current", "past_15min", "past_30min", "past_2hr"

    # Accuracy metrics
    activity_matches_gt: bool = True
    domain_matches_gt: bool = True
    demarcation_episodes: list[str] = field(default_factory=list)
    # sub-activities within the recall window

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prompt_time": self.prompt_time,
            "response_time": self.response_time,
            "response_lag_min": self.response_lag_min,
            "prompt_type": self.prompt_type.value,
            "recall_window": self.recall_window,
            "gt_activity": self.gt_activity.value,
            "gt_domain": self.gt_domain.value,
            "gt_location_type": self.gt_location_type.value,
            "gt_social": self.gt_social.value,
            "gt_specific_location": self.gt_specific_location,
            "gt_is_wearing_device": self.gt_is_wearing_device,
            "reported_activity": self.reported_activity.value,
            "reported_domain": self.reported_domain.value,
            "reported_location": self.reported_location,
            "reported_social": self.reported_social.value,
            "activity_matches_gt": self.activity_matches_gt,
            "domain_matches_gt": self.domain_matches_gt,
            "demarcation_episodes": self.demarcation_episodes,
        }


@dataclass
class EMASchedule:
    """Configuration for how EMA prompts are distributed."""
    prompt_type: EMAPromptType = EMAPromptType.RANDOM_SIGNAL
    prompts_per_day: int = 6
    waking_start: str = "07:00"
    waking_end: str = "23:00"
    min_gap_between_prompts_min: int = 60
    response_window_sec: int = 300       # 5 min before timeout
    max_lag_min: float = 15.0            # max simulated response delay
    lag_distribution: str = "right_skewed"  # most responses are quick
    missingness_rate: float = 0.15       # 15% prompts unanswered
    missingness_bias: str = "mvpa_correlated"  # missing when active
    recall_window: str = "current"       # what the EMA asks about


@dataclass
class WeekDiary:
    """A complete week of diaries for one persona."""
    persona: Persona = field(default_factory=Persona)
    days: list[DailyDiary] = field(default_factory=list)
    ema_schedule: EMASchedule = field(default_factory=EMASchedule)
    ema_probes: list[EMAProbe] = field(default_factory=list)
    weekly_narrative: str = ""
    memory_threads: list[dict] = field(default_factory=list)
    # cross-day consistency anchors: [{"day": 1, "episode_id": "...", 
    #  "memory": "still sore from Monday's run", "affects_days": [2,3]}]

    def all_episodes(self) -> list[Episode]:
        return [ep for day in self.days for ep in day.episodes]

    def validate_cross_day_consistency(self) -> list[str]:
        """Check that day-to-day narratives are coherent."""
        issues = []
        # Check sleep/wake times are consistent
        for i in range(1, len(self.days)):
            prev_last = self.days[i-1].episodes[-1] if self.days[i-1].episodes else None
            curr_first = self.days[i].episodes[0] if self.days[i].episodes else None
            if prev_last and curr_first:
                if prev_last.primary_activity != ActivityType.LYING:
                    issues.append(
                        f"Day {i}: Previous day doesn't end with sleep episode"
                    )
        return issues
