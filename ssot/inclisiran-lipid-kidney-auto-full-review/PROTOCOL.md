# Protocol - Inclisiran for elevated low-density lipoprotein cholesterol in HeFH, ASCVD or ASCVD-risk equivalents

> **What in this document is specific to this review, and what is not.** Sections 1,
> 3, 8, 9 and 12 are built from facts recorded on this topic and differ genuinely
> between reviews. Sections 4 to 7, 10 and 11 follow the house standard and their
> wording is shared with other protocols in this repository. This is stated because a
> protocol that does not distinguish the two reads as more particular than it is.

> ## ⚠ THIS IS AN UNANCHORED DRAFT. IT IS NOT A REGISTRATION.
>
> It becomes a registration when it is committed, pushed to a public branch, and
> anchored in a public transparency log - and only then, and only before the first
> query for this topic is attempted. The pipeline removes this banner at that point.

## 1 - Review question

The question recorded on this topic, quoted exactly:

> In Inclisiran for elevated low-density lipoprotein cholesterol in HeFH, ASCVD or ASCVD-risk equivalents, what do the contributing trials show?

## 2 - Estimand

**Primary outcome as recorded:** Multiple trial-declared outcomes: Percent Change in LDL-C From Baseline To Day 510 | Percentage Change in LDL-C From Baseline to Day 510

**Definition as recorded:** Multiple trial-declared outcomes: Percent Change in LDL-C From Baseline To Day 510 | Percentage Change in LDL-C From Baseline to Day 510

**Effect measure:** MD

One estimand is primary. Where several are reported, the one named above governs and
the others are secondary; the choice is fixed here rather than after the results are
seen.

## 3 - Eligibility, as the record actually constrains it

**Trials already held on this topic (3), by registration id,
which is the only identity key used:**

- NCT03397121 - ORION-9
- NCT03399370 - ORION-10
- NCT03400800 - ORION-11

**Scope decisions recorded on this topic:**

- SCOPE:three-estimands-never-merged
- SCOPE:the-label-on-the-quantity-is-not-the-quantity
- SCOPE:publication-two-component-first-event-composite
- SCOPE:drug-wide-pivotal-not-heart-failure
- SCOPE:no-number-needed-to-treat

**Populations or arms explicitly excluded:**

*No exclusions are recorded on this topic.*

**Eligible but not contributing:**

- note
- studies

**Populations present in a trial but deliberately not pooled here:**

*None recorded on any trial in this topic.*

## 4 - Information sources

Five sources, named honestly:

1. **PubMed**, via NCBI E-utilities.
2. **Europe PMC**, via its REST search.
3. **ClinicalTrials.gov**, API v2.
4. **An ICTRP route, served by ISRCTN.** ISRCTN is a route to some ICTRP-registered
   trials and **is not ICTRP**. It is recorded under its own name for that reason.
5. **Guideline bodies as a source class**, enumerated from the GIN membership
   registry, which lists **136** bodies. GIN is an index and **an index is not a
   source**: not one of its 136 records carries an external URL, so it supplies a
   denominator and no addresses.

**There is no Embase search.** No Embase licence is held. This is stated in every
protocol rather than omitted, because a reader who is not told assumes it was
searched.

Each source returns exactly one of three outcomes per query: **EXECUTED**, **EMPTY**,
or **FAILED**. A non-200 response is FAILED and never carries a record count of zero,
because a failure that reports zero is indistinguishable from a search that found
nothing.

**Guideline coverage is reported as a fraction with its denominator, never as a
checkmark**, and "all guideline bodies" is not a claim any search here supports.

## 5 - Search strategy

The executed query strings, the time each was attempted, the time each executed, and
the count returned are recorded in `SEARCH-RECORD.json` beside this file. The record
is written after execution and anchored, so both ends of the operation carry a time
supplied by someone other than us.

## 6 - Study selection

Records are screened against section 3. A trial with no registration id cannot be
matched and is listed as unmatched rather than dropped, because an item that fails to
join is a fact about the join and not about the world.

## 7 - Data extraction

Extraction is keyed on the registration id. Where a field is absent it is recorded as
absent; **a missing field must never fall through to the value that flatters the
review.**

## 8 - Outcomes

- **primary:** Multiple trial-declared outcomes: Percent Change in LDL-C From Baseline To Day 510 | Percentage Change in LDL-C From Baseline to Day 510 - Multiple trial-declared outcomes: Percent Change in LDL-C From Baseline To Day 510 | Percentage Change in LDL-C From Baseline to Day 510

**3 of 3** trials carry per-outcome data on
this topic. Where that count is below the number of trials, the shortfall is a known
limit of this review and is reported as such rather than being absorbed silently.

## 9 - Risk of bias, and what was not read

**Tool:** RoB 2 (Cochrane risk-of-bias tool for randomized trials)

**Assessed per:** RESULT, not trial -- Handbook 8.2

**Sources read for the assessment (3):**

- ClinicalTrials.gov API v2 NCT03397121 -- ORION-9, n=482, RANDOMIZED, DOUBLE [participant, care provider], arms Inclisiran | Placebo, TWO co-primaries
- ClinicalTrials.gov API v2 NCT03399370 -- ORION-10, n=1561, same design, arms Inclisiran | Saline Solution, TWO co-primaries
- ClinicalTrials.gov API v2 NCT03400800 -- ORION-11, n=1617, same design, arms Inclisiran | Saline Solution, TWO co-primaries

**Sources NOT read (70):**

- T
- h
- e
-  
- O
- R
- I
- O
- N
-  
- p
- u

This section is pre-specified because an assessment's blind spots are worth more
stated in advance than discovered afterwards.

## 10 - Synthesis

House standard, shared wording. Random-effects inverse-variance pooling on the log
scale for ratio measures, back-transformed for presentation. Heterogeneity reported
as tau-squared alongside I-squared, because I-squared is a proportion and not an
amount. With fewer than 10 studies, DerSimonian-Laird is not used; REML or
Paule-Mandel is. Prediction intervals use t with k-1 degrees of freedom and are
undefined for k below 2.

**k is 3 on this topic**, so the small-k rules above are
binding here rather than hypothetical.

## 11 - Certainty of evidence

GRADE, following the Cochrane Handbook chapter 14. Randomised evidence starts HIGH and is rated down with reasons.

## 12 - What this protocol does not establish

- It does not establish that the search was **complete**. It fixes what will be
  searched and how the result will be recorded.
- It does not establish **guideline coverage**. Source 5 reports a fraction against
  the GIN denominator of 136, and most bodies are not resolved to a queryable
  endpoint at all.
- It does not make this review **prospective**. Trials are already held on this
  topic, so the search is retrospective with respect to them. What the registration
  fixes is the protocol, before the search that follows it.
- A git commit timestamp is **author-supplied and forgeable**; this was demonstrated,
  not assumed. Only the transparency-log times are independent of us.

## 13 - Amendments

None at this registration commit. Amendments are recorded as further commits to this
file, and the full history rather than only its head is what the review page shows.
