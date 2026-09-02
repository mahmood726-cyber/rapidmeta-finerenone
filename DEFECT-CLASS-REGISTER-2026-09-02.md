# Defect Class Register

Opened 2026-09-02, **committed before any fix in this lane** (commit `c73c4a5cd`) so it
could not be trimmed to match what was achieved. Statuses updated as work landed; rows are
never removed when a class turns out to be hard.

Every claim is marked **MEASURED** (a command was run and its output is committed under
`scripts/baselines/`), **INFERRED** (follows from code read, not executed), or **CLAIMED**
(asserted by a review or by this document, not yet checked).

## The denominator every blast-radius column uses

MEASURED, `scripts/measure_defect_classes.py`:

| population | n | is it the served surface? |
|---|---:|---|
| all HTML deployed by the Pages workflow | 2228 | published, reachable by URL |
| **root-level `*.html`** | **1464** | **yes -- this is the page denominator** |
| `out/` | 190 | adjudication + withdrawal artefacts, not reader pages |
| `outputs/` | 327 | of which **319 are `*backup*`: ARCHIVE** |
| other subdirectories | 247 | not reader pages |

1464 + 190 + 327 + 247 = 2228. Archive files are named and excluded rather than silently
dropped: an archive or a control is a third kind of item, neither data nor defect, and
every count has to decide which of the three each item is.

Two further denominators are used below, because the gates read objects, not pages:
**152 topic objects** that `ssot/PAGE_MAP.json` resolves, and **155 canonical objects**
under `ssot/`. Of the 1464 served pages, **19 carry the page-standard property table**;
18 of those resolve to an object and the 19th (`ALIROCUMAB_LIPID_SSOT.html`) is named as
unchecked rather than counted as passing.

## SCREEN is not CONFIRMED

A **screen** is an upper bound from string co-occurrence on one page. It is not a finding.
The screens written for this register were measured to be over-inclusive in the worst
direction: the first `not drawn` screen returned **151 pages** and every hit was
`GOSH plot -- not drawn at this k`, a **correct refusal**. Screens are promoted only by a
predicate that reads the same object twice.

## What this lane got wrong first, and in which direction

Recorded because an instrument with no measured error rate is an assumption wearing a
number. **Eight false findings on correct pages**, plus one silent exemption, all caught
before anything was reported:

| predicate | wrong how | cost if shipped |
|---|---|---|
| `p2_k_cascade` | treated `k4_comparator` as a filter stage; it is a sibling role bucket ("records where the topic drug is the comparator instead") | 6 correct pages refused, all at one transition |
| `p5_extraction_table` | required `derived_by`; a cell naming its method as `se = (ln(upper) - ln(lower)) / (2 x 1.959964)` was refused | 2 correct pages refused |
| structural password test | regex flagged P6/P7/P8, which sit in an `if/else` with a REFUSING branch a regex cannot see | 3 correct emitters called passwords |
| declared-skip narrowing in `audit_exclusion_by_absence.py` | a 5-line window read the NEXT guard's report as this one's | 119 baselined guards silently exempted -- caught by its own negative proof |

The first three failed the same way: **accusing correct code**. The fourth failed the
opposite way, and was caught only because its proof writes two adjacent guards and requires
the bare one to still be counted. Every gate this lane landed now carries a negative
control, and those controls are the cases these predicates wrongly judged.

## Register

`FIXED` = emitter changed, gate landed, negative test fired before the fix.
`PARTIAL` = the machinery is fixed and gated; existing instances are measured and NOT
repaired, because no page is regenerated in this lane. `NOT FIXED` = not attempted, reason
stated.

### A -- SOURCE HIERARCHY  (commit `8bac179f2`)

`ssot/provenance_tier.py` ranked `REGISTRY_POSTED_RESULT` above `JOURNAL_FULL_TEXT`. The
order is now split by QUESTION: **PRIMARY PUBLICATION -> SUPPLEMENT -> SAP -> PROTOCOL ->
REGISTRY** for a value, registry first for pre-specification, because its
deposited-under-duty argument is correct for that question and wrong for the other.
`TIERS[t]["rank"]` is left untouched -- nothing outside the module indexes it, and silently
redefining a published number is the substitution class this project audits for.

The negative test fires against the parent commit (3 FAIL / 3 PASS) and does not cheat by
looking for new names: it asks the module for its ordering the way a caller would, falling
back to `rank`, which is all the old module had.

