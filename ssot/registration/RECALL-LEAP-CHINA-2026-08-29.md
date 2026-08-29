# Recall test: would our search have found LEAP China?

**Answer: the search found it. The reading threw it away.**

That is not the result I expected, and it is worse for us than a bad query would have been.

---

## The test

`LEAP China` — a randomised lefamulin-vs-moxifloxacin CABP trial (ECR ≈ 50/83 vs 27/42),
supplied by an external reader as ground truth. Our page holds two trials and was generated
in August 2026.

**The query was run exactly as the pipeline sent it** — not an improved one:

> `Lefamulin moxifloxacin community-acquired bacterial`

Improving it first would have answered *"could a better search find it"* and quietly turned
a failed recall test into a passed one.

## What each leg returned

| leg | result |
|---|---|
| **PubMed** | ⭐ **FOUND.** Returned **PMID 40964629** (2025), whose abstract reads: *"the LEAP 1 and LEAP 2 trials, along with the bridging LEAP China trial."* Also returned **PMID 33964925** (2021 pooled). |
| **Europe PMC** | ⭐ **FOUND.** Returned the same 2025 pooled analysis. |
| **ClinicalTrials.gov** | **MISSED** — returned exactly the two trials already held, 0 new. |
| **ICTRP leg (ISRCTN)** | **EMPTY.** |
| guideline bodies | not applicable to trial identification |

## Two distinct failures, and they need different fixes

### 1. A structural registry gap — real, and not fixable by rewording

**LEAP China is not on ClinicalTrials.gov at all.** Querying `lefamulin` returns 8 studies;
the only one with a China site is a post-market surveillance study (`NCT07697885`), not LEAP
China. It is presumably registered in **ChiCTR**.

⚠️ **Our "ICTRP leg" is served by ISRCTN, and ISRCTN does not aggregate ChiCTR.** So **no
registry leg in the current design can reach a Chinese-registered trial.** That is a genuine
gap in a live search strategy, measured against a known answer — and it is exactly the class
of thing that only a ground-truth test can reveal. WHO ICTRP proper does aggregate ChiCTR;
calling ISRCTN "an ICTRP route" understates this, and the search records already name ISRCTN
honestly for that reason.

### 2. The reading failure, which is ours and is worse

**The literature legs returned the paper that names LEAP China.** The pipeline recorded
`pubmed EXECUTED n=22` and stopped. The object recorded **"19 read, 1 appraised."**

> **The search did not fail. The reading did.**

A count of 19 "read" is precisely what makes that invisible: it reads as diligence and it
means retrieval.

## This is now mechanical and corpus-wide

New gate: `scripts/lint_read_is_not_appraised.py` — it refuses when a topic reports reading
more records than it appraised without saying so. Run over all 155 topics:

```
directories under ssot/                             292
topics with an object                               155
   no published-comparison denominator              132   not examined
   denominator present, counts not integers          11   not examined
comparable                                           12
   of which read exceeds appraised                  12   <- ALL of them
   and the gap was declared                          0
```

⚠️ **Corrected while writing this.** I first wrote "12 of 23 topics have the gap". The
denominator is not 23: **11 of those 23 carry counts that are not integers and could not be
compared at all.** Every single topic that *could* be compared has the gap — 12 of 12, not
12 of 23. The check reports on **23 of 155 topics (15%)**, and the other 132 were not clean,
they were **not looked at**.

| topic | read | appraised |
|---|---|---|
| finerenone-cv | **252** | 1 |
| cangrelor-pci-review | 99 | 1 |
| rotavirus-vaccine-africa-review | 70 | 1 |
| incretin-hfpef-review | 51 | 1 |
| cab-prep-hiv-review | 46 | 1 |
| ceftaroline-auto-full-review | 42 | 1 |
| nirsevimab-infant-rsv-review | 39 | 1 |
| malaria-vaccines | 28 | 2 |
| gepotidacin-urinary-tract | 25 | 1 |
| tigecycline-ciai | 22 | 1 |
| lefamulin-cabp | 19 | 1 |
| agyw-hiv-prep-review | 8 | **0** |

⭐ **689 records were retrieved and never appraised.** The declaration is now written into
**11** of these search records (`READ_IS_NOT_APPRAISED`, with the arithmetic). `gepotidacin`
is left untouched per the standing order that it belongs to another lane.

## The recall denominator, which is the point

**Two confirmed genuine misses, both found by external readers, both PICO-matched:**

```
EAGLE-J      confirmed genuine
LEAP China   confirmed genuine
```

Both are same-drug, same-comparator, same-indication, same-outcome — **not** the nirsevimab
shape where a broader meta-analysis manufactured false missing trials. Two is a small
denominator and it is the only ground truth we have. **It is worth more than any coverage
statistic in this repository, all of which measure our own reach.**

⚠️ **Neither was found by us.** Both arrived from outside. A recall measurement whose every
positive came from an external reader tells you nothing about the rate — only that the rate
is not zero.

## The honest qualifier, stated at its real size

Adding LEAP China moves the pooled result from **0.9884 to about 0.9875** and leaves
**I² = 0%**.

> **The omission does not overturn the number. It is a COMPLETENESS failure, not an
> arithmetic one.**

Overstating this would be as wrong as ignoring it. The review's estimate stands; its claim to
have found the evidence does not.

## The free validation — present, and not being used as one

The reviewer noted a published pooled analysis reporting **89.3% vs 90.5%, risk difference
−1.1 points**, matching our extracted counts. Retrieved and confirmed verbatim:

> **PMID 33964925**: *"Lefamulin (n = 646) was noninferior to moxifloxacin (n = 643) for ECR
> (89.3% vs 90.5%; difference −1.1%; 95% CI −4.4 to 2.2)"*

⭐ **This paper is already recorded on the topic** — it sits in `published_comparison.reviews`
and was already used for a different finding (that the experimental arms are not the same
intervention). So it is not missing. **What is missing is the use of it as an external
validation of our own extracted counts**, which is free, strengthens the review, and is
currently uncited as such.

## What this changes about how we test

Every coverage number this pipeline produces is a statement about its own reach. **This is
the first measurement against an answer established outside it**, and it found a structural
registry gap and a process failure that no amount of internal auditing had surfaced. More
ground truth is worth more than more coverage.
