# Development of a Standalone EMA Simulation Module for Paper 3

**A development report: from task brief and evidence base to a verified, live-validated module**

| | |
|---|---|
| Module | `paper3_ema` — event-enriched stratified semi-random hybrid EMA protocol, `paper3_ema_v1` |
| Repository | `aminsens/temp`, branch `arena/01a0d410-temp` |
| Companion documents | `ARCHITECTURE.md` (final architecture + API) · `PHASE0_ARCHAEOLOGY.md` (evidence from the prior implementation) · `SCIENTIFIC_ASSUMPTIONS.md` (assumptions register, classes A/B/C) · `FINAL_REVIEW.md` (ten-question review) · `LIVE_DEEPSEEK_VALIDATION.md` (live gate report) · `FINAL_ACCEPTANCE_AUDIT.md` (final audit + implementation contract) · `POLICY_REVISION_1_1_0.md` (post-audit protocol revision) · `EMA_RUNTIME_FREEZE.md` (runtime freeze record) |
| Status | Module complete, protocol `paper3_ema_v1` v**1.1.0** (schema 1.0.0); live-validated against DeepSeek in two runs (1024 and 4096-token budget, both CONDITIONAL PASS, 12/12 gates); final acceptance audit 1037/1037 (PASS); 49-day Appa integration run (49/49 valid days after policy revision 1.1.0) |

---

## Abstract

This document reports *how* the Paper 3 EMA module was developed: the task as originally
posed, the evidence base it was built against, the design decisions and their
justifications, the implementation structure, and the verification process — ending with
a live validation against the real DeepSeek API and an independent final acceptance
audit. The central methodological stance, fixed by the task brief and enforced
throughout, is that EMA is a **contextual and subjective annotation layer** over
inherited, authoritative contextual facts — never a ground-truth source, never a
corruption layer, and (except for rendering one optional note) never an LLM
responsibility. Every design rule is classified in the scientific assumptions
register as (A) directly evidence-supported, (B) evidence-motivated with a
design-chosen parameter, or (C) a Paper 3 engineering choice; nothing of class C
is presented as if it were A.

---

## 1. Introduction

### 1.1 Background

Ecological Momentary Assessment in body-mounted accelerometer studies of physical
activity (PA) and sedentary behaviour (SB) contributes what movement sensing cannot:
the domain, purpose, social setting, location and subjective meaning of movement.
Seven independent deep-research runs over this literature, consolidated in
`EMA_Definitive_Synthesis.md`, converge on five universal findings that shaped every
design decision in this module:

1. EMA is not ground truth — it is near-ground-truth, weak labelling or contextual metadata.
2. EMA's core value is *context*.
3. Temporal alignment of sparse EMA against dense sensor data is the hardest unsolved problem.
4. EMA is routinely collected but rarely integrated into modelling — the field's largest missed opportunity.
5. Event-triggered (sensor-informed) EMA is methodologically superior to pure random prompting.

Paper 3 requires a *synthetic* EMA layer for simulated contextual days: a
scientifically defensible stand-in for what such a layer would produce, with
reproducibility and auditability as first-class requirements — because its outputs
will feed downstream alignment and analysis work, and because any hidden
assumption in the simulation would contaminate that work.

### 1.2 The original task (the prompt)

Development started from a written brief with a precise boundary. In summary, the
brief required:

- **A standalone module** consuming an externally supplied *contextual day* and
  emitting a complete, provenance-traced EMA bundle — explicitly **no DayForge,
  no Appa, no connection to the existing September cohort**, working in an
  isolated environment. Appa was intentionally unavailable; any Appa statement in
  the evidence corpus is unverified, and the package had to work completely
  without it (integration to be handled separately later, by a narrow host adapter).
- **A fixed protocol shape**: five EMA opportunities per participant-day under an
  *event-enriched stratified semi-random hybrid* (≥3 background semi-random,
  ≤2 event-enriched), with event categories **detected, never fabricated**.
- **Immutability of inherited context**: contextual facts are copied verbatim from
  the supplied day, never re-reported with noise and never altered by an LLM; the
  historical generator's reporting-noise layer (standing under-reporting, forced
  misses, genericised locations) was explicitly rejected as a method to carry
  forward.
- **Synthetic subjective states** — valence/energy/stress on a documented
  5-point ordinal scale — from a *seeded, bounded, context-conditioned,
  rule-traced* generator, with **no demographic path** into state generation
  (no age/sex/occupation/health/fitness/personality/hobbies; only a closed
  allowlist of contextually-justified stable persona facts, enforced and tested).
- **A strictly bounded role for the LLM**: render an optional one-sentence
  context note under a closed-world contract (validated, retried, offline
  fallback, `null` always acceptable). The LLM may not schedule, change facts,
  invent events/places/people/journeys/delays/weather/causes, make medical
  diagnoses, or infer psychological traits; LLM selection of the subjective
  values was prohibited *unless* accompanied by documented justification and
  demonstrated superiority over the structured generator.
- **Scientific integrity machinery**: a versioned configuration as the single
  source of policy; full field-level provenance; a read-only schedule auditor;
  bundle validation; and a **scientific assumptions register in which class-C
  choices must not be disguised as class-A**.
- **Stop conditions** under which the developer must stop and report rather than
  improvise: evidence/design conflict, an undiscovered historical capability,
  DeepSeek unreliability, insufficient transparency, or obvious
  stereotypes/incoherence in generated states.
- **Code-quality constraints**: simple typed Python, small modules, explicit
  rules, minimal dependencies (standard library + optional PyYAML; `requests`
  only in tests), deterministic seeds, no agent frameworks, databases, web
  servers or plugins.
