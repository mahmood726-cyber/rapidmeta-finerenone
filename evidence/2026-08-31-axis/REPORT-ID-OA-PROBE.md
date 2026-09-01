# The open-access lane on infectious disease: **23 of 24 MATCHED, and it is an artefact.**

    REF.rule    604ed6957a1adf17   ⛔ FROZEN
    REF.source  Europe PMC cursorMark, free, no key
    REF.verify  abstract   ⛔ not comparable to any CDSR number
    REF.pre     prediction recorded in the header of `scripts/rekey20/oa_id_probe.py`
                BEFORE the run

---

# 1 THE RAW RESULT **[MEASURED]**

    topics with a LIVE retrieval : 24 / 24        all exhausted, zero lower bounds
    fetched                      : 82,489
    protocols excluded           : 755
    VERIFIED PAIRS               : 1,894          unjudged
    MATCHED                      : 23 / 24

**⛔ Do not read that as "the lane reaches infectious disease."** It does not.

---

# 2 ⚠️ THE IMPLAUSIBILITY WAS THE TELL

Seven unrelated drugs returned **6,902–7,010** hits each; eight more returned
**3,366–3,558**. Rifapentine, tigecycline, eravacycline, fidaxomicin, plazomicin and
tecovirimat do not have near-identical literatures.

**[MEASURED]** the intervention terms actually searched:

    rifapentine-tb        ['antibiotic', 'rifamycin derivative', 'rifapentine']
    plazomicin-…          ['antibiotic', 'micromonospora strain', 'plazomicin']
    remdesivir-covid      ['antiviral', 'polymerase inhibitor', 'remdesivir', …]

**[MEASURED]** drug alone vs class alone, same filter:

| topic | drug only | class only | as shipped | class share |
|---|---|---|---|---|
| rifapentine | 79 | `antibiotic` **6,955** | 7,010 | **99%** |
| plazomicin | 13 | `antibiotic` **6,955** | 6,957 | **100%** |
| remdesivir | 559 | `antiviral` **3,365** | 3,501 | **96%** |
| **delamanid** | 51 | `acid inhibitor` 7 | 58 | **12%** |

⇒ **The bare word `antibiotic` retrieved 6,955 systematic reviews while `plazomicin`
retrieved 13.** The drug contributed nothing; the class word *was* the retrieval.

⭐ **`delamanid` is the control and it discriminates:** where the class phrase is narrow, the
drug dominates. So this is not "every topic is class-dominated" — it is specifically the
topics whose USAN class is a broad single word, which in infectious disease is most of them.

---

# 3 ⛔ THREE TERM-GENERATION DEFECTS, VISIBLE IN THE TERM LISTS

**[MEASURED]** from `oa_id_probe.json`:

    'not benzoxazinone derivative'   agyw-hiv-prep-review, doravirine-hiv
    'undefined group'                anidulafungin ×2
    'micromonospora strain'          fidaxomicin ×2, plazomicin
    'acid inhibitor'                 delamanid  (from "mycolic acid inhibitor")

1. ⛔ **A NEGATION BECAME A POSITIVE SEARCH TERM.** `class_phrases` split a definition
   containing a negated clause and emitted `not benzoxazinone derivative` as a term to match.
   This is the *negated-count* defect this project has recorded before — *"Not Randomized
   1,807"* extracted as an N — arriving on the term-generation side.
2. **A source placeholder was promoted to a term.** `undefined group` is the vocabulary
   saying it has no class; the rule searched for the words.
3. **A genus of origin was treated as a therapeutic class.** *Micromonospora* is the
   bacterium fidaxomicin and plazomicin are derived FROM, not what they treat. And splitting
   "mycolic acid inhibitor" yields `acid inhibitor`, which means something else entirely.

⇒ These are **new items for a pre-registered amendment**, not fixes. The rule stays frozen.
They are recorded here so `PROPOSED-RULE-AMENDMENT-3.md` — already committed and awaiting a
decision — is not edited after submission.

---

# 4 THE PREDICTION, SCORED — two misses, both HIGH

| prediction | result | |
|---|---|---|
| ≥20 of 24 with a live retrieval | **24 of 24** | **HIT** |
| 14–20 reaching MATCHED | **23** | **MISS, high** |
| 200–900 verified pairs | **1,894** | **MISS, high** |
| the CONDITION axis is the binding constraint | **it is not — the intervention axis collapsed first** | **MISS** |

## 4.1 ⭐ The miss that matters is the fourth one, and it corrects my whole framing

I have measured term specificity on **three condition axes** tonight and concluded the defect
was a property of the matcher. That conclusion is right and **my scoping of it was wrong**:

> **[INFERRED] Specificity is AXIS-AGNOSTIC, and on infectious disease the INTERVENTION axis
> is far worse than the condition axis.**

`disease` at df 17.5% of a 1,186-row frame was the worst condition term I found all night.
`antibiotic` returns **6,955 of the open-access systematic-review literature** and is an
intervention term for six topics. I spent the night looking at one axis because that is where
the first failure appeared.

⚠️ This is my third consecutive prediction miss of the same shape — **modelling one term of a
two-term system.** AACT: registry conditions are wider, treated as one-way. ID rule
carry-over: titles worse *and* drug step better, assumed the first dominated. Here: condition
axis promiscuous *and* intervention axis worse, assumed the condition axis would bind.

---

# 5 WHAT IS AND IS NOT CLAIMED

**Claimed:** the open-access lane retrieves for every drug-keyed ID topic and exhausts.
Retrieval is not the ID constraint.

⛔ **NOT claimed:** that any ID topic has a counterpart. Nothing was judged — deliberately,
because judging is the stage measured as unstable and a new specialty needs its own
pre-registration. **`MATCHED` is not a counterpart**, and here 23 of 24 of them rest on a
class word doing 96–100% of the retrieval.

⛔ **NOT claimed:** that the 1,894 verified pairs mean anything. At 96–100% class domination
they are overwhelmingly pairs between a topic and a review of a *different drug in the same
enormous class*.

⇒ **[INFERRED] The ID candidate pool for a full-standard page is NOT expanded by this run.**
The pool remains the 10 cardiology topics with judged counterparts.
