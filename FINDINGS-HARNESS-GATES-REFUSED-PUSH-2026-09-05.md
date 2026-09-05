# Five harness gates refused a push, 2026-09-05. Eight findings on two served objects.

STATUS AT 2026-09-05 22:40, UPDATED IN PLACE. SIX of the eight are FIXED WITH THEIR GATE
PASSING (1, 2, 3, 4, 5, 6), each verified by re-running the gate that raised it rather
than by assertion. A ninth defect of the same class as finding 6 was found on a third
object (incretin-hfpef-review) by the corpus sweep below and is also fixed and passing.
Finding 8 is CORRECTED IN CONTENT BUT ITS GATE STILL REFUSES. Finding 7 is BLOCKED.

CONTENT CORRECTED AND GATE PASSING ARE DIFFERENT STATES AND THIS FILE KEEPS THEM APART.
Conflating them is how a page comes to claim more than it has earned. An earlier version
of this header said "1-6 and 8 are FIXED" while its own table two lines below said finding
8's gate still fails, and the commit that carried it (5da8296c2) says "seven of eight" in
its subject for the same reason. Both are recorded here rather than rewritten: the count
that is true is SIX fixed with gates passing, plus incretin, plus one corrected-but-
blocked, plus one blocked.

  1 NNT withdrawn ................................. derived_recompute_gate PASSES
  2 leave-one-out block withdrawn ................. derived_recompute_gate PASSES
  3 estimator panel withdrawn, headline confirmed .. derived_recompute_gate PASSES
  4 ANSWER-HF exclusion withdrawn, RoB D5 created .. contradicting_surfaces_gate PASSES
  5 prediction interval recomputed at t_3 .......... method_label_gate PASSES
  6 config.scale withdrawn (bococizumab) ........... method_label_gate PASSES
  6b config.scale withdrawn (incretin-hfpef) ....... method_label_gate PASSES
  7 chronology ..................................... BLOCKED, see below
  8 refusal basis corrected at 5 sites ............. gate still FAILS, see below

WHAT WAS FIXED WAS NOT DECIDED BY GUESSING. Where the right value was determined it was
recomputed; where it was not, the value was WITHDRAWN with its reason and the date, and the
withdrawn value kept verbatim beside the key that retires it. No number was replaced by a
confident new number that nobody had verified.

TWO BLOCKERS REMAIN, BOTH WITH THE REPO OWNER, AND NEITHER IS A PHRASING PROBLEM.

  (i) registration_chronology_gate's own stated remedy cannot clear it. Its rules
      SEARCH_PRECEDES_SCREENING and CONTENT_PREDATES_REGISTRATION compare timestamps and
      never consult a disclosure, so they FAIL unconditionally while the recorded order is
      inverted. The gate says to withdraw the claim and disclose; doing exactly that does
      not make it pass. Only changing the timestamps would, and the timestamps are the
      facts. (One of its four findings WAS cleared, by using the corpus's recognised term
      "retrospectively formalised" -- the gate matches disclosure literally by design.)

  (ii) A CORRECTION THAT QUOTES WHAT IT WITHDRAWS IS INDISTINGUISHABLE, TO A
      STRING-SCANNING GATE, FROM THE THING IT WITHDRAWS. Both registration_chronology_gate
      and refusal_reads_outcome_groups_gate scan json.dumps(obj) as one blob with no
      supersession awareness. So the verbatim superseded text this corpus REQUIRES a
      retraction to keep, and the correction text itself -- which quotes the withdrawn
      claim so a reader can see what changed -- both read to the gates as live claims. Of
      the 11 residual hits on refusal_reads_outcome_groups_gate, 4 are on _superseded_*
      keys and several are on the correction text. The gate therefore penalises exactly
      the disclosure discipline the corpus mandates, and every future correction makes an
      object look worse.

  NOTHING WAS DELETED TO SATISFY EITHER GATE AND NEITHER GATE WAS EDITED. A blocked lane
  does not edit the gate blocking it. Both are with the owner.

