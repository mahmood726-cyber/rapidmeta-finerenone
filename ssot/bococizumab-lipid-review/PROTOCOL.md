# Protocol - Bococizumab and LDL cholesterol

> ## ⚠ THIS IS AN UNANCHORED DRAFT. IT IS NOT A REGISTRATION.
>
> Drafted 2026-08-27 and committed **only so the work is preserved** when the
> registration stream was paused. Three things that a registration has, this does not:
>
> - **No transparency-log anchor exists for it.** Nothing has been submitted to Rekor.
> - **No search has been run against it.** The ordering test it describes below —
>   protocol anchored before the first query — has NOT been performed.
> - **Its own Status line, written by the drafting model, calls it a registration.**
>   That line is wrong until the two steps above happen, and is left in place rather
>   than edited so that the draft is preserved exactly as generated.
>
> To become a registration this file must be committed, pushed, anchored in the public
> log, and only then searched, with the log index and the first query time recorded.
> Until then it is a proposal. See `ssot/registration/PAUSED-POSITION.md`.

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash is the strong half of that record: the content is
immutable under it, so this text cannot be altered later without producing a
different hash, and anyone can check that much without asking us.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** Both the author and the committer date on a git commit are supplied
by whoever makes the commit and can be set to any value; GitHub stores and
displays what it is given, and an unsigned commit carries nothing further.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of
the signing key, and a worked example are at
[`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the
limitation plainly as well: the log time is independent of us, the key custody is
not. A stranger can verify the text existed by the log time and that we signed it;
a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review publishes
is that this commit precedes the first executed query -- the first *attempt*, not
the first success, because reporting only the successful execution would move the
first-query time later and flatter the claim. The search record is anchored
afterwards, so two third-party times bracket the operation: the protocol anchor
before the first query attempt, and the search-record anchor after the search has
been executed and recorded.

Both execution times are read from the search lane's own clock. The databases
return records and hit counts, not independent execution times, so no part of the
ordering is timestamped by a database. The sequence is therefore auditable and
internally consistent only when the two external anchors are checked against the
recorded lane times. It is recorded here as less than proof.

The anchor proves **when this text was written** and cannot prove the trials had
not already been seen. A timestamp bounds when, never what was known.

---

## 1 - Review question, in PICO

This topic already holds 6 trials:
NCT01968954, NCT01968967, NCT01968980, NCT02100514, NCT02135029, and
NCT02458287. The question is being authored after that evidence was assembled.
However carefully it is written now, this is a retrospectively registered
protocol, not an instrument that can prove ignorance of the evidence base before
registration. The anchor proves when this text existed and cannot prove the
trials had not already been seen.

| | |
|---|---|
| **Population** | Adults with primary hyperlipidaemia, mixed dyslipidaemia, or heterozygous familial hypercholesterolaemia. |
| **Intervention** | Bococizumab, including PF-04950615 and RN316 names and registered dose variants. |
| **Comparator** | Placebo or an active lipid-lowering comparator. |
| **Outcome** | Percent change from baseline in LDL cholesterol at week 12. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with primary hyperlipidaemia, mixed dyslipidaemia
or heterozygous familial hypercholesterolaemia, what is the effect of
bococizumab compared with placebo or an active lipid-lowering comparator on the
percent change from baseline in LDL cholesterol at week 12?

## 2 - Estimand, stated in advance

The estimand is the **between-arm difference in percent change from baseline in
LDL cholesterol at week 12**, expressed as a mean difference in percentage
points, with the randomised participant as the unit of analysis.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is pre-specified because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly about bococizumab and still fail this review's
eligibility because it reports something else. Specifically and in advance:

- An absolute LDL cholesterol concentration at week 12 is not the percent change
  from baseline.
- A percent change at a timepoint other than week 12 is not this estimand unless
  week 12 is also reported for the same comparison.
- A dichotomous lipid target, responder outcome, adverse-event outcome,
  pharmacokinetic outcome, immunogenicity outcome, or device-use outcome is not
  this estimand.
- A cardiovascular event outcome is not this estimand, even if collected in a
  bococizumab trial.

## 3 - Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with
primary hyperlipidaemia, mixed dyslipidaemia or heterozygous familial
hypercholesterolaemia; it randomises bococizumab against placebo or an active
lipid-lowering comparator; it reports percent change from baseline in LDL
cholesterol at week 12; and the comparison can be mapped to a randomised arm
contrast.

**Exclude** on any single failed axis -- population, intervention, comparator,
measure, or design -- and record which axis failed and what the study reports
instead. Section 7 will classify records against these axes and no others.

An axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

Populations narrower than the question are **not** indirect on that ground alone;
narrowness is recorded and carried into the GRADE indirectness domain rather
than used as an exclusion.

## 4 - Information sources

Only two sources will be searched: PubMed through NCBI E-utilities and
ClinicalTrials.gov API v2.

Embase was **not** searched. CENTRAL was **not** searched. Web of Science was
**not** searched. Scopus was **not** searched. This is not a comprehensive
search. The cost of that omission is that conference records, non-MEDLINE
indexing, trial reports captured only in CENTRAL, and citation-database-only
records may be missed. Any resulting absence is a limitation of the search, not
evidence that such records do not exist.

## 4A - Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications by:
matching explicit NCT identifiers in PubMed records; reading PubMed links exposed
from the registry record; reading registry references whose
`reference_type='result'`; and then checking that the linked publication describes
the same trial identity, population, arms, and LDL cholesterol outcome. A link is
accepted only after identity is checked; the presence of a PMID or citation field
is not enough.

Two measured failure modes on this corpus are fixed here before execution.
First, PubMed silently drops trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Second, registry `reference_type='result'` links can point at the wrong
paper, which is worse than a missing link because a wrong link looks like a
successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is linked analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept under 20 Boolean operators
because the interface refuses longer registered strings, and an unexecutable
registered string would force a departure on the first attempt.

**PubMed through NCBI E-utilities**

```
("bococizumab"[tiab] OR "PF-04950615"[tiab] OR "RN316"[tiab])
AND ("LDL"[tiab] OR "low density lipoprotein"[tiab] OR hyperlipidemia[tiab] OR hypercholesterolemia[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date.

**ClinicalTrials.gov API v2**

```
query.intr=bococizumab OR PF-04950615 OR RN316
query.term=LDL OR hyperlipidemia OR dyslipidemia OR hypercholesterolemia
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

Filters: none on study phase, geography, sponsor, sex, age subgroup, date, or
posted-results status.

## 5A - How this search can fail, decided in advance

If the search reproduces the held set, that will be read as a searched-for
result rather than a convenient match to a pre-existing object. The held set is
not evidence that the search was unnecessary; it is the thing the search was
asked to test.

If the search returns additional eligible trials, that will be read as a finding
about the review. Each additional trial will be named and included or excluded on
one of the axes declared in section 3: population, intervention, comparator,
measure, or design.

If the search returns fewer trials than the object holds, that will be read as a
finding about the search, never reported as the review being wrong. Worked
example: the finerenone-cv registry query missed FIGARO-DKD (NCT02545049), a
pivotal trial, because it registers its condition as "Diabetic Kidney Disease"
alone while its sibling FIDELIO-DKD registers "Chronic Kidney Disease". A narrow
query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** -- the cross-family
rule is a requirement, not a preference, because two instances of one model is
one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract or registry summary, then full
text or full registry record. **Each screener's decision is recorded per record
at the stage it was applied**, together with the reason. Both screeners'
decisions are published, not only the reconciled outcome, along with the
agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication
where linked, year, design, population, arms, comparator identity, analysed
denominator and randomised total separately, the week-12 LDL cholesterol percent
change result by arm where reported, and the published between-arm effect
estimate with its interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or outcome module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No result is derived from a graph unless the graph extraction is explicitly
recorded as such. No count is derived from a percentage. No outcome definition is
inferred from a title. Identifiers are resolved by lookup, never from recall.

Each candidate record is classified only against the section 3 axes: population,
intervention, comparator, measure, and design. Any axis read from a registry
title remains provisional until the registered primary outcome measure is read
from the outcome module, because a title is not an outcome definition.

Where two populations exist for one outcome -- for example a full analysis set
and a randomised set -- both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** percent change from baseline in LDL cholesterol at week 12.

**Read and reported but not pooled unless they instantiate the primary
estimand:** other LDL cholesterol timepoints; non-HDL cholesterol; HDL
cholesterol; triglycerides; apolipoprotein B; lipoprotein(a); lipid target
attainment; adverse events; immunogenicity outcomes; cardiovascular outcomes;
and device-use outcomes. They are shown when recovered because a reader should
see them; they are not pooled as the headline because the review's estimand is
week-12 percent change in LDL cholesterol.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: percent change from baseline in LDL cholesterol at week 12.
One trial may therefore carry a different judgement for this result than it
would for its own primary endpoint, and that is the intended behaviour of the
tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat randomised comparison estimates. The adherence
variant is not used, and no result assessed under one variant will be reported
as though assessed under the other.

**Domains.** All five, each reached through the RoB-2 signalling questions
rather than by overall impression, with a recorded answer per signalling
question, a **domain judgement** of low / some concerns / high, and a rationale
naming the evidence it rests on:

1. Bias arising from the randomization process
2. Bias due to deviations from intended interventions (effect of assignment)
3. Bias due to missing outcome data
4. Bias in measurement of the outcome
5. Bias in selection of the reported result

An **overall judgement** follows the standard RoB-2 algorithm: low only if every
domain is low; high if any domain is high or if multiple domains raise some
concerns in a way that substantially lowers confidence; some concerns otherwise.

**Assessors.** Two independent assessors **from different model families**. Two
instances of one model is one assessor run twice and its agreement statistic is
meaningless, so same-family duplication does not satisfy this requirement.
Neither assessor may be the agent that assembled the canonical object, because
assessing one's own extraction is not an independent assessment.

**Both sets of judgements are recorded and published** -- per domain, per
assessor, with rationales -- not only the reconciled outcome. The **per-domain
agreement rate is published as measured**. Agreement on RoB-2 domains is expected
to be substantially lower than agreement on screening; if that proves true it is
a finding worth reporting and it will not be smoothed. **Disagreements are
adjudicated by a named human**, and the adjudication and its reason are recorded
per disagreement.

**Evidence admissible to an assessment.** The trial's registry record including
its protocol and statistical analysis plan where posted, the primary publication
and its supplement, and the posted results module. A judgement made from an
abstract alone is not the same act as one made from a protocol, so **the sources
actually consulted are recorded per domain**, and a domain judged without access
to the protocol is marked as such rather than presented as equivalent.

**Relationship to the recorded bias features.** Any object-held bias-relevant
features are **inputs to the assessment and never substitutes for a domain
judgement**. No existing prose in the object may stand in for a signalling
question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any reasoning from recorded features. When it
does, the review will state **whether the GRADE rating moves and why -- and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment is registered by this protocol. Performing
it later **executes this section rather than amending it**, and the object will
record that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis on the mean-difference scale in percentage points,
inverse-variance weighted.

**Pre-specified, so that reporting a disagreement between methods is a
commitment rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool.
- An **estimator comparison** -- DerSimonian-Laird, REML, Paule-Mandel -- is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval,
and Q with its degrees of freedom and p value. I-squared is reported with the
caveat that at small k a low value reflects imprecision as much as agreement.

## 10A - Network geometry and what it forbids

This is a network meta-analysis object for the comparison structure, even though
the outcome estimand is a continuous lipid measure. The topology below is
derived from the object's own arms and is an established fact, not an assumption:

- Nodes (7): Bococizumab; Bococizumab (PF-04950615; RN316); Bococizumab
  (PF-04950615;RN316); Bococizumab 150mg; Bococizumab 75mg placebo; Placebo;
  placebo.
- Edges: 5.
- Connected: False.
- Independent loops (E - V + 1): -1.

There are **ZERO LOOPS**. The object reports `Connected: False`, so no
whole-network indirect comparison may be asserted across disconnected
components. Within any connected component, indirect comparisons are computable
because the network is connected at that component level, but the consistency
assumption they rest on **CANNOT BE TESTED** -- not "was not tested", cannot be,
by the geometry. Node-splitting and design-by-treatment interaction are
unavailable, and their absence must never be reported as consistency having been
checked.

No SUCRA or ranking will be reported. Publication bias is **NOT ASSESSABLE**
rather than not serious, and GRADE carries incoherence as untestable.

A head-to-head trial between two non-comparator nodes would add a direct edge
between treatments that are currently linked, if at all, only through comparator
paths or isolated components. If that edge closed a loop, the network would gain
the first geometry capable of testing local incoherence for that loop; if it only
joined disconnected components without forming a loop, it would improve
connectivity but still would not make consistency testable.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out; the estimator comparison above;
exclusion of records whose comparator mapping is active rather than placebo; and
exclusion of records where the reported result must be transformed onto the
primary scale rather than read directly. These are reported as sensitivity to the
primary pool, never as replacements for the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot and Egger's regression for the pairwise continuous-outcome pool where
the number of studies makes the display or model meaningful. **Pre-specified
caveat:** below approximately ten studies these tests have almost no power and
the Cochrane Handbook advises against interpreting them. Where k is below that
threshold the tests may still be computed for completeness, and will be reported
as computed values, explicitly not as evidence about small-study effects.

For the network, publication bias is **NOT ASSESSABLE** rather than not serious.
Where publication bias cannot be assessed, the GRADE domain will read *not
assessable* rather than *not serious* -- the two are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

For this network, incoherence is carried as untestable because the geometry has
zero loops. That limitation is not the same as a completed consistency check.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No completed GRADE assessment is registered by this protocol.
Performing it later executes this section rather than amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

The protocol commit is pushed and anchored in a public transparency log before
the first search query attempt. The executed search record is anchored after the
search, so the two anchor times bracket the operation. The ordering test uses
the earliest query time including a failed attempt, not the first successful
query.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
