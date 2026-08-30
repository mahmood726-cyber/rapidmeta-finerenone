# A flag on a linked document says nothing about the document you need

Written 2026-08-30, from a retraction. Three defects in one night, all the same shape.

## The rule

**An availability flag attached to a document that is LINKED to an identifier says nothing
about the availability of the document that PLAYS A PARTICULAR ROLE for that identifier.**

Concretely: "is there an open-access paper citing NCT01507831?" and "is the primary report
of NCT01507831 open access?" are different questions with different answers, and the first
is nearly always YES while the second is often NO.

## What happened

I reported **"56 of 56 blocked trials have reachable full text"** and had to withdraw it.
The query behind that number resolved an NCT to the first open-access Europe PMC hit. What
that actually measured was *"some paper citing this NCT is open access"*, which is true for
almost every registered trial and selects **the wrong paper almost every time**.

Reading the titles is what exposed it:

| trial | what the selector picked | what it is |
|---|---|---|
| NCT01453608 | "Iron Dysregulation and Vascular Diseases: A Contemporary Review" | a review |
| NCT01968954 | "Population PK/PD modeling of LDL-C" | a modelling paper |
| NCT01507831 | "Which is the optimal choice in lipid-lowering therapy" | a review |
| NCT00509106 | "Treatment outcomes of secondary bacteraemia" | a secondary analysis |

⚠️ **AND THE OBVIOUS FIX DID NOT WORK.** Filtering on `pubTypeList` for
`Randomized Controlled Trial` still selected sub-studies, because **a trial's genetics
sub-study, PK analysis and subgroup paper all carry the RCT type tag.**

> **A TYPE TAG IS NOT A ROLE.** Selecting "the trial report" requires the document's role
> in relation to the trial, and no field in the index encodes that.

## Why the correct answer was hidden

For the large trials where we are blocked, the primary report is **paywalled** and the
open-access papers are the satellites. Verified rather than assumed:

* **SCORED / sotagliflozin** — NEJM primary `OA=N`, Lancet D&E `OA=N`; the only open paper
  is a CJASN kidney-outcomes secondary.
* **ODYSSEY / alirocumab** — NEJM primary `OA=N`; the open papers are PK analyses, a
  Japanese subgroup, and a diabetes-incidence secondary.

So the flag was not merely uninformative — it was **anti-correlated** with what we needed.
The more prominent the trial, the more likely its primary report is closed and its
satellites open.

## The family this belongs to

Third instance of one shape in a single run:

1. **A name match is a filter, not an identity.**
2. **Open access is a licence, not a retrieval status.**
3. **A type tag is not a role.**

All three substitute a cheap attribute for the expensive question, and all three fail
silently in the flattering direction. The detection habit that caught this one is the only
one that has ever worked here: **read the titles, do not trust the flags.**

## What replaced it, and it is worth more

The measurement that matters is not "can we get a paper" but **"which source answers the
domain we cannot rate"**. Measured with one protocol across three source classes:

| source | D1 concealment | D2 analysis population | D3 missing data |
|---|---|---|---|
| registry record (what we used) | NO | NO | NO |
| journal publication (n=2) | NO | NO | YES 2/2 |
| **FDA Statistical Review (n=1)** | NO | **YES** | **YES** |

The FDA review is the only source so far that answers **D2**, quoting its own estimand
section: *"The ITT estimand uses all data, regardless of treatment adherence."*

⚠️ **D1 IS UNANSWERED BY ALL THREE.** Allocation concealment is in none of them. Only the
Statistical Review was tested; the Medical Review and the protocol/SAP were not, and that
is where D1 would be if it is anywhere.

⚠️ **AND THE n's ARE SMALL AND STATED.** Two journal papers, both tigecycline; one FDA
review. These numbers say which source to test next, not what the answer is.

## Coverage of the FDA source class, with the kinds enumerated

Nine drugs behind the blocked topics:

* **7 have a review document** — finerenone, empagliflozin, ceftaroline, bempedoic acid,
  sotagliflozin, cabotegravir, tafamidis, plus alirocumab already fetched.
* **1 genuinely has none** — **bococizumab was discontinued in development and never
  approved**, so no FDA review exists. A real boundary of this source class, not a miss.
* **1 is a defect in my own lookup** — `apixaban` resolved to `ANDA209810`, a **generic**
  application with zero reviews, because `openfda.generic_name` returns whichever
  application sorts first and generics carry no review. The innovator NDA was not
  consulted. ⚠️ *This is the same rule as above arriving a fourth time: an application
  number matched by drug name is not the application whose review you want.*

Never report that class as "8 of 9 available". The kinds are: **7 available · 1 absent by
fact · 1 absent by my lookup being wrong.**

## The same rule again, one level down: SEARCH FOR THE THING, NOT THE TERM

Probing the FDA Medical Review for D1, a keyword scan returned:

* `allocation conceal` — **0 hits**
* `IVRS | IWRS | interactive voice/web response` — **2 hits**

⚠️ **A scan for the RoB 2 PHRASE would have reported D1 unanswerable, while the document
describes the MECHANISM.** A central randomisation service *is* allocation concealment;
regulatory reviewers write "IVRS", not "allocation was concealed". Sequentially numbered
identical containers and central telephone randomisation are the same case.

> **An instrument that searches for the vocabulary of the question rather than the
> substance of the answer produces a confident NO about the world when the true finding is
> about the instrument.**

This is the fourth face of the same defect, and it is the one that would have been hardest
to notice, because a 0-hit result reads as a clean negative finding rather than as a
broken probe. It is the sibling of the `h[ae]moglobin` regex that silently missed every
British spelling: the query encoded one wording of an open vocabulary.

**So the assessor prompt names the mechanisms explicitly and tells the reader to judge the
mechanism rather than the term.** Where a check must span an open vocabulary, hand the
judgement to something that can read, and say in the prompt that the phrase may never
appear.
