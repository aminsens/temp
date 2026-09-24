"""
DSPy Modules for EMA Diary Generation.

Each module wraps a signature with reasoning strategy (CoT, Pred, etc.)
and can be optimized by GEPA/GRPO.
"""

import dspy
from signatures.diary_signatures import (
    PersonaGenSignature,
    RoutineGenSignature,
    DailyDiaryGenSignature,
    EMAProbeGenSignature,
    MemoryThreadGenSignature,
    CoherenceAuditSignature,
    EpisodeRefineSignature,
    DaySummarySignature,
)


# ──────────────────────────────────────────────────────────────────────
# Stage 1: Persona Generation
# ──────────────────────────────────────────────────────────────────────

class PersonaGenerator(dspy.Module):
    """Generate a detailed synthetic persona.

    Uses CoT to reason about realistic persona constraints before
    producing the structured output.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(PersonaGenSignature)

    def forward(self, persona_description: str):
        return self.generate(persona_description=persona_description)


# ──────────────────────────────────────────────────────────────────────
# Stage 2: Routine Template Generation
# ──────────────────────────────────────────────────────────────────────

class RoutineGenerator(dspy.Module):
    """Generate a weekly routine template from a persona.

    Uses CoT to reason about how the persona's characteristics
    (occupation, commute, fitness, social life) shape their
    typical weekly pattern.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(RoutineGenSignature)

    def forward(self, persona: str, previous_routine: str = "none"):
        return self.generate(
            persona=persona,
            previous_routine=previous_routine,
        )


# ──────────────────────────────────────────────────────────────────────
# Stage 3: Memory Thread Generation
# ──────────────────────────────────────────────────────────────────────

class MemoryThreadGenerator(dspy.Module):
    """Generate cross-day memory threads for narrative consistency.

    This is what makes the diary feel like a REAL PERSON rather than
    independent random days. Memory threads create causal chains:
    "Tuesday gym session → Wednesday muscle soreness → Thursday skipped run"
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(MemoryThreadGenSignature)

    def forward(self, persona: str, num_days: str, previous_threads: str = "none"):
        return self.generate(
            persona=persona,
            num_days=num_days,
            previous_threads=previous_threads,
        )


# ──────────────────────────────────────────────────────────────────────
# Stage 4: Daily Diary Generation (core module)
# ──────────────────────────────────────────────────────────────────────

class DailyDiaryGenerator(dspy.Module):
    """Generate a single day's diary with memory-consistent episodes.

    This is the heart of the pipeline. Uses CoT to:
    1. Review the persona, routine, and previous days
    2. Consider active memory threads
    3. Generate temporally continuous episodes
    4. Ensure each episode has all required EMA variables

    The key innovation: previous_days_summary feeds back into generation,
    creating the "fluid and rooted in memory" quality the user wants.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(DailyDiaryGenSignature)

    def forward(
        self,
        persona: str,
        routine: str,
        day_number: str,
        previous_days_summary: str = "none",
        memory_threads: str = "none",
    ):
        return self.generate(
            persona=persona,
            routine=routine,
            day_number=day_number,
            previous_days_summary=previous_days_summary,
            memory_threads=memory_threads,
        )


# ──────────────────────────────────────────────────────────────────────
# Stage 5: EMA Probe Generation
# ──────────────────────────────────────────────────────────────────────

