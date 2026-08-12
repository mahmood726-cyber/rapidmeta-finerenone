# Count recovery — round 2 progress

**Date:** 2026-08-12 · **Harness:** 16 checks, 15 negative controls, all passing · **Corpus read-only.** No file in `F:\rapidmeta-finerenone` was modified.

---

## 1. The rate, with its denominator

Denominator from the corpus, not from judgement: `cardiology_mortality_atlas.json` — **63 trial rows across 30 classes**.

| | rows | % of 63 |
|---|---|---|
| Complete at baseline | 38 | 60.3% |
| Recovered round 1 | +8 | |
| **Recovered round 2** | **+2** | |
| **Complete now** | **48** | **76.2%** |
| Still open | 15 | 23.8% |
| Blocked by the harness | **0** | — |

Round 2 additions: **LEADER** and **HEART-FID**. HEART-FID was the row the harness blocked last round; it is now resolved by reading, not by inference.

Second front opened: **6 non-cardio diagnostic-accuracy datasets, 34 study rows, 68 cells** — audited for the first time. Result below, and it is not good.

---

## 2. Round 2 counts recovered

| Trial | NCT | Arm | Deaths | Analysed | Tier | Pointer |
|---|---|---|---|---|---|---|
| LEADER | NCT01179048 | liraglutide | 381 (8.2%) | 4668 | T1 | NEJM 2016;375:311-322, Results |
| | | placebo | 447 (9.6%) | 4672 | T1 | " |
| HEART-FID | NCT03037931 | ferric carboxymaltose | 361 (23.6%) | 1532 | T1 | NEJM 2023;389:975-986, Results/Safety |
| | | placebo | 376 (24.5%) | 1533 | T1 | " |

All ten recovered pairs re-verified independently: every printed percentage reproduces its count to within 0.06pp, and every implied risk ratio sits within 2% of the atlas hazard ratio. Zero failures.

### HEART-FID — how it was resolved, and why it took reading

Four different numbers existed for one concept:

| Source | Count | Window / population |
|---|---|---|
| Registry Outcome 1 "Number of Deaths" | 131 / 158 | ITT, **12 months** |
| Registry adverse-events module | 354 / 367 | safety population, **67.5 months** |
| **Publication, Results/Safety** | **361 / 376** | **randomised, full follow-up — prespecified exploratory outcome** |
| Atlas stored HR | 0.95 (0.79–1.14) | — |

Last round the evidence *pointed* at the long window. Pointing is not reading, so it stayed blocked. The publication gives 361 / 376 with HR **0.90 (0.78–1.05)** — close to the long-window registry figure but not equal to it, and the atlas's stored **0.95** matches neither. The corpus's own `ctgov_mining_gaps.md` (2026-04-10) had independently flagged this row: "IV iron / NCT03037931 / Atlas HR 0.95 / CT.gov HR 0.8142 / 14.3% diff". Three independent lines now say the atlas HEART-FID hazard ratio is wrong. **The counts are recovered; the stored HR is a separate defect for the build lane.**

---

## 3. Second front — the non-cardio datasets, and the biggest finding so far

Six diagnostic-accuracy datasets (SARS-CoV-2 antigen, D-dimer for PE, GeneXpert Ultra, prostate mpMRI, plasma p-tau217, hs-cTn 0/1h) were adapted into harness cells and run.

**53 BLOCK / 64 WARN on 68 cells.**

The blocks are almost entirely one thing. The corpus records a `provenance` field on each row, and it says:

| provenance value | rows |
|---|---|
| `pubmed_abstract_back_computed` | 22 |
| `pubmed_abstract_raw_counts` | 5 |
| `pubmed_abstract_back_computed_pending_full_text_verification` | 2 |
| *(missing)* | 2 |
| `ctgov_pub_table_via_abstract` | 1 |
| `ptau181_paper_relabel_2026-04-29` | 1 |
| `pubmed_abstract_explicit_npv_back_compute` | 1 |

**26 of 34 rows (76%) are back-computed from published sensitivity/specificity percentages rather than read as counts.** That is the multiply-a-percentage move this programme has banned, applied at scale, to 52 of 68 cells.

