# Vacuity audit: every gate against the population it actually runs on

2026-08-18. Prompted by `CHK024`, which emitted 115 results on this corpus, passed all
115, and adjudicated nothing — found only because a ceiling moved.

**The headline is not vacuity. It is scope.** Of the checks that do run, 294 of 302
emissions were genuinely adjudicated (97%). The problem is how few run at all.

---

## The numbers

| | n |
|---|---|
| Checks defined in `probes*.py` | **31** |
| Registered (can run anywhere) | **30** — `CHK031_SEARCH_RECALL` is defined and never registered |
| Declared `ARTEFACT_DECIDABLE` (the pre-push gate's blocking set) | **20** |
| **That ever emitted a single payload on this corpus** | **7** |
| Emissions | 302 |
| Adjudicated | **294 (97%)** |
| Vacuous | 8 — 3 `CHK016`, 5 `CHK021`, all already reported as INVALID |

**The pre-push gate declares twenty blocking checks and runs seven.** Thirteen are
declared blocking-capable and produce no payload at all:

`CHK002_TOKEN_MATCH` · `CHK005_EXTERNAL_REFERENT` · `CHK006_IDENTITY_KEY` ·
`CHK008_FRAME_DENOMINATOR` · `CHK013_FIELD_SEMANTICS` · `CHK023_CROSS_AGENT_POOLING` ·
`CHK024_FALSE_METHOD_CLAIM` · `CHK025_MULTI_SURFACE_DISAGREEMENT` ·
`CHK026_WRONG_REASON_ABSENCE_PANEL` · `CHK027_SENTINEL_LEAK` ·
`CHK028_DISQUALIFIED_REFERENT_PROMOTED` · `CHK029_SIGN_NORMALISATION` ·
`CHK030_BUILD_MODE_BLIND_TEXT`

A further 10 are retrieval-scoped and correctly absent here — that partition is a data
structure precisely so they are not counted as build coverage.

**`CHK024` is worse than vacuous and it is not alone in kind.** It emitted and decided
nothing; these thirteen do not even emit. A check that produces no payload cannot be
caught by a vacuity ceiling, because it contributes nothing to the denominator. **The
mechanism that found `CHK024` structurally cannot find these.**

### The seven that work

| Check | adjudicated / emitted |
|---|---|
| `CHK009_POOL_IDENTITY` | 17 / 17 |
| `CHK016_PRECISION_SAMPLE_MISMATCH` | 35 / 38 |
| `CHK017_DUP1_BIT_EQUALITY` | 15 / 15 |
| `CHK018_MIXED_POOLING` | 14 / 14 |
| `CHK019_INERT_ENGINE` | 29 / 29 |
| `CHK020_ORPHAN_POOLED_RESULT` | 119 / 119 |
| `CHK021_MEASURE_SCALE_MISMATCH` | 65 / 70 |

All seven are failable on real payloads — a real object from this corpus can be mutated
into a FAIL. That is a genuine result and it is the good news here.

---

## Was tonight's clean result clean or empty?

**Neither, and the honest answer is uncomfortable.**

Across all fifteen new artefacts, **exactly one blocking check emitted: `CHK020_ORPHAN_POOLED_RESULT`, once each. Fifteen emissions total, out of twenty
declared blocking checks.**

The fifteen are verdict-only objects: no pooled estimate, no per-trial rows, no entries.
Nineteen of the twenty checks are pool-shaped and had nothing to read.

Two things are true and both should be said:

- **The one check that ran is the pertinent one.** `CHK020` asks whether a page displays a
  pooled estimate on an outcome the object says cannot pool — which is the single most
  relevant question about a verdict page. It ran, it adjudicated, it passed.
- **"All preconditions clean" on the fifteen means one check, not twenty.** The green is
  worth one check's assurance. My build-commit message did not say that, and it implied
  more.

The standalone preconditions (eligibility-vs-k, null comparator, marker prefix, sibling
fields) did run and were clean — those are separate from the harness. But the harness
figure was one.

---

## The certainty-language detector

Built as `scripts/overclaim_detector.py` and **it is not yet good enough to act on
broadly.** A naive grep returns 226 hits across 76 files; my classifier narrowed it to 324
and still calls policy statements ("UNCHECKABLE IS NEVER A PASS") claims about the world.
Reported as a partial result rather than tuned indefinitely.

**Tightened to the exact `CHK017` signature it finds three, and one of them is the real
one** — already corrected. But it found something better in the near-miss class.

### The best thing it found

`probes_corpus.py`, the fixture-status table for `CHK017`, written by its author:

> FIDELIO/FIGARO are real and distinct, but no two independently derived floats are ever
> bit-equal, so the negative cannot plausibly fire. **A near-miss negative — two entries
> agreeing to 6+ dp but not at full precision — would stress it and I do not have one.**
> THIS IS THE WEAKEST NEGATIVE OF THE TEN.

Every clause of that is right except the last four words. **The author named the gap,
named the exact fixture that would close it, graded the negative WEAK — and did not go
looking.** The fixture was in the corpus: `sglt2-hf` holds DAPA-HF at 0.75 (0.65–0.85) and
EMPEROR-Reduced at 0.75 (0.65–0.86), two trials agreeing exactly at published precision.

It is now the second negative and it is load-bearing, because **it FAILED under the old
check** — which is how the false premise surfaced at all.

So the detector's real form is sharper than a word-list: **wherever a fixture table grades
its own negative WEAK and says what would strengthen it, the counterexample may already be
in the corpus.** That is a query, not a grep, and it is cheap.

---

## What this changes

The delivery count of **115 of 116** stands — it was gated by `verdict_gate` and
`content_gate`, which are standalone and not part of this registry.

What does not stand is any implication that the harness verified those pages twenty ways.
It verified them one way. **Coverage claims must name the checks that emitted, not the
checks that exist** — which is the same correction as `CHK024`, one layer out: a check that
exists and never runs is coverage of zero, and counting it is the error.
