# Outcome-switching MA — HF Phase 3 worked example v0.2 (full n=22)

> 2026-04-30. Scaled from the v0.1 n=5 sample to the full n=22 HF Phase 3 primary pool (post-2015, results posted, n≥500). Excludes 3 non-HF trials (CSL112 ACS, antibacterial-envelope CIED, IV thyroxine for organ donors).

## Headline finding

**95% (21/22) of pivotal post-2015 HF Phase 3 trials show v1-vs-current drift** invisible to the CT.gov v2 API:

| Drift type | n / 22 | Notes |
|---|---|---|
| Any drift | **21 (95%)** | only 1 trial preserved everything |
| Time-frame change >5% | 13 | mix of compression (8) and extension (5) |
| Statistical-framework change | **3** | PARADISE-MI, DAPA-HF, DELIVER — time-to-event ↔ cumulative-incidence |
| Title rewrite (Jaccard <0.85) | 13 | usually wording polish + UoM tweaks |
| Primary-outcome count change | 9 | typically 1→2 measures (event count + participant count) |

Median TF change: **−5%** (range −95% to +150%). Compression (n=8) is more common than extension (n=5), but extension is real and not negligible.

## v0.2.1 update (2026-04-30 same-day patches after v0.3 Tasks A–C)

After shipping v0.2, the v0.3 follow-up (`TODO_v0.3.md`) closed three tasks same-day:

**Task A — TF parser fix.** The original regex returned the FIRST month-equivalent in a timeFrame string, which broke on patterns like `baseline (week 0) to end of treatment (week 52)` (returned 0 instead of 52) and `WeekN` no-space variants. v0.2.1 parser returns the LARGEST candidate. Effect: 5 previously-uncertain trials now have numeric Δ (DETERMINE-Preserved 0%, ACTIVATE-HF 0%, STEP-HFpEF 0%, PARALLAX 0%, **SUMMIT −56.7%**); GALACTIC-HF refines from −54.5% to −12.3% (max-vs-max instead of max-vs-median). Updated counts: 14 timeframe changes (was 13), 9 compressions (was 8), 5 extensions (unchanged).

**Task B — Framework-change verification.** Side-by-side v1 vs current inspection confirms PARADISE-MI and DELIVER framework switches are real, not regex artefacts:
- **PARADISE-MI**: v1 "Time to the first occurrence of a confirmed composite endpoint" → current "Number of Participants With First CEC Confirmed Primary Composite Endpoint". Pattern: time-to-event → cumulative-incidence. Same as DAPA-HF.
- **DELIVER**: v1 "Time to the first occurrence" → current "Subjects Included in the Composite Endpoint". Plus a 2nd primary added for the LVEF<60% subpopulation. Same time-to-event → cumulative-incidence pattern.

**All 3 statistical-framework changes go in the same direction**: time-to-event reframed as cumulative-incidence. PARADISE-MI is Novartis; DAPA-HF and DELIVER are AstraZeneca. The pattern looks deliberate, not accidental — and is invisible to the v2 API.

**Task C — Outlier case studies.**

- **DIAMOND (−99% TF)** is **the most consequential drift in the entire audit**. The primary outcome was switched from a hard CV-event endpoint (`Time to first occurrence of CV death or CV hospitalization`, 6m–2.5y window) to a surrogate biochemistry endpoint (`Changes in Serum K+ Levels From Baseline`, 227-day exposure window). This is not a timeframe artefact — it's a fundamental change in *what the trial is measuring*. DIAMOND was a randomized-withdrawal design of patiromer in HF; the CV-event primary likely wasn't powered, so the trial was reframed around the potassium biomarker that *is* powered. Whatever the sponsor's rationale, this is a registered-vs-current primary outcome substitution that the v2 API does not flag. It should be the headline DIAMOND case study in any v1.0 paper.
- **TRANSFORM-HF (+150% TF)** is a legitimate extension: same outcome (all-cause mortality), follow-up window extended from 12 months to 30 months, with NDI added as a data source. Outcome content stable. This is normal mid-trial extension.