| id | class | emitter | status | gate | negative test | blast radius | date |
|---|---|---|---|---|---|---|---|
| A1 | `hasResults=False` read as "no results exist" | `ssot/provenance_tier.py::registry_silence_problems` | PARTIAL | `source_hierarchy_gate.py` | `test_source_hierarchy_refuses.py` | **MEASURED: 2 dispositions on 1 of 152 topics.** The 4 CLAIMED pages (APROPOS, AVERT, STEP-HFpEF DM) are NOT among them and were not verified | 2026-09-02 |
| A2 | An effect carries its endpoint NAME but not its ANALYSIS VARIANT | effect schema | PARTIAL | `source_hierarchy_gate.py` | same | **MEASURED: 610 stored points on 51 topics declare no variant; ZERO declare one.** So "0 pools mix variants" is NOT_FOUND, not ABSENT -- the check has nothing to compare, which is exactly how inclisiran's I2=74% stayed invisible | 2026-09-02 |
| A3 | A reference that is a REGISTRATION rendered as a PUBLICATION | reference projector | NOT FIXED | -- | -- | not measured. The `REGISTRY_REFERENCE_ROW` tier exists with `never_counts_as_evidence`; whether the projector honours it was not checked | 2026-09-02 |
| A4 | Blinded-adjudication facts missed because only registry fields were read | registry-only extraction path | NOT FIXED | -- | -- | not measured | 2026-09-02 |
| A5 | AMPLIFY `61/76` impossible reconstruction | reconstruction path | NOT FIXED | -- | -- | 1 page CLAIMED, not reproduced | 2026-09-02 |

### B -- THE PASSWORD  (commit `85b47a449`)

| id | class | emitter | status | gate | negative test | blast radius | date |
|---|---|---|---|---|---|---|---|
| B1 | A `P*` property ASSERTED `HELD` with a reason describing what ought to be true | `ssot/build_to_standard.py` -> now `ssot/page_properties.py` | **FIXED** | `property_recompute_gate.py` | `test_properties_can_refuse.py` -- **fires against the parent commit: P1, P2, P4 and P5 are only ever assigned HELD** | **MEASURED: 11 flips on 10 of the 18 served pages whose object resolves** (P1 7, P3 2, P5 2). P2 and P4 had no branch either, but their objects do not contradict them | 2026-09-02 |

### D -- DENOMINATORS  (commit `83da17936`)

| id | class | emitter | status | gate | negative test | blast radius | date |
|---|---|---|---|---|---|---|---|
| D1 | "Randomised" holds an ANALYSIS denominator | page/object axis labelling | PARTIAL | `denominator_axis_gate.py`, positive control a page printing the ANALYSED total under "randomised" | control pair in-gate | **MEASURED: 1 FAIL (`ARNI_HF_REVIEW`) of 1464. 2 pages carry no object path and 2 have no derivable axis -- all four NAMED, none reads PASS** | 2026-09-02 |
| D2 | SoF prints the TOPIC total instead of the outcome's contributing n | `ssot/sof_projector.py` | NOT FIXED | -- | -- | not measured; the gate reads the randomised/analysed axis, not the SoF column | 2026-09-02 |
| D3 | A pairwise `n` equals a MULTI-ARM trial total | pairwise contrast construction | NOT FIXED | -- | -- | not measured | 2026-09-02 |
| D4 | "Analysed" holds ITT totals despite missingness | extraction | PARTIAL | `denominator_axis_gate.py` | same | covered by the same axis check; no separate count | 2026-09-02 |
| D5 | A missing denominator FILLED IN WITH A ZERO | PRISMA/remainder projector | NOT FIXED | -- | -- | **SCREEN: 12 served pages**; not confirmed against each candidate pool | 2026-09-02 |

### S -- SEARCH AND SCREENING ACCOUNTING

**Nothing in this family was fixed.** `scripts/registry_adapter.py` is on `origin/main` and
already writes an executed search record and a screening ledger whose length is the
denominator; the pages are still not wired to it. That wiring is a generator change with a
rendering consequence, and this lane regenerates nothing.

| id | class | status | blast radius | date |
|---|---|---|---|---|
| S1 | PRISMA triples do not reconcile; two renderings disagree | NOT FIXED | not measured | 2026-09-02 |
| S2 | `searchLog` fields empty | NOT FIXED | 869 of 887 CLAIMED, not verified on served bytes | 2026-09-02 |
| S3 | A pooled trial logged `ELIGIBLE_POOLABLE_NOT_INCLUDED` | NOT FIXED | **SCREEN: 6 served pages** carry the label; not intersected with the pooled set | 2026-09-02 |
| S4 | `remainder = 0` while records are `NEEDS_ADJUDICATION` | NOT FIXED | see D5 | 2026-09-02 |
| S5 | A stated trial count contradicts the actual `k` | NOT FIXED | 3 pages CLAIMED | 2026-09-02 |

### C -- CONTRADICTORY / STALE SURFACES  (commit `83da17936`)

These are ONE SHAPE: two surfaces from different sources with nothing asserting they agree.
The gate attacks the shape; the individual instances below were not separately confirmed.

