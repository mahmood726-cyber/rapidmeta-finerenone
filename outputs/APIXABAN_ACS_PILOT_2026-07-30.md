# Pilot: APIXABAN_ACS run through the cardio upgrade recipe, end to end

**Date:** 2026-07-30 · **Branch:** `audit/cardio-program-2026-07-30` · **Status:** STAGED, NOT PUSHED
**App:** `APIXABAN_ACS_AUTO_FULL_REVIEW.html` (911 KB) + `APIXABAN_ACS_AUTO_REVIEW.html` (redirect stub)
**Recipe:** `outputs/CARDIO_UPGRADE_RECIPE.md` · **Gate output:** `outputs/apixaban_acs_integrity_gates.json`
**Transparency ledger:** `outputs/apixaban_acs_source_verification.json`

**No app file was modified.** This pilot verifies the recipe and estimates effort. §7 lists
exactly what would change; nothing in §7 has been applied.

> **Why this app.** Rank 14 of 107 by upgrade value, importance 5, k=4, green badge, trial
> counts disagreeing across surfaces — the **modal** single-drug cardiology app rather than
> an outlier. It is not HFrEF, not on the HFrEF branch, and all four of its trials have
> posted ClinicalTrials.gov results, so every number in it was checkable. That last property
> is what makes it a fair test: nothing below is excused by inaccessible evidence.

---

## 1. Phase 0–1 — Both verdict surfaces, and what they disagree about

Three surfaces state a trial count. They do not agree.

| Surface | Value |
|---|---|
| Visible badge (`#rapidmeta-integrity-badge`, green `#15803d`) | `INTERNAL CHECKS PASSED` · Fabrication-risk score **0.275** · **Trials: 2** |
| `window.__verdict` | `"verdict": "STABLE"`, `"n_trials_seen": 2`, `"p0_total": 0` |
| `realData` ledger | **4 trials**, 8 arm rows |

**Badge findings, before any data was checked:**

**B1 — false green.** The badge says `INTERNAL CHECKS PASSED` in green. `window.__verdict`
carries `P1_aact_concord: 2`, `P2_evidence_incomplete: 2`, `P2_aact_advisory: 2` and three
reasons. `p0_total: 0` means "no P0s", not "passed".

**B2 — the verdict object already named the bug.** `reasons[]` contains
**`"2 AACT outcome-direction divergence(s)"`**. That is precisely the defect the gates below
confirm as CRITICAL: rows whose counts point the opposite way to the effect estimate beside
them. **The machinery detected it, and the badge rendered green over it.** This is the single
most important observation in the pilot — the corpus's own audit output is more honest than
its badges.

**B3 — the audit covered half the evidence, silently.** Both verdict surfaces say 2 trials.
The app pools 4. Nothing on the page says which two were audited.

**B4 — the badge contradicts itself inside its own body.** Sentence one:
*"AACT 2026-04-12 + PubMed + **10** internal-consistency rounds"*. Sentence two:
*"Audited via AACT 2026-04-12 + PubMed + **14** internal-consistency rounds"*. Same badge,
two numbers, same quantity. This is the HFrEF 28-vs-27 defect class, shipped.

**B5 — `P0_grim: 0` overstates.** GRIM is **not applicable** to binary per-arm counts —
there are no means to reconstruct. A zero reads as a pass.

**B6 — the two variants disagree about whether an audit exists.** The `_AUTO_REVIEW.html`
stub has **no badge and no `__verdict`**. Same app, two files, one asserting PASSED and one
asserting nothing.

**B7 — the method claim is unverified even after this audit.** The badge names the
**AACT 2026-04-12 snapshot**. This audit used the live ClinicalTrials.gov API v2. Concordance
against the snapshot itself remains unchecked.

---

## 2. Phase 2 — Source verification, all four trials

Every PMID resolved against PubMed; every NCT against ClinicalTrials.gov API v2 including
posted results. Nothing below is from recall. Full evidence with quoted source text in
`outputs/apixaban_acs_source_verification.json`.

**All four trials have posted registry results. Not one of the eight arm rows survived
verification.**

