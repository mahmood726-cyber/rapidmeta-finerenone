# Pre-registration: the open-access frame, and the condition vocabulary

Written 2026-08-31 **before** either is built. Both are decided in advance so the run can
only confirm or refute, not be read favourably afterwards.

    REF.git      8e825e9e6
    REF.rule     604ed6957a1adf17     ⛔ FROZEN. Not retuned for either experiment.
    REF.matcher  axis_match v1        ⛔ FROZEN.
    REF.cdsr     a0d44914a5ef99e3     the incumbent frame, 1,216 rows / 1,186 reviews

---

# PART A — THE OPEN-ACCESS FRAME

## A.1 The demand list is PRE-SPECIFIED, and it is not mine to choose

The seven topics the new frame must answer are **exactly** the seven the two-axis run put
in `INTERVENTION_MISMATCH` or `NO_CANDIDATE_RETRIEVED` against the CDSR frame. They were
named by the matcher before this document existed, in
`evidence/2026-08-31-axis/axis_states_twenty.json`. **No topic may be added to this list
later, and none may be dropped.**

| # | topic | CDSR state | CDSR axis I | CDSR axis C |
|---|---|---|---|---|
| 1 | etripamil-psvt | INTERVENTION_MISMATCH | 0 | 3 |
| 2 | riociguat-pah | INTERVENTION_MISMATCH | 0 | 19 |
| 3 | selexipag-pah | INTERVENTION_MISMATCH | 0 | 19 |
| 4 | sotatercept-pah | INTERVENTION_MISMATCH | 0 | 19 |
| 5 | mavacamten-hcm-review | INTERVENTION_MISMATCH | 0 | 1 |
| 6 | evolocumab-dyslipidemia-review | NO_CANDIDATE_RETRIEVED | 0 | 0 |
| 7 | evolocumab-mixed-dyslipidemia-auto-full-review | NO_CANDIDATE_RETRIEVED | 0 | 0 |

⭐ **The other thirteen are carried through unchanged as a CONTROL GROUP.** A new frame that
improves the seven while quietly degrading the thirteen has not improved anything, and only
running all twenty can show it.

## A.2 ⛔ THE RULE IS FROZEN. If it behaves badly on open-access SRs, that ships as a finding

Not one line of `rekey_rule.py`, `axis_states.py` or `axis_match.py` changes. The only thing
that changes is the frame. That is what makes this an experiment rather than a fitting
exercise — and it is why a bad result is publishable rather than embarrassing.

## A.3 ⚠️ THE HAZARD I EXPECT TO DOMINATE, NAMED BEFORE IT HAPPENS

**`objectives_verbatim` is not a field the open-access literature has.**

The matcher's verification step is *"both axes match again in `objectives_verbatim` ALONE"*,
and its whole power comes from that field being **short and purpose-specific** — a Cochrane
objectives statement is one or two sentences. The nearest thing Europe PMC offers is the
**abstract**, which is ~250 words.

⇒ **Substituting an abstract for an objectives statement changes what `MATCHED` MEANS
without changing a line of the rule.** Verification becomes nearly free, `MATCHED` inflates,
and the number looks like an improvement. This is *the material decides the verdict* arriving
through a frame swap rather than through a prompt.

**Committed in advance: the OA frame will carry `objectives_verbatim` = the abstract, and
every OA number will be reported as NOT COMPARABLE to a CDSR number on the same axis.**
Comparing 6/20 on CDSR with any figure from an abstract-verified frame would be comparing
two different measurements under one name.

## A.4 THE PREDICTION — and I am predicting LOW, because the record says to

Fifteen optimistic misses. So:

**A.4.1 Retrieval — I predict the drugs ARE there.** The coverage gap is *Cochrane-specific*,
not literature-wide. Every one of these seven has an approved drug with published trials.

    intervention axis becomes LIVE (>0 rows) for   6 or 7 of the 7

**A.4.2 Matching — I predict most of them match, and that this is the least meaningful
number in the run.**

    MATCHED for  >= 5 of the 7

**A.4.3 ⭐ Judgement — THE NUMBER THAT MATTERS, AND I PREDICT IT IS SMALL: at most 2 of
the 7 will carry a judged COUNTERPART.**

The reason is the olmesartan lesson, restated: *an SR of "PAH therapies" is not a counterpart
to "sotatercept against placebo in PAH"*, exactly as CD004434 was not a counterpart to
olmesartan. Retrieval finds topical neighbours; adjudication decides counterparts; and the
open-access SR literature is much richer in topical neighbours than Cochrane is.

**A.4.4 Precision — I predict it FALLS below the CDSR figure of 6/14 = 43%.** A larger,
noisier frame plus a class-fragment matcher (`receptor antagonist`, `enzyme inhibitor`) plus
abstract-based verification all push the same way.

**A.4.5 The frozen rule's specific predicted misbehaviour, named so it can be scored:**

  * `need = min(2, len(cond))` with a ONE-term condition will be **promiscuous**. On CDSR,
    `stroke` already matched 198 of 1,186 (17%). On a larger frame I expect one-term topics
    (`dabigatran-stroke`, `olmesartan-htn`, `pitavastatin`, `evolocumab-dyslipidemia`) to
    match a comparable or larger *fraction*.
  * The two-word class suffixes will match far more rows than on CDSR, so `AMBIGUOUS` and
    false `MATCHED` both rise.
  * **These are predicted FAILURES OF THE FROZEN RULE and they ship as findings. They are
    not licence to retune it.**

