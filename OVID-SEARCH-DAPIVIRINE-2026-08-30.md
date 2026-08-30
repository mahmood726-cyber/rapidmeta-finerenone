> # ⛔ WITHDRAWN 2026-08-30 — DO NOT RUN AS A SEARCH STRATEGY
>
> Mahmood ruled Embase out of the method the same day this was written:
> **"Embase is not available in Laos and Uganda."** A method that depends on a
> subscription cannot be reproduced by the reader it is for, and the audience is a
> clinician with no full-text access. **Free-source-only search is now a standing scope
> rule.**
>
> The strategies below are technically correct and are retained for ONE purpose: they are
> the instrument in **`EMBASE-CALIBRATION-PROTOCOL-2026-08-30.md`**, which uses Embase ONCE
> as a measuring stick against a question already completed with free sources. Embase never
> enters the method.
>
> ⚠️ **This file must not be cited as a search strategy in any protocol.** Read the
> calibration protocol instead.

# Ovid search strategies — dapivirine vaginal ring vs placebo ring

**For Mahmood to run in the Royal Free London NHS Trust Ovid session. Paste one block per
database. Do not translate one into the other — they are written separately on purpose.**

Review question: *Does a dapivirine vaginal ring reduce HIV-1 seroconversion compared with
a placebo vaginal ring in women?*
Our stated search date: **2026-08-18** (the date the seeded registrations were read).
Our current included set: **2 trials** — ASPIRE / MTN-020 (NCT01539226) and The Ring Study
/ IPM 027 (NCT01617096).

---

## ⚠️ READ THIS BEFORE RUNNING — three things that would otherwise silently cost recall

**1. DAPIVIRINE IS NOT A MeSH DESCRIPTOR.** Verified against the NLM MeSH browser on
2026-08-30: it is a **Supplementary Concept Record**, mapped to the descriptor
`Pyrimidines`, with pharmacologic action `Anti-HIV Agents`. So `exp Dapivirine/` **does not
exist in Ovid MEDLINE** and a strategy written that way returns nothing or errors. The
substance is reachable through the **substance-name field, `.nm.`**, which is what line 2
of the MEDLINE strategy uses. This is exactly the kind of thing a MEDLINE strategy
relabelled as an Embase one gets wrong.

**2. THE ENTRY TERMS MATTER FOR THE EARLY RECORD.** MeSH lists `TMC120-R147681`, `TMC-120`,
`TMC 120`, `R-147681`, `R 147681`. Early dapivirine literature — the phase 1/2 work and the
IPM development programme — uses the development codes, not the INN. A strategy without
them loses that end of the record.

**3. I CANNOT VERIFY EMTREE FROM HERE.** Emtree is licensed and I have no access, so I have
**not asserted** that `dapivirine/` is an Emtree preferred term — I have written the Embase
strategy so it does not depend on that being true. ⚠️ **When you paste line 1, Ovid will
show you what it maps to. If it maps to a dapivirine heading, keep the explosion; if it
does not, delete line 1 and the free-text lines still carry the search.** Please tell me
what the mapping shows either way — that is itself information I do not currently have.

---

## A. OVID EMBASE  (Embase 1974 to 2026 Aug 27)

Run these as numbered lines. Ovid will number them 1, 2, 3 … as shown.

```
1     exp dapivirine/
2     (dapivirine or dapavirine).ti,ab,kw.
3     ("TMC 120" or TMC120 or "TMC-120").ti,ab,kw.
4     ("R 147681" or R147681 or "R-147681").ti,ab,kw.
5     (DPV adj3 (ring or vaginal or intravaginal)).ti,ab,kw.
6     or/1-5
7     exp vaginal ring/
8     (vaginal adj3 ring$).ti,ab,kw.
9     (intravaginal adj3 (ring$ or device$)).ti,ab,kw.
10    or/7-9
11    exp human immunodeficiency virus infection/
12    exp human immunodeficiency virus prophylaxis/
13    (HIV or "human immunodeficiency virus").ti,ab,kw.
14    (pre-exposure adj2 prophylaxis).ti,ab,kw.
15    PrEP.ti,ab,kw.
16    or/11-15
17    6 and 16
18    6 and 10
19    17 or 18
20    limit 19 to human
```

**Subheadings: NONE are applied, deliberately.** Drug and disease subheadings in Emtree are
applied inconsistently by indexers, and restricting on `/dt`, `/pc` or `/ad` would trade
recall for precision on a set this small. The question is narrow enough that precision is
not the binding constraint — please do **not** add subheadings.

**Explosion is applied** on lines 1, 7, 11 and 12 (`exp`) so narrower Emtree terms are
included.

⚠️ **Do NOT apply an RCT filter.** The whole dapivirine-ring literature is small; a
methodological filter would lose conference abstracts and registry-linked records, which
are precisely what Embase adds over MEDLINE. Screening a few hundred records is cheap.

⚠️ **Do NOT apply a date limit in the strategy.** Send me the full set and I will restrict
to our search date of 2026-08-18 on the export, where the record's entry date is a field I
can filter exactly. That way we get both numbers — like-for-like against our search, and
what has appeared since — from one run, and I am not guessing at Ovid's entry-date field
syntax, which I cannot verify without access.

---

## B. OVID MEDLINE(R) ALL  (1946 to 2026 Aug 28)

**Note how different lines 1–5 are from the Embase block. This is the point.**

