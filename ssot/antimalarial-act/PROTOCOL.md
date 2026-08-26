# Protocol - artemisinin-based combination therapy network anchored on artemether-lumefantrine

**Status: REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a commit in a public repository rather than in
PROSPERO. The commit hash binds this exact text and the repository is public.
This document is written before the search runs and contains no results, no
yields, and no counts from any search.

**The commit timestamp is the weak half, and this document will not pretend
otherwise.** The commit timestamp is author-supplied and forgeable: git author
and committer dates are set by whoever makes the commit, and commits here are
unsigned.

What the mechanism supports, and no more: this exact text is bound to this hash,
and the repository is public, so the text is readable by anyone at that hash. A
public transparency-log entry gives an inclusion time set by a third party,
proving something narrow: THE TEXT EXISTED NO LATER THAN THE LOG TIME - not when
the commit was made, not that no earlier or parallel version existed elsewhere.

What it does not support: it does not prove when the commit was made, it does not
prove that no earlier or parallel version existed elsewhere, it does not prove
the data had not already been seen, and it says nothing about the independence of
the people who wrote it. Those are claims about conduct, and no timestamp can
carry them.

**How to check this without us.** The verification recipe, the public half of the signing key, and a worked example are at [`ssot/registration/VERIFY.md`](../registration/VERIFY.md). It states the limitation plainly as well: the log time is independent of us, the key custody is not. A stranger can verify the text existed by the log time and that we signed it; a stranger cannot verify we did not hold an earlier version.

**It is written before the search runs.** This protocol is committed, pushed, and
log-anchored before the first query. The ordering test this review publishes uses
the earliest query time, including a failed attempt, rather than the first
successful one, because reporting only the successful execution would move the
first-query time later and flatter the claim.

The search record will itself be log-anchored afterwards, so two third-party
times bracket the operation: one before the first query attempt, and one after
the search record exists. Both local execution times are read from the search
lane's own clock. The databases return records and hit counts, not authoritative
timestamps for our act of searching. The sequence is therefore auditable and
bounded by third-party log times, and it is recorded here as less than proof.

---

## 1. Review question, in PICO

| | |
|---|---|
| **Population** | People enrolled in randomised malaria treatment trials of artemisinin-based combination therapy. |
| **Intervention** | Dihydroartemisinin-piperaquine, artesunate-amodiaquine, or pyronaridine-artesunate. |
| **Comparator** | Artemether-lumefantrine as the common comparator. |
| **Outcome** | PCR-corrected treatment failure. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** among trials comparing an artemisinin-based combination
therapy with artemether-lumefantrine, what is the PCR-corrected treatment failure
in each direct comparison, and can the resulting network support an indirect
comparison between the non-comparator arms?

## 2. Estimand, stated in advance

The estimand is **PCR-corrected treatment failure**, read at the follow-up time
specified by the trial's registered or published outcome definition. The
participant is the unit of analysis. The primary arm-level quantity is the
proportion of analysed participants with PCR-corrected treatment failure in each
arm.

For each direct comparison, the primary contrast is the log risk ratio for
PCR-corrected treatment failure. Risk difference and odds ratio are reported as
sensitivity measures where the required per-arm counts and denominators are
available. PCR-uncorrected failure, crude recurrent parasitaemia, reinfection,
and adequate clinical and parasitological response are not silently substituted
for PCR-corrected treatment failure.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME axis, not on grounds of quality.** This is pre-registered because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
because it reports something else.

## 3. Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols participants in
a malaria treatment trial; it includes at least two of the four network nodes
listed in Section 10A; and it reports PCR-corrected treatment failure, or enough
source-backed information to recover PCR-corrected treatment failure, for the
eligible arms.

**Exclude** on any single failed axis - population, intervention, comparator, or
outcome measure - and record which axis failed and what the study reports
instead.

The canonical object already fixes the starting network as three trials on three
edges: Guinea-Bissau for dihydroartemisinin-piperaquine versus
artemether-lumefantrine; Cameroon for artesunate-amodiaquine versus
artemether-lumefantrine; and Nigeria for pyronaridine-artesunate versus
artemether-lumefantrine. Candidate status is not inclusion: each candidate must
still pass the axes above, and any searched record must pass the same axes before
it can enter the analysis.

