# Prediction, logged BEFORE the re-run — the regenerated page against CD007961.pub3

**Written 2026-08-30, before any judge has seen the regenerated page. Nothing below may be
edited after the run; corrections go underneath, dated.**

---

## ⛔ THE CLAIM WE HAVE NOT EARNED

**The 6-of-6 win was measured on the HAND-BUILT page. The harness produces a DIFFERENT
ARTEFACT.** Six blinded judges preferred `DAPIVIRINE_RING_PILOT_REVIEW.html`, 23,090 rendered
characters, every section authored. What is now served is `AGYW_HIV_PREP_REVIEW.html`, 84,182
rendered characters, every section generated.

⚠️ **These are not the same page and the verdict does not transfer.** 13 of 13 says the harness
reproduces the FEATURES the judges named. It says nothing about whether the generated prose
persuades the way the authored prose did. Until the re-run, the honest statement is:

> *Six judges preferred a hand-built page. A harness now generates all thirteen features that
> page won on. Whether the generated page also wins is UNTESTED.*

---

## The prediction

### Axes I expect to HOLD or IMPROVE

| axis | why |
|---|---|
| **absolute effects / NNT** | The generated table is *more* complete than the hand page's: it prints the baseline, both arms per 1,000, the absolute reduction and the NNT with an interval, plus an explicit statement that the interval carries the ratio's uncertainty only. The hand page gave the NNT and less of the scaffolding. |
| **age-stratified efficacy** | **This should improve, and for a reason a judge can check.** The hand page mislabels the prespecified stratum "18 to 24"; ASPIRE's is **under 25**, P = 0.64. The hand page omits the **interaction test, P = 0.02**, which is the strongest available statement about the finding. The generated version has both, and separates the prespecified split from the post-hoc thirds instead of merging them. |
| **provenance / audit trail** | The generated trail is walked from the object and prints a **denominator** — 2,440 sourced records, 146 carrying their sentence. The hand page listed five rows it chose. A judge who values checkability should prefer the one that admits its own gap. |
| **GRADE certainty** | **The largest expected gain, and the axis the comparator won.** The hand page contains the string "GRADE" **zero times**. The generated page carries the full profile with the rating recomputed from its own steps. |
| **integrity / §10** | Unchanged component; Anthropic's judge scored it directly last time. |

### ⚠️ Axes I expect to get WORSE

| axis | why |
|---|---|
| **clinical reading** | **The prediction Mahmood named, and I agree with it.** The hand page's version is fluent argumentative prose. The generated version is an assembled clause list — each clause conditional on a derived fact, and it *reads* like an assembled clause list. It also ends with a paragraph naming every clause it could NOT earn, which is honest and is not persuasive writing. **If a judge scores writing quality, this drops.** |
| **length / density** | 23k → 84k rendered characters. A judge reading for signal may find the generated page **buried**: seven new sections, most of the corpus-facing ones carrying refusals. The hand page was short and every paragraph earned its place. |
| **other STI outcomes** | The hand page printed gonorrhoea RR 1.00 (0.87–1.15) and trichomoniasis RR 1.06 (0.92–1.23). **Those numbers appear in no document this project holds** and are not carried forward. The generated page says the comparator reports these qualitatively and gives no figure. **That is more honest and it looks weaker.** A judge comparing tables sees two fewer numbers. |

### The overall call

**I predict the regenerated page still wins the head-to-head against CD007961.pub3, but by a
narrower margin than 4-decisive-of-6 — and I predict at least one judge that previously chose us
decisively now chooses us only narrowly, or flips, citing readability or length.**

⛔ **Falsifiable, and here is what would falsify each half:**
* *"Still wins"* is **wrong** if fewer than 4 of 6 choose us.
* *"Narrower margin"* is **wrong** if the decisive count is ≥ 4 again.
* *"Clinical reading gets worse"* is **wrong** if no judge's rationale mentions readability,
  prose quality, structure or length as a weakness of our page.

⚠️ **AND THE RESULT IS INFORMATIVE EITHER WAY.** If the generated page holds, repeatability cost
nothing. If it drops, **that is the price of repeatability and we report the price** — a
generator that produces a slightly less persuasive page forty times is worth more than an author
who produces a brilliant one once. What we must not do is discover a drop and quietly re-hand-edit
the page.