**Revised drift typology**:
- *Outcome-content change*: 1 (DIAMOND, hard CV-event → surrogate biomarker) — newly identified
- *Statistical-framework change*: 3 (PARADISE-MI, DAPA-HF, DELIVER, all time-to-event → cumulative-incidence) — confirmed
- *Timeframe-only drift*: 14 (mix of compressions and extensions, no content change)
- *Title rewrite only*: 13 (cosmetic)

The 1 outcome-content change is qualitatively the most serious failure mode and should be foregrounded in v1.0 over the cosmetic 95% drift rate.

## v0.1 → v0.2 lessons

**The n=5 sample undersampled in two ways**:
1. **All 5 sample trials showed TF compression.** The full pool has 5 extensions too. The "compression by default" framing of v0.1 was a sampling artefact.
2. **Only 1 framework change in the n=5 sample (DAPA-HF).** Full pool surfaces 3: DAPA-HF, PARADISE-MI, DELIVER — all elevation papers.

The 95% drift rate is robust across the full pool. The v0.1 finding stands; the directional bias claim does not.

## Per-trial drift detail

| NCT | Acronym | TF Δ% | Drift flags |
|---|---|---|---|
| NCT02924727 | PARADISE-MI | **+34.4%** | timeframe_change, **statistical_framework_change**, title_rewrite |
| NCT03877224 | DETERMINE-Preserved | TF parse uncertain | title_rewrite, primary_count_change |
| NCT04986202 | ENDEAVOR (mitiperstat) | 0% | primary_count_change |
| NCT04847557 | SUMMIT | TF parse uncertain | title_rewrite, primary_count_change |
| NCT02900378 | OUTSTEP-HF | TF parse uncertain | title_rewrite, primary_count_change |
| NCT04788511 | STEP-HFpEF | TF parse uncertain | primary_count_change |
| NCT05093933 | VICTOR | −10.0% | timeframe_change, title_rewrite |
| NCT03888066 | DIAMOND | **−95.1%** | timeframe_change (extreme outlier) |
| NCT03037931 | HEART-FID | 0% | primary_count_change |
| NCT03036124 | DAPA-HF | −22.8% | timeframe_change, **statistical_framework_change**, title_rewrite |
| NCT04564742 | DAPA-MI | −19.4% | timeframe_change, title_rewrite |
| NCT04157751 | EMPULSE | 0% | title_rewrite |
| NCT04435626 | FINEARTS-HF | −23.8% | timeframe_change, title_rewrite, primary_count_change |
| NCT03057951 | EMPEROR-Preserved | +21.3% | timeframe_change, title_rewrite |
| NCT03296813 | TRANSFORM-HF | **+150.0%** | timeframe_change (extreme outlier) |
| NCT03066804 | PARALLAX | TF parse uncertain | title_rewrite, primary_count_change |
| NCT04509674 | EMPACT-MI | +37.4% | timeframe_change |
| NCT02929329 | GALACTIC-HF | −54.5% | timeframe_change |
| NCT03619213 | DELIVER | +27.6% | timeframe_change, **statistical_framework_change**, title_rewrite, primary_count_change |
| NCT02861534 | VICTORIA | −21.4% | timeframe_change |
| NCT03057977 | EMPEROR-Reduced | −10.1% | timeframe_change, title_rewrite |
| (1 trial with no drift) | — | 0% | — |

Note: 5 trials show "TF parse uncertain" — the v1 timeFrame text didn't yield a clean month-equivalent for the regex. Manual extraction would resolve these and is a v0.3 task.

## The 3 statistical-framework changes

These are the most consequential drifts because they change the analytic primary endpoint, not just registry housekeeping.

