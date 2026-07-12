# Protocol pre-registration by git commit (STAGED — not deployed)

Turns the discipline registries impose on **trialists** onto the **reviewer**: a
RapidMeta review's protocol is content-hashed and committed to git **before the
search and extraction run**, so outcome-switching and post-hoc PICO drift become
tamper-evident and *diffable inside the app itself*.

## Workflow (the order is the whole point)
1. Write `protocol/<REVIEW>.json` (schema below) — PICO, eligibility, the
   **pre-specified primary outcome**, planned analysis, search strategy.
2. `python scripts/preregister_protocol.py protocol/<REVIEW>.json` → writes
   `<REVIEW>.LOCK.json` (sha256 of the protocol + git HEAD + UTC).
3. **`git commit protocol/<REVIEW>.json`** — this commit's hash + timestamp *is*
   the registration. Optionally anchor it to a neutral external timestamp
   (Zenodo DOI / OpenTimestamps) and record it in the lock's `external_anchor`.
4. **Then** run search → extraction → build the app.
5. `python scripts/protocol_diff.py protocol/<REVIEW>.json <APP>_REVIEW.html` →
   `CONCORDANT` / `MINOR-DRIFT` / `DRIFT` (flags primary-outcome switch, a
   registered-primary demoted to secondary, effect-measure change, unregistered
   or uncommitted lock).
6. `python scripts/inject_protocol_badge.py protocol/<REVIEW>.json <APP>.html --apply`
   surfaces the hash, commit, timestamp and verdict **in the app** (offline-safe,
   additive, idempotent).
7. `--check` at any later point re-hashes the protocol; if it changed since
   registration, `check` fails — a silent post-hoc amendment cannot pass.

## Schema (`protocol/<REVIEW>.json`)
```
review_id            string, unique
title                string
pico.population      string
pico.intervention    string
pico.comparator      string
pico.outcomes        [string]           # primary first
eligibility.inclusion  [string]
eligibility.exclusion  [string]
primary_outcome      string             # the ONE pre-specified primary
planned_analysis.model          string  # e.g. random-effects (REML) + HKSJ
planned_analysis.effect_measure string  # HR|OR|RR|MD
planned_analysis.subgroups      [string]
search.databases     [string]
search.date_run      string|null        # null until the search is run
search.strategy      string
```

## Prior art (credited — this is a re-combination, not a from-scratch invention)
- **git-commit + external timestamp** pre-registration is established
  (`git-timestamp` on PyPI; OSF / Zenodo trusted timestamps; a raw git commit
  timestamp is *self-asserted*, so an external anchor is recommended).
- **PROSPERO** registers systematic-review protocols, but >20 % of reviews drift
  from their protocol and PROSPERO is **not machine-diffable** against the run.
- **OSF / AsPredicted** timestamp frozen protocol snapshots but do not emit a
  protocol-vs-analysis diff embedded in the analysis artifact.

**What is fresh here:** the lock is committed *before* search in the **same repo
that builds the app**, and the **app carries a machine-computed
protocol-as-registered vs analysis-as-run diff** — so a living meta-analysis that
quietly swaps its primary outcome can no longer hide it. Legitimate amendments
are *allowed* (Cochrane's "differences between protocol and review"); they are
just made **visible and dated**, not silent.

## Files
| File | Role |
|---|---|
| `preregister_protocol.py` | validate + hash-lock a protocol; `--check` detects tampering |
| `protocol_diff.py` | protocol-as-registered vs analysis-as-run diff |
| `inject_protocol_badge.py` | surface hash/commit/timestamp/verdict in the app |
| `FINERENONE_CKD.json` + `.LOCK.json` | worked demo (verdict CONCORDANT) |
