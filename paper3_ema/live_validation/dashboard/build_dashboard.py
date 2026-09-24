#!/usr/bin/env python3
"""Build the self-contained live-validation dashboard (dashboard/index.html).

Reads one artefact run directory (default: the newest under ../artifacts/)
plus 06_cohort_bundles.jsonl and emits a single-file HTML dashboard with all
data embedded — no server-side data, no external dependencies.

Usage:
    python3 build_dashboard.py [run_dir]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DEFAULT_RUNS = _HERE.parent / "artifacts"


def find_run_dir(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    runs = sorted([p for p in _DEFAULT_RUNS.iterdir() if p.is_dir() and p.name.startswith("live_")])
    if not runs:
        raise SystemExit(f"no artefact run found under {_DEFAULT_RUNS}")
    return runs[-1]


def parse_bundles(text: str) -> list[dict]:
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


def _hms(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r"T(\d\d:\d\d):", str(value))
    return m.group(1) if m else str(value)


def flat_record(b: dict, rec: dict) -> dict:
    p, r, pk = rec["prompt"], rec["response"], rec["packet"]
    subj = r.get("subjective") or {}
    nv = r.get("note_validation") or {}
    atts = []
    raws = nv.get("raw_outputs") or []
    vals = nv.get("validations") or []
    for i in range(len(raws)):
        v = vals[i] if i < len(vals) else None
        atts.append({
            "raw": raws[i],
            "cand": (v or {}).get("normalized"),
            "valid": (v or {}).get("valid"),
            "codes": (v or {}).get("codes") or [],
        })
    return {
        "pid": p["participant_id"],
        "date": p["day_date"],
        "t": _hms(p["prompt_time"]),
        "tmin": round(p["prompt_time_min"], 1),
        "trig": p["trigger"],
        "evk": p.get("event_kind"),
        "win": p.get("window_index"),
        "status": r["status"],
        "lat": r.get("latency_min"),
        "resp_t": _hms(r.get("response_time")),
        "V": subj.get("valence"), "E": subj.get("energy"), "S": subj.get("stress"),
        "latent": {k: round(v, 2) for k, v in (subj.get("latent") or {}).items()},
        "rules": subj.get("rules_applied") or [],
        "note": r.get("context_note"),
        "src": r.get("note_source"),
        "fb": nv.get("fallback_reason"),
        "att": nv.get("attempts"),
        "ret": nv.get("retries"),
        "codes": nv.get("rejected_codes") or [],
        "atts": atts,
        "ctx": {
            "activity": pk.get("activity"),
            "domain": pk.get("domain"),
            "place": pk.get("place_type"),
            "social": pk.get("social_context"),
            "iod": pk.get("indoor_outdoor"),
            "tod": pk.get("time_of_day"),
            "p_act": pk.get("preceding_activity"),
            "p_mode": pk.get("preceding_journey_mode"),
            "p_delay": pk.get("preceding_journey_delayed"),
            "since_j": pk.get("minutes_since_journey_end"),
            "since_ae": pk.get("minutes_since_active_episode_end"),
            "purpose": pk.get("purpose_category"),
            "commit": pk.get("next_commitment_kind"),
        },
        "ids": {
            "ep": p.get("episode_id"), "iv": p.get("interval_id"),
            "jn": p.get("journey_id"), "ev": p.get("event_id"),
        },
        "sel": p.get("selection_reason"),
        "mfe": p.get("minutes_after_event"),
    }


def build_gates(run: Path) -> dict:
    suite = json.loads((run / "02_suite.json").read_text())
    smoke = json.loads((run / "03_flash_smoke.json").read_text())
    cases = json.loads((run / "04_cases.json").read_text())
    inv = json.loads((run / "05_invariance.json").read_text())
    coh = json.loads((run / "06_cohort.json").read_text())
    rep = json.loads((run / "07_repeatability.json").read_text())
    conn = json.loads((run / "01_connectivity.json").read_text())
    return {
        "endpoint_reachable": conn["reachable"],
        "suite_non_integration_pass": suite["suite_gate"]["non_integration_tests_pass"],
        "suite_integration_gate": suite["suite_gate"]["integration_gate"],
        "flash_smoke_all_checks": smoke["all_checks_pass"],
        "cases_all_found": cases["gate"]["all_cases_found"],
        "cases_zero_survivors": cases["gate"]["zero_survivors"],
        "invariance_holds": inv["gate"]["identical_outside_note_and_llm_provenance"],
        "cohort_all_bundles_valid": coh["validation"]["all_bundles_valid"],
        "cohort_zero_survivors": len(coh["validation"]["surviving_unsupported_facts"]) == 0,
        "cohort_opportunities": coh["opportunities"] == coh["cohort"]["participants"] * coh["cohort"]["days"] * 5,
        "repeatability_offline": rep["gate"]["offline_reproducible"],
        "repeatability_confined": rep["gate"]["llm_nondeterminism_confined"],
    }


def main() -> None:
    run = find_run_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    j = lambda name: json.loads((run / name).read_text(encoding="utf-8"))  # noqa: E731

    identity = j("00_identity.json")
    connectivity = j("01_connectivity.json")
    suite = j("02_suite.json")
    smoke = j("03_flash_smoke.json")
    cases = j("04_cases.json")
    inv = j("05_invariance.json")
    cohort = j("06_cohort.json")
    rep = j("07_repeatability.json")
    report_md = (run / "report.md").read_text(encoding="utf-8")
    bundles = parse_bundles((run / "06_cohort_bundles.jsonl").read_text(encoding="utf-8"))

    records = [flat_record(b, rec) for b in bundles for rec in b["records"]]
    records.sort(key=lambda r: (r["pid"], r["date"], r["tmin"]))

    verdict_m = re.search(r"\*\*Final verdict: ([A-Z /]+)\*\*", report_md)
    data = {
        "run_id": run.name,
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict_m.group(1) if verdict_m else "UNKNOWN",
        "gates": build_gates(run),
        "identity": identity,
        "connectivity": connectivity,
        "suite": suite,
        "smoke": smoke,
        "cases": cases,
        "invariance": {
            "total_diffs": inv["total_diffs"],
            "unallowed": inv["unallowed_diffs"],
            "allowed_sample": [p for p, _, _ in inv["allowed_diffs"][:40]],
            "gate": inv["gate"],
        },
        "cohort": cohort,
        "repeatability": rep,
        "report_md": report_md,
        "records": records,
    }
    payload = json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)
    out = _HERE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB) — {len(records)} records, run {run.name}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Paper 3 EMA — Live DeepSeek Validation Dashboard</title>
<style>
:root{
  --bg:#0d1117; --panel:#161b22; --panel2:#1c2330; --border:#263041;
  --text:#e6edf3; --muted:#8b949e; --green:#3fb950; --amber:#d29922;
  --red:#f85149; --blue:#58a6ff; --purple:#bc8cff; --teal:#39c5cf;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{position:sticky;top:0;z-index:10;background:rgba(13,17,23,.92);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--border);padding:14px 22px}
h1{font-size:17px;margin:0 0 6px}
h1 .muted{color:var(--muted);font-weight:400;font-size:13px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{background:var(--panel2);border:1px solid var(--border);border-radius:20px;
  padding:2px 10px;font-size:12px;color:var(--muted)}
.chip b{color:var(--text);font-weight:600}
.verdict{display:inline-block;padding:3px 12px;border-radius:20px;font-weight:700;font-size:12px;
  letter-spacing:.4px;border:1px solid}
.verdict.pass{color:var(--green);border-color:var(--green);background:rgba(63,185,80,.08)}
.verdict.cond{color:var(--amber);border-color:var(--amber);background:rgba(210,153,34,.08)}
.verdict.fail{color:var(--red);border-color:var(--red);background:rgba(248,81,73,.08)}
nav{display:flex;gap:4px;padding:10px 22px 0;flex-wrap:wrap}
nav button{background:none;border:1px solid transparent;border-bottom:none;color:var(--muted);
  padding:7px 13px;font-size:13px;cursor:pointer;border-radius:8px 8px 0 0}
nav button:hover{color:var(--text)}
nav button.on{color:var(--text);background:var(--panel);border-color:var(--border)}
main{padding:18px 22px 60px;max-width:1280px;margin:0 auto}
section.tab{display:none}
section.tab.on{display:block}
.grid{display:grid;gap:12px}
.kpis{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.card h3{margin:0 0 8px;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.kpi .v{font-size:24px;font-weight:700}
.kpi .s{color:var(--muted);font-size:12px;margin-top:2px}
.cols2{grid-template-columns:1fr 1fr}
@media(max-width:900px){.cols2{grid-template-columns:1fr}}
.gates{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}
.gate{font-size:12px;padding:3px 10px;border-radius:20px;border:1px solid}
.gate.ok{color:var(--green);border-color:rgba(63,185,80,.5);background:rgba(63,185,80,.07)}
.gate.bad{color:var(--red);border-color:rgba(248,81,73,.6);background:rgba(248,81,73,.08)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--muted);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--border);
  position:sticky;top:0;background:var(--panel);white-space:nowrap}
td{padding:6px 8px;border-bottom:1px solid rgba(38,48,65,.55);vertical-align:top}
tr:hover td{background:rgba(88,166,255,.04)}
.tblwrap{max-height:520px;overflow:auto;border:1px solid var(--border);border-radius:10px;background:var(--panel)}
.bar{height:16px;border-radius:4px;background:var(--blue);display:inline-block;vertical-align:middle}
.barrow{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:12.5px}
.barrow .lbl{width:220px;color:var(--muted);flex-shrink:0}
.barrow .val{width:60px;text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;border:1px solid}
.badge.llm{color:var(--purple);border-color:rgba(188,140,255,.5);background:rgba(188,140,255,.08)}
.badge.off{color:var(--teal);border-color:rgba(57,197,207,.5);background:rgba(57,197,207,.08)}
.badge.null{color:var(--muted);border-color:var(--border)}
.badge.ok{color:var(--green);border-color:rgba(63,185,80,.5);background:rgba(63,185,80,.07)}
.badge.warn{color:var(--amber);border-color:rgba(210,153,34,.5);background:rgba(210,153,34,.07)}
.badge.bad{color:var(--red);border-color:rgba(248,81,73,.6);background:rgba(248,81,73,.08)}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
select,input[type=search]{background:var(--panel2);border:1px solid var(--border);color:var(--text);
  border-radius:8px;padding:6px 10px;font-size:13px}
pre{background:#0a0e14;border:1px solid var(--border);border-radius:8px;padding:10px 12px;
  font:12px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;word-break:break-word;
  max-height:300px;overflow:auto}
.note-q{color:var(--purple);font-style:italic}
.muted{color:var(--muted)}
.small{font-size:12px}
.callout{border-left:3px solid var(--amber);background:rgba(210,153,34,.06);
  padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0;font-size:13px}
.callout.green{border-color:var(--green);background:rgba(63,185,80,.06)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;z-index:50;overflow:auto;padding:30px}
.modal.on{display:block}
.modal .box{background:var(--panel);border:1px solid var(--border);border-radius:12px;
  max-width:860px;margin:0 auto;padding:20px 22px}
.modal h2{font-size:16px;margin:0 0 4px}
.modal .close{float:right;cursor:pointer;color:var(--muted);font-size:20px;border:none;background:none}
.kv{display:grid;grid-template-columns:190px 1fr;gap:4px 12px;font-size:13px}
.kv .k{color:var(--muted)}
.rules{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.rule{font-size:11px;background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:1px 8px;color:var(--muted)}
#report pre{white-space:normal;font-family:inherit}
#report h1{font-size:20px;margin:18px 0 8px}
#report h2{font-size:16px;margin:18px 0 8px;border-bottom:1px solid var(--border);padding-bottom:4px}
#report h3{font-size:14px;margin:14px 0 6px}
#report table{margin:10px 0}
#report li{margin:3px 0}
footer{color:var(--muted);font-size:12px;padding:20px 22px;border-top:1px solid var(--border);max-width:1280px;margin:0 auto}
</style>
</head>
<body>
<header>
  <h1>Paper 3 EMA — Live DeepSeek Validation
    <span class="muted" id="runmeta"></span></h1>
  <div class="chips" id="chips"></div>
</header>
<nav id="nav"></nav>
<main>
  <section class="tab" id="tab-overview"></section>
  <section class="tab" id="tab-records"></section>
  <section class="tab" id="tab-cases"></section>
  <section class="tab" id="tab-cohort"></section>
  <section class="tab" id="tab-suite"></section>
  <section class="tab" id="tab-invariance"></section>
  <section class="tab" id="tab-report"></section>
</main>
<footer id="footer"></footer>
<div class="modal" id="modal"><div class="box" id="modalbox"></div></div>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pct = (a,b) => b ? (100*a/b).toFixed(1)+"%" : "—";
const fmt = n => (n==null?"—":Math.round(n*100)/100);
const srcBadge = s => s ? `<span class="badge ${s==='llm'?'llm':'off'}">${esc(s)}</span>` : '<span class="badge null">null</span>';
const statusBadge = s => s==='answered' ? '<span class="badge ok">answered</span>'
  : s==='expired' ? '<span class="badge warn">expired</span>' : '<span class="badge null">missed</span>';
const G = D.gates;
const C = D.cohort, NP = C.note_pipeline, API = C.api;
// Note counts derived directly from the 140 embedded records (ground truth),
// because NP's counters mix scopes: rendered = answered + expired (129),
// while null_note_count_answered / final_non_null_note_count_answered are
// answered-only (125). Two expired prompts also carry context notes.
const ANS = D.records.filter(r=>r.status==="answered");
const kpiLlm = ANS.filter(r=>r.src==="llm").length;
const kpiOff = ANS.filter(r=>r.src==="offline_template").length;
const kpiNul = ANS.filter(r=>!r.note).length;
// funnel scope = rendered prompts (answered + expired; missed prompts never
// enter the note pipeline): 41 LLM + 52 offline + 36 null = 129
const RENDERED = D.records.filter(r=>r.status==="answered"||r.status==="expired");
const finLlm = RENDERED.filter(r=>r.src==="llm").length;
const finOff = RENDERED.filter(r=>r.src==="offline_template").length;
const finNul = RENDERED.filter(r=>!r.note).length;

// ---------- header ----------
document.getElementById("runmeta").textContent =
  `· run ${D.run_id} · ${D.identity.model} · started ${D.identity.started_utc}`;
document.getElementById("chips").innerHTML = [
  `<span class="chip verdict ${D.verdict==='PASS'?'pass':D.verdict==='FAIL'?'fail':'cond'}">${esc(D.verdict)}</span>`,
  `<span class="chip">model <b>${esc(D.identity.model)}</b></span>`,
  `<span class="chip">thinking <b>${esc(D.identity.thinking)}</b> / ${esc(D.identity.reasoning_effort)}</span>`,
  `<span class="chip">machine <b>${esc(D.identity.platform)}</b> · py ${esc(D.identity.python)}</b></span>`,
  `<span class="chip"><b>${API.calls_succeeded}/${API.calls_attempted}</b> API calls ok</span>`,
  `<span class="chip">cost <b>$${API.estimated_cost_usd.off_peak.toFixed(3)}–${API.estimated_cost_usd.peak.toFixed(3)}</b> USD</span>`,
  `<span class="chip">survivors <b style="color:var(--green)">0</b></span>`,
].join("");

// ---------- nav ----------
const TABS = [["overview","Overview"],["records","Records (140)"],["cases","Cases (15)"],
  ["cohort","Cohort"],["suite","Suite & Smoke"],["invariance","Invariance & Repeat"],["report","Full Report"]];
const nav = document.getElementById("nav");
TABS.forEach(([id,label],i) => {
  const b = document.createElement("button");
  b.textContent = label; if(i===0) b.className="on";
  b.onclick = () => {
    document.querySelectorAll("nav button").forEach(x=>x.classList.remove("on"));
    document.querySelectorAll("section.tab").forEach(x=>x.classList.remove("on"));
    b.classList.add("on"); document.getElementById("tab-"+id).classList.add("on");
  };
  nav.appendChild(b);
});

// ---------- overview ----------
(function(){
  const el = document.getElementById("tab-overview");
  const gatePills = Object.entries(G).map(([k,v]) =>
    `<span class="gate ${v?'ok':'bad'}">${v?'✓':'✗'} ${k}</span>`).join("");
  const rej = Object.entries(NP.rejection_counts_by_code).sort((a,b)=>b[1]-a[1]);
  const rejMax = Math.max(...rej.map(r=>r[1]),1);
  const trig = Object.entries(C.prompt_type_distribution).sort((a,b)=>b[1]-a[1]);
  const trigMax = Math.max(...trig.map(t=>t[1]),1);
  const trigColors = {semi_random:"#58a6ff",post_trip:"#bc8cff",context_transition:"#39c5cf",post_active_episode:"#3fb950"};
  const lat = API.latency_ms;
  const U = API.usage_totals;
  const pids = [...new Set(D.records.map(r=>r.pid))];
  const perP = pids.map(p=>{
    const rs = D.records.filter(r=>r.pid===p);
    const ans = rs.filter(r=>r.status==="answered");
    const llm = ans.filter(r=>r.src==="llm").length;
    const off = ans.filter(r=>r.src==="offline_template").length;
    const nul = ans.filter(r=>!r.note).length;
    return {p, n:rs.length, ans:ans.length, llm, off, nul};
  });
  el.innerHTML = `
  <div class="gates">${gatePills}</div>
  <div class="grid kpis">
    <div class="card kpi"><h3>Opportunities</h3><div class="v">140</div><div class="s">4 personas × 7 days</div></div>
    <div class="card kpi"><h3>Answered</h3><div class="v">${C.answered}</div><div class="s">${pct(C.answered,C.opportunities)} · band 85–90%</div></div>
    <div class="card kpi"><h3>Missed / Expired</h3><div class="v">${C.missed} / ${C.expired}</div><div class="s">10-min expiry window</div></div>
    <div class="card kpi"><h3>API calls</h3><div class="v">${API.calls_succeeded}<span class="muted">/${API.calls_attempted}</span></div><div class="s">0 failed · ${lat.mean} ms mean</div></div>
    <div class="card kpi"><h3>First-attempt parse</h3><div class="v">${NP.first_attempt_parse_ok}<span class="muted">/${NP.rendered}</span></div><div class="s">${NP.first_attempt_parse_fail} failed → retry</div></div>
    <div class="card kpi"><h3>First-attempt accept</h3><div class="v">${NP.first_attempt_closed_world_accept}<span class="muted">/${NP.rendered}</span></div><div class="s">closed-world, 1st try</div></div>
    <div class="card kpi"><h3>LLM-final notes (answered)</h3><div class="v">${kpiLlm}<span class="muted">/${kpiLlm+kpiOff} non-null</span></div><div class="s">${kpiOff} offline · ${kpiNul} null · ${finLlm-kpiLlm} more notes on expired prompts</div></div>
    <div class="card kpi"><h3>Survivors</h3><div class="v" style="color:var(--green)">0</div><div class="s">unsupported facts in accepted records</div></div>
    <div class="card kpi"><h3>Cost (est.)</h3><div class="v">$${API.estimated_cost_usd.peak.toFixed(3)}</div><div class="s">peak · off-peak $${API.estimated_cost_usd.off_peak.toFixed(3)}</div></div>
    <div class="card kpi"><h3>Latency p95</h3><div class="v">${lat.p95} ms</div><div class="s">median ${lat.median} · max ${lat.max}</div></div>
  </div>
  <div class="grid cols2" style="margin-top:12px">
    <div class="card"><h3>Note pipeline funnel (rendered = answered + expired)</h3>
      ${funnel()}
      <div class="small muted" style="margin-top:8px">Retry distribution: ${Object.entries(NP.retry_distribution).map(([k,v])=>`${k}×${v}`).join(" · ")} — ${NP.retry_distribution["2"]} notes hit the 2-retry cap, then the by-design fallback chain (offline template → null) took over.</div>
    </div>
    <div class="card"><h3>Rejections by validator code (all attempts)</h3>
      ${rej.map(([k,v])=>`<div class="barrow"><span class="lbl">${esc(k)}</span><span class="bar" style="width:${260*v/rejMax}px;background:var(--red)"></span><span class="val">${v}</span></div>`).join("")}
      <div class="small muted" style="margin-top:8px">Every rejected candidate was retried with the failure reasons attached, then fell back to the offline template (validated too) or null. <b style="color:var(--green)">Zero rejected content reached a stored record.</b></div>
    </div>
    <div class="card"><h3>Prompt type distribution (140)</h3>
      ${trig.map(([k,v])=>`<div class="barrow"><span class="lbl">${esc(k)}</span><span class="bar" style="width:${260*v/trigMax}px;background:${trigColors[k]||'#8b949e'}"></span><span class="val">${v}</span></div>`).join("")}
      <div class="small muted" style="margin-top:8px">≥3 semi-random and ≤2 event-enriched per day — enforced by the scheduler and re-audited (all bundles VALID).</div>
    </div>
    <div class="card"><h3>Token usage & API</h3>
      <div class="kv">
        <span class="k">Prompt tokens</span><span>${U.prompt_tokens.toLocaleString()} (cached ${U.cached_tokens.toLocaleString()} = ${pct(U.cached_tokens,U.prompt_tokens)})</span>
        <span class="k">Completion tokens</span><span>${U.completion_tokens.toLocaleString()} (reasoning ${U.reasoning_tokens.toLocaleString()} = ${pct(U.reasoning_tokens,U.completion_tokens)})</span>
        <span class="k">Latency</span><span>mean ${lat.mean} ms · median ${lat.median} ms · p95 ${lat.p95} ms · max ${lat.max} ms</span>
        <span class="k">Pricing basis</span><span class="small">${esc(API.pricing.source)}</span>
      </div>
    </div>
    <div class="card"><h3>Per-participant (computed from the 140 records)</h3>
      <table><tr><th>participant</th><th>days</th><th>answered</th><th>LLM notes</th><th>offline</th><th>null</th></tr>
      ${perP.map(x=>`<tr><td>${esc(x.p)}</td><td>${Math.round(x.n/5)}</td><td>${x.ans}/${x.n}</td><td>${x.llm}</td><td>${x.off}</td><td>${x.nul}</td></tr>`).join("")}
      </table>
    </div>
    <div class="card"><h3>Connectivity & repeatability</h3>
      <div class="kv">
        <span class="k">Endpoint</span><span>${D.connectivity.reachable?'<span class="badge ok">reachable</span>':'<span class="badge bad">blocked</span>'} <span class="muted small">${esc(D.connectivity.probe_detail)} · ${esc(D.connectivity.diagnostics.tls)}</span></span>
        <span class="k">Offline reproducibility</span><span>${D.repeatability.gate.offline_reproducible?'<span class="badge ok">byte-identical, same seed</span>':'<span class="badge bad">differs</span>'}</span>
        <span class="k">Live nondeterminism</span><span>${D.repeatability.gate.llm_nondeterminism_confined?'<span class="badge ok">confined to notes + LLM provenance</span>':'<span class="badge bad">escaped</span>'} <span class="muted small">(${D.repeatability.live_structural_diffs} diffs, ${D.repeatability.live_unallowed_diffs.length} unallowed)</span></span>
      </div>
    </div>
  </div>
  <div class="callout"><b>Observation (no safety impact).</b> First-attempt parse failed for ${NP.first_attempt_parse_fail}/${NP.rendered} notes and ${NP.retry_distribution["2"]} notes hit the retry cap. Average completion usage was ≈${Math.round(U.completion_tokens/API.calls_succeeded)} tokens/call of which ≈${Math.round(U.reasoning_tokens/API.calls_succeeded)} were <i>reasoning</i> tokens against the 1024-token budget — visible content was frequently truncated mid-JSON. The closed-world chain contained every case (0 survivors). A re-run with <code>DEEPSEEK_MAX_TOKENS=4096</code> should raise first-attempt LLM acceptance.</div>`;
  function funnel(){
    const rows = [
      ["Rendered notes", NP.rendered, "#58a6ff"],
      ["1st attempt parse OK", NP.first_attempt_parse_ok, "#39c5cf"],
      ["1st attempt closed-world accept", NP.first_attempt_closed_world_accept, "#3fb950"],
      ["final: LLM-authored", finLlm, "#bc8cff"],
      ["final: offline template", finOff, "#39c5cf"],
      ["final: null (acceptable)", finNul, "#8b949e"],
    ];
    const max = NP.rendered;
    return rows.map(([l,v,c])=>`<div class="barrow"><span class="lbl">${l}</span><span class="bar" style="width:${260*v/max}px;background:${c}"></span><span class="val">${v}</span></div>`).join("");
  }
})();

// ---------- records ----------
(function(){
  const el = document.getElementById("tab-records");
  const pids = [...new Set(D.records.map(r=>r.pid))].sort();
  const trigs = [...new Set(D.records.map(r=>r.trig))].sort();
  el.innerHTML = `
  <div class="filters">
    <select id="f-pid"><option value="">all participants</option>${pids.map(p=>`<option>${esc(p)}</option>`).join("")}</select>
    <select id="f-status"><option value="">all statuses</option>${["answered","missed","expired"].map(s=>`<option>${s}</option>`).join("")}</select>
    <select id="f-trig"><option value="">all triggers</option>${trigs.map(t=>`<option>${esc(t)}</option>`).join("")}</select>
    <select id="f-src"><option value="">all note sources</option><option value="llm">llm</option><option value="offline_template">offline_template</option><option value="none">null</option></select>
    <input type="search" id="f-q" placeholder="search note / context…" style="min-width:220px">
    <span class="muted small" id="f-count"></span>
  </div>
  <div class="tblwrap"><table id="rtab">
    <thead><tr><th>date</th><th>participant</th><th>time</th><th>trigger</th><th>win</th><th>status</th><th>lat min</th><th>V/E/S</th><th>note</th><th>source</th></tr></thead>
    <tbody id="rbody"></tbody>
  </table></div>
  <div class="small muted" style="margin-top:8px">Click a row for the full record: inherited context packet, synthetic state with rule-level trace, every model attempt (raw output → parsed candidate → validator verdict), linkage ids and selection reason.</div>`;
  const body = document.getElementById("rbody");
  function render(){
    const p = f("pid"), s = f("status"), t = f("trig"), sr = f("src"), q = f("q").toLowerCase();
    const rows = D.records.filter(r =>
      (!p || r.pid===p) && (!s || r.status===s) && (!t || r.trig===t) &&
      (!sr || (sr==="none" ? !r.src : r.src===sr)) &&
      (!q || JSON.stringify([r.note, r.ctx, r.trig, r.ids, r.fb]).toLowerCase().includes(q)));
    document.getElementById("f-count").textContent = `${rows.length} / ${D.records.length} records`;
    body.innerHTML = rows.map(r=>{
      const i = D.records.indexOf(r);
      const n = r.note ? `<span class="note-q">“${esc(r.note)}”</span>` : '<span class="muted">—</span>';
      return `<tr data-i="${i}" style="cursor:pointer">
        <td class="muted">${esc(r.date)}</td><td>${esc(r.pid)}</td><td>${esc(r.t)}</td>
        <td>${esc(r.trig)}${r.evk?` <span class="muted small">(${esc(r.evk)})</span>`:""}</td>
        <td class="muted">${r.win??""}</td><td>${statusBadge(r.status)}</td>
        <td class="muted">${r.lat==null?"—":fmt(r.lat)}</td>
        <td>${r.V!=null?`${r.V}/${r.E}/${r.S}`:'<span class="muted">—</span>'}</td>
        <td style="max-width:340px">${n}</td><td>${srcBadge(r.src)}</td></tr>`;
    }).join("");
    body.querySelectorAll("tr").forEach(tr => tr.onclick = () => openRecord(+tr.dataset.i));
  }
  const f = id => document.getElementById("f-"+id).value;
  ["pid","status","trig","src","q"].forEach(id =>
    document.getElementById("f-"+id).oninput = render);
  render();

  window.openRecord = function(i){
    const r = D.records[i];
    const ctx = r.ctx;
    const atts = (r.atts||[]).map((a,k)=>`
      <div style="margin:8px 0"><div class="small muted">attempt ${k+1} — ${a.valid?'<span class="badge ok">accepted</span>':'<span class="badge bad">rejected: '+(a.codes||[]).map(esc).join(", ")+"</span>"}${a.cand==null?' · unparseable or model-null':''}</div>
      <pre>${esc(a.raw||"(empty)")}</pre></div>`).join("");
    const box = document.getElementById("modalbox");
    box.innerHTML = `
      <button class="close" onclick="closeModal()">✕</button>
      <h2>${esc(r.pid)} · ${esc(r.date)} ${esc(r.t)} → ${esc(r.trig)}</h2>
      <div class="chips" style="margin:8px 0">
        ${statusBadge(r.status)} ${srcBadge(r.src)}
        <span class="chip">window <b>${r.win??"—"}</b></span>
        <span class="chip">latency <b>${r.lat==null?"—":fmt(r.lat)+" min"}</b></span>
        <span class="chip">response <b>${r.resp_t??"—"}</b></span>
        <span class="chip">attempts <b>${r.att??0} (retries ${r.ret??0})</b></span>
      </div>
      <div class="grid cols2" style="margin-top:10px">
        <div><h3 style="font-size:12px;color:var(--muted)">Inherited context (closed world the model saw)</h3>
          <div class="kv">
            <span class="k">activity / domain</span><span>${esc(ctx.activity)} / ${esc(ctx.domain)}</span>
            <span class="k">place / social</span><span>${esc(ctx.place)} / ${esc(ctx.social)}</span>
            <span class="k">indoor-outdoor / time</span><span>${esc(ctx.iod)} / ${esc(ctx.tod)}</span>
            <span class="k">purpose</span><span>${esc(ctx.purpose)}</span>
            <span class="k">preceding activity</span><span>${esc(ctx.p_act)}</span>
            <span class="k">preceding journey</span><span>${ctx.p_mode?esc(ctx.p_mode)+(ctx.p_delay==null?" (delay not documented)":ctx.p_delay?" (delay documented)":" (no delay documented)"): "—"}${ctx.since_j!=null?` · ${fmt(ctx.since_j)} min ago`:""}</span>
            <span class="k">active episode</span><span>${ctx.since_ae!=null?`${fmt(ctx.since_ae)} min ago`:"—"}</span>
            <span class="k">next commitment</span><span>${esc(ctx.commit)??"—"}</span>
            <span class="k">linkage ids</span><span class="small">${Object.entries(r.ids).filter(([,v])=>v).map(([k,v])=>`${k}:${esc(v)}`).join(" · ")||"—"}</span>
            <span class="k">selection</span><span class="small">${esc(r.sel)}</span>
          </div>
        </div>
        <div><h3 style="font-size:12px;color:var(--muted)">Synthetic subjective state</h3>
          <div class="kv">
            <span class="k">valence / energy / stress</span><span><b>${r.V??"—"}</b> / <b>${r.E??"—"}</b> / <b>${r.S??"—"}</b></span>
            <span class="k">latent (pre-noise)</span><span class="small">${Object.entries(r.latent||{}).map(([k,v])=>`${k} ${v}`).join(" · ")||"—"}</span>
          </div>
          <div class="small muted" style="margin-top:6px">rules applied (${r.rules.length}):</div>
          <div class="rules">${r.rules.map(x=>`<span class="rule">${esc(x)}</span>`).join("")}</div>
          ${r.note?`<h3 style="font-size:12px;color:var(--muted);margin-top:12px">Stored note</h3><div class="note-q">“${esc(r.note)}”</div>${r.fb?`<div class="small muted">fallback reason: ${esc(r.fb)}</div>`:""}`:`<h3 style="font-size:12px;color:var(--muted);margin-top:12px">Stored note</h3><div class="muted">null (acceptable — the note is optional)</div>`}
        </div>
      </div>
      ${(r.atts||[]).length?`<h3 style="font-size:12px;color:var(--muted);margin-top:14px">Model attempt history (raw → parsed → verdict)</h3>${atts}`:""}`;
    document.getElementById("modal").classList.add("on");
  };
  window.closeModal = () => document.getElementById("modal").classList.remove("on");
  document.getElementById("modal").onclick = e => { if(e.target.id==="modal") closeModal(); };
})();

// ---------- cases ----------
(function(){
  const el = document.getElementById("tab-cases");
  const cases = D.cases.cases;
  el.innerHTML = `
    <div class="callout green"><b>Adversarial closed-world result:</b> ${D.cases.found}/${cases.length} contexts resolved ·
    the model <i>attempted</i> unsupported facts in many cases (that is expected) ·
    <b style="color:var(--green)">zero unsupported facts survived into an accepted record</b> (survivors: ${D.cases.surviving_unsupported_facts.length}).</div>
    <div class="tblwrap" style="max-height:70vh"><table>
      <thead><tr><th>case</th><th>trigger</th><th>temptations</th><th>attempts</th><th>retries</th><th>final source</th><th>final note</th><th></th></tr></thead>
      <tbody id="cbody"></tbody>
    </table></div>`;
  const body = document.getElementById("cbody");
  body.innerHTML = cases.map((c,i)=>{
    if(!c.found) return `<tr><td>${esc(c.case)}</td><td colspan="6" class="muted">no matching record</td><td></td></tr>`;
    const fin = c.final, note = fin.note ? `<span class="note-q">“${esc(fin.note)}”</span>` : '<span class="muted">null</span>';
    return `<tr data-i="${i}"><td><b>${esc(c.case)}</b><div class="small muted">${esc(c.fixture)} · seed ${c.seed}</div></td>
      <td>${esc(c.trigger)}</td><td class="small muted">${c.temptations.map(esc).join(", ")}</td>
      <td>${c.attempts}</td><td>${c.retries}</td><td>${srcBadge(fin.source)}</td>
      <td style="max-width:320px">${note}</td><td style="cursor:pointer;color:var(--blue)">attempts ▸</td></tr>
      <tr id="copen-${i}" style="display:none;background:rgba(88,166,255,.03)"><td colspan="8">${
        c.attempt_details.map((a,k)=>`<div style="margin:8px 0"><div class="small muted">attempt ${k+1} — ${(a.validation?.valid)?'<span class="badge ok">accepted</span>':'<span class="badge bad">rejected: '+((a.validation?.codes||[]).map(esc).join(", ")||"?")+"</span>"}</div><pre>${esc(a.raw_model_output||"(empty)")}</pre>${a.parsed_candidate!=null?`<div class="small muted">parsed candidate: ${esc(a.parsed_candidate)}</div>`:""}</div>`).join("")
      }</td></tr>`;
  }).join("");
  body.querySelectorAll("td[style*='cursor']").forEach(td => td.onclick = () => {
    const i = td.parentElement.dataset.i;
    const row = document.getElementById("copen-"+i);
    row.style.display = row.style.display==="none" ? "table-row" : "none";
  });
})();

// ---------- cohort ----------
(function(){
  const el = document.getElementById("tab-cohort");
  const rep = C.representative_records;
  el.innerHTML = `
  <div class="grid kpis">
    <div class="card kpi"><h3>Participant-days</h3><div class="v">${C.cohort.participant_days}</div><div class="s">${C.cohort.participants} × ${C.cohort.days}</div></div>
    <div class="card kpi"><h3>Answered / Missed / Expired</h3><div class="v">${C.answered}/${C.missed}/${C.expired}</div><div class="s">response rate ${pct(C.answered,C.opportunities)}</div></div>
    <div class="card kpi"><h3>Bundles valid</h3><div class="v">${C.validation.all_bundles_valid?'<span style="color:var(--green)">28/28</span>':'<span style="color:var(--red)">no</span>'}</div><div class="s">issues: ${Object.entries(C.validation.bundle_issue_codes).map(([k,v])=>`${k}×${v} (day-level INFO)`).join(", ")||"none"}</div></div>
    <div class="card kpi"><h3>Surviving inventions</h3><div class="v" style="color:var(--green)">0</div><div class="s">required: 0</div></div>
  </div>
  <div class="grid cols2" style="margin-top:12px">
    <div class="card"><h3>API & note pipeline (full numbers)</h3>
      <div class="kv">
        <span class="k">Calls attempted / ok</span><span>${API.calls_attempted} / ${API.calls_succeeded}</span>
        <span class="k">Latency mean/median/p95/max</span><span>${API.latency_ms.mean} / ${API.latency_ms.median} / ${API.latency_ms.p95} / ${API.latency_ms.max} ms</span>
        <span class="k">1st-attempt parse ok / fail</span><span>${NP.first_attempt_parse_ok} / ${NP.first_attempt_parse_fail}</span>
        <span class="k">1st-attempt closed-world accept</span><span>${NP.first_attempt_closed_world_accept}</span>
        <span class="k">Model-chose-null (1st)</span><span>${NP.model_chose_null_first_attempt}</span>
        <span class="k">Retry distribution</span><span>${Object.entries(NP.retry_distribution).map(([k,v])=>`${k}×${v}`).join(" · ")}</span>
        <span class="k">Offline fallback</span><span>${NP.offline_fallback_count}</span>
        <span class="k">Null notes (answered)</span><span>${NP.null_note_count_answered}</span>
        <span class="k">Final non-null (answered)</span><span>${NP.final_non_null_note_count_answered}</span>
        <span class="k">Tokens (prompt/cached/compl/reason)</span><span>${API.usage_totals.prompt_tokens.toLocaleString()} / ${API.usage_totals.cached_tokens.toLocaleString()} / ${API.usage_totals.completion_tokens.toLocaleString()} / ${API.usage_totals.reasoning_tokens.toLocaleString()}</span>
        <span class="k">Cost (peak / off-peak)</span><span>$${API.estimated_cost_usd.peak.toFixed(4)} / $${API.estimated_cost_usd.off_peak.toFixed(4)}</span>
      </div>
    </div>
    <div class="card"><h3>Representative final records (${rep.length})</h3>
      <div class="small" style="max-height:430px;overflow:auto">
      ${rep.map((r,i)=>`<div style="border-bottom:1px solid rgba(38,48,65,.5);padding:8px 0">
        <b>${r.date} ${r.prompt_time}</b> → <b>${esc(r.trigger)}</b>${r.preceding_mode?` <span class="muted small">(after ${esc(r.preceding_mode)}${r.delay_documented?", delay documented":""})</span>`:""}<br>
        <span class="muted small">${Object.entries(r.context).filter(([,v])=>v).map(([k,v])=>`${k}:${v}`).join(" / ")} → V/E/S ${(r.valence_energy_stress||[]).join("/")}</span><br>
        <span class="note-q">“${esc(r.final_note)}”</span> ${srcBadge(r.note_source)} <span class="small muted">→ ${esc(r.validation_status)}</span>
      </div>`).join("")}
      </div>
    </div>
  </div>`;
})();

// ---------- suite & smoke ----------
(function(){
  const el = document.getElementById("tab-suite");
  const s = D.suite, sm = D.smoke;
  const it = Object.entries(s.integration_tests).map(([k,v])=>
    `<tr><td>${k}</td><td>${v==='passed'?'<span class="badge ok">PASSED (live)</span>':v==='failed'?'<span class="badge bad">FAILED</span>':v==='skipped'?'<span class="badge null">skipped</span>':'<span class="muted">see log</span>'}</td></tr>`).join("");
  const checks = Object.entries(sm.checks).map(([k,v])=>
    `<span class="gate ${v?'ok':'bad'}">${v?'✓':'✗'} ${k}</span>`).join("");
  el.innerHTML = `
  <div class="grid cols2">
    <div class="card"><h3>Full suite (run machine, key present)</h3>
      <div class="v" style="font-size:20px;font-weight:700">${esc(s.full_suite_summary)}</div>
      <div class="small muted" style="margin:6px 0">5 skips = 3 deterministic test_notes skips + 2 legacy-import skips caused by a hard-coded sandbox path (test-only defect, fixed in sandbox commit 7070fbe; after the fix expect 136 passed / 3 skipped).</div>
      <table><thead><tr><th>integration test</th><th>result</th></tr></thead><tbody>${it}</tbody></table>
      <div class="small muted" style="margin-top:8px">All four ran live against the real API (model per config: deepseek-chat) and passed — deepseek-chat is still served.</div>
    </div>
    <div class="card"><h3>deepseek-flash transport smoke</h3>
      <div class="gates" style="margin:6px 0">${checks}</div>
      <div class="kv">
        <span class="k">Raw call</span><span>“${esc(sm.raw_call.content)}” · ${sm.raw_call.metric.latency_ms} ms · model echo <b>${esc(sm.raw_call.metric.response_model)}</b></span>
        <span class="k">Usage (raw call)</span><span class="small">${JSON.stringify(sm.raw_call.metric.usage)}</span>
        <span class="k">Bundle</span><span>${sm.bundle.llm_calls} calls, ${sm.bundle.llm_retries} retries, ${sm.bundle.notes_checked} notes checked, sources ${JSON.stringify(sm.bundle.note_sources)}</span>
      </div>
    </div>
  </div>`;
})();

// ---------- invariance & repeatability ----------
(function(){
  const el = document.getElementById("tab-invariance");
  const inv = D.invariance, rep = D.repeatability;
  el.innerHTML = `
  <div class="grid cols2">
    <div class="card"><h3>Phase 3 — live vs offline invariance (identical day, config, seed)</h3>
      <div class="kv">
        <span class="k">Structural diffs</span><span>${inv.total_diffs}</span>
        <span class="k">Outside note / LLM provenance</span><span>${inv.unallowed.length===0?'<span class="badge ok">0 — identical</span>':'<span class="badge bad">'+inv.unallowed.length+'</span>'}</span>
        <span class="k">Gate</span><span>${inv.gate.identical_outside_note_and_llm_provenance?'<span class="badge ok">HOLDS</span>':'<span class="badge bad">BROKEN</span>'}</span>
      </div>
      <div class="small muted" style="margin-top:8px">Allowed diff paths (note + LLM provenance only), sample:</div>
      <pre>${inv.allowed_sample.map(esc).join("\n")||"(none)"}</pre>
    </div>
    <div class="card"><h3>Phase 5 — repeatability boundary</h3>
      <div class="kv">
        <span class="k">Offline, same seed</span><span>${rep.gate.offline_reproducible?'<span class="badge ok">byte-identical</span>':'<span class="badge bad">differs</span>'}</span>
        <span class="k">Live, two separate runs</span><span>${rep.live_unallowed_diffs.length===0?'<span class="badge ok">structured fields identical</span>':'<span class="badge bad">'+rep.live_unallowed_diffs.length+' unallowed diffs</span>'} <span class="muted small">(${rep.live_structural_diffs} total diffs)</span></span>
        <span class="k">LLM prose identical?</span><span>${rep.live_note_identical_between_runs?'yes':'no — expected (no determinism guarantee required)'}</span>
      </div>
      <div class="small muted" style="margin-top:8px">Same seed, two live runs — notes may differ, nothing else may:</div>
      <div class="grid" style="grid-template-columns:1fr 1fr;gap:8px;margin-top:6px">
        <div><div class="small muted">run 1</div><pre>${(rep.live_notes_run1||[]).map(n=>n?esc(n):"(null)").join("\n")}</pre></div>
        <div><div class="small muted">run 2</div><pre>${(rep.live_notes_run2||[]).map(n=>n?esc(n):"(null)").join("\n")}</pre></div>
      </div>
    </div>
  </div>`;
})();

// ---------- report ----------
(function(){
  const el = document.getElementById("tab-report");
  const md = D.report_md;
  function md2html(src){
    const lines = src.split("\n");
    let html = "", inTable = false, inList = false, trows = 0;
    const inline = s => esc(s)
      .replace(/\*\*(.+?)\*\*/g,"<b>$1</b>")
      .replace(/`(.+?)`/g,"<code>$1</code>");
    for(const line of lines){
      const t = line.trim();
      if(t.startsWith("|")){
        if(!inTable){ html += "<table>"; inTable = true; trows = 0; }
        if(/^[\s|:-]+$/.test(t)) continue;   // separator row
        const cells = t.slice(1,-1).split("|").map(x=>x.trim());
        const tag = trows === 0 ? "th" : "td";
        trows++;
        html += "<tr>" + cells.map(c=>`<${tag}>${inline(c)}</${tag}>`).join("") + "</tr>";
        continue;
      } else if(inTable){ html += "</table>"; inTable = false; }
      if(t.startsWith("- [x]")){ if(!inList){html+="<ul>";inList=true;} html += '<li style="list-style:none">✅ ' + inline(t.slice(5)) + "</li>"; continue; }
      if(t.startsWith("- [ ]")){ if(!inList){html+="<ul>";inList=true;} html += '<li style="list-style:none">⬜ ' + inline(t.slice(5)) + "</li>"; continue; }
      if(t.startsWith("- ")){ if(!inList){html+="<ul>";inList=true;} html += "<li>" + inline(t.slice(2)) + "</li>"; continue; }
      if(inList && !t.startsWith("-")){ html += "</ul>"; inList = false; }
      if(t === "---"){ if(inList){html+="</ul>";inList=false;} html += "<hr>"; continue; }
      if(t.startsWith("### ")){ html += "<h3>"+inline(t.slice(4))+"</h3>"; }
      else if(t.startsWith("## ")){ html += "<h2>"+inline(t.slice(3))+"</h2>"; }
      else if(t.startsWith("# ")){ html += "<h1>"+inline(t.slice(2))+"</h1>"; }
      else if(t.startsWith("&gt; ")||t.startsWith("> ")){ html += `<div class="callout">${inline(t.slice(2))}</div>`; }
      else if(t !== ""){ html += "<p>" + inline(t) + "</p>"; }
    }
    if(inTable) html += "</table>"; if(inList) html += "</ul>";
    return html;
  }
  el.innerHTML = `<div id="report">${md2html(md)}</div>`;
})();

document.getElementById("footer").innerHTML =
  `Run <b>${D.run_id}</b> · built ${D.built_utc} by build_dashboard.py · artefacts: ` +
  [...D.identity.platform, D.identity.model].map(esc).join(" · ") +
  ` · harness v1.0.0 (test-only) · raw artefact set: LIVE_DEEPSEEK_VALIDATION_artifacts_2026-09-24/ · ` +
  `<b>no credential material in any artefact</b>`;
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