| id | class | status | gate | blast radius | date |
|---|---|---|---|---|---|
| C-shape | Two surfaces rendered from different sources with nothing asserting they agree | PARTIAL | `contradicting_surfaces_gate.py` | **MEASURED: 1 FAIL of 155 objects** -- arni-hfref pools a trial the same object records as excluded. 61 PASS, 1 unjudgeable, 92 not applicable | 2026-09-02 |
| C1 | Certainty simultaneously "pending" and "very LOW" | NOT FIXED | -- | not confirmed; the page-level screen was over-inclusive and is withdrawn | 2026-09-02 |
| C2 | "not drawn" beside a figure caption for THAT figure | NOT FIXED | -- | 3 pages CLAIMED. **A page-level screen returns 151 and is WRONG** -- those are protected small-k refusals | 2026-09-02 |
| C3 | Relative-effect boilerplate on an ABSOLUTE MD outcome | NOT FIXED | -- | 2 pages CLAIMED | 2026-09-02 |
| C4 | `NOT READY` beside `Publishable: True` | NOT FIXED | -- | not confirmed | 2026-09-02 |
| C5 | tau2 / I2 / Q beside "no model was run" | NOT FIXED | -- | not confirmed | 2026-09-02 |
| C6 | RoB "assessors disagree" beside 15/15 agreement | NOT FIXED | -- | **SCREEN: 1 served page** | 2026-09-02 |

### M -- METHOD AND JUDGEMENT  (commit `83da17936`)

| id | class | status | gate | blast radius | date |
|---|---|---|---|---|---|
| M-label | A method LABEL naming an analysis the numbers were not produced by | PARTIAL | `method_label_gate.py`; its positive control is a prediction interval computed with a NORMAL quantile and labelled t on k-1 -- at k=2 that is 1.96 against 12.706 | **MEASURED: 3 FAIL of 155** (arni-hfref, bococizumab-lipid, incretin-hfpef); 49 PASS, 2 unjudgeable, 101 not applicable | 2026-09-02 |
| M-derived | A derived value that is a SNAPSHOT of superseded operands | PARTIAL | `derived_recompute_gate.py` | **MEASURED: 2 FAIL of 155.** Concretely: bococizumab records 5 leave-one-out rows each claiming k=4; omitting one trial from 6 leaves 5. 132 objects declare no derivation at all | 2026-09-02 |
| M1 | RoB domain-5 downgrade whose reason names a decision THE REVIEW made | NOT FIXED | -- | not measured | 2026-09-02 |
| M2 | GRADE indirectness downgrade naming a review decision | NOT FIXED | -- | not measured | 2026-09-02 |
| M3 | Imprecision downgraded on STUDY COUNT | NOT FIXED | -- | screen returned 0 from an UNPROVEN pattern, so NOT_FOUND, not ABSENT | 2026-09-02 |
| M4 | A confounded two-factor change attributed to one factor | NOT FIXED | -- | not measured | 2026-09-02 |
| M5 | Multi-arm contrasts sharing one control pooled as independent | NOT FIXED | -- | not measured. The off-diagonal covariance is tau2/2 | 2026-09-02 |
| M6 | Eligibility gated on whether the OUTCOME was reported | NOT FIXED | -- | not measured | 2026-09-02 |

### X -- REFUSAL REASONS  (commit `83da17936`)

| id | class | emitter | status | gate | negative test | blast radius | date |
|---|---|---|---|---|---|---|---|
| X1 | A refusal defended by grounds that do not hold | topic objects' stored reasons | PARTIAL | `refusal_reason_gate.py` | its two controls are the SAME SENTENCE under two edits: strip the `k=1` clause and the identical wording must be flagged | **MEASURED: 17 non-pooling reasons read across 152 objects. 0 rest ONLY on invalid grounds. 1 states three of them beside a valid one -- reported, never failed** | 2026-09-02 |

**A correction to the framing this lane was given.** iv-iron-hf's win-ratio refusal names
FOUR grounds, not three. Three do not survive the arithmetic -- the unit being a pair
(log(WR) pools by inverse variance like log(HR)); the direction being inverted (a sign
convention, so negate the log); a 99% interval (`se = (ln(u) - ln(l)) / (2 x 2.5758)`).
The fourth, in the same sentence, is that **a single trial reports it**, and k=1 is a
complete reason. So the refusal is SOUND and is protected, and the gate reports the
sentence rather than failing it: a reader who carries "opposite direction means unpoolable"
to the next review will exclude something poolable, but failing on it would push authors
toward thinner reasons, which is the worse defect.

## What was NOT fixed, gathered in one place

- **19 of the 29 classes are `NOT FIXED`**: A3, A4, A5, D2, D3, D5, S1-S5, C1-C6, M1-M6.
- **No page is regenerated and no stored value is repaired.** Every FAIL above sits in a
  baseline. `arni-hfref` appears in FOUR of the five object gates and is left there.
- **No effect is back-filled with its analysis variant**, so A2's 610 stand. That needs
  sources re-read, not a code change.
- **No trial dropped on registry silence is reinstated.**
- **The pages are not wired to `registry_adapter.py`**, so the whole S family stands.
- **Detection is not built here.** A sibling lane owns the oracle-free suite; this lane
  owns emitters, fixes and gates, and consumes theirs.
- **One instrument defect is outstanding and is not this lane's to exempt.**
  `scripts/lint_recurring_traps.py` flags `scripts/comparator_seed/phase3_measure.py:414`
  as an `unanchored_substring`. It is a FALSE POSITIVE -- `held_pmid` is a `set`, so `in`
  is membership, not a substring test -- but the value reaches that line through a
  tuple-unpacked subscript, so no sound static narrowing was available, and stamping an
  exemption on another lane's file is not this lane's call.
