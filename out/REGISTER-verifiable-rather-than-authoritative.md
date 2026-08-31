# Free composition overclaims; derivation does not — the same model, twice

**Registered 2026-08-30. CORRECTED the same day: the reference page was written by Claude Code,
not by a person. This is not machine-versus-human. It is THE SAME MODEL IN TWO MODES.**

⛔ **Every framing below that read as "better than the hand-written version" has been struck.**
It was wrong on the facts and it understated the result. The finding is not that a generator
beat an author. It is that **the identical model overclaims when composing prose freely and does
not when constrained to derive from typed fields** — and there are two independent instances,
C1 and C10, both in the direction of overstating certainty.

---

## The two sentences

**Freely composed** by the same model, on the page six blinded judges preferred:

> Condoms, STI screening and partner services remain necessary.

**Generated**, from the object:

> This effect was measured **on top of** counselling on HIV-1 risk reduction, partner HIV-1
> testing, treatment of sexually transmitted infections in participants and partners, and free
> condoms, given to every participant in both arms. It describes the intervention ADDED to that
> care and says nothing about it used instead of that care.

**Both leave the reader with the same decision.** Only one of them can be checked.

---

## What is actually different

The freely composed sentence is a **care recommendation**. It is almost certainly correct
clinical advice — and this review has no standing to give it. Nothing in the object supports it;
it came out of the model's own knowledge under no constraint to source it, and a reader who
wanted to verify it would have nowhere to go. ⚠️ **Its authority is nobody's that can be
checked.**

The generated sentence is a **property of the estimate**. The trials record that every
participant in both arms received that package — verbatim, in ASPIRE's own words:

> "All participants received a package of HIV-1 prevention services, including counseling with
> respect to HIV-1 risk reduction, partner HIV-1 testing, treatment of sexually transmitted
> infections in participants and partners, and free condoms."

⇒ So the effect *is* an effect measured on top of that care, and *does* say nothing about the
ring used instead of it. **Its authority is the trial's, and the sentence carries the route
back to it** — `results.by_outcome.primary.background_care`, sourced to `PMC4993693`,
sha256 `a6c75ad7e331aff7…`, with the quote stored beside the field.

⭐ **AND IT IS MORE USEFUL, NOT MERELY MORE CAUTIOUS.** "Condoms remain necessary" tells a
programme what to do. "This estimate is conditional on a package your programme may not deliver"
tells it *what its own result will be if it does not* — which is the question a programme
actually has.

---

## The rule this yields

> **When you are about to write what a reader SHOULD DO, look for the fact in the evidence that
> makes them do it, and write that instead.**

The recommendation and the fact usually point the same way. The difference is that the fact can
be checked, can be disagreed with on its merits, and does not require the reader to trust the
author's judgement about a domain the review never studied.

### How to tell which one you have written

| authoritative | verifiable |
|---|---|
| *remain necessary*, *should be offered*, *clinicians should* | *was measured on top of*, *was delivered to both arms*, *is conditional on* |
| the modal verb carries the claim | the tense carries the claim |
| no field in the object supports it | a named field supports it, with a quote |
| a reader can only accept or reject the author | a reader can go to the source and check |

⛔ **AND THE TEST IS MECHANICAL: can you name the field?** If the sentence cannot be traced to a
key in the object, it is the author speaking, and it belongs either in a source-backed form or
not at all.

---

## Why this matters beyond one sentence

The whole project's claim is that a generated review can be trusted *because* it can be checked.
**C10 is the smallest complete demonstration of that claim**: the constrained pass was handed a
sentence the unconstrained pass had written, could not source it, went to the trial report,
found the fact underneath it, and produced a sentence that is weaker in authority and stronger
in use.

⭐ **AND C1 IS THE SECOND INSTANCE, FOUND BY A SIBLING LANE.** Free composition wrote *"In women
over 21 the ring works"* flat. ASPIRE calls that analysis POST HOC. The constrained pass carries
the label three times — *"22 to 26 years (post-hoc); 27 to 45 years (post-hoc); Over 21 years,
combined (post-hoc)"*. ⚠️ **A post-hoc subgroup presented as a finding is the difference between
a hypothesis and a recommendation**, and that is the whole clinical weight of the claim.

⇒ ***Two instances, same model, same page, both in the direction of overstating certainty, both
removed by the constraint.*** **That is a CORRECTNESS claim and it is worth more than the
repeatability claim it was found inside of.** "13 of 13 features regenerate" says the harness
can repeat itself. **"Derivation eliminates a demonstrated overclaim class" says it is right
more often** — and the two must be reported separately, because the second is the one that
matters and it would otherwise hide inside the first.

⚠️ **It also shows the failure mode to watch.** The easy move, under pressure to reach parity,
was to copy the recommendation into the generator. That would have scored the same on a claim
count and been exactly the defect this project keeps finding — prose asserting more than the
store holds. **The claim recall number would not have caught it. Only asking "which field?"
caught it.**

---

## Companion, same night: a checker that read bytes the page never showed

The claim scorer measured hedge strength over a **360-character window** around each match, so a
neighbouring sentence's "is" scored three correctly-hedged claims as overclaims. Same family as
a verifier searching a different haystack than it displayed — an instrument accusing the thing
it is checking, using bytes that thing did not say.

⭐ **And the fix carries a linguistic point worth keeping for every hedge check we write:**
take the **WEAKEST** modal marker present, not the strongest. **English hedges are ADDED to
assertive clauses rather than substituted for them** — "it has not been demonstrated" still
contains "is" — so reading the strongest marker scores every hedged sentence as assertive, and
every honest page as an overclaiming one.

