# Task 2 scoping — SGLT2-HF base-template clones needing REBUILD (not patch)

_Scoped 2026-06-09. 29 non-SGLT2/non-HF apps still carry the full
SGLT2-HF base-template scaffold (PICO, subtitle, SEO/JSON-LD, hardcoded
PUBLISHED_META_BENCHMARKS, JS screening `hasRelevantPop` regex, and `hfref`
element IDs). Only the realData trial table was swapped to the correct topic.
`regenerate_pico.py` correctly EXCLUDED these as non-standard — they cannot be
auto-derived. A partial literal-replace would leave benchmarks/screening still
SGLT2 (inconsistent + scientifically wrong). Correct fix = per-topic rebuild via
the living-pipeline; fabricating per-topic benchmarks is forbidden.

| App | contam-hits | SGLT2 benchmarks? | Topic |
|---|---:|:--:|---|
| PHYSICAL_REHAB_OLDER_REVIEW.html | 167 | YES | RapidMeta Physiotherapy | Physical Rehabilitation in Older Adults NMA  |
| CRYPTOCOCCAL_MENINGITIS_AFRICA_REVIEW.html | 165 | YES | RapidMeta Infectious Disease | Cryptococcal Meningitis NMA in African  |
| DIABETIC_MACULAR_EDEMA_REVIEW.html | 165 | YES | RapidMeta Ophthalmology | DME Anti-VEGF NMA &mdash; Protocol T + YOSEM |
| DIABETIC_RETINOPATHY_REVIEW.html | 165 | YES | RapidMeta Ophthalmology | Diabetic Retinopathy NMA &mdash; Protocol S  |
| HEMOPHILIA_GENE_THERAPY_REVIEW.html | 165 | YES | RapidMeta Hematology | Hemophilia Gene Therapy NMA &mdash; GENEr8-1 +  |
| HIDRADENITIS_SUPPURATIVA_REVIEW.html | 165 | YES | RapidMeta Dermatology | Hidradenitis Suppurativa Biologics NMA &mdash; |
| HIV_TB_COINFECTION_ART_TIMING_REVIEW.html | 165 | YES | RapidMeta HIV-TB | HIV-TB Co-infection ART Timing NMA &mdash; SAPiT +  |
| HPV_VACCINE_SCHEDULES_REVIEW.html | 165 | YES | RapidMeta Vaccinology | HPV Vaccine Schedules NMA &mdash; PATRICIA + F |
| HYDROCORTISONE_SEPTIC_SHOCK_REVIEW.html | 165 | YES | RapidMeta ITU | Hydrocortisone in Septic Shock NMA &mdash; ADRENAL + A |
| ICU_SEDATION_REVIEW.html | 165 | YES | RapidMeta ITU | ICU Sedation NMA &mdash; SPICE-III + Strom-2010 + A2B- |
| MDR_TB_SHORTENED_REVIEW.html | 165 | YES | RapidMeta TB | MDR-TB Shortened-Regimen NMA &mdash; BPaLM + BPaL (TB-P |
| MEDITERRANEAN_DIET_CV_REVIEW.html | 165 | YES | RapidMeta Nutrition | Mediterranean Diet for CV Prevention NMA &mdash; |
| PEDIATRIC_HIV_ART_REVIEW.html | 165 | YES | RapidMeta Pediatric HIV | First-line ART Simplification NMA &mdash; OD |
| POLYCYTHEMIA_VERA_REVIEW.html | 165 | YES | RapidMeta Hematology | Polycythemia Vera NMA &mdash; RESPONSE + RESPON |
| POSTPARTUM_HEMORRHAGE_REVIEW.html | 165 | YES | RapidMeta Maternal Health | Postpartum Hemorrhage NMA &mdash; E-MOTIVE |
| ROTAVIRUS_VACCINE_AFRICA_REVIEW.html | 165 | YES | RapidMeta Vaccinology | African Rotavirus Vaccine NMA &mdash; Rotarix  |
| SEPSIS_RESUSCITATION_REVIEW.html | 165 | YES | RapidMeta ITU | Sepsis Early Resuscitation NMA &mdash; CENSER + CLOVER |
| SEVERE_PEDIATRIC_FEBRILE_AFRICA_REVIEW.html | 165 | YES | RapidMeta Pediatrics | Severe African Pediatric Febrile Illness NMA &m |
| VITAMIN_D_FRACTURE_FALL_REVIEW.html | 165 | YES | RapidMeta Nutrition | Vitamin D Mega-Trials NMA &mdash; VITAL + D-Heal |
| VITILIGO_REVIEW.html | 165 | YES | RapidMeta Dermatology | Vitiligo NMA &mdash; TRuE-V1 + TRuE-V2 + UpA-V |
| HIV_PREP_INJECTABLE_REVIEW.html | 164 | YES | RapidMeta HIV/Prevention | HIV PrEP NMA — Injectable CAB-LA + Oral F/T |
| MALARIA_VACCINE_REVIEW.html | 164 | YES | RapidMeta Vaccinology | Malaria Vaccine NMA — RTS,S/AS01 + R21/Matrix- |
| EBOLA_VACCINE_REVIEW.html | 108 | YES | RapidMeta Vaccinology | rVSV-ZEBOV Ebola Vaccine v0.1 (STRIVE Sierra L |
| HEPATITIS_B_TAF_TDF_REVIEW.html | 108 | YES | RapidMeta Hepatology | TAF vs TDF for Chronic Hepatitis B v0.1 (Buti+C |
| MHEALTH_ART_ADHERENCE_REVIEW.html | 108 | YES | RapidMeta Digital-Health | mHealth SMS for ART Adherence v0.1 (WelTel  |
| PNEUMONIA_AMOXICILLIN_DURATION_REVIEW.html | 108 | YES | RapidMeta Pediatric ID | Amoxicillin Dose+Duration for Pediatric CAP v |
| SAM_SIMPLIFIED_PROTOCOL_REVIEW.html | 108 | YES | RapidMeta Pediatric Nutrition | OptiMA/ComPAS Simplified-Protocol Acut |
| SCHISTOSOMIASIS_ARPRAZIQUANTEL_REVIEW.html | 108 | YES | RapidMeta NTD | L-PZQ ODT (Arpraziquantel) Phase 3 for Pediatric Schis |
| TB_DRUG_SUSCEPTIBLE_4MO_REVIEW.html | 108 | YES | RapidMeta Infectious-Disease | 4-Month Rifapentine-Moxifloxacin for Dr

---

## Task 2 — in-place decontamination DONE (2026-06-09)

User chose **decontaminate-in-place** (over quarantine / full-rebuild). Codemod
`scripts/decontaminate_sglt2_clones.py` (dry-run default, `--apply`, idempotent),
verified by `scripts/verify_decontamination.py` (**29/29 clean, inline JS parses,
2nd run = 0 changes**). Existing `tests/test_clone_no_leftover.py` +
`tests/test_data_integrity.py` = 10 passed. `realData` never touched.

**Two template tiers detected & handled differently:**
- Tier-1 (22 apps): display layer was SGLT2 — retargeted meta/OG + JSON-LD
  (description/keywords/mentions), H2 header, subtitle, PICO population
  (trial-scoped truthful phrasing), and the `hfref quadruple therapy` display slug
  (+ filename slug) to each app's own title-parsed topic.
- Tier-2 (7 apps): display already topic-correct; fixed the residual CT.gov drug
  query, the `mf-indication` value/label-mismatch bug, and a prose sentence that
  cited the SGLT2 Vaduganathan 2022 meta as a concordance check.

**Both tiers:** emptied the false `PUBLISHED_META_BENCHMARKS` to `{}` (consumer
returns `[]` = "no benchmark configured" — verified safe, no crash); neutralised
live CT.gov/PubMed/OpenAlex search queries off SGLT2 drug terms onto topic keywords.

**NOT fabricated:** no per-topic benchmark numbers, no intervention/comparator/
outcome drug names invented.

**Class-D residue intentionally LEFT (the genuine rebuild core, documented):**
engine-internal SGLT2 logic that is dormant (these apps carry trial names but
`tE/tN/cE/cN = null`, so nothing pools through it) and cannot be replaced without
breaking JS wiring or fabricating per-topic definitions —
~286 `empagliflozin`/`dapagliflozin` refs (relevance/HR screening regexes),
~820 `heart failure` (CV-relevance scorers + outcome-key maps),
~85 `HFrEF/HFpEF` (phenotype subgroup options), ~1083 `MACE` (outcome taxonomy),
and the Arabic translation **values** (الفينيرينون). These need the per-topic
living-pipeline rebuild, unchanged from the original verdict above. |