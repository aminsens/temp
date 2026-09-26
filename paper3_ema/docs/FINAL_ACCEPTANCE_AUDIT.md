# Final Acceptance Audit — Live DeepSeek Validation & Dashboard

**Date:** 2026-09-24 · **Auditor:** independent re-computation in the Arena sandbox
**Run under audit:** `live_20260924-192504` (user's own machine, Windows 10, Python 3.11.15,
`deepseek-flash`, thinking enabled, reasoning effort `high`, max_tokens 1024)
**Tool:** `live_validation/final_audit.py` (independent re-implementation of every check; does not
reuse harness report values except where a check is explicitly *agreement with* a harness artefact)
**Result:** **1037/1037 checks passed → PASS** (machine-readable: `live_validation/audit_out/final_audit.json`)

---

## 1. What was audited

The 11 acceptance items, each mapped to independent checks (A1–A12) run against the **actual
generated data** — the 12 raw artefacts plus the 28 live cohort bundles (140 prompt records) — with
offline regeneration through the identical code path (`generate_ema(mapping, seed, llm_client=None)`)
used wherever the acceptance item is about invariance or about what the LLM must *not* touch:

| # | Acceptance item | Check | Result |
|---|-----------------|-------|--------|
| 1 | Five prompts per day | A1 | PASS |
| 2 | Event/background balance | A2 | PASS |
| 3 | Exclusions (activity / non-realised / unstable) | A4 | PASS |
| 4 | Correct prompt-time linkage (inherited context at t) | A5 | PASS |
| 5 | Response / missing / expired counts | A6 | PASS |
| 6 | Latency | A7 | PASS |
| 7 | Non-degenerate valence/energy/stress | A8 | PASS |
| 8 | Zero inherited-context mutations | A5 + A9 | PASS |
| 9 | Zero unsupported facts surviving note validation | A10 | PASS |
| 10 | Live-LLM invariance of all structured fields | A11 (+A9) | PASS |
| 11 | Exact agreement between dashboard and underlying outputs | A12 | PASS |

Plus cross-checks: schedule audit status (A3), request/context fingerprint & request-hash
recomputation (A9), and no-credential-sweep of the dashboard (A12).

## 2. Per-check evidence

- **A1 — five prompts/day, strictly increasing (28 checks × sub-asserts):** every one of the 28
  participant-days has exactly 5 records; `prompt_time_min` strictly increasing; day index 1..5
  unique. 192 assertions, 0 failures.
- **A2 — balance (28 days):** ≥3 background (semi_random) and ≤2 event-enriched prompts per day in
  all 28 days. Cohort totals: semi_random 89, post_trip 35, context_transition 9,
  post_active_episode 7 (140).
- **A3 — schedule audit (28 days):** `bundle.audit.status == "VALID"` and `valid == true` in all 28.
- **A4 — exclusions (140 records × 3 rules):** no prompt falls in an episode whose activity is in
  `{sleeping, lying_awake, driving, cycling, running, other_vigorous}` unless the prompt carries the
  `post_active_episode` trigger with the episode *ended before* the prompt; no prompt in a
  non-realised interval/episode; no prompt in an unstable or unresolved episode unless
  `stability_relaxed == true`. 0 violations.
- **A5 — prompt-time linkage (28 days × 5 prompts × 4 assertions = 560):**
  - packet `episode_id` / `interval_id` / `journey_id` equal the day's `episode_at(t)` /
    `interval_at(t)` / `journey_at(t)` recomputed independently from the raw day;
  - every inherited-context field in the packet (`activity`, `domain`, `place_type`,
    `social_context`, `indoor_outdoor`) equals the day's value **at prompt time t** (recomputed, not
    read from the bundle) — this is the zero-mutation proof, item 8;
  - `post_trip` prompts: linked journey ended before the prompt, `current_journey_mode` matches,
    `minutes_after_event ≥ 0`;
  - packet fingerprint recomputed offline from the raw day equals the stored
    `record_provenance[prompt_id].packet_fingerprint` (no silent context drift between
    generation and storage). **0 mismatches.**
