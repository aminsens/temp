# Final package architecture

This document is deliverable #3 (final package architecture) and #4 (typed
public API) of the Paper 3 EMA task, together with the design decisions the
evidence base required to be made explicit — above all §7 (role of the LLM).

## 1. Layering

```
┌─────────────────────────────────────────────────────────────────────┐
│ public API (paper3_ema/__init__.py)                                 │
│   generate_ema · generate_ema_multi_day · schedule_prompts          │
│   audit_schedule · validate_bundle · contextual_day_from_mapping    │
│   default_config · models (EMARequest … EMABundle)                  │
├─────────────────────────────────────────────────────────────────────┤
│ pipeline.py        orchestration + provenance assembly              │
├──────────────┬──────────────┬───────────────┬───────────────────────┤
│ scheduler.py │ context.py   │ state.py      │ missingness.py        │
│ (+events.py, │ (bounded     │ (seeded,      │ latency.py            │
│  eligibility)│  packet)     │  bounded,     │ notes.py + llm.py     │
│              │              │  transparent) │ (closed-world)        │
├──────────────┴──────────────┴───────────────┴───────────────────────┤
│ day.py (importer) · models.py · vocab.py · timeutil.py · config.py  │
├─────────────────────────────────────────────────────────────────────┤
│ audit.py (read-only) · validate.py (read-only) · provenance.py      │
└─────────────────────────────────────────────────────────────────────┘
        configuration: config/paper3_ema_v1.yaml  (single source of policy)
```

Dependencies: **Python standard library only** (dataclasses, enum, random,
hashlib, json, re, urllib). PyYAML is used when present; a built-in parser
(verified byte-equivalent to PyYAML on the shipped config) is the fallback.
No DSPy, no agent frameworks, no databases, no web servers.

## 2. The boundary object: `EMARequest` / `ContextualDay`

`ContextualDay` is the generic, host-agnostic description of a day:

- `episodes` — semantic episodes (activity, domain, place **type**, social
  context, indoor/outdoor, purpose, optional exertion, `is_fixed_commitment`,
  `discretionary_event`, `is_realised`, `stability`);
- `intervals` — sensor-derived intervals, optionally flagged
  **unresolved** / **non-realised** / **unstable**;
- `journeys` — travel legs (mode, purpose, place types, optional documented
  `delayed` / `crowded`);
- `fixed_commitments` — appointments used for schedule pressure;
- `device_wear` — **optional**; never fabricated;
- `waking_windows` — host-supplied daytime strata (default: eight equal
  strata 08:00–23:00);
- `wake_min`, `sleep_min`, `weather` (only if documented), `timezone`.

`contextual_day_from_mapping` is the tolerant importer (several field-naming
conventions are accepted; unknown activity values become `None`, they are not
guessed). The legacy adapter (`paper3_ema.legacy`) proves the contract against
the repository's historical diaries.

**Inheritance rule.** Anything in `EMARequest.day` is *inherited context*:
copied into records verbatim, hashed into the `context_fingerprint`, and
re-derived by the validator. The module never re-reports these facts with
noise (the historical corruption layer is rejected —
`docs/PHASE0_ARCHAEOLOGY.md` §2).

## 3. Scheduling (deliverable #6)

`schedule_for_day(day, config, seed)`:

1. **Event detection** (`events.py`) — four trigger families in Paper 3
   priority order:
   1. `post_trip` — a journey ended (or a transport episode without a journey
      record); prompts **after** the trip;
   2. `post_active_episode` — an exercise/vigorous bout ≥10 min ended;
   3. `context_transition` — a meaningful transition (domain / place /
      indoor–outdoor change) that has settled ≥5 min;
   4. `discretionary_fallback` — a discretionary event (shopping, childcare,
      social, self-care) under way;
   each event carries its source episode/interval/journey ids (events are
   detected, never invented); per-kind daily caps; sleep-adjacent transitions
   excluded.
2. **Event slots** — up to `max_event_enriched` (2) placements, each at the
   **first stable opportunity** after the event (search horizon 45 min), in a
   daytime window not already used, respecting the 30-min minimum gap.
3. **Background slots** — at least `min_background` (3) semi-random draws,
   stratified: windows shuffled, preferring windows not yet represented and
   with the most eligible minutes; candidate minutes are the exclusion-safe,
   stable minutes of the window (step 1 min).
4. **Top-up** — if fewer than 5 placements succeeded, remaining slots are
   filled semi-randomly across all windows; if the day is genuinely
   infeasible, fewer than 5 prompts are emitted **with an explicit note**
   rather than by violating an exclusion.
5. **Fragmented-day fallback** — when the strict boundary-stability rule
   yields no legal minute, a documented relaxed path (boundary margin dropped,
   *all safety exclusions retained*) is used, and every affected prompt carries
   the `stability_relaxed` flag plus the marker in `selection_reason`; the
   auditor reports these as warnings, never silent.

Seeding: `stable_seed(participant, date, seed)` (SHA-256 based — never Python
`hash`) drives all randomness; identical inputs give byte-identical bundles.