| Ledger row | True identity | Ledger 2×2 | Source 2×2 | Verdict |
|---|---|---|---|---|
| `NCT00313300` "Alexander 2009" | **APPRAISE (APPRAISE-1)** | 18/611 vs 18/317 | apixaban 2.5 mg 18/315 · placebo 18/599 | **FINDING** — arms inverted, phase wrong, sources mixed |
| `NCT00831441` "APPRAISE-2" | **APPRAISE-2** | 515/3687 vs 489/3705 | apixaban **279/3705** · placebo **293/3687** | **FINDING** — counts manufactured, arms swapped |
| `NCT00852397` "Ogawa 2013" | **APPRAISE-J** | 17/52 vs 19/49 | apixaban 2/49 and 2/50 · placebo 1/52 | **FINDING** — counts reconcile with nothing |
| `NCT02415400` "Lopes 2018" | **AUGUSTUS** | 284/1153 vs 413/1153 | apixaban 10.5% of 2290 · VKA 14.7% of 2259 | **FINDING** — wrong paper, counts manufactured, wrong PICO |

### 2.1 The root cause: a rate read as a proportion

**This is one bug, and it explains most of the corrupted numbers.**

ClinicalTrials.gov posts each outcome with a `unitOfMeasure`. For APPRAISE-2 that unit is
**`"percentage of participants/100-pt years"`** — an incidence rate over person-time. For
AUGUSTUS it is **`"Percentage per year"`**. The extractor treated both as a percentage of
participants and multiplied by an arm denominator:

| Trial | Posted value | × denominator | = ledger count | Truth |
|---|---|---|---|---|
| APPRAISE-2 | 13.96 (placebo) | × 3687 / 100 = 514.6 | **515** | 293 |
| APPRAISE-2 | 13.20 (apixaban) | × 3705 / 100 = 489.1 | **489** | 279 |
| AUGUSTUS | 24.66 (apixaban) | × 1153 / 100 = 284.3 | **284** | 10.5% of 2290 |
| AUGUSTUS | 35.79 (VKA) | × 1153 / 100 = 412.7 | **413** | 14.7% of 2259 |

All four reproduce to under one unit. **These counts appear in no document.** The APPRAISE-2
publication states its primary plainly: *"279 of the 3705 patients (7.5%) assigned to
apixaban … 293 of the 3687 patients (7.9%) assigned to placebo"* — the same abstract that
supplies the 13.2 and 14.0 per-100-patient-year rates the extractor mistook for proportions.
The correct numbers were in the sentence it read.

Worse for AUGUSTUS: the denominator **1153** matches no arm. The registry's arms are 2290 and
2259; 1153 ≈ 4614/4, a quarter of total enrolment. **Both ledger arms are given the same
invented denominator.**

### 2.2 Arms bound by index, not by title — three of four trials inverted

ClinicalTrials.gov lists **Placebo as group `OG000`** in APPRAISE-1, APPRAISE-2 and
APPRAISE-J. The extractor mapped group index 0 to "treatment":

- **APPRAISE-2:** ledger `tN = 3687` is the **placebo** denominator; `cN = 3705` is apixaban's.
- **APPRAISE-1:** ledger `tN = 611` is the publication's **placebo** n; `cN = 317` is apixaban 2.5 mg.
- **APPRAISE-J:** ledger `tN = 52` is the **placebo** n; `cN = 49` is an apixaban n.

APPRAISE-1 is the clearest harm. The app reads apixaban bleeding as 18/611 = **2.9%** against
placebo 18/317 = **5.7%**. The trial found the opposite: apixaban increased major/CRNM
bleeding dose-dependently (2.5 mg HR 1.78, 10 mg QD HR 2.45), and its two highest-dose arms
were **stopped for excess bleeding**. The app inverts the trial's central safety finding.

*Both ledger counts are 18, and 18 is recoverable both as 3.0% × 599 (placebo) and as
5.7% × 315 (apixaban 2.5 mg). The identical 18/18 is an artifact of two different
percentages on two different denominators — not a coincidence in the data.*

### 2.3 APPRAISE-J: counts with no located source

The publication states: *"major or clinically relevant nonmajor bleeding occurred in
**2 patients (4.1%) in each apixaban treatment group and 1 patient (2.0%) in the placebo
group**"*. The registry posts 4.1%, 4.1% and 2.0% on denominators 49, 49 and 51 — recoverable
counts **1 and 2**.

The ledger carries **17 and 19**. An order of magnitude out, matching nothing in either
document, for the outcome the ledger's own `title` field names.

*17/52 = 32.7% and 19/49 = 38.8% would be plausible as an "any bleeding" tally, which the
paper reports only qualitatively. That is a hypothesis and is **not** used to justify the
numbers. Disposition: quarantine or re-extract.*

### 2.4 AUGUSTUS: wrong paper, and wrong PICO

