# Phase 0 — Repository Archaeology Report

**Task:** Paper 3 standalone EMA module (no DayForge, no Appa).
**Date of inspection:** 2026-09-24
**Repository:** `aminsens/temp` @ branch `arena/01a0d410-temp` (base commit `1241faa`)
**Inspector note:** every claim below was verified by reading the file cited. Line numbers refer to
the state of the repository at the base commit.

---

## 0. What is actually in the repository

| Path | Kind | Size | Role for Paper 3 |
|---|---|---|---|
| `EMA_Definitive_Synthesis.md` | Evidence synthesis (532 lines) | 46 KB | **Current scientific design brief source** (cross-source synthesis of 7 deep-research runs, April 2026) |
| `EMA_Accelerometer_Synthesis_v1.md` | Earlier synthesis (439 lines) | 36 KB | Predecessor of the definitive synthesis; used only to check that the definitive version did not silently drop findings |
| `CONCLUSION.md` | Synthesis-of-syntheses (402 lines) | 21 KB | Agreement / disagreement / overrated / underrated register; contains the only explicit "Paper 3" reference (line 393) |
| `Chatgpt.md`, `Chatgpt_deep_research.md`, `Deepseek.md`, `Gemini.md`, `Kimi.md`, `Scite_Opus4.6.md`, `Scite_Opus4.6_v2.md` | 7 primary research reports | 23–67 KB each | Underlying evidence base; consulted to verify individual design decisions (see §3) |
| `EMA-Diary-Generation/` | Historical snapshot (current) | 12 dirs | Prior DSPy-based diary + EMA pipeline (Trondheim, "Jar of Life") |
| `EMA-Diary-Generation-BACKUP-20260409/` | Historical snapshot (backup) | 10 dirs | Earlier state of the same pipeline |
| `EMA-Diary-Generation/output/*.json` | Historical generated outputs | 2–133 KB | Evidence of what the historical EMA generator actually produced |
| `EMA-Diary-Generation/{TEST_RESULTS.md,FINAL_STATUS.md,README.md}` | Historical test/status reports | — | Evidence of historical acceptance criteria (which encode the artificial reporting-rate assumptions) |

There is **no** Appa code, **no** DayForge code, and **no** `EMARequest` / `EMABundle` /
`paper3_ema_v1.yaml` anywhere in the repository. A full-text search for
`EMARequest|EMABundle|EMAContextPacket|audit_schedule|paper3|waking window|stratified` returns
hits only in the research reports (Deepseek.md lines 281/462 on stratification across waking hours)
and in the historical `EMASchedule`/`EMAConfig` dataclasses. Consequence: the "approximately eight
waking/daytime windows spanning roughly 08:00–23:00" concept referenced by the design brief is
**not present in this repository** — it belongs to the (unavailable) host system. It is therefore
implemented here as a *configurable, host-supplied* stratification with a documented default, and
never as a hard-coded assumption about Appa.

---

## 1. Verification of the "known historical findings"

