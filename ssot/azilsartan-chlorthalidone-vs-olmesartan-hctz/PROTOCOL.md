# Protocol - Azilsartan medoxomil plus chlorthalidone against olmesartan medoxomil plus hydrochlorothiazide on change in clinic systolic blood pressure: the two trials that share both arms

> **What in this document is specific to this review, and what is not.** Sections 1,
> 3, 8, 9 and 12 are built from facts recorded on this topic and differ genuinely
> between reviews. Sections 4 to 7, 10 and 11 follow the house standard and their
> wording is shared with other protocols in this repository. This is stated because a
> protocol that does not distinguish the two reads as more particular than it is.

## 1 - Review question

The question recorded on this topic, quoted exactly:

> In Azilsartan medoxomil plus chlorthalidone against olmesartan medoxomil plus hydrochlorothiazide on change in clinic systolic blood pressure: the two trials that share both arms, what is the effect on mmHg change from baseline in trough, sitting, clinic systolic blood pressure?

## 2 - Estimand

**Primary outcome as recorded:** mmHg change from baseline in trough, sitting, clinic systolic blood pressure

**Definition as recorded:** mmHg change from baseline in trough, sitting, clinic systolic blood pressure

**Effect measure:** MD

One estimand is primary. Where several are reported, the one named above governs and
the others are secondary; the choice is fixed here rather than after the results are
seen.

## 3 - Eligibility, as the record actually constrains it

**Trials already held on this topic (2), by registration id,
which is the only identity key used:**

- NCT00846365
- NCT01033071

**Scope decisions recorded on this topic:**

*No scope decisions are recorded on this topic. Eligibility is therefore stated at the level the record supports, and this section must not be read as a summary of decisions already taken.*

**Populations or arms explicitly excluded:**

*No exclusions are recorded on this topic.*

**Eligible but not contributing:**

- [{"nct": "NCT00591578", "reason": "Azilsartan medoxomil against VALSARTAN -- a different comparator, so not the contrast this page answers."}, {"nct": "NCT00818883", "reason": "Azilsartan + chlorthalidone against azilsartan + hydrochlorothiazide -- the drug against ITSELF on a different partner diur
- Held a LIST where the generator reads blk.get("studies") -- a mapping with a studies sequence. Entries preserved unchanged under studies. A SHAPE THE CONSUMER CANNOT READ IS THE SAME DEFECT AS A FIELD IT CANNOT FIND.

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

- **primary:** mmHg change from baseline in trough, sitting, clinic systolic blood pressure - mmHg change from baseline in trough, sitting, clinic systolic blood pressure

**2 of 2** trials carry per-outcome data on
this topic. Where that count is below the number of trials, the shortfall is a known
limit of this review and is reported as such rather than being absorbed silently.

## 9 - Risk of bias, and what was not read

**Tool:** RoB 2

**Assessed per:** not recorded

**Sources read for the assessment (0):**

*None recorded.*

**Sources NOT read (0):**

*None recorded as unread - which is not the same as everything having been read, and must not be reported as though it were.*

This section is pre-specified because an assessment's blind spots are worth more
stated in advance than discovered afterwards.

## 10 - Synthesis

House standard, shared wording. Random-effects inverse-variance pooling on the log
scale for ratio measures, back-transformed for presentation. Heterogeneity reported
as tau-squared alongside I-squared, because I-squared is a proportion and not an
amount. With fewer than 10 studies, DerSimonian-Laird is not used; REML or
Paule-Mandel is. Prediction intervals use t with k-1 degrees of freedom and are
undefined for k below 2.

**k is 2 on this topic**, so the small-k rules above are
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
