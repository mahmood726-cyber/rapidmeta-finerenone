# IV_IRON_HF_REVIEW.html — scope-lock fix and source-verification ledger

**Date:** 2026-07-30
**Branch:** `fix/iv-iron-hf-scope-lock-2026-07-30`
**File:** `IV_IRON_HF_REVIEW.html` (RapidMeta Cardiology, IV iron in heart failure, v12.5)
**Status:** staged and committed on the branch, **not pushed**. Cross-family gate + Mahmood's go required before publish.

---

## 1. The reported failure, and its actual root cause

An external review found the outcome selector reading **"All-cause mortality"** while every
trial displayed a different endpoint: recurrent-event composites, a win ratio, CV-death
composites. This is confirmed and reproduced. The cause is **two independent defects that
compose**, both in the outcome-selection layer:

**Defect 1 — the label and the binding were decoupled.**
`outcomeLabel("default")` returned the *modal outcome title* across the corpus of trials:

```js
outcomeLabel(key){const m=this._derivedOutcomeMap();
  if("default"===key||null==key||""===key){
    const entries=[...m.values()].sort((a,b)=>b.count-a.count);
    return entries.length>0?entries[0].title:"Primary outcome"}   // <-- modal title
```

Three of the four trials carried a row with `shortLabel:"AllCauseMortality"`, so
"All-cause mortality" was the most frequent title and became the visible label of the
`default` option. But `applyOutcomeScope("default")` bound each trial to **`outcomes[0]`** —
that trial's own primary composite. Label said mortality; binding said composite.

**Defect 2 — null-coalescing fallbacks leaked the previous scope's numbers.**

```js
oc ? (t.data.tE = oc.tE ?? t.data.tE, t.data.cE = oc.cE ?? t.data.cE, …)
```

When a selected row had `tE:null` (HEART-FID's mortality row did), `??` fell through to
whatever `t.data.tE` already held — the previously bound endpoint's count. Denominators were
worse: `null != oc.nT && (t.data.tN = oc.nT)` left `tN`/`cN` at the composite's values
entirely, which is how `336/569` came to be printed as a percentage.

**Defect 3 (found during the fix) — a post-load block that overwrote the scoped values.**
An inline `pooling-repair` routine near the end of the file copied `realData[id].tE/cE`
(the trial-level default counts) into `t.data` whenever the *scoped* row had no counts, and
force-set `effectMeasure` to `"HR"`. That is a direct scope-lock bypass: under the win-ratio
scope it would have injected HEART-FID's 131/158 death counts. Disabled, with the reason
recorded inline.

**Defect 4 (found during in-browser verification) — the Paper tab silently changed the scope.**
`PS.ensureAnalysisReady()` in the shared asset `assets/js/paper-studio.js` tested
`state.selectedOutcome` against each row's `shortLabel` and, on a miss, assigned
`trials[0].allOutcomes[0].shortLabel` — the same *"just take `outcomes[0]`"* heuristic behind
Defect 1, reimplemented in the Paper module. Because the state now holds a scope **key**
(`ALLCAUSE_MORTALITY`) while rows carry shortLabels, the test always missed, so merely opening
the Paper tab flipped the analysis scope from all-cause mortality to the recurrent composite —
bypassing `setOutcome`, leaving the selector showing one scope while the state held another.
Caught by walking all eight tabs and re-reading `state.selectedOutcome` after each. Neutralised
with an **app-local override** (a no-op `ensureAnalysisReady`) rather than an edit to
`paper-studio.js`, which is shared corpus-wide. Verified: the scope now holds across all eight
tabs. **The underlying `paper-studio.js` heuristic still ships to every other app** and warrants
a separate corpus sweep.

---

## 2. What the scope lock now does

* Every outcome row is **typed**: `scopeClass` (what is being measured), `unit`
  (`patients` | `events` | `continuous` | `hierarchical`) and `estimandType`
  (`RR` | `HR` | `RateRatio` | `WinRatio` | `MD`).
* The selector offers **scope classes**, not per-trial labels. Selecting
  *All-cause mortality (death from any cause)* admits only rows with
  `scopeClass === "all_cause_mortality"`. CV-death-alone, CV-death/HF-hosp composites
  (first-event or recurrent), HF-hospitalisation rows, hierarchical win ratios and
  functional outcomes are all rejected — they are not silently relabelled.
* `applyOutcomeScope` **clears every scoped field before rebinding**. No `??` fallback to a
  prior value survives a scope change. A trial with no row in the selected scope is excluded
  with a stated reason; it is never shown carrying another endpoint's numbers.
* A trial whose scoped row exists but is not a patient-count is **shown with its true
  estimand and excluded from pooling**, with the reason printed on the card.
* **Percentages are computed only when `unit === "patients"`.** Recurrent-event totals render
  as "N vs M total events" plus the published per-100-patient-year rates, never as a
  proportion of the randomised n.
* `default` is now labelled *"Trial-registered primary endpoint (mixed estimands — not
  pooled)"* and pools nothing: across these four trials the registered primaries are a
  continuous 6MWD difference, two recurrent-event rate ratios and a hierarchical win ratio.
