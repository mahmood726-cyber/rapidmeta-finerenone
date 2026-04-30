# Outcome-switching MA — v0.3 follow-up

> Created 2026-04-30 after the n=22 v0.2 ship (commit `fa9ffb5`).
> Target: any future Claude session. Run `cat outcome_switching/TODO_v0.3.md` and proceed.

Working directory: `C:\Projects\Finrenone\outcome_switching\`

---

## Task A — Manual TF extraction for the 5 parse-uncertain trials  ✅ CLOSED 2026-04-30

Fixed via parser patch in `compute_v1_vs_current.py` (use LARGEST candidate, accept `WeekN` no-space). All 22 trials now have numeric Δ%.

Findings folded into FINDINGS_v0.2.md "v0.2.1 update" section. SUMMIT −56.7%, GALACTIC-HF revised −54.5% → −12.3%, four trials confirmed stable at 0%.

---

## Task A (original) — Manual TF extraction for the 5 parse-uncertain trials

The v0.2 regex parser failed to extract a numeric month-equivalent from v1 timeFrame text on these 5 trials:

- **DETERMINE-Preserved** (NCT03877224)
- **SUMMIT** (NCT04847557)
- **OUTSTEP-HF / ACTIVATE-HF** (NCT02900378)
- **STEP-HFpEF** (NCT04788511)
- **PARALLAX** (NCT03066804)

For each:
1. Open `https://clinicaltrials.gov/study/<NCT>?tab=history&a=1` (Playwright Python, same script as `scrape_v1_history.py`)
2. Read the rendered Primary Outcome Measures block
3. Manually extract the numeric timeFrame and add to `hf_v1_vs_current_full.json`
4. Re-run `compute_v1_vs_current.py` to refresh the diff metrics

Some of these may have multiple primary outcomes where the FIRST one has a non-numeric timeFrame (e.g. "Week 12") — the parser handles weeks but only when prefixed with a number. Manual eyeball will catch the patterns the regex misses.

---

## Task B — Verify the 2 unconfirmed statistical-framework changes  ✅ CLOSED 2026-04-30

Both confirmed by side-by-side v1 vs current inspection. PARADISE-MI: time-to-event → cumulative-incidence (Novartis). DELIVER: time-to-event → cumulative-incidence (AstraZeneca). Same pattern as DAPA-HF (AstraZeneca). 3/3 framework changes go in the same direction. Findings folded into FINDINGS_v0.2.md.

---

## Task B (original) — Verify the 2 unconfirmed statistical-framework changes

The v0.2 detector flagged 3 framework changes (PARADISE-MI, DAPA-HF, DELIVER). DAPA-HF was fully verified in v0.1. The other 2 need eyeball confirmation because the regex pattern can hit on shared wording like "occurrence of":

- **PARADISE-MI** (NCT02924727) — flagged as v1 framework `time_to_event` → current `cumulative_incidence_or_count`. Verify by reading both versions side-by-side.
- **DELIVER** (NCT03619213) — same flag. Also has primary_count_change (1 → 2 measures).

For each: confirm whether the framework genuinely switched (DAPA-HF case) vs whether it's a regex artefact from shared phrasing. Update the `framework_change` flag in `hf_v1_vs_current_full.json`.

---

## Task C — Case studies on 2 extreme outliers  ✅ CLOSED 2026-04-30

**DIAMOND** is the headline finding: primary outcome **content-changed** from hard CV event (CV death or CV hospitalization, 6m–2.5y window) to surrogate biomarker (serum K+ levels, 227-day exposure). This is a fundamental switch in *what the trial measures*, not a TF artefact. Most serious drift in the entire pool. New typology label: "outcome_content_change" (1/22).

**TRANSFORM-HF** is a legitimate extension: same outcome (all-cause mortality), follow-up extended 12m → 30m with NDI added. Outcome content stable. Normal mid-trial extension.

Findings folded into FINDINGS_v0.2.md.

---

## Task C (original) — Case studies on 2 extreme outliers

- **DIAMOND** (NCT03888066) — TF Δ −95.1%. Likely reflects a randomized-withdrawal trial with multiple "primary outcome" candidates at different windows. Read v1 and current carefully and write a case-study paragraph for FINDINGS_v0.2.md.
- **TRANSFORM-HF** (NCT03296813) — TF Δ +150%. Likely reflects mid-trial extension as event rate came in lower than planned. Same case-study treatment.