Two things must be said in the corpus's favour, because they are the reason this was findable at all: it records `provenance` honestly, it stores a `raw_quote` for every row, and two rows are explicitly labelled `pending_full_text_verification`. Nobody hid anything. But an honest label on a derived number does not make it a read number, and these cells currently feed pooled sensitivity and specificity estimates.

One further block: `Pereira Battaglia 2025` in the hs-cTn set has no registration and no PMID (`CHK010`), and two hs-cTn rows have an empty 2×2 with an empty provenance field.

**Recommendation:** this is a bigger, more concentrated defect than anything in the cardiology atlas, and it is in a domain nobody had audited. It deserves its own recovery lane. Back-computation from a 2×2's marginals is *sometimes* exactly recoverable — when sensitivity, specificity and both group sizes are all reported, the four cells are determined — so a portion of these may be legitimate under a stricter rule than "never compute". That rule needs writing before the lane starts, not after.

---

## 4. Harness — now 16 checks

Added this round, each with a negative control:

- **`CHK015_INHERITED_WITHOUT_PRIMARY_VERIFICATION`** — a count taken from a published synthesis and never read at a primary source. `CHK011` asks whether a T4 source was *flagged*; this asks whether anyone actually *looked*. A cell can be correctly labelled and silently inherited forever.
- **`CHK016_COMPOSITE_CONSTRUCTED_BY_ADDITION`** — blocks composites built by summing components (PARADIGM-HF: 914 read, 1095 if summed), composites implausibly close to the component sum, and counts declared `back_calculated`. This is the check that caught the 52 diagnostic-accuracy cells.

**The CHK014 limitation now travels with the check.** `CHK014_CAVEAT` prints at the top of every markdown report containing a CHK014 finding and is written into the JSON output under `chk014_caveat`. A reader who never opens the procedure doc still sees that agreement authenticates nothing.

Two more live instances of that principle turned up in the defect ledger: the atlas's TWILIGHT row (implied RR 0.995 against stored 0.99) and its GLOBAL LEADERS row (0.937 against 0.93) are each internally consistent and each wrong.

Negative controls: 15, all caught. Self-test exit 0. Cardio extraction exit 0 (no blocks). Diagnostic-accuracy extraction exit 1 (53 blocks, correctly).

---

## 5. Defect ledger — DEFECT-01 escalated

`DEFECT_LEDGER_cardiology_mortality_atlas.md` documents three defects at exact JSON paths. One changed materially during round 2.

**DEFECT-01 (TWILIGHT) is no longer a denominator problem — it is an outcome substitution.** The TWILIGHT publication's Results text reads: the key secondary composite of *death from any cause, nonfatal myocardial infarction, or nonfatal stroke* occurred in 135 (3.9%) vs 137 (3.9%), **hazard ratio 0.99, 95% CI 0.78 to 1.25**, in the per-protocol population of 3524 / 3515.

`classes[20].trials[0]` stores **hr 0.99, lo 0.78, hi 1.25**. Exact match on all three numbers. In a mortality atlas, that row is a composite of death, MI and stroke wearing a mortality label — and it is currently pooled with genuine mortality estimates in `classes[20].pool` (k=2), which is therefore invalid until fixed.

