# Protocol - AMR101 4 g/day versus placebo for triglyceride lowering

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

**Status: RETROSPECTIVELY REGISTERED BY COMMIT, PUBLIC PUSH, AND TRANSPARENCY-LOG ANCHOR. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds the text: the content is immutable under it, so
this text cannot be altered later without producing a different hash, and anyone
can check that much without asking us. The repository is public, so the text is
readable by anyone at that hash. At registration, this document contains no
search results, no search yields, and no counts from any search.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable -- git author
and committer dates are set by whoever makes the commit and commits here are
unsigned. A transparency-log entry gives an inclusion time set by a third party,
proving something narrow: the text existed no later than the log time.

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

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The ordering test this review publishes
is that this protocol is committed, pushed to the public repository, and anchored
in a public transparency log before the first executed query. The first query
means the earliest query time including a failed attempt, not the first success,
because reporting only the successful execution would move the first-query time
later and flatter the claim. The search record is anchored afterwards, so two
third-party times bracket the operation: the protocol anchor before the first
query attempt, and the search-record anchor after the search has been executed
and recorded.

Both execution times are read from the search lane's own clock. The databases
return records and hit counts, not third-party execution times, so no query time
is timestamped by a database. The sequence is therefore auditable and internally
consistent only when the two external anchors are checked against the recorded
lane times. It is recorded here as less than proof.

The anchor proves **when this text was written** and cannot prove the trials had
not already been seen. A timestamp bounds when, never what was known.

---

## 1 - Review question, in PICO

This topic already holds 2 trials: NCT01047501 and NCT01047683. The question is
being authored after that evidence was assembled. However carefully it is
written now, this is a RETROSPECTIVELY REGISTERED protocol, not an instrument
that can prove ignorance of the evidence base before registration. The anchor
proves when this text was written and cannot prove the trials had not already
been seen. A timestamp bounds when, never what was known.

| | |
|---|---|
| **Population** | Adults with hypertriglyceridemia. |
| **Intervention** | AMR101 (ethyl icosapentate, icosapent ethyl) 4 g/day. |
| **Comparator** | Placebo. |
| **Outcome** | Difference between treatment groups in triglyceride lowering effect. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with hypertriglyceridemia, does AMR101 (ethyl
icosapentate) 4 g/day compared with placebo affect the difference between
treatment groups in triglyceride lowering effect?

## 2 - Estimand, stated in advance

The estimand is the **between-arm mean difference in triglyceride lowering from
baseline**, expressed as AMR101 4 g/day minus placebo on the scale reported for
the registered or published triglyceride outcome, with the randomized participant
as the unit of analysis.

**Quantities that cannot be converted into that estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is fixed before execution because
it is a criterion and not a judgement made after seeing search results. A trial
may be large, well conducted and directly about ethyl icosapentate and still fail
this review's eligibility because it reports something else. Specifically and in
advance:

- A non-triglyceride lipid outcome is not this estimand.
- A triglyceride responder proportion or target-attainment proportion is not a
  between-arm mean difference in triglyceride lowering.
- A cardiovascular event outcome, inflammatory biomarker, pharmacokinetic
  outcome, or safety outcome is not this estimand.
- A dose other than AMR101 4 g/day is not this intervention unless a separable
  4 g/day randomized arm is reported against placebo.
- A non-placebo comparator does not instantiate this comparison unless a placebo
  arm is also available for the AMR101 4 g/day contrast.

Where a publication or registry reports both per-arm changes and a between-arm
contrast, the reported between-arm contrast is extracted rather than recomputed.
Where only per-arm values and their uncertainty are available, any calculation
needed to form the contrast is marked as a derivation and the source inputs are
retained.

## 3 - Eligibility criteria

**Include** a study if all five hold: it is randomised; it enrols adults with
hypertriglyceridemia; it randomizes AMR101 (ethyl icosapentate, icosapent ethyl)
4 g/day; it includes a placebo comparator for that 4 g/day arm; and it reports
the difference between treatment groups in triglyceride lowering effect, or
enough source data to derive the same contrast without changing population,
dose, comparator, lipid analyte, or outcome scale.

**Exclude** on any single failed axis: DESIGN, POPULATION, INTERVENTION,
COMPARATOR, or MEASURE. The failed axis and the reported reason are recorded.
Those are the only exclusion axes for this review. Section 7 will classify
records against these axes and no others.

Populations narrower than the question, including strata defined by baseline
triglyceride concentration, background lipid-modifying therapy, diabetes, or
cardiovascular risk, are not indirect on that ground alone; narrowness is
recorded and carried into the GRADE indirectness domain rather than used as an
additional exclusion axis.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

Only two sources will be searched: PubMed through NCBI E-utilities and
ClinicalTrials.gov API v2.

