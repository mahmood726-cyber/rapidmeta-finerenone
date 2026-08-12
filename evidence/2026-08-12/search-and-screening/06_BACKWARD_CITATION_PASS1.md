# Backward citation search — pass 1 (partial)

Protocol §5: *"The included-study table of every retrievable synthesis of this comparison is read and diffed against this review's included set in both directions. A trial present in theirs and absent from ours is a candidate; a trial present in ours and absent from theirs is recorded as a difference to explain."*

**Status: PARTIAL — 1 of 45 flagged syntheses read.** This is a first pass, not the registered step completed. It is reported now because it already found something.

---

## Synthesis read

Ali S, et al. *Efficacy and Safety of Sacubitril/Valsartan Versus Enalapril in the Treatment of Heart Failure With Reduced Ejection Fraction: A Systematic Review and Meta-Analysis.* Cureus 2026. PMID **41773097**, PMCID **PMC12950259**.

Chosen first because its question is the closest match in the corpus to ours — same intervention, same comparator, same population. Included-study table read at source (Table 1, 12 studies).

## Diff — their included set against ours

| Their study | Design (theirs) | Matched in our 423-record corpus? | Our decision | Note |
|---|---|---|---|---|
| McMurray 2014 | RCT, n=8399 | ✅ PMID 25176015 | **INCLUDE** | PARADIGM-HF |
| Tsutsui 2021 | RCT, n=225 | ✅ PMID 33731544 | **INCLUDE** | PARALLEL-HF |
| Velazquez 2019 | RCT, n=881 | ✅ PMID 30415601 | exclude OUTCOME | PIONEER-HF — on re-examination list |
| Desai 2019 | RCT, n=464 | ✅ PMID 31475296 | exclude OUTCOME | EVALUATE-HF — on re-examination list |
| Piepoli 2021 | RCT, n=619 | ✅ PMID 33314487 | exclude OUTCOME | OUTSTEP-HF — on re-examination list |
| Halle 2021 | RCT, n=201 | ✅ PMID 33992607 | exclude OUTCOME | on re-examination list |
| Khandwalla 2020 | RCT, n=140 | ✅ PMID 32978755 | exclude OUTCOME | AWAKE-HF — on re-examination list |
| **Bano 2021** | RCT, n=364 | ✅ PMID 34395116 | was **undetermined** | **now resolved → exclude OUTCOME** (see `05_ADJUDICATION_LOG.md` Conflict 2) |
| **Santos 2021** | RCT, n=52 | ⚠️ probably NCT03190304 (n=52, exercise tolerance, S/V vs enalapril) — the *publication* is not identifiable in our PubMed set | — | **unmatched publication** |
| **Zhao 2022** | RCT, n=97 | ❌ no match found | — | **candidate miss** |
| Bhat 2022 | prospective cohort, n=200 | ❌ no match found | — | would fail randomisation; not a threat to the included set |
| Zhang 2024 | prospective cohort, n=123 | ❌ no match found | — | would fail randomisation; not a threat to the included set |

### Direction 1 — in theirs, absent from ours

> ## ⚠ CORRECTION, 2026-08-12 — the claim below this line was wrong
>
> The original pass-1 text said Zhao 2022 and Santos 2021 "cannot be matched to any record in our corpus" and concluded: *"This is the registered backward-citation step doing what it is for: it found records that neither registered database string returned."*
>
> **That was an error in my diff, and the conclusion drawn from it was an over-claim.** Both studies were in the corpus. I failed to match them because I matched their table rows to our PMIDs from author surnames and sample sizes rather than resolving the reference list. Resolving references [16] and [19] at source gives:
>
> - **Santos 2021 [16]** = Dos Santos MR, et al. *Am Heart J.* 2021;239:1–10 — **PMID 33992607**, in our corpus, excluded OUTCOME. I had mislabelled this row "Halle 2021".
> - **Zhao 2022 [19]** = Zhao Y, Tian LG, Zhang LX, et al. *Pulm Circ.* 2022;12 — **PMID 35874853**, in our corpus, excluded OUTCOME.
> - **Halle 2021 [22]** = ACTIVITY-HF — **PMID 34591356**, in our corpus, excluded OUTCOME.
>
> The original table rows are left standing below with strikethrough rather than rewritten. The lesson is the same one as Conflict 1: I matched from surface features instead of resolving identifiers, which is the "identifiers by lookup, never from recall" rule broken again, this time in the diff rather than in the screen.

