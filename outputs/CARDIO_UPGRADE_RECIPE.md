# The HFrEF upgrade procedure, made operational

**Version:** 1.0 (2026-07-30) · **Derived from:** the HFrEF GDMT network audit
(`outputs/HFREF_INTEGRITY_GATES_2026-07-30.md`, `outputs/HFREF_FINDINGS_RESOLVED_2026-07-30.md`)
and validated end-to-end on the APIXABAN_ACS pilot
(`outputs/APIXABAN_ACS_PILOT_2026-07-30.md`).

One lane, one app, in this order. Do not skip ahead: several steps exist only because
skipping them produced a wrong answer on HFrEF or on the pilot.

Throughout: **every number and identifier by lookup, never by recall.** If you cannot
read a value from a primary source in this pass, state the evidence tier — do not gloss.

---

## Phase 0 — Preflight (5 min)

**0.1 Branch.** Work on `audit/cardio-<app>-<date>`. Never touch `main`,
`audit/hfref-integrity-gates-2026-07-30`, or `bias-adjusted-nma-adv`.

**0.2 Enumerate the variants.** One app ships as up to four files:
`X_AUTO_FULL_REVIEW.html`, `X_FULL_REVIEW.html`, `X_AUTO_REVIEW.html`, `X_REVIEW.html`.
```
ls X*_REVIEW.html
```
Some are ~1.5 KB redirect stubs (`<title>… - opening the full RapidMeta…`), some are
~900 KB apps. **A fix applied to one variant is not applied to the app.** Record which
variant is canonical (largest non-stub, richest ledger) and which others must be kept
consistent or explicitly left alone.

**0.3 Confirm the app's identity from its own `<title>`, not its filename.**
```
grep -oE '<title>[^<]{0,110}' X_AUTO_FULL_REVIEW.html
```
Four cardio-adjacent apps in this corpus have filenames that describe a different drug
from their content (`TIRZEPATIDE_ARDS` holds an andexanet app; `ICAGEN` holds an
edoxaban app). Audit what the file contains.

**0.4 Read the ledger before touching anything.**
```
python scripts/cardio_inventory.py --all      # or read outputs/cardio_inventory.json
```

---

## Phase 1 — Grep BOTH verdict surfaces (10 min)

**This is the rule that catches false-green badges. Never read one surface alone.**

| Surface | Where | How to read it |
|---|---|---|
| **A — machine verdict** | `window.__verdict = {...}` in an inline `<script>` | `grep -o '__verdict[^;]\{0,400\}'` |
| **B — visible badge** | `<div id="rapidmeta-integrity-badge">` | balanced-`<div>` walk, **not** a regex; see 1.3 |
| **C — the ledger itself** | `realData:{…}` | depth-1 key count |

**1.1 Extract all three and write down the trial count each asserts.** In the pilot,
surface B said `Trials: 2`, surface A said `n_trials_seen: 2`, and surface C carried
**4** trials. The audit covered half the pooled evidence and neither verdict surface
said so.

**1.2 Test badge colour against verdict content, not against the headline.**
`#15803d` green / "INTERNAL CHECKS PASSED" is **false green** whenever
`window.__verdict.counts` has any non-zero `P1_*` or `P2_*`, or a non-empty `reasons[]`.
A `p0_total` of 0 is not a pass; it is "no P0s".

> Pilot: the badge was green while `__verdict` listed
> `"2 AACT outcome-direction divergence(s)"` — the machinery had already detected the
> defect the gates later confirmed as CRITICAL, and the badge rendered green over it.
> **Read `reasons[]`. It often already names the bug.**

**1.3 Read the badge with a balanced-`<div>` walk, and check it against itself.**
The badge is one long single-line `<div>` containing nested `<div>`s. A regex that
matches "the badge" will match a prefix and silently leave the rest. Also scan the badge
body for **self-contradiction**: two different numbers for the same quantity.

> HFrEF: a partial replacement left "Trials: 28" beside the new "27 trials".
> Pilot: the badge says "10 internal-consistency rounds" in one sentence and
> "14 internal-consistency rounds" in the next. Both were shipped.

