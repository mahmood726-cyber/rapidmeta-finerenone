# Protocol - Apixaban for the treatment of venous thromboembolism: eight trials report an outcome named for recurrent VTE, and three of them count the same thing

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
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned. GitHub stores and displays what it is given, and an unsigned commit
carries nothing further. The commit hash binds the text; the repository is
public; the timestamp alone is not evidence that this was written at that time.

What the mechanism supports, and no more: this exact text is bound to this hash;
the repository is public, so the text is readable by anyone at that hash; and
where an entry for the commit exists in a public transparency log, that log's
inclusion time is an upper bound on when this text existed, set by a third party
rather than by us. A transparency-log entry proves something narrow: **the text
existed no later than the log time**.

What it does not support: it does not prove the commit was made when it says it
was, it does not prove that no earlier or parallel version existed elsewhere, it
does not prove the trials had not already been seen, and it says nothing about
the independence of the people who wrote it. The anchor proves when this text was
written and cannot prove the trials had not already been seen. A timestamp bounds
when, never what was known.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** The required ordering is that this
protocol is committed, pushed, and anchored in a public transparency log before
the first executed query. The ordering test uses the earliest query time,
including a failed attempt, not the first successful query. Reporting only the
first successful execution would move the first-query time later and flatter the
claim.

The search record is anchored afterwards, so two third-party times bracket the
operation. The first anchor states that this protocol text existed no later than
the log time; the second anchor states that the search record existed no later
than its later log time. Those two anchors bracket the operation; they do not
prove what the authors knew.

---

## 1 - Review question, in PICO

This topic already holds 4 trials: NCT01780987, NCT02829957, NCT03045406, and
NCT03266783. The question is being authored after that evidence was assembled.
However carefully it is written now, this is a retrospectively registered
protocol. The anchor proves when this text was written and cannot prove the
trials had not already been seen. A timestamp bounds when, never what was known.

| | |
|---|---|
| **Population** | Adults with acute or recent venous thromboembolism. |
| **Intervention** | Apixaban used for treatment of the index venous thromboembolism. |
| **Comparator** | Conventional anticoagulation, another direct oral anticoagulant, or placebo, classified as separate comparator nodes where the network allows. |
| **Outcome** | Recurrent venous thromboembolism and bleeding, read by the registered outcome definition rather than by title alone. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with acute or recent venous thromboembolism, what
is the effect of apixaban compared with conventional anticoagulation, another
direct oral anticoagulant, or placebo on recurrent venous thromboembolism and on
bleeding?

## 2 - Estimand, stated in advance

The primary estimand is the **risk ratio for recurrent symptomatic venous
thromboembolism**, on the log scale, with the participant as the unit of analysis
and the first recurrent venous thromboembolism event counted once per
participant.

The outcome case definition is fixed before execution as recurrent symptomatic
venous thromboembolism without a death term: nonfatal deep vein thrombosis or
nonfatal pulmonary embolism. A recurrent-VTE label is not enough. If a trial's
registered or published outcome includes VTE-related death, all-cause death,
major bleeding, clinically relevant non-major bleeding, menstrual blood loss, or
another component in the same measure, it is excluded from this estimand on the
OUTCOME axis unless a separate count matching the fixed case definition is read.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME axis, not on grounds of quality.** This is pre-specified because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
for the recurrent-VTE pool because it reports something else. Specifically and
in advance:

- A composite including a death term is not the no-death recurrent-VTE estimand.
- A bleeding endpoint is not an efficacy endpoint, even where the trial is a VTE
  treatment trial.
- A time-to-event hazard ratio is not stored in a risk-ratio field unless the
  review explicitly reports it as a separate sensitivity analysis.
- A dichotomous risk ratio at a fixed timepoint is the headline only for the
  recurrent-VTE count-based pool; it will not be described as a time-to-first
  hazard ratio.

## 3 - Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
acute or recent venous thromboembolism; it randomises apixaban used as a
treatment strategy against conventional anticoagulation, another direct oral
anticoagulant, or placebo; and it reports recurrent symptomatic venous
thromboembolism as a countable participant-level outcome without a death term.

**Exclude** on any single failed axis -- population, intervention, comparator, or
measure -- and record which axis failed and what the study reports instead.
Section 7 classifies records against those axes and no others.

Populations narrower than the question, for example cancer-associated VTE, are
**not** indirect on that ground alone; narrowness is recorded and carried into
the GRADE indirectness domain rather than used as an exclusion.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition.

## 4 - Information sources

PubMed via NCBI E-utilities and ClinicalTrials.gov API v2 only.

