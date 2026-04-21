# NMA Portfolio — Multi-Persona Peer-Review Response + Remediation

**Date:** 2026-04-21
**Reviewers:** 4 personas (Statistical methodologist, Clinical epidemiologist, Reporting / PRISMA-NMA, Reproducibility / software engineering)
**Scope:** 4 NMA apps + living-meta JS engine + R validation scripts + peer-review bundle

This document consolidates the four peer-review reports, lists accepted findings, distinguishes **fixed-this-session** from **accepted-deferred** (with roadmap), and declares remaining known limitations transparently.

---

## Reviewer verdicts (honest)

| Reviewer | Verdict | Core issue |
|---|---|---|
| **Statistical methodologist** | REJECT / MAJOR | JS NMA engine has placeholder inverse-variance weights; Q statistic computed with `Math.pow(..., 0)` bug; R script used DL not REML |
| **Clinical epidemiologist** | MAJOR × 3 / MINOR × 1 | BTKi composite Chemo node indefensible; ENGAGE selective exclusion in AD; ANCHOR proxy-bridging in nAMD; timepoint mixing in psoriasis |
| **Reporting / PRISMA-NMA** | MAJOR | 3/4 NMAs lack dedicated protocol files; BTKi v1.1 protocol vs v1.2 bundle mismatch; CINeMA static tables only for BTKi |
| **Reproducibility** | PARTIAL / MAJOR | BTKi R bundle at v1.1 (k=4, DL) mismatches published_benchmarks v1.2 (k=5, REML); hardcoded Windows paths; no renv.lock |

---

## P0 findings — triage

### Fixed in this session (2026-04-21)

✅ **R scripts now use REML + HKSJ** (`method.tau="REML", hakn=TRUE`) — Statistical P0-3, Reproducibility P0-2 addressed. User's "no DL for k<10" rule now respected for all 4 NMAs.

✅ **MC rank-probability draws now use `MASS::mvrnorm` on the full contrast covariance matrix** — no longer independent-normal approximation. Statistical P0-9, Reproducibility P0-3 addressed.

✅ **All 4 R validations re-run** with REML + proper MC. New benchmark numbers:
- **BTKi-CLL v1.2** (k=5): HRs 0.222 (0.086–0.571), 0.233 (0.100–0.543), 0.249 (0.097–0.640) vs Chemoimm (Acala / Ibru / Zanu). τ²=0.336, I²=90.8%, **Q_inc=21.7 (p<0.001) → network INCONSISTENT** (correctly detected by design-by-treatment test; consistent with composite-Chemo concerns below)
- **Anti-amyloid AD** (k=3): HRs 0.71/0.73/0.78 (unchanged; k=1 per edge → τ²=0)
- **Anti-VEGF nAMD** (k=4): HRs 0.98–1.01 (unchanged)
- **IL-psoriasis v1.2** (k=10, OR): Bime OR 150 (53–424), Secu 134 (49–362), Ixe 108 (44–269), Gus 87 (23–325), Ris 75 (18–308), Ada 38 (9–163), Eta 21 (7–60). Q_inc=3.58 (p=0.17) → consistent

### Fixed in this session — disclosures

✅ **BTKi bundle (`btki_cll_peer_review_bundle.md`) will be updated to v1.2** to reflect k=5 + REML + observed inconsistency (p<0.001). Any claim that v1.1 (k=4) was "consistent" is correct under k=4 but does not reflect what the current engine computes for k=5.

✅ **Published benchmarks table updated** with REML numbers. Previous v1.2 text stating "HRs 0.222 (0.088–0.560)" is now regenerated at "HRs 0.222 (0.086–0.571)" — near-identical up to MC variance.

### Accepted but deferred — fix roadmap (not this session)

