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

## THE reproducibility root cause: the page and the object have SEPARATE data sources

Building EMPAGLIFLOZIN to "perfect" surfaced the structural reason pages drift from their objects --
the deeper cause behind "the store knowing is not the reader seeing":

- **reproduce_review and the gates read the ssot object** (`ssot/<app>/<app>.json`).
- **The served page is built by `generate_living_ma_v13.py`** (repo root), which reads its data from,
  in order: a **staging profile** at `C:\Projects\rapidmeta-staging\profiles\<key>.json` (a DIFFERENT
  repo, populated by a "parallel swarm") if present, else the generator's own **`APPS` cfg**. For
  EMPAGLIFLOZIN no profile exists, so the page's heterogeneity narrative is computed from the cfg.
- **These are separate sources of truth.** Fixing the ssot object's `heterogeneity_status` (Q 0.368949
  -> 0.2785) cleared gate 38 but did NOT change the page, because the page is not built from that
  object. A reader still meets the stale odds-ratio narrative.

**Consequence for reproduce_review, stated honestly:** its RENDER axis returning REPRODUCES means only
that *the headline pooled number appears on the page and recomputes from the object's inputs* -- it
does NOT mean the whole page is consistent with the object. EMPAGLIFLOZIN RENDER-REPRODUCES on 0.7708
while the page still serves a contradictory heterogeneity paragraph from a different source. This is a
"reach is not coverage" limit in the reproduction tool itself, now recorded: a true render check must
verify the page's SOURCE (profile/cfg) equals the object, not just that the number is present.

**Why this is the most valuable finding of the EMPAGLIFLOZIN pass:** it locates the single remaining
structural gap in the loop. Everything upstream -- protocol -> search -> screen -> extract ->
synthesise -> object -> reproduce -- works end to end and is proven able to fail. The gap is that the
RENDER stage draws from a parallel-swarm profile / generator cfg rather than the ssot object, so the
object and the page can be individually correct and mutually inconsistent. Closing the loop fully
means making the generator read the ssot object (single source of truth), or making reproduce_review's
RENDER axis diff the object against the generator's actual source and FAIL on divergence.

## EMPAGLIFLOZIN_HF against the four "perfect" conditions

1. **reproduce_review REPRODUCES** -- YES on all three axes (RENDER 0.7708, PROTOCOL k=2 0.7708,
   PIPELINE orchestrator 0.7708), each proven able to DIFFER. The loop is real. (Caveat: RENDER checks
   the number, not full page consistency -- see the source-divergence finding above.)
2. **Every validated gate passes** -- gate 38 now clears (was a real finding: stale OR heterogeneity
   cited live; fixed in the object, gate control made synthetic so it cannot self-retire); gate 53
   clean. Full validated-gate sweep still owed.
3. **Every reviewer finding fixed** -- the gate-38 finding fixed in the OBJECT; the PAGE still serves
   the stale narrative because it is built from a different source (the render-divergence gap).
4. **External benchmark matches** -- no truly independent external exists (any empagliflozin-HF pool is
   these two trials); EMPEROR-Pooled is a disclosed same-trials IPD cross-check, not independent.

Status: object-perfect and loop-perfect; page-perfection is blocked on the render-source-divergence
architecture gap, not on a value we cannot verify.

## Reproducibility scorecard across the five brief metas (using reproduce_review)

| meta | protocol registered | RENDER | PROTOCOL | PIPELINE |
|---|---|---|---|---|
| SGLT2_HF | yes (ac95196c) | DIFFERS -- stale 0.884 served live (candidate) | DIFFERS (k=3 object vs k=4 protocol; DELIVER blocked) | CANNOT_RUN (no evidence set) |
| EMPAGLIFLOZIN_HF | yes (45cbe9bff) | DIFFERS -- stale OR-analysis numbers served live | REPRODUCES | REPRODUCES |
| INCLISIRAN (lipid-kidney) | no | CANNOT_RUN | CANNOT_RUN | CANNOT_RUN |
| ALIROCUMAB (lipid) | no | CANNOT_RUN | CANNOT_RUN | CANNOT_RUN |

Three findings from the scorecard:
1. **The stale-served / source-divergence class is CORPUS-WIDE**: both metas with a resolvable page fail
   RENDER on a superseded value narrated live. This confirms the object<->page two-source problem is not
   an EMPAGLIFLOZIN quirk -- it is the corpus's default state.