- **A6 — status semantics & cohort counts:** 140 records = **125 answered / 11 missed / 4 expired**
  (89.3% response rate), matching `06_cohort.json` exactly; `answered`/`expired` flags consistent
  with `status`; every missed record has `nonresponse_reason == "not_answered"`, every expired one
  `"expired"`; all 28 bundles `validation.valid == true` (only issue code:
  `response_rate_outside_calibration`, by-design simulation property).
- **A7 — latency (n=129 = answered + expired):** all ≥ 0; every answered latency ≤ 10 min; every
  expired latency > 10 min; mean (2.21) > median (1.03) as the simulated distribution requires.
- **A8 — V/E/S non-degeneracy (140 × 3 scales + 3 aggregate):** every valence/energy/stress in
  1..5; per-day each scale has ≥3 distinct values, std > 0.3, min ≤ 2, max ≥ 4 — no collapsed,
  constant or stereotyped states in any of the 28 days.
- **A9 — fingerprints & hashes (28 days):** offline-regenerated day
  `fingerprint(16)` equals the live bundle's `context_fingerprint`; `EMARequest.hash()`
  recomputed from the canonical request mapping equals the stored `request_hash` in all 28 bundles.
- **A10 — zero unsupported facts surviving (93 stored notes):** every non-null `context_note`
  re-validated with the closed-world validator `validate_note(note, packet)` against
  **offline-regenerated** packets (identical to live packets by A5/A11): **0 survivors**. This is
  item 9, independent of the harness's own counts.
- **A11 — live/offline invariance, all 28 cohort days:** each live bundle deep-diffed against an
  independently regenerated offline bundle for the same `(mapping, seed)`. Only allowed diffs:
  `context_note`, `note_source`, `note_validation`, per-record LLM note-rendering telemetry
  (`record_provenance.<prompt_id>.{llm_model, llm_provider, llm_decoding, note_attempts,
  note_fallback_reason, note_rejected_codes, retry_count}`), bundle-level `provenance.llm_*`,
  `summary.{notes_rendered, notes_null, note_sources}`. **0 unallowed diffs in all 28 days** —
  every scheduled, factual, subjective, latency, missingness and linkage field is byte-identical
  between offline and live-LLM runs. This is item 10 at cohort scale (the harness's phase-3
  single-day check is the same logic on one fixture day).
- **A12 — dashboard ↔ raw outputs (exact agreement, item 11):**
  - every dashboard-embedded block (`identity`, `connectivity`, `suite`, `smoke`, `cases`,
    `cohort`, `repeatability`, `invariance`) is **field-for-field equal** to the corresponding raw
    artefact JSON;
  - all 140 record rows match the raw bundles field-by-field (pid, date, time, trigger, status,
    note text, source, latency, V/E/S) after the same deterministic sort — **0 mismatches**;
  - KPI derivations recomputed from raw records: answered 125/125/125, answered-with-note
    91/91/91, LLM-final (answered) 40/40;
  - verdict and all 12 gate flags in the dashboard equal the raw run report;
  - no credential-shaped string (`sk-…`) anywhere in the HTML.

## 3. Defects found and fixed during this audit

Both defects are in **deliverable tooling** (never in the generated data, the module, or the
scientific parameters). Neither changes any live-run result; both are regression-pinned.

- **D1 — Phase-3 invariance allow-list regression (harness).** The committed
  `live_harness.py` carried a narrower marker set (bundle-level `provenance.llm_*` only). Verified
  against this run's `05_invariance.json`: that list would have classified **139 of the 255**
  recorded diffs (the per-record LLM telemetry paths) as *unallowed* on any re-run, flipping the
  invariance gate. The marker set that actually produced the 255/0 result is now restored in
  `live_harness.py` (and mirrored in `final_audit.py`) and pinned by
  `test_harness_offline.py::test_invariance_allowlist_covers_per_record_llm_provenance` (15 allowed
  paths asserted allowed, 10 non-LLM paths asserted denied).
