# Running report #6 — registry cache built, paired-sibling swaps resolved

**Date:** 12 August 2026 · extends reports #1–#5
**Project:** Nafis
**Access:** read-only mount. No repo writes.

---

## 1. Headline

**The bulk registry endpoint works, and it returns the registry's own acronym — which is the ground truth the audit needed.**

`clinicaltrials.gov/api/v2/studies?filter.ids=NCT…,NCT…&fields=NCTId,BriefTitle,Acronym,LeadSponsorName,EnrollmentCount,InterventionName&format=json`

Legacy field names work; dotted paths do not. Up to ~10 studies return per page with a `nextPageToken`. **This is the cache primitive** — the full 2,279-NCT cache is now a mechanical build, specified in §5.

**Applied to the paired-sibling swaps, it resolved eight of them immediately. Eight new confirmed errors.**

**The structural insight that makes this cheap: for every conflicted pair, the corpus contains BOTH the right and the wrong label** — one app has it correct, another does not. The corpus carries its own ground truth. The bijection test finds the conflict; one registry call decides which side is right.

**Running total: 34 rows adjudicated — 15 correct, 19 wrong.**

---

## 2. Registry ground truth (read verbatim, 12 Aug 2026)

| NCT | Registry acronym | Sponsor | Enrolment |
|---|---|---|---|
| NCT02912468 | **SINUS-24** | Sanofi | 276 |
| NCT02898454 | **SINUS-52** | Sanofi | 448 |
| NCT02696785 | **COAST-V** | Eli Lilly | 341 |
| NCT02696798 | **COAST-W** | Eli Lilly | 316 |
| NCT02696031 | **PREVENT** | **Novartis** | 555 |
| NCT02484547 | **EMERGE** | Biogen | 1,643 |
| NCT02201953 | **ASTRAL-3** | Gilead | 558 |
| NCT00424476 | **BLISS-52** | Human Genome Sciences | 865 |
| NCT02366143 | **IMpower150** | Hoffmann-La Roche | 1,202 |
| NCT03397121 | **ORION-9** | The Medicines Company | 482 |
| NCT03400800 | **ORION-11** | The Medicines Company | 1,617 |
| NCT03705234 | **ORION-4** | University of Oxford | 16,124 |

---

## 3. Eight new confirmed errors

| # | NCT | Corpus label | Registry truth | Severity |
|---|---|---|---|---|
| 12 | NCT02898454 | "SINUS-24" | **SINUS-52** (n=448 vs 276) | wrong sibling |
| 13 | **NCT02696031** | "COAST-V" | **PREVENT — secukinumab, Novartis, non-radiographic axSpA** | **wrong drug, wrong sponsor, wrong population** |
| 14 | **NCT03705234** | "ORION-11" | **ORION-4 — Oxford, n=16,124 CV outcomes trial** | **severe: 16,124-patient outcomes trial recorded as a 1,617-patient lipid trial** |
| 15 | NCT03400800 | "ORION-9" | **ORION-11** (n=1,617 vs 482) | wrong sibling |
| 16 | NCT02366143 | "IMPOWER130" | **IMpower150** | wrong sibling |
| 17 | NCT00424476 | "BLISS-76" | **BLISS-52** | wrong sibling |
| 18 | NCT02201953 | "ASTRAL-1" | **ASTRAL-3** | wrong sibling |
| 19 | NCT02484547 | "ENGAGE" | **EMERGE** | wrong sibling (aducanumab pair) |

**#13 and #14 are the most consequential.**

**#13** puts a **Novartis secukinumab** trial in non-radiographic axSpA under the label of a **Lilly ixekizumab** trial in radiographic axSpA. Wrong drug, wrong sponsor, wrong population — and it sits alongside the MEASURE-4 error on NCT02696785. Two independent secukinumab/ixekizumab confusions in the same therapeutic area.

**#14** is the largest magnitude error found so far. ORION-4 is a **16,124-patient cardiovascular outcomes trial**; ORION-11 is a **1,617-patient LDL-C trial**. Recording one as the other misstates the evidence base by an order of magnitude in weight and swaps a surrogate endpoint for a hard one.

---

## 4. Eight new confirmed-correct rows

Reported first-class. Each conflicted pair resolved into one correct and one wrong label:

**COAST-W** @ NCT02696798 · **ORION-9** @ NCT03397121 · **ORION-11** @ NCT03400800 · **BLISS-52** @ NCT00424476 · **IMpower150** @ NCT02366143 · **ASTRAL-3** @ NCT02201953 · **EMERGE** @ NCT02484547 · **SINUS-24** @ NCT02912468

---

## 5. The full cache — specification for the build lane

