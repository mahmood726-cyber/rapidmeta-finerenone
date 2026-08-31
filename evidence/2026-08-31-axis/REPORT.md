# Counterpart identification, scored on two axes. And the answer about twenty.

## REF — every number below is addressed to this and only this

    REF.git             8e825e9e6
    REF.rule            604ed6957a1adf17     rekey_rule.rule_fingerprint
    REF.frame           a0d44914a5ef99e3     sha256 over the SORTED SET of 1,216 cd_bases
    REF.frame_path      F:/claude-temp/pend/cdsr_frame_cardiology.jsonl   2,693,862 bytes
    REF.reviews_scanned 1,186                (30 protocols cannot be a counterpart)
    REF.twenty          cbb0ff1630820509     sha256 over the SORTED SET of 20 app_ids
    REF.matcher         axis_match v1
    REF.judgements      evidence/2026-08-31-rekey/corrected/judgements.json

Sets are hashed, never counts. Two runs that return fourteen rows each and disagree about
*which* fourteen are a difference no count can show.

---

# 1 ⛔ THE ANSWER FIRST: TWENTY IS NOT REACHABLE, AND HERE IS THE NUMBER

**Ceiling in this frame: 13 of 20. Standing today: 5. The shortfall of at least 7 is
ABSENCE, not tuning.**

| | topics | can a better matcher reach it? |
|---|---|---|
| judged COUNTERPART today | **5** | already there |
| MATCHED but judged not a counterpart | 1 | no — adjudication killed it, correctly |
| AMBIGUOUS — retrieved, verification could not settle | 4 | **maybe**, needs a verification source |
| CONDITION_MISMATCH — drug present, condition vocabulary dead | 1 | **maybe**, needs a condition authority |
| REFUSED_NO_TERMS — the condition was never searched at all | 2 | **maybe**, needs a condition that is not the title |
| INTERVENTION_MISMATCH — the frame holds the disease and not the drug | **5** | ⛔ **no** |
| NO_CANDIDATE_RETRIEVED — the frame holds neither | **2** | ⛔ **no** |

For those last 7 the intervention axis matches **0 of 1,186 reviews** with the drug name
*and* every class term the rule yields. `mavacamten` 0 · `etripamil` 0 · `riociguat` 0 ·
`selexipag` 0 · `sotatercept` 0 · `evolocumab` 0. **No threshold reaches a review that does
not exist.** These are drugs approved after Cochrane last covered their areas.

⇒ **Twenty is reached by a SECOND FRAME or not at all**, and the states say precisely which
one: a frame containing systematic reviews of post-2018 cardiology drugs — the open-access
non-Cochrane SR literature. Not by a looser rule. Loosening here would convert
`INTERVENTION_MISMATCH` into false positives, and section 4 shows the matcher is already
running at 43% precision.

**Told at eleven rather than at nineteen, as asked: the honest number is 5, the ceiling is
13, and 7 of the twenty are unreachable in this frame no matter what we build.**

---

# 2 THE MATCHER — a named state per topic, never a silent drop

`scripts/rekey20/axis_states.py` · `axis_match.py`. The two limbs are scored
**independently against the whole frame** before they are scored together, so the report can
say *which one* killed each pair.

    REFUSED_NO_TERMS        an axis has an EMPTY term list — NOTHING WAS SEARCHED
    MATCHED                 a row carries both axes and re-verifies in objectives alone
    AMBIGUOUS               a row carries both axes; none verifies
    PAIR_ABSENT             both axes LIVE, no single row carries both
    INTERVENTION_MISMATCH   condition axis live, intervention axis matches nothing
    CONDITION_MISMATCH      intervention axis live, condition axis matches nothing
    NO_CANDIDATE_RETRIEVED  neither axis matches anything

⛔ `NO_CANDIDATE_RETRIEVED` and `INTERVENTION_MISMATCH` are never merged, and plant **A6**
asserts it: from the same plant, making the condition axis live must yield
`INTERVENTION_MISMATCH` and making the intervention axis live must yield
`CONDITION_MISMATCH`. Both siblings pass.