* Pooling refuses to run below k = 2 on the selected scale, reporting the reason instead of
  the previous `NaN` point estimate with `I² = 100%`.

Fresh load lands on **All-cause mortality**, effect measure **AUTO** (resolves to RR from
counts here, since only one trial reports a mortality HR), **k = 3 of 4**, pooled
**RR 0.90 (95% CI 0.76–1.07)**, I² = 0% (Q(2) = 1.3, p = 0.536), HKSJ 0.62–1.30,
prediction interval 0.60–1.34.

> **Note for review:** the app's protocol PICO still names *"CV Death or HF Hospitalization"*
> as the review's primary outcome, while the enforced landing scope is all-cause mortality.
> That divergence is deliberate and visible: under the corrected typing the protocol's own
> primary outcome is **not poolable** across these trials (IRONMAN and AFFIRM-AHF report it as
> a recurrent-event rate ratio; only AFFIRM-AHF reports a time-to-first-event hazard ratio,
> k = 1). Whether to amend the protocol or keep mortality as the pooled surface is a
> review-design decision, not a code decision, and is left to Mahmood.

---

## 3. Per-trial source verification

Every review point was checked against the trial's own primary source. Values retrieved
2026-07-30 via PubMed (`pubmed` MCP), PubMed Central, Europe PMC, and the ClinicalTrials.gov
API v2 results section.