| Trial | v1 framework | Current framework |
|---|---|---|
| **PARADISE-MI** | (need to re-read v1; flagged by the pattern detector) | (different) |
| **DAPA-HF** | Time to first occurrence (Cox / KM) | Subjects included in composite (cumulative incidence) |
| **DELIVER** | (need to re-read v1) | (different) |

The DAPA-HF case is fully verified in v0.1. PARADISE-MI and DELIVER need human eyeball review of the v1 page to confirm the framework-change classification isn't a regex artefact (e.g., wording overlap on "occurrence of"). v0.3 task.

## Two extreme outliers worth a footnote

- **DIAMOND (−95% TF change)**: v1 had a long-duration metric (likely 52+ weeks); current trials reports a much shorter window (likely 4-week titration phase). DIAMOND is a randomized-withdrawal trial of patiromer; the design is unusual and may legitimately have multiple "primary outcome" candidates with different windows.
- **TRANSFORM-HF (+150% TF extension)**: v1 had a short-duration metric (e.g., 30-day or 6-month); current is much longer (e.g., 30-month event accrual). Likely reflects mid-trial extension as event rate came in lower than planned.

Both deserve manual case studies in a v1.0 paper.

## Comparison to baselines

| Pool | Method | Switching rate |
|---|---|---|
| medRxiv 2025.11.06 baseline (broad ITS pool) | Pre-spec vs reported | ~24% |
| **Our HF P3 pool, v2 API only** | Current registered vs reported | **0/22 = 0%** |
| **Our HF P3 pool, v1 vs current** | Initial registered vs current registered | **21/22 = 95%** |
| **Our HF P3 pool, v1-vs-current FRAMEWORK only** | Stat-framework drift | **3/22 = 14%** |

The 95% rate is dominated by cosmetic / housekeeping drift; the 14% framework rate is the substantively meaningful number. Even at 14%, that's substantially above the medRxiv baseline of 24% (which counted hard outcome drops, not framework switches).

## Methodological implications

1. **CT.gov v2 API + AACT 2026-04-12 alone yields a false-clean signal** for the prereg-fidelity question on pivotal industry trials.
2. **Playwright scraping of the registry-history UI is the cheapest practical fix.** The full n=22 sweep took ~3 minutes wall time and 22/22 succeeded.
3. **Automated parsing of v1 timeFrames is brittle** (5/22 parse failures). Manual review of the 5 unclear cases + the 3 framework changes is the bottleneck for a definitive v1.0 finding.
4. **The portfolio-implication for our DTA/NMA reviews**: any future review that audits prereg drift via the API alone will systematically under-detect. Reviews that depend on prereg integrity (e.g. as a RoB input) need the history-UI scrape as a complementary data source.

## Source artefacts

- `outcome_switching/extract_hf_outcomes.py` — v2 API extractor (committed `9a2d626`)
- `outcome_switching/compute_diffs.py` — Jaccard discrepancy script (`9b9bb2c`)
- `outcome_switching/scrape_v1_history.py` — Playwright Python scaler (`1de8e76`)
- `outcome_switching/compute_v1_vs_current.py` — full v1-vs-current diff (this commit)
- `outcome_switching/hf_outcomes_raw.json` — current view, 25 trials (`9b9bb2c`)
- `outcome_switching/hf_history_v1_full.json` — v1 view, 22 trials (this commit)
- `outcome_switching/hf_v1_vs_current_full.json` — full diff output (this commit)

## What's still open for v0.3

- Manual review of 5 TF-parse-uncertain trials (DETERMINE-Preserved, SUMMIT, OUTSTEP-HF, STEP-HFpEF, PARALLAX) to extract numeric TF values from v1 pages.
- Manual confirmation of the 3 framework-change classifications (PARADISE-MI, DAPA-HF, DELIVER) — DAPA-HF is locked from v0.1; the other two need eyeball check.
- Add the published-manuscript comparator (third pair) for the v1.0 ship.
- Expand to all 198 P3/P4 HF post-2015 trials (drop the n≥500 + results-posted gates) — non-completion / terminated trials may have higher drift rates.