Embase was NOT searched. CENTRAL was NOT searched. Web of Science was NOT
searched. Scopus was NOT searched. This is not a comprehensive search. The cost
of that omission is that conference records, non-MEDLINE indexed articles,
records captured only in CENTRAL, and citation-database-only records may be
missed. Any resulting absence is a limitation of the search, not evidence that
such records do not exist.

## 4A - Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications by:
matching explicit NCT identifiers in PubMed records; reading PubMed links exposed
from the registry record; reading registry references whose
`reference_type='result'`; and then checking that the linked publication
describes the same trial identity, population, arms, AMR101 4 g/day dose,
placebo comparator, and triglyceride outcome. A link is accepted only after
identity is checked; the presence of a PMID or citation field is not enough.

Two measured failure modes on this corpus are fixed here before execution.
First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Second, registry `reference_type='result'` links can point at the WRONG
paper, which is worse than a missing link because a wrong link looks like a
successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure whose denominator
is LINKED analyses, not all analyses, and therefore it is not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted. Each string is kept under 20 Boolean operators
because the interface refuses more, and a registered string that cannot be
executed forces a departure on the first attempt.

**PubMed topic search, through NCBI E-utilities**

```
("AMR101"[tiab] OR "ethyl icosapentate"[tiab] OR "icosapent ethyl"[tiab] OR Vascepa[tiab])
AND (placebo[tiab])
AND (triglyceride*[tiab] OR hypertriglyceridemia[tiab] OR hypertriglyceridaemia[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab])
```

Filters: none on language, none on date.

**PubMed registry-publication linkage query template, through NCBI E-utilities**

```
"{NCT_ID}"[si] OR "{NCT_ID}"[tiab]
```

The concrete NCT identifier substituted into `{NCT_ID}` is recorded for each
execution. A failed execution still counts as a query attempt for the ordering
test.

**ClinicalTrials.gov API v2**

