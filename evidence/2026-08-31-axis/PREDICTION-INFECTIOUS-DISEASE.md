# Prediction: does the lane carry over to infectious disease? Written before the run.

I said, twice, *"the lane should carry over unchanged, which remains a claim until run."*
This is the run. Predicted before applying the rule to a single ID topic.

    REF.rule   604ed6957a1adf17   ⛔ FROZEN. Not one line changes for this specialty.
    REF.base   evidence/2026-08-31-rekey/corrected/pool.json — 56 cardiology topics

## THE BASELINE **[MEASURED]**

    DRUG_KEYED_AND_REKEYABLE   17   30%
    F1_NO_CONDITION             7   12%
    F2_NO_DRUG                  6   11%
    F5_MODALITY_CLASS           6   11%
    F3_MULTI_DRUG               6   11%
    F0_NO_TITLE                 6   11%
    F4_NO_CLASS                 4    7%
    EXCLUDED_BY_INSTRUCTION     3    5%
    F6_CIRCULAR_CLASS           1    2%

**[MEASURED]** The ID population is **62 topics** — larger than the cardiology 56.

## ⛔ I NOW EXPECT MY OWN CLAIM TO BE WRONG, AND THE TITLES ARE WHY

Reading the 62 titles before running anything, three structural differences are visible:

1. **Empty titles.** `bamlanivimab-outp`, `bezlotoxumab-cdiff`, `ceftolozane-taz-…`,
   `cvncov-sarscov2`, `ertapenem-infect-…`, `lefamulin-cap-…`, `lenacapavir-prep-review` —
   at least 7, against 6 in all of cardiology.
2. **Title-cased slugs rather than sentences.** `Cefepime Taz`, `Caspofungin Fungal`,
   `Men Acwy`, `Ivermectin Lf`, `Pediatric HIV Art`, `Doripenem`, `Meropenem`. These have no
   condition connective at all, so R1 cannot split them.
3. **Interventions that are not one drug.** `malaria-vaccine`, `menacwy-booster`,
   `influenza-recombinant`, `prevnar15-pneumo` are VACCINES; `covid-oral-antivirals` names
   two agents; `mdr-tb-shortened` names three; `cryptococcal-meningitis-africa` is a timing
   strategy, not a drug.

## THE PREDICTION

| | cardiology | predicted ID |
|---|---|---|
| DRUG_KEYED_AND_REKEYABLE | 30% | **12–22%** |
| F0_NO_TITLE | 11% | **≥ 15%** |
| F1_NO_CONDITION | 12% | **≥ 20%** |
| F3_MULTI_DRUG | 11% | **≥ 12%** |
| topics the rule can carry end-to-end | 17 of 56 | **8–14 of 62** |

⇒ **[INFERRED] I predict the lane does NOT carry over unchanged, and that the cause is the
TITLES rather than the rule.** The rule's first act is to split a title at a condition
connective; ID titles are more often slugs, blanks, or regimens, so the rule loses them
earlier and for reasons that have nothing to do with infectious disease as a subject.

⭐ **That distinction is the whole point of running it.** "The rule fails on ID" and "the ID
objects have worse titles than the cardiology objects" are different findings with different
owners, and only the per-failure-state breakdown separates them.

## SECONDARY PREDICTIONS

* **[INFERRED]** ChEMBL will resolve antibiotics and antivirals well but **fail on vaccines**
  — a vaccine is not a molecule with a USAN stem — so I expect vaccine topics to land in
  `F2_NO_DRUG` rather than being mis-keyed. If instead a vaccine resolves to some molecule,
  that is the identity defect again and it is the thing to look for.
* **[INFERRED]** `F5_MODALITY_CLASS` will be **higher** than cardiology's 11%, because
  monoclonals are common in ID (bamlanivimab, casirivimab, etesevimab, bezlotoxumab,
  nirsevimab) and their USAN stem names a modality, not a therapeutic class.

## WHICH WAY I EXPECT TO MISS

My recent misses have been low. Here I am predicting a WORSE result than the baseline, so
the symmetric risk is that I am now over-correcting into pessimism about my own lane.
**[INFERRED]** The specific way I could be wrong: ID drug names are highly distinctive
(`ceftolozane`, `bezlotoxumab`, `tecovirimat`) and ChEMBL may resolve them more reliably
than cardiology's, so `DRUG_KEYED_AND_REKEYABLE` could hold near 30% despite the worse
titles. If that happens, the claim I doubted is the one that survives.
