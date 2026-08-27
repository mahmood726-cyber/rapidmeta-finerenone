# Protocol - Dabigatran for thromboprophylaxis after elective arthroplasty

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

**Status: RETROSPECTIVELY REGISTERED BY COMMIT. This document is the
registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds the text; the repository is public. This
document is written before the search runs and contains no results, no yields,
and no counts from any search.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned.

What the mechanism supports, and no more: this exact text is bound to this hash,
and the repository is public, so the text is readable by anyone at that hash. A
public transparency-log entry gives an inclusion time set by a third party,
proving something narrow: THE TEXT EXISTED NO LATER THAN THE LOG TIME. Not when
the commit was made, not that no earlier version existed elsewhere, and not what
was already known.

What it does not support: it does not prove when the commit was made, it does
not prove that no earlier or parallel version existed elsewhere, it does not
prove the data had not already been seen, and it says nothing about the
independence of the people who wrote it. Those are claims about conduct, and no
timestamp can carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs, but after the object already held
trials.** This protocol is committed, pushed, and anchored in a public
transparency log BEFORE the search runs. The ordering test this review publishes
uses the earliest query time, including a failed attempt, rather than the first
successful one, because reporting only the successful execution would move the
first-query time later and flatter the claim.

The search record will itself be anchored afterwards, so two third-party times
bracket the operation: one before the first query attempt, and one after the
search record exists. Both local execution times are read from the search lane's
own clock. The databases return records and hit counts, not authoritative
timestamps for our act of searching. The sequence is therefore auditable and
bounded by third-party log times, and it is recorded here as less than proof.

This is a retrospectively registered protocol. The anchor proves WHEN this text
was written and CANNOT prove the trials had not already been seen. A timestamp
bounds when, never what was known.

---

## 1 - Review question, in PICO

This topic already holds 8 trials: NCT00152971, NCT00168805, NCT00168818,
NCT00246025, NCT00657150, NCT01225822, NCT01431456, and NCT06581965. The
review question is being authored after that evidence was assembled. However
carefully it is written now, this is a retrospectively registered protocol, and
the anchor proves WHEN this text was written and CANNOT prove the trials had not
already been seen. A timestamp bounds when, never what was known.

| | |
|---|---|
| **Population** | Adults undergoing elective hip or knee arthroplasty. |
| **Intervention** | Dabigatran thromboprophylaxis. |
| **Comparator** | The comparator each trial actually randomised against. |
| **Outcome** | Venous thromboembolism during the trial-defined postoperative prophylaxis period. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** In adults undergoing elective hip or knee arthroplasty,
does dabigatran prevent venous thromboembolism compared with the comparator each
trial actually randomised against?

## 2 - Estimand, stated in advance

The primary efficacy estimand is the **randomised contrast for venous
thromboembolism during the trial-defined postoperative prophylaxis period**, with
the participant as the unit of analysis and the comparator defined within each
trial rather than imposed across trials after the fact.

The preferred outcome is the trial's registered or published venous
thromboembolism endpoint for the arthroplasty prophylaxis period. If the trial's
primary VTE endpoint includes asymptomatic venographic deep-vein thrombosis,
symptomatic VTE, pulmonary embolism, and all-cause mortality, that composite is
read as the trial's endpoint and not rewritten after seeing the publication. If
symptomatic VTE is separately available, it is extracted and reported as a
component or sensitivity outcome rather than silently substituted for the
registered composite.

The primary effect measure is the randomized comparative measure reported for
the eligible endpoint. If arm-level event counts and denominators are available,
count-based contrasts may be computed under the synthesis rules below. If a
trial reports a time-to-first-event hazard ratio for the eligible endpoint, it is
stored as a hazard ratio and not mixed into a count-based pool unless the
required counts are also available.

**Quantities that cannot be converted into this estimand are excluded on the
MEASURE axis, not on grounds of quality.** This is registered because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly relevant to thromboprophylaxis and still fail this
review's eligibility because it reports something else. Specifically and in
advance:

- A treatment trial for established acute venous thromboembolism is not
  thromboprophylaxis after elective arthroplasty.
- A trial in atrial fibrillation, acute coronary syndrome, mechanical valves, or
  another non-arthroplasty population is not this population.
- A pharmacokinetic, dose-finding, extension, observational, registry cohort, or
  before-after comparison without a randomized eligible comparator is not this
  estimand.
- A bleeding-only result is not an efficacy result for VTE prevention, though
  bleeding is extracted as safety where the trial is otherwise eligible.
- A composite, component, or timepoint whose definition cannot be read is not
  silently treated as the primary VTE endpoint.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults
undergoing elective hip or knee arthroplasty; it randomises dabigatran
thromboprophylaxis against the comparator used within that trial; and it reports
venous thromboembolism with extractable randomized comparative data.

**Exclude** on any single failed axis - population, intervention, comparator, or
measure - and record which axis failed and what the study reports instead.

