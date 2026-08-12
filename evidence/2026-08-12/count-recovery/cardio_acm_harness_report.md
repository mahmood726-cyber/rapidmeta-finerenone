# Count-extraction harness report (v1.0.0)

**Verdict: BLOCKED** — 4 BLOCK, 31 WARN across 14 checks on 52 cells.

- cells with counts: **20** / 52
- independently confirmed (>=2 sources): **2**
- single-source: **18**
- unretrieved due to an obstacle (NOT absence): **0**

## BLOCK (4)

- `CHK003_DUPLICATE_OUTCOME_POPULATION` — **HEART-FID/ferric carboxymaltose/all_cause_death** — registry/publication offers 2 arm-pairs for this outcome ([('ITT, 12-month window', 131, 1532), ('safety population (adverse events module), 67.5 months', 354, 1532)]); exactly one must set selected=true with its population named. Refusing to choose for you.
- `CHK003_DUPLICATE_OUTCOME_POPULATION` — **HEART-FID/placebo/all_cause_death** — registry/publication offers 2 arm-pairs for this outcome ([('ITT, 12-month window', 158, 1533), ('safety population (adverse events module), 67.5 months', 367, 1533)]); exactly one must set selected=true with its population named. Refusing to choose for you.
- `CHK013_AE_MODULE_DEATHS_NOT_EFFICACY` — **HEART-FID/ferric carboxymaltose/all_cause_death** — this count comes from the registry adverse-events module (safety population, AE collection window) and is being used as the efficacy all-cause mortality endpoint. Observed divergence from the efficacy outcome ranges from 0 to >2x. Recover the efficacy endpoint, or set selected=false and label the population.
- `CHK013_AE_MODULE_DEATHS_NOT_EFFICACY` — **HEART-FID/placebo/all_cause_death** — this count comes from the registry adverse-events module (safety population, AE collection window) and is being used as the efficacy all-cause mortality endpoint. Observed divergence from the efficacy outcome ranges from 0 to >2x. Recover the efficacy endpoint, or set selected=false and label the population.

## WARN (31)