**1.4 Record the badge's method claims as claims to be checked**, e.g. "Audited via
AACT 2026-04-12 + PubMed". If your audit used the live ClinicalTrials.gov API rather
than that snapshot, the badge's provenance claim is still unverified after your pass —
say so.

---

## Phase 2 — Verify every extracted number to a primary source (60–120 min; the bulk)

For **each** trial row in `realData`:

**2.1 Resolve the PMID.** PubMed (`get_article_metadata`). Check three things people skip:
- Does the paper describe **this randomisation**? A design/protocol paper, a sub-study,
  or a pooled analysis cannot substantiate per-arm counts.
  *Pilot F4a: PMID 29898844 is the AUGUSTUS **protocol** paper — PubMed types it
  "Clinical Trial Protocol". HFrEF F1: RESOLVD cited a paper with no metoprolol arm.*
- Does PubMed's **`article_types`** match the ledger's `phase`?
  *Pilot: three of four rows said phase III; PubMed and the registry said phase 2, 2 and 4.*
- Is the **acronym** in the record? If not, an acronym-keyed search will fail and you may
  wrongly conclude no source exists. *HFrEF F3: SPICE's primary exists (PMID 10740141)
  but the acronym never appears in the PubMed record; the first audit called it unsourced
  and was wrong.* **Search by author + year + population before declaring a source absent.**

**2.2 Resolve the NCT against ClinicalTrials.gov API v2.** Pull `phases`,
`enrollmentInfo`, `designInfo.maskingInfo`, `armGroups`, `overallStatus`, `hasResults`,
and — critically — `resultsSection.outcomeMeasuresModule`.

**2.3 For every posted outcome, read the `unitOfMeasure` before using the value.**
**This is the single highest-yield check in the procedure.** ClinicalTrials.gov posts
many cardiology primary outcomes as:
- `"percentage of participants"` → a **proportion**. `value × denominator / 100` = a count. Valid.
- `"percentage of participants/100-pt years"`, `"Percentage per year"` → an **incidence
  rate over person-time**. `value × denominator / 100` is **not a count**. It is a
  fabricated number.

> Pilot F2a: APPRAISE-2's ledger counts 515 and 489 are exactly
> `3687 × 13.96/100` and `3705 × 13.20/100`, from a posted outcome in units of
> **events per 100 patient-years**. The true counts are 279 and 293. The ledger's
> figures exist in no document.
> Pilot F4b: AUGUSTUS's 284 and 413 are `1153 × 24.66/100` and `1153 × 35.79/100`
> from `"Percentage per year"` — and 1153 corresponds to **no arm of the trial**.

**2.4 Bind arms by group TITLE, never by group index.** ClinicalTrials.gov frequently
lists **placebo first** (`OG000 = Placebo`). An extractor that maps index 0 → treatment
inverts the trial.

> Pilot F2b: `tN = 3687` is APPRAISE-2's **placebo** denominator. F1b, F3c: same
> inversion in APPRAISE-1 and APPRAISE-J. Three of four rows had the arms backwards.

**2.5 Reconcile counts against percentages in both directions.** Back-compute the
percentage from the ledger's counts and compare to the source's stated percentage; then
forward-compute the count from the source's percentage and denominator. Agreement to
<0.1 pp is a verification. Disagreement is a finding. *HFrEF verified 12 of 15 rows this
way, all to <0.06 pp.*

**2.6 Triangulate — and record how many independent sources you actually reached.**
Target order: (1) the primary publication, (2) ClinicalTrials.gov posted results,
(3) FDA/EMA review documents, (4) prior published or Cochrane meta-analyses,
(5) open-access full text (PMC/Europe PMC). Two sources is a **2-source** verification —
label it that way. Do not describe a 2-source pass as "multi-source audit completed".

**2.7 Assign an evidence tier to every row and never gloss one.**