The design brief lists nine suspected behaviours of the historical EMA generator. Each was checked
against `EMA-Diary-Generation/modules/ema_generator.py` (201 lines),
`EMA-Diary-Generation/modules/refined_diary_gen.py`, `EMA-Diary-Generation/configs/pipeline_config.py`,
`EMA-Diary-Generation/evaluation/qa_validator.py`, `EMA-Diary-Generation/evaluation/diary_eval.py`,
`EMA-Diary-Generation/optimizers/coherence_optimizers.py` and the generated outputs.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | defaults to ≈6 probes | **CONFIRMED** | `generate_ema_probes(diary, num_probes: int = 6, seed=42)` (`ema_generator.py:16`); `EMAConfig.prompts_per_day = 6` (`pipeline_config.py`); `EMASchedule.prompts_per_day = 6` (`data/models.py:383`) |
| 2 | selects roughly evenly spaced **waking episodes** | **CONFIRMED** | filters `hetus_code != "011"` (sleep), then `step = len(waking_eps)//num_probes; target_eps = [waking_eps[i*step] …]` (`ema_generator.py:25-31`). Note: spacing is by *episode index*, not by *clock time* — a fragmented day yields clustered prompts |
| 3 | forces certain activity examples into the sample | **CONFIRMED** | "Ensure at least 1 standing episode (for underreporting)" overwrites `target_eps[0]`; "Ensure at least 1 cycling episode" overwrites `target_eps[1]` (`ema_generator.py:33-41`). Also forced in the LLM path: `refined_diary_gen.py:224-226` ("Include at least 1 probe during a standing episode (should be misreported)… Exactly 1 probe should be missed") |
| 4 | simulates exactly one missed response | **CONFIRMED** | `miss_idx = rng.randint(1, len(target_eps)-2)`; that single probe is emitted with `missed: True` (`ema_generator.py:44-45, 88-107`). LLM prompt hard-codes "Exactly 1 of {num_probes} prompts missed" (`refined_diary_gen.py:211-213`) |
| 5 | injects standing under-reporting | **CONFIRMED** | `if gt_activity == "standing": if rng.random() > 0.35: reported_activity = rng.choice(["sitting","walking"])` → 65 % misreport in the current snapshot; the backup uses `> 0.4` → 60 % misreport. `EMAConfig.standing_report_rate = 0.4`, `standing_misreported_as = ["sitting","walking"]` |
| 6 | simplifies / genericises location | **CONFIRMED** | `genericize_location()` maps specific strings to coarse buckets via a 24-entry Trondheim-specific keyword table, default `"other"` (`ema_generator.py:141-176`) |
| 7 | generates reporting noise programmatically | **CONFIRMED** | the whole `reported_*` block (`ema_generator.py:96-125`) is a pure-Python corruption layer over ground truth; a parallel LLM corruption path exists in `refined_diary_gen.generate_refined_ema` |
| 8 | does not produce genuinely context-grounded subjective EMA responses | **CONFIRMED** | the generated probes contain **no subjective variables at all**. `data/models.py:EMAProbe` declares `reported_affect_valence/arousal/fatigue` (lines ~300) but `EMAProbe.to_dict()` never emits them and `ema_generator.py` never sets them. Inspection of `output/test_run_output.json` confirms: 6 probes, keys are `prompt_time, response_time, response_lag_min, gt_*, reported_activity/domain/location/social, activity_matches_gt, missed` — no valence, no energy, no stress, no note |
| 9 | validator encodes artificial expected reporting rates | **CONFIRMED (3 places)** | `qa_validator.validate_ema_probes`: `if report_rate > 0.7: issues.append("standing overreported … (should be ~40%)")` and `if miss_rate < 0.05 …: "miss rate too low"` (lines 187-200); `diary_eval.ema_recall_realism`: `standing_underreported = standing_report_rate < 0.7`, `0.05 <= mismatch_rate <= 0.35`, `0.05 <= miss_rate <= 0.25` (lines 266-320); `coherence_optimizers.compute_ema_quality_reward`: rewards a 5–35 % mismatch rate and the *existence* of missed prompts (lines 102-158) |

Additional historical finding not listed in the brief (relevant to the demographic safeguard):
`data/models.py:Persona.to_prompt_context()` (lines 156-170) dumps **name, age, gender, occupation,
living situation, city, commute mode/duration, fitness level, work schedule, bike/car ownership,
health notes, sleep/wake times, hobbies and personality traits** into a single LLM prompt string.
That is precisely the wholesale persona exposure the Paper 3 brief prohibits for subjective-state
generation. It is used by the *diary* generator (world-building), not by the historical EMA probe
generator (which is persona-blind), so the historical EMA layer has no demographic path to inherit —
but the pattern must not be copied into the new state generator.

---

## 2. Implementation salvage table

Legend — **REUSE**: lift logic with light edits. **ADAPT**: keep the idea, re-implement against the
new contract. **REJECT**: do not carry forward.

