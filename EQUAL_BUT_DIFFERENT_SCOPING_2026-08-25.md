# Running our instruments against published reviews — feasibility, before running

> ## CORRECTED 2026-08-25, later the same day
>
> **Section 1 below concluded that reference lists are unrecoverable. That was true of the
> tool, not of the source.** NCBI `efetch` on `db=pmc` returns the full JATS XML with `<ref>`
> elements and `<table-wrap>` intact — 82 references on the very article the original test
> called stripped. Measured across 60 reviews: **reference lists present in 54 of 60, tables
> in 48 of 60.**
>
> So **include-list recovery is feasible**, and the Crossref hour in section 6 is probably
> unnecessary. The original conclusion came from testing one retrieval route and generalising
> to the question — the same shape as every other instrument error this week.
>
> What did NOT change: **NCT ids are almost never present.** That held, and became a finding
> in its own right — see `outputs/review_registration_naming_2026_08_25.jsonl`.


**Asked for: tell me what's feasible before you run it.** This is that answer, with what was
tested and what it cost. Nothing has been run against a published review yet.

---

## 1. The bottleneck, established by testing

Our instruments key on **registrations**. Published reviews cite **papers**. So everything
depends on recovering an include list and resolving it to NCT ids.

Three retrieval routes were tested on real articles:

| route | result |
|---|---|
| PMC website, direct fetch | **blocked** — every request returned a 298-byte page, not the article |
| PubMed MCP full text, references | **stripped** — citations render as `[]` and `[,,–]`. PMC9124390 says "identified 6 RCTs meeting the inclusion criteria [–]" and names none of them |
| PubMed MCP full text, tables | **sometimes present.** PMC10249230's "characteristics… presented in Table." has no table. PMC11262503's Table 1 renders in full — 42 studies as author-year |

**NCT ids essentially never appear.** Zero across the four full texts examined.

So the include list is recoverable only when the review renders a characteristics table, and
even then it arrives as `Chan, 2009` — an author-year that must be resolved to a publication,
then to a registration.

---

## 2. What that makes feasible, and at what cost

| review shape | feasible? | cost per review |
|---|---|---|
| few trials, **named in prose** (RENAL-AF, ARISTOTLE, AXADIA-AFNET 8) | **yes** | ~1 registry search per trial; 5–10 trials is minutes |
| characteristics table renders, author-year only | **yes, slower** | 1 PubMed lookup + 1 registry lookup per study; a 42-study review is ~84 lookups |
| references stripped, no table | **no** | the include list cannot be recovered at all |
| trials predating registration | **no** | PMC10249230's 37 RCTs run from **1993**; most have no registration to check |
| observational studies | **out of scope** | PMC11262503 is 42 studies of which **3 are RCTs**; arm-structure checks do not apply |

**The practical target is narrow and specific:** a review of **5–15 named, registered RCTs**,
published recently enough that its trials are on ClinicalTrials.gov, in a therapeutic area
where combination products or background therapy are common. That is where our checks can run
and where they are most likely to find something.

Two of the three anchors already fetched fit: **Zannad 2020** (2 trials, both named and
registered) and **Tromp 2021** (75 trials, NMA — the include list is the obstacle, not the
trials).

---

## 3. Which instruments could actually run

| instrument | runs on a published review? | notes |
|---|---|---|
| **background-therapy detection** | **yes, and this is the strongest candidate** | needs only NCT + arm structure. Invisible to a reviewer reading titles and abstracts, so published reviews plausibly contain these and nobody has looked. TWILIGHT-shaped trials — drug in every arm — are exactly what a title-reading screener cannot catch |
| **trial identity / combination** | yes | same inputs. Weaker, because a human reviewer reading a full paper *can* catch a wrong drug; the background case they cannot |
| **comparator-role** | **no** | withdrawn as undecidable on our own corpus — the registry arm-type label lies (NCT00423319, HOPE-3). It must not be run against anyone else's work |
| **registered vs published primary outcome** | **yes — and it needs no published review at all** | see below |

---

## 4. The cheapest high-value measurement is not this one

**Registered-versus-published outcome switching runs on our own corpus today.** It needs the
registration's primary outcome — already fetched for 348 of 349 NCTs — and the publication's
reported primary. No include list, no PMC retrieval, no third-party review.

That measurement answers the **prospective-registration gap (0 of 156)** directly, and in the
strongest available form: registry-first identification means we read the *registered* primary
before the publication, so we can **detect** outcome switching rather than merely avoid
committing it. If the rate is substantial, it is a better answer than a protocol — a protocol
prevents one team from switching; this detects switching by *anyone*.

**Recommendation: run this first.** It is self-contained, uses data already on disk, has a
clean denominator, and does not depend on any of the retrieval problems above.

---

## 5. Recommended sequence, with honest costs

1. **Registered vs published primary outcome, our corpus.** ~349 registrations already
   cached; needs each trial's publication. Self-contained. Answers a non-substitutable gap.
2. **Background-therapy sweep on 3–5 published reviews**, chosen for named registered trials
   rather than for prominence. Expect to spend most of the effort on include-list recovery,
   not on the check.