| Tier | Meaning |
|---|---|
| `VERIFIED_FULL` | Denominators **and** per-arm counts confirmed against the cited source |
| `VERIFIED_DENOM_ONLY` | Denominators confirmed; counts not stated in the accessible record — neither confirmed nor contradicted |
| `SECONDARY_CORROBORATED` | Read via two independent retrievals of a page you could not access directly (state the barrier, e.g. a Cloudflare check that was **not** circumvented) |
| `FINDING` | A discrepancy, a wrong identifier, or an unlocatable source |

`VERIFIED_DENOM_ONLY` is an honest limit, not a failure. *HFrEF: 8 of 28 rows.*

**2.8 Check the PICO of every row against the app's own question.** Comparator,
population, blinding, phase, and outcome. A row can be perfectly extracted and still not
belong.

> Pilot F4c: AUGUSTUS is apixaban **vs vitamin K antagonist** in patients with **atrial
> fibrillation**, open-label, phase 4 — pooled into an app asking about apixaban vs
> placebo in ACS.
> HFrEF: PARACHUTE-HF is Chagas cardiomyopathy and the only open-label trial in the
> network; He 2015 is idiopathic DCM only. Both retained, both disclosed.

**2.9 Never pool two outcomes as if they were one.** If rows carry different endpoints,
split into explicitly marked **co-primary** analyses.

> Pilot F2d: three rows are bleeding, one is an ischaemic composite. The pooled number is
> not an estimate of anything, whatever its value.

**2.10 Disclose arm pooling and arm dropping.** If dose arms are merged, state it and
test equivalence **on the outcome actually pooled** — not on the trial's own primary.

> HFrEF F4: He 2015's benazepril doses differ significantly (P=0.042) on the primary
> *composite*, but on all-cause death they are 11/97 vs 8/101, Fisher p=0.49 — the
> pooling is defensible **for that outcome**, and saying so requires the distinction.
> Pilot F1d/F3d: APPRAISE-1 drops 3 of 4 apixaban arms (53% of enrolment) and APPRAISE-J
> drops its 5 mg arm, both silently.

---

## Phase 3 — Run the integrity gates (10 min, automated)

```
python scripts/cardio_integrity_gates.py X_AUTO_FULL_REVIEW.html
echo $?     # non-zero when CRITICAL or HIGH findings exist
```

| Gate | What it does | Notes |
|---|---|---|
| **G1** | per-arm count plausibility: integer, `0 ≤ e ≤ N`, denominators agree | |
| **G1b** | effect recompute from the 2×2 | must reproduce to <1e-8 |
| **G2** | GRIM / GRIMMER | **N/A** for binary per-arm counts — no means or SDs to reconstruct. Report "N/A, not passed". A `P0_grim: 0` in `__verdict` **overstates**: it reads as a pass. |
| **G3** | Benford first-digit | needs **≥30** values. At k=4 there are 16 — the gate reports `UNDERPOWERED`, which is the honest answer, not "no signal". |
| **G4** | arm-balance ratio | advisory; explain every flag rather than dismissing it |
| **G5** | identifier well-formedness | NCT + PMID present and valid |
| **G6** | registry concordance: phase, enrolment, masking | applies **only** to registered trials |
| **G6b** | **rate-vs-proportion unit gate** | the Phase-2.3 check, automated; tries registry **and** ledger denominators |
| **G6c** | **arm orientation** | which registry group does each ledger slot actually reproduce? |
| **G6d** | **posted-results reconcilability** | trial has posted results but the count matches no arm of them → no located source |
| **G7** | Fragility Index (Walsh 2014, Fisher exact) | **trial-level only** — see below |
| **G8** | published-effect vs crude-2×2 direction | a row carrying HR<1 beside counts giving RR>1 is self-contradictory |

**3.1 Registry concordance is N/A, not passed, for unregistered trials.** State the
denominator: *"covers 9 of 27 trials; the other 18 predate ClinicalTrials.gov or are
registered elsewhere (EudraCT, ChiCTR), so concordance is N/A — there is no record to
concord with, and none is claimed."*

**3.2 The fragility index is UNDEFINED for indirect estimates.** Walsh's FI is defined on
an observed 2×2. An indirect network contrast has none. Computing one requires inventing
patients. *HFrEF: 16 of 17 CI-excludes-1 contrasts were purely indirect (`direct_k = 0`).*
**Never quote an FI for an indirect estimate, and say the fragility is unmeasurable
rather than favourable.**