Embase was **not** searched. CENTRAL was **not** searched. Web of Science was
**not** searched. Scopus was **not** searched. This is not a comprehensive
search, and the review will not call it one.

The cost of those omissions is explicit: trials, conference reports, regulatory
documents, and non-PubMed-indexed publications may be missed; citation networks
outside PubMed are not traversed; and an absent record in this review cannot be
treated as evidence that no such trial or publication exists. The search is a
bounded reproducibility check against two public APIs, not a claim to exhaustive
retrieval.

## 4A - Linkage method and its known failure modes

Registry records will be linked to publications before extraction by the
following rule, applied in order and recorded per trial:

1. Query PubMed through NCBI E-utilities using the trial registration identifier
   as a text term and, where necessary, as a secondary-source identifier.
2. Read the ClinicalTrials.gov API v2 references module and candidate
   publication links, including reference records marked with
   `reference_type='result'`.
3. Accept a publication link only after the NCT identifier, trial name, enrolled
   population, interventions, comparators, and outcome definition agree with the
   registry record.
4. If the registry and publication disagree, keep both pointers and record the
   disagreement rather than forcing a match.

Two linkage failure modes are known before this search is run and have been
measured on this corpus:

- PubMed silently drops trials from ID-based queries when the record is not
  indexed, so an absent result is indistinguishable from a trial that does not
  exist.
- ClinicalTrials.gov `reference_type='result'` links can point at the wrong
  paper, which is worse than a missing link because a wrong link looks like a
  successful one.

Where linkage succeeds, registry data matched the publication in 26 of 28
analyses compared on this corpus. That is a conditional figure with a denominator
of **linked analyses**, not all analyses, and therefore is not a general
reliability rate.

## 5 - Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what
it actually ran, on what date, with what filters, and how many records each
returned; any departure from the strings below will be recorded as a departure
rather than silently substituted.

Each string is kept under 20 Boolean operators because the interface refuses
longer strings and a registered string that cannot be executed forces a
departure on the first attempt.

**PubMed (NCBI E-utilities)**

```
("apixaban"[tiab] OR "Eliquis"[tiab])
AND ("venous thromboembolism"[tiab] OR VTE[tiab] OR "deep vein thrombosis"[tiab] OR "pulmonary embolism"[tiab])
AND (randomized[tiab] OR randomised[tiab] OR trial[tiab] OR "randomized controlled trial"[pt])
```

Filters: none on language, none on date.

**ClinicalTrials.gov (API v2)**