HOW THEY SURFACED, WHICH IS ITSELF THE POINT. The harness gates run in DIFF SCOPE
against origin/main. All eight were pre-existing and invisible until two commits
(edb7856ab, 4662db4b6) made `arni-hfref` and `bococizumab-lipid-review` "changed",
pulling them into scope. Proof they were not introduced: the operands the gates call
authoritative are byte-identical before and after -- arni's
`count_panels.rd.point` is -0.02305292779417 at b024ad089 and at 4662db4b6 -- and the
commits touched no NNT, no RD, no exclusion record and no `inputs.trials`.

  ENTERING A CHECK'S SCOPE IS WHAT REVEALS A DEFECT.
  12 of 155 canonical objects were in that push's scope. 143 were not.

EVERY GATE BELOW PROVED ITSELF BEFORE REFUSING. Each printed a positive control that
must FAIL and a negative control that must not, and each reported "both controls held."
These are working instruments, not misfires.

---

## 1. arni-hfref -- NNT is a snapshot of a superseded operand

- **GATE** `scripts/derived_recompute_gate.py`
- **PATH** `results.by_outcome.cvdeath_or_hfh_first.count_panels.nnt.{pooled_rd,nnt,rd_ci_high,nnt_low,rd_ci_low,nnt_high}`
- **VERBATIM**
  > count_panels.nnt.pooled_rd keeps its own copy of the operand as -0.044191, while the authoritative count_panels.rd.point is -0.0230529. The derived block is a snapshot of an operand that no longer exists.
  >
  > count_panels.nnt.nnt shows 22.629. Recomputed from the current count_panels.rd.point (-0.0230529) by NNT = 1 / |RD| it is 43.3784. The page must decline to show a value it cannot recompute, not show the old one.
- **CONFLICT**

  | quantity | displayed | recomputed | stored operand | authoritative operand |
  |---|---|---|---|---|
  | NNT | 22.629 | 43.3784 | -0.044191 | -0.0230529 |
  | nnt_low | 37.2258 | 59.7028 | -0.026863 | +0.0167496 |
  | nnt_high | 16.2551 | 15.9095 | -0.061519 | -0.0628555 |

- **A FIX MUST DECIDE**
  1. Which operand is authoritative -- the RD panel, or the frozen copy inside the NNT
     block. They cannot both be right and the gate does not know which is.
  2. Whether the page should DECLINE to display an NNT it cannot recompute, rather than
     display either number. The gate's wording asserts this; that is a claim to ratify,
     not to assume.
  3. The stored `rd_ci_high` is negative (-0.026863) while the authoritative
     `rd.ci_high` is POSITIVE (+0.0167496) -- the interval crosses no difference.
     Whether an NNT should be shown at all for an interval spanning zero is a separate
     judgement, and it is the one that decides whether findings (1) and (2) matter.
- **SEVERITY** A published NNT wrong by ~1.9x, on a number clinicians act on. ARNI is
  one of the 26 reviews under active review.

---

## 2. bococizumab-lipid-review -- leave-one-out block computed from a different synthesis

- **GATE** `scripts/derived_recompute_gate.py`
- **PATH** `results.by_outcome.ldlc_pct_change_wk12` -- `sensitivity.analyses`
- **VERBATIM**
  > sensitivity.analyses holds 5 analyses for a synthesis of 6 trials. Leaving one out of 6 gives 6 analyses, so this block was computed from a different synthesis.
  >
  > 5 of 5 leave-one-out rows record k=4/4/4/4; omitting one trial from 6 leaves 5.
- **CONFLICT** synthesis k=6 vs 5 LOO analyses each recording k=4.
- **A FIX MUST DECIDE** which synthesis is the real one. Regenerating the LOO block
  against k=6 would silently discard whatever the k=4 synthesis was; ruling it a
  superseded run is a different answer with different consequences for the headline.

---

## 3. bococizumab-lipid-review -- estimator panel and headline are different syntheses

- **GATE** `scripts/derived_recompute_gate.py`
- **PATH** `results.by_outcome.ldlc_pct_change_wk12` -- estimator panel REML row
- **VERBATIM**
  > the REML row of the estimator panel gives -55.4593, -55.4593, while the outcome's registered headline is -55.24. The panel and the headline are not the same synthesis.
- **CONFLICT** panel REML -55.4593 vs registered headline -55.24.
- **A FIX MUST DECIDE** which is the review's answer. Aligning panel-to-headline and
  headline-to-panel are both one-line edits and they publish different effect sizes.

---

## 4. arni-hfref -- a trial is both excluded and pooled

