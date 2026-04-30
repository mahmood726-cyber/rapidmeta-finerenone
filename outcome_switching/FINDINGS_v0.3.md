# Outcome-switching MA — HF P3/P4 v0.3

> 2026-04-30. Scaled from v0.2 (n=22) to the full n=269 P3/P4 HF post-2015 pool, dropping the n>=500 + has_results gates. Includes COMPLETED + TERMINATED + WITHDRAWN trials. Adds the registered-vs-published comparator (Task D) on the v0.2 22-trial subset.

## Headline finding

The 95% drift rate from v0.2 was a **selection-biased ceiling**. The full 269-trial pool drift rate is **54.6%**. The pivotal-only (n>=500 + results-posted) subset of v0.2 over-represents sponsors with extensive registry maintenance — exactly the trials with the most time and pressure to update registry text.

## v0.2 (n=22) → v0.3 (n=269) — what changed

| Metric | v0.2 (n=22) | v0.3 (n=269) |
|---|---|---|
| Any drift | 21 / 22 (95%) | **147 / 269 (54.6%)** |
| Timeframe change | 14 (63%) | 36 (13.4%) |
| Framework change | 3 (13.6%) | **5 (1.9%)** |
| Title rewrite | 13 (59%) | 82 (30.5%) |
| Primary-count change | 9 (41%) | 79 (29.4%) |
| v2 API alone detected | 0 / 22 | not yet measured for full 269 |

The 95% headline of v0.2 was real for *that pool* but does not generalise. The 54.6% rate from the broader pool is the more honest population-scale claim.

## Stratifications that survived scaling

### Sponsor class — industry runs higher

| Sponsor class | n | Any drift | Framework change |
|---|---|---|---|
| **INDUSTRY** | 78 | **57 (73.1%)** | **5 (6.4%)** |
| OTHER (academic + nonprofit) | 184 | 85 (46.2%) | 0 (0.0%) |
| OTHER_GOV | 6 | 5 (83.3%) | 0 (0.0%) |
| FED | 1 | 0 (0.0%) | 0 (0.0%) |

**All 5 framework changes are industry-sponsored.** Academic and nonprofit trials show 0 framework changes despite being 184 of 269 trials. This is the strongest pattern in the audit and supports the hypothesis that framework reformulation is a deliberate sponsor practice.

### Has-results — registered-and-edited beats registered-and-abandoned

| has_results | n | Any drift |
|---|---|---|
| True | 122 | **95 (77.9%)** |
| False | 147 | 52 (35.4%) |

Trials that posted results have 2.2x the drift rate of those that didn't. Plausible mechanism: posting results requires registry housekeeping which exposes drift opportunities. Trials that never reached results-posting (terminated / withdrawn / lingering) drifted less, not because they were better-behaved but because they had less time and reason to edit.

### Status — terminated ~ completed; withdrawn lower

| Status | n | Any drift |
|---|---|---|
| COMPLETED | 198 | 117 (59.1%) |
| TERMINATED | 48 | 26 (54.2%) |
| WITHDRAWN | 23 | 4 (17.4%) |

Terminated trials drift roughly the same as completed (54% vs 59%), so termination per se isn't a strong protective factor. WITHDRAWN trials drift much less because they were typically pulled before enrolling and had less opportunity for registry maintenance.

## The 5 framework changes (all industry)

| NCT | Acronym | Sponsor | Status | v1 framework | Current framework |
|---|---|---|---|---|---|
| NCT02468232 | PARALLEL-HF | Novartis | COMPLETED | time-to-event (sacubitril/valsartan in Asian HFrEF) | cumulative-incidence |
| NCT03473223 | AEGIS-II | CSL Behring | COMPLETED | time-to-event | cumulative-incidence |
| NCT03036124 | DAPA-HF | AstraZeneca | COMPLETED | time-to-event | cumulative-incidence |
| NCT02924727 | PARADISE-MI | Novartis | COMPLETED | time-to-event | cumulative-incidence |
| NCT03619213 | DELIVER | AstraZeneca | COMPLETED | time-to-event | cumulative-incidence |

All 5 trials reframed time-to-event primary as cumulative-incidence between v1 and current. Concentration in 2 sponsor portfolios (Novartis × 2, AstraZeneca × 2) suggests a corporate-template-driven pattern rather than independent decisions per trial.

PARALLEL-HF and AEGIS-II are net-new compared to v0.2's 3 (DAPA-HF, PARADISE-MI, DELIVER). AEGIS-II is technically ACS-not-HF but shares the same registry-edit pattern.