**Wrong paper.** The ledger cites **PMID 29898844** = Lopes RD et al., *"An open-label, 2×2
factorial, randomized controlled trial … **Rationale and design** of the AUGUSTUS trial"*,
*Am Heart J* 2018;200:17-23. PubMed types it **"Clinical Trial Protocol"**. It reports no
outcome data and cannot substantiate any extracted count. This is the HFrEF RESOLVD finding
class exactly.

The results paper — located via the registry's own `referencesModule`, then confirmed in
PubMed — is **PMID 30883055**, *N Engl J Med* 2019;380(16):1509-1524.

**Wrong PICO.** AUGUSTUS randomised patients with **atrial fibrillation** who had an ACS or
PCI, comparing apixaban against a **vitamin K antagonist**. The registry's own brief title
begins *"A Study of Apixaban in Patients With Atrial Fibrillation"*. The other three trials
compare apixaban against **placebo** on top of antiplatelet therapy in ACS. AUGUSTUS is also
the only **open-label** (masking `NONE`) and only **phase 4** trial in an otherwise
double/triple-blind phase 2–3 set, and it is a **2×2 factorial** that cannot be represented
by a single 2×2 table without stating which factor is estimated.

This is borrowed evidence from a neighbouring PICO. It is invisible to a donor-string
contamination scan and only appears when each row's comparator and population are checked
against the app's own question.

### 2.5 Outcome mixing makes the pooled number meaningless

Three rows contribute **bleeding** outcomes. `NCT00831441` contributes an **ischaemic
composite** (CV death, MI, ischaemic stroke). They are pooled into one estimate. **Whatever
its value, that estimate is not an estimate of anything.** APPRAISE-2's own bleeding row is
available and unused: TIMI major bleeding 46/3673 vs 18/3642, HR 2.59 (1.50–4.46).

### 2.6 Phase wrong on three of four rows

| Trial | Ledger | Registry | PubMed article type |
|---|---|---|---|
| APPRAISE-1 | III | **PHASE2** | Clinical Trial, Phase II |
| APPRAISE-2 | III | PHASE3 | Clinical Trial, Phase III ✓ |
| APPRAISE-J | III | **PHASE2** | Clinical Trial, Phase II |
| AUGUSTUS | III | **PHASE4** | — |

Two dose-ranging phase 2 studies and a phase 4 trial are presented as phase 3 evidence.

### 2.7 Undisclosed arm dropping

| Trial | Ledger total N | Registry enrolment | Dropped |
|---|---:|---:|---|
| APPRAISE-1 | 928 | 1741 (53%) | apixaban 10 mg QD (318), 10 mg BID (248), 20 mg QD (221) |
| APPRAISE-J | 101 | 151 (67%) | apixaban 5 mg BID (50) |
| AUGUSTUS | 2306 | 4614 (50%) | half the factorial |

None of this is stated on the page.

---

## 3. Phase 3 — Gate battery result

```
python scripts/cardio_integrity_gates.py APIXABAN_ACS_AUTO_FULL_REVIEW.html   # exit 1
```

**9 CRITICAL · 9 HIGH · 1 MEDIUM · 4 ADVISORY**

| Gate | Result |
|---|---|
| **G1** per-arm count plausibility | **0 findings** — all 8 arm rows are non-negative integers with `e ≤ N`. *The arithmetic layer is clean. Every corrupted number here is internally plausible; that is why file-level checks passed it.* |
| **G2** GRIM / GRIMMER | **N/A, not passed** — binary per-arm counts only, no means or SDs to reconstruct |
| **G3** Benford | **UNDERPOWERED** — 16 values, needs ≥30. The honest answer is "cannot test", not "no signal". |
| **G4** arm balance | 1 advisory: APPRAISE-1 1.93:1 — an artifact of the inverted arms, not a randomisation feature |
| **G5** identifiers | 0 findings — all NCTs and PMIDs well-formed. *Well-formed and wrong: PMID 29898844 is valid and points at a protocol paper.* |
| **G6** registry concordance | 3 HIGH (phase), 3 ADVISORY (enrolment). **4 of 4 trials registered with posted results — concordance applies to all four, unusually.** |
| **G6b** rate-vs-proportion units | **4 CRITICAL, 4 HIGH** — the §2.1 root cause |
| **G6c** arm orientation | **1 CRITICAL** (APPRAISE-2 explicitly reproduces the Placebo group), 1 MEDIUM (APPRAISE-1 ambiguous because both counts are 18) |
| **G6d** posted-results reconcilability | **2 CRITICAL** — APPRAISE-J's 17 and 19 |
| **G7** fragility index | APPRAISE-1 **FI = 1** at p = 0.0486 — one event overturns it, and the significance is itself an artifact of the swap. APPRAISE-2 and APPRAISE-J not significant. |
| **G8** effect-vs-crude direction | **1 HIGH** — APPRAISE-2 carries HR 0.95 beside counts giving RR 1.058 |