Populations narrower than the question, including a single country, transmission
setting, age band, or parasite species, are **not** indirect on that ground alone.
Narrowness is recorded and carried into the GRADE indirectness domain rather
than used as an exclusion unless the population is not a malaria treatment trial
population.

## 4. Information sources

PubMed (NCBI E-utilities) and ClinicalTrials.gov API v2 only.

Embase was NOT searched. CENTRAL, Web of Science and Scopus were NOT searched.
Regional African databases were NOT searched. This is not a comprehensive search,
and it must not be described as comprehensive. The cost of the omission is that
records indexed only in the omitted services, conference material present only
there, trial reports discoverable through regional indexing, and citations missed
by the stated PubMed and ClinicalTrials.gov strings may be absent from the
review. For African trial literature, the omission of regional databases is a
real limitation.

Only open-access records and documents are admissible as evidence for extraction.
Memory is not evidence, and no paywalled text will be treated as source material
unless an openly accessible copy is available and cited.

## 5. Search strategy - the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted.

The strings cover all four network nodes, not only artemether-lumefantrine,
because a network search scoped to one common-comparator edge would be unable to
find a loop-closing trial between two non-comparator ACTs.

**PubMed (NCBI E-utilities)**

```
("artemether-lumefantrine"[tiab] OR "artemether lumefantrine"[tiab] OR "artemether/lumefantrine"[tiab] OR Coartem[tiab] OR "dihydroartemisinin-piperaquine"[tiab] OR "dihydroartemisinin piperaquine"[tiab] OR "dihydroartemisinin/piperaquine"[tiab] OR "DHA-PPQ"[tiab] OR piperaquine[tiab] OR "artesunate-amodiaquine"[tiab] OR "artesunate amodiaquine"[tiab] OR "artesunate/amodiaquine"[tiab] OR "AS-AQ"[tiab] OR amodiaquine[tiab] OR "pyronaridine-artesunate"[tiab] OR "pyronaridine artesunate"[tiab] OR "pyronaridine/artesunate"[tiab] OR pyronaridine[tiab])
AND (malaria[MeSH Terms] OR malaria[tiab] OR "Plasmodium falciparum"[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language or date filter
would narrow the record set for reasons not part of the eligibility criteria.

**ClinicalTrials.gov (API v2)**

```
query.intr=artemether lumefantrine OR artemether-lumefantrine OR Coartem OR dihydroartemisinin piperaquine OR dihydroartemisinin-piperaquine OR DHA-PPQ OR piperaquine OR artesunate amodiaquine OR artesunate-amodiaquine OR AS-AQ OR amodiaquine OR pyronaridine artesunate OR pyronaridine-artesunate OR pyronaridine
query.cond=malaria OR Plasmodium falciparum
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

No backward citation search, forward citation search, registry outside
ClinicalTrials.gov, or bibliographic database outside PubMed is registered for
this review.

## 5A. How this search can fail, decided in advance

Four readings are fixed before execution.

**A. The search reproduces the held set.** That is evidence that the three
starting trials were searched-for rather than convenient. It is not evidence that
the search was comprehensive, because the sources are deliberately limited to
PubMed and ClinicalTrials.gov.

**B. The search returns additional eligible trials.** That is a finding about the
review. Each additional trial will be named and included or excluded on a stated
axis. If eligible, it changes the object rather than being treated as a nuisance
record.

**C. The search returns fewer trials than the object holds.** That is a finding
about the search, never reported as the review being wrong. Worked example:
earlier today on finerenone-cv the registered ClinicalTrials.gov condition query
missed FIGARO-DKD (NCT02545049), a pivotal trial, because it registers its
condition as "Diabetic Kidney Disease" alone while its sibling FIDELIO-DKD
registers "Chronic Kidney Disease". A narrow query looks exactly like a wrong
review.

**D. The search returns a head-to-head trial between two of the three
non-comparator ACTs.** That closes a loop and converts the consistency assumption
from untestable to testable. It is the single most valuable thing this search
could return and it is named in advance.

## 6. Study selection process

Two **independent screeners of different model families** - the cross-family rule
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