⭐ **`PAIR_ABSENT` is a sixth state the brief's five do not hold, and it is ADDED rather
than folded.** When one axis matches 4 rows and the other 22 and no row carries both,
neither axis failed — the pair did. Calling that `INTERVENTION_MISMATCH` would assert the
frame lacks a drug the frame plainly has, which is the same collapse under another name.
It is observed 0 times on the twenty and is proven live by plant A3.

## The twenty

| app_id | state | axis I | axis C | both | ver | counterpart |
|---|---|---|---|---|---|---|
| apixaban-af-review | AMBIGUOUS | 15 | 22 | 2 | 0 | 0 |
| apixaban-vte-prophylaxis | **REFUSED_NO_TERMS** | – | – | – | – | 0 |
| bosentan-pah | MATCHED | 9 | 19 | 3 | 2 | 1 |
| bosentan-pah-children | MATCHED | 9 | 14 | 3 | 2 | 1 |
| bosentan-pah-monotherapy | MATCHED | 9 | 19 | 3 | 2 | 1 |
| colchicine-cvd-review | MATCHED | 5 | 51 | 3 | 2 | 2 |
| dabigatran-af | AMBIGUOUS | 5 | 22 | 2 | 0 | 0 |
| dabigatran-stroke | AMBIGUOUS | 5 | **198** | 2 | 0 | 0 |
| enoxaparin-vte | MATCHED | 33 | 37 | 11 | 4 | 1 |
| etripamil-psvt | INTERVENTION_MISMATCH | **0** | 3 | 0 | 0 | 0 |
| evolocumab-ascvd-auto2 | **REFUSED_NO_TERMS** | – | – | – | – | 0 |
| evolocumab-dyslipidemia-review | NO_CANDIDATE_RETRIEVED | **0** | **0** | 0 | 0 | 0 |
| evolocumab-mixed-dyslipidemia… | NO_CANDIDATE_RETRIEVED | **0** | **0** | 0 | 0 | 0 |
| mavacamten-hcm-review | INTERVENTION_MISMATCH | **0** | 1 | 0 | 0 | 0 |
| olmesartan-htn | MATCHED | 9 | **95** | 3 | 2 | **0** |
| pitavastatin-auto-full-review | CONDITION_MISMATCH | 5 | **0** | 0 | 0 | 0 |
| riociguat-pah | INTERVENTION_MISMATCH | **0** | 19 | 0 | 0 | 0 |
| selexipag-pah | INTERVENTION_MISMATCH | **0** | 19 | 0 | 0 | 0 |
| sotatercept-pah | INTERVENTION_MISMATCH | **0** | 19 | 0 | 0 | 0 |
| warfarin-af | AMBIGUOUS | 5 | 22 | 1 | 0 | 0 |

Tally: MATCHED 6 · AMBIGUOUS 4 · INTERVENTION_MISMATCH 5 · NO_CANDIDATE_RETRIEVED 2 ·
REFUSED_NO_TERMS 2 · CONDITION_MISMATCH 1 · PAIR_ABSENT 0. **Sums to 20.**

---

# 3 ⭐⭐ THE SECOND AXIS HAS NO VOCABULARY LAYER, AND THAT IS THE PORTABLE FINDING

The intervention axis goes through an authority: ChEMBL resolves the molecule, USAN gives
the class. **The condition axis is literal title words, stemmed, with `need = min(2, n)`.**
Nothing expands it. The same defect therefore fails in both directions:

    dabigatran-stroke   condition = ['stroke']              matches 198 of 1,186   PROMISCUOUS
    olmesartan-htn      condition = ['hypertension']        matches  95 of 1,186   PROMISCUOUS
    pitavastatin        condition = ['hypercholesterolemia'] matches   0 of 1,186   DEAD

