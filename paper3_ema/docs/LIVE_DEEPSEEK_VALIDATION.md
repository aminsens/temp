# Live DeepSeek validation — standalone Paper 3 EMA module

**Verdict: CONDITIONAL PASS**

## 1. Environment / model identity

- python 3.11.15 on Windows-10-10.0.26200-SP0
- harness v1.0.0 (test-only, untracked; production code unmodified except any documented follow-up fix)
- provider endpoint: `https://api.deepseek.com` (default config base URL)
- model: **deepseek-flash** (thinking=enabled, reasoning_effort=high, max_tokens override=1024)
- credential: `DEEPSEEK_API_KEY` present via environment only (`yes`); never written to any artefact

## 2. Test date

- 2026-09-24T19:25:04+00:00 (UTC) / 2026-09-24T19:25:04+00:00 (Europe/Copenhagen)

## 3. Exact commit tested

- `` () on branch ``; working tree dirty: False

## 4. Connectivity

- reachable: **True** (HTTP 401)
- diagnostics: {"dns": "ok -> 3.173.21.63", "tcp": "ok", "tls": "ok (TLSv1.3)"}

## 5. Full test-suite result

- full suite: **134 passed, 5 skipped in 67.42s (0:01:07)**
- integration tests: {'test_real_llm_end_to_end_bundle': None, 'test_real_llm_retries_are_bounded': None, 'test_real_llm_never_alters_inherited_context': None, 'test_real_llm_subjective_values_are_not_model_chosen': None}
- raw outputs: `02_suite_full.txt`, `02_integration_verbose.txt`

## 6. Controlled live-note cases (phase 2)

| case | trigger | attempts | retries | final source | final note |
|---|---|---:|---:|---|---|
| semi_random_home | semi_random | 3 | 2 | offline_template | Feeling stressed right now while sitting. |
| work_study | post_trip | 2 | 1 | llm | Sitting at work with colleagues this early morning, I fee… |
| childcare | semi_random | 3 | 2 | offline_template | In a good mood after the walk. |
| social | semi_random | 3 | 2 | offline_template | In a good mood right now after the bus trip, at home. |
| post_walk | post_trip | 2 | 1 | llm | Sitting at home this evening for a meal, I feel very posi… |
| post_run_exercise | post_active_episode | 2 | 1 | llm | After my run, standing at the gym with strangers, my ener… |
| post_cycle | post_trip | 1 | 0 | llm | Sitting at work in the early morning after my bike ride, … |
| post_public_transport | post_trip | 3 | 2 | offline_template | Feeling stressed, feeling drained. |
| post_car | post_trip | 3 | 2 | None | null |
| documented_delayed_journey | post_trip | 2 | 1 | llm | Sitting at work with colleagues this early morning, after… |
| journey_without_documented_delay | post_trip | 2 | 1 | llm | Sitting at work with colleagues this early morning, I fee… |
| context_transition | context_transition | 3 | 2 | offline_template | Feeling fairly neutral right now while standing, at home. |
| evening | semi_random | 3 | 2 | None | null |
| no_eligible_event_day | semi_random | 2 | 1 | llm | I am sitting at home in the quiet morning, with free time… |
| sparse_ambiguous | post_trip | 3 | 2 | offline_template | Feeling pressured right now after the bus trip, at work. |

- cases found: 15/15

## 7. Adversarial closed-world results

Temptation coverage per case is recorded in `04_cases.json` (`temptations`). The required result is not that the model never *attempts* unsupported facts; it is that **zero unsupported facts survive into an accepted record**.

- surviving unsupported facts (phase 2): **0**
- surviving unsupported facts (phase 4 cohort): **0**
- rejection counts by code (cohort): {'medical_condition': 11, 'multiple_sentences': 2, 'unparseable_output': 149, 'unsupported_delay': 32, 'unsupported_event': 3, 'unsupported_place': 2, 'unsupported_reference': 147}

## 8. Live/offline invariance (phase 3)

- total diffs: 255; unallowed diffs: **0**
- allowed-diff markers (note + LLM provenance only): `.context_note`, `.note_source`, `.note_validation`, `.note_result`, `.llm_provider`, `.llm_model`, `.llm_decoding`, `.llm_calls`, `.llm_retries`, `.note_attempts`, `.note_fallback_reason`, `.note_rejected_codes`, `.retry_count`, `provenance.llm_template_version`, `summary.notes_rendered`, `summary.notes_null`, `summary.note_sources`
- **Allow-list regression fix (post-run, Arena sandbox):** the committed `live_harness.py` was found to carry a narrower marker set (bundle-level `provenance.llm_*` only), which — as verified by re-running the classification against this run's `05_invariance.json` — would have flagged the 139 per-record LLM-provenance diffs (`record_provenance.<prompt_id>.{llm_model, llm_provider, note_attempts, note_fallback_reason, note_rejected_codes, retry_count}`) as unallowed on any re-run. The marker list above is the one that produced the 255/0 result; it is now restored in `live_harness.py` and pinned by a regression test (`live_validation/test_harness_offline.py::test_invariance_allowlist_covers_per_record_llm_provenance`).

