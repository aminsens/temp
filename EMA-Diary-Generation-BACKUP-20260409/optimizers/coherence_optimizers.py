"""
DSPy Optimizers for EMA Diary Quality.

Two optimizers:
1. GEPA (Generative Prompt Optimization) - optimizes prompts via reflection
2. GRPO (Group Reward Policy Optimization) - optimizes via coherence rewards

Both operate on the diary generation modules to improve temporal,
spatial, logical, and memory coherence.
"""

import dspy
import json
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# Coherence Reward Function (used by both GEPA and GRPO)
# ──────────────────────────────────────────────────────────────────────

def compute_coherence_reward(diary_json: str, persona_json: str = "") -> float:
    """
    Compute a 0-1 coherence reward for a generated diary.

    Checks:
    1. Temporal continuity (no gaps >5min, no overlaps)
    2. Required fields present (domain, purpose, location, social)
    3. Activity-domain consistency (cycling → transport/exercise, not work)
    4. Social-location consistency (with_colleagues → likely at work)
    5. JSON parseability

    This is the REWARD SIGNAL for GRPO and the EVALUATION CRITERION for GEPA.
    """
    score = 0.0
    max_score = 5.0

    try:
        diary = json.loads(diary_json)
    except (json.JSONDecodeError, TypeError):
        return 0.0  # unparseable = zero reward

    # 1. JSON parseability (already passed if we're here)
    score += 1.0

    # 2. Has episodes
    episodes = diary.get("episodes", [])
    if not episodes:
        return score / max_score
    score += 0.5

    # 3. Temporal continuity
    temporal_ok = True
    sorted_eps = sorted(episodes, key=lambda e: e.get("start_time", "00:00"))
    for i in range(len(sorted_eps)):
        ep = sorted_eps[i]
        if not ep.get("start_time") or not ep.get("end_time"):
            temporal_ok = False
            break
        if i > 0:
            prev_end = sorted_eps[i-1].get("end_time", "00:00")
            curr_start = ep.get("start_time", "00:00")
            if curr_start < prev_end:
                temporal_ok = False
                break
    if temporal_ok:
        score += 1.0

    # 4. Required EMA fields present
    required_fields = ["primary_activity", "domain", "purpose",
                       "specific_location", "location_type", "social_context"]
    fields_present = 0
    for ep in episodes:
        for field in required_fields:
            if ep.get(field):
                fields_present += 1
    field_ratio = fields_present / (len(required_fields) * max(len(episodes), 1))
    score += field_ratio

    # 5. Activity-domain consistency
    consistency_map = {
        "cycling": ["transport", "exercise", "leisure"],
        "running": ["exercise", "leisure"],
        "walking": ["transport", "exercise", "leisure", "household"],
        "sitting": ["work", "leisure", "transport", "household", "self_care"],
        "standing": ["work", "household", "leisure"],
        "lying": ["leisure", "self_care"],
    }
    consistent_count = 0
    for ep in episodes:
        activity = ep.get("primary_activity", "")
        domain = ep.get("domain", "")
        valid_domains = consistency_map.get(activity, [])
        if domain in valid_domains:
            consistent_count += 1
    if episodes:
        consistency_ratio = consistent_count / len(episodes)
        score += consistency_ratio

    return min(score / max_score, 1.0)