class EMAProbeGenerator(dspy.Module):
    """Generate EMA prompt responses from ground-truth diary.

    Simulates the gap between ground truth and self-report:
    - Response lag (person answers late)
    - Recall bias (person simplifies what they report)
    - Demarcation error (single label covers multiple sub-activities)
    - Missing prompts (person ignores the notification)

    This module encodes the EMA literature's findings:
    - Standing is underreported
    - Sedentary activities are simplified to "sitting"
    - Social context is usually reported accurately
    - Domain is often not asked about (but we generate it anyway)
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(EMAProbeGenSignature)

    def forward(
        self,
        diary: str,
        ema_schedule_config: str,
        prompt_times: str,
    ):
        return self.generate(
            diary=diary,
            ema_schedule_config=ema_schedule_config,
            prompt_times=prompt_times,
        )


# ──────────────────────────────────────────────────────────────────────
# Stage 6: Coherence Audit
# ──────────────────────────────────────────────────────────────────────

class CoherenceAuditor(dspy.Module):
    """Audit a diary for temporal, spatial, logical, and social coherence.

    Uses Prediction (not CoT) for structured output -- we want a clean
    audit report, not reasoning traces.
    """

    def __init__(self):
        super().__init__()
        self.audit = dspy.Predict(CoherenceAuditSignature)

    def forward(
        self,
        daily_diary: str,
        persona: str,
        previous_days: str = "none",
    ):
        return self.audit(
            daily_diary=daily_diary,
            persona=persona,
            previous_days=previous_days,
        )


# ──────────────────────────────────────────────────────────────────────
# Stage 7: Episode Refinement
# ──────────────────────────────────────────────────────────────────────

class EpisodeRefiner(dspy.Module):
    """Fix coherence issues identified by the auditor.

    Uses CoT to reason about minimal fixes that preserve the
    narrative quality of the diary while resolving temporal,
    spatial, or logical errors.
    """

    def __init__(self):
        super().__init__()
        self.refine = dspy.ChainOfThought(EpisodeRefineSignature)

    def forward(self, daily_diary: str, audit_report: str, persona: str):
        return self.refine(
            daily_diary=daily_diary,
            audit_report=audit_report,
            persona=persona,
        )


# ──────────────────────────────────────────────────────────────────────
# Stage 8: Day Summary (for memory feedback)
# ──────────────────────────────────────────────────────────────────────

class DaySummarizer(dspy.Module):
    """Summarize a day for feeding back into future diary generation.

    This is the MEMORY mechanism. The summary captures:
    - Key events (what happened)
    - Emotional trajectory (how mood shifted)
    - Fatigue state (end-of-day tiredness → affects tomorrow)
    - Carry-over effects (what tomorrow inherits from today)
    """

    def __init__(self):
        super().__init__()
        self.summarize = dspy.ChainOfThought(DaySummarySignature)

    def forward(self, daily_diary: str, persona: str):
        return self.summarize(daily_diary=daily_diary, persona=persona)


# ──────────────────────────────────────────────────────────────────────
# Full Pipeline Orchestrator
# ──────────────────────────────────────────────────────────────────────

class EMADiaryPipeline(dspy.Module):
    """
    Full pipeline: Persona → Routine → MemoryThreads → DailyDiaries → EMAProbes

    Orchestrates the generation of a complete multi-day diary with:
    - Persona-grounded episode generation
    - Memory-consistent cross-day narratives
    - Coherence auditing and refinement
    - EMA probe simulation with realistic recall bias

    Usage:
        pipeline = EMADiaryPipeline(num_days=7, max_refine_iterations=3)
        result = pipeline(
            persona_description="30yo software engineer in Copenhagen, cycles to work"
        )
    """

    def __init__(
        self,
        num_days: int = 7,
        max_refine_iterations: int = 3,
        include_affect: bool = True,
    ):
        super().__init__()
        self.num_days = num_days
        self.max_refine_iterations = max_refine_iterations
        self.include_affect = include_affect

        # Pipeline stages
        self.persona_gen = PersonaGenerator()
        self.routine_gen = RoutineGenerator()
        self.memory_gen = MemoryThreadGenerator()
        self.diary_gen = DailyDiaryGenerator()
        self.ema_gen = EMAProbeGenerator()
        self.auditor = CoherenceAuditor()
        self.refiner = EpisodeRefiner()
        self.summarizer = DaySummarizer()

    def forward(self, persona_description: str, ema_schedule_config: str = "{}"):
        """Run the full pipeline."""

        # Stage 1: Generate persona
        persona_result = self.persona_gen(persona_description=persona_description)
        persona_str = persona_result.persona

        # Stage 2: Generate routine template
        routine_result = self.routine_gen(persona=persona_str)
        routine_str = routine_result.routine

        # Stage 3: Generate memory threads for the full period
        memory_result = self.memory_gen(
            persona=persona_str,
            num_days=str(self.num_days),
        )
        memory_str = memory_result.memory_threads

        # Stage 4-8: Generate each day with memory feedback
        day_diaries = []
        day_summaries = []
        ema_probes_all = []
        previous_summary = "none"

        for day_num in range(1, self.num_days + 1):
            day_of_week = self._day_num_to_weekday(day_num)

            # Generate diary for this day
            diary_result = self.diary_gen(
                persona=persona_str,
                routine=routine_str,
                day_number=f"Day {day_num} ({day_of_week})",
                previous_days_summary=previous_summary,
                memory_threads=memory_str,
            )

            diary_str = diary_result.daily_diary

            # Coherence audit + refinement loop
            for iteration in range(self.max_refine_iterations):
                audit_result = self.auditor(
                    daily_diary=diary_str,
                    persona=persona_str,
                    previous_days=str([d for d in day_summaries]),
                )

                # Check if there are issues to fix
                if self._audit_is_clean(audit_result.audit_report):
                    break

                # Refine
                refine_result = self.refiner(
                    daily_diary=diary_str,
                    audit_report=audit_result.audit_report,
                    persona=persona_str,
                )
                diary_str = refine_result.refined_diary

            # Generate EMA probes for this day
            if ema_schedule_config != "{}":
                prompt_times = self._generate_prompt_times(ema_schedule_config)
                ema_result = self.ema_gen(
                    diary=diary_str,
                    ema_schedule_config=ema_schedule_config,
                    prompt_times=str(prompt_times),
                )
                ema_probes_all.append(ema_result.ema_probes)

            # Summarize for next day's memory
            summary_result = self.summarizer(
                daily_diary=diary_str,
                persona=persona_str,
            )
            day_summaries.append(summary_result.day_summary)
            previous_summary = self._build_running_summary(day_summaries)
            day_diaries.append(diary_str)

        return dspy.Prediction(
            persona=persona_str,
            routine=routine_str,
            memory_threads=memory_str,
            day_diaries=day_diaries,
            ema_probes=ema_probes_all,
            day_summaries=day_summaries,
        )

    def _day_num_to_weekday(self, day_num: int) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]
        return days[(day_num - 1) % 7]

    def _audit_is_clean(self, audit_report: str) -> bool:
        """Check if audit found no issues."""
        # Simple heuristic: if all arrays are empty, it's clean
        return '"temporal_issues": []' in audit_report and \
               '"spatial_issues": []' in audit_report and \
               '"logical_issues": []' in audit_report

    def _build_running_summary(self, summaries: list) -> str:
        """Build a cumulative summary of all previous days."""
        if not summaries:
            return "none"
        combined = []
        for i, s in enumerate(summaries, 1):
            combined.append(f"Day {i}: {s}")
        return "\n".join(combined)

    def _generate_prompt_times(self, config: str) -> list:
        """Generate EMA prompt times based on schedule config."""
        import json
        import random

        try:
            cfg = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            cfg = {}

        n_prompts = cfg.get("prompts_per_day", 6)
        start = cfg.get("waking_start", "07:00")
        end = cfg.get("waking_end", "23:00")
        min_gap = cfg.get("min_gap_between_prompts_min", 60)

        # Parse times
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        start_min = sh * 60 + sm
        end_min = eh * 60 + em

        # Generate evenly-spaced windows with random jitter
        window_size = (end_min - start_min) // n_prompts
        times = []
        for i in range(n_prompts):
            window_start = start_min + i * window_size
            window_end = min(window_start + window_size, end_min)
            t = random.randint(window_start, window_end - 1)
            h, m = divmod(t, 60)
            times.append(f"{h:02d}:{m:02d}")

        return sorted(times)