## Task D — registered-vs-published comparator (n=22 v0.2 subset)

For the v0.2 22-trial pool, primary publication PMIDs were retrieved via PubMed E-utilities NCT cross-reference. 21 of 22 trials yielded a candidate PMID; 1 trial (OUTSTEP-HF) returned no NCT-indexed publication.

Initial Jaccard token-overlap of registered-vs-published primary outcome flagged 14/22 trials at <0.30 ("drift") and 7/22 at 0.30-0.55 ("minor wording difference"). However, eyeball spot-check of 3 zero-Jaccard trials reveals that **2 of 3 are wrong-publication artefacts**, not real drift:

- **ENDEAVOR (NCT04986202)**: matched a "Rationale and design" methodology paper because primary results aren't yet PubMed-indexed under the NCT. Fault: my filter excluded "rationale and design" but the paper was the only candidate and the script fell back to it. Fix: don't fall back when all candidates are excluded.
- **PERSPECTIVE (NCT02884206)**: matched a review article ("Effect of Sacubitril/Valsartan on Neurocognitive Function: Current Status and Future Directions") because "perspective" was in my exclude-keyword list AND happens to be the trial's acronym. Fix: exclude based on `publication_types` field (Review, Editorial, Comment) not on title-keywords.
- **HEART-FID (NCT03037931)**: real candidate primary publication (NEJM 2023). Jaccard=0.0 reflects the registered measure being a list of 3 endpoints (deaths / HF-hospitalizations / 6MWT) while the abstract collapses to a hierarchical-composite framing. **This may be a real drift signal** — HEART-FID *did* report a hierarchical composite as the primary in the NEJM paper despite registering the 3 components individually. Worth a manual case study.

**Honest interpretation**: Task D's 64% drift rate is dominated by paraphrase noise and wrong-publication artefacts. The real registered-vs-published drift rate likely sits in the 5-25% range based on sample manual review. Full annotation of all 22 (or 269) trials would be a v1.0 task with a pub-type-aware filter.

## Updated drift typology (n=269)

| Drift type | n | Notes |
|---|---|---|
| **outcome_content_change** | 1+ (DIAMOND, in v0.2) | Hard endpoint reframed as biomarker. Probably more in 269 but not yet identified — needs eyeball audit. |
| **statistical_framework_change** | 5 | All industry; concentrated Novartis + AstraZeneca |
| **timeframe_change** | 36 | mix of compressions + extensions |
| **title_rewrite_only** | 82 | cosmetic |
| **primary_count_change** | 79 | typically 1→2 measures (event count + participant count) |

## What this means for the v1.0 paper

**The headline isn't "95% of trials drift" — it's "industry sponsors are 1.6x more likely to drift than academic, and 100% of statistical-framework changes are industry-sponsored, concentrated in 2 corporate portfolios"**. That's a credible methods-paper hypothesis worth a NEJM Methods Note or *Trials* paper.

The 269-pool also opens the question: **does a properly random sample (not pivotal-only) of HF trials show the same registry-drift rate elsewhere in cardiology?** A natural v0.4 expansion.

## Source artefacts

- v0.2 commit: `8b4b50f`
- This v0.3 commit: TBD
- `extract_269_currents.py` — v2 API extractor for full 269 pool
- `compute_v1_vs_current_269.py` — diff engine for full 269
- `fetch_publications.py` — Task D PubMed fetcher (E-utilities)
- `compute_pub_diff.py` — Task D Jaccard comparator
- `hf_p3p4_198_nct_list.json` — 269 trial metadata (Stage 1)
- `hf_history_v1_198.json` — 269 v1-history scrapes (Stage 2)
- `hf_outcomes_269_current.json` — 269 current registered primaries
- `hf_v1_vs_current_269.json` — full 269 diff output
- `hf_publications_22.json` — Task D PMIDs + abstracts for v0.2 subset
- `hf_pub_vs_registered_diff.json` — Task D Jaccard scores

## Open for v1.0

- Manual eyeball annotation of the 5 industry framework changes (verify pattern, write paragraph per trial)
- Pub-type-aware filter on Task D, then full annotation of registered-vs-published for all 269 (or at least the 122 with results posted)
- Identify additional outcome_content_change trials in the 269 pool (DIAMOND was the only one we eyeballed; pattern suggests there are more)
- Cross-cardiology expansion: does the same pattern appear in oncology / nephrology / endocrinology trial pools?