- **D2 — dashboard KPI scope-mixing (KPI card + funnel).** The KPI "LLM-final notes" was derived as
  `final_non_null_answered − offline_fallback = 91 − 52 = 39`, which mixes scopes: the 52 offline
  renderings include one **expired** prompt not part of the 91 answered notes. Ground truth from the
  140 records: **40** answered LLM notes (91 answered-with-note = 40 LLM + 51 offline; 2 further
  notes on expired prompts = 1 LLM + 1 offline → 93 total non-null, 41 LLM overall). The funnel's
  final rows likewise summed to 125 while its "Rendered" row is 129 (answered + expired). Both are
  now computed directly from the embedded records: KPI shows **40/91** with the breakdown; funnel
  finals 41 + 52 + 36 = 129. Verified by re-running the audit (A12_kpis) and the DOM smoke test.

No live-run artefact was modified. The module and its tests are untouched by this audit (141
passed / 7 skipped after the two tooling fixes; the 7 skips are the no-network integration tests +
sandbox-conditional note tests, identical to before).

## 4. Verdict

**Audit verdict (the 11 acceptance items): PASS — 1037/1037 independent checks.**

The live-validation gate verdict **CONDITIONAL PASS stands** — the audit found no new condition.
The two documented caveats from the gate run are unchanged and remain the only reasons the overall
verdict is not an unqualified PASS:

1. **Reasoning-token budget:** with `max_tokens=1024`, ≈777 reasoning tokens/call mean left
   frequently truncated JSON (149/129 first-attempt parse failures were recovered by the retry +
   closed-world fallback chain; safety impact 0, quality impact = higher offline-fallback rate).
   A re-run with `DEEPSEEK_MAX_TOKENS=4096` is expected to raise first-attempt LLM acceptance.
2. **Synthetic cohort:** 4×7 fixture personas by design; the `response_rate_outside_calibration`
   issue code on every bundle is a documented simulation property, not a protocol violation
   (cohort response rate 89.3% is inside the 85–90% target band at cohort level).

---

## 5. Definitive minimal `EMARequest` / `EMABundle` contract (paste-ready)

The module boundary is exactly one function call: **`EMARequest` → `EMABundle`** for one
participant-day. An implementer (e.g. Codex) must reproduce these types, defaults and invariants.
Exhaustive serialised field order is demonstrated by
`paper3_ema/examples/example_input.json` (497 lines) and
`paper3_ema/examples/example_output.json` (11,684 lines), which are normative examples.

