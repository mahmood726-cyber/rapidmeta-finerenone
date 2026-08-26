# Registry-vs-publication verification, and why the import did not proceed

Measured 2026-08-26 at `ssot-shell a87f10342`, against the local AACT snapshot dated
**2026-04-12**. Committed because a measurement that lives only in a session report is,
downstream, indistinguishable from one that was never made.

## The verdict

**12 of 20 sampled trials comparable. Exactly 8 unresolvable. Pre-registered threshold: 8.
The rule trips. NOT_ASSESSABLE. The 152-trial import does not proceed on this sample.**

The threshold and the classification scheme were frozen in `IMPORT-GATE-v1.md` before any
comparison was run, and the 20-trial sample was drawn at recorded seed `20260826` before any
trial was compared. Neither was altered afterwards. The rule tripped at exactly its limit on
a night when the surrounding instruction was to proceed; it was honoured rather than
reinterpreted, which is the only reason the number below means anything.

## THE BOUND — read this before quoting the number

**The denominator is LINKED analyses, not all analyses.**

This licenses: *registry-derived screening is sound where the record can be linked to its
publication.*

It does **not** license: *registry data is 93% reliable.* Nothing here measures the
unlinkable records, and 8 of 20 trials could not be linked at all. Their accuracy is
unknown, not assumed, and they are not in the denominator.

## What was compared

28 analyses across 12 trials, classified as:

* **S1 — same quantity, same value: 26**
* **S2 — same quantity, different value: 1**
* **S3 — different quantity: 1**

| trial | registry | publication | class |
|---|---|---|---|
| NCT00412984 ARISTOTLE | HR 0.79 (0.66–0.95), 0.69 (0.60–0.80), 0.92 (0.74–1.13), 0.51 (0.35–0.75) | identical | S1 ×4 |
| NCT00412984 ARISTOTLE, all-cause death | HR 0.89 (0.80–**1.0**) | HR 0.89 (0.80–**0.99**) | **S2** |
| NCT00000620 ACCORD | HR 0.91 (0.81–1.03), timeframe **4.9 years** | HR 0.90 (0.78–1.04), **3.5-year interim** | **S3** |
| NCT01106014 GRIPHON | HR 0.60 (99% CI 0.46–0.78) | identical | S1 |
| NCT02842086 DISCOVER | RR 0.468 (**95.003%** CI 0.191–1.149) | IRR 0.47 (95.003% CI 0.19–1.15) | S1 |
| NCT04349072 VALOR-HCM | 58.93 (43.989–73.868); 41.07; 9.45; 0.33; 0.53 | 58.9% (44.0–73.9); 41.1%; 9.4; 0.33; 0.53 | S1 ×5 |
| NCT02070757 ASPECT-NP | 1.1% (−5.13 to 7.39); 1.1% (−6.17 to 8.29) | 1.1% (−5.1 to 7.4); 1.1% (−6.2 to 8.3) | S1 ×2 |
| NCT03183128 ECOSPOR III | RR 0.32 (0.18–0.58) | identical | S1 |
| NCT00680186 RE-COVER II | HR 1.08 (0.64–1.8); RD 0.2 (−1.0 to 1.3) | identical | S1 ×2 |
| NCT02285998 Flublok | RVE 30.0 (10.0–47.0) | 30% (10 to 47) | S1 |
| NCT00604214 PROWESS-SHOCK | RR 1.088 (0.923–1.283); 1.042 (0.909–1.193) | 1.09 (0.92–1.28); 1.04 (0.90–1.19) | S1 ×2 |
| NCT04427501 BLAZE-1 | MD 0.09 (−0.35 to 0.52) | identical | S1 |
| NCT00496769 AVERROES | HR 0.45 (0.32–0.62); 0.79 (0.62–1.02) | identical | S1 ×2 |

Publications retrieved from PubMed. DOIs: 10.1056/NEJMoa1107039, 10.1056/NEJMoa0802743,
10.1056/NEJMoa1503184, 10.1016/S0140-6736(20)31065-5, 10.1016/j.jacc.2022.04.048,
10.1016/S1473-3099(19)30403-7, 10.1056/NEJMoa2106516, 10.1161/CIRCULATIONAHA.113.004450,
10.1056/NEJMoa1608862, 10.1056/NEJMoa1202290, 10.1001/jama.2021.0202, 10.1056/NEJMoa1007432.

**The single S2 is precision at the bound, not disagreement about the estimate.** The
registry rounds to two significant figures where the paper reports two decimals, which
flips the interval from excluding the null to touching it. Corpus-wide this affects **19 of
1,433 classifiable tier-A rows (1.3%)** — a bounded exception list, not a systemic problem.
Import rule: any registry CI bound landing exactly on its null at two significant figures is
reconciled against the publication rather than imported verbatim.

**The single S3 is a follow-up difference**, separable only because the registry publishes
its own analysis-population and timeframe fields. Without them these would read as two
discrepancies.

## Why 8 could not be linked — the barrier is linkage, not accuracy

* **3 have no PubMed record under their NCT at all** (NCT01223352, NCT01225822, NCT05201079).
  PubMed *silently drops* an unindexed NCT from a boolean query rather than erroring, and the
  other terms still return hits — so the miss is invisible and reads as a completed search.
  Measured: of 12 trials known to be indexed, **12 of 12 survived** in `query_translation`,
  so the drop signals genuine absence. **15% of this sample has no NCT-indexed record.**
  Any NCT lookup should query one ID at a time and check the translation echoes it back.
* **3 have AACT `reference_type='result'` pointing at the wrong paper** — a pregnancy
  pharmacokinetics sub-study, a research letter with no abstract, a dried-blood-spot methods
  paper. Not missing: **wrong**, at 25% of what was checked. **No tier-A manifest row depends
  on this link** — the manifest joins `nct_id` into `outcome_analyses` directly, never through
  `study_references` — so the import does not inherit it. Verification does.
* **2 surfaced only secondary or pharmacokinetic analyses**, not the trial's results paper.

## What follows

A second sample needs a **new threshold and a new linkage protocol written before the draw**,
not a reinterpretation of this one. The linkage route must avoid both failures above: not
PubMed-ID queries, and not `study_references`. DOI-and-title resolution keyed on the trial's
own identity, confirmed by the abstract naming the registration, is the candidate.
