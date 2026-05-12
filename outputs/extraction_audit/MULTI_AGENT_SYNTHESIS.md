# Multi-agent internal-consistency audit — 2026-05-12

## Method

3 specialized agents reviewed a stratified sample of 77 trials:
- Agent 1 — drug/disease coherence (is the drug plausibly used for this disease?)
- Agent 2 — effect-size plausibility (HR magnitude, CI consistency, schema)
- Agent 3 — trial identity triangulation (NCT ⟷ acronym ⟷ PMID ⟷ year)

Per arXiv:2604.16706 (Apr 2026), substring-match grading is chance-level vs
human (κ≈0.05); LLM ensemble at ≥3 judges achieves κ≈0.43. We use ≥2-of-3
agreement as the HIGH-confidence consensus gate.

## Sample
- Tier 1 (n=24): trials from reviews with highest post-fix M11 count
- Tier 2 (n=13): the 6 known cross-review NCT-divergent-value cases
- Tier 3 (n=40): random calibration baseline across the corpus

## Results

- Total trials flagged: **44/77**
  - 3-of-3 agreement: **2** (highest confidence)
  - 2-of-3 agreement: **12** (high confidence)
  - 1-of-3 agreement: **30** (single-lens flag; manual review)

- Max severity:
  - HIGH: **24**
  - MED:  **11**
  - LOW:  **9**

- Tier 2 catch rate: **11/13** of known divergent pairs

## Top defect categories

- plausibility · other: 15
- plausibility · literature-mismatch: 10
- identity · generic-name: 7
- identity · famous-trial-wrong-nct: 6
- plausibility · magnitude-extreme: 5
- plausibility · wrong-direction: 4
- coherence · acronym-mismatch: 3
- plausibility · crude-vs-HR-mismatch: 3
- identity · other: 3
- identity · nct-acronym-mismatch: 2
- identity · name-drug-mismatch: 1
- identity · year-nct-era-mismatch: 1

## Highest-confidence findings (3-of-3 + HIGH)

### id=20 — WAYFINDER (NCT04039113) in SEVERE_ASTHMA_BIOLOGICS_REVIEW
- year=2023 pmid=39653044 group=Tezepelumab pediatric/adolescent
  - **coherence** (LOW / acronym-mismatch): Tezepelumab pediatric/adolescent severe asthma program is conventionally NOZOMI (NCT04673630); 'WAYFINDER' is not a recognized tezepelumab trial acronym.
  - **plausibility** (HIGH / literature-mismatch): WAYFINDER trial published 2024 has HR/RR=0.55 with CI [0.42, 0.71] identical to SIROCCO (id 19) — exact duplicate effect sizes across two different trials is statistically implausible and indicates copy-paste error.
  - **identity** (HIGH / famous-trial-wrong-nct): WAYFINDER label paired with NCT04039113 does not match the tezepelumab pediatric/adolescent (6-17y) program; NCT04039113 corresponds to DESTINATION (long-term safety extension), and the pediatric tezepelumab Ph3 is NCT04673630 (FUTURE/COURSE program). PMID 39653044 is also inconsistent with a pediatric efficacy primary publication.

## 2-of-3 + HIGH findings

### id=26 — CheckMate-238-ADJ (NCT02388906) in ADJUVANT_IO_PAN_TUMOR_REVIEW
- year=2017 pmid=28891423 group=Nivolumab adjuvant melanoma IIIB-IV
  - **plausibility** (HIGH / literature-mismatch): Same NCT02388906 (CheckMate-238) appears 3 times (ids 25, 26, 31) with different HRs: 0.65 (CI 0.51-0.83), 0.71 (0.58-0.88), 0.71 (0.58-0.88); published RFS HR was 0.65 (Weber NEJM 2017) so id 25 matches; ids 26 and 31 use HR=0.71 which is the 12mo recurrence-free RATE difference HR from later updates — inconsistent extractions for the same trial across reviews.
  - **identity** (MED / generic-name): Name 'CheckMate-238-ADJ' uses a non-canonical '-ADJ' suffix; CheckMate-238 is already the adjuvant melanoma trial, so the suffix is redundant and not used in the literature. Likely auto-generated label; identity itself (NCT02388906, PMID 28891423) is correct.

### id=27 — QuANTUM-R (NCT02668653) in AML_TARGETED_NEW_REVIEW
- year=2019 pmid=None group=Quizartinib (R/R FLT3+)
  - **plausibility** (HIGH / literature-mismatch): QuANTUM-R (Cortes Lancet Oncol 2019) quizartinib vs salvage chemo in R/R FLT3+ AML OS HR was 0.76 (95% CI 0.58-0.98) — matches. BUT NCT02668653 is QuANTUM-R; id 28 names QuANTUM-First with same NCT — QuANTUM-First is actually NCT02668653 too? No, QuANTUM-First is NCT02668653; QuANTUM-R is NCT02039726. NCT swap between trials.
  - **identity** (HIGH / nct-acronym-mismatch): NCT02668653 is QuANTUM-First (newly diagnosed FLT3-ITD AML, quizartinib + 7+3 chemo, Erba Lancet 2023), NOT QuANTUM-R. QuANTUM-R (relapsed/refractory FLT3+ AML, Cortes Lancet Oncol 2019) is NCT02039726. The two trials have been swapped/conflated.