**G6b, G6c and G6d did not exist before this pilot.** The battery inherited from HFrEF had
G1–G7 and would have reported: arithmetic clean, GRIM N/A, Benford underpowered, one
fragility finding, three phase discordances. **It would have missed every manufactured
count.** The three new gates are the pilot's main contribution to the recipe.

**The gate can also pass.** `scripts/test_cardio_inventory.py` asserts it returns zero
blocking findings on a clean synthetic ledger and non-zero on an `e > N` ledger — 15/15
tests pass. Building that test found a real crash: the fragility index called Fisher's exact
on an implausible 2×2 and raised `math domain error` instead of skipping the row.

---

## 4. Phase 5 — The consequence: the correction flips the sign

Estimator: **Mantel-Haenszel OR with Robins-Breslow-Greenland SE**. No τ² or I² is quoted —
at k < 10 DerSimonian-Laird is inadmissible (`rules/advanced-stats.md`) and a random-effects
τ² at k = 2 is not interpretable.

**As the app pools it now** (ledger numbers, 4 trials, bleeding and ischaemic mixed):

| Trial | 2×2 | OR |
|---|---|---|
| Alexander 2009 | 18/611 vs 18/317 | 0.504 |
| APPRAISE-2 | 515/3687 vs 489/3705 | 1.068 |
| Ogawa 2013 | 17/52 vs 19/49 | 0.767 |
| Lopes 2018 | 284/1153 vs 413/1153 | 0.586 |
| **Pooled** | k=4 | **0.850 (0.780–0.926)** — nominally significant, favours apixaban |

**Verified, coherent PICO** — apixaban vs placebo on top of antiplatelet therapy, ISTH major
or clinically relevant non-major bleeding; AUGUSTUS excluded (VKA comparator, AF population,
open-label, phase 4):

| Trial | 2×2 | OR |
|---|---|---|
| APPRAISE-1 apixaban 2.5 mg BID | 18/315 vs 18/599 | 1.956 |
| APPRAISE-J apixaban 2.5+5 mg | 4/99 vs 1/52 | 2.147 |
| **Pooled** | k=2 | **1.975 (1.223–3.189)** — nominally significant, apixaban roughly **doubles** bleeding |

**APPRAISE-2 reported on its own outcomes**, not pooled with bleeding trials:
- Ischaemic primary: 279/3705 vs 293/3687, crude OR 0.943; published **HR 0.95 (0.80–1.11), P=0.51 — not significant**.
- TIMI major bleeding: 46/3673 vs 18/3642; published **HR 2.59 (1.50–4.46), P=0.001**.

> **The app's live headline is on the wrong side of 1.0.** It reports a significant benefit
> where the verified evidence shows significant harm. This is not a marginal shift: apixaban's
> development in ACS ended because APPRAISE-2 was terminated for exactly this bleeding excess
> without a counterbalancing ischaemic benefit. The app currently reverses that conclusion.
>
> Stated as the recipe requires: **this is a provenance correction, not a result that got
> worse.** The evidence did not change. The app was wrong.

---

## 5. What the recipe got right, and what the pilot changed in it

**Held up unchanged:**
- **Grep both verdict surfaces.** Found four badge defects (B1–B4) before any data was touched.
- **Read `reasons[]`.** It already named the bug (B2).
- **Bind arms by title, not index.** Three of four rows inverted.
- **Check the cited paper substantiates the extraction.** Caught the AUGUSTUS protocol paper.
- **Check each row's PICO against the app's question.** Caught the AF/VKA contamination.
- **N/A is not a pass.** GRIM N/A, Benford underpowered — both honest non-results.

**Changed by the pilot:**
1. **New gate G6b — rate vs proportion.** Promoted to the recipe's highest-yield check
   (Phase 2.3). Found 4 CRITICAL manufactured counts.
2. **New gate G6c — arm orientation.** Mechanises the bind-by-title rule.
3. **New gate G6d — posted-results reconcilability.** A count matching no arm of posted
   results has no source. Found APPRAISE-J.
4. **Benford needs an explicit underpowered verdict.** At k ≤ 7 there are < 30 digits. The
   HFrEF report quoted a χ² because it had 28 trials; most cardio apps cannot.
