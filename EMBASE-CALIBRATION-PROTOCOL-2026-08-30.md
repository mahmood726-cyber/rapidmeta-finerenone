# Embase as a MEASURING STICK, once — never as a source

**Supersedes `OVID-SEARCH-DAPIVIRINE-2026-08-30.md`, which is withdrawn.** That document
wrote general-purpose Embase strategies, and general-purpose Embase strategies are now
against scope.

## The scope rule that withdrew it

Mahmood, 2026-08-30: **"Embase is not available in Laos and Uganda. We can use an occasional
firewalled paper but want to avoid Embase if possible."**

⇒ **A METHOD THAT DEPENDS ON A SUBSCRIPTION CANNOT BE REPRODUCED BY THE READER IT IS FOR.**
The audience is a clinician with no full-text access. If the search requires Embase, our
reviews are not checkable by them — and *verifiable, not authoritative* is the axis this
project wins on, so the dependency would cost more than the coverage it buys.

**Standing rule: FREE-SOURCE-ONLY search.** An occasional firewalled paper for a specific
datum is permitted. A database as a dependency is not.

## What is left, and why it is stronger than the thing it replaces

Embase can be used **ONCE**, on a question already completed with free sources, to answer
one question:

> *Of everything Embase names as eligible for this question, how much did the free sources
> already find?*

Embase never enters the method. It is the ruler, not the material. What comes out is a
sentence nobody else can write:

> **"This search uses only sources freely available worldwide. Measured against a
> subscription database, it recovered N of M eligible trials."**

⭐ That converts *"we searched fewer databases"* — a proxy, and the thing that lost three
verdicts — into **a coverage fraction with a denominator**, which is falsifiable. A count of
databases cannot be wrong. A fraction can.

⚠️ **And if the number is poor, it is a finding about our free-source strategy, not a
defence of it.** The prediction below is logged before the run for exactly that reason.

---

## 1. Which completed question

**`agyw-hiv-prep-review` — dapivirine vaginal ring versus placebo ring, HIV-1
seroconversion in women.**

Chosen for four reasons, and the fourth is the one that matters:

1. It is **complete**: search executed, two trials included, protocol committed.
2. It is the **live comparison** — this is the question on which six blinded judges chose
   our page over Cochrane CD007961.pub3, and search breadth was the axis we lost.
3. It is **small enough to adjudicate exhaustively**. Every Embase hit can be screened by
   hand; there is no sampling step to argue about.
4. ⭐ **It is the case least likely to flatter us.** A drug–device question is where Embase
   is strongest: Emtree indexes drugs exhaustively where MeSH has only a Supplementary
   Concept for dapivirine, and Embase carries the conference abstracts that MEDLINE thins.
   If free sources hold up *here*, the result generalises downward. Picking a question
   where Embase is weak would prove nothing.

## 2. What the denominator is OF

⚠️ **This is the part that decides whether the number means anything, so it is fixed before
the run.**

**M — the denominator — is:** every trial that the Embase result set names, **which a
blinded screen judges ELIGIBLE for this review's question** — a randomised comparison of a
dapivirine vaginal ring against a placebo vaginal ring reporting HIV-1 seroconversion.

**N — the numerator — is:** how many of those M our free-source search already holds.

**It is NOT:**

* **not** the number of Embase *records* — Embase will return several hundred, most of them
  conference abstracts of trials we already have. Records are not trials.
* **not** the number of *registry identifiers* Embase mentions — that counts everything the
  discussion sections cite.
* **not** trials that are *ineligible* on population, comparator or design. HOPE and DREAM
  are open-label extensions with no placebo arm; REACH is a crossover against oral PrEP;
  MTN-023 and MTN-024 are phase 2a safety studies. If Embase surfaces those, they are
  **correctly excluded**, and counting them as misses would manufacture a failure.

⭐ **EVERY DIFFERENCE IS ATTRIBUTED BEFORE IT IS COUNTED** — search miss, eligibility
difference, or source boundary — and only the first measures recall. That rule is already
enforced in code: `scripts/search_coverage_fraction.py` **refuses to emit a recall figure**
while any difference is unattributed, and it is currently refusing on this very question
because two PACTR registrations cannot be attributed from a page that returns a 3,679-byte
JavaScript shell.

**The screen is blinded to provenance.** Whoever screens the Embase set must not know which
records we already hold, or the eligibility judgement becomes a judgement about our
performance.

## 3. The prediction, logged before the run

| quantity | prediction |
|---|---|
| Embase records returned | **300–700** |
| of those, trials judged ELIGIBLE (**M**) | **2** |
| of those, already held by free sources (**N**) | **2** |
| **recovery N/M** | **2/2 = 100%** |
| additional eligible trials Embase adds | **0** |
| Embase records absent from MEDLINE | **substantial** — conference abstracts |

**Reasoning, so this is falsifiable rather than a hedge.** Only two placebo-controlled
efficacy trials of the dapivirine ring were ever conducted. Both are large, both published
in the New England Journal of Medicine, both indexed in MEDLINE. Embase's advantage is drug
indexing, European sources and conference abstracts — which multiply *records about the
same two trials* rather than adding trials.

⚠️ **THE PREDICTION IS DELIBERATELY THE ONE THAT CAN EMBARRASS US.** Predicting 100% means
any Embase-only eligible trial falsifies it outright. If that happens, the judges were
right on substance and not merely on the proxy, and it goes in the report at the top rather
than in a limitation.

⭐ **And a null result is worth as much as a positive one here.** "Embase added nothing" is
the first direct evidence that a free-source search reaches what a subscription database
reaches for a question of this shape — which is precisely the claim the free-source scope
rule needs, and which nobody currently publishes.

## 4. What is run

One Ovid Embase search, on the strategy in the withdrawn document's section A — which
remains technically correct and is retained **only** as the calibration instrument. It is
not a search strategy for the review, and it must not be cited as one in any protocol.

Export: RIS, Complete Reference, abstracts on, plus the Ovid search history with per-line
counts. One run, one date, recorded with the search date of **2026-08-18** applied on the
export so the comparison is like-for-like.

## 5. What is published afterwards

The sentence, with its denominator, and the attribution table behind it. Plus the honest
companion finding, which is ours and unflattering:

> **Of the 18 primary registries in the WHO ICTRP network, our free registry search
> currently returns a determinate answer from 1.** Six answer HTTP 200 with results
> rendered in the browser, so what we hold is a shell and not an answer; one refuses all
> automated access by robots.txt; ten have no free query endpoint we have established.
> Measured 2026-08-30 by `scripts/registry_search.py`.

⚠️ **That number is reported beside the Embase result, not buried under it.** The
free-source scope rule is a commitment, and a commitment that only reports its wins is
marketing.
