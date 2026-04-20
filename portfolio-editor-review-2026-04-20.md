# Journal-Editor Multi-Persona Review — RapidMeta 41-App Portfolio

**Date:** 2026-04-20
**Reviewed:** 41 living meta-analysis apps, 41 protocols, `PUBLISHED_META_BENCHMARKS.json`, `v2_selfcheck_report.md`, `index.html`
**Perspective:** What would a journal editor (JAMA / NEJM / BMJ / J Clin Epidemiol / Research Synthesis Methods) flag if this portfolio were submitted today?
**Personas:** Statistical Editor, Clinical/Methods Editor, Reporting Guidelines Editor, Ethics/Reproducibility Editor, Peer-Review Gatekeeper
**Summary:** 8 P0 (blockers before submission) · 12 P1 (reviewer-will-flag) · 6 P2 (polish)

## Status update — 2026-04-20 fix pass

- **[FIXED] P0-3 / P1-10** — `benchmark_type` and `pool_type` added to all 41 entries in `PUBLISHED_META_BENCHMARKS.json`. Distribution: `external_IPD`=4, `external_aggregate`=7, `self_reference`=30; `same_drug`=15, `class_level`=26. `v2_selfcheck_report.md` rewritten to separate intra-app V2-regex agreement from external-benchmark validation.
- **[FIXED] P0-4** — "PROSPERO-style" phrasing removed from all 41 protocols; replaced with explicit "GitHub-canonical-URL freeze" mechanism + honest comparison to PROSPERO + instruction for authors targeting PROSPERO-required journals.
- **[FIXED] P0-5** — CART_MM protocol §8 rewritten: fixed-effect IVW as primary at k=2; DL-HKSJ and Bayesian half-normal(0, 0.5) prior as sensitivity pools; primary switches to DL-HKSJ once k>=3.
- **[FIXED] P0-6 (banner)** — All 41 apps now display a "Provisional RoB-2 and GRADE — AI-drafted from the record excerpts; authors confirm each domain against those excerpts before submission" banner in the Extraction tab. The formal dual-assessor RoB-2 requirement for the demonstrator set remains P1 work (see below).
- **[FIXED] P0-7** — MA left the Synthēsis editorial board on 2026-04-20. Editorial-board COI retired across E156 infrastructure. Middle-author rule still in force on CRediT grounds. Memory updated.
- **[FIXED] P0-8 (indirectness flag)** — Every `pool_type: "class_level"` entry now carries `indirectness_note` in the JSON that pre-specifies GRADE indirectness as `serious` unless a within-agent subgroup analysis confirms homogeneity. GRADE-profile display auto-downgrade for class pools remains a UI implementation task (still P2).

Still open after the 2026-04-20 pass:

- **P0-1 / P0-2** — Publication strategy decision (framework paper + 4-6 demonstrators). User decision required.
- **P0-6 (formal RoB-2)** — Dual-assessor formal RoB-2 with kappa for the demonstrator set. Banner is now honest; the formal assessment is still needed.
- **P1-2** — AMSTAR-2 appendix (either complete for demonstrators or remove the promise).
- **P1-6 / P1-8** — R/Python export reproducibility and PRISMA-2020 checklist export verification.
- **P1-11** — N-randomized CONSORT verification spot-check.

---

## P0 — Blockers before submission

### P0-1 [Peer-Review Gatekeeper] Scope is wrong for a single manuscript
41 living meta-analyses cannot be a single paper. Split into:
- **Framework paper** (Research Synthesis Methods / J Clin Epidemiol): "RapidMeta: a browser-hosted living meta-analysis framework with frozen protocol + CT.gov auto-sync + V2 regex verification" — portfolio as proof-of-concept.
- **4–6 demonstrator living MAs** as individual submissions to topic journals (Cochrane Living, BMJ, JAMA specialty journals). Pick the ones with genuine external benchmarks: DOAC-AF, SGLT2-HF, PCSK9, GLP1-CVOT, Finerenone.
- **Do not** submit 41 pools as 41 papers — looks like salami and will be rejected at triage.
**Fix:** decide publication strategy before the next writing push.

