"""
DSPy Signatures for EMA Diary Generation.

Each signature defines a clear input/output contract.
These are the "what" -- the modules (in modules/) define the "how".
"""

import dspy


class PersonaGenSignature(dspy.Signature):
    """Generate a richly detailed synthetic persona for diary generation.

    The persona must be specific enough to determine realistic daily patterns,
    commute behaviour, work schedule, social life, and health constraints.
    Ground the persona in a real city with real geography.
    """
    persona_description: str = dspy.InputField(
        desc="Brief constraints: age range, occupation type, city, living situation"
    )
    persona: str = dspy.OutputField(
        desc="Detailed JSON persona with name, age, gender, occupation, city, "
             "living_situation, commute_mode, commute_duration, hobbies, "
             "personality_traits, health_notes, sleep_schedule, fitness_level"
    )


class RoutineGenSignature(dspy.Signature):
    """Generate a weekly routine template from a persona.

    The routine is a TEMPLATE, not a fixed schedule. It captures habitual patterns
    (wake time, commute, work hours, typical evening) while leaving room for
    daily variation. Must be grounded in the persona's real constraints.
    """
    persona: str = dspy.InputField(desc="Full persona JSON")
    previous_routine: str = dspy.InputField(
        desc="Previous routine template if refining, or 'none' for first generation"
    )
    routine: str = dspy.OutputField(
        desc="Weekly routine template as JSON with weekday_pattern, "
             "weekend_pattern, fixed_commitments, flexible_blocks, "
             "typical_activities_by_domain"
    )


class DailyDiaryGenSignature(dspy.Signature):
    """Generate a single day's diary from routine + persona + memory.

    CRITICAL: Each episode must have ALL of these fields:
    - start_time, end_time (HH:MM, no overlaps)
    - primary_activity (sitting/standing/walking/running/cycling/lying)
    - domain (work/leisure/transport/household/exercise/social/self_care)
    - purpose (why: "commute to office", "recreational run", "desk work")
    - specific_location (where exactly: "Nørrebrogade bike lane")
    - location_type (home/work_office/gym/park/street/etc)
    - indoor_outdoor (indoor/outdoor/mixed)
    - social_context (alone/with_partner/with_family/with_friends/with_colleagues)
    - narrative (brief natural description of what happened)

    The day must be temporally continuous (no gaps >5min, no overlaps).
    If something unusual happened (late wake, skipped gym, social event),
    generate it naturally -- real life isn't perfectly routine.
    """
    persona: str = dspy.InputField(desc="Full persona JSON")
    routine: str = dspy.InputField(desc="Weekly routine template JSON")
    day_number: str = dspy.InputField(desc="Day number (1-7) and day of week")
    previous_days_summary: str = dspy.InputField(
        desc="Summary of what happened on previous days for memory consistency. "
             "Include fatigue accumulation, events that carry over, "
             "social commitments that reference earlier days. "
             "Or 'none' for day 1."
    )
    memory_threads: str = dspy.InputField(
        desc="Active memory threads: ongoing situations that span days. "
             "e.g., 'still sore from Monday run', 'big presentation on Wednesday', "
             "'friend visiting Thursday-Saturday'"
    )
    daily_diary: str = dspy.OutputField(
        desc="Complete day diary as JSON with: date, day_of_week, "
             "episodes (array of episode objects with all required fields), "
             "device_wear_schedule, daily_narrative, is_typical_day, anomalies. "
             "Episodes must cover the full waking day with no gaps >5min."
    )


class EMAProbeGenSignature(dspy.Signature):
    """Generate EMA prompt responses given the ground-truth diary.

    For each prompt time, simulate:
    1. What is ACTUALLY happening (from diary - ground truth)
    2. What the person REPORTS (subject to recall bias, lag, demarcation error)
    3. The response lag (how late they answer)

    The self-report should be realistic:
    - "current" recall: report what they're doing RIGHT NOW
    - "past_15min" recall: may blend multiple sub-activities into one label
    - People report COARSE categories, not fine-grained details
    - Standing is underreported (cognitively backgrounded)
    - Sedentary activities are simplified ("sitting" not "sitting at desk reading email")
    - Response lag means the activity may have changed between prompt and answer
    """
    diary: str = dspy.InputField(desc="Complete daily diary JSON")
    ema_schedule_config: str = dspy.InputField(
        desc="EMA schedule: prompt_type, prompts_per_day, recall_window, "
             "max_lag, missingness_rate, missingness_bias"
    )
    prompt_times: str = dspy.InputField(
        desc="Pre-computed prompt times for this day (HH:MM array)"
    )
    ema_probes: str = dspy.OutputField(
        desc="Array of EMA probe objects, each with: prompt_time, response_time, "
             "response_lag_min, prompt_type, gt_activity, gt_domain, gt_location_type, "
             "gt_social, gt_specific_location, gt_is_wearing_device, "
             "reported_activity, reported_domain, reported_location, reported_social, "
             "reported_affect_valence, reported_fatigue, recall_window, "
             "activity_matches_gt, domain_matches_gt, demarcation_episodes. "
             "Include a null entry with 'missed': true for missed prompts."
    )


