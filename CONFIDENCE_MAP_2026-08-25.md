# Confidence map — 2026-08-25

**Written because a lot of numbers were relayed this week and several of them moved.** Where
the confidence actually sits is now more useful than another fix. Everything below names its
source and how it was established; where a number changed, the earlier value is shown beside
it, because a retracted number is part of the record and not an embarrassment to tidy away.

Deadline is the 28th. From here the bar for any change is that **a reader would be misled
without it**.

---

## 1. Numbers relayed that later moved

These were passed to Mahmood before they settled. All three moved *downward*, and in every
case the corpus was unchanged — the instrument was wrong.

### Trial identity: 160 → 65 → 19

| reading | count | what was actually wrong |
|---|---|---|
| first | 160 records, 84 pages | the combination rule rejected any combination containing the drug — wrong in **9 of 12** cases; `sacubitril` vs `Sacubitril/valsartan` is ARNI's own drug |
| second | 65 records, 43 pages | "no arm name matches" returned NOT STUDIED; arm names are **paraphrases** (`Procedure: Radiofrequency ablation` vs `catheter ablation`) |
| **final** | **19 records, 16 pages** | placebo arms are **named after the drug they mimic** (`Placebo (for alirocumab)`), so a double-dummy trial shows the drug in every arm; and the registry arm-**type** label is unreliable |

Two of the three reductions were caught only because a **proportion looked implausible** —
more than half the corpus, then 6 of 6 alirocumab trials called background therapy in the
alirocumab programme. Each intermediate number was a defensible-looking result from a
controlled instrument.

### Remedy scope: 29 → 43 → 16, retracted twice

| relayed | basis | status |
|---|---|---|
| 29 pages | the model sweep's own verdicts | superseded — sweep labels are unverified claims, and at least one (RAMBLE) is wrong |
| 43 pages | registry-derived, before the placebo and label fixes | **retracted** |
| **16 pages** | registry arm structure, placebo-aware, label-independent | current |

I reported the *growth* to 43 as a real finding. It was not. The 16 is the number that has
survived every check applied to it so far.

### Paper Studio quality: the four-of-149 denominator

The panel's "1 of 50 full manuscripts cleared an editor" rested on **one draw**. Replicated
across 3 published anchors × 2 personas × 2 families × both orderings (24 jobs), ARNI came
back **DESK-REJECT 10 of 12**, and 4 of 4 against the anchor it had "beaten". Eleven of twelve
editor cells were position-dependent.

**Any single page verdict is one draw with roughly a 1-in-6 chance of flipping on family
alone.** The aggregate over 149 pages stands; per-page verdicts are anecdotes.

---

## 2. What is verified, and how

| claim | number | how it was established | strength |
|---|---|---|---|
| trials that are background therapy in every arm | 19 records, 16 pages | registered arm structure, ClinicalTrials.gov API v2, 348 of 349 NCTs fetched | **strong** — needs no arm-type label, and every one has a positive reason |
| mismatched trials reaching a published pooled estimate | **0** | contributor check over pages that publish pools; controlled (8 of 8 pooling pages found their real contributors) | **strong** — the control proves the zero is a measurement, not blindness |
| abstract claiming a search the object says never ran | 3 → **0** | object `query_as_executed` vs abstract prose; controlled both directions | **strong**, verified on delivered pages |
| agreement statistic over a pool the page does not present | 15 → **0** | positive control is a real page in git history at a named pre-fix SHA | **strong** |
| GRADE certainty stated over "0 pooled outcomes rated" | 13 → **0** | object `grade.by_outcome` vs abstract | **strong** |
| the I² fix moved a reader | 6 of 6 attributable verdicts flipped MISLEADING → SAFE; 9 of 9 already-safe pages unchanged | panel round 2, both families, 184 jobs | **moderate** — verdicts are model output, but the *direction* is consistent and the negative control held |
| corpus panel aggregate rates | student SAFE 74.5%, editor REVIEW 2.7%, over 149 pages | 298 of 298 jobs, 0 failures, blind comparator, order alternated | **moderate** — cross-family agreement 83% (34 of 41), disagreements symmetric |
| registry-first search recall | 97.3% (73 of 75) | prior measurement, both misses development code names | **moderate**, not re-verified this week |
| the control-char guard can actually block | refused a planted tracked probe; passed after removal | negative control run both directions | **strong** |

---

## 3. What is unverified, and why

| item | scale | why it is not settled |
|---|---|---|
| **trial identity, undecidable** | **113 records on 55 pages** | 94 because arm names are paraphrases; 19 because the drug sits outside the experimental arm and the arm-type label is demonstrably unreliable. **Not a pass.** The pages now say so in those words. |
| — of which, defective topic patterns | 32 records, 10 pages | `TOPICS` supplies `intravenous`, `inhibitors`, `multiple`, `injectable`, `intensive` as drug patterns. No synonym helps; five defective strings. |
| — of which, development-code paraphrases | ~12 records | `sacubitril`→`LCZ696`, `netarsudil`→`AR-13324`, `bezlotoxumab`→`MK-3415`. `DRUG_SYNS` exists with **5 entries and none of these**. |
| — long tail | ~50 records | genuine vocabulary variety. Should stay undecidable rather than become model-asserted. |
| the matcher itself | — | `add_topic_autodiscover.py` reads an AACT snapshot; `AACT_DIR` unset, `~/AACT` absent. The identity **rule** is fixed and validated on 9 registry-checked cases; the matcher **cannot be re-run here**. |
| the sweep's 42 role labels | — | superseded. RAMBLE proves them unreliable. No remedy was written from them. |
| CLAIMS_DEFECT | — | permanently UNVERIFIED; the harvester never verifies its own inputs. |
| uncontrolled checks | ~55 of ~177 by the earlier count | not re-measured since; the denominator itself drifted between measurements and should be re-derived before quoting. |
| specialist's two clinical objections | 2 | open, and Mahmood's to settle: urgent HF visit vs hospitalisation, DELIVER exclusion. |

---

## 4. What the corpus actually contains

Stated plainly because "149 Paper Studio pages" has never meant 149 papers:

| | pages |
|---|---|
| a pooled synthesis written up | **22** |
| a long argument for why this topic does not pool | 28 |
| a short note — one trial, or no results at all | 99 |

69 objects hold no result on any outcome; 21 hold exactly one trial. **90 of 149 topics
cannot support a meta-analysis, and the pages say so.**

---

## 5. The one thing worth knowing before changing anything

**The poolability gate is providing accidental protection against the matcher.** It rejects on
endpoint and contrast identity, and a trial set containing a wrong drug rarely survives that —
which is why 0 of the mismatches reached a published estimate. That protection is not by
design, is not documented anywhere else, and **any future loosening of endpoint or contrast
identity removes it**. Run the identity check and require it clean before relaxing poolability.

---

## 6. Instrument failures this week: 9 caught, 0 shipped

Every one was mine, and eight were caught by a control. The ninth was a commit message —
prose is the only artefact with no verification, which is why counts now carry their source.

The pattern is stable enough to state: **when a count changes after a fix, the first
hypothesis is that the instrument moved, not the corpus.** Over-flagging is not the safe
direction; a manufactured defect class costs the same review time as a real one and sends the
fix to the wrong layer.