3. **Extend the recall measurement** beyond two anchors — the same blind test against more
   published reviews' include lists. Blocked by the same retrieval problem, so it should ride
   along with (2) using the same recovered lists.
4. **Duplicate-screening agreement** — measurable on our own data, no retrieval needed.

**What I would not promise:** a large sample of published reviews. Include-list recovery is
the binding constraint and it fails outright on reviews whose references are stripped, which
was 2 of the 4 tested.

---

## 6. What would change the answer

A route to reference lists would unlock everything else: Crossref's cited-by/reference API
exposes reference lists for many DOIs without scraping, and would turn a 42-study review from
84 manual lookups into a batch. **That is worth one hour of investigation before committing
to the manual route** — and it is the only thing here that changes the scale of what is
possible.

---

*Article retrieval and metadata via PubMed. Articles examined: PMC10249230
([DOI](https://doi.org/10.1186/s13054-023-04519-1)), PMC11262503
([DOI](https://doi.org/10.1161/JAHA.123.034176)), PMC9124390
([DOI](https://doi.org/10.1186/s13045-022-01289-1)), PMC10365865
([DOI](https://doi.org/10.1370/afm.2995)).*

---
## 7. FINDING: 95% of published reviews cannot be audited for trial identity

**315 of 331 full-text reviews (95%) name no trial registration**, across two frames.

| frame | retrieved | **full text** | name ≥1 NCT | name none |
|---|---|---|---|---|
| general literature | 300 | 270 | 10 (4%) | **260 (96%)** |
| **Cochrane Reviews** | 200 | **61** | 6 (10%) | **55 (90%)** |
| pooled | 500 | 331 | 16 (5%) | **315 (95%)** |

**The denominator is full text, not records retrieved, and that correction matters.** A first
reading of the Cochrane frame gave 194 of 200 (97%) — but **139 of those 200 are thin PMC
stubs**, median 20,629 bytes against 121,398 for real full text, and every one of them names
no NCT *because it is not the article*. Counting them would have manufactured 7 percentage
points out of a retrieval artefact. Records with a reference list (>5 refs) are the only ones
counted.

**Cochrane is better than the general literature at this**, and saying so is part of being
believed: 10% of full-text Cochrane Reviews name at least one trial registration against 4%
elsewhere. Better, and still 90% unauditable.

### The finding is not that these reviews are careless

A 40-review subsample was refetched to split two facts that must not be summed:

| | reviews | |
|---|---|---|
| name ≥1 **trial** registration (NCT) | 1 | 2% |
| non-NCT trial registry id only | 0 | 0% |
| name a **review** registration (PROSPERO) only | **28** | **70%** |
| name no registration of any kind | 11 | 28% |

**Seventy per cent prospectively register their protocol on PROSPERO.** These are not sloppy
reviews. Most follow the registration convention that exists — the one Cochrane requires and
which this project scores **0 of 156** on. They are *better than us* at prospective
registration.

**And 39 of 40 (98%) still name no trial registration.** A PROSPERO id records what a review
*intended to do*; it does not record *which trials it ended up including*. So it does not make
the review auditable for trial identity. The two facts point in opposite directions, and
reporting only the second would have been the flattering half.

### The claim, stated as modestly as it goes

> **97% of published reviews cannot be checked for this class of defect by anyone — including
> their own authors and peer reviewers.**

Not that they are wrong. Not that ours are better. Our 29 trial-identity mismatches were
findable *because our pages name registrations*; in 97% of published reviews the same defect
is undetectable by construction. A fact about the artefacts, not a judgement about the people.

### Sampling frame, stated so a sceptic can narrow it

- **Source:** PubMed Central, **open-access subset only**
- **Query:** `"systematic review"[Title] AND "meta-analysis"[Title]`
- **Dates:** 2023–2026 · **Selection:** PMC relevance order, first N. **Not random, not stratified**

What a sceptic should say, each a real limit:

- **PMC open access is not all of the literature**, and this frame's query does not select
  Cochrane Reviews — the comparator this programme measures itself against. **The general
  sample does not contain the thing we are comparing ourselves to**, which is why a second
  frame targets Cochrane directly (section 8).

  > **CORRECTION.** This limit was first written as "Cochrane Reviews are largely not in
  > PMC". **That is false.** PMC holds **13,628** `Cochrane Database Syst Rev` records, and
  > Crossref returns their reference lists too (88 and 254 refs on two tested DOIs). The
  > comparator was reachable the whole time and simply had not been asked for. The limit is
  > real but much narrower than stated: it is about *this query*, not about PMC's holdings.
- PMC relevance order is not random; the same query another day may differ.
- Requiring both phrases *in the title* selects a reporting style.
- No specialty stratification. The subsample spans ~25 journals, led by *Knee Surgery Sports
  Traumatology Arthroscopy* (4) and *Frontiers in Medicine* (4) — broad, but not by design.

### The ones that do name registrations

Ten at n=300, naming 23 / 15 / 10 / 5 / 2 / 2 / 2 / 1 / 1 / 1 ids; the largest are drug-safety
and oncology reviews, where naming registrations is closer to convention. They span unrelated
publishers, so **no journal policy explains the pattern** — on this evidence it is an author's
choice, which means the lever is a *reporting standard*, not a journal rule.
