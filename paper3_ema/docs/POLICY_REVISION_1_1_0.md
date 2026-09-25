# POLICY_REVISION_1_1_0.md

**Protocol 1.0.0 -> 1.1.0 — unknown physical posture is no longer an EMA exclusion,
and event detection now agrees with event placement about what "eligible" means.**

| | |
|---|---|
| Revision | 1.1.0 |
| Files changed | `config/paper3_ema_v1.yaml`, `paper3_ema/config.py`, `paper3_ema/events.py`, `paper3_ema/eligibility.py` (docstring only) |
| Tests added | `tests/test_policy_unknown_posture_and_event_window.py` (10), `tests/test_config.py` (+2) |
| Regression suite | 145 passed, 7 skipped (was 133 passed, 7 skipped) |
| Schema | unchanged (`schema_version` 1.0.0) — no field added, removed or retyped |
| Triggered by | the 49-day Appa integration: 46 valid days, 243/245 opportunities, 3 invalid bundles |

---

## 1. Correction A — `eligibility.exclude_unknown_activity` was set to `true`

### What changed

```diff
- exclude_unknown_activity: true            # [C] cannot verify stability -> do not prompt
+ exclude_unknown_activity: false           # [C] revised; see docs/POLICY_REVISION_1_1_0.md
```

and the key was added to `REQUIRED_KEYS`, so the policy can never again fall back
to an implicit code default.

### Why — the five audit questions

**A1. Is `exclude_unknown_activity` a Paper-3 design choice rather than a hard
safety/evidence requirement? — Yes, on both counts.**

* It is tagged **`[C]`** in the shipped configuration. The legend defined by
  `docs/SCIENTIFIC_ASSUMPTIONS.md:6-11` is: *A — directly supported by the
  supplied evidence corpus; B — broadly motivated by the evidence, but the
  parameter value is a design choice; C — Paper 3-specific engineering/design
  choice, no direct evidence claim.*
* It is **absent from the evidence table's own exclusion row**. Assumption
  **S-11** (`docs/SCIENTIFIC_ASSUMPTIONS.md:30`) is class **A** and enumerates
  the exclusion set as: *asleep, driving, cycling, running/vigorous,
  non-realised movement, unresolved interval, unstable micro-transition*. Unknown
  posture is not in that set.
* The primary source cited for S-11 (`Gemini.md:158`) requires that *"if the
  accelerometer detects that the user is currently engaged in high-intensity
  exercise, cycling, or driving, the prompt delivery must be delayed to ensure
  safety and prevent survey non-response."* It says nothing about unknown
  posture.
* The second citation (`EMA_Definitive_Synthesis.md` §10.2 UNDERRATED #4,
  demarcation uncertainty) is about *linking one EMA label to a heterogeneous
  accelerometer epoch*. It is an **alignment** problem, not a **prompt-safety**
  problem, and it is already carried by `exclude_unresolved_intervals`,
  `exclude_unstable_episodes` and the boundary stability margins.

**A2. Can a stable, realised diary episode with known behavioural context be
safely promptable when physical state is unknown? — Yes.**

