# The open-access lane, scored against the pre-registration

    REF.git       8e825e9e6
    REF.rule      604ed6957a1adf17   ⛔ FROZEN. Not one line retuned for this lane.
    REF.source    Europe PMC REST (free, no key)
    REF.filter    (PUB_TYPE:"systematic-review" OR PUB_TYPE:"meta-analysis")
                  AND OPEN_ACCESS:Y AND HAS_ABSTRACT:Y
    REF.page_cap  100    hitCount printed beside every fetched count
    REF.verify    abstract   ⛔ NOT comparable to a CDSR number (pre-registration A.3)
    REF.gate      gate_label_vs_reason.check — the SAME gate the CDSR judgements passed

---

# 1 THE HEADLINE: FIVE OF THE SEVEN UNREACHABLE TOPICS NOW CARRY A JUDGED COUNTERPART

    candidates (fetched)  241   ->   verified  33   ->   judged COUNTERPART  13
    INDEPENDENT TOPICS carrying one : 5 / 7
    DISTINCT open-access reviews    : 13
    verified-stage precision        : 13/33 = 39%     (CDSR was 6/14 = 43%)

⛔ These are the figures AFTER `oa_frame_contract.py` removes protocols (§4). Before it,
they read 34 verified and 38%, and one of the 34 was a Cochrane PROTOCOL that had to be
refused by hand.

| topic | fetched | verified | COUNTERPART | state |
|---|---|---|---|---|
| etripamil-psvt | 8 of 8 | 1 | **1** | MATCHED |
| mavacamten-hcm-review | 18 of 18 | 10 | **7** | MATCHED |
| riociguat-pah | 69 of 69 | 9 | **1** | MATCHED |
| selexipag-pah | 32 of 32 | 7 | **1** | MATCHED |
| sotatercept-pah | 10 of 10 | 4 | **3** | MATCHED |
| evolocumab-dyslipidemia-review | 100 of 125 | 2 | **0** | MATCHED |
| evolocumab-mixed-dyslipidemia… | 100 of 125 | 0 | **0** | CONDITION_MISMATCH |

⭐ **All thirteen counterparts are DISTINCT reviews.** There is none of the near-duplicate
inflation the CDSR result carried, where three bosentan topics shared one review — 5 topics
there rested on 4 reviews, 5 topics here rest on 13.

⭐⭐ **Five of the seven retrievals were COMPLETE, not truncated** — 8 of 8, 18 of 18, 69 of
69, 32 of 32, 10 of 10. For those five the verified set is a population and not a window.
Only the two evolocumab topics hit the 100-row cap, and they are the two that produced
nothing.

## The combined position, stated without padding

    CDSR frame           5 of 20 topics with a judged counterpart   (4 distinct reviews)
    open-access lane   + 5 of the 7 CDSR-unreachable topics         (13 distinct reviews)
    ------------------------------------------------------------------------------
    UNION              10 of 20 topics                              17 distinct reviews

⚠️ **The union is 10, not more, and the reason matters.** The open-access lane also ran the
thirteen control topics, and **their pairs are deliberately NOT judged**: every one of the
thirteen was truncated at the 100-row cap against up to 3,541 hits, so their 90 verified
rows are an arbitrary relevance-ordered window rather than a population. Judging a window
and reporting it beside a population is the reach-versus-coverage defect, and the gate
refuses out-of-scope judgements rather than accepting them quietly.

⇒ **The path from 10 to 20 is now a known piece of work, not an unknown: page through the
thirteen controls' retrievals and adjudicate them.** That is bounded and it is the first
time tonight the remaining distance has had a shape.

---

# 2 ⛔ THE ANSWER I GAVE EARLIER NEEDS AMENDING, AND IN THE FLATTERING DIRECTION

`REPORT.md` said: *"20 is not reachable. Ceiling 13."* **That was a ceiling for the CDSR
frame and it was correctly scoped, but the sentence has been read as a ceiling for the
project.** The open-access lane reaches five of the seven topics the CDSR ceiling excluded.

**The corrected statement: 20 is not reachable IN COCHRANE. It is not yet shown unreachable
overall, and the measured position is 10 of 20 with a bounded route to more.** The
underlying finding is unchanged and is the durable one:

> **no threshold reaches a review that does not exist — and the review did exist, in a
> different corpus.**

---

# 3 THE PRE-REGISTRATION, SCORED ROW BY ROW

| prediction | result | |
|---|---|---|
| **A.4.1** intervention axis live for 6 or 7 of 7 | all 7 drugs have OA SRs | **HIT** |
| **A.4.2** MATCHED for ≥5 of 7 | **6** | **HIT** |
| **A.4.3** at most **2** of 7 carry a judged COUNTERPART | **5** | ⛔ **MISS — pessimistic** |
| **A.4.4** precision falls below 43% | **39%** | **HIT** |
| **A.4.6** `sotatercept` and `etripamil` are the two I'd bet against | both have OA SRs; sotatercept yielded 3 counterparts | **MISS — pessimistic** |
| **Addendum** `INTERVENTION_MISMATCH` and `PAIR_ABSENT` unreachable here | both fired 0 | **HOLDS** |
| **A.3** MATCHED inflates on abstract verification | 6/20 → 16/20 | **HIT** |

⭐ **A.4.3 is the miss worth dwelling on, because it is the FIRST PESSIMISTIC ONE in
sixteen.** I reasoned from the olmesartan case — *an SR of "PAH therapies" is not a
counterpart to "sotatercept in PAH"* — and that reasoning was **right about the landscape
reviews and wrong about the population**. Landscape reviews were duly refused (`eighteen
targeted drugs`, `present and future pharmaco-structural therapies`, `medications for the
treatment of PAH` — all NOT_COUNTERPART). What I did not anticipate is that the
open-access literature *also* contains drug-specific reviews with titles like *"Efficacy and
safety of sotatercept in pulmonary arterial hypertension"* — which Cochrane simply has not
written. **I generalised a property of the Cochrane corpus to the literature.**