- **GATE** `scripts/contradicting_surfaces_gate.py`
- **PATH** `screening.records[3]` and `inputs.trials`
- **VERBATIM**
  > ANSWER-HF (NCT04853758) is recorded as an exclusion here and is also in inputs.trials, contributing to the pooled estimate. No supersession is declared on the record, so the object asserts both at once.
- **A FIX MUST DECIDE** whether ANSWER-HF belongs in this synthesis. If it does, the
  exclusion must be withdrawn WITH ITS REASON, because a withdrawn exclusion is a change
  to the screening result. If it does not, it leaves `inputs.trials` -- and k, the pooled
  estimate, tau2, I2, Q and every derived block including finding 1's NNT all move.
  This is not bookkeeping.

---

## 5. arni-hfref -- prediction interval labelled t, computed with z

- **GATE** `scripts/method_label_gate.py`
- **PATH** `results.by_outcome.cvdeath_or_hfh_first.panels.prediction`
- **VERBATIM**
  > the label says 't_{k-1}, Cochrane Handbook v6.5', and the numbers 0.6862 to 1.1070 are what a NORMAL quantile (1.9600) gives. The t quantile on 3 degrees of freedom is 3.1824 and gives 0.5911 to 1.2850. The label describes a computation that was not performed.
- **CONFLICT** published PI 0.6862-1.1070 (z=1.9600) vs t(3)=3.1824 giving 0.5911-1.2850.
- **A FIX MUST DECIDE** whether t or z is correct at k=4 -- **not merely which label to
  write**. Relabelling to "normal quantile" leaves the number wrong under an honest name
  if t is the right method; recomputing to t widens the published interval by 62%. Both
  intervals exclude 1, so the direction of the conclusion is unchanged but the stated
  precision is not. Cochrane Handbook v6.5 says t_{k-1}, which makes the LABEL likely
  correct and the NUMBER likely wrong -- the more expensive of the two repairs.

---

## 6. bococizumab-lipid-review -- review-level scale label contradicts the pooling

- **GATE** `scripts/method_label_gate.py`
- **PATH** `config.scale`
- **VERBATIM**
  > config.scale is 'log', and 1 of 2 outcome(s) were pooled on a different scale: ldlc_pct_change_wk12=natural. A review-level default rendered as a method label states, for those outcomes, a computation that was not performed.
- **A FIX MUST DECIDE** whether a percent-change outcome should be pooled on the natural
  scale (it normally should), and therefore whether `config.scale` is the wrong
  ABSTRACTION rather than the wrong VALUE -- a per-outcome scale, not a review-level
  default. Setting it to `natural` would mislabel the other outcome instead of this one.

---

## 7. arni-hfref -- inverted chronology under a prospectiveness claim

- **GATE** `scripts/registration_chronology_gate.py`
- **PATH** `search.databases[0].executed_utc`; `registration.ordering.protocol_committed_utc`
- **VERBATIM**
  > 9 of 9 DATED screening decision(s) predate the earliest executed query (search.databases[0].executed_utc at 2026-08-12T12:22:39); the other 440 of 449 record(s) carry no date at all and are outside this comparison. Earliest decision 2026-08-09T23:59:59. Trials: Bano 2021, EVALUATE-HF, HFN-LIFE, Li 2019, OUTSTEP-HF, PARALLAX. A decision taken before the search that retrieved the record is a decision about a different corpus.
  >
  > the object claims prospectiveness in 4 place(s) ... while the object's own content puts work before the protocol. The claim must be withdrawn, or replaced with a retrospective-formalisation statement that discloses the chronology.
- **A FIX MUST DECIDE** whether this review was prospectively registered. Only 9 of 449
  records carry a date, so the evidence is thin in BOTH directions. Note
  `2026-08-09T23:59:59` is a midnight-sentinel default, not an observed time -- so the
  first question is whether these timestamps mean anything at all. If they do not, the
  fix is to stop emitting a sentinel as a decision time, and the prospectiveness claim
  becomes unevidenced rather than refuted.

---

## 8. bococizumab-lipid-review -- a refusal resolved from the wrong table