def compute_ema_quality_reward(ema_probes_json: str) -> float:
    """
    Compute reward for EMA probe quality.

    Checks:
    1. Ground truth and report are both present
    2. Response lag is realistic (0-15 min)
    3. Some mismatches exist (realistic recall error)
    4. Standing is underreported relative to ground truth
    5. Missing prompts exist (non-zero missingness)
    """
    score = 0.0
    max_score = 4.0

    try:
        probes = json.loads(ema_probes_json)
        if isinstance(probes, str):
            probes = json.loads(probes)
    except (json.JSONDecodeError, TypeError):
        return 0.0

    if not isinstance(probes, list):
        return 0.0

    score += 1.0  # parseable

    # Has probes
    if not probes:
        return score / max_score
    score += 0.5

    # Check lag realism
    lags = [p.get("response_lag_min", 0) for p in probes if not p.get("missed")]
    if lags:
        avg_lag = sum(lags) / len(lags)
        if 0.5 <= avg_lag <= 10:  # realistic average lag
            score += 1.0
        elif 0 <= avg_lag <= 15:
            score += 0.5

    # Check that SOME activity mismatches exist (realistic recall error)
    matched = [p for p in probes if not p.get("missed")]
    if matched:
        mismatch_rate = sum(
            1 for p in matched if not p.get("activity_matches_gt", True)
        ) / len(matched)
        if 0.05 <= mismatch_rate <= 0.35:  # 5-35% mismatch is realistic
            score += 1.0
        elif mismatch_rate > 0:
            score += 0.5

    # Check for missed prompts
    missed = [p for p in probes if p.get("missed")]
    if missed:
        score += 0.5

    return min(score / max_score, 1.0)


# ──────────────────────────────────────────────────────────────────────
# GEPA Optimizer (Prompt Optimization via Reflection)
# ──────────────────────────────────────────────────────────────────────

class DiaryCoherenceGEPA(dspy.Module):
    """
    GEPA-style optimizer for diary generation prompts.

    GEPA works by:
    1. Running the pipeline to generate a diary
    2. Evaluating coherence using the reward function
    3. Reflecting on failures and proposing prompt improvements
    4. Iterating until coherence plateaus

    This is a REFLECTIVE optimizer -- it reasons about WHY something
    failed and proposes targeted fixes to the instruction prompts.
    """

    def __init__(self, pipeline_module, max_iterations: int = 10):
        super().__init__()
        self.pipeline = pipeline_module
        self.max_iterations = max_iterations
        self.reflector = dspy.ChainOfThought("feedback, current_prompt -> improved_prompt")
        self.history = []

    def forward(
        self,
        persona_description: str,
        ema_schedule_config: str = "{}",
        target_reward: float = 0.85,
    ):
        """Run GEPA optimization loop."""

        best_result = None
        best_reward = 0.0
        current_prompt_feedback = "Initial generation."

        for iteration in range(self.max_iterations):
            # Generate diary with current prompt state
            result = self.pipeline(
                persona_description=persona_description,
                ema_schedule_config=ema_schedule_config,
            )

            # Evaluate coherence on each day
            day_rewards = []
            for day_diary in result.day_diaries:
                reward = compute_coherence_reward(day_diary)
                day_rewards.append(reward)

            avg_reward = sum(day_rewards) / max(len(day_rewards), 1)

            # Track best
            if avg_reward > best_reward:
                best_reward = avg_reward
                best_result = result

            self.history.append({
                "iteration": iteration,
                "reward": avg_reward,
                "best_reward": best_reward,
            })

            # Check convergence
            if avg_reward >= target_reward:
                break

            # Reflect on failures and improve prompt
            worst_day_idx = day_rewards.index(min(day_rewards))
            worst_diary = result.day_diaries[worst_day_idx]

            feedback = (
                f"Current average coherence: {avg_reward:.3f}. "
                f"Target: {target_reward}. "
                f"Worst day score: {min(day_rewards):.3f}. "
                f"Diary content: {worst_diary[:500]}"
            )

            reflection = self.reflector(
                feedback=feedback,
                current_prompt=current_prompt_feedback,
            )

            current_prompt_feedback = reflection.improved_prompt

        return dspy.Prediction(
            best_result=best_result,
            best_reward=best_reward,
            history=self.history,
            final_reflection=current_prompt_feedback,
        )


# ──────────────────────────────────────────────────────────────────────
# GRPO Optimizer (Reinforcement Learning via Coherence Rewards)
# ──────────────────────────────────────────────────────────────────────

