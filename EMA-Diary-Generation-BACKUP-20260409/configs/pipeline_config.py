"""
Configuration for the EMA Diary Generation Pipeline.

All hyperparameters, prompt templates, and constraint definitions in one place.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PersonaConfig:
    """Controls persona generation."""
    default_city: str = "Copenhagen"
    age_range: tuple = (22, 65)
    include_health_notes: bool = True
    include_personality_traits: bool = True
    num_hobbies_range: tuple = (1, 4)


@dataclass
class RoutineConfig:
    """Controls routine template generation."""
    weekday_variability: float = 0.2  # 20% of routine can vary day-to-day
    weekend_differs_from_weekday: bool = True
    include_flexible_blocks: bool = True  # unscheduled time in the day


@dataclass
class DiaryConfig:
    """Controls daily diary generation."""
    num_days: int = 7
    min_episodes_per_day: int = 10
    max_episodes_per_day: int = 25
    max_gap_between_episodes_min: int = 5
    include_affect: bool = True
    include_fatigue: bool = True
    include_pain: bool = False
    anomaly_probability: float = 0.15  # chance of unusual day
    device_wear_rate: float = 0.95  # 95% of waking hours device is worn


@dataclass
class EMAConfig:
    """Controls EMA probe generation.

    Based on EMA literature best practices:
    - 4-6 prompts/day is the sustainable sweet spot
    - ±15min is the standard alignment window
    - Response lag of 0.5-5min is typical (right-skewed)
    - 10-20% missing rate is realistic
    """
    prompt_type: str = "random_signal"  # random_signal, event_triggered, hybrid
    prompts_per_day: int = 6
    waking_start: str = "07:00"
    waking_end: str = "23:00"
    min_gap_between_prompts_min: int = 60
    response_window_sec: int = 300  # 5 minutes
    max_response_lag_min: float = 15.0
    lag_distribution: str = "right_skewed"  # most responses are quick
    missingness_rate: float = 0.15
    missingness_bias: str = "mvpa_correlated"  # miss more during activity
    recall_window: str = "current"  # current, past_15min, past_30min

    # Standing underreporting (from EMA literature)
    standing_report_rate: float = 0.4  # only 40% of standing is correctly reported
    standing_misreported_as: list = field(default_factory=lambda: ["sitting", "walking"])

    # Sedentary simplification
    sedentary_simplification: bool = True  # "sitting at desk reading email" → "sitting"


@dataclass
class OptimizerConfig:
    """Controls GEPA/GRPO optimization."""
    enable_gepa: bool = True
    enable_grpo: bool = True
    gepa_max_iterations: int = 10
    gepa_target_reward: float = 0.85
    grpo_group_size: int = 4
    grpo_iterations: int = 5
    run_gepa_first: bool = True  # coarse prompt optimization before fine-tuning


@dataclass
class CoherenceConfig:
    """Controls coherence auditing."""
    max_refine_iterations: int = 3
    temporal_weight: float = 0.25
    spatial_weight: float = 0.20
    logical_weight: float = 0.25
    social_weight: float = 0.10
    memory_weight: float = 0.20
    min_acceptable_score: float = 0.80


@dataclass
class PipelineConfig:
    """Master configuration."""
    persona: PersonaConfig = field(default_factory=PersonaConfig)
    routine: RoutineConfig = field(default_factory=RoutineConfig)
    diary: DiaryConfig = field(default_factory=DiaryConfig)
    ema: EMAConfig = field(default_factory=EMAConfig)
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    coherence: CoherenceConfig = field(default_factory=CoherenceConfig)

    # LLM settings
    lm_model: str = "openai/gpt-4o-mini"
    lm_temperature: float = 0.7
    lm_max_tokens: int = 4096

    # Output settings
    output_dir: str = "./output"
    save_intermediate: bool = True
    output_format: str = "json"  # json, csv, parquet


# ──────────────────────────────────────────────────────────────────────
# Persona Templates (seed descriptions for generation)
# ──────────────────────────────────────────────────────────────────────

PERSONA_TEMPLATES = [
    {
        "name": "Copenhagen Commuter",
        "description": "30-35yo professional, works in office 3-4 days/week, "
                       "cycles to work, lives with partner in Nørrebro, "
                       "moderate fitness, goes to gym 2x/week"
    },
    {
        "name": "Remote Worker",
        "description": "28-32yo software developer, works from home most days, "
                       "lives alone in Vesterbro, walks for exercise, "
                       "low-moderate fitness, social on weekends"
    },
    {
        "name": "Student",
        "description": "22-25yo university student, lives in shared apartment, "
                       "cycles everywhere, active social life, "
                       "irregular schedule, high fitness"
    },
    {
        "name": "Parent",
        "description": "38-42yo working parent, 2 children, drives to work, "
                       "busy household, limited exercise time, "
                       "moderate fitness, family activities on weekends"
    },
    {
        "name": "Older Active Adult",
        "description": "60-65yo semi-retired, walks daily, volunteers 2 days/week, "
                       "lives with partner in Østerbro, "
                       "mild knee pain, active social life"
    },
    {
        "name": "Shift Worker",
        "description": "35-40yo healthcare worker, rotating shifts, "
                       "drives to hospital, irregular sleep pattern, "
                       "trains when possible, lives with family"
    },
]


# ──────────────────────────────────────────────────────────────────────
# Prompt Templates (base instructions for each pipeline stage)
# ──────────────────────────────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "persona_system": """You are generating a realistic synthetic person for a physical 
activity research study. The person must be specific enough to determine 
realistic daily patterns, commute behaviour, work schedule, social life, 
and health constraints. Ground everything in the specified city with real 
geography and plausible routines.""",

    "routine_system": """You are generating a weekly routine template for a synthetic 
