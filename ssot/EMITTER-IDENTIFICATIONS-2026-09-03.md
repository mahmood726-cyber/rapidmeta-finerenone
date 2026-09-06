# Emitter identifications + sweep counts — SGLT2_HF_REVIEW lane, 2026-09-03

Written under memory pressure (806 MB free, 43 concurrent `claude`, MemoryError in two
other lanes) because everything below existed only in a session transcript.
**A run can exit 0 with an empty artefact right now — every number here carries the probe
that produced it, so it can be re-checked rather than re-trusted.**

---

## 1. The `_absolute_rows` defect — ALREADY FIXED, do not re-apply

Defect text (`measure` accepted, never read; every ratio multiplied by the baseline):

```python
def _absolute_rows(measure, point, lo, hi, grid=None):
    """RR x baseline, at each baseline. Arithmetic, not a transfer claim."""
    ...
    cell.append(None if not isinstance(v, (int, float)) else round(b * v, 1))   # <- line 192
```

**Fix commit (already on `main`, and `main`'s tip):**

```
a3f22424e2e37ce977b01fc79e34a7b3c7199213   2026-09-02 22:01:28 +0100
"A measure that steered the prose and never the arithmetic"
siblings: 91cc078ab "a hazard-type ratio states its assumption, or it declines"
          fb332abb1 "participants is the number analysed for the outcome, not enrolment"
```

The fix introduces `_absolute_from_ratio(measure, p0, v)` dispatching
RR -> `p0*v`, OR -> odds form, HR/rate -> `1-(1-p0)**v`.

### Every copy on disk, with sha256 (first 16) of the file

| path | branch @ commit | lines | sha256[:16] | state |
|---|---|---|---|---|
| `E:\rm-work\rapidmeta` | `main` @ `a3f22424e` | 717 | `6beec09032aeb347` | **FIXED** |
| `E:\audit\rmf` | `main` @ `add369578` | 717 | `6beec09032aeb347` | **FIXED** |
| `E:\rmf-harness` | `harness/complete-20260902` @ `a88466e46` | 717 | `6beec09032aeb347` | **FIXED** |
| `E:\rmf-lanes\hgates` | (no `.git`) | 717 | `11fa3bd0e1e23b06` | **FIXED** |
| `E:\rm-work\probe` | (no `.git`) | 717 | `11fa3bd0e1e23b06` | **FIXED** |
| `E:\land\rmf` | `detect/pcheck-held-contradicted-20260902` @ `dfb469f93` | 672 | `f22a499769b0ebfc` | **DEFECTIVE — line 192** |
| `E:\repro-demo\repo` | `main` @ `97a479027` | 371 | `a1e32069ef799b81` | **DEFECTIVE — line 128** |

`E:\repro-demo\repo` carries the older 371-line variant: `_absolute_rows(measure, point, lo, hi)`
at line 122, no `grid` parameter, same `round(b * v, 1)` at line 128.

### ⛔ THE TWO DEFECTIVE COPIES ARE DETECTOR CONTROLS, DELIBERATELY HELD PRE-FIX

**CONFIRMED 2026-09-03. DO NOT PATCH. DO NOT TIDY. DO NOT "BRING UP TO DATE".**

| path | ref | sha256[:16] | status |
|---|---|---|---|
| `E:\land\rmf\ssot\projectors_sof.py` | `detect/pcheck-held-contradicted-20260902` @ `dfb469f93` | `f22a499769b0ebfc` | **CONTROL — held pre-fix** |
| `E:\repro-demo\repo\ssot\projectors_sof.py` | `main` @ `97a479027` | `a1e32069ef799b81` | **CONTROL — held pre-fix** |

Standing law: **a detector must be pointed, unchanged, at a case that MUST fire before a
zero from it means anything.** These are the only pre-fix cases we hold. Patch either one
and every subsequent green from the D3 detector becomes unfalsifiable — the suite would
report zero because there is nothing left that can fire, and that reads identically to
zero because the corpus is clean.

**THE HAZARD THIS NOTE EXISTS TO PREVENT:** a future cleanup pass reads these two as
unpatched stragglers and fixes them. They look exactly like the defect they are controls
for — that is what makes them good controls and what makes them vulnerable. If you have
arrived here because a scan flagged these two files, **the scan is working and the files
are correct.** Verify by sha256 against the table above, then leave them alone.

A control is not data and is not a defect. It is a third thing.

Earlier searches missed all of this because they covered `C:` and `F:` only. The whole
`ssot/` tree lives on **`E:`**.

## 2. Corpus sweep — n of N, N NAMED

### Population A: `E:\rm-work\rapidmeta` — the ssot-rendered corpus (the right population)

**N = 1,464** `*.html`. Kinds enumerated:

| kind | n |
|---|---|
| no absolute-effect grid | 1,462 |
| **HR grid computed by MULTIPLICATION (defective)** | **2** |
| HR grid computed by survival form (correct) | 0 |
| grid present, non-HR measure | 0 |
| grid present, unparsed | 0 |
| read failed | 0 |

**=> 2 of 2.** Every HR-derived absolute-effect grid in the corpus is defective, because
no page has been regenerated since the 22:01 fix. Not 2 of 1,464.

### CODE-FIXED, CORPUS-STALE — a standing state, not a one-off

**Every HR grid in the corpus is defective because nothing has been regenerated since the
fix landed at `a3f22424e`, 2 Sep 22:01.** That is `CODE-FIXED, CORPUS-STALE`.

**This is the SECOND confirmed instance, after the τ² estimator.** Two independent
occurrences make it a standing state we must test for rather than a one-off:

> **A FIX THAT HAS LANDED IS NOT A FIX THAT IS SERVED.**

Test for it directly — compare the mtime/commit of every rendered artefact against the
commit of the emitter that produced it, and treat a served artefact older than its emitter
as UNVERIFIED rather than as passing. A green source suite says nothing about the bytes a
reader receives. Note that the reporting asymmetry is what makes this class survive: the
source fix is visible, celebrated and committed, while the staleness is silent and lives
in a different artefact from the one anybody is looking at.

Method note, to be kept: classification here was decided **numerically** — the printed
value compared against both candidate formulas, and classified only on rows where the two
differ by >= 0.1. A textual detector would have had to trust a label; this one cannot be
fooled by one.

```
SGLT2_HF_REVIEW.html    baseline 50/1000, HR 0.7636 -> printed 38.2  (mult 38.2 | survival 38.4)
IV_IRON_HF_REVIEW.html  baseline 50/1000, HR 0.7957 -> printed 39.8  (mult 39.8 | survival 40.0)
```

Method: byte-mode regex over each file; for every (baseline, printed) pair and every HR on
the page, compare against `round(b*v,1)` and `round(1000*(1-(1-b/1000)**v),1)`, and classify
only on rows where the two formulas differ by >= 0.1. Detection is numeric, not textual.

### Population B: `F:\rapidmeta-finerenone` — the v12 JS corpus (DIFFERENT EMITTER)

**N = 1,243** `*.html`: 493 no grid, 749 correct, 1 grid-without-converter
(`LivingMeta.html`), **0 defective**.

That corpus is emitted by JS `computeInterventionEventRate(controlRisk, effectValue, measure)`,
which already branches (`"HR"===em -> 1-Math.pow(1-cer,effect)`) and already derives
`totalN` from `c.plotData` (the trials that entered the fit). **It is not the population
this finding is about.** Recorded so the two are never conflated.

## 2b. SERVE PATH — identified, AMBIGUOUS, NOT ACTED ON

Live: `https://mahmood726-cyber.github.io/rapidmeta-finerenone/` — public, https enforced,
status `built`. API reports `build_type: "workflow"`, `source: {branch: "main", path: "/"}`.
Deployer: `.github/workflows/pages.yml` on `main` (3 hits for `deploy-pages` /
`upload-pages-artifact`), triggered `on: push: branches: [main]`.

**LIVE CONTENT PROBE — the exposure is real and is the ssot page:**
`GET .../SGLT2_HF_REVIEW.html` -> `http=200 bytes=3918595`; `152.7` x1, `20725` x2,
`0.7636` x12, `NONE AT ANY RANK` x1, `Ultra-Precision v12.0` x0 (so it is the ssot page,
not the `F:` v12 corpus page of the same name). The blob at `origin/main` is byte-identical
at 3,918,595 — Pages is serving `main`'s file verbatim.

**THE AMBIGUITY, WHICH IS WHY NOTHING WAS TOUCHED.** `pages.yml`'s own header states the
site *is currently built by the legacy branch builder* and that **"THIS WORKFLOW DOES NOT
SWITCH THE BUILDER"** — the Settings -> Pages change is manual and had not been made when
the file was written. The API now says `workflow`. Those two disagree, and I cannot tell
from outside which builder actually served the bytes I just probed.

**AND EITHER WAY THE ACTION IS UNSAFE TONIGHT.** Removing two files means a push to `main`,
which rebuilds the whole surface: **1,478 root HTML pages, ~1.1 GB**. `pages.yml` records
that a commit rewriting several hundred pages **has been observed to exceed the builder's
timeout**, and that `cancel-in-progress: false` exists because *"a cancelled deploy can
leave the site serving a partially-swapped tree."* So the downside of unpublishing 2 pages
tonight is a partially-swapped tree across 1,478.

=> **Left served, deliberately.** Standing instruction: if the path is ambiguous, carry the
exposure rather than unpublish the wrong surface. Resolve by reading Settings -> Pages
(which builder is selected) before any attempt.

## 3. SGLT2_HF_REVIEW.html — served-byte state (STALE)

**CORRECTED 2026-09-03.** Three provenance errors in the first version of this section,
each caught by a later probe and each recorded rather than silently overwritten:

1. The file I first probed (`E:\rm-work\rapidmeta\SGLT2_HF_REVIEW.html`, 3,914,767 bytes,
   mtime 2026-09-02 20:41:40) is a **locally MODIFIED working file**, not the committed
   blob. The committed and served blob is **3,918,595 bytes**. Both carry `152.7` and
   `20725`, so the conclusion is unchanged — but "the served bytes" was the wrong label.
2. **`origin/main` is `d2d5069a3`, TEN commits ahead of the local `main` I read.** I
   reported "main's tip IS the fix"; that was true of the local clone only. Checked
   properly: `git merge-base --is-ancestor a3f22424e origin/main` -> **YES**. So the fix
   **IS published in source** — which does not weaken CODE-FIXED/CORPUS-STALE, it confirms
   it on the published surface rather than merely locally.
3. A scan reporting "no Pages deploy workflow exists on main" was a **broken command**, not
   a finding: Git Bash MSYS path conversion mangles `origin/main:.github/...` into
   backslashes and the command fails silently to empty output. Re-run with
   `MSYS_NO_PATHCONV=1`, `pages.yml` is present and is the deployer. *A tool that fails to
   empty output produces a confident wrong belief about a repository.* Any `git show
   <ref>:<path>` in this shell needs `MSYS_NO_PATHCONV=1`.

The page's last commit is `39816a951`, which PREDATES the fix `a3f22424e`. So the page has
genuinely never been regenerated since the fix — it was not touched-but-unfixed.

Content probes in the SERVED bytes (live fetch and `origin/main` blob, byte-identical):
`152.7` x1, `20725` x2, `0.7636` x12.

- Table 30: `HR 0.7636 (0.7062 to 0.8258)` | № participants **20725** | № studies **3**
- Table 31: `200 per 1000 -> 152.7 per 1000` (correct under PH: 156.7)

- Table 30: `HR 0.7636 (0.7062 to 0.8258)` | № participants **20725** | № studies **3**
- Table 31: `200 per 1000 -> 152.7 per 1000` (correct under PH: 156.7)

## 4. Pooled estimates — all reproduced independently, exactly

Trial inputs: DAPA-HF harmonised **0.75 (0.65–0.85)** (NOT the 0.74 primary — 0.74 gives
0.7602/Q=0.5124 and does not reproduce), EMPEROR-Reduced 0.75 (0.65–0.86),
EMPEROR-Preserved 0.79 (0.69–0.90), DELIVER 0.82 (0.73–0.92) primary / 0.80 (0.71–0.91)
harmonised (UNSOURCED, see §6).

| pool | result | note |
|---|---|---|
| page k=3 | 0.7636 (0.7062–0.8258), τ²=0, Q=0.3837, I²=0%, HKSJ 0.6431–0.9068 | matches served page to the digit |
| corrected k=4 (DELIVER 0.80) | **0.7738 (0.7243–0.8268)**, τ²=0, Q=0.7698, I²=0%, HKSJ 0.6950–0.8616 | |
| corrected k=4 (DELIVER 0.82) | 0.7809 (0.7319–0.8332) | sensitivity |
| HFrEF pair (DAPA+EMP-Red) | 0.7500 (0.6808–0.8263) | |
| EF>40 pair (EMP-Pres+DELIVER 0.80) | 0.7953 (0.7264–0.8708) | |
| EF>40 pair (EMP-Pres+DELIVER 0.82) | 0.8069 (0.7395–0.8805) | |
| withdrawn 4-trial (naive) | 0.7785 (0.7296–0.8306) | |
| Vaduganathan FE, 5 trials | 0.7709 (0.7241–0.8208) | published 0.77 (0.72–0.82) |

"modified HKSJ" = the `q = max(1, ...)` floor firing (Q < k-1 in every pool here).

**Direction: omitting DELIVER moved the estimate 0.7738 -> 0.7636. The omission flattered
the intervention.** Invariant to the 0.80/0.82 choice.

Denominators: k=3 = 14,462; k=2 = 11,007; k=4 = **20,725**. `20,725` is exactly right for
k=4 and is printed against a k=3 pool — the denominator path sees DELIVER while the
contributor path does not. Corroborated externally: 20,725 + SOLOIST 1,222 = 21,947 =
Vaduganathan's n exactly; 6,263 + 5,988 = 12,251 = its EF>40 subset n exactly.

## 5. Other confirmed defects in the served bytes (probes included)

- **Eligibility/poolability conflated.** Both present: *"Eligible trials that do not
  contribute: No trial is in this category"* and *"The eleven ELIGIBLE-but-not-poolable
  trials …"*. Table 39 has a header row and **no body rows**; its heading carries unfilled
  placeholders *"32 screened, — included, — excluded, — not-assessable"*; and it contains a
  corrupted token *"reporting a quantity s10.9 does not permit combining"*. The eleven are
  asserted and never enumerated (`PRESERVED-HF`, `DEFINE-HF`, `EMPERIAL` all x0 on the page).
- **Undeclared phase criterion, polarity inverted.** Query 1 (narrower, "missed an included
  trial") = `phase=[PHASE3,PHASE4]`. Query 2 (**broader, "covers the included set"**) =
  `phase=[PHASE3]`, run 2026-08-19, 56 records. The comprehensive query carries the narrower
  phase filter. Concrete miss verified on CT.gov: **DAPA ACT HF–TIMI 68 = NCT04363697,
  PHASE4, enrolment 2,401 ACTUAL, COMPLETED, `hasResults: true`.**
- **GRADE renderer emits a constant.** All five domains, on BOTH the k=3 and k=2 blocks
  (10 rows), render `<td class="cert-state good">no downgrade</td>` with Levels `—`, while
  the Reason cell in the same row says *"Rated down one level because some concerns is not
  low"* and the stored steps read `risk_of_bias -1 … imprecision -1`. Not a two-domain
  mismatch — a hardcoded verdict. Hand to the NMA lane (FINDING 0 class).
- **Table 7's recompute check cannot fail.** It reports *"AGREES — the stored point lies
  between the fixed-effect and DerSimonian-Laird estimates"*, but τ²=0 makes FE and DL
  identical (both 0.7636, 0.7062–0.8258), so "between" is vacuous and it cannot discriminate
  the declared REML from either.
- **DELIVER's exclusion is registry-derived, verbatim.** Table 38: *"NONE AT ANY RANK. Every
  heart-failure composite it **registers** — primary and secondary — includes an urgent
  heart-failure visit. This is why pool A is k=3 and not k=4."*

## 6. OPEN BLOCKER — the corrected headline is not yet sourceable

`DELIVER 475/3131 vs 577/3132, HR 0.80 (0.71–0.91)` for the two-component endpoint
**could not be verified.** The DELIVER primary publication (*NEJM* 2022;387:1089–1098,
PMID 36027570, doi:10.1056/NEJMoa2206286, via PubMed) reports only:
three-component primary 512/3131 vs 610/3132 HR 0.82 (0.73–0.92); worsening HF 368 vs 455
HR 0.79 (0.69–0.91); CV death 231 vs 261 HR 0.88 (0.74–1.05).

The claimed counts are internally consistent (475<512, 577<610; crude RR 0.8235) and almost
certainly come from Vaduganathan 2022's harmonisation, but the Lancet supplement was not
obtained. **The EF>40 reproduction does NOT validate them**: DELIVER at 0.80 gives 0.7953
and at 0.82 gives 0.8069, against a published 0.80 (0.73–0.87) — both round to 0.80.

=> **Withdrawal is invariant to the DELIVER input, publication is not.**

That sentence is the whole decision rule for this blocker. Withdrawing the k=3 headline is
justified NOW, because k=4 exceeds k=3 under *either* candidate input (0.7738 with 0.80,
0.7809 with 0.82). Publishing `0.774` is NOT justified until the harmonised DELIVER HR is
sourced, because the published digits depend on which input is used.

**A NON-DISCRIMINATING CHECK IS NOT CORROBORATION.** The EF>40 reproduction was initially
offered — by this lane and then onward — as confirmation of DELIVER's two-component input.
It is not: 0.80 -> 0.7953 and 0.82 -> 0.8069 against a published 0.80 (0.73–0.87), so it
cannot distinguish the two candidates and confirms neither. A check that returns the same
verdict under both hypotheses has zero information about which is true, however exactly it
reproduces. This is the class of error we audit other people's papers for, and it was
caught here only because the sensitivity was run rather than assumed.

## 7. Store defect — localised further

`contributing_n()` returns the topic total because the two live pools hold no
`inputs.trials[*].by_outcome` rows (per commit `a3f22424e`'s "NOT FIXED, DELIBERATELY"
section). The reframing narrows it: the **denominator path already resolves DELIVER** while
the contributor path does not, so the two read different sets. A gate asserting
"N = sum of trials in the fit" must be **refuse-or-match** (None renders as an absence,
never as the topic total); computing the sum at the projector is the manufacture that was
deliberately refused.

## 8. NOT DONE (named, not dropped)

- k=3 headline withdrawal — the hand-edit instruction was **withdrawn by the requester**
  on 2026-09-03 after this lane refused it. Refusal upheld: hand-editing a 3.9 MB generated
  page would manufacture a rendered value that does not regenerate from its object (the
  exact class the NMA lane is chasing), and regenerating under tonight's memory pressure is
  the operation that exits 0 with an empty artefact. **A HALF-WITHDRAWAL IS WORSE THAN THE
  CURRENT STATE**: store desynchronised from page, flattering estimate still served.
  The agreed lever instead is to **stop serving the pages without regenerating anything** —
  a reversible file operation on the published surface. Serve path to be identified and
  REPORTED BEFORE ANY ACTION; if ambiguous, leave the pages served and carry the exposure.

- **Do not work from `E:`.** All of §1's paths are on the external drive that detached
  two days ago, taking seven unpushed commits with it. This file survived only because it
  was written to `C:` and pushed with a content probe. Next session: clone from GitHub to
  `C:`, never `--shared`, never from `F:`.
- Detector suite D1–D8, incl. the registry-as-world detector across its three instances
  (DELIVER endpoint, RoB masking fields, tigecycline Study 306) — deferred by instruction.
- Rotavirus extraction rebuild; DELIVER restoration — deferred by instruction.
- Protocol comparison (DL vs REML, two- vs one-reviewer screening): **NOT_RUN** — no
  protocol document was available. The page itself states *"These methods were NOT
  prespecified before the search"*; the strings "two reviewer" / "one screener" appear x0.
- `ssot/projectors_sof.py:192` and the D1–D8 taxonomy are in **no memory file** (all 16
  greped). They existed only in transcripts. That is what this file is for.

---

# APPENDIX, 2026-09-03 — added when this file was re-landed in the repo that serves the site

## A1. Why this file moved, and the rule it cost us

This file was first written and pushed to `mahmood726-cyber/rapidmeta-staging`. That repo
**has no GitHub Pages site** (`gh api .../pages` -> 404), is not a fork of anything, and has
**no sync path** to this one: every reference to `rapidmeta-finerenone` inside it is a local
read path (`CORPUS = r"F:\rapidmeta-finerenone"`), and none is a push, deploy or sync.

The push was real and content-verified. It was verified against the wrong surface.

> **VERIFY A LANDING AGAINST THE SURFACE THAT SERVES IT, NOT THE ONE YOU PUSHED TO.**

> **THE PROBE ANSWERED A DIFFERENT QUESTION FROM THE ONE THAT MATTERED, AND I DID NOT NOTICE BECAUSE IT RETURNED THE SHA I EXPECTED.**

`git ls-remote origin` returning exactly the sha predicted is the most convincing possible
form of a check that is measuring the wrong thing. It is the "green and worthless" family,
and it fooled two people independently — the commits were reported onward as landed on the
strength of it.

And the reason it mattered here rather than being mere misfiling:

> **THE WARNING IS NOT MERELY IN THE WRONG PLACE — IT IS IN THE WRONG PLACE RELATIVE TO THE HAZARD IT GUARDS, WHICH IS THE ONE PLACEMENT THAT MAKES IT USELESS.**

The §1 control note exists to stop a cleanup pass from patching two deliberately-held
pre-fix files. Anyone doing that cleanup is working in **this** repo. That is why the file
now sits beside `ssot/do_not_rebuild.py` — the existing mechanical home for "do not patch
this" — rather than in a repo they have no reason to open. The staging copies are left in
place deliberately: deleting them is an unforced write and they cost nothing.

## A2. Two records that cut the OTHER way — a cleanup pass must not read these as failures

1. **The `_absolute_rows` fix itself was verified correctly.** `a3f22424e` is in THIS repo
   and was checked as an ancestor of THIS repo's `origin/main` (`d2d5069a3`) with
   `git merge-base --is-ancestor`. **That check was against the right surface.** The code
   fix is published. Only the documentation went astray. Do not let A1 cast doubt on it.

2. **`MSYS_NO_PATHCONV=1` breaks in the opposite direction from the bug it fixes.** It is
   required for `git show <ref>:<path>` in Git Bash (without it the colon-path is mangled to
   backslashes and the command fails **silently to empty output**, which reads as "file
   absent"). But with it set, `/e/...` is no longer translated to `E:\`, so
   `git -C /e/rm-work/rapidmeta` returns **"No such file or directory"** — which reads as a
   detached drive. Both failures are silent and both produce a confident wrong belief about
   infrastructure. **A workaround for one silent failure caused another, in the opposite
   direction.** Set it for `<ref>:<path>` operations only; never leave it exported.

## A3. IV_IRON_HF_REVIEW.html — NEITHER of the two hypotheses. It is four outcomes.

Checked read-only before regenerating, because a tile reading `RATE_RATIO 0.8066` over a
grid built from `HR 0.7957` is either a mislabel or a much larger defect.

It is neither. The page carries **four outcomes, each with its own measure and its own
absolute grid**:

| table | driving measure | value | 50/1000 printed | mult | survival |
|---|---|---|---|---|---|
| 66 | `RATE_RATIO` | 0.8066 (0.6856–0.9488) | 40.3 | 40.3 | **40.5** |
| 69 | `HR` | 0.7957 (0.6857–0.9233) | 39.8 | 39.8 | **40.0** |
| 72 | `RATE_RATIO` | 0.7645 (0.636–0.9191) | 38.2 | 38.2 | **38.5** |
| 75 | `HR` | 0.978 (0.7523–1.2714) | — | — | — |

Attribution was confirmed **numerically**, not by proximity: every printed value equals its
attributed measure times the baseline (50 x 0.8066 = 40.33, 50 x 0.7957 = 39.79,
50 x 0.7645 = 38.23, 100 x 0.978 = 97.8). So each grid really is driven by the measure
named above it.

**Two measures on one page is legitimate structure here**, not mixed pooling: recurrent-event
outcomes carry rate ratios and time-to-first-event outcomes carry hazard ratios. No estimate
mixes them. There is no label defect either — the labels are correct.

**The consequence for the fix: `_absolute_from_ratio` is right for BOTH.** A rate ratio acts
multiplicatively on the rate exactly as a hazard ratio acts on the hazard, so
`1 - (1 - p0)**v` is the correct conversion for `RATE_RATIO`, `IRR` and `HR` alike — which is
why the fixed function already dispatches all three to the same branch.

**Corrected defect count.** My sweep reported IV_IRON once, as a page, and quoted one row.
That was right per page and wrong per grid: this page carries **four** defective grids, not
one. Corpus-wide the correct statement is **2 pages / 6 grids** (SGLT2_HF 2, IV_IRON_HF 4),
not 2 of 2. The page-level `2 of 2` stands; the grid-level count was never taken.

## A4. REGISTERED — unfilled template on the served landing page

The index at `https://mahmood726-cyber.github.io/rapidmeta-finerenone/` serves literal
ellipsis placeholders inside its own audit block:

> "Extraction identifier checks — run …, covering **…** of **…** cards, with **…** flagged
> and **…** not measured at all"
> "**…** of **…** currently state they are ready"

Class: the placeholder-leak family (Python `None` / unfilled f-string token reaching rendered
output; see the three-layer defence — generator `js_val()` helper, regression test that
BLOCKS on bare placeholder tokens, and a commit-time rule).

**Aggravating factors, which are why this ranks above a normal placeholder leak:**
it is **above the fold on the landing page**, it is the **first thing a reviewer sees**, and
**the section that exists to prevent overclaiming is the one serving nothing.** A block whose
entire purpose is to state what has and has not been checked, stating neither.

## A5. This commit skipped seven gates, and says so on its face

`.githooks/pre-push` **line 229**, verified by reading it:

```sh
if [ -z "$CHANGED" ]; then
    echo "[pre-push] No *_REVIEW.html pages in this push; nothing to regression-check."
    exit 0
fi
```

A push carrying no `*_REVIEW.html` exits 0 **there**, before the harness gate (20
artefact-decidable detectors), before the regression gate, and before the block at line 408
— *"SEVEN REPO GATES WIRED, 2026-08-31. Each was written, tested, and CALLED BY NOTHING."*

This commit is documentation only. It therefore **skipped all of them, structurally** — not
because they passed. Recorded here as well as in the commit message, because

> **A COMMIT THAT LANDED BECAUSE A GATE WAS STRUCTURALLY UNREACHABLE SHOULD SAY SO ON ITS FACE.**

Same shape as the CI finding already in the lessons file: a green run can contain a skipped
step, and `conclusion == success` on the parent proves nothing about the child.
