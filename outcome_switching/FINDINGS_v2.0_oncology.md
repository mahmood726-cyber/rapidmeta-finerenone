# Outcome-switching MA — v2.0 cross-therapeutic-area expansion: oncology

> 2026-04-30. Replicates the HF v0.3 methodology on oncology Phase 3 trials post-2015 with results posted, n≥500. Tests whether the HF-specific findings generalise.

## Headline finding

**Oncology drifts much more than HF on every metric, but the industry-vs-academic asymmetry on framework changes holds across both areas.**

| Metric | HF P3/P4 v0.3 | Oncology P3 v2.0 | Oncology / HF |
|---|---|---|---|
| n | 269 | 184 | — |
| Any drift | 147 (54.6%) | **170 (92.4%)** | **1.7×** |
| Timeframe change | 36 (13.4%) | **120 (65.2%)** | **4.9×** |
| Framework change | 5 (1.9%) | 6 (3.3%) | 1.7× |
| Title rewrite | 82 (30.5%) | 116 (63.0%) | 2.1× |
| Primary count change | 79 (29.4%) | 93 (50.5%) | 1.7× |
| Content-change candidate (auto-detector) | 43 (16.0%) | **56 (30.4%)** | 1.9× |

Oncology's 92.4% any-drift rate is essentially the ceiling — only 14 of 184 oncology trials had no detectable drift between v1 and current registration.

## Why oncology drifts more

Plausible mechanisms (to be tested in v3.0):

1. **Longer follow-up windows.** Oncology Phase 3 trials with overall-survival primary endpoints can run 5-10+ years. Each event-accrual interim updates the registry timeframe field, so timeframe drift accumulates by construction. HF P3/P4 trials typically run 1-3 years.
2. **More amendments.** Oncology trials commonly have multiple protocol amendments for biomarker stratification, dosing, expansion-cohort additions, or analysis-cutoff redefinition. Each amendment is a registry-edit opportunity.
3. **Complex composite primaries.** Hierarchical / time-dependent primaries common in oncology (PFS-then-OS, ORR-confirmed-by-imaging, etc.) are harder to summarise stably and get rewritten as the protocol matures.
4. **Different regulatory cycle.** FDA accelerated-approval pathways for oncology depend on surrogate endpoints (PFS, ORR) which often need post-hoc reframing for confirmatory analyses.

These are hypotheses, not findings. The 4.9× timeframe-change ratio is the most striking — it's almost certainly mechanism (1) plus (2) rather than worse sponsor behaviour.

## Sponsor-class asymmetry — same direction in both areas

| Pool | Industry framework-change rate | Academic framework-change rate |
|---|---|---|
| HF P3/P4 (v0.3) | 5/78 (6.4%) | 0/184 (0.0%) |
| **Oncology P3 (v2.0)** | **6/171 (3.5%)** | **0/13 (0.0%)** |

**All 6 oncology framework changes are industry-sponsored** — same pattern as HF's 5/5 industry. The framework-change phenomenon is **therapy-area-independent** but **sponsor-class-specific**. This is the strongest cross-area generalisation from this audit.

The "no academic framework changes" finding is structural: of 184 oncology trials in the pool, only 13 are academic (NETWORK + OTHER + NIH + OTHER_GOV combined). The rate of zero is therefore noisy but consistent across both areas.

## Industry drift rate generalises but is uniformly higher in oncology

| Pool | Industry any-drift rate |
|---|---|
| HF P3/P4 (v0.3) | 57/78 (73.1%) |
| **Oncology P3 (v2.0)** | **160/171 (93.6%)** |

Industry oncology trials drift 1.3× as often as industry HF trials. Mechanisms (1)-(4) above probably explain the gap.

## Combined cross-area drift typology

| Drift type | HF (n=269) | Oncology (n=184) | Combined (n=453) |
|---|---|---|---|
| Any drift | 54.6% | 92.4% | 70.0% |
| Timeframe change | 13.4% | 65.2% | 34.4% |
| Framework change | 1.9% | 3.3% | 2.4% |
| Content-change candidate | 16.0% | 30.4% | 21.9% |

Combined across both areas, **70.0% of pivotal Phase 3 trials drift** between v1 and current — a much higher number than the medRxiv 2025.11.06 24% baseline. The discrepancy is likely because the medRxiv baseline measures *outcome dropping* (a stricter event), while our methodology captures *outcome reformulation* including timeframe and title edits.

## Implications for the v1.0/v2.0 paper