### id=33 — PSILO-MDD (NCT03775200) in DEPRESSION_NEW_RAPID_REVIEW
- year=2021 pmid=33999283 group=Psilocybin 25mg single dose (MDD)
  - **coherence** (LOW / acronym-mismatch): 'PSILO-MDD' is a generic placeholder-looking name; NCT03775200 is COMP-001 (Compass Pathways psilocybin TRD), same NCT used at id=34 with correct acronym — suggests label fabrication while drug/disease (psilocybin/MDD) remains coherent.
  - **plausibility** (HIGH / literature-mismatch): NCT03775200 is the COMPASS COMP360 phase 2b psilocybin trial (Goodwin NEJM 2022), not a 2021 PSILO-MDD trial; pmid 33999283 is the Carhart-Harris NEJM 2021 escitalopram comparator trial which is NCT03429075. NCT-PMID mismatch.

### id=34 — COMP-001 (NCT03775200) in DEPRESSION_PSYCHEDELIC_NMA_REVIEW
- year=2022 pmid=None group=COMP360 25mg psilocybin TRD (COMP-001)
  - **plausibility** (HIGH / other): COMP-001 (Goodwin NEJM 2022) MADRS change at wk3 was -6.6 (95% CI -10.2, -2.9) for 25mg vs 1mg — matches extracted MD=-6.6 (CI -10.2, -3.0). BUT tE=cE=cN suggests counts not applicable for MD outcome; tN=79 for active arm but cN should be 1mg arm=79, not all 233 (5+10+25mg) participants. tE=79 (all 'events') in continuous-outcome row is nonsensical.
  - **identity** (MED / generic-name): 'COMP-001' is a sponsor program code (Compass Pathways protocol code), not a trial acronym. The published trial (Goodwin NEJM 2022) is typically referenced by sponsor + program identifier. NCT03775200 actually corresponds to a different psilocybin study (likely the Davis JAMA Psych 2021 trial, PMID 33999283 shown in id=33), suggesting the NCT-trial pairing is wrong here.

### id=47 — QUILT-3032 (NCT04165116) in BLADDER_NMIBC_NEW_NMA_REVIEW
- year=2023 pmid=None group=N-803 + BCG QUILT-3032 (single-arm)
  - **plausibility** (HIGH / other): QUILT-3032 N-803 + BCG is a single-arm trial (no historical-control HR published); extracted RR=0.65 (CI 0.55-0.77) with cE=cN=0 is fabricated — no comparator exists. Single-arm trials cannot produce relative effect estimates without indirect comparison.
  - **identity** (HIGH / famous-trial-wrong-nct): QUILT-3032 (N-803/anktiva + BCG, BCG-unresponsive NMIBC, Chamie 2023) is NCT03022825 (originally registered as QUILT-3.032), not NCT04165116. NCT04165116 does not correspond to the published QUILT-3.032 pivotal cohort.

### id=49 — Vivitrol-OUD (NCT00604682) in OUD_NEW_AGENTS_NMA_REVIEW
- year=2017 pmid=None group=Vivitrol naltrexone IM OUD
  - **plausibility** (HIGH / magnitude-extreme): Vivitrol naltrexone XR-OUD (Lee Lancet 2018, X:BOT) — extracted publishedHR=7.0 (CI 3.0-11.0) labeled estimandType=MD but value is OR-like and CI is symmetric absolute integers around 7 (3-11), suggesting confusion between point estimate and CI bounds being SD-like. estimandType=MD but counts 90/125 vs 38/125 produce RR≈2.4 not 7.0.
  - **identity** (MED / generic-name): 'Vivitrol-OUD' is a brand-name-plus-indication construction, not a canonical trial acronym; suggests post-hoc labelling rather than identification of a specific RCT. NCT00604682 should be verified against a named trial (e.g., XBOT/CTN-0051 is NCT02032433; Krupitsky 2011 is a different NCT).

