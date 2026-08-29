# New class: AN EXECUTED SEARCH IS NOT A VALID ONE

**Sibling of *a 200 is not a document* and *a 000 is not a paywall*.**
Recorded 2026-08-29 from `sglt2-mace-cvot-review`.

## The statement

**A query that runs and returns a number is indistinguishable, in the record, from a query
that means something.** Success at the transport layer is not success at the question layer,
and a three-count law that records EXECUTED / EMPTY / FAILED measures only the transport.

## The instance

`sglt2-mace-cvot-review` sent **`Multiple trial-declared outcomes Time`** — four generic
English words, naming no drug and no condition. It was built from the topic's `title`, which
is not a title but four ClinicalTrials.gov outcome-measure strings joined with `|`.

```
PubMed              EXECUTED   78,608
Europe PMC          EXECUTED  125,695
ClinicalTrials.gov  EXECUTED       22
ISRCTN              EXECUTED       42
```

**Four EXECUTED, nothing FAILED, nothing EMPTY.** A perfectly clean row. The record had no
way to express what was wrong, because nothing was wrong with the transport.

## Why it is more dangerous than a failure

A malformed query that **fails** is safe: `icosapent-lipid` sent an unbalanced bracket,
ClinicalTrials.gov returned HTTP 400, and the record says FAILED. The defect announced
itself.

A malformed query that **succeeds** is silent, and it is silent in the flattering direction —
it contributes a clean row to the coverage statistics and a large-looking count to the
evidence base.

## The trigger, phrased so it fires without knowing the topic

**Before recording a search as executed, read the query string that was actually sent and
ask whether it names the thing being reviewed.** If it contains no intervention and no
population — if you could not tell from the query alone which review it belongs to — the
count is about the transport, not the topic.

A second, purely syntactic trigger: **a count that is implausibly large is a query defect
until shown otherwise.** 125,695 hits for a two-trial SGLT2 review is not a rich literature;
it is evidence that the query matched the language, not the subject.

## Where the existing law falls short, stated plainly

The three-count law was built to stop a failure being recorded as a zero, and it does that.
It has **no category for "ran, and meant nothing"**, so this class is invisible to it. That
is a gap in the instrument, not in the data, and naming it is the first repair.

## The remedy, which is method rather than cleanup

1. **Record the original query, its result, and that it was malformed.**
2. **A dated protocol amendment** naming the defect and the corrected query, committed
   **before** the corrected query runs.
3. **Re-run and publish both results side by side. Never replace the first with the second.**

Changing a strategy after seeing its result is the defect. Changing it after **disclosing**
the result is method. The difference is the disclosure, not the change — which is precisely
what committing the protocol first buys, and the reason to do it at all.

## Related

- *A page name is not an artefact identity* — same family: something that looks like an
  identifier and is not.
- *A scan reports where it looked, not the population it claims to cover* — this is that
  lesson at the level of a single query rather than a corpus.
- `CORRECTION-E7-2026-08-29.md` — the accusation I got wrong on the same day, by reading
  eight lines of a gate's output instead of all of it.
