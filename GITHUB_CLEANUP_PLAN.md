<!-- sentinel:skip-file — this doc literally enumerates local C:\Projects\*_LivingMeta paths as data describing where each excluded sibling repo lives. The paths ARE the documentation, not hardcoded code. -->

# GitHub Cleanup Plan — 8 EXCLUDED_APPS Sibling Repos

> Generated 2026-04-16 alongside QUALITY_GATE v1.1 enforcement.
> These 8 sibling repos host apps that were removed from active portfolio scope because they have <2 published RCTs in the same disease/outcome — i.e. they are not meta-analyses by the v1.1 definition.
> The validator's `EXCLUDED_APPS` set already keeps them out of portfolio scans. This document is for **deciding what to do with the GitHub repos themselves**.
>
> **No action is taken by this document.** It enumerates options + provides commands for the option you choose. Run nothing without reviewing the blast radius first.

---

## The 8 repos

| # | Repo (GitHub) | Local dir | Why excluded | Re-admission gate |
|---|---------------|-----------|--------------|-------------------|
| 1 | [Coronary-IVL-LivingMeta](https://github.com/mahmood726-cyber/Coronary-IVL-LivingMeta) | `C:\Projects\Coronary_IVL_LivingMeta\` | k=0 — Disrupt CAD III/IV are single-arm IDE (not RCT) | Wait for ISAR-WAVE / DECALCIFY / China RCT publications (~2025-27) |
| 2 | [orforglipron-livingmeta](https://github.com/mahmood726-cyber/orforglipron-livingmeta) | `C:\Projects\Orforglipron_LivingMeta\` | k=0 — Phase 2 only | Wait for ACHIEVE-1/3/4 + ATTAIN-1/2 publications (2025-26) |
| 3 | [Empa_MI_LivingMeta](https://github.com/mahmood726-cyber/Empa_MI_LivingMeta) | `C:\Projects\Empa_MI_LivingMeta\` | k=1 effective — only EMPACT-MI has clinical HR; EMMY (NT-proBNP) + EMPRESS-MI (LV volumes) are imaging/biomarker | Re-admit if a 2nd clinical-outcome SGLT2-post-MI RCT publishes |
| 4 | [Iptacopan_LivingMeta](https://github.com/mahmood726-cyber/Iptacopan_LivingMeta) | `C:\Projects\Iptacopan_LivingMeta\` | k=1 — APPLY-PNH is the only PNH RCT. APPLAUSE-IgAN exists but is a different disease (cannot pool across diseases) | Re-admit if a 2nd PNH iptacopan RCT publishes (e.g. APPOINT-PNH) |
| 5 | [Leadless-Pacing-LivingMeta](https://github.com/mahmood726-cyber/Leadless-Pacing-LivingMeta) | `C:\Projects\Leadless_Pacing_LivingMeta\` | k=1 — Micra/Aveir are single-arm pivotal IDEs vs historical controls, not RCTs | Re-admit when a head-to-head leadless-vs-transvenous RCT publishes (Leadless AV vs DDD trial 2026) |
| 6 | [Semaglutide_CKD_LivingMeta](https://github.com/mahmood726-cyber/Semaglutide_CKD_LivingMeta) | `C:\Projects\Semaglutide_CKD_LivingMeta\` | k=1 — FLOW only; REMODEL is bone-density, not CV/kidney outcome | Re-admit when a 2nd kidney-outcome semaglutide RCT publishes |
| 7 | [Sparsentan_IgAN_LivingMeta](https://github.com/mahmood726-cyber/Sparsentan_IgAN_LivingMeta) | `C:\Projects\Sparsentan_IgAN_LivingMeta\` | k=1 — PROTECT only; DUET was phase 2 | Re-admit when a 2nd phase 3 sparsentan IgAN RCT publishes |
| 8 | [Tricuspid-TEER-LivingMeta](https://github.com/mahmood726-cyber/Tricuspid-TEER-LivingMeta) | `C:\Projects\Tricuspid_TEER_LivingMeta\` | k=1 — TRILUMINATE Pivotal only RCT; CLASP-TR / bRIGHT are single-arm/registry | Re-admit when a 2nd tricuspid-TEER RCT publishes (TriCLASP, TRISCEND II, TRILUMINATE Long-Term) |

---

## Three options per repo

Pick one option per repo (or one for all).

### Option A — Archive (recommended default)

Keep the repo on GitHub. Add a deprecation banner so anyone landing on it understands current status. Pages stays live (preserves any URL citations in submitted papers).

**Blast radius**: low. Reversible. Citations and inbound links remain valid.

**Per-repo commands** (substitute `<repo>` and run from each repo dir):
```bash
# 1. Add banner to README.md and HTML <title>:
gh repo edit <user>/<repo> --description "DEPRECATED 2026-04-16: <1-line reason>. Out of portfolio per QUALITY_GATE v1.1."

# 2. Optional: archive the repo (read-only, can be unarchived):
gh repo archive <user>/<repo> --yes

# 3. Optional: add a DEPRECATED.md banner file:
cat > DEPRECATED.md <<EOF
# DEPRECATED 2026-04-16

This app has been removed from the active RapidMeta Living MA Portfolio
because it has fewer than 2 published RCTs in the same disease and outcome
(QUALITY_GATE v1.1 — see Finrenone repo).

The HTML and Pages site are retained for archival reference only.
Re-admission requires a second qualifying RCT publication.
EOF
git add DEPRECATED.md && git commit -m "docs: deprecate per QUALITY_GATE v1.1" && git push
```

### Option B — Delete (irreversible)

Remove the repo from GitHub entirely. **WARNING**: any inbound link, citation, Zenodo DOI, or workbook reference becomes a 404. Cannot be undone.

**Blast radius**: high. Pre-flight check before running:
```bash
# Check for inbound references to the repo:
gh search code --owner mahmood726-cyber "<repo-name>"  # in your own code
# Manually search submitted papers, INDEX.md, push_all_repos.py, workbook
```

**Command**:
```bash
gh repo delete <user>/<repo> --yes
```

### Option C — Convert to "Single-Trial Evidence Review"

Keep the repo, but rename headers/title from "Meta-Analysis" → "Single-Trial Evidence Review" so it's honestly framed. Re-add to portfolio under a separate, clearly-labeled cohort.

**Blast radius**: medium. Requires HTML edits + workbook entry update + `EXCLUDED_APPS` removal in validator. Not recommended unless the single-trial review has standalone value (e.g. educational dashboard for a landmark trial like FLOW or PROTECT).

**Per-repo work**: HTML title + h2 header rewrite + add `<!-- single-trial-review -->` marker; remove from validator's `EXCLUDED_APPS`; add a new `SINGLE_TRIAL_REVIEWS` set in validator that exempts those apps from Gate 1.

---

## Recommendation per repo

| # | Repo | My recommendation | Why |
|---|------|-------------------|-----|
| 1 | Coronary-IVL | **A** (archive, banner) | Future RCTs imminent; preserve repo for re-admission |
| 2 | Orforglipron | **A** | Phase 3 read-out 2025-26; will likely re-admit |
| 3 | Empa_MI | **C** (single-trial review) | EMPACT-MI is a landmark RCT worth a standalone dashboard |
| 4 | Iptacopan | **C** | APPLY-PNH is a landmark single trial in PNH |
| 5 | Leadless-Pacing | **A** | Comparative RCT pending 2026 |
| 6 | Semaglutide_CKD | **C** | FLOW is a landmark trial, standalone review valuable |
| 7 | Sparsentan_IgAN | **A** | Limited audience; archive until 2nd RCT |
| 8 | Tricuspid-TEER | **A** | TRILUMINATE long-term + 2nd RCTs pending |

**Net**: 5 archive (A), 3 single-trial review (C), 0 delete (B). No irreversible actions.

---

## Execution checklist (per chosen option)

For each repo you decide to act on:

- [ ] **Option A (archive)**:
  - [ ] `gh repo edit` description with deprecation note
  - [ ] Add `DEPRECATED.md` to repo root
  - [ ] Commit + push
  - [ ] (Optional) `gh repo archive` to make read-only
  - [ ] Update `C:\ProjectIndex\INDEX.md` to mark as ARCHIVED
  - [ ] Update workbook entry (preserve YOUR REWRITE per `e156.md` rule)

- [ ] **Option C (single-trial review)**:
  - [ ] Rename HTML `<title>` and h2 header from "Meta-Analysis" → "Single-Trial Evidence Review"
  - [ ] Add `<!-- single-trial-review -->` HTML comment near top
  - [ ] Remove app from `EXCLUDED_APPS` in `validate_living_ma_portfolio.py`
  - [ ] Add app to a new `SINGLE_TRIAL_REVIEWS` set (gate exemption per QUALITY_GATE v1.1 edge case)
  - [ ] Update `INDEX.md` to mark as "Single-Trial Review" tier
  - [ ] Update workbook entry to reflect single-trial framing

- [ ] **Option B (delete)** — only if absolutely sure:
  - [ ] Pre-flight: `gh search code` + manual citation audit
  - [ ] `gh repo delete --yes`
  - [ ] Remove from `INDEX.md`, `push_all_repos.py`, workbook (CURRENT BODY only; preserve YOUR REWRITE)
  - [ ] Document deletion in `C:\ProjectIndex\STUCK_FAILURES.md` for audit trail

---

## Validator-side: already done

`validate_living_ma_portfolio.py` already excludes all 8 apps from portfolio scans via `EXCLUDED_APPS` (commit `fabca51`, `3c3xxxxx`). No code changes needed regardless of which GitHub option you pick.

If you do (C) for any repo, that app goes back into scans — remove from `EXCLUDED_APPS` and add to `SINGLE_TRIAL_REVIEWS` in the same edit.

## Re-admission flow

When a 2nd qualifying RCT publishes for any of these:
1. Update the app's HTML with the new trial in `realData`
2. Run `validate_living_ma_portfolio.py --gate` and confirm pool computes
3. Remove the app from `EXCLUDED_APPS` in the validator
4. Add a benchmark entry to `BENCHMARKS` dict
5. Commit + push to both the sibling repo AND Finrenone
6. Update `INDEX.md` to mark as ACTIVE again

The validator will then include it in the portfolio scan automatically.
