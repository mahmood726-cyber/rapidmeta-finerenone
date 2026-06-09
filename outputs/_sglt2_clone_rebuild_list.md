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
| TB_DRUG_SUSCEPTIBLE_4MO_REVIEW.html | 108 | YES | RapidMeta Infectious-Disease | 4-Month Rifapentine-Moxifloxacin for Dr |