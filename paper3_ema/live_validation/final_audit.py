#!/usr/bin/env python3
"""Final acceptance audit against the ACTUAL live-generated EMA data.

Re-computes every protocol invariant independently (does NOT trust the
harness' own numbers):

  A1   exactly five prompts per day, strictly increasing
  A2   event/background balance (>=3 semi-random, <=2 event-enriched)
  A3   schedule auditor status VALID
  A4   exclusions: no prompt inside sleep/driving/cycling/running/vigorous,
       non-realised episodes, unresolved or unstable minutes
  A5   prompt-time linkage: episode/interval ids and inherited-context
       fields must equal the day's values AT the prompt time; post_trip
       must reference a journey that ended before the prompt
  A6   response/missed/expired semantics + counts (vs 06_cohort.json)
  A7   latency: >=0, answered <=10 min, expired >10, right-skewed cohort
  A8   valence/energy/stress in 1..5 and non-degenerate
  A9   zero inherited-context mutations: regenerated day fingerprint and
       request hash must equal the bundle provenance
  A10  zero unsupported facts surviving note validation (every stored note)
  A11  live-LLM invariance: live bundle vs independently regenerated
       OFFLINE bundle — only note/LLM-provenance fields may differ
  A12  dashboard agreement: every value embedded in dashboard/index.html
       must equal the raw artefacts / bundles

Writes: live_validation/audit_out/final_audit.json + prints a summary.
Exit code 0 = all checks pass, 1 = failures.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from statistics import mean, median, pstdev

_HERE = Path(__file__).resolve().parent
_PKG_ROOT = _HERE.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from paper3_ema.config import default_config                      # noqa: E402
from paper3_ema.day import contextual_day_from_mapping            # noqa: E402
from paper3_ema.fixtures import demo_cohort                       # noqa: E402
from paper3_ema.notes import validate_note                        # noqa: E402
from paper3_ema.pipeline import as_request, generate_ema          # noqa: E402
from paper3_ema.validate import validate_bundle                   # noqa: E402

RUN = _HERE / "artifacts" / "live_20260924-192504"
DASH = _HERE / "dashboard" / "index.html"
OUT = _HERE / "audit_out"

EXCLUDED_ACTIVITIES = {"sleeping", "lying_awake", "driving", "cycling", "running", "other_vigorous"}
ACTIVE_EPISODE_ACTIVITIES = {"running", "other_vigorous", "walking"}

# Mirrors live_harness.ALLOWED_DIFF_MARKERS (kept in sync; regression-tested
# in live_validation/test_harness_offline.py). Per-record LLM note-rendering
# telemetry keys are dot-anchored so they match at both bundle level
# ($.provenance.record_provenance.<prompt_id>.<key>) and inside each record's
# provenance copy ($.records[i].provenance.record_provenance.<prompt_id>.<key>).
ALLOWED_DIFF_MARKERS = (
    ".context_note", ".note_source", ".note_validation", ".note_result",
    ".llm_provider", ".llm_model", ".llm_decoding",
    ".note_attempts", ".note_fallback_reason", ".note_rejected_codes", ".retry_count",
    "provenance.llm_template_version", ".llm_calls", ".llm_retries",
    "summary.notes_rendered", "summary.notes_null", "summary.note_sources",
)


def deep_diff(a, b, path="$"):
    if type(a) is not type(b):
        if a != b:
            yield (path, a, b)
        return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                yield (f"{path}.{k}", None, b[k])
            elif k not in b:
                yield (f"{path}.{k}", a[k], None)
            else:
                yield from deep_diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield (f"{path}.length", len(a), len(b))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            yield from deep_diff(x, y, f"{path}[{i}]")
    else:
        if a != b:
            yield (path, a, b)


def parse_bundles(text: str):
    dec = json.JSONDecoder()
    bundles, idx = [], 0
    while idx < len(text):
        while idx < len(text) and text[idx] in " \t\r\n":
            idx += 1
        if idx >= len(text):
            break
        obj, end = dec.raw_decode(text, idx)
        bundles.append(obj)
        idx = end
    return bundles


def main() -> int:
    config = default_config()
    bundles = parse_bundles((RUN / "06_cohort_bundles.jsonl").read_text())
    cohort_json = json.loads((RUN / "06_cohort.json").read_text())

    # regenerate the exact cohort inputs (deterministic)
    cohort_days = demo_cohort(participants=4, days=7, start_date="2026-05-04", seed=20260504)
    day_map = {(d["participant_id"], d["date"]): d for d in cohort_days}

    results: dict = {"days": 0, "records": 0, "checks": {}, "failures": []}

    def check(name: str, ok: bool, detail: str = ""):
        results["checks"][name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            results["failures"].append(f"{name}: {detail}")

    offline_by_id: dict = {}
    live_by_pid_date: dict = {}

    for b in bundles:
        pid = b["participant_id"]
        date = b["day_date"]
        live_by_pid_date[(pid, date)] = b
        results["days"] += 1

        mapping = day_map.get((pid, date))
        check(f"day_input_regen[{pid}/{date}]", mapping is not None,
              "cohort day could not be regenerated deterministically")
        if mapping is None:
            continue
        day = contextual_day_from_mapping(mapping)
        records = b["records"]
        results["records"] += len(records)

        # ---- A1 five prompts, increasing -----------------------------------
        check(f"A1_count[{pid}/{date}]", len(records) == 5, f"{len(records)} prompts")
        tmins = [r["prompt"]["prompt_time_min"] for r in records]
        check(f"A1_increasing[{pid}/{date}]", tmins == sorted(tmins) and len(set(tmins)) == 5,
              str(tmins))

        # ---- A2 balance -----------------------------------------------------
        triggers = [r["prompt"]["trigger"] for r in records]
        semi = triggers.count("semi_random")
        check(f"A2_balance[{pid}/{date}]", semi >= 3 and (5 - semi) <= 2,
              f"semi={semi} event={5 - semi}")

        # ---- A3 auditor -----------------------------------------------------
        check(f"A3_audit[{pid}/{date}]",
              b.get("audit", {}).get("status") == "VALID",
              json.dumps(b.get("audit", {}).get("status")))

        # ---- offline regeneration (for A9/A10/A11) --------------------------
        off_bundle = generate_ema(mapping, seed=20260504, llm_client=None)
        offline_by_id[(pid, date)] = off_bundle

        # ---- A9 fingerprints / request hash ---------------------------------
        prov = b["provenance"]
        req = as_request(mapping, seed=20260504)
        check(f"A9_fingerprint[{pid}/{date}]",
              prov.get("context_fingerprint") == req.context_fingerprint(),
              f"{prov.get('context_fingerprint')} vs {req.context_fingerprint()}")
        check(f"A9_request_hash[{pid}/{date}]",
              prov.get("request_hash") == req.hash(),
              f"{prov.get('request_hash')} vs {req.hash()}")

        # ---- per-record checks ---------------------------------------------
        off_records = {r.prompt.prompt_id: r for r in off_bundle.records}
        for rec in records:
            p = rec["prompt"]
            t = p["prompt_time_min"]
            tag = f"[{pid}/{date}/{p['prompt_id']}]"
            ep = day.episode_at(t)
            iv = day.interval_at(t)

            # ---- A4 exclusions ------------------------------------------------
            viol = []
            if ep is None:
                viol.append("no episode at prompt time")
            else:
                if ep.activity is not None and ep.activity.value in EXCLUDED_ACTIVITIES:
                    viol.append(f"excluded activity {ep.activity.value}")
                if not ep.is_realised:
                    viol.append("non-realised episode")
                if ep.is_unstable and not p.get("stability_relaxed"):
                    viol.append(f"unstable episode (stability={ep.stability})")
                if ep.is_unresolved and not p.get("stability_relaxed"):
                    viol.append(f"unresolved episode (stability={ep.stability})")
            if iv is not None and iv.is_excluding and not p.get("stability_relaxed"):
                viol.append(f"excluding interval (resolved={iv.resolved}, realised={iv.realised})")
            check(f"A4_exclusions{tag}", not viol, "; ".join(viol))

            # ---- A5 linkage at prompt time ------------------------------------
            viol = []
            if ep is not None and p.get("episode_id") != ep.episode_id:
                viol.append(f"episode_id {p.get('episode_id')} != {ep.episode_id}")
            if iv is not None and p.get("interval_id") is not None and p.get("interval_id") != iv.interval_id:
                viol.append(f"interval_id {p.get('interval_id')} != {iv.interval_id}")
            ic = p.get("inherited_context", {})
            if ep is not None:
                expect = {
                    "activity": ep.activity.value if ep.activity else None,
                    "domain": ep.domain.value if ep.domain else None,
                    "place_type": ep.place_type.value if ep.place_type else None,
                    "social_context": ep.social.value if ep.social else None,
                    "indoor_outdoor": ep.indoor_outdoor.value if ep.indoor_outdoor else None,
                }
                for k, v in expect.items():
                    if ic.get(k) != v:
                        viol.append(f"inherited {k}={ic.get(k)!r} != day {v!r}")
            if p["trigger"] == "post_trip":
                jn = next((j for j in day.journeys if j.journey_id == p.get("journey_id")), None)
                if jn is None:
                    viol.append(f"post_trip journey {p.get('journey_id')} not in day")
                else:
                    if not (jn.end_min <= t):
                        viol.append("post_trip prompt not after journey end")
                    pm = (p.get("packet", {}).get("preceding_journey_mode"))
                    if pm and jn.mode and pm.lower() != jn.mode.lower():
                        viol.append(f"preceding mode {pm} != journey mode {jn.mode}")
                mfe = p.get("minutes_after_event")
                if mfe is not None and mfe < 0:
                    viol.append(f"minutes_after_event {mfe} < 0")
            else:
                jn_at = day.journey_at(t)
                if jn_at is None and p.get("journey_id") is not None:
                    viol.append(f"bg prompt journey_id {p.get('journey_id')} but no journey at t")
                if jn_at is not None and p.get("journey_id") != jn_at.journey_id:
                    viol.append(f"bg journey_id {p.get('journey_id')} != {jn_at.journey_id}")
            check(f"A5_linkage{tag}", not viol, "; ".join(viol))

            # packet fingerprint recorded in provenance
            rp = prov.get("record_provenance", {}).get(p["prompt_id"], {})
            off = off_records.get(p["prompt_id"])
            if off is not None:
                check(f"A5_packet_fp{tag}",
                      rp.get("packet_fingerprint") == off.packet.fingerprint(12),
                      f"{rp.get('packet_fingerprint')} vs {off.packet.fingerprint(12)}")

            # ---- A6/A7 status + latency ---------------------------------------
            r = rec["response"]
            lat = r.get("latency_min")
            st = r["status"]
            viol = []
            if st == "answered":
                if lat is None or lat > 10.0:
                    viol.append(f"answered latency {lat} not in (0,10]")
                if r.get("subjective") is None:
                    viol.append("answered without subjective")
            elif st == "expired":
                if lat is None or lat <= 10.0:
                    viol.append(f"expired latency {lat} not >10")
                if r.get("usable_for_alignment"):
                    viol.append("expired usable_for_alignment=True")
            elif st == "missed":
                if lat is not None or r.get("response_time") is not None or r.get("subjective") is not None:
                    viol.append("missed carries response data")
            else:
                viol.append(f"unknown status {st}")
            if lat is not None and lat < 0:
                viol.append(f"negative latency {lat}")
            check(f"A6_status{tag}", not viol, "; ".join(viol))

            # ---- A8 values ------------------------------------------------------
            subj = r.get("subjective")
            if subj is not None:
                vals = [subj.get(k) for k in ("valence", "energy", "stress")]
                bad = [v for v in vals if v is None or not (1 <= int(v) <= 5)]
                check(f"A8_range{tag}", not bad, str(vals))
            else:
                check(f"A8_range{tag}", st == "missed", f"status {st} without subjective")

            # ---- A10 note validation (against the identical offline packet) ----
            note = r.get("context_note")
            if note is not None:
                off = off_records.get(p["prompt_id"])
                ok = bool(off is not None and validate_note(note, off.packet, config).valid)
                check(f"A10_note{tag}", ok, f"note rejected: {note!r}")
            elif r.get("note_source") not in (None,):
                check(f"A10_note{tag}", True, "null note (acceptable)")

        # ---- A11 invariance: live vs regenerated offline ----------------------
        live_dict = json.loads(json.dumps(b))
        off_dict = off_bundle.to_dict()
        diffs = list(deep_diff(off_dict, live_dict))
        unallowed = [(pa, a, bb) for pa, a, bb in diffs
                     if not any(m in pa for m in ALLOWED_DIFF_MARKERS)]
        check(f"A11_invariance[{pid}/{date}]", not unallowed,
              f"{len(unallowed)} unallowed diffs, e.g. {unallowed[:3]}")
        results.setdefault("A11_diffs", []).append(
            {"day": f"{pid}/{date}", "total": len(diffs), "unallowed": len(unallowed)})

    # ---- A6/A7 cohort-level counts & skew ------------------------------------
    all_recs = [rec for b in bundles for rec in b["records"]]
    counts = {s: sum(1 for r in all_recs if r["response"]["status"] == s) for s in ("answered", "missed", "expired")}
    check("A6_cohort_counts",
          counts == {"answered": cohort_json["answered"], "missed": cohort_json["missed"],
                     "expired": cohort_json["expired"]}
          and cohort_json["opportunities"] == 140,
          f"bundles {counts} vs 06_cohort.json {cohort_json['answered']}/{cohort_json['missed']}/{cohort_json['expired']}")
    lats = [r["response"]["latency_min"] for r in all_recs if r["response"].get("latency_min") is not None]
    check("A7_skew", len(lats) > 0 and mean(lats) > median(lats) and all(0 <= l <= 60 for l in lats),
          f"mean={mean(lats):.2f} median={median(lats):.2f} n={len(lats)} max={max(lats):.1f}")

    # ---- A8 cohort non-degeneracy ---------------------------------------------
    for item in ("valence", "energy", "stress"):
        vals = [r["response"]["subjective"][item] for r in all_recs
                if r["response"].get("subjective")]
        distinct = sorted(set(vals))
        check(f"A8_nondegenerate[{item}]",
              len(distinct) >= 3 and pstdev(vals) > 0.3 and min(vals) <= 2 and max(vals) >= 4,
              f"n={len(vals)} distinct={distinct} mean={mean(vals):.2f} std={pstdev(vals):.2f}")

    # ---- A10 cohort survivors ---------------------------------------------------
    survivors = 0
    for rec in all_recs:
        note = rec["response"].get("context_note")
        if note is None:
            continue
        pid, date = rec["prompt"]["participant_id"], rec["prompt"]["day_date"]
        off = offline_by_id[(pid, date)]
        off_rec = next((x for x in off.records if x.prompt.prompt_id == rec["prompt"]["prompt_id"]), None)
        if off_rec is None or not validate_note(note, off_rec.packet, config).valid:
            survivors += 1
    check("A10_zero_survivors", survivors == 0, f"{survivors} notes fail closed-world validation")

    # ---- A12 dashboard agreement -------------------------------------------------
    html = DASH.read_text(encoding="utf-8")
    m = re.search(r"const D = ", html)
    assert m, "embedded dashboard data not found"
    D = json.loads(html[m.end():html.index(";\n", m.end())])

    check("A12_verdict", D["verdict"] == "CONDITIONAL PASS"
          and "**Final verdict: CONDITIONAL PASS**" in (RUN / "report.md").read_text(), D["verdict"])
    check("A12_all_gates", all(D["gates"].values()),
          json.dumps({k: v for k, v in D["gates"].items() if not v}))
    for art, key in (("00_identity.json", "identity"), ("01_connectivity.json", "connectivity"),
                     ("02_suite.json", "suite"), ("03_flash_smoke.json", "smoke"),
                     ("04_cases.json", "cases"), ("06_cohort.json", "cohort"),
                     ("07_repeatability.json", "repeatability")):
        a = json.loads((RUN / art).read_text())
        d = D.get(key)
        check(f"A12_{key}_equals_artefact", d == a, "dashboard data differs from raw artefact")
    inv_art = json.loads((RUN / "05_invariance.json").read_text())
    check("A12_invariance_maps",
          D["invariance"]["total_diffs"] == inv_art["total_diffs"]
          and D["invariance"]["unallowed"] == inv_art["unallowed_diffs"]
          and [p for p, _, _ in inv_art["allowed_diffs"][:40]] == D["invariance"]["allowed_sample"]
          and D["invariance"]["gate"] == inv_art["gate"], "invariance block mismatch")

    # records: dashboard rows vs raw bundles
    drecs = D["records"]
    check("A12_records_count", len(drecs) == len(all_recs) == 140, f"{len(drecs)} rows")
    mism = 0
    for d, r in zip(drecs, sorted(all_recs, key=lambda x: (x['prompt']['participant_id'],
                                                           x['prompt']['day_date'],
                                                           x['prompt']['prompt_time_min']))):
        pr, rs = r["prompt"], r["response"]
        if (d["pid"], d["date"], d["t"], d["trig"], d["status"], d["note"], d["src"]) != (
                pr["participant_id"], pr["day_date"],
                pr["prompt_time"][11:16], pr["trigger"], rs["status"],
                rs.get("context_note"), rs.get("note_source")):
            mism += 1
            continue
        if d["lat"] != rs.get("latency_min"):
            mism += 1
        s = rs.get("subjective") or {}
        if (d["V"], d["E"], d["S"]) != (s.get("valence"), s.get("energy"), s.get("stress")):
            mism += 1
    check("A12_records_fields", mism == 0, f"{mism} row-field mismatches dashboard vs bundles")

    # dashboard KPI derivations vs raw bundle records (independent recompute).
    # NOTE: the cohort artefact's note_pipeline counters are answered-only
    # (125), while two expired prompts also carry context notes; the LLM-final
    # count is therefore recomputed from records, never derived by
    # final_non_null - offline_fallback (that mixed scopes: 91 - 52 = 39 vs
    # the true 40 answered LLM notes).
    d_answered = sum(1 for r in drecs if r["status"] == "answered")
    d_nonnull = sum(1 for r in drecs if r["status"] == "answered" and r["note"])
    d_llm = sum(1 for r in drecs if r["status"] == "answered" and r["src"] == "llm")
    raw_answered = sum(1 for r in all_recs if r["response"]["status"] == "answered")
    raw_nonnull = sum(1 for r in all_recs
                      if r["response"]["status"] == "answered" and r["response"].get("context_note"))
    raw_llm = sum(1 for r in all_recs
                  if r["response"]["status"] == "answered"
                  and r["response"].get("note_source") == "llm")
    np_ = cohort_json["note_pipeline"]
    check("A12_kpis",
          d_answered == raw_answered == cohort_json["answered"]
          and d_nonnull == raw_nonnull == np_["final_non_null_note_count_answered"]
          and d_llm == raw_llm,
          f"answered {d_answered}/{raw_answered}/{cohort_json['answered']} "
          f"nonnull {d_nonnull}/{raw_nonnull}/{np_['final_non_null_note_count_answered']} "
          f"llm {d_llm}/{raw_llm}")

    check("A12_no_secrets", re.search(r"sk-[A-Za-z0-9]{20,}", html) is None,
          "credential-shaped string found in dashboard")

    # ---- verdict ------------------------------------------------------------------
    n_fail = len(results["failures"])
    results["verdict"] = "PASS" if n_fail == 0 else "FAIL"
    OUT.mkdir(exist_ok=True)
    (OUT / "final_audit.json").write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps({k: v for k, v in results["checks"].items() if not v["ok"]}, indent=1))
    total = len(results["checks"])
    print(f"AUDIT: {total - n_fail}/{total} checks passed — {results['verdict']}")
    for f in results["failures"][:20]:
        print("  FAIL:", f)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
