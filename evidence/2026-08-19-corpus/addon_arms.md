# Add-on Arm Sweep

> **THE HEADLINE IS 52% NOT_ASSESSABLE, NOT THE 9.**
>
> This is an OBJECT-SIDE LABEL TEST and it is known to be weaker than the method that found
> the defect it was written to sweep for. sglt2-hf's seven add-on trials were caught by
> READING THE REGISTRY -- arm types and intervention records from the raw ClinicalTrials.gov
> v2 payload. **This sweep would have missed every one of them**, because those trials are not
> in any object's `inputs.trials` at all; they were search results.
>
> So the result is: **9 suspected over the assessable half, by a method weaker than the one
> that found the original seven.** 165 of 319 trial records (52%) carry no arm labels that
> support the test and are NOT_ASSESSABLE -- not clean.
>
> What this mostly establishes is that **the object-side test is not the instrument for this
> question.** A corpus-wide answer needs registry reads for every included trial, which is a
> different job with a different cost, and it has not been done. The 9 must not be quoted as
> a corpus count.


Date: 2026-08-19

Scope: object-side only; no network; read `inputs.trials[].arms[].label` and `inputs.trials[].arms[].role` from `ssot/<topic>/<topic>.json`.

## Method

- A trial is `SUSPECTED_ADDON` when at least one retained intervention component appears in both a treatment-role arm label and a control-role arm label.
- Labels are split on `/`, `+`, `,`, `plus`, `and`, and `with`; doses, units, route/frequency words, and generic study/formulation words are removed.
- Matching-placebo guard: components containing `placebo`, `matching`, `matched`, `dummy`, or `sham` do not count as containing the named active drug. This prevents `Placebo matching X` from becoming evidence that X is in the control arm.
- A trial with no usable labelled treatment and control arms is `NOT_ASSESSABLE`, not a clean negative.

## Known-answer check

PASS: the `sglt2-hf` included trials NCT03036124 DAPA-HF, NCT03057977 EMPEROR-Reduced, NCT03057951 EMPEROR-Preserved, and NCT03619213 DELIVER returned zero suspected add-on hits.

- NCT03036124 DAPA-HF: NO_ADDON_FOUND; treatment "dapagliflozin 10 mg once daily"<br>control "placebo"
- NCT03057951 EMPEROR-Preserved: NO_ADDON_FOUND; treatment "empagliflozin 10 mg once daily"<br>control "placebo"
- NCT03057977 EMPEROR-Reduced: NO_ADDON_FOUND; treatment "empagliflozin 10 mg once daily"<br>control "placebo"
- NCT03619213 DELIVER: NO_ADDON_FOUND; treatment "dapagliflozin 10 mg once daily"<br>control "placebo"

## Corpus totals

- Objects read: 135
- Objects without included trials: 4
- Included trial records read: 319
- Assessable trial records: 154
- `NOT_ASSESSABLE` trial records: 165
- Suspected add-on/shared-token trial records: 9
- Topics with at least one suspected trial: 7
- Matching-placebo guard prevented trial-level candidates: 5
- Matching-placebo guard removed shared-token matches: 8

## Ranked suspected topics