```text
BOUNDARY
  generate_ema(request: EMARequest) -> EMABundle
  (pipeline entry point: paper3_ema.pipeline.generate_ema(mapping, seed=..., llm_client=...);
   mapping is the EMARequest.to_dict() form shown in examples/example_input.json)

EMARequest            # public input; paper3_ema/models.py
  day: ContextualDay                     # the simulated day (episodes, intervals, journeys,
                                         # commitments, wear periods) — see example_input.json
  participant_id: str
  day_date: date
  seed: int = 0
  protocol_name: str = "paper3_ema_v1"
  protocol_config_hash: str | None = None    # sha256-based hash of the protocol config
  persona_context: PersonaContextFacts | None = None
  request_id: str | None = None        # auto: "req-{participant_id}-{date}-{seed}"
  prior_same_day_state: dict | None = None   # same-day continuity only
  llm: dict | None = None              # LLMSettings.to_dict() or None (offline)
  methods:
    context_fingerprint() -> str       # day.fingerprint(16); recomputed by validators —
                                       # any inherited-context mutation is detected
    hash() -> str                      # sha256(canonical_json()) hexdigest[:32]

PersonaContextFacts   # allow-listed stable persona facts (contextually justified only)
  childcare_responsibility, work_schedule_pattern,
  usual_commute_mode, usual_sleep_schedule
  # demographic attributes (age/sex/occupation/health/fitness/personality/hobbies)
  # MUST NOT be present or used — enforced and tested boundary.

EMABundle             # public output: one participant-day
  participant_id: str
  day_date: date
  protocol_name: str
  records: list[EMARecord]
  provenance: EMAProvenance
  validation: EMAValidationResult | None
  scales: dict
  summary: dict
  audit: ScheduleAuditResult | None
  convenience: .prompts, .responses, .answered(), .rows()  # rows() = [r.flat_row()]

EMARecord
  prompt: EMAPrompt
  response: EMAResponse
  packet: EMAContextPacket
  provenance: EMAProvenance             # run-level object shared by all records;
                                        # per-record trace at
                                        # provenance.record_provenance[prompt_id]

EMAPrompt
  prompt_id, participant_id, day_date, schedule_index: int,
  trigger: "semi_random"|"post_trip"|"post_active_episode"|"context_transition"|
           "discretionary_fallback",
  prompt_time: datetime, prompt_time_min: float,
  window_index: int|None, window_label: str|None,
  episode_id / interval_id / journey_id / event_id: str|None,
  event_kind: str|None, minutes_after_event: float|None,
  selection_reason: str,
  is_event_enriched: bool, stability_relaxed: bool,
  recall_frame: str = "current_at_prompt_time",
  expiry_minutes: float = 10.0,
  expires_at: datetime|None,
  inherited_context: dict               # {activity, domain, place_type,
                                        #  social_context, indoor_outdoor} at prompt time
  packet: EMAContextPacket

EMAResponse
  prompt_id, status: "answered"|"missed"|"expired",
  prompt_time: datetime, response_time: datetime|None, latency_min: float|None,
  expiry_minutes: float = 10.0,
  answered: bool, expired: bool, usable_for_alignment: bool,
  subjective: SubjectiveState|None,
  context_note: str|None,
  note_source: "llm"|"offline_template"|None,
  note_validation: dict|None,           # attempts, retries, source, fallback_reason,
                                        # raw_outputs, validations, rejected_codes, model, provider
  device_wear: DeviceWear|None,
  nonresponse_reason: "not_answered"|"expired"|None,
  response_probability: float|None,     # simulated propensity (audit only)
  context_reference_time: str = "prompt_time"

SubjectiveState
  valence: int, energy: int, stress: int     # each in 1..5
  latent: dict[str, float]
  contributions: dict[str, dict[str, float]] # rule-level trace
  noise: dict[str, float]
  rules_applied: tuple[str, ...]
  generator_version: str

EMAContextPacket    # bounded factual context given to generator/renderer;
  prompt_time_min, prompt_time, time_of_day, minutes_since_wake,
  window_index, window_label,
  activity, activity_label, domain, place_type, social_context, indoor_outdoor,
  purpose_category, device_wear,
  episode_id, interval_id, journey_id,
  minutes_in_current_episode, minutes_since_activity_change, episode_is_unstable,
  current_journey_mode,
  preceding_activity, preceding_domain, preceding_place_type, preceding_journey_mode,
  preceding_journey_duration_min, preceding_journey_delayed, preceding_journey_crowded,
  minutes_since_journey_end, minutes_since_active_episode_end,
  recent_activity_summary, minutes_to_next_commitment, next_commitment_kind,
  next_commitment_requires_travel, previous_state, minutes_since_previous_prompt,
  allowed_entities, allowed_causes, weather_available
  # NO proper names, NO narrative text, NO demographic attributes — every field
  # inherited from the day or derived by a documented rule.

EMAProvenance
  protocol_version, schema_version, package_version, scheduler_version,
  state_generator_version, auditor_version, note_validator_version,
  llm_provider, llm_model, llm_template_version, llm_decoding,
  llm_calls: int, llm_retries: int, seed, request_hash, context_fingerprint,
  config_hash, config_name, participant_id, day_date, generated_at,
  field_provenance: dict,                 # field -> origin class
  record_provenance: dict[str, dict],     # per prompt_id: prompt_type, prompt_time,
                                          # response_time, episode/interval/journey ids,
                                          # validation_state, retry_count,
                                          # note_attempts, note_source, note_fallback_reason,
                                          # note_rejected_codes, note_template_version,
                                          # llm_provider, llm_model, llm_decoding,
                                          # packet_fingerprint, ...
  notes: list[str]                        # static documentation strings (not note texts)

EMAValidationResult
  valid: bool, status: "PASS"|"FAIL",
  issues: list[EMAValidationIssue{code, severity, message, prompt_id, field}],
  checks_run: int, summary: dict

ScheduleAuditResult
  status: AuditStatus, valid: bool,
  issues: list[ScheduleAuditIssue], metrics: dict,
  prompt_times: list[str], auditor_version: str

Input-day reference types (example_input.json shows exact shapes)
  EpisodeRef     activity, domain, place, social_context, indoor_outdoor, purpose,
                 exertion, is_fixed_commitment, is_realised, stability
  IntervalRef    kind, resolved, realised, stability
  JourneyRef     mode, purpose, distance_km, delayed, crowded
  FixedCommitmentRef, WearPeriodRef
  ContextualDay  lookup methods: episode_at(t), interval_at(t), journey_at(t), wear_status_at(t)

REQUIRED INVARIANTS (all audited in A1–A12; an implementation that violates any of them fails
the acceptance audit)
  1. Exactly 5 prompts per day, strictly increasing prompt times.
  2. Per day: >= 3 background (semi_random) and <= 2 event-enriched prompts.
  3. Exclusions: never prompt during sleeping / lying_awake / driving / cycling / running /
     other_vigorous episodes (a finished active episode may trigger post_active_episode);
     never in non-realised intervals/episodes; unstable/unresolved only with stability_relaxed.
  4. Every inherited-context value equals the day's value AT PROMPT TIME (lookups at t);
     the LLM sees only EMAContextPacket and can never alter inherited facts.
  5. 10-minute expiry: answered latency <= 10, expired > 10, all >= 0.
  6. Status semantics: answered/missed/expired mutually consistent; nonresponse_reason set;
     usable_for_alignment only for answered records with a usable state.
  7. V/E/S integers in 1..5; per-day non-degenerate (>=3 distinct values, std > 0.3,
     min <= 2, max >= 4); demographic attributes have no causal path into the state
     (enforced boundary + tests).
  8. Notes: LLM renders prose only; closed-world validation against the packet; on failure the
     fallback chain is offline template -> None; 0 unsupported facts may survive (medical
     claims, invented events/places/people, unsupported delay references, multiple sentences).
  9. Provenance: request_hash, context_fingerprint, per-record traces and
     packet_fingerprint present and recomputable offline.
  10. Invariance: with the same (mapping, seed), a live-LLM run must be byte-identical to an
      offline run everywhere except context_note / note_source / note_validation and LLM
      provenance (bundle-level provenance.llm_* and per-record note-rendering telemetry).
  11. Schedule audit VALID on every bundle; response-rate calibration reported, not faked.
  12. Determinism: same (mapping, seed) offline run is byte-identical (phase-5 repeatability).
  13. No credentials in any artefact, log or provenance (audited by sweep).
  14. No new architecture: simple typed Python, explicit rules, deterministic seeds, minimal
      dependencies; the LLM never owns scheduling, facts, events, places, people or journeys.

Protocol config (hash 6cd9101d73e98891): 5 prompts/day, 10-minute expiry, target response
rate band 85-90%, trigger mix and base rates as in paper3_ema/config/.
```

## 6. Reproduction

```bash
# venv
python3 -m venv /home/user/.venv-ema && /home/user/.venv-ema/bin/pip install pyyaml pytest requests

# full local suite (no network needed for 141 tests)
cd /home/user/temp && /home/user/.venv-ema/bin/python -m pytest paper3_ema/tests paper3_ema/live_validation -q

# final acceptance audit (needs the run artefacts in live_validation/artifacts/live_20260924-192504/)
/home/user/.venv-ema/bin/python paper3_ema/live_validation/final_audit.py
# → live_validation/audit_out/final_audit.json ; exit 0 on PASS

# dashboard (static; any static file server)
python3 -m http.server 8090 --bind 0.0.0.0 --directory paper3_ema/live_validation/dashboard

# a fresh live run (user machine, key only in env)
cd paper3_ema && DEEPSEEK_API_KEY=... /home/user/.venv-ema/bin/python -m live_validation.live_harness --phase all
```