## 9. 4x7 live cohort summary (phase 4)

- participant-days: **28** (4 x 7)
- opportunities: **140** · answered **125** · missed **11** · expired **4**
- prompt types: {'context_transition': 9, 'post_active_episode': 7, 'post_trip': 35, 'semi_random': 89}
- DeepSeek calls attempted: **339** · succeeded **339** · failed **0**
- first-attempt parse ok/fail: **73 / 56** · first-attempt closed-world accept: **16** · model-null first attempt: 0
- retry distribution: {'0': 16, '1': 16, '2': 97}
- rejections by code: {'medical_condition': 11, 'multiple_sentences': 2, 'unparseable_output': 149, 'unsupported_delay': 32, 'unsupported_event': 3, 'unsupported_place': 2, 'unsupported_reference': 147}
- offline fallback: **52** · null notes (answered): 34 · final non-null notes (answered): **91** = 40 LLM + 51 offline
- note: two **expired** prompts also carry context notes (1 LLM + 1 offline), so total non-null = 93 and total LLM-final = 41. The dashboard KPI card reports the answered-only scope (40 LLM of 91 non-null) derived from the embedded records; do not derive it as `final_non_null − offline_fallback` (91 − 52 = 39 mixes scopes: the 52 offline renderings include one expired prompt not in the 91).
- API latency ms: mean 4231.0 · median 4735.0 · p95 5656.0 · max 5969.0
- token usage: {'prompt_tokens': 254871, 'completion_tokens': 270199, 'cached_tokens': 185320, 'reasoning_tokens': 263453}
- estimated API cost (from returned usage x published rates): peak $0.346216 / off-peak $0.173108 — DeepSeek official pricing table, synced 2026-09-10..2026-09-23
- bundle validation: all valid = **True** (issue codes: {'response_rate_outside_calibration': 28})
- unsupported factual inventions that survived validation: **0** (required: 0)

## 10. Representative final EMA records

prompt time → trigger → inherited context → V/E/S → final note → validation status

1. `2026-05-04 11:12` → **semi_random**, after bus (delay documented) → sitting / workplace / with_colleagues / work → 3/2/4 → “Sitting at work this morning, I feel neutral and low in energy.” [llm] → bundle PASS
2. `2026-05-04 16:35` → **post_trip**, after bus → walking / shop / alone / shopping → 3/3/3 → “Feeling fairly neutral after the bus trip.” [offline_template] → bundle PASS
3. `2026-05-04 17:17` → **post_active_episode**, after bike → standing / home / alone / self_care → 4/2/4 → “Standing at home this evening after the run and bike ride, I feel positive but low on energy and high on stress.” [llm] → bundle PASS
4. `2026-05-04 09:55` → **context_transition** → standing / home / with_children / household → 5/2/3 → “In a good mood, energy is low.” [offline_template] → bundle PASS
5. `2026-05-04 11:55` → **semi_random**, after bike → sitting / workplace / alone / work → 4/3/4 → “Sitting alone at work this morning, I feel positive but the stress is high.” [llm] → bundle PASS
6. `2026-05-04 08:48` → **post_trip**, after train → sitting / workplace / with_colleagues / work → 1/2/4 → “Feeling pressured, energy is low.” [offline_template] → bundle PASS
7. `2026-05-04 20:40` → **semi_random**, after bus → sitting / home / alone / leisure → 1/2/4 → “Feeling stressed right now while sitting.” [offline_template] → bundle PASS
8. `2026-05-05 16:35` → **post_trip**, after bus (delay documented) → walking / shop / alone / shopping → 3/3/3 → “Feeling okay right now after the bus trip, at the shop.” [offline_template] → bundle PASS

## 11. Fallbacks / retries / rejections (complete)

- phase 2 per-case attempts, retries, raw outputs and rejection codes: `04_cases.json`
- cohort retry distribution: {'0': 16, '1': 16, '2': 97}
- cohort rejection counts by code: {'medical_condition': 11, 'multiple_sentences': 2, 'unparseable_output': 149, 'unsupported_delay': 32, 'unsupported_event': 3, 'unsupported_place': 2, 'unsupported_reference': 147}
- offline fallbacks: 52 (offline template renderer is part of the by-design pipeline, not an error)
- failed API calls: 0