| topic | n trials | n not assessable | n suspected add-on | shared token(s) | arm labels |
|---|---:|---:|---:|---|---|
| cryptococcal-meningitis | 3 | 0 | 3 | amphotericin, antiretroviral, deoxycholate, fluconazole, flucytosine | ACTA: amphotericin, deoxycholate, fluconazole, flucytosine; treatment "oral fluconazole plus flucytosine for two weeks; the trial calls this the oral-regimen group"<br>treatment "one week of amphotericin B deoxycholate, partner drug randomised between flucytosine and fluconazole; the 1-week amphotericin B group"<br>control "two weeks of amphotericin B deoxycholate, partner drug randomised between flucytosine and fluconazole; the 2-week amphotericin B group, which is the trial's active control"<br>AMBITION-cm: amphotericin, fluconazole, flucytosine; treatment "a single ten milligram per kilogram dose of liposomal amphotericin B with flucytosine and fluconazole for two weeks; the trial calls this the AmBisome group"<br>control "one week of amphotericin B deoxycholate with flucytosine, then fluconazole; the trial's active control, being the standard care it was tested against"<br>NCT01075152: antiretroviral; treatment "antiretroviral therapy started within forty-eight hours of randomisation; the earlier-ART group"<br>control "antiretroviral therapy started four weeks after randomisation; the deferred-ART group, which is the trial's control strategy" |
| acs-antiplatelet-review | 4 | 0 | 1 | ticagrelor | NCT02270242 TWILIGHT: ticagrelor; treatment "Aspirin + Ticagrelor"<br>control "Placebo + Ticagrelor" |
| attr-pn-review | 3 | 0 | 1 | vutrisiran | NCT03759379 HELIOS-A: vutrisiran; treatment "Vutrisiran + Vutrisiran (HELIOS-A)"<br>control "Patisiran + Vutrisiran (HELIOS-A)" |
| evolocumab-mixed-dyslipidemia-auto-full-review | 2 | 0 | 1 | atorvastatin | NCT02662569 BERSON: atorvastatin; treatment "Atorvastatin (Q2W)"<br>control "Evolocumab QM + Atorvastatin" |
| malaria-vaccines | 8 | 0 | 1 | chemoprevention | NCT03143218 RTS,S/AS01 seasonal vaccination against seasonal chemoprevention: chemoprevention; treatment "RTS,S/AS01 alone"<br>control "seasonal chemoprevention alone"<br>treatment "vaccine and chemoprevention combined" |
| netarsudil-ocular-hypertension-auto-full-review | 3 | 0 | 1 | ar-13324 | NCT02207621 ROCKET-2: ar-13324; treatment "AR-13324 Ophthalmic Solution 0.02% & pla"<br>control "AR-13324 Ophthalmic Solution 0.02% BID" |
| rivaroxaban-vasc-review | 4 | 0 | 1 | aspirin | NCT01776424 COMPASS: aspirin; treatment "Rivaroxaban 2.5mg + Aspirin 100mg"<br>control "Rivaroxaban Placebo + Aspirin 100mg" |

## Suspected-trial details

### cryptococcal-meningitis

- ACTA
  - shared token(s): amphotericin, deoxycholate, fluconazole, flucytosine
  - arm labels: treatment "oral fluconazole plus flucytosine for two weeks; the trial calls this the oral-regimen group"<br>treatment "one week of amphotericin B deoxycholate, partner drug randomised between flucytosine and fluconazole; the 1-week amphotericin B group"<br>control "two weeks of amphotericin B deoxycholate, partner drug randomised between flucytosine and fluconazole; the 2-week amphotericin B group, which is the trial's active control"
- AMBITION-cm
  - shared token(s): amphotericin, fluconazole, flucytosine
  - arm labels: treatment "a single ten milligram per kilogram dose of liposomal amphotericin B with flucytosine and fluconazole for two weeks; the trial calls this the AmBisome group"<br>control "one week of amphotericin B deoxycholate with flucytosine, then fluconazole; the trial's active control, being the standard care it was tested against"
- NCT01075152
  - shared token(s): antiretroviral
  - arm labels: treatment "antiretroviral therapy started within forty-eight hours of randomisation; the earlier-ART group"<br>control "antiretroviral therapy started four weeks after randomisation; the deferred-ART group, which is the trial's control strategy"

### acs-antiplatelet-review

- NCT02270242 TWILIGHT
  - shared token(s): ticagrelor
  - arm labels: treatment "Aspirin + Ticagrelor"<br>control "Placebo + Ticagrelor"

### attr-pn-review

- NCT03759379 HELIOS-A
  - shared token(s): vutrisiran
  - arm labels: treatment "Vutrisiran + Vutrisiran (HELIOS-A)"<br>control "Patisiran + Vutrisiran (HELIOS-A)"

### evolocumab-mixed-dyslipidemia-auto-full-review

- NCT02662569 BERSON
  - shared token(s): atorvastatin
  - arm labels: treatment "Atorvastatin (Q2W)"<br>control "Evolocumab QM + Atorvastatin"

### malaria-vaccines

- NCT03143218 RTS,S/AS01 seasonal vaccination against seasonal chemoprevention
  - shared token(s): chemoprevention
  - arm labels: treatment "RTS,S/AS01 alone"<br>control "seasonal chemoprevention alone"<br>treatment "vaccine and chemoprevention combined"

### netarsudil-ocular-hypertension-auto-full-review

- NCT02207621 ROCKET-2
  - shared token(s): ar-13324
  - arm labels: treatment "AR-13324 Ophthalmic Solution 0.02% & pla"<br>control "AR-13324 Ophthalmic Solution 0.02% BID"

### rivaroxaban-vasc-review

- NCT01776424 COMPASS
  - shared token(s): aspirin
  - arm labels: treatment "Rivaroxaban 2.5mg + Aspirin 100mg"<br>control "Rivaroxaban Placebo + Aspirin 100mg"

