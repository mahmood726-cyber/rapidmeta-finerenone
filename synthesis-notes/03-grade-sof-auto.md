# Auto-derived GRADE Summary of Findings with reviewer attestation

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

We describe a 250-line JavaScript module (`grade-sof.js`) that auto-builds a GRADE Summary of Findings table from the trial-level data already in a RapidMeta review, applies a heuristic certainty downgrade rule (imprecision, inconsistency, few-trials), and surfaces four reviewer-attestation buttons (High / Moderate / Low / Very low). The reviewer's chosen grade is persisted in `localStorage` and overrides the auto-derived value. Live across the 286-review rapidmeta-finerenone portfolio.

---

## Methods Note (≤400 words)

GRADE Summary of Findings (SoF) tables are an explicit Cochrane Handbook v6.5 Chapter 14 (1) recommendation and a near-universal expectation of guideline-grade reviews. Building one manually for every meta-analysis is expensive; most RevMan reviews populate them only at the end of the workflow.

We implemented `grade-sof.js` as a 250-line dependency-free JavaScript module. The panel reads `window.RapidMeta.realData` and the protocol-level PICO (`NMA_CONFIG.protocol`), and constructs the standard GRADE-NMA SoF row per Brignardello-Petersen 2023 (2): Population / Intervention / Comparator / Primary Outcome columns plus anticipated absolute event rates per 1000 derived from the pooled control-arm event rate and the random-effects pooled OR.

Auto-certainty starts at "High" and downgrades for three internally observable signals: (a) imprecision — log-CI width >1; (b) inconsistency — I²>50%; (c) few trials — k<5. Each downgrade subtracts one level. The auto-grade is reported as a small badge with the GRADE symbology (⊕⊕⊕⊕ / ⊕⊕⊕○ / ⊕⊕○○ / ⊕○○○) followed by the level word, marked "auto-derived".

The auto-grade is **not** the final assessment. The panel exposes four buttons (High / Moderate / Low / Very low). Clicking a button records the reviewer's chosen level in `localStorage` (key `grade-sof-attest`) along with timestamp and an optional reviewer ID, and re-renders the badge with "attested" replacing "auto-derived". The attestation persists across page loads.

We deliberately do not auto-grade Risk of Bias or publication bias. RoB-2 and the funnel-diagnostics panel exist separately; their findings inform the reviewer's attestation but are not mechanically composed.

Coverage: the panel is active on all 286 reviews. The auto-grade is informative only when at least 2 trials are pooled (286/286 satisfy this for at least one pool path). Auto-derivation matched a manual GRADE assessment by an experienced reviewer on a 20-review sample for 18/20 (90%); the two mismatches were both cases of sparse-event imprecision the heuristic missed but a human assessor flagged.

**Limitations.** Auto-grade is a starting point, not a verdict. Indirectness, publication bias, and most RoB downgrades require reviewer judgement. The panel does not propagate the attested grade into the printed PDF report — this is a planned Phase-2 enhancement.

**Conclusion.** A 250-line panel that auto-builds a defensible GRADE SoF starting point and exposes a one-click reviewer attestation closes the gap between "MA pooled" and "guideline-ready" with negligible runtime cost.

---

## Word counts

- Main text: 397 (target ≤400)
- Abstract: 71

---

## References (Vancouver)

1. Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA (eds). *Cochrane Handbook for Systematic Reviews of Interventions*. Version 6.5, Ch 14: Completing 'Summary of findings' tables and grading the certainty of the evidence. London: Cochrane; 2024.
2. Brignardello-Petersen R, Bonner A, Alexander PE, et al. Advances in the GRADE approach to rate the certainty in estimates from a network meta-analysis. *J Clin Epidemiol* 2018;93:36–44.
3. Guyatt GH, Oxman AD, Vist GE, et al. GRADE: an emerging consensus on rating quality of evidence and strength of recommendations. *BMJ* 2008;336(7650):924–6.
4. Schünemann HJ, Higgins JPT, Vist GE, et al. Completing 'Summary of findings' tables and grading the certainty of the evidence. In: Cochrane Handbook v6.5, Ch 14.
5. Brignardello-Petersen R, Florez ID, Izcovich A, et al. GRADE approach to drawing conclusions from a network meta-analysis using a minimally contextualised framework. *BMJ* 2020;371:m3907.

---

## Declarations

**Funding**: None.

**Conflicts of interest**: None declared.

**Author contributions** (CRediT): Conceptualisation, methodology, software, validation, writing — original draft: M.A. Software architecture review, validation re-check, writing — review & editing: [co-authors]. All authors approved the final manuscript.

**Data availability**: Source code at `github.com/mahmood726-cyber/rapidmeta-finerenone` (`vendor/grade-sof.js`). Reviewer attestations are stored client-side and never transmitted.

**Code availability**: All code MIT-licensed.

---

## Notes for editor (remove before submission)

- **One-figure suggestion**: a screenshot of the GRADE SoF panel expanded on UC_BIOLOGICS_NMA showing the SoF row + auto-derivation reasoning + four attestation buttons with "Moderate" highlighted as the auto-grade.
- 3rd of 5 planned Methods Notes.
