# 8-Agent Data Audit — Consolidated Findings (2026-05-12)

**Scope**: 411 reviews / 2,210 trials. 52 reviews × 7 agents + 48 × 1 agent.

## Critical bugs surviving prior fixes

### 1. Empty `evidence[]` blocks — fabrication-risk pattern (user-flagged)

The "data not in excerpts" pattern is **portfolio-wide**:

| Slice (52 reviews) | Trials with extracted values but empty/missing evidence |
|---|---|
| Agent 1 | 295 / 356 (83%) |
| Agent 2 | 311 / 318 (98%) |
| Agent 5 | 190 trials in 19 reviews use a no-evidence template |
| Agent 6 | 277 / 277 trials (100%) |

**Worst whole-review cases**: `ACUTE_HF_DIURESIS_NEW_REVIEW` (10/10), `ATOPIC_DERM_NMA_REVIEW`, `BIPOLAR_DEPRESSION_NEW_NMA`, `ANTIPSYCHOTICS_SCHIZO`, `ALS_NEW_AGENTS_NMA`, `IPF_ANTIFIBROTICS_NMA`, `MM_1L_DARA`, `MASH_DRUGS`, `JAK_RA`, `LYMPHOMA_BISPECIFIC_CD20`.

### 2. Cross-review NCT-identity collisions (real bugs)

| NCT | Reviews | Conflict |
|---|---|---|
| **NCT03775200** | DEPRESSION_NEW_RAPID vs DEPRESSION_PSYCHEDELIC_NMA | Labelled "PSILO-MDD" (Carhart-Harris 2021) in one, "COMP-001" (COMP360 ph2) in the other — **two different trials** |
| **NCT02418585** | DEPRESSION_NEW_RAPID vs ESKETAMINE_TRD | "TRANSFORM-1" PMID 31194883 vs "TRANSFORM-2" PMID 36273682 — pivotal swap |
| **NCT02601313** | CAR_T_LBCL_BROAD vs CART_B_CELL_LYMPHOMA | "ZUMA-1" vs "ZUMA-2" — real ZUMA-1 is NCT02348216; both files mis-bind |
| **NCT00866619, NCT04704830** | MALARIA_VACCINE vs MALARIA_VACCINES | Totals doubled/halved |
| **NCT01710358, NCT02629159, NCT02889796** | JAK_RA vs JAKI_RA_NMA | HRs differ by ~2× across 3 overlapping trials |
| **NCT03860935** | ACORAMIDIS_ATTR_CM vs ATTR_CM | ATTRibute-CM with different N/HR |
| **NCT02388906** | ADJUVANT_IO_MELANOMA vs ADJUVANT_IO_PAN_TUMOR | CheckMate-238 HR=0.65 vs 0.71 (same N — likely RFS vs OS split) |
| **NCT03410992** | BIMEKIZUMAB_PSORIASIS vs IL_PSORIASIS_NMA | BE-READY RR=67.27 vs 871.9 (different PASI threshold/comparator) |
| **NCT02668653** | AML_TARGETED vs AML_VEN_FLT3 | "QuANTUM-R" vs "QuANTUM-First" — name swap with different values |

### 3. P0 events > N — still present (survived prior fix)

7 P0 cases in agent 4's slice alone:
- `GnRH_ANTAGONISTS_GYN_REVIEW / NCT01931670`: tE=256, tN=248 (Elagolix; 256 = total events across 2 dose arms)
- `HoFH_LIPID_NEW_NMA_REVIEW / NCT03399786`: tE=44, tN=43
- `HoFH_LIPID_NEW_NMA / NCT00730821`: tE=24, tN=23
- `HEAD_NECK_IO_BROAD_REVIEW / NCT02551159`: tE=274, tN=240
- `HEMOPHILIA_FACTOR_PROPHYLAXIS / NCT02622321`: cE=21, cN=18

### 4. Single-arm-as-2-arm confusion (highest-impact P0 stat bug)

40-50 trials per slice, ~250+ portfolio-wide. cN=0 with no `singleArm:true` → silently pooled as 2-arm with zero-event control:

- `FGFR_INHIBITORS_SOLID_REVIEW`: 6/7 trials single-arm phase-2 baskets (pemigatinib, infigratinib)
- `NSCLC_TARGETED_RARE_DRIVER_REVIEW`: 9/12 single-arm (CodeBreaK-100, KRYSTAL-1, GEOMETRY, VISION, LIBRETTO-001, ARROW, CHRYSALIS, TRIDENT-1, NAVIGATE-NTRK)
- `LYMPHOMA_BISPECIFIC_CD20`: 7/10 single-arm (EPCORE-NHL-1, glofitamab, etc.)
- `MM_BISPECIFIC_TRISPECIFIC`: 8/9 (MajesTEC-1, EPCORE-MM-1, etc.)
- `MELANOMA_NEOADJUVANT`: 7/10
- `INTRAVASCULAR_LITHOTRIPSY_NMA`: 4/9 (DISRUPT-CAD-1, DISRUPT-CAD-3)
- `BISPECIFIC_LYMPHOMA_NMA`: 5/9 (GO29781, NP30179, EPCORE, ELM-2, ALPHA-2)
- `CAR_T_LBCL_BROAD_NMA`: ZUMA-1, JULIET, TRANSCEND
- `DUCHENNE_GENE_THERAPY`: SRP-9001-101, VILTOLARSEN-101, ETEPLIRSEN-201
- `ANTI_PDL1_BLADDER`: KEYNOTE-052 (cisplatin-ineligible cohort)
- `AML_TARGETED / NCT04065399`: AUGMENT-101

### 5. Continuous-outcome mis-extracted as zero-event binary

Real bug — primary endpoint is continuous (BCVA letters, VMS/day, MADRS, CDR-SB) but extracted as `tE=0, cE=0`:

- `FARICIMAB_NAMD_REVIEW`: TENAYA + LUCERNE
- `FEZOLINETANT_VMS_REVIEW`: SKYLIGHT-1 + SKYLIGHT-2
- `ESKETAMINE_TRD_REVIEW`: TRANSFORM-1 + TRANSFORM-2
- `ELACESTRANT_BC_REVIEW`, `EBOLA_VACCINE_REVIEW`

### 6. Surviving fabricated PMIDs (`37937770[a-z]` family)

After the prior batch-cleanup, agent 4 + agent 3 still found ~6 instances:

- `HBV_NEW_AGENTS_NMA` (x/y/z suffixes)
- `HEP_D_BULEVIRTIDE_NMA` (d/e)
- `HoFH_LIPID_NEW_NMA` (e)
- `HCC_LOCAL_THERAPY` (w)
- `HOT_FLASH_NK3R_BROAD_NMA` (raw 37937770)
- `ESD_VS_EMR_EARLY_GI_NMA / NCT04253158` (raw 37937770)

### 7. Surviving synthetic-fixture trial

`ICH_MIS_HEMATOMA_NMA_REVIEW / NCT05001984` matches Tier-A 4-of-4 fingerprint (year=2024, no PMID, baseline.n=2×tN). Passed prior quarantine.

### 8. Duplicate-NCT-within-review (`b` suffix)

Same trial entered twice — once with NCT and once with NCT+b — double-counted by pooler:

- `OVARIAN_PARP_REVIEW`: NCT01874353/b, NCT03522246/b
- `NSCLC_PD1_1L_REVIEW`: NCT02366143/b
- `PD1_RCC_1L_REVIEW`: NCT04338269/b

### 9. PMID/year era mismatches

3 worst cases:
- `MELANOMA_NEOADJUVANT / NCT04042259`: PMID 18567918 (2008) vs year=2024 — **16-year gap, wrong-trial citation**
- `LIPID_HUB / NCT01841944`: PMID 24928284 (2014) vs year=2021
- `ITP_NEW_THERAPY_NMA / NCT00373932`: PMID 18242413 (2008) vs year=2017

Plus ~25 minor (3-7 year gaps) across the corpus.

### 10. Template-default `year: 2017` leak

PMIDs from 2011-2013 paired with year=2017 in agent 6's slice — extractor default-fill leaking past the year field. ≥5 trials affected.

## Defect class counts (consolidated)

