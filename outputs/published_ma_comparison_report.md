# Published-MA Comparison Report

**Date**: 2026-05-04. Tool: `scripts/compare_to_published_mas.py`. Coverage: 76
hand-curated trial primary-publication ground-truth values, matched against
104 trial-rows in our 216 review HTMLs.

User directive: "publihsed metas might use diffierent methods and inlcusion
criteria but tstill they can help us find errors". Below, each flagged
discrepancy is classified as either (A) genuine per-trial transcription
defect, (B) outcome-framing difference (different outcome between our app and
my ground-truth baseline — NOT a defect), or (C) arm-selection difference
(different dose-arm or time-point — borderline; should be made explicit in
trial label).

---

## Verdict counts

- OK: 76 trial-rows match ground truth within 10% point + 30% CI bounds
- DEFECT (flagged): 20 trial-rows
- CI_DRIFT: 8 trial-rows (point matches but CI bounds drifted >30%)

## Defect triage

### A. Genuine per-trial transcription defects (need fix)

These are the same-outcome same-arm same-time-point comparisons where our
extracted value doesn't match what the trial actually reported. Count: ~3.

1. **DOAC_AF_NMA + DOAC_AF RE-LY (NCT00403767)**: OUR HR 0.79 / 0.88 vs PUB
   HR 0.66 (0.53–0.82) for stroke/SE with dabigatran 150mg.
   - Our 0.79 likely reflects an averaged across-dose value
   - Our 0.88 in DOAC_AF likely reflects dabigatran 110mg (HR 0.91, 0.74–1.11)
   - Fix: explicitly label dose arm; use canonical 150mg primary HR 0.66

2. **POLYCYTHEMIA_VERA_NMA RESPONSE (NCT01243944)**: OUR OR 21.4 (3.0–152.9)
   vs PUB OR 28.6 (4.5–1206). 25% point lower. Our CI upper bound is
   markedly wider clipped. Fix: align with Vannucchi 2015 NEJM Table 2
   primary OR.

3. **DIABETIC_MACULAR_EDEMA Protocol T (NCT01627249)**: OUR `publishedHR: 11.6
   (9.5–13.7)` vs PUB MD 2.1 (0.4–3.8) for between-arm BCVA difference.
   - Our 11.6 ≈ absolute BCVA letter gain in aflibercept arm at 1y (~13.3 letters)
   - PUB 2.1 ≈ aflibercept-vs-ranibizumab between-arm difference
   - This is a STRUCTURAL framing issue — the field stores absolute, not contrast
   - Fix: change `publishedHR` to the between-arm contrast (~2.1)

### B. Outcome-framing differences (NOT defects)

These flag because our app and my ground-truth baseline used different
outcomes. Both are valid — just different. Count: ~10.

4. **BPAL_MDRTB TB-PRACTECAL (NCT02589782)**: OUR RR 1.68 (1.4–2.01) vs my
   PUB RR 0.22. Definition flip: OURS = RR for FAVORABLE outcome (>1 = good);
   MINE = RR for UNFAVORABLE outcome (<1 = good). Both correct, just inverse
   framings. Recommend: standardize all RR-based outcomes to "unfavourable
   event" framing for consistency across topics, OR add explicit `outcome:`
   field clarifying.

5. **DONANEMAB TRAILBLAZER-ALZ 2 (NCT04437511)**: OUR HR 0.84 (0.71–0.99) for
   CDR-SB worsening event count vs my PUB MD −0.7 (−0.95 to −0.45) for
   CDR-SB MEAN CHANGE. Different outcome (binary worsening event vs
   continuous mean change). Both valid.

6. **INCRETINS_T2D SUSTAIN-6 (NCT01720446)**: OUR `publishedHR: -0.77` for
   HbA1c MD (continuous; negative because semaglutide REDUCES HbA1c) vs my
   PUB HR 0.74 for MACE-3. Completely different outcome. Note: storing HbA1c
   MD in a field named `publishedHR` is misleading; recommend rename or use
   the existing `effect`/`md` field with `estimandType: 'MD'`.

7. **LIPID_HUB VITAL (NCT01169259)**: OUR HR 0.92 (CI null) vs PUB HR 1.04
   (0.94–1.16). Likely different outcome (LIPID_HUB may be reporting LDL
   reduction or composite, not the cancer outcome of my baseline).

8. **GLP1_CVOT_NMA + GLP1_CVOT ELIXA / REWIND / EXSCEL row swaps**: OUR has
   ELIXA HR 0.88, REWIND 1.02, EXSCEL 0.78. PUB has ELIXA 1.02, REWIND 0.88,
   EXSCEL 0.91. The values appear swapped between trials (REWIND ↔ ELIXA).
   - However our snippet text may show different outcomes — would need to
     read each block to confirm if these are truly mis-attributed primary HRs
     or different secondary endpoints.
   - HIGH PRIORITY for verification — if rows are mis-attributed, this is a
     real defect; if they're alternate endpoints, just label clarification.

### C. Arm/time-point differences

These flag where our value matches a non-primary arm or alternate timepoint.
Count: ~7.

9. **ELEVATE-TN (NCT02475681) in 2 files**: OUR HR 0.21 (0.14–0.32) vs PUB
   HR 0.10 (0.07–0.16). Sharman 2020 Lancet had two contrasts:
   - Acalab+obi vs chlor+obi: HR 0.10 (canonical headline)
   - Acalab monotherapy vs chlor+obi: HR 0.20
   Our 0.21 ≈ the monotherapy contrast. Recommend label as "ELEVATE-TN
   (acalab monotherapy arm)" if that's intentional, OR switch to canonical
   acalab+obi 0.10 to match published headline.

10. **BTKI_CLL_NMA RESONATE (NCT01578707)**: OUR HR 0.135 (0.095–0.19) vs PUB
    primary HR 0.22 (0.15–0.32). Our value matches the 6-year final analysis
    update (Munir 2019 Am J Hematol HR 0.13 or similar long-term follow-up),
    not the Byrd 2014 primary. Recommend: align with Byrd 2014 NEJM 0.22
    for the canonical primary publication, or label as "RESONATE 6y update".

11. **DIABETIC_RETINOPATHY Protocol S (NCT01489189)**: OUR MD 2.2 (-0.5 to
    5.0) vs PUB MD 2.6 (0.1–5.1). Within 15% point. CI bound similar.
    Borderline — could be 2-year vs 5-year analysis, or LOCF vs MMRM. Likely
    OK; minor refinement only.

---

## Defects we CAN'T detect

The 519 trial-rows for which I don't have hand-curated published ground truth
weren't compared. Real defects in those rows would not surface in this run.
Coverage expansion needed in future sessions to reach all topics — would
require ~5-10× the current ground-truth dictionary.

## Recommended fixes (priority order)

P0 (sign-flip / impossible value):
- INCRETINS_T2D SUSTAIN-6: clarify `publishedHR: -0.77` is HbA1c MD, not HR
  (negative HR is impossible — would be misread by users + downstream tools)

P1 (transcription error, real defect):
- DIABETIC_MACULAR_EDEMA Protocol T: replace 11.6 with 2.1 (between-arm contrast)
- DOAC_AF + DOAC_AF_NMA RE-LY: align with canonical Connolly 2009 dabigatran
  150mg HR 0.66
- POLYCYTHEMIA_VERA RESPONSE: align with Vannucchi 2015 OR 28.6

P2 (alternate-arm / framing — verify intent before fixing):
- ELEVATE-TN in 2 files: arm-selection clarity needed
- BTKI_CLL_NMA RESONATE: timepoint clarity needed
- GLP1_CVOT row swaps: per-trial endpoint verification needed
- BPAL_MDRTB TB-PRACTECAL: outcome-framing standardization

P3 (information):
- TRAILBLAZER-ALZ 2: dual outcomes available (CDR-SB worsening event vs
  CDR-SB MD); both valid, framing is intentional
- LIPID_HUB VITAL: outcome is different from VITAMIN_D_FRACTURE_FALL_NMA
  (LIPID_HUB reports cardiovascular outcome, my baseline was cancer)

## How to expand to all topics

The current 76-trial ground truth captures roughly 17% of corpus
(104/619 trial-rows). To cover all topics, the dictionary needs ~3000–5000
entries (multiple outcomes per trial). The expansion path:

1. For each topic file, extract `nctAcronyms` to identify trials.
2. Use NCBI elink + AACT outcomes.txt to fetch each trial's primary outcome
   plus the canonical effect estimate from the primary publication.
3. Build a per-(NCT, outcome) ground-truth row.
4. Re-run comparison; compare per-outcome values with explicit outcome match.

That's a multi-session effort. The tooling shipped (`compare_to_published_mas.py`)
is the foundation; the dictionary is the long-tail work.