### P0-2 [Peer-Review Gatekeeper] Framing must lead with the framework, not the pools
Most individual pools overlap with existing Cochrane / network MAs (IL-23 psoriasis, JAK-UC, dupilumab-AD, CFTR-CF, DOAC-AF, SGLT2-HF). Novelty is the **framework** (living + frozen protocol + auto-sync + V2 regex two-source verification), not the pool values. Current landing-page copy buries this.
**Fix:** rewrite the portfolio abstract and framework paper to lead with methods novelty. The pools are demonstrators.

### P0-3 [Statistical Editor] "Internal DL pool as benchmark" is circular for methodological validation
~14 of 41 benchmarks cite the app's own DL random-effects pool as the reference (DOAC_AF is external; Tirzepatide, IL-23, Semaglutide, CAR-T, Romosozumab, COPD-Triple, Dupilumab-AD, High-Efficacy-MS, Risankizumab-CD, RSV-Vaccine are internal). An "EXACT" match to the app's own computation is a tautology, not a validation.
**Fix:** relabel these entries as `benchmark_type: "self_reference"` in the JSON and exclude them from the `n_EXACT/n_total` agreement statistic reported in `v2_selfcheck_report.md`. Recompute true-benchmark agreement (trials with an external IPD MA or published network MA). This currently overstates the portfolio's cross-validation claim.

### P0-4 [Reporting Guidelines Editor] Not PROSPERO-registered despite "PROSPERO-style" framing
All 41 protocols self-describe as "PROSPERO-style." Peer reviewers will ask: *was it submitted?* PROSPERO does not accept post-hoc registrations and the canonical-URL GitHub freeze is not a substitute.
**Fix:** either (a) submit protocols to PROSPERO before journal submission (their "Living SR" registration path exists), or (b) remove "PROSPERO-style" phrasing and describe the GitHub freeze as an *alternative* pre-registration mechanism with a frank comparison to PROSPERO. Do not claim PROSPERO equivalence.

### P0-5 [Statistical Editor] k=2 analyses need explicit method adjustment (CART_MM)
`CART_MM_REVIEW` has k=2 (CARTITUDE-4 + KarMMa-3). Problems at k=2:
- HKSJ with df=k−1=1 inflates the CI to near-infinity if Q>df. The protocol says HKSJ; the app's output "0.55 (0.35–0.84)" looks finite, so either HKSJ isn't actually applied at k=2 or the floor `max(1, Q/(k-1))` is masking something.
- DL τ² is unreliable at k=2.
- PI is undefined (protocol already notes this).
**Fix:** (a) make fixed-effect the primary pool at k=2 with DL as sensitivity, (b) document the HKSJ floor behavior explicitly in the Methods, (c) add a Bayesian half-normal-prior(0.5) sensitivity pool that gives stable CI at k=2.

### P0-6 [Ethics/Reproducibility Editor] RoB-2 is labeled "design-based priors pending formal assessment"
Every app ships with a visible banner saying ratings are "design-based priors" not formal RoB-2 by trained assessors. This propagates into GRADE, which downgrades for risk of bias — so every GRADE profile is also provisional. You cannot submit a meta-analysis with provisional RoB to a peer-reviewed journal.
**Fix:** complete formal dual-assessor RoB-2 with documented disagreements + inter-rater kappa for at least the demonstrator trials (4-6 topics). For the rest, explicitly label them "screening-only, full RoB-2 pending" and keep them out of the submission package.

### P0-7 [Ethics/Reproducibility Editor] Editorial-board COI not stated in protocols
Per the user's standing rule (`feedback_e156_authorship.md`): MA carries editorial-board COI for Synthesis submissions; MA is never first/last on Synthesis papers; explicit "no role in editorial decisions" disclosure required. Current protocols say only "None declared for the corresponding author." If any of these 41 MAs target Synthesis — or any journal where MA sits on the board — this is a disclosure failure.
**Fix:** audit target journals, add topic-specific COI statements to the protocols of those meant for Synthesis or other conflicted venues. Use the exact Synthesis name with macron (`Synthēsis`).

