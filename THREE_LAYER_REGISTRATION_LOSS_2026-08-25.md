# Obtained at D5, discarded at every layer below

## Trial registration identifiers in Cochrane meta-analysis data: three measured losses

---

### Summary

A Cochrane risk-of-bias assessment **requires** the assessor to consult the trial registry.
Domain 5 of RoB 2 — bias in selection of the reported result — cannot be judged without it,
and the identifier duly appears, written into the free text of the justification.

It appears nowhere else. Measured at three independent layers, the registration identifier is
obtained and then discarded:

| layer | what a third party receives | measured |
|---|---|---|
| the structured extraction | no field to hold it | **0 of 27 columns** |
| the review's own text | not stated | **315 of 331 name none — 95%** |
| the underlying paper's record | not indexed | **137 of 220 modern RCTs carry none** |

Each was measured separately, on its own sample, with its own denominator. None is derived
from another, and no rates are multiplied.

---

### Validation before any of it: the route reproduces a policy change it was never told about

Before the losses, the instrument that measures them has to be shown to work. It is a
pipeline from a Cochrane study label to a trial registration:

```
"Carter 1970"
  → the review's own bibliography, via review_doi + Crossref
  → that reference's DOI
  → PMID
  → NCT, via PubMed's DataBank secondary-identifier field
```

Run on 886 real Cochrane labels from 40 reviews, its yield stratifies like this:

| era | labels | with a registration |
|---|---|---|
| pre-1990 | 28 | **0%** |
| 1990–1999 | 73 | **0%** |
| 2000–2004 | 93 | **0%** |
| 2005–2009 | 123 | 13% |
| 2010–2014 | 154 | 16% |
| 2015+ | 384 | **23%** |

**Trial registration became a condition of publication under the ICMJE policy in 2005.** The
pipeline was never told that. It reproduces the discontinuity exactly.

**Replicated out of sample at ten times the scale.** The same rule applied at offsets 0–9 of
the same every-15th selection gives 400 reviews and 8,651 labels, of which **360 reviews and
7,765 labels are held out** — never seen when the original result was formed. Criteria were
fixed before the widened artefact existed:

| held-out 360 reviews, 7,765 labels | criterion | result |
|---|---|---|
| resolution to one reference | 66–86% | **74%** |
| pre-2005 labels carrying a registration | ≤2% | **0 of 1,688 — 0.0%** |
| null, resolved in another review's bibliography | ≤2% | **0.3%** |

**Zero of one thousand six hundred and eighty-eight.** Across three pre-2005 eras, not one
label in the held-out set resolves to a registration; from 2005 the rate is 8%, then 14%, then
17%. The discontinuity is not a small-sample artefact.

That is checkable by a reader in under a minute, and it is stronger evidence that the route
measures what it claims than any pass rate could be: a broken pipeline has no reason to place
its step in the right year.

Two further checks support it. The **null** — resolving each label against a *different*
review's bibliography — yields 1 in 886. And the resolution step is corroborated by an
independent database: matching used **Crossref's** author field, while **PubMed's** own
indexing agrees with the Cochrane label for **583 of 584** resolutions, against a null of 6.2%.

---

### Layer 1 — the extraction schema has no column for it

The public extraction package's structured schema, in full:

```
Analysis.group, Analysis.number, Analysis.name, Subgroup, Applicability,
Study, Study.year,
Experimental.cases, Experimental.N, Control.cases, Control.N,
Experimental.mean, Experimental.SD, Control.mean, Control.SD,
GIV.Mean, GIV.SE, O.E, Variance, Weight, Mean, CI.start, CI.end,
Footnotes, review_url, review_doi
```

Everything a meta-analysis needs, and **nowhere to record which trial a row is**. Studies are
`Carter 1970`, `Coope 1986`, `SHEP 1991`.

Where an identifier does appear, it is inside prose — the support text for *"Bias in selection
of the reported result"*:

> *"The prospective trial registry is available ClinicalTrials.gov (NCT00597194). Outcome
> analysed as pre-specified. Risk assessed to be low…"*

That is the one RoB 2 domain whose assessment requires the registry. The identifier exists in
the record because the method forced the lookup — and exists *only* there. Across a sample of
59 datasets, a registration appears anywhere in **2 (3%)**.

---

### Layer 2 — the review does not name them

**315 of 331 full-text reviews (95%) name no trial registration**, measured across two
sampling frames:

| frame | retrieved | **full text** | names ≥1 NCT | names none |
|---|---|---|---|---|
| general literature | 300 | 270 | 10 (4%) | **260 — 96%** |
| **Cochrane Reviews** | 200 | **61** | 6 (10%) | **55 — 90%** |
| pooled | 500 | 331 | 16 (5%) | **315 — 95%** |

**Cochrane is better than the general literature at this, and saying so is part of being
believed.** 10% of full-text Cochrane Reviews name at least one registration against 4%
elsewhere. Better — and still 90% unauditable.

**The denominator is full text, not records retrieved, and the correction matters.** A first
reading of the Cochrane frame gave 194 of 200 (97%). But **139 of those 200 are thin PMC
stubs** — median 20,629 bytes against 121,398 for real full text — and every one names no
registration *because it is not the article*. Counting them would have manufactured seven
percentage points out of a retrieval artefact. Only records carrying a reference list are
counted; 169 stubs are excluded rather than scored as reviews printing nothing.

#### The pair, and why both are reported

