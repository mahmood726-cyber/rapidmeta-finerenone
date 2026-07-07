# REMOVED / QUARANTINED apps — DO2 count-correction follow-up (2026-07-07)

These live public apps have **no clean drug-vs-control single-drug pivotal** and cannot be made honest by a count re-derivation or a native-effect rebuild (active-comparator-only, single-arm, dose-comparison, wrong-drug/PK source, temporal impossibility, or negative-primary misrepresentation). Truth-first action: de-list.

**Fully REVERSIBLE and git-tracked.** App HTML files are **moved (not deleted)** root -> `removed/`; `index.html` cards + curated rows + E156-map entries and `sitemap.xml` URLs are stripped. Restore: `git mv removed/<APP>.html <APP>.html` + revert the index/sitemap edits.

**Status: STAGED — NOT deployed.** Built against `origin/main` blobs (DO1 deploy b23579c5f). Applying live needs Mahmood's go.

**Bases de-listed:** 17  |  **Files to move:** 36

| # | App file | Reason |
|---|---|---|
| 1 | `ANIFROLUMAB_SLE_AUTO_FULL_REVIEW.html` | TULIP-1 primary SRI-4 was NEGATIVE (65/180 vs 74/184, p=0.41); displayed OR 1.55 does not match primary — no honest single-drug pivotal |
| 2 | `ANIFROLUMAB_SLE_AUTO_REVIEW.html` | TULIP-1 primary SRI-4 was NEGATIVE (65/180 vs 74/184, p=0.41); displayed OR 1.55 does not match primary — no honest single-drug pivotal |
| 3 | `ANIFROLUMAB_SLE_PHASE23_DOSE_RESP_REVIEW.html` | TULIP-1 primary SRI-4 was NEGATIVE (65/180 vs 74/184, p=0.41); displayed OR 1.55 does not match primary — no honest single-drug pivotal |
| 4 | `ANIFROLUMAB_SLE_REVIEW.html` | TULIP-1 primary SRI-4 was NEGATIVE (65/180 vs 74/184, p=0.41); displayed OR 1.55 does not match primary — no honest single-drug pivotal |
| 5 | `DABRAFENIB_MELANOMA_AUTO_FULL_REVIEW.html` | DREAMseq is dab+tram vs nivo+ipi (active comparator, OS%); no drug-vs-placebo 2x2; single-drug framing not supportable |
| 6 | `DABRAFENIB_MELANOMA_AUTO_REVIEW.html` | DREAMseq is dab+tram vs nivo+ipi (active comparator, OS%); no drug-vs-placebo 2x2; single-drug framing not supportable |
| 7 | `DARUNAVIR_HIV_AUTO_FULL_REVIEW.html` | replacement PMID 25950206 is a darunavir PK-in-pregnancy paper, not an efficacy RCT; displayed 2x2 not verifiable |
| 8 | `DARUNAVIR_HIV_AUTO_REVIEW.html` | replacement PMID 25950206 is a darunavir PK-in-pregnancy paper, not an efficacy RCT; displayed 2x2 not verifiable |
| 9 | `DELGOCITINIB_AD_AUTO_FULL_REVIEW.html` | replacement PMID 40186746 is a HRQoL/PRO paper of the phase-2b CHE trial, not primary efficacy results; 2x2 not verifiable |
| 10 | `DELGOCITINIB_AD_AUTO_REVIEW.html` | replacement PMID 40186746 is a HRQoL/PRO paper of the phase-2b CHE trial, not primary efficacy results; 2x2 not verifiable |
| 11 | `DELGOCITINIB_HAND_AUTO_FULL_REVIEW.html` | replacement PMID 40186746 is a HRQoL/PRO paper of the phase-2b CHE trial, not primary efficacy results; 2x2 not verifiable |
| 12 | `DELGOCITINIB_HAND_AUTO_REVIEW.html` | replacement PMID 40186746 is a HRQoL/PRO paper of the phase-2b CHE trial, not primary efficacy results; 2x2 not verifiable |
| 13 | `ELVITEGRAVIR_HIV_AUTO_FULL_REVIEW.html` | replacement PMID 29520730 is an efavirenz dose-reduction population-PK paper (wrong drug, PK, not elvitegravir efficacy) |
| 14 | `ELVITEGRAVIR_HIV_AUTO_REVIEW.html` | replacement PMID 29520730 is an efavirenz dose-reduction population-PK paper (wrong drug, PK, not elvitegravir efficacy) |
| 15 | `IPILIMUMAB_RENAL_AUTO_FULL_REVIEW.html` | CheckMate-914 primary is DFS HR 0.92 (0.71-1.19); displayed 2x2 6/405,3/411 represents treatment-related deaths, not the primary |
| 16 | `IPILIMUMAB_RENAL_AUTO_REVIEW.html` | CheckMate-914 primary is DFS HR 0.92 (0.71-1.19); displayed 2x2 6/405,3/411 represents treatment-related deaths, not the primary |
| 17 | `OLANZAPINE_CINV_AUTO_FULL_REVIEW.html` | PMID 19775450 (2009) PRE-DATES NCT02484911 (registered 2015) — temporal impossibility; cannot be that trial results |
| 18 | `OLANZAPINE_CINV_AUTO_REVIEW.html` | PMID 19775450 (2009) PRE-DATES NCT02484911 (registered 2015) — temporal impossibility; cannot be that trial results |
| 19 | `PASIREOTIDE_CUSHING_AUTO_FULL_REVIEW.html` | PMID 29032078 is pasireotide 10mg-vs-30mg dose comparison (no placebo arm); both arms active — invalid as drug-vs-control |
| 20 | `PASIREOTIDE_CUSHING_AUTO_REVIEW.html` | PMID 29032078 is pasireotide 10mg-vs-30mg dose comparison (no placebo arm); both arms active — invalid as drug-vs-control |
| 21 | `ROXADUSTAT_ANEMIA_CKD_AUTO_FULL_REVIEW.html` | PMID 36749544 is a POOLED SAFETY analysis of 4 roxadustat phase-3 trials (MACE HR), not the DOLOMITES single-trial efficacy |
| 22 | `ROXADUSTAT_ANEMIA_CKD_AUTO_REVIEW.html` | PMID 36749544 is a POOLED SAFETY analysis of 4 roxadustat phase-3 trials (MACE HR), not the DOLOMITES single-trial efficacy |
| 23 | `ROXADUSTAT_RENAL_ANEMIA_AUTO_FULL_REVIEW.html` | PMID 36749544 is a POOLED SAFETY analysis, not the DOLOMITES (NCT02021318) single-trial results; displayed MD not in source |
| 24 | `ROXADUSTAT_RENAL_ANEMIA_AUTO_REVIEW.html` | PMID 36749544 is a POOLED SAFETY analysis, not the DOLOMITES (NCT02021318) single-trial results; displayed MD not in source |
| 25 | `TICAGRELOR_STROKE_AUTO_FULL_REVIEW.html` | PMID 36682595 is a small platelet-aggregation/inflammation PD study (ticagrelor vs clopidogrel in CKD), not a stroke outcome trial |
| 26 | `TICAGRELOR_STROKE_AUTO_REVIEW.html` | PMID 36682595 is a small platelet-aggregation/inflammation PD study (ticagrelor vs clopidogrel in CKD), not a stroke outcome trial |
| 27 | `UPADACITINIB_RA_AUTO_FULL_REVIEW.html` | PMID 31194885 is an upadacitinib exposure-response PK modeling paper (phase-2 E-R), not efficacy results; 2x2 not verifiable |
| 28 | `UPADACITINIB_RA_AUTO_REVIEW.html` | PMID 31194885 is an upadacitinib exposure-response PK modeling paper (phase-2 E-R), not efficacy results; 2x2 not verifiable |
| 29 | `UPADACITINIB_RA_SELECT_DOSE_RESP_REVIEW.html` | PMID 31194885 is an upadacitinib exposure-response PK modeling paper (phase-2 E-R), not efficacy results; 2x2 not verifiable |
| 30 | `ZIRCONIUM_HYPERKALEMIA_AUTO_FULL_REVIEW.html` | PMID 35135481 is a DIALIZE post-hoc analysis; displayed OR 68.77 (CI 10.85-2810.85) is broken/disconnected from the 2x2 |
| 31 | `ZIRCONIUM_HYPERKALEMIA_AUTO_REVIEW.html` | PMID 35135481 is a DIALIZE post-hoc analysis; displayed OR 68.77 (CI 10.85-2810.85) is broken/disconnected from the 2x2 |
| 32 | `BPAL_MDRTB_REVIEW.html` | Nix-TB is a SINGLE-ARM study (no control arm); its 2x2 is arm-vs-subgroup, not a drug-vs-control comparison — cannot be pooled honestly |
| 33 | `LINEZOLID_TB_AUTO_FULL_REVIEW.html` | Lee 2012 is immediate-vs-delayed linezolid start — BOTH arms receive the drug; there is no drug-vs-control contrast |
| 34 | `LINEZOLID_TB_AUTO_REVIEW.html` | Lee 2012 is immediate-vs-delayed linezolid start — BOTH arms receive the drug; there is no drug-vs-control contrast |
| 35 | `CAPMATINIB_LUNG_AUTO_FULL_REVIEW.html` | recovered pivotal GEOMETRY mono-1 is single-arm ORR (no control arm); no drug-vs-control effect exists — cannot be made a comparison |
| 36 | `CAPMATINIB_LUNG_AUTO_REVIEW.html` | recovered pivotal GEOMETRY mono-1 is single-arm ORR (no control arm); no drug-vs-control effect exists — cannot be made a comparison |
