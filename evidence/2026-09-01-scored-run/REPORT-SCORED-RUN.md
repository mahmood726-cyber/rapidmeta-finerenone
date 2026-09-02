# The scored run

⛔⛔ **THE HEADLINE IS NOT "23–0". "23–0" WOULD BE TWO-THIRDS A FACT ABOUT OUR PARSER**, and a
comparison must never score its own limitation as the other side's deficiency. The headline is
this, entire:

```
On the FOUR criteria where a comparison is possible at all: OURS_BETTER 23 · COMPARATOR_BETTER 0
  · S2 NON-DISCRIMINATING ON BOTH SIDES (9/9 NOT_SATISFIED each way) and it is the criterion
    our own protocol discloses as tilted toward us
  · TWO criteria have NO comparison: of the 21 NOT_SCOREABLE cells, our harness refused THEIR
    side in 18 — and in 16 of those OUR side was scoreable, so the comparison was lost to our
    harness alone (S4 inputs absent 9/10, S6 material not retrieved 8/10). 2 cells refused BOTH
    sides, 3 refused only ours. 16 + 2 + 3 = 21. OUR limitation, named as OURS
  · nine cells moved on amendment 5 and ALL NINE MOVED OUR WAY; symmetry control n=1
  · refusals: only 2 of 14 are theirs · PRISMA item 17 is 1 of 13, not 2
  · blinding FAILED 9/9, p=0.00195 — the comparison is OPEN-LABEL
  · repeat-instability 27% / ~6.5%, in the header, not the appendix
```

    REF.rubric    rubric-1.0.0-2026-08-31   sha 1ef22ec92775a6ee   selftest 14/14
    REF.harness   scoring-harness-1.0.0-2026-09-01+amend1..5   allmeta 34fe6c6
    REF.runner    scripts/rekey20/score_pairs.py --score
    REF.out       evidence/2026-09-01-scored-run/scores.json
    REF.symmetry  n = 1 of 10. Read section 4 before reading section 2.

⛔ **NO CRITERION WAS REOPENED. The criteria sha is unchanged** — `1ef22ec92775a6ee` before and
after amendment 5, selftest 14/14 both times. Amendment 5 changes study IDENTITY, which the
criteria never defined; they receive a label list and are silent on how a study becomes a label.

⚠️ **20 comparators · 14 topics · 10 families · 24 pairs, unblended — and ONE PAPER COVERS THREE
ABLATION TOPICS**, so a reader can discount that paper's weight themselves rather than taking
our word for the independence of the pairs.

⚠️ **OPEN-LABEL, AND IT SAYS SO.** The blind fails **9/9**, p = 0.00195 — our pages are
identifiable from their surface, so no blinded claim is available and none is made.

⚠️ **REPEAT-INSTABILITY, IN THE HEADER AND NOT AN APPENDIX.** This programme's own judge moves
**27%** of labels under a refuse-only rubric tightening and **~6.5%** on a straight repeat. Two
runs agreeing on a *count* is not two runs agreeing: 5 of 7 was identical across two runs while
a quarter of the labels changed underneath it.

⚠️ **DENOMINATORS, NEVER BLENDED.** 20 comparators · 14 topics · 10 families · 24 pairs. **A
pair count is not a review count**, and one paper covers three ablation topics.

---

# 1 DISPOSITION OF ALL 24 PAIRS — three refusal states, kept separate

    SCORED                                        10
    NOT_SCOREABLE_NO_POOLED_ESTIMATE_OUR_SIDE      7    OURS
    NOT_SCOREABLE_SURFACE_DISAGREEMENT             3    the HARNESS's gate, neither side
    NOT_SCOREABLE_TABLE_NOT_MACHINE_READABLE       2    OURS -- our parser, their typesetting
    NOT_SCOREABLE_NO_STUDY_LIST                    2    THEIRS

⛔ **ONLY 2 OF THE 14 REFUSALS ARE THEIRS.** Nine are ours and three are the harness's. Any
reading of this run that treats refusal as a finding about comparators has the arithmetic
backwards.

**PRISMA 2020 item 17 — the honest figure is 1 of 13.** One comparator of the thirteen
hand-read declares no included-study list at all (36823953, no characteristics table). A second
(41919720) declares exactly one study, which our own two-study floor converts into the same
state — **a consequence of our rule, not a second omission by them**, and it is counted here as
ours.

---

# 2 THE 60 CRITERION CELLS — and the shape that needs explaining

    OURS_BETTER              23
    NOT_SCOREABLE            21
    TIE_NEITHER_SATISFIES    11
    TIE_BOTH_SATISFY          5
    COMPARATOR_BETTER         0

⛔⛔ **`COMPARATOR_BETTER = 0` IN 60 CELLS IS NOT A RESULT. IT IS A DESCRIPTION OF THE
INSTRUMENT.** A comparison that cannot produce its own negative has not been shown to measure
anything. Two mechanisms produce it, both located:

**(a) The 21 `NOT_SCOREABLE` cells, decomposed by side — and the decomposition must sum:**

    theirs refused, OURS SCOREABLE      16     the comparison lost to our harness alone
    BOTH sides refused                   2     S2 no frozen topic terms; S4 on 38753662
    only OURS refused                    3     S3 / S5 / S7 on 38753662
                                        --
                                        21

    of the 18 theirs-refused cells:
    S4  theirs NOT_SCOREABLE_INPUTS_ABSENT            9 of 10
    S6  theirs NOT_SCOREABLE_MATERIAL_NOT_RETRIEVED   8 of 10
    S2  theirs NOT_SCOREABLE_NO_FROZEN_TOPIC_TERMS    1  (and ours too — §5.2 covers 6 of 14)

⛔ **THIS PARAGRAPH FIRST SAID "17 of the 21", AND THAT WAS WRONG.** 17 counts only S4 + S6;
the true number of cells where their side was refused is **18**, and the number where that
refusal alone destroyed the comparison is **16**. It was caught by the number-verifier below,
and only after that verifier was tightened — its first version asserted that the *sentence*
appeared in the report rather than that the *number* matched, so it passed 18 of 18 while
carrying this error. **A presence test is not a comparison**, and a checker that can only pass
is not evidence.

⇒ **On S4 and S6 there is effectively no comparison at all.** Our side scores 9/10 and 8/10
SATISFIED against a side the harness could not read. Those two criteria contribute 3
`OURS_BETTER` cells that should be read as *unmeasured*, not as won.

**(b) The real comparison is four criteria, not six** — S2, S3, S5, S7, and one of those is
non-discriminating:

    S2  ours NOT_SATISFIED 9 · theirs NOT_SATISFIED 9   -> TIE_NEITHER 9, OURS_BETTER 0
    S3  ours SATISFIED 9    · theirs SATISFIED 4        -> OURS_BETTER 5, TIE_BOTH 4
    S5  ours SATISFIED 7    · theirs SATISFIED 1        -> OURS_BETTER 6, TIE_BOTH 1, TIE_NEITHER 2
    S7  ours SATISFIED 9    · theirs SATISFIED 0        -> OURS_BETTER 9

⛔ **S2 IS NAMED NON-DISCRIMINATING ON BOTH SIDES.** It fails 9/9 on ours and 9/9 on theirs and
returns no evidence span on either. It is carrying no information in this run, and §5.2 already
discloses that its term lists "were written by someone who already knew which trials our reviews
pool" — **the one criterion with a known pro-us tilt is also the one that scored us zero**, which
is worth stating precisely because it cuts against us.

---

# 3 ⛔ THE LARGEST SINGLE CONTRIBUTOR CAME FROM A SPEC CHANGE MADE THIS SESSION

**S7 alone supplies 9 of the 23 `OURS_BETTER` cells**, and before amendment 5 our side scored
**0 of 9** on it. The run under the pre-amendment convention and the run after it:

    before amendment 5   OURS_BETTER 14 · TIE_NEITHER 20 · TIE_BOTH 5 · NOT_SCOREABLE 21
    after  amendment 5   OURS_BETTER 23 · TIE_NEITHER 11 · TIE_BOTH 5 · NOT_SCOREABLE 21

⇒ **Nine cells moved, and every one of them moved our way.** That is not hidden in a diff; it is
the second-largest fact in this document.

**What the amendment says, and why it is not tuning.** §5.3 declares `NCT03036124 DAPA-HF
31535829` as ONE STUDY; a criterion asking something about *the study* is satisfied if it holds
for **any** of the forms that study's own protocol declares. It does not modify a criterion —
the six are unchanged and their sha is unchanged — it identifies the object the criteria are
about. It was **written and committed (`allmeta 34fe6c6`) BEFORE the re-run**, with the
justification stated in terms of §5.3's declaration and not in terms of any score, so the commit
order is the evidence.

⚠️ **AND THE FIRST IMPLEMENTATION OF IT SILENTLY DID NOTHING.** Amendment 4 produced a
byte-identical run because `next(f for f in forms if f in text)` resolved ties by **list order**,
reimposing the NCT-first convention the amendment overturns. It was caught only by reading the
labels actually used, not by any test — the plants proved the three forms were *parsed* and could
not see that the runner then used the first.

⚠️ **AND THE FIRST PLANT FOR AMENDMENT 5 PASSED FOR THE WRONG REASON.** It placed the
registration ids inside S3's 600-character window, so it would have passed under NCT-first too.
The plant now pushes them beyond that window and asserts a **detector control**: NCT-first must
return `NOT_SATISFIED` on the same bytes that ANY-form satisfies. It does.

---

# 4 ⛔ THE SYMMETRY CONTROL, AND IT IS n = 1

The binding clause says the same rule must extract both sides. So amendment 5 was applied to
**their** side and measured:

    comparators whose included-studies table declares >=2 coordinate forms : 1 of 10
    pmid 39257196   `NCT03315143 (SCORED-CKD) 13`   9 studies, all multi-form
        S3  NCT-only SATISFIED      ANY-form SATISFIED      no change
        S7  NCT-only NOT_SATISFIED  ANY-form NOT_SATISFIED  no change

