# Two read failures, measured across all 135 objects

Both found while taking `apixaban-vte` to the standard. Neither is a wrong stored value: in both
cases **the object is right and the instrument reading it is wrong**, which is the night's
central finding continuing into the morning.

Both are in the **withholding** direction. Neither is visible to any detector now in
`.githooks/pre-commit`, and the reason each is invisible is stated rather than left to be
rediscovered.

---

## 1. `arms_as_registered` — 41 objects report "no readable arms" while carrying complete arm data

`ssot/preconditions.py` reads `inputs.trials[].arms`. **41 of 135 objects store their arm data
under `inputs.trials[].arms_as_registered` instead**, and carry nothing at `arms`.

```
objects with arm data ONLY under the alternate key      41 of 135
arm records held there                                 247
   ...carrying a registry `type` (EXPERIMENTAL, ...)   198
   ...with no type at all                               49
```

So on those 41 objects, two preconditions return `NOT_ASSESSABLE`:

```
arm_role_resolved                  NOT-ASSESSABLE
    "cannot assess: inputs.trials has 2 trial(s) with no readable arms ['NCT02366871',
     'NCT02829957'] and 0 with a blank arm role"
contributes_a_randomised_contrast  NOT-ASSESSABLE
    "cannot assess: 2 of 2 trial(s) carry no readable arm roles"
```

and `bosentan-pah` — **third in the build queue** — carries this, in full, with types:

```json
NCT00303459  [{"type": "EXPERIMENTAL",       "label": "A", "interventions": "Drug: bosentan"},
              {"type": "PLACEBO_COMPARATOR", "label": "B", "interventions": "Drug: placebo"}]
```

> **THE REASON IS TRUE AND THE VERDICT IS A READ FAILURE.** `arms` really is absent. The arm
> data is not.

### Why `lint_restraint.py` cannot see it

E4's Lane 2 catches "a precondition returns NOT_ASSESSABLE citing absence while **the field it
names** is present and non-empty". Here the field it names is genuinely absent — the data is
under a *different name*. The lane tests the cited field, so a **schema drift** slips straight
through a check built for a **read** failure. The two are indistinguishable from the outside and
completely different underneath.

### Why this is not fixed in the same breath as being reported

The two keys are not a rename, they are **two vocabularies**:

```
arms[].role               treatment / control          (this project's vocabulary)
arms_as_registered[].type EXPERIMENTAL / ACTIVE_COMPARATOR / PLACEBO_COMPARATOR   (the registry's)
```

Making the precondition read the second means mapping registry types to project roles — and
`ssot/topic_identity.locate()` exists precisely because **that mapping is not literal**:
AFFIRM-AHF and HEART-FID type their active arm ACTIVE_COMPARATOR, ADVANCE-2 and ADVANCE-3 type
one design in opposite directions. A literal map would import exactly the defect `locate()` was
written to fix.

It would also **change 41 topics' precondition verdicts at once**. That is a corpus-wide
restatement and it deserves its own pass, with old and new side by side, rather than being
folded into a topic build. Recorded here with its measurement so it cannot quietly become
"the preconditions were not assessable on those".

**49 of the 247 arm records carry no type**, so even after the fix a genuine `NOT_ASSESSABLE`
remains for some — which is the correct outcome and is stated now, before the fix, so the
improvement cannot later be overstated.

---

## 2. The question is the object's own verdict — 58 of 135

`population_stated` returns **PASS** on `apixaban-vte`, whose `question` reads:

```
"Apixaban Vte: NOT POOLABLE AS POSED -- the COMPARATOR and PARTICIPANTS and OUTCOME limb
 fails on each trial's own registered primary outcome?"
```

That is the object's **verdict**, generator-composed from `title` and `which_limb_fails`, with a
question mark appended. Counted across the corpus:

```
objects whose `question` is the object's own verdict     58 of 135
```

`scripts/lint_question_is_a_question.py` is **correctly silent** on all 58. It compares the
question against the registry text of the object's own trials, and this string appears in no
registry record — it was generated here. The check is not broken; it was built against the
shape that had been found.

> A check written against the shape that was found does not see the shape that was not. The
> ablation-af instance was **one trial's endpoint, truncated**; this is **the object's own
> conclusion**; both fail the same property, which is *is there a stated question to audit
> against*.

### What this costs, concretely

A question decides the included set. Where the question is a verdict:

- there are no criteria to screen a remainder against, so **the remainder cannot be screened**;
- `criteria_stated`, `criteria_predefined` and `eligibility_met` all return `NOT_ASSESSABLE`,
  correctly, and the topic cannot reach P3 of the page standard;
- `population_stated` nonetheless reads **PASS**, so a summary counting passed preconditions
  reports the topic as healthier than it is.

### The detector this needs, named rather than implied

It is mechanically buildable and is **not built**: flag a `question` that contains the object's
own `topic_state`, `which_limb_fails`, or a normalised form of its `title`. It needs a baseline
of 58 and a ratchet, on the same terms as the existing check — and the baseline must be **named,
not counted**, for the reason recorded in `lint_question_is_a_question.py` this morning.

Not built today, and listed as an exposure rather than as future work, because "we wrote it
down" is the status DEFECT-REGISTRY.md exists to refuse.

---

## What both have in common

Neither is a wrong number. Both are an instrument reporting **absence** where the object holds
the thing — once because it looked under a different key, once because it accepted any non-empty
string as the property its name claims.

> Every check in this repository should be read against the gap between the property CLAIMED and
> the property VERIFIED. Two more instances of that gap, at 41 and 58 objects out of 135.

*Measured 2026-08-19. Every count above is an observed output, reproducible from `ssot/**/*.json`.*