**3.3 A gate that cannot fail is theatre.** Before trusting a gate run, confirm the gate
exits non-zero on a known-bad input and zero on a known-good one
(`python scripts/test_cardio_inventory.py` asserts both). Never read a gate's exit status
through a pipe without `${PIPESTATUS[0]}` or `set -o pipefail`.

**3.4 Fail loud on an unreachable source.** A registry timeout is **"not checked"**,
never "concordant".

---

## Phase 4 — Disposition, never silent deletion (30 min)

**4.1 One of five dispositions per finding**, each recorded with its evidence:

| Disposition | When |
|---|---|
| **Citation corrected** | the extraction was right, the provenance record was wrong |
| **Claim withdrawn** | *your own audit finding* was wrong — record that too |
| **Re-sourced** | a source was located that the first pass missed |
| **Quarantined** | no source exists for the value; retain the row **flagged**, with a stated reinstatement condition |
| **Counts corrected** | the source states a different number — reconcile **to the source** |

**4.2 Quarantine, do not delete.** Keep quarantined rows in a ledger JSON with the
condition for reinstatement, and make the app verifier **block** if a quarantined row is
deleted rather than flagged. *HFrEF: CARMEN quarantined, arm rows retained.*

**4.3 Never invent a number to resolve a discrepancy.** If a source's abstract and body
text disagree, keep what the source states, label the tier, and **quantify the impact of
the alternative** rather than switching. *HFrEF F1: the RESOLVD 3.4%-vs-3.7% residual was
closed as an inconsistency internal to the source, with the impact measured at 0.045 SE.*

**4.4 Re-source before quarantining.** *HFrEF F3: had SPICE been quarantined as the first
audit proposed, the network would have lost its only between-trial loop. It had a source.*

**4.5 Check whether the codebase already contradicts the ledger.** *HFrEF F2:
`hfref_eightcell_fit.R:377` already annotated CARMEN inadmissible while the fitted ledger
supplied its counts.* Grep the repo for the trial name before deciding.

---

## Phase 5 — Measure the consequence, and describe it honestly (20 min)

**5.1 Re-fit and produce a before → after anchor table.** Every headline number.

**5.2 Choose an admissible estimator and say why.** At k<10, DerSimonian-Laird is
inadmissible (`rules/advanced-stats.md`); use REML or Paule-Mandel, or a
Mantel-Haenszel fixed-effect summary. **At k=2, do not quote a τ² or I² as if
interpretable.**

**5.3 Say which direction the correction moved things, and refuse to describe a
provenance fix as an improvement.**

> HFrEF: removing CARMEN moved estimates **away** from the null and raised
> CI-excludes-1 from 12 to 17. The badge says this is "a provenance correction, **not** a
> result that got better."
> Pilot: the correction flips the sign — OR 0.850 favouring apixaban becomes OR 1.975
> against it, both nominally significant.

**5.4 State the structural consequence separately from the numerical one.** *HFrEF:
cyclomatic number fell 2 → 1 but **ICDF was unchanged at 1**, because the lost loop was
internal to one multi-arm study and had never been counted. The audit's expectation was
wrong and the report says so.*

---

## Phase 6 — Rewrite the verdict badge honestly (20 min)

**6.1 Replace the badge's ENTIRE inner content.** Locate it by balanced-`<div>` matching
and swap the whole block. **Partial replacement of a surface that states numbers is not
safe** — regex-and-append is what shipped the HFrEF 28-vs-27 contradiction.

**6.2 Reconcile surface A and surface B.** After the rewrite, `window.__verdict` and the
visible badge must assert the same trial count, the same finding count, and the same
verdict word. Fix both, or the next audit finds one lying.

**6.3 Running the gates does not earn a PASS.** It converts "untested" into "tested,
with N findings". Say which.