The canonical object already names NCT00152971, NCT00168805, NCT00168818,
NCT00246025, NCT00657150, NCT01225822, NCT01431456, and NCT06581965 as trials
held by this topic. Held status is not automatic inclusion in the synthesis:
each trial must still pass the axes above, and any searched record must pass the
same axes before it can enter the analysis.

Populations narrower than the question, such as total hip arthroplasty only,
total knee arthroplasty only, unilateral procedures only, bilateral procedures
only, or a single postoperative prophylaxis duration, are **not** indirect on
that ground alone. Narrowness is recorded and carried into the GRADE
indirectness domain rather than used as an exclusion unless the setting is not
elective hip or knee arthroplasty prophylaxis.

Any axis read from a registry TITLE is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2 only.

Embase was NOT searched, nor CENTRAL, Web of Science or Scopus. This is not a
comprehensive search. The cost of the omission is that records indexed only in
the omitted services, conference material present only there, non-PubMed
bibliographic records, regional database records, and citations missed by the
stated PubMed and ClinicalTrials.gov strings may be absent from the review.

Only open-access records and documents are admissible as evidence for
extraction. Memory is not evidence, and no paywalled text will be treated as
source material unless an openly accessible copy is available and cited.

## 4A - Linkage method and its known failure modes

Before the search runs, registry records will be linked to publications by this
ordered method:

1. Read the ClinicalTrials.gov API v2 record for the NCT identifier.
2. Extract registry references that assert a publication link, including
   reference records whose type is marked as result.
3. Query PubMed through NCBI E-utilities by NCT identifier and by any PMID
   supplied in the registry record.
4. Accept a link only when the publication and registry match on the trial
   identifier or on enough design fields to make the link auditable: population,
   intervention, comparator, outcome definition, trial acronym or registration
   identifier, and trial timing.
5. Record the link source and the fields that supported the match.

Two failure modes are known before execution and are measured on this corpus.
First, PubMed silently DROPS trials from ID-based queries when the record is not
indexed, so an absent result is indistinguishable from a trial that does not
exist. Second, registry reference_type='result' links can point at the WRONG
paper, which is worse than a missing link because a wrong link looks like a
successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That figure is conditional on LINKED analyses:
its denominator is linked analyses, not all analyses, and it is therefore not a
general reliability rate for the registry, PubMed, this topic, or unlinked
records.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted.

Each string is kept under 20 Boolean operators because the interface refuses
larger expressions. A registered string that cannot be executed would force a
departure on the first attempt, and the departure would be recorded.

**PubMed (NCBI E-utilities)**