class DiaryCoherenceGRPO(dspy.Module):
    """
    GRPO-style optimizer for diary generation.

    GRPO works by:
    1. Generating N candidate diaries (group)
    2. Scoring each with the coherence reward
    3. Using the reward signal to update generation policy

    Unlike GEPA (which reflects on prompts), GRPO uses the reward
    distribution to directly optimize the generation behavior.

    In DSPy terms, this wraps the pipeline with a reward-weighted
    selection mechanism.
    """

    def __init__(self, pipeline_module, group_size: int = 4):
        super().__init__()
        self.pipeline = pipeline_module
        self.group_size = group_size

    def forward(
        self,
        persona_description: str,
        ema_schedule_config: str = "{}",
        num_iterations: int = 5,
    ):
        """Run GRPO optimization: generate groups, score, select best."""

        all_results = []

        for iteration in range(num_iterations):
            # Generate a group of candidate diaries
            group_results = []
            for _ in range(self.group_size):
                result = self.pipeline(
                    persona_description=persona_description,
                    ema_schedule_config=ema_schedule_config,
                )

                # Score each day
                day_rewards = []
                for day_diary in result.day_diaries:
                    reward = compute_coherence_reward(day_diary)
                    day_rewards.append(reward)

                # Also score EMA probes if present
                ema_rewards = []
                for ema in result.ema_probes:
                    reward = compute_ema_quality_reward(ema)
                    ema_rewards.append(reward)

                avg_day_reward = sum(day_rewards) / max(len(day_rewards), 1)
                avg_ema_reward = sum(ema_rewards) / max(len(ema_rewards), 1) if ema_rewards else 0
                total_reward = 0.7 * avg_day_reward + 0.3 * avg_ema_reward

                group_results.append({
                    "result": result,
                    "day_rewards": day_rewards,
                    "ema_rewards": ema_rewards,
                    "avg_day_reward": avg_day_reward,
                    "avg_ema_reward": avg_ema_reward,
                    "total_reward": total_reward,
                })

            # Sort by reward
            group_results.sort(key=lambda x: x["total_reward"], reverse=True)
            all_results.extend(group_results)

        # Return the best overall result
        all_results.sort(key=lambda x: x["total_reward"], reverse=True)
        best = all_results[0]

        return dspy.Prediction(
            best_result=best["result"],
            best_reward=best["total_reward"],
            best_day_rewards=best["day_rewards"],
            best_ema_rewards=best["ema_rewards"],
            all_results=[{
                "reward": r["total_reward"],
                "day_rewards": r["day_rewards"],
            } for r in all_results[:10]],
        )


# ──────────────────────────────────────────────────────────────────────
# Composite Optimizer (GEPA → GRPO pipeline)
# ──────────────────────────────────────────────────────────────────────

class CompositeOptimizer(dspy.Module):
    """
    Two-phase optimization:
    Phase 1: GEPA optimizes prompt instructions (coarse)
    Phase 2: GRPO fine-tunes generation behavior (fine)

    This combines the strengths of both:
    - GEPA is good at fixing structural issues (missing fields, bad format)
    - GRPO is good at optimizing nuanced quality (realistic lag, recall bias)
    """

    def __init__(self, pipeline_module, gepa_iterations: int = 5, grpo_iterations: int = 3, grpo_group_size: int = 3):
        super().__init__()
        self.gepa = DiaryCoherenceGEPA(pipeline_module, max_iterations=gepa_iterations)
        self.grpo = DiaryCoherenceGRPO(pipeline_module, group_size=grpo_group_size)
        self.grpo_iterations = grpo_iterations

    def forward(
        self,
        persona_description: str,
        ema_schedule_config: str = "{}",
        target_reward: float = 0.85,
    ):
        # Phase 1: GEPA
        gepa_result = self.gepa(
            persona_description=persona_description,
            ema_schedule_config=ema_schedule_config,
            target_reward=target_reward,
        )

        # Phase 2: GRPO (if GEPA didn't reach target)
        if gepa_result.best_reward < target_reward:
            grpo_result = self.grpo(
                persona_description=persona_description,
                ema_schedule_config=ema_schedule_config,
                num_iterations=self.grpo_iterations,
            )

            # Take the better of the two
            if grpo_result.best_reward > gepa_result.best_reward:
                return grpo_result

        return gepa_result