---

# ⛔⛔⛔ A METRIC CANNOT DISTINGUISH THE FIX THAT EARNS IT FROM THE FIX THAT FAKES IT

**Registered 2026-08-30. This is the generalisation, and it applies to every acceptance number
this project will ever set — including the regeneration count itself.**

The clinical-reading target was 12 of 12 claims. **It was reachable two ways:**

| route | claim recall | what it means |
|---|---|---|
| make the STORE hold the facts, then derive the claims | **12 of 12** | the review knows four things it did not know before, each traceable to a sentence in a trial report |
| write the four sentences into the generator | **12 of 12** | the page asserts four things the store cannot support |

⚠️ **IDENTICAL SCORE. OPPOSITE MEANING. And the metric is blind to the difference** — it counts
propositions, and both routes produce the propositions.

⇒ ***So "the four claims were missing because the store did not hold the facts" is the FINDING,
and 12 of 12 is only its RECEIPT.*** A number reported without saying which route produced it is
not evidence of anything.

## What to do about it, since the metric cannot be repaired

The metric is not broken — **no metric can carry this distinction, because the distinction is
about provenance and a count is about output.** So it must be carried alongside:

1. **Report the ROUTE beside the number, always.** "12 of 12, of which 4 required new typed
   fields read at source" is a claim. "12 of 12" is a score.
2. **Make the route mechanically checkable.** Every claim in the reference set names
   `derivable_from` — a key in the object. A claim whose sentence exists but whose field does
   not is the faked route, and that IS checkable even though the recall count is not.
3. ⛔ **Be most suspicious when a number moves quickly.** The four claims took a retrieval, a
   read, and three typed fields. If they had taken ten minutes of writing, that speed would
   have been the signal.

## The same shape, elsewhere in this run

* **The regeneration count itself.** 13 of 13 is reachable by putting the features in the
  harness, or by loosening the detectors until the old page passes. That is exactly why the
  final detector set was re-run against a genuine pre-change build and had to score **4 of 13**
  — the number was checked against the route, not just reported.
* **Gate 9's shared path.** "No finding" was reachable by fixing the collision, or by assembling
  the path at runtime so the lint could not see it. Same verdict, opposite meaning, and the gate
  said so in its own coverage note.
* **The C12 band.** An overclaim count of 0 was reachable by correcting a wrong band assignment,
  or by weakening a right one. The distinguishing fact was that **recall was 12 of 12 under both
  bands** — the correction could not move the headline number, which is what made it safe.

⭐ **The general test: ask what ELSE would have produced this number, and check which one you
did.** If a cheaper route existed and you cannot show you did not take it, the number is not yet
evidence.

---

# ⛔⛔⛔ FIX / REBUILD / SERVED ARE NOT THREE STAGES — THEY ARE THREE DIFFERENT SUBJECTS A NUMBER CAN BE ABOUT

**Registered 2026-08-30, after two lanes reported incompatible readings of "the same page" and
both were right.**

> ***"My 12/12 is a claim about one section of an unpublished build. It was never a claim about
> the live page, and I should have said so in those words."***

## What happened

A sibling lane reported a safety-critical absence: *"'not been shown' occurs ZERO times on the
whole generated page, while the benefit claim is present."* This lane had just reported the same
page at **12 of 12 claims, 0 overclaims**. Two lanes, one page, incompatible readings.

**Neither was wrong. They were describing different bytes.**

| subject | rendered chars | `not been shown` | the 18–21 non-demonstration |
|---|---|---|---|
| **LIVE** — what a reader can fetch | 56,827 | **0** | **absent** |
| **BUILT, not served** — this lane's worktree | 84,533 | 1 | **present in 5 places** |

The live page predates the components entirely: it carries none of the seven sections. The
sibling lane scanned what is REAL. This lane scanned what is BUILT. **Both true; neither
transferable.**

## The rule

⇒ **A number must name its subject, every time: LIVE, or BUILT-NOT-SERVED.**

⚠️ **And the reason is not pedantry — it is that a number which does not name its subject will be
read as being about the strongest one.** "13 of 13" and "12 of 12" were heard as facts about a
published review. They were facts about a directory. Nobody lied; the subject was simply never
said, and the strongest reading filled the gap.

## Why this is the completion of a rule already held

The project already had *"push ≠ deploy"* and *"nothing counts until it is SERVED"*, and a commit
on `main` already records the same failure in another lane's words: **"my four components were on
0 of 163 delivered pages, and I had reported them landed."**

⛔ **What was missing is that FIX, REBUILT and SERVED are not a sequence to complete — they are
three different objects, all of which exist simultaneously, and any measurement is about exactly
one of them.** A generator can be fixed while every delivered page still shows the defect; a page
can be rebuilt on disk while the served bytes are months old. Asking "is it fixed?" is not a
well-formed question until you say *which of the three*.

## The method that resolved it, in one exchange

**Do not argue. TABULATE.** Version, byte count, rendered characters, phrase counts, per artefact,
side by side. The disagreement dissolved the moment both subjects were named, and what remained
was a genuine finding about the live page that this lane had not noticed and the sibling had.

⭐ **A disagreement between two parties who both actually looked is a finding about the QUESTION,
not about either party.** The first move is to establish what each one measured — reference,
target, and version — and the second is to publish both with their denominators.
