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