2. **reproduce_review is RATIO-ONLY**: `_outcomes_with_pool` requires point/CI > 0 and `reml_pool` works on
   the log scale, so INCLISIRAN and ALIROCUMAB (LDL % change, a DIFFERENCE measure with NEGATIVE values,
   e.g. -50.54) return CANNOT_RUN. Their objects are fine (per_trial + pooled present); the TOOL cannot
   read difference-scale outcomes yet. A natural-scale pooling path is the fix. Recorded as a coverage gap.
3. **Naming is inconsistent across the corpus**: object slug vs page filename diverge (object `arni-hfref`
   vs page `ARNI_HF_REVIEW.html`; object `alirocumab-lipid` vs page `ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html`).
   A review whose id does not deterministically resolve to its object AND its page is a reproducibility
   hazard in itself -- reproduce_review cannot even find both halves for ARNI.

Only 2 of 5 target metas have a registered protocol; 1 of 5 (EMPAGLIFLOZIN) reproduces on PROTOCOL+PIPELINE.
None reproduces on RENDER, because of the source-divergence gap. The honest state of "reproducibility" for
the corpus tonight: the LOOP is proven and works end-to-end on the object, but the SERVED PAGE is not yet
built from the reproduced object anywhere -- that is the single change that would make pages reproducible.

## WORKED EXAMPLE: the discipline caught a silent disarming of the harness's own guard

A parallel process rewrote `protocol_schema_v2.py` in the shared working tree (uncommitted, mtime
21:24). It looked like an improvement -- a more elaborate typed structure. It had **no runnable
selftest** (exited 0, printed nothing) and **zero refusals** (no reference to CAB-LA, inclisiran,
bempedoic, PLATFORM, LEAP-China -- every one of the 13 proven refusal fixtures was gone). A schema
with no refusals is not a schema; it validates everything. It would have silently disarmed the single
most valuable artefact of the day while reading as a refactor.

This is **"a fix that clears every failure is a loosened test"** firing in real time, on the very
component whose whole purpose is to refuse. The tell was structural, not semantic: `python
protocol_schema_v2.py` produced no ALL-PASS line, and a grep for the incident names returned zero.

Resolution (per Mahmood): restored the 16/16 version (`git checkout HEAD --`), discarded the rewrite,
and made the refusal count a **HARD INVARIANT** -- the 13 refusal fixtures + 2 permitted-input
fixtures are now an explicit list, and the selftest asserts `refusals_fired >= 13` and `permits == 2`
directly, so a shrunk refusal set fails the selftest before anything else. **A rewrite that removes
behaviour is the hardest kind to spot, because the tests it deletes are the ones that would have
caught it** -- which is exactly why every Codex/parallel artefact is a hypothesis until its self-test
is run here and its guard-count checked.

## TOMORROW DECISION (do not divert tonight): embedding the recompute in the HTML page

Mahmood's idea: "can the harness also fit inside the html file and is this a good idea?" Assessment,
recorded so it is not lost and not confused with reproducibility:

