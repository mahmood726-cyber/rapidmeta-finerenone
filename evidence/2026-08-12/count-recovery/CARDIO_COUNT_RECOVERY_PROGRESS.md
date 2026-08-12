# Cardiology per-arm count recovery — progress report

**Date:** 2026-08-12 · **Harness:** `rapidmeta_count_harness.py` v1.0.0 (14 checks) · **Corpus read-only**, nothing written to `F:\rapidmeta-finerenone`.

---

## 1. The rate, with its denominator

The denominator comes from the corpus itself, not from my judgement: `cardiology_mortality_atlas.json` (generated 2026-06-02) holds **63 trial rows across 30 drug classes**, each row wanting per-arm all-cause-mortality counts (`tE`, `cE`) and denominators (`tN`, `cN`).

| | rows | % of 63 |
|---|---|---|
| Had a complete per-arm 2×2 before this round | 38 | 60.3% |
| **Recovered this round** | **8** | **+12.7pp** |
| Complete now | **46** | **73.0%** |
| Blocked by the harness, pending resolution | 1 | 1.6% |
| Still open | 16 | 25.4% |

Recovered rows: PARADIGM-HF (HFrEF NMA), DAPA-HF (HFrEF NMA), PARAGON-HF, SPRINT, ACCORD, DECLARE-TIMI 58, ODYSSEY OUTCOMES, EMPA-KIDNEY.

Separately, the ARNI/HFrEF review deliverable from the prior round stands at **24 of 24 cells** across PARADIGM-HF, PARACHUTE-HF and PARALLEL-HF, 22 doubly-confirmed and 2 single-source.

Harness run on this round's extraction file (52 deliverable cells + 10 alternate-population rows): **4 BLOCK, 31 WARN**. All 4 BLOCKs are HEART-FID, deliberately left unresolved so the harness would have to catch it — it did, twice, from two different directions.

---

## 2. Counts recovered this round

All read, none computed. Population and denominators recorded for every cell.

| Trial | NCT | Arm | Deaths | Analysed | Randomised | Tier | Pointer |
|---|---|---|---|---|---|---|---|
| PARAGON-HF | NCT01920711 | sacubitril/valsartan | 342 | 2407 | 2419 | T2 | Outcome 5 "All-cause Mortality" |
| | | valsartan | 349 | 2389 | 2403 | T2 | " |
| DAPA-HF | NCT03036124 | dapagliflozin 10 mg | 276 | 2373 | 2373 | T2 | Outcome 6 all-cause mortality |
| | | placebo | 329 | 2371 | 2371 | T2 | " |
| SPRINT | NCT01206062 | intensive SBP | 155 | 4678 | 4678 | T2 | Outcome 2 |
| | | standard SBP | 210 | 4683 | 4683 | T2 | " |
| ACCORD (glycemia) | NCT00000620 | intensive glycaemia | 391 | 5128 | 5128 | T2 | Outcome 2 "Death From Any Cause in the Glycemia Trial" |
| | | standard glycaemia | 327 | 5123 | 5123 | T2 | " |
| DECLARE-TIMI 58 | NCT01730534 | dapagliflozin 10 mg | 529 | 8582 | 8582 | T2 | Outcome 4 |
| | | placebo | 570 | 8578 | 8578 | T2 | " |
| ODYSSEY OUTCOMES | NCT01663402 | alirocumab | 334 (3.5%) | 9462 | 9462 | **T1** | NEJM 2018;379:2097-2107 Results text |
| | | placebo | 392 (4.1%) | 9462 | 9462 | **T1** | " |
| EMPA-KIDNEY | NCT03594110 | empagliflozin 10 mg | 148 (4.5%) | 3304 | 3304 | **T1** | NEJM 2023;388:117-127 Table 2 |
| | | placebo | 167 (5.1%) | 3305 | 3305 | **T1** | " |
| PARADIGM-HF | NCT01035255 | sacubitril/valsartan | 711 (17.0%) | 4187 | 4209 | T1+T2 | NEJM 2014 Results text; CT.gov Outcome 2 |
| | | enalapril | 835 (19.8%) | 4212 | 4233 | T1+T2 | " |

**Single-source flag.** 18 of the 20 filled cells rest on one source. Only PARADIGM-HF's two cells are doubly confirmed. Every count-vs-percentage pair that could be tested agreed; every recovered pair reproduced the atlas's stored hazard ratio to within 8%.

---

## 3. The finding that changes how the rest should be done

ClinicalTrials.gov requires an all-cause death count in the **adverse-events module**. It is an integer, it is posted even when the efficacy outcomes are percentage-only, and it looked like the key that would unlock every remaining row in one pass. It is not the efficacy endpoint.

| Trial | AE module | Efficacy endpoint | |
|---|---|---|---|
| SPRINT | 155 / 210 | 155 / 210 | identical |
| DECLARE-TIMI 58 | 529 / 570 | 529 / 570 | identical |
| PARAGON-HF | 347 / 357 | 342 / 349 | small |
| DAPA-HF | 286 / 333 | 276 / 329 | small |
| ODYSSEY OUTCOMES | 238 / 278 | 334 / 392 | **~100 events per arm** |
| EMPA-KIDNEY | 314 / 353 | 148 / 167 | **>2×** |

It agrees exactly in two trials and is out by more than a factor of two in another. Had this sweep used it as a shortcut, roughly half the recovered rows would have been quietly wrong, and the error would have been invisible downstream because — and this is the part worth dwelling on — **the wrong numbers also reproduce the stored hazard ratio**. ODYSSEY's AE pair gives RR 0.856 and its efficacy pair gives RR 0.852, against a stored HR of 0.85. A consistency check would have waved both through.