| COMPONENT | CURRENT IMPLEMENTATION (`EMA-Diary-Generation/`) | BACKUP IMPLEMENTATION (`…-BACKUP-20260409/`) | SCIENTIFIC BASIS (verified source) | DECISION | REASON |
|---|---|---|---|---|---|
| Controlled vocabularies: activity, domain, location type, social context, valence, arousal, fatigue, device wear, prompt/trigger type, indoor–outdoor | `data/models.py:22-125` — 10 `str, Enum` classes | byte-identical (`diff` empty) | Synthesis §6.1 variable hierarchy; §9.5 "always collect activity, domain, location, social, device wear"; Kimi.md:119 (Energetic/Tired/Happy/Stressed items) | **REUSE (adapt names)** | Vocabularies are the strongest asset in the historical code. Adapted: 5-point ordinal *numeric* scales (1–5) with documented labels instead of string enums for valence/arousal/fatigue; trigger enum reduced to the Paper 3 set (`semi_random, post_trip, post_active_episode, context_transition, discretionary_fallback`); `place_type` replaces `location_type`; **no** HETUS coupling |
| HETUS 2018 taxonomy + `HETUS_TO_OUR_FORMAT` | `data/hetus_taxonomy.py` (295 lines) | identical | Not required by the synthesis for EMA; it is a *diary/world* taxonomy | **REJECT (for the EMA package)** | Paper 3 EMA consumes an already-contextualised day. Re-implementing HETUS mapping would import world-generation responsibility ("do not build a second DayForge"). Activity/domain/place vocabularies are accepted as host-supplied strings validated against our enums |
| `EMAProbe` record shape (dual timestamps, prompt type, recall window, ground-truth vs reported split) | `data/models.py:246-320` | identical | Synthesis §7.3 "dual-timestamp recording — STRONGEST in theory, almost never implemented"; §9.1 "record both prompt delivery and response timestamps" | **ADAPT** | Keep prompt/response/latency and the trigger field. Drop the `gt_* vs reported_*` corruption pair entirely — Paper 3 inherited context is authoritative and is **not** re-reported with noise (§"do not reintroduce historical reporting noise"). Add explicit provenance class per field |
| `EMASchedule` config block (prompts/day, waking window, min gap, response window, lag distribution, missingness rate/bias, recall window) | `data/models.py:381-395`; `configs/pipeline_config.py:EMAConfig` | identical | Synthesis §9.3 (5–6 prompts/day, random-within-window), §9.5 (4–6 prompts/day), Gemini.md:162 (max latency 5–10 min), §7.2 (non-random missingness) | **ADAPT** | Structure is right, values are wrong for Paper 3: 6 → **5** prompts/day; `response_window_sec = 300` → **10 min expiry**; `missingness_rate = 0.15` → **calibrated 85–90 % response**; `mvpa_correlated` bias retained as an explicit, documented modifier; single flat config → **versioned YAML** (`paper3_ema_v1.yaml`) with no policy in code constants |
| Waking-window stratification idea (`waking_start/waking_end`, "random within window") | `EMASchedule.waking_start="07:00"`, `waking_end="23:00"` | identical | Deepseek.md:281,462 ("stratify prompts across waking hours"); Chatgpt_deep_research.md:53,56 (random within six 2-hr windows 08:00–20:00; random within 2-hr intervals) | **ADAPT** | Historical code has only a single start/end pair, no stratification. Paper 3 needs ≈8 host-supplied daytime windows (default 08:00–23:00 → eight 112.5-min strata, configurable) with ≥3 background prompts spread across strata |
| Prompt-time selection = index-spaced episodes | `ema_generator.py:24-31` | identical | Contradicts Synthesis §7.3 (random-within-window) and §9.3 | **REJECT** | Deterministic even-spacing is neither random nor stratified; it clusters on fragmented days and cannot express event enrichment |
| Forced standing / cycling probe insertion | `ema_generator.py:33-41`; LLM prompt `refined_diary_gen.py:224-226` | identical | No support anywhere in the corpus; directly contradicts "do not force artificial event categories merely to satisfy diversity" | **REJECT** | This is sampling contamination for the benefit of a validator, not science |
| Exactly-one-missed-probe rule | `ema_generator.py:44-45`; `refined_diary_gen.py:211-213`; `FINAL_STATUS.md` ("1 missed") | identical | Synthesis §7.2 (missingness is stochastic and non-random); §13.1 (compliance 70–92 %) | **REJECT** | Replaced by a configurable stochastic response model with per-trigger base rates and documented modifiers, calibrated to ≈85–90 % overall |
| Standing under-reporting (60–65 % misreport) | `ema_generator.py:100-107`; `EMAConfig.standing_report_rate=0.4` | 60 % variant (`> 0.4`) | Real literature finding (WEALTH 32 % agreement for standing — Synthesis §5.3) **but** it is a finding about *human self-report error*, not a property a synthetic annotation layer should inject | **REJECT for Paper 3** | The brief explicitly forbids re-introducing reporting noise on inherited facts. The finding is instead *recorded* in the assumptions register as a downstream analytic caveat (labels produced here are noise-free inherited context; real-world standing agreement would be worse) |
| `genericize_location()` (24-key Trondheim keyword table) | `ema_generator.py:141-176` | identical | Synthesis §9.5 wants *location type* collected; nothing supports destroying specific place information | **REJECT (as corruption); ADAPT (as privacy rule)** | Place **type** is now an inherited fact supplied by the host day. The context packet deliberately carries place *type* and not proper names — same privacy outcome, no information destruction, no city-specific table |
| Sedentary simplification flag | `EMAConfig.sedentary_simplification=True`; `refined_diary_gen.py:196-199` | identical | none for a synthetic annotation layer | **REJECT** | Same reasoning as standing under-reporting |
| Device-wear handling (read a wear schedule, evaluate at prompt time) | `ema_generator.py:117-124`; `data/models.py:DeviceWearStatus`; `qa_validator.validate_device_wear` | identical | Synthesis §6.2 / §10.2 UNDERRATED #1 ("device wear compliance … shockingly undercollected … always collect") | **ADAPT** | Keep the *lookup* pattern (`status_at(t)`) and keep the field **optional**: never fabricate wear/non-wear when the host day supplies none. Historical code silently defaults `is_wearing = True`, which fabricates a fact — that default becomes `None` ("not supplied") |
| Response-lag model (right-skewed, longer during exercise) | `ema_generator.py:78-84` (`uniform(4,8)` if running/cycling else `uniform(0.5,4)`) | identical | Chatgpt_deep_research.md:156 (mean ≈5 min lag); Gemini.md:108,182 (each extra minute of lag −20 % odds of confirming behaviour); Synthesis §7.2, §10.2 UNDERRATED #3 | **ADAPT** | Keep "right-skewed, longer when the prompt lands near/after exertion". Replace uniform draws with a lognormal, add explicit **10-min expiry** with `expired` status (Gemini.md:162 supports a hard 5–10 min bound), keep both timestamps, always interpret context at **prompt time** |
| Missingness bias ("miss more during activity") | `EMAConfig.missingness_bias="mvpa_correlated"` (declared, **not implemented** in `ema_generator.py`) | identical | Synthesis §7.2 / Opus v2:210 / Gemini.md:118 (responses less likely during vigorous activity, driving, intense social situations) | **ADAPT (implement)** | The historical code declared the bias and never used it. Implemented as documented modifiers on the response probability |
| Prompt exclusion during sleep | implicit (`hetus_code != "011"` filter) | identical | Gemini.md:158 (delay delivery during high-intensity exercise, cycling, driving for safety and to prevent non-response) | **ADAPT + extend** | Extended to the full Paper 3 exclusion set: asleep, driving, cycling, running/vigorous exercise, inside a non-realised movement, inside an unresolved interval, inside an unstable micro-transition — plus the "prompt **after** the event at the first stable opportunity" rule |
| Event-triggered / hybrid sampling | **absent** (`EMAConfig.prompt_type="random_signal"`; `EMAPromptType.HYBRID_*` enum values exist but are never produced) | absent | Synthesis §7.3 + §9.1 + §9.4 + §10.2 UNDERRATED #5 (hybrid designs "almost never implemented … significant methodological opportunity"); Opus v2:293; Chatgpt_deep_research.md:210 | **BUILD NEW** | Nothing to salvage. This is the core Paper 3 contribution: 5 opportunities/day = ≥3 semi-random + ≤2 event-enriched with priority `post_trip > post_active_episode > meaningful_context_transition > discretionary fallback` |
| Schedule auditor | **absent** (validators judge *diaries*, and `validate_ema_probes` judges *realism of corruption*, never schedule legality) | absent | Synthesis §9.5 ("report prompt schedule, compliance by day, latency distribution, missingness pattern, exact linkage rule") | **BUILD NEW** | `audit_schedule()` returning `VALID / NEEDS_REPAIR` with reasons, read-only by construction |
| Provenance / versioning | **absent** (no seed, model, template or version metadata in any output; `output/test_run_output.json` has only `persona, diary, ema_probes, validation`) | absent | Synthesis §8 "weak temporal alignment reporting … reproduction essentially impossible"; §9.5 reporting requirements | **BUILD NEW** | Field-level origin classes (`inherited_context, derived_context, synthetic_protocol, synthetic_subjective, llm_rendered`) + version/hash/seed/retry record |
| Subjective-state generation (valence/energy/stress) | **absent in the EMA layer.** Episode-level `affect_valence`/`fatigue` exist in the *diary* world (`models.py:Episode`, set by LLM prompt or by `enforce_fatigue()` in `jar_of_life_llm.py:229` which *forces* fatigue to rise with the hour) | absent | Synthesis §6.1 Tier 3 (2-item affect valence+arousal "include when primary RQ"); Kimi.md:119 (Energetic/Tired/Happy/Stressed); Maes 2023 / Maher 2020 antecedent-consequence designs (Synthesis §4.4) | **BUILD NEW (do not copy `enforce_fatigue`)** | Historical fatigue forcing is a deterministic stereotype (`hour → fatigue`), exactly the failure mode the brief prohibits. New generator: seed-controlled latent state + modest contextual modifiers + bounded ordinal sampling, every rule registered |
| Optional context note (1 short sentence) | **absent** | absent | Synthesis §6.3 lists open-ended text as "operationally weak / unscalable" — hence *optional*, ≤1 sentence, `null` allowed, and explicitly **not** a quantitative outcome | **BUILD NEW** | Implemented behind a closed-world contract with allow/deny lexicons, retry, and `context_note = null` fallback |
| LLM client with retry / robust JSON extraction | `configs/llm_config.py:LlamaClient` (local llama.cpp, presets, thinking-tag stripping); `modules/jar_of_life_llm.py:extract_json` (handles `<json>` tags and markdown fences); `run_pipeline.py` model fallback chain | `configs/api_config.py` (OpenRouter + Gemma free tier) | Historical `TEST_RESULTS.md` documents that free-tier models emit reasoning text instead of JSON → extraction hardening is real, hard-won knowledge | **ADAPT** | Reuse the `<json>`-tag + fenced-block extraction strategy and the low-temperature JSON preset idea. Reject DSPy, GEPA/GRPO optimizers, OpenRouter/llama.cpp specifics; target a DeepSeek OpenAI-compatible chat endpoint over stdlib `urllib` (zero new hard dependencies) |
| LLM-owned EMA generation (`generate_refined_ema` asks the model to invent prompt times, misses and biases) | `refined_diary_gen.py:169-229` | identical | Contradicts the Paper 3 role-of-LLM contract (LLM must not own scheduling or facts) | **REJECT** | LLM is confined to optional note rendering (and, only if separately justified, constrained judgement) |
| DSPy signatures / modules / GEPA / GRPO optimizers | `signatures/diary_signatures.py` (8 signatures incl. `EMAProbeGenSignature`), `optimizers/coherence_optimizers.py` (GEPA/GRPO/Composite), `evaluation/diary_eval.py` | subset in backup | none for a standalone EMA component; brief says "avoid agent frameworks unless necessary" | **REJECT** | Heavy dependency, prompt-optimisation machinery aimed at diary generation. `compute_ema_quality_reward` actively rewards corruption (mismatch 5–35 %, "missed prompts exist") — must not be inherited |
| Diary generation, backstory, "jar of life", sand layer, memory threads, OSM/Trondheim index (25 338 POIs, SQLite), routing, map viewer, persona templates | `modules/{refined_diary_gen,hybrid_diary_gen,jar_of_life*,backstory_gen,sand_layer}.py`, `osm/*`, `routing/*`, `cities/trondheim/profile.md` | partial | out of scope | **REJECT** | "Do not build a second DayForge." The EMA package consumes a day; it must not synthesise one |
| QA/self-correction loop (`self_correct_diary`, `generate_with_qa`) | `qa_validator.py:295-391` | identical | none for EMA | **REJECT** | LLM-driven repair of diaries; incompatible with immutable inherited context |
| Temporal validators (overlap/gap checks, completeness) | `qa_validator.validate_temporal`, `models.DailyDiary.validate_temporal_coverage` | identical | useful hygiene for *input* days | **ADAPT (input diagnostics only)** | Reused as read-only warnings about a supplied day (gaps/overlaps/unresolved intervals feed the exclusion and eligibility logic), never as a repair mechanism |
| Historical outputs as fixtures | `output/test_run_output.json`, `week_diary_output.json`, `jar_of_life_staged.json`, `xml_*.json` | `output/test_run_output.json` | — | **ADAPT** | Used as the shape reference for the legacy-day importer (`paper3_ema.legacy`) and as a regression fixture proving the importer reads a real historical day; their EMA probe blocks are **not** reused |