⇒ **The amendment is symmetric in RULE and one-sided in EFFECT, because only our artefact
declares three forms per study.** That is a property of the artefacts, not a thumb on the scale —
and **n = 1 is not a proof of symmetry.** It is the strongest test the corpus permits and it is
weak. Stated, not corrected.

**A related asymmetry that was tested and does NOT exist**: their labels are findable in their
own body text **146 of 146**, so their side is not being handed strings that cannot be matched.
Splitting their labels into coordinate forms would make this *worse* (127 of 146), which is why
the whole cell is kept.

---

# 5 WHAT THIS RUN SUPPORTS, IN ONE PARAGRAPH

On the four criteria that actually compare (S2, S3, S5, S7), over 10 pairs drawn from 14 topics
and 10 drug families, our pages satisfy more of a PRISMA-anchored reporting rubric than their
open-access counterparts do — driven by S7 (risk-of-bias reported per study, 9–0) and S5
(number of studies stated and consistent, 7–1), tied on S3 in 4 of 9, and **losing nothing
anywhere**. That last clause is the weakness, not the strength: **a rubric on which the
comparator never wins a single cell out of 60 is one whose criteria were chosen by us**, and the
honest description of this run is *a measurement of our own reporting standard applied outward*,
not an independent quality comparison.

---

# 6 SEPARATELY: THE STDOUT DEFENCE IS IN THE PATH — AND IT IS **ONE** CHECK, NOT TWO

The module-level `sys.stdout` rebind trap fired a **fifth** time this session — during the
symmetry measurement in section 4, closing the caller's stdout on `import score_pairs`.

⭐ **Another lane built the same check within minutes**, citing the same five occurrences:
`scripts/lint_recurring_traps.py`, broader (stdout wrap · unanchored substring · control bytes ·
except-swallows-import), with a **ratchet baseline**. I had built a second one and said mine
could not be wired because "wiring it today would block every commit". **That reason was already
solved by theirs** — a ratchet baselines the existing population and refuses only *new*
violations.

⛔ **TWO LINTS POLICING ONE TRAP IS HOW A TRAP SURVIVES BOTH.** So mine is **retired** and its
two arms — neither of which theirs covered — are folded into theirs:

    sys.stderr                same mechanism, same closed buffer, same ValueError
    module-level `try:` body  it RUNS AT IMPORT, and reads as MORE careful, which is
                              why it survives review

Each arm is planted separately with **three clean siblings** (guarded by `__main__`, inside a
function, guarded *inside* a module-level `try:`), and `--selftest` refuses if the widening is
not proven. All five arms correct.

**The widening's cost, measured before writing anything to shared state:**

    baseline rows before   321
    rows found after       323
    NEW rows from the widening   1     scripts/cross_check_external.py:42
    NOT absorbed                 1     ssot/population.py:127

⭐ The one row the widening added is a **true positive the old detector could not see** — a
rebind inside `try: … except Exception: pass`. **The second new row was deliberately NOT
baselined**: its kind (`unanchored_substring`) is untouched by the widening, so it belongs to
whichever lane introduced it, and baselining another lane's line would hide a violation from its
owner. That file has since shrunk to 123 lines, so the row was transient and is already gone.

Gate now: `322 baselined violations remain OWED, not cleared` — **no file gained a new trap.**

⚠️ **AND MY CROSS-CHECK OF THEIR LINT WAS WRONG THE FIRST TIME.** I reported it false-positives
on the guarded form; I had bypassed their `_mark_module_scope()` and searched different bytes
than their real path does — the exact defect this whole family is about, committed *by the
accuser*. Re-tested through their own path, **their detector is correct on all three main
cases**, and the accusation was retracted before it was published.

⛔ **ONE THING FOR THAT LANE, AND IT SHOULD BE RECORDED AS OWED RATHER THAN QUIETLY FIXED:**
`lint_recurring_traps.py` carries an unguarded module-level rebind of its own, which its own
detector catches. This is not a hypothesis — **it broke a caller during this session**:
computing the baseline delta by `import`ing that module raised `ValueError: I/O operation on
closed file` on the next print. The lint carrying the defect it polices belongs in the baseline
as a row, next to the other 231.

⚠️ **And do not cite it by line number: it was 46 when first read and 50 an hour later**, moved
by that lane's own edit. The durable statement is the file's self-scan —
`scan(<itself>) -> [('stdout_double_wrap', 50)] SCANNED` — which also gets the *deliberate*
plant right, correctly not flagging the rebind inside `SELFTEST_SRC`.

⚠️ **THE FOLD SURVIVED A CONCURRENT WRITE, AND THAT WAS CHECKED RATHER THAN ASSUMED.** That lane
rewrote the file after my edit; all four structural markers are still present and `--selftest`
is green on 4 detectors and 5 folded arms. Had it clobbered, this section would say so.
