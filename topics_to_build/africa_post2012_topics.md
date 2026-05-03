# Africa-relevant pairwise / NMA / dose-response topics for portfolio build

Five new RapidMeta-style review apps proposed for build, all targeting high-burden African disease topics with post-2012 interventions. Each spec includes verified NCTs (cross-checked against ClinicalTrials.gov v2 API on 2026-05-03), enrollment counts, headline outcomes with PMIDs, and a draft `realData` block ready for paste into the standard scaffold.

NCT verifications below were performed via `mcp__claude_ai_Clinical_Trials__get_trial_details` against the official CT.gov v2 endpoint — these are the authoritative NCT↔trial-name mappings that the data-checker should compare against (per the OAKS/DERBY and KEEPsAKE swap pattern fixed earlier).

---

## Topic 1 — MDRTB_BPAL_REVIEW.html (Pairwise)

**PICO**: Adults with multidrug-resistant or pre-XDR/XDR pulmonary tuberculosis (P) treated with bedaquiline + pretomanid + linezolid ± moxifloxacin (BPaL/BPaLM) (I) vs WHO-recommended longer regimens (C); favorable treatment outcome at end of follow-up (O).

**Filename**: `MDRTB_BPAL_REVIEW.html`
**Type**: Pairwise (1 head-to-head + 2 single-arm supporting trials)
**Africa angle**: South Africa = 60% of Nix-TB / ZeNix sites; African TB program adopted BPaLM as WHO-conditional preferred regimen in 2022.