- A **deliverables checklist of 21 items** (architecture, typed API, scheduling,
  auditor, context packet, state generator, missingness, latency, provenance,
  validation, register, …) that doubles as the acceptance checklist.

### 1.3 Scope of this document

This report covers the *development* — requirements, evidence handling, design,
implementation, testing, and verification. Numerical results of the live run are
reported in `LIVE_DEEPSEEK_VALIDATION.md`; the machine-checked acceptance verdict
in `FINAL_ACCEPTANCE_AUDIT.md`.

---

## 2. Source materials and epistemics

### 2.1 Source hierarchy

The repository at the base commit contained three distinct kinds of material,
and the brief fixed a strict hierarchy for using them:

| Source | Role | Files |
|---|---|---|
| **Design brief (the prompt)** | current authoritative requirements | the task message; constraints restated above |
| **Evidence corpus** | verification base for design decisions | `EMA_Definitive_Synthesis.md` (532-line cross-source synthesis, April 2026), `CONCLUSION.md` (agreement/disagreement register), seven primary research reports: `Chatgpt.md`, `Chatgpt_deep_research.md`, `Deepseek.md`, `Gemini.md`, `Kimi.md`, `Scite_Opus4.6.md`, `Scite_Opus4.6_v2.md`, plus the predecessor synthesis `EMA_Accelerometer_Synthesis_v1.md` (used only to check the definitive version dropped nothing silently) |
| **Historical implementation** | prior-implementation *evidence only* — never a source of scientific requirements | `EMA-Diary-Generation/` (current DSPy-based diary + EMA pipeline, "Jar of Life", Trondheim) and `EMA-Diary-Generation-BACKUP-20260409/` |

The rule of use: the brief says *what*; the evidence corpus says *what is
supported*; the historical code says *what was done before* (salvageable
assets vs. anti-patterns). No scientific requirement was inferred from
historical code.

### 2.2 Phase 0 — repository archaeology

Before writing any module code, a full archaeology pass
(`PHASE0_ARCHAEOLOGY.md`) inventoried the repository and **verified all nine
suspected behaviours of the historical EMA generator** against the cited source
lines — every claim confirmed, including the exact mechanisms:

- 6 probes by default, placed at **episode-index** spacing (clusters on fragmented days);
- **forced** standing and cycling probes inserted "for under-reporting";
- **exactly one** missed response hard-coded (in both the deterministic and the LLM path);
- a programmatic **65% standing misreport** layer (60% in the backup);
- **location genericisation** through a 24-entry city-specific keyword table;
- a complete `gt_*` vs. `reported_*` corruption layer over ground truth;
- **no subjective variables at all** in emitted probes (declared but never populated);
- validators that **reward the corruption** (5–35% mismatch rates, existence of misses);
- and — a finding *beyond* the brief's list — the diary generator's persona
  prompt context dumping age, gender, occupation, fitness, health notes, hobbies
  and personality traits into an LLM prompt: precisely the wholesale demographic
  exposure the brief prohibits. (The historical EMA layer itself was
  persona-blind, so there is no demographic path to inherit — but the pattern
  was explicitly not to be copied.)

The same pass produced a **salvage table** (REUSE / ADAPT / REJECT per
component), which is the direct lineage between old and new:

| Historical asset | Decision | Rationale |
|---|---|---|
| Controlled vocabularies (activity, domain, place type, social, I/O, wear, triggers) | **REUSE (adapted)** | strongest asset in the old code; adapted to 5-point *numeric* ordinal scales, `place_type`, the Paper 3 trigger set |
| `EMAProbe` dual-timestamp record shape | **ADAPT** | prompt/response/latency and trigger kept; the entire `gt_*/reported_*` corruption pair dropped — inherited context is authoritative and is not re-reported |
| `EMASchedule` config block | **ADAPT** | structure kept; values corrected for Paper 3: 6→**5** prompts/day, 300 s→**10-min** expiry, flat 0.15 missingness→**calibrated 85–90%**, single flat config→**versioned YAML** |
| Waking-window start/end pair | **ADAPT** | upgraded to stratification across host-supplied daytime windows |
| HETUS 2018 taxonomy mapping | **REJECT** | a diary/world responsibility; importing it would build a second DayForge |
| Index-spaced prompt placement | **REJECT** | neither random nor stratified; cannot express event enrichment |
| Forced standing/cycling probes | **REJECT** | sampling contamination for a validator's benefit, no evidence support |
| All reporting-noise layers + genericisation | **REJECT** | explicitly forbidden by the brief |

### 2.3 Stop conditions, and what actually stopped

The brief's stop conditions were applied, and the final review
(`FINAL_REVIEW.md`, "Stop-condition report") records the outcome honestly:

1. **Evidence/design conflict** — *two material divergences found and declared*
   rather than improvised over: (i) the item set (synthesis prefers a 2-item
   affect battery; Paper 3's primary RQ justifies 3 items — §7.1 below);
   (ii) event-triggered compliance (real event-triggered compliance can be far
   below the 85–90% calibration band; the canonical profile simulates events
   only slightly harder to answer, with a `literature_divergent` sensitivity
   profile as a one-line config change).
2. **Historical capability not represented in the brief** — the wholesale
   persona dump (§2.2) was reported; it informed the demographic allowlist
   design rather than the schedule.
3. **DeepSeek unreachable from the sandbox** — *true*: no credential and a
   platform-level egress block to `api.deepseek.com`. Reported as such; the
   live validation was subsequently run by the author on their own machine
   (see §6.2), which closed this gap.
4. **Insufficient state-generator transparency** — *false*: every draw carries
   a full rule-level trace.
5. **Deterministic stereotypes / incoherent states** — *false*: covered by
   dedicated tests (§5.3).

---

## 3. Requirements analysis

### 3.1 Functional requirements

Derived from the brief and the evidence corpus (with the class of each
governing rule from the assumptions register):

| # | Requirement | Governing evidence/decision |
|---|---|---|
| R1 | Exactly 5 opportunities per participant-day | S-2 (B): synthesis §9.3 "5–6 prompts/day", §9.5 "4–6 for studies >7 days"; 5 is Paper 3's choice inside the supported range |
| R2 | Hybrid sampling: ≥3 semi-random stratified across host-supplied daytime windows + ≤2 event-enriched | S-3 (A for the design), S-4/S-5 (C for the exact split and priority order), S-7 (B) |
| R3 | Event families `post_trip`, `post_active_episode`, `context_transition`, `discretionary_fallback`, **detected from the day, never invented**; semi-random fill when no eligible events | S-3/S-5/S-6 |
| R4 | Exclusions: sleep, driving, cycling, running/vigorous, non-realised movement, unresolved intervals, unstable micro-transitions. (Unknown *posture* was an additional class-C exclusion in 1.0.0 and was removed by policy revision 1.1.0 — §6.5.) | S-11 (A): safety + non-response evidence; demarcation-uncertainty motivation |
| R5 | Inherited facts copied verbatim, hashed, re-derivable; no re-reporting noise | S-1 (A) |
| R6 | Subjective states V/E/S, 5-point ordinal, seeded, bounded, context-conditioned, rule-traced; no demographic path | S-14 (B, divergence declared), S-19…S-30 (C) |
| R7 | Stochastic missingness (never forced), calibrated 85–90% answered at cohort level as a *simulation property* | S-31…S-34 (A/B) |
| R8 | Right-skewed latency, 10-minute expiry, dual timestamps, context anchored to prompt time | S-35…S-37 (B/C), S-17 (A) |
| R9 | Optional one-sentence closed-world note; LLM renders only; `null` acceptable; offline fallback | S-38…S-42 (C, A-motivated) |
| R10 | Full provenance (field origin classes, versions, hashes, seeds, rule traces) | S-43…S-45 (C) |
| R11 | Read-only schedule auditor + ten-family bundle validation | deliverables #7, #14 |
| R12 | Versioned YAML as single source of policy; loader hard-rejects historical anti-patterns | S-13 et al.; the loader refuses `force_event_diversity`, `force_one_miss_per_day`, LLM-selecting-subjective-values, and response-time context anchoring |

### 3.2 Non-functional requirements

- **Determinism**: identical `(day, seed, config)` → byte-identical bundle
  (SHA-256-based stable seeds; `generated_at` is a deterministic run anchor —
  midnight of the simulated day — not wall-clock time).
- **Standalone operation**: no network, no credential, no external service
  required; the LLM is an optional renderer with a deterministic offline
  fallback, so the module is fully functional offline.
- **Credential hygiene**: the DeepSeek key may exist only as an environment
  variable; never in any file, log, artefact, provenance, commit or error
  message (swept by the harness and re-audited).
- **Simplicity**: standard library only (+ optional PyYAML with a verified
  byte-equivalent built-in parser fallback; `requests` only in tests).

### 3.3 Explicit non-goals

No DayForge/Appa/diary/world generation, no OSM or routing, no persona
generation, no second DSPy-style optimiser, no LLM self-correction loops on
diaries, no cross-day narrative continuity (same-day structured continuity
only), no databases/services/web layers, no reintroduction of historical
reporting noise. Each was a deliberate rejection, recorded in
`ARCHITECTURE.md` §12.

---

## 4. Design

### 4.1 The boundary: `EMARequest` → `EMABundle`

The module's entire public surface is one boundary: a typed `EMARequest`
(carrying a host-agnostic `ContextualDay` — episodes, intervals, journeys,
fixed commitments, optional device wear, host-supplied waking windows) in, a
complete `EMABundle` out (5 `EMARecord`s + run-level `EMAProvenance` +
`EMAValidationResult` + `ScheduleAuditResult` + summary). The tolerant
importer `contextual_day_from_mapping` accepts several field-naming
conventions and never guesses unknown activity values; the `legacy` adapter
proves the contract against the repository's historical diaries. The full
field-level contract is reproduced paste-ready in
`FINAL_ACCEPTANCE_AUDIT.md` §5 — it is the specification an independent
implementation (e.g. a Codex re-implementation) must meet.

**The inheritance rule** is the design's load-bearing wall: anything in
`EMARequest.day` is *inherited context* — copied verbatim into records, hashed
into the `context_fingerprint`, and re-derived by the validator from the day.
Immutability is enforced three ways: structurally (frozen dataclasses),
forensically (the validator re-derives every inherited field and recomputes the
fingerprint, so tampering is detected), and by construction (the only factual
material the state generator and renderer ever see is the bounded
`EMAContextPacket`).

### 4.2 Scheduling design

`schedule_for_day` implements the hybrid in five steps:

1. **Event detection** — the four trigger families in Paper 3 priority order
   (`post_trip > post_active_episode > context_transition >
   discretionary_fallback`), each event carrying the ids of the
   episode/interval/journey it was detected from; per-kind daily caps;
   sleep-adjacent transitions excluded. Detection thresholds (S-13, class C)
   are bounded design choices motivated by the sedentary-bout literature.
   Since policy 1.1.0, all four detectors share one eligibility predicate —
   `_has_stable_opportunity` (a stable minute *inside a waking window*),
   so detection, placement and audit agree by construction (revision
   correction B; §6.5).
2. **Event slots** — up to 2 placements, each at the *first stable
   opportunity* after the event (45-min search horizon, S-10: event-triggered
   delivery eliminates recall error — the synthesis's "STRONGEST in theory"
   alignment result), in an unused window, respecting a 30-min minimum gap.
3. **Background slots** — ≥3 semi-random draws, stratified across the
   host-supplied daytime windows (default: eight strata 08:00–23:00,
   configurable — the *concept* is host-supplied, never asserted, since the
   host system is unavailable and not in the repository); candidate minutes
   are the exclusion-safe, stable minutes of the window.
4. **Top-up / infeasibility** — remaining slots filled semi-randomly across all
   windows; a genuinely infeasible day emits fewer than 5 prompts *with an
   explicit note* rather than violating an exclusion.
5. **Fragmented-day fallback** (S-12, class C) — when the strict
   5-min-boundary-stability rule yields no legal minute, a documented relaxed
   path drops *only* the boundary margin (all safety exclusions retained),
   and every affected prompt carries `stability_relaxed` plus a
   `selection_reason` marker; the auditor reports these as warnings, never
   silently.

Randomness is driven by `stable_seed(participant, date, seed)` (SHA-256-based,
never Python's `hash`), so identical inputs give byte-identical schedules.

### 4.3 The context packet (the closed world)

`EMAContextPacket` is the **only** factual input to the state generator and
the note renderer. It is bounded by construction: current-episode facts
(activity, domain, place *type*, social context, indoor/outdoor, coarse
purpose) plus linkage ids and optional wear status; derived bounded
quantities (minutes-since-wake/activity-change/journey-end within 180-min
windows, a bounded 0–1 recent-exertion aggregate, 60-min activity summary,
minutes-to-next-commitment); the immediately preceding activity and preceding
journey (delay/crowding **only if the host documented them**); and
`allowed_entities`/`allowed_causes` — the closed vocabulary handed to the
renderer. Same-day structured continuity only (`previous_state`,
`minutes_since_previous_prompt`) — no previous-day narrative anywhere. No
proper names, no narratives, no demographic attributes; enforced by tests on
the serialised packet.

### 4.4 The subjective-state generator

A seeded latent-state model with a visible equation:

```
latent  = baseline(item) + day_effect(persona-day) + clip(Σ rules)
        → + continuity anchor (same-day previous EMA, weight 0.35, ≤240 min)
        + noise(σ per item) → hard clip [1,5]
ordinal = clamp5(round(latent + sampling noise σ=0.6))
```

Every rule is named, magnitude-configured in YAML, and traced per draw
(`subjective_trace` in record provenance). The rule set (S-19…S-30) covers
circadian offsets, wake ramp, recent exertion (energy ↓ / valence ↑ / stress ↓,
45-min half-life), post-journey mode offsets, *documented-only*
delay/crowding, schedule pressure (stress ↑ as a commitment approaches),
post-transition and social-company offsets, domain offsets **capped at ±0.30
per item**, and the two allowlisted persona facts, each applicable *only
inside its contextual role* (childcare facts inside childcare episodes;
commute-mode mismatch in transport contexts).

Two tests pin the brief's "no stereotypes" requirement from both sides: a
**fixed-work-context stereotype test** proves `domain=work` does not
deterministically map to one state (≥2 distinct values across 30 seeds), and a
**no-constant-random test** proves states are context-sensitive (40-seed
latent means differ between contexts). Baselines (3.2/3.2/2.6) and all
magnitudes are class-C design choices with no empirical claim — the register
states this explicitly.

### 4.5 Missingness and latency

Missingness is an **independent Bernoulli draw per prompt** — never
"exactly one miss" (the loader hard-rejects it). Base rates per trigger
(0.88–0.94, events slightly lower) plus direction-evidenced modifiers
(high exertion ×0.92, engaged context ×0.97, late window ×0.95, device not
worn ×0.85, optional study-day decay off by default) are calibrated so a
large cohort lands at **85–90% answered** — declared in the YAML and the
register as *a simulation property inside the observed literature range
(67–92%)*, never as a claim about true human compliance. The declared
divergence for event-triggered prompts (real compliance can be much lower)
has a one-line `literature_divergent` sensitivity profile.

Latency is a right-skewed lognormal (μ=−0.05, σ=1.3 ⇒ mean ≈2.1 min, median
≈0.9 min, P(>10 min)≈3.4%) with mild post-exertion/late-window multipliers.
**Dual timestamps are always recorded**; responses past the 10-minute expiry
are stored as `EXPIRED` — content kept, flagged, `usable_for_alignment=false`.
Context is anchored to `prompt_time`, hard-locked by the config loader
(`latency.context_reference_time` is not configurable away).

### 4.6 The closed-world LLM note

The LLM's one permitted job: render **one sentence** (≤24 words / ≤160 chars /
one sentence) about the packet's closed world, or reply `null`. The validator
`notes.validate_note` rejects with category-coded issues
(`unsupported_person/place/activity/event/delay/weather/cause/journey`,
`medical_condition`, `psychological_trait_inference`, `demographic_reference`,
`proper_noun`, `too_long`, `multiple_sentences`, `unparseable_output`,
`unsupported_reference`). The render loop retries on rejection, falls back to
a deterministic offline template (closed-world *by construction*, and still
re-validated), and finally to `null`. **Every stored note is re-validated** —
a violation cannot ship. Decoding settings (temp 0.4, top_p 0.9) are recorded
in provenance.

### 4.7 The explicit LLM-role decision

**The LLM does not select valence/energy/stress.** `llm.allowed_to_select_subjective_values`
is validated to be `false` by the config loader. The documented justification
(`ARCHITECTURE.md` §7, register S-40): (1) the evidence base is explicitly
cautious about open LLM text at dataset scale, and the historical pipeline's
own test reports document LLMs emitting unbounded reasoning around JSON and
corrupting fields; (2) the brief requires *demonstrated superiority* before
LLM subjective selection — a rule-traced seeded generator is auditable and
reproducible per draw, while an LLM choosing 1–5 values is opaque per draw and
couples quantitative outputs to API nondeterminism, a strict downgrade for a
simulation whose goal is reproducibility; (3) the evidence base's own best
practice for affect is a short structured battery — which is exactly what the
state generator implements; (4) the LLM's irreplaceable contribution is
natural-language rendering, and there the closed-world contract bounds the
risk completely. Flipping the flag is a config change the loader rejects
without new justification and comparative evidence.

### 4.8 Provenance and validation

Every emitted field maps to exactly one origin class —
`inherited_context | derived_context | synthetic_protocol | synthetic_subjective |
llm_rendered`; unclassified fields fail validation. Run-level provenance
records protocol/schema/scheduler/state-generator/auditor/note-validator
versions, LLM provider/model/template/decoding, seed, `request_hash`,
`context_fingerprint`, `config_hash`, participant/date and the deterministic
`generated_at` anchor. Record-level provenance carries the per-record trace:
linkage ids, prompt/response times, retry counts, validation state, the
complete packet (with its own fingerprint) and the rule-level subjective trace.

`validate_bundle` runs **ten check families** (sampling; placement via the
auditor; linkage; inherited-facts re-derivation; subjective bounds/presence;
missingness explicitness; latency arithmetic and expiry semantics; note
closed-world re-validation; provenance completeness; demographic-leak scan)
and returns coded, severity-tagged issues. `audit_schedule` is read-only
(covered by a test that proves it cannot mutate its inputs) and reports
`VALID`/`NEEDS_REPAIR` with ~20 coded reasons.

### 4.9 Configuration as the single source of policy

`config/paper3_ema_v1.yaml` (hash `6cd9101d73e98891`) is the *only* place
protocol policy lives; every parameter carries its A/B/C class inline. The
loader refuses to run with missing required keys and **hard-rejects the
historical anti-patterns** — `force_event_diversity`, `force_one_miss_per_day`,
LLM-selecting-subjective-values, and response-time context alignment — so the
anti-patterns found in Phase 0 cannot re-enter through configuration.

---

## 5. Implementation

### 5.1 Module structure

Twenty-one small, typed, stdlib-only modules with a strict layering
(`ARCHITECTURE.md` §1): `models` (the public boundary types) · `vocab`
(vocabularies, scales, lexicons, the demographic persona guard) · `timeutil` ·
`config` (loader) · `day` (tolerant importer + diagnostics) · `eligibility`
(exclusions, stability, candidate minutes) · `events` (detection) ·
`scheduler` (the hybrid) · `audit` (read-only auditor) · `context` (bounded
packet) · `state` (seeded generator) · `missingness` · `latency` · `notes`
(closed-world validator) · `llm` (DeepSeek client, renderer, retry, offline
template) · `provenance` (origin classes + traceability) · `validate` (bundle
validators) · `pipeline` (orchestration) · `fixtures` (adversarial test days +
demo cohort) · `legacy` (historical-format importer) · `__init__` (public API).
Dependencies: standard library only (+ optional PyYAML; `requests` only in
tests). No DSPy, no agent frameworks, no databases, no web servers.

### 5.2 Construction order

Development proceeded in phases, each leaving the suite green:

1. **Phase 0 — archaeology** (§2.2): inventory, verification of the nine
   historical claims, salvage table. *No module code written yet.*
2. **Models and configuration**: the boundary types, vocabularies, the versioned
   YAML with inline A/B/C classes, and the strict loader (anti-pattern
   rejections) — because the config loader is where historical anti-patterns
   are killed, it was built before the components it constrains.
3. **Day model, eligibility, events, scheduler** — the schedule first, since it
   is the part most constrained by the evidence (S-1…S-13) and the part the
   auditor must police; the read-only auditor was built alongside, not after.
4. **Context packet, state generator, missingness, latency** — the synthetic
   layers, each with its assumptions-register section written *with* the code
   (classes assigned per rule, divergences declared as found).
5. **Notes + LLM + offline fallback**, with the closed-world validator before
   the renderer (the contract first, the generator second).
6. **Provenance, validation, pipeline**, then fixtures, the demonstration
   cohort, and the final review (ten questions).
7. **Live-validation harness** (separate, test-only package under
   `live_validation/`): a six-phase protocol — Phase 1 (suite + live
   connectivity), Phase 2 (15 controlled adversarial cases: each a known
   unsupported-fact template that *must* be found and contained), Phase 3
   (single-day live/offline invariance), Phase 4 (4×7 live cohort), Phase 5
   (offline repeatability + live confined diff), Phase 6 (credential sweep +
   gate report). Designed so the author could run it on their own machine
   (the sandbox has no egress to `api.deepseek.com`) with the key only in the
   environment.

### 5.3 Testing strategy

- **Offline suite (130+ tests, no network, no credential)**: scheduling
  invariants (five prompts, increasing times, balance, exclusions, gaps,
  stratification, infeasible-day behaviour, relaxed-fallback flagging),
  importer tolerance, packet boundedness (no proper names/narratives/
  demographics in serialised form), state-generator bounds + both
  anti-stereotype tests, missingness/latency arithmetic and expiry semantics,
  note validator (each rejection code exercised), **tampering tests** (mutate
  an inherited field in a bundle → validator must detect via
  re-derivation + fingerprint mismatch), provenance completeness, config
  anti-pattern rejection, determinism (byte-identical repeat runs).
- **DeepSeek integration tests (4)**: activate automatically when
  `DEEPSEEK_API_KEY` is set *and* `api.deepseek.com` is reachable; otherwise an
  explicit SKIP. A local-HTTP-server transport test covers the client offline.
- **Adversarial fixtures**: deliberately pathological days (fragmented,
  event-dense, event-free, unstable) in `fixtures.py`, used by both the tests
  and the live harness's controlled-case phase.
- **Harness-level tests** (offline): the structural diff + allow-list
  filtering, the case matrix, cost-estimator arithmetic, the secret-redaction
  sweep, the report/verdict builder — plus the regression test added by the
  final audit (§6.4, defect D1).

At hand-off the module suite stood at 133 passed / 7 skipped locally (136 /
3 on a machine with network for the integration tests); after the audit's two
regression tests, 141 passed / 7 skipped; after policy revision 1.1.0
(10 new policy regression tests + 2 config tests), **145 passed / 7 skipped**.

---

## 6. Verification and validation

### 6.1 The ten-question final review

`FINAL_REVIEW.md` answers, with file/line evidence, the ten questions the
brief implies (runs without DayForge? consumes a generic day? exactly five
opportunities? event+random combined correctly? inherited facts immutable?
subjective variables clearly synthetic? can DeepSeek invent unsupported facts?
everything traceable? same seed reproduces structured output? what remains
scientifically uncertain?). All seven scientific uncertainties are declared
open — calibration-vs-reality, item set, rule magnitudes, window concept,
live LLM behaviour (then untested), prompt reactivity, demarcation beyond
placement — and Q7's conditional answer ("pending live validation") is what
the live phase exists to close.

### 6.2 Live validation against DeepSeek (gate: CONDITIONAL PASS)

Because the sandbox could not reach `api.deepseek.com` (platform-level
destination-IP block; no guardrail was bent — no certificate-verify disabling,
no third-party routing, no SNI spoofing), the six-phase harness was shipped
turnkey and run by the author on their own machine
(run `live_20260924-192504`, Windows, Python 3.11.15, `deepseek-flash`,
thinking enabled, reasoning effort high, 1024-token completion budget):

- Phase 1: 134 passed / 5 skipped; **4/4 live integration tests** passed
  (the config-default `deepseek-chat` alias serves as of the run date).
- Phase 2: **15/15 controlled cases found, 0 survivors** — every
  unsupported-fact template (invented people/places/events, medical claims,
  improper nouns, multi-sentence, unsupported delay) was rejected by the
  closed-world chain.
- Phase 3: live/offline invariance — **255 diffs, 0 unallowed** (all diffs in
  note + LLM-provenance fields only).
- Phase 4: **28 participant-days, 140 opportunities: 125 answered / 11 missed
  / 4 expired (89.3%)**; 339/339 API calls succeeded; 28/28 bundles valid;
  0 unsupported facts survived; latency mean 4231 ms / p95 5656 ms; cost
  $0.346 peak / $0.173 off-peak from returned token usage × published rates.
- Phase 5: offline repeatability byte-identical; live confined diff 133 / 0
  unallowed.
- **Gate: 12/12 → CONDITIONAL PASS**, with one documented finding: with a
  1024-token completion budget, ≈777 reasoning tokens/call mean truncated
  visible JSON (149 first-attempt parse failures, all recovered by the
  retry + closed-world fallback chain — zero safety impact; quality impact =
  a 52/129 offline-fallback rate). The recommended re-run
  (`DEEPSEEK_MAX_TOKENS=4096`) was carried out and is reported in §6.5.

The 4096-token run (`live_20260924-220804`, frozen runtime) confirmed the
diagnosis: first-attempt valid parse 73/56 → **127/2**, truncation
rejections 149 → 9 (−94%), offline fallbacks 52 → 25 (40% → 19% of rendered
notes), null notes (answered) 34 → 16, non-null (answered) 91 → 109; 15/15
controlled cases again with zero survivors; **CONDITIONAL PASS, 12/12
gates** — with the fallback rate still above the 15% reporting threshold,
retained as the report's caveat. Cross-run invariance (all 28 cohort bundles,
1024 vs 4096): **4,451 diffs, 0 unallowed** — every difference confined to
`context_note` and note-rendering telemetry. The run was recorded in the
runtime freeze record (`EMA_RUNTIME_FREEZE.md`): status
`READY_FOR_APPA_ADAPTER`, no prompt/protocol/schema/validation/API changes.

