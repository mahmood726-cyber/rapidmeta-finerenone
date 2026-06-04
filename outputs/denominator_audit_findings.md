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

## Open (need per-arm sourcing before fixing — not rushed)
- **PEARL-2 (NCT03580369)** in CHRONIC_URTICARIA_BIOLOGICS: stored 498/498 is
  wrong (placebo was 106). PEARL-1 (NCT03580356, stored 502/501) likely shares
  the problem. Fix needs the UAS7-responder counts per chosen ligelizumab dose
  arm vs the 106-placebo, from CT.gov results. Note: ligelizumab failed phase 3.
- **MASH_DRUGS / NCT05633147**: NCT05633147 is a linaprazan-glurate GERD study,
  not the "ESSENCE" MASH trial. Needs the correct MASH NCT + data.

Tooling: `scripts/denominator_candidates.py`, `scripts/verify_denominators.py`;
CT.gov pulls in `outputs/ctgov_denom/`.