- **GATE** `scripts/refusal_reads_outcome_groups_gate.py`
- **PATH** `results.by_outcome.ldlc_pct_change_wk12.POOL_FINDINGS_2026_08_20.a_spire_ai_pairs_a_dose_with_the_other_doses_placebo`
  (also `.display_change_announced[1].what_changed` and
  `.risk_of_bias.by_outcome.ldlc_pct_change_wk12.NCT02458287.domains.D5_selection_of_the_reported_result.reason`)
- **VERBATIM**
  > this refusal says it was resolved from "registry's arm table" -- a TRIAL-LEVEL source, which lists every arm of the trial and cannot say which two belong to one outcome. Only the outcome-specific group table can.
  >
  > the refusal says the NCT02458287 contrast is not registered, while this object's own registration_other_outcome_counts for NCT02458287 holds a PRIMARY entry titled 'Percent Change From Baseline at Week 12 in Fasting Low Density Lipoprotein Cholesterol (LDL-C) Level for Bococizumab 150 mg Dose Group and Matched Placebo'. The outcome names its own comparator; the refusal is contradicted by the capture it should have read.
- **A FIX MUST DECIDE** whether SPIRE-AI's week-12 LDL-C contrast IS registered. If it
  is, the refusal that excluded it must be withdrawn -- which changes what this review
  pools, and therefore findings 2 and 3. This is the one finding where the object
  already contains the evidence against its own stated reason.

---

## COUNT, WITH ITS DENOMINATOR

**EIGHT findings**, from five gates on two objects: `derived_recompute_gate` raised
three distinct defects (1, 2, 3), `method_label_gate` two (5, 6), the other three one
each. By object: arni-hfref 4 (1, 4, 5, 7); bococizumab-lipid-review 4 (2, 3, 6, 8).

Findings 2, 3 and 8 are plausibly ONE event on bococizumab seen from three surfaces --
if the SPIRE-AI refusal in 8 is withdrawn the synthesis changes, which would explain
both the LOO arity in 2 and the headline gap in 3. Recorded separately because that is
a hypothesis and the gates measured three distinct disagreements.

---

## CORPUS-WIDE SWEEP, 2026-09-05 -- THE NUMBER NOBODY HAD

All five gates re-run read-only with `--all` over every canonical object under `ssot/`.
**155 of 155 reached. No timeouts, nothing not_reached.**

| gate | N | JUDGED | FAIL | failing objects |
|---|---|---|---|---|
| contradicting_surfaces | 155 | 62 | 1 | arni-hfref |
| derived_recompute | 155 | 7 | 2 | arni-hfref, bococizumab-lipid-review |
| method_label | 155 | 52 | 3 | arni-hfref, bococizumab-lipid-review, **incretin-hfpef-review** |
| registration_chronology | 155 | 1 | 1 | arni-hfref |
| refusal_reads_outcome_groups | 155 | 2 | 2 | bococizumab-lipid-review, **evolocumab-mixed-dyslipidemia-auto-full-review** |

**FOUR distinct failing objects corpus-wide. Two are new** and had never entered diff
scope:

- `ssot/incretin-hfpef-review/incretin-hfpef-review.json` -- method_label_gate
- `ssot/evolocumab-mixed-dyslipidemia-auto-full-review/...json` -- refusal_reads_outcome_groups_gate

### THE JUDGED DENOMINATOR IS THE REAL FINDING

**These gates can speak about only a fraction of the corpus, and the fraction is small:**

- `registration_chronology` judged **1 of 155**. 154 record no dates at all.
- `refusal_reads_outcome_groups` judged **2 of 155**. 153 carry no such refusal.
- `derived_recompute` judged **7 of 155**. 132 declare no derivation, 14 NO_RECORD, 2 undeterminable.
- `method_label` judged **52 of 155**.
- `contradicting_surfaces` judged **62 of 155**.

A rule that judged nothing reads NOT OBSERVED, not SAFE. So the corpus-wide result is
NOT "4 bad objects in 155". It is **"4 bad objects among the minority these gates could
judge at all"** -- and for two of the five gates that minority is one object and two
objects respectively. `registration_chronology` failed 1 of 1 judged: that is not a 100%
corpus failure rate, it is a gate that could only speak about a single object.

**The unmeasured population is the backlog.** 154 objects record no dates, 153 carry no
resolvable refusal, 132 declare no derivation. Those are not passes. Until an object
records the field a gate reads, that gate is silent about it, and silence has been
indistinguishable from health.