DEFECT-02 (GLOBAL LEADERS: two control-arm denominators, 8011 vs 7988, and an event count roughly double the registry's) and DEFECT-03 (CANVAS Program row pointing at NCT01032629, which is CANVAS alone at n=4330, not the pooled programme with CANVAS-R NCT01989754 at n=5813) stand as documented. CANVAS/CANVAS-R identities were verified by live registry title search.

All three share one root cause, and the ledger's cross-cutting recommendation is to make `outcome`, `population` and `window` required fields on every trial row. DEFECT-01 would have been impossible to create.

---

## 6. Still open — 15 cardio rows

Not one is "no data". Each carries a named obstacle.

**Registry percentage-only, publication table paywalled (12):** FOURIER, GLOBAL LEADERS, ATLAS ACS 2, COMMANDER HF, CREDENCE, EMPEROR-Reduced, SUSTAIN-6, SOLOIST-WHF, EMPA-REG OUTCOME, VERTIS-CV, CANVAS Program, AMPLITUDE-O.

**Registry posts no death-titled outcome (2):** TWILIGHT, VADT.

**No results module (1):** ADVANCE.

### The obstacle that now dominates, named precisely

**NEJM renders outcome tables outside the DOM.** `document.querySelectorAll('table').length` returns 0 on a full-text NEJM article; the Table 2 anchors are in-page fragments whose content never loads. The Results *body text* carries per-arm counts only when the authors chose to write them in prose — which worked for ODYSSEY OUTCOMES, HEART-FID and TWILIGHT's composite, and failed for FOURIER, CREDENCE and EMPEROR-Reduced, where the body text reports hazard ratios only.

Two further obstacles hit and recorded, neither an absence:
- **pubmed.ncbi.nlm.nih.gov served a reCAPTCHA interstitial** to the browser. Not bypassed — CAPTCHAs are not to be solved. The PubMed MCP tool was used instead and worked.
- **nejm.org rate-limited** after repeated requests, returning a Cloudflare interstitial. Resolved by pausing.

**Next step for the remaining 12 is tier T3** — FDA statistical reviews and EMA EPARs — which the fallback chain already lists as step 6 and which no lane has yet exercised. That is the natural start for round 3.

---

## 7. Files

All under `C:\Users\mahmo\AppData\Roaming\Claude\local-agent-mode-sessions\bdc5772c-ca03-473f-9464-80d37a7559d2\44788c9b-d162-4f2e-b3c2-d89031e65ab6\local_95f555f3-c719-446f-9f1a-d5253bed5c4e\outputs\`

| File | What it is |
|---|---|
| `rapidmeta_count_harness.py` | The harness. 16 checks, 15 negative controls, stdlib only. `--selftest`, `--chain`. |
| `COUNT_RECOVERY_PROCEDURE.md` | Procedure: retrieval fallback chain, tiers, cell schema, standing order, non-intervention adapter rules. |
| `DEFECT_LEDGER_cardiology_mortality_atlas.md` | Three defects at exact JSON paths, for the build lane. |
| `build_cardio_extraction.py` → `cardio_acm_extraction.json` | Cardio extraction, 64 cells (50 deliverable + 14 alternate-population). |
| `cardio_acm_harness_report.md` / `.json` | Harness output — 0 blocks. |
| `adapt_dta_to_cells.py` → `dta_extraction.json` | Diagnostic-accuracy adapter, 68 cells. |
| `dta_harness_report.md` / `dta_harness_findings.json` | Harness output — 53 blocks. |
| `CARDIO_COUNT_RECOVERY_PROGRESS.md` | Round 1 report. |
| `ARNI_HFrEF_per_arm_event_counts_extraction.md` | ARNI/HFrEF deliverable, 24 cells. |

*Filenames retain their original prefix; nothing has been renamed. New artefacts are named neutrally.*

---

## Sources

- Mehran R et al. Ticagrelor with or without Aspirin in High-Risk Patients after PCI. *N Engl J Med* 2019. [Article](https://www.nejm.org/doi/full/10.1056/NEJMoa1908419)
- Mentz RJ et al. Ferric Carboxymaltose in Heart Failure with Iron Deficiency. *N Engl J Med* 2023. [Article](https://www.nejm.org/doi/full/10.1056/NEJMoa2304968) · [PMID 37632463](https://pubmed.ncbi.nlm.nih.gov/37632463/)
- Marso SP et al. Liraglutide and Cardiovascular Outcomes in Type 2 Diabetes. *N Engl J Med* 2016;375:311-322. [PMID 27295427](https://pubmed.ncbi.nlm.nih.gov/27295427/)
- Perkovic V et al. Canagliflozin and Renal Outcomes in Type 2 Diabetes and Nephropathy. *N Engl J Med* 2019. [Article](https://www.nejm.org/doi/full/10.1056/NEJMoa1811744)
- ClinicalTrials.gov: [NCT02270242](https://clinicaltrials.gov/study/NCT02270242), [NCT01813435](https://clinicaltrials.gov/study/NCT01813435), [NCT01032629](https://clinicaltrials.gov/study/NCT01032629), [NCT01989754](https://clinicaltrials.gov/study/NCT01989754), [NCT03037931](https://clinicaltrials.gov/study/NCT03037931?tab=results)
- Corpus (read-only): `cardiology_mortality_atlas.json`, `ctgov_mining_gaps.md`, and the six `*_trials.json` diagnostic-accuracy datasets.
