# EMA Runtime Freeze — final DeepSeek note-rendering configuration

**Date:** 2026-09-25 (Europe/Copenhagen) · **Module state:** frozen, no further changes

## Repository HEAD

- Frozen tree commit: `fff4a3338b37e86ff0fd4897dcfefc619eeeede5` (branch `main`, noreply identity, local repo root = this folder)
- This document is the only change committed on top of `fff4a3338b37e86ff0fd4897dcfefc619eeeede5`.

## Protocol / config hash

- `paper3_ema/config/paper3_ema_v1.yaml` — sha256 `7dc0928a6fc924282c3bb034a162ead3a765c1bfa0f5c5c58575250a16d67f95`
- Module code digest (`paper3_ema/` package, 21 Python files, path+content): sha256 `b921dc51158660b6cfdece573b17b8d40f2c29a7438ff51fafb787d62b9306d7`

## Model

- `deepseek-flash` via `https://api.deepseek.com` — thinking enabled, `reasoning_effort=high`

## Final runtime settings

- `DEEPSEEK_MAX_TOKENS=4096` (raised from 1024) — the only changed setting
- Unchanged: model, thinking, reasoning effort, seeds, workers=4, `--phase all --write-docs`
- Frozen-state run (4096): `live_validation/artifacts/live_20260924-220804` — **CONDITIONAL PASS, all 12 gates pass**
- Baseline run (1024): `live_validation/artifacts/live_20260924-192504`
- No prompt, protocol, schema, validation or public-API changes were made for this freeze.

## Comparison — 1024 → 4096 tokens (4x7 cohort, 140 opportunities)

| metric | 1024 | 4096 |
|---|---|---|
| calls attempted | 339 | 297 |
| first-attempt valid parse (ok / fail) | 73 / 56 | 127 / 2 |
| first-attempt closed-world accept | 16 | 19 |
| retries 0 / 1 / 2 | 16 / 16 / 97 | 19 / 52 / 58 |
| offline fallbacks | 52 | 25 |
| null notes (answered) | 34 | 16 |
| non-null notes (answered) | 91 | 109 |
| unsupported facts surviving validation | 0 | 0 |
| API latency mean / median / p95 (ms) | 4231 / 4735 / 5656 | 6741 / 5640 / 15750 |
| tokens prompt / completion | 254,871 / 270,199 | 224,972 / 418,241 |
| tokens cached / reasoning | 185,320 / 263,453 | 165,627 / 408,380 |
| est. cost peak / off-peak (USD) | 0.346 / 0.173 | 0.521 / 0.260 |

- Truncation (`unparseable_output` rejections): **149 → 9 (−94%)**; validator rejections shifted accordingly (`unsupported_reference` 147 → 188) as real evaluation replaced truncation failures.
- Controlled cases (phase 2): 15/15 found, zero survivors, both runs; live-rendered notes 6 → 10 of 15 (`post_car` now renders live; `evening` still refuses by design).
- Residual: offline-template fallback rate still above the 15% reporting threshold (25/129 ≈ 19%) and flagged as the report caveat — materially reduced from 40%, not eliminated; the accepted fallback chain remains scientifically valid.
- Latency and cost increases are the expected consequence of the larger completion budget; not correctness defects.

## Invariance under the budget change (verified)

- Cross-run deep-diff of all 28 cohort bundles (1024 vs 4096): **4,451 diffs, 0 unallowed** — every difference confined to `context_note` and note-rendering telemetry/provenance.
- Phase-2 structured fields (inherited context, state, prompt_time, trigger, seeds): identical.
- Unchanged as required: prompt schedule, trigger, linkage, inherited context, answered/missed/expired status, latency, valence, energy, stress.
- Both runs: zero unsupported facts surviving validation; bundles valid; invariance and repeatability gates pass.

**Final status: READY_FOR_APPA_ADAPTER**