| Class | Estimated portfolio-wide | Severity |
|---|---:|---|
| Empty evidence excerpts | **~1,500 trials** (~70%) | P1 (fabrication risk) |
| Single-arm not flagged | **~250 trials** | P0 (silent stat bug) |
| Empty evidence + full review | 19 review-level template gaps | P1 |
| Events > N (post-fix surviving) | ~7-15 cases | P0 |
| Cross-review NCT identity swaps | 9 confirmed pairs | P0 |
| Continuous-as-binary | ~10-15 trials | P0 (numbers meaningless) |
| Duplicate NCT (b suffix) | ~6 within-review | P0 (double-count) |
| Surviving fabricated PMIDs | ~6 | P0 |
| Synthetic fixtures (post-quarantine residue) | ~1 | P0 |
| PMID/year gap ≥7y | ~28 portfolio-wide | P1 |
| T01 invalid NCT format | 66 (mostly recoverable) | P2 (validator regex) |
| T10 baseline.n mismatch | 139 (mostly 3-arm scope) | P2 (validator policy) |
| R06 pool divergence | 79 (mostly scale-mix) | P2 (detector bug) |

## Recommended actions (priority order)

### P0 — must fix before any release
1. **Add `singleArm: true` to ~250 trials** with cN=0 that are real single-arm cohorts. Cross-references vendor/single-arm-proportion.js logic.
2. **Resolve 9 cross-review NCT-identity collisions** by AACT-verifying each NCT and overwriting both reviews.
3. **Fix 7+ events>N P0 cases** — re-extract from primary sources.
4. **Re-extract continuous-as-binary reviews** (FARICIMAB_NAMD, FEZOLINETANT_VMS, ESKETAMINE_TRD, ELACESTRANT_BC, EBOLA_VACCINE).
5. **Quarantine ICH_MIS_HEMATOMA NCT05001984** (4-of-4 synthetic, missed prior sweep).
6. **De-duplicate within-review NCT/NCTb pairs** in OVARIAN_PARP, NSCLC_PD1_1L, PD1_RCC_1L.
7. **Null the 6 surviving 37937770 PMIDs**.
8. **Fix MELANOMA_NEOADJUVANT/NCT04042259** wrong-trial PMID (16-year gap).

### P1 — schema improvements
9. **Mandate `evidence[]` schema on every trial** + back-fill the 19 templated reviews lacking it.
10. **Sentinel rules to add**:
    - `P0-cross-review-effect-mismatch`: same NCT in ≥2 reviews → require value agreement within 5%.
    - `P0-singlearm-pooled-as-rct`: `cN=0` without `singleArm:true` → block.
    - `P1-pmid-year-era-mismatch`: PMID-issue-year vs claimed year ≥5y → WARN; ≥10y → BLOCK.
    - `P1-evidence-required`: trial with `publishedHR` but empty `evidence[]` → WARN.
11. **Reframe FGFR_INHIBITORS_SOLID + NSCLC_TARGETED_RARE_DRIVER + DUCHENNE_GENE_THERAPY** as single-arm response-rate syntheses (not RCT MAs).

### P2 — detector hygiene
12. Suppress T10 false positives for 3-arm trials (90% of T10 hits).
13. Whitelist `LEGACY-*` / `ISRCTN*` / `NCT…b` / `NCT…_TOKEN` in T01 regex.
14. Fix R06 detector scale-mix bug (compares log-OR pool to natural-scale publishedHR).

## Files
- `agent_partitions/agent_{1..8}.txt` — per-agent review lists
- `findings.csv` — deterministic-flag list (post-batch fix)
- `SYNTHESIS_REPORT.md` — prior 9-agent audit (pre-fix baseline)
- `AUDIT_8AGENT_SYNTHESIS.md` — this report

## Bottom line

**The corpus-wide quarantine + per-cell Haldane + PMID strip in commits 42f88e42→2e6d5784 closed the largest defect classes** (563 synthetic trials, 71 letter-suffix PMIDs, 103 events>N). The 8-agent audit confirms ~5% residual defects in well-defined classes:

- **~250 silent single-arm pooling bugs** — highest-impact remaining work
- **9 cross-review NCT-identity swaps** — small count but high integrity damage
- **~70% trial-level evidence gaps** — schema-debt blocking provenance audits
- **~10 continuous-as-binary mis-extractions** — easy to fix once identified

The next defensible release candidate needs items 1-8 above closed.