person. The routine captures habitual patterns while leaving room for 
daily variation. Consider the person's occupation, commute, fitness 
habits, social life, and health. Real life isn't perfectly routine -- 
build in natural flexibility.""",

    "diary_system": """You are generating a realistic single day's diary for a synthetic 
person. Each episode must have complete EMA-relevant fields: activity type, 
domain (work/leisure/transport/household), purpose, specific location, 
social context, and a brief narrative.

CRITICAL REQUIREMENTS:
1. Temporal continuity: no gaps >5 minutes, no overlaps
2. Every episode has: primary_activity, domain, purpose, specific_location, 
   location_type, indoor_outdoor, social_context, narrative
3. Reference previous days' events for memory consistency
4. Include natural variations from routine (real life is messy)
5. If the person has physical discomfort, social commitments, or work stress 
   from previous days, carry those forward naturally""",

    "ema_system": """You are generating EMA (Ecological Momentary Assessment) prompt 
responses based on a ground-truth diary.

RECALL BIAS RULES (from EMA literature):
- Standing is UNDERREPORTED (only ~40% correctly reported; often mislabeled 
  as sitting or walking)
- Sedentary activities are SIMPLIFIED ("sitting at desk reading email" → "sitting")
- People report COARSE categories, not fine-grained details
- Social context is usually reported ACCURATELY
- Location is reported GENERICALLY ("work" not "3rd floor meeting room B")
- Response LAG means the activity may have changed between prompt and answer
- Some prompts are MISSED entirely (10-20%), especially during vigorous 
  activity, driving, or social situations""",

    "audit_system": """You are auditing a synthetic diary for coherence. Check:
1. TEMPORAL: No overlaps, no gaps >5min
2. SPATIAL: Transit time between locations is feasible (walking ~5km/h, 
   cycling ~15km/h)
3. LOGICAL: Activity-domain-location combinations make sense
4. SOCIAL: Social context is plausible for activity/location
5. MEMORY: References to previous days are consistent
Be precise and constructive.""",

    "memory_system": """You are generating cross-day memory threads that create 
narrative consistency across multiple days of a synthetic diary.

Memory threads are causal chains that span days:
- Physical: "Tuesday gym → Wednesday soreness → Thursday easy day"
- Social: "Wednesday dinner plans → Thursday actual dinner → Friday hangover"
- Work: "Monday deadline announced → building stress → Friday submission"
- Weather: "Wednesday rain → indoor day → Thursday catch-up outdoor activities"
- Health: "Monday mild cold → Tuesday worse → Wednesday rest day → Thursday recovery"

These threads make the diary feel like a REAL PERSON'S LIFE, not disconnected 
random days. Each thread should have a natural arc with onset, development, 
and resolution.""",
}
