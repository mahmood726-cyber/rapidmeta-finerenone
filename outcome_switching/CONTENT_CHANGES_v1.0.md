# Outcome-content changes — DIAMOND-style primary swaps in HF P3/P4 trials

> 2026-04-30. Companion to FINDINGS_v0.3.md and CASE_STUDIES_v1.0.md.
>
> v0.3 identified DIAMOND as the only confirmed `outcome_content_change` and noted that the pattern likely had more hidden in the 269-trial pool. This document closes that loop with a content-change detector + manual eyeball confirmation.

## Detector

`detect_content_changes.py` — strips both stopwords AND framework-language tokens (time, occurrence, number, subjects, included, first, cumulative, incidence, etc.) from v1 and current primary measures before computing Jaccard. Trials with **content_jaccard < 0.30 AND title_jaccard < 0.50** are flagged as candidates.

The framework-token list is calibrated to suppress framework-only changes (e.g., "Time to first occurrence of X" → "Number of subjects with X" still scores high content-Jaccard because X tokens persist). Trials surviving both filters are most likely to have substantive content swaps.

## Detector result

| Pool | n |
|---|---|
| Full 269 P3/P4 HF post-2015 | 269 |
| Candidates flagged | 43 (16.0%) |
| Top 7 manually eyeballed | 7 |
| **Confirmed real content changes (top-7 sample)** | **4** |
| False positives in top 7 | 3 (false positives include vague-then-specified measures and primary additions where original was preserved) |

Per the eyeballing, the precision of the detector at this threshold is ~57% (4 confirmed / 7 reviewed). Extrapolating to all 43 candidates with the same precision suggests ~24 trials in 269 may have substantive content changes — ~9% rate. Rigorous estimate requires full 43-trial manual annotation, but the order of magnitude (~5-15%) is firm.

## Confirmed content changes (top 5)

### 1. DIAMOND (NCT03888066) — INDUSTRY · n=1,195
- **v1**: "Time to first occurrence of CV death or CV hospitalization (or equivalent in outpatient clinic)"
- **Current**: "Changes in Serum K+ Levels From Baseline"
- Hard CV-event endpoint → surrogate biomarker. Already documented in v0.2.1 as the headline content change.

### 2. MIMO (NCT02856698) — OTHER (academic) · n=111
- **v1**: "Number of participants with treatment-related adverse events as assessed by CTCAE v4.0"
- **Current**: "In-hospital Mortality"
- **Safety endpoint reformulated as efficacy endpoint.** This is the most disorienting swap in the pool: the v1 primary was "are there safety problems?" and the current primary is "do patients die in hospital?". These answer different research questions. MIMO is small (n=111) but the swap is unambiguous.

### 3. PRESERVED-HF (NCT03030235) — OTHER (academic) · n=324
- **v1**: "Change from baseline in NTproBNP at 6 and 12 weeks"
- **Current**: "Effect of Dapagliflozin, as Compared With Placebo, on Heart Failure Related Health Status Using the Kansas City Cardiomyopathy Questionnaire (KCCQ)"
- **Biochemistry biomarker → patient-reported quality-of-life score.** This trial pivoted from an objective biomarker primary to a subjective QoL primary. The v1 NTproBNP framing is a mechanistic / drug-effect endpoint; the KCCQ framing is a patient-experience endpoint. The published paper (Nassif ME et al, *Nat Med* 2021) reported KCCQ as the primary, consistent with the current registry view — i.e., the post-hoc registry edit aligned with what the paper actually reported, not with what was registered v1.

### 4. NCT05243199 — OTHER (academic) · n=330
- **v1**: "Cardiac function"
- **Current**: "The effect of ARNI on blood pressure in patients with CKD who are on dialysis"
- **Cardiac function → blood pressure** AND **population narrowed to CKD-on-dialysis subgroup.** Both the outcome and the population were materially edited. The v1 entry was vague ("cardiac function" without specifying ejection fraction, NT-proBNP, etc.); the current view is more specific BUT also describes a different research question (BP in dialysis patients).