## 4. The schedule auditor (deliverable #7)

`audit_schedule(day, prompt_times, config)` is **read-only** (it cannot mutate
its inputs — covered by a test). It accepts HH:MM strings, datetimes, minutes,
`EMAPrompt`s or mappings with metadata, and reports `VALID` / `NEEDS_REPAIR`
with explicit, coded reasons:

`prompt_count` · `outside_waking_window` · `excluded_context` ·
`window_linkage_mismatch` · `prompt_clustering` · `duplicate_prompt_time` ·
`insufficient_spread_windows` · `insufficient_spread_minutes` ·
`window_overload` · `insufficient_background` · `too_many_event_prompts` ·
`event_enrichment_missing` · `event_without_detected_event` ·
`invalid_episode_linkage` · `invalid_interval_linkage` ·
`invalid_journey_linkage` · `episode_linkage_mismatch` ·
`interval_linkage_mismatch` · `prompt_before_event_end` ·
`prompt_too_far_after_event` · `stability_relaxed` (warning) ·
`trigger_unspecified` (warning).

## 5. Context packet (deliverable #8)

`EMAContextPacket` is the **only** factual material the state generator and
renderer may see. Bounded by construction:

- current episode facts (activity, domain, place **type**, social, I/O,
  coarse purpose category) + linkage ids + optional device-wear status;
- derived bounded quantities: `minutes_since_wake`,
  `minutes_since_activity_change`, `minutes_in_current_episode`,
  `minutes_since_journey_end` (≤180 min window),
  `minutes_since_active_episode_end` (≤180 min), `recent_exertion_60min`
  (bounded 0–1 exponential-decay aggregate), `recent_activity_summary` (60-min
  minutes-per-activity), `minutes_to_next_commitment` (+ kind, travel flag);
- the immediately preceding activity/domain/place and preceding journey
  (mode, duration, **documented** delay/crowding only);
- `allowed_entities` / `allowed_causes` — the closed-world vocabulary handed
  to the renderer;
- `previous_state` / `minutes_since_previous_prompt` — **same-day** continuity
  only (no previous-day narrative anywhere in the packet).

**No proper names, no narratives, no demographic attributes** — enforced by
tests on the serialised packet.

## 6. Subjective-state generator (deliverable #9)

`state.generate_state(packet, seed, ...)` — seeded, reproducible, bounded,
transparent:

```
latent = baseline(item) + day_effect(persona-day) + clip(Σ rules)
       → continuity anchor (same-day previous EMA, weight 0.35, ≤240 min)
       + noise(σ per item)  → hard-clip [1,5]
ordinal = clamp5(round(latent + sampling noise))
```

Rules (each named, magnitude-configured, traced per draw; registered in
`docs/SCIENTIFIC_ASSUMPTIONS.md` S-4…S-11):

| rule | effect (direction) |
|---|---|
| `circadian.<period>` | small time-of-day offsets per construct |
| `wake_ramp` | early-morning energy ramp over first 60 min awake |
| `recent_exertion.*` | post-activity energy ↓, valence ↑, stress ↓ (bounded, 45-min half-life) |
| `post_journey.{active|public|car}` | small mode-specific offsets, 30-min window |
| `journey_delayed` / `journey_crowded` | **only** when the host documents delay/crowding |
| `schedule_pressure.*` | stress ↑ as a fixed commitment approaches (30/60/120-min horizons) |
| `post_transition.*` | tiny offset within 20 min of an activity change |
| `social_company.*` | small valence/stress offset when company is present |
| `domain.<domain>.*` | **capped at ±0.30 per item** — deliberately unable to dominate |
| `outdoor.*` | tiny outdoor offset |
| `childcare_responsibility.*` | allowed persona fact, **only inside childcare episodes** |
| `commute_mode_mismatch.*` | allowed persona fact, **only in transport contexts** |

Both prohibited extremes are tested out: the fixed work-context stereotype
test proves `domain=work` does **not** deterministically map to one state
(≥2 distinct values across 30 seeds, no stereotyped bucket), and the
no-constant-random test proves states are context-sensitive (40-seed latent
means differ between contexts). The full per-rule contribution of every draw
is stored in `record_provenance[prompt_id].subjective_trace`.

## 7. Role of the LLM (explicit decision + justification)

**Decision: the LLM renders the optional note only. It does not select
`valence`/`energy`/`stress`.** `llm.allowed_to_select_subjective_values` is
validated to be `false` by the config loader; flipping it requires the
justification below plus comparative evidence.

Why this is the evidence-supported choice (required justification):

1. The synthesis is explicitly cautious about LLM/EMA content quality: open
   text is "rich but unscalable … cannot be automatically processed at
   dataset scale" (§6.3), and the historical pipeline's own test reports
   document that LLMs emit unbounded reasoning around JSON and corrupt fields
   — the failure mode a closed-world contract must contain.
2. The brief's stop conditions require that, if the LLM is given subjective
   selection, it must "demonstrate stronger behaviour than a transparent
   structured generator". A structured generator is trivially auditable
   (rule-level traces, seed reproducibility); an LLM choosing 1–5 values would
   be opaque per draw and would couple the quantitative outputs to API
   nondeterminism — a strict downgrade for a scientific simulation whose
   stated goal is reproducibility and auditability.
