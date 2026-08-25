# The join works. What it recovers is capped by something else entirely.

**886 real Cochrane study labels, run end to end to a registration: 128 reach one, against a
null of 1. But the flat rate is not the finding — stratified by year it is 0% before 2005 and
23% after 2015, and the reason is that the papers themselves do not carry registrations.**

---

## The pipeline, and one denominator

```
Study label ("Carter 1970")
  → the review's own bibliography, via review_doi + Crossref
  → that reference's DOI
  → PMID, via PubMed
  → NCT, via PubMed's DataBank secondary-id field
```

| of **886 labels attempted** | |
|---|---|
| not of the form `<name> <year>` | 31 |
| absent from its own bibliography | 117 |
| ambiguous — 2+ references matched | 62 |
| **resolved to exactly one reference** | **676 — 76%** |
| that reference carried a DOI | 620 |
| a PMID was found | 587 |
| **a registration exists in the DataBank field** | **128** |
| **END TO END, label → NCT** | **128 / 886 — 14.4%** |
| **NULL** — resolved in *another* review's bibliography | **1 / 886 — 0.1%** |

**No stage rates are multiplied.** Every figure above shares the denominator 886. The null is
1 in 886, so the resolution is not spurious surname-and-year agreement.

---

## The rate is not flat, and the shape is the finding

| era | labels | paper found | NCT | NCT / label | NCT / paper |
|---|---|---|---|---|---|
| pre-1990 | 28 | 16 | **0** | 0% | 0% |
| 1990–1999 | 73 | 49 | **0** | 0% | 0% |
| 2000–2004 | 93 | 60 | **0** | 0% | 0% |
| 2005–2009 | 123 | 88 | 16 | 13% | 18% |
| 2010–2014 | 154 | 109 | 25 | 16% | 23% |
| 2015+ | 384 | 265 | 87 | 23% | 33% |

**Zero before 2005 and non-zero after.** Trial registration became an ICMJE condition of
publication in 2005. The instrument was never told that and reproduces the discontinuity
exactly — which is the strongest internal-validity signal this measurement produces.

So 14.4% is a statement about *the age distribution of trials in Cochrane reviews*, not about
the join. A trial from 1970 has no registration to find, and no pipeline will find one.

---

## Why even the modern rate is 33%, and it is not the field

Two explanations had to be separated, and the cached records separate them:

**It is not that PubMed holds the registration somewhere else.** Of 2015+ records that name a
registration *anywhere* — abstract included — **87 of 87, 100%, carry it in the structured
DataBank field.** The field is not lossy. When a registration exists in the record, the
structured field has it.

**It is not that the wrong reference was matched.** Of the 178 modern records carrying no
registration, **137 — 77% — are PubMed-typed `Randomized Controlled Trial`.** These are real
trial reports, not review articles pulled in by a bad match.

Which leaves the actual reason:

> **Of 220 randomised controlled trials published 2015 or later and included in these Cochrane
> meta-analyses, 83 name a trial registration in their PubMed record and 137 do not — 62%
> carry none.**

---

## What that claim is, precisely

It is an **auditability** claim, not a registration claim. "No registration identifier in the
PubMed record" is not "the trial was never registered" — a paper may state its registration in
full text where PubMed does not capture it. The measurable fact is that a third party working
from the public record cannot get from the trial to its registration for 62% of modern RCTs in
this sample.

That is the same shape as the two findings before it, and they now form one argument:

| where the identifier is lost | measured |
|---|---|
| the Cochrane extraction schema has no registration column | 0 of 27 fields |
| the review does not name registrations in its text | 58 of 60 name none |
| **the underlying paper's PubMed record carries none** | **137 of 220 modern RCTs** |

The registration is obtained during risk-of-bias assessment — it appears in the free text of
D5 justifications — and then discarded at every layer below it.

---

## The resolution step is corroborated by a second database

"Exactly one reference matched" is a statement about the matcher. A matcher that agrees with
itself proves nothing — *consistency does not authenticate a row*. So the resolutions were
checked against an independent source.

Matching used **Crossref's** author field, carried in the review's own reference list. PubMed
indexes the same papers separately with its own `<LastName>`. Two databases, two population
processes:

| | |
|---|---|
| surname resolutions checkable against PubMed | 584 |
| **PubMed's own first author agrees with the Cochrane label** | **583 / 584 — 99.8%** |
| disagrees | 1 — `Høj 2005`, an ASCII-folding limit, not a wrong match |
| **null** — agrees with a *different* label's token | 36 / 584 — 6.2% |

The null is 6.2% rather than near zero because Cochrane labels repeat surnames inside one
review (`Legare 2008a`, `Legare 2011`, `Legare 2012`), so a shifted pairing is not a hard
test. That is precisely why it is reported rather than assumed away.

**Accent folding is load-bearing, not cosmetic.** Cochrane labels are ASCII while PubMed holds
the accented form. Compared raw, 21 correct resolutions score as disagreements — a 4% error
rate invented entirely by character encoding, and one that would have been reported as a
property of the join.

---

## Limits, stated

- **Sample rule fixed before the run:** every 15th of the 595 `.rda` files in
  `Pairwise70/data`, alphabetical — 40 reviews, 886 distinct labels. Not chosen after seeing
  which reviews behaved.
- **Pairwise70 is a third-party extraction of Cochrane data, not Cochrane's publication.** Its
  own repository description says 501 datasets where `/data` holds 595; the 595 is what was
  sampled.
- **"Resolved" means exactly one matching reference.** 62 ambiguous labels are counted as
  failures, not resolved by picking one.
- **Year matching is strict.** A ±1 variant is recorded per row and is deliberately excluded
  from every figure here.
- **Acronym labels** (`HYVET 2008`) are matched against reference titles rather than author
  surnames, counted separately, never folded into the surname rate.
- **The publication-type check is PubMed's own indexing**, not our judgement of what the paper
  is.
- Two instrument faults were found and fixed before these numbers: the NCBI id converter
  answers only for records **in PMC** and returned 218 of 620 (the PubMed-wide route returns
  587), and a cache-extension mismatch silently reduced a 265-record check to 1. Both were
  caught by the number being implausible, which is the only reason they were caught.