The exclusion's stated rationale was *"cannot verify stability -> do not prompt"*.
Stability is already enforced independently, by `_resolve_unstable_periods`
(boundary margins), `exclude_unstable_episodes` and
`exclude_unstable_micro_transitions`; and unresolvedness by
`exclude_unresolved_intervals`. The flag was therefore **redundant as a
stability guard** while removing the moments EMA exists to capture. The evidence
base states the opposite priority directly: assumption `UNDERRATED #2`
(`EMA_Definitive_Synthesis.md` §10.2) finds **domain — not posture — is the
variable that most resolves sensor ambiguity** ("why is this person
sitting/walking?").

**A3. Can explicit unsafe states still be excluded independently? — Yes,
verified.** All of S-11 remains enforced by mechanisms that do not consult this
flag:

| Unsafe state | Mechanism |
|---|---|
| sleep | `exclude_during_sleep_period` (`wake_min`/`sleep_min`) + `Activity.SLEEPING` / `LYING_AWAKE` in `exclude_activities` |
| realised cycling | `include_journeys` mode block (`journey_mode:bike`) + `Activity.CYCLING` |
| driving | journey mode block (`car`, `bus`, `train`, …) + `Activity.DRIVING` |
| running / vigorous | `VIGOROUS_ACTIVITIES` unioned into the excluded set unconditionally |
| non-realised movement | `exclude_non_realised_movements` (episode **and** interval level) |
| unresolved interval / episode | `exclude_unresolved_intervals` |
| unstable transition | `exclude_unstable_episodes`, `exclude_unstable_micro_transitions`, boundary margins |

Measured on the frozen 49-day cohort after the change, every one of those still
fired (minutes excluded):

| Reason | Minutes |
|---|---|
| `asleep` | 29 595 |
| `unstable_micro_transition` | 7 089 |
| `activity:lying_awake` | 5 216 |
| `non_realised_movement` | 1 353 |
| `journey_mode:bike` | 1 246 |
| `activity:sleeping` | 1 070 |
| `non_realised_interval` | 373 |
| `uncovered_time` | 49 |
| `activity:cycling` | 35 |
| `unresolved_episode` | 2 |

A targeted scan of the 11 527 newly-eligible minutes found **0** inside a
vehicle-typed place and **0** inside a sleep, driving, cycling, running or
vigorous episode. All newly-eligible transport minutes are `walk_transition`,
`commute_to_work`, `commute_home`, `transit_transition`, `indoor_transition` and
`school_dropoff` on walking legs.

**A4. Would allowing these episodes fabricate physical-state information? — No.**

The adapter is untouched by this revision: `episode.activity` stays `None`, so
the EMA record's `ctx_activity` is `null`. Nothing derives sitting, standing or
mixed from the domain label, and `context._fallback_exertion(None)` returns
`None`, so no exertion is synthesised either. Across the corrected 49-day dry
run, **102 of 245 prompts carry `ctx_activity = null`**, and a cohort-wide check
found **0** records where an unknown-posture episode produced a non-null
activity.

**A5. How many excluded minutes and days become legally promptable?**

| Metric | 1.0.0 | 1.1.0 | Change |
|---|---|---|---|
| Cohort eligible minutes | 13 005 | 24 532 | **+11 527 (+88.6 %)** |
| EMA opportunities | 243 / 245 | **245 / 245** | +2 |
| Invalid bundles | 3 | **0** | −3 |
| Days with fewer than 5 prompts | 2 | **0** | −2 |

Newly-eligible minutes by (episode posture, domain): `(None, work)` 5 974,
`(None, leisure)` 3 413, `(None, household)` 1 082, `(None, self_care)` 643,
`(None, transport)` 415.

---

## 2. Correction B — event detection disagreed with event placement

### Root cause

Four event detectors each decided "is this event eligible?" with their own
ad-hoc test, and none of them enforced the same rule the scheduler uses to place
a prompt:

| Detector | Old test | Problem |
|---|---|---|
| `_post_trip_events` | `_has_stable_opportunity` = a stable minute exists in `[end, end+45]` | no window requirement |
| `_post_active_events` | same helper | no window requirement |
| `_context_transition_events` | inline `eligibility.is_stable(anchor)` | no window requirement; also tested only the single anchor minute |
| `_discretionary_events` | inline `is_stable(anchor)` + interior search | no window requirement |

The scheduler additionally requires
`sampling.waking_windows.require_prompt_inside_window: true`, i.e. the chosen
minute must be contained in a host-declared daytime stratum. The auditor
(`audit.py`) consumes the **same** `detect_events`, so when detection accepted an
event that placement could not serve, the auditor reported the contradiction as
`event_enrichment_missing` — an error on a day where no legal prompt existed.

**This is answer C: the auditor labels an event "eligible" differently from the
scheduler.** It is also a genuine scheduler/auditor contract defect, because both
sides read one detector that did not implement the documented placement rule.

### The demonstrated case — `p_48f_heal_0014`, 2026-10-01

194 eligible minutes, 5/5 opportunities, six detected events, zero event prompts.
Every event ended before the first waking window (08:00):

| Event | Kind | End | First stable minute | Waking window |
|---|---|---|---|---|
| `evt-trip-…:4:explicit` | post_trip | 06:37 | 06:37 | **none** |
| `evt-trip-…:7:explicit` | post_trip | 07:07 | 07:07 | **none** |
| `evt-active-…:ep004` | post_active_episode | 06:47 | 07:02 | **none** |
| `evt-active-…:ep007` | post_active_episode | 07:17 | 07:35 | **none** |
| `evt-transition-…:ep004` | context_transition | 06:32 | 06:32 | **none** |
| `evt-transition-…:ep007` | context_transition | 07:02 | 07:02 | **none** |

The 45-minute horizon expires at 07:22 at the latest, before any window opens, so
no legal prompt minute existed. The scheduler correctly skipped all six.

### Fix

One shared legality test, `_has_stable_opportunity`, now requires a **stable
minute contained in a waking window** within the post-event horizon, and all four
detectors use it:

* it iterates the day's waking windows, intersects each with `[event_end,
  event_end + horizon]`, and accepts only if `first_stable_minute` finds a minute
  there (`Interval.contains` is half-open, so the last contained minute is
  strictly below `window.end`);
* `_context_transition_events` and `_discretionary_events` now call it instead of
  testing a single anchor minute.

This makes detection, placement and audit agree **by construction**. It is a
correction in both directions: events that are genuinely unplaceable are no
longer reported, and transitions whose anchor minute happened to be unstable but
which do have a legal later minute are no longer discarded.

### Latent scope of the defect

The invariant test found the same class of violation in a **pre-existing
fixture** (`evening_shift_day`: a journey ending 23:00, after the last window),
not only in the Appa cohort. Before the fix, 12 of the 49 frozen days failed for
this reason; after it, none do.

---

## 3. Measured effect of 1.1.0 on the frozen 49-day cohort (offline)

Scheduler and auditor only — **no provider call was made**.

| Metric | 1.0.0 | 1.1.0 |
|---|---|---|
| Participant-days | 49 | 49 |
| Valid participant-days | 46 | **49** |
| Opportunities | 243 / 245 | **245 / 245** |
| Days with fewer than 5 prompts | 2 | **0** |
| Background (semi-random) | 155 | 154 |
| Event-enriched | 88 | 91 |
| Trigger mix | `semi_random` 155, `post_trip` 70, `context_transition` 10, `post_active_episode` 8 | `semi_random` 154, `post_trip` 74, `post_active_episode` 10, `context_transition` 7 |
| Detected events with no legal prompt minute | 12 days affected | **0** |
| Days with events but no event prompt | 3 | **0** |
| Prompts in an excluded minute | 0 (non-relaxable) | 0 (non-relaxable) |
| Fabricated postures | 0 | 0 |
| Protected upstream changes | 0 | 0 |

### The three previously failing days

| Date | Eligible minutes | Opportunities | Validation | Self-audit |
|---|---|---|---|---|
| 2026-09-30 | 39 -> **494** | 4 -> **5** (bg 2->3, event 2->2) | FAIL -> **PASS** | NEEDS_REPAIR -> **VALID** |
| 2026-10-01 | 194 -> **526** | 5 -> 5 (bg 5->4, event **0->1**) | FAIL -> **PASS** | NEEDS_REPAIR -> **VALID** |
| 2026-10-02 | 69 -> **522** | 4 -> **5** (bg 2->4, event 2->1) | FAIL -> **PASS** | NEEDS_REPAIR -> **VALID** |

No other protocol rule was weakened to reach 245. The fragmented-day relaxation
still drops only the boundary margin and is still flagged `stability_relaxed`
(one prompt on the cohort, on `p_25f_acad_0022` 2026-10-03, whose sole exclusion
reason is `unstable_micro_transition`; the same relaxation fired on the same day
under 1.0.0 at 14:16).

---

## 4. What deliberately did NOT change

* **Schema** — `schema_version` stays 1.0.0. No field was added, removed, renamed
  or retyped.
* **Safety exclusions** — S-11 is intact and independently enforced (section 1,
  A3).
* **Sampling policy** — `opportunities_per_day`, `min_background`,
  `max_event_enriched`, `min_gap_minutes`, coverage targets and the event
  priority order are untouched.
* **Stability policy** — `stability_margin_minutes`,
  `exclude_unstable_episodes`, `exclude_unstable_micro_transitions` and the
  fragmented-day relaxation are untouched.
* **State generator, missingness and latency** — untouched.
* **The note-rendering runtime** — untouched. The DeepSeek `deepseek-flash`
  accepted runtime and the note-rendering config override are unchanged.
* **Upstream DayForge / Appa artifacts** — none were read for writing; the frozen
  cohort is byte-identical (147/147 hashes).

---

## 5. Versioning and provenance

* `meta.protocol_version` is now `1.1.0`; `protocol_name` remains
  `paper3_ema_v1`. Every bundle records `protocol_version` in its provenance, and
  the run identity records both the frozen-config and runtime-config hashes, so a
  1.1.0 cohort is distinguishable from a 1.0.0 one without inspecting the data.
* The change is confined to four files and is reversible by restoring
  `exclude_unknown_activity: true` and the previous `_has_stable_opportunity`
  body; both old behaviours are reproduced by dedicated tests
  (`test_legacy_unknown_posture_rule_is_reproducible_but_non_default`).

---

## 6. Residual limitations

1. The correction changes **which** minutes are promptable, so a 1.1.0 cohort is
   not comparable minute-for-minute with the 1.0.0 run; the earlier 49-day EMA
   output remains archived development output and must not be mixed with it.
2. 102 of 245 prompts (41.6 %) sit in episodes whose posture is unknown. The EMA
   record is honest about this (`ctx_activity = null`), but any analysis that
   conditions on posture will have a materially smaller denominator than one
   that conditions on domain.
3. The unknown-posture share is driven by the frozen physical-state layer
   (24.2 % of cohort episode hours refused, 240 h of them as
   `UNSUPPORTED_ACTIVITY` with a model-judged hint of `unknown`/`mixed`). This
   revision makes EMA robust to that refusal; it does not improve the upstream
   posture evidence.
4. `sampling.waking_windows.require_prompt_inside_window` is documented as a
   configurable policy, but `schedule_for_day` requires window membership
   unconditionally. Detection now matches the scheduler. If that flag is ever set
   to `false`, the scheduler — not the detector — must be changed first.
