# The scoreboard: end-to-end reproduction of a fixed published meta, scored per outcome

**Date:** 2026-09-06. **Goal (Mahmood):** train the harness to match the metas on our site and
published open metas. The measurable version is whether the whole chain runs —
`protocol -> search -> screen -> identify -> extract arms -> pool -> compare` — with every step
recorded, scored per outcome against a benchmark fixed before any run.

## What runs now

- `scripts/reproduce_benchmark.py` (a prior lane) — the rigorous **single-outcome** (all-cause
  death) reproducer: AACT extraction, HEART-FID cross-check, published anchors, self-failing.
- `scripts/benchmark_scoreboard.py` (new) — the **per-outcome table**, composing the reproducer
  (it calls `extract_death` verbatim, not a copy) and adding SAE from the AE-module 'serious'
  totals. One data source (AACT), RR pooled by REML tau2 + HKSJ t_{k-1}, method named on both
  sides.

## Galli 2025 (GLP-1 CV) — first per-outcome table

Their measure is **IRR** (needs person-time); ours is **RR** (events+n). They coincide only under
balanced arm follow-up, so the estimate column is indicative, not an identity — stated, not elided.

| outcome | their k | our k | theirs | ours (method named) |
|---|---|---|---|---|
| all-cause death | 18 | **10** | IRR 0.88 (crude 0.871) | RR 0.869 [0.812, 0.931] REML+HKSJ, τ²=0 |
| serious AEs | 18 | **14** | IRR 0.91 (crude 0.926) | RR 0.945 [0.912, 0.980] |
| cv death | 19 | 0 | IRR 0.87 | blocked: titled-outcome extraction + denominator |
| MACE | 15 | 0 | IRR 0.87 | blocked: titled composite extraction + denominator |
| HF hospitalisation | 14 | 0 | IRR 0.85 | blocked: titled-outcome extraction + denominator |
| nonfatal MI | 13 | 0 | — | blocked: titled-outcome extraction + denominator |
| nonfatal stroke | 12 | 0 | — | blocked: titled-outcome extraction + denominator |
| neoplasm | 14 | 0 | IRR 1.04 | blocked: AE-term (MedDRA) parsing |
| infections | 14 | 0 | IRR 0.90 | blocked: AE-term (MedDRA) parsing |
| GI disorders | 18 | 0 | IRR 1.63 | blocked: AE-term (MedDRA) parsing |
| acute kidney failure | 10 | 0 | IRR 0.91 | blocked: AE-term (MedDRA) parsing |
| pancreatitis | 13 | 0 | IRR 0.96 | blocked: AE-term (MedDRA) parsing |
| gallbladder | 8 | 0 | IRR 1.26 | blocked: AE-term (MedDRA) parsing |

**Anchors exact** on the death row (EXSCEL 507/584, PIONEER-6 23/45, REWIND 536/592).

### The disagreement set (the finding, not the delta)

- **all-cause death** — ours 10 of their 18. Could not populate 7: ELIXA, FIGHT, LEADER,
  LIVE-Jorsal, SUSTAIN-6, STEP-HFpEF DM (carry death only outside the AE module), GRADE (arms
  unresolved). Plus 4 NCTs unresolved: Kyhl, Chen, Zhang (unregistered), STRIDE (not in the
  2026-08-30 snapshot).
- **serious AEs** — ours 14 of their 18. Could not populate 3: GRADE, LIVE-Jorsal, STEP-HFpEF DM;
  same 4 unresolved NCTs.

### The work list (what to build, ordered by reach)

1. **Resolve the 4 NCTs** (STRIDE needs a newer AACT snapshot; Kyhl/Chen/Zhang are unregistered —
   a publication-read source, not a registry one). Caps every outcome's k.
2. **Titled-outcome extraction + its own denominator** — unlocks cv_death (19), MACE (15),
   HF-hosp (14), MI (13), stroke (12): the whole efficacy block.
3. **AE-term (MedDRA) parsing** — unlocks neoplasm, infections, GI, AKI, pancreatitis, gallbladder.

## Navarese 2023 (revascularisation) — a different ceiling, by design

Run to stop over-fitting to Galli. Its benchmark records, as a pre-run hypothesis confirmed on
2026-09-04, that the wall is **upstream of extraction**: the acquisition matcher is
drug × condition, and this question is a **procedure** (PCI/CABG) vs **medical therapy** — not a
named agent. The well-formed query returned 112 trials; **2 of 18** were identifiable (FAME-2,
ORBITA). Its effect measure is **RR** (so no IRR/RR gap), and its per-trial cells are not served
even in the paper.

- **Galli's ceiling is EXTRACTION** (we identify the trials; the arms are the wall).
- **Navarese's ceiling is IDENTIFICATION** (the acquisition query cannot express the question).

Two benchmarks, two ceilings — the point. Navarese's single-outcome schema differs from Galli's;
wiring it into the scoreboard needs a small adapter, and the honest verdict there is already known:
reproduction blocked at identification, beatable only on disclosure, not on k or data.

## Not tuned to the target

Every blocked row reports k=0 and names the step; no branch raises a number by relaxing a rule. An
honest k=10 with a named 8-trial remainder is the deliverable, not a filled-in 18.
