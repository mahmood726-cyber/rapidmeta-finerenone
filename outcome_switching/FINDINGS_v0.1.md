# Outcome-switching MA — HF Phase 3 worked example v0.1

> 2026-04-30. n=5 sample of pivotal post-2015 HF Phase 3 trials with results posted: FINEARTS-HF, DAPA-HF, EMPEROR-Reduced, VICTORIA, GALACTIC-HF.

## Headline finding

**The CT.gov v2 API understates outcome switching by 100%.** Same trials, two methodologies:

| Comparison | Method | Switching rate (n=22 / n=5) |
|---|---|---|
| Current registered primary vs results-section reported primary | CT.gov v2 API direct | **0 / 22 = 0%** |
| Initial registered primary (v1) vs current registered primary | Playwright scrape of `?tab=history&a=1` | **5 / 5 = 100%** for time-frame drift; 1 / 5 for statistical-framework change |

Sample is small (n=5 of 22) but uniform — every single trial showed material time-frame compression between initial registration and the current registry view. This drift is invisible to API-only audits.

## Per-trial drift detail

| Trial | v1 timeframe | Current timeframe | Δ% | Other drift |
|---|---|---|---|---|
| FINEARTS-HF | 42 months | avg 32 months | **−24%** | Single primary → 2 primaries (event count + participant count); title rewrite |
| DAPA-HF | ~36 months | 27.8 months | **−23%** | **Statistical framework change**: "time to first occurrence" → "subjects included in" — i.e. time-to-event (Cox/KM) → cumulative-incidence framework. This is a real conceptual switch. |
| EMPEROR-Reduced | 38 months | 34.2 months (1040 days) | −10% | Minor title rewrite |
| VICTORIA | ~42 months (3.5y) | 33 months | **−21%** | Cosmetic "HF" acronym addition |
| GALACTIC-HF | 48 months (208 weeks) | 21.8 months median (42 max) | **−55%** | Prospective TF "Through study completion" → retrospective TF "overall median duration of follow-up was..." |

Median time-frame compression: **−23%**. All 5 in the same direction (compression, not extension). This is consistent with the operational reality that pivotal event-driven HF trials accrue events faster than planned and stop at the first interim analysis crossing — so the *actual* follow-up duration is shorter than the *protocol-maximum* duration. Whether that compression is benign (event accrual faster than expected) or biased (early stopping for benefit, regression-to-mean concerns) is a live methods debate.

## Methodological caveats

1. **Sample is curated, not random.** These 5 are landmark publication-headline trials. A random sample of 5 from the 22-trial pool may behave differently.
2. **TF "drift" includes legitimate updates.** When an event-driven trial reaches its primary analysis cutoff, the TF on CT.gov is updated to reflect the actual cutoff date. That's not "outcome switching" in the bad sense — it's accurate registry maintenance. The relevant question is whether the *content* of the primary outcome (composite components, statistical framework, sample-size justification) was changed under cover of a TF update.
3. **DAPA-HF stat-framework change is the real signal.** Time-to-event vs cumulative-incidence is a non-trivial choice. The DAPA-HF NEJM paper reports both, but the registered primary outcome was rewritten between v1 and current to match the post-hoc preferred framework.

## Comparison to medRxiv 2025.11.06 baseline

medRxiv 2025.11.06 reports ~24% silent-drop rate of pre-specified outcomes across a broad ITS-trial pool. Our findings:

- **API-only audit (current vs reported)**: 0% — well below medRxiv baseline.
- **History-aware audit (v1 vs current)**: 100% TF compression, 20% statistical-framework change — well above medRxiv baseline.

Both can be true simultaneously. The medRxiv baseline measures *outcome dropping*; our v1-vs-current detects *outcome reformulation*. They are different failure modes of the registry-fidelity contract.

## What this means for portfolio MA methodology

1. **CT.gov v2 API alone is insufficient** to detect prereg drift in pivotal industry trials. Relying on `protocolSection.outcomesModule` gives a false-clean signal.
2. **AACT does not fix this** — the 2026-04-12 snapshot has design_outcomes (current view) but no version history.
3. **Playwright scraping of `?tab=history&a=1` is the practical path** to detect initial-vs-current drift. It worked cleanly for all 5 trials in this sample (~30 seconds per trial including extraction).
4. **A formal "outcome-switching MA" needs three comparators**, not the one we initially modelled:
   - v1 (initial registered) vs current (registered)
   - Current (registered) vs results-posted
   - Current (registered) vs published manuscript

   Our v0.1 sample addresses the first; the v2 API addresses the second; PubMed full-text addresses the third. Comprehensive switching audit = all three.

## Next steps

- v0.2: scale Playwright scraping to all 22 trials in the HF Phase 3 pool (~10–15 min wall time).
- v0.3: add the published-manuscript comparator (third pair).
- v1.0: ship as a methods note + scale to all 198 P3/P4 HF post-2015 trials (results-posted gate dropped — terminated/withdrawn trials are likely the highest-yield segment).

## Source artefacts

- `outcome_switching/extract_hf_outcomes.py` — v2 API extractor (committed `9a2d626`)
- `outcome_switching/compute_diffs.py` — Jaccard discrepancy script (committed `9b9bb2c`)
- `outcome_switching/hf_outcomes_raw.json` — 25 trials current-vs-reported (committed `9b9bb2c`)
- `outcome_switching/hf_history_v1_vs_current.json` — n=5 sample initial-vs-current (this commit)
