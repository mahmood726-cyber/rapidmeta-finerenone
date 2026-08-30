# RUN SHEET — Embase calibration, `agyw-hiv-prep-review`

**This is a CALIBRATION INSTRUMENT, not a search strategy.** Embase does not enter the
method. It is run once to measure what the free-source search already found. See
`EMBASE-CALIBRATION-PROTOCOL-2026-08-30.md` for why.

Question: *Does a dapivirine vaginal ring reduce HIV-1 seroconversion compared with a
placebo vaginal ring in women?*
Our search date: **2026-08-18** · Our included set: **2 trials** — ASPIRE / MTN-020
(NCT01539226), The Ring Study / IPM 027 (NCT01617096).

---

## ⚠️ ONE THING TO WATCH ON LINE 1, AND PLEASE TELL ME WHAT IT DOES

Emtree is licensed; I have no access and **have not assumed** that `dapivirine/` is an
Emtree preferred term. The strategy is built so the free-text lines carry it if the
explosion does not resolve.

**When you paste line 1, Ovid shows what it maps to.**
* Maps to a dapivirine heading → **keep it**.
* Maps to nothing, or to something broader like an antiretroviral class → **delete line 1**
  and change line 6 to `or/2-5`. Nothing else changes.

Either way, **tell me what it mapped to.** That is information I cannot get from here, and
it is the single point where a MEDLINE-strategy-relabelled-as-Embase would silently narrow
the search — MeSH has only a *Supplementary Concept* for dapivirine, Emtree almost
certainly has a full drug term, and that asymmetry is the whole reason the two blocks are
written separately.

---

## THE STRATEGY — Ovid Embase (1974 to 2026 Aug 27)

Paste line by line. Ovid numbers them as shown.

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
12    (HIV or "human immunodeficiency virus").ti,ab,kw.
13    (pre-exposure adj2 prophylaxis).ti,ab,kw.
14    PrEP.ti,ab,kw.
15    or/11-14
16    6 and 15
17    6 and 10
18    16 or 17
19    limit 18 to human
```

**Explosion:** applied on lines 1, 7, 11 (`exp`), so narrower Emtree terms come in.
**Truncation:** `$` (Ovid unlimited truncation). **Adjacency:** `adj3` / `adj2`.
**Free-text fields:** `.ti,ab,kw.` — title, abstract, Embase keyword field.

*(I dropped the separate `exp human immunodeficiency virus prophylaxis/` line I had
earlier. I am not confident it is an Emtree term, lines 13–14 cover the concept in free
text, and a line that fails to map adds nothing but a chance to mis-transcribe.)*

---

## THE TWO ANSWERS YOU ASKED FOR, GIVEN STRAIGHT

### RCT filter: **NONE. Do not apply one.**

Not a hedge — for a calibration it would be an error. The denominator is *"trials Embase
names that a blinded screen judges eligible."* A methodological filter decides part of that
question before the screen does, so the denominator would become "eligible trials **that
the filter also catches**", and our recovery figure would be measured against a target the
filter had already trimmed in our favour. It would also lose conference abstracts, which
are the main thing Embase adds over MEDLINE and therefore the main place an Embase-only
trial could hide. **Screening a few hundred records by hand is cheap; a biased denominator
is not recoverable.**

### Date limit: **apply it in Ovid's Limits panel, not as a strategy line — and tell me which limit you used.**

I will not hand you a syntax line I cannot verify. In Ovid the useful restriction is an
**entry/record date**, not publication year (`yr=`), and the exact field differs between
Ovid MEDLINE and Ovid Embase. So:

1. Run to **line 19** and **record that count** — this is the unrestricted total.
2. Then **Limits → Additional Limits**, set the date restriction to **on or before
   2026-08-18**, run it, and **record that count too**.
3. **Tell me which limit field you used** (its label in the panel).

⭐ **And export the UNRESTRICTED set.** Each RIS record carries its own dates, so I can
apply the 2026-08-18 cut exactly on my side, and we get both numbers — like-for-like
against our search, and what has appeared since — from one run. The Ovid limit is the
cross-check on my filtering, not the other way round.

---

## EXPORT — so it is one pass

1. Run to **line 19**. Select **all** results.
2. **Export → Format: `RIS`.** Not EndNote, not Word, not plain text.
3. **Fields: `Complete Reference`.** ⭐ This is the one that matters. It carries the
   abstract, the Emtree indexing, the accession number, and any trial-registry numbers in
   the record. The default `Citation` export drops all of that, and the registry numbers
   are how I match Embase records to trials.
4. **Include Abstract: YES.** Screening without abstracts is not screening.
5. Filename: **`embase_dapivirine_2026-08-30.ris`**

⭐ **AND SAVE THE SEARCH HISTORY.** Ovid: **Search History → expand → Print / Email / Save**,
**with result counts**, as `ovid_history_dapivirine_2026-08-30.txt`.
⚠️ This is what makes the run reproducible and it is the part everyone forgets. It also
gives the per-line counts, which tell us which concept block did the work — and if line 1
returned zero, that alone answers the Emtree question.

**Nothing else. No PDFs, no full text.** Running a search and exporting records is the
ordinary sanctioned use of the subscription; bulk full-text retrieval is not, and is not
being asked for.

---

## THE PREDICTION — logged before the run, and it stays at the top of the report either way

| quantity | prediction |
|---|---|
| Embase records at line 19 | **300–700** |
| trials judged ELIGIBLE (**M**) | **2** |
| of those already held by free sources (**N**) | **2** |
| **recovery N/M** | **2/2 = 100%** |
| additional eligible trials Embase adds | **0** |
| Embase records absent from MEDLINE | substantial — conference abstracts |

**A single Embase-only eligible trial falsifies this outright.** If that happens, the judges
were right on substance and not merely on the proxy, and it leads the report.

If it holds, the sentence we can then write is:
> *"This search uses only sources freely available worldwide. Measured against a
> subscription database, it recovered 2 of 2 eligible trials."*

---

## BROWSER DISCOVERY — the six queries, since you offered

For each, load the search page, issue the query, and report **the XHR the page calls**: URL,
method, request body/params, and the shape of the JSON that comes back. **Discovery only —
one query each.** Anything built afterwards respects each registry's robots policy, and
**CRiS stays refused** (`Disallow: /`).

Query term for all six: **`dapivirine`**

| registry | page to load |
|---|---|
| **DRKS** | `https://drks.de/search/en/trial/search?query=dapivirine` |
| **ANZCTR** | `https://www.anzctr.org.au/TrialSearch.aspx` — type `dapivirine`, Search |
| **EU-CTR** | `https://www.clinicaltrialsregister.eu/ctr-search/search?query=dapivirine` |
| **ChiCTR** | `https://www.chictr.org.cn/searchproj.html` — enter `dapivirine` |
| **jRCT** | `https://jrct.mhlw.go.jp/search?language=en&keyword=dapivirine` |
| **IRCT** | `https://www.irct.ir/search?query=dapivirine` |

⚠️ **What I need per registry, in order of usefulness:**
1. the request URL and method of the call that returns results;
2. how the search term is passed (query string? JSON body? form field name?);
3. whether the response is JSON or HTML, and the key/element holding the trial identifier;
4. **the result count the page displays** — because for any registry showing *zero*, that
   count converts my `INDETERMINATE` into a genuine `EMPTY`, which is a real answer and
   currently unearned.

⭐ Point 4 is worth as much as the endpoints. **1 of 18 determinate is the number I have to
publish today**, and every registry that turns out to genuinely hold nothing moves it
honestly rather than by assumption.
