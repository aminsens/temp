"""Multi-day demonstration cohort (independent of DayForge/Appa).

Generates a contained synthetic cohort (default 4 personas x 7 days) through the
standalone EMA module and writes an inspectable report:

    demo_output/cohort_report.md      human-readable inspection report
    demo_output/cohort_summary.json   machine-readable aggregate statistics
    demo_output/ema_rows.csv          flat one-row-per-opportunity table
    demo_output/bundle_example.json   one complete, fully-provenanced bundle

Usage:
    /home/user/.venv-ema/bin/python -m paper3_ema.demo.run_demo
    /home/user/.venv-ema/bin/python paper3_ema/demo/run_demo.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

_DEMO_ROOT = Path(__file__).resolve().parent
_PKG_ROOT = _DEMO_ROOT.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from paper3_ema.config import default_config  # noqa: E402
from paper3_ema.fixtures import DEMO_ARCHETYPES, demo_cohort  # noqa: E402
from paper3_ema.pipeline import generate_ema  # noqa: E402
from paper3_ema.vocab import ResponseStatus  # noqa: E402

OUTPUT_DIR = _DEMO_ROOT / "demo_output"


def _pct(n: float) -> str:
    return f"{n:.0%}"


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


def run(participants: int = 4, days: int = 7, seed: int = 20260504) -> Path:
    config = default_config()
    start = "2026-05-04"
    from datetime import date

    start_date = date.fromisoformat(start)
    cohort = []
    for p_index in range(participants):
        archetype = DEMO_ARCHETYPES[p_index % len(DEMO_ARCHETYPES)]
        pid = f"demo-p{p_index + 1:02d}"
        for d_index in range(days):
            mapping = demo_day_mapping_local(archetype, pid, (start_date + timedelta(days=d_index)).isoformat(),
                                             seed + p_index * 100 + d_index)
            cohort.append(mapping)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bundles = []
    for mapping in cohort:
        bundle = generate_ema(mapping, seed=seed, config=config)
        bundles.append(bundle)

    rows = [record.flat_row() for bundle in bundles for record in bundle.records]

    # ---- aggregate statistics -------------------------------------------
    total = len(rows)
    answered = [r for r in rows if r["status"] == "answered"]
    expired = [r for r in rows if r["status"] == "expired"]
    missed = [r for r in rows if r["status"] == "missed"]
    latencies = [r["latency_min"] for r in rows if r["latency_min"] is not None]
    triggers = Counter(r["trigger"] for r in rows)
    windows = Counter(r["window_index"] for r in rows if r["window_index"] is not None)
    per_participant: dict[str, list[dict]] = {}
    for row in rows:
        per_participant.setdefault(row["participant_id"], []).append(row)

    rate_by_trigger: dict[str, dict[str, float]] = {}
    for row in rows:
        entry = rate_by_trigger.setdefault(row["trigger"], {"total": 0, "answered": 0})
        entry["total"] += 1
        if row["status"] == "answered":
            entry["answered"] += 1
    rate_by_trigger = {
        name: {
            "total": int(e["total"]),
            "response_rate": round(e["answered"] / e["total"], 3) if e["total"] else 0.0,
        }
        for name, e in rate_by_trigger.items()
    }

    item_distributions = {}
    for item in ("valence", "energy", "stress"):
        values = [r[item] for r in answered if r.get(item) is not None]
        item_distributions[item] = {
            "n": len(values),
            "mean": _mean(values),
            "median": _median(values),
            "distribution": {str(v): sum(1 for x in values if x == v) for v in range(1, 6)},
        }

    notes_rendered = sum(1 for r in answered if r.get("context_note"))
    notes_null = sum(1 for r in answered if not r.get("context_note"))
    event_rows = [r for r in rows if r["is_event_enriched"]]
    background_rows = [r for r in rows if not r["is_event_enriched"]]

    summary = {
        "protocol": config.protocol_name,
        "protocol_version": config.protocol_version,
        "config_hash": config.hash(),
        "cohort": {
            "participants": participants,
            "days_per_participant": days,
            "days": len(cohort),
            "opportunities": total,
            "archetypes": list(DEMO_ARCHETYPES),
        },
        "response": {
            "answered": len(answered),
            "expired": len(expired),
            "missed": len(missed),
            "response_rate": round(len(answered) / total, 3) if total else None,
            "target_band": list(config.get("missingness.calibration_target_response_rate")),
            "by_trigger": rate_by_trigger,
        },
        "latency_minutes": {
            "n": len(latencies),
            "mean": _mean(latencies),
            "median": _median(latencies),
            "p90": _p90(latencies),
            "max": max(latencies) if latencies else None,
            "right_skewed": bool(latencies and _mean(latencies) > _median(latencies)),
            "expiry_minutes": float(config.get("latency.expiry_minutes")),
        },
        "sampling": {
            "background": len(background_rows),
            "event_enriched": len(event_rows),
            "trigger_counts": dict(triggers),
            "windows_used": dict(sorted(windows.items())),
            "windows_per_day": sorted({len({r["window_index"] for r in recs if r["window_index"] is not None}) for recs in per_participant.values()} or {8}),
        },
        "subjective": item_distributions,
        "notes": {
            "rendered": notes_rendered,
            "null": notes_null,
            "sources": dict(Counter(r.get("note_source") for r in answered if r.get("note_source"))),
        },
        "per_participant": {
            pid: {
                "days": len(recs) // 5,
                "response_rate": round(
                    sum(1 for r in recs if r["status"] == "answered") / len(recs), 3
                ),
                "triggers": dict(Counter(r["trigger"] for r in recs)),
                "means": {
                    item: _mean([r[item] for r in recs if r.get(item) is not None])
                    for item in ("valence", "energy", "stress")
                },
            }
            for pid, recs in sorted(per_participant.items())
        },
        "provenance_sample": {
            "protocol_version": bundles[0].provenance.protocol_version,
            "scheduler_version": bundles[0].provenance.scheduler_version,
            "state_generator_version": bundles[0].provenance.state_generator_version,
            "seed": bundles[0].provenance.seed,
            "config_hash": bundles[0].provenance.config_hash,
            "context_fingerprint": bundles[0].provenance.context_fingerprint,
            "note_source_mix": dict(Counter(r.get("note_source") for r in rows if r.get("note_source"))),
        },
    }

    # ---- write outputs ----------------------------------------------------
    (OUTPUT_DIR / "cohort_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    fieldnames = list(rows[0].keys())
    with (OUTPUT_DIR / "ema_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    example = bundles[0]
    (OUTPUT_DIR / "bundle_example.json").write_text(example.to_json(indent=2))

    report = _render_report(summary, bundles, rows)
    report_path = OUTPUT_DIR / "cohort_report.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path


def _p90(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1))))]


def _render_report(summary: dict, bundles: list, rows: list) -> str:
    lines: list[str] = []
    lines.append("# Paper 3 EMA — multi-day demonstration cohort")
    lines.append("")
    lines.append(
        f"Protocol `{summary['protocol']} v{summary['protocol_version']}` (config hash "
        f"`{summary['config_hash']}`).  {summary['cohort']['participants']} synthetic personas × "
        f"{summary['cohort']['days_per_participant']} days, {summary['cohort']['opportunities']} EMA "
        f"opportunities.  Generated by the standalone module — **no DayForge, no Appa**, "
        "offline deterministic renderer (no LLM calls in this run)."
    )
    lines.append("")
    lines.append("## 1. Cohort response and missingness")
    lines.append("")
    r = summary["response"]
    lines.append(f"- answered: **{r['answered']}** / {r['answered'] + r['expired'] + r['missed']} "
                 f"({_pct(r['response_rate'])} of opportunities)")
    lines.append(f"- expired (response after the 10-min window): {r['expired']}")
    lines.append(f"- missed (no response): {r['missed']}")
    low, high = r["target_band"]
    lines.append(f"- calibration target band: {_pct(low)}–{_pct(high)} "
                 f"({'met' if low <= r['response_rate'] <= high else 'not met'} at cohort level)")
    lines.append("")
    lines.append("| trigger | opportunities | response rate |")
    lines.append("|---|---:|---:|")
    for trigger, entry in sorted(r["by_trigger"].items()):
        lines.append(f"| {trigger} | {entry['total']} | {_pct(entry['response_rate'])} |")
    lines.append("")
    lines.append("> The response rate is a *simulation calibration property*, not a claim about true "
                 "human compliance. Per-trigger rates differ by design (event-enriched prompts are "
                 "simulated to be slightly harder to answer — see the assumptions register, M-2).")
    lines.append("")
    lines.append("## 2. Sampling distribution")
    lines.append("")
    s = summary["sampling"]
    lines.append(f"- background (semi-random): **{s['background']}** opportunities")
    lines.append(f"- event-enriched: **{s['event_enriched']}** opportunities")
    lines.append(f"- trigger mix: " + ", ".join(f"{k}×{v}" for k, v in sorted(s["trigger_counts"].items())))
    lines.append(f"- daytime windows used: {len(s['windows_used'])} of 8 per day")
    lines.append("")
    lines.append("| window | prompts |")
    lines.append("|---:|---:|")
    for window, count in sorted((int(k), v) for k, v in s["windows_used"].items()):
        lines.append(f"| {window} | {count} |")
    lines.append("")
    lines.append("## 3. Response latency")
    lines.append("")
    lat = summary["latency_minutes"]
    lines.append(f"- mean {lat['mean']} min · median {lat['median']} min · p90 {lat['p90']} min · "
                 f"max {lat['max']} min (n={lat['n']})")
    lines.append(f"- right-skewed: {'yes' if lat['right_skewed'] else 'no'} "
                 f"(documented mean lag in the literature: ~2–5 min)")
    lines.append(f"- expiry window: {lat['expiry_minutes']:.0f} min — responses past the window are "
                 "recorded, flagged `expired` and excluded from alignment")
    lines.append("")
    lines.append("## 4. Synthetic subjective state (valence / energy / stress, 1–5)")
    lines.append("")
    lines.append("| item | n | mean | median | 1 | 2 | 3 | 4 | 5 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for item in ("valence", "energy", "stress"):
        d = summary["subjective"][item]
        dist = d["distribution"]
        lines.append(
            f"| {item} | {d['n']} | {d['mean']} | {d['median']} | "
            + " | ".join(str(dist.get(str(v), 0)) for v in range(1, 6)) + " |"
        )
    lines.append("")
    lines.append("Values are **synthetic** outputs of a seeded context-conditioned generator — "
                 "not observed human measurements. Distribution shape (unimodal, centred on 3, "
                 "bounded tails) is the intended signature of the bounded latent model.")
    lines.append("")
    lines.append("## 5. Per-participant view")
    lines.append("")
    lines.append("| participant | archetype | days | response rate | trigger mix | valence mean | energy mean | stress mean |")
    lines.append("|---|---|---:|---:|---|---:|---:|---:|")
    archetypes = list(DEMO_ARCHETYPES)
    for pid, entry in summary["per_participant"].items():
        index = int(pid.replace("demo-p", "")) - 1
        archetype = archetypes[index % len(archetypes)]
        mix = ", ".join(f"{k}×{v}" for k, v in sorted(entry["triggers"].items()))
        lines.append(
            f"| {pid} | {archetype} | {entry['days']} | {_pct(entry['response_rate'])} | {mix} | "
            f"{entry['means']['valence']} | {entry['means']['energy']} | {entry['means']['stress']} |"
        )
    lines.append("")
    lines.append("## 6. Notes (closed-world rendering)")
    lines.append("")
    n = summary["notes"]
    lines.append(f"- rendered: **{n['rendered']}** · null: **{n['null']}** (null is always acceptable)")
    lines.append(f"- sources: " + (", ".join(f"{k}×{v}" for k, v in sorted(n["sources"].items())) or "n/a"))
    lines.append("")
    shown = 0
    for bundle in bundles:
        for record in bundle.records:
            if record.response.context_note and shown < 8:
                lines.append(
                    f"  - `{record.prompt.day_date.isoformat()}` {record.prompt.prompt_time.strftime('%H:%M')} "
                    f"({record.prompt.trigger.value}, "
                    f"{record.prompt.inherited_context.get('activity')}/"
                    f"{record.prompt.inherited_context.get('place_type')}): “{record.response.context_note}”"
                )
                shown += 1
    lines.append("")
    lines.append("Every stored note was re-validated against the closed-world contract "
                 "(validator `notes.validate_note`); unsupported people/places/activities/"
                 "events/delays/weather/causes/journeys and medical claims are rejected with "
                 "retry, then offline-template fallback, then `null`.")
    lines.append("")
    lines.append("## 7. Provenance")
    lines.append("")
    prov = summary["provenance_sample"]
    lines.append(f"- protocol v{prov['protocol_version']} · scheduler v{prov['scheduler_version']} · "
                 f"state generator v{prov['state_generator_version']} · seed {prov['seed']}")
    lines.append(f"- config hash `{prov['config_hash']}` · context fingerprint `{prov['context_fingerprint']}` "
                 "(recomputed by the validator from the supplied day: any mutation of inherited "
                 "facts is detected)")
    lines.append("- per-record: prompt type, prompt/response times, episode/interval/journey ids, "
                 "retry counts, rule-level contribution traces and the full context packet "
                 "(see `bundle_example.json`)")
    lines.append("")
    lines.append("## 8. Full day-by-day table")
    lines.append("")
    lines.append("One row per EMA opportunity (also `ema_rows.csv`).  "
                 "`V/E/S` = valence/energy/stress; `—` = not recorded (missed).")
    lines.append("")
    lines.append("| date | participant | # | time | trigger | window | status | latency min | V | E | S | note |")
    lines.append("|---|---|---:|---|---|---:|---|---:|---:|---:|---:|---|")
    for row in rows:
        note = (row.get("context_note") or "")
        if len(note) > 44:
            note = note[:41] + "…"
        note = note.replace("|", "/").replace("\n", " ")
        v = row.get("valence")
        e = row.get("energy")
        ss = row.get("stress")
        latency = row.get("latency_min")
        lines.append(
            f"| {row['date']} | {row['participant_id']} | {row['schedule_index'] + 1} "
            f"| {row['prompt_time']} | {row['trigger']} | {row['window_index']} "
            f"| {row['status']} | {latency if latency is not None else '—'} "
            f"| {v if v is not None else '—'} | {e if e is not None else '—'} | {ss if ss is not None else '—'} "
            f"| {note or '—'} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("*Demonstration purpose: inspect sampling distribution, event/background balance, "
                 "response rate, latency, subjective-state variation, note grounding, missingness "
                 "and provenance. Not a behavioural-realism claim.*")
    lines.append("")
    return "\n".join(lines)


def demo_day_mapping_local(archetype: str, pid: str, day: str, seed: int) -> dict:
    from paper3_ema.fixtures import demo_day_mapping

    return demo_day_mapping(archetype, pid, day, seed=seed)


if __name__ == "__main__":
    participants = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20260504
    path = run(participants, days, seed)
    print(f"wrote {path}")
    print(f"wrote {OUTPUT_DIR / 'cohort_summary.json'}")
    print(f"wrote {OUTPUT_DIR / 'ema_rows.csv'}")
    print(f"wrote {OUTPUT_DIR / 'bundle_example.json'}")