## arni-hfref callout

`arni-hfref` is the flagship active-comparator programme (sacubitril/valsartan against enalapril, on background therapy).
It does not trip this label-only shared-token test in any included trial. The explicit arm labels name sacubitril/valsartan in the treatment arms and enalapril in the control arms; background therapy is not named as a shared arm-label component.

- NCT01035255 PARADIGM-HF: NO_ADDON_FOUND; treatment "LCZ696 (sacubitril/valsartan) 200 mg twice daily"<br>control "enalapril 10 mg twice daily"
- NCT02468232 PARALLEL-HF: NO_ADDON_FOUND; treatment "sacubitril/valsartan 200 mg twice daily"<br>control "enalapril 10 mg twice daily"
- NCT04023227 PARACHUTE-HF: NO_ADDON_FOUND; treatment "sacubitril/valsartan, target 200 mg twice daily"<br>control "enalapril, target 10 mg twice daily"
- NCT04853758 ANSWER-HF: NO_ADDON_FOUND; treatment "sacubitril/valsartan"<br>control "enalapril"

## Matching-placebo guard removals

The guard removal count is a finding: without it, matching-placebo labels would create false shared-token candidates.

| topic | trial | removed token(s) | remaining suspected token(s) | arm labels |
|---|---|---|---|---|
| apixaban-af-review | NCT04218266 PACIFIC-AF | apixaban, bay2433334 | none | treatment "BAY2433334 50mg+Apixaban matching placebo"<br>control "BAY2433334 matching placebo+Apixaban" |
| bococizumab-lipid-review | NCT02458287 SPIRE-AI | bococizumab | none | treatment "Bococizumab 150mg"<br>control "Bococizumab 75mg placebo" |
| colchicine-cvd-review | NCT02551094 COLCOT | colchicine | none | treatment "colchicine"<br>control "colchicine placebo" |
| doac-af-review | NCT00781391 ENGAGE AF-TIMI 48 | edoxaban, warfarin | none | treatment "High Dose Edoxaban/Placebo Warfarin"<br>control "Warfarin/Placebo Edoxaban" |
| incretin-hfpef-review | NCT04916470 STEP-HFpEF DM | semaglutide | none | treatment "Semaglutide 2.4 mg once weekly (OW)"<br>control "Semaglutide placebo OW" |
| rivaroxaban-vasc-review | NCT01776424 COMPASS | rivaroxaban | aspirin | treatment "Rivaroxaban 2.5mg + Aspirin 100mg"<br>control "Rivaroxaban Placebo + Aspirin 100mg" |

## NOT_ASSESSABLE topics

`NOT_ASSESSABLE` means the included trial record lacks enough arm-label structure for this test. These rows are not clean negatives.

| topic | n trials | n not assessable | reason counts |
|---|---:|---:|---|
| malaria-act-review | 5 | 5 | no inputs.trials[].arms array with arm labels: 5 |
| anidulafungin-candida-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| ceftaroline-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| ceftolozane-infection-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| ceftolozane-taz-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| enoxaparin-vte | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| evolocumab-ascvd-auto2 | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| fidaxomicin-cdi-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| fidaxomicin-cdiff | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| hiv-prep-injectable-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| ivermectin-lf-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| malaria-vaccine | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| mdr-tb-shortened | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| menacwy-booster | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| meropenem-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| mipomersen-hofh | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| olmesartan-htn | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| plazomicin-infection-auto-full-review | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| raltegravir-hiv | 3 | 3 | no inputs.trials[].arms array with arm labels: 3 |
| agyw-hiv-prep-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| amoxicillin-aom | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| anidulafungin-fungal-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| apixaban-vte | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| azilsartan-chlorthalidone-vs-olmesartan-hctz | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| bezlotoxumab-cdi | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| bezlotoxumab-cdiff | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| bosentan-pah | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| cab-prep-hiv-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| cefepime-taz-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| ceftazidime-avibactam-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| covid-oral-antivirals | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| cvncov-covid19 | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| cvncov-sarscov2 | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| dabigatran-af | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| dabigatran-stroke | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| delamanid-tb | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| doravirine-hiv | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| doripenem | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| drotrecogin-sepsis | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| edoxaban-vte | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| eravacycline-infection-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| ertapenem-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| ertapenem-infect-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| etripamil-psvt | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| fondaparinux-vte | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| gepotidacin-urinary-tract-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| influenza-recombinant | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| lefamulin-cabp-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| lefamulin-cap-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| lenacapavir-hiv | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| lenacapavir-prep-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| linezolid-mrsa | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| menacyw-healthy-volunteers-auto-full-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| nirsevimab-infant-rsv-review | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| posaconazole-fungal | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| rifapentine-tb | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| riociguat-pah | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| sarilumab-covid | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| sotatercept-pah | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| sotatercept-pah-auto2 | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| thiamine-sepsis | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| warfarin-af | 2 | 2 | no inputs.trials[].arms array with arm labels: 2 |
| bamlanivimab-covid | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| bamlanivimab-outp | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| casirivimab-covid | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| cryptococcal-meningitis-africa | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| evinacumab-hofh | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| inclisiran-hofh | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| maribavir-cmv | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| mavacamten-ohcm | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| moxifloxacin-respi | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| omecamtiv-heartfail | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| omecamtiv-hf | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| omecamtiv-hfref | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| pediatric-hiv-art | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| remdesivir-covid | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| sacubitril-heartfail | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| sacubitril-valsartan-hf | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| selexipag-pah | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| ser109-cdi | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| tecovirimat-mpox | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |
| tigecycline-infection | 1 | 1 | no inputs.trials[].arms array with arm labels: 1 |