## 7. Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, country, population, parasite species where specified, arms,
follow-up timepoint, the analysed denominator and the randomised total
separately, per-arm PCR-corrected treatment-failure counts, and any published
effect estimate with its interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table, figure, registry module, or outcome field within
it, so that a human check can be made without leaving the page. **Nothing is
computed that can be read.** No count is derived from a percentage; no composite
is reconstructed by summing its components. Identifiers are resolved by lookup,
never from recall.

Any axis read from a registry title is provisional until the registered primary
outcome measure is read from the outcome module. A title is not an outcome
definition. A title may suggest that a trial is about malaria treatment, an ACT,
or treatment failure, but eligibility on the OUTCOME axis rests on the registered
or published outcome definition and the extraction source for PCR-corrected
treatment failure.

Where two populations exist for one outcome - for example a full analysis set and
a randomised set - both are recorded, exactly one is marked as selected, and the
population is named on the cell.

No invented trial data, effect sizes, counts, or PROSPERO numbers are permitted.

## 8. Outcomes and prioritisation

**Primary:** PCR-corrected treatment failure at the trial-defined follow-up
timepoint, with the timepoint read from the source record and not assumed from
the drug class or country.

**Secondary, read and reported but not substituted for the primary outcome:**
PCR-uncorrected treatment failure; recurrent parasitaemia; reinfection; adequate
clinical and parasitological response; serious adverse events; and withdrawals.
They are shown where available because a reader should see them. They are not
pooled as the headline because the review's estimand is PCR-corrected treatment
failure.

## 9. Risk of bias

**Tool.** Cochrane risk-of-bias tool for randomized trials, version 2 (RoB-2).

**Unit of assessment.** RoB-2 is applied **to the result being pooled, not to the
trial as a whole**: PCR-corrected treatment failure. One trial may therefore
carry a different judgement for this result than it would for another endpoint,
and that is the intended behaviour of the tool.

**Variant.** The **effect of assignment to intervention** variant, because this
review estimates the effect of allocation to an ACT regimen. The adherence
variant is not used, and no result assessed under one variant will be reported as
though assessed under the other.

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
bias-relevant features. These are **inputs to the assessment and never
substitutes for a domain judgement**. No existing prose in the object may stand
in for a signalling question or a domain rating.

**Feeding GRADE.** The completed RoB-2 result becomes the basis of the GRADE
risk-of-bias domain, replacing any current reasoning from recorded features. When
it does, the review will state **whether the GRADE rating moves and why - and if
it does not move, will say so explicitly** rather than leaving the reader to
infer that nothing changed.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No RoB-2 assessment exists for these trials in this protocol.
Performing it later **executes this section rather than amending it**, and the
object will record that distinction.

## 10. Synthesis methods

Each direct edge is analysed first as its own randomised comparison. For each
trial, PCR-corrected treatment failure is extracted as events over analysed
participants by arm. The primary direct contrast is the log risk ratio, inverse
variance estimated from the extracted 2x2 table. Risk difference and odds ratio
are reported as sensitivity contrasts where they can be computed from
source-backed counts.

Zero cells are handled by a pre-specified continuity correction of 0.5 added to
all four cells of the affected 2x2 table for ratio measures. Risk differences
are computed directly from observed risks. If a trial reports an adjusted effect
estimate for PCR-corrected treatment failure that cannot be reconciled with the
2x2 estimand, the adjusted estimate is recorded but not substituted into the
primary field.

Because the established starting network has one trial on each direct edge,
there is no within-edge meta-analysis. No between-study variance is estimated
within an edge. If the search finds additional eligible trials on an existing
edge, that edge will be pooled using random-effects meta-analysis on the log risk
ratio scale, with REML as the headline between-study-variance estimator and
Hartung-Knapp-Sidik-Jonkman intervals reported alongside Wald intervals.

If the connected network remains a star, indirect comparisons between
dihydroartemisinin-piperaquine, artesunate-amodiaquine, and
pyronaridine-artesunate are computed through the common
artemether-lumefantrine comparator by subtracting the corresponding log risk
ratios. Their uncertainty is propagated from the two direct contrasts used in
each indirect comparison.

The analysis is cross-checked in a second engine at build time where a second
engine is available. Any disagreement between engines is published with enough
detail to distinguish definitional differences from errors.