Naming no registration is one sufficient reason a review cannot be checked. There is a second,
independent one:

| | general | Cochrane | pooled |
|---|---|---|---|
| **names no trial registration** | 260 / 270 — 96% | 55 / 61 — 90% | **315 / 331 — 95%** |
| **prints no per-trial outcome table** | 185 / 270 — 69% | **NOT MEASURABLE** | **246 / 331 — 74%** |

Either alone stops an audit. A review could fix one and remain uncheckable, which is why they
are never reported separately.

**`NOT MEASURABLE` is in the table, not in a footnote.** Cochrane reviews *do* publish
per-trial data — Characteristics of Included Studies, and an Analysis table under every
comparison. Those tables are **not in the PMC deposit**, which carries 0–2 tables and no
captions for these records. A measured "0 of 61" would have been a property of the deposit and
not of Cochrane, so no rate is reported for that cell.

---

### Layer 3 — and neither does the paper

If the schema and the review both drop it, the last recourse is the trial report itself. Of
**220 randomised controlled trials published 2015 or later** and included in these
meta-analyses, **83 name a registration in their PubMed record and 137 do not.**

Two alternative explanations were tested and both fail:

- **Not a lossy field.** Of 2015+ records naming a registration *anywhere*, including the
  abstract, **87 of 87 — 100%** carry it in the structured DataBank field.
- **Not a mismatched reference.** Of the 178 modern records with no registration, **137 (77%)
  are PubMed-typed `Randomized Controlled Trial`** — real trial reports, not review articles
  pulled in by a bad match.

---

### The obvious remedy, and the one that does not work

**It cannot be recovered by effort.** The natural response is that a determined third party
could simply search the registry. Measured against 128 trials whose registration is *known* to
exist, a title search returns the correct record **42 of 128 times (33%)** and, of the 31
occasions it declared a confident match, **10 were the wrong trial**.

A method with 33% recall and 68% precision cannot establish that a registration is absent, and
cannot substitute for having the identifier. **The identifier is not a convenience that saves
labour. Labour does not replace it.**

**What does work costs one column.** At the moment of extraction the assessor already holds
the number — the method required them to look it up. Recording it is a keystroke, not a task.
No new lookup, no new burden, no methodological change. Everything downstream already
functions: given a registration, the public record answers.

---

### What this is, and is not

These are **auditability** claims. "No registration identifier in the record" is not "the trial
was never registered" — a paper may state its registration in full text where the indexed
record does not capture it. What is measurable is that a third party working from the public
record cannot get from a meta-analysis row to the trial's registration, and therefore cannot
mechanically check whether the row is about the trial it says it is.

**Limits.**

**PMC is not the literature.** Every full-text measurement here runs on PubMed Central
deposits. PMC is a subset of what is published, its deposits are not always the complete
article, and what a publisher deposits varies by publisher. Any figure derived from it
describes *the public deposit*, which is precisely the object an external auditor would have —
but it is not the same object as the published paper.

**Cochrane's own reviews are largely absent from it.** Of 200 Cochrane records retrieved, only
**61 carried full text**; the other 139 are thin stubs. Cochrane's per-trial tables do not
appear in the deposit at all. This cuts both ways and both are stated: it is why the per-trial
cell is `NOT MEASURABLE` rather than zero, and it is why the Cochrane frame's denominator is 61
rather than 200.

**A third-party extraction, not Cochrane's publication.** The schema examined is a public
extraction package. What Cochrane holds internally in RevMan is not visible here and may well
include registrations. The claim is about *the structured data that reaches third parties*,
which is what determines whether anyone outside can audit.

**The registry search covers ClinicalTrials.gov only.** Trials registered in ISRCTN, ANZCTR,
ChiCTR or another WHO primary registry are invisible to it, which makes 33% a floor rather
than a ceiling on what some combined search might achieve.

**Every panel figure this project holds is a single draw.** Counted from the ledgers: 298, 184
and 123 verdicts, all k=1, plus 38 adjudications of which 36 are k=1 and none records the SHA
of the artefact judged. The adopted specification is three independent adjudications by
majority vote against a pinned artefact — one draw is 91% reproducible, three are 99%. **No
figure in this document is a panel figure**; every number here is produced by executing code
against data. That separation is the reason this material is publishable while the panel
material is not yet.

**And reproducibility is not accuracy.** Where model judgements are used elsewhere in this
project, no ground truth exists for them: a consistently wrong panel is exactly as reproducible
as a consistently right one.

**Sampling rules were fixed before each run** and are recorded with each figure.

---

### Sources

| finding | evidence |
|---|---|
| the join and its era stratification | `FINDING_END_TO_END_JOIN_AND_THE_REGISTRATION_CEILING.md` |
| resolution corroborated against PubMed | `outputs/resolution_validated_2026_08_25.json` |
| the schema has no registration field | `FINDING_COCHRANE_EXTRACTION_HAS_NO_REGISTRATION_FIELD.md` |
| identification vs retrieval | `FINDING_THE_JOIN_FAILS_AT_IDENTIFICATION_NOT_RETRIEVAL.md` |
| title search is not a substitute | `FINDING_TITLE_SEARCH_IS_NOT_A_SUBSTITUTE_FOR_A_REGISTRATION.md` |

Every figure in this document is produced by executing code against data, not by a model
judgement. None of it is affected by the k=3 adjudication specification
(`ADJUDICATION_DRAW_INVENTORY_2026-08-25.md`).