## Full per-topic summary

| topic | n trials | n assessable | n not assessable | n suspected add-on | status counts |
|---|---:|---:|---:|---:|---|
| ablation-af-review | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| acs-antiplatelet-review | 4 | 4 | 0 | 1 | NO_ADDON_FOUND: 3; SUSPECTED_ADDON: 1 |
| agyw-hiv-prep-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| alirocumab-lipid | 6 | 6 | 0 | 0 | NO_ADDON_FOUND: 6 |
| amoxicillin-aom | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| anidulafungin-candida-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| anidulafungin-fungal-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| antimalarial-act | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| apixaban-acs-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| apixaban-af-review | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| apixaban-vte | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| arni-hfref | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| attr-cm-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| attr-pn-review | 3 | 3 | 0 | 1 | NO_ADDON_FOUND: 2; SUSPECTED_ADDON: 1 |
| azilsartan-chlorthalidone-vs-olmesartan-hctz | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| bamlanivimab-covid | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| bamlanivimab-outp | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| bempedoic-acid-review | 1 | 1 | 0 | 0 | NO_ADDON_FOUND: 1 |
| bezlotoxumab-cdi | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| bezlotoxumab-cdiff | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| bococizumab-lipid-review | 5 | 5 | 0 | 0 | NO_ADDON_FOUND: 5 |
| bosentan-pah | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| cab-prep-hiv-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| cangrelor-pci-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| casirivimab-covid | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| caspofungin-fungal-auto-full-review | 0 | 0 | 0 | 0 | NO_INCLUDED_TRIALS: 1 object |
| cefepime-taz-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| ceftaroline-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| ceftazidime-avibactam-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| ceftolozane-infection-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| ceftolozane-taz-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| colchicine-cvd-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| covid-oral-antivirals | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| covid19-vaccines | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| cryptococcal-meningitis | 3 | 3 | 0 | 3 | SUSPECTED_ADDON: 3 |
| cryptococcal-meningitis-africa | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| cvncov-covid19 | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| cvncov-sarscov2 | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| dabigatran-af | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| dabigatran-stroke | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| dabigatran-vte-review | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| delamanid-tb | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| doac-af-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| doac-cancer-vte-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| doravirine-hiv | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| doripenem | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| drotrecogin-sepsis | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| edoxaban-vte | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| empagliflozin-hf-auto-full-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| emtricitabine-hiv-auto-full-review | 0 | 0 | 0 | 0 | NO_INCLUDED_TRIALS: 1 object |
| enoxaparin-vte | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| eravacycline-infection-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| ertapenem-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| ertapenem-infect-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| etesevimab-covid-auto-full-review | 0 | 0 | 0 | 0 | NO_INCLUDED_TRIALS: 1 object |
| etripamil-psvt | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| evinacumab-hofh | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| evolocumab-ascvd-auto2 | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| evolocumab-dyslipidemia-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| evolocumab-mixed-dyslipidemia-auto-full-review | 2 | 2 | 0 | 1 | NO_ADDON_FOUND: 1; SUSPECTED_ADDON: 1 |
| fcm-hf-review | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| fidaxomicin-cdi-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| fidaxomicin-cdiff | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| finerenone-cv | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| finerenone-review | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| fondaparinux-vte | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| gepotidacin-urinary-tract-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| hepatitis-b-taf-tdf-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| hiv-prep-injectable-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| icosapent-lipid-auto-full-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| inclisiran-hofh | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| inclisiran-lipid-kidney-auto-full-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| incretin-hfpef-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| influenza-recombinant | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| intensive-bp-review | 6 | 6 | 0 | 0 | NO_ADDON_FOUND: 6 |
| iv-iron-hf | 5 | 5 | 0 | 0 | NO_ADDON_FOUND: 5 |
| ivermectin-lf-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| lefamulin-cabp-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| lefamulin-cap-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| lenacapavir-hiv | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| lenacapavir-prep | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| lenacapavir-prep-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| linezolid-mrsa | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| malaria-act-review | 5 | 0 | 5 | 0 | NOT_ASSESSABLE: 5 |
| malaria-vaccine | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| malaria-vaccines | 8 | 8 | 0 | 1 | NO_ADDON_FOUND: 7; SUSPECTED_ADDON: 1 |
| maribavir-cmv | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| mavacamten-hcm-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| mavacamten-ohcm | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| mavacamten-ohcm-review | 1 | 1 | 0 | 0 | NO_ADDON_FOUND: 1 |
| mdr-tb-shortened | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| men-acwy-auto-full-review | 0 | 0 | 0 | 0 | NO_INCLUDED_TRIALS: 1 object |
| menacwy-booster | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| menacyw-healthy-volunteers-auto-full-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| meropenem-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| mipomersen-hofh | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| mitral-funcmr-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| moxifloxacin-respi | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| netarsudil-ocular-hypertension-auto-full-review | 3 | 3 | 0 | 1 | NO_ADDON_FOUND: 2; SUSPECTED_ADDON: 1 |
| nirsevimab-infant-rsv-review | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| olmesartan-htn | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| omecamtiv-heartfail | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| omecamtiv-hf | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| omecamtiv-hfref | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| pcsk9-inhibitors-cv-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| pcsk9-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| pediatric-hiv-art | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| pitavastatin-auto-full-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| plazomicin-infection-auto-full-review | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| posaconazole-fungal | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| prevnar15-pneumo | 7 | 7 | 0 | 0 | NO_ADDON_FOUND: 7 |
| raltegravir-hiv | 3 | 0 | 3 | 0 | NOT_ASSESSABLE: 3 |
| remdesivir-covid | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| rifapentine-tb | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| riociguat-pah | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| rivaroxaban-acs-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| rivaroxaban-vasc-review | 4 | 4 | 0 | 1 | NO_ADDON_FOUND: 3; SUSPECTED_ADDON: 1 |
| rosuvastatin-auto-full-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| rotavirus-vaccine-africa-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| sacubitril-heartfail | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| sacubitril-valsartan-hf | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| sarilumab-covid | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| selexipag-pah | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| ser109-cdi | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| sglt2-ckd-review | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| sglt2-hf | 4 | 4 | 0 | 0 | NO_ADDON_FOUND: 4 |
| sglt2-mace-cvot-review | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| sotagliflozin-hf | 2 | 2 | 0 | 0 | NO_ADDON_FOUND: 2 |
| sotatercept-pah | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| sotatercept-pah-auto2 | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| tecovirimat-mpox | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| thiamine-sepsis | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |
| tigecycline-ciai | 3 | 3 | 0 | 0 | NO_ADDON_FOUND: 3 |
| tigecycline-infection | 1 | 0 | 1 | 0 | NOT_ASSESSABLE: 1 |
| warfarin-af | 2 | 0 | 2 | 0 | NOT_ASSESSABLE: 2 |

## Could not determine

165 included trial record(s) were not assessable because they lacked usable arm labels or roles. They are not counted as no add-on found.
This sweep can identify shared treatment/control label components, but it does not prove clinical add-on status, topic-drug identity, or whether a shared molecule is part of a dose, timing, formulation, or background contrast. The arm labels quoted above are the evidence for each suspect.

## Hardcode disclosure

| Item | Static or dynamic | Disclosure |
|---|---|---|
| SSOT object data | dynamic | Read live from `ssot/<topic>/<topic>.json`; no trial counts are hardcoded. |
| Matching-placebo guard and stop words | static | Encoded in `ssot/sweep_addon_arms.py` to make the detector deterministic and reviewable. |
| SGLT2 known-answer check | static | The four expected `sglt2-hf` included NCT IDs are fixed as a fail-closed regression test. |

Generated by `python -W error ssot/sweep_addon_arms.py --output evidence/2026-08-19-corpus/addon_arms.md`.