**Net result:** ~15 % of the historical code base is worth carrying (vocabularies, dual-timestamp
record shape, config block skeleton, wear-status lookup, lag-shape idea, JSON extraction
hardening). Everything that made the historical EMA layer "realistic by corruption" is rejected,
and the four things Paper 3 actually needs (hybrid event-enriched scheduler, schedule auditor,
transparent subjective-state generator, provenance/validation) do not exist historically and are
built new.

---

## 3. Evidence checks behind individual Paper 3 design decisions

Each decision below was traced to the corpus rather than accepted from the brief alone.

| Paper 3 decision | Supporting evidence in repo | Evidence class |
|---|---|---|
| EMA is an annotation layer, not ground truth; inherited context stays authoritative | `EMA_Definitive_Synthesis.md` §1, §3.3 ("⚠ OVERRATED: calling EMA 'ground truth' inverts the reliability relationship"); `CONCLUSION.md` §1.1 (all 7 sources) | A |
| Hybrid = random background + event-triggered enrichment | Synthesis §7.3 table (event-triggered alignment "STRONGEST"), §9.1, §9.4, §10.2 UNDERRATED #5; `Chatgpt_deep_research.md:210`; `Scite_Opus4.6_v2.md:293`; `Gemini.md:158` | A (design), C (the exact 3+2 split) |
| 5 opportunities/day | Synthesis §9.3 ("5–6 prompts/day"), §9.5 ("limit to 4–6 prompts/day for studies >7 days"); `CONCLUSION.md` §1.7 ("all sources converge on 4–6"); `Deepseek.md:281` (5–7) | A/B — 5 sits inside every reported range; the exact integer is a design choice |
| Stratify across ≈8 waking/daytime windows 08:00–23:00 | `Chatgpt_deep_research.md:53` (Maher 2018: 6 prompts randomly within **six 2-hr windows 08:00–20:00**), `:56` (IJBNPA 2021: random within 2-hr intervals), `Deepseek.md:462`; window count/span is host-supplied in Paper 3 | B/C |
| Exclude prompts during driving / cycling / running / vigorous exercise (delay to after the event) | `Gemini.md:158` ("if the accelerometer detects … high-intensity exercise, cycling, or driving, the prompt delivery must be delayed to ensure safety and prevent survey non-response") | A |
| Exclude prompts during sleep | `ema_generator.py:25` historical practice + obvious protocol requirement; Synthesis §7.2 (missingness at sleep transitions, Opus 4.6:224) | A/C |
| Prompt **after** an event, at the first stable opportunity; contextual reference = prompt time | Synthesis §7.3 (event-triggered alignment eliminates recall error), §9.1, §7.2 (prompt-response lag ⇒ use prompt time); `Gemini.md:112` (demarcation / boundary ambiguity) | A (principle), C (stability margin value) |
| Never prompt inside an unresolved interval / non-realised movement / unstable micro-transition | `Gemini.md:112,190` (demarcation crisis; incorrect start/end boundaries); Synthesis §10.2 UNDERRATED #4 | B — the *concept* is well supported; the specific interval flags are host-supplied (Paper 3 engineering) |
| Dual timestamps + 10-min expiry | Synthesis §7.3 ("dual-timestamp recording — STRONGEST in theory"), §9.1 ("discard or downweight responses with >10-minute lag"), §10.2 UNDERRATED #3; `Gemini.md:162` ("strict maximum latency threshold … e.g. 5 to maximum 10 minutes"); `Gemini.md:182` (−20 % odds per minute of lag) | A (record both, hard bound), C (exactly 10 min) |
| Right-skewed latency, mean ≈2–3 min | `Chatgpt_deep_research.md:156` (~5 min average adolescent lag); `Kimi.md:135` ("a 5-minute delay is common"); `Deepseek.md:68` (response window up to 15 min) | B |
| Stochastic (not fixed) missingness, target ≈85–90 % answered | Synthesis §13.1 (reported compliance typically 70–92 %); `Scite_Opus4.6.md:198` (Maher 92 %, Brannon 81 %); `Kimi.md:161` (mean 76 %); `Scite_Opus4.6_v2.md:41` (Le 2024: 67.7 % at 12–20 prompts/hour) | B — 85–90 % is inside the observed band for a 5-prompt/day protocol but the exact target is a calibration choice |
| Non-random missingness (lower response under high exertion / engaged contexts / late windows) | Synthesis §7.2 ("significantly less likely to respond during vigorous activity, driving, intense social situations"); `Opus v2:210`; `Gemini.md:118` | A (direction), C (magnitudes) |
| Event-triggered prompts may have *lower* compliance than random ones | `Gemini.md:172` (WEALTH: event-based compliance dropping to a **median 34 %**); Synthesis §7.2 (compliance decay after day 3 in event-triggered setups); `CONCLUSION.md` §5.x | A — recorded as an open tension with the 85–90 % target; implemented as a configurable per-trigger base rate (`literature_divergent` profile supplied) |
| 5-point ordinal valence / energy / stress | Synthesis §6.1 Tier 3 + §6.3 ("use 2-item valence + arousal if affect is needed", reject long batteries); `Kimi.md:119` (Energetic, Tired, Happy, Stressed as the common item set); `Gemini.md:53` (affect/stress/motivation/fatigue as momentary precursors); `Chatgpt.md:65` (arousal links consistent, valence mixed, stress inconclusive) | B — the *item family* is evidence-supported; **stress as a third item and the exact 5-point labels are Paper 3 design choices** (the synthesis prefers valence+arousal; "energy" is our arousal analogue). Registered as class B/C, divergence documented |
| Optional single-sentence context note, `null` allowed | Synthesis §6.3 ("open-ended text responses: rich but unscalable … cannot be automatically processed at dataset scale") ⇒ keep it optional, tiny, non-quantitative | C ( Paper 3 interpretability device), consistent with A |
| Device wear optional, never fabricated | Synthesis §6.2 + §10.2 UNDERRATED #1 ("always collect", "shockingly undercollected"); brief: standalone module must not invent wear | A (value), C (optional-field engineering) |
| No demographic/personality path into subjective state | Not an evidence claim but an ethics/design constraint; the corpus contains the *counter-example* (`Persona.to_prompt_context`) and no support for demographic affect inference. `Chatgpt.md:65` notes stress findings are inconclusive even for real populations | C (safeguard), with A-grade motivation from the absence of any supporting evidence |
| LLM confined to rendering; closed-world contract | Synthesis §8 (weak reporting/reproducibility) and §6.3 (open text unscalable) motivate strict bounding; historical `TEST_RESULTS.md` documents unbounded LLM output as the failure mode | C (engineering), A-motivated |

