# paper3_ema — standalone Paper 3 EMA module

A clean, standalone, scientifically defensible **Ecological Momentary Assessment**
module for synthetic contextual-day data. It turns an externally supplied
**contextual day** into a complete, provenance-traced EMA bundle:

```
any contextual-day generator
              │
              ▼
          EMARequest
              │
              ▼
   ┌────────────────────────┐
   │   standalone EMA module│   ← this package (no DayForge, no Appa)
   └────────────────────────┘
              │
              ▼
           EMABundle
```

Later, separately, a **narrow host adapter** will map an Appa frozen day onto
`EMARequest`. This package does not know Appa exists.

---

## What the module does

For each participant-day it schedules **exactly five EMA opportunities** using
the Paper 3 *event-enriched stratified semi-random hybrid*:

- **≥ 3 background (semi-random)** prompts, drawn at random inside
  host-supplied daytime windows (default: eight strata spanning 08:00–23:00);
- **≤ 2 event-enriched** prompts, detected from the day in priority order
  `post_trip → post_active_episode → meaningful_context_transition →
  discretionary_fallback`, delivered **after** the event at the first suitable
  **stable** opportunity;
- when the day has no eligible events, **all five are semi-random** — event
  categories are never fabricated to satisfy diversity.

For every opportunity it records:

- **inherited contextual facts** (activity, domain, place type, social
  context, indoor/outdoor, linkage ids, device wear *if supplied*) — copied
  verbatim from the supplied day, **never altered, never hallucinated**;
- **synthetic protocol** values: prompt/response times, latency (right-skewed,
  10-minute expiry), trigger, window, response/miss/expiry status;
- **synthetic subjective values** `valence`, `energy`, `stress` on a documented
  5-point ordinal scale, produced by a **seeded, bounded, context-conditioned
  generator** (every rule is named, traced and registered);
- an **optional one-sentence context note** rendered by the LLM under a strict
  **closed-world contract** (validated, retried, offline fallback, `null`
  allowed) — or by the deterministic offline renderer when no LLM is available;
- **full provenance**: field-level origin classes, versions, hashes, seeds,
  rule traces, retry counts, the complete context packet.

EMA is treated exactly as the evidence base says it should be: a
**contextual and subjective annotation layer**, not accelerometer ground
truth. Inherited facts are authoritative; the module adds only what movement
sensing cannot provide.

## Quickstart

```python
import sys
sys.path.insert(0, "paper3_ema")          # or: pip install -e paper3_ema

from paper3_ema import generate_ema, audit_schedule, validate_bundle, default_config

# 1. a generic contextual day from any host system (mapping or ContextualDay)
day = {
    "participant_id": "p01",
    "date": "2026-05-04",
    "wake_time": "07:00",
    "sleep_time": "23:00",
    "episodes": [
        {"start_time": "07:50", "end_time": "08:20", "activity": "public_transport",
         "domain": "transport", "place_type": "vehicle", "social_context": "with_strangers"},
        {"start_time": "08:30", "end_time": "16:00", "activity": "sitting",
         "domain": "work", "place_type": "workplace", "social_context": "with_colleagues"},
        # ... more episodes covering the day ...
    ],
    "journeys": [
        {"journey_id": "jn-1", "start_time": "07:50", "end_time": "08:20", "mode": "bus",
         "origin_place_type": "home", "destination_place_type": "workplace"},
    ],
    "fixed_commitments": [
        {"commitment_id": "fc-1", "start_time": "10:30", "end_time": "10:45", "kind": "work"},
    ],
    # "device_wear": [...]            # optional — never fabricated if absent
}

bundle = generate_ema(day, seed=7)
print(len(bundle.records))             # 5
print(bundle.summary["response_rate"]) # calibrated 85–90% at cohort level
print(bundle.validation.status)        # PASS
print(bundle.audit.status.value)       # VALID

# 2. audit an existing (host-generated) schedule — read-only
from paper3_ema import contextual_day_from_mapping
cd = contextual_day_from_mapping(day)
verdict = audit_schedule(cd, ["09:00", "11:00", "13:00", "15:00", "19:00"])
print(verdict.status.value, verdict.reasons)

# 3. validate any bundle against the contract (e.g. after tampering checks)
result = validate_bundle(bundle, default_config(), day=cd)
print(summarise := result.status, len(result.errors))
```

Worked artifacts: [`examples/example_input.json`](examples/example_input.json)
and [`examples/example_output.json`](examples/example_output.json).

### Running the demonstration cohort

```
/home/user/.venv-ema/bin/python paper3_ema/demo/run_demo.py [participants] [days] [seed]
```

Writes `demo/demo_output/cohort_report.md` (human-readable),
`demo/demo_output/cohort_summary.json`, `demo/demo_output/ema_rows.csv` and
`demo/demo_output/bundle_example.json`.

### Running the tests

```
# deterministic / offline suite (no network, no credentials required)
/home/user/.venv-ema/bin/python -m pytest paper3_ema/tests -q

# DeepSeek integration tests activate automatically when DEEPSEEK_API_KEY is
# set AND api.deepseek.com is reachable; otherwise they report an explicit SKIP.
```

## Public API