**Pitavastatin is the clean case Mahmood named, and the matcher now shows its mechanism
rather than its outcome.** `pitavastatin` matches 1 row and `enzyme inhibitor` 4, so the
drug is in the frame; `hypercholesterolemia` matches **zero**, because Cochrane writes
*hyperlipidaemia*, *lipid lowering*, *primary prevention*. One word, dead, kills the topic —
and with `need = min(2, 1) = 1` there is no second word to carry it.

⇒ **The fix is the same one the intervention axis already had: attach a free authority.**
MeSH entry terms are free and are already called by `search_topic.mesh_entry_terms`. That is
the next build, and it is not shipped here because it would go out unmeasured.

---

# 4 ⛔ WHERE THE MATCHES ACTUALLY COME FROM — and it is not the drug name

`olmesartan-htn` and `bosentan-pah` return **the identical verified set**:
`{CD004434, CD015824}`, sha `00b545cac4d09e98`. One is judged COUNTERPART, the other
NOT_COUNTERPART. Same two rows, opposite verdicts. The per-term liveness says why:

    bosentan-pah    bosentan 0 · endothelin receptor antagonist 4 · receptor antagonist 9
    olmesartan-htn  olmesartan 0 · angiotensin ii receptor antagonist 0 · receptor antagonist 9

**Neither drug name appears anywhere in 1,186 reviews.** The corpus's single most productive
counterpart — CD004434, covering three bosentan topics — was found *entirely by a two-word
class fragment*, and the same fragment `receptor antagonist` manufactured olmesartan's two
false positives. The true positive and the false positive share their mechanism.

    candidates 33  ->  verified 14  ->  judged COUNTERPART 6      precision 6/14 = 43%
    5 topics carry a counterpart; 4 INDEPENDENT reviews underlie them
    CD004434 · CD006681 · CD014808 · CD015003
    ⚠️ three bosentan topics are one question under three names and share ONE review.
       Per-topic counts over this corpus carry that inflation.

⇒ **This is why loosening the rule to reach twenty is the wrong move.** At 43% precision the
adjudication step, not the retrieval step, is what makes a counterpart real — and
adjudication is the expensive one.

---

# 5 ⭐ THE VACUOUS SET — zeros that were never measurements

`all([])` is `True`. Here it wears numbers: with an empty condition list the natural test
`len(hits) >= min(2, len(cond))` is `0 >= 0`, **true for every row**. An unguarded empty
condition list does not return zero — **it returns the entire frame, 1,186 of 1,186**. Plant
A8b asserts that size rather than merely asserting the guard exists.

    topics with an EMPTY condition term list  : 2   apixaban-vte-prophylaxis, evolocumab-ascvd-auto2
    topics with an EMPTY intervention list    : 0
    topics where the rule REFUSED a class     : 7   colchicine(F4) evolocumab-ascvd(F5)
                                                    evolocumab-dyslipidemia(F5) evolocumab-mixed(F5)
                                                    selexipag(F4) sotatercept(F5) warfarin(F6)

**The old scan printed `B 0/0` for each of those 7 and it was not a class that was searched
and missed — the class was never searched at all.** Seven of twenty arm-B zeros were
vacuous and indistinguishable from measurements.

---

# 6 CONTROLS — both kinds, because they answer different questions

`plant_axis_match.py` **29/29** · `plant_seed_guards.py` **17/17**.

* **ARTEFACT control (A10)** — pinned frame bytes, row count and base-set sha256. It proves
  *which* bytes were read. It is pinned to a file outside the repo, so if it fails the first
  question is *did the world change?*, not *did the code break?*
* **DETECTOR control (A9)** — all 7 states observed as positives on the live frame. A clause
  that can never fire has a numerator fixed before a row is read.

⭐ **A sweep can pass the first perfectly and be measuring nothing.** Every state is planted
separately, and every plant has a **clean sibling** that differs in exactly the deciding
thing and must land elsewhere. Without the siblings, "flag everything" would pass every
plant here.