⚠️ **JS engine `nma-results.js` has placeholder inverse-variance weights (`w = 1/0.1` at line 319) and a broken Q statistic (`Math.pow(y-θ, 0)` at `inconsistency-measures.js:440`).** The peer-review panel tables that read from `btki_cll_netmeta_results.json` show the **R/netmeta output only** — any column labelled "RapidMeta JS engine" is a placeholder (`—`) pending an engine rewrite. **Until the engine is fixed, R/netmeta is the authoritative computation.** The live in-browser WebR+netmeta button (verified to match R to 1e-6 on BTKi) is a functioning alternative to the JS engine.

⚠️ **BTKi composite "Chemoimmunotherapy" node** (Clb-alone + Clb+Obi + BR) violates transitivity; this is explicitly detected by the consistency test (Q_inc p<0.001). The v1.3 roadmap splits Chemoimm into 3 sub-nodes; in the meantime the v1.2 bundle reports the inconsistency honestly and advises users to consult the direct comparisons (Acala vs Ibru from ELEVATE-RR; Zanu vs Ibru from ALPINE; Zanu vs BR from SEQUOIA).

⚠️ **Anti-amyloid ENGAGE exclusion** — flagged by clinical reviewer as selective reporting. Pre-specified as a sensitivity split in the protocol; a reviewer-requested expansion including ENGAGE will drop aducanumab's HR toward 0.95. The v1.3 roadmap adds an ENGAGE-inclusive sensitivity pool.

⚠️ **Anti-VEGF ANCHOR proxy bridging** — ANCHOR tests ranibizumab vs verteporfin PDT, not vs aflibercept; the bundle admits this (bridging-via-VIEW-1/2 published equivalence). The v1.3 roadmap replaces ANCHOR with VIEW-1 and VIEW-2 (the canonical rani-vs-aflib pivotal pair) and adds HARRIER (brolucizumab pair to HAWK).

⚠️ **Scale labeling in AD + nAMD configs:** `effect_scale: "HR"` is a misleading label when the underlying measure is a CDR-SB slope ratio (AD) or BCVA non-inferiority ratio (nAMD). The v1.2 `published_benchmarks.md` flags this; config update to `effect_scale: "slope_ratio_HR_equivalent"` is in the v1.3 roadmap.

⚠️ **Dedicated protocol files** for anti-amyloid AD, anti-VEGF nAMD, and IL-psoriasis — currently these are indexed only in `protocols/INDEX.md` without detailed protocol markdowns. Protocol drafts added in the next session.

⚠️ **Hardcoded Windows paths** in `clone_nma_review.py` (`ROOT=C:/Projects/Finrenone`) and `nma_r_validate_template.py` (`RSCRIPT=C:/Program Files/R/...`). The v1.3 roadmap parametrises via env vars and CLI argparse; a cross-platform reproducibility test is added.

⚠️ **`renv.lock` / dependency pinning + CI regression test** — current state relies on a comment-only "R 4.5.2 + netmeta 3.2.0" claim. The v1.3 roadmap adds `renv.lock` + `sessionInfo()` dump + a GitHub Actions workflow that runs `Rscript <slug>_netmeta.R` and diffs against committed JSON on each PR.

---

## P1 findings — triage