### 6.3 The final acceptance audit (PASS, 1037/1037)

`final_audit.py` re-computed **all 11 acceptance items independently** from
the raw artefacts and offline regeneration — not from the harness's own
reports: five prompts/day (A1), balance (A2), exclusions (A4), prompt-time
linkage with context values recomputed *at time t from the raw day* (A5 — the
zero-mutation proof), status/latency semantics (A6/A7), V/E/S non-degeneracy
in all 28 days (A8), fingerprint + request-hash recomputation (A9), all 93
stored notes re-validated closed-world → 0 survivors (A10), live-vs-offline
deep-diff on **all 28 days** → 0 unallowed (A11), and exact
dashboard↔artefact agreement including KPI derivations and a credential sweep
(A12). Result: **1037/1037 — PASS**; the CONDITIONAL PASS gate verdict stands
with its two documented caveats. The audit also contains the definitive,
paste-ready `EMARequest`/`EMABundle` contract.

### 6.4 Defects found by verification, and how they were handled

Verification found six defects across three phases (module development,
final audit, post-audit use); all were **genuine**, all fixed minimally with
regression tests and documented commits — none by loosening a check or
tuning a scientific parameter:

1. **Legacy-path test** hard-coded an absolute sandbox path → false skips on
   other machines. Fixed to source-level assertions + a regression test.