| Function | Purpose |
|---|---|
| `generate_ema(request, seed, config, ...)` | full pipeline → `EMABundle` |
| `generate_ema_multi_day(requests, seed, ...)` | one bundle per day (same-day continuity only) |
| `generate_bundle(...)` / `generate_responses(...)` / `build_context(...)` | pipeline stages |
| `schedule_prompts(request, config, seed)` | the five scheduled `EMAPrompt`s (+ diagnostics via `schedule_for_day`) |
| `audit_schedule(day, prompt_times, config)` | read-only `VALID` / `NEEDS_REPAIR` verdict with reasons |
| `validate_bundle(bundle, config, day)` | bundle contract validation (10 check families) |
| `contextual_day_from_mapping(mapping)` | tolerant importer for host days |
| `default_config()` | the versioned `paper3_ema_v1` configuration |

Typed models: `EMARequest`, `ContextualDay`, `EMAContextPacket`, `EMAPrompt`,
`EMAResponse`, `EMARecord`, `EMAProvenance`, `EMABundle`, `EMAValidationResult`,
`ScheduleAuditResult`, `PersonaContextFacts`, `SubjectiveState`, `DayEvent`.

Configuration lives in a single versioned file,
[`config/paper3_ema_v1.yaml`](config/paper3_ema_v1.yaml) — **no protocol policy
is scattered through code constants**; the loader refuses to run with missing
required keys and hard-rejects the historical anti-patterns
(`force_event_diversity`, `force_one_miss_per_day`, LLM-selecting-subjective-values,
response-time context alignment).

## What this package deliberately does NOT do

- **No DayForge, no Appa, no diary/world generation, no OSM, no routing, no
  persona generation.** It consumes days; it does not build them.
- **No historical reporting noise.** The historical generator's standing
  under-reporting, forced misses, genericised locations and LLM-corrupted
  `reported_*` fields are rejected (see
  [`docs/PHASE0_ARCHAEOLOGY.md`](docs/PHASE0_ARCHAEOLOGY.md)). Inherited
  contextual facts stay authoritative.
- **The LLM never schedules, never edits facts, never invents**
  people/places/events/delays/weather/causes/journeys/diagnoses, and (by
  default) never selects the subjective values. It renders the optional note
  under a closed-world contract; see
  [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) §7.
- **No demographic path into subjective state.** A closed allowlist
  (childcare responsibility, work-schedule pattern, usual commute mode, usual
  sleep schedule) is enforced at construction; age, sex, occupation, health,
  fitness, personality and hobbies are refused (and tested).

## Package layout

```
paper3_ema/
├── config/paper3_ema_v1.yaml      versioned protocol configuration (single source of policy)
├── paper3_ema/
│   ├── __init__.py                public API
│   ├── vocab.py                   controlled vocabularies, scales, lexicons, persona guard
│   ├── timeutil.py                interval/time helpers
│   ├── models.py                  typed public models (EMARequest … EMABundle)
│   ├── config.py                  config loader (PyYAML optional; built-in parser fallback)
│   ├── day.py                     contextual-day importer + diagnostics
│   ├── eligibility.py             exclusions, stability, candidate minutes
│   ├── events.py                  event detection (the four Paper 3 trigger families)
│   ├── scheduler.py               event-enriched stratified semi-random hybrid
│   ├── audit.py                   read-only schedule auditor
│   ├── context.py                 bounded EMAContextPacket builder
│   ├── state.py                   seeded context-conditioned subjective-state generator
│   ├── missingness.py             stochastic response/non-response model
│   ├── latency.py                 right-skewed latency + 10-min expiry
│   ├── notes.py                   closed-world note validator
│   ├── llm.py                     DeepSeek client, renderer, retry, offline template
│   ├── provenance.py              field-level origin classes + run-level traceability
│   ├── pipeline.py                orchestration (generate_ema & friends)
│   ├── validate.py                bundle validators
│   ├── fixtures.py                adversarial test days + demonstration cohort
│   └── legacy.py                  importer for the historical diary format
├── tests/                         130+ offline tests (+ auto-skipping DeepSeek integration)
├── demo/run_demo.py               multi-day demonstration cohort
├── examples/                      example input / output JSON
└── docs/                          archaeology, architecture, assumptions, final review
```

## Provenance model

Every field of every record is traceable to exactly one origin class:

| class | meaning |
|---|---|
| `inherited_context` | copied verbatim from the supplied day (immutable) |
| `derived_context` | computed from the day by a documented rule (window, minutes-since-*, …) |
| `synthetic_protocol` | produced by the Paper 3 protocol (schedule, latency, expiry, status) |
| `synthetic_subjective` | produced by the seeded state generator (valence/energy/stress + trace) |
| `llm_rendered` | the optional note (LLM or offline template, closed-world validated) |

Run-level provenance records protocol/schema/scheduler/state-generator/auditor/
note-validator versions, LLM provider/model/template/decoding, seed, request
hash, context fingerprint, config hash, participant/date, linkage ids, prompt
type, prompt/response times, retry counts and validation state. The context
fingerprint is recomputed by the validator from the supplied day, so any
mutation of inherited facts is detected.

## Status

- Standalone module: **complete** — 132 offline tests passing; zero imports
  outside the standard library (+ optional PyYAML, + `requests` only in tests).
- Real DeepSeek integration: **implemented, pending credentials** — the sandbox
  currently has no `DEEPSEEK_API_KEY` and no egress route to
  `api.deepseek.com`; the integration tests report explicit SKIPs and a
  local-HTTP-server transport test covers the client offline. See
  [`docs/FINAL_REVIEW.md`](docs/FINAL_REVIEW.md) Q7.
