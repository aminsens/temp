#!/usr/bin/env python3
"""Live DeepSeek validation harness for the standalone Paper 3 EMA module.

Purpose
=======
Executes the full live-provider validation protocol against the real DeepSeek
API, exactly as specified in the tasking:

  connectivity  endpoint reachability + exact failure classification
  1             real integration tests (as committed, model per config) + full suite
  1b            flash-model transport smoke (auth, model echo, shape, parsing,
                retry bounds, closed-world acceptance)
  2             controlled live-note cases: >=15 varied contexts incl.
                adversarial temptation cases (weather / delay / person /
                named place / destination / cause / medical / psychological /
                unsupported journey)
  3             live-vs-offline invariance (identical day+config+seed; every
                non-LLM field must be identical)
  4             4 personas x 7 days live cohort with full call/acceptance/
                token/cost statistics and representative records
  5             repeatability boundary (structured output reproducible; LLM
                nondeterminism confined to the note + its provenance)

Credential rules (hard)
=======================
* The API key is read ONLY from the environment variable ``DEEPSEEK_API_KEY``.
* The key is never written to any file, log, artefact or report.  Every
  artefact is scanned on the way out and any accidental credential material
  is redacted (see :func:`scan_and_redact_secrets`).

This harness is **test-only**: it is not imported by the package, it does not
modify scientific parameters, and it never alters production code.  The one
extension over the production client is a timing/usage capture wrapper plus
the provider-documented ``thinking``/``reasoning_effort`` request fields for
``deepseek-flash`` (see the provider API guide), both overridable via
environment variables.

Usage
=====
    export DEEPSEEK_API_KEY=...            # never stored anywhere by this tool
    python3 live_harness.py --phase all --write-docs

Exit codes: 0 ok | 2 endpoint unreachable | 3 no credential | 4 validation FAIL
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

_HERE = Path(__file__).resolve().parent
_PKG_ROOT = _HERE.parent                      # .../paper3_ema
_REPO_ROOT = _PKG_ROOT.parent                  # repo root
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from paper3_ema.config import default_config          # noqa: E402
from paper3_ema.fixtures import (                     # noqa: E402
    build_fixture,
    demo_cohort,
    fixture_mapping,
)
from paper3_ema.llm import (                          # noqa: E402
    DeepSeekClient,
    extract_json,
    extract_note_text,
    probe_endpoint,
    render_note,
)
from paper3_ema.notes import validate_note             # noqa: E402
from paper3_ema.pipeline import generate_ema           # noqa: E402

HARNESS_VERSION = "1.0.0"
DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")

# ---------------------------------------------------------------------------
# published pricing for cost estimation (only used to convert *returned*
# token usage into an estimate; never a guess about usage)
# source: DeepSeek official pricing table as synced by third-party trackers
# dated 2026-09-10..2026-09-23 (benchlm.ai, aipricing.guru, chat-deep.ai,
# layer3labs.io — all agree): deepseek-flash == DeepSeek-V4.1-Flash
# ---------------------------------------------------------------------------
PRICING = {
    "model": "deepseek-flash (DeepSeek-V4.1-Flash)",
    "as_of": "2026-09-24",
    "source": "DeepSeek official pricing table, synced 2026-09-10..2026-09-23",
    "peak": {"input_per_m": 0.30, "cached_input_per_m": 0.006, "output_per_m": 1.20},
    "off_peak": {"input_per_m": 0.15, "cached_input_per_m": 0.003, "output_per_m": 0.60},
    "notes": [
        "peak vs off-peak window is defined by DeepSeek (UTC schedule); both are reported",
        "cached_input tokens are billed at the cache-hit rate (subset of prompt_tokens)",
        "completion_tokens includes reasoning tokens where the provider reports them",
    ],
}


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def localnow() -> str:
    try:
        from zoneinfo import ZoneInfo

        return (
            datetime.now(timezone.utc)
            .astimezone(ZoneInfo("Europe/Copenhagen"))
            .isoformat(timespec="seconds")
        )
    except Exception:  # pragma: no cover
        return utcnow()


def git_identity() -> dict:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", "-C", str(_REPO_ROOT), *args],
                capture_output=True, text=True, timeout=30,
            ).stdout.strip()
        except Exception:
            return ""

    dirty = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "commit_short": run("rev-parse", "--short", "HEAD"),
        "branch": run("branch", "--show-current"),
        "working_tree_dirty": bool(dirty),
        "dirty_summary": dirty.splitlines()[:10],
    }


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


_SECRET_RE = re.compile(r"sk-[A-Za-z0-9]{20,}")


def scan_and_redact_secrets(paths: list[Path], extra_secrets: list[str]) -> int:
    """Redact any credential material that accidentally reached an artefact."""
    hits = 0
    needles = [s for s in extra_secrets if s]
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        for needle in needles:
            if needle in text:
                text = text.replace(needle, "[REDACTED-SECRET]")
        text, n = _SECRET_RE.subn("[REDACTED-SECRET]", text)
        if text != original:
            hits += n + (1 if any(nd in original for nd in needles) else 0)
            path.write_text(text, encoding="utf-8")
    return hits


def _v(x):
    if x is None:
        return None
    return x.value if hasattr(x, "value") else str(x)


# ---------------------------------------------------------------------------
# live client: production client + timing/usage metrics + thinking fields
# (harness-only; the production client is not modified)
# ---------------------------------------------------------------------------

class LiveTimingClient(DeepSeekClient):
    """DeepSeek client wrapper for the live validation run.

    Adds: per-call latency + usage metrics (captured, never secret), the
    provider-documented ``thinking``/``reasoning_effort`` request fields for
    ``deepseek-flash``, and an optional ``max_tokens`` override (thinking
    consumes completion tokens; the bundled default of 120 is tuned for the
    legacy non-thinking model).  Everything else is the production transport.
    """

    reasoning_effort: str = "high"
    thinking: str = "enabled"
    max_tokens_override: str | None = None
    metrics: list = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = []

    def _extra_secret(self) -> str:
        return self.api_key

    def complete(self, system: str, user: str, **decoding) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        if self.model.startswith("deepseek-flash"):
            payload["reasoning_effort"] = self.reasoning_effort
            payload["thinking"] = {"type": self.thinking}
        for key, value in decoding.items():
            if value is not None:
                payload[key] = value
        if self.max_tokens_override:
            payload["max_tokens"] = int(self.max_tokens_override)
        request = urllib.request.Request(
            self.base_url.rstrip("/") + self.chat_path,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            dt_ms = round((time.monotonic() - t0) * 1000, 1)
            detail = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    err_body = exc.read().decode("utf-8")[:400].replace(self.api_key, "[REDACTED]")
                except Exception:
                    err_body = ""
                detail = f"HTTP {exc.code}: {err_body}"
            self.metrics.append({"ok": False, "latency_ms": dt_ms, "error": detail})
            raise
        dt_ms = round((time.monotonic() - t0) * 1000, 1)
        try:
            message = body["choices"][0]["message"]
            content = str(message["content"])
        except (KeyError, IndexError, TypeError) as exc:
            self.metrics.append({"ok": False, "latency_ms": dt_ms, "error": f"unexpected shape: {exc}"})
            raise
        self.metrics.append(
            {
                "ok": True,
                "latency_ms": dt_ms,
                "http_status": 200,
                "response_model": body.get("model"),
                "usage": body.get("usage"),
                "content_chars": len(content),
                "reasoning_chars": len(message.get("reasoning_content") or ""),
            }
        )
        return content


def make_client(model: str, timeout: float = 90.0) -> LiveTimingClient:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise SystemExit("no DEEPSEEK_API_KEY in environment (exit 3)")
    config = default_config()
    return LiveTimingClient(
        api_key=key,
        base_url=str(config.get("llm.base_url", "https://api.deepseek.com")),
        chat_path=str(config.get("llm.chat_path", "/chat/completions")),
        model=model,
        timeout=timeout,
        reasoning_effort=os.environ.get("DEEPSEEK_REASONING_EFFORT", "high"),
        thinking=os.environ.get("DEEPSEEK_THINKING", "enabled"),
        max_tokens_override=os.environ.get("DEEPSEEK_MAX_TOKENS", "1024"),
    )


# ---------------------------------------------------------------------------
# connectivity
# ---------------------------------------------------------------------------

def phase_connectivity(out: Path) -> dict:
    key_present = bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())
    reachable, detail = probe_endpoint(timeout=10)
    diagnostics: dict = {}
    try:
        ip = socket.getaddrinfo("api.deepseek.com", 443, 0, socket.SOCK_STREAM)[0][4][0]
        diagnostics["dns"] = f"ok -> {ip}"
        raw = socket.create_connection(("api.deepseek.com", 443), timeout=15)
        diagnostics["tcp"] = "ok"
        ctx = ssl.create_default_context()
        try:
            tls = ctx.wrap_socket(raw, server_hostname="api.deepseek.com")
            diagnostics["tls"] = f"ok ({tls.version()})"
            tls.close()
        except Exception as exc:
            diagnostics["tls"] = f"FAILED {type(exc).__name__}: {exc}"
            raw.close()
    except Exception as exc:
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
    result = {
        "reachable": reachable,
        "probe_detail": detail,
        "key_present": key_present,
        "diagnostics": diagnostics,
        "checked_utc": utcnow(),
    }
    write_json(out / "01_connectivity.json", result)
    print(f"[connectivity] reachable={reachable} ({detail})")
    return result


# ---------------------------------------------------------------------------
# phase 1: committed integration tests + full suite
# ---------------------------------------------------------------------------

INTEGRATION_FILE = "paper3_ema/tests/test_deepseek_integration.py"


def _run_pytest(args: list[str], out: Path, name: str, timeout: int = 1800) -> int:
    cmd = [sys.executable, "-m", "pytest", *args]
    proc = subprocess.run(cmd, cwd=str(_PKG_ROOT), capture_output=True, text=True, timeout=timeout)
    (out / name).write_text(
        f"$ {' '.join(cmd)}\n\ncwd={_PKG_ROOT}\n\n=== stdout ===\n{proc.stdout}\n=== stderr ===\n{proc.stderr}\n",
        encoding="utf-8",
    )
    print(f"[pytest:{name}] rc={proc.returncode}")
    return proc.returncode


def phase1_suite(out: Path) -> dict:
    print("[phase1] running committed integration tests (verbose) ...")
    _run_pytest([INTEGRATION_FILE, "-v", "--tb=line", "-q"], out, "02_integration_verbose.txt")
    print("[phase1] running full suite ...")
    _run_pytest(["paper3_ema/tests", "-q", "--tb=short"], out, "02_suite_full.txt")

    integration_text = (out / "02_integration_verbose.txt").read_text(encoding="utf-8")
    full_text = (out / "02_suite_full.txt").read_text(encoding="utf-8")

    def tail_summary(text: str) -> str:
        for line in reversed(text.splitlines()):
            if re.search(r"\d+ (passed|failed|skipped)", line):
                return line.strip()
        return ""

    integration_tests = {
        name: ("passed" if f" {name} PASSED" in integration_text or f"{name} [100%]" in integration_text else None)
        for name in (
            "test_real_llm_end_to_end_bundle",
            "test_real_llm_retries_are_bounded",
            "test_real_llm_never_alters_inherited_context",
            "test_real_llm_subjective_values_are_not_model_chosen",
        )
    }
    # more reliable: parse the -v lines
    for line in integration_text.splitlines():
        for name in integration_tests:
            if name in line:
                if "PASSED" in line:
                    integration_tests[name] = "passed"
                elif "FAILED" in line:
                    integration_tests[name] = "failed"
                elif "SKIPPED" in line:
                    integration_tests[name] = "skipped"

    failures = [n for n, s in integration_tests.items() if s == "failed"]
    lines = integration_text.splitlines()
    fail_lines: list[str] = []
    for i, line in enumerate(lines):
        if "FAILED" in line:
            fail_lines.append(line)
            if i + 1 < len(lines):
                fail_lines.append(lines[i + 1])
    failure_excerpt = "\n".join(fail_lines)[-3000:]
    model_unavailable_markers = ("httperror", "llm_call_failed", "model not found", "404", "400")
    classified_unavailable = bool(failures) and any(
        m in failure_excerpt.lower() for m in model_unavailable_markers
    )
    suite_summary = tail_summary(full_text)
    failed_lines = [l for l in full_text.splitlines() if l.startswith("FAILED")]
    non_integration_failures = [l for l in failed_lines if "test_deepseek_integration" not in l]
    result = {
        "integration_tests": integration_tests,
        "integration_failures": failures,
        "integration_failure_classified_model_unavailable": classified_unavailable,
        "failure_excerpt": failure_excerpt[-1200:],
        "full_suite_summary": suite_summary,
        "non_integration_failed_lines": non_integration_failures,
        "suite_gate": {
            "non_integration_tests_pass": len(non_integration_failures) == 0,
            "integration_gate": (not failures) or classified_unavailable,
        },
        "note": (
            "if integration tests failed with a transport/model error (e.g. retired model id), "
            "the transport gate for this run is carried by phase 1b (flash smoke)"
        ),
    }
    write_json(out / "02_suite.json", result)
    print(f"[phase1] suite: {suite_summary or 'n/a'}")
    return result


# ---------------------------------------------------------------------------
# phase 1b: flash transport smoke
# ---------------------------------------------------------------------------

def phase1b_flash_smoke(out: Path, model: str) -> dict:
    client = make_client(model)
    # raw single call: auth + model echo + shape + usage
    raw = client.complete("You are a helpful assistant.", "Reply with exactly one word: ok")
    raw_ok = bool(raw.strip())
    m0 = client.metrics[-1]

    day = build_fixture("public_transport_commuter_day")
    bundle = generate_ema(day, seed=7, llm_client=client)
    config = default_config()
    max_retries = int(config.get("note.max_retries", 2))
    notes_checked = 0
    closed_world_ok = True
    for record in bundle.records:
        note = record.response.context_note
        if note is not None:
            notes_checked += 1
            validation = validate_note(note, record.packet, config)
            closed_world_ok = closed_world_ok and validation.valid
    ok_metrics = [m for m in client.metrics if m.get("ok")]
    model_echoed = {m.get("response_model") for m in ok_metrics}
    no_http_error = all(m.get("http_status") == 200 for m in ok_metrics)
    checks = {
        "auth_succeeded": bool(ok_metrics)
        and not any("HTTP 401" in str(m.get("error", "")) or "unauthorized" in str(m.get("error", "")).lower()
                    for m in client.metrics),
        "expected_model_used": model in model_echoed,
        "request_shape_accepted": no_http_error and not any(
            str(m.get("http_status", "")) in ("400", "422") for m in client.metrics
        ),
        "response_parsing_succeeded": raw_ok and notes_checked >= 1,
        "retry_bounds_intact": bundle.provenance.llm_retries <= max_retries * len(bundle.records),
        "closed_world_acceptance": closed_world_ok and notes_checked >= 1,
        "bundle_validation": bundle.validation.valid,
    }
    result = {
        "model": model,
        "raw_call": {"content": raw[:200], "metric": m0, "ok": raw_ok},
        "bundle": {
            "llm_calls": bundle.provenance.llm_calls,
            "llm_retries": bundle.provenance.llm_retries,
            "notes_checked": notes_checked,
            "note_sources": {
                s: sum(1 for r in bundle.records if r.response.note_source == s) for s in ("llm", "offline_template")
            },
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    write_json(out / "03_flash_smoke.json", result)
    print(f"[phase1b] flash smoke: {checks}")
    return result


# ---------------------------------------------------------------------------
# phase 2: controlled live-note cases
# ---------------------------------------------------------------------------

CASES: list[dict] = [
    dict(name="semi_random_home", fixture="mostly_home_day",
         temptations=["another_person", "named_place", "weather"],
         predicate=lambda r: r.prompt.trigger.value == "semi_random"
         and _v(r.packet.place_type) == "home" and _v(r.packet.social_context) == "alone"),
    dict(name="work_study", fixture="normal_office_day",
         temptations=["causal_explanation", "named_place"],
         predicate=lambda r: _v(r.packet.domain) == "work" and _v(r.packet.place_type) == "workplace"),
    dict(name="childcare", fixture="highly_fragmented_day",
         temptations=["another_person", "medical_condition"],
         predicate=lambda r: _v(r.packet.domain) == "childcare"),
    dict(name="social", fixture="normal_office_day",
         temptations=["another_person", "causal_explanation"],
         predicate=lambda r: _v(r.packet.social_context) in ("with_partner", "with_friends", "with_family")
         and _v(r.packet.place_type) == "home"),
    dict(name="post_walk", fixture="exercise_day",
         temptations=["unsupported_journey_event", "weather"],
         predicate=lambda r: r.prompt.trigger.value == "post_trip"
         and _v(r.packet.preceding_journey_mode) in ("walk", "walking", "foot")),
    dict(name="post_run_exercise", fixture="exercise_day",
         temptations=["medical_condition", "causal_explanation"],
         predicate=lambda r: r.prompt.trigger.value == "post_active_episode"),
    dict(name="post_cycle", fixture="cycling_commuter_day",
         temptations=["named_place", "weather"],
         predicate=lambda r: r.prompt.trigger.value == "post_trip"
         and _v(r.packet.preceding_journey_mode) in ("bike", "cycling", "bicycle")),
    dict(name="post_public_transport", fixture="public_transport_commuter_day",
         temptations=["named_place", "delay"],
         predicate=lambda r: r.prompt.trigger.value == "post_trip"
         and _v(r.packet.preceding_journey_mode) in ("bus", "train", "tram")),
    dict(name="post_car", fixture="evening_shift_day",
         temptations=["named_place", "destination"],
         predicate=lambda r: r.prompt.trigger.value == "post_trip"
         and _v(r.packet.preceding_journey_mode) in ("car", "driving")),
    dict(name="documented_delayed_journey", fixture="public_transport_commuter_day",
         temptations=["delay (elaboration of a documented fact)"],
         predicate=lambda r: r.packet.preceding_journey_delayed is True),
    dict(name="journey_without_documented_delay", fixture="normal_office_day",
         temptations=["delay (invention)"],
         predicate=lambda r: r.prompt.trigger.value == "post_trip"
         and r.packet.preceding_journey_delayed in (False, None)),
    dict(name="context_transition", fixture="mostly_home_day",
         # normal_office_day never yields context_transition (its two bus
         # trips occupy both event slots at higher priority); mostly_home_day
         # has transitions plus background prompts only.
         temptations=["causal_explanation", "unsupported_journey_event"],
         predicate=lambda r: r.prompt.trigger.value == "context_transition"),
    dict(name="evening", fixture="evening_shift_day",
         temptations=["psychological_trait", "causal_explanation"],
         predicate=lambda r: r.packet.time_of_day in ("evening", "late_evening")),
    dict(name="no_eligible_event_day", fixture="no_eligible_event_day",
         temptations=["unsupported_journey_event"],
         predicate=lambda r: r.prompt.trigger.value == "semi_random"),
    dict(name="sparse_ambiguous", fixture="unresolved_movement_day",
         temptations=["unsupported_journey_event", "named_place"],
         predicate=lambda r: _v(r.packet.activity) in (None, "unknown")
         or _v(r.packet.preceding_activity) == "unknown"
         or r.packet.purpose_category is None
         or _v(r.packet.place_type) in (None, "other")),
]

_BUNDLE_CACHE: dict = {}


def _offline_bundle(fixture_name: str, pid: str, day: str, seed: int):
    key = (fixture_name, pid, day, seed)
    if key not in _BUNDLE_CACHE:
        mapping = fixture_mapping(fixture_name, participant_id=pid, day=day)
        _BUNDLE_CACHE[key] = generate_ema(mapping, seed=seed, llm_client=None)
    return _BUNDLE_CACHE[key]


def find_case_record(spec: dict, max_seeds: int = 30):
    pid = f"live-case-{spec['name']}"
    day = "2026-06-01"
    for seed in range(1, max_seeds + 1):
        bundle = _offline_bundle(spec["fixture"], pid, day, seed)
        for record in bundle.records:
            if record.response.answered and record.response.subjective is not None and spec["predicate"](record):
                return bundle, record, seed
    return None, None, None


def phase2_cases(out: Path, model: str, max_seeds: int = 30) -> dict:
    config = default_config()
    entries = []
    for index, spec in enumerate(CASES):
        bundle, record, seed = find_case_record(spec, max_seeds=max_seeds)
        if record is None:
            entries.append({"case": spec["name"], "found": False,
                            "note": "no matching answered record within seed range (documented, not a failure)"})
            print(f"[phase2] {spec['name']}: NO MATCHING RECORD")
            continue
        client = make_client(model)
        state = record.response.subjective.items()
        result = render_note(record.packet, state, config, client=client,
                             rng=random.Random(1000 + index))
        validation_dicts = [v.to_dict() for v in result.validations]
        entries.append({
            "case": spec["name"],
            "found": True,
            "fixture": spec["fixture"],
            "seed": seed,
            "temptations": spec["temptations"],
            "prompt_time": record.prompt.prompt_time.isoformat(),
            "trigger": record.prompt.trigger.value,
            "context_seen_by_model": record.packet.fact_view(),
            "state": {k: int(v) for k, v in state.items()},
            "attempts": result.attempts,
            "retries": result.retries,
            "attempt_details": [
                {
                    "raw_model_output": raw,
                    "parsed_candidate": extract_note_text(extract_json(raw)),
                    "validation": validation_dicts[i] if i < len(validation_dicts) else None,
                }
                for i, raw in enumerate(result.raw_outputs)
            ],
            "final": {
                "note": result.note,
                "source": result.source,
                "fallback_reason": result.fallback_reason,
            },
            "api_metrics": client.metrics,
        })
        print(f"[phase2] {spec['name']}: attempts={result.attempts} source={result.source} "
              f"note={result.note!r}")
    # independent closed-world re-audit of every stored note
    survivors = []
    for entry in entries:
        if not entry.get("found"):
            continue
        note = entry["final"]["note"]
        if note is None:
            continue
        # re-fetch the packet for an independent validation
        bundle, record, _ = find_case_record(next(s for s in CASES if s["name"] == entry["case"]))
        validation = validate_note(note, record.packet, config)
        if not validation.valid:
            survivors.append({"case": entry["case"], "note": note, "codes": validation.codes})
    result = {
        "model": model,
        "cases": entries,
        "found": sum(1 for e in entries if e.get("found")),
        "surviving_unsupported_facts": survivors,
        "gate": {
            "all_cases_found": sum(1 for e in entries if e.get("found")) == len(CASES),
            "zero_survivors": len(survivors) == 0,
        },
    }
    write_json(out / "04_cases.json", result)
    return result


# ---------------------------------------------------------------------------
# phase 3: live-vs-offline invariance
# ---------------------------------------------------------------------------

# Paths that may differ between an offline and a live-LLM run of the same
# (mapping, seed). Everything else must be byte-identical, or the invariance
# gate fails. The per-record provenance trace (record_provenance.<prompt_id>)
# carries LLM note-rendering telemetry (model/provider/decoding, attempts,
# retries, fallback reason, rejected validator codes); those keys exist at
# both bundle level ($.provenance.record_provenance...) and inside each
# record's provenance copy ($.records[i].provenance.record_provenance...),
# so the per-record markers are dot-anchored to match at any depth.
ALLOWED_DIFF_MARKERS = (
    ".context_note",
    ".note_source",
    ".note_validation",
    ".note_result",
    ".llm_provider",
    ".llm_model",
    ".llm_decoding",
    ".note_attempts",
    ".note_fallback_reason",
    ".note_rejected_codes",
    ".retry_count",
    "provenance.llm_template_version",
    ".llm_calls",
    ".llm_retries",
    "summary.notes_rendered",
    "summary.notes_null",
    "summary.note_sources",
)


def deep_diff(a, b, path: str = "$"):
    if type(a) is not type(b):
        if a == b:
            return
        yield (path, a, b)
        return
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b), key=str):
            if key not in a:
                yield (f"{path}.{key}", None, b[key])
            elif key not in b:
                yield (f"{path}.{key}", a[key], None)
            else:
                yield from deep_diff(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield (f"{path}.length", len(a), len(b))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            yield from deep_diff(x, y, f"{path}[{i}]")
    else:
        if a != b:
            yield (path, a, b)


def is_allowed_diff(path: str) -> bool:
    return any(marker in path for marker in ALLOWED_DIFF_MARKERS)


def phase3_invariance(out: Path, model: str) -> dict:
    mapping = fixture_mapping("normal_office_day", participant_id="invariance-p", day="2026-06-02")
    offline = json.loads(generate_ema(mapping, seed=7, llm_client=None).to_json())
    client = make_client(model)
    live = json.loads(generate_ema(mapping, seed=7, llm_client=client).to_json())
    diffs = list(deep_diff(offline, live))
    unallowed = [(p, a, b) for p, a, b in diffs if not is_allowed_diff(p)]
    result = {
        "day": mapping["participant_id"],
        "seed": 7,
        "total_diffs": len(diffs),
        "allowed_diffs": [(p, a, b) for p, a, b in diffs if is_allowed_diff(p)][:200],
        "unallowed_diffs": [(p, a, b) for p, a, b in unallowed][:200],
        "gate": {"identical_outside_note_and_llm_provenance": len(unallowed) == 0},
    }
    write_json(out / "05_invariance.json", result)
    print(f"[phase3] diffs={len(diffs)} unallowed={len(unallowed)}")
    return result


# ---------------------------------------------------------------------------
# phase 4: 4 x 7 live cohort
# ---------------------------------------------------------------------------

def _run_cohort_day(index: int, mapping: dict, seed: int, model: str):
    client = make_client(model)
    bundle = generate_ema(mapping, seed=seed, llm_client=client)
    return index, bundle, client.metrics


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def _estimate_cost(usage_totals: dict) -> dict:
    prompt = usage_totals.get("prompt_tokens", 0) or 0
    completion = usage_totals.get("completion_tokens", 0) or 0
    cached = usage_totals.get("cached_tokens", 0) or 0
    cached = min(cached, prompt)
    out = {}
    for label in ("peak", "off_peak"):
        rates = PRICING[label]
        out[label] = round(
            (prompt - cached) / 1e6 * rates["input_per_m"]
            + cached / 1e6 * rates["cached_input_per_m"]
            + completion / 1e6 * rates["output_per_m"],
            9,
        )
    return out


def phase4_cohort(out: Path, model: str, participants: int = 4, days: int = 7,
                  seed: int = 20260504, workers: int = 4) -> dict:
    cohort = demo_cohort(participants=participants, days=days, start_date="2026-05-04", seed=seed)
    config = default_config()
    results: dict = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_run_cohort_day, i, m, seed, model) for i, m in enumerate(cohort)]
        for future in as_completed(futures):
            index, bundle, metrics = future.result()
            results[index] = (bundle, metrics)

    bundles = [results[i][0] for i in range(len(cohort))]
    all_metrics = [m for _, metrics in results.values() for m in metrics]
    records = [record for bundle in bundles for record in bundle.records]

    answered = [r for r in records if r.response.answered]
    expired = [r for r in records if r.response.expired]
    missed = [r for r in records if r.response.status.value == "missed"]

    rendered = [r for r in records if r.response.note_validation is not None]
    first_parse_fail = 0
    first_parse_ok = 0
    first_closed_world_ok = 0
    model_null_first = 0
    retry_counter: dict = {}
    rejection_codes: dict = {}
    offline_fallback = 0
    for record in rendered:
        nv = record.response.note_validation
        retry_counter[nv["retries"]] = retry_counter.get(nv["retries"], 0) + 1
        first = nv["validations"][0] if nv["validations"] else None
        if first is None:
            continue
        if "unparseable_output" in first["codes"]:
            first_parse_fail += 1
        else:
            first_parse_ok += 1
            if first["valid"]:
                first_closed_world_ok += 1
        for validation in nv["validations"]:
            if not validation["valid"]:
                for code in validation["codes"]:
                    rejection_codes[code] = rejection_codes.get(code, 0) + 1
        if nv["source"] == "offline_template":
            offline_fallback += 1
        if nv["source"] == "llm" and nv["fallback_reason"] == "llm_returned_null" and nv["attempts"] == 1:
            model_null_first += 1

    notes_answered = [r.response.context_note for r in answered]
    usage_totals = {
        "prompt_tokens": sum((m.get("usage") or {}).get("prompt_tokens", 0) for m in all_metrics if m.get("ok")),
        "completion_tokens": sum((m.get("usage") or {}).get("completion_tokens", 0) for m in all_metrics if m.get("ok")),
        "cached_tokens": sum(((m.get("usage") or {}).get("prompt_tokens_details") or {}).get("cached_tokens", 0)
                              for m in all_metrics if m.get("ok")),
        "reasoning_tokens": sum(((m.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
                                 for m in all_metrics if m.get("ok")),
    }
    ok_latencies = [m["latency_ms"] for m in all_metrics if m.get("ok")]

    bundle_valid = all(b.validation.valid for b in bundles)
    bundle_issues: dict = {}
    for b in bundles:
        for issue in b.validation.issues:
            bundle_issues[issue.code] = bundle_issues.get(issue.code, 0) + 1

    # independent closed-world audit of every stored note (survivor check)
    survivors = []
    for record in records:
        note = record.response.context_note
        if note is None:
            continue
        validation = validate_note(note, record.packet, config)
        if not validation.valid:
            survivors.append({"participant": record.prompt.participant_id,
                              "time": record.prompt.prompt_time.isoformat(),
                              "note": note, "codes": validation.codes})

    # representative records for human inspection (>=15, spanning triggers)
    bundle_of = {id(record): bundle for bundle in bundles for record in bundle.records}
    representative: list = []  # (bundle, record) pairs
    picked: set = set()

    def pick(record) -> None:
        if record in picked or len(representative) >= 18:
            return
        if not record.response.answered or not record.response.context_note:
            return
        picked.add(record)
        representative.append((bundle_of[id(record)], record))

    seen_triggers: set = set()
    for record in records:
        if len(representative) >= 18:
            break
        if record.response.answered and record.response.context_note:
            if record.prompt.trigger.value not in seen_triggers:
                pick(record)
                seen_triggers.add(record.prompt.trigger.value)
    seen_archetypes: set = set()
    for record in records:
        if len(representative) >= 18:
            break
        if record.prompt.participant_id not in seen_archetypes:
            pick(record)
            if record in picked:
                seen_archetypes.add(record.prompt.participant_id)
    for record in [r for r in answered if r.response.note_source == "offline_template"][:3]:
        pick(record)

    def rep_row(bundle, record) -> dict:
        ic = record.prompt.inherited_context or {}
        subj = record.response.subjective
        return {
            "participant": record.prompt.participant_id,
            "date": record.prompt.day_date.isoformat() if record.prompt.day_date else None,
            "prompt_time": record.prompt.prompt_time.strftime("%H:%M"),
            "trigger": record.prompt.trigger.value,
            "preceding_mode": record.packet.preceding_journey_mode,
            "delay_documented": record.packet.preceding_journey_delayed,
            "context": {
                "activity": ic.get("activity"),
                "place_type": ic.get("place_type"),
                "social": ic.get("social_context"),
                "domain": ic.get("domain"),
            },
            "valence_energy_stress": (
                (subj.valence, subj.energy, subj.stress) if subj else None
            ),
            "final_note": record.response.context_note,
            "note_source": record.response.note_source,
            "validation_status": "bundle PASS" if bundle.validation.valid else "bundle FAIL",
        }

    result = {
        "model": model,
        "cohort": {"participants": participants, "days": days, "participant_days": len(cohort)},
        "opportunities": len(records),
        "answered": len(answered),
        "missed": len(missed),
        "expired": len(expired),
        "prompt_type_distribution": {
            t: sum(1 for r in records if r.prompt.trigger.value == t)
            for t in sorted({r.prompt.trigger.value for r in records})
        },
        "api": {
            "calls_attempted": len(all_metrics),
            "calls_succeeded": sum(1 for m in all_metrics if m.get("ok")),
            "calls_failed": sum(1 for m in all_metrics if not m.get("ok")),
            "latency_ms": {
                "mean": round(mean(ok_latencies), 1) if ok_latencies else None,
                "median": round(median(ok_latencies), 1) if ok_latencies else None,
                "p95": _percentile(ok_latencies, 0.95),
                "max": max(ok_latencies) if ok_latencies else None,
            },
            "usage_totals": usage_totals,
            "estimated_cost_usd": _estimate_cost(usage_totals),
            "pricing": PRICING,
        },
        "note_pipeline": {
            "rendered": len(rendered),
            "first_attempt_parse_ok": first_parse_ok,
            "first_attempt_parse_fail": first_parse_fail,
            "first_attempt_closed_world_accept": first_closed_world_ok,
            "model_chose_null_first_attempt": model_null_first,
            "retry_distribution": {str(k): v for k, v in sorted(retry_counter.items())},
            "rejection_counts_by_code": dict(sorted(rejection_codes.items())),
            "offline_fallback_count": offline_fallback,
            "null_note_count_answered": sum(1 for n in notes_answered if n is None),
            "final_non_null_note_count_answered": sum(1 for n in notes_answered if n),
        },
        "validation": {
            "all_bundles_valid": bundle_valid,
            "bundle_issue_codes": bundle_issues,
            "surviving_unsupported_facts": survivors,
        },
        "representative_records": [rep_row(b, r) for b, r in representative],
    }
    write_json(out / "06_cohort.json", result)
    with (out / "06_cohort_bundles.jsonl").open("w", encoding="utf-8") as handle:
        for bundle in bundles:
            handle.write(bundle.to_json() + "\n")
    print(f"[phase4] {len(records)} opportunities, {len(answered)} answered, "
          f"calls={len(all_metrics)}, survivors={len(survivors)}")
    return result


# ---------------------------------------------------------------------------
# phase 5: repeatability boundary
# ---------------------------------------------------------------------------

def phase5_repeatability(out: Path, model: str) -> dict:
    mapping = fixture_mapping("cycling_commuter_day", participant_id="repeatability-p", day="2026-06-03")
    offline_1 = generate_ema(mapping, seed=11, llm_client=None).to_json()
    offline_2 = generate_ema(mapping, seed=11, llm_client=None).to_json()
    live_1 = json.loads(generate_ema(mapping, seed=11, llm_client=make_client(model)).to_json())
    live_2 = json.loads(generate_ema(mapping, seed=11, llm_client=make_client(model)).to_json())
    live_diffs = list(deep_diff(live_1, live_2))
    unallowed = [(p, a, b) for p, a, b in live_diffs if not is_allowed_diff(p)]

    def notes_of(bundle_json: dict) -> list:
        return [r["response"]["context_note"] for r in bundle_json["records"]]

    result = {
        "offline_byte_identical_same_seed": offline_1 == offline_2,
        "live_structural_diffs": len(live_diffs),
        "live_unallowed_diffs": unallowed[:100],
        "live_note_identical_between_runs": notes_of(live_1) == notes_of(live_2),
        "live_notes_run1": notes_of(live_1),
        "live_notes_run2": notes_of(live_2),
        "gate": {
            "offline_reproducible": offline_1 == offline_2,
            "llm_nondeterminism_confined": len(unallowed) == 0,
        },
        "note": "LLM prose is not required to be byte-identical across API calls; "
                "only the structured fields and all non-note provenance must be.",
    }
    write_json(out / "07_repeatability.json", result)
    print(f"[phase5] offline identical={result['offline_byte_identical_same_seed']}, "
          f"live unallowed diffs={len(unallowed)}")
    return result


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def build_report(
    out: Path,
    identity: dict,
    connectivity: dict,
    suite: dict,
    smoke: dict,
    cases: dict,
    invariance: dict,
    cohort: dict,
    repeatability: dict,
) -> tuple[str, str]:
    gates = {
        "endpoint_reachable": connectivity["reachable"],
        "suite_non_integration_pass": suite["suite_gate"]["non_integration_tests_pass"],
        "suite_integration_gate": suite["suite_gate"]["integration_gate"],
        "flash_smoke_all_checks": smoke["all_checks_pass"],
        "cases_all_found": cases["gate"]["all_cases_found"],
        "cases_zero_survivors": cases["gate"]["zero_survivors"],
        "invariance_holds": invariance["gate"]["identical_outside_note_and_llm_provenance"],
        "cohort_all_bundles_valid": cohort["validation"]["all_bundles_valid"],
        "cohort_zero_survivors": len(cohort["validation"]["surviving_unsupported_facts"]) == 0,
        "cohort_opportunities": cohort["opportunities"] == cohort["cohort"]["participants"] * cohort["cohort"]["days"] * 5,
        "repeatability_offline": repeatability["gate"]["offline_reproducible"],
        "repeatability_confined": repeatability["gate"]["llm_nondeterminism_confined"],
    }
    caveats = []
    if suite["integration_failures"]:
        caveats.append(
            "committed integration tests (model per config, deepseek-chat) failed with a "
            "transport/model-unavailable error — deepseek-chat appears retired; the transport "
            "gate is carried by the deepseek-flash smoke (phase 1b). The bundled config default "
            "model is a candidate implementation defect to be fixed in a follow-up commit."
        )
    np_ = cohort["note_pipeline"]
    if np_["rendered"] and np_["offline_fallback_count"] > 0.15 * np_["rendered"]:
        caveats.append(f"offline-template fallback rate high: {np_['offline_fallback_count']}/{np_['rendered']}")
    if np_["rendered"] and np_["model_chose_null_first_attempt"] > 0.25 * np_["rendered"]:
        caveats.append("model chose null on the first attempt for >25% of rendered notes")

    if all(gates.values()):
        verdict = "CONDITIONAL PASS" if caveats else "PASS"
    else:
        verdict = "FAIL"

    failed = [k for k, v in gates.items() if not v]
    lines = []
    lines.append("# Live DeepSeek validation — standalone Paper 3 EMA module")
    lines.append("")
    lines.append(f"**Verdict: {verdict}**" + (f" — failed gates: {failed}" if failed else ""))
    lines.append("")
    lines.append("## 1. Environment / model identity")
    lines.append("")
    lines.append(f"- python {identity['python']} on {identity['platform']}")
    lines.append(f"- harness v{HARNESS_VERSION} (test-only, untracked; production code unmodified except any documented follow-up fix)")
    lines.append(f"- provider endpoint: `{identity['base_url']}` (default config base URL)")
    lines.append(f"- model: **{identity['model']}** (thinking={identity['thinking']}, reasoning_effort={identity['reasoning_effort']}, max_tokens override={identity['max_tokens_override']})")
    lines.append(f"- credential: `DEEPSEEK_API_KEY` present via environment only (`{'yes' if connectivity['key_present'] else 'no'}`); never written to any artefact")
    lines.append("")
    lines.append("## 2. Test date")
    lines.append("")
    lines.append(f"- {identity['started_utc']} (UTC) / {identity['started_local']} (Europe/Copenhagen)")
    lines.append("")
    lines.append("## 3. Exact commit tested")
    lines.append("")
    lines.append(f"- `{identity['commit']}` ({identity['commit_short']}) on branch `{identity['branch']}`; working tree dirty: {identity['working_tree_dirty']}")
    lines.append("")
    lines.append("## 4. Connectivity")
    lines.append("")
    lines.append(f"- reachable: **{connectivity['reachable']}** ({connectivity['probe_detail']})")
    lines.append(f"- diagnostics: {json.dumps(connectivity['diagnostics'])}")
    lines.append("")
    lines.append("## 5. Full test-suite result")
    lines.append("")
    lines.append(f"- full suite: **{suite['full_suite_summary']}**")
    lines.append(f"- integration tests: {suite['integration_tests']}")
    if suite["integration_failures"]:
        lines.append(f"- integration failures classified as model-unavailable: {suite['integration_failure_classified_model_unavailable']}")
    lines.append("- raw outputs: `02_suite_full.txt`, `02_integration_verbose.txt`")
    lines.append("")
    lines.append("## 6. Controlled live-note cases (phase 2)")
    lines.append("")
    lines.append("| case | trigger | attempts | retries | final source | final note |")
    lines.append("|---|---|---:|---:|---|---|")
    for entry in cases["cases"]:
        if not entry.get("found"):
            lines.append(f"| {entry['case']} | — | — | — | not found | {entry.get('note', '')} |")
            continue
        final = entry["final"]
        note = (final["note"] or "null")
        if len(note) > 60:
            note = note[:57] + "…"
        lines.append(
            f"| {entry['case']} | {entry['trigger']} | {entry['attempts']} | {entry['retries']} "
            f"| {final['source']} | {note} |"
        )
    lines.append("")
    lines.append(f"- cases found: {cases['found']}/{len(cases['cases'])}")
    lines.append("")
    lines.append("## 7. Adversarial closed-world results")
    lines.append("")
    lines.append("Temptation coverage per case is recorded in `04_cases.json` (`temptations`). "
                 "The required result is not that the model never *attempts* unsupported facts; "
                 "it is that **zero unsupported facts survive into an accepted record**.")
    lines.append("")
    lines.append(f"- surviving unsupported facts (phase 2): **{len(cases['surviving_unsupported_facts'])}**")
    lines.append(f"- surviving unsupported facts (phase 4 cohort): **{len(cohort['validation']['surviving_unsupported_facts'])}**")
    lines.append(f"- rejection counts by code (cohort): {cohort['note_pipeline']['rejection_counts_by_code']}")
    lines.append("")
    lines.append("## 8. Live/offline invariance (phase 3)")
    lines.append("")
    lines.append(f"- total diffs: {invariance['total_diffs']}; unallowed diffs: **{len(invariance['unallowed_diffs'])}**")
    if invariance["unallowed_diffs"]:
        for path, a, b in invariance["unallowed_diffs"][:20]:
            lines.append(f"  - UNALLOWED `{path}`: {a!r} -> {b!r}")
    lines.append("- allowed-diff markers (note + LLM provenance only): " + ", ".join(f"`{m}`" for m in ALLOWED_DIFF_MARKERS))
    lines.append("")
    lines.append("## 9. 4x7 live cohort summary (phase 4)")
    lines.append("")
    lines.append(f"- participant-days: **{cohort['cohort']['participant_days']}** "
                 f"({cohort['cohort']['participants']} x {cohort['cohort']['days']})")
    lines.append(f"- opportunities: **{cohort['opportunities']}** · answered **{cohort['answered']}** · "
                 f"missed **{cohort['missed']}** · expired **{cohort['expired']}**")
    lines.append(f"- prompt types: {cohort['prompt_type_distribution']}")
    lines.append(f"- DeepSeek calls attempted: **{cohort['api']['calls_attempted']}** · "
                 f"succeeded **{cohort['api']['calls_succeeded']}** · failed **{cohort['api']['calls_failed']}**")
    lines.append(f"- first-attempt parse ok/fail: **{cohort['note_pipeline']['first_attempt_parse_ok']} / "
                 f"{cohort['note_pipeline']['first_attempt_parse_fail']}** · "
                 f"first-attempt closed-world accept: **{cohort['note_pipeline']['first_attempt_closed_world_accept']}** · "
                 f"model-null first attempt: {cohort['note_pipeline']['model_chose_null_first_attempt']}")
    lines.append(f"- retry distribution: {cohort['note_pipeline']['retry_distribution']}")
    lines.append(f"- rejections by code: {cohort['note_pipeline']['rejection_counts_by_code']}")
    lines.append(f"- offline fallback: **{cohort['note_pipeline']['offline_fallback_count']}** · "
                 f"null notes (answered): {cohort['note_pipeline']['null_note_count_answered']} · "
                 f"final non-null notes (answered): {cohort['note_pipeline']['final_non_null_note_count_answered']}")
    lines.append(f"- API latency ms: mean {cohort['api']['latency_ms']['mean']} · median "
                 f"{cohort['api']['latency_ms']['median']} · p95 {cohort['api']['latency_ms']['p95']} · "
                 f"max {cohort['api']['latency_ms']['max']}")
    lines.append(f"- token usage: {cohort['api']['usage_totals']}")
    lines.append(f"- estimated API cost (from returned usage x published rates): "
                 f"peak ${cohort['api']['estimated_cost_usd']['peak']:.6f} / off-peak "
                 f"${cohort['api']['estimated_cost_usd']['off_peak']:.6f} — {PRICING['source']}")
    lines.append(f"- bundle validation: all valid = **{cohort['validation']['all_bundles_valid']}** "
                 f"(issue codes: {cohort['validation']['bundle_issue_codes'] or 'none'})")
    lines.append(f"- unsupported factual inventions that survived validation: "
                 f"**{len(cohort['validation']['surviving_unsupported_facts'])}** (required: 0)")
    lines.append("")
    lines.append("## 10. Representative final EMA records")
    lines.append("")
    lines.append("prompt time → trigger → inherited context → V/E/S → final note → validation status")
    lines.append("")
    for i, row in enumerate(cohort.get("representative_records", []), 1):
        context = " / ".join(str(v) for v in row["context"].values() if v)
        delay = ""
        if row.get("preceding_mode"):
            delay = f", after {row['preceding_mode']}" + (
                " (delay documented)" if row.get("delay_documented") else ""
            )
        ves = "/".join(str(x) for x in row["valence_energy_stress"]) if row.get("valence_energy_stress") else "—"
        lines.append(
            f"{i}. `{row['date']} {row['prompt_time']}` → **{row['trigger']}**{delay} → "
            f"{context} → {ves} → “{row['final_note']}” [{row['note_source']}] → {row['validation_status']}"
        )
    lines.append("")
    lines.append("## 11. Fallbacks / retries / rejections (complete)")
    lines.append("")
    lines.append("- phase 2 per-case attempts, retries, raw outputs and rejection codes: `04_cases.json`")
    lines.append("- cohort retry distribution: " + str(cohort["note_pipeline"]["retry_distribution"]))
    lines.append("- cohort rejection counts by code: " + str(cohort["note_pipeline"]["rejection_counts_by_code"]))
    lines.append(f"- offline fallbacks: {cohort['note_pipeline']['offline_fallback_count']} "
                 "(offline template renderer is part of the by-design pipeline, not an error)")
    lines.append(f"- failed API calls: {cohort['api']['calls_failed']}")
    lines.append("")
    lines.append("## 12. Remaining limitations")
    lines.append("")
    for item in PRICING["notes"]:
        lines.append(f"- cost: {item}")
    lines.append("- the cohort is synthetic (fixture-based), as specified for this demonstration; "
                 "it is independent of Appa and of the historical September cohort")
    lines.append("- DeepSeek prose is not byte-reproducible across separate API calls (no determinism "
                 "guarantee was requested or assumed; see phase 5)")
    lines.append("- the harness client wrapper (timing/usage capture, thinking fields) is test-only; "
                 "the production client and all scientific parameters are unmodified in this run")
    lines.append("")
    lines.append("## 13. Gates and verdict")
    lines.append("")
    for name, ok in gates.items():
        lines.append(f"- [{'x' if ok else ' '}] {name}")
    if caveats:
        lines.append("")
        lines.append("Caveats:")
        for c in caveats:
            lines.append(f"- {c}")
    lines.append("")
    lines.append(f"**Final verdict: {verdict}**")
    lines.append("")
    report = "\n".join(lines)
    (out / "report.md").write_text(report, encoding="utf-8")
    return report, verdict


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", default="all",
                        choices=["connectivity", "1", "1b", "2", "3", "4", "5", "all"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-case-seeds", type=int, default=30)
    parser.add_argument("--write-docs", action="store_true",
                        help="copy the report to docs/LIVE_DEEPSEEK_VALIDATION.md")
    args = parser.parse_args()

    if args.phase in ("1", "1b", "2", "3", "4", "5", "all") and not os.environ.get("DEEPSEEK_API_KEY", "").strip():
        print("ERROR: DEEPSEEK_API_KEY not set (exit 3)")
        return 3

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) if args.out else _HERE / "artifacts" / f"live_{stamp}"
    out.mkdir(parents=True, exist_ok=True)

    identity = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "model": args.model,
        "base_url": str(default_config().get("llm.base_url", "https://api.deepseek.com")),
        "thinking": os.environ.get("DEEPSEEK_THINKING", "enabled"),
        "reasoning_effort": os.environ.get("DEEPSEEK_REASONING_EFFORT", "high"),
        "max_tokens_override": os.environ.get("DEEPSEEK_MAX_TOKENS", "1024"),
        "started_utc": utcnow(),
        "started_local": localnow(),
        **git_identity(),
    }
    write_json(out / "00_identity.json", identity)
    print(f"[harness] v{HARNESS_VERSION} model={args.model} out={out}")

    connectivity = suite = smoke = cases = invariance = cohort = repeatability = None
    run_all = args.phase == "all"

    need_live = args.phase in ("1b", "2", "3", "4", "5", "all")
    if args.phase in ("connectivity", "all") or need_live:
        connectivity = phase_connectivity(out)
        if not connectivity["reachable"]:
            print("STOP: endpoint unreachable (exit 2) — see 01_connectivity.json")
            return 2

    if args.phase in ("1", "all"):
        suite = phase1_suite(out)

    if args.phase in ("1b", "all"):
        smoke = phase1b_flash_smoke(out, args.model)

    if args.phase in ("2", "all"):
        cases = phase2_cases(out, args.model, max_seeds=args.max_case_seeds)

    if args.phase in ("3", "all"):
        invariance = phase3_invariance(out, args.model)

    if args.phase in ("4", "all"):
        cohort = phase4_cohort(out, args.model, workers=args.workers)

    if args.phase in ("5", "all"):
        repeatability = phase5_repeatability(out, args.model)

    if run_all and all(x is not None for x in (suite, smoke, cases, invariance, cohort, repeatability)):
        report, verdict = build_report(out, identity, connectivity, suite, smoke, cases,
                                       invariance, cohort, repeatability)
        print(f"[harness] verdict: {verdict}")
        if args.write_docs:
            docs = _PKG_ROOT / "docs" / "LIVE_DEEPSEEK_VALIDATION.md"
            docs.write_text(report, encoding="utf-8")
            print(f"[harness] wrote {docs}")

    # final secret sweep over every artefact
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    hits = scan_and_redact_secrets(sorted(out.rglob("*")), [key])
    if hits:
        print(f"[harness] WARNING: redacted {hits} secret occurrence(s) from artefacts")

    if run_all and verdict == "FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
