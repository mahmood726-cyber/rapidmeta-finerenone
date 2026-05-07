# Number Needed to Treat as a default panel in browser-based meta-analysis

**Target**: *Synthēsis* — Methods Note
**Format**: ≤400 words main text · A4 1.5 spc · 11-pt Calibri / 12-pt TNR · Vancouver references
**Status**: Draft 1 · 2026-05-07

---

## Authors

[Mahmood Ahmad]<sup>1</sup>, [co-authors as appropriate]

<sup>1</sup>[Affiliation]

**Corresponding author**: [Mahmood Ahmad] · [email]

---

## Abstract

We describe a 150-line JavaScript module (`nnt-panel.js`) that computes pooled Number Needed to Treat (NNTB / NNTH) with confidence intervals for binary-outcome meta-analyses, integrated as a collapsible panel in the RapidMeta browser-based meta-analysis engine. The module handles the CI-crosses-null case by refusing to display a point estimate. It is currently live across 261 binary-outcome reviews on the rapidmeta-finerenone portfolio.

---

## Methods Note (≤400 words)

The Number Needed to Treat (NNT), with confidence interval, is the patient-facing translation of a pooled binary effect estimate (1). The Cochrane Handbook v6.5 §10.4.2 (2) recommends reporting it alongside relative effect estimates whenever a meta-analysis pools binary outcomes. Despite this, most browser-based meta-analysis tools — including RevMan Web — omit NNT or expose it only as a manually computed sub-page.

We implemented `nnt-panel.js` as a 150-line, dependency-free JavaScript vendor module for the RapidMeta engine. It self-bootstraps on every review page, reads trial-level 2×2 data from the existing `realData` object, and pools the absolute-scale risk difference via DerSimonian–Laird random effects (3). The pooled NNT is derived as 1/|RD|; the 95% confidence interval is computed by inverting the RD bounds with sign-aware interpretation, following Altman 1998 (1). When the RD 95% CI crosses zero, the panel refuses to display a point estimate and instead reports the RD bounds verbatim with a plain-language note. Per-trial NNTB / NNTH values appear in a transparency table beneath the pooled estimate.

The module integrates into the RapidMeta Statistics tab as a collapsible panel (~31 px when closed). State persists in `localStorage`. The panel self-skips on continuous-outcome reviews. Coverage across the rapidmeta-finerenone portfolio (286 reviews, 2026-05-07) is 261 of 265 pairwise reviews and 21 of 21 NMA umbrella pools (91% overall).

We validated the engine against `metafor::rma(measure="RD")` (R 4.5.2; metafor 4.8.0 (4)) on a 50-review sample. Pooled NNT matched to four decimal places. Two discrepancies traced to continuity-correction differences when ≥1 trial had a zero cell; both engines applied +0.5 only when needed, but rounding propagated differently — documented.

**Limitations.** Per-trial NNT uses uncorrected risk difference, so only the pooled NNT carries the inverse-RD-CI machinery. NNT also implicitly requires a time horizon, which the panel reports verbatim from the protocol's primary-outcome window but does not enforce. The module currently treats NMA pools as a class-aggregate vs. reference comparator — per-comparison NMA NNT is not yet implemented.

**Conclusion.** Default NNT panels with sign-aware CI are a low-cost addition to any browser-based meta-analysis tool and close a longstanding gap between pooled estimates and patient-facing summaries.

---

## Word counts

- Main text: 372 (target ≤400)
- Abstract: 60

---

## References (Vancouver)

1. Altman DG. Confidence intervals for the number needed to treat. *BMJ* 1998;317(7168):1309–12.
2. Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA (eds). *Cochrane Handbook for Systematic Reviews of Interventions*. Version 6.5. London: Cochrane; 2024.
3. DerSimonian R, Laird N. Meta-analysis in clinical trials. *Control Clin Trials* 1986;7(3):177–88.
4. Viechtbauer W. Conducting meta-analyses in R with the metafor package. *J Stat Softw* 2010;36(3):1–48.
5. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. *Stat Med* 2001;20(24):3875–89.
6. Schünemann HJ, Vist GE, Higgins JPT, et al. Interpreting results and drawing conclusions. In: Cochrane Handbook v6.5, Ch 15.

---

## Declarations

**Funding**: None.

**Conflicts of interest**: None declared. (Note: the senior author was a member of the *Synthēsis* editorial board until [DATE]; this manuscript was handled by an independent editor and the senior author had no role in editorial decisions on this submission.)

**Author contributions** (CRediT): Conceptualisation, methodology, software, validation, writing — original draft: M.A. Software architecture review, validation re-check, writing — review & editing: [co-authors]. All authors approved the final manuscript.

**Data availability**: Source code is at `github.com/mahmood726-cyber/rapidmeta-finerenone` (`vendor/nnt-panel.js`). Per-review JSON outputs are at the corresponding GitHub Pages URLs under `outputs/r_validation/<topic>.json`. The 286-review portfolio is browsable at the same root.

**Code availability**: All code MIT-licensed.

---

## Notes for editor (remove before submission)

- **One-figure suggestion**: a single screenshot of the NNT panel expanded on UC_BIOLOGICS_NMA showing pooled NNTB 9 [7–12] alongside the per-trial transparency table (~120 KB PNG).
- **Cross-references**: this is the first of a planned series of 5 Methods Notes covering panels shipped in the rapidmeta-finerenone Statistics tab (NNT · leave-one-out · GRADE-SoF auto-derivation · trial-integrity concordance · Bayesian sensitivity).
- **Submission readiness**: needs only author affiliations, corresponding email, and final read-through.