---

## FINDING 9, AND IT REVERSED UNDER TEST

`refusal_reads_outcome_groups_gate` was still refusing after finding 8's correction. Eleven
residual hits were classified individually rather than dismissed as false positives -- four
were quoted retractions in `_superseded_*` keys, five were the correction text itself, and
**two were a live claim nobody had addressed**: `risk_of_bias.by_outcome.ldlc_pct_change_wk12
.NCT02458287.domains.D5_selection_of_the_reported_result.reason`, asserting

> "THE ARM PAIR RECORDED ON THIS OBJECT IS NOT A REGISTERED CONTRAST: 'Bococizumab 150mg'
> against 'Bococizumab 75mg placebo'"

**THE REGISTRY SETTLES IT AND THE CLAIM IS FALSE.** NCT02458287's posted PRIMARY analysis:

    title      ...LDL-C Level for Bococizumab 150 mg Dose Group and Matched Placebo
    OG000      Placebo Matched to Bococizumab 150 mg
    OG001      Bococizumab 150 mg
    analysis   groupIds ['OG000','OG001'], LS Mean Difference -63.4, CI [-72.0, -54.7]

`-63.4` matches this object's stored SPIRE-AI value to the digit. The stored contrast is the
trial's REGISTERED PRIMARY, read from the posted analyses block exactly as its `derivation`
says. The 75 mg comparison is a SEPARATE SECONDARY outcome at `-43.0` -- had the object used
the 75 mg placebo the stored figure would have been `-43.0`. **No published number moves and
the pooled -55.24 stands.**

So the gate caught a FACTUAL ERROR, not an unevidenced claim. That is a stronger result than
"the refusal named no table", which is what it was asked to detect.

## A GATE WHOSE PREMISE IS CONFIRMED BY THE DATA IT GOVERNS

The same registry record proves the gate's founding rule, empirically rather than by
argument:

    PRIMARY   (150 mg):  OG000 = Placebo Matched to Bococizumab 150 mg
    SECONDARY (75 mg) :  OG000 = Placebo Matched to Bococizumab 75 mg

**`OG000` denotes two different arms in two different outcomes of the same trial.** A
trial-level arm table therefore CANNOT say which two arms belong to one outcome -- as a
matter of fact about how registries are structured, not as a convention this project
adopted. Only the outcome-specific group table can.

**A gate whose premise is confirmed by the data it governs is a different object from one
that merely has not fired wrongly yet.** That is what a measured precision looks like, and
this corpus has recorded that no gate has one.

## THE 100-CHARACTER HYPOTHESIS, REJECTED BEFORE IT WAS ACTED ON

Finding 9 exposed a second defect: this object's stored `outcome_definition` for SPIRE-AI is
an exact PREFIX of the registry title, cutting the 54 characters
` for Bococizumab 150 mg Dose Group and Matched Placebo` -- the only text that names the
comparator, and therefore the only text that settles arm identity. With it retained the
false claim could not have been written.

The stored value is **exactly 100 characters**, which looks like a limit. Measured across
the corpus, it is not:

    stored outcome_definition values, corpus-wide : 196
    values exactly 100 characters                 :   2
    values longer than 100 characters             :  84
    longest value                                 : 627

**THERE IS NO LENGTH RULE.** A repair aimed at a 100-character limit would have fixed the one
case already known and nothing else -- **and it would have looked like it worked, because the
only case anyone would check is the one that prompted it.** The mechanism has to be
established before the fix; a fix aimed at the wrong mechanism is indistinguishable from a
fix that succeeded.

A second measurement, and it is deliberately reported TWO-SIDED:

    stored definitions carrying a "for <group>" comparator clause : 0 of 196

That is consistent with a capture layer that strips such clauses AND with a corpus whose
registry titles never carried them. **Stating only the first would assert the conclusion the
test exists to reach.** The discriminating test is whether stored values are exact PREFIXES
of real registry titles, run over the 190 of 196 that resolve to a registration (6 do not
and are excluded, stated rather than hidden), across 118 distinct registrations and 44
objects. If that count comes back at or near zero, the honest reading is that the capture is
faithful and SPIRE-AI is isolated -- and that result is to be reported as plainly as an
alarming one would have been.
