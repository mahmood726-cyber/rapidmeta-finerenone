# Defect Class Register

Opened 2026-09-02. **Committed before any fix in this lane, so it cannot be trimmed to
match what was achieved.** Rows are added when a class is identified, never removed when
one turns out to be hard. A register that hides its own gaps is the overclaiming we audit
others for.

Every claim below is marked **MEASURED** (a command was run and its output is committed
under `scripts/baselines/`), **INFERRED** (follows from code read, not executed), or
**CLAIMED** (asserted by a review or by this document, not yet checked).

## The denominator every blast-radius column uses

MEASURED, `scripts/measure_defect_classes.py`, output `scripts/baselines/defect_class_baseline.json`:

| population | n | is it the served surface? |
|---|---:|---|
| all HTML deployed by the Pages workflow | 2228 | published, reachable by URL |
| **root-level `*.html`** | **1464** | **yes -- this is the denominator** |
| `out/` | 190 | adjudication + withdrawal artefacts, not reader pages |
| `outputs/` | 327 | of which **319 are `*backup*`: ARCHIVE** |
| other subdirectories | 247 | not reader pages |

1464 + 190 + 327 + 247 = 2228. The archive files are named and excluded rather than
silently dropped: a control or an archive is a third kind of item, neither data nor
defect, and every count has to decide which of the three each item is.

Of the 1464 served pages, **19 carry the page-standard property table**. A further 123
copies of that table exist under `out/` and `outputs/*backup*` and are NOT served; an
earlier version of this measurement globbed those in and would have reported a
142-page population for a 19-page surface.

## SCREEN is not CONFIRMED

A **screen** count is an upper bound from string co-occurrence on one page. It is not a
finding, because two strings on one page do not establish that they describe the same
outcome. The screens written for this register were measured to be over-inclusive in the
worst direction: the first `not drawn` screen returned **151 pages**, and its hits were
`GOSH plot -- not drawn at this k`, which is a **correct refusal**. Screens are promoted
to confirmed only by a predicate that reads the same object twice.

## Register

Status: `OPEN` = identified, not fixed. `FIXED` = emitter changed, gate landed, negative
test fired before the fix. `PARTIAL` = some instances fixed, remainder named.
`NOT FIXED` = deliberately not attempted this lane, with the reason stated.

### A -- SOURCE HIERARCHY

One rule dissolves five classes: PRIMARY PUBLICATION -> SUPPLEMENT / SAP / PROTOCOL ->
REGISTRY. Today the registry is privileged so hard that a fully published RCT is dropped
because its registry entry has no results section.

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| A1 | `hasResults=False` read as "no results exist" rather than "the registry has posted nothing" | registry consumers; disposition text in topic objects | OPEN | -- | -- | 4 pages CLAIMED (APROPOS, AVERT, STEP-HFpEF DM); not yet MEASURED | 2026-09-02 |
| A2 | An effect carries its endpoint NAME but not its ANALYSIS VARIANT (observed-case / imputed / washout / adjusted) | extraction cell schema; `ssot/build_to_standard.py` P5 | OPEN | -- | -- | inclisiran ORION-11 CLAIMED: 3 values for one endpoint (-53.5 observed / -47.8 washout / -49.9 published imputation); mixed variants manufactured I2=74%, harmonised tau2=0 | 2026-09-02 |
| A3 | A reference that is a REGISTRATION is rendered as though it were a PUBLICATION | reference projector | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| A4 | Blinded-adjudication facts missed because only registry fields were read | registry-only extraction path | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| A5 | Impossible reconstruction survives because no source outranks the registry (AMPLIFY `61/76`) | reconstruction path | OPEN | -- | -- | 1 page CLAIMED | 2026-09-02 |

### B -- THE PASSWORD

A marker satisfiable by assertion is a password. Until this is fixed every other green we
hold is unaudited, including the gates written in this lane.

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| B1 | A `P*` property is ASSERTED `HELD` with a reason string describing what ought to be true, computed from nothing that could contradict it | `ssot/build_to_standard.py:785` (P1), `:807` (P2), `:817` (P3), `:867` (P4), `:918` (P5) | OPEN | -- | -- | **MEASURED: 15 contradictions on 13 of the 19 served pages carrying the table (68%)** -- P1 7, P5 6, P3 2 | 2026-09-02 |

### D -- DENOMINATORS

Five sightings, one family. Randomised, ITT, imputed-ITT and observed-value must be FOUR
SEPARATE FIELDS, and an unknown must render as unknown, never as 0.

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| D1 | "Randomised" holds an ANALYSIS denominator | topic object arm counts | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| D2 | Summary-of-findings prints the TOPIC total instead of the outcome's contributing n (Cochrane ch.14) | `ssot/sof_projector.py` | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| D3 | A pairwise `n` equals a MULTI-ARM trial total | pairwise contrast construction | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| D4 | "Analysed" holds ITT totals despite missingness | extraction | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| D5 | A missing denominator is FILLED IN WITH A ZERO ("Surfaced records not yet screened: 0" against 1,191 candidates) | PRISMA/remainder projector | OPEN | -- | -- | **SCREEN: 12 served pages** render a `not yet screened ... 0`; confirmation requires reading the candidate pool for each | 2026-09-02 |