### P0-8 [Clinical/Methods Editor] Same-drug vs class-level pools must be distinguished
Some pools are same-drug (SURPASS all tirzepatide; SOLO/CHRONOS all dupilumab; STEP all semaglutide; ORION all inclisiran) — defensible. Others are cross-agent class pools:
- **IL-23 psoriasis** (3 different agents: guselkumab/risankizumab/tildrakizumab)
- **DOAC-AF** (4 different drugs at different doses)
- **Anti-CD20 MS** (ocrelizumab vs ofatumumab with different platform comparators)
- **CAR-T MM** (cilta-cel vs ide-cel at different line strata)
- **IV iron HF**, **ATTR-CM**, **Biologic asthma** (mixed targets)

Journal editors will require **pre-specified indirectness downgrade** in GRADE for all class-level pools, and a statement of the class-effect assumption.
**Fix:** add `pool_type: same_drug | class_level` to the benchmark JSON. For class-level pools: add an "indirectness: serious" downgrade in the default GRADE profile and document the class-effect assumption in the protocol's Synthesis section.

---

## P1 — Reviewer will flag; should address

### P1-1 [Clinical/Methods Editor] Comparator heterogeneity inside single pools
- **Tirzepatide T2D** mixes placebo-controlled (SURPASS-1, -5 at MD -2.11 and -1.66) with active-controlled (SURPASS-3 vs insulin degludec, MD -1.04). The "effect" against placebo and against an active comparator is not the same estimand. Current method note acknowledges this; quantify with a pre-specified subgroup analysis.
- **Semaglutide STEP** mixes monotherapy (STEP-1) with IBT concurrent (STEP-3); concurrent IBT inflates placebo-arm response and compresses ETD. Subgroup by IBT status.
- **Anti-CD20 MS** mixes IFN-beta-1a comparator (OPERA) with teriflunomide (ASCLEPIOS). Different active comparators ≠ same estimand.
- **Risankizumab CD** pools induction (12 wk) with maintenance (52 wk) — different trial phases.

**Fix:** add formal subgroup / meta-regression on comparator or trial phase in the SAP for each affected app, and report the within-subgroup pool as primary where comparator heterogeneity is mechanistic.

### P1-2 [Reporting Guidelines Editor] AMSTAR-2 appendix is a visible TODO on all 41 protocols
Every protocol ends with "AMSTAR-2 appendix under development." This is a visible promised-but-not-delivered item that every peer reviewer will flag.
**Fix:** either complete AMSTAR-2 (the critical-domain subset is ~8 items per MA, 1-2 hours per app) or remove the promise entirely. Deliver what is promised or don't promise it.

### P1-3 [Statistical Editor] Zero-cell handling is not operationalised
Protocol says "0.5 continuity correction when ≥1 cell is zero." Per user's `advanced-stats.md`: *"Add 0.5 ONLY if ≥1 cell is zero. Unconditional correction biases OR→1."*
**Fix:** document the Mantel-Haenszel-without-correction and Peto-OR options as sensitivity choices. Make sure the app implements *conditional* not unconditional correction. Add a per-app sensitivity pool that uses Peto-OR for sparse-cell trials.

### P1-4 [Clinical/Methods Editor] Primary outcomes are surrogates; GRADE should flag
- **Romosozumab**: new vertebral fracture (radiographic, often asymptomatic)
- **Semaglutide Obesity**: % body weight change (surrogate for morbidity/mortality)
- **Inclisiran**: LDL-C (surrogate for MACE)
- **Tirzepatide T2D**: HbA1c (surrogate for microvascular complications)
- **Renal Denervation**: office SBP (surrogate for CV events)

All are valid regulatory endpoints but should carry an **indirectness** downgrade in GRADE for the surrogate→outcome step.
**Fix:** add a `surrogate_endpoint: true` flag to the benchmark JSON for these apps; auto-downgrade indirectness in the GRADE profile display.

### P1-5 [Reporting Guidelines Editor] Living-MA update cadence is under-specified
Protocols say "Trigger: new phase 3 publication." Cochrane Living SR guidance requires an explicit review cycle (monthly/quarterly) even when no new trial appears. Otherwise "living" collapses to "last updated whenever."
**Fix:** add an explicit cycle to each protocol: "Formal search and protocol-check every 3 months regardless of new publications; summary posted in the app's Version Timeline." Document the next scheduled review date on the landing page.