2. **D1 — invariance allow-list regression** (found by the final audit): the
   committed harness allow-list had narrowed to bundle-level markers that
   would have classified 139 of the 255 recorded per-record LLM-provenance
   diffs as *unallowed* on any re-run. The marker set that produced the
   recorded 255/0 was restored and pinned by
   `test_invariance_allowlist_covers_per_record_llm_provenance`.
3. **D2 — dashboard KPI scope-mixing** (found by the final audit):
   "LLM-final notes" was derived as 91−52=39, mixing scopes (the 52 offline
   renderings include one expired prompt not in the 91). Correct value from
   the records: 40 answered LLM notes (93 total non-null, 41 LLM overall);
   funnel finals corrected to 41+52+36=129.

Two further defects surfaced in post-audit use by the author, handled by the
same discipline (minimal fix, regression tests, documented commit):

4. **D3 — harness runtime bugs** (found by the author's own live run):
   `LiveTimingClient` missing its `@dataclass` decorator (constructor
   rejected the thinking/reasoning/max-token overrides), `_run_pytest`
   invoked with the wrong cwd (repo-root-relative test paths unresolved), and
   `id()`-based set membership for unhashable `EMARecord`s in representative
   picking. All three fixed in one commit; offline harness self-tests 8/8
   after the fix.
5. **D4 — unknown posture made whole stable episodes unpromptable** (found by
   the 49-day Appa integration): `eligibility.exclude_unknown_activity`
   defaulted to `true` — the only class-C entry among the exclusions, absent
   from the class-A evidence row (S-11) that defines the exclusion set, and
   redundant as a stability guard (stability is enforced by the
   unstable-episode/micro-transition exclusions and boundary margins). It
   removed exactly the moments where EMA adds most value (the evidence base
   holds that *domain*, not posture, resolves sensor ambiguity). Revision
   1.1.0: default `false`, and the key added to `REQUIRED_KEYS` so the policy
   can never silently revert to an implicit code default. Physical state
   stays unknown — nothing is inferred to enable a prompt.
6. **D5 — event detection disagreed with event placement** (same integration):
   each of the four detectors used its own ad-hoc eligibility test and none
   enforced the scheduler's `require_prompt_inside_window` rule, so events
   ending before the first waking window were reported eligible while
   unplaceable — and the auditor (consuming the same detector) raised
   `event_enrichment_missing` on days where no legal prompt existed.
   Revision 1.1.0: the shared `_has_stable_opportunity` predicate; detection,
   placement and audit now agree by construction.

### 6.5 Post-audit development (author, 2026-09-25)

After the audit, development continued on the same branch with three
commits: the harness runtime fixes (D3); the second live run plus artefacts,
logs and the runtime freeze record (reported in §6.2); and the 49-day **Appa
integration** — the separately-planned host-adapter step, run by the author
against real frozen Appa days. The integration produced 46/49 valid days and
243/245 opportunities; the three invalid bundles were fully accounted for by
D4 + D5, both fixed as **policy revision 1.1.0** (`POLICY_REVISION_1_1_0.md`,
285 lines: the five audit questions per correction, the demonstrated failing
case, the latent scope of the defect, the measured effect, and what
deliberately did not change).

Measured effect of 1.1.0 on the frozen 49-day cohort (offline, scheduler +
auditor only — no provider call): **49/49 valid days, 245/245
opportunities**, 0 days with fewer than 5 prompts, 0 detected events with no
legal prompt minute (was 12 days affected), 0 prompts in an excluded minute,
0 fabricated postures, 0 protected upstream changes; the three previously
failing days flipped FAIL → PASS and NEEDS_REPAIR → VALID (eligible minutes
39 → 494, 194 → 526, 69 → 522). The schema is unchanged (1.0.0 — no field
added, removed or retyped); the safety exclusion set S-11 is intact; sampling,
stability, state-generator, missingness, latency and note-rendering policy
are untouched; `meta.protocol_version` is now `1.1.0` so 1.1.0 cohorts are
distinguishable in provenance from 1.0.0 ones.

---

## 7. Scientific assumptions and their limits

The full register is `SCIENTIFIC_ASSUMPTIONS.md` (S-1…S-45 with evidence
citations). Its integrity rules, restated here because they are the
module's core scientific-ethics contract:

- Classes: **A** directly supported by the evidence corpus · **B**
  evidence-motivated, parameter value is a design choice · **C** Paper 3
  engineering choice. **Nothing of class C is presented as A** — e.g. the
  exact 3+2 split (S-4), the event priority order (S-5), the stability margin
  (S-9), all state-generator magnitudes (S-19…S-30) are C and are labelled C
  in the YAML.
- **Three divergences from the evidence are declared, not hidden** (§7.1 of
  the register): the 3-item battery vs. the synthesis's 2-item preference
  (justified by Paper 3's primary RQ); event-triggered compliance simulated
  only slightly harder than background (with a `literature_divergent`
  sensitivity profile); and the eight-window concept treated as
  host-supplied input because the host system is unavailable and not in the
  repository.
- **One policy correction is declared** (revision 1.1.0): the class-C
  unknown-posture exclusion added in 1.0.0 was removed as redundant with the
  class-A stability guards and counter to the evidence base's domain-over-
  posture principle — corrected via the register's own discipline (the
  correction cites S-11 and the A/B/C legend directly, `POLICY_REVISION_1_1_0.md`).
- **What is explicitly not claimed**: no 85–90% figure is a claim about true
  human compliance; no subjective value is an observed human measurement; no
  note text is human speech; no rule is a claim about the psychology of real
  people. All synthetic outputs are declared synthetic in the YAML
  (`scales.synthetic_declaration`) and in the data.

---

## 8. Limitations

1. **Calibration vs. reality** — 85–90% is a simulation target inside the
   observed 67–92% literature range; event-triggered prompts in particular
   are simulated more compliant than the most extreme published evidence
   (WEALTH event-based median 34%). The sensitivity profile exists precisely
   for this.
2. **No real human data** — the module is a synthetic layer for synthetic
   days; its ecological validity is bounded by its inputs.
3. **Rule magnitudes are bounded design choices** (class C) — directionally
   motivated, not fitted; no empirical moment estimates for synthetic
   participants exist in the corpus.
4. **Live LLM quality is budget-sensitive** — the 1024-token run showed
   reasoning tokens consuming the completion budget; the 4096-token re-run
   confirmed first-attempt acceptance rises sharply (127/129 parse, 19/129
   first-attempt accept) and the offline-fallback rate falls (40% → 19%),
   though it remains above the 15% reporting threshold — retained as the
   frozen runtime's declared caveat. Safety (zero survivors) was unaffected
   in both runs.
5. **Prompt reactivity is not modelled** (Maher 2018: small post-prompt PA
   reduction) and **demarcation** is handled at placement (stability margins)
   but not as a data-quality model.
6. **The eight-window default** is a documented stand-in for the
   host-supplied stratification; results that depend on window structure
   should be re-run with the real host windows.

---

## 9. Reproducibility

```bash
# environment
python3 -m venv .venv-ema && .venv-ema/bin/pip install pyyaml pytest requests

# offline suite (deterministic; no network, no credential)
.venv-ema/bin/python -m pytest paper3_ema/tests paper3_ema/live_validation -q

# demonstration cohort (offline)
.venv-ema/bin/python paper3_ema/demo/run_demo.py

# normative I/O examples
paper3_ema/examples/example_input.json      # an EMARequest-day mapping
paper3_ema/examples/example_output.json     # the resulting EMABundle

# live validation (author machine; key only in the environment)
DEEPSEEK_API_KEY=... .venv-ema/bin/python -m live_validation.live_harness --phase all
DEEPSEEK_MAX_TOKENS=4096                    # recommended for the next run

# final acceptance audit (against a run's artefacts)
.venv-ema/bin/python paper3_ema/live_validation/final_audit.py
```

Protocol identity: `paper3_ema_v1` — protocol version `1.0.0` (config hash
`6cd9101d73e98891`) for the live runs and the audit; protocol version
`1.1.0` (schema unchanged, 1.0.0) from the post-audit policy revision,
frozen-record config sha256 `7dc0928a…d67f95`. Bundles are pure functions of
`(day, seed, config)`.

---

## 10. Future work

- **Downstream integration**: feeding `EMABundle` rows (`.rows()`) into the
  Paper 3 alignment pipeline, where EMA plays the annotation-layer role the
  evidence base prescribes — the runtime freeze record
  (`READY_FOR_APPA_ADAPTER`) and the 49-day Appa integration are the
  stepping-stones for this.
- **Sensitivity analysis** on the declared divergences (item set;
  `literature_divergent` event base rates) for the paper.
- **Provider robustness**: an optional second-model run (the frozen runtime
  is `deepseek-flash`-specific by design).
- **Fallback-rate reduction** if the 19% offline-template rate at 4096
  tokens becomes material for the paper (e.g. budget or prompt-level
  changes — any such change would follow the revision-1.1.0 discipline:
  documented, class-tagged, regression-tested).

---

## 11. Source documents (this repository)

| Document | Role in development |
|---|---|
| `EMA_Definitive_Synthesis.md` | the definitive cross-source synthesis (the "full report"); primary design brief |
| `CONCLUSION.md` | cross-source agreement/disagreement register; the only explicit "Paper 3" reference |
| `Chatgpt.md`, `Chatgpt_deep_research.md`, `Deepseek.md`, `Gemini.md`, `Kimi.md`, `Scite_Opus4.6.md`, `Scite_Opus4.6_v2.md` | the seven research reports; cited per-decision in the assumptions register |
| `EMA_Accelerometer_Synthesis_v1.md` | predecessor synthesis (completeness check only) |
| `EMA-Diary-Generation/`, `…-BACKUP-20260409/` | historical implementation; evidence for Phase 0, not for requirements |
| `paper3_ema/docs/PHASE0_ARCHAEOLOGY.md` | Phase 0 report (verified historical claims; salvage table) |
| `paper3_ema/docs/ARCHITECTURE.md` | final architecture, typed API, the LLM-role decision (§7) |
| `paper3_ema/docs/SCIENTIFIC_ASSUMPTIONS.md` | the A/B/C assumptions register (S-1…S-45) |
| `paper3_ema/docs/FINAL_REVIEW.md` | ten-question review + stop-condition report |
| `paper3_ema/docs/LIVE_DEEPSEEK_VALIDATION.md` | live gate report (CONDITIONAL PASS) |
| `paper3_ema/docs/FINAL_ACCEPTANCE_AUDIT.md` | final audit (1037/1037 PASS) + definitive implementation contract |
| `paper3_ema/docs/POLICY_REVISION_1_1_0.md` | post-audit protocol revision (unknown posture promptable; detection/placement/audit alignment), with measured effect |
| `EMA_RUNTIME_FREEZE.md` (repo root) | runtime freeze record: 1024→4096 comparison, cross-run invariance, `READY_FOR_APPA_ADAPTER` |
| `paper3_ema/live_validation/artifacts/live_20260924-192504/` | live run, 1024-token budget (baseline) |
| `paper3_ema/live_validation/artifacts/live_20260924-220804/` | live run, 4096-token budget (frozen runtime) |
| `paper3_ema/config/paper3_ema_v1.yaml` | the versioned protocol (v1.1.0), single source of policy, inline A/B/C classes |