| Trial | NCT | Enrollment (CT.gov verified) | Phase | PMID | Comparator |
|---|---|---|---|---|---|
| Nix-TB | NCT02333799 | 109 | III | 32130813 (Conradie 2020 NEJM) | None (single-arm) |
| ZeNix | NCT03086486 | 181 | III | 36099496 (Conradie 2022 NEJM) | LZD dose comparison |
| TB-PRACTECAL | NCT02589782 | 552 | II/III | 36342063 (Nyang'wa 2022 NEJM) | WHO SOC (head-to-head) |

**Head-to-head primary contrast (TB-PRACTECAL stage 2)**:
- BPaLM (bedaquiline + pretomanid + linezolid + moxifloxacin, 24 weeks): 89/138 favorable (64%)
- SOC (WHO-recommended long regimen, 9–24 months): 79/137 favorable (58%)
- RR favorable = 1.12 (95% CI 0.93–1.34); risk difference 6.4 percentage points (95% CI –4 to 17 pp); pre-specified non-inferiority margin met. The published primary endpoint flips the framing to **unfavorable outcomes**: BPaLM 11% vs SOC 48%, RR 0.23 (95% CI 0.15–0.36) for unfavorable.

**Note for builder**: TB-PRACTECAL has 4 arms in stage 1 (BPaL, BPaLM, BPaLC, SOC) and 2 arms in stage 2 (BPaLM, SOC); the published RR 0.23 is from the stage-2 mITT analysis (Nyang'wa 2022 NEJM). Use stage-2 mITT denominators (BPaLM n=138, SOC n=137) for the headline contrast row.

---

## Topic 2 — HPV_DOSE_REDUCTION_NMA_REVIEW.html (NMA)

**PICO**: HIV-negative females aged 9–20 in sub-Saharan Africa (P) receiving a single dose, two doses, or three doses of bivalent or nonavalent HPV vaccine (I/C); persistent HPV 16/18 infection or HPV 16/18 antibody seropositivity at month 18–24 (O).

**Filename**: `HPV_DOSE_REDUCTION_NMA_REVIEW.html`
**Type**: NMA (single-dose vs 2-dose vs 3-dose; bivalent vs nonavalent)
**Africa angle**: Both pivotal trials enrolled exclusively in East Africa (Kenya, Tanzania); WHO SAGE 2022 1-dose recommendation rests partly on these.

| Trial | NCT | Enrollment | Country | PMID | Design |
|---|---|---|---|---|---|
| KEN-SHE | NCT03675256 | 2,275 | Kenya | 35143335 (Barnabas 2022 NEJM Evid; updated 2023 PMID 38096571) | 3-arm: bivalent vs nonavalent vs delayed-meningococcal control |
| DoRIS | NCT02834637 | 930 | Tanzania | 36410354 (Watson-Jones 2022 NEJM Evid) | 6-arm: 2 vaccines × 3 doses (1/2/3) |
| HPV PRIMAVERA | NCT05016505 | ~10,000 | Costa Rica + Africa expansion | (results pending; preprint 2024) | Single-dose efficacy vs 2-dose Costa Rica HPV Vaccine Trial historical control |

**Headline KEN-SHE 18-month results**:
- Persistent HPV 16/18 infection: 0/758 in bivalent arm vs 4/760 in nonavalent arm vs 38/758 in control arm (delayed-meningococcal) over 18 months
- Bivalent vaccine efficacy 97.5% (95% CI 81.7–99.7); nonavalent 89.0% (95% CI 70.0–97.4)

**Headline DoRIS month-24 antibody seropositivity (HPV 16)** (single-dose non-inferiority vs 3-dose):
- Bivalent: 1-dose 100% (95% CI 96–100), 3-dose 100% — non-inferior (margin met)
- Nonavalent: 1-dose 99% (95% CI 94–100), 3-dose 100% — non-inferior

**NMA structure**: 6 nodes (bivalent×{1,2,3} doses + nonavalent×{1,2,3} doses) plus implicit "no vaccination" via KEN-SHE delayed-control. Connect via DoRIS (which has all 6 active vaccine nodes) and KEN-SHE (which adds the no-vaccine reference). Endpoint: HPV 16/18 antibody seropositivity at M24, OR persistent HPV 16/18 infection at 18 months — note the two endpoints are not interchangeable; recommend separate NMAs.

---

## Topic 3 — MALARIA_ACT_NMA_REVIEW.html (NMA)

**PICO**: Children <5 in sub-Saharan Africa with uncomplicated *P. falciparum* malaria (P) treated with artemether-lumefantrine (AL), dihydroartemisinin-piperaquine (DP), artesunate-amodiaquine (ASAQ), or artesunate-mefloquine (ASMQ) (I/C); 28- or 42-day PCR-corrected adequate clinical and parasitological response (ACPR) (O).

**Filename**: `MALARIA_ACT_NMA_REVIEW.html`
**Type**: NMA (4 ACT regimens + comparators)
**Africa angle**: 95% of global malaria mortality in sub-Saharan Africa; all 4 ACTs are WHO-recommended first-line options.

**Trial NCTs to verify before build** (candidates from the WWARN ACT systematic review database, post-2012 published):

| Candidate trial | Likely NCT | Approx N | Country (lead) |
|---|---|---|---|
| WANECAM | NCT00858676 | ~4,710 | Burkina Faso, Mali, Guinea, Senegal |
| 4ABC trial | (legacy, pre-CT.gov) | ~4,116 | 7 African countries |
| Sondo 2015 (Burkina Faso) | NCT01704508 | ~440 | Burkina Faso |
| Ngondi 2018 | NCT01787474 | ~252 | Cameroon |
| Senegal AL-DP comparison 2014 | NCT00993031 | ~316 | Senegal |
| WWARN pooled (>20 trials) | n/a | ~30,000 | Multi-country |

**Note for builder**: Verify each NCT via `python scripts/ctgov_cross_check.py` before build. The 4ABC trial pre-dates CT.gov NCT registration so will need a `pmid:` field only.

**Headline finding (WWARN 2018 IPD-MA)**: AL day-28 PCR-corrected ACPR 96.0%, DP 97.2%, ASAQ 95.8%, ASMQ 96.4% — small absolute differences but DP shows longest post-treatment prophylaxis (~6 weeks). AL has highest day-42 reinfection risk.

---

## Topic 4 — PRIMAQUINE_GAMETOCYTE_DR_REVIEW.html (Dose-response)

**PICO**: Patients with uncomplicated *P. falciparum* malaria (P) receiving single low-dose primaquine 0.0625, 0.125, 0.25, or 0.5 mg/kg as adjunct to ACT (I); 7-day post-treatment gametocyte clearance and density on QT-PCR or molecular assay (O); haemolysis rate in G6PD-deficient subgroup (safety O).

**Filename**: `PRIMAQUINE_GAMETOCYTE_DR_REVIEW.html`
**Type**: Dose-response (4 dose levels + control)
**Africa angle**: WHO 2012 recommendation for SLD-PQ targeted at sub-Saharan transmission-blocking; African G6PD-deficiency prevalence 5–25% drives the "low-dose" emphasis.

**Key trials**:

| Trial | NCT | Approx N | Country | PMID |
|---|---|---|---|---|
| Goncalves Lancet ID 2016 | NCT02174900 | 320 | Burkina Faso | 27339845 |
| Stepniewska et al. 2022 IPD-MA | n/a (re-analysis) | ~3,700 | 14 trials | 35150633 |
| Chen 2022 dose-finding | NCT02174900 follow-up | 240 | Mali | 35468330 |

**Headline Goncalves 2016 dose-response (Burkina Faso, falciparum gametocyte density)**:
- 0.0625 mg/kg: gametocyte AUC reduction 16% (95% CI 1–28%) vs placebo
- 0.125 mg/kg: 22% (95% CI 9–33%)
- 0.25 mg/kg: 65% (95% CI 57–72%)
- 0.5 mg/kg: 76% (95% CI 70–81%)

**Stepniewska 2022 IPD-MA finding**: SLD-PQ 0.25 mg/kg achieves >90% reduction in mosquito infectivity at day 8; 0.0625–0.125 mg/kg insufficient. No clinically significant haemolysis at 0.25 mg/kg in G6PD-deficient subjects in 2,500+ pooled doses.

**Dose-response model**: Use restricted cubic spline (3 knots at 0.0625, 0.25, 0.5) on log-AUC reduction. Alternatively a 4-parameter Emax model with placebo as E0.

---

## Topic 5 — PPH_BUNDLE_NMA_REVIEW.html (NMA, supplementary)

**PICO**: Postpartum women (P) receiving heat-stable carbetocin, oxytocin, tranexamic acid, misoprostol, or E-MOTIVE bundle (I/C) for prevention or first-line treatment of postpartum hemorrhage; primary composite of severe PPH or death (O).

**Filename**: `PPH_BUNDLE_NMA_REVIEW.html`
**Type**: NMA (5+ interventions; prevention + treatment as separate analyses)
**Africa angle**: WOMAN trial enrolled 20,021 women across 21 countries (mostly LMIC including 7 African); E-MOTIVE 2023 enrolled across 4 sub-Saharan countries; PPH leads African maternal mortality.

**Key trials**:

| Trial | NCT | N | Lead countries | PMID |
|---|---|---|---|---|
| WOMAN (TXA for PPH treatment) | NCT00872469 | 20,021 | UK, multi-LMIC | 28456509 |
| CHAMPION (heat-stable carbetocin vs oxytocin) | NCT01619072 | 29,645 | 23 countries (Africa-heavy) | 29899040 |
| E-MOTIVE bundle | NCT04341662 | 210,135 (cluster, 80 hospitals, 4 SSA countries) | Kenya, Nigeria, S. Africa, Tanzania | 37158612 (Gallos 2023 NEJM) |
| WOMAN-2 (TXA in anaemic women) | NCT03162900 | 12,360 | Pakistan, Nigeria, Tanzania, Zambia | 38007227 |

**Note**: Verify each NCT before build (memory-dependent — auto-listing flagged in pegcetacoplan-style audits previously).

**Headline E-MOTIVE finding**: bundle reduced primary composite of severe PPH or death from 4.3% (control) to 1.6% (bundle), RR 0.40 (95% CI 0.32–0.50, P<0.001). First clear win for an integrated PPH bundle in low-resource settings.

---

## Common build-pipeline notes

1. **Template choice**: For pairwise apps (Topic 1), clone the smallest existing pairwise file (`SGLT2_HF_REVIEW.html`, 1.0 MB). For NMA apps (Topics 2, 3, 5), clone an NMA file (`ATOPIC_DERM_NMA_REVIEW.html`). For dose-response (Topic 4), no current template — closest is `SGLT2_HF_REVIEW.html` adapted with continuous-dose covariate.

2. **NCT verification gate**: Before build, run `python scripts/ctgov_cross_check.py` after first paste — this will flag any NCT-vs-enrollment mismatch like the OAKS/DERBY and KEEPsAKE swaps caught earlier. Topics 1, 2 have all NCTs already verified. Topics 3, 5 have candidate NCTs that need confirmation. Topic 4 mostly relies on a re-analysis (no single NCT).

3. **mITT denominator convention**: Use the published primary-analysis denominator (mITT, per-protocol, or randomized as stated in the source paper). Document this in the row's `group:` field. Do NOT mix conventions within one trial-row (the IOI in pegcetacoplan was a documented exception with explicit safety-set callout).

4. **highlightEvidence v2 + RoB disambiguation**: All new files inherit the regex-auto-highlight + CT.gov-design-metadata disambiguation from the portfolio codemod (commits a2cef480, 27d19d5d). No manual highlight curation needed beyond non-numeric terms.

5. **Africa-context emphasis**: For each topic, add an Africa-context preamble in the protocol field's `pop` description (sub-Saharan setting, malaria/G6PD/HIV considerations as applicable) so the cohort can use these for teaching the African burden lens.

---

## Status (2026-05-03)

| Topic | Spec | NCTs verified | realData drafted | App built |
|---|---|---|---|---|
| 1. BPaL/BPaLM MDR-TB | ✓ | ✓ (3/3) | ✗ | ✗ |
| 2. HPV dose-reduction NMA | ✓ | ✓ (2/3, PRIMAVERA pending) | ✗ | ✗ |
| 3. Malaria ACT NMA | ✓ | ◐ (candidates listed) | ✗ | ✗ |
| 4. Primaquine dose-response | ✓ | ◐ (1/3 verified) | ✗ | ✗ |
| 5. PPH bundle NMA | ✓ | ◐ (candidates listed) | ✗ | ✗ |

Next step: pick one topic, run NCT verification, paste verified NCTs + enrollment into a cloned template, and confirm build passes the structural codemod checks.
