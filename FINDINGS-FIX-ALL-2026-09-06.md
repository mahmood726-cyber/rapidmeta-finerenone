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

## ROOT CAUSE of the largest defect family: there is no shared screener to fix

The gap inventory the SGLT2 loop produced contains one line that explains the whole week:

> **No generic screener — only ~30 bespoke per-review scripts.**

The screening defects recurred **because there is no shared screener to fix**. Every "fix" landed
in one of thirty scripts (`screen_apixaban_*.py`, `screen_sglt2_*.py`, ...), so the next review
inherited the bug untouched. The three-time repeats — the primary-outcome parser (ODYSSEY→CHOICE→
PIONEER), the `hasResults` flag (ANSWER-HF→Mokadem/APROPOS/AVERT), the registry-over-publication
hierarchy — were **not carelessness. They were structurally guaranteed by a per-review
architecture.** "We fixed the instance and not the class" was true because the class had no single
home to be fixed in. This is the argument for the generic every-outcome-rank screener: not that it
is tidier, but that it is the only structure in which a screening fix can be applied once.

**EXTRACT is per-review too — same diagnosis.** `ls scripts/` shows `extract_apixaban_treatment_
2026_08_19.py`, `extract_pericarditis_from_publications_2026_08_19.py`, and siblings; there is **no
generic `extract.py`/`extractor.py`.** So the estimand-variant failures (inclisiran observed-case
vs ITT-imputed) and the population-mixing failures have the **same structural cause** as the
screening ones: an extraction rule fixed on one review's script cannot reach the next review's. This
changes the priority — the effect+CI extractor is not only the SGLT2/DELIVER unblock, it is the
single home the estimand-variant class has been missing. Two whole defect families, one root.

## reproduce_review.py — the milestone, and its verdict on SGLT2

`scripts/reproduce_review.py` re-runs a review from its registered protocol and diffs the served
bytes on three axes (a page can pass one and fail another):

- **RENDER** — served headline == engine's pooling of the object's own stored inputs.
- **PROTOCOL** — served result == the answer the registered protocol specifies.
- **PIPELINE** — the inputs can be regenerated autonomously SEARCH→SCREEN→EXTRACT.

Each axis returns `REPRODUCES` / `DIFFERS (with diff)` / `CANNOT_RUN (naming the missing
component)`. **It is proven able to return a negative** — `--selftest` perturbs one trial input and
asserts the RENDER axis flips to `DIFFERS`, asserts a value absent from the served bytes fails, and
asserts a protocol expecting a different k/value `DIFFERS`. A reproduction check that has never
returned a negative has not been shown capable of one.

**Verdict on SGLT2_HF** (registered at SHA `ac95196c`):

| axis | verdict | why |
|---|---|---|
| RENDER | **REPRODUCES** | served 0.7636 recomputes exactly from the 3 stored trial effects (and 3-component 0.7835 from 2). The rendering is faithful to the object. |
| PROTOCOL | **DIFFERS** | protocol expects **k=4, 0.774**; object has **k=3, 0.7636**; delta **−0.0104**. The served review does not conform to its own registered protocol — it drops DELIVER. |
| PIPELINE | **CANNOT_RUN** | autonomous rebuild blocked — no generic SCREEN, no generic EXTRACT. |

The RENDER/PROTOCOL split is the value: the page is not *corrupt* (it faithfully shows its object),
it is *non-conformant* (its object was built without DELIVER, against a protocol that includes it).
The fix is not to edit the page — it is to build EXTRACT so the object can carry DELIVER's published
HR 0.80, re-synthesise to k=4 0.774, and let RENDER follow. `reproduce_review.py` is the test that
this happened, and today it correctly says it has not.

## Codex is usable after all -- the block was a missing flag, not the environment

This morning Codex was declared unusable here after five diagnosed failure modes. With full access
granted, a sixth surfaced and it was the actual blocker: **"Not inside a trusted directory and
--skip-git-repo-check was not specified."** Codex refuses to run in a non-git scratch dir without
that flag. The working invocation, verified by BOTH model tokens AND artefact:

```
cd <scratch>; codex exec --skip-git-repo-check --sandbox workspace-write "<task>" < /dev/null
```

Probe returned `tokens used 22,587`, named its model ("Codex, GPT-5 family" -- openai, independent
of Claude=anthropic, good decorrelation), and wrote `probe_out.txt`. Six checkers were then built by
Codex in parallel scratch dirs and EACH cleared its own fixture here before being trusted
(boilerplate-by-k, absolute-effect, composite-decomposition, self-reference-overlap, harms-presence,
num/denom-consistency -- 6/6 selftests green on my run, positive fires + negative controls silent).

## SGLT2 k=4 is blocked on ONE paywalled number, and the brief's DELIVER value is a mis-attribution

The overnight target set SGLT2_HF to k=4 HR 0.774 by adding DELIVER at "0.80 (0.71-0.91)". Verified
against three sources we can read (PubMed): the value is not DELIVER's individual harmonised
two-component, and that individual value is not in any open-access source.

- **DELIVER primary** (NEJM, DOI 10.1056/NEJMoa2206286): the 3-component primary (CV death or
  worsening HF, where worsening HF INCLUDES urgent visits) is 0.82 (0.73-0.92); "worsening HF"
  alone is 0.79 (0.69-0.91) -- **includes urgent visits**, so NOT the two-component; CV death alone
  0.88 (0.74-1.05). The two-component (CV death or first HF HOSPITALISATION, excluding urgent) is
  **not a reported DELIVER outcome** (confirmed by web search of the secondary-analysis literature).
- **Vaduganathan 5-trial** (Lancet, DOI 10.1016/S0140-6736(22)01429-5): DELIVER+EMPEROR-Preserved
  two-component POOL = 0.80 (0.73-0.87); five-trial pool = 0.77 (0.72-0.82). The "0.80" the reviewer
  attributed to DELIVER is the **DELIVER+EMPEROR-Preserved two-trial pool**. Adding it as a single
  trial would **double-count EMPEROR-Preserved** -- a defect, not a fix.
- **Jhund DAPA-HF+DELIVER patient-level pool** (Nat Med, DOI 10.1038/s41591-022-01971-4, full text):
  the two-component (EMPEROR-endpoint) POOL = 0.78 (0.72-0.86). Still a pool, not DELIVER alone.

So the object's k=3 caution was right on the merits: **"a k=3 pool we can fully vouch for beats a
k=4 with one input we cannot."** DELIVER's individual harmonised two-component exists only in the
Vaduganathan/Jhund supplementary per-trial tables (paywalled webappendix), which is exactly the
`owed_retrieval` the object already records. Per the standing stop-rule -- do not change a served
clinical number in a direction unverifiable from a source we own -- DELIVER is NOT added tonight. The
reviewer was right that DELIVER belongs and wrong about the value: an external reviewer can be right
about the finding and wrong about the number.

**Consequence for the protocol:** the v2 protocol registered at ac95196c cites a "known answer k=4
0.774" that rests on this mis-attribution. That benchmark citation is corrected -- the fully-vouched
primary is the k=3 pool; k=4 is a declared pending amendment with the named owed source; the
external five-trial 0.77 is context, not a same-trial-set benchmark.

## EMPAGLIFLOZIN_HF reproduces its target EXACTLY -- but its only benchmark is a self-reference

The k=2 pool of EMPEROR-Reduced (0.75, 0.65-0.86) and EMPEROR-Preserved (0.79, 0.69-0.90) -- both
the trials' REGISTERED PRIMARY two-component, fully verifiable -- is HR **0.7708 (0.700-0.849)**,
matching the brief's target to 4 dp. Its natural external, EMPEROR-Pooled, pools the SAME two trials
(Jaccard 1.0): cited as "independent validation" it would be the self_reference the brief forbids.
It is a legitimate same-trials IPD consistency check only if disclosed as same-trials. This is the
general trap: a meta of exactly the trials in a named pooled analysis always has that analysis as a
same-set comparator. A genuine external needs a DIFFERENT/broader set -- which is precisely why
SGLT2's k=4-vs-Vaduganathan-5-trial was chosen as #1.

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