---

## 4. Material divergences between the evidence synthesis and the requested design
(Stop-condition check #1 — reported, not silently resolved.)

1. **Affect item set.** The synthesis (§6.1, §10.1 OVERRATED #2) is mildly *negative* about affect in
   accelerometer research ("over-collected", "low modelling value for classification") and recommends
   a **2-item valence + arousal** set only when affect is a primary research question. The Paper 3
   brief requests **three** items (valence, energy, stress). Resolution: implement the brief's three
   items (Paper 3's research question *is* about contextual/subjective annotation), keep the battery
   at the minimal end of the burden range, and record the divergence in the assumptions register
   (`docs/SCIENTIFIC_ASSUMPTIONS.md`, item S-12). No code path treats these items as activity labels.
2. **Event-triggered compliance.** `Gemini.md:172` reports WEALTH event-based compliance collapsing to
   a median 34 %, and Synthesis §7.2 reports decay after day 3 in event-triggered setups. A flat
   85–90 % target across trigger types is therefore *optimistic relative to the event-triggered
   evidence*. Resolution: per-trigger base response probabilities are configurable; the canonical
   Paper 3 profile hits the 85–90 % calibration target as instructed, and a second profile
   (`literature_divergent`) reproduces the lower event-triggered compliance for sensitivity analysis.
   Registered as B/C, not disguised as A.
3. **"Eight waking windows 08:00–23:00" is not in this repository.** The closest evidence is
   Maher 2018's six 2-hour windows (08:00–20:00) and IJBNPA 2021's 2-hour intervals. Resolution:
   windows are **host-supplied**, with a documented default of eight equal strata spanning
   08:00–23:00. Nothing in the package asserts that Appa or DayForge produces this shape.
4. **No evidence contradicts the 5-prompt/day hybrid design**; it sits inside every reported range
   (4–6, 5–6, 5–7). No stop condition triggered here.

## 5. Historical capabilities *not* represented in the Paper 3 brief
(Stop-condition check #2 — reported.)

| Capability in historical code | Should Paper 3 adopt it? | Decision |
|---|---|---|
| `recall_window` field (`current`, `past_15min`, `past_30min`, `past_2hr`) on `EMAProbe` (`models.py`) | The synthesis (§7.2 "recall window mismatch") says mixing recall frames inside one protocol is a structural error, but *declaring* the frame is good practice | **Adopt as a constant, declared field**: every Paper 3 record carries `recall_frame = "current_at_prompt_time"`. No mixed frames. |
| `demarcation_episodes` (sub-activities inside the recall window) | Synthesis §10.2 UNDERRATED #4 says demarcation uncertainty is systematically ignored | **Adopt in reduced form**: the context packet records whether the prompt window straddles an episode boundary and the elapsed time since the last transition (`minutes_since_activity_change`), which is what an analyst needs to down-weight ambiguous labels. Full sub-activity decomposition stays with the host world model. |
| Prompt reactivity (Maher 2018: small post-prompt PA reduction, Synthesis §4.1/§11.1) | Would mean EMA prompts *change* the synthetic world | **Reject** — the EMA module must not mutate the day. Recorded as a known un-modelled phenomenon. |
| Compliance decay over study days (Synthesis §7.2, §10.2 UNDERRATED #6) | Multi-day demonstrations should be able to show it | **Adopt as optional, off-by-default modifier** (`missingness.study_day_decay`), documented as class B; canonical Paper 3 profile keeps it at 0 so the 85–90 % calibration holds |
| Device-wear *fabrication* (`pipeline_config.device_wear_rate = 0.95`, "device worn all waking hours except …" prompts) | Brief forbids fabricating wear | **Reject** |
| Cross-day memory threads / carryover | Belongs to world generation | **Reject**; only `previous same-day structured EMA state` continuity is used (explicitly allowed by the brief) |

## 6. Environment findings that affect the plan

* Python 3.11.2. No `pyyaml`, `pytest`, `requests` preinstalled; a virtualenv was created outside the
  repository (`/home/user/.venv-ema`) and the three packages installed there. The package itself is
  written so that **only PyYAML is optional** (a minimal built-in parser handles the shipped
  `paper3_ema_v1.yaml`), HTTP uses stdlib `urllib.request`, and tests use `pytest` with a
  stdlib `unittest`-compatible fallback.
* **No DeepSeek credential is present** in the sandbox environment (no `DEEPSEEK_API_KEY` or
  equivalent), and outbound TLS to `api.deepseek.com` is blocked at the sandbox egress layer
  (TCP connects, TLS handshake is reset — `SSL_ERROR_SYSCALL`), while `github.com` and `pypi.org`
  work. Real end-to-end LLM testing is therefore **not currently possible**.
  Response: the DeepSeek client, the closed-world validator and the retry/fallback path are
  implemented and unit-tested offline against scripted adversarial clients; the real integration
  test (`tests/test_deepseek_integration.py`) auto-activates when `DEEPSEEK_API_KEY` is set **and**
  the endpoint is reachable, and reports SKIP with an explicit reason otherwise. This is reported as
  a partial stop condition in `docs/FINAL_REVIEW.md` §Q7 rather than worked around by pretending.
