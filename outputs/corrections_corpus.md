# Corrections corpus (the RLHF-analog labelled dataset)

**1164 labelled correction examples** (our-value -> corrected-value -> source).

## By who/what caught it

- gate: 976
- portfolio-scan (seeded by user report 2026-06-01): 128
- internal-logic: 57
- source-read: 2
- user: 1

## By error class

- label: 450
- year: 422
- transcription-blank: 190
- transcription: 39
- pmid: 32
- estimand-mixing: 31

## The number that decides whether a flag predictor is trainable TODAY
- **Gate-independent labels (human read the source, no rule fired first): 3.**
- These are the ONLY labels that can show a learned flag catching a class the hand-written gates MISS. Every other label was produced by a gate/audit, so training on them and scoring flag-recall is CIRCULAR — the predictor can only relearn the rules it was trained from.
- With 3 gate-independent example(s), a flag predictor **cannot yet be trained for its stated purpose**. The in-app "Report a data issue" capture (built this session) is the funnel that produces gate-independent labels going forward. This is a **wait-for-data**, not a **train-now**, situation — and saying so is the honest result.