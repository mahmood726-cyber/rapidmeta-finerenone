# Denominator verification — MEASURE-UP-type wrong-arm audit

Follow-up to the JAKI_AD MEASURE-UP fix (record claimed the 30 mg arm but used
the 15 mg arm's n). Goal: find other records whose stored arm size (tN/cN)
belongs to the wrong arm.

## Method
1. `scripts/denominator_candidates.py` — dose-specific RR/OR records (group/title
   names a dose): **253 unique NCTs**.
2. Narrow to the exact MEASURE-UP signature (tN == cN, i.e. same denominator for
   active and placebo): **33 records**.
3. `scripts/verify_denominators.py` — compare stored tN/cN against ClinicalTrials.gov
   per-arm sizes (participant-flow + outcome-measure denoms): **5 flagged**.

## Result: the bug is largely ISOLATED

Of the 5 flags, 3 are false positives and 2 are genuine issues:

| NCT | App | CT.gov real arms | Verdict |
|---|---|---|---|
| NCT02074982 (CLEAR secukinumab) | IL_PSORIASIS_NMA | 334 / 335 | false positive (off by 1, ITT) |
| NCT01405508 (BRV epilepsy) | EPILEPSY_NEW_AEDS | safety sub-table misparsed | false positive |
| NCT01261325 (BRV N01253) | EPILEPSY_NEW_AEDS | 252 / 249 / 259; stored 240 | minor (mITT-ish; app labels it "N01252" — possible study mislabel) |
| **NCT03580369 (PEARL-2 ligelizumab)** | CHRONIC_URTICARIA_BIOLOGICS | Lige 72mg=306, 120mg=312, Oma=306, **Placebo=106** | **GENUINE: stored 498/498 matches no arm; placebo was 106** |
| **NCT05633147 ("ESSENCE" MASH)** | MASH_DRUGS | results are a *linaprazan glurate GERD* PK study | **NCT-IDENTITY ERROR: wrong NCT for the MASH trial** |

So beyond the one the user found (MEASURE-UP), the highest-risk subset surfaced
only **one** additional genuine wrong-denominator record (PEARL-2) and **one**
wrong-NCT record (MASH_DRUGS / NCT05633147). The portfolio's denominators are
otherwise sound.

## FIXED (both, with verified source data)

- **PEARL-1 / PEARL-2 ligelizumab** (CHRONIC_URTICARIA_BIOLOGICS) — the comparison
  is ligelizumab 120 mg vs **omalizumab** (not placebo). Per CT.gov UAS7=0
  responders: PEARL-1 Lige120 103/320 vs Oma 94/321 -> RR 1.10 [0.87,1.39];
  PEARL-2 Lige120 104/322 vs Oma 116/318 -> RR 0.89 [0.71,1.10]. The stored
  values (1.26, 1.23) had shown FALSE superiority; corrected to reflect the real
  result (ligelizumab did NOT beat omalizumab; PEARL failed).
  `scripts/fix_pearl_denominators.py`.
- **ESSENCE semaglutide MASH** (MASH_DRUGS) — was filed under NCT05633147 (a
  linaprazan GERD study). Correct NCT is **NCT04822181**. Per the primary
  (Sanyal et al, NEJM 2025, PMID 40305708, 10.1056/NEJMoa2413258): MASH
  resolution without worsening fibrosis 62.9% (336/534) semaglutide vs 34.3%
  (91/266) placebo -> RR 1.84 [1.54,2.20]. The record's NCT, counts (was
  165/400 vs 56/400), effect (was 2.95), year, and PMID all corrected.
  `scripts/fix_mash_essence.py`.

Both apps validate: CHRONIC_URTICARIA pools 10 trials RR 1.94, MASH_DRUGS 10
trials RR 1.99; portfolio 2033 apps, 19/19 benchmarks.

Tooling: `scripts/denominator_candidates.py`, `scripts/verify_denominators.py`;
CT.gov pulls in `outputs/ctgov_denom/`.