```
("dabigatran etexilate"[tiab] OR dabigatran[tiab] OR "BIBR 1048"[tiab] OR Pradaxa[tiab])
AND (arthroplasty[tiab] OR "joint replacement"[tiab] OR "hip replacement"[tiab] OR "knee replacement"[tiab])
AND ("venous thromboembolism"[tiab] OR thromboprophylaxis[tiab] OR prophylaxis[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language filter would make
the search less reproducible across interfaces and would exclude eligible
records solely because of metadata rather than the review question.

**ClinicalTrials.gov (API v2)**

```
query.intr=dabigatran OR "dabigatran etexilate" OR "BIBR 1048"
query.cond=venous thromboembolism OR thrombosis
query.term=arthroplasty OR "hip replacement" OR "knee replacement"
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING|RECRUITING|NOT_YET_RECRUITING
```

Filters: none on phase, sponsor, geography, sex, language, or date. Rationale:
the review question is defined by randomisation, population, intervention,
comparator, and measure, not by sponsor or posting date.

## 5A - How this search can fail, decided in advance

The interpretation of every search outcome is fixed before execution:

- If the search reproduces the held set, the held set is described as
  searched-for rather than convenient. Reproduction does not make this protocol
  prospective, and it does not prove that no evidence had already been seen.
- If the search returns additional eligible trials, that is a finding about the
  REVIEW. Each additional trial is named and included or excluded on a stated
  Section 3 axis: population, intervention, comparator, or measure.
- If the search returns fewer trials than the object holds, that is a finding
  about the SEARCH, never reported as the review being wrong. A narrower search
  can miss real eligible trials.

Worked example for the third case: the finerenone-cv registry query missed
FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its condition as
"Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD registers
"Chronic Kidney Disease". A narrow query looks exactly like a wrong review.

## 6 - Study selection process

Two **independent screeners of different model families** - the cross-family
rule is a requirement, not a preference, because two instances of one model is
one screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text. **Each
screener's decision is recorded per record at the stage it was applied**,
together with the reason. Both screeners' decisions are published, not only the
reconciled outcome, along with the agreement rate and how every disagreement was
resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Every held trial and every searched record is classified against the Section 3
axes and no others: population, intervention, comparator, and measure. A record
that fails an axis is excluded on that axis; a record that passes all axes is
eligible for extraction. No extra exclusion axis is introduced during
extraction.

Any axis read from a registry TITLE is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, arthroplasty type, prophylaxis duration, population, arms, **the
analysed denominator and the randomised total separately**, per-arm event
counts, bleeding counts, and the published effect estimate with its interval and
its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or outcome module field within it, so that a human
check can be made without leaving the page. **Nothing is computed that can be
read.** No count is derived from a percentage; no composite is reconstructed by
summing its components. Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome - for example a full analysis set,
modified intention-to-treat set, safety set, evaluable venography set, or
randomised set - all relevant populations are recorded, exactly one is marked as
selected for a given analysis, and the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** venous thromboembolism during the trial-defined postoperative
prophylaxis period, using the trial's registered or published eligible endpoint.

**Components, read and reported but not silently substituted for the primary:**
symptomatic deep-vein thrombosis; pulmonary embolism; proximal deep-vein
thrombosis; distal deep-vein thrombosis; all-cause death where part of the VTE
composite; and major VTE where separately defined.

**Safety, read and reported but not pooled as efficacy:** major bleeding;
clinically relevant non-major bleeding where defined; any bleeding; and
bleeding definitions as stated by the source.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: venous thromboembolism during the trial-defined postoperative
prophylaxis period, expressed as the selected randomized contrast. One trial may
therefore carry a different judgement for this result than it would for its own
primary endpoint or safety endpoint, and that is the intended behaviour of the
tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat randomized contrast estimates. The adherence
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

**Both sets of judgements are recorded and published** - per domain, per
assessor, with rationales - not only the reconciled outcome. The **per-domain
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

**Relationship to the recorded bias features.** The object may already hold
bias-relevant features such as blinding, endpoint adjudication, endpoint rank
within its own trial, early stopping, analysis population, or missing outcome
data. These are **inputs to the assessment and never substitutes for a domain
judgement**. No existing prose in the object may stand in for a signalling
question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features.
When it does, the review will state **whether the GRADE rating moves and why -
and if it does not move, will say so explicitly** rather than leaving the reader
to infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis will be used for each effect-measure family that
has at least two eligible studies with compatible data. Count-based efficacy
analyses will use the log risk-ratio scale as the headline count-based measure,
with odds ratio and risk difference reported as pre-specified sensitivities
where the same 2x2 data support them.

Different endpoint definitions are not silently pooled as though identical. A
trial-defined total VTE composite, a major VTE composite, and symptomatic VTE are
separate outcomes unless the sources define them identically or the component
needed for a pre-specified outcome is separately extractable. Differences in
arthroplasty type and prophylaxis duration are recorded and carried into
interpretation and GRADE indirectness rather than hidden inside a pooled label.

**Pre-specified, so that reporting a disagreement between methods is a
commitment rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung-Knapp-Sidik-Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool where the number
  of studies makes it defined.
- An **estimator comparison** - DerSimonian-Laird, REML, Paule-Mandel - is run
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

## 10A - Static commitments and hardcode disclosure

This protocol contains static commitments and object identifiers, not results.
The table below separates what is fixed by the protocol from what must be read
or computed later.

| Item | Status in this protocol | Later source |
|---|---|---|
| Topic slug, title, and frozen question | Static, supplied before this file was written | Canonical object and this protocol |
| Held NCT identifiers | Static disclosure of the evidence already on the object | Canonical object |
| Search strings and databases | Static method commitment | Search lane execution record |
| Search yields, added records, and missed records | Not present | Search record anchored after execution |
| Trial eligibility classification | Pending | Section 3 axes applied to registry records and publications |
| Effect sizes, event counts, denominators, and pooled results | Not present | Open source documents and analysis scripts |
| RoB-2 and GRADE | PENDING | Independent assessments and GRADE domain records |

No simulated, placeholder, filler, or hardcoded fake trial data may be promoted
from this protocol into the canonical object, analysis output, or review page.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out where defined; the estimator
comparison above; exclusion of trials available only as registry results where
no publication link is confirmed; and, where per-arm counts are recovered, the
same 2x2 data pooled as a risk ratio, an odds ratio and a risk difference -
reported as sensitivity to the primary count-based pool, never as a replacement
for the primary outcome definition.

**Subgroup: none pre-specified.** Hip-only and knee-only trials, short and
extended prophylaxis durations, and dose groups are recorded. With the small
number of trials this comparison has, formal subgroup contrasts would be
underpowered and post-hoc, and none will be presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and - for any count-based pool - Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
Where k is below that threshold the tests may still be computed for
completeness, and will be reported as computed values, explicitly not as
evidence about small-study effects. Where publication bias cannot be assessed,
the GRADE domain will read *not assessable* rather than *not serious* - the two
are different statements.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this protocol. Performing it
later executes this section rather than amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the session information
and the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The protocol commit, the pre-search transparency-log anchor, the first query
attempt time, the executed search record, and the post-search transparency-log
anchor are all retained in the canonical object or its registration record so a
reader can check the order without relying on prose.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
