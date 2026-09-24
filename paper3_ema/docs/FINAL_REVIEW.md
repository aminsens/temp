# Final review — the ten questions

Deliverable #19 companion. Answers are stated explicitly and each is backed by
a test or an artifact in this repository.

## Q1. Can this package run without DayForge?

**Yes.** Zero imports from DayForge or Appa anywhere in the package (verified:
`paper3_ema/` imports only the standard library, its own submodules, and —
optionally — PyYAML). The full offline test-suite (132 tests) runs against
standalone fixture days with no host system present. The demo cohort
(`demo/run_demo.py`) is generated entirely from internal fixtures.

## Q2. Can it consume a generic externally supplied day?

**Yes.** `contextual_day_from_mapping` (and `generate_ema` taking a mapping
directly) accepts a generic day mapping with tolerant field naming
(`start`/`start_time`, `activity`/`primary_activity`, `place_type`/
`location_type`, `social`/`social_context`/`company`, …). Missing elements stay
absent (never fabricated); unknown activity values become `None` rather than
being guessed. Proof: `examples/example_input.json` is exactly such a mapping,
and `tests/test_legacy_import.py` imports the repository's *historical*
diaries (a different schema) through the same contract.

## Q3. Does it generate exactly five EMA opportunities?

**Yes** — `sampling.opportunities_per_day: 5`, and
`test_exactly_five_opportunities` asserts five prompts for **all ten**
adversarial fixtures. The one documented exception is a genuinely infeasible
day (no legal minute exists at all), where the scheduler emits fewer prompts
**with an explicit INFEASIBLE note** rather than violating an exclusion — and
the auditor would then report `prompt_count` as `NEEDS_REPAIR`, so the
deviation is never silent.

## Q4. Are event and random sampling combined correctly?

**Yes.** Tests assert: ≥3 semi-random and ≤2 event-enriched on every fixture;
event prompts only exist when the detector found a real eligible event
(`no_eligible_event_day` produces 5×`semi_random` and the auditor flags any
event trigger on it as `event_without_detected_event`); `post_trip` prompts
land after the trip end (and no later than the 45-min horizon); priority
`post_trip > post_active_episode` is observable when both exist; and a day
with no eligible events never gets a fabricated category
(`test_no_forced_artificial_event_diversity`).

## Q5. Are inherited facts immutable?

**Yes, enforced three ways.**
1. Structurally: the context packet and day model are frozen dataclasses;
   tampering in place raises `FrozenInstanceError` (the tamper test relies on
   that).
2. Forensically: the validator re-derives every inherited field from the
   supplied day and compares (`inherited_context_altered` — detection proven
   by `test_inherited_facts_are_detected_as_tampered`).
3. Cryptographically: the day's `context_fingerprint` is stored in provenance
   at generation time; the validator recomputes it, and the pipeline aborts
   with `InheritedContextMutationError` if the day changed mid-run.

## Q6. Are subjective variables clearly synthetic?

**Yes.** Every `EMAResponse.subjective` is declared in the model docstring and
in `scales.synthetic_declaration` (emitted in every bundle): "synthetic
simulation outputs … not observed human measurements". The 5-point anchors
are documented in `vocab.SCALE_LABELS` and in the bundle's `scales` block;
per-draw rule traces are stored in provenance; and the demographic-leak scan
(validator family 10) fails any bundle that exposes a forbidden persona field.

## Q7. Can DeepSeek invent unsupported facts?

**In shipped output, no.** The renderer validates *every* candidate note
against the closed-world contract (`notes.validate_note`) before it is stored;
rejections are retried (≤`note.max_retries`) with the failure reasons fed back;
then the offline template fallback (closed-world by construction) is validated
the same way; only then does the note become `null`. The stored note is
re-validated by the bundle validator, so an unsafe note cannot ship.
Category-coded rejections are covered by tests: unsupported person / place /
activity / event / delay / weather / cause / journey, medical claims,
psychological-trait claims, proper nouns, length/sentence limits, unparseable
output, and transport-failure handling.

**Status caveat (reported, per the stop conditions):** real end-to-end
DeepSeek calls could not be executed in this sandbox — no `DEEPSEEK_API_KEY`
is present and outbound TLS to `api.deepseek.com` is blocked at the egress
layer (TCP connects, the TLS handshake is reset; `github.com`/`pypi.org`
work). The integration tests
(`tests/test_deepseek_integration.py`) therefore report explicit SKIPs, and
the *client transport itself* is exercised offline against a local HTTP stub
server (`tests/test_llm_transport_offline.py`: request shape, Bearer auth,
JSON extraction around reasoning text, retry feedback, null fallback,
transport-failure fallback). As soon as a credential and a route are
available, the same tests activate automatically (`llm_available()` probe)
without code changes. The offline deterministic renderer means the module is
fully functional and testable regardless.

