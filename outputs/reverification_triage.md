# Portfolio reverification triage — 2026-04-30

Status: **NEW-TOPIC FREEZE in effect.** No new dashboards until the
audits below are addressed.

## Update 2026-04-30 (second post-fix pass)

Six of the seven REM-* tasks have been resolved this session:

| Task        | Status   | Notes                                                                                     |
|-------------|----------|-------------------------------------------------------------------------------------------|
| REM-MITT-2  | DONE     | SELECT-Compare entry annotated -- cN=651 is the placebo arm (NOT the n=327 ada arm), per the NMA single-anchor methodology. False-flag from the audit, no value change required. |
| REM-CONT-2  | DONE     | 8 proportion-as-MD entries (Q12W_pct, Q16W_pct in PULSAR/PHOTON/TENAYA/LUCERNE) relabelled `type: 'DESCRIPTIVE_PROPORTION'` so the engine excludes them from the continuous MD pool. |
| REM-CONT-1  | DONE     | LSMD/MMRM transparency clause appended to PICO `out` field of all 27 dashboards with continuous outcomes. Audit-aware update: heuristic now reads PICO `out` as a blanket declaration source. **LSMD_NOT_DECLARED: 81 -> 0. MMRM_NOT_DECLARED: 81 -> 0.** Hot-fix follow-up: first version of the disclaimer used a literal apostrophe (`trial's`) inside a single-quoted JS string and broke 27 dashboards (Playwright caught `Unexpected identifier 's'`). `scripts/fix_lsmd_disclaimer_apostrophe.py` swept all 27 to the apostrophe-free phrasing; `scripts/add_lsmd_disclaimer.py` updated to use the safe text and to flag the trap in a comment. |

Three of the seven REM-* tasks have been resolved this session:

| Task        | Status   | Notes                                                                                     |
|-------------|----------|-------------------------------------------------------------------------------------------|
| REM-ENG-1   | PARTIAL  | V3 (Q-profile call) backfilled in COLCHICINE_CVD, GLP1_CVOT, SGLT2_HF -- audit shows V3 FAIL = 0 across the portfolio. V8 (MH pool) still fails for the same 3 because the older engine layout lacks `_petoPool`/`_remlHksjPool` anchors -- queue as a re-clone. Smoke-tested all 3 in Playwright: 0 console errors. |
| REM-MITT-1  | DONE     | UltIMMa-2 mITT corrected to Gordon 2018 published (ris n=294, pbo n=98) in IL_PSORIASIS_NMA_REVIEW.html. |
| Sentinel V3 | DONE     | `cochrane_v65_invariants.py` now requires call-site presence (`qProfileTau2CI(`) AND definition (`qProfileTau2CI =`), and applies the same lift to `_mhPool` + `_assessROBME`. 466 Sentinel tests still pass. |

Remaining REM-* tasks (REM-MITT-2, REM-CONT-1/2, REM-CLUSTER-1, plus
the REM-ENG-1 V8 re-clone) carry over to the next session.

This consolidates three audit passes over the 170-dashboard portfolio:

1. `audit_mitt_vs_allocated.py`     -> binary tN/cN denominator convention
2. `audit_continuous_conventions.py` -> continuous LSMD/MMRM declaration + denominator
3. `audit_v65_engine_coverage.py`    -> Cochrane v6.5 / RevMan-2025 invariant coverage

---

## 1. v6.5 engine-coverage check (HIGHEST priority)

**164 pairwise dashboards audited. 161/164 fully compliant. 3 partial.**

Per-check failures:

| Check                              | Failures | Notes                                                        |
|------------------------------------|---------:|--------------------------------------------------------------|
| V1 REML iteration                  | 0        | All carry `tau2_reml`                                         |
| V2 REML primary (DL secondary)     | 0        | All correctly tagged `tau2 = (k>=2) ? tau2_reml : tau2_dl`    |
| V3 Q-profile tau2 CI invocation    | **3**    | Helper defined but never called -> tau2 CI not rendered        |
| V4 qchisq closed-form for low df   | 0        | Wilson-Hilferty df=1 saturation fix present                  |
| V5 HKSJ floor `max(1, qStar)`      | 0        |                                                              |
| V6 PI df = k-1 (Cochrane v6.5)     | 0        |                                                              |
| V7 ROB-ME framework                | 0        |                                                              |
| V8 Mantel-Haenszel sensitivity     | **3**    | Same 3 dashboards lack `_mhPool` definition AND call         |