## 12. Remaining limitations

- cost: peak vs off-peak window is defined by DeepSeek (UTC schedule); both are reported
- cost: cached_input tokens are billed at the cache-hit rate (subset of prompt_tokens)
- cost: completion_tokens includes reasoning tokens where the provider reports them
- the cohort is synthetic (fixture-based), as specified for this demonstration; it is independent of Appa and of the historical September cohort
- DeepSeek prose is not byte-reproducible across separate API calls (no determinism guarantee was requested or assumed; see phase 5)
- the harness client wrapper (timing/usage capture, thinking fields) is test-only; the production client and all scientific parameters are unmodified in this run

## 13. Gates and verdict

- [x] endpoint_reachable
- [x] suite_non_integration_pass
- [x] suite_integration_gate
- [x] flash_smoke_all_checks
- [x] cases_all_found
- [x] cases_zero_survivors
- [x] invariance_holds
- [x] cohort_all_bundles_valid
- [x] cohort_zero_survivors
- [x] cohort_opportunities
- [x] repeatability_offline
- [x] repeatability_confined

Caveats:
- offline-template fallback rate high: 52/129

**Final verdict: CONDITIONAL PASS**

---

## Appendix A — Post-run verification (performed in the Arena sandbox, 2026-09-24)

The artefact set for this run was executed on a Windows 10 machine (Python
3.11.15) from an unzipped copy of the repository, committed by the user as
`b450224` on `main` (`LIVE_DEEPSEEK_VALIDATION_artifacts_2026-09-24/`).
All artefacts were then independently re-inspected in the sandbox:

- **All 12 gates re-confirmed** against the raw artefacts (connectivity,
  suite, smoke, cases, invariance, cohort, repeatability).
- **Zero surviving unsupported facts** re-confirmed for phase 2 (15/15 cases)
  and phase 4 (129 rendered notes, incl. every stored non-null note).
- **Invariance** re-confirmed: 255 structural diffs, 0 outside the note /
  LLM-provenance allow-list.  **Repeatability** re-confirmed: offline
  byte-identical under the same seed; live nondeterminism confined to notes.
- **Suite cross-check:** `134 passed, 5 skipped` on the run machine vs
  `132 passed, 7 skipped` in the sandbox — exactly the 4 integration tests
  now executing live (all 4 PASSED against the real API, 33.07 s) minus the
  2 legacy-import skips that were *false* (see below).
- **Artefact hygiene:** no credential material in any artefact file
  (secret-sweep clean; the API key appears nowhere).

### Notes on this specific run

1. **Identity commit field is empty.** The run was performed from an unzipped
   copy (no `.git`), so `00_identity.json` has no commit hash.  The executed
   code is identical to the harness/module commits the zip was built from
   (module `0f36951`, harness `2066d7a` in the sandbox branch, built before
   the follow-up fix below).
2. **5 skips = 3 deterministic + 2 false.** The 3 `test_notes` skips are
   documented context-conditional skips.  The 2 `test_legacy_import` skips
   were caused by a hard-coded sandbox path
   (`/home/user/temp/EMA-Diary-Generation/output`) — a test-only portability
   defect revealed by this run.  Fixed in commit `7070fbe` (checkout-relative
   path + regression test).  With the fix, the suite on any full checkout is
   expected to read `136 passed, 3 skipped`.
3. **`deepseek-chat` is still served.** All four committed integration tests
   (model per config, `deepseek-chat`) passed live — the bundled config
   default model is *not* a defect; earlier third-party "retired alias"
   listings were contradicted by the live API.
4. **Token-budget observation (no safety impact).** First-attempt parse
   failures were 56/129 and 97/129 notes hit the 2-retry cap; average
   completion usage was ≈797 tokens/call of which ≈777 were *reasoning*
   tokens against the 1024-token completion budget, i.e. the visible content
   was often truncated mid-JSON (`unparseable_output` ×149,
   `unsupported_reference` ×147).  The closed-world chain (retry → offline
   template → null) contained every case — **zero survivors** — so this is a
   quality/efficiency observation, not a safety finding.  A re-run with
   `DEEPSEEK_MAX_TOKENS=4096` (harness env var) is recommended if higher
   first-attempt LLM acceptance is desired.
5. **`response_rate_outside_calibration` ×28** in bundle issue codes are
   per-day INFO flags (day-level rate over 5 prompts is inherently coarse);
   the cohort-level calibration band is met: 125/140 = 89.3% (target 85–90%).