```
query.intr=apixaban OR Eliquis
query.cond=venous thromboembolism OR deep vein thrombosis OR pulmonary embolism
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

Filters: none on phase, sponsor, country, sex, or date.

## 5A - How this search can fail, decided in advance

The meaning of every search outcome is fixed before execution:

- If the search reproduces the held set, that is reported as searched-for rather
  than convenient. It does not change the retrospective status and does not
  prove that no other trial exists.
- If the search returns additional eligible trials, that is a finding about the
  REVIEW. Each additional trial is named and included or excluded on a stated
  eligibility axis.
- If the search returns fewer trials than the object holds, that is a finding
  about the SEARCH, never reported as the review being wrong.

The worked example for the third case is the finerenone-cv registry query, which
missed FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its
condition as "Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD
registers "Chronic Kidney Disease". A narrow query looks exactly like a wrong
review.

## 6 - Study selection process

Two **independent screeners of different model families** -- the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text or registry
record. **Each screener's decision is recorded per record at the stage it was
applied**, together with the reason. Both screeners' decisions are published, not
only the reconciled outcome, along with the agreement rate and how every
disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not
content.** The website release requires the two cross-family AI assessments and
states plainly that it has not been human-verified. The submission release
additionally requires two named human reviewers to have checked every included
study and every extracted datum; the statement to that effect is emitted only
when those attestation records exist and is never written as prose.

## 7 - Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm event counts, and the published effect estimate with
its interval and its stated confidence level where one exists.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table or outcome module within it, so that a human check
can be made without leaving the page. **Nothing is computed that can be read.**
No count is derived from a percentage; no composite is reconstructed by summing
its components. Identifiers are resolved by lookup, never from recall.

Records are classified only on the axes declared in section 3: population,
intervention, comparator, and measure. A registry title may suggest one of those
axes, but that reading is provisional until the registered primary and secondary
outcome measures are read from the outcome module. A title is not an outcome
definition.

Where two populations exist for one outcome -- for example a full analysis set
and a randomised set -- both are recorded, exactly one is marked as selected, and
the population is named on the cell.

## 8 - Outcomes and prioritisation

**Primary:** recurrent symptomatic venous thromboembolism without a death term,
reported as a participant-level risk ratio on the log scale.

**Components and safety outcomes, read and reported but not pooled into the
primary efficacy estimand:** deep vein thrombosis; pulmonary embolism; major
bleeding; clinically relevant non-major bleeding; any bleeding; all-cause death;
VTE-related death. They are shown because a reader should see them; they are not
pooled into the primary recurrent-VTE estimand when their definitions differ.

## 9 - Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: recurrent symptomatic venous thromboembolism without a death
term, expressed as a participant-level risk ratio. One trial may therefore carry
a different judgement for this result than it would for its own primary
endpoint, and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because that
is what an intention-to-treat comparison estimates. The adherence variant is not
used, and no result assessed under one variant will be reported as though
assessed under the other.

**Domains.** All five, each reached through the RoB-2 signalling questions rather
than by overall impression, with a recorded answer per signalling question, a
**domain judgement** of low / some concerns / high, and a rationale naming the
evidence it rests on:

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

**Relationship to the recorded bias features.** The object may hold bias-relevant
features such as open-label design, endpoint rank within its own trial, early
stopping, adjudication, or analysis population. These are **inputs to the
assessment and never substitutes for a domain judgement**. No existing prose in
the object may stand in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any reasoning from recorded features. When it
does, the review will state **whether the GRADE rating moves and why -- and if it
does not move, will say so explicitly** rather than leaving the reader to infer
that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for this protocol registration.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10 - Synthesis methods

Random-effects meta-analysis on the log risk-ratio scale, inverse-variance
weighted.

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

**Heterogeneity:** tau-squared, I-squared with its Q-profile confidence interval
where computable, and Q with its degrees of freedom and p value. I-squared is
reported with the caveat that at small k a low value reflects imprecision as
much as agreement.

## 10A - Network geometry and what it forbids

This is a network. Its topology is derived from the object's own arms and is an
established fact, not an assumption.

Nodes:

- ACTIVE -- LMWH
- ACTIVE -- another direct oral anticoagulant
- ACTIVE -- heparin/vitamin-K antagonist
- Apixaban

The network has 4 nodes, 3 edges, is connected, and has zero independent loops
under E - V + 1. Indirect comparisons are computable because the network is
connected, but the consistency assumption they rest on **cannot be tested** --
not "was not tested", cannot be, by the geometry.

Node-splitting and design-by-treatment interaction are unavailable. Their
absence must never be reported as consistency having been checked. With zero
loops there is no closed path on which direct and indirect evidence can disagree,
so incoherence is not estimable from the data structure.

No SUCRA or ranking will be reported. Ranking in this geometry would convert a
sparse connected tree into an apparent hierarchy without a testable consistency
claim underneath it.

Publication bias is **not assessable** rather than not serious, and GRADE carries
incoherence as untestable. A head-to-head trial between two non-comparator nodes
would add an edge. If that edge closes a loop, the network would gain an
independent cycle, making at least one local inconsistency check possible and
allowing node-splitting or design-by-treatment interaction to answer a question
that this geometry currently forbids.

## 11 - Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out; the estimator comparison above;
fixed-effect versus random-effects comparison; and, where per-arm counts are
available, the same 2x2 data pooled as a risk ratio, an odds ratio and a risk
difference. Only the prespecified primary risk-ratio pool is the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 - Meta-bias assessment

Funnel plot, Egger's regression and -- for any count-based pool -- Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
Where k is below that threshold the tests may still be computed for completeness,
and will be reported as computed values, explicitly not as evidence about
small-study effects. Where publication bias cannot be assessed, the GRADE domain
will read *not assessable* rather than *not serious* -- the two are different
statements.

For the network described in section 10A, publication bias is **not assessable**
rather than not serious.

## 13 - Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 sections 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

The incoherence domain is carried as **untestable** for the network geometry in
section 10A. It will not be reported as checked, absent, or not serious.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for this protocol registration.
Performing it later executes this section rather than amending it.

## 14 - Data sharing and reproducibility

The canonical data object from which every number on the review page is
projected is published with the review, together with the session information and
the analysis scripts actually executed. The intent is that the review can be
rebuilt from the object alone.

The protocol commit, the pre-search transparency-log anchor, the executed search
record, and the post-search transparency-log anchor are part of the public audit
trail. The search record contains the earliest query attempt, including any
failed attempt, so the ordering claim is tested against the beginning of the
operation rather than the first clean result.

## 15 - Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 - Amendments

No amendments exist at the time of this commit.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
