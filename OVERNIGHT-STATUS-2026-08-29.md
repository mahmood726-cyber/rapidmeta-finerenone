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

---

## Rulings 1 and 2 — proven, deliberately unrun

`scripts/lane_rob/apply_rulings_2026_08_28.py` — dry-run by default, `--plant` proves it both ways.

```
PLANT ruling 1  defect cell detected, derives HIGH   [PASS]
                clean cell untouched                 [PASS]
PLANT ruling 2  unfalsifiable claim detected         [PASS]
                claim naming a route and an id kept  [PASS]

DRY RUN   ruling 1: 21 domain cells across 7 topics
          ruling 2: 50 unfalsifiable claims across 19 topics
          fixed 0 / rebuilt 0 / SERVED 0
```

**Nothing applied, and that is the ruling being followed rather than deferred.** Ruling 1
requires the change verified SERVED and disclosed on the page with its date — a fleet rebuild.
Landing the store write without it leaves every page showing the old value, which is the
staleness class this project has spent the week on. **An unrun applier is a task; a
half-applied one is a defect.**

⚠️ **50, not 54.** The earlier count asked only whether a claim names an identifier. The
applier also keeps a claim that names a **route** — four claims say which route was tried
without naming the document, and those are falsifiable. The stricter rule drops 50.

**To run after the reset:** `--plant`, then apply, then rebuild, then verify served, then
disclose. In that order.

## Ruling 3 — SPIRE scope, HELD for Mahmood

- **6 trials** (current): the lipid-lowering studies only. Consistent with the review's stated
  question; the two trials whose protocols we hold stay out.
- **8 trials**: adds SPIRE-1 `NCT01975376` and SPIRE-2 `NCT01975389`, the cardiovascular
  outcomes trials. **Their protocols are the only ones we hold** (168pp and 167pp, staged), so
  D5 becomes answerable for them — but they answer a different question (events, not lipids),
  which is exactly why it is a scoping call and not ours.