### S -- SEARCH AND SCREENING ACCOUNTING

`scripts/registry_adapter.py` (landed, on `origin/main`) already writes an executed search
record and a screening ledger whose length is the denominator. The pages must be WIRED TO
IT, not given a second one.

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| S1 | PRISMA triples do not reconcile, and two renderings of the same flow disagree | PRISMA projector | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| S2 | `searchLog` fields empty | page data blocks | OPEN | -- | -- | 869 of 887 CLAIMED; not yet MEASURED on served bytes | 2026-09-02 |
| S3 | A trial that IS pooled is logged `ELIGIBLE_POOLABLE_NOT_INCLUDED` | screening ledger writer | OPEN | -- | -- | **SCREEN: 6 served pages** carry the label; confirmation requires intersecting with the pooled set | 2026-09-02 |
| S4 | `remainder = 0` while records are `NEEDS_ADJUDICATION` | remainder computation | OPEN | -- | -- | see D5 screen (12) | 2026-09-02 |
| S5 | A stated trial count contradicts the actual `k` ("named two-trial programme") | prose projector | OPEN | -- | -- | 3 pages CLAIMED | 2026-09-02 |

### C -- CONTRADICTORY / STALE SURFACES

These are ONE SHAPE: two surfaces rendered from different sources with nothing asserting
they agree. Fix the shape, not the instances.

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| C1 | Certainty simultaneously "pending" and "very LOW" | GRADE projector | OPEN | -- | -- | not yet CONFIRMED; page-level co-occurrence screen was over-inclusive and is withdrawn | 2026-09-02 |
| C2 | "not drawn" beside a figure caption for THAT figure | figure projector | OPEN | -- | -- | 3 pages CLAIMED. **A page-level screen returns 151 and is WRONG** -- those are correct small-k refusals | 2026-09-02 |
| C3 | Relative-effect boilerplate on an ABSOLUTE mean-difference outcome | effect-sentence projector | OPEN | -- | -- | 2 pages CLAIMED | 2026-09-02 |
| C4 | `NOT READY` beside `Publishable: True` | readiness projector vs precondition verdict | OPEN | -- | -- | not yet CONFIRMED | 2026-09-02 |
| C5 | tau2 / I2 / Q reported beside "no model was run" | heterogeneity projector | OPEN | -- | -- | not yet CONFIRMED | 2026-09-02 |
| C6 | RoB "assessors disagree" beside 15/15 agreement | RoB projector | OPEN | -- | -- | **SCREEN: 1 served page** carries the wording | 2026-09-02 |

### M -- METHOD AND JUDGEMENT

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| M1 | RoB domain-5 downgrade whose stated reason names a decision THE REVIEW made, not the trial | `ssot/rob2_algorithm.py` | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| M2 | GRADE indirectness downgrade whose stated reason names a review decision | `ssot/indirectness_procedure.py` | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| M3 | Imprecision downgraded on STUDY COUNT rather than on the interval | `ssot/grade_engine.py` | OPEN | -- | -- | screen returned 0; pattern UNPROVEN, so this is NOT_FOUND, not ABSENT | 2026-09-02 |
| M4 | A confounded two-factor change attributed to one factor | analysis narrative | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| M5 | Multi-arm contrasts sharing ONE control pooled as independent (off-diagonal covariance is tau2/2) | pooling path | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |
| M6 | Eligibility gated on whether the OUTCOME was reported | screening rules | OPEN | -- | -- | not yet MEASURED | 2026-09-02 |

### X -- REFUSAL REASONS

A refusal is a claim and its REASON is part of the claim. Audit every refusal reason in
the generator, not just the refusal.

| id | class | emitter | status | gate | negative test | blast radius (served) | date |
|---|---|---|---|---|---|---|---|
| X1 | IV-iron declines to pool a win ratio for three mathematically false reasons (compares pairs / opposite direction / 99% CI). The one TRUE reason -- k=1 -- is present but not load-bearing | `ssot/iv-iron-hf/iv-iron-hf.json` `.outcomes[4].estimand.case_definition` | OPEN | -- | -- | 1 page MEASURED (string located) | 2026-09-02 |

## What this register does not yet contain

- **Detection.** A sibling lane owns the oracle-free detection suite. This lane owns
  emitters, fixes and gates, and consumes that lane's detectors. No detector is built here.
- **Confirmed blast radius for 19 of the 29 rows.** Those rows say "not yet MEASURED"
  rather than carrying a screen count dressed as a finding.
