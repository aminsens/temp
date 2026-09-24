"""Offline self-tests for the live validation harness (no network, no key).

Run:  /home/user/.venv-ema/bin/python -m pytest live_validation -q

These verify the harness machinery that the live run depends on:
* the structural diff + allowed-diff filtering (phase 3/5 logic)
* the controlled-case matrix actually finds matching records for every case
* the cost estimator arithmetic
* the secret redaction sweep (phase: final artefact scan)
* the report/verdict builder
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_harness as lh  # noqa: E402


# ---------------------------------------------------------------------------
# structural diff + allow-list
# ---------------------------------------------------------------------------

def test_deep_diff_detects_and_allowlist_filters():
    base = {
        "records": [
            {"response": {"context_note": "hello", "note_source": "llm",
                          "latency_min": 2.0, "valence": 4}},
        ],
        "provenance": {"llm_calls": 1, "llm_model": "x", "config_hash": "h"},
        "summary": {"notes_rendered": 1, "answered": 4},
    }
    tampered = json.loads(json.dumps(base))
    tampered["records"][0]["response"]["context_note"] = "world"      # allowed
    tampered["records"][0]["response"]["note_source"] = "offline_template"  # allowed
    tampered["provenance"]["llm_calls"] = 3                          # allowed
    tampered["summary"]["notes_rendered"] = 2                        # allowed
    tampered["records"][0]["response"]["latency_min"] = 3.5          # NOT allowed
    tampered["records"][0]["response"]["valence"] = 2                # NOT allowed

    diffs = list(lh.deep_diff(base, tampered))
    assert len(diffs) == 6
    unallowed = [d for d in diffs if not lh.is_allowed_diff(d[0])]
    assert {d[0] for d in unallowed} == {
        "$.records[0].response.latency_min",
        "$.records[0].response.valence",
    }


def test_deep_diff_identical_is_empty():
    data = {"a": [1, {"b": None, "c": [2, 3]}], "s": "x"}
    assert list(lh.deep_diff(data, json.loads(json.dumps(data)))) == []


def test_invariance_allowlist_covers_per_record_llm_provenance():
    """Regression: the allow-list must cover the per-record LLM note-rendering
    telemetry keys at BOTH bundle level ($.provenance.record_provenance.<pid>
    .<key>) and inside each record's provenance copy
    ($.records[i].provenance.record_provenance.<pid>.<key>).

    A narrower list (bundle-level `provenance.llm_*` only) silently classified
    the 139 per-record diffs of the live run live_20260924-192504 as unallowed,
    which would have flipped the invariance gate on any re-run.
    """
    allowed = [
        "$.provenance.record_provenance.ema-x.llm_model",
        "$.provenance.record_provenance.ema-x.llm_provider",
        "$.provenance.record_provenance.ema-x.llm_decoding",
        "$.provenance.record_provenance.ema-x.note_attempts",
        "$.provenance.record_provenance.ema-x.note_fallback_reason",
        "$.provenance.record_provenance.ema-x.note_rejected_codes.length",
        "$.provenance.record_provenance.ema-x.retry_count",
        "$.records[2].provenance.record_provenance.ema-x.llm_model",
        "$.records[2].provenance.record_provenance.ema-x.note_attempts",
        "$.records[2].response.note_validation.attempts",
        "$.records[2].response.context_note",
        "$.provenance.llm_calls",
        "$.provenance.llm_retries",
        "$.provenance.llm_template_version",
        "$.summary.note_sources.llm",
    ]
    for path in allowed:
        assert lh.is_allowed_diff(path), f"expected allowed: {path}"

    # Non-LLM fields must remain protected — the gate's whole point.
    denied = [
        "$.records[0].prompt.episode_id",
        "$.records[0].prompt.prompt_time_min",
        "$.records[0].response.latency_min",
        "$.records[0].response.subjective.valence",
        "$.records[0].packet.activity",
        "$.provenance.request_hash",
        "$.provenance.context_fingerprint",
        "$.provenance.record_provenance.ema-x.episode_id",
        "$.summary.answered",
        "$.summary.trigger_counts.semi_random",
    ]
    for path in denied:
        assert not lh.is_allowed_diff(path), f"expected denied: {path}"


# ---------------------------------------------------------------------------
# cost estimator
# ---------------------------------------------------------------------------

def test_cost_estimator_arithmetic():
    totals = {"prompt_tokens": 1_000_000, "completion_tokens": 100_000, "cached_tokens": 900_000}
    cost = lh._estimate_cost(totals)
    # peak: 0.1M*0.30 + 0.9M*0.006 + 0.1M*1.20 = 0.03 + 0.0054 + 0.12 = 0.1554
    assert cost["peak"] == pytest.approx(0.1554, abs=1e-9)
    # off-peak: 0.1M*0.15 + 0.9M*0.003 + 0.1M*0.60 = 0.015 + 0.0027 + 0.06 = 0.0777
    assert cost["off_peak"] == pytest.approx(0.0777, abs=1e-9)


def test_cost_estimator_clamps_cached_to_prompt():
    # cached is clamped to prompt_tokens; all prompt tokens then bill at the cache-hit rate
    cost = lh._estimate_cost({"prompt_tokens": 100, "completion_tokens": 0, "cached_tokens": 500})
    assert cost["peak"] == pytest.approx(100 / 1e6 * 0.006, abs=1e-12)


# ---------------------------------------------------------------------------
# case matrix: every case must find a matching answered record (offline)
# ---------------------------------------------------------------------------

def test_case_matrix_finds_records():
    missing = []
    for spec in lh.CASES:
        bundle, record, seed = lh.find_case_record(spec, max_seeds=30)
        if record is None:
            missing.append(spec["name"])
            continue
        assert record.response.answered
        assert record.response.subjective is not None
        # the record's packet must satisfy the case predicate
        assert spec["predicate"](record)
    assert not missing, f"cases with no matching record: {missing}"
    assert len({c["name"] for c in lh.CASES}) >= 15


# ---------------------------------------------------------------------------
# secret redaction
# ---------------------------------------------------------------------------

def test_secret_redaction(tmp_path):
    key = "sk-" + "a1b2c3d4" * 4
    p1 = tmp_path / "art1.json"
    p1.write_text(json.dumps({"raw_model_output": f"Bearer {key} appears here"}), encoding="utf-8")
    p2 = tmp_path / "art2.json"
    p2.write_text(json.dumps({"clean": "no secrets"}), encoding="utf-8")
    hits = lh.scan_and_redact_secrets([p1, p2], [key])
    assert hits >= 1
    assert key not in p1.read_text(encoding="utf-8")
    assert "[REDACTED-SECRET]" in p1.read_text(encoding="utf-8")
    # a generic sk- pattern without an explicit needle is redacted too
    p3 = tmp_path / "art3.json"
    p3.write_text(json.dumps({"x": "leak sk-ffffffffffffffffffffffffffffffff end"}), encoding="utf-8")
    lh.scan_and_redact_secrets([p3], [])
    assert "sk-ffffffffffffffffffffffffffffffff" not in p3.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# report / verdict builder
# ---------------------------------------------------------------------------

def _minimal_phase_results():
    connectivity = {"reachable": True, "probe_detail": "HTTP 401", "key_present": True,
                    "diagnostics": {"dns": "ok", "tcp": "ok", "tls": "ok"}, "checked_utc": "t"}
    suite = {"integration_tests": {}, "integration_failures": [],
             "integration_failure_classified_model_unavailable": False,
             "failure_excerpt": "", "full_suite_summary": "132 passed, 7 skipped in 40s",
             "non_integration_failed_lines": [],
             "suite_gate": {"non_integration_tests_pass": True, "integration_gate": True},
             "note": ""}
    smoke = {"model": "deepseek-flash",
             "raw_call": {"content": "ok", "metric": {"ok": True}, "ok": True},
             "bundle": {"llm_calls": 5, "llm_retries": 0, "notes_checked": 4,
                        "note_sources": {"llm": 4, "offline_template": 0}},
             "checks": {k: True for k in ("auth_succeeded", "expected_model_used",
                                          "request_shape_accepted", "response_parsing_succeeded",
                                          "retry_bounds_intact", "closed_world_acceptance",
                                          "bundle_validation")},
             "all_checks_pass": True}
    cases = {"model": "deepseek-flash", "cases": [], "found": 15,
             "surviving_unsupported_facts": [],
             "gate": {"all_cases_found": True, "zero_survivors": True}}
    invariance = {"day": "p", "seed": 7, "total_diffs": 3, "allowed_diffs": [],
                  "unallowed_diffs": [],
                  "gate": {"identical_outside_note_and_llm_provenance": True}}
    cohort = {
        "model": "deepseek-flash",
        "cohort": {"participants": 4, "days": 7, "participant_days": 28},
        "opportunities": 140, "answered": 125, "missed": 12, "expired": 3,
        "prompt_type_distribution": {"semi_random": 95, "post_trip": 30,
                                     "post_active_episode": 10, "context_transition": 5},
        "api": {"calls_attempted": 128, "calls_succeeded": 128, "calls_failed": 0,
                "latency_ms": {"mean": 900.0, "median": 700.0, "p95": 2500.0, "max": 4000.0},
                "usage_totals": {"prompt_tokens": 200000, "completion_tokens": 20000,
                                 "cached_tokens": 0, "reasoning_tokens": 0},
                "estimated_cost_usd": {"peak": 0.084, "off_peak": 0.042},
                "pricing": lh.PRICING},
        "note_pipeline": {"rendered": 128, "first_attempt_parse_ok": 126,
                          "first_attempt_parse_fail": 2,
                          "first_attempt_closed_world_accept": 120,
                          "model_chose_null_first_attempt": 4,
                          "retry_distribution": {"0": 124, "1": 3, "2": 1},
                          "rejection_counts_by_code": {"unsupported_reference": 6},
                          "offline_fallback_count": 2, "null_note_count_answered": 6,
                          "final_non_null_note_count_answered": 119},
        "validation": {"all_bundles_valid": True, "bundle_issue_codes": {},
                       "surviving_unsupported_facts": []},
        "representative_records": [],
    }
    repeatability = {"offline_byte_identical_same_seed": True,
                     "live_structural_diffs": 4, "live_unallowed_diffs": [],
                     "live_note_identical_between_runs": False,
                     "live_notes_run1": ["a"], "live_notes_run2": ["b"],
                     "gate": {"offline_reproducible": True, "llm_nondeterminism_confined": True},
                     "note": ""}
    identity = {"python": "3.12", "platform": "x", "model": "deepseek-flash",
                "base_url": "https://api.deepseek.com", "thinking": "enabled",
                "reasoning_effort": "high", "max_tokens_override": "1024",
                "started_utc": "2026-09-24T00:00:00+00:00", "started_local": "2026-09-24T02:00:00+02:00",
                "commit": "abc123" * 5, "commit_short": "abc123", "branch": "b",
                "working_tree_dirty": False}
    return identity, connectivity, suite, smoke, cases, invariance, cohort, repeatability


def test_report_builder_verdicts(tmp_path):
    phases = _minimal_phase_results()
    report, verdict = lh.build_report(tmp_path, *phases)
    assert verdict == "PASS"
    assert "Final verdict: PASS" in report
    assert (tmp_path / "report.md").exists()

    # a survivor breaks the gate -> FAIL
    phases[6]["validation"]["surviving_unsupported_facts"] = [{"note": "bad"}]
    _, verdict2 = lh.build_report(tmp_path, *phases)
    assert verdict2 == "FAIL"

    # unallowed invariance diff -> FAIL
    phases = _minimal_phase_results()
    phases[5]["gate"]["identical_outside_note_and_llm_provenance"] = False
    phases[5]["unallowed_diffs"] = [("$.records[0].response.latency_min", 1, 2)]
    _, verdict3 = lh.build_report(tmp_path, *phases)
    assert verdict3 == "FAIL"

    # chat-model unavailability -> CONDITIONAL PASS (transport gate carried by 1b)
    phases = _minimal_phase_results()
    phases[2]["integration_failures"] = ["test_real_llm_end_to_end_bundle"]
    phases[2]["suite_gate"] = {"non_integration_tests_pass": True, "integration_gate": True}
    _, verdict4 = lh.build_report(tmp_path, *phases)
    assert verdict4 == "CONDITIONAL PASS"
