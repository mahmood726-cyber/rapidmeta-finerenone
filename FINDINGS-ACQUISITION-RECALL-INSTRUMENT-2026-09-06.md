# Correction: the Galli "21/21 recall" and the NCT dedup are built on unreliable instruments

**Date:** 2026-09-06. **Status:** retraction of a number reported earlier the same session.

## What was claimed

`scripts/galli_recall.py` reported **FOUND 21/21** — every Galli 2025 GLP-1 CV trial reachable
by the Europe PMC RCT search — and it was reported and acted on as a solid recall number.

## Why it is not trustworthy

The recall test was a per-trial membership sub-query `(BASE) AND (identifying terms)`, and for
most trials the identifying term was the trial's **acronym**. **Eight of the 21 acronyms are
ordinary English words** — LEADER, SELECT, SOUL, GRADE, FLOW, SUMMIT, STRIDE, FIGHT — so
`(BASE) AND ("SELECT" AND semaglutide)` matches any semaglutide CV RCT paper that contains the
word "select", not the SELECT trial. A hit is *consistent with* the trial being present; it is
not *proof* of it. Building the precision funnel surfaced this directly: the top records for
`("LEADER" AND liraglutide)` are 2025–26 semaglutide and albiglutide papers, none of them the
LEADER trial.

So the honest split is:
- **Reliably confirmed** (distinctive acronym / distinctive author): ELIXA, SUSTAIN-6, EXSCEL,
  HARMONY OUTCOMES, PIONEER-6, REWIND, AMPLITUDE-O, STEP-HFpEF(/DM), LIVE-Jorsal, Kyhl — the
  acronym or author name is not an ordinary word.
- **Consistent but UNPROVEN** by this method: LEADER, SELECT, SOUL, GRADE, FLOW, SUMMIT, STRIDE,
  FIGHT, Chen, Zhang — matched on a common word or a common surname.

**21/21 is withdrawn.** The trustworthy claim is "≈11 reliably confirmed present, the rest
consistent-but-unproven", pending a proper measurement.

## The NCT dedup is unreliable for the same class of reason

`scripts/precision_funnel.py` deduplicates records to trials by the NCT ids text-mined into
each Europe PMC record. But a record cites **several** NCTs (a pooled or design paper: e.g. one
record carried `['NCT01720446','NCT02692716']`), and first-one-wins mis-assigns — LEADER,
SUSTAIN-6 and PIONEER-6 all "resolved" to `NCT01720446`, and LEADER's real registration is
`NCT01179048`. So the funnel's `665 trials`, `164 eligible`, and its `10/12` recall are **not
trustworthy numbers** and are not to be quoted.

## The fix (not yet done)

- **Recall** must be measured against an **authoritative NCT per trial** (verified individually,
  or marked unregistered for the pre-registration small trials), then membership tested by that
  NCT appearing in a record's text-mined set — not by an acronym that may be a common word.
- **Dedup** needs a single authoritative trial id per record (the record's own registration
  cross-reference), not a regex over every NCT the abstract happens to mention.

## Why this is recorded rather than quietly re-run

It is the session's recurring shape: a broken instrument produces a confident number, and the
number is worse than none because it gets built on. The 21/21 was called "the most valuable
number of the session" and a plan was set on it. Retracting it in the record — before four more
adapters were written against it — is the correction. The adapter's own five-field records and
its `NOT_RUN`/`RAN_ERROR` discipline stand; what fails here is the *acronym recall proxy* and
the *text-mined-NCT dedup*, and both are named so neither returns silently.
