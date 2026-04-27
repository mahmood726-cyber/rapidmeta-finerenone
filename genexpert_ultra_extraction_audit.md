# GeneXpert MTB/RIF Ultra DTA Extraction Audit

**Extracted:** 2026-04-27
**Pipeline:** CT.gov MCP (T9) + PubMed-abstract MCP (T10) → trial JSON for review (T11)
**Spec:** `docs/superpowers/specs/2026-04-27-rapidmeta-dta-engine-design.md`

## Headline numbers

| Tier | k | Notes |
|------|---|-------|
| **Primary** (CT.gov-results + pub-table-via-CT.gov) | **1** | Dorman 2018 only |
| **Sensitivity** (PubMed-abstract back-computed) | **4** | Andama 2021, Quan 2023, Carvalho 2024, Kabir 2021 |
| **Combined** | **5** | Just clears combined k ≥ 5 floor |

Per spec §5 acceptance gate:
- Primary k = 1 < 5 → ship with `coverage_warning: true` + headline banner
- Combined k = 5 ≥ 5 → ship (does not clear k ≥ 8 ceiling, so coverage banner applies regardless)
- Engine flags: `coverage_warning: true` (k < 10), `cc_applied: true` (Carvalho 2024 has FP=0)

## Trial-by-trial

| # | Study | Year | Country | Specimen | Ref std | TP | FP | FN | TN | Provenance | Notes |
|---|---|---|---|---|---|----|----|----|----|------------|-------|
| 1 | Dorman 2018 | 2018 | 8-country | Sputum | Culture | 407 | 39 | 55 | 938 | ctgov_pub_table | NCT03072576; back-computed from abstract Sens 88% Spec 96% on 462 culture-positive + 977 culture-negative |
| 2 | Andama 2021 | 2021 | Uganda | Sputum | Xpert+culture composite | 304 | 7 | 32 | 355 | pubmed_abstract_back_computed | DOI 10.1186/s12879-020-05727-8; n=698, 336 TB+, 362 TB-; Sens 90.5% Spec 98.1% |
| 3 | Quan 2023 | 2023 | China | Mixed (sputum + GA) | Composite (clinical+micro) | 149 | 2 | 182 | 58 | pubmed_abstract_raw | DOI 10.1097/INF.0000000000003866; pediatric; raw counts in abstract (149/331, 58/60); LOW SENSITIVITY (45%) |
| 4 | Carvalho 2024 | 2024 | Brazil | Sputum + GA | Clinical-radiological + Tx response | 13 | **0** | 13 | 15 | pubmed_abstract_raw | DOI 10.36416/1806-3756/e20240241; pediatric; 41 patients; **ZERO CELL → triggers continuity correction** |
| 5 | Kabir 2021 | 2021 | Bangladesh | **Stool** (not sputum) | Bact-confirmed on induced sputum | 17 | 50 | 12 | 368 | pubmed_abstract_back_computed | DOI 10.1093/cid/ciaa583; pediatric; alternative-specimen study; SPECIMEN CAVEAT |

## Heterogeneity flags (will surface in review HTML)

- **Population mix**: 2 adult (Dorman, Andama) + 3 pediatric (Quan, Carvalho, Kabir)
- **Specimen mix**: 4 sputum-or-mixed-respiratory + 1 stool (Kabir)
- **Reference-standard mix**: 1 pure culture (Dorman), 1 composite culture+Xpert (Andama), 3 clinical/composite (Quan, Carvalho, Kabir)

The review HTML's Subgroups tab will allow filtering by `population`, `specimen`, and `reference_standard` so users can isolate the most homogeneous subset.

## Excluded studies and reasons

| Reason | Count | Examples |
|--------|-------|----------|
| Cochrane / meta-analysis (not primary research) | 4 | CD012768, CD014841, CD015543, CD012768 |
| Different test (not Xpert Ultra) | 2 | TB-EASY (10.1183/13993003.01493-2024), Xpert HR (10.1093/cid/ciaf445) |
| Methodology paper / no results | 1 | RaPaed-TB (10.1097/INF.0000000000003853) |
| Cannot back-compute (Sens% given but no N+ breakdown) | 2 | Yenew 2024 (10.1183/23120541.00710-2023), Slail 2023 (10.1007/s44197-023-00150-z) |
| Population subgroup not target (e.g. trace-result interpretation only) | 1 | Sung 2024 (10.1093/cid/ciad595) |

## CT.gov-pubmed linkage

Dorman 2018 is the published report of NCT03072576 (the FIND multicentre Xpert Ultra DTA study). The other 4 PubMed papers do not have an obvious CT.gov registration linkage in their abstracts. This is normal for observational DTA studies, which historically register in PROSPERO or aren't pre-registered at all.

## Negation-context guard (per `lessons.md`)

For each back-computed row, I scanned ±30 chars around each Sens%/Spec%/N match for negation tokens (`not`, `non`, `never`, `excluding`). All 5 extractions are clean — no negation context detected.

## Why no full-text extraction

User instruction (2026-04-27): "Take pubmed data as well but only abstracts and not full papers." All initial retrievals in this pipeline come from the PubMed abstract field only — no full-text retrieval. Reviewers consult source publications independently when verifying extracted values.

Trade-off: published full texts of these studies typically include trial-level 2×2 tables in the supplement that would give much tighter back-computed counts (and per-subgroup data the abstracts omit). For an MVP this is acceptable; a v1.1 build could swap to full-text extraction with explicit consent.

## Engine-side handling

The 5 trials will be passed to `RapidMetaDTA.fit(trials)` where:
- `applyContinuityCorrection` will fire (Carvalho FP=0) → 0.5 added to all 4 cells of all 5 studies
- `reitsmaREML` (k=5) — runs full Nelder-Mead optimizer; if convergence fails on this small/heterogeneous dataset it will fall back to `feBivariate` and set `fallback: 'fe_bivariate'`
- `coverage_warning: true` (k=5 < 10)
- Spearman threshold-effect detection runs; with this k=5 mixed-design pool, expect `threshold_effect: false` (the studies don't form a clean threshold-monotone pattern)

The review HTML will surface ALL of these flags as colored badges in the Summary tab (per spec §4 / T13).
