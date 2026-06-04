# Cross-app NCT-identity audit — findings

Detector: `scripts/cross_app_nct_name_check.py`. Flags NCTs carrying materially
different trial NAMES across apps (after dropping NCT-literal placeholders and
substring/dose aliases), and marks each record LIVE vs NULLED.

## Severity (important)

These are **wrong NCT *labels* on otherwise-correct trial records** — NOT
corrupted meta-analyses. Each app holds ONE record per NCT with the correct
value+name for the trial it represents; the only error is the NCT identifier,
which collides with a different trial's NCT in another app. No single app
double-counts a trial, so **pooled MA results are unaffected**. Fixing improves
registration-identifier accuracy (the "as good as published MA" goal), but is
metadata cleanup, not a results correction.

## Counts (run 2026-06-04)

- 169 NCTs with >1 distinct name → 59 after dropping alias/placeholder noise.
- **45 LIVE-vs-LIVE** (both names are non-NULLED records in their apps).
- ~14 already-NULLED/inert (one side excluded by a prior audit — metadata only).

## Verified true identities (PubMed) — examples

| NCT | True trial (verified) | Misplaced record (wrong NCT label) |
|---|---|---|
| NCT04557098 | MajesTEC-1, teclistamab (35661166) | "MIRAGE" prostate SBRT (real NCT04384770) |
| NCT02867709 | ACHIEVE II, ubrogepant (33241721) | "SAMURAI" lasmiditan |
| NCT00316524 | MVA-BN smallpox/mpox vaccine (36408618) | "BAT" bronchiectasis (real NCT00415350) |
| NCT02696785 | COAST-V, ixekizumab raxSpA (39004432) | "MEASURE 4" secukinumab; "COAST-W" |

## Fixed this round (2, both NULLED records, verified NCTs)

- SBRT_PROSTATE_LOCAL_NMA: MIRAGE key NCT04557098 → **NCT04384770**
  (Kishan, JAMA Oncol 2023, 10.1001/jamaoncol.2022.6558).
- BRONCHIECTASIS_BROAD_NMA: BAT key NCT00316524 → **NCT00415350**
  (Altenburg BAT trial; NCT in 10.1016/j.rmed.2021.106718).

## Remaining (~57) — recommended approach

Each needs the named trial's true NCT looked up (PubMed/CT.gov) and the NCT key
corrected (label-map + realData, 2 spots; keep NULLED prefix if inert). This is a
dedicated batched effort (~50-60 per-trial lookups). Full triage list:
`outputs/nct_name_conflicts.txt`. Notable swaps to fix: EMERGE/ENGAGE
(aducanumab, NCT02477800/NCT02484547 mirror-swapped), ADVANCE/MOTIVATE
(risankizumab), ASTRAL-1/ASTRAL-3 (NCT02201940/NCT02201953 swapped), BE-MOBILE-1/2,
ELEVATE-UC-12/52, IMpower130/150, BLISS-52/76.