### P1-6 [Ethics/Reproducibility Editor] Reproducibility of R/Python export not verified
Protocols promise `metafor::rma` and `scipy` reference scripts exportable from the Analysis Suite. For the published demonstrator set, run the export on one app, load into R 4.5.2, verify the pooled estimate and CI match to 1e-6 tolerance. Otherwise the reproducibility claim is unvalidated.
**Fix:** run 1 validation per demonstrator app, document PASS in `v2_selfcheck_report.md` as a separate section. Any disagreement >1e-4 is a P0.

### P1-7 [Clinical/Methods Editor] ITT vs modified-ITT N drift (CAR-T specifically)
CARTITUDE-4 enrolled 419 (208 infused with cilta-cel, 211 SoC). App uses `tN=208` — that's the infused-ITT, not the randomized-ITT of ~210 per arm. KarMMa-3 uses `tN=254` which matches enrolled ide-cel.
**Fix:** re-audit N-randomized per arm across all 41 apps, especially for biologics with bridging therapy and CAR-T. Use the published ITT CONSORT number, not mITT or PP.

### P1-8 [Reporting Guidelines Editor] PRISMA-2020 27-item checklist is promised but not exported
Protocol §10 says "PRISMA-2020 checklist exportable." Verify this works for each demonstrator app and that all 27 items are addressable from the app's state.
**Fix:** export PRISMA-2020 checklist for 5 demonstrator apps, complete the items manually, save as `prisma-checklists/` in the repo for review.

### P1-9 [Statistical Editor] Publication-bias assessment skipped with "k<4 limits formal testing"
Most apps have k=3-4, below the k≥10 threshold for Egger/Peters. Protocol notes this correctly. But journals still expect: (a) contour-enhanced funnel plot, (b) trim-and-fill as sensitivity (acknowledging low power), (c) discussion of unpublished trials via CT.gov search.
**Fix:** add "Duval-Tweedie trim-and-fill as sensitivity (noting low power at k<10)" as explicit text in the Synthesis section.

### P1-10 [Peer-Review Gatekeeper] Benchmark entries should split "agreement type"
Current `PUBLISHED_META_BENCHMARKS.json` mixes three benchmark types:
1. External IPD meta-analysis (DOAC-AF/Ruff, GLP1-CVOT/Sattar, Finerenone/FIDELITY) — gold standard
2. External aggregate-data meta-analysis (SGLT2-HF/Vaduganathan, PCSK9/Guedeney, SGLT2-CKD/Nuffield) — good
3. Self-reference internal DL pool (Tirzepatide, IL-23, CAR-T, etc.) — circular for validation

**Fix:** add `benchmark_type: "external_IPD" | "external_aggregate" | "self_reference"` to each entry. The framework paper's validation table should only cite (1) and (2).

### P1-11 [Ethics/Reproducibility Editor] Disposition-table N extraction risk
Per `lessons.md` (2026-04-15): *"Regex patterns like `(\d+) subjects randomized` silently match `Not Randomized 1,807`."* Verify that all 41 apps' N values were hand-checked against the primary ITT CONSORT table, not pulled via regex.
**Fix:** run a `verify_n_vs_consort.py` spot-check on 10 random apps comparing the app's `tN`/`cN` vs the published CONSORT.

### P1-12 [Clinical/Methods Editor] Pooling different primary timepoints
RSV vaccine trials use different primary case definitions (≥2 vs ≥3 symptoms). Romosozumab uses 12-mo (FRAME, BRIDGE) vs 24-mo (ARCH) endpoints.
**Fix:** document the primary-timepoint harmonisation rule in the SAP. For Romosozumab, consider 12-mo-only primary with 24-mo as sensitivity.

---

## P2 — Polish

### P2-1 [Reporting] Protocol date mismatch (04-19 vs 04-20)
37 protocols frozen 2026-04-19; 4 newest frozen 2026-04-20. Either harmonise to a single freeze date or describe the April 2026 rolling update as v1.0 → v1.1.