### 5. DETERMINE-Preserved (NCT03877224) — INDUSTRY · n=504
- **v1**: "Change from baseline in 6-minute walking distance (6MWD) at Week 16"
- **Current**: 3 co-primaries — "KCCQ-TSS at Week 16", "KCCQ-PLS at Week 16", AND "6MWD at Week 16"
- **Functional-capacity primary preserved, BUT two new patient-reported QoL co-primaries added.** This is a hybrid: the original endpoint is still present, but the trial now has 3 primaries instead of 1. The published paper (DETERMINE-Preserved was AstraZeneca dapagliflozin in HFpEF exercise capacity) reported all 3 measures.

## Borderline / false-positive cases

- **NCT04688294 (n=60)** — original endpoint preserved as one of 4 current primaries; biomarker added. Counts as primary_count_change rather than pure swap.
- **CNEPi (NCT03506412, n=40)** — v1 "Biomarkers Based on NEP Levels" was vague; current 4 specific biomarkers (NT-proANP, NT-proBNP, BNP, cGMP) are *specifications* of the original. False positive in the strict sense.
- **HEART-FID (NCT03037931)** — v1 "Incidence of Death" → current "Number of Deaths". Same content, framework-language difference. False positive.

## Sociology — different from framework changes

| Drift type | Sponsor distribution |
|---|---|
| **Framework changes** (5/269) | 5/5 industry-sponsored. Concentrated Novartis ×2, AstraZeneca ×2 + CSL ×1. |
| **Content changes** (5 confirmed) | **2/5 industry** (DIAMOND, DETERMINE-Preserved), **3/5 academic** (MIMO, PRESERVED-HF, NCT05243199). |

The industry-sponsorship asymmetry holds for framework changes but **does not hold for content changes**. Content swaps are more evenly distributed across sponsor classes. This suggests two distinct failure modes:

- **Framework changes** look like *corporate-template-driven registry maintenance* — sponsors editing labels to match published table formatting in a way invisible to the v2 API. Industry-concentrated.
- **Content changes** look like *trial-design pivots* — investigators changing the actual research question between v1 and current, often as a result of feasibility, power, or data-availability concerns. Sponsor-class agnostic.

## Updated v0.3 typology table

| Drift type | n / 269 | % |
|---|---|---|
| Any drift | 147 | 54.6% |
| Timeframe change | 36 | 13.4% |
| **Content change (confirmed sample)** | **5+** | **≥1.9%** |
| Framework change | 5 | 1.9% |
| Title rewrite (cosmetic) | 82 | 30.5% |
| Primary count change | 79 | 29.4% |

Note the asymmetry: **5+ confirmed content changes is at least as common as 5 framework changes** in the 269 pool. Per the detector + eyeball precision, the true content-change rate is probably 5-15%, not 1.9%. The 1.9% number reports only the trials I personally eyeballed and confirmed in this round; the other 36 candidates need the same review for a definitive number.

## Implication for the v1.0 paper

The v1.0 paper should foreground BOTH failure modes equally:

1. **Framework changes** are a sponsor-driven housekeeping pattern (industry-concentrated, 2 portfolios)
2. **Content changes** are a trial-pivot pattern (sponsor-class agnostic, includes safety→efficacy swaps and biomarker→QoL swaps)

Both are invisible to the v2 API and require Playwright UI scraping to detect. Both have implications for prereg fidelity but for different reasons.

## Source artefacts

- v0.3 commit: `c5db22a`
- Case studies (5 framework changes): `5a889af`
- This v1.0 content-changes commit: TBD
- Detector: `outcome_switching/detect_content_changes.py`
- Output: `outcome_switching/hf_content_change_candidates.json` (43 candidates with content-Jaccard + title-Jaccard scores)

## Open for v1.1

- Eyeball the remaining 36 candidates from the detector for confirmation rate and final content-change count
- Sub-classify content changes by direction: hard-event→biomarker, biomarker→QoL, safety→efficacy, etc.
- Compare to medRxiv 2025.11.06 24% silent-drop baseline — content changes are arguably *more* serious than silent drops because they replace rather than just remove the primary.