5. **Fragility must skip rows failing G1** rather than crash on them.
6. **G6b must try the ledger's own denominators**, not only the registry's — the worst case
   (AUGUSTUS) invents a denominator matching no arm, and a registry-only search misses it.

---

## 6. Effort, measured

| Phase | Elapsed |
|---|---|
| 0–1 preflight + both surfaces | ~15 min |
| 2 source verification, 4 trials | **~80 min** (~20 min/trial) |
| 3 gate run | ~2 min (after development) |
| 4 disposition, 23 findings | ~45 min |
| 5 consequence measurement | ~25 min |
| 7 transparency ledger | ~20 min |
| **Total audit** | **~3 h 10 min** |
| Gate development (one-off, now reusable) | ~90 min |
| Phase 6 badge rewrite + Phase 8 verify/render — **not done** | est. ~40 min |

**Model: `95 min + 20·k + 5·findings`.** For this app: 95 + 80 + 115 ≈ 4.8 h including the
badge rewrite. At the corpus mean k = 3.6, budget **~3–4 h per app** steady-state.

---

## 7. Exactly what would change (nothing below is applied)

**Ledger — `realData` in both variants**

| Row | Change |
|---|---|
| `NCT00313300` | `name` → `"APPRAISE-1"`; `phase` → `"II"`; **swap arms** → `tE:18, tN:315` (apixaban 2.5 mg BID), `cE:18, cN:599` (placebo), registry-analysed denominators, source labelled; disclose that 3 apixaban arms (787 patients) are excluded |
| `NCT00831441` | `phase` stays `"III"`; **counts corrected** → `tE:279, tN:3705` (apixaban), `cE:293, cN:3687` (placebo); outcome marked as the **ischaemic** co-primary; add the bleeding co-primary row `46/3673 vs 18/3642`, HR 2.59 (1.50–4.46) |
| `NCT00852397` | `name` → `"APPRAISE-J"`; `phase` → `"II"`; counts **quarantined** pending a located source, or re-extracted as `tE:4, tN:99` (both apixaban arms) vs `cE:1, cN:52` (placebo) with the pooling stated |
| `NCT02415400` | `pmid` → `30883055`; `doi` → `10.1056/NEJMoa1817083`; `year` → `2019`; `name` → `"AUGUSTUS"`; `phase` → `"IV"`; `pubHR_UCI` → `0.81`; **excluded from the primary pool** (VKA comparator, AF population) or moved to a marked comparator-stratified analysis; factorial marginalisation stated |

**Analysis structure**
- Split into two **co-primary** analyses — safety (ISTH major/CRNM bleeding) and efficacy
  (ischaemic composite) — each marked. Never one pooled number across both.
- Headline becomes OR **1.975 (1.223–3.189)** for bleeding, k=2, apixaban vs placebo.
- Add an `indirect`/`comparator` marker to every row so a VKA-comparator trial can never
  silently join a placebo-comparator pool again.

**Badge — replace the entire inner content, both surfaces reconciled**

> **VERDICT: UNCERTAIN — 23 FINDINGS, 4 OF 4 TRIALS AFFECTED, 1 ROW QUARANTINED**
> Pool: **2 trials** (bleeding co-primary) · Quarantined: **1** (APPRAISE-J, counts unsourced)
> · Excluded on PICO: **1** (AUGUSTUS — vitamin K antagonist comparator, atrial-fibrillation
> population) · Arithmetic gates: **0 findings** · Provenance findings: **23**
>
> Per-trial gates were executed 2026-07-30. **Arithmetic is clean — a *tested* zero, not a
> pass:** all 8 arm rows satisfy count plausibility. That is exactly why the defects below
> survived: every corrupted number is internally plausible.
>
> **Counts corrected in 2 of 4 trials.** APPRAISE-2's 515/489 and AUGUSTUS's 284/413 were
> computed by multiplying a ClinicalTrials.gov posted value by an arm denominator, where the
> posted unit is **events per 100 patient-years** / **percentage per year** — a rate, not a
> proportion. Those counts appear in no source. APPRAISE-2's true primary is 279/3705 vs
> 293/3687, HR 0.95 (0.80–1.11), **P=0.51 — not significant**.
>
> **Arms were swapped in 3 of 4 trials** — ClinicalTrials.gov lists placebo first and the
> extraction bound arms by group index. **Phase was wrong in 3 of 4** (two phase 2
> dose-ranging studies and one phase 4 trial presented as phase 3).
>
> **Quarantined:** APPRAISE-J — ledger 17/19 reconciles with no arm of the posted results
> (recoverable counts are 1 and 2; the paper states 2, 2 and 1). Rows retained, not deleted.
>
> **Anchor moved, and it changed sign:** pooled OR **0.850 (0.780–0.926) → 1.975
> (1.223–3.189)**. The previous figure mixed a bleeding outcome with an ischaemic composite
> and rested on inverted arms. **This is a provenance correction, not a result that got
> worse** — apixaban roughly doubles major/CRNM bleeding, which is why APPRAISE-2 was
> terminated.
>
> **GRIM/GRIMMER: N/A**, not passed (binary counts, no means). **Benford: UNDERPOWERED** —
> 16 values, needs ≥30; cannot test, not "no signal". Registry concordance covers **4 of 4**
> trials, unusually — all have posted results.
>
> **Still not done:** full text of all four trials; FDA/EMA review documents; prior published
> or Cochrane meta-analyses. Verification is **2-source** (publication + registry), not
> multi-source. Concordance against the AACT 2026-04-12 snapshot named by the previous badge
> is unverified. AMSTAR-2 confidence: **CRITICALLY LOW**.

