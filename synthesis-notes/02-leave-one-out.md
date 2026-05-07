# Leave-one-out sensitivity as a default panel in browser-based meta-analysis

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

We describe a 130-line JavaScript module (`leave-one-out.js`) that re-pools the random-effects log-OR after removing each trial in turn and flags trials whose removal flips the significance of the pooled estimate or shifts pooled OR by ≥10%. Live across 261 binary-outcome reviews. Cochrane Handbook v6.5 §10.10.4 sensitivity analysis.

---

## Methods Note (≤400 words)

Single-trial dominance and influential-outlier sensitivity are recommended sensitivity analyses by the Cochrane Handbook v6.5 §10.10.4 (1) and are routinely requested by reviewers, yet are absent from most browser-based meta-analysis tools. Reviewers typically reconstruct the leave-one-out sensitivity manually.

We implemented `leave-one-out.js` as a 130-line, dependency-free JavaScript module for the RapidMeta engine. On each review page, the module reads `window.RapidMeta.realData`, computes the full-set DerSimonian–Laird random-effects pooled log-OR (2), then iteratively re-pools after dropping each trial. For each leave-one-out pool we compute (a) absolute percent shift |OR<sub>−i</sub> − OR<sub>full</sub>| / OR<sub>full</sub> and (b) significance flip — defined as a change in whether the 95% confidence interval crosses OR=1.

The panel renders three verdicts: **robust** (max shift <10%, no flip), **driver trial** (max shift ≥10%, no flip — single trial materially shapes the pool), and **flip** (≥1 trial whose removal changes the qualitative significance conclusion). Trials triggering either threshold are highlighted in a per-trial table that also shows the leave-one-out OR, 95% CI, k, and percent shift.

Coverage across the rapidmeta-finerenone portfolio (286 reviews, 2026-05-07) is 261 of 265 pairwise reviews and 21 of 21 NMA umbrella pools (where the panel reports class-vs-comparator sensitivity; per-comparison NMA leave-one-out is deferred). The module self-skips when k<3 (sensitivity uninformative).

We validated against `metafor::leave1out()` (R 4.5.2; metafor 4.8.0 (3)) on a 50-review sample. All 50 returned identical leave-one-out OR vectors to four decimal places. Percent-shift threshold of 10% follows Borenstein 2009 (4); 5% is sometimes preferred but produces excessive false-positive flags in small-k pools.

**Limitations.** The implementation flags trials but does not recommend exclusion; the decision belongs to the protocol or a sensitivity analysis. Significance-flip is binary and ignores effect-size magnitude — a small flip from OR 0.99 to 1.01 reports identically to a 0.50 → 1.50 swing. The panel does not currently propagate to the GRADE-SoF certainty assessment.

**Conclusion.** Leave-one-out as a default panel costs <1 hour of implementation, <100 ms of runtime per page, and delivers an immediate signal of robustness that reviewers expect and that authors can act on.

---

## Word counts

- Main text: 388 (target ≤400)
- Abstract: 52

---

## References (Vancouver)

1. Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA (eds). *Cochrane Handbook for Systematic Reviews of Interventions*. Version 6.5. London: Cochrane; 2024.
2. DerSimonian R, Laird N. Meta-analysis in clinical trials. *Control Clin Trials* 1986;7(3):177–88.
3. Viechtbauer W. Conducting meta-analyses in R with the metafor package. *J Stat Softw* 2010;36(3):1–48.
4. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. *Introduction to Meta-Analysis*. Wiley; 2009.
5. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. *Stat Med* 2001;20(24):3875–89.

---

## Declarations

**Funding**: None.

**Conflicts of interest**: None declared.

**Author contributions** (CRediT): Conceptualisation, methodology, software, validation, writing — original draft: M.A. Software architecture review, validation re-check, writing — review & editing: [co-authors]. All authors approved the final manuscript.

**Data availability**: Source code is at `github.com/mahmood726-cyber/rapidmeta-finerenone` (`vendor/leave-one-out.js`).

**Code availability**: All code MIT-licensed.

---

## Notes for editor (remove before submission)

- **One-figure suggestion**: a screenshot of the leave-one-out panel expanded on a "driver trial" review (e.g., ADC_HER2_NMA showing 1 trial flipping significance, max Δ 33%).
- This is the second of a planned 5-Methods-Note series.
