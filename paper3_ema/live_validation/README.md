# Live DeepSeek validation — run on a machine with normal internet

Turnkey live-provider validation harness for the standalone Paper 3 EMA
module.  It runs the full protocol against the real DeepSeek API and writes
a gate report plus a complete set of machine-readable artefacts.  It **uses**
the package but never modifies it, and it changes **no scientific parameters**.

## Requirements

- Python 3.10+
- outbound HTTPS to `api.deepseek.com`
- a DeepSeek API key (temporary is fine)
- bash (for the wrapper) — or run the two plain commands below

## Run

```bash
cd paper3_ema/live_validation
export DEEPSEEK_API_KEY="sk-..."        # environment only; this tool never stores it
./run_live_validation.sh
```

The wrapper creates `.venv-live` (pyyaml, pytest, requests), sets
`DEEPSEEK_MODEL=deepseek-flash` with the provider-documented request shape
(thinking enabled, `reasoning_effort=high`, `max_tokens=1024`), and runs
`live_harness.py --phase all --write-docs`.

**Without bash** (e.g. Windows cmd/PowerShell, using the venv's own python):

```bat
python -m venv .venv-live
.venv-live\Scripts\python -m pip install pyyaml pytest requests
set DEEPSEEK_API_KEY=sk-...
set DEEPSEEK_MODEL=deepseek-flash
.venv-live\Scripts\python live_harness.py --phase all --write-docs
```

**Expect:** 15–45 minutes wall time (≈200–260 API calls).  Let it run to
completion; it prints progress per phase.  API cost is a few dollars at most
at published rates — the exact cost is computed from the returned token usage
and reported (peak and off-peak windows).

## What it does (phases)

1. **connectivity** — endpoint reachability + exact failure classification
2. **phase 1** — the committed integration tests (model per config) + the full test suite
3. **phase 1b** — deepseek-flash transport smoke (auth, model echo, request shape, parsing, retry bounds, closed-world acceptance)
4. **phase 2** — 15 controlled live-note cases: varied contexts incl.
   post-walk / post-run / post-cycle (only after cycling) / post-bus-train /
   post-car / documented-delay / no-delay / context-transition / evening /
   no-event-day / sparse-ambiguous, each designed to tempt a specific
   unsupported fact (weather, delay, person, named place, destination, cause,
   medical condition, psychological trait, unsupported journey)
5. **phase 3** — live-vs-offline invariance: identical day+config+seed, every
   non-note field must be identical
6. **phase 4** — 4 personas × 7 days live cohort (140 opportunities) with
   call/parse/acceptance/retry/rejection/fallback/null counts, latency
   mean/median/p95, token usage, cost estimate, bundle validation, and 18
   representative records for human inspection
7. **phase 5** — repeatability boundary: structured output reproducible under
   the same seed; LLM nondeterminism confined to the note + its provenance
8. **report** — PASS / CONDITIONAL PASS / FAIL gate document

## Outputs

- `artifacts/live_<UTC-stamp>/` — the full artefact set
  (`00_identity.json` … `07_repeatability.json`, `report.md`,
  `06_cohort_bundles.jsonl`)
- `../docs/LIVE_DEEPSEEK_VALIDATION.md` — the same report in the package docs

## Send back

Zip the whole `artifacts/live_<stamp>/` directory and send it over.  The
artefacts contain **no secret material** — every file passes a final
secret-scan/redaction sweep and the API key is only ever held in the
process environment.

## Verify the harness offline (no key, no network)

```bash
python -m pytest live_validation -q   # 7 self-tests: case matrix, diff/allow-list, cost math, redaction, verdicts
python -m pytest ../tests -q          # committed module test-suite: 132 passed, 7 skipped
```

## Credentials

The key is read only from `DEEPSEEK_API_KEY` in the environment.  It is never
written to any file, log or artefact, never printed, and never committed.
Unset/delete it after the run.
