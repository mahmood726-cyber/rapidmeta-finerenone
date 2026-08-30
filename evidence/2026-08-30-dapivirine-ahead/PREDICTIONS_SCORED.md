# PREDICTIONS SCORED — 2026-08-30

Scored against `PREDICTIONS.md`, which was written before any of the
measurements below were run. Items 2, 4 and 5 are not yet measured and are
marked OPEN rather than scored, because scoring an unrun prediction is the same
error as reporting an unrun check.

---

## P1 — the bibliographic screen denominator ✅ CORRECT, both halves

**Predicted:** the 1,375 bibliographic records were never screened and the
"2 of 2" recall was registry-internal. Then: 0 additional eligible trials (70%
confidence); at least one randomised-ring record outside the NCT set (60%).

**Found:** exactly that. `candidates_screened: 63` was the ClinicalTrials.gov
set alone and nothing in the object said so. Screening 1,443 deduplicated
records returned **0 additional eligible trials** and **2 randomised vaginal-ring
records naming registrations outside the retrieved set** — NCT02404038
(UChoose) and NCT01796613 (Ring-Plus). Both were read: contraceptive-ring
trials with no dapivirine arm.

Both halves right, and the second half is the one that mattered — a recall check
that returns candidates is worth something, a recall check that returns none is
indistinguishable from a broken one.

## P2 — AACT ghost count ⬜ OPEN

Not run. The AACT snapshot is located and its tables are mapped, but the ghost
enumeration is rank 4 in the plan and rank 3 was taken first.

## P3 — participant flow closing RoB D3 ⚠️ OUTCOME RIGHT, REASONING WRONG

**Predicted:** per-arm started/completed counts are present for both trials, so
signalling question 3.1 becomes answerable (75%). And: *"I predict this does NOT
change the domain judgement to LOW, because 3.2–3.4 concern differential
missingness and dependence on the true value, which the flow table alone cannot
answer"* (80%).

**Found:** the first half is right. 3.1 is answerable and answers YES for both
trials — 1952/1959 (99.64%) and 2626/2629 (99.89%).

**The second half is wrong, and wrong in a way that matters.** RoB 2's Table 10,
as implemented in this repo's own `ssot/rob2_algorithm.py:122`, reads:

    if _i(a, YPY):
        return LOW, 'Table 10 row 1: 3.1 = Y/PY -> Low'

3.2, 3.3 and 3.4 are reached **only** when 3.1 is No, Probably no, or No
information. With 3.1 = Yes the domain is LOW on row 1 and the other three
questions are never asked. My prediction reasoned from questions the algorithm
does not reach.

The domain did not move in this session — but because I declined to move it, not
because the algorithm would have refused. **The correction runs against me:** the
evidence I gathered probably *does* move D3 to LOW, and D3 is one of the two
domains the GRADE risk-of-bias downgrade names by name. That makes routing this
to the second assessor more important than I had thought when I wrote the
prediction, not less. A change that improves our own rating, discovered by the
person who gathered the evidence, is exactly the case the two-assessor rule
exists for.

## P4 — citation chasing ⬜ OPEN

Not run.

## P5 — the estimand mismatch ⬜ OPEN

Not run.

## P6 — what the four-reader renderings expose ✅ CORRECT, both halves

**Predicted:** the HTA rendering will force disclosure that the review's
comparator is not the decision-relevant comparator, and that this is nowhere
stated in the object (90%). The guideline EtD will have more empty cells than
filled (85%).

**Found:** both. The comparator problem is now the HTA rendering's opening
section, and the head-to-head registrations it names — NCT03965923, NCT04140266,
NCT03593655 — were found by this review's own search and excluded on outcome,
which is a sharper statement than I predicted: the trial an HTA body needs has
not been done, and we can name the near-misses.

The EtD came out **7 of 12 not addressed against 5 informed or partially
informed**. More empty than filled, as predicted.

---

## Two things that happened which no prediction covered

**The ClinicalTrials.gov guard could not fail.** Both registry queries recorded
`status: OK` with `reported_count: null`, because `countTotal=true` was never
requested. Re-run with counts and paging the answer was 52 and 63 — identical to
what had been recorded. The figure was right and the check was absent, and only
one of those two was ever in our control.

**The result-group index means different arms in different modules of one
registration.** On NCT01539226 the baseline, participant-flow and adverse-event
modules put placebo at index 000; the outcome module puts dapivirine there. On
NCT01617096 all four agree. An extractor joining flow to outcome on the index —
the obvious join — inverts one trial and not the other and returns a complete,
plausible, wrong 2×2. I did not predict this because I did not know it was
possible.

**And a scoring note on scoring itself.** Three of the six predictions are still
open. The two that scored clean (P1, P6) were about things I had already half
seen while reading the store; the one that scored badly (P3) was the only one
that required me to reason about a procedure I had not opened. That is a small
sample and it points the obvious direction: predictions about what a document
says are cheap, predictions about what an algorithm does are the ones worth
logging.
