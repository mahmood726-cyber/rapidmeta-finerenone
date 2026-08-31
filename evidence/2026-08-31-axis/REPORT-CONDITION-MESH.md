# Part B: the MeSH condition axis, run alongside. **NOT ADOPTED.**

    REF.frame   a0d44914a5ef99e3   1,186 CDSR cardiology reviews
    REF.rule    604ed6957a1adf17   ⛔ FROZEN — this adds a COLUMN, not a rule
    REF.mesh    NLM E-utilities, free, no key.  19 lookups, **19 OK, 0 failures**
    REF.gates   R1–R4, written in PRE-REGISTRATION §B.3 before the first query

---

# 1 THE VERDICT

**No pre-registered criterion tripped. The expansion is still refused.**

    R1  no MATCHED topic became unmatched          PASSED
    R2  CD004434 CD006681 CD014808 CD015003 all survive   PASSED
    R3  precision must not fall below 43%          NOT COMPUTABLE without adjudicating
                                                   the new pairs (15 vs 14 verified)
    R4  no condition axis above 25% of the frame   PASSED (max stays 17%, dabigatran-stroke)

⇒ **Published alongside, pending R3. Not adopted. The incumbent literal axis stands.**

---

# 2 ⛔ THE FINDING R1–R4 COULD NOT SEE, AND IT IS THE REASON FOR THE REFUSAL

**Every criterion I pre-registered was quantitative. The defect is semantic.**

    etripamil-psvt    supraventricular  ->  ventricular tachycardia
    olmesartan-htn    hypertension      ->  primary pulmonary hypertension
    bosentan-pah      arterial          ->  primary pulmonary hypertension
    colchicine-cvd    prevention        ->  control                        47 rows

* **`supraventricular → ventricular tachycardia` is a different arrhythmia** — close to the
  clinical opposite of the one the topic is about.
* **`hypertension → primary pulmonary hypertension` on `olmesartan-htn`** would push a
  systemic-hypertension topic *further toward the PAH reviews that already produced its two
  adjudicated false positives.* The expansion's live effect is to strengthen the corpus's
  known error.
* **`prevention → control` matches 47 rows** and is pure noise injection.

⭐ **Nothing in R1–R4 fires on any of that, and I would have reported a clean pass.** A
pre-registered gate can only check what it was told to check; writing the criteria in
advance protects against moving the goalposts, and protects against nothing else.

⇒ **This is exactly what "alongside, never instead" is for.** Had MeSH replaced the
incumbent, olmesartan's false positives would have grown and every number would have
looked fine.

---

# 3 WHY IT MISFIRES — two mechanisms, both measured

## 3.1 The unit is wrong: a condition is a PHRASE, and I expanded its WORDS

The incumbent's concepts are single words — `pulmonary`, `arterial`, `hypertension`. Sending
each to MeSH queries the authority with something that **is not a concept**. `arterial` is
not a disease; `supraventricular` is not a disease. MeSH answers anyway, about whichever
record it best matches:

    supraventricular  ->  53 entry terms, headed by
                          "Arrhythmogenic Right Ventricular Cardiomyopathy"

⚠️ **This is the seed defect again, on the other axis.** `SGLT2` → the protein,
`Intravenous` → the route, `supraventricular` → a ventricular cardiomyopathy. **A wrong seed,
confidently expanded by an authority, returning a plausible-looking list.** The intervention
axis was fixed by seeding from the object's own record; the condition axis needs the same
move — expand the **span**, not its words.

## 3.2 The direction is wrong for the case it was meant to rescue

**`pitavastatin` did not move: 0 → 0.** My prediction B.4 said it *would* be rescued,
because *"MeSH entry terms for Hypercholesterolemia include Hyperlipidemia"*. **They do
not — and the reason is structural, not a lookup failure.**

    hypercholesterolemia  ->  status OK, 96 entry terms, ALL familial/genetic variants:
                              "Apolipoprotein B-100, Familial Defective"
                              "Autosomal Dominant Hypercholesterolemia"
                              ... and `hyperlipidemia` is not among them.

**MeSH entry terms are SYNONYMS. `Hyperlipidemia` is a BROADER term — a tree parent, not a
synonym.** So no amount of entry-term expansion reaches it.

⇒ **A DEAD term needs a BROADER term; a PROMISCUOUS term needs a NARROWER one. Synonym
expansion supplies neither.** It is the wrong instrument for both halves of the defect, and
that is why 1,190 of 1,211 added synonyms match nothing:

    synonyms added   1,211
    live on frame       21   (1.7%)
    dead             1,190   (98.3%)

---

# 4 WHAT CHANGED AT ALL

| topic | condition axis literal → MeSH | verified |
|---|---|---|
| colchicine-cvd-review | 51 (4%) → **56 (5%)** | 2 → 2 |
| enoxaparin-vte | 37 (3%) → **38 (3%)** | 4 → **5** |
| etripamil-psvt | 3 → **4** | 0 → 0 |
| *the other 15 expandable topics* | unchanged | unchanged |

**One new verified pair, on `enoxaparin-vte`, and it is unjudged.** Under R3 it is as likely
to be a precision loss as a gain — the incumbent already refused 3 of that topic's 4
verified pairs. **A rise in verified pairs with no rise in judged counterparts is a
precision loss wearing the costume of a recall gain**, which is exactly the trap B.5 named
in advance.

---

# 5 THE PREDICTION, SCORED

| B.4 prediction | result | |
|---|---|---|
| the two `REFUSED_NO_TERMS` topics are not helped — no span to expand | both unchanged | **HIT** |
| MeSH trips R4 on at least one topic | **nothing tripped**, max 17% | **MISS** |
| net change in judged counterparts across all 20 = **0** | 0 judged change (1 unjudged pair added) | **HIT** |
| `pitavastatin` is rescued from CONDITION_MISMATCH | **0 → 0, not rescued** | **MISS** |

⭐ **The pitavastatin miss is the useful one.** I predicted a rescue from a mechanism I had
not checked — that entry terms include broader concepts. They do not. **I asserted a
property of an external authority instead of querying it**, which is the same class of error
as asserting `record_kind` in the OA lane instead of reading it. Two instances tonight of
*assumed instead of read*.

---

# 6 WHAT THE NEXT BUILD IS

1. **Expand the SPAN, not the words.** `condition_span` is already on every topic —
   `"pulmonary arterial hypertension"` — and it is a real MeSH concept where its individual
   words are not.
2. **Use the TREE, not the entry terms.** A dead term needs its parent
   (`Hypercholesterolemia` → `Hyperlipidemias`); a promiscuous term needs its children.
   Direction should be chosen by the measured failure, which the two-axis matcher already
   names per topic: `CONDITION_MISMATCH` → broaden, an axis over ~15% of the frame → narrow.
3. **Add a SEMANTIC criterion to the pre-registration.** R1–R4 could not see
   `supraventricular → ventricular tachycardia`. A cheap mechanical one: refuse a synonym
   that is not a superstring or substring of its concept **and** whose MeSH record differs
   from the concept's own — it would have caught all four bad expansions in §2.
