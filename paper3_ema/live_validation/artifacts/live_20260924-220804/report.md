# Live DeepSeek validation — standalone Paper 3 EMA module

**Verdict: CONDITIONAL PASS**

## 1. Environment / model identity

- python 3.11.15 on Windows-10-10.0.26200-SP0
- harness v1.0.0 (test-only, untracked; production code unmodified except any documented follow-up fix)
- provider endpoint: `https://api.deepseek.com` (default config base URL)
- model: **deepseek-flash** (thinking=enabled, reasoning_effort=high, max_tokens override=4096)
- credential: `DEEPSEEK_API_KEY` present via environment only (`yes`); never written to any artefact

## 2. Test date

- 2026-09-24T22:08:04+00:00 (UTC) / 2026-09-24T22:08:04+00:00 (Europe/Copenhagen)

## 3. Exact commit tested

- `` () on branch ``; working tree dirty: False

## 4. Connectivity

- reachable: **True** (HTTP 401)
- diagnostics: {"dns": "ok -> 3.173.21.63", "tcp": "ok", "tls": "ok (TLSv1.3)"}

## 5. Full test-suite result

- full suite: **134 passed, 5 skipped in 67.56s (0:01:07)**
- integration tests: {'test_real_llm_end_to_end_bundle': None, 'test_real_llm_retries_are_bounded': None, 'test_real_llm_never_alters_inherited_context': None, 'test_real_llm_subjective_values_are_not_model_chosen': None}
- raw outputs: `02_suite_full.txt`, `02_integration_verbose.txt`

## 6. Controlled live-note cases (phase 2)

| case | trigger | attempts | retries | final source | final note |
|---|---|---:|---:|---|---|
| semi_random_home | semi_random | 2 | 1 | llm | I am sitting at home in the afternoon, with the free time… |
| work_study | post_trip | 2 | 1 | llm | Sitting at work in the early morning, I feel neutral, wit… |
| childcare | semi_random | 2 | 1 | llm | It is midday, I am at home walking with the children duri… |
| social | semi_random | 3 | 2 | offline_template | In a good mood right now after the bus trip, at home. |
| post_walk | post_trip | 3 | 2 | llm | Sitting at home in the evening with my partner before a m… |
| post_run_exercise | post_active_episode | 3 | 2 | llm | Standing at the gym in the early morning after the run, I… |
| post_cycle | post_trip | 1 | 0 | llm | Sitting at work with colleagues this early morning after … |
| post_public_transport | post_trip | 3 | 2 | llm | After the train trip and the walk, sitting at work in the… |
| post_car | post_trip | 2 | 1 | llm | My stress feels high while standing after the drive this … |
| documented_delayed_journey | post_trip | 3 | 2 | llm | Sitting at work in the early morning after the train trip… |
| journey_without_documented_delay | post_trip | 3 | 2 | offline_template | Feeling pressured right now after the bus trip. |
| context_transition | context_transition | 3 | 2 | offline_template | Feeling fairly neutral right now while standing, at home. |
| evening | semi_random | 3 | 2 | None | null |
| no_eligible_event_day | semi_random | 1 | 0 | llm | I am sitting at home in the morning, with the free time, … |
| sparse_ambiguous | post_trip | 3 | 2 | offline_template | Feeling pressured right now after the bus trip, at work. |

- cases found: 15/15

## 7. Adversarial closed-world results

Temptation coverage per case is recorded in `04_cases.json` (`temptations`). The required result is not that the model never *attempts* unsupported facts; it is that **zero unsupported facts survive into an accepted record**.

- surviving unsupported facts (phase 2): **0**
- surviving unsupported facts (phase 4 cohort): **0**
- rejection counts by code (cohort): {'medical_condition': 14, 'multiple_sentences': 4, 'unparseable_output': 9, 'unsupported_delay': 31, 'unsupported_event': 1, 'unsupported_reference': 188}

## 8. Live/offline invariance (phase 3)

- total diffs: 278; unallowed diffs: **0**
- allowed-diff markers (note + LLM provenance only): `.context_note`, `.note_source`, `.note_validation`, `.note_result`, `provenance.llm_provider`, `provenance.llm_model`, `provenance.llm_decoding`, `provenance.llm_calls`, `provenance.llm_retries`, `summary.notes_rendered`, `summary.notes_null`, `summary.note_sources`, `.llm_model`, `.llm_provider`, `.llm_decoding`, `.llm_calls`, `.llm_retries`, `.note_attempts`, `.note_fallback_reason`, `.note_rejected_codes`, `.retry_count`, `provenance.llm_template_version`