**A.4.6 The direction I expect to miss: optimistic, and specifically about A.4.1.** I expect
to over-estimate how many of the seven have an OA systematic review *of that drug* rather
than an SR of its disease area that merely mentions it. `sotatercept` (2023) and `etripamil`
(2023) are the two I would bet against first.

## A.5 What is reported, and what may never be reported

    candidates -> verified -> judged            three numbers, never padded
    COMPARATORS / INDEPENDENT TOPICS            because three bosentan topics were one review
    per-topic, for all 20: CDSR state -> OA state

⛔ **No target number appears anywhere in the pipeline.** 40 is Mahmood's goal, not an input;
the moment a criterion is chosen because it reaches a number, the pre-registration is void.

## A.6 Coordination — one frame, not two

I could not identify the ID-frame lane: `ListAgents` returns **242 peer sessions**, almost
all named after the same directories, and broadcasting into 242 sessions is noise rather than
coordination. ⇒ **So the coordination point is an artefact, not a message.** The frame
contract is published at `scripts/rekey20/oa_frame_contract.py` with the same discipline as
`frame_contract.py`: required fields, one row per identifier, `null` means UNOBTAINABLE and
never the empty string, `record_kind` stated. Any lane building an open-access frame should
build to that contract and the two frames concatenate; a lane that builds to a different
contract will be **REFUSED by the consumer**, loudly, rather than silently producing a second
incompatible frame.

⛔ **`frame_contract.py` is NOT modified.** Its `CD\d{6}` key check is correct for what it
gates, and widening it so one contract covers two frames would delete the check that makes
it useful. Two contracts, both strict, is right; one loose contract is not.

---

# PART B — THE CONDITION VOCABULARY, ALONGSIDE AND NEVER INSTEAD

## B.1 The defect, restated as a measurement

The intervention axis passes through an authority (ChEMBL → USAN). **The condition axis is
literal title words.** Measured on CDSR:

    dabigatran-stroke   ['stroke']               198 / 1,186   PROMISCUOUS
    olmesartan-htn      ['hypertension']          95 / 1,186   PROMISCUOUS
    pitavastatin        ['hypercholesterolemia']   0 / 1,186   DEAD

⚠️ **The 198 is as much a defect as the 0**, and only one of them looks like one. A dead term
returns an obvious zero; a promiscuous term returns a plausible number and manufactures the
false positives that adjudication then has to kill by hand. `olmesartan-htn`'s two false
pairs are `hypertension` (95 rows) crossed with the fragment `receptor antagonist` (9 rows).

## B.2 The intervention: MeSH entry terms, free, already in the repo

`search_topic.mesh_entry_terms` already calls NLM E-utilities. The condition axis gets the
same treatment the intervention axis has had all along. **Both axes are run in parallel over
all 20 and BOTH columns are published per topic — `literal → MeSH`.** The incumbent is not
removed.

## B.3 ⛔ REGRESSION IS DEFINED HERE, BEFORE THE FIRST QUERY

MeSH expansion is **rejected** if any of these holds:

  * **R1** any topic that is `MATCHED` under literal terms is not `MATCHED` under MeSH;
  * **R2** any topic loses a judged `COUNTERPART` it currently holds — the 4 independent
    reviews `CD004434 · CD006681 · CD014808 · CD015003` must all survive, by cd_base, hashed
    as a set;
  * **R3** verified-stage precision falls below the incumbent **6/14 = 43%**;
  * **R4** any topic's condition axis exceeds **25% of the frame** (297 of 1,186). A term
    matching a quarter of everything is not a condition, and `stroke` at 198 (17%) is
    already close enough that this bound can bite.

⭐ **R3 and R4 are the ones that make this a real gate.** R1 and R2 alone would let MeSH pass
by adding matches while degrading every one of them — the exact trade that "more topics
matched" would otherwise hide.

## B.4 The prediction, low again

  * `pitavastatin` **will** be rescued from `CONDITION_MISMATCH`: MeSH entry terms for
    *Hypercholesterolemia* include *Hyperlipidemia*, which is live on CDSR at 1 row. ⚠️ One
    row is not much of a rescue, so I predict its state changes and its **judged counterpart
    count stays 0**.
  * The two `REFUSED_NO_TERMS` topics are **NOT** helped: their titles have no condition
    connective, so there is no span to expand. Expanding nothing yields nothing —
    `norm([])` is still `[]`. **Predicted: still `REFUSED_NO_TERMS`.**
  * **I predict MeSH TRIPS R4 on at least one topic** and that the honest outcome is
    *"adopt for dead terms, refuse for promiscuous ones"* — i.e. expansion helps recall and
    hurts precision, which is what expansion always does.
  * Net predicted change in judged counterparts across all 20: **0**.

## B.5 The direction I expect to miss

Optimistic, and about B.4's last line: I expect to be tempted to read a rise in `MATCHED` as
success. **A rise in `MATCHED` with no rise in judged `COUNTERPART` is a precision loss
wearing the costume of a recall gain**, and section 4 of `REPORT.md` already showed that
`MATCHED` and `COUNTERPART` come apart badly on this corpus — 6 topics matched, 5 with a
counterpart, and 8 of 14 verified pairs refuted.