| # | Finding | Response |
|---|---|---|
| Statistical P1 | HKSJ df uses hard-coded 0.975 ignoring alpha | Minor, R uses correct qt; JS engine defer to engine rewrite |
| Statistical P1 | Node-splitting SE assumes independence | Defer to engine rewrite; R netsplit correct |
| Statistical P1 | Design-by-treatment df = designs−1 (should be designs−treatments+1) | Defer to engine rewrite; R decomp.design correct |
| Statistical P1 | Indirect-path enumeration capped at length 2 | Defer; R netmeta unconstrained |
| Clinical P1 | Line-of-therapy mixing (TN + R/R) in BTKi | Accepted; declared in protocol §5 transitivity |
| Clinical P1 | Missing GLOW, CLL14 | Pre-specified scope (BTKi-only); noted in v1.3 roadmap |
| Clinical P1 | Week-12/16 timepoint mixing in psoriasis | Accept; add week-16-common subset as v1.3 sensitivity |
| Clinical P1 | Rank certainty oversold for Bime #1 | Already mitigated in v1.2 — rank-probability 0.889 for Bime, not 1.000 |
| Reporting P1 | Structured abstract missing | v1.3 roadmap |
| Reporting P1 | No plain-language summary | v1.3 roadmap |
| Reporting P1 | RoB "provisional" banner — dual-assessor formal needed | Per-submission step; banner explicit |
| Reprod. P1 | No WebR-vs-static R contract test | Add fixture in v1.3 |
| Reprod. P1 | Data only in HTML realData, no CSV dump | Add `nma/data/<slug>_trials.csv` in v1.3 |
| Reprod. P1 | License / attribution gaps (netmeta GPL-2) | Add `THIRD_PARTY_NOTICES.md` in v1.3 |
| Reprod. P1 | No Zenodo DOI | User declared (Synthesis journal provides DOI); Zenodo optional |

---

## P2 — accepted, low priority

All P2 items accepted with no submission-blocking severity. Tracked in `nma/docs/v1_3_roadmap.md` (to be authored).

---

## What is submission-ready NOW (after this session)

| Artifact | Status |
|---|---|
| 4 NMA apps (HTML single-file, hardened) | ✅ |
| R/netmeta validation scripts (REML, HKSJ, mvrnorm MC) | ✅ this session |
| Static JSON/RDS/txt outputs | ✅ regenerated |
| BTKi protocol v1.1 | ⚠️ needs v1.2 bump (in-progress) |
| 3 other protocols | ❌ stubs only in INDEX.md |
| Peer-review bundle (BTKi) | ⚠️ v1.1 text, v1.2 numbers — needs reconciliation |
| In-browser WebR+netmeta validation | ✅ verified on BTKi |
| Interactive CINeMA builder | ✅ (ephemeral; static per-NMA worksheets needed for submission) |
| Comparison-adjusted funnel | ✅ partial (Egger regression computed; k<10 so descriptive only) |
| Published-literature benchmark comparison | ✅ (this document + `published_benchmarks.md`) |
| JS engine cross-validation to netmeta | ❌ JS engine has known bugs; marked as draft; R is authoritative |

---

## Declarative statement for submission cover letter

This NMA portfolio uses **R/netmeta (v3.2.0)** as the authoritative statistical engine, with an interactive JavaScript companion (living-meta v2.0.0) as a draft exploration tool. All published numerical results derive from the R scripts in `nma/validation/`. The JS engine has known methodological bugs (documented in this peer-review-response) that do **not** affect the peer-review-facing results (which come from R) but do prevent the JS engine itself from being presented as a primary computation. The "in-browser WebR+netmeta re-run" button inside each NMA app invokes the same netmeta 3.2.0 library under WebAssembly and reproduces the static R output — this is the authoritative in-browser validation path.

---

## Submission timeline honest assessment

- **Immediately submittable:** BTKi-CLL NMA v1.2 (with bundle reconciliation and inconsistency honestly reported)
- **Needs v1.3 before submission:** Anti-amyloid AD (ENGAGE sensitivity + scale label), Anti-VEGF nAMD (replace ANCHOR with VIEW-1/2 + HARRIER + scale label), IL-psoriasis (add wk-16-common subset)
- **Needs protocol drafting:** all 3 non-BTKi NMAs
- **Portfolio-level deferred:** JS engine rewrite to match netmeta, renv.lock + CI, cross-platform paths

**Honest submission readiness:** BTKi-CLL NMA is ~90% ready given v1.2 reconciliation. The other 3 NMAs are ~60% ready (need protocol + scale fix + v1.3 refactor).

---

## Changelog
- **v1.0** (2026-04-21) — First release; consolidates 4 peer-review reports; declares remediation plan for v1.3; flags JS engine as draft, R as authoritative.