Not run here (2,279 NCTs ÷ ~10 per page ≈ 230 paged calls, beyond this session). Fully specified:

```
GET https://clinicaltrials.gov/api/v2/studies
    ?filter.ids=<comma-separated NCTs, batch ~10>
    &fields=NCTId,BriefTitle,OfficialTitle,Acronym,OverallStatus,Phase,
            EnrollmentCount,InterventionName,LeadSponsorName,StudyType,
            DesignAllocation,DesignPrimaryPurpose
    &format=json
```
Follow `nextPageToken`. Store one record per NCT. Then run:

- **Comparator test:** row's stated comparator/`group` vs registry `InterventionName`. *This is the class the bijection test cannot see* — a wrong NCT used **consistently** across every app. Consistency is not correctness, and that blind spot is currently unmeasured.
- **Identity test:** row `name` vs registry `Acronym`.
- **Design test:** row's stated design (single-arm vs randomised) vs `DesignAllocation`.
- **Weight test:** row `tN`+`cN` vs `EnrollmentCount` — catches #14-class magnitude errors.

---

## 6. Cumulative scoreboard

| Metric | Value |
|---|---|
| Rows adjudicated at primary | **34** |
| — **confirmed correct** | **15 (44%)** |
| — confirmed wrong | 19 (56%) |
| Corpus rows | 3,656 |
| Fraction adjudicated | **0.93%** |

**Flags vs diagnoses, kept separate:** 229 raw identity flags → ~65 high-signal → **19 confirmed wrong**. The selection is deliberately enriched; **this is not a corpus error rate.**

### Failure modes

| Mode | Confirmed |
|---|---|
| **(a) Search breadth** | **0** |
| **(b) Checking** | **22** (19 corpus rows + 3 published syntheses) |

Twenty-two to zero. The field-internal caveat stands and remains decisive: both instruments measuring breadth (backward citation across 44 syntheses; this corpus sweep) test recall against the field's own coverage. **The prespecified non-MEDLINE / non-English / off-registry hunt is still the only thing that can falsify the null.**

---

## 7. Back-computation ruling — applied

**Reviewed every cell in this audit classified as unrecoverable. No row was classified defective purely for determined back-calculation, so no reclassification is required.** Detail:

| Cell | Status under the new rule |
|---|---|
| PARACHUTE-HF all-cause mortality HR | **Remains underdetermined.** A hazard ratio is not determined by 27.9% vs 29.1% plus denominators — it requires time-to-event information. Correctly excluded then and now |
| PARACHUTE-HF stratified win ratio from 103,086 / 67,097 | **Correctly refused.** The stratified estimate is inverse-size weighted, so raw win counts do not determine it. *However* eFigure 2 states the stratified WR **is** the ratio of total weighted wins, and gives 111.3 and 73.0 — that pair **does** determine it. Moot: 1.524 was read verbatim |
| ANSWER-HF per-arm counts | **Remains underdetermined**, and now additionally classified as *never defined* (no composite endpoint existed) |
| **Jyotsna 2023 N reconciliation** | **Upgraded.** Previously hedged as "diagnostic reasoning, not an extracted cell." Now permitted as determined back-computation, with inputs stored: Table 1 rows 5,674 + 7,352 + 5,674 + 13,026 + 7,352 = **39,078**, against a reported 39,995, the residue accounted for by the two phase 2 trials in Table 2. The duplication finding no longer needs the hedge |

---

## 8. Next

1. **Resolve the remaining ~45 high-signal identity flags** — KEYNOTE-585/689/859, VOYAGE-1, AURORA, EXPEDITION-1, SPARTAN/STAMPEDE-ABI, ACIS/TITAN, CABANA/RFVSCRYOAF, ACHIEVE-II/SAMURAI, CHAMPION-PNH/COMMODORE-1. One batched registry call each ≈ 5 calls total.
2. **Build the full cache** per §5, then run the comparator/design/weight tests — the only route to the consistent-wrong-NCT blind spot.
3. **The 1,044 hazard-ratio rows with no evidence block.**
4. **The breadth hunt** per report #5 §6.

---

## 9. Caveats

- 34 of 3,656 rows = 0.93%. No corpus-wide rate claimed.
- Suspect set enriched by construction; 56% wrong applies to adjudicated flags, not to the corpus.
- The bijection test is blind to consistently-applied wrong NCTs. §5 is the fix and it is unrun.
- Zero breadth failures remains *not yet caught*, with both instruments field-internal.
- Every identifier resolved by live lookup; every value read verbatim from the registry response.

**Attribution:** ClinicalTrials.gov API v2, retrieved 12 August 2026.
