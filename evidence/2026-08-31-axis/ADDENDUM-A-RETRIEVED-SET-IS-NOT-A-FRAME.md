# ADDENDUM to the pre-registration. The original stands unedited.

`PRE-REGISTRATION-OA-FRAME-AND-CONDITION-VOCAB.md` is **not modified**. Editing a
pre-registration after seeing data is the one thing it exists to prevent, so what was
learned goes here and the original claim stays where it was written.

Recorded 2026-08-31, after three construction probes and before any OA topic was scored.

    REF.git      8e825e9e6
    REF.rule     604ed6957a1adf17     still FROZEN
    REF.source   Europe PMC REST, free, no key

---

## 1 ⭐ THE MEASUREMENT THAT SURVIVES INTACT: A.4.1 IS CONFIRMED, AND MORE STRONGLY THAN PREDICTED

For every drug on the pre-specified demand list, open-access systematic reviews exist.

| drug | any record | + systematic review / meta-analysis | + OPEN_ACCESS:Y |
|---|---|---|---|
| etripamil | 74 | 3 | **3** |
| riociguat | 2,993 | 88 | **60** |
| selexipag | 1,447 | 51 | **32** |
| sotatercept | 1,034 | 17 | **10** |
| mavacamten | 1,424 | 35 | **18** |
| evolocumab | 4,915 | 216 | **126** |

Against 0 of 1,186 in CDSR for every one of them.

⇒ **The coverage gap is COCHRANE-SPECIFIC, not literature-wide.** That is the sentence the
seven `INTERVENTION_MISMATCH` / `NO_CANDIDATE_RETRIEVED` states were pointing at, now
measured rather than inferred.

⚠️ **And I named `sotatercept` and `etripamil` as the two I would bet against first. Both
have OA systematic reviews.** The prediction missed optimistic on the pessimistic side —
sixteenth miss, first in that direction.

---

## 2 ⛔ THE CONSTRUCTION FAILURE: A MeSH-SCOPED OPEN-ACCESS FRAME CANNOT BE BUILT HERE

Three scope definitions were tried. The scope was to be an **external taxonomy declared
once** — the MeSH tree C14 children — precisely so I was not hand-picking terms to fit the
sample.

| scope | frame size | etripamil | riociguat | sotatercept | mavacamten | evolocumab |
|---|---|---|---|---|---|---|
| MeSH C14 children | **2** | 0 | 0 | 0 | 0 | 0 |
| C14 + `KW:cardiovascular/cardiology` | 3,514 | 0 | 2 | 0 | 2 | 41 |
| no scope | **131,862** | 3 | 60 | 10 | 18 | 126 |

**A MeSH scope captures none of the demand list.** Europe PMC's MeSH indexing does not
explode the parent term and is sparse on open-access records; `MESH:"Cardiovascular Diseases"
AND sotatercept` returns **0** while `sotatercept` alone returns 1,034.

⇒ Had I built the frame on the scope I intended, **every one of the seven would have failed
for a frame-construction reason and the output would have read as a literature finding.**
That is the artefact this project keeps re-meeting: a number that is true of the data
collected, read as true of the world.

---

## 3 ⭐⭐ THE STRUCTURAL POINT, AND IT IS THE REAL FINDING OF THIS ADDENDUM

**CDSR is enumerable. The open-access literature is not.** 1,216 rows against 131,862 OA
systematic reviews — and 131,862 is itself a lower bound on a population with no boundary.

So the open-access comparator cannot be a *slab* that is walked. It must be **RETRIEVED PER
TOPIC BY A FIXED PROCEDURE.** That still satisfies Mahmood's test — *"would this apply to
the next topic without being redone?"* — because a uniform procedure applied per topic is
repeatable; what is forbidden is a query hand-authored per topic, and none is.

⛔ **BUT A RETRIEVED SET IS NOT A FRAME, AND THE DIFFERENCE IS NOT COSMETIC.**

The two-axis matcher's power comes from the frame being an **enumerated population that does
not depend on the query**. That is what makes `axis_intervention == 0` mean *"the population
holds no review of this drug"* rather than *"my query found none"*.

Retrieve by the intervention, and **the intervention axis becomes the retrieval itself** —
scoring it is circular. Concretely, two of the seven states become **structurally
unreachable** in the OA configuration:

    INTERVENTION_MISMATCH   requires axis_I == 0 AND axis_C > 0. Impossible: the condition
                            axis is scored over the RETRIEVED set, so axis_C == 0 whenever
                            axis_I == 0.
    PAIR_ABSENT             requires both axes live and disjoint. Impossible: the condition
                            hits are a SUBSET of the retrieved rows, so `both == axis_C`.

**Still reachable, and still meaningful:** `MATCHED`, `AMBIGUOUS`, `CONDITION_MISMATCH`
(retrieval returned rows, none matches the condition), `NO_CANDIDATE_RETRIEVED` (retrieval
returned nothing), `REFUSED_NO_TERMS`.

⭐ **These two dead clauses are DECLARED, not left looking live.** A run that printed
`INTERVENTION_MISMATCH 0` in this configuration would be reporting a numerator that was
fixed before a record was read — the exact defect the detector control exists to catch, and
the one a laptop sweep passed its artefact control while committing earlier tonight.

## 3.1 What the OA run therefore measures — stated, so it cannot be conflated

> *Given that a drug's open-access systematic-review literature exists, does any of it match
> the topic's CONDITION and survive verification?*

That is a **different question** from the CDSR run's, and a good answer to it is not a
better answer to the old one. ⛔ **No OA number may be compared to a CDSR number**, for two
independent reasons now:

1. **A.3, already committed:** verification material differs — a Cochrane objectives
   statement is one or two sentences, an abstract is ~250 words. Substituting one for the
   other changes what `MATCHED` means without changing a line of the rule.
2. **This addendum:** the intervention axis is a retrieval, not a measurement.

---

## 4 WHAT DOES NOT CHANGE

* **The rule stays frozen.** `rekey_rule.py`, `axis_states.py`, `axis_match.classify` are
  untouched. The OA lane calls the same `classify()`.
* **The demand list stays frozen.** The same seven, chosen by the matcher before this
  document existed. No topic added, none dropped.
* **All twenty are carried**, the thirteen as a control group.
* **`frame_contract.py` is not modified.** Its `CD\d{6}` key check is correct for what it
  gates. The OA lane gets its **own** strict contract; two strict contracts is right, one
  loose contract that covers both is not.
* **Predictions A.4.2–A.4.6 stand and will be scored**, with the two unreachable states
  excluded from scoring and the exclusion named.