### CONFIRM-HF — NCT01453608
Ponikowski et al., *Eur Heart J* 2015;36(11):657–668. PMID 25176939, PMC4359359,
DOI [10.1093/eurheartj/ehu385](https://doi.org/10.1093/eurheartj/ehu385). Full text read.

| Field | Was displayed | Verdict | Corrected value | Source |
|---|---|---|---|---|
| "CV death or HF hospitalization" 25/150 vs 36/151, HR 0.69 (0.41–1.17) | shown as the trial's contribution under the mortality selector | **WRONG — unsourced** | **row removed** | No such counts and no HR 0.69 appear anywhere in the primary publication. What it does report: any-cause first hospitalisation 32 (21%) vs 44 (29%), HR 0.71 (0.45–1.12); first worsening-HF hospitalisation HR 0.39 (0.19–0.82), P=0.009; post-hoc death-or-first-worsening-HF-hospitalisation HR 0.53 (0.30–0.95), P=0.03. None is 25/36 or 0.69. |
| All-cause mortality | absent | **added** | **12/150 vs 14/151** | Abstract: "The number of deaths (FCM: 12, placebo: 14 deaths)". Results/Follow-up: "Of the 150 patients assigned to FCM, 29 (19.3%) … did not complete the study of whom 12 (8.0%) patients died. Of the 151 patients assigned to placebo, 24 (15.9%) … of whom 14 (9.3%) patients died." Denominators are the FAS (150/151), **not** the 152/152 randomised. |
| All-cause mortality HR | — | **not carried** | none | The publication reports no hazard ratio for all-cause death; only incidence, FCM 8.9 vs placebo 9.9 per 100 patient-years at risk. The reviewer-supplied "HR 0.89 (0.41–1.93)" **could not be confirmed** against the primary text and is therefore not displayed. |
| Post-hoc death-or-first-HF-hosp composite | reviewer cited "18 vs 33 patients, HR 0.53" | **partly confirmed** | HR 0.53 (0.30–0.95), P=0.03 carried; counts not carried | HR confirmed verbatim. The per-arm counts 18 vs 33 are **not** in the publication text; not displayed. |
| Registered primary | mislabelled | corrected | Δ6MWD at week 24, 33 ± 11 m, P = 0.002 (continuous, not poolable) | Abstract + Results/Primary end-point. |

### AFFIRM-AHF — NCT02937454
Ponikowski et al., *Lancet* 2020;396(10266):1895–1904. PMID 33197395,
DOI [10.1016/S0140-6736(20)32339-4](https://doi.org/10.1016/S0140-6736(20)32339-4).
Plus ClinicalTrials.gov NCT02937454 **posted results** (raw API v2 fetch).

| Field | Was displayed | Verdict | Corrected value | Source |
|---|---|---|---|---|
| Primary 293/558 and 372/550 with percentages | shown as patients | **WRONG typing** | **293 vs 372 total recurrent events**, 57.2 vs 72.5 per 100 patient-years, rate ratio **0.79 (0.62–1.01)**, p=0.059; n = 558 vs 550 | Lancet abstract verbatim. Registry confirms `unitOfMeasure: "Events"` with `denoms: Participants 558/550`. The invalid percentages are removed. |
| All-cause mortality 65 vs 74, HR 0.93 (0.78–1.10) | shown | **WRONG — unsourced, and wrong in direction** | **98/558 vs 96/550, HR 0.99 (0.75–1.31), p=0.944** | ClinicalTrials.gov posted results, outcome "All-cause Mortality" (OTHER_PRE_SPECIFIED, up to 52 weeks, "Number of participants who died"), Full Analysis Set. The corrected estimate is null, not favourable. |
| CV death 77/558 vs 78/550, HR 0.96 | — | confirmed, but **quarantined** | 77/558 vs 78/550, HR 0.96 (0.70–1.32), p=0.809 | Registry "CV Mortality". Confirms the reviewer's figures exactly. Selectable only under the *Cardiovascular death only* scope; it can no longer stand in for all-cause mortality. |
| HF-hosp-or-CV-death, first event | — | added | 181/558 vs 209/550, HR 0.80 (0.66–0.98), p=0.030 | Registry secondary "Composite of HF Hospitalisations or CV Death". |

### IRONMAN — NCT02642562
Kalra et al., *Lancet* 2022;400(10369):2199–2209. PMID 36347265,
DOI [10.1016/S0140-6736(22)02083-9](https://doi.org/10.1016/S0140-6736(22)02083-9).

| Field | Was displayed | Verdict | Corrected value | Source |
|---|---|---|---|---|
| 336/569 and 411/568 with percentages | shown as patients/deaths | **WRONG typing** | **336 vs 411 total recurrent events**, 22.4 vs 27.5 per 100 patient-years, rate ratio **0.82 (0.66–1.02)**, p=0.070; n = 569 vs 568, median follow-up 2.7 y | Lancet abstract verbatim. Percentages removed; presented under the composite scope, not mortality. |
| All-cause mortality 166 vs 180, HR 0.93 (0.75–1.15) | shown | **WRONG — unsourced** | **UNAVAILABLE — deliberately blank** | Could not be obtained from any accessible primary source: the Lancet report is not open access, has no PMCID and is not in Europe PMC (`isOpenAccess: N`, `inEPMC: N`); ClinicalTrials.gov NCT02642562 has **no posted results section** (`hasResults: false`). All-cause mortality *is* a registered secondary outcome, so the value exists behind the paywalled full text. It is **not** reconstructed from the rounded ~32% vs 34% in the review, per instruction. IRONMAN is excluded from the mortality pool with this reason displayed on its card. |

### HEART-FID — NCT03037931
Mentz et al., *N Engl J Med* 2023;389(11):975–986. PMID 37632463,
DOI [10.1056/NEJMoa2304968](https://doi.org/10.1056/NEJMoa2304968).
Plus ClinicalTrials.gov NCT03037931 **posted results**.

| Field | Was displayed | Verdict | Corrected value | Source |
|---|---|---|---|---|
| "win ratio 1.02 (99% CI 0.87–1.18; P=0.78)" | shown | **WRONG** | **unmatched win ratio 1.10, 99% CI 0.99–1.23**, Wilcoxon–Mann–Whitney **P = 0.02** against a prespecified significance level of **0.01** | NEJM abstract verbatim. (The review cited P=0.019; the abstract reports it to two decimals as 0.02. Either way it does not meet the prespecified α of 0.01.) |
| HR 0.93 (0.81–1.06) attached to the hierarchical primary | shown | **WRONG attachment, and unsourced** | **removed, not reassigned** | A win ratio is not a hazard ratio. No CV-death/HF-hospitalisation hazard ratio of 0.93 could be verified in the NEJM abstract or the registry results, so it is removed rather than moved to a CV-death/HF-hosp row that would itself be unsourced. |
| 560 / 581 over 1532 / 1533 | in the evidence highlights | **WRONG — unsourced** | **removed** | No statement matching 560 or 581 exists in the NEJM report or the posted registry results. |
| All-cause mortality | absent / HR 0.95 (0.79–1.14) unsourced | **added (counts); HR removed** | **131/1532 vs 158/1533 (8.6% vs 10.3%)** at 12 months | NEJM: "Death by month 12 occurred in 131 patients (8.6%) in the ferric carboxymaltose group and 158 (10.3%) in the placebo group." Independently confirmed by the registry outcome "Number of Deaths" (1 year): 131 of 1532 vs 158 of 1533. No mortality hazard ratio is reported in either source, so none is displayed. |
| HF hospitalisations to 12 months | — | added | 297 vs 332 total hospitalisations (events) | NEJM. The registry lists the same 297/332 under a "Participants" unit label; the NEJM wording ("a total of 297 and 332 hospitalizations") is taken as authoritative and the row is typed as **events**. |
| Δ6MWD to 6 months | — | added | 8 ± 60 vs 4 ± 59 m (registry means 8.179 / 3.979) | NEJM + registry. |

---

## 4. Corpus-wide fixes applied

**(1) `safeRob` sanitiser — resolved unknown ratings to the most favourable level.**

```js
// before
safeRob = rob => { const valid=["low","some","high"];
  return Array.isArray(rob) ? rob.map(r=>valid.includes(r)?r:"low")
                            : ["low","low","low","low","low"] }
```

Every trial in this app stores `"some-concerns"`, which is not in `valid`, so it was coerced
to `"low"` — and since the overall judgement is `rob.includes("high")?"high":rob.includes("some")?"some":"low"`,
all four trials rendered **"Low Risk"** when their true rating is **"Some concerns"**.
Now: known aliases (`some-concerns`, `some concerns`, `unclear`, `moderate`, `medium`) map to
`"some"`; `serious`/`critical` map to `"high"`; **any unrecognised value resolves to `"some"`,
never `"low"`**, and a non-array resolves to all-`"some"`. Verified in-browser: HEART-FID now
renders **Some Concerns**.

**(2) Both verdict surfaces made honest and brought into agreement.**

| Surface | Before | After |
|---|---|---|
| `window.__verdict` (line ~33062) | `UNCERTAIN`, all counts 0, `n_trials_seen: 0`, `reasons: []` | `UNCERTAIN`, `grade: SOUND`, `scope: ALLCAUSE_MORTALITY`, `k_poolable: 3`, `k_included: 4`, `n_trials_seen: 4`, four explicit reasons |
| Grade badge (line ~1182) | green **"EVIDENCE GRADE: VERIFIED — externally validated vs a published meta-analysis; passes all gates"** | amber **"EVIDENCE GRADE: SOUND · VERDICT: UNCERTAIN — NOT externally validated…"** |
| Verify banner (line ~1184) | green **"✓ VERIFIED · k = 4 contributing trial(s) · externally validated … every displayed number was checked against its source"** | amber **"UNCERTAIN · all-cause mortality scope · k = 3 of 4 trials poolable · not externally validated"** |

The three now agree on verdict, k and external-validation status. The "externally validated"
claim was independently false: the only stored benchmark is `PUBLISHED_META_BENCHMARKS.MACE`
(Graham 2023, RR 0.84, 0.76–0.93), whose declared scope is **"CV death + HHF"** — a composite,
not mortality — and whose `k: 3` contradicts the four trials named in its own scope string.
`BENCHMARK_OUTCOME_MAP` previously mapped `default`, `ACM` and `ACH` onto it, so an all-cause
mortality selection was being "validated" against a composite-outcome meta-analysis. It is now
bound to the composite scopes only, and the record is relabelled as not re-verified in this build.

---

## 5. Verification performed

* **JS syntax:** all 17 inline script blocks pass `node --check` after every patch step.
* **Structure:** `<div>` open/close delta unchanged from HEAD (−1, pre-existing); no literal
  `</script>` introduced.
* **In-browser** (served over HTTP, `localStorage` cleared atomically before load):
  * all 8 tabs render without throwing (protocol, search, screen, extract, analysis, report, paper, statistics);
  * **0 console errors**; the only console output is a `[pooling-repair]` advisory correctly naming IRONMAN as unpoolable;
  * scope binding checked across all 9 scopes + `default` — no value leaks between scopes; every non-matching trial shows null counts and a stated exclusion reason;
  * **0 occurrences of `NaN`** anywhere in the rendered document, in every scope × effect-measure combination tested;
  * no invalid percentages: the only percentages shown are 8.6/10.3, 17.6/17.5 and 8.0/9.3, each a genuine patients-with-event proportion;
  * both verdict surfaces read consistently.
* **Contamination gate:** `python scripts/clone_contamination_gate.py <file>` → **GATE OK, 0 hard findings** (1 pre-existing advisory WARN, identical before and after). `--selftest` → **SELFTEST PASS**, confirming the gate can actually fail.
* **Build gate:** `python scripts/build_gate.py <file>` → **BUILD OK, 0 hard violations**. One advisory WARN, `blank_counts_with_effect`, which is the intended consequence of this fix: rows that report an effect estimate without per-arm counts (CONFIRM-HF's HR 0.39 and HR 0.53, HEART-FID's win ratio) are now shown honestly as effect-only rather than being given fabricated counts.

---

## 6. Flagged, not changed (out of the scope of this task)

* **`e156-submission/assets/IV_IRON_HF_REVIEW.html`** is an older, unminified copy of this
  same app carrying the same defects (`tE: 560, cE: 581` for HEART-FID, the 25/150 vs 36/151
  CONFIRM-HF row, the same `safeRob`). It ships inside a submission bundle. It was **not**
  modified here to avoid silently diverging a submission asset from its own `paper.md` /
  `config.json`. It needs the same treatment before that bundle is submitted.
* **`FCM_HF_REVIEW.html`** is a *different* app over an overlapping trial set (it adds FAIR-HF
  and drops nothing). It carries its own unverified values — e.g. CONFIRM-HF as
  `tE:33, tN:152, cE:49, cN:152, HR 0.61 (0.39–0.94)` labelled *"Change in 6MWD at 24 weeks
  (HF hosp secondary endpoint)"*, which conflates a continuous endpoint with an event count.
  Not touched.
* **The `pooling-repair` scope-lock bypass is corpus-wide.** The identical block appears in a
  large number of `*_REVIEW.html` files (confirmed by grep in `ABATACEPT_PSA`, `ABATACEPT_RA`,
  `ABEMACICLIB_BREAST`, …). In any app with more than one typed outcome per trial it can
  re-inject the trial's default counts under a different endpoint's label. Worth a separate
  corpus sweep.

---

# Round 2 — TIER 1 (2026-07-30)

A second external review raised 39 issues plus a standing data-sourcing rule: pull numbers
from outside paywalls — published meta-analysis supplements first, then ClinicalTrials.gov
/AACT, FDA, EMA and open-access papers; for firewalled papers use their supplements. This
section records Tier 1 only. Tier 2 (the four-analysis rebuild) follows in a separate commit.

## T1.0 The invalid headline was already unreachable — and is now structurally impossible

The reported headline **"All-cause mortality: pooled HR 0.86 (0.77–0.97)"** — built by pooling
IRONMAN's rate ratio 0.82, AFFIRM-AHF's rate ratio 0.79, HEART-FID's secondary HR 0.93 and
CONFIRM-HF's misattributed 0.69 — does not occur in this build. Round 1's scope lock removed it
by typing every outcome row and refusing to bind a row whose unit is not `patients` into a
binary pool. Verified empirically: iterating all nine scopes plus `default`, no scope yields a
pool with more than one `unit`, and the mortality pool is built from 2×2 counts only.

Two guards were added so this is impossible rather than merely absent:

* `RapidMeta.poolingBasis()` returns `INVALID` and logs `[estimand-guard]` if a scoped pool ever
  mixes units. Every analysis render now prints its **pooling basis** above the results:
  *"Pooled from 2×2 patient counts as a RR. Effect estimates reported by the source publications
  (for example a hazard ratio) are shown per trial for reference but are NOT the pooled input: a
  hazard ratio is never combined with a count-derived risk ratio."*
* `trialHasPublishedHR()` now rejects any trial that is `_notPoolable`, `_outcomeExcluded` or
  `_scopeUnavailable`, whose `estimandType` is not `HR`, **or whose interval is not a 95%
  interval**. That last clause matters: HEART-FID's secondary HR carries a **96%** interval, and
  the SE formula divides the log-CI width by `2·z(0.975)`. Feeding a 96% interval through it
  understates the variance and overweights the trial.

Current mortality pool: k = 3, **RR 0.90 (95% CI 0.76–1.07)**, I² = 0%, HKSJ 0.62–1.30. The Wald
tile is now labelled *"Wald interval; the declared primary inference surface is the HKSJ interval
below"*, so the narrower interval cannot be read as the headline. The app states that the
interval crosses 1.0 and that there is no statistically significant difference; no significance
claim is made anywhere.

## T1.1 HEART-FID — win ratio and the secondary hazard ratio

**Win ratio — verified.** According to PubMed, Mentz et al., *N Engl J Med* 2023;389(11):975–986
([DOI](https://doi.org/10.1056/NEJMoa2304968), PMID 37632463) reports the primary hierarchical
composite as **unmatched win ratio 1.10, 99% CI 0.99 to 1.23, Wilcoxon–Mann–Whitney P = 0.02**,
against a **prespecified significance level of 0.01** — so it did not meet the threshold. Round 1
had already replaced the page's wrong "win ratio 1.02 (99% CI 0.87–1.18), P = 0.78". The review's
"P ≈ 0.019" is consistent with the abstract's two-decimal 0.02; the app carries 0.02 because that
is what the source prints.

**HR 0.93 — reinstated as a separate record, flagged unverified.** Round 1 deleted it as
unsourced. The reviewer is right that deleting it loses information: it is the *secondary*
time-to-first CV-death-or-HF-hospitalisation endpoint, not the hierarchical primary. It is now its
own row with `scopeClass: hf_cvdeath_composite_first`, `ciLevel: 0.96`, `poolable: false`,
`unverified: true`.

I could **not** verify it within the data-sourcing rule. It is absent from the NEJM abstract, from
the ClinicalTrials.gov NCT03037931 posted results (which carry only the three primary components:
deaths 131/158, HF hospitalisations 297/332, Δ6MWD 8.179/3.979 m), from the open-access FCM IPD
commentary and from the open-access six-trial review. The NEJM full text is paywalled. Its
provenance string says exactly this. It is barred from every pool by three independent mechanisms
(`poolable:false`, `unverified`, and the new 95%-interval requirement in `trialHasPublishedHR`).

## T1.2 Small-k diagnostics suppressed

A `K_GATES` table drives suppression at both the engine level (defence in depth) and the
presentation level (`applyKGates()`, called after every render). Each suppressed panel states its
threshold and reason instead of a number.

| Diagnostic | Threshold | Was showing at k=3 |
|---|---|---|
| Meta-regression | k ≥ 10 per covariate (Cochrane 10.11.5.1) | slope −0.0215, p = 0.723, **R² = 100.0%** |
| Funnel plot + Egger | k ≥ 10 (Cochrane 13.3.5.4) | intercept 0.094, p = 0.964, "suggests absence of publication bias" |
| Trim-and-fill | k ≥ 10 | k₀ = 0, adj RR 0.90 |
| L'Abbé plot | k ≥ 10 | "Clustering below the line supports the pooled estimate of benefit" |
| Galbraith plot | k ≥ 10 | radial outlier assessment |
| Copas | k ≥ 15 | "Robust — findings are insensitive to potential selection bias" |
| TSA / RIS | k ≥ 10 | RIS = 703, IF 21%, O'Brien–Fleming ±4.28 |
| NNT | pooled interval must exclude 1 | "At a baseline event rate of 10%, NNT ≈ 100" |
| Mantel–Haenszel | k ≥ 5 | concordance verdict |

Peto was already correctly withheld ("N/A — no rare-event studies"): event rates here are 8–18%,
far from the rare-event regime Peto requires.

One disclosure: **Mantel–Haenszel is itself a valid fixed-effect estimator at k = 3.** What is not
informative at k = 3 is the panel's framing of it as a *concordance check* on the random-effects
pool. It is suppressed per the review instruction, with that reasoning stated rather than implied
— this one is a presentational judgement, not a statistical necessity.

## T1.3 safeRob, verdict surfaces, and the false internal-checks banner

* **safeRob** — fixed in round 1 and re-verified: unknown ratings resolve to `"some"`, never
  `"low"`. All four trials store `"some-concerns"` and render "Some Concerns".
* **"INTERNAL CHECKS PASSED"** banner — replaced. It asserted a pass, printed a fabrication-risk
  score of 0.025 to three decimals, said "Trials: 4" while only 3 are poolable under the primary
  scope, and gave **two different audit-round counts (10 and 14) in adjacent sentences**. It now
  reads "INTERNAL CHECKS: NOT A PASS CERTIFICATE", states that the automated checks test internal
  consistency only and did not catch the scope and estimand defects, and drops the unreproducible
  round counts rather than picking one. Strip recoloured green → amber.
* **Version drift** — title/meta said v12.5, the exported R script header said v11.0 (×2) and the
  exported Python script said v11.0 (×2). All now v12.5.
* **Both verdict surfaces plus `window.__verdict`** updated and still in agreement (UNCERTAIN,
  k = 3 of 4).

## T1.4 "No external benchmark exists" was false — two now recorded

The page claimed benchmark type SELF-REFERENCE, "no external IPD/aggregate MA at protocol freeze",
while simultaneously storing a `Graham 2023` record of RR 0.84 (0.76–0.93) with `k: 3` over a scope
string naming **four** trials — internally contradictory and not traceable. Replaced with two real,
open-access-sourced benchmarks:

* **FCM individual-participant-data meta-analysis** (CONFIRM-HF + AFFIRM-AHF + HEART-FID, n = 4501;
  FCM only — IRONMAN is not in it). Total CV hospitalisations and CV death **RR 0.86 (0.75–0.98),
  p = 0.029**; co-primary total HF hospitalisations and CV death RR 0.87 (0.75–1.01), p = 0.076;
  total CV hospitalisations RR 0.83 (0.73–0.96); total HF hospitalisations RR 0.84 (0.71–0.98);
  time to first CV death or HF hospitalisation **HR 0.88 (0.78–0.99), p = 0.039**; time to first CV
  death or CV hospitalisation HR 0.89 (0.80–0.99). **No overall all-cause mortality benefit** —
  significant mortality reductions appear only in the TSAT < 15% subgroup. According to PubMed, via
  the open-access account in Kotit S, *Glob Cardiol Sci Pract* 2024;2024(2):e202410
  ([DOI](https://doi.org/10.21542/gcsp.2024.10), PMID 38746071, PMC11090186).
* **Six-trial IV-iron systematic review** (FAIR-HF, CONFIRM-HF, AFFIRM-AHF, IRONMAN, HEART-FID,
  FAIR-HF2; n = 7175; Bayesian, IPD from five trials). All-cause mortality **HR 0.82 (0.65–1.03)**
  at 12 months and **HR 0.92 (0.80–1.07)** over complete follow-up. According to PubMed, Anker SD
  et al., *Nat Med* 2025;31(8):2640–2646 ([DOI](https://doi.org/10.1038/s41591-025-03671-1),
  PMID 40159279, PMC12353798, open access).

**The reviewer is right that the 0.86 resemblance is coincidental.** The real 0.86 is a *rate ratio
for a CV-hospitalisation/CV-death composite* with CI 0.75–0.98 over three FCM trials. The app's old
headline was an *all-cause-mortality "HR"* with CI 0.77–0.97 over four trials of mixed estimands.
Different outcome, different estimand, different trial set, different interval. Neither benchmark is
a like-for-like comparator for the app's count-based mortality RR, and the verdict text now says so
rather than claiming validation.

## T1.5 Verification

* 17/17 inline script blocks parse (`node --check`) after every patch step; `<div>` balance
  unchanged from HEAD; CRLF preserved (6383 CRLF, 0 bare LF).
* In-browser, `localStorage` cleared atomically before load: all 8 tabs render, **0 console
  errors**, **0 `NaN`**, every gated panel shows its threshold and reason, and none of `R²=100`,
  `RIS 703`, `NNT ≈`, Egger `p = 0.964`, Copas "insensitive to selection bias", L'Abbé "supports
  the pooled estimate of benefit", "CHECKS PASSED" or `v11.0` survives.
* Contamination gate **OK** (0 hard, selftest passes); build gate **OK** (0 hard).

## T1.6 Sourcing completed during Tier 1, applied in Tier 2

**IRONMAN all-cause deaths — now sourced**, resolving the round-1 UNAVAILABLE. According to PubMed,
Cleland JGF et al., *J Am Coll Cardiol* 2024;84(18):1704–1717
([DOI](https://doi.org/10.1016/j.jacc.2024.08.052), PMID 39443013, PMC11496827, open access),
Table 3 and Table 4 report all-cause deaths of **184 (ferric derisomaltose)** vs **192 (Table 3) or
193 (Table 4) (usual care)**; the Results text gives 377 of 1137 (33%) dead overall, which
reconciles with 193, not 192. 184/568 = 32.4% and 193/569 = 33.9%, matching the "~32% vs 34%" the
first review quoted. Two discrepancies must travel with these numbers: (a) the paper's own Tables 3
and 4 disagree by one death in the control arm; (b) the arm sizes are **swapped** relative to the
Lancet primary report — Lancet 2022 gives FDI n = 569 / usual care n = 568, JACC 2024 gives FDI
n = 568 / usual care n = 569. Counts and denominators are therefore taken from the same source
(JACC) for internal consistency, with the conflict disclosed. Applied in Tier 2.

The verdict text was updated in this commit so it no longer asserts these counts could not be found.
