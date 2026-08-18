# The page standard, versioned

**`PAGE_STANDARD_VERSION = "1.0.0-2026-08-19"`**

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
