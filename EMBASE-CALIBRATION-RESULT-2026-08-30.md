# Embase calibration: what a subscription database adds to a free-source search

**Topic:** dapivirine vaginal ring for HIV-1 prevention in women (`agyw-hiv-prep-review`).
**Run:** Ovid Embase, executed by Mahmood 2026-08-30, exported as RIS and handed over.
**Purpose:** measure, once, what our free-source-only search misses. Embase is a *ruler
here, never a source* — it is unavailable in Laos and Uganda, and a method that depends on
a subscription cannot be reproduced by the reader it is for.

---

## THE SENTENCE THIS WAS FOR

> **This search uses only sources freely available worldwide. Measured against a
> subscription database, it recovered 2 of 2 eligible trials.**

---

## 1. THE EXPORT WAS VERIFIED BEFORE ANYTHING WAS COUNTED

| check | result |
|---|---|
| record count | **1,044 `TY` starts, 1,044 `ER` terminators — matches Ovid's 1,044 exactly.** Not truncated. |
| format | Abstracts 927/1044 (89%), Emtree 1044/1044 (100%) → **Complete Reference**. |
| registry numbers | ⚠️ `RN` present in **0/1044**. Ovid's RIS carries no structured registry field. |
| Human limit | **NOT applied** — 451 records carry animal/nonhuman Emtree terms. Filtered on our side. |

⚠️ **The `RN` finding changes the method, not just a footnote.** Absent registry numbers
would normally mean the default `Citation` format, but abstracts and Emtree are both
present, so this *is* Complete Reference — Ovid's RIS simply has no tag for registry
numbers. **Trial matching therefore had to come from NCT strings in free text.**

⭐ **AND THAT IS WHY THE SCREEN COULD NOT STOP AT NCTs.** 62 distinct NCTs appear in the
file. The Ring Study's own primary report — *Safety and efficacy of a dapivirine vaginal
ring for HIV prevention in women*, N Engl J Med 2016, n=1,959, South Africa and Uganda —
**carries no NCT at all**. An NCT-only match would have missed one of the two trials the
review is built on, while reporting a clean result.

## 2. THE PREDICTION, SCORED AS WRITTEN

Logged **before** the run, both halves:

| half | predicted | observed | verdict |
|---|---|---|---|
| eligible trials | **2 of 2, 100%, ZERO additional** | 2 of 2, zero Embase-only eligible trials | **CONFIRMED** |
| record count | **300–700** | **1,044** | ⛔ **MISSED — 49% above the upper bound** |

⛔ **The miss is reported in the same breath as the confirmation, and it is the half that
should temper the other.** The eligibility prediction was falsifiable by a single
Embase-only eligible trial and none was found; the record-count prediction was simply
wrong, and being wrong about the size of the haystack is a reason to distrust intuitions
about what is in it. Both stand.

## 3. THE COVERAGE FRACTION

    trials named by any source            45
    retrieved by our free-source search    2
    excluded on ELIGIBILITY               43
    outside what our sources index         0
    SEARCH MISSES                          0
    ---------------------------------------
    eligible denominator                   2
    RECALL                              100% (2/2)

⚠️ **43 IS NOT A NUMBER OF MISSING TRIALS, AND SUBTRACTION IS HOW IT WOULD BECOME ONE.**
`search_coverage_fraction.py` refuses to report a recall figure while any non-retrieved
trial is unattributed, so every one of the 43 carries its specific exclusion, derived from
registry fields rather than assigned by hand: 17 have a safety or pharmacokinetic primary
outcome, 12 are open label with no placebo comparison, 6 are WITHDRAWN registrations with
0 actual enrolment, 5 are non-randomised (open-label extensions HOPE and DREAM among
them), 2 are observational, and 1 measures PrEP uptake rather than infection.

The two most tempting near-misses were settled rather than waved past:

- **IPM 009A / 009B** (`NCT01337570`, `NCT01337583`) are phase 3, randomised,
  double-masked, dapivirine ring versus placebo, with **HIV-1 seroconversion as the primary
  outcome** — eligible on every design field. Both are **WITHDRAWN with 0 actual
  enrolment**. No participants, no data, no trial.
- **MTN-023/IPM 030** in adolescents is randomised, double-blind and placebo-controlled,
  and is **phase IIa with a safety primary outcome**.

## 4. WHAT THIS RESULT IS NOT

⚠️ **THE SCREEN WAS MECHANICAL, NOT BLINDED, AND I KNEW THE ANSWER.** The eligibility
rules are registry fields — study type, allocation, masking, primary-outcome text,
recruitment status, actual enrolment — and they were applied by the same agent that knows
which two trials the review holds. That is a real weakness and it is recorded as one
rather than dropped. A second screen by an assessor blind to the included set would
strengthen this, and nothing here should be read as though that has been done.

⚠️ **THE DENOMINATOR IS TWO.** A 100% recall over two eligible trials is a weak
measurement in isolation, however clean. It says the free-source route lost nothing *on
this question*, not that it loses nothing. The claim widens only by running the same
calibration on further topics.

⚠️ **IT MEASURES RETRIEVAL, NOT THE SCREEN.** What was tested is whether free sources
surface the eligible trials. Whether our *screen* would admit them correctly is a separate
property, already qualified elsewhere: the search generalises, the screen does not.