### P2-2 [Statistical] HKSJ variance-inflation floor not prominent in protocol text
Protocol §8 says "floor variance inflation at max(1, Q/(k-1))" — technically correct but buried. Promote to a separate bullet in the SAP.

### P2-3 [Clinical/Methods] Sample-size heterogeneity note needed
App pools range from n=245 (Romosozumab BRIDGE smallest trial) to n=34,284 (RSV RENOIR). Very large weight imbalance. DL weights handle this fine but GRADE indirectness should note the heterogeneous population scale.

### P2-4 [Reporting] Landing page should note k<3 where PI is undefined
Of the 41 apps, CAR-T has k=2; future single-trial additions may have k=1. Current landing page doesn't flag where the prediction interval is undefined.
**Fix:** add a "PI undefined" footnote flag in the portfolio table for k<3 entries.

### P2-5 [Ethics/Reproducibility] Protocol `canonical_url` is a raw .md file on GitHub Pages
Journal editors expect a DOI or Zenodo archive for pre-registration. GitHub-hosted .md files can be edited retroactively (though git history exists).
**Fix:** configure GitHub-Zenodo integration; release tags become Zenodo DOIs; add DOI to each protocol's frontmatter.

### P2-6 [Peer-Review Gatekeeper] Network-MA extension is a natural Discussion point
For class-level pools users will ask "why pairwise not network?" Future work section should propose a browser NMA module.

---

## Deduplicated action list (priority-ordered)

1. **P0-1 / P0-2** — Decide: framework paper + 4-6 demonstrator papers vs 41 salami papers. *This is the gating decision.* Everything else depends on it.
2. **P0-6** — Complete formal dual-assessor RoB-2 for the demonstrator set (4-6 apps). Keep the rest labeled screening-only.
3. **P0-3 / P1-10** — Add `benchmark_type` field to JSON; recompute true validation stats; relabel self-reference pools.
4. **P0-4** — PROSPERO-register demonstrator protocols OR rewrite the "PROSPERO-style" framing.
5. **P0-5** — Fix k=2 method (CAR-T) with explicit FE-primary + Bayesian sensitivity.
6. **P0-7** — Audit target journals for COI; add Synthesis/editorial-board statements where relevant.
7. **P0-8** — Add `pool_type: same_drug | class_level` and auto-downgrade indirectness for class pools.
8. **P1-2** — Complete AMSTAR-2 for demonstrators OR remove the promise.
9. **P1-6 / P1-8** — Run R/Python reproducibility + PRISMA-2020 checklist for 5 demonstrators; save results.
10. **P1-11** — Verify N-randomized for the 41 apps against CONSORT (spot-check 10).

---

## Overall editorial verdict

**Framework paper = publishable after P0 fixes.** The novelty (browser-hosted living MA with frozen protocol, CT.gov auto-sync, two-source V2 regex verification, HMAC-signed dual-reviewer seals) is real and rare. Target: **J Clin Epidemiol, Research Synthesis Methods, or BMJ Medicine.**

**Demonstrator pools = publishable individually after P0-5/6/7/8 fixes.** Pick 4-6 topics with genuine external benchmarks. **Recommended demonstrators: DOAC-AF (Ruff 2014 IPD, EXACT), SGLT2-HF (Vaduganathan 2022), Finerenone (FIDELITY pooled IPD), GLP1-CVOT (Sattar 2021), PCSK9 (Guedeney 2020), Inclisiran (ORION fixed-effect pool).** Avoid topics where pools duplicate recent Cochrane reviews.

**41-apps-as-one-submission = will be rejected at triage.** Salami-looking. Don't do it.

**Fastest path to first submission (weeks, not months):**
1. Week 1: Framework paper draft + complete AMSTAR-2 for 6 demonstrators.
2. Week 2: Dual-assessor RoB-2 for 6 demonstrators (split into pairs, 1 hour per trial).
3. Week 3: Add `benchmark_type` + `pool_type` fields + indirectness-auto-downgrade; run reproducibility checks.
4. Week 4: PROSPERO registration of 6 demonstrators; submission to J Clin Epi (framework) + JAMA/BMJ specialty (demonstrator #1).
