# DTA portfolio v1.1 follow-up

> Created 2026-04-29 after the hs-cTn 0/1h NSTEMI build (commit `aed1979` on master) and the published-MA + Cochrane DTA Handbook §10.4 review.
>
> Target: any future Claude session, ~2 weeks from creation. Run `cat TODO_v1.1_follow_up.md` to load this brief, then proceed.

Working directory: `C:\Projects\Finrenone\`

---

## Task A — hs-cTn three-zone framing (`HSCTN_NSTEMI_DTA_REVIEW.html`)

The current build treats `rule-in + observe` as test positive (rule-out safety framing). Burgos 2020 ([PMID 32597681](https://pubmed.ncbi.nlm.nih.gov/32597681), DOI 10.1177/2048872620935399) and Chiang 2020 ([PMID 32245882](https://pubmed.ncbi.nlm.nih.gov/32245882), DOI 10.1136/heartjnl-2019-316343) report Spec ~91-95% using the **exclude-observe** convention. Per Cochrane DTA Handbook §10.4 (Macaskill 2010 with 2023 update), both framings are defensible but **both should be reported when a test is genuinely three-zone**.

Add to the HTML:

1. **Methods paragraph** (in the Methods tab, after the strategy-heterogeneity paragraph) that explicitly declares the three-zone framing choice. State that the primary 2x2 uses the rule-out safety framing (rule-in + observe = test positive), and a sensitivity analysis using the exclude-observe convention is provided alongside.
2. **Sensitivity-analysis tier** in the screening dataset: re-extract the 5 primary 2x2 cells with observe-zone patients EXCLUDED from the 2x2 entirely. Pool with the engine and report alongside the primary tier. Expected pooled Sens ~98%, Spec ~91-95% (matching Burgos / Chiang).
3. Add a comparison row in the Substantive-comparators section noting the framing alignment.

---

## Task B — Full-text re-extraction (`HSCTN_NSTEMI_DTA_REVIEW.html`)

Currently flagged with `provenance: "pubmed_abstract_back_computed_pending_full_text_verification"`:

- **Boeddinghaus 2017** Circulation (PMID 28283497, DOI 10.1161/CIRCULATIONAHA.116.025661) — APACE 0/1h hs-cTnI Abbott direct-comparison 2x2 cells (currently TP=138, FP=252, FN=1, TN=593)
- **Twerenbold 2019** JACC (PMID 31345421, DOI 10.1016/j.jacc.2019.05.046) — ESC 0/1h outcome study 2x2 cells (currently TP=156, FP=380, FN=1, TN=826)

Retrieve full-text Tables 2/3 (or supplementary) for each, extract the actual TP/FP/FN/TN counts, and update the `screeningStudies` array entries. Update the `provenance` field to `"pubmed_full_text_table"` once verified, and remove the v1.1-flag caveat from `data_caveats`.

---

## Task C — D-dimer ADJUST-validation 2019 PMID

In `ddimer_pe_trials.json` line ~104, the entry `"ADJUST-validation - van der Pol 2019"` has `pmid: null` with note: *"prior PMID 29669607 was a Medicaid/CABG paper; prior DOI 10.1016/S2352-3026(18)30048-6 was a haemophilia paper; the cited van der Pol Lancet Haematol 2019 ADJUST/age-adjusted-validation paper could not be re-located in PubMed during the 2026-04-28 verification round."*

Retry with PubMed `lookup_article_by_citation` and `search_articles` using broader search terms (`"van der Pol"` + Wells + age-adjusted + D-dimer + 2019). If a real paper exists, populate the PMID and DOI. If no verifiable paper exists, drop the row from the dataset (cite under p-tau217 fallback rule (c)) and document the removal in the audit log `dta_doi_check_2026-04-28.md`.

---

## Task D — Run engine tests + commit

After Tasks A-C, run from `C:\Projects\Finrenone\`:

```bash
node --test tests/test_dta_engine.mjs
```

Must report 31/31 pass. Commit each task as a separate commit with the standard footer:

```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Then push.

---

## Hard rules (carried forward from T35 + 2026-04-29 hs-cTn build)

- Every new PMID + DOI must be verified via PubMed `get_article_metadata` against the in-page citation label before adding. Per `lessons.md` 2026-04-28 LLM-citation-misattribution rule and the T35 D-dimer audit (~62% misattribution rate in the prior LLM-drafted dataset).
- Do NOT introduce any citation that isn't on the verified list in `hsctn_nstemi_trials.json` or the engine-math reference list in `PTAU217_AD_DTA_REVIEW.html`.
- Do NOT use placeholder authors / years / DOIs anywhere.
- Do NOT skip the engine test step before commit.
- Sentinel must remain 0 BLOCK.
- For multi-hour edits in this repo, **commit a stub immediately after creation** so the harvest peer-review workflow doesn't delete untracked files mid-build (per `feedback_finrenone_build_safety.md` memory).

---

## End-of-task report

List which of A-D completed cleanly, which are blocked, and any new misattributions discovered. Then delete this file (`rm TODO_v1.1_follow_up.md`) as the closing commit.

---

## Source-of-truth pointers

- Build commit: `aed1979` (`feat(dta-hsctn): 6th DTA review — hs-cTn 0/1h algorithm for NSTEMI rule-out`)
- Trial JSON: `hsctn_nstemi_trials.json` (committed in `563f4b1`)
- Audit log: `dta_doi_check_2026-04-28.md` — append v1.1 results here
- Engine: `rapidmeta-dta-engine-v1.js` v1.0.0 (do not modify)
- Tests: `tests/test_dta_engine.mjs` (31 tests; do not modify)
- Memory pointers: `~/.claude/projects/C--Users-user/memory/feedback_subagent_dispatch.md` and `feedback_finrenone_build_safety.md`