class MemoryThreadGenSignature(dspy.Signature):
    """Generate cross-day memory threads for multi-day consistency.

    Memory threads are narrative arcs that span multiple days:
    - Physical: "left knee started hurting on Tuesday, still sore Thursday"
    - Social: "met friend for dinner Wednesday, texted about weekend plans"
    - Work: "big deadline Friday, increasingly stressed all week"
    - Planning: "ordered groceries Tuesday, delivered Wednesday"
    - Weather: "rainy Wednesday, skipped cycling"

    These threads ensure the diary feels like a REAL PERSON'S life,
    not disconnected random days.
    """
    persona: str = dspy.InputField(desc="Full persona JSON")
    num_days: str = dspy.InputField(desc="Number of days to generate threads for")
    previous_threads: str = dspy.InputField(
        desc="Memory threads from any prior generation, or 'none'"
    )
    memory_threads: str = dspy.OutputField(
        desc="JSON array of memory threads, each with: thread_type "
             "(physical/social/work/planning/weather/health), "
             "description, starts_day, affects_days (array), "
             "influence_on_episodes (how it changes diary content), "
             "resolution_day (when it resolves, or null)"
    )


class CoherenceAuditSignature(dspy.Signature):
    """Audit a diary for temporal, spatial, and logical coherence.

    Check for:
    1. TEMPORAL: No overlaps, no gaps >5min, episodes in correct order
    2. SPATIAL: Transit time between locations is feasible
    3. LOGICAL: Activity-domain-location combinations make sense
    4. SOCIAL: Social context is plausible for the activity/location
    5. MEMORY: References to previous days are consistent
    6. WEAR: Device wear periods don't overlap with activity reporting

    For each issue found, provide: severity (error/warning), description,
    affected_episode_ids, and suggested_fix.
    """
    daily_diary: str = dspy.InputField(desc="Complete daily diary JSON")
    persona: str = dspy.InputField(desc="Full persona JSON")
    previous_days: str = dspy.InputField(
        desc="Previous days' diaries for cross-day consistency check"
    )
    audit_report: str = dspy.OutputField(
        desc="JSON audit report with: overall_score (0-1), "
             "temporal_issues, spatial_issues, logical_issues, social_issues, "
             "memory_issues, wear_issues. Each issue: {severity, description, "
             "episode_ids, suggested_fix}. If no issues, return empty arrays."
    )


class EpisodeRefineSignature(dspy.Signature):
    """Refine specific episodes based on coherence audit feedback.

    Given identified issues, fix the episodes while preserving as much
    of the original content as possible. Changes should be minimal
    and targeted -- don't regenerate the whole day.
    """
    daily_diary: str = dspy.InputField(desc="Current daily diary JSON with issues")
    audit_report: str = dspy.InputField(desc="Coherence audit report JSON")
    persona: str = dspy.InputField(desc="Full persona JSON")
    refined_diary: str = dspy.OutputField(
        desc="Corrected daily diary JSON. Include a 'refinements_made' field "
             "listing what was changed and why."
    )


class DaySummarySignature(dspy.Signature):
    """Summarize a completed daily diary for use as memory in future days.

    Extract the key events, emotional state, fatigue level, and any
    carry-over effects that should influence tomorrow's diary.
    """
    daily_diary: str = dspy.InputField(desc="Complete daily diary JSON")
    persona: str = dspy.InputField(desc="Full persona JSON")
    day_summary: str = dspy.OutputField(
        desc="Concise summary as JSON with: key_events, emotional_trajectory, "
             "fatigue_end_of_day, physical_soreness, social_commitments_created, "
             "carryover_to_tomorrow (what affects next day), "
             "memory_anchors (specific things to remember)"
    )