### id=52 — ILLUMENATE-EU (NCT01858363) in PERIPHERAL_DCB_PAD_NMA_REVIEW
- year=2017 pmid=None group=Stellarex DCB EU (ILLUMENATE-EU)
  - **plausibility** (HIGH / wrong-direction): ILLUMENATE-EU Stellarex DCB vs POBA primary patency at 12mo published 70.9% vs 54.7% (Steiner JACC Cardiovasc Interv 2017); the DCB was SUPERIOR (RR<1 for restenosis or RR>1 for patency). Extracted 145/196=74% vs 65/98=66% with RR=1.11 (CI 0.94-1.31) crosses null and direction is ambiguous — but published primary was statistically significant (p=0.013). Inconsistent magnitude and CI.
  - **identity** (MED / famous-trial-wrong-nct): ILLUMENATE EU RCT (Stellarex DCB, Krishnan Circulation 2017) is NCT01927068. NCT01858363 is a different DCB study and does not match the ILLUMENATE EU pivotal cohort.

### id=58 — PEDAP (NCT04420572) in T1D_CLOSED_LOOP_NMA_REVIEW
- year=2023 pmid=37207334 group=Tandem CIQ pediatric 2-5y (PEDAP)
  - **plausibility** (HIGH / magnitude-extreme): PEDAP closed-loop pediatric T1D — extracted MD=12.0 (CI 9.0-15.0); the actual published outcome (Wadwa NEJM 2023) was time-in-range difference of +12.4 percentage points which IS plausible. BUT tE=68 (all) cE=32/34 as event counts with estimandType=MD is illegal — can't have both event counts and mean difference. Schema corruption.
  - **identity** (HIGH / famous-trial-wrong-nct): PEDAP (Pediatric Artificial Pancreas, Tandem Control-IQ in children 2-5y, Wadwa NEJM 2023) is NCT04796779, not NCT04420572. The NCT does not match the pediatric Control-IQ pivotal.

### id=67 — HELIOS-B (NCT05534659) in ATTR_CM_REVIEW
- year=2024 pmid=None group=ATTR-CM (mixed)
  - **plausibility** (LOW / other): HELIOS-B vutrisiran ATTR-CM ACM HR was 0.65 (Fontana NEJM 2024) primary composite; extracted HR=0.67 (CI 0.47-0.95) plausibly matches secondary ACM-alone HR. Consistent.
  - **identity** (HIGH / famous-trial-wrong-nct): HELIOS-B (vutrisiran ATTR-CM pivotal, Fontana NEJM 2024) is NCT04153149, not NCT05534659. The cited NCT does not correspond to the HELIOS-B pivotal cohort.

### id=71 — MEZAGITAMAB-ITP (NCT04278924) in ITP_NEW_AGENTS_REVIEW
- year=2024 pmid=41950473 group=Mezagitamab anti-CD38 ITP
  - **plausibility** (LOW / other): MEZAGITAMAB-ITP platelet response 36/40=90% vs 6/20=30%; RR=3.0 (CI 1.55-5.81) plausible for anti-CD38 phase 2 response endpoint.
  - **identity** (MED / generic-name): 'MEZAGITAMAB-ITP' name is drug-plus-indication, not an acronym; combined with the impossible PMID this row is likely a fabricated identity.

## 1-of-3 + HIGH (single-lens; review individually)

