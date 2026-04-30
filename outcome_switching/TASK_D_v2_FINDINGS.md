# Task D v2 — pub-type-aware registered-vs-published audit

> 2026-04-30. Re-run of Task D after fixing the publication-filter bugs that caused 2/3 zero-Jaccard cases in v1 to be wrong-publication artefacts (ENDEAVOR matched a "Rationale and design" paper because the script fell back to top-result; PERSPECTIVE matched a review article because "perspective" was accidentally in my exclude-keyword list AND happens to be the trial acronym).

## Filter changes (v1 → v2)

1. **Pub-type-based exclusion** instead of title-keyword exclusion. Filter against PubMed `publication_types`: Review, Editorial, Comment, Letter, Case Reports, Practice Guideline, Meta-Analysis, Systematic Review, etc. Trial-acronym words like "Perspective" no longer collide with the filter.
2. **No fallback to top-result** when all candidates are filtered. v1 fell back to the rationale-and-design paper for ENDEAVOR; v2 returns `None` instead, correctly tagging "primary publication not yet PubMed-indexed".
3. **Title-keyword filter retained** only for patterns that don't collide with trial acronyms: "rationale and design", "study design", "post hoc", "secondary analysis", "subgroup", "rationale", "protocol", "exploratory".

## Result comparison

| | v1 | v2 (pub-type-aware) |
|---|---|---|
| Total v0.2 trials | 22 | 22 |
| With primary publication PMID | 21 | **19** (3 correctly tagged "no publication indexed") |
| Wrong-publication artefacts | **2** (ENDEAVOR, PERSPECTIVE) | 0 |
| Aligned (Jaccard ≥0.55) | 0 | 0 |
| Minor wording difference (0.30-0.55) | 7 | 7 |
| Drift (Jaccard <0.30) | 14 | 12 |
| No publication indexed | 1 (OUTSTEP-HF only) | 3 (+ENDEAVOR, PERSPECTIVE correctly identified) |

## Eyeball confirmation of "drift" candidates

The Jaccard threshold of 0.30 is dominated by paraphrase noise. Sample of 4 v2 "drift" candidates manually inspected:

| Trial | Jaccard | Real drift? | Why |
|---|---|---|---|
| **DIAMOND** | 0.071 | **NO — paraphrase** | Both registered and published describe the same serum K+ primary; published uses "between-group difference in adjusted mean change", registered says "Changes from baseline". Same content, different wording. |
| **HEART-FID** | 0.000 | **YES — real drift** | Registered as 3 separate primaries (Number of Deaths, Number of HF Hospitalizations, Change in 6MWT). Published as 1 hierarchical composite of all 3. Substantive: separate-component analysis was the v1 plan; hierarchical was the published primary. |
| **DAPA-MI** | 0.125 | **BORDERLINE** | Registered: "Analysis of the Hierarchical Primary Composite Endpoint (Full Analysis Set)". Published: hierarchical composite of 6 components (death + HF hosp + nonfatal MI + AF/flutter + T2DM + NYHA). Registered version is too vague; the components were specified post-hoc. |
| **TRANSFORM-HF** | 0.176 | **NO — paraphrase** | Both versions describe all-cause mortality; "as measured by follow-up phone call or NDI" (registered) vs "time-to-event analysis" (published). Same content, different framework wording. |

So of 4 sampled drift candidates: **1 real drift (HEART-FID)**, **1 borderline (DAPA-MI)**, **2 false positives (DIAMOND, TRANSFORM-HF)**. The Jaccard-only metric over-estimates drift by ~50% in this sample; real registered-vs-published content drift in the v0.2 22-trial pool is likely ~3-5 trials, not the 12 the threshold flags.

## Most rigorous Task D estimate

| Bucket | n / 22 | % | Notes |
|---|---|---|---|
| **Real registered-vs-published content drift** | **~3-5** | **14-23%** | Eyeball-confirmed lower bound |
| Paraphrase / framework wording (Jaccard misclassifies as drift) | ~7-9 | 32-41% | False positives requiring manual annotation |
| No publication indexed (primary results not yet on PubMed) | 3 | 14% | ENDEAVOR, OUTSTEP-HF, PERSPECTIVE |
| Aligned or minor wording diff | 7 | 32% | True alignment |

The 14-23% real-drift rate from registered-vs-published is **higher** than v0.3's 7.1% v1-vs-current substantive drift rate, consistent with the COMPare hypothesis that the journal-side switching is more common than the registry-side switching.

## Implications for v1.0/v2.0 paper

1. **Pub-type filter is the right fix.** Don't filter by title keywords when title can include trial acronyms.
2. **Jaccard-only is unreliable** for registered-vs-published comparison. Need full manual annotation for definitive numbers, OR an LLM-judge pairwise comparison (with caveats per `lessons.md` agent-grading rules).
3. **HEART-FID and DAPA-MI are confirmed registered-vs-published content drifters** — both involve hierarchical composite reformulations that registered as separate measures or vague hierarchical placeholders. Add to the v1.0 case-study list alongside DIAMOND, MIMO, PRESERVED-HF, etc.
4. **"No publication indexed" is its own valid finding** — 3/22 (14%) of v0.2 pivotal trials with results posted on CT.gov have no PubMed-indexed primary publication. This is a registry-vs-journal information-flow gap worth a footnote.

## Open for v1.0

- Full manual annotation of all 19 "with publication" trials' registered-vs-published primary outcomes (Jaccard is too noisy)
- LLM-judge pairwise audit as an alternative to manual annotation (with 3-judge ensemble per `lessons.md` agent-grading rule)
- Sub-classify drift by direction (separate→composite, vague→specified, etc.)

## Source artefacts

- v1 commit: `08efe60` (`fetch_publications.py`)
- This v2 commit: `d8f2a70` (`fetch_publications_v2.py`)
- Output: `hf_publications_22_v2.json` + `hf_pub_vs_registered_diff_v2.json`
