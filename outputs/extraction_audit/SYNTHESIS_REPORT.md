# RapidMeta Data Extraction Audit — Synthesis Report

**Date**: 2026-05-10
**Method**: 9-agent parallel audit on 414 of 421 reviews (98.3%) where `realData` could be cleanly extracted
**Total findings**: 603 (after refining false-positive thresholds; was 897)

## Headline findings

The audit uncovered three load-bearing P0 data-integrity issues:

### 1. **LLM-fabricated trials in 20.3% of the corpus**

563 of 2,769 trials (20.3%) match a synthetic-fixture fingerprint:
- 189 with **full 4-of-4 fingerprint**: NCT in `NCT05000xxx`/`NCT06xxxxxxx` block + empty PMID + year ≥ 2024 + `baseline.n == 2 × tN`
- 374 with **3-of-4 fingerprint**: real-looking NCT but other criteria match

**Spot-check of 8 "real-looking-NCT" trials**: 0 of 8 are actually real.
- 2 NCTs **don't exist** in AACT (NCT04567666, NCT04250117 — fabricated)
- 4 NCTs are **stolen from unrelated trials** in completely different specialties (e.g. NCT04138472 = a 30-pt anesthesia study, extracted as "ABROGATE" 188-pt vasculitis trial)
- 2 NCTs are real and topically related but stripped to fictional shells with halved arm counts

**75+ reviews implicated** (vs. the 9 reviews Agent 1 originally identified). This is a session-wide LLM-extraction template-fill defect, not a localised cluster.

### 2. **Fabricated PMID family**

71 trials cite PMIDs in the `37937770[a-z]` and `37937775[a-z]` families. **PMID 37937770 alone is cited 40 times across unrelated topics** (ADHD, HBV, RSV, mpox, hot flashes…). The actual PubMed paper is on **organoselenium chemistry**.

This matches the existing `feedback_review_build_audit_lessons.md` family `37935201/37937770/37935200` — same numeric prefix, same letter-suffix disambiguation, same hallucination signature.

### 3. **103 P0 "events > N" defects**

Physically impossible event counts (e.g. tE=110 / tN=100). Agent 1 grouped into 3 patterns:
- **68 cases**: rate ratios stuffed into binary fields (e.g. IMPACT trial, tE=4420 = AECOPD episode count, not patients with ≥1 event)
- **30 cases**: continuous mean-difference values stuffed into integer event slots (publishedHR field overloaded for MD outcomes)
- **28 cases**: synthetic-fixture rows with un-reconciled arm halving

## Findings that turned out to be mostly false positives

The audit's deterministic rules generated noise. After agent triage:

| Rule | Raw count | Real bugs after triage | False-positive cause |
|---|---:|---:|---|
| T01 invalid NCT format | 70 | **0 real bugs** | All recoverable: 30 cohort suffixes (`b`, `c`, RECOVERY arms), 22 legacy non-NCT registry IDs (`LEGACY-ISRCTN-...`), 9 wrong-prefix (ISRCTN/UMIN/ACTRN), 9 underscore tags (`NCT01206062_CKD` SPRINT subgroup) |
| T05/T06/T07 HR-CI defects | 124 | **0 strict HR-outside-CI** | All field-overload symptoms; `publishedHR` triple is overloaded across 5 scales (HR/OR/RR/MD/SMD). 39 are valid mean-differences with negative signs; 25 are sparse-event RR with degenerate CI; 16 have missing `estimandType` tag |
| R06 pool divergence | 88 | **0 real bugs** | All scale-mismatch (mixed estimands within review), single-arm contamination, or weighted-vs-unweighted noise |
| T10 baseline.n mismatch | 139 | **13 real bugs** | 90.6% are scope mismatches: 114 are 3-arm trials (baseline = full N, tN/cN = pooled pair), 12 are 2:1 randomization, 4 are PP-vs-ITT exclusions |

## Cross-review consistency check (side-finding from Agent 4)

Same NCT, two different effect values across reviews:

- **NCT03410992 BE-READY (bimekizumab)**: `publishedHR = 67.27` in `BIMEKIZUMAB_PSORIASIS_REVIEW` but `871.9` in `IL_PSORIASIS_NMA_REVIEW`. Same trial, different RR encoding. Real defect — likely different comparator arm or PASI threshold being silently encoded as the same field.

## Internal vs external consistency comparison (Agent 7)

External cross-check on 30 sample reviews (out of 411). The check compared each review's stated "Published HR" claim (from inline `PUBLISHED_META_BENCHMARKS` JS array) to a recomputed random-effects log-OR pool from the per-trial 2x2 data:

| Disposition | n | Notes |
|---|---:|---|
| **Converging** (\|Δlog\| ≤ 0.10) | 5 | ACS_ANTIPLATELET, ADJUVANT_IO_MELANOMA, ARNI_HF, ARPI_mHSPC, BELIMUMAB_SLE — all converge with claimed published HR |
| **Methodological divergence** (HR vs OR scale; FE vs RE; k=1 single-trial mis-tagged) | 9 | Real reviews where claim and re-pool answer slightly different questions |
| **Topic-mismatched-claim copy-paste** | 1 | ARPI_NMCRPC carries the **mHSPC** ARPI benchmark instead of nmCRPC |
| **Inline-placeholder bleed** (SGLT2i HF benchmark templated into unrelated reviews) | 15 | Half the sample shows the Vaduganathan 2022 SGLT2i HF benchmark (HR 0.77 [0.72-0.82], k=5) as the "published" claim regardless of topic |

The **15-of-30 placeholder bleed** is a portfolio-wide finding — many other reviews likely carry the same default benchmark scaffold without topic-specific replacement. A simple grep `grep -l "Vaduganathan 5-trial pooled analysis" *.html` would size the full impact.