## Q8. Is every output traceable?

**Yes.** Five origin classes cover every emitted field
(`provenance.FIELD_PROVENANCE`; unclassified fields fail validation). Run
provenance carries protocol/schema/scheduler/state-generator/auditor/
note-validator versions, LLM provider/model/template/decoding, seed,
`request_hash`, `context_fingerprint`, `config_hash`, participant/date,
`generated_at` (deterministic anchor). Per-record provenance carries prompt
type, prompt/response times, episode/interval/journey ids, retry counts,
validation state, the complete context packet (fingerprinted) and the
rule-level subjective-state trace. `examples/example_output.json` shows the
full structure; `test_provenance_is_complete` asserts all of it.

## Q9. Can the same seed reproduce the structured EMA output?

**Yes.** `test_canonical_json_is_stable` asserts two runs with the same seed
produce **byte-identical** bundles (canonical JSON equality — prompts,
responses, latencies, subjective states, notes, provenance). All randomness is
derived from `stable_seed(participant, date, seed)` (SHA-256-based, no Python
`hash`), and `generated_at` is a deterministic run anchor, not wall-clock
time. `test_scheduler_deterministic_across_seeds_and_runs` and the
state-generator reproducibility tests cover the individual stages.

## Q10. What remains uncertain scientifically?

Declared honestly (see also `SCIENTIFIC_ASSUMPTIONS.md` §7):

1. **Calibration vs. reality.** 85–90% is a simulation target inside the
   observed 67–92% band; real compliance depends on device, population and
   trigger type, and event-triggered compliance can be far lower
   (WEALTH median 34% per the corpus). The canonical profile simulates events
   only slightly harder to answer; the `literature_divergent` profile is a
   one-line config change for sensitivity analysis.
2. **Item set.** Three items (valence/energy/stress) vs. the synthesis's
   preferred two-item battery — justified for Paper 3's RQ, but it remains a
   declared divergence (S-14).
3. **State-generator magnitudes.** All rule magnitudes are bounded design
   choices (class B/C), not fitted to real EMA dynamics; the *signs* follow
   the corpus where it is decisive (post-exertion fatigue, schedule pressure,
   social company, demarcation effects), but the sizes should be revisited if
   Paper 3 ever anchors to empirical affect distributions.
4. **Window concept.** The eight-windows 08:00–23:00 stratification is
   host-supplied with a documented default; the corpus's concrete instances
   are 2-hour windows (08:00–20:00 / after-school intervals).
5. **LLM behaviour untested against the live service.** The closed-world
   pipeline is proven against scripted adversarial outputs and a local HTTP
   stub, but real DeepSeek output diversity (refusals, formatting drift,
   multilingual leakage) remains to be observed once credentials/route are
   available. Mitigation is architectural: no unsafe note can ship regardless
   of model behaviour.
6. **Prompt reactivity** (Maher 2018: small post-prompt PA reduction) is not
   modelled: the EMA module must not mutate the world. Flagged for the
   host-system level.
7. **Demarcation** is handled at prompt placement (stability margins) but not
   as an analytic weight; analysts may wish to down-weight prompts close to
   transitions — the packet exposes `minutes_since_activity_change` for that.

## Stop-condition report

Per the task's stop conditions, the following were checked and **reported**
rather than improvised:

1. *Evidence vs. requested design conflict* — two material divergences found
   and declared (item set S-14; event-triggered compliance S-32/S-33), both
   resolved in favour of the brief with documentation. No unresolved conflict.
2. *Historical capability not represented* — the historical
   `recall_window`/`demarcation_episodes` fields and device-wear schedule were
   absorbed in reduced, documented form (packet fields + optional wear);
   historical reactivity simulation and LLM diary repair were rejected as out
   of scope for an annotation layer. Reported in `PHASE0_ARCHAEOLOGY.md` §5.
3. *DeepSeek cannot be reached* — **true in this sandbox** (no credential +
   egress block). Not improvised around: the client, validator, retry and
   fallback paths are fully implemented and tested offline; integration tests
   auto-activate when the environment changes. This is the only partial stop
   condition; the module's functionality does not depend on it.
4. *State generator not transparent enough* — false: every draw carries a
   named, magnitude-traced rule log (stored in provenance); transparency is
   asserted by tests.
5. *Deterministic stereotypes / incoherent states* — false: the stereotype
   test (fixed context × 30 seeds) and the context-sensitivity test (40-seed
   latent means) both pass; the domain cap (±0.30) structurally prevents
   single-context dominance.
