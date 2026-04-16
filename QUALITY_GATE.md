# QUALITY_GATE.md — RapidMeta Living MA Portfolio

> Pre-publish acceptance checklist. An app is **GATE-PASS** only if every threshold below is met by the **deployed HTML** (not the source, not the spec).
> The validator script (`validate_living_ma_portfolio.py`) implements gates 1–4 and 7. Gates 5, 6, 8 are human-attested at submission time and recorded in `gate_attestation.json` per repo.
>
> **You set the thresholds.** Defaults below are my recommendation based on the 17/17 fix-all session (2026-04-16). Edit the `THRESHOLD:` line in each gate to your editorial bar. Once values are locked, the validator should reject any app that violates them.
>
> Linked rules: `~/.claude/rules/rules.md`, `~/.claude/rules/advanced-stats.md`, `~/.claude/rules/e156.md`. This file enforces app-level quality; those govern broader workflow.

---

## Gate 1 — Minimum trial count

A "meta-analysis" of one trial is not a meta-analysis. Continuous-MD apps and HR apps both bound by k.

- **Why this matters:** Single-trial apps shipped under "Meta-Analysis" headers are a misrepresentation. Ground-truth review of this portfolio (2026-04-16) found 6 apps documented as k=1 that were actually k=3-5 (stale README) and 0 apps that were genuinely single-trial after parser fixes.
- **Trade-off:** Higher k blocks novel/sparse-evidence topics from the portfolio (e.g. ATTR-CM had k=1 for years). Lower k accepts weak pools as MAs.
- **THRESHOLD:** `k_min_hr = 2`, `k_min_md = 2` (any pool with <2 published RCTs is not a meta-analysis)
- **REMOVAL POLICY (v1.1, 2026-04-16):** Apps below `k_min` that cannot be expanded to >=2 published RCTs (in same disease and outcome) are *removed from portfolio scope*, not relabeled. Local HTML and sibling repo retained for archival; validator's `EXCLUDED_APPS` set excludes them from scans. Re-admission requires a 2nd RCT.
- **Edge case:** Single-trial reviews are allowed in the portfolio if and only if the app header is renamed from "Meta-Analysis" to "Single-Trial Evidence Review" and the portfolio page tags them distinctly.

## Gate 2 — Benchmark agreement tolerance

`|live_pool − benchmark| / benchmark ≤ X%`

- **Why this matters:** Benchmarks anchor live pools to externally-published reference values. Drift beyond tolerance = dataset error, parser bug, or honest divergence requiring annotation. LIPID_HUB at 18.7% diff (this session) was a real divergence — benchmark was wrong, not the pool.
- **Trade-off:** Tighter (e.g. 5%) catches drift earlier but may flag legitimate revisions when new trials publish. Looser (e.g. 15%) hides slow drift across multiple updates.
- **THRESHOLD:** `tolerance_pct = 10` (HR/OR), `tolerance_mmhg = 0.5` (MD absolute)
- **Action on violation:** WARN at 5–10%, BLOCK at >10% under `--strict`.

## Gate 3 — Required computational witnesses

What must pass before an app can ship:

- [ ] `validate_living_ma_portfolio.py` exits 0 and reports `Within X%` for this app
- [ ] `Rscript validate_<app>.R` agrees with `metafor::rma()` to **TODO: tolerance** (recommended: `1e-6` deterministic; `0.05` for stochastic Monte Carlo per `rules.md` testing section)
- [ ] CT.gov augmentation report (`ctgov_integration_report.py`) flags zero >5% drift between mined and curated HRs
- [ ] Peto fallback computed for any trial with `tE`/`cE` event counts but `publishedHR: null` (or explicit comment in HTML explaining why Peto is unsuitable for that trial)
- **THRESHOLD:** `required_witnesses = ["validator", "r_parity", "ctgov_concordance", "peto_fallback"]` — all 4 MUST for new apps. Legacy apps may set `# r_parity_skip: <reason>` per-file.

## Gate 4 — Published-HR provenance

Every trial entry's `publishedHR` field must be one of:

- (a) Cox HR cited from a peer-reviewed publication (citation in `evidence[]`)
- (b) Peto-derived from event counts, marked `hrSource: 'peto_from_counts'`
- (c) Pre-specified IPD pool (e.g. FIDELITY for FINERENONE), marked `hrSource: 'ipd_pool'`
- (d) `null` — only acceptable if the app uses MD outcome (continuous-MD engine)

- **Why this matters:** Without provenance flags, downstream consumers can't tell whether HR 0.71 is a Cox-adjusted ITT estimate or a Peto approximation. APOLLO-B (this session) became k=4 only after explicit Peto annotation.
- **THRESHOLD:** `provenance_required = true` for every trial with non-null `publishedHR`. Acceptable values: `cox_published`, `peto_from_counts`, `ipd_pool`.

## Gate 5 — Heterogeneity reporting

When pooled, each app must report:

- [ ] Q-statistic with df
- [ ] I² (point estimate)
- [ ] τ² (REML or PM, not DL when k<10 per `advanced-stats.md`)
- [ ] Prediction interval using `t_{k-2}` (not `t_{k-1}`; undefined for k<3)
- [ ] HKSJ-adjusted CI when k<30, with `max(1, Q/(k-1))` floor

- **Why this matters:** I²=0 doesn't mean homogeneity — it means Q≤df. Without τ² + PI, conditional reproducibility claims are unsupported.
- **THRESHOLD:** `min_heterogeneity_fields = 5` (all of: Q+df, I², τ², PI with t_{k-2}, HKSJ-adjusted CI when k<30)

## Gate 6 — Editorial-board COI disclosure (Synthesis-bound apps only)

For E156 micro-papers submitted to *Synthēsis* (where MA serves on editorial board):

- [ ] MA is NOT first author and NOT last author on the manuscript
- [ ] COI statement explicitly names "*Synthēsis* editorial board" and states "no role in editorial decisions on this manuscript"
- [ ] Independent handling editor confirmed in submission cover letter
- [ ] Journal name spelled with macron (`Synthēsis`)

- **Why this matters:** Per `feedback_e156_authorship.md` (2026-04-15), disclosure-only is insufficient when MA serves on the journal's board. Structural separation (positional + editorial) is required.
- **THRESHOLD:** `synthesis_coi_strict = true` — BLOCK submission if any of the 4 fields is missing.

## Gate 7 — E156 workbook ↔ deployed HTML reproducibility

Before promoting a workbook entry to `SUBMITTED: [x]`:

- [ ] Every trial named in CURRENT BODY appears in deployed HTML's `realData`
- [ ] Pooled estimate cited in CURRENT BODY matches live `validate_living_ma_portfolio.py` output to within **TODO: tolerance**
- [ ] Sample size N cited in CURRENT BODY equals sum of `tN+cN` from poolable trials
- [ ] `audit_livingmeta_claims.py` exits 0 for this project

- **Why this matters:** Per `lessons.md` portfolio-defects, claim drift between workbook prose and deployed pool was systemic (21 of 40 projects in 2026-04-14 batch). The audit script catches this, but only if it's run.
- **THRESHOLD:** `workbook_match_hr = 0.005`, `workbook_match_md_mmhg = 0.5`, `workbook_match_n_pct = 2` (matches `audit_livingmeta_claims.py` v5 tolerance)

## Gate 8 — Topic admission criteria (new apps only)

Before scaffolding a new `_LivingMeta` repo from `generate_living_ma_v13.py`:

- [ ] At least **TODO: N** completed RCTs of the intervention exist on CT.gov
- [ ] At least **TODO: M** of those RCTs report a CV/mortality outcome with extractable HR or event counts
- [ ] No more than **TODO: P** are subgroup re-analyses of a single parent trial (avoid the SPRINT-SENIOR/SPRINT-CKD non-independence pitfall)
- [ ] Topic is not already covered by a sibling repo (check `INDEX.md` Shipped portfolio + `audit_livingmeta_claims.py`)
- [ ] Outcome model selected (HR vs OR vs MD vs RR) before generator runs — not after

- **Why this matters:** RENAL_DENERV shipped with k=0 publishedHRs because it was scaffolded as an HR app for trials that only report MD outcomes. Topic admission must match outcome model to trial reality.
- **THRESHOLD:**
  - `min_rct_count = 3`
  - `min_outcome_reporting_count = 2`
  - `max_subgroup_strata = 2`

---

## How this gate is enforced

- **Pre-push (Sentinel)**: gates 1, 4, 5, 7 should be added as Sentinel rules in `~/.sentinel/rules/` so `git push` blocks app updates that violate.
- **Nightly (Overmind)**: gate 2, 3 run as the verifier's primary witness. UNVERIFIED verdict for skip-due-to-missing-baseline.
- **Submission (manual)**: gates 6, 8 attested in `gate_attestation.json` at submission time.

## Threshold version log

Once you fill the `<TODO>` values, increment a version + date here so we can audit when each threshold changed.

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-04-16 | Initial stub by Claude. Awaiting threshold fills. |
| 1.0 | 2026-04-16 | First locked threshold set. User delegated decision; values are conservative defaults from fix-all session reasoning. Loosen any gate by editing the THRESHOLD line and bumping version. |
| 1.1 | 2026-04-16 | Gate 1 `k_min_hr` lowered 3 -> 2 (no meta without >=2 RCTs). Sub-threshold apps with no expansion path are *removed from portfolio scope*, not relabeled. First removal batch (7 apps): CORONARY_IVL, ORFORGLIPRON, IPTACOPAN, LEADLESS_PACING, SEMAGLUTIDE_CKD, SPARSENTAN_IGAN, TRICUSPID_TEER. |
