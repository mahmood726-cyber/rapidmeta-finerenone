# Protocol — sacubitril/valsartan versus enalapril in heart failure with reduced ejection fraction

**Status: REGISTERED BY COMMIT. This document is the registration.**

This protocol is registered as a timestamped commit in a public repository rather
than in PROSPERO. The commit hash and its committer timestamp are the record: the
content is immutable under that hash, the timestamp is set by the repository and
not by the authors, and anyone can verify both without asking us. The claim this
supports is narrow and it is stated here so it cannot be overstated later — a
commit proves *when this text entered this repository*. It does not prove that no
earlier or parallel version existed elsewhere, that the data had not already been
seen, or anything about the independence of the people who wrote it.

**It is written before the search runs.** The ordering test this review will
publish is that this commit precedes the first executed query. The search lane
records its own start time independently; both timestamps go into the canonical
object so a reader can check the sequence. That is the thing PROSPERO records
cannot demonstrate, because a PROSPERO entry can be edited and its history is not
public in the same way.

---

## 1 · Review question, in PICO

| | |
|---|---|
| **Population** | Adults with chronic heart failure and reduced ejection fraction. |
| **Intervention** | Sacubitril/valsartan (LCZ696). |
| **Comparator** | Enalapril. |
| **Outcome** | The composite of cardiovascular death or first hospitalisation for heart failure, whichever occurs first. |
| **Study design** | Randomised controlled trials. |

**Frozen question:** in adults with heart failure and reduced ejection fraction,
what is the hazard of a first cardiovascular death or heart-failure
hospitalisation with sacubitril/valsartan compared with enalapril?

## 2 · Estimand, stated in advance

The estimand is the **time-to-first-event hazard ratio for the composite**, on the
log scale, with the participant as the unit of analysis and the time to the first
component event as the event time.

**Quantities that cannot be converted into that estimand are excluded on the
OUTCOME axis, not on grounds of quality.** This is pre-registered because it is a
criterion and not a judgement made after seeing results. A trial may be large,
well conducted and directly on topic and still fail this review's eligibility
because it reports something else. Specifically and in advance:

- A **recurrent-event rate ratio** counts repeat events per person over time; a
  time-to-first hazard ratio counts each person once, at their first event. The
  two share a scale and a direction and answer different questions. A rate ratio
  will not be stored in a hazard-ratio field.
- A **win ratio** over a hierarchical composite is not this estimand.
- A **dichotomous risk ratio** at a fixed timepoint is not this estimand, though
  where per-arm counts are recovered a risk ratio, odds ratio and risk difference
  will be computed and reported as **sensitivity analyses only**, never as the
  headline.

## 3 · Eligibility criteria

**Include** a study if all four hold: it is randomised; it enrols adults with
heart failure and reduced ejection fraction; it randomises sacubitril/valsartan
against enalapril; and it reports the composite of cardiovascular death or first
heart-failure hospitalisation as a time-to-first-event hazard ratio.

**Exclude** on any single failed axis — population, intervention, comparator, or
measure — and record which axis failed and what the study reports instead.

Populations narrower than the question (for example a single aetiology) are
**not** indirect on that ground alone; narrowness is recorded and carried into the
GRADE indirectness domain rather than used as an exclusion.

## 4 · Information sources

PubMed; ClinicalTrials.gov; the reference lists and included-study tables of every
retrievable published synthesis of the same comparison; and, where a cell cannot
be established from those, the FDA statistical review and the EMA EPAR for
Entresto.

## 5 · Search strategy — the exact strings to be executed

These strings are stated **before** execution. The search lane will record what it
actually ran, on what date, with what filters, and how many records each returned;
any departure from the strings below will be recorded as a departure rather than
silently substituted.

**PubMed**

```
("sacubitril valsartan"[tiab] OR "LCZ696"[tiab] OR sacubitril[tiab] OR Entresto[tiab])
AND (enalapril[tiab] OR "angiotensin converting enzyme inhibitor"[tiab] OR ACEI[tiab])
AND ("heart failure"[MeSH Terms] OR "heart failure"[tiab] OR HFrEF[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

Filters: none on language, none on date. Rationale: a language filter would make
the search unreproducible across interfaces and would exclude the Japanese and
Chinese literature this comparison has.

**ClinicalTrials.gov (API v2)**

```
query.intr=sacubitril valsartan OR LCZ696
query.cond=heart failure
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

**Backward citation search**

The included-study table of every retrievable synthesis of this comparison is
read and diffed against this review's included set in both directions. A trial
present in theirs and absent from ours is a candidate; a trial present in ours and
absent from theirs is recorded as a difference to explain.

## 6 · Study selection process

Two **independent screeners of different model families** — the cross-family rule
is a requirement, not a preference, because two instances of one model is one
screener run twice and its agreement statistic is meaningless.

Screening is in two stages: title and abstract, then full text. **Each screener's
decision is recorded per record at the stage it was applied**, together with the
reason. Both screeners' decisions are published, not only the reconciled outcome,
along with the agreement rate and how every disagreement was resolved.

