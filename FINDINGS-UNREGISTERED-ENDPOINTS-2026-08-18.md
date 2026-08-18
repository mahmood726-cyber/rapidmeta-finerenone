# Trials that register no clinical endpoint — measured across two specialties

The prior number was a screen over primary titles. This is a **reading of every rank —
primary, secondary and other — on every seeded trial of every topic** in two sections.

---

## The measurement

| | infectious disease | cardiology |
|---|---|---|
| topics in section | 62 | 53 |
| **topics readable by this method** | **58** | **24** |
| **ALL seeded trials register no clinical endpoint** | **12** | **6** |
| MIXED — some do, some do not | 6 | 7 |
| every trial registers one | 40 | 11 |
| no registration seeded *(not readable)* | 4 | **29** |

**The cardiology denominator is 24, not 53, and that has to be said first.** Twenty-nine
of its pages carry no `AUTO_INCLUDE_TRIAL_IDS` seed — they are the v1 projector
generation, which holds its trials in the SSOT object rather than in an embedded
JavaScript seed. **This method cannot read them**, so cardiology's figure is over the 24
app-generation pages only.

---

## The comparison, and it is not what was expected

**On readable topics: infectious disease 12 of 58 (21%); cardiology 6 of 24 (25%).**

**These are not meaningfully different.** The working hypothesis — that the class is
systematic in infectious disease because vaccine trials register immunogenicity while the
literature reports efficacy — **is not supported by this comparison.** The class appears
at a similar rate in both sections.

**And it corrects our own closed section.** Cardiology was closed having found **three**
instances of this class by hand. Reading every rank systematically finds **6 ALL and 7
MIXED among just the 24 readable pages.** The hand search under-counted, which is what a
hand search does — and the correction belongs on our record, not on anyone else's.

---

## The distinction that matters more than the count

**"Registers no clinical endpoint" is a statement about the registration, not about the
trial.** Two very different situations produce it, and only one is a criticism of a
synthesis:

| | infectious disease | cardiology |
|---|---|---|
| trials in the ALL group | 30 | 15 |
| whose registration's **own title** says safety / immunogenicity / pharmacokinetics | **15** | **12** |
| the remaining, selective-reporting shape | 15 | 3 |

**Half the infectious-disease cases, and four fifths of the cardiology ones, are trials
that say on their own face what they are.** A phase-3 immunogenicity trial registering
immunogenicity endpoints **is behaving correctly**. The defect is a synthesis treating it
as an efficacy trial.

**The criticism belongs on the pooling, not on the registration**, and this file is
written that way deliberately.

The other half — 15 in infectious disease, 3 in cardiology — are the **selective-reporting
shape**: registrations that are not self-described as non-clinical, whose clinical result
appears in the literature and not in the registration. Those fall under Handbook 6.5
**§8.7**, bias in selection of the reported result, and the ruling already applies: **keep,
flag high risk, sensitivity-analyse, do not exclude on eligibility.**

---

## What this does not establish

- **NOT that the published efficacy figures are wrong.** It establishes that the quantity
  was not pre-specified in the registration the page keys to.
- **NOT that no clinical endpoint exists in the publication.** Registries are amended and
  publications report more than they register. This reads registrations only.
- **NOT a rate for either specialty as a whole.** Cardiology's 24 readable pages are a
  biased subset — the app generation — and nothing here establishes that the 29
  unreadable ones behave the same way.
- **NOT a criticism of trialists.** See above; for more than half the cases the
  registration is doing exactly what it should.
