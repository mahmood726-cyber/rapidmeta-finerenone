# The data is in ClinicalTrials.gov. It is just not where people look.

**A finding worth giving away, because it costs us nothing and it is actionable for anyone
doing evidence synthesis.**

## The claim

Querying ClinicalTrials.gov's **`outcomeMeasures`** section and concluding "the data isn't
available" is wrong often enough to matter. For a large class of outcomes — anything that was
a *safety* signal rather than the trial's efficacy endpoint — the numbers are in the
**`adverseEventsModule`**, in exactly the events-and-denominator form a meta-analysis needs.

We hit this while measuring something else, and it moved a recovery rate from **1% to 67%**
without touching the data source. One query field.

## The worked example

A 2026 systematic review of **heart-failure events with DPP-4 inhibitors** tabulates, per
trial, the events and denominators in each arm — the ordinary shape of a binary-outcome
extraction:

| trial | events (drug) | n | events (control) | n |
|---|---|---|---|---|
| CARMELINA | 209 | 3494 | 226 | 3485 |
| CAROLINA | 112 | 3023 | 92 | 3010 |
| SAVOR-TIMI | 289 | 8280 | 228 | 8212 |

Query those trials' **outcome measures** and you find almost none of it. These are diabetes
trials. Their registered and posted primary outcomes are **glycaemic** — HbA1c change,
proportion reaching target — because that is what they were designed to show. Heart failure
was never a posted outcome measure.

Query the **adverse-events module** of the same registration and it is there. NCT00622284:

```
seriousEvents → term: "Cardiac failure"
    groupId EG000 (Linagliptin)  numAffected 3   numAtRisk 776
    groupId EG001 (Glimepiride)  numAffected 2   numAtRisk 775
```

Events and denominators, per arm, structured, free. The same shape as the review's table.

## Why this is not a small technical note

**It plausibly explains part of why "you need the full text" is treated as given.** A team
that queries outcome measures, finds glycaemic endpoints, and concludes the cardiovascular
data is not in the registry will go to the publication — and will then reasonably believe that
full-text access is a *requirement* rather than a convenience. The belief is well-founded
given the query, and the query is the wrong one.

The asymmetry is worth stating plainly:

- **Efficacy outcomes** are usually in `outcomeMeasures`, because they are what the trial
  registered.
- **Harms, and any outcome that was not this trial's endpoint but is someone else's review
  question**, are usually in `adverseEventsModule`.
- A review asking about a *harm* — or asking about an outcome that was secondary or
  unregistered in the source trials — is systematically looking in the wrong section.

That is a large fraction of safety reviews and of any review repurposing efficacy trials to
answer a different question, which is most reviews of drug class effects.

## What to do about it

For anyone extracting from ClinicalTrials.gov, three concrete points:

1. **Query both sections.** `resultsSection.outcomeMeasuresModule` *and*
   `resultsSection.adverseEventsModule`. The second is not a fallback; for harm outcomes it is
   the primary location.
2. **`numAtRisk` is the denominator you want.** It is per event-group and it is not always the
   randomised n — it is the number at risk in that safety population, which is the correct
   denominator for that count and often differs from the ITT figure a publication reports.
3. **Search the MedDRA term, not the review's phrasing.** The review says "heart failure
   events"; the registry says `Cardiac failure`, `Cardiac failure congestive`,
   `Cardiac failure acute`. A term-level search that does not expand across these will
   under-recover.

## Limits

- One review, one drug class, and the trials were well-registered industry studies. The
  effect will be smaller where trials post no results at all.
- `adverseEventsModule` exists only for trials that posted results. Where a trial posted
  nothing, neither section helps.
- Adverse-event counts are **not** always identical to a publication's adjudicated counts —
  the registry reports investigator-reported terms, and a review using adjudicated events may
  legitimately differ. **A recovered number is not automatically the same number**, and that
  distinction belongs in any extraction that uses this route.

## How we found it

Not by looking for it. A data-recovery measurement reported **1 exact match in 116** and read
as "ClinicalTrials.gov does not have these numbers". That number was implausible — these are
large, well-documented cardiovascular outcome trials — and an implausible proportion is a
statement about the instrument before it is a statement about the world. Checking the
registration by hand found the events immediately.

The measurement then went **1% → 3% → 67%** across three fixes, none of which touched the
data source.
