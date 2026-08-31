# PREDICTION, written before the two-axis matcher was written or run

Recorded 2026-08-31. Written after reading the CORRECTED re-key run
(`evidence/2026-08-31-rekey/corrected/`) and before a single line of the new matcher
existed. Nothing below was adjusted after a number came back.

## REF — the identity of everything predicted here

    REF.git            8e825e9e6
    REF.rule           604ed6957a1adf17          (rekey_rule.rule_fingerprint)
    REF.frame          a0d44914a5ef99e3          (sha256 over the SORTED SET of cd_bases,
                                                  not over the count: 1,216 unique bases)
    REF.frame_path     F:/claude-temp/pend/cdsr_frame_cardiology.jsonl   2,693,862 bytes
    REF.matcher        axis_match v1  (does not exist yet)

## THE QUESTION THIS IS A PREDICTION ABOUT

Not "how many counterparts can we find" — that is settled and the answer is **5 topics,
3 independent reviews** (CD004434 covering three bosentan topics, CD014808+CD015003 for
colchicine, CD006681 for enoxaparin). The re-key measurement is closed.

The question is **WHY the other fifteen failed, named per topic**, and whether the named
reasons say 20 is reachable.

## ⛔ THE PREDICTION I EXPECT TO BE UNPOPULAR: THE MATCHER WILL NOT MOVE THE NUMBER

A two-axis matcher is a **diagnostic**, not a looser rule. `MATCHED` keeps the identical
conjunction the current scan uses — an intervention term and >=2 condition terms, in
title+objectives, re-verified in `objectives_verbatim` alone. Scoring the axes separately
adds information about the FAILURES; it cannot add a candidate.

**So I predict `MATCHED` = 6 topics, exactly the six that already verify, and
`judged COUNTERPART` = 5 topics / 3 independent reviews, exactly as now.** If the new
matcher returns MORE than 6 matched, that is not a success — it is evidence I loosened
something without noticing, and it should be treated as a defect until explained.

## THE PER-TOPIC PREDICTION — every one of the twenty, named

| # | topic | predicted state | why |
|---|---|---|---|
| 1 | apixaban-af-review | AMBIGUOUS | 1 candidate, 0 verified today |
| 2 | apixaban-vte-prophylaxis | REFUSED_NO_TERMS | condition_terms is **empty** — never searched |
| 3 | bosentan-pah | MATCHED | |
| 4 | bosentan-pah-children | MATCHED | |
| 5 | bosentan-pah-monotherapy | MATCHED | |
| 6 | colchicine-cvd-review | MATCHED | drug arm |
| 7 | dabigatran-af | AMBIGUOUS | 1 candidate, 0 verified |
| 8 | dabigatran-stroke | AMBIGUOUS | 1 candidate, 0 verified |
| 9 | enoxaparin-vte | MATCHED | |
| 10 | etripamil-psvt | INTERVENTION_MISMATCH | PSVT is live in CDSR; etripamil is not |
| 11 | evolocumab-ascvd-auto2 | REFUSED_NO_TERMS | condition_terms **and** class terms empty |
| 12 | evolocumab-dyslipidemia-review | INTERVENTION_MISMATCH | F5 killed the class; drug alone absent |
| 13 | evolocumab-mixed-dyslipidemia-auto-full-review | INTERVENTION_MISMATCH | as 12 |
| 14 | mavacamten-hcm-review | INTERVENTION_MISMATCH | drug too new for CDSR |
| 15 | olmesartan-htn | MATCHED | **and I predict it is a FALSE positive** — see below |
| 16 | pitavastatin-auto-full-review | CONDITION_MISMATCH | the second axis, named in advance |
| 17 | riociguat-pah | INTERVENTION_MISMATCH | PAH live (bosentan proves it), riociguat absent |
| 18 | selexipag-pah | INTERVENTION_MISMATCH | F4 killed the class |
| 19 | sotatercept-pah | INTERVENTION_MISMATCH | F5 killed the class |
| 20 | warfarin-af | AMBIGUOUS | 1 candidate, 0 verified; F6 killed the class |

**Totals predicted:** MATCHED 6 · AMBIGUOUS 4 · INTERVENTION_MISMATCH 7 ·
CONDITION_MISMATCH 1 · REFUSED_NO_TERMS 2 · NO_CANDIDATE_RETRIEVED 0 · PAIR_ABSENT 0.

## ⭐ THE VACUOUS SET, PREDICTED BEFORE IT IS COUNTED

`all([])` is `True` and an empty term list searched against 1,186 rows returns `0`, which
prints identically to "searched and found nothing". I predict the current scan is already
reporting vacuous zeros as real ones:

    condition_terms == []   predicted 2 topics   (apixaban-vte-prophylaxis, evolocumab-ascvd-auto2)
    class_terms     == []   predicted 7 topics   (the F4/F5/F6 refusals + the two above)

**7 of 20 arm-B zeros are predicted to be VACUOUS — the class was never searched, because
the rule refused to produce one.** Reported today as `B 0/0`, indistinguishable from a
class that was searched and missed.

## ⭐ OLMESARTAN IS PREDICTED TO BE THE MATCHER'S FALSE POSITIVE, AND IT IS ALREADY ON THE RECORD

`olmesartan-htn` verifies 2 pairs and **both were judged NOT_COUNTERPART**: its class
phrase reaches `endothelin receptor antagonist` reviews on a shared two-word suffix. That
is fragment noise, exactly the risk named in `EXPECTATION-RERUN.md` for `heparin` —
it did not materialise there and I predict the axis run shows it materialised here instead.

**So verified-stage precision is predicted at 6/14 pairs = 43%,** and the two-axis matcher
must not be allowed to launder that.

## THE ANSWER I PREDICT TO THE QUESTION MAHMOOD ACTUALLY ASKED

**Is 20 reachable? I predict NO, and I predict the matcher will say so with a number.**

Predicted ceiling **within this frame**: the topics with any live intervention axis at all.
I predict **at most 8 of 20 could ever match here, and 5 is what stands.** The 7 predicted
INTERVENTION_MISMATCH topics are not a tuning problem — mavacamten, sotatercept, etripamil,
riociguat and selexipag are drugs Cochrane has not reviewed, and no threshold reaches a
review that does not exist.

⇒ **20 requires a SECOND FRAME, not a looser rule.** The matcher's job is to say which
second frame: if the failures are INTERVENTION_MISMATCH, the frame must contain newer
drugs (open-access non-Cochrane SRs); if CONDITION_MISMATCH, the frame is fine and the
condition vocabulary is the defect.

## THE DIRECTION I EXPECT TO MISS: OPTIMISTIC. IT ALWAYS HAS BEEN.

Thirteen consecutive optimistic misses, then one low, then one optimistic-by-one on the
re-key rerun. **I predict optimistic again, and specifically here:**

I expect to have OVER-estimated `INTERVENTION_MISMATCH` and UNDER-estimated
`NO_CANDIDATE_RETRIEVED`. My reasoning assumes the CONDITION axis is live for PAH, HCM and
dyslipidaemia because the words look common. If the stemmed condition terms miss Cochrane's
own phrasing, those topics fall to `NO_CANDIDATE_RETRIEVED` — a strictly WORSE diagnosis,
because it means neither axis works and the failure is not localised.

The secondary optimistic risk: that naming the failure states feels like progress on
reachability. **It is not. A well-named absence is still an absence.**

## WHAT WOULD MAKE THIS PREDICTION MEANINGLESS

Editing it after the run. It is committed before the matcher exists; the run's report cites
this file by name and scores against it row by row, including the rows I get wrong.