```
query.intr=AMR101 OR ethyl icosapentate OR icosapent ethyl OR Vascepa
query.cond=hypertriglyceridemia OR hypertriglyceridaemia OR triglycerides
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

Filters: none on study phase, geography, sponsor, sex, age subgroup, date, or
posted-results status.

## 5A - How this search can fail, decided in advance

Every search outcome is interpreted before execution:

- If the search reproduces the held set, the held set is described as
  searched-for rather than convenient. It is still not proof that no other
  eligible trial exists.
- If the search returns additional eligible trials, that is a finding about the
  review. Each additional trial is named and included or excluded on one of the
  axes declared in section 3: DESIGN, POPULATION, INTERVENTION, COMPARATOR, or
  MEASURE.
- If the search returns fewer trials than the object holds, that is a finding
  about the search, never reported as the review being wrong.

Worked example for the third outcome: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
"Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD registers "Chronic
Kidney Disease". A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** will screen all
records. The cross-family rule is a requirement, not a preference, because two
instances of one model is one screener run twice and its agreement statistic is
meaningless.

Screening is in two stages: title and abstract where PubMed supplies them, then
the full ClinicalTrials.gov API v2 registry record and PubMed-linked publication
record where available. **Each screener's decision is recorded per record at the
stage it was applied**, together with the reason. Both screeners' decisions are
published, not only the reconciled outcome, along with the agreement rate and how
every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, linked publication if
accepted under section 4A, year, design, population, arms, comparator identity,
analysed denominator and randomised total separately, the triglyceride lowering
result by arm where reported, the published between-arm effect estimate where
reported, its uncertainty, the stated confidence level, and the timepoint and
scale on which the triglyceride outcome is defined.

Every included or excluded record is classified against the section 3 axes and
no others: DESIGN, POPULATION, INTERVENTION, COMPARATOR, and MEASURE. If a
record fails more than one axis, each failed section 3 axis is recorded, but no
new axis is introduced during extraction or reporting.

Any axis read from a registry title remains provisional until the registered
primary outcome measure is read from the outcome module. A title is not an
outcome definition. Trial IDs, NCT IDs, PMIDs, DOIs, study dates, arms, outcome
names, and analysis populations are resolved from source records rather than
from recall.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, outcome module, or results field within it, so that
a human check can be made without leaving the page. **Nothing is computed that
can be read.** No model-adjusted contrast is reconstructed where the contrast is
reported directly. No value is derived from a rounded percentage when an
unrounded value or standard error is available from the source. No count is
derived from a percentage.

Where two populations exist for one outcome, both are recorded, exactly one is
marked as selected, and the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** difference between AMR101 4 g/day and placebo treatment groups in
triglyceride lowering effect.

**Read and reported but not pooled unless they instantiate the primary
estimand:** non-HDL cholesterol; LDL cholesterol; HDL cholesterol; total
cholesterol; apolipoprotein B; lipoprotein(a); inflammatory biomarkers;
cardiovascular outcomes; adverse events; pharmacokinetic outcomes; and
triglyceride outcomes at non-selected doses or comparator structures. They are
shown when recovered because a reader should see them; they are not pooled as
the headline because the review's estimand is the AMR101 4 g/day versus placebo
triglyceride-lowering contrast.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: difference between AMR101 4 g/day and placebo treatment
groups in triglyceride lowering effect. One trial may therefore carry a
different judgement for this result than it would for its own primary endpoint,
and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what a randomized treatment-group contrast estimates. The adherence variant
is not used, and no result assessed under one variant will be reported as though
assessed under the other.

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
agreement rate is published as measured**. Agreement on RoB-2 domains is
expected to be substantially lower than agreement on screening; if that proves
true it is a finding worth reporting and it will not be smoothed.
**Disagreements are adjudicated by a named human**, and the adjudication and its
reason are recorded per disagreement.

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

Random-effects meta-analysis on the mean-difference scale for triglyceride
lowering, inverse-variance weighted. The headline contrast is AMR101 4 g/day
minus placebo, using the selected triglyceride-lowering measure as defined in the
source record.

**Fixed before execution, so that reporting a disagreement between methods is a
commitment rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where it is
  defined.
- An **estimator comparison** -- DerSimonian-Laird, REML, Paule-Mandel -- is run
  and reported, per Cochrane Handbook v6.5 section 10.10.4.4, on the
  understanding that with few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k-1 degrees
  of freedom per Handbook v6.5 where defined, and is not reported where k makes
  it undefined.
- The analysis is **cross-checked in a second engine** at build time and the
  comparison published, including any quantity on which the two engines disagree
  by definition rather than by error.

**Heterogeneity:** tau^2, I^2 with its Q-profile confidence interval, and Q with
its degrees of freedom and p value. I^2 is reported with the caveat that at small
k a low value reflects imprecision as much as agreement.

## 10A - Pairwise geometry and what it forbids

This review is a pairwise AMR101 4 g/day versus placebo review for a continuous
triglyceride-lowering outcome. It is not a dose-response review, not a
multi-comparator network review, and not a cardiovascular-outcomes review.

Dose arms other than AMR101 4 g/day are not pooled into the primary contrast.
They may be extracted as contextual information when source-backed, but they do
not become indirect evidence for the 4 g/day contrast. Active comparator arms do
not become placebo arms. Lipid outcomes other than triglycerides do not become
surrogates for the primary outcome.

No SUCRA, treatment ranking, node-splitting, or design-by-treatment interaction
test will be reported for this pairwise review. Publication bias is not
assessable rather than not serious when the evidence base is too small for the
planned small-study-effect methods to be interpretable. GRADE carries that as a
limitation of assessability, not as reassurance.

| Choice | Fixed before search | Dynamic after source read | Hardcode risk control |
|---|---|---|---|
| Review contrast | AMR101 4 g/day versus placebo | Arm labels and dose wording are read from registry and publication records | No local path, remembered trial name, or source-free arm mapping may define a contrast |
| Eligibility axes | DESIGN, POPULATION, INTERVENTION, COMPARATOR, MEASURE | The reason text for each excluded record is source-derived | No new exclusion axis may be introduced during extraction |
| Outcome identity | Triglyceride lowering effect | Timepoint, units, scale, and analysis population are read from the outcome module or publication | A registry title is never treated as an outcome definition |

## 11 - Subgroup and sensitivity analyses

**Sensitivity, fixed before execution:** leave-one-out where defined; the
estimator comparison above; exclusion of records where the selected outcome is
not the registered primary outcome; exclusion of records where the selected
analysis set is not the randomized or intention-to-treat population; exclusion
of records where the reported result must be transformed onto the primary scale
rather than read directly; and a display separating directly reported
between-arm contrasts from derived contrasts.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression, and any continuous-outcome small-study-effect
display are planned only where the evidence base is large enough for their
assumptions to be meaningful. **Fixed caveat:** below approximately ten studies
these tests have almost no power and the Cochrane Handbook advises against
interpreting them. Where k is below that threshold the tests may still be
computed for completeness, and will be reported as computed values, explicitly
not as evidence about small-study effects.

Where publication bias cannot be assessed, the GRADE domain will read *not
assessable* rather than *not serious* -- the two are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

RoB-2 is **PENDING**. GRADE is **PENDING**. No completed RoB-2 or GRADE
judgement is implied by this protocol.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the session information
and the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The protocol anchor, first query attempt time, executed-search record, and
post-search anchor are stored with the canonical object. The search record is not
allowed to overwrite this protocol; departures are additive records.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments are recorded at the time of this commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
