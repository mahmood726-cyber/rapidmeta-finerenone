# The question "are they findable by hand?" could not be answered — and that is the answer

**137 RCTs published 2015+ in these Cochrane meta-analyses carry no registration in their
PubMed record. The obvious next question is whether a determined third party could find them
anyway by searching the registry on title. Measured against trials whose registration is
already known, that method recovers 33% and is wrong a third of the time it feels certain. So
it cannot answer the question — and the reason it cannot is itself the finding.**

---

## The ceiling, measured before the result was read

128 papers in the same sample **do** carry a registration in their PubMed DataBank field, so
their NCT is known independently of any search. Running the identical title search on those:

| on trials whose registration is KNOWN to exist | |
|---|---|
| true NCT returned anywhere in the result set | **42 / 128 — 33%** |
| a record cleared the pre-stated 0.50 title-overlap rule | 31 / 128 — 24% |
| **the record it picked was the true NCT** | **21 / 128 — 16%** |

Two things follow, and the second is worse than the first:

**Recall is 33%.** Two thirds of registrations that certainly exist are not retrieved by a
title search at all.

**Precision is 68%.** Of the 31 cases where the rule declared a confident match, **10 were the
wrong trial.** One example from the run: a paper whose true registration is `NCT03150589`
matched `NCT02611778` at 0.58 overlap — over threshold, confidently reported, wrong.

A method that finds a third of what exists and misidentifies a third of what it finds cannot
be used to establish that anything is *absent*.

## So the findable measurement is NOT MEASURABLE

The run over the 137 returned 0 found. **That number is not reported as a result.** With a
33% ceiling and 68% precision, "0 found" is indistinguishable from "the search cannot see
them", and the honest verdict is that this method cannot answer the question.

---

## What is established, and it is not nothing

> **Title-based registry lookup is not a workable substitute for a registration identifier.**
> On trials whose registration is known to exist, it recovers 33% and misidentifies 32% of its
> confident answers.

That sharpens the auditability argument rather than weakening it. The hoped-for finding was
"auditable only by per-trial detective work". The measured position is worse: **the obvious
form of detective work does not reliably work either.** A third party who does the labour the
field assumes nobody will do still ends up with a third of the registrations and no way to
know which third of their confident matches are wrong.

The registration identifier is not a convenience that saves effort. It is not substitutable by
effort.

---

## Three instruments, and only the known positive settled it

This measurement was built three times, and the first two produced clean, plausible, entirely
false numbers:

| version | query | reported | what it actually measured |
|---|---|---|---|
| v1 | AND of 18 title words | **4% findable** | ClinicalTrials.gov ANDs bare terms; almost no registry title contains all eighteen |
| v2 | OR of 12 title words | **0% findable** | 50 candidates returned every time, true record never among them |
| v3 | AND of 4, backing off to 3 then 2 | — | retrieves the known case exactly; **still only 33% recall** |

Both false versions produced a *number*, formatted like a result, with a null test attached
and passing. Neither was caught by the null, by the controls on the matcher, or by inspection.
**Only running the search against trials whose answer was already known exposed them** — and a
known positive was available from the start.

That is rule 00c, and this is the case that earns it: *a new check's first run is not
information until a known positive proves it.*

---

## Limits, stated

- **128 known-registered papers** from the same 886-label sample. The ceiling carries that
  denominator.
- **The 0.50 title-overlap rule was fixed before any run** and is not tuned to these results.
  Loosening it would raise recall and lower precision; both are reported so the trade is
  visible rather than chosen.
- **This measures ClinicalTrials.gov only.** A trial registered in ISRCTN, ANZCTR, ChiCTR or
  another WHO primary registry is invisible to this search, which is one reason recall is low
  and a reason the 33% is a floor on what *some* combined search might achieve.
- **Sponsor and year were not used as additional filters.** Adding them would change precision
  and recall in unknown directions; the claim is about title search specifically.
- A found record would in any case prove only that a third party could *reach* a plausible
  registration — never that the trial was prospectively registered, nor that the registration
  is correct.
