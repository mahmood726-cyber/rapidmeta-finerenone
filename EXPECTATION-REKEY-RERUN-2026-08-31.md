# Expectation for the CORRECTED run — written BEFORE the re-run, 2026-08-31

## Why this is a bug fix and not a rule change

⭐ **Amendment 2 was authored, justified and frozen in `RULE-AMENDMENT.md` BEFORE the scan
ran.** It then failed to propagate: `scan.py` line 79 (controls) called `class_phrases()`
live and got the amended splitter, while line 140 (the twenty) read `class_phrases` frozen
into `twenty.json` at draw time, before the amendment.

**Re-running applies the ALREADY-FROZEN rule CORRECTLY. Nothing about the rule changes.**

The surface appearance is the thing to answer head-on: *"they re-ran after learning the
number might improve."* The defence is not our word — it is the amendment's own timestamp
and content. `RULE-AMENDMENT.md` states, before any scan output existed, that
`beta-blockers (propranolol type)` must split to `beta blocker`. The corrected run is the
first run in which the twenty are scored by the rule as written.

## The expectation, on the record

Current published figure: **A 1/20 → A∪B 4/20**.

| arm | published | predicted after correction |
|---|---|---|
| A — drug only | 1 / 20 | **1 / 20** (unchanged; drug terms are untouched by the amendment) |
| B — class only | 3 / 20 | **5 / 20** |
| A∪B — the re-key | 4 / 20 | **6 / 20** |

**Predicted movement: +2 topics.** Reasoning, per affected topic:

- `enoxaparin-vte` — **most likely to flip.** The amended split fragments the stem into
  `heparin` as a standalone phrase, which is broad and will match the many LMWH-for-VTE
  reviews in the frame.
- `dabigatran-af`, `dabigatran-stroke` — `thrombin inhibitor argatroban type` becomes the
  matchable `thrombin inhibitor`. **One of the two may flip.**
- `etripamil-psvt` — `coronary vasodilator`; no such Cochrane framing expected. **No flip.**
- `pitavastatin-auto-full-review` — `hmg coa inhibitor` vs Cochrane's *"HMG CoA reductase
  inhibitors"*; the word `reductase` breaks the phrase, and the condition limb fails anyway.
  **No flip.**

## The direction I expect to miss

**OPTIMISTIC, again.** Eleven consecutive optimistic misses precede this one, and the
twelfth was optimistic on both arms. I have no reason to believe the twelfth cured it, so
the honest expectation is that **the true figure lands BELOW 6 — most likely 5.**

⚠️ **And the counter-direction, named so this is falsifiable:** the amended split produces
`heparin` as a bare one-word phrase, which is far broader than any class term in the
original run. If that alone drags in verified pairs across several topics, A∪B could land
ABOVE 6 — and if it does, **that is a finding about the amendment introducing retrieval
noise, not a vindication of the re-key.** I would report it as the former.

## What would make me distrust the corrected number

If the flips come from one-word fragments (`heparin`) rather than genuine class phrases,
the corrected figure is worse evidence than the original, not better. I will report which
phrase produced each flip alongside the count, so that cannot hide.
