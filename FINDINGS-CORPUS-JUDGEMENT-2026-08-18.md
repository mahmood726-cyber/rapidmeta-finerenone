# The corpus is better built than our ledger implies

**A reader of `MISTAKE-LEDGER.md` alone would conclude this architecture is broken. The
evidence says otherwise**, and the summary judgement belongs written down rather than said
in passing — because the ledger is long, the good properties are diffuse, and only one of
those two facts is self-advertising.

## What was tested and held

| property | evidence |
|---|---|
| **the arithmetic is correct** | **19 of 19** published pooled estimates re-derive from their own objects' per-trial inputs, **14 to machine precision** |
| **the generator marks absence rather than inventing** | it renders `"not stated"` where an object is silent, with its own comment: *"a zero is a claim"* |
| **the one guard with no override is the one that works** | the pre-push regression gate caught a JavaScript syntax error that **eight** of our own structural checks passed |
| **all-or-nothing holds at scale** | **57 simultaneous build failures produced zero half-written pages and zero partially-updated objects** — asserted from one failure, then demonstrated across a batch |
| **the schema is self-declaring** | `estimator` is present on **35 of 35** pooled blocks; ignoring it, not its absence, caused a false accusation against four live pages |

**The defects have been in the connections between things, not in the things.** Objects
that never reached pages. A generator filed where no search looked. A field the consumer
reads under a name the producer didn't write. Two artefact kinds sharing a file extension.
**Every one is a seam. None is a component.**

That distinction decides what the remedy costs: **a broken component must be rebuilt; a
broken seam must be connected.** Fifty-seven blank pages are a `build_tabbed.py` command
each — which is exactly what the thirteen infectious-disease pages were before they went
live.

---

## The schema grew unversioned, so newer objects are systematically thinner

Older objects carry fields newer ones were never built to hold — `_estimand_rule`,
`_prose_rule`, `_sourcing_rule`, `cited_total`, `claims_corrected`. **Nobody wrote down
what a complete object contains**, so each generation carried what its author needed and
the shape drifted in both directions at once.

**This is not degradation and it is not carelessness.** It is the absent-registry problem
one layer down from where the artefact manifest solved it: **a schema with no declared
version drifts, and the drift is invisible because every individual object is valid.**

Two consequences already measured:

- **The sibling-field check cannot work without a generation key.** A 60% cut across 28
  members produced a 39-field "norm" no recent object meets, flagging **14 objects when 3
  were real**. Scoping on the `built` date failed — every object reads `2026-08`. **The
  real generation signal is the schema richness itself, which means the fix is a different
  design, not a different field.** It remains broken and is reported as such.
- **Eleven closures built by one script carried `registered_primaries`; six composed by
  hand did not.** Same session, same purpose. **A machine composing from one path cannot
  forget a field; a person composing individually omits whatever is not load-bearing for
  the argument in front of them.** Relevance-driven omission — it feels like judgement
  while it happens.

---

## The codebase supplies its own conventions, and following them has been right twice

**Absence.** The generator renders `"not stated"` rather than a zero, and its comment says
why: *"a zero is a claim."* When a verdict-only topic needed a measure it does not have,
the answer was that same idiom — `"not applicable"` — not a borrowed sibling value.

**Control.** `build_app_v2.py` is documented as *"the FLAT control — emits the pre-tab
layout byte-identically, which is what every A/B is measured against."* An A/B harness
existed before we arrived; we nearly built verification of our own.

**The rule: when the codebase already has a convention for the situation you are in,
follow it rather than invent one.** Three rounds this week were spent rediscovering
conventions that were already there and readable — the tabbed projector named in
`STATUS.md`, `projectors.py` named in ARNI's own CSS, the generating commit named in its
build stamp.

---

## The most transferable finding: a written rule has never prevented a recurrence here

Four rules became mechanical this week — **staging paths, pipeline exit status, encoding
defaults, subprocess decoding.** Every one was built **only after prose had failed on it
repeatedly**: `text=True` three times, `$?`-through-a-pipe ten times, `git add -A` once
immediately after being written down.

**Three of the four have already caught something.** The pipeline-status ratchet earned
itself on its first real use, reporting `BUILT=0 FAILED=57` where the old form would have
said success — the identical shape that had reported six built pages that did not exist.

**In this project, a written rule has never prevented a recurrence, and a refusing check
has prevented one every time it existed.**

That is the same argument as *"a check that cannot fail is not a check"*, arriving from the
enforcement side rather than the measurement side — and it generalises well beyond this
corpus.

**With one honest limit.** Every guard built this week has an environment-variable escape
except one, and the one without an override is the only one that has stopped a defect we
would otherwise have shipped. **A guard for something that must never happen should not
have a hatch; if it needs one, that is evidence it is checking the wrong thing.**