**6.4 The badge must state, in this order:**
1. The verdict word and why (`UNCERTAIN — N FINDINGS DISPOSITIONED, M QUARANTINED`).
2. `k` in the fitted analysis, and `k` on record if they differ, with the reason.
3. What was **tested and clean** — "a *tested* zero, not an untested one".
4. What is **N/A** and why — GRIM (binary outcome), registry concordance (unregistered trials).
5. Every quarantine, with its reason, and where the retained rows live.
6. Every claim **withdrawn as wrong**, including your own audit's errors.
7. The direction the anchor moved, framed as a correction not an improvement.
8. Indirect estimates marked as indirect, with fragility stated as **undefined**.
9. What is **still not done** — full text, inconsistency testing, snapshot concordance.
10. AMSTAR-2 confidence.

**6.5 Add a badge self-contradiction check to the verifier.** Label-anchored checks
verify the numbers the badge is *supposed* to state and are blind to a stale leftover
sentence asserting a different one. Assert that **every** trial-count and arm-row figure
anywhere in the badge equals the post-disposition value. Confirm the check fires on the
bug it was written for.

---

## Phase 7 — Transparency ledger (15 min)

Write `outputs/<app>_source_verification.json` carrying, **per number**: the ledger value,
the source value, the exact quoted source text, the identifier and DOI, the evidence tier,
and the finding with its proposed fix. Plus:
- a `summary` with the tier counts,
- a `consequence_measured` block naming the estimator and why it is admissible,
- an explicit **`not_tested`** list.

Attribute the tools used (PubMed, ClinicalTrials.gov API v2, Walsh 2014 for FI).

---

## Phase 8 — Verify the artefact, then flag for the cross-family gate (20 min)

**8.1 Re-run every check on the final file**, not on an intermediate:
```
python scripts/cardio_integrity_gates.py X_AUTO_FULL_REVIEW.html   # exit status
python scripts/test_cardio_inventory.py                            # scanner + gate self-tests
python scripts/cardio_inventory.py                                 # both surfaces re-read
```

**8.2 Render it.** Serve over HTTP, activate every tab, read the DOM, and check the
console. **Rendering catches defects the file-level gate misses** — the HFrEF badge
contradiction was found by serving the page and reading the DOM, after a file-level gate
had passed it. Confirm no stale pre-correction number survives anywhere in the rendered
text.

**8.3 Check div balance and inline-JS parse** after any HTML edit
(`<div[\s>]` vs `</div>`; no literal `</script>` in a template literal).

**8.4 Fix all variants or state which you did not.** See 0.2.

**8.5 Commit on the branch. Do NOT push.** State in the commit message: STAGED, not
pushed, pending a cross-family gate and an explicit go.

**8.6 Flag for the cross-family gate.** A new integrity claim must be reviewed by a model
of a **different vendor family** (Codex = openai, Claude = anthropic, agy routed to
**Gemini** = google). Routing agy to its Claude models is the same family as the reviewer
and does not decorrelate. Verify liveness with a real exec that names its own model —
a status page or a quota meter is not a liveness check.

**8.7 Push ≠ deploy.** If you are later cleared to push, confirm which ref the deploy
pipeline tracks. A feature-branch push creates a remote branch and triggers no deploy when
the pipeline tracks `main`. Say "on GitHub, NOT live" whenever the pushed ref ≠ the deploy ref.

---

## The seven rules that catch the most

1. **Grep both verdict surfaces.** `window.__verdict` and the visible badge disagree far
   more often than either is wrong alone — and `reasons[]` often already names the bug.
2. **Read `unitOfMeasure` before using a posted value.** Rate ≠ proportion. This one check
   found manufactured counts in half the pilot's rows.
3. **Bind arms by title, never by index.** Registries list placebo first.
4. **A count that reconciles with nothing has no source.** Quarantine it; do not pool it.
5. **Replace whole badges, never patch them.** Then check the badge against itself.
6. **N/A is not a pass.** GRIM on binary outcomes, registry concordance on unregistered
   trials, fragility on indirect estimates — all undefined, none passed.
7. **A provenance correction is not a better result.** Say which direction it moved and
   refuse to sell it as an improvement.