```
1     Pyrimidines/
2     dapivirine.nm.
3     (dapivirine or dapavirine).ti,ab,kf.
4     ("TMC 120" or TMC120 or "TMC-120").ti,ab,kf.
5     ("R 147681" or R147681 or "R-147681").ti,ab,kf.
6     (DPV adj3 (ring or vaginal or intravaginal)).ti,ab,kf.
7     or/2-6
8     exp Anti-HIV Agents/
9     1 and 8
10    7 or 9
11    Contraceptive Devices, Female/
12    Administration, Intravaginal/
13    (vaginal adj3 ring$).ti,ab,kf.
14    (intravaginal adj3 (ring$ or device$)).ti,ab,kf.
15    or/11-14
16    exp HIV Infections/
17    Pre-Exposure Prophylaxis/
18    (HIV or "human immunodeficiency virus").ti,ab,kf.
19    (pre-exposure adj2 prophylaxis or PrEP).ti,ab,kf.
20    or/16-19
21    10 and 20
22    10 and 15
23    21 or 22
24    limit 23 to humans
```

**Why line 1 + line 9 exist and are combined that way.** `Pyrimidines/` is the descriptor
dapivirine maps to, and on its own it is enormously broad — tens of thousands of records —
so it is **never used alone**. Line 9 intersects it with `exp Anti-HIV Agents/`, which is
the pharmacologic action MeSH assigns to dapivirine. That pair recovers records where the
indexer applied the descriptors but the free text never spells the drug name. Line 2
(`.nm.`) is the direct substance-name route and will do most of the work.

**Subheadings: NONE, for the same reason as Embase.** `HIV Infections/pc` would look
appealing and would lose records indexed only under the unsubheaded term.

**Explosion** on lines 8, 16.

---

## C. GLOBAL HEALTH

Run the **Embase block (A) verbatim** but delete line 1 (`exp dapivirine/`) and lines 7,
11, 12 — Global Health uses CABI headings, not Emtree, so the explosions will not resolve.
Lines 2–5, 8, 9, 13–15 are all free text and will run unchanged. This database is included
because the dapivirine trials were conducted in South Africa, Uganda, Malawi and Zimbabwe,
and Global Health indexes African public-health literature that MEDLINE thins out.

---

## D. EXPORT SETTINGS — so you click once

For **each** database separately (do not merge before export; I need to know which database
produced which record, or the coverage fraction cannot be attributed):

1. Run the final line (Embase **line 20**, MEDLINE **line 24**, Global Health equivalent).
2. Select **all** results.
3. **Export → Format: `RIS`**  ⭐ not EndNote, not Word, not plain text.
4. **Fields: `Complete Reference`** — this is the important one. It carries the abstract,
   the indexing terms, the accession number, and any trial-registry numbers in the record.
   The default "Citation" export drops all of that.
5. **Include: Abstract — YES.** Screening without abstracts is not screening.
6. Filename: `embase_dapivirine_2026-08-30.ris`, `medline_dapivirine_2026-08-30.ris`,
   `globalhealth_dapivirine_2026-08-30.ris`.

⭐ **AND EXPORT THE SEARCH HISTORY ITSELF.** In Ovid: **Search History → expand → Print /
Email / Save → include result counts.** Save it as
`ovid_search_history_dapivirine_2026-08-30.txt`. ⚠️ **This is the part that makes the search
reproducible and it is the part everyone forgets.** A result set without the history that
produced it is a pile of records; with it, it is a search anyone can re-run and check. It
also gives us the per-line counts, which tell us which concept block did the work.

---

## E. ⭐ MY PREDICTION, LOGGED BEFORE YOU RUN IT

**Additional trials ELIGIBLE for this review's question that Embase yields over our current
set of 2: I predict ZERO.**

Reasoning, so the prediction is falsifiable rather than a hedge:

* The question is narrow — dapivirine ring **versus placebo ring**, outcome HIV-1
  seroconversion. Only two such trials were ever run.
* Both are large, both published in the NEJM, both indexed in MEDLINE. Embase's advantage
  is drug indexing, European sources and **conference abstracts** — which will surface more
  *records* about the *same two trials*, not new trials.
* The other dapivirine-ring studies that exist are excluded on eligibility, not missed:
  HOPE/MTN-025 and DREAM/IPM-032 are open-label extensions with no placebo arm, REACH/
  MTN-034 is a crossover against oral PrEP, MTN-023 and MTN-024 are phase 2a safety.

**Secondary predictions, also falsifiable:**

| quantity | prediction |
|---|---|
| Embase records at line 20 | **300–700** |
| of which conference abstracts | a large minority, roughly **1 in 4** |
| distinct trial registry IDs mentioned | **5–12** |
| additional ELIGIBLE trials | **0** |
| records Embase has that MEDLINE does not | **substantial** — this is the real test |

⭐ **IF IT YIELDS ZERO ELIGIBLE TRIALS, THAT IS A RESULT AND NOT A DISAPPOINTMENT.** It is
the first direct evidence that our four-source search reaches what Embase reaches for a
question of this shape — and it is exactly the number needed for the coverage fraction that
answers the judges. Embase was the biggest hole in that denominator; measuring it as zero
closes the hole with evidence rather than argument.

⚠️ **AND IF IT YIELDS MORE THAN ZERO, I WILL REPORT THAT JUST AS LOUDLY**, because it would
mean our search misses eligible trials and the judges were right on the substance rather
than only on the proxy. That is the more valuable outcome of the two and I am not
predicting it away.

---

## F. WHAT I NEED BACK

The three `.ris` files and the search-history text file. Nothing else — **no PDFs and no
full text.** Running a search and exporting the records is the ordinary sanctioned use of
the subscription; bulk full-text retrieval is not, and is not being asked for.

Tell me what line 1 of the Embase block mapped to. I could not verify Emtree from here and
I would rather record what it actually did than assume.
