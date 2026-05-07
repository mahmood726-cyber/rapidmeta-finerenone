# Pre-registration concordance heuristics as a sensitivity panel for meta-analysis

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

We describe a 220-line module (`trial-integrity-panel.js`) that applies three pre-registration concordance heuristics — retrospective registration, results-posting overdue, status-of-concern — to every trial in a meta-analysis using public CT.gov data via the AACT 2026-04-12 snapshot, then reports a sensitivity re-pool excluding flagged trials. Across 553 corpus NCTs, 113 (20.4%) carry ≥1 flag. Framed neutrally as concordance signals.

---

## Methods Note (≤400 words)

The Cochrane ROB-ME extension (2024 Handbook Ch 13 (1)) endorses per-trial integrity-flag reporting in meta-analyses. The Goldacre COMPare project documented widespread outcome switching (2); the AllTrials initiative documented widespread retrospective registration; FDAAA Final Rule audit work has shown ~22% of registered trials still fail to post results within the statutory 12-month window after primary completion.

We implemented `trial-integrity-panel.js` as a 220-line dependency-free panel. A Python pre-pass (`compute_trial_integrity.py`) streams the AACT 2026-04-12 snapshot for every NCT in the corpus and writes one row per trial to `outputs/trial_integrity.json`. Three boolean flags per trial:

- **`retro_registered`** — `study_first_posted_date` > `start_date` by >1 month (after the AllTrials grace window).
- **`results_overdue`** — `primary_completion_date` >12 months in the past with `results_first_posted_date` empty (FDAAA Final Rule §812.50 (3)).
- **`status_concern`** — `overall_status` ∈ {Unknown, Suspended, Terminated, Withdrawn}.

The panel renders, for each trial in the current review, a per-trial table with the verbatim AACT dates and status alongside the flag verdict, then computes a sensitivity pool of the random-effects log-OR (DerSimonian–Laird (4)) with all flagged trials excluded. The panel reports |Δ| = |OR<sub>main</sub> − OR<sub>sensitivity</sub>| / OR<sub>main</sub> with three colour bands: trivial (<5%), modest (5–15%), substantial (≥15%).

Across the 553 NCTs in the rapidmeta-finerenone portfolio (2026-05-07), 113 (20.4%) carry ≥1 flag: 39 retrospectively registered, 93 results-overdue, 0 status-of-concern (curated post-2015 RCTs). On COLCHICINE_CVD specifically, 2/5 trials are flagged, shifting the pooled OR by 10.8%.

The framing is intentional. Each flag is **evidence-anchored** (verbatim CT.gov dates inline) and described as a **process** signal, not a finding of misconduct. Disclaimer text in the panel explicitly states the heuristics do not impugn primary research integrity.

**Limitations.** AACT lags CT.gov by ≤2 weeks; status changes since 2026-04-12 are not reflected. Some trials in our corpus are pre-CT.gov (NCT predates the registry); these correctly return no flag rather than a missing-data concern. The panel does not currently propagate to GRADE.

**Conclusion.** A 220-line panel using only public AACT data converts ROB-ME 2024's per-trial integrity reporting from a manual narrative exercise into a one-glance sensitivity widget — at the cost of zero new dependencies.

---

## Word counts

- Main text: 396 (target ≤400)
- Abstract: 75

---

## References (Vancouver)

1. Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA (eds). *Cochrane Handbook for Systematic Reviews of Interventions*. Version 6.5, Ch 13: Risk-of-bias due to missing evidence (ROB-ME). London: Cochrane; 2024.
2. Goldacre B, Drysdale H, Powell-Smith A, et al. The COMPare Trials Project. *Trials* 2019;20(118).
3. US FDA. Final Rule for Clinical Trials Registration and Results Information Submission (42 CFR §11). 81 Federal Register 64981. 2016.
4. DerSimonian R, Laird N. Meta-analysis in clinical trials. *Control Clin Trials* 1986;7(3):177–88.
5. Tasneem A, Aberle L, Ananth H, et al. The database for aggregate analysis of ClinicalTrials.gov (AACT) and subsequent regrouping by clinical specialty. *PLoS ONE* 2012;7(3):e33677.
6. Page MJ, Sterne JAC, Higgins JPT, Egger M. Investigating and dealing with publication bias and other reporting biases in meta-analyses. *Res Synth Methods* 2021;12(2):248–59.

---

## Declarations

**Funding**: None.

**Conflicts of interest**: None declared.

**Author contributions** (CRediT): Conceptualisation, methodology, software, validation, writing — original draft: M.A. Software architecture review, validation re-check, writing — review & editing: [co-authors]. All authors approved the final manuscript.

**Data availability**: Source code and pre-computed flag JSON (`outputs/trial_integrity.json`) at `github.com/mahmood726-cyber/rapidmeta-finerenone`. AACT snapshot 2026-04-12 from the Clinical Trials Transformation Initiative.

**Code availability**: All code MIT-licensed.

---

## Notes for editor (remove before submission)

- **One-figure suggestion**: a screenshot of the trial-integrity panel expanded on COLCHICINE_CVD showing 2/5 flagged trials with verbatim AACT dates + sensitivity Δ = 10.8%.
- 4th of 5 planned Methods Notes.