## Top 8 worst reviews — deep-audit verdicts

| Review | Trials | Real-anchor | Fake/corrupt | events>N | Verdict |
|---|---:|---:|---:|---:|---|
| MPOX_VACCINE_NMA | 10 | 3 | 7 | **10/10** | **QUARANTINE** |
| MR_FUS_TREMOR | 10 | 2 | 8 | 4 | **QUARANTINE** |
| PFA_AF_PULSED_FIELD | 10 | 1 | 9 | 7 | FIX |
| INTRAVASCULAR_LITHOTRIPSY_NMA | 10 | 4 | 6 | 5 | FIX |
| PEDIATRIC_PSORIASIS_BIOLOGIC | 10 | 4 | 6 | 7 | FIX |
| MASTOCYTOSIS_NEW_NMA | 10 | 3 | 7 | 7 | FIX |
| T1D_CLOSED_LOOP_NMA | 10 | 7 | 3 | 6 | FIX (field-misuse) |
| NEUROENDOCRINE_PITUITARY_NMA | 10 | 7 | 3 | 3 | FIX |
| **80 trials total** | | **31 (39%)** | **49 (61%)** | **49 (61%)** | |

## Recommended priority actions

### P0 (block any release)

1. **Quarantine 189-trial Tier-A synthetic block** — move every trial matching the 4-of-4 fingerprint to `outputs/extraction_audit/quarantine/` and mark the originating reviews as `synthetic_contamination_pct` in metadata.
2. **Quarantine 374-trial Tier-B suspicious block** — same treatment; spot-check confirmed 0/8 are real.
3. **Strip all PMIDs in the `37937770[a-z]`/`37937775[a-z]` families** — null the `pmid` field; route to a re-extraction queue keyed by `(review, NCT, trial.name, year)`.
4. **Fix all 49 events-over-N rows** in the top 8 worst reviews — re-extract from primary sources or quarantine.

### P1 (close defects without blocking)

5. **Migrate to typed effect-scale schema**:
   ```json
   { "effectScale": "HR"|"OR"|"RR"|"MD"|"SMD",
     "effect": <signed_float>, "ci_lower": .., "ci_upper": .. }
   ```
   Deprecate `publishedHR`/`hrLCI`/`hrUCI` triple. Filters T05/T06/T07 from 124 → ~8.

6. **Tighten audit rules** to suppress false positives:
   - T01 regex: `^(NCT\d{8}([a-zA-Z]|_[A-Z0-9]+)?|LEGACY-[A-Z0-9-]+|(ISRCTN|UMIN|ACTRN)\d+)$` (clears 65/70)
   - T10 (baseline.n): suppress when ratio ∈ {1.50±0.10, 2.00±0.10} or arms 2:1 imbalanced (cuts 139 → ~13)
   - R06 (pool divergence): require all-binary estimand + `|Δlog| ≥ 1.0` (cuts 88 → ~2)

7. **Resolve 15+ placeholder-benchmark bleed reviews** — replace inline `PUBLISHED_META_BENCHMARKS` SGLT2i scaffold with topic-specific entries.

8. **Resolve cross-review inconsistency** for NCT03410992 BE-READY (bimekizumab psoriasis).

### P2 (Sentinel rule additions for future prevention)

9. **`P0-llm-synthetic-trial-fixture`**: block any review with ≥3-of-4 fingerprint trials. Start at WARN.
10. **`P1-pmid-placeholder-cluster`**: extend existing PMID blocklist (`37935201/37937770/37935200`) to detect any base-PMID reused across ≥2 unrelated review topics.
11. **`P1-effect-scale-required`**: block when `publishedHR` is set but `estimandType` (or `effectScale`) is missing.
12. **`P1-cross-review-effect-mismatch`**: when same NCT appears in ≥2 reviews, assert `(effectScale, effect)` agree within 5%.

## Coverage summary

- **414 / 421** reviews extractable (98.3%); 7 DTA-style reviews use a different data shape — handled separately
- **2,769 trials** total in extracted corpus
- **2,206 trials** with no synthetic fingerprint flag (potential clean tier)
- **563 trials** with at least 3-of-4 synthetic fingerprint (quarantine candidates)

## Key artifacts

- `outputs/extraction_audit/data/` — 414 per-review JSON files
- `outputs/extraction_audit/findings.csv` — 603-row deterministic-flag list
- `outputs/extraction_audit/findings.json` — same, structured
- `outputs/extraction_audit/summary.json` — per-review severity counts
- `outputs/extraction_audit/agent_inputs/*.csv` — per-domain CSV slices (input to each agent)
- `outputs/synthetic_fixture_sweep.json` — Agent 6 corpus-wide sweep output
- `outputs/cross_check_external_report.md` — Agent 7 published-meta comparison

## Bottom line

**The corpus contains substantial LLM-fabricated content sitting alongside genuine RCT extractions.** Estimated **20% of trials are synthetic, 6% have fabricated citations, and ~5% have impossible event counts**. The clean tier (~75–80% of trials) appears scientifically credible; the contamination is concentrated in a session-wide template-fill defect rather than spread evenly.

Internal consistency checks (the user-validated highest-value method per `feedback_meta_analysis_error_methods_synthesis.md`) caught all of this without needing external truth — the synthetic fingerprint is detectable purely from internal field-shape regularities. External comparison (Agent 7) added topic-relevance verification but was bottlenecked by the placeholder-benchmark bleed in the comparison source itself.

The path forward is: quarantine the synthetic block, deprecate the overloaded `publishedHR` triple in favour of a typed schema, and add the 4 Sentinel rules above so future LLM template-fill incidents are caught at push-time.
