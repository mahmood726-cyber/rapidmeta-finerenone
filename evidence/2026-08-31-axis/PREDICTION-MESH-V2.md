# Prediction for the MeSH condition axis, v2. Written before `condition_mesh_v2.py` ran.

    REF.rule    604ed6957a1adf17   ⛔ still FROZEN
    REF.frame   a0d44914a5ef99e3   1,186 CDSR cardiology reviews
    REF.lookup  mesh_lookup.py — [MeSH Terms]-bound, record-identity VERIFIED, [TN] broader

## What changed since v1, and it is not what v1's report blamed

`REPORT-CONDITION-MESH.md` §3.1 said the defect was the UNIT — words expanded instead of
phrases. **Measured since: the phrase queries fail too.**

    free-text esearch, phrase query               descriptor actually returned
    hypercholesterolemia                       -> Hyperlipoproteinemia Type III
    pulmonary arterial hypertension            -> Familial Primary Pulmonary Hypertension
    paroxysmal supraventricular tachycardia    -> Tachycardia, Ventricular

⇒ **The root cause is an UNVERIFIED RECORD, not a wrong unit.** `esearch db=mesh` is
relevance-ranked over every field; taking `idlist[0]` asks a confident authority a question
and never checks which question it answered. v1's §3.1 stands in the record and this
supersedes it.

Three fixes, each measured before this file was written:
1. Bind to `[MeSH Terms]` — fixes 5 of 8 probe terms outright.
2. **Verify the record's own NAME against the query; refuse on mismatch.** This is the
   semantic criterion §6 of the v1 report said was missing. `paroxysmal supraventricular
   tachycardia` still returns `Tachycardia, Ventricular` even when bound — and is now
   REFUSED rather than expanded.
3. Broader terms via the tree, field `[TN]`. `Hypercholesterolemia` → **`Hyperlipidemias`**.
   ⚠️ `[MeSH Tree Number]` — the obvious spelling — returns count=0 **silently**; it was a
   dead branch found only by giving each candidate field its own count.

## The v2 axis, stated so the comparison is not smuggled

    incumbent   the span's WORDS, need = min(2, n)          -- loose on words
    v2          PHRASE match on {span} ∪ verified entry terms ∪ verified broader terms

⚠️ **This is not uniformly looser.** It is STRICTER on the phrase (the whole span must
appear, not 2 of 3 words) and adds synonyms. It trades word-level looseness for phrase-level
strictness, so it can lose rows as well as gain them. **R1 is therefore genuinely at risk**,
which is the point of running it alongside.

## THE PREDICTION — low, and naming the risk rather than the hope

| | predicted |
|---|---|
| topics that trip **R1** (a MATCHED topic becomes unmatched) | **0 or 1** — and `bosentan-pah` is the one I would bet on, because its 19 rows come from 2-of-3 of `pulmonary/arterial/hypertension` and a phrase match needs all three |
| net change in judged COUNTERPARTS across all 20 | **0** |
| `pitavastatin` rescued from `CONDITION_MISMATCH` | **state changes, counterpart count stays 0** — `Hyperlipidemias` normalises to `hyperlipidemia`, which matches exactly **1** of 1,186 rows, and I do not expect that row to also carry a statin |
| `dabigatran-stroke` promiscuity (198 rows) | **unchanged** — its span is the single word `stroke`, so phrase match *is* word match. v2 cannot help a one-word condition, and that is a real limit |
| concepts REFUSED for record mismatch | **at least 1** (`paroxysmal supraventricular tachycardia`) |
| **verdict** | **not adopted**, published alongside |

⭐ **The honest expected outcome is that v2 is CORRECT where v1 was WRONG and still does not
move the number.** A fix that removes a false expansion without adding a true one is worth
shipping as a correction and worth nothing as a result, and I expect exactly that.

## Which way I expect to miss

Sixteen misses: fifteen optimistic, then two pessimistic in one run after I over-corrected.
**So I am not applying a direction this time.** The specific thing I am least sure of is
whether phrase-matching costs `bosentan-pah` its counterpart — if it does, R1 trips, v2 is
refused on the spot, and that is a clean result rather than a disappointment.