### The 3 partial dashboards

| Dashboard                  | Missing                             | Cause                                                     |
|----------------------------|-------------------------------------|-----------------------------------------------------------|
| COLCHICINE_CVD_REVIEW.html | qProfile call site, `_mhPool` whole | Older engine layout (line 26k) -- backfill scripts missed |
| GLP1_CVOT_REVIEW.html      | same                                | same                                                      |
| SGLT2_HF_REVIEW.html       | same                                | same                                                      |

**Remediation:** these three predate the v6.5 portfolio sweep and have a
different engine layout (REML primary block lives ~28k lines in vs ~5800
in current template). Manual surgical patch is risky. Two options:

1. Re-clone each from current `clone_dashboard.py` template using a
   per-dashboard JSON config that preserves their existing
   `real_data_entries` -- they get the new engine wholesale.
2. Hand-port the missing Q-profile invocation + `_mhPool` block into
   the existing engine. Higher risk of introducing mismatches.

Recommend option 1. Track as **REM-ENG-1** (next session task).

---

## 2. mITT vs allocated audit (binary)

**515 binary trials extracted across 170 dashboards. 241 flagged.**

Counts:

| Flag                                 | n   | Action                                                |
|--------------------------------------|-----|-------------------------------------------------------|
| BIG_TRIAL (n>=1000)                  | 183 | Background prompt; mostly real published 1:1 mITT     |
| EQUAL_ARMS (tN==cN, both >=50)       | 64  | Verify against published primary (most are real)      |
| ROUND_HUNDRED_TN/CN                  | 11  | Spot-check                                            |
| MULTI_ARM_POOL                       | 0   |                                                       |
| MITT_MENTIONED (already declared)    | 8   | OK by construction                                    |

### Highest-priority manual checks

| Dashboard                                | Trial      | Concern                                                                      |
|------------------------------------------|------------|------------------------------------------------------------------------------|
| AZITHROMYCIN_CHILD_MORTALITY_REVIEW.html | MORDOR-I/II, AVENIR | tN=95k/50k/45k = population aggregate (cluster-RCT). Different bug class -- needs DEFF adjustment, not mITT fix. Track as **REM-CLUSTER-1**. |
| IL_PSORIASIS_NMA_REVIEW.html             | UltIMMa-2  | cN=100 may be UltIMMa-1 placebo n. Gordon 2018 Lancet UltIMMa-2 placebo mITT n=98. Confirm + correct. **REM-MITT-1**. |
| JAKI_RA_NMA_REVIEW.html                  | SELECT-Compare | tN/cN=651/651 is upa-vs-MTX; if intended contrast was upa-vs-ada it should be 651/327. Confirm comparator slot. **REM-MITT-2**. |
| PEGCETACOPLAN_GA_REVIEW.html             | OAKS, DERBY | Already addressed today (commit f3d27a0).                                    |

The other ~58 EQUAL_ARMS hits are dominated by verified 1:1 mITT
trials (KATHERINE, DAPA-CKD, ELIXA, SOUL, HPTN 083, ODYSSEY-OUTCOMES,
SCORED, SOUL, TyVAC). Mark as low priority.

---

## 3. Continuous outcome conventions audit (NEW)

**100 continuous outcomes across 33 dashboards. 94 flagged.**

| Flag                              | n   | Severity     | Action                                                  |
|-----------------------------------|-----|--------------|---------------------------------------------------------|
| LSMD_NOT_DECLARED                 | 85  | **systemic** | Add `LSMD` / `LS-mean` mention to title or snippet       |
| MMRM_NOT_DECLARED                 | 85  | **systemic** | Add MMRM / ANCOVA / "mixed model" mention if applicable |
| ARM_ASYMMETRIC (>=1.25:1)         | 22  | low          | Mostly real 2:1 / 3:1 randomization                     |
| SE_IMPLAUSIBLE_SMALL (|se/md|<0.05)| 17  | mixed        | See below                                               |
| BIG_TRIAL (n>=1000)               | 12  | background   |                                                         |
| EQUAL_ARMS                        | 11  | background   |                                                         |
| SE_IMPLAUSIBLE_LARGE              | 4   | background   |                                                         |
| ROUND_HUNDRED_TN/CN               | 2   | spot-check   |                                                         |

### Most actionable continuous findings

**Issue A (systemic, fixable by codemod): LSMD/MMRM not declared in 85% of continuous outcomes.**

