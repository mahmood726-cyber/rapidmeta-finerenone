# Prediction: paging out the truncated retrievals. Written before `oa_page_all.py` existed.

Every claim below is marked **[MEASURED]** with the command that produced it, or
**[INFERRED]** — because a report that does not mark which sentences are measured and which
are reasoned launders an inference into a finding. I did exactly that in
`REPORT-CONDITION-MESH` §3.1 and had to supersede it.

    REF.rule    604ed6957a1adf17   ⛔ FROZEN
    REF.source  Europe PMC REST, cursorMark pagination, free, no key
    REF.prior   evidence/2026-08-31-axis/oa_states_twenty.json  (cdf4855d1)

---

## 1 THE STARTING POSITION

**[MEASURED]** — `python scripts/rekey20/oa_retrieve.py`, output in `oa_states_twenty.json`:
15 of 20 topics were truncated at the 100-row cap; hitCount ranges 125 → 3,541; the 13
control topics contributed 90 verified rows from ~1,300 fetched and were **deliberately not
judged** because a window is not a population.

**[MEASURED]** — `python scripts/rekey20/oa_judge.py`: 10 of 20 topics carry a judged
counterpart (CDSR 5 + open-access 5), over 17 distinct reviews.

## 2 ⛔ THE CEILING IS 18, NOT 20 — AND THE BLOCKER IS NOT THE LITERATURE

**[MEASURED]** — `axis_states_twenty.json`: `apixaban-vte-prophylaxis` and
`evolocumab-ascvd-auto2` are `REFUSED_NO_TERMS`. Their titles carry **no condition
connective**, so `condition_span` is null and `condition_terms` is `[]`.

**[INFERRED]** — no amount of retrieval can match a topic that has nothing to match on. Under
the frozen rule those two are **structurally unreachable**, and the defect is in the
OBJECTS' titles, not in the search. ⛔ I will not author a condition span to reach a number;
that is precisely what pre-registration exists to prevent.

⇒ **[INFERRED] Ceiling: 18 of 20.** The eight topics that could still gain are
`apixaban-af-review`, `dabigatran-af`, `dabigatran-stroke`, `olmesartan-htn`,
`pitavastatin-auto-full-review`, `warfarin-af` (all truncated) plus
`evolocumab-dyslipidemia-review` and `evolocumab-mixed-…` (truncated at 100 of 125, so
little headroom).

## 3 THE PREDICTION

| | predicted | basis |
|---|---|---|
| topics gaining a counterpart from full paging | **2 to 4 of 8** | [INFERRED] |
| resulting position | **12 to 14 of 20** | [INFERRED] |
| topics still at zero after paging | **≥ 6**, including the 2 with no condition span | [INFERRED] |
| verified pairs across all 20, after paging | **600 to 1,500** (from 124) | [INFERRED] from ~7% of fetched rows verifying at the current cap |

⛔ **THE PREDICTION THAT MATTERS MOST IS THE COST ONE.** If verified pairs land anywhere in
that range, **hand adjudication of the funnel's last stage becomes infeasible** — 33 pairs
took careful work; ~1,000 will not be done by one lane in one night. ⇒ The route from 10
toward 18 is **bounded but not cheap**, and I expect to be reporting a judging bottleneck
rather than a retrieval one.

**[INFERRED]** I also expect precision to FALL below the current 13/33 = 39%: paging reaches
lower-relevance records, and Europe PMC orders by relevance, so the rows added are by
construction the weaker ones.

## 4 WHICH WAY I EXPECT TO MISS

Seventeen scored predictions tonight: fifteen optimistic, two pessimistic, one
"neither-but-incomplete". **I am not applying a direction.** The thing I am least sure of is
the verified-pair count, because the ~7% verification rate was measured on a
relevance-ordered *head* and I am extrapolating it to a *tail* — which is exactly the shape
of extrapolation that has failed all night. If the rate drops in the tail, the count lands
low and judging stays feasible; if it holds, it does not.
