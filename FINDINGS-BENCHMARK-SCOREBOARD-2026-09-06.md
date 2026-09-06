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
| MACE | 15 | **3** | IRR 0.87 (crude 0.889) | RR 0.854 [0.708, 1.031] |
| nonfatal MI | 13 | **3** | — | RR 0.930 [0.721, 1.200] |
| nonfatal stroke | 12 | **3** | — | RR 0.830 [0.598, 1.152] |
| cv death | 19 | **2** | IRR 0.87 (crude 0.889) | RR 0.693 [0.055, 8.728] (k=2, wide) |
| HF hospitalisation | 14 | **1** | IRR 0.85 | RR 0.884 [0.740, 1.055] (k=1, Wald) |
| neoplasm | 14 | 0 | IRR 1.04 | blocked: AE-term (MedDRA) parsing |
| infections | 14 | 0 | IRR 0.90 | blocked: AE-term (MedDRA) parsing |
| GI disorders | 18 | 0 | IRR 1.63 | blocked: AE-term (MedDRA) parsing |
| acute kidney failure | 10 | 0 | IRR 0.91 | blocked: AE-term (MedDRA) parsing |
| pancreatitis | 13 | 0 | IRR 0.96 | blocked: AE-term (MedDRA) parsing |
| gallbladder | 8 | 0 | IRR 1.26 | blocked: AE-term (MedDRA) parsing |

**Anchors exact** on the death row (EXSCEL 507/584, PIONEER-6 23/45, REWIND 536/592).

## Titled-outcome extraction (item 2) — the efficacy block moved

`scripts/titled_outcome_extract.py` reads a trial's OWN posted efficacy outcome (not the AE
module), with four rules encoded as code, each with a test on a known-hard case
(`scripts/test_titled_outcome_extract.py`, **12/12**):

1. **Denominator in the class title** (`(n=2629, 2616)`), positional to arms, overriding
   `outcome_counts` (the randomised total) — the source of 48 prior wrong integers. Records which
   field it read.
2. **Arithmetic route** (events = posted % × analysis N) or direct count — no prose parser.
3. **No AE substitution** for an efficacy outcome; cross-check and flag, never replace. Proven on
   HEART-FID: titled 131/158 (RR 0.830) vs AE 354/367 (RR 0.965) — the extractor keeps the titled
   value.
4. **0/0 → NOT_DISCRIMINATING**, never folded into "could not determine".

**A confidently-wrong integer was caught and fixed before it reached the table.** The first wired
run read AMPLITUDE-O and HARMONY MACE as 5 events — because their MACE is posted as an **incidence
rate** ("events per 100 participant-years"), and reading a rate as a count fabricates a number. A
fifth rule now **refuses rate units** (they need person-time → an IRR, not a 2×2); both trials
correctly dropped to NOT_FOUND, and MACE went from a false k=5 to an honest **k=3** (FLOW 212,
PIONEER-6 61, SOUL 579 — all verified counts, internally consistent: PIONEER-6 CVd 15 + MI 37 +
stroke 12 ≈ MACE 61).

### Efficacy disagreement sets (which trials we have, which we don't)

- **MACE** ours 3 of 15: FLOW, PIONEER-6, SOUL. The other 12 post MACE as a rate/HR (refused) or
  under a title our matcher does not resolve.
- **cv death** ours 2 of 19: LEADER (arithmetic 4.7%×4668), PIONEER-6. **nonfatal MI / stroke**
  ours 3 each: LEADER, PIONEER-6, REWIND. **HF hosp** ours 1: LEADER.
- The wall for the rest of the efficacy block is the same: these trials report the outcome as an
  incidence rate or a hazard ratio, not as an extractable participant count. That is a **measure**
  limit, not a matcher bug — and refusing it is the correct behaviour, not a gap to paper over.

### No reader-facing change

The extractor and scoreboard write only to `evidence/acquisition/`. No `*_REVIEW.html` generator
consumes them, so no served number changed. If this extraction is later wired into a served page,
any number it changes is a finding to report first.

## Did the same mistake already reach a served page? Scanned — no.

The rate-vs-proportion catch is worth generalising: **a number's scale does not tell you its
unit, and a plausible-looking magnitude is the most dangerous kind of wrong** — `3.9` reads as a
percentage and is an incidence rate, the same family as reading `denoms.counts` for 48 wrong
integers. So `scripts/scan_rate_as_proportion.py` checks whether any *already stored* value came
in through a rule that could confuse a rate for a proportion, across all **155 objects**. It
carries a self-test that plants one of each defect and asserts it is caught — a zero is reported
only because the instrument is proven able to find a positive.

Result: **0** pools that pool or relabel a rate ratio (RATE_RATIO/IRR) as a risk ratio (RR/OR) —
the direct defect; **0** arm-level values with events > N or a proportion > 1; **1** softer case,
`malaria-vaccines / exploratory_recurrent_rate`, which pools an HR with an IRR and is labelled
exploratory (reported, not merged into the count). The corpus does not carry the stored-data form
of this mistake — objects take effects from the printed ratio, not from a `pct × N` arithmetic,
so the path that would make it does not run.

## Three things to survive this session

### 1. The remaining Galli gap is a MEASURE limit, not an extraction limit

This is a **different diagnosis** from the one the day started with, and it changes what work is
worth doing. The efficacy trials we do not reach (most of MACE, CV death, MI, stroke, HF-hosp)
report the outcome as an **incidence rate** or a **hazard ratio**; we pool **risk ratios**; the
harness **refuses rather than coerces**, which is correct. So "our k is 3 vs their 15" is NOT an
extraction failure and must not be read as one. **Do not rebuild the extractor to close this gap** —
it is already doing the right thing by declining a measure it cannot honestly convert. The
extractor's job on these is to refuse, and it does.

### 2. Open decision (for Mahmood): pool on their scale, or not

Matching Galli's k on the efficacy outcomes requires pooling on **their** scale — an IRR over
person-time — rather than the risk ratio we pool now. This is a methods decision, recorded as a
fork with both sides, NOT to be taken by drifting into it because it raises a number:

- **For:** it would let us reach the trials that only report rates/HRs, closing the k gap on MACE,
  CV death, MI, stroke, HF-hosp, and comparing like-for-like against Galli's IRRs.
- **Against:** we would have to **derive person-time**, and the available derivation
  (`person-time ≈ n × follow-up`) **biases toward the null under censoring** — it overstates
  person-time for arms with more early events, shrinking the rate difference. An IRR built on
  n×follow-up is not the IRR Galli computed from actual exposure, and the discrepancy is
  systematic, not noise.
- **Status:** UNDECIDED. Do not adopt IRR pooling to improve the scoreboard's k without an
  explicit decision on how person-time is obtained. A number reached by drifting into a biased
  denominator is worse than an honest k=3.

### 3. The scan's zero is only worth its control

`scan_rate_as_proportion.py` reported 0 rate-as-risk defects across 155 objects **only because its
self-test first plants one of each defect (a pool mixing IRR+RR, an arm with events>N) and
asserts both are caught** — a scan that can only return zero measures nothing. The one case it did
surface, `malaria-vaccines / exploratory_recurrent_rate` (an HR pooled with an IRR), was
**reported, not merged** — it is labelled exploratory on the object, and the scan flags it as the
softer B class rather than silently folding it into the count.

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