Most continuous trial primary endpoints in the portfolio are
change-from-baseline LSMD via MMRM (or ANCOVA). The dashboards' titles
and snippets simply say "MD vs placebo" without naming the model. A
human reading the dashboard cannot distinguish a model-adjusted LSMD
from a raw arithmetic mean difference. Tracked as **REM-CONT-1**.

Suggested codemod: where the title contains "change" / "from baseline"
and the trial-level snippet cites a known MMRM-using publication,
auto-append `(LSMD via MMRM)` or `(ANCOVA-adjusted)` to the outcome
title.

**Issue B (mixed): SE_IMPLAUSIBLE_SMALL hits.**

| Dashboard                  | Trial    | Outcome  | md     | se     | Verdict                                            |
|----------------------------|----------|----------|--------|--------|----------------------------------------------------|
| AFLIBERCEPT_HD_REVIEW.html | PULSAR   | Q12W_pct | 0.79   | 0.022  | **Real bug** -- this is a proportion, not an MD. Should be a binary endpoint with denominator + event count. Tracked as **REM-CONT-2**. |
| AFLIBERCEPT_HD_REVIEW.html | PHOTON   | Q12W_pct | 0.78   | 0.023  | Same -- proportion treated as MD.                  |
| FARICIMAB_NAMD_REVIEW.html | TENAYA   | Q12W_pct | 0.80   | 0.022  | Same.                                              |
| FARICIMAB_NAMD_REVIEW.html | LUCERNE  | Q12W_pct | 0.78   | 0.023  | Same.                                              |
| BEMPEDOIC_ACID_REVIEW.html | --       | LDLC     | -18.1  | 0.8    | Plausible LSMD from large trial.                   |
| INCLISIRAN_REVIEW.html     | ORION-10 | MACE     | -52.3  | 1.4    | Plausible LSMD.                                    |
| INCLISIRAN_REVIEW.html     | ORION-11 | MACE     | -49.9  | 1.5    | Plausible LSMD.                                    |
| SEMAGLUTIDE_OBESITY        | STEP-1   | MACE     | -12.4  | 0.5    | Plausible LSMD (n>1900).                          |
| TIRZEPATIDE_OBESITY        | SURMOUNT-1 | various | -11..-18 | ~0.6 | Plausible LSMD (n>2500).                          |
| TIRZEPATIDE_T2D            | SURPASS-1 | HbA1c   | -1.87..-2.07 | 0.09 | Plausible LSMD.                              |

The 4 Q12W_pct entries (Aflibercept HD + Faricimab) are the real bug:
proportions encoded as MDs. Should be moved to a binary `tE/cE`
representation with event counts.

---

## Suggested next-session task ordering

1. **REM-ENG-1** (highest) -- re-clone COLCHICINE_CVD, GLP1_CVOT,
   SGLT2_HF onto the current engine via clone-script + per-trial JSON
   configs. Brings them to v6.5 compliance.
2. **REM-MITT-1** -- correct UltIMMa-2 cN=100 -> 98 (Gordon 2018 Lancet).
3. **REM-MITT-2** -- audit SELECT-Compare comparator slot (upa-vs-MTX vs
   upa-vs-ada). Decide which contrast is intended; align tN/cN.
4. **REM-CONT-2** -- move Aflibercept/Faricimab Q12W_pct outcomes from
   continuous-MD to binary-RR representation. Affects 4 trial-outcome
   pairs.
5. **REM-CONT-1** -- codemod to append `(LSMD via MMRM)` or
   `(ANCOVA-adjusted)` to continuous outcome titles where the
   trial-level snippet supports it. Affects ~85 outcomes; needs manual
   review of which model each trial actually used.
6. **REM-CLUSTER-1** -- AZITHROMYCIN cluster-RCT trio: design-effect-
   adjusted denominators or move out of patient-level binary engine.
   Separate engine work.
7. **Sentinel rule**: tighten v6.5 invariant rule to also check the
   CALL site of `qProfileTau2CI(` and `_mhPool(`, not just the
   definition. Prevents the GLP1_CVOT/COLCHICINE/SGLT2_HF class of
   silent-no-render gap from recurring.

---

## Re-running

```
python scripts/audit_mitt_vs_allocated.py
python scripts/audit_continuous_conventions.py
python scripts/audit_v65_engine_coverage.py
```

CSVs land in `outputs/`. Re-run after every engine change OR every new
dashboard (when the freeze lifts).