3. The evidence base's own best practice for affect is a *2–3 item bounded
   battery* (valence/arousal/energy ± stress, §6.1 Tier 3, Kimi item table) —
   i.e. a small structured instrument, not an open generative process. The
   state generator implements exactly that instrument.
4. The LLM's irreplaceable contribution is **natural-language rendering**
   (the optional interpretability note), where its strengths lie, and where
   the closed-world contract + validator + retry + fallback bounds its risks
   completely (every stored note is re-validated; violations are impossible
   to ship).

What the LLM may do: render one sentence (≤24 words, ≤160 chars, ≤1 sentence)
referring only to packet-supplied entities/events/places/activities/causes,
or reply `null`. What it may not do: schedule; alter facts; invent people,
places, activities, events, delays, weather, causes, journeys; produce medical
or psychological-trait claims; reference demographics. The contract is
enforced by `notes.validate_note` (category-coded rejections:
`unsupported_person/place/activity/event/delay/weather/cause/journey`,
`medical_condition`, `psychological_trait_inference`, `demographic_reference`,
`proper_noun`, `too_long`, `multiple_sentences`, `unparseable_output`,
`unsupported_reference`).

## 8. Missingness & latency (deliverables #11–12)

- **Missingness** (`missingness.py`): independent Bernoulli draw per prompt,
  base rate per trigger (0.88–0.94), documented direction-evidenced modifiers
  (high exertion, engaged context, late window, device not worn, optional
  study-day decay). **Never** "exactly one miss" (hard-rejected by the config
  loader). Canonical calibration: 85–90% answered across a large cohort —
  a simulation property, not a compliance claim (literature: 67–92%;
  event-triggered compliance can be much lower — registered as B).
- **Latency** (`latency.py`): lognormal (μ=−0.05, σ=1.3 ⇒ mean ≈2.1 min,
  median ≈0.9 min, P(>10 min) ≈3.4%), mild multipliers after exertion / late
  window. **Dual timestamps always recorded.** Responses past the 10-minute
  expiry are recorded as `EXPIRED`: content kept, flagged,
  `usable_for_alignment=false`. Context is **always** anchored to
  `prompt_time` (`latency.context_reference_time` hard-locked to
  `prompt_time` by the config loader).

## 9. Provenance (deliverable #13) and determinism

- Field-level: `FIELD_PROVENANCE` maps **every** emitted field to
  `inherited_context | derived_context | synthetic_protocol |
  synthetic_subjective | llm_rendered`; unclassified fields fail validation.
- Run-level: protocol/schema/scheduler/state-generator/auditor/note-validator
  versions, LLM provider/model/template/decoding, seed, `request_hash`,
  `context_fingerprint` (day facts), `config_hash`, participant/date,
  `generated_at`.
- Record-level: prompt type, prompt/response times, episode/interval/journey
  ids, `retry_count`, `validation_state`, the complete context packet (with
  its own fingerprint) and the rule-level subjective trace.
- `generated_at` is a **deterministic run anchor** (midnight of the simulated
  day), not wall-clock time — bundles are pure functions of
  (day, seed, config), so identical inputs give byte-identical artifacts.
- Immutability is enforced structurally (frozen context dataclasses) **and**
  forensically (the validator re-derives inherited facts from the day and
  recomputes the fingerprint; tampering tests prove detection).

## 10. Validation (deliverable #14)

`validate_bundle` runs ten check families (sampling, placement via the
auditor, linkage, inherited-facts re-derivation, subjective bounds/presence,
missingness explicitness, latency arithmetic & expiry semantics, note
closed-world re-validation, provenance completeness, demographic-leak scan)
and returns `EMAValidationResult` with coded, severity-tagged issues.
`summarise_validation` renders it for reports.

## 11. Host-adapter contract (for the later, separate integration)

A future Appa/DayForge adapter needs only to:

1. map one frozen day into the `ContextualDay` mapping shape (any tolerant
   field names; see `contextual_day_from_mapping`);
2. supply `wake`/`sleep`, `waking_windows` (or accept the default eight
   strata), `episodes` with activity/domain/place **type**/social/I-O,
   `journeys` (with documented delay/crowding when the host has them),
   `fixed_commitments`, and `device_wear` **only if the host records it**;
3. call `generate_ema(day_mapping, seed=…)`.

No callback, no shared state, no import. The module stays standalone; the
adapter is a function, not a framework.

## 12. What was deliberately not built

Second DayForge (diary/world generation, OSM, routing, personas) — rejected;
DSPy/GEPA/GRPO optimisers — rejected (heavy, diary-oriented); LLM self-correct
loops on the diary — rejected (incompatible with immutable inherited context);
fixed standing-underreporting, forced-miss, genericised-location corruption —
rejected (Phase 0 §2); cross-day narrative continuity — rejected (only
same-day structured continuity is in the brief); databases/services/web
layers — rejected by the code-quality constraints.