---

# 7 THE SEED, BEFORE AND AFTER, FOR ALL TWENTY — and a new defect the fix itself introduced

The seed was fixed and scored on four topics before tonight. Extended to all twenty:

    seeds CHANGED  8 / 20        seeds UNCHANGED 12 / 20
    provenance:  11 LAST RESORT (title's first word) · 6 arm labels · 3 executed query

⚠️ **11 of 20 are still on the LAST RESORT path — and the seed is nevertheless correct on
all 11, for a reason that invalidates the twenty as a test of the fix.** The twenty were
selected by rule R3 as topics whose *intervention span holds exactly one drug*. Selecting
for that property selects for titles whose first word is a drug. **The twenty cannot expose
the seed defect, because they were drawn for the property that hides it.** The four scored
comparison topics remain the only evidence, and they pass as a regression control:
`arni-hfref`, `sotagliflozin-hf`, `iv-iron-hf`, `sglt2-hf` all unmoved by tonight's guards.

## ⛔ The fix moved the seed from the title to the arms, and the arms can be wrong

`evolocumab-mixed-dyslipidemia-auto-full-review`, NCT02662569:

    role=treatment   'Atorvastatin (Q2W)'
    role=control     'Evolocumab QM + Atorvastatin'

The roles are **inverted** — the review is of evolocumab. The arms path therefore seeded the
**comparator** as the intervention, and the block sent to PubMed was
`Atorvastatin OR Q2W OR Evolocumab`:

    seed_old 'Evolocumab'   1,558 PubMed records
    seed_new (as shipped)  15,370      <- 9.9x, driven by the comparator and a dosing token

⚠️ **15,370 is a plausible size for the statin literature.** The same failure shape as
`16,917` for SGLT2 — a wrong number that survives every check we own because it looks right.

**Two guards added, each planted with a clean sibling:**

1. **A schedule token is a pattern, not a word list.** `Q2W`, `QM`, `BID`, `PRN` are matched
   as a shape; only a term that is *entirely* schedule tokens is dropped. Sibling: a
   non-schedule parenthetical (`Metoprolol (extended release)`) survives, and `LCZ696` is
   untouched — without that sibling, "drop every parenthetical" would pass too.
   **Effect: 15,370 → 14,500.**
2. **`arm_role_conflicts` + `seed_role_state`** — a term cannot be this review's
   intervention and its comparator at once. Terms are **named, never repaired**: an add-on
   design legitimately puts a drug in both arms.

       SEED_ROLE_NOT_APPLICABLE  14      SEED_ROLE_OK  4      SEED_LEADS_WITH_CONFLICT  2

   ⛔ `evolocumab-mixed` — leads with `Atorvastatin`; `atorvastatin` *and* `evolocumab` are
   both in both roles across its two trials.
   ⛔ `apixaban-af-review` — NCT04218266 is asundexian **versus apixaban** while NCT02942407
   is apixaban versus warfarin. Apixaban is genuinely the intervention in one trial and the
   comparator in another. **A true positive, and a pooling-direction hazard worth a look.**

## Two of my own assertions were wrong and the detector was right

Both were caught by **live-corpus** plants, not by fixtures, and both are kept as arms:

* I asserted `evolocumab-mixed` would conflict on `atorvastatin` alone. It returns
  `['atorvastatin', 'evolocumab']` — across two trials evolocumab is treatment in one and
  control in the other. The detector saw more than I did.
* I asserted `colchicine-cvd-review` would be clean. It returned
  `['colchicine','stent','synergy']`. `colchicine placebo` is a control label naming the
  drug — excludable. `SYNERGY Stent` **really is in both arms** — not excludable, and still
  reported.
* ⛔ **My first exclusion was itself wrong**: dropping the whole control label whenever it
  contained a placebo marker would have thrown away `SYNERGY Stent` from
  `Placebo +/- SYNERGY Stent`. The marker binds to its **conjunct**, not the label. Only
  running it on the corpus showed that; the fixtures passed.

---

# 8 THE PREDICTION, SCORED — 18 of 20 exact, and the miss is the direction named in advance

`PREDICTION-BEFORE-THE-AXIS-MATCHER.md`, committed before `axis_match.py` existed.

| predicted | observed | |
|---|---|---|
| MATCHED 6 | **6** | HIT |
| topics with a judged counterpart 5 | **5** | HIT |
| AMBIGUOUS 4 | **4** | HIT |
| CONDITION_MISMATCH 1 (pitavastatin, by name) | **1** | HIT |
| REFUSED_NO_TERMS 2 (both by name) | **2** | HIT |
| PAIR_ABSENT 0 | **0** | HIT |
| olmesartan is the matcher's own false positive | 2 pairs, both NOT_COUNTERPART | HIT |
| vacuous: 2 condition-empty, 7 class-refused | **2 and 7** | HIT |
| INTERVENTION_MISMATCH 7 | **5** | ✗ |
| NO_CANDIDATE_RETRIEVED 0 | **2** | ✗ |

**Per-topic: 18 of 20 exact.** The two misses are the same two topics
(`evolocumab-dyslipidemia-review`, `evolocumab-mixed`) and they moved in exactly the
direction written down in advance:

> *"I expect to have OVER-estimated `INTERVENTION_MISMATCH` and UNDER-estimated
> `NO_CANDIDATE_RETRIEVED` … those topics fall to `NO_CANDIDATE_RETRIEVED` — a strictly
> WORSE diagnosis."*

`dyslipidemia` matches 0 of 1,186. I assumed a common word was live because it looked
common. **Optimistic again — the fifteenth consecutive optimistic miss, and the first one
whose direction was named correctly in advance.**

⚠️ **One further correction to the prediction, in the flattering direction.** It said "3
independent reviews"; the observed figure is **4**. `CD014808` and `CD015003` are two
distinct colchicine reviews and I collapsed them into one while writing. The number in
section 4 is 4.

---

# 9 WHAT I DID NOT DO

* **Did not reopen the frozen join to reach twenty.** The ceiling of 13 is reported as a
  ceiling, not converted into a target.
* **Did not attach a condition authority.** MeSH expansion for the condition axis is the
  named next build; shipping it tonight would put it out unmeasured, and section 3 would
  then be a claim instead of a measurement.
* **Did not repair `NCT02662569`'s inverted arm roles, or `apixaban-af-review`'s
  direction.** Both are named. Editing trial data on the strength of a mechanical flag is a
  repair a machine cannot justify.
* **Did not commit.** `F:/rapidmeta-finerenone/.git/worktrees/rapidmeta-ssot-shell/
  index.lock` has been held by another session for 52 minutes and is 1.6 MB. This is a
  shared worktree and removing another session's lock can corrupt its index, so the commands
  are recorded in section 10 rather than forced.

---

# 10 REPRODUCE / COMMIT

    cd F:/rapidmeta-ssot-shell/scripts/rekey20
    python plant_axis_match.py        # 29/29, gates the run
    python plant_seed_guards.py       # 17/17
    python run_axis_twenty.py         # the twenty, one named state each
    python seed_before_after.py --hits

    # once the index lock clears, explicit pathspec only:
    git add -- evidence/2026-08-31-axis scripts/rekey20/axis_states.py \
               scripts/rekey20/axis_match.py scripts/rekey20/plant_axis_match.py \
               scripts/rekey20/plant_seed_guards.py scripts/rekey20/run_axis_twenty.py \
               scripts/rekey20/seed_before_after.py scripts/search_topic.py

**I/O note.** F: costs ~78 ms per file open, so the matcher does **one** walk of the frame
and reuses it across all twenty topics and all 29 plants: 1,216 rows read once, 2.9 s.
Per-topic re-reads would have been 20 opens of a 2.7 MB file for the same answer.
