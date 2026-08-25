# Running our instruments against published reviews — feasibility, before running

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