**Worth doing, for a narrow real purpose.** Embedding the extracted inputs + the pooling code lets a
reader recompute the diamond in their own browser, offline -- the one thing none of the 24 surveyed
AI synthesis tools does -- and makes the page archive-proof. It also structurally KILLS two defect
families rather than gating them: a panel computed at view time cannot go stale (empagliflozin's dead
OR values; bococizumab's k=4 leave-one-out), and a sentence derived from the numbers beside it cannot
contradict them (the eight "no heterogeneity" at I^2 56-80% pages).

**Guardrail (the important part):** only the POOL stage can live in the HTML -- search/screen/extract
need registries and publications. And every defect in 22 reviews was UPSTREAM of pooling (22 audits,
zero arithmetic errors), so the embedded recompute makes visible the only stage that has never been
wrong. That is the **self-benchmarking trap in a new form -- the page validating itself**: a reader
who recomputes and gets the same number may conclude the review is sound when the failure was a trial
excluded three stages earlier. So the page must state exactly what the recompute proves:
> "this re-derives the pooled estimate from the extracted inputs; it does not verify that these are
> the right inputs."

**Second benefit:** embedding the source object in the page makes it self-describing -- the direct
structural fix for the 291 pages with no object behind them.

**`reproduce_review.py` from the protocol SHA remains what "reproducible" means. The in-page recompute
is transparency of the last mile, not reproducibility of the review.** Tomorrow decision, not tonight.

## STANDING RULE for tonight's five-meta run: synthetic fixture BEFORE fixing the page

Every gate in tonight's catalogue took its control from a reviewer finding on a LIVE page. Fixing that
page RETIRES the control (empagliflozin nearly did this to gate 38 -- fixing the real defect made the
gate's positive control stop firing, so the gate reported a control FAILURE and looked like a
regression). Never leave a defect live to keep a gate armed. Instead, for EACH validated gate, capture
its firing signature as a SYNTHETIC fixture (a fabricated object carrying the defect signature) BEFORE
correcting the page it came from. Synthetic is preferred over version-pinning: a pinned real object
still ages (rename/restructure/regenerate makes it silently stop resolving and the gate goes quiet).
Applied to gate 38 already; apply to every gate a meta controls as that meta is fixed.

## HEADLINE ARCHITECTURAL GAP: SGLT2_HF_REVIEW.html is NOT generated from its object

This is the important output of the SGLT2 run, not a blocker. `SGLT2_HF_REVIEW.html` is a 3.9MB
hand-maintained single-file app with the pooled estimate baked into **14 places** and no object→page
generator. That is *why full byte reproduction cannot be met* — not because the pipeline failed
(reproduce_review's PROTOCOL and PIPELINE axes both REPRODUCE on the k=4 object), but because **no page
generator exists for it**. A page whose numbers are typed in 14 places, not generated once from the
object, is the architectural CAUSE of the stale-panel and two-live-values defect families gated all
night (empagliflozin's dead OR values; the eight "no heterogeneity" at I² 56–80%).

**The generic page generator is the FOURTH missing component**, alongside the screener, the extractor
and the reproducer — and it is the one that would make "reproducible" true end to end. Until it exists,
correcting such a page means either 14 in-place edits (14 chances to create the very half-migration
defect we gate against — empagliflozin IS what that looks like) or a single generated disclosure
banner. Route 2 (the banner) was taken, correctly.

## SGLT2_HF — 4 of 5 conditions met; the 5th blocked by the named gap and DISCLOSED on the live page

LIVE at https://mahmood726-cyber.github.io/rapidmeta-finerenone/SGLT2_HF_REVIEW.html, verified by
fetching the marker `SGLT2_K4_CORRECTION_2026_09_06` (exists only in the banner) and confirming the
served page is byte-identical (3,921,121 bytes) to the built page.

1. **reproduce_review** — PROTOCOL REPRODUCES (object k=4 0.7738 vs protocol 0.774) and PIPELINE
   REPRODUCES (orchestrator autonomously rebuilds k=4 0.7738), both proven able to DIFFER. RENDER
   (full page byte reproduction) does NOT reproduce — the ONE blocked axis, blocked by the missing
   page generator, and that blocker is stated in the banner itself. → the 5th, honestly blocked.
2. **Gates** — every validated pre-push gate PASSES. The harness caught FOUR real issues in the k=4
   work (variantless effects, stale r_output, untiered DELIVER provenance, a negative-guard) and each
   was fixed properly, none waived. ✓
3. **Reviewer findings** — fixed in the object (DELIVER added k=4; false benchmark replaced; stale
   states superseded; component decomposition added; amendment recorded) and DISCLOSED on the page via
   the generated banner. ✓
4. **External benchmark** — Vaduganathan five-trial 0.77 (0.72–0.82), a genuine superset (adds
   SOLOIST-WHF), NOT a self_reference. In the object and the banner. ✓
5. **Live** — deployed to `main` by cherry-picking ONLY the page (git plumbing, not a merge of
   harness-fixes), verified by fetched bytes. ✓

DELIVER's HR 0.80 (0.71–0.91) was NOT accepted on trust: it is the Vaduganathan supplement value,
disclosed at its JOURNAL_SUPPLEMENT provenance tier, and CORROBORATED by de-pooling Jhund's DAPA-HF+
DELIVER pool (0.78) against DAPA-HF (0.75) → ≈0.81. The benchmark was fetched from a source we own,
not adopted from the reviewer's figure.

## REVIEWER AUDIT of the live corrected pages — findings and rules (2026-09-07)

External reviewers audited the five live pages. The corrections were confirmed against independent
sources (INCLISIRAN −50.55 matched by five external estimates incl. the JACC patient-level pool −50.7;
EMPAGLIFLOZIN components reproduced). But three defects were named, two of them created BY tonight's work:

### DEPLOY RULE (new, non-negotiable): a page and the object it cites LAND TOGETHER, always
My cherry-pick strategy deployed only the PAGE to `main` and left the corrected OBJECT on
`harness-fixes`. Result: `main` carried a k=4 correction banner over a k=3 object (SGLT2 0.7636) — the
two-live-values / object↔page-divergence defect we gate against, created by the deploy strategy itself.
The banner's claim "generated from the current object" was FALSE as committed. Fixed by cherry-picking
all five corrected objects to `main` (commit b733d63). **Rule: every page deploy carries its object in
the same commit; verify `main`'s object matches the served page before calling a deploy done.**

### THE PROTOCOL-TIMING WORDING, for all five: "retrospectively registered; prospectively fixed only for the re-run search"
Anchoring a protocol SHA immediately before a re-run search is NOT prospective registration when the
review object already existed (empagliflozin's was built 2026-08-17 with both trials and the pooled OR).
The SHA proves WHEN the protocol was written; it does not prove the evidence was unseen. The honest label
is *retrospectively registered review; prospectively fixed only for the re-run search* — apply verbatim
to all five, and state what was known at authoring (the pooled answer, the external benchmark, both
intervals).

### RoB-2 gate description (add): assesses the trial, not our retrieval
> RoB 2 assesses risk of bias IN THE TRIAL RESULT — not deficiencies in the reviewer's document
> retrieval. Downgrading certainty because our assessors did not fetch a paper is invalid; a randomised,
> double-blind, ITT trial with blinded adjudication and low balanced loss is low-RoB regardless of our
> retrieval gaps.

### The declared-method-vs-served-number defect (interval), unresolved value
SGLT2's September protocol declares REML + modified HKSJ + t_{k-1} + floor 1; the page serves the Wald
interval 0.7243–0.8268 while the abstract calls it HKSJ. The DEFECT is confirmed. The VALUE is not yet
reconciled: metafor (`rma REML test="knha"`, tau²=0) gives modified HKSJ 0.7328–0.8171, NOT the reviewer's
0.695–0.862 — a genuine discrepancy in the exact "modified HKSJ + floor 1" definition. Do NOT serve a
number until the definition is pinned and metafor-reproduced; serving the wrong HKSJ is a fresh error.
The conclusion survives either interval (excludes 1). Fix in the protocol first, then regenerate.

### The banner route's cost, named by every reviewer: HALF-MIGRATION → the page generator is now top priority
The banner fixes the headline and leaves the body contradicting it (SGLT2/INCLISIRAN/EMPAGLIFLOZIN bodies
still say the old value, "the pool STANDS", "no heterogeneity" beside I² 74%). That is gate 38 on the
served page — a DISCLOSED defect, right under the 14-hand-edits constraint but not a resolution. **The
generic page generator is the ONLY route that ends this, and it fixes all five at once. It is now THE
priority, above a fifth banner.** Until it exists, banners must say plainly that the body below is
superseded in full, not merely that a correction exists.

## MICRO-MODEL FOR SCREENING — design scope (Mahmood: scope, do not build tonight)

Connecting a small model to the SCREENING stage, per Mahmood. Decisive argument is REPRODUCIBILITY, not
cost.
- **Committed weights make the protocol SHA pin the model.** An API model drifts; a rerun a year later
  screens differently and `reproduce_review.py` can never be true for the screen stage. A few MB of
  weights in the repo replays the run bit-identically forever. THIS is why it is local, not remote.
- **Model class: TF-IDF + logistic regression or naive Bayes, ASReview-style relevance ranking** — NOT an
  LLM. Auditable: it can name the features that drove a decision, which suits a corpus where every
  exclusion carries a rule id.
- **Gold standard already exists**: every trial the reviewers caught us excluding — CLEAR Wisdom,
  PIONEER-HF, CHOICE I, CHOICE II, STEP-HFpEF DM, AVERT, APROPOS, ADAM VTE, Mokadem, Botticelli,
  LEAP-China, DELIVER. Simulation mode measures recall against it directly.
- **⛔ TRAINING TRAP**: training on our own PAST screening decisions teaches it to reproduce our errors.
  Train on CORRECTED labels; validate on the reviewers' findings (held-out).
- **⛔ Screening/ranking ONLY. Never extraction** — a small model fails silently at extraction, and silent
  extraction errors are the family we spent the day finding.
- Integration: the model RANKS candidates and the generic screener applies the rule-id verdicts
  (every-outcome-rank, gate-53 three states, eligible-but-non-contributing, EXECUTED_UNRESOLVED); a human
  adjudicates the boundary. The model never issues a terminal exclusion on its own.

## PAGE GENERATOR — design + why I did NOT start the build at the tail of this session

Authorised by Mahmood (AUTO_FULL family first), with the explicit constraint: *build it deliberately,
do not rush it to close out the session; a half-built generator that produces a page nobody can
regenerate would be the worst outcome.* Honouring that: I did the deliberate ANALYSIS and recorded the
design, and I am NOT starting the large build now — it deserves a fresh, focused effort, not the tail of
an already-enormous session.

**Structural analysis of an AUTO_FULL page (EMPAGLIFLOZIN, 1.37 MB, 1198 lines):** it is STATIC HTML
with the values baked in — 29 tables, 26 h2 / 44 h3 sections, 9 SVG forest plots, one small
tab-navigation `<script>`, no data-binding markers, no `{{placeholders}}`, and it does NOT embed its
object (`data-store` points at the ssot path but nothing reads it at runtime). So a generator must EMIT
all of that from the object.

**The tractable path — the building blocks already exist.** `generate_living_ma_v13.py` has
`generate_app(cfg)`, `build_evidence_js`, `build_outcomes_js` and a forest builder; it already generates
26 apps. The AUTO_FULL review pages are NOT in its APPS list and it reads a staging profile / its cfg,
NOT the ssot object. The build is therefore an **object→cfg adapter**: `cfg_from_object(review_id)` reads
`ssot/<slug>/<slug>.json` and produces the cfg `generate_app` needs, so the page becomes a pure function
of the committed object. Then `reproduce_review`'s RENDER axis verifies the regenerated bytes, and the
half-migration ends for all four AUTO_FULL pages at once.

**Build sequence (next focused session):**
1. `cfg_from_object(review_id)` for ONE page — EMPAGLIFLOZIN (it already REPRODUCES on PROTOCOL+PIPELINE,
   so it is the cleanest first target). Emit via `generate_app`.
2. **Acceptance test, both directions**: the regenerated page must (a) RENDER-reproduce from the object
   (headline + no superseded value served live), AND (b) lose no content vs the current served page
   (diff the section set; a generator that drops the harms table or the RoB narrative is a regression).
   Only when both hold is the page object-generated.
3. Roll to the other three AUTO_FULL pages (inclisiran, arni-if-AUTO, alirocumab).
4. SGLT2's 3.9 MB hand-maintained app is the HARD case (no shared structure) — it stays bannered longer;
   do not force it into the AUTO_FULL generator.
5. Only after the generator reproduces a page: fix the protocol (modified-HKSJ interval per
   `scripts/modified_hksj.py`, one method named), regenerate all five FROM it, land page+object together.

**This is the load-bearing build** — it is what turns "redo all five" from "more banners" into real
regeneration, and it is the single change that makes condition 5 pass rather than be disclosed-blocked.
It must be built deliberately and acceptance-tested in both directions, not rushed.

## THIRD AUDIT (SGLT2) + a critical correction to the generator plan (2026-09-07)

**The generator plan was WRONG and de-risking caught it before a wasted build.** `generate_living_ma_v13.py`
generates a DIFFERENT family — 26 `*_REVIEW.html` topic pages (PFA, WATCHMAN, VERICIGUAT…), none of them our
five, none `*_AUTO_FULL_REVIEW.html`. So `generate_app` is NOT the AUTO_FULL generator, and "reuse it via an
object→cfg adapter" does not apply. The AUTO_FULL family (empagliflozin/inclisiran/alirocumab) and SGLT2's
3.9 MB hand-app have **no discoverable generator** — building one is a **from-scratch** reverse-engineering of
the 29-table / 9-forest-SVG structure, larger than assessed. This is the deliberate build; it must not be
rushed at a session's tail (a half-built generator producing an unregenerable page is the worst outcome).

**Split #2: RESOLVED, not a path defect.** The reviewer saw a k=3 linked object; the page links to
`ssot/sglt2-hf/sglt2-hf.json`, and the LIVE object at that exact path now returns 0.7738/k=4 (HTTP 200). The
audit predated the b733d63 object push; Pages has rebuilt. No second object location.

**HKSJ 0.6950–0.8616 independently confirmed by a third reviewer** — the floor-at-1 + t_{k-1} definition in
`scripts/modified_hksj.py` is validated against two independent computations. Write it into the protocol.

**SGLT2 object-correction backlog (object-only, NO banner — fold into the regeneration; some need sourcing):**
- **three-component pool k=2→k=4**: add EMPEROR-Reduced and EMPEROR-Preserved prespecified three-component
  analyses. Reviewer target 0.7754 (0.7276–0.8263), Q 1.466. My pool from assumed inputs (EMPEROR 0.76/0.77)
  gave 0.7777, Q 1.228 — NOT a match, so the exact EMPEROR three-component per-trial values must be sourced
  verbatim before serving. "The EMPEROR trials cannot join" is a FALSE reason (registry-absence ≠ data-absence,
  7th instance). Do not serve until sourced.
- **DELIVER provenance UPGRADE** (the mirror of an over-claim — an unnecessary self-downgrade): 0.80 (0.71–0.91)
  is in the main Lancet forest plot AND a later direct DELIVER publication with event counts (475 vs 577), not
  supplement-only. Upgrade JOURNAL_SUPPLEMENT → JOURNAL_FULL_TEXT; remove the retrieval-blocker caveat.
- **Zannad 2020 relabel**: DAPA-HF's three-component was used as a PROXY for the EMPEROR two-component endpoint;
  it is a useful comparison, NOT an exact harmonised benchmark.
- **screening log**: DAPA ACT HF–TIMI 68 (2025) must be dispositioned (likely excluded acute HF), not absent.
- **eligible-but-non-contributing** must list DEFINE-HF, PRESERVED-HF, EMPERIAL, DETERMINE.
- **PICO boundary**: state "chronic HF" precisely (not "stable ambulatory") so the SOLOIST-WHF exclusion is
  prespecified on that boundary.
- **precision**: HRs were reported on the RATIO scale and transformed to log HRs — not "reported on the log scale".
- confirmed components (for the regenerated page): HHF 0.721 (0.666–0.780), CV death 0.871 (0.794–0.955),
  all-cause 0.927 (0.861–0.997).

**Three reviewers, three pages, one unanimous verdict: complete rebuild, not another banner.** No further banners
on any page. The page generator (from scratch, deliberately, acceptance-tested both directions) is the sole
remaining path to a submittable page and it fixes all five at once.

## ROTAVIRUS_VACCINE_AFRICA — the unbiased generalisation test (a page we never touched)

Chosen because we had NOT corrected or looked at it. Result: **the catalogue generalises. Every defect
class it exhibits is already in the catalogue except two — and the two new ones are BOTH estimand
defects.** The defect space is converging on estimand definition, which is exactly what the protocol
schema's typed fields exist to catch. NOT corrected tonight (no more banners; it needs the generator);
recorded, with two new gates and two new schema fields added.

**NEW GATE 59 — effect scale must match the trials' own estimand.** Vaccine efficacy is 1-RR / 1-IRR /
1-HR, NEVER 1-OR. The page converted cumulative counts to ODDS RATIOS, discarded person-time, and served
1-OR as "~51% efficacy" -- a methodological error served as a headline. Built
`scripts/gate59_effect_scale_matches_estimand.py` (synthetic controls pass; found 7 corpus candidates to
review) AND added it to the SCHEMA: estimand now carries `trial_native_effect` (risk|rate|hazard|odds|mean)
and validate() refuses an effect_measure that does not match it (log_OR from risk/rate trials refused).

**NEW GATE 60 — follow-up windows must be harmonised before pooling cumulative counts.** Rotarix through
age 1, RotaTeq median 527d (~21mo), RotaSIIL ~9.8mo -- cumulative odds across those is not a common
estimand. This is the concrete form of "time horizon is part of the estimand" (apixaban prophylaxis).
Built `scripts/gate60_followup_window_harmonised.py` (synthetic controls pass) AND added `follow_up_window`
{harmonised, window} as a required estimand field; validate() refuses unharmonised-window cumulative pooling.

**IT MANUFACTURED HETEROGENEITY AGAIN (4th instance).** Published first-year ratios 0.388/0.358/0.397 pool
to I² 0%; the served I² 57.6% appears ONLY after mixing the longer waning RotaTeq window with two shorter
ones. Same family as inclisiran (observed-vs-imputed) and empagliflozin (OR-vs-HR): heterogeneity
manufactured by a non-estimand choice, dissolving when the estimand is fixed.

**Correction well-established for whenever the rebuild reaches it (do NOT serve tonight):** pooled RR
0.386 (0.307-0.486), VE 61.4% (51.4-69.3), tau2 0, I² 0%, Q 0.102; raw-count sensitivity RR 0.390; modified
HKSJ 0.233-0.639 (still excludes 1); product- and time-stratified. Plus: gate 46 third instance (per-protocol
counts with randomised denominators, Rotarix row cannot be reconciled -- num/denom population check is now
HIGH priority); gate 9 (abstract "no heterogeneity" at I² 57.6% -- externally corroborates the validated
list of 8); two-live-values (tau2 0.05718/0.0557); NCT00383903 unexplained.

**The schema hard-invariant is now 15 refusals** (13 + gate 59 + gate 60), each fixtured. Extending the
required estimand fields means the existing five protocols now need `trial_native_effect` + `follow_up_window`
-- added during the regeneration, which is correct: the schema flags exactly the estimand gaps the reviewers
found.

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

---

## 2026-09-07 — path-convention split as a CLASS, and the structural answer

**THE CLASS: a path convention split across subsystems produces "not found", and "not found"
degrades to a benign-looking state.** Four instances, four subsystems, one cause — every one
silently DISABLED a check rather than failing it:

| # | subsystem | split | axis it silently killed |
|---|---|---|---|
| 1 | `reproduce_review` | `--page` ignored entirely | RENDER never tested a generated file |
| 2 | `reproduce_review.resolve_paths` protocol glob | hyphens vs underscore protocol names | PROTOCOL → CANNOT_RUN |
| 3 | `run_review` protocol + evidence lookup | hyphens vs underscore dir names | PIPELINE → CANNOT_RUN |
| 4 | `reproduce_review.resolve_paths` page glob | hyphens vs underscore page names (`SGLT2-HF_REVIEW` vs `SGLT2_HF_REVIEW`) | RENDER → no page found → false DIFFERS |

**THE STRUCTURAL ANSWER (not "remember to try both spellings"): `HARNESS_FAULT`.**
`reproduce_review` now FAILS LOUDLY (verdict `HARNESS_FAULT`, exit 3) if any axis returns
`CANNOT_RUN` while its inputs are present. A `CANNOT_RUN` proven to be genuine input-absence is a
result; one that has not been proven is a fault in disguise. Silence is never an acceptable answer
from a checker whose whole job is to answer.

**CONVENTION RULE (owed, one line): review-id ↔ filename derivation must be SINGLE-SOURCED.**
ARNI's page is `ARNI_HF_REVIEW.html` but its review-id is `arni-hfref` — the page name does not
derive from the review-id AT ALL (`HF` ≠ `HFREF`). That is the same class wearing different clothes:
every subsystem re-derives the filename from the id its own way, so they disagree. There must be ONE
function `review_id -> {object, protocol, evidence, page}` that every subsystem calls, and irregular
pages (like ARNI) must be recorded in an explicit map rather than pattern-derived.

## 2026-09-07 — method-imposition gate (declared method vs served number)

Defect (caught by reading a subtitle, not a check): the generator imposed modified HKSJ on every
ratio page, recomputing `t_{k-1}`; at k=2 `t(1)=12.706` blew EMPAGLIFLOZIN's interval to 0.413–1.44,
a second interval beside the object's own fixed-effect CI [0.700, 0.849]. Behaviour fixed AND made a
standing gate: `scripts/gate_served_interval_matches_declared_method.py` — the page's shown interval
must equal its EMBEDDED object's pooled CI (self-contained via `<script id="ssot-current">`); an
imposed method makes them disagree and the gate fires. Synthetic positive control pinned in code
(imposed 0.413–1.44 over fixed-effect CI) so it cannot self-retire.
