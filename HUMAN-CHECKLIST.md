# The three no gate can catch

Every other control in this repository refuses mechanically. **These three cannot**, and saying
so is itself the control: it tells you where to be careful instead of letting you assume the
machine has it covered.

A helper that raises when you hand it the answer is not a control — it requires you to already
know. `instrument_controls.py` holds three such helpers. They are documentation with a function
signature, and they are listed here so nobody mistakes them for enforcement.

Run this checklist when you are about to **report a number**, **accept a disagreement**, or
**declare something absent**.

---

## 1. Read the artefact, not the tag

> `page_states_its_own_condition()` · **cannot be mechanised**

**When a page states its own condition and your instrument disagrees, the page is the evidence
and the instrument is the hypothesis.**

On 2026-08-23 legacy pages carried a banner reading, in plain English, *"47 number(s) on this
page marked UNVERIFIED — no resolvable trial id"*. An extraction found NCTs on 128 of 129 of
them and reported that the bare-count distinction "failed". The NCTs were real but belonged to
other, verified content; **zero were among the numbers flagged unverified**, which is exactly
what the banner had already said. Corrected overlap: 1 of 129.

**The corpus was telling the instrument the answer and the instrument overrode it.**

- [ ] Does the page, object, or commit message say something about its own state?
- [ ] Does my measurement contradict it?
- [ ] If so — **check the probe first.** Every time this arose, the probe was asking a subtly
      different question. Not once was the page wrong about itself.

No gate can do this. A machine cannot tell "the page is lying" from "my question is different".

---

## 2. Abstain rather than guess

> `abstain_or_answer()` · **cannot be mechanised**

**A check that requires judgement should be built to abstain, not to guess.**

The asymmetry that makes this concrete:

| limb | needs | publishable? |
|---|---|---|
| "does `NCT01084557` exist" | the registry's own 404 | **yes** — no judgement |
| "is this the RIGHT trial for this page" | acronym expansion, synonyms, MeSH | **no** — needs a person |

Implemented as substring overlap, the second produced **727 of 745**, then **149 of 602**. Both
withdrawn. `ALS_NEW_AGENTS` → terms `['agents']` against *"Amyotrophic Lateral Sclerosis"*;
`ALK_NSCLC` matched against an **alectinib ALK trial** and called a donor.

- [ ] Does this check need world knowledge — synonyms, acronyms, "is X the same thing as Y"?
- [ ] If yes, can it return `NOT_ASSESSABLE` rather than a verdict?
- [ ] Am I about to publish a rate whose numerator required judgement?

**A guess dressed as a measurement costs more than silence.** Roughly a third of that day's
value was in refusing to answer.

---

## 3. Composed at render time, or stored?

> `composed_or_stored()` · **partly mechanisable, currently not**

**Before fixing a rendered string, establish whether it is composed at render time or stored. A
projector fix cannot reach a baked value, and both look identical on the page.**

`_flatten_container` was fixed, unit-tested, and MAVACAMTEN was rebuilt to prove it. The page
came back with the **same three hits** — the text was written into the object by a *different
function*, days earlier. The renderer was fixed and the defect was in the writer.

- [ ] For the string I intend to change, have I found **both** the render-time path and any
      field that may already hold it?
- [ ] Which one am I fixing?
- [ ] **A rebuild that changes nothing is the signature of getting this wrong** — and it is
      silent, because a page that was never going to change looks exactly like a page that had
      nothing to fix.

---

## Why these three and not the others

Four sibling lessons **were** mechanised on the same day, and the difference is instructive:

| lesson | why it could be a gate |
|---|---|
| a channel nothing validates | the corrupted byte is detectable — `lint_control_chars` |
| a gate never seen to fail | you can plant the defect and observe |
| a selector keyed to the defect | the population is enumerable independently |
| every probe names a corpus positive | the declaration is checkable — `lint_instrument_declares_a_control` |

The three above have no such handle. Each turns on *whether the question being asked is the
question that matters*, and no program can check that. Only a person reading the instance can.

**That is the whole reason a person reads the instance.**