---

## Run conditions — fixed now, not after

* Same comparator: **Cochrane CD007961.pub3**, PMID 33719075, the object's designated comparator.
* Three families, both positions (ours first and second), **six verdicts**.
* Each model **proved from its own CLI log**, never from a self-claim.
* Grounding gate armed; **shared-substring blinding detector must read 0**.
* ⛔ **The page judged is the SERVED page**, fetched from the live URL, not a local build — and
  its **sha256 recorded beside each verdict**, because a review raised at one time and checked at
  another is not a comparison unless both sides name the same bytes.

---

## Addendum, logged before any judge is asked — the length asymmetry is extreme

Measured on the blinded documents actually written to the prompts:

| document | blinded chars |
|---|---|
| ours (regenerated) | **87,437** |
| theirs (CD007961.pub3, dapivirine section, PICO-matched) | **7,365** |

**A ratio of 11.9 to 1.** In round 2 our page was 23,090 rendered characters — roughly 3 to 1.
⚠️ **So the asymmetry the judges see has quadrupled, and it is the single largest change in the
comparison that is not a content improvement.**

⇒ This sharpens the falsifier already logged rather than replacing it. **If a judge scores us
down on structure, focus, or reading burden, that is the length prediction resolving — not the
clinical-reading prediction.** The two must be scored separately, because the clinical reading is
1,623 characters of the 87,437 and could hold perfectly while the page around it loses an axis.

⛔ **AND THE PAGE IS NOT BEING TRIMMED TO IMPROVE THE ODDS.** The length audit found only 1,287
characters of repetition attributable to this lane — 1.5% — and four of those repeats are source
quotes appearing in both an outcome row and the audit trail, which is the audit layer doing the
job a judge previously praised. Trimming to look tidy would remove the thing that won. **It runs
long, and we find out what that costs.**

## Blinding, verified before the run

* residual identifying marks: **0** in ours, **0** in theirs
* shared substrings of 60 characters or more appearing in BOTH documents: **0**

⚠️ That check mattered more this round than last: our page now QUOTES the comparator for
chlamydia and syphilis, because the comparator is the only source we hold for those outcomes.
A long shared string would have told a judge which document was derivative. It reads 0.

---

## ⭐⭐⭐ CORRECTION TO WHAT THIS RUN IS TESTING — logged before the judges, 2026-08-30

**Mahmood: *"That page was written by Claude Code and not me."***

⛔ **THE REFERENCE IS AI-WRITTEN. This is not machine-versus-human.** It is **the same model,
twice, in two modes** — and every framing of this run that said "hand-written" or implied a human
author is wrong.

| mode | what it produced |
|---|---|
| **free composition** | stated a POST HOC subgroup flat (C1); wrote *"condoms… remain necessary"*, advice a review has no standing to give (C10) |
| **constrained to derive from typed fields** | carried the post-hoc label three times; stated the background package as what both arms RECEIVED |

⇒ ***The failure is not the model. It is free composition.*** And that is the strongest argument
the architecture has: **derivation is not a slower path to the same prose — it prevents a class of
overclaim that the identical model commits when unconstrained.** Two independent instances, C1
and C10, both in the direction of overstating certainty, both removed by the constraint.

### The two claims, stated separately so the second cannot hide inside the first

1. **REPEATABILITY** — 13 of 13 winning features regenerate from the SSOT object; bespoke
   fraction 0%. *The harness can repeat itself.*
2. ⭐ **CORRECTNESS** — derivation eliminates a demonstrated overclaim class that the same model
   commits when composing freely. *The harness is right more often.*

**The second is worth more, and it was found inside the first rather than looked for.**

### What the six judges are therefore being asked

Not "does a harness beat a person". **"Does constrained derivation beat free composition, both
from the same model, against a published comparator."** ⚠️ That is a far more interesting
question, and if the regenerated page wins it is the version to write up.

⛔ **AND IT DOES NOT SOFTEN THE CRITERION.** Mahmood's prediction — *"today is the day we solve
the issue and beat Cochrane using harness"* — still resolves only on the SERVED regenerated page,
judged blind, six verdicts. Nothing above changes that.