These two outliers probably explain ~30% of the variance in the TF-change distribution and deserve their own footnote in the v1.0 paper.

---

## Task D — Add the published-manuscript comparator (third pair)

Currently we have:
- v1 (initial registered) vs current (registered) — Playwright UI scrape ✅
- Current (registered) vs results-section (reported) — v2 API ✅
- Current (registered) vs **published manuscript** — TODO

Approach:
1. For each of the 22 NCTs, find the primary publication via PubMed `lookup_article_by_citation` (NCT cross-reference)
2. Pull the published-paper primary outcome from PubMed abstract or full text
3. Compare to current registered primary outcome with the same Jaccard token-overlap matching used in `compute_diffs.py`
4. Flag any registered-vs-published switching events

Caveat: PubMed full text isn't always accessible programmatically. Abstracts often summarise the primary outcome in a short phrase that doesn't preserve the registry wording, which can produce false-positive switching flags. Manual review required.

This is the **highest-value extension** for a methods paper because reported-vs-published switching is the COMPare methodology and is what hits journal stats reviewers.

---

## Task E — Expand to all 198 P3/P4 HF trials post-2015

Drop the n≥500 + has_results gates. The 22-trial pool is biased toward FDAAA-compliant pivotal industry trials. Expanding to:

- All 198 P3/P4 HF trials post-2015 (current: 25 with results posted ≥500; expanding by ~8x)
- Including TERMINATED + WITHDRAWN trials (where prereg drift may be highest)
- Stratifying by sponsor class (industry vs academic vs govt)

Run with the same `scrape_v1_history.py` pipeline. Wall time estimate: 30 min for 198 trials × 6 sec each.

This produces a properly-powered rate estimate that can be compared to the medRxiv 2025.11.06 24% baseline.

---

## Task F — Run engine tests + commit

After Tasks A-E, no engine tests apply (this isn't a DTA review with the Reitsma engine). But verify Sentinel passes:

```bash
cd C:\Projects\Finrenone
python -m sentinel scan --repo C:\Projects\Finrenone
```

Must report 0 BLOCK introduced. Commit each task as a separate commit with the standard footer:

```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Then push.

---

## Task G — Update the E156 workbook entry

After v0.3 is shipped:

1. Update `C:\E156\rewrite-workbook.txt` entry `[560/549] outcome-switching-ma-hf` with the v0.3 numbers
2. Update the header counter line `+1 outcome-switching-ma-hf 2026-04-30 [v0.2; n=22 full pool, 21/22 drift]` to reflect v0.3
3. Re-run the E156 validator (informational only; YOUR REWRITE field stays blank for the user to fill)

---

## Hard rules (carried forward from `feedback_*.md` memory)

- Every PMID + DOI in the published-manuscript comparator must be verified via PubMed `get_article_metadata` against the trial's registered title. Per `lessons.md` 2026-04-28 LLM-citation-misattribution rule.
- Do NOT introduce any citation that isn't on the verified per-trial PMID list.
- Do NOT use placeholder authors / years / DOIs anywhere.
- Sentinel must remain 0 BLOCK.
- For multi-hour edits in this repo, **commit a stub immediately after creation** so the harvest peer-review workflow doesn't delete untracked files mid-build (per `feedback_finrenone_build_safety.md`).

---

## End-of-task report

After Tasks A-G complete, list which closed cleanly + any blockers. Then delete this file (`rm outcome_switching/TODO_v0.3.md`) as the closing commit.

---

## Source-of-truth pointers

- v0.2 commit: `fa9ffb5` (`feat(outcome-switching): v0.2 — n=22 full HF P3 pool, 21/22 drift detected`)
- Workbook entry: `C:\E156\rewrite-workbook.txt` line ~40936 `[560/549] outcome-switching-ma-hf`
- Findings: `outcome_switching/FINDINGS_v0.2.md`
- Diff data: `outcome_switching/hf_v1_vs_current_full.json`
- Scaler: `outcome_switching/scrape_v1_history.py`
- Diff engine: `outcome_switching/compute_v1_vs_current.py`
- Memory pointers: `~/.claude/projects/C--Users-user/memory/feedback_subagent_dispatch.md` and `feedback_finrenone_build_safety.md`
