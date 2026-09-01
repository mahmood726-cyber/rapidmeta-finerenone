# The delegated judge is not stable enough to move the headline. **[MEASURED]**

    REF.run1   0d30230b8 : oa_judgements_delegated.json, rubric WITHOUT the clause
    REF.run2   working tree : same 129 pairs, rubric WITH the restricted-population clause
    REF.judge  codex.cmd (GPT-5), 16 slices, both known-answer controls OK in every slice
    REF.pre    PREDICTION-RUBRIC-V2.md, written before run 2

The only difference between the runs is **one added clause that can only REFUSE**. Same 129
pairs, same order, same controls, same gate.

---

# 1 THE MEASUREMENT

    pairs judged in BOTH runs : 129 of 129

    COUNTERPART before clause : 35
    COUNTERPART after clause  :  8
      kept      C -> C        :  4
      flipped   C -> NOT      : 31    <- the clause SHOULD cause these
      flipped   NOT -> C      :  4    ⛔ A STRICTER RUBRIC CANNOT CAUSE THESE

    label changes on IDENTICAL evidence : 35 of 129 = 27%

⛔⛔ **Four acceptances APPEARED under a strictly stricter rule.** The clause added text that
only disqualifies; it removed no permission. A judge applying the rubric as a rule cannot
accept something under the stricter version that it refused under the looser one. So those
four are not rule application — they are **noise**.

    apixaban-af-review  PMC11049767   "…on COGNITIVE FUNCTION in patients with AF"
    warfarin-af         PMC11049767   same record, same flip
    dabigatran-stroke   PMC12596288   "ARGATROBAN as an adjunct to antiplatelet therapy"
    olmesartan-htn      PMC5765479    "Olmesartan-based MONOTHERAPY vs COMBINATION therapy"

⚠️ Note what they are: a cognitive-outcome study, **a review of a different drug entirely**,
and a strategy comparison — three of the four are things the clause makes *more* clearly
refusable, and one names argatroban where the topic is dabigatran.

---

# 2 ⛔ WHY THE HEADLINE DOES NOT MOVE

Run 2 reports `5 of 7 topics gain`. **Four of those five rest ENTIRELY on the four impossible
acceptances above.** Removing them:

| topic | sole surviving basis | verdict |
|---|---|---|
| dabigatran-af | PMC13133535 *"Direct oral anticoagulants for stroke prevention in patients with atrial fibrillation: a network meta-analysis"* — kept C→C, and I accept it independently | **gains** |
| apixaban-af-review | only PMC11049767, an impossible acceptance | does not |
| warfarin-af | only PMC11049767, an impossible acceptance | does not |
| dabigatran-stroke | only PMC12596288, an impossible acceptance, wrong drug | does not |
| olmesartan-htn | only PMC5765479, an impossible acceptance | does not |

⇒ **1 of 7 topics gains on evidence that survives both runs.** ⭐ **The measured position
stays 10 of 20, 17 distinct reviews** — I am not banking even the one, because a single
kept acceptance out of two runs is a thin thread and the instability is the headline.

⭐⭐ **AND THE BINARY HEADLINE HID THE INSTABILITY.** `topics with >=1 counterpart` read
`5 of 7` in BOTH runs while 27% of the underlying labels changed and the surviving pair set
was almost disjoint. A per-topic "any" metric is insensitive to judge noise, **which makes
it look more robust than the evidence under it is**. That is the same shape as a green
aggregate hiding a dead branch, one level up.

---

# 3 THE PREDICTION, SCORED

| prediction | result | |
|---|---|---|
| COUNTERPART drops to 4–12 | **8** | **HIT** |
| ≥25 of the 35 flip to NOT | **31** | **HIT** |
| both controls still pass | yes, all 16 slices | **HIT** |
| topics gaining: 3 of 7 | **5 reported, 1 defensible** | **MISS**, and the instability is why |
| resulting position 13 of 20 | **10 of 20, unchanged** | **MISS** |

⚠️ I also predicted the failure mode as **over-refusal induced by my own clause** — "if
COUNTERPART lands below 4, that is a defect in the clause". It landed at 8, so the clause
is not over-refusing. **The defect is in a different place than the one I guarded.**

---

# 4 WHAT THIS SAYS, AND WHAT IT DOES NOT

**[MEASURED]** Two independent reliability figures on the same judge tonight:

    27%    of labels change when the rubric is tightened in a way that can only refuse
    ~6.5%  of labels flip on a straight repeat with NO rubric change (2 of 31 pairs,
           collected accidentally from the filename race)

**[INFERRED]** A single call to a single judge is not a measurement of a pair. This is not a
claim that the model is poor at the task — the 31 correct C→NOT flips show it applies a
transmitted clause well, and it passed both known-answer controls in all 32 slice-runs
across both runs. It is a claim about **one call being one sample**.

**[INFERRED]** The fix is not a better prompt. It is **replication**: the same pair judged
n times, and a label taken only where the calls agree. That is a design change to the funnel
and it is not made here, because making it after seeing these numbers and reporting the
result in the same breath is the shape this report exists to avoid.

⛔ **What this does NOT license:** concluding that the open-access counterparts are not
there. `apixaban-af-review` has **103 verified pairs and 25 examined**; `warfarin-af` has
**102 and 25**. Those remain **LOWER BOUNDS**, not zeros. The judge's instability means the
25 were not reliably judged — not that the remaining 78 are empty.