⚠️ And note what the prediction record now shows: fifteen optimistic misses, then two
pessimistic ones in the same run. **After a long optimistic streak I over-corrected.** The
lesson is not "predict lower"; it is that a correction applied as a constant is just a new
bias.

---

# 4 ⛔ WHAT ADJUDICATION CAUGHT THAT THE FRAME CONTRACT DID NOT

**Protocols reached the verified set and were labelled `systematic_review`.**

    verified rows across all twenty        124
    labelled systematic_review by the lane 124   -- it labels EVERY row that
    rows that are ACTUALLY PROTOCOLS         4   (2 distinct records)

       PMC12183782  Myosin inhibitors for treatment of hypertrophic cardiomyopathy
                    "This is a protocol for a Cochrane Review (intervention)"
       PMC12964950  Direct oral anticoagulants versus vitamin K antagonists ...
                    reached apixaban-af-review, dabigatran-af and dabigatran-stroke

**The CDSR frame contract has `record_kind` and excludes 30 protocols on exactly this
ground — a protocol reports no results and cannot be a comparator. The OA lane had no
`record_kind` test and hard-coded the value.** So the kind was asserted rather than read.

⇒ It was caught by a **human-authored judgement quoting the record's own words**, not by
the contract, and not by any plant. *List the kinds before the number* was the rule, and
the OA lane skipped it while the CDSR lane obeyed it.

## 4.1 CLOSED — `oa_frame_contract.py`, and the kind is now READ

The contract derives `record_kind` from the record's own text and **refuses a row whose
stated kind disagrees with what it reads**. `oa_retrieve.py` no longer states a kind at all;
it asks. Measured over the twenty:

    rows excluded by kind : 18 protocols
    verified rows         : 124 -> 120       (mavacamten 11 -> 10)
    judgements            : 34 -> 33         PMC12183782 is now excluded UPSTREAM of
                                             adjudication -- a mechanical exclusion beats a
                                             hand judgement, and the counterpart count is
                                             unchanged because it was NOT_COUNTERPART

`plant_oa_frame_contract.py` **19/19**: every refusal planted with a clean sibling that must
pass — a title as key, an empty-string objectives field, an undeclared verification
material, a missing field, a duplicate id, a cross-kind comparison, and the kind-claim
disagreement. ⭐ **And both real protocols fire DIFFERENT marks on live data** —
PMC12183782 on `cochrane_protocol` + `protocol_for_review`, PMC12964950 on `study_protocol`
— so two branches are proven on the corpus rather than one branch carrying the rule. A
sibling proves the detector is not merely matching the word: *"we followed our registered
analysis plan"* is still read as a review.

---

# 5 ⚠️ CONFLICT OF INTEREST, DECLARED

**I built the matcher and I am the sole labeller of its output.** This project has already
recorded that as a real weakness — *"the labeller should not be the classifier's author"* —
and it is recorded again rather than quietly repeated.

Mitigations that are real: every label passes `gate_label_vs_reason` **34/34**, quoting a
span literally present in the row's own title+abstract; the counterpart rule was **written
down before the labels** and taken from the CDSR judgements rather than invented; and the
refusals are specific and checkable (`chronic thromboembolic`, `connective tissue diseases`,
`congenital heart disease`, `low, medium, and high dosages`).

Mitigations that are **not** real: none of this makes it an independent adjudication.
⇒ **These 13 counterparts should be re-judged by a lane that did not write
`axis_match.py`.** Until then the honest figure is *13 counterparts, single-rater,
interested party, gate-checked.*

---

# 6 WHAT THE FROZEN RULE DID BADLY, SHIPPED AS A FINDING

⛔ **The rule was not retuned.** Predicted misbehaviours from A.4.5, observed:

* **`MATCHED` inflated to 16 of 20** against 6 on CDSR, because an abstract is ~250 words
  and a Cochrane objectives statement is one or two sentences. `MATCHED` is close to
  meaningless in this lane and is reported only beside `COUNTERPART`.
* **The one-term condition axis stayed fragile in both directions.**
  `evolocumab-mixed-dyslipidemia` is `CONDITION_MISMATCH` on `['mixed','dyslipidemia']` with
  `need=2` — 0 of 100 rows carry both. `pitavastatin` moved from `CONDITION_MISMATCH` on
  CDSR to `AMBIGUOUS` here, with 4 condition hits and 0 verified.
* **The class fragments did their usual double duty.** `mavacamten`'s 7 counterparts include
  three found through `cardiac myosin inhibitors` — the class, not the drug — which is the
  same mechanism that produced olmesartan's false positives. The mechanism behind the best
  result and the mechanism behind the errors is still one mechanism.

---

# 7 STILL NOT DONE, NAMED

* **The condition vocabulary (pre-registration Part B) is NOT run.** Regression criteria
  R1–R4 are declared and unused. It is the next build.
* **The thirteen control topics are unjudged** and their retrievals are truncated. Paging
  them out and adjudicating them is the bounded route from 10 toward 20.
* **Infectious disease is untouched.** The 40 target needs a second specialty; nothing here
  is cardiology-specific except the topic list, so the lane should carry over unchanged —
  which is a claim, not a measurement, until it is run.
* ~~`oa_frame_contract.py` was never written.~~ **Written, planted 19/19, and wired — see
  §4.1.** It is the coordination artefact for the ID lane: build to it and the two frames
  concatenate; build to something else and the consumer refuses loudly instead of quietly
  producing a second incompatible frame. `frame_contract.py` is untouched.