## 10A. Network geometry and what it forbids

This is a network, and its topology is an established fact stated in advance. It
is derived from the object's own arms, not assumed.

| Network element | Pre-specified value |
|---|---|
| **Nodes** | Artemether-lumefantrine; dihydroartemisinin-piperaquine; artesunate-amodiaquine; pyronaridine-artesunate |
| **Edges** | Dihydroartemisinin-piperaquine versus artemether-lumefantrine; artesunate-amodiaquine versus artemether-lumefantrine; pyronaridine-artesunate versus artemether-lumefantrine |
| **Trials per edge** | One trial per edge: Guinea-Bissau; Cameroon; Nigeria |
| **Shape** | A star centred on artemether-lumefantrine |
| **Connected** | Yes, all four nodes are reachable |
| **Independent loops** | E - V + 1 = 3 - 4 + 1 = 0 |

The network is connected, so indirect comparisons between the three ACTs ARE
computable.

There is NO closed loop, so the consistency assumption on which every indirect
comparison rests CANNOT BE TESTED. Not "was not tested" - cannot be, by the
geometry.

Therefore node-splitting, design-by-treatment interaction and every other
consistency check are UNAVAILABLE here, and their absence must never be reported
as consistency having been checked and found acceptable.

Each edge carries exactly ONE trial, so between-study heterogeneity is not
estimable on any edge and tau-squared cannot be separated from within-trial
error.

SUCRA or any ranking metric over this network would be a re-description of three
unreplicated comparisons and will NOT be reported as a ranking.

The single thing that would change this: a head-to-head trial between any TWO of
the three ACTs would close a loop and make consistency testable. Whether the
search finds one is a real, pre-specified test and not a formality.

## 11. Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** risk difference and odds ratio alongside the
primary log risk ratio; the zero-cell continuity correction described in Section
10; exclusion of records whose PCR-corrected treatment-failure definition cannot
be matched across arms; and, if an edge gains additional eligible trials,
leave-one-out and estimator comparison for that edge.

**Subgroup: none pre-specified.** With one trial on each established edge, any
subgroup contrast would be underpowered and post-hoc. Country, age band,
parasite species, dosing regimen, follow-up timepoint, and transmission setting
are extracted as descriptors and GRADE inputs, not as planned subgroup tests.

## 12. Meta-bias assessment

Funnel plot, Egger's regression, and Peters' test are not interpretable for the
pre-specified starting network. Below approximately ten studies these tests have
almost no power and the Cochrane Handbook advises against interpreting them.
With one trial per edge and three direct edges, publication bias and small-study
effects are therefore **not assessable**, not **not serious**. Where publication
bias cannot be assessed, the GRADE domain will read *not assessable* rather than
*not serious* - the two are different statements.

If the search returns enough additional eligible studies for a valid small-study
effects assessment, the tests named above may be computed for completeness and
will be reported as computed values with the same caveat.

## 13. Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 Section 14.2.1-14.2.2 and MECIR C74/C75. All
five downgrade domains are assessed and **each rating is published with the
evidence it rests on**; the overall certainty is computed from the domains and
shown against them so a reader can check the arithmetic.

For indirect comparisons, GRADE starts from the lower certainty of the two direct
comparisons that form the indirect estimate and then considers additional
downgrading for intransitivity, imprecision, incoherence where testable, and
publication bias where assessable. In this starting star network, incoherence is
not testable because there is no loop, and that limitation is carried into GRADE
rather than hidden.

**Status at the time of this commit: PENDING, and stated as pending rather than
implied as done.** No GRADE assessment exists for these comparisons in this
protocol. Performing it later **executes this section rather than amending it**,
and the object will record that distinction.

## 14. Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the scripts actually executed and the
session information for the analysis engines used. The intent is that the review
can be rebuilt from the object alone.

The search record is part of the reproducibility record. It records the exact
query attempted, source, local execution time, outcome of the attempt including
failed attempts, and any departure from Section 5. It is anchored after execution
so the protocol anchor and the search-record anchor bracket the operation.

## 15. Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16. Amendments

No amendments exist at the time this protocol is first written.

Amendments will be recorded as further commits to this file; the full commit
history, not only its head, is projected onto the review page, because a log that
displays only its own head is no better than a mutable document.