**`window.__verdict`** — must be rewritten to match: `verdict: "UNCERTAIN"`,
`n_trials_seen: 4`, the finding counts above, and `reasons[]` naming the unit error, the arm
swaps and the quarantine. **Both surfaces or neither.**

**Verifier additions**
- Badge **self-contradiction** check: every trial-count and arm-row figure anywhere in the
  badge must equal the post-disposition value. Confirm it fires on B4 (the 10-vs-14 rounds
  contradiction) before trusting it.
- Block if the quarantined APPRAISE-J row is deleted rather than flagged.
- Block if any row's comparator label is absent.

**Also fix the stub.** `APIXABAN_ACS_AUTO_REVIEW.html` carries neither surface (B6).

---

## 8. Not done, and not claimed

1. **No app file was modified.** §7 is a proposal.
2. **Phase 6 (badge rewrite) and Phase 8 (verify + render) were not executed.** In particular
   the app was **not rendered in a browser**. On HFrEF, rendering caught a badge
   contradiction that a passing file-level gate had missed.
3. **Verification is 2-source.** No FDA or EMA review document was consulted; no prior
   published or Cochrane meta-analysis of apixaban in ACS was consulted. The recipe's
   4-source triangulation was **not** achieved for any row.
4. **Abstract- and registry-level only.** Full texts were not read. Secondary-outcome per-arm
   counts were not sought.
5. **AACT snapshot concordance not tested.** The live API was used instead.
6. **The app's own analysis engine was not re-run.** The §4 figures were computed
   independently, outside the app; whether the app reproduces them is unverified.
7. **Publication bias, small-study effects and prediction intervals not assessed** — at
   k = 2–4 they are not assessable.
8. **No cross-family gate has run.** These are new integrity claims and require review by a
   model of a different vendor family before anything goes live.
9. **Nothing is pushed.** Staged on `audit/cardio-program-2026-07-30`. `main` is the deploy
   ref; pushing this branch would deploy nothing.

---

## Attribution

Source verification used **PubMed** (NCBI E-utilities, via the bio-research PubMed MCP
server) and the **ClinicalTrials.gov API v2**. Per-trial DOIs are recorded in
`outputs/apixaban_acs_source_verification.json`. Fragility index per Walsh M et al.,
*J Clin Epidemiol* 2014;67:622-628.

Primary sources, with DOI links as required by the PubMed terms of use:
- APPRAISE-1 — Alexander JH et al., *Circulation* 2009;119(22):2877-85. [DOI](https://doi.org/10.1161/CIRCULATIONAHA.108.832139)
- APPRAISE-2 — Alexander JH et al., *N Engl J Med* 2011;365(8):699-708. [DOI](https://doi.org/10.1056/NEJMoa1105819)
- APPRAISE-J — Ogawa H et al., *Circ J* 2013;77(9):2341-8. [DOI](https://doi.org/10.1253/circj.cj-13-0209)
- AUGUSTUS results — Lopes RD et al., *N Engl J Med* 2019;380(16):1509-1524. [DOI](https://doi.org/10.1056/NEJMoa1817083)
- AUGUSTUS design (the paper wrongly cited by the app) — Lopes RD et al., *Am Heart J* 2018;200:17-23. [DOI](https://doi.org/10.1016/j.ahj.2018.03.001)