## 9. 4x7 live cohort summary (phase 4)

- participant-days: **28** (4 x 7)
- opportunities: **140** · answered **125** · missed **11** · expired **4**
- prompt types: {'context_transition': 9, 'post_active_episode': 7, 'post_trip': 35, 'semi_random': 89}
- DeepSeek calls attempted: **297** · succeeded **297** · failed **0**
- first-attempt parse ok/fail: **127 / 2** · first-attempt closed-world accept: **19** · model-null first attempt: 0
- retry distribution: {'0': 19, '1': 52, '2': 58}
- rejections by code: {'medical_condition': 14, 'multiple_sentences': 4, 'unparseable_output': 9, 'unsupported_delay': 31, 'unsupported_event': 1, 'unsupported_reference': 188}
- offline fallback: **25** · null notes (answered): 16 · final non-null notes (answered): 109
- API latency ms: mean 6740.7 · median 5640.0 · p95 15750.0 · max 19172.0
- token usage: {'prompt_tokens': 224972, 'completion_tokens': 418241, 'cached_tokens': 165627, 'reasoning_tokens': 408380}
- estimated API cost (from returned usage x published rates): peak $0.520686 / off-peak $0.260343 — DeepSeek official pricing table, synced 2026-09-10..2026-09-23
- bundle validation: all valid = **True** (issue codes: {'response_rate_outside_calibration': 28})
- unsupported factual inventions that survived validation: **0** (required: 0)

## 10. Representative final EMA records

prompt time → trigger → inherited context → V/E/S → final note → validation status

1. `2026-05-04 11:12` → **semi_random**, after bus (delay documented) → sitting / workplace / with_colleagues / work → 3/2/4 → “Feeling pressured right now after the bus trip, at work.” [offline_template] → bundle PASS
2. `2026-05-04 16:35` → **post_trip**, after bus → walking / shop / alone / shopping → 3/3/3 → “After the bus trip, I am on the walk at the shop this afternoon, with light rain and the quiet.” [llm] → bundle PASS
3. `2026-05-04 17:17` → **post_active_episode**, after bike → standing / home / alone / self_care → 4/2/4 → “This evening, standing at home alone after my run and bike ride, I feel positive but low on energy and stressed.” [llm] → bundle PASS
4. `2026-05-04 09:55` → **context_transition** → standing / home / with_children / household → 5/2/3 → “While standing at home in the morning, I am very positive and low on energy.” [llm] → bundle PASS
5. `2026-05-04 11:55` → **semi_random**, after bike → sitting / workplace / alone / work → 4/3/4 → “I am sitting alone at work in the quiet morning after my walk and bike ride in light rain.” [llm] → bundle PASS
6. `2026-05-04 08:48` → **post_trip**, after train → sitting / workplace / with_colleagues / work → 1/2/4 → “Sitting at work with colleagues in the early morning, I feel very negative, low on energy, and high in stress.” [llm] → bundle PASS
7. `2026-05-04 20:40` → **semi_random**, after bus → sitting / home / alone / leisure → 1/2/4 → “Feeling stressed right now while sitting.” [offline_template] → bundle PASS
8. `2026-05-07 10:59` → **semi_random**, after bus (delay documented) → sitting / workplace / with_friends / work → 4/3/4 → “Feeling pressured, energy is steady.” [offline_template] → bundle PASS

## 11. Fallbacks / retries / rejections (complete)

- phase 2 per-case attempts, retries, raw outputs and rejection codes: `04_cases.json`
- cohort retry distribution: {'0': 19, '1': 52, '2': 58}
- cohort rejection counts by code: {'medical_condition': 14, 'multiple_sentences': 4, 'unparseable_output': 9, 'unsupported_delay': 31, 'unsupported_event': 1, 'unsupported_reference': 188}
- offline fallbacks: 25 (offline template renderer is part of the by-design pipeline, not an error)
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
- offline-template fallback rate high: 25/129

**Final verdict: CONDITIONAL PASS**