- **id=13** — GEMINI-2 (NCT01224171) in CD_BIOLOGICS_NMA_REVIEW
   - plausibility/literature-mismatch: GEMINI-2 (Crohn's, Sandborn NEJM 2013) wk6 remission was 14.5% (32/220) vedolizumab vs 6.8% (10/148) placebo — extracted counts match. However reported event rate in placebo arm corresponds to vedolizumab GEMINI-2 wk6 endpoint but the named outcome 'remission' has crude OR≈2.34 not 2.54; pmid 24859203 actually refers to Sandborn UC GEMINI-1, not GEMINI-2 Crohn's. PMID mismatch likely.
- **id=18** — SOURCE (NCT03406078) in SEVERE_ASTHMA_BIOLOGICS_REVIEW
   - plausibility/wrong-direction: SOURCE tezepelumab OCS-sparing trial (Wechsler Lancet Resp Med 2022) reported FAVORABLE odds ratio (1.28 favors tezepelumab for ≥50% OCS reduction is plausible but the trial actually MISSED its primary endpoint with OR=1.28 (0.69-2.39) — the extracted CI crosses 1, consistent with the published null. Acceptable but estimandType=OR correctly labeled.
- **id=24** — ATTRibute-CM (NCT03860935) in ACORAMIDIS_ATTR_CM_REVIEW
   - identity/other: PMID 41205147 is out of the plausible PubMed range for a 2024 publication (current 2024 PMIDs are ~38xxxxxx-39xxxxxx); ATTRibute-CM (Gillmore et al., NEJM 2024) is PMID 38122639. The cited PMID appears fabricated.
- **id=28** — QuANTUM-First (NCT02668653) in AML_VEN_FLT3_NMA_REVIEW
   - plausibility/literature-mismatch: QuANTUM-First (Erba Lancet 2023) quizartinib + 7+3 in ND FLT3-ITD AML OS HR was 0.78 (95% CI 0.62-0.98) — matches reported. BUT NCT02668653 is the QuANTUM-First trial; id 27 (QuANTUM-R) shares this NCT incorrectly (QuANTUM-R is NCT02039726). One of the two trials has wrong NCT.
- **id=32** — TRANSFORM-1 (NCT02418585) in DEPRESSION_NEW_RAPID_REVIEW
   - identity/nct-acronym-mismatch: NCT02418585 is TRANSFORM-2 (esketamine TRD pivotal, Popova 2019), NOT TRANSFORM-1. TRANSFORM-1 is NCT02417064 (Fedgchin 2019). The labels appear swapped with the TRANSFORM-2 row at id=35 (which has correct name but wrong PMID).
- **id=36** — BE READY (NCT03410992) in IL_PSORIASIS_NMA_REVIEW
   - plausibility/magnitude-extreme: BE READY PASI90 extracted as 318/349=91% vs 1/86=1.2% giving HR=871.9 (CI 117.5-6483); same trial id 30 has 273/349 vs 1/86 → HR=67.27. Same trial, two different event counts and OR=871.9 is absurdly extreme even for OR — likely single-event placebo + wrong active-arm n. estimandType=null misleading.
- **id=37** — ZUMA-1 (NCT02348216) in CART_B_CELL_LYMPHOMA_REVIEW
   - plausibility/other: ZUMA-1 axi-cel is a single-arm CAR-T pivotal trial (Neelapu NEJM 2017) — there is no control arm and no published HR; extracted publishedHR=0.83 (CI 0.74-0.9) with cE=cN=0 implies a phantom comparator. Single-arm trials cannot generate hazard ratios.
- **id=60** — SUPREME (NCT05012007) in SCLC_IO_REVIEW
   - identity/famous-trial-wrong-nct: Serplulimab maintenance ES-SCLC pivotal is ASTRUM-005 (NCT04063163, Cheng JAMA 2022, PMID 36194215), labelled as 'SUPREME' here. SUPREME is not a canonical SCLC trial acronym; the NCT05012007 + year 2024 + PMID 37731137 triple is inconsistent (PMID 37731137 is from 2023 and does not match a 2024 ES-SCLC pivotal).
- **id=61** — REACH-1 (NCT02953678) in GVHD_NEW_AGENTS_REVIEW
   - plausibility/other: REACH-1 ruxolitinib aGVHD is a single-arm phase 2 (Jagasia Blood 2020); extracted RR=0.549 (CI 0.43-0.67) with cE=cN=0 is fabricated — no comparator. Single-arm responses (54.9% ORR) being repackaged as RR.
- **id=63** — TRITON (NCT01568359) in PAH_SOTATERCEPT_BROAD_REVIEW
   - identity/year-nct-era-mismatch: TRITON (triple-combo upfront PAH, Chin et al., 2021/2022) is NCT02558231 (registered 2015). NCT01568359 was registered ~2012, predating the TRITON triple-combo concept, and does not correspond to the published TRITON trial.
- **id=70** — PROMISE-1 (NCT02559895) in CGRP_MIGRAINE_PREVENT_REVIEW
   - plausibility/wrong-direction: PROMISE-1 eptinezumab 100mg quarterly (Ashina Cephalalgia 2020) — extracted RR=1.51 (CI 1.24-1.84) is for 50% responder rate (favoring eptinezumab so RR>1 is correct for response) but extracted rates 129/223=58% vs 85/222=38% match published 50% MMD-responder analysis. Direction OK if outcome is response — flagged because label 'PREVENT' suggests migraine-day reduction where lower=better.
- **id=74** — LUTONIX-AV (NCT01710033) in HEMODIALYSIS_AV_ACCESS_DCB_NMA_REVIEW
   - plausibility/wrong-direction: LUTONIX-AV (Trerotola JVIR 2020) showed paclitaxel DCB SUPERIOR to POBA for primary patency (HR/RR favoring DCB, i.e. RR<1 for restenosis); extracted RR=1.46 (CI 1.13-1.88) with 87/142=61% vs 60/143=42% — this is RR for PATENCY (higher=better) so RR>1 is correct directionally IF outcome=patency. Estimand definition ambiguous; flagged for clarification.
- **id=76** — HARMONIZE (NCT01737697) in HYPERKALEMIA_K_BINDER_NMA_REVIEW
   - plausibility/crude-vs-HR-mismatch: HARMONIZE sodium zirconium cyclosilicate (Kosiborod JAMA 2014) — extracted tE=175/196 (89%) vs cE=30/62 (48%) labeled MD=-0.7 (CI -0.85,-0.55); MD is in mEq/L for K reduction (~-0.7 plausible) but event counts paired with MD outcome is schema-illegal. Estimand and counts contradict.
