# "Fix all fully" — execution log and the laws it surfaced

**Date:** 2026-09-06. Executing the seven parked decisions, ordered by harm to a reader. Report
after each item lands; disclosure/correction only, no regeneration, no bypass.

## Three laws recorded before the work continued

### 1. THE STORE KNOWING IS NOT THE READER SEEING — a correction that does not reach the rendering has not been made

Items 2 and 3 are the same law from opposite ends:

- **ARNI NNT.** The store had *withdrawn* the number needed to treat (the risk-difference interval
  crosses zero → NNT undefined; the stale operand was moved to `superseded_values_2026_09_05`).
  The served page still displayed `22.6 (16.3 to 37.2)` — a static paragraph the withdrawal never
  reached.
- **Rosuvastatin title.** The store recorded that "adults with stroke" is wrong ("stroke" is
  HOPE-3's counted *outcome*, leaked from its registry `conditions` array, not its *population*)
  and withdrew the label on 2026-08-21. The served page still served it as the title and `<h1>`.

Both are a value that is **correct in one place and wrong where a reader meets it**. A store record
of a correction is a note to ourselves; until the rendered surface changes, the reader still acts
on the wrong number. So a fix is not done when the object says so — it is done when the served
bytes say so, verified on the served bytes.

### 2. RECOMPUTING A VALUE IS NOT THE SAME AS ESTABLISHING THAT THE VALUE EXISTS

When this defect was first relayed, the summary said "22.6 recomputes to 43.4." That was wrong: no
NNT is defined at all, because the risk-difference interval crosses zero (−0.063 to +0.017). A
recomputed 43.4 would have been a **second wrong number with better arithmetic** — the same
mistake one operand-refresh later. The gate that *refused to show a value* was righter than the
fix proposed for it. Before recomputing a derived quantity, establish that the quantity is
defined; an interval that includes no effect does not have an NNT to recompute.

### 3. HAZARD (do not change the gate): the pre-push check prices a broad change at N× a deep one

The pre-push regression gate (`scripts/regression_check.py`) walks **every page the push touches**
in a headless browser — a 12-second settle window per page, serial. So marking 288 pages (item 1),
a broad-but-shallow disclosure change, costs ~70–90 minutes, the same per-page price as a deep
single-page fix paid 288 times. This is a **structural bias in the guard**: it makes the class of
change we most want to be cheap — disclosure across many pages — the most expensive, and it is the
reason a broad safety mark feels costly. Recorded as a hazard, not fixed: the gate's per-page
browser check is correct for what it verifies; the bias is inherent to walking touched pages, and
"cheapen it by skipping pages" is how a guard becomes inert. The right response is to expect the
wall-clock cost of broad marks, not to weaken the gate.

## A clean zero from an unvalidated instrument is the most dangerous result — worked example

Gate 9's first scan (does a page assert "no heterogeneity" while its own I² is high?) returned
**0 pages**. That zero was false. The pages write the statistic as **"I-squared 56.8%"**, and the
regex matched only "I²"/"I2" — so it could not see any of them, and returned a number that read
as corpus health. The defect it was meant to find was on **8 pages**, two of them the reviewers'
own fixtures (bococizumab 56.8%, inclisiran 74.1%).

It was caught only because the scan was run against cases KNOWN to be positive before its own
answer was trusted. The lesson, stated as a rule:

> **A SCAN'S ZERO IS WORTH EXACTLY WHAT ITS CONTROL IS WORTH, AND THE CONTROL MUST BE A CASE
> KNOWN TO BE POSITIVE.** An unvalidated zero is more dangerous than a wrong non-zero, because a
> non-zero gets investigated and a zero gets filed as health.

The mirror case, handled the same way: gate 23's first scan returned **151 of 167** — held back,
not reported, because a number that high is far likelier to be an over-matching parser than a
corpus that broken. Reporting it would have cost more credibility than it bought. Both directions
of the rule: a suspicious zero and a suspicious near-total both mean *validate the instrument
against a known case before the number leaves the room.*

## Why the protocol-first policy closes the standing review-quality findings

Recorded because it is the reason the policy is worth its cost (per Mahmood): post-hoc eligibility
narrowing, criteria that do not reproduce their own exclusions (SGLT2_HF/SOLOIST-WHF,
IV_IRON/FAIR-HF), outcome-based eligibility, the 16 objects with no screening decision, and the 30
reviews with no protocol — every one dissolves if a review begins from a committed protocol SHA
and is rebuilt to it, with `reproduce_review.py` as the test that it was. Nine external reviews
found zero arithmetic errors and only inclusion/extraction/estimand/provenance defects, which is
exactly the class a protocol-first, gate-checked loop makes structurally hard.

## A review finds an instance; a gate finds the class — 5 → 91

The `hasResults=false` defect (a fact about ClinicalTrials.gov mistaken for a fact about the trial)
was found **five times** by external reviewers reading pages (ANSWER-HF, Mokadem, APROPOS, AVERT,
and the class "fixed" once weeks ago). `gate53_hasresults_not_publication.py` — one detector,
validated against three of those as controls — found it **91 times**. That 5 → 91 ratio is the
argument for the whole re-scope: the deliverable is not 22 page repairs, it is the gates, because a
review finds an instance and a gate finds the class. (Over-match caught first: a naive node-walk
flagged 1356 by counting every nested NCT; the per-trial-record detector is 91, and the
completed-vs-ongoing boundary is stated inline, not defended later.)

## EVERY DEFECT WE HAVE FIXED TWICE WAS FIXED THE FIRST TIME AT THE WRONG LEVEL

Three classes are now three-time repeats, and each recurred because the first fix was applied to a
**row**, not to the **rule**: the registry-primary-only outcome parser (ODYSSEY LONG TERM →
CHOICE I → PIONEER), the `hasResults` flag (ANSWER-HF → Mokadem/APROPOS/AVERT), and the stale-value
class (ARNI operand → the half-migrations). The fix that sticks is a gate on the class plus a
fixture drawn from the original instance, so a recurrence fails a test rather than waiting for the
next reviewer. That is why gate 53 ships with AVERT/APROPOS/Mokadem as controls that fail if the
class returns.

## Gate 53's outcome is a THREE-state task, not a two-state relabel

The 91 must not be bulk-relabelled `PUBLICATION_SEARCH_REQUIRED` — that is a task, not a verdict.
Each trial resolves to `PUBLISHED_RESULTS_FOUND` / `SEARCHED_NONE_FOUND` / `NOT_YET_SEARCHED`, and a
trial at `NOT_YET_SEARCHED` is an **open task on its review that must render as one** — otherwise a
silent exclusion is replaced by a silent to-do, the same defect wearing a better label.

## Codex cannot write files in this environment — delegation for artefacts is not viable here

Four `codex exec` attempts returned exit 0 with **zero artefacts**. Root cause, finally isolated:
the read-only sandbox rejects file writes ("workspace mounted read-only, approval disabled"), and
`--sandbox workspace-write` **crashes the Windows sandbox setup helper**
(`orchestrator_helper_exit_nonzero`, status 143). This matches the earlier measured lesson (two
jobs, ~90 min, zero artefacts). Conclusion: Codex is confirmed live (real model tokens) but cannot
produce file artefacts here; the central schema and every gate were therefore written in-tree. The
artefact-not-exit-code check is what caught this each time — exit 0 four times, zero files four
times.

## Item log

- **1. Mark the 291** — 288 object-less pages marked (commit `ab026ad6`), disclosure only,
  instrument reconciled against the audit (severe 100 / needs-review 16 exact). Push runs the
  ~90-min gate.
- **2. ARNI NNT** — served page corrected to render the refusal (RD interval crosses zero), stale
  `22.6` removed; object already fixed at root.
- **3. Rosuvastatin title** — title/`<h1>` corrected to "adults without established cardiovascular
  disease"; object `title` fixed at root.
- **4–7** — index false claims; the 30 protocol-less reviews; the IRR pre-declared sensitivity;
  the six AE-organ outcomes. (In progress.)
