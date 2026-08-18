# The page standard, versioned

**`PAGE_STANDARD_VERSION = "1.1.0-2026-08-19"`**

Until tonight this standard existed only as practice and as one exemplary object
(`arni-hfref`). It had **no version marker anywhere in the repo** — `grep` for `build_stamp`
or `standard_version` across every object returns nothing, ARNI included. That is the gap
this file closes, and it closes it in the direction the ratchet requires: a page records the
standard version it was built to, so a page built to v1 while the standard is v3 is
**honestly labelled rather than silently stale**.

**No page is grandfathered, `arni-hfref` included.** ARNI is presently unstamped and is
therefore *unknown-version*, not *compliant*. That is a fact about the register, not a
criticism of the page.

---

## The properties

A page meets the standard when **every property below is either HELD or REFUSING WITH A
STATED REASON ON THE PAGE**. A refusal is a complete outcome. A blank is not.

| # | property | held means |
|---|---|---|
| P1 | **Executed search** | query string verbatim, date, records returned, per database; PRISMA counts that reconcile arithmetically |
| P2 | **k cascade** | k reported at every stage, never as a single number |
| P3 | **Inclusion criteria** | a criteria block carrying `predefined:` on its face |
| P4 | **Preconditions** | every precondition with its verdict and its cited authority |
| P5 | **Extraction table** | verbatim source sentence per cell, resolvable link, and each cell labelled READ or DERIVED |
| P6 | **Analysis output verbatim** | the model call, estimate with CI, heterogeneity and package version, quoted. **If there is no quotable output, the absence is recorded as a finding** |
| P7 | **Published-meta comparison** | with a denominator, present in BOTH the page and the Word manuscript, charts aligned |
| P8 | **Registration identity** | every trial keyed to a registration id verified against the registry |
| P9 | **Build stamp** | naming this standard version |
| P10 | **Served-bytes verification** | the property is confirmed in bytes served over HTTP, not in a source file and not by an exit code |
| P11 | **Coded field governs** | where the object holds BOTH a coded field and a free-text label for the same thing, the verdict is taken from the CODE; the text only corroborates. Where the code is absent and the verdict falls back to text, **the verdict says so on its face** |
| P12 | **The known-answer suite ran** | the suite executed and passed in this build. An import error is a BUILD FAILURE, not a skipped test |

## The ratchet

Each topic must meet everything learned **up to the moment it is built**. The version string
is what makes staleness visible instead of silent. When a lesson is added, the version rises
and every page below it is *known* to be below it.

## What a refusal must carry

A refusing property states **which** property, **why**, and **what would change it**. "Not
applicable" is not a reason; "k=1, so there is no between-study variance to estimate" is.

Nothing is generated to fill a slot. A tab with nothing to render keeps refusing.

---

## Version log

### 1.1.0-2026-08-19
Adds P11 and P12, both from live defects on 2026-08-19.

**P11 — the coded field governs.** `comparators_identified_and_consistent` FAILed `sglt2-hf`
on `'placebo added to background heart failure therapy'` vs `'placebo'`, while
`comparator_type` read `'placebo'` on both and every control arm was labelled exactly
`placebo`. Routing through `text_match` was necessary and NOT sufficient: the strings really
are different and `text_match` was right to say so. **The error was asking a text question at
all**, when the semantic answer was recorded in the coded field beside it. This will recur
anywhere the corpus holds both a code and a label, so it is a property rather than one
assessor's fix.

**P12 — the suite ran.** The `criteria_stated` / `criteria_predefined` split was committed
without re-running `known_answer_preconditions.py`, which had been erroring on import since
the rename. It was "verified" by running the batch assessment and reading the matrix — which
is checking VERDICTS, not REASONING, for the third time in one night, and done to the suite
whose entire job is to catch that. **A green matrix is not evidence the suite ran.**

### 1.0.0-2026-08-19
First versioned statement. Encodes the lessons established through 2026-08-19:

- absent / empty / unreadable input is NOT_ASSESSABLE, never FAIL
- an instrument asserts the shape of its input and **raises** rather than returning a verdict
- a cross-instrument disagreement is evidence about the instruments only if both were asked
  the same question
- the known answer must come from the data, never from a fixture the author invented
- an object's record of what it EXCLUDED is not what it INCLUDED
- a Handbook section cited from memory is a registration number cited from memory
- a correct verdict reached by broken reasoning passes every outcome-based test; verdict and
  reason are two outputs and both need testing
- defects can run toward noise as well as toward silence — a check that fires on most of the
  corpus is more likely broken than the corpus is
