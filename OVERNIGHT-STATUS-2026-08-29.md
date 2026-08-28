# Overnight status — RoB lane, written before stopping

## Running / finished

**All three requested jobs are COMPLETE. Nothing is still running, and nothing needs a lane alive.**

| job | state | output |
|---|---|---|
| abstract-only re-test | **done before the brief arrived** | `MORNING-REPORT-2026-08-29.md`, commit `0a1566d39` |
| funder vs retrievability | **done, 353/353** | `MORNING-REPORT-2026-08-29.md`, commit `bc3c0847c` |
| multi-route full-text harvest | **done, 317/317** | `F:\claude-temp\pend\out\` — report, JSONL, 317 XML files, `FULLTEXT-HARVEST.DONE` |

Harvest outputs live under `F:\claude-temp\pend\out\` and are NOT committed: 317 full texts are
third-party copyrighted material and a scratch cache, not a repository artefact. The scripts
that produce them are committed; re-running reproduces the cache.

## The harvest result

**317 of 317 deposits retrieved — 100%.** Routes: **europepmc 274 · ncbi_efetch 25 · pmc_direct 18.**

⇒ **43 of 317 (14%) needed a route beyond the first.** A single-index retriever would have
declared those 43 unavailable. That is the same 14% the funder probe measured, reproduced by an
independent job.

⚠️ **Retrieved is not assessable.** 317 documents arrived; whether they answer D1, D2, D3 is
untested. On the one trial measured, a full text answered 4 of 5 signalling questions — the
miss being allocation concealment, which the trial genuinely never reported.

## ⛔ Retracted overnight — do not publish

**"An open-path review systematically under-assesses industry-funded trials" is REFUTED.**
INDUSTRY 205/214 = 96% reachable; OTHER 97/121 = 80%. Ratio 1.19 the *other* way, and the
harvest confirms it — 100% retrieval in every funder class. The claim came from two trials, one
per arm. It was mine and it must not enter the defect taxonomy.

## Needs a ruling (nothing blocked on me overnight)

1. **21 re-derivations** — 15 raise a domain to HIGH and change GRADE.
2. **54 unfalsifiable access claims** — no identifier, no route named; cannot be confirmed or
   refuted. Rewrite to name both, or withdraw.
3. **SPIRE scope** — 6 trials or 8.

## Not done, deliberately

**Splitting `NO_INFORMATION` into trial-silent / not-retrieved / not-yet-attempted.** It writes
to `risk_of_bias` corpus-wide and wants a plant both ways before touching a store. Designed, not
landed.

**`agy` unspent.** No genuine cross-family judgement has arisen.

## State

Tree clean, nothing half-applied, no plant left in place, everything pushed to `origin/main`.