**Corrected finding: pass 1 identified ZERO randomised studies missing from our corpus.** All eight randomised studies in the synthesis's table are present in our 423 records.

Two entries are absent from our corpus, and both are non-randomised:

- **Bhat 2022 [23]** — Bhat TS, et al. *Indian Heart J.* 2022;74:178–181, "a prospective observational study"
- **Zhang 2024 [24]** — Zhang Q, et al. *Altern Ther Health Med.* 2024;30:250–256, prospective cohort

Both would fail the randomisation condition of protocol §3, so neither threatens the included set. Their absence is nonetheless diagnostic of the PubMed string: the fourth block requires `randomized controlled trial[pt] OR randomised OR randomized OR trial` in title/abstract, and a self-described observational study may contain none of those. The registered string is, by construction, a randomised-trial filter — correct for this review, and worth noting for any future review reusing it that expects to see cohorts.

**So pass 1 did not find a missing trial. It found an error in my own matching, and it confirmed the corpus.** Both are worth having; only one of them is what I claimed.

### Direction 2 — in ours, absent from theirs

Recorded as differences to explain:

- **PARACHUTE-HF** (n=922) — absent from their table. Plausibly a date-of-search artefact; the JAMA primary publication is dated 2026 Jan 6. On our adjudicated set this is an *included* trial, so its absence from theirs is a substantive difference in the two reviews' included sets, not a coding difference.
- **ANSWER-HF** (n=190) — absent from their table. Same likely explanation.
- **PANORAMA-HF** (n=375) — absent, consistent with our population exclusion.
- Their table also treats prospective cohorts as includable, which our protocol §3 does not. That is a design-eligibility difference, not an error on either side, and it explains two of their twelve rows.

---

## Remaining registered sources — still not run

| Source | Status |
|---|---|
| 44 further flagged syntheses (`synthesis_candidate=Y` in `02_CORPUS_AND_SCREENING.tsv`) | **not read.** Next by priority: PMID 37554618 (PMC10405977), 39970741 (PMC11883387), 33257469 (PMC7705560), 38764991 (PMC11097924). PMID 41923142 — the Chagas-specific synthesis, and the most likely to matter now that PARACHUTE-HF is in — has **no PMC record** and was not retrievable. Named as blocked. |
| FDA statistical review, Entresto (application 207620) | **not consulted.** One attempt made and abandoned — see below. |
| EMA EPAR, Entresto | **not consulted.** |

### The FDA attempt, and why I stopped it

I tried to reach the Drugs@FDA review package by typing a URL for application 207620 **from recall**. It returned 404 (`Page Not Found`). I stopped rather than trying further guesses.

Stopping was the right call and worth recording: the protocol's own rule is *identifiers by lookup, never from recall*, and constructing a document URL from memory is that same error wearing different clothes. Two or three more guesses might well have landed on the file, and the result would have been a source I could not honestly say I had located rather than reconstructed. The correct route is a lookup through the Drugs@FDA search interface, which has not been run.

**Trigger condition.** Protocol §4 admits the regulatory documents "where a cell cannot be established from those" other sources. For PARADIGM-HF and PARALLEL-HF the cells are established and the trigger is not met. For **ANSWER-HF** it now arguably is — its JACC full text is paywalled — but the Entresto review package predates that trial and will not contain it, so it is the wrong source for that gap. The real remedy for ANSWER-HF is access to the JACC article.

Two databases plus one synthesis is still not the registered search.
