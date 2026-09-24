"""
EMA Diary Generation Pipeline - Main Runner

Usage:
    python run_pipeline.py                                    # default: 7 days, Copenhagen commuter
    python run_pipeline.py --persona "student in Copenhagen"  # custom persona
    python run_pipeline.py --config configs/custom.yaml       # custom config
    python run_pipeline.py --optimize                         # run with GEPA+GRPO optimization

This script generates synthetic EMA diaries that are:
- Temporally continuous (no gaps or overlaps)
- Memory-consistent (events reference previous days)
- EMA-complete (all variables the literature says matter)
- Coherence-audited (temporal, spatial, logical checks pass)
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dspy

from modules.diary_modules import EMADiaryPipeline
from optimizers.coherence_optimizers import (
    DiaryCoherenceGEPA,
    DiaryCoherenceGRPO,
    CompositeOptimizer,
    compute_coherence_reward,
)
from evaluation.diary_eval import evaluate_diary
from configs.pipeline_config import (
    PipelineConfig,
    PERSONA_TEMPLATES,
    PROMPT_TEMPLATES,
    EMAConfig,
)


def setup_lm(model: str = "openai/gpt-4o-mini", temperature: float = 0.7):
    """Configure the DSPy language model."""
    lm = dspy.LM(model=model, temperature=temperature, max_tokens=4096)
    dspy.configure(lm=lm)
    return lm


def generate_prompt_times(ema_config: EMAConfig) -> list[str]:
    """Generate EMA prompt times for a single day."""
    import random

    sh, sm = map(int, ema_config.waking_start.split(":"))
    eh, em = map(int, ema_config.waking_end.split(":"))
    start_min = sh * 60 + sm
    end_min = eh * 60 + em

    n = ema_config.prompts_per_day
    window_size = (end_min - start_min) // n
    times = []

    for i in range(n):
        ws = start_min + i * window_size
        we = min(ws + window_size, end_min - 1)
        t = random.randint(ws, we)
        h, m = divmod(t, 60)
        times.append(f"{h:02d}:{m:02d}")

    return sorted(times)


def run_single_persona(
    persona_description: str,
    config: PipelineConfig,
    optimize: bool = False,
) -> dict:
    """
    Generate a complete diary suite for one persona.

    Returns:
        {
            "persona": {...},
            "routine": {...},
            "memory_threads": [...],
            "days": [
                {
                    "day": 1,
                    "date": "2026-04-07",
                    "diary": {...},
                    "ema_probes": [...],
                    "evaluation": {...}
                },
                ...
            ],
            "overall_evaluation": {...}
        }
    """

    # Setup LM
    setup_lm(config.lm_model, config.lm_temperature)

    # Build pipeline
    pipeline = EMADiaryPipeline(
        num_days=config.diary.num_days,
        max_refine_iterations=config.coherence.max_refine_iterations,
        include_affect=config.diary.include_affect,
    )

    # EMA schedule config as JSON string
    ema_schedule = {
        "prompt_type": config.ema.prompt_type,
        "prompts_per_day": config.ema.prompts_per_day,
        "waking_start": config.ema.waking_start,
        "waking_end": config.ema.waking_end,
        "min_gap_between_prompts_min": config.ema.min_gap_between_prompts_min,
        "max_response_lag_min": config.ema.max_response_lag_min,
        "missingness_rate": config.ema.missingness_rate,
        "recall_window": config.ema.recall_window,
    }

    if optimize:
        # Run with optimization
        optimizer = CompositeOptimizer(
            pipeline_module=pipeline,
            gepa_iterations=config.optimizer.gepa_max_iterations,
            grpo_iterations=config.optimizer.grpo_iterations,
            grpo_group_size=config.optimizer.grpo_group_size,
        )

        result = optimizer(
            persona_description=persona_description,
            ema_schedule_config=json.dumps(ema_schedule),
            target_reward=config.optimizer.gepa_target_reward,
        )

        actual_result = result.best_result
    else:
        # Run without optimization
        actual_result = pipeline(
            persona_description=persona_description,
            ema_schedule_config=json.dumps(ema_schedule),
        )

    # Parse and structure output
    output = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "num_days": config.diary.num_days,
            "ema_prompts_per_day": config.ema.prompts_per_day,
            "ema_prompt_type": config.ema.prompt_type,
            "optimized": optimize,
        },
    }

    # Parse persona
    try:
        output["persona"] = json.loads(actual_result.persona)
    except (json.JSONDecodeError, TypeError):
        output["persona_raw"] = actual_result.persona

    # Parse routine
    try:
        output["routine"] = json.loads(actual_result.routine)
    except (json.JSONDecodeError, TypeError):
        output["routine_raw"] = actual_result.routine

    # Parse memory threads
    try:
        output["memory_threads"] = json.loads(actual_result.memory_threads)
    except (json.JSONDecodeError, TypeError):
        output["memory_threads_raw"] = actual_result.memory_threads

    # Parse daily diaries
    output["days"] = []
    all_day_dicts = []

    for i, day_diary_str in enumerate(actual_result.day_diaries):
        try:
            day_dict = json.loads(day_diary_str)
        except (json.JSONDecodeError, TypeError):
            day_dict = {"raw": day_diary_str}

        all_day_dicts.append(day_dict)

        day_entry = {
            "day": i + 1,
            "diary": day_dict,
        }

        # Add EMA probes if present
        if i < len(actual_result.ema_probes):
            try:
                probes = json.loads(actual_result.ema_probes[i])
                if isinstance(probes, str):
                    probes = json.loads(probes)
                day_entry["ema_probes"] = probes
            except (json.JSONDecodeError, TypeError):
                day_entry["ema_probes_raw"] = actual_result.ema_probes[i]

        # Add day summary
        if i < len(actual_result.day_summaries):
            try:
                day_entry["summary"] = json.loads(actual_result.day_summaries[i])
            except (json.JSONDecodeError, TypeError):
                day_entry["summary_raw"] = actual_result.day_summaries[i]

        output["days"].append(day_entry)

    # Run overall evaluation
    ema_probes_for_eval = []
    for day in output["days"]:
        if "ema_probes" in day:
            ema_probes_for_eval.append(day["ema_probes"])

    output["evaluation"] = evaluate_diary(
        day_diaries=all_day_dicts,
        ema_probes=ema_probes_for_eval if ema_probes_for_eval else None,
    )

    return output


def run_batch(
    num_personas: int = 5,
    config: PipelineConfig = None,
    optimize: bool = False,
    output_dir: str = "./output",
) -> list[dict]:
    """
    Generate diaries for multiple personas.

    Uses the PERSONA_TEMPLATES to create diverse synthetic participants.
    """
    if config is None:
        config = PipelineConfig()

    os.makedirs(output_dir, exist_ok=True)
    results = []

    templates = PERSONA_TEMPLATES[:num_personas]

    for i, template in enumerate(templates):
        print(f"\n{'='*60}")
        print(f"Generating persona {i+1}/{len(templates)}: {template['name']}")
        print(f"{'='*60}")

        try:
            result = run_single_persona(
                persona_description=template["description"],
                config=config,
                optimize=optimize,
            )

            result["template_name"] = template["name"]
            results.append(result)

            # Save individual result
            output_path = os.path.join(
                output_dir,
                f"persona_{i+1:02d}_{template['name'].lower().replace(' ', '_')}.json"
            )
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)

            print(f"  Saved to: {output_path}")
            print(f"  Overall score: {result['evaluation'].get('overall_score', 'N/A')}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"template_name": template["name"], "error": str(e)})

    # Save summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "num_personas": len(results),
        "successful": sum(1 for r in results if "error" not in r),
        "failed": sum(1 for r in results if "error" in r),
        "scores": {
            r.get("template_name", f"persona_{i}"): r.get("evaluation", {}).get("overall_score", 0)
            for i, r in enumerate(results)
            if "error" not in r
        },
    }

    summary_path = os.path.join(output_dir, "generation_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Generation complete: {summary['successful']}/{summary['num_personas']} successful")
    print(f"Summary saved to: {summary_path}")
    print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="EMA Diary Generation Pipeline")
    parser.add_argument("--persona", type=str, help="Custom persona description")
    parser.add_argument("--days", type=int, default=7, help="Number of days to generate")
    parser.add_argument("--batch", type=int, default=0, help="Number of personas to generate")
    parser.add_argument("--optimize", action="store_true", help="Enable GEPA+GRPO optimization")
    parser.add_argument("--model", type=str, default="openai/gpt-4o-mini", help="LLM model")
    parser.add_argument("--output", type=str, default="./output", help="Output directory")
    parser.add_argument("--prompts-per-day", type=int, default=6, help="EMA prompts per day")
    parser.add_argument("--prompt-type", type=str, default="random_signal",
                       choices=["random_signal", "event_triggered", "hybrid"],
                       help="EMA prompt type")

    args = parser.parse_args()

    # Build config
    config = PipelineConfig()
    config.diary.num_days = args.days
    config.ema.prompts_per_day = args.prompts_per_day
    config.ema.prompt_type = args.prompt_type
    config.lm_model = args.model

    if args.batch > 0:
        # Batch mode
        run_batch(
            num_personas=args.batch,
            config=config,
            optimize=args.optimize,
            output_dir=args.output,
        )
    else:
        # Single persona mode
        persona_desc = args.persona or PERSONA_TEMPLATES[0]["description"]

        print(f"Generating {args.days}-day diary for: {persona_desc}")
        print(f"EMA: {args.prompts_per_day} prompts/day ({args.prompt_type})")
        print(f"Model: {args.model}")
        print(f"Optimize: {args.optimize}")
        print()

        result = run_single_persona(
            persona_description=persona_desc,
            config=config,
            optimize=args.optimize,
        )

        # Save
        os.makedirs(args.output, exist_ok=True)
        output_path = os.path.join(args.output, "diary_output.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\nSaved to: {output_path}")
        print(f"Overall score: {result['evaluation'].get('overall_score', 'N/A')}")


if __name__ == "__main__":
    main()