**Adjudication of disagreements is by a named human.**

**Two release tiers, and the difference between them is attestation, not content.**
The website release requires the two cross-family AI assessments and states plainly
that it has not been human-verified. The submission release additionally requires
two named human reviewers to have checked every included study and every extracted
datum; the statement to that effect is emitted only when those attestation records
exist and is never written as prose.

## 7 · Data extraction

Extracted per trial and per outcome: registry identifier, primary publication,
year, design, population, arms, **the analysed denominator and the randomised
total separately**, per-arm event counts, and the published effect estimate with
its interval and its stated confidence level.

Every extracted cell carries a resolvable pointer to the specific document and,
where possible, to the table within it, so that a human check can be made without
leaving the page. **Nothing is computed that can be read.** No count is derived
from a percentage; no composite is reconstructed by summing its components.
Identifiers are resolved by lookup, never from recall.

Where two populations exist for one outcome — for example a full analysis set and
a randomised set — both are recorded, exactly one is marked as selected, and the
population is named on the cell.

## 8 · Outcomes and prioritisation

**Primary:** the composite of cardiovascular death or first heart-failure
hospitalisation, as a time-to-first-event hazard ratio.

**Components, read and reported but not pooled:** cardiovascular death; first
heart-failure hospitalisation; all-cause death. They are shown because a reader
should see them; they are not pooled because the review's estimand is the
composite.

## 9 · Risk of bias

Cochrane RoB-2, at the level of the result being pooled, by two independent
cross-family assessors with human adjudication.

**PENDING, and stated as pending rather than implied as done.** At the time of
this commit no RoB-2 assessment exists for these trials. The object currently
holds *recorded bias-relevant features* — blinding status, endpoint adjudication,
endpoint rank within its own trial, early stopping — each traceable to a source,
and those features feed the GRADE risk-of-bias domain. They are not a RoB-2
judgement and are not presented as one.

## 10 · Synthesis methods

Random-effects meta-analysis on the log hazard-ratio scale, inverse-variance
weighted.

**Pre-specified, so that reporting a disagreement between methods is a commitment
rather than a post-hoc observation:**

- **REML** is the headline between-study-variance estimator.
- The **Hartung–Knapp–Sidik–Jonkman interval is reported alongside** the Wald
  interval, and where the two disagree about whether the interval crosses the
  null, that disagreement is reported in the results rather than resolved by
  choosing one.
- **Leave-one-out** analysis is run and reported for every pool.
- An **estimator comparison** — DerSimonian–Laird, REML, Paule–Mandel — is run and
  reported, per Cochrane Handbook v6.5 §10.10.4.4, on the understanding that with
  few studies the choice is plausibly influential.
- A **prediction interval** is reported using the t distribution on k−1 degrees of
  freedom per Handbook v6.5, and is not reported where k makes it undefined.
- The analysis is **cross-checked in a second engine** (R with metafor) at build
  time and the comparison published, including any quantity on which the two
  engines disagree by definition rather than by error.

**Heterogeneity:** τ², I² with its Q-profile confidence interval, and Q with its
degrees of freedom and p value. I² is reported with the caveat that at small k a
low value reflects imprecision as much as agreement.

## 11 · Subgroup and sensitivity analyses

**Sensitivity, pre-specified:** leave-one-out; the estimator comparison above;
and, where per-arm counts are recovered, the same 2×2 pooled as a risk ratio, an
odds ratio and a risk difference — reported as sensitivity to the primary
hazard-ratio pool, never as the headline.

**Subgroup: none pre-specified.** With the small number of trials this comparison
has, any subgroup contrast would be underpowered and post-hoc, and none will be
presented as though it were planned.

## 12 · Meta-bias assessment

Funnel plot, Egger's regression and — for any count-based pool — Peters' test.
**Pre-specified caveat:** below approximately ten studies these tests have almost
no power and the Cochrane Handbook advises against interpreting them. Where k is
below that threshold the tests may still be computed for completeness, and will be
reported as computed values, explicitly not as evidence about small-study effects.
Where publication bias cannot be assessed, the GRADE domain will read *not
assessable* rather than *not serious* — the two are different statements.

## 13 · Certainty of the evidence

GRADE, per Cochrane Handbook v6.5 §14.2.1–14.2.2 and MECIR C74/C75. All five
downgrade domains are assessed and **each rating is published with the evidence it
rests on**; the overall certainty is computed from the domains and shown against
them so a reader can check the arithmetic.

## 14 · Data sharing and reproducibility

The canonical data object from which every number on the review page is projected
is published with the review, together with the R session information and the
analysis scripts actually executed. The intent is that the review can be rebuilt
from the object alone.

## 15 · Funding and conflicts of interest

**No funding was received for this review.** No competing interests are declared
by the authors of this protocol at the time of this commit. Any change is to be
recorded as an amendment rather than by editing this section.

## 16 · Amendments

None at the time of this commit. Amendments will be recorded as further commits
to this file; the full commit history, not only its head, is projected onto the
review page, because a log that displays only its own head is no better than a
mutable document.
