# Scientific assumptions register

Deliverable #21. Every non-trivial simulation rule in the Paper 3 EMA module is
listed with its classification:

- **A** — directly supported by the supplied evidence corpus
  (`EMA_Definitive_Synthesis.md`, `CONCLUSION.md`, and the seven research
  reports);
- **B** — broadly motivated by the evidence, but the *parameter value* is a
  design choice;
- **C** — Paper 3-specific engineering/design choice, no direct evidence claim.

Evidence citations give the file and (where useful) the section/line of the
repository corpus. Nothing classified C is presented as A.

## 1. Sampling design

| # | Rule | Class | Evidence / rationale |
|---|---|---|---|
| S-1 | EMA is a contextual + subjective **annotation layer**, not ground truth; inherited context stays authoritative | **A** | Synthesis §1, §3.3 (OVERRATED #1), §5.2; CONCLUSION §1.1 (all 7 sources) |
| S-2 | **5 opportunities per participant-day** | **B** | Synthesis §9.3 ("5–6 prompts/day"), §9.5 ("limit to 4–6 prompts/day for studies >7 days"), CONCLUSION §1.7 (all sources converge on 4–6), Deepseek.md:281 (5–7). The exact integer 5 is Paper 3's choice inside the supported range |
| S-3 | Hybrid design: random background **plus** event-triggered enrichment | **A** (design) | Synthesis §7.3 (event-triggered alignment STRONGEST), §9.1/§9.4, §10.2 UNDERRATED #5; Chatgpt_deep_research:210; Opus v2:293 |
| S-4 | Exact 3+2 split (≥3 semi-random, ≤2 event-enriched) | **C** | Paper 3 protocol specification; no published study fixes this split |
| S-5 | Event priority `post_trip > post_active_episode > context_transition > discretionary_fallback` | **C** | Paper 3 specification (active transport focus makes trips first); the evidence supports event-triggering generally (A) but not this ordering |
| S-6 | Fill with semi-random when insufficient eligible events; **never fabricate event categories** | **A** (principle) / **C** (mechanism) | Fabricating categories would be the reverse of the evidence's warning against forced diversity; the fill rule is engineering |
| S-7 | Stratify across **≈8 host-supplied daytime windows**, default 08:00–23:00 | **B** | Chatgpt_deep_research:53 (Maher 2018: six 2-hr windows 08:00–20:00), :56 (IJBNPA 2021: 2-hr intervals), Deepseek.md:462 (stratify across waking hours). Window count/span are host-supplied; the default is a design choice. **Note:** the "eight windows 08:00–23:00" concept is not in this repository — it belongs to the unavailable host system, so it is implemented as configurable input, never asserted |
| S-8 | 30-min minimum gap between prompts | **C** | Burden-control choice; the literature supports 4–6 prompts/day (A) but not a specific gap |
| S-9 | 5-min stability margin from episode boundaries (adaptive cap for short episodes) | **C** | Motivated by demarcation uncertainty (Synthesis §10.2 UNDERRATED #4, Gemini:112 — A for the *problem*), value is engineering |
| S-10 | Prompts placed **after** the event at the first stable opportunity (45-min horizon) | **B** | Synthesis §7.3 (event-triggered alignment eliminates recall error), Gemini:158 (delay delivery during exercise/cycling/driving); horizon value is a design choice |
| S-11 | Exclusions: asleep, driving, cycling, running/vigorous, non-realised movement, unresolved interval, unstable micro-transition | **A** | Gemini:158 (safety + non-response for exercise/cycling/driving); sleep-adjacent missingness (Opus 4.6:224); demarcation uncertainty for unresolved/unstable (Synthesis §10.2 #4, Gemini:112) |
| S-12 | Fragmented-day relaxed fallback (drop boundary margin only, keep all safety exclusions, flag `stability_relaxed`) | **C** | Engineering decision to keep feasibility on pathological days while preserving every safety exclusion; documented per prompt and reported by the auditor as a warning |
| S-13 | Event detection thresholds (trip ≥5 min; active bout ≥10 min & exertion ≥0.4; transition settles ≥5 min; discretionary ≥15 min; per-kind caps) | **C** | Motivated by the sedentary-triggered literature's bout thresholds (Giurgiu 2020: 20–30 min sitting — Synthesis §9.2; B for the *idea* of bout-based triggers), but each Paper 3 value is a design choice |

## 2. Context & subjects

| # | Rule | Class | Evidence / rationale |
|---|---|---|---|
| S-14 | Items: **valence, energy, stress**, 5-point ordinal | **B** | Synthesis §6.1 Tier 3 (2-item valence+arousal "include when primary RQ"; reject long batteries), §6.3; Kimi:119 (Energetic/Tired/Happy/Stressed item set); Chatgpt:65 (arousal links consistent, valence mixed, stress inconclusive). **Divergence documented:** the synthesis prefers valence+arousal; Paper 3's primary RQ is contextual/subjective annotation, so the 3-item battery is the brief's specification — "energy" is the arousal analogue; stress is the third item. Recorded here, not disguised |
| S-15 | Exact 5-point anchor labels (e.g. stress 1 = "none/very low") | **C** | Standard Likert convention; the corpus supports short ordinal scales (B) but not these exact labels |
| S-16 | Context packet bounded to current + bounded recent context (60/180-min windows), no proper names, no narratives, same-day continuity only | **C** | Paper 3 specification; motivated by recall-window discipline (Synthesis §7.2 — A for the *problem* of mixed frames) |
| S-17 | Context anchored to **prompt time** | **A** | Synthesis §7.3 (dual-timestamp recording; use prompt time for alignment — "STRONGEST in theory"), §9.1 |
| S-18 | Device-wear field optional; **never fabricated** | **A** (value) / **C** (optionality) | Synthesis §6.2 & §10.2 UNDERRATED #1 ("always collect", "shockingly undercollected"); optionality is standalone-module engineering |

## 3. Subjective-state generator

| # | Rule | Class | Evidence / rationale |
|---|---|---|---|
| S-19 | Seeded latent-state model: baseline + day effect + clipped rule sum + noise → ordinal sampling | **C** | The *form* is a simulation engineering choice; the corpus contains no affect dynamics to copy, and the brief requires bounded transparency rather than a specific model |
| S-20 | Baselines (valence 3.2, energy 3.2, stress 2.6) and noise SDs | **C** | Centre-of-scale defaults; no empirical moment estimates exist in the corpus for synthetic participants |
| S-21 | Circadian modifiers (per-construct time-of-day offsets) | **B** | Time-of-day effects on EMA affect/energy are ubiquitous in the literature (Kimi:161 compliance varies by time of day; Maes 2023 intraindividual dynamics — Synthesis §4.4); magnitudes are design choices, deliberately small |
| S-22 | Recent-exertion rule (energy ↓, valence ↑, stress ↓, 45-min half-life) | **B** | Post-activity subjective dynamics are a documented EMA use (Synthesis §4.4 antecedent/consequence designs; Chatgpt:65 PA↔arousal links consistent); signs/sizes are design choices |
| S-23 | Post-journey mode offsets (active/public/car), 30-min window | **C** | No mode-specific affect findings in the corpus; Paper 3 design choice, small magnitude |
| S-24 | Journey delay/crowding offsets **only** when the host documents them | **A** (grounding discipline) / **C** (magnitudes) | The closed-world discipline follows directly from S-1; magnitudes are design choices |
| S-25 | Schedule-pressure rule (commitment within 30/60/120 min → stress ↑, energy/valence ↓) | **B** | Schedule pressure as an affect determinant is a classic EMA antecedent variable (Synthesis §4.4, Maher 2020 intentions/pressure designs); horizons and sizes are design choices |
| S-26 | Social-company offset (small valence ↑ / stress ↓ with company) | **B** | Hevel 2021: affect during SB depends on social context (Synthesis §4.3/§11.2); magnitude is a design choice |
| S-27 | Domain offsets **capped at ±0.30 per item** | **C** | Explicit anti-stereotype guard (the brief's "BAD: work → stress high"); the cap is engineering |
| S-28 | Same-day continuity anchor (weight 0.35, ≤240 min) | **C** | Within-day state persistence is a reasonable simulation property; the corpus does not specify a weight; cross-day continuity is deliberately excluded (brief) |
| S-29 | Persona allowlist (childcare, work-schedule pattern, commute mode, sleep schedule) with contextual gating | **C** | Brief-mandated demographic safeguard; the corpus contains **no** evidence supporting demographic affect inference (that absence is the motivation). Each allowed fact applies only inside its contextual role |
| S-30 | Modifier clip 1.5; hard latent clip [1,5]; ordinal sampling SD 0.6 | **C** | Boundedness parameters; no empirical basis in corpus, chosen for visible-but-bounded effect sizes |

## 4. Missingness & latency

| # | Rule | Class | Evidence / rationale |
|---|---|---|---|
| S-31 | Stochastic Bernoulli response model; **no forced-miss** | **A** | Synthesis §7.2 (missingness is stochastic and non-random); historical exactly-one-miss explicitly rejected (Phase 0 §1.4) |
| S-32 | Canonical calibration **85–90%** answered over a large cohort | **B** | Reported compliance 70–92% (Synthesis §13.1), Maher 2018: 92%, Brannon 2016: 81%, Kimi:239 mean 76%; the 85–90 band is Paper 3's calibration target *inside* the observed range, for a 5-prompt/day protocol — a simulation property, not a compliance claim |
| S-33 | Per-trigger base rates (0.88–0.94; events slightly lower) | **B** | Direction: event-triggered compliance is harder to maintain (Synthesis §7.2 decay; Gemini:172 WEALTH event-based median 34% — extreme); magnitudes are design choices set so the canonical profile meets S-32 |
| S-34 | Modifiers: high exertion ×0.92, engaged context ×0.97, late window ×0.95, not-worn ×0.85, optional study-day decay (off by default) | **B** (direction) / **C** (magnitude) | Synthesis §7.2, Opus v2:210, Gemini:118 (less likely during vigorous activity/driving/intense social situations); device non-wear (Synthesis §6.2); compliance decay after day 3 (Synthesis §7.2, UNDERRATED #6) |
| S-35 | Latency: right-skewed lognormal (mean ≈2.1 min, median ≈0.9 min) | **B** | Chatgpt_deep_research:156 (~5-min average adolescent lag), Kimi:135 ("a 5-minute delay is common"), Deepseek:68 (window up to 15 min); the distribution form/parameters are design choices calibrated to a 2–5 min mean |
| S-36 | **10-minute expiry**; expired responses recorded, flagged, excluded from alignment | **A** | Synthesis §9.1 ("discard or downweight responses with >10-minute lag"), §7.3 (dual timestamps), Gemini:162 (strict maximum latency bound 5–10 min), §10.2 UNDERRATED #3 (latency reporting). The exact 10-min value and the record-and-flag policy are the brief's specification within the supported range |
| S-37 | Post-exertion / late-window latency multipliers (1.35 / 1.15) | **C** | Plausibility choice; no magnitude evidence in corpus |

## 5. Notes & LLM

| # | Rule | Class | Evidence / rationale |
|---|---|---|---|
| S-38 | Optional **one-sentence** context note (≤24 words / 160 chars), `null` always acceptable, not a quantitative outcome | **C** | Synthesis §6.3 (open text "rich but unscalable … cannot be automatically processed at dataset scale") motivates making it optional, tiny and non-quantitative; Paper 3 uses it for interpretability/auditability |
| S-39 | Closed-world contract + category-coded validator + retry + offline fallback + null fallback | **C** | Engineering discipline motivated by the corpus's reproducibility warnings (Synthesis §8) and the historical LLM failure modes (TEST_RESULTS.md) |
| S-40 | **LLM renders notes only; does not select subjective values** | **C** (decision, A-motivated) | Full justification in `docs/ARCHITECTURE.md` §7. The structured generator is the scientifically defensible choice for bounded, reproducible, auditable 1–5 outputs; the corpus's best practice is a short structured battery, not open generation |
| S-41 | Offline deterministic template renderer as LLM-free fallback | **C** | Guarantees the module is fully functional offline; its output is closed-world *by construction* and always re-validated |
| S-42 | LLM decoding settings (temp 0.4, top_p 0.9, max_tokens 120) | **C** | Conventional low-temperature structured-output settings; recorded in provenance |

## 6. Provenance & validation

| # | Rule | Class | Evidence / rationale |
|---|---|---|---|
| S-43 | Five field-origin classes; every field classified | **C** | Brief specification; motivated by the corpus's reporting/reproducibility failures (Synthesis §8, §10.2 #3) |
| S-44 | Deterministic `generated_at` run anchor (bundles are pure functions of (day, seed, config)) | **C** | Engineering choice for byte-reproducible artifacts |
| S-45 | Ten-family bundle validation; inherited-fact re-derivation; demographic-leak scan | **C** | Brief specification; the forensic immutability check is motivated by S-1 |

## 7. Known divergences from the evidence (declared, not hidden)

1. **S-14 (item set):** the synthesis recommends a 2-item affect battery and
   warns affect is "over-collected" in PA research; Paper 3 keeps 3 items
   because its research question *is* contextual/subjective annotation. The
   battery stays at the minimal end of the burden range and the items are
   explicitly synthetic.
2. **S-32/S-33 (event-triggered compliance):** real event-triggered compliance
   can be far below 85% (Gemini:172: WEALTH event-based median 34%). The
   canonical profile simulates events only *slightly* harder to answer so the
   overall calibration target holds; a `literature_divergent` sensitivity
   profile (lower event base rates) is a documented one-line config change for
   the paper's sensitivity analysis.
3. **S-7 (window concept):** the "eight windows 08:00–23:00" concept is not in
   this repository; it is treated as host-supplied input with a documented
   default, per the Appa-availability constraint.

## 8. What is explicitly NOT claimed

- No 85–90% figure is presented as a claim about true human compliance.
- No subjective value is presented as an observed human measurement.
- No note text is presented as human speech; it is synthetic rendering.
- No rule in this register is a claim about the psychology of real people;
  the rules are simulation rules for synthetic participants, documented as such
  in the YAML and in `SCHEMA/scales.synthetic_declaration`.
