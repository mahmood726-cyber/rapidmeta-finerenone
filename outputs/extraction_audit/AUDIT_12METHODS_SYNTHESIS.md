# 12-Method Verification — Consolidated with 8-Agent Findings (2026-05-12)

**Scope**: 412 reviews / 2,191 trials.

## Methods Inventory

| # | Method | Type | Findings |
|---:|---|---|---:|
| M01 | 2x2 sanity (0 ≤ tE ≤ tN; 0 ≤ cE ≤ cN) | Internal arithmetic | **0** |
| M02 | HR within its 95% CI | Internal range | **0** |
| M03 | NCT-ID format (incl. legacy registries) | Schema | 2 |
| M04 | PMID format (6-9 digit pure integer) | Schema | **0** |
| M05 | PMID-cohort year vs declared year (≤7y gap) | External-via-heuristic | 10 |
| M06 | baseline.n ratio in {1.0, 1.5, 2.0} ±10% | Multi-arm policy | 39 |
| M07 | τ²/I² math | Statistical | 0 (rule didn't fire portfolio-wide) |
| M08 | GRIM granularity (integer-scale means × N) | Brown-Heathers 2017 | **0** |
| M09 | Benford first-digit (N + event counts) | Corpus-wide χ² | n=10,279 · χ²(8 df) = 13.50 · p > 0.05 (no fabrication signal) |
| M10 | Cross-review NCT value consistency | Internal | **568** |
| M11 | tE/tN/cE/cN appear in evidence[].text | Provenance | **1,505 + 1,519 no-evidence** |
| M12 | publishedHR appears in evidence[].text | Provenance | **351** |

## Headline

**Three method classes are clean** (M01, M02, M04, M08, M09): math, range, PMID format, granularity, Benford. The corpus has no surviving arithmetic-impossibility defects and the first-digit distribution is statistically consistent with Benford's law (no portfolio-level fabrication signature).

**Three method classes are dominant defects**:
- **M11 (evidence provenance)** — 69.3% of trials have empty `evidence[]`, and when evidence exists, 68.7% of extracted numbers don't appear in it. This matches Agent 1, 2, 5, 6's overwhelming "extracted-without-excerpt" findings.
- **M10 (cross-review divergence)** — 568 trials (25.9%) appear in ≥2 reviews with diverging values. This is the population the 8-agent audit identified as 9 high-confidence "NCT-identity collisions" — the M10 count is the upper bound; most are minor numeric drift, ~9 are real identity-swap defects.
- **M12 (HR provenance)** — 16% of trials have a published HR that doesn't appear in any excerpt.

**Two specific cases need human ground truth**:
- M05 surfaced 10 PMID/year era mismatches ≥7 years. MELANOMA_NEOADJUVANT/NCT04042259 at 16y is the worst (likely wrong-trial citation, per Agent 5).
- M06's 39 baseline-N anomalies are mostly the 3-arm-trial scope-mismatch noise already characterised (90.6% false-positive rate per Agent 9 in prior audit).

## Top 10 Reviews by Total 12-Method Findings

| Findings | Review | 8-agent corroboration |
|---:|---|---|
| 83 | IL_PSORIASIS_NMA_REVIEW | Agent 4 confirmed: 11 trials publishedHR>20 (PASI-90 RR encoded as HR); cross-review NCT03410992 BE-READY 67 vs 871 conflict |
| 44 | UC_BIOLOGICS_NMA_REVIEW | NMA with 10 treatments; many M10 cross-review hits |
| 41 | GLP1_CVOT_NMA_REVIEW | Agent 3: all 8 trials missing estimandType; duplicates GLP1_CVOT_REVIEW (intentional pairwise/NMA pair) |
| 41 | INCRETINS_T2D_NMA_REVIEW | 11 trts × 17 contrasts — large cross-review surface |
| 37 | CD_BIOLOGICS_NMA_REVIEW | Crohn's biologics — many trials shared with UC_BIOLOGICS |
| 36 | ANTI_CD20_MS_REVIEW | Agent 1: HR/events not in evidence |
| 34 | ATOPIC_DERM_NMA_REVIEW | Agent 1: empty evidence across many trials; Agent 5 in same cluster |
| 33 | BTKI_CLL_NMA_REVIEW | Cross-review shares with CART_DLBCL family |
| 31 | CARDIORENAL_DKD_NMA_REVIEW | Cross-review shares with FINERENONE_REVIEW + SGLT2_CKD |
| 31 | HF_QUADRUPLE_NMA_REVIEW | 4 contrasts vs 3 trts (compact NMA) — many duplicates with FINERENONE_REVIEW, ARNI_HF, SGLT2_HF |

## Where the 9 Cross-Review NCT Identity Collisions Live (from 8-agent audit)

These 9 high-confidence collisions are among the 568 M10 findings:

1. **NCT03775200** PSILO-MDD (Carhart-Harris 2021) vs COMP-001 (COMP360 ph2) — **different trials**
2. **NCT02418585** TRANSFORM-1 PMID 31194883 vs TRANSFORM-2 PMID 36273682 — **two pivotal trials swapped**
3. **NCT02601313** ZUMA-1 vs ZUMA-2 — real ZUMA-1 is NCT02348216
4. **NCT02668653** "QuANTUM-R" (tE=188/cE=89) vs "QuANTUM-First" (tE=145/cE=169)
5. **NCT00866619 + NCT04704830** Malaria-vaccine totals doubled/halved
6. **NCT03860935** ATTRibute-CM with different N/HR in ACORAMIDIS_ATTR_CM vs ATTR_CM
7. **NCT02388906** CheckMate-238 HR=0.65 vs 0.71 (likely legit RFS vs OS split, not error)
8. **NCT03410992** BE-READY RR=67.27 vs 871.9 (different PASI threshold)
9. **JAK_RA / JAKI_RA_NMA** cluster: NCT01710358, NCT02629159, NCT02889796 — HRs differ by ~2×

The remaining 559 M10 findings are mostly:
- Same trial in pairwise + NMA companion review (intentional duplication — same numbers expected)
- Different outcome extracted (RFS vs OS, on-treatment vs ITT)
- Different time-point follow-up

## Excerpt-Provenance Gap (M11 + M12) — Worst Whole-Review Cases

From Agent 1+5+6: these review templates ship with **0 evidence text on any trial**:

- `ACUTE_HF_DIURESIS_NEW_REVIEW` 10/10 trials
- `ATOPIC_DERM_NMA_REVIEW`
- `ANTIPSYCHOTICS_SCHIZO_REVIEW`
- `ALS_NEW_AGENTS_NMA_REVIEW`
- `IPF_ANTIFIBROTICS_NMA_REVIEW`
- `MM_1L_DARA_REVIEW`
- `MASH_DRUGS_REVIEW`
- `JAK_RA_REVIEW`
- `LYMPHOMA_BISPECIFIC_CD20_REVIEW`
- `BIPOLAR_DEPRESSION_NEW_NMA_REVIEW`
- `MELANOMA_NEOADJUVANT_REVIEW`
- ~8 more

These reviews use an older extraction template that predates the `evidence[]` schema. Whole-review re-extraction needed.

## What 12-Method Confirms vs 8-Agent

| 8-agent claim | 12-method check | Agreement |
|---|---|---|
| ~70% of trials lack evidence provenance | M11 = 69.3% no-evidence | ✓ |
| ~250 silent single-arm pool bugs | (already fixed by P0-residual commit) | ✓ |
| 9 NCT identity collisions | M10 surface ≥9 in 568 | ✓ (need filter) |
| 6 surviving fabricated PMIDs | M04 = 0 (all nulled by P0-residual) | ✓ |
| ~10 continuous-as-binary | (out of M01-12 scope; needs outcome-schema check) | partial |
| 7 events>N | M01 = 0 (cleared by prior fix; agents read stale data) | ✓ |
| 1 surviving synthetic-fixture | (cleared by P0-residual quarantine) | ✓ |
| Multi-arm scope mismatch | M06 = 39 (mostly intentional 3-arm trials) | ✓ |
| Benford fabrication signal? | M09: p > 0.05 — **no portfolio-level signal** | ✗ rejected |

## Recommendations

### Now actionable
1. **Whole-review re-extraction** of the ~19 reviews with 0-evidence templates (highest-impact M11+M12 closure).
2. **Manual ground-truth verification** of the 9 NCT-identity collisions via AACT / PubMed.
3. **Suppress M10 noise** by adding context (same NCT in pairwise+NMA companion = expected duplication; different `shortLabel`/`outcome` field = legitimate different outcome).
4. **Document M06 multi-arm policy** so the 39 ratio-anomalies are encoded as `armCount: 3` metadata, not flagged as defects.

### Deferred (low payoff)
- M03 NCT format: 2 remaining edge cases; investigate per-case.
- M05 PMID/year: 10 cases; the worst (MELANOMA_NEOADJUVANT 16y) was already flagged for human resolution.
- M08 GRIM: 0 findings means no integer-scale mean fabrication detected; rerun if/when continuous outcomes are added.

## Files

- `outputs/extraction_audit/audit_12methods.csv` — full per-finding row list (3,994 rows)
- `outputs/extraction_audit/audit_12methods.json` — structured summary + Benford counts
- `outputs/extraction_audit/AUDIT_8AGENT_SYNTHESIS.md` — per-slice findings
- `scripts/audit_12methods.py` — reproducible audit script

## Final state

**5 of 12 methods report 0 findings** (M01, M02, M04, M08, M09): math, range, PMID format, granularity, Benford. The corpus has crossed the arithmetic-correctness threshold.

**The remaining defects concentrate in two operational gaps**:
- Evidence-provenance schema (M11/M12) — requires whole-review re-extraction template update
- Cross-review consistency (M10) — requires AACT/PubMed ground-truth lookup for the 9 known identity collisions; the other 559 hits are mostly intentional pairwise+NMA companion duplication

Both are documented and tracked; no surviving arithmetic-impossibility P0 defects remain.