1. **Industry framework-change pattern** (5/5 in HF, 6/6 in oncology — all industry, 0 academic) is the **headline finding** that generalises across two distinct therapy areas. This is a credible Methods Note hypothesis.
2. **Oncology timeframe drift (65%)** is mostly a consequence of long follow-up windows and amendment cycles — likely a separate mechanism from the registry-housekeeping pattern in HF. v3.0 should test the amendment-count hypothesis directly.
3. **Drift rates are therapy-area-dependent** for cosmetic axes (timeframe, title) but **sponsor-class-specific** for the framework axis. Two distinct dimensions of drift.
4. **Content-change candidate rate is ~2× in oncology** (30% vs 16%) — likely reflects more complex primary endpoints in oncology (hierarchical composites, time-dependent biomarkers) rather than worse practice. Manual eyeball annotation needed for confirmation.

## The 6 oncology framework-change trials — eyeball detail

All 6 are industry-sponsored. Eyeball reveals the patterns are different from HF's homogeneous "time-to-event → cumulative-incidence" housekeeping:

| NCT | Sponsor | n | v1 → current | Type |
|---|---|---|---|---|
| NCT03409614 | Regeneron | 789 | **PFS → OS** | Surrogate→final endpoint switch |
| NCT02578680 | Merck Sharp & Dohme | 616 | "Progression Free" → "Progression-Free" | **False positive** — only hyphenation difference triggered TTE→rate detector |
| NCT02394795 PARADIGM | Takeda | 823 | OS overall → OS in left-sided tumors | Population narrowing within primary |
| NCT03412773 | BeiGene | 684 | **OS → Safety Run-in TEAEs** | Efficacy→safety primary swap (DIAMOND-style content change) |
| NCT02420821 IMmotion151 | Roche | 915 | PFS time-to-event → "Percentage with Disease Progression" | TTE → cumulative-incidence (DAPA-HF-style housekeeping) |
| NCT03504423 | Cornerstone | 528 | **ORR → OS** | Rate→TTE reverse direction (surrogate→final) |

After removing the false positive, the **true framework-change rate is 5/184 (2.7%)** — slightly higher than HF's 1.9%. Still 5/5 industry.

The oncology pattern is more **substantively varied** than HF's: NCT03412773 (efficacy OS → safety TEAEs) is a content change as significant as DIAMOND; NCT03409614 and NCT03504423 are surrogate↔final endpoint swaps; NCT02394795 is a population narrowing. Only IMmotion151 fits the HF-style pure-housekeeping pattern.

**No sponsor concentration** in oncology framework changes — Regeneron, MSD, Takeda, BeiGene, Roche, Cornerstone (5 different sponsors). HF had Novartis ×2 + AstraZeneca ×2 concentration. The corporate-template hypothesis from HF doesn't hold for oncology — each oncology framework change looks like an independent decision.

## Recommended v3.0 work

- **Cross-area meta-finding**: replicate on nephrology and endocrinology pools to test whether the industry framework-change pattern is universal across cardiology / oncology / nephrology / endocrinology.
- **Mechanism test**: pull amendment counts from CT.gov (`statusModule.lastUpdatePostDateStruct`) and correlate against any-drift rate. If the correlation is strong, the timeframe-drift difference is mostly amendment-count-driven, not sponsor-behaviour-driven.
- **Manual annotation of 56 oncology content-change candidates** for confirmation rate (HF v1.1 detector precision was ~57% on top-7 sample; oncology may differ).
- **Headline-grade single-figure** for the v1.0 paper: industry-vs-academic framework-change rate stratified by therapy area — a 2x2 table that compresses the entire finding.

## Source artefacts

- v0.3 commit (HF): `c5db22a`
- v2.0 commit (oncology): TBD
- `outcome_switching/scrape_oncology.py` — 3-stage pipeline
- `outcome_switching/oncology_p3_nct_list.json` — 184 trials Stage 1
- `outcome_switching/oncology_p3_v1_history.json` — 184 trials v1 history
- `outcome_switching/oncology_p3_current.json` — 184 trials current registered
- `outcome_switching/compute_oncology_diff.py` — diff engine
- `outcome_switching/oncology_p3_v1_vs_current.json` — full diff output

## Open for v2.1

- Identify the 6 oncology framework-change trials by NCT and write per-trial case studies (DAPA-HF / DELIVER analogues for oncology)
- Manual eyeball confirmation of the 56 content-change candidates
- Add nephrology + endocrinology pools to test 3-area generalisation
- Compare sponsor concentration: HF was Novartis ×2 + AstraZeneca ×2 + CSL ×1. What's the oncology pattern?
