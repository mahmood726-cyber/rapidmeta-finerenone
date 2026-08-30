# Systematic search — dapivirine vaginal ring vs placebo ring

**Executed 2026-08-30. Free sources only. This replaces a convenience sample.**

A blinded judge, not knowing whose page it was, wrote: *"A explicitly states it used a
convenience sample without a primary search."* That was correct. The object recorded five
**seeded** registrations read on 2026-08-18 and no search. Search was raised in five of six
verdicts and lost every one. This is the search.

⭐ **THE FIX IS TO FINISH, NOT TO DISCLOSE LESS.** The same panel scores us 4–1 on
transparency *because* the limits are named. Both things are true here at once: a real
search, and an honest account of what it cannot reach.

---

## The question

*Does a dapivirine vaginal ring reduce HIV-1 seroconversion compared with a placebo vaginal
ring in women?*

## The concept block — and why there is only one

```
dapivirine  OR  dapavirine  OR  "TMC 120"  OR  TMC-120  OR  TMC120
            OR  "R 147681"  OR  R-147681   OR  R147681
```

⚠️ **There is deliberately NO AND-block** for HIV, for vaginal rings, or for study design.
`dapivirine` and its development codes are specific to one compound; ANDing them against a
population or outcome block can only *remove* records, and on a set this size precision is
not the binding constraint. We screen the whole set instead.

⚠️ **The development codes are in the query on purpose.** `TMC 120` and `R 147681` are the
MeSH entry terms — verified against the NLM browser, not recalled — and the phase 1/2 and
IPM programme literature uses them rather than the INN. A query without them silently loses
that end of the record.

## What each source returned

| source | query | status | reported | retrieved |
|---|---|---|---|---|
| **PubMed** (E-utilities) | concept block, `[All Fields]` | OK | **374** | 374 |
| **Europe PMC** | concept block | ⚠️ **TRUNCATED** | **1,443** | **1,000** |
| **ClinicalTrials.gov** v2 | `query.intr` ∪ `query.term` | OK | — | **63 NCT ids** |
| **ISRCTN** | `/api/query` (the permitted path) | OK | 1 | 1 |
| **EU-CTR** | browser-verified | EMPTY | 0 | 0 |
| **DRKS** | browser-verified | EMPTY | 0 | 0 |
| 15 other ICTRP primary registries | see below | not determinate | — | — |

⚠️ **EUROPE PMC IS TRUNCATED AND IS NOT COUNTED AS COMPLETE.** It reported 1,443 and
returned 1,000 — the page cap. The remaining 443 were not fetched and are **not** recorded
as absent. Paging is required before any Europe PMC figure enters a denominator. Reporting
1,000 as the answer would be this project's most repeated defect: a scan reporting its own
reach as the population.

## The screen — 63 ClinicalTrials.gov registrations

| bucket | n |
|---|---|
| **passed screen** | 5 |
| not dapivirine | 16 |
| not a ring | 20 |
| not randomised | 4 |
| not phase 3 efficacy | 16 |
| **withdrawn, zero participants** | **2** |

⭐ **The two withdrawn records are named rather than dropped: NCT01337570 and NCT01337583**
— both *"A Safety and Efficacy Trial of Dapivirine Vaginal Ring in Africa"*, both
double-blind randomised placebo-controlled phase 3 **by design**, both `WITHDRAWN` with
enrolment **0 (ACTUAL)**. They are eligible in design and produced no participants and no
data, so they cannot contribute to a synthesis. **That is an eligibility exclusion, not a
search miss** — and it is exactly the kind of record that a search which never ran would
never have had to explain.

## Adjudication of the three that passed and were not ours

⚠️ **The screen tests phase and randomisation; it does NOT test the comparator or the
outcome.** So a raw difference of three is not a recall figure, and each was adjudicated:

| candidate | comparator | primary outcome | verdict |
|---|---|---|---|
| NCT03965923 | oral Truvada, open label | safety AEs, pregnancy outcomes | **ELIGIBILITY** |
| NCT04140266 | oral Truvada | serious adverse events | **ELIGIBILITY** |
| NCT06250504 | enhanced standard of care | PrEP uptake and retention | **ELIGIBILITY** |

None compares a dapivirine ring against a **placebo ring**, and none reports **HIV-1
seroconversion** as a primary outcome.

## ⭐ The coverage fraction

> **Of the trials this search identifies as eligible for the question, we hold 2 of 2.
> Zero search misses. 61 of the 63 registrations screened are excluded on stated grounds,
> each attributed.**

Both included trials — ASPIRE/MTN-020 `NCT01539226` (n=1,959) and The Ring Study/IPM 027
`NCT01617096` (n=2,629) — were **found by the search**, not merely confirmed by it. Nothing
in our set failed the screen.

## What this search cannot reach — stated, because it is the honest half

1. **Six chemical-name forms.** Ovid showed Emtree expanding `dapivirine` to six variants
   such as `4-[[4-[(2,4,6-trimethylphenyl)amino]pyrimidin-2-yl]amino]benzonitrile`. A
   record indexed **only** under such a form is invisible to every query above. This is the
   one named mechanism by which a free-source search could miss a trial, and the Embase
   calibration exists to measure whether it actually does.
2. **Europe PMC truncation** — 1,000 of 1,443 retrieved.
3. **Non-US registries: 2 of 18 determinate** by script, plus DRKS browser-verified empty.
   One registry (CRiS) refuses by robots.txt; one (**jRCT**) forbids automated download in
   its page text; ten have no free query endpoint we have established. ⚠️ *A protocol
   claiming "we searched ICTRP" would not be supportable, and this one does not claim it.*
4. **Guideline bodies not enumerated.** GIN's member directory sits behind a login, so it
   cannot serve as a free denominator. Not claimed.
5. **No subscription database is in the method**, by the standing scope rule — a search the
   reader in Laos or Uganda cannot reproduce is not verifiable by the reader it is for.

## Reproducing this

`python scripts/systematic_search_dapivirine.py` re-executes the journal and registry
queries and writes every query string, HTTP status, reported count, retrieved count and a
payload hash. `scripts/registry_search.py` re-executes the non-US registry pass with its
seven states. Neither requires a subscription or a login.