- `CHK002_DENOMINATOR_NOT_RANDOMISED` — **PARAGON-HF/sacubitril/valsartan/all_cause_death** — analysed 2407 < randomised 2419 (12 excluded) and the source does not say why: 'NOT STATED in the registry results module; 12 and 14 participants excluded from the FAS respectively, reason not given — open item for primary verification'. Open item for primary verification — an unexplained exclusion is not the same as an explained one.
- `CHK002_DENOMINATOR_NOT_RANDOMISED` — **PARAGON-HF/valsartan/all_cause_death** — analysed 2389 < randomised 2403 (14 excluded) and the source does not say why: 'NOT STATED in the registry results module; 12 and 14 participants excluded from the FAS respectively, reason not given — open item for primary verification'. Open item for primary verification — an unexplained exclusion is not the same as an explained one.
- `CHK005_SINGLE_SOURCE_CELL` — **PARADIGM-HF/sacubitril/valsartan/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01035255 results, Outcome 3 adjudicated primary causes of death. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **PARADIGM-HF/enalapril/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01035255 results, Outcome 3 adjudicated primary causes of death. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **PARAGON-HF/sacubitril/valsartan/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01920711 results, Outcome 5 All-cause Mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **PARAGON-HF/valsartan/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01920711 results, Outcome 5 All-cause Mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **DAPA-HF/dapagliflozin 10 mg/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03036124 results, Outcome 6 all-cause mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **DAPA-HF/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03036124 results, Outcome 6 all-cause mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **SPRINT/intensive SBP control/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01206062 results, Outcome 2 Number of Participants With All-cause Mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **SPRINT/standard SBP control/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01206062 results, Outcome 2 Number of Participants With All-cause Mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **ACCORD (glycemia)/intensive glycaemic control/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT00000620 results, Outcome 2 Death From Any Cause in the Glycemia Trial. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **ACCORD (glycemia)/standard glycaemic control/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT00000620 results, Outcome 2 Death From Any Cause in the Glycemia Trial. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **DECLARE-TIMI 58/dapagliflozin 10 mg/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01730534 results, Outcome 4 all-cause mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **DECLARE-TIMI 58/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01730534 results, Outcome 4 all-cause mortality. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **ODYSSEY OUTCOMES/alirocumab/all_cause_death** — SINGLE-SOURCE cell (T1): NEJM 2018;379:2097-2107 Results text. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **ODYSSEY OUTCOMES/placebo/all_cause_death** — SINGLE-SOURCE cell (T1): NEJM 2018;379:2097-2107 Results text. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **EMPA-KIDNEY/empagliflozin 10 mg/all_cause_death** — SINGLE-SOURCE cell (T1): NEJM 2023;388:117-127 Table 2 'Death from any cause'. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **EMPA-KIDNEY/placebo/all_cause_death** — SINGLE-SOURCE cell (T1): NEJM 2023;388:117-127 Table 2 'Death from any cause'. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **ODYSSEY OUTCOMES/alirocumab/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01663402 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **ODYSSEY OUTCOMES/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01663402 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **EMPA-KIDNEY/empagliflozin 10 mg/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03594110 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **EMPA-KIDNEY/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03594110 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **DAPA-HF/dapagliflozin 10 mg/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03036124 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **DAPA-HF/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03036124 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **PARAGON-HF/sacubitril/valsartan/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01920711 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **PARAGON-HF/valsartan/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT01920711 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **HEART-FID/ferric carboxymaltose/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03037931 results, Outcome 1 Number of Deaths. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **HEART-FID/ferric carboxymaltose/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03037931 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **HEART-FID/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03037931 results, Outcome 1 Number of Deaths. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK005_SINGLE_SOURCE_CELL` — **HEART-FID/placebo/all_cause_death** — SINGLE-SOURCE cell (T2): CT.gov NCT03037931 adverseEventsModule deathsNumAffected. Not independently confirmed; must be visibly distinguished in any 'n of m confirmed' statement.
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **HEART-FID/all_cause_death/ITT, 12-month window** — implied RR 0.830 vs stored HR 0.950 (12.7% apart). Likely the wrong outcome, population, or follow-up window.

## INFO (87)

- `CHK001_COUNT_PERCENT_AGREEMENT` — **PARADIGM-HF/sacubitril/valsartan/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **PARADIGM-HF/enalapril/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **PARAGON-HF/sacubitril/valsartan/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **PARAGON-HF/valsartan/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **DAPA-HF/dapagliflozin 10 mg/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **DAPA-HF/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **SPRINT/intensive SBP control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **SPRINT/standard SBP control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ACCORD (glycemia)/intensive glycaemic control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ACCORD (glycemia)/standard glycaemic control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **DECLARE-TIMI 58/dapagliflozin 10 mg/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **DECLARE-TIMI 58/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ODYSSEY OUTCOMES/alirocumab/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ODYSSEY OUTCOMES/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **EMPA-KIDNEY/empagliflozin 10 mg/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **EMPA-KIDNEY/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **DAPA-HF/dapagliflozin 10 mg/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **DAPA-HF/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **PARAGON-HF/sacubitril/valsartan/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **PARAGON-HF/valsartan/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **HEART-FID/ferric carboxymaltose/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **HEART-FID/ferric carboxymaltose/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **HEART-FID/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **HEART-FID/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **FOURIER/evolocumab/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **FOURIER/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **LEADER/liraglutide/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **LEADER/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **GLOBAL LEADERS/ticagrelor monotherapy/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **GLOBAL LEADERS/reference strategy/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ATLAS ACS 2/rivaroxaban low dose/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ATLAS ACS 2/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **TWILIGHT/ticagrelor monotherapy/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **TWILIGHT/ticagrelor + aspirin/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **COMMANDER HF/rivaroxaban 2.5 mg/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **COMMANDER HF/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **CREDENCE/canagliflozin/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **CREDENCE/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **EMPEROR-Reduced/empagliflozin 10 mg/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **EMPEROR-Reduced/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **SUSTAIN-6/semaglutide/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **SUSTAIN-6/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **AMPLITUDE-O/efpeglenatide/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **AMPLITUDE-O/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **SOLOIST-WHF/sotagliflozin/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **SOLOIST-WHF/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **EMPA-REG OUTCOME/empagliflozin pooled/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **EMPA-REG OUTCOME/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **CANVAS Program/canagliflozin pooled/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **CANVAS Program/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **VERTIS-CV/ertugliflozin pooled/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **VERTIS-CV/placebo/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **VADT/intensive glycaemic control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **VADT/standard glycaemic control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ADVANCE/intensive glycaemic control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK001_COUNT_PERCENT_AGREEMENT` — **ADVANCE/standard glycaemic control/all_cause_death** — no printed percentage captured; agreement not testable
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **FOURIER/evolocumab/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **FOURIER/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **LEADER/liraglutide/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **LEADER/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **GLOBAL LEADERS/ticagrelor monotherapy/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **GLOBAL LEADERS/reference strategy/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **ATLAS ACS 2/rivaroxaban low dose/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **ATLAS ACS 2/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **COMMANDER HF/rivaroxaban 2.5 mg/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **COMMANDER HF/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **CREDENCE/canagliflozin/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **CREDENCE/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **EMPEROR-Reduced/empagliflozin 10 mg/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **EMPEROR-Reduced/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **SUSTAIN-6/semaglutide/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **SUSTAIN-6/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **SOLOIST-WHF/sotagliflozin/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **SOLOIST-WHF/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **EMPA-REG OUTCOME/empagliflozin pooled/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **EMPA-REG OUTCOME/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **VERTIS-CV/ertugliflozin pooled/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK004_PERCENTAGE_ONLY_REGISTRY` — **VERTIS-CV/placebo/all_cause_death** — registry posts 'percentage of participants' only and no count was recovered. Publication retrieval required; derivation from the percentage is prohibited.
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **PARADIGM-HF/all_cause_death/FAS** — implied RR 0.857 vs stored HR 0.840 (2.0% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **PARAGON-HF/all_cause_death/FAS** — implied RR 0.973 vs stored HR 0.970 (0.3% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **DAPA-HF/all_cause_death/randomised** — implied RR 0.838 vs stored HR 0.830 (1.0% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **SPRINT/all_cause_death/randomised** — implied RR 0.739 vs stored HR 0.730 (1.2% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **ACCORD (glycemia)/all_cause_death/randomised (glycemia trial)** — implied RR 1.195 vs stored HR 1.190 (0.4% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **DECLARE-TIMI 58/all_cause_death/randomised** — implied RR 0.928 vs stored HR 0.930 (0.3% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **ODYSSEY OUTCOMES/all_cause_death/randomised** — implied RR 0.852 vs stored HR 0.850 (0.2% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **EMPA-KIDNEY/all_cause_death/randomised** — implied RR 0.886 vs stored HR 0.870 (1.9% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).
- `CHK014_EFFECT_ESTIMATE_CONSISTENCY` — **HEART-FID/all_cause_death/safety population (adverse events module), 67.5 months** — implied RR 0.965 vs stored HR 0.950 (1.6% apart). Consistent — but consistency does NOT authenticate the count (see ODYSSEY OUTCOMES in the docstring).

## PASS counts by check

- `CHK001_COUNT_PERCENT_AGREEMENT`: 6
- `CHK002_DENOMINATOR_NOT_RANDOMISED`: 28
- `CHK003_DUPLICATE_OUTCOME_POPULATION`: 10
- `CHK005_SINGLE_SOURCE_CELL`: 2
- `CHK006_READ_NOT_COMPUTED`: 62
- `CHK008_EVENTS_WITHIN_DENOMINATOR`: 30
- `CHK010_IDENTIFIER_PROVENANCE`: 25
- `CHK012_ARM_PAIR_COMPLETE`: 15
- `CHK013_AE_MODULE_DEATHS_NOT_EFFICACY`: 8