That is now `CHK013_AE_MODULE_DEATHS_NOT_EFFICACY` (blocks the substitution) and a stated limitation on `CHK014_EFFECT_ESTIMATE_CONSISTENCY` (agreement authenticates nothing; only disagreement is informative).

---

## 4. What the harness caught on live data

**HEART-FID (NCT03037931) — 4 BLOCKs, unresolved.** The registry offers two death counts and neither is labelled as the efficacy all-cause-mortality endpoint:

- Outcome 1 "Number of Deaths", ITT, 12-month window: **131 / 1532 vs 158 / 1533**
- Adverse-events module, 67.5 months: **354 / 1532 vs 367 / 1533**

They differ by a factor of 2.7. `CHK003` refused to pick between them; `CHK013` blocked the AE variant; `CHK014` noted that the 12-month pair implies RR 0.830 against the atlas's stored HR of 0.95, while the long-window pair implies 0.965. The evidence points at the long window, but pointing is not reading, so the cell stays blocked until someone reads the publication. **This is the correct outcome, not a failure.**

**PARAGON-HF — 2 WARNs.** Analysed 2407/2389 against randomised 2419/2403: 12 and 14 participants excluded, and the registry results module does not say why. Recorded as `NOT STATED`, which downgrades CHK002 to WARN and marks it an open item rather than letting an unexplained exclusion pass as an explained one.

---

## 5. Corpus data-quality flags found along the way

1. **TWILIGHT appears twice with irreconcilable denominators.** In class "P2Y12 mono": tN/cN 3555/3564. In class "Ticagrelor mono": tE/cE 172/168 on tN/cN 4614/4603. Those denominators sum to 9217, which exceeds the trial's own randomised total in the registry (7119). One of the two rows is wrong.
2. **GLOBAL LEADERS likewise.** "P2Y12 mono" carries cN 8011; "Ticagrelor mono" carries cN 7988 for the same trial.
3. **CANVAS Program is an entity mismatch.** The atlas row is the pooled CANVAS + CANVAS-R programme; NCT01032629 is CANVAS alone (1442/1445/1443). Extraction against that NCT would silently substitute a sub-trial for the pooled entity. CANVAS-R is a separate registration and must be pooled explicitly.
4. **ADVANCE (NCT00145925) has no results module at all** — publication or regulatory route only.
5. **Six atlas rows carry a hazard ratio with no denominators whatsoever** (SPRINT, ACCORD, ADVANCE, VADT, EMPA-REG, CANVAS, VERTIS, DECLARE). Three of those are now filled.

---

## 6. Still open — 16 rows, with the reason each is open

Not one of these is "no data". Each has a named obstacle and a named next step.

**Registry posts percentages / KM estimates only — publication required (13):** FOURIER, LEADER, GLOBAL LEADERS, ATLAS ACS 2, COMMANDER HF, CREDENCE, EMPEROR-Reduced, SUSTAIN-6, SOLOIST-WHF, EMPA-REG OUTCOME, VERTIS-CV, CANVAS Program (plus entity mismatch above).

**Registry posts no death-titled outcome at all (3):** TWILIGHT, AMPLITUDE-O, VADT.

**No results module (1):** ADVANCE.

Denominators were recovered from participant flow for most of these even where events were not, so the remaining work is narrower than the row count suggests.

---

## 7. Files

| File | What it is |
|---|---|
| `rapidmeta_count_harness.py` | The harness. 14 named checks, 11 negative controls, stdlib only. `--selftest` and `--chain`. |
| `COUNT_RECOVERY_PROCEDURE.md` | Procedure doc: retrieval fallback chain, tiers, cell schema, standing order. |
| `build_cardio_extraction.py` | Builds this round's extraction file from what was read. |
| `cardio_acm_extraction.json` | 62 cells (52 deliverable + 10 alternate-population). |
| `cardio_acm_harness_report.md` | Harness output on the above. |
| `cardio_acm_harness_findings.json` | Machine-readable findings. |
| `ARNI_HFrEF_per_arm_event_counts_extraction.md` | Prior round's ARNI deliverable. |

---

## Sources

- McMurray JJV et al. *N Engl J Med* 2014;371:993-1004. [DOI](https://doi.org/10.1056/NEJMoa1409077)
- Schwartz GG et al. Alirocumab and Cardiovascular Outcomes after Acute Coronary Syndrome. *N Engl J Med* 2018;379:2097-2107. [DOI](https://doi.org/10.1056/NEJMoa1801174)
- The EMPA-KIDNEY Collaborative Group. Empagliflozin in Patients with Chronic Kidney Disease. *N Engl J Med* 2023;388:117-127. [PMC7614055](https://pmc.ncbi.nlm.nih.gov/articles/PMC7614055/)
- ClinicalTrials.gov posted results: [NCT01920711](https://clinicaltrials.gov/study/NCT01920711?tab=results) · [NCT03036124](https://clinicaltrials.gov/study/NCT03036124?tab=results) · [NCT01206062](https://clinicaltrials.gov/study/NCT01206062?tab=results) · [NCT00000620](https://clinicaltrials.gov/study/NCT00000620?tab=results) · [NCT01730534](https://clinicaltrials.gov/study/NCT01730534?tab=results) · [NCT03037931](https://clinicaltrials.gov/study/NCT03037931?tab=results) · [NCT03594110](https://clinicaltrials.gov/study/NCT03594110?tab=results) · [NCT01663402](https://clinicaltrials.gov/study/NCT01663402?tab=results)
- Corpus: `F:\rapidmeta-finerenone\cardiology_mortality_atlas.json` (read-only)
