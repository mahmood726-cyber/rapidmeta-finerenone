# What a check's evidence is worth, and the 27 split before it settled

2026-08-18. Written because three results tonight look alike on a summary line and are
worth completely different amounts.

---

## The two bounded classes

**Check 1 confirmed an absence.** It ran, it returned zero, and zero was the right
answer. That is a real result and it is nearly worthless as evidence about the
instrument, because *a check that can only return zero is indistinguishable from a check
that does not run.* Nothing in its output separates "I looked and there was nothing"
from "I did not look", and no amount of re-running it changes that.

**The subject-role gate had to find four things and found exactly the four.** It flagged
`fidaxomicin-cdi`, `fidaxomicin-cdiff`, `fondaparinux-vte` and `olmesartan-htn` — every
topic already closed on comparator-as-subject grounds, and no others. It could have
returned zero. It could have returned forty. It returned the four whose answers were
independently known.

**The second is far stronger evidence, and the asymmetry is the point.** The first
result is consistent with a broken instrument. The second is not: a gate that returns
the known answer set on a population where the answer set is known has demonstrated it
can see. It is the first gate this week to earn trust *at introduction* rather than after
misfiring and being corrected.

The practical rule: **when introducing a check, point it first at a population whose
answer you already know.** A green light on unknown territory tells you nothing about the
light.

---

## The third instance, which cuts the other way

`CHK017_DUP1_BIT_EQUALITY` had a founding case and fired on it, which by the rule above
should count as earned trust. It does not, and the reason completes the pattern.

The check asserted that "two distinct trials cannot agree to 16 significant digits" and
called this "a PROOF, not an inference." **Its own founding value, `-0.15082288973458366`,
is bit-identical to `math.log(0.86)`.** The sixteen digits are manufactured by `math.log`
out of a two-decimal published hazard ratio. Every trial reporting 0.86 produces that
exact float. The check was reading the precision of the float and calling it the
precision of the estimate.

So it fired on its founding case *for a reason that was not the stated one* — the case
happened to also carry the genuine proof (pooled bit-identical to the entry), which sat
in the code as an appended sentence on a verdict already reached without it.

Tonight it blocked a push over `sglt2-hf`, where DAPA-HF posts HR 0.75 (0.65–0.85) for CV
death or heart-failure hospitalisation and EMPEROR-Reduced posts 0.75 (0.65–0.86). Both
verified against posted registry results today. Two trials, two intervals, one
two-decimal number. Among three entries in a plausible ratio band, that collision occurs
**about 8% of the time by chance alone** — more in practice, because effect sizes cluster.

**A check firing on its founding case proves the check fires. It does not prove the
stated reason is the operative one.** Which extends the rule above: a known-answer
population demonstrates the instrument can see, and still does not establish *what it is
seeing by*.

The correction requires the arithmetic proof — pooling two distinct values cannot return
either one exactly — or a shared value beyond any publishable precision. The founding case
still fails, on the first. Narrower in what it asserts; not weaker in what it catches.

### And I reproduced the same error inside the fix

The mutation I wrote to prove the corrected check still depended on `entries` used the
value `-0.1984512345678901`, which sits 3e-7 from `log(0.82)`. The corrected check read it
as published precision, returned PASS, and **CHK017 went vacuous on thirteen real
artefacts.** Caught by the gate's mutation test, not by me — one commit after writing the
paragraph explaining exactly this trap.

---

## `CHK024`: 115 emissions, 115 passes, nothing adjudicated

The same family, at corpus scale. `CHK024_FALSE_METHOD_CLAIM` decides something only when
the claimed method is a network meta-analysis — it asks whether the object holds a network
to support the claim. **Every artefact in this corpus claims `pairwise`.** So it fell
through to an unconditional PASS 115 times, and every one was counted as coverage.

**The gate did not start failing because tonight's work was worse.** The vacuity was
always there; fifteen new artefacts pushed the INVALID share past the 50% ceiling and made
it visible. A defect that only surfaces when its population grows was never a new defect.

Fixed at the projection, so it now emits nothing here. **Zero results from an inapplicable
check is coverage of zero, stated. One hundred and fifteen passes is coverage of zero,
concealed** — and the second is worse, because it reads as verification.

---

## The 27 unassessable, split by cause

Split before the number settled, because "27 unassessable" reads as one backlog and is
five populations with five different answers.

**My proposed three-way split was wrong.** I expected combination products, class-named
topics, and brand-versus-molecule. Combination products cause nothing here. The largest
cause I did not propose at all.

| Cause | n | Resolvable? |
|---|---|---|
| **Development code** — registry names the arm by the sponsor's compound code | 10 | **3 of 10, measured** |
| **Token is not a drug** — disease, population or anatomy | 6 | Gate's own bug |
| **Class or target name** — topic asks class-level, arms name molecules | 6 | Needs a curated map + a scope decision |
| **Tokenisation** — `ser109` against the registry's `ser-109` | 1 | Free |
| **No arm typed EXPERIMENTAL** — the RE-LY shape | 4 | Not at all; the field is empty at source |

**Development code** is the big one: bamlanivimab is LY3819253, bezlotoxumab is MK-3415A,
nirsevimab is MEDI8897, sacubitril/valsartan is LCZ696, Prevnar-15 is V114. The topic is
named for the drug the world calls it; the registration for the compound the sponsor
filed. `interventions[].otherNames` carries the mapping for **3 of the 10** — measured
against the real seeded registrations, not asserted. For the other 7 the registry simply
never records the approved name, so a curated code→name map is the only route. *Partly
resolvable* stated as a number rather than as a promise.

**The second group matters most and is the least comfortable.** Six of the 27 are my
instrument misfiring: `subject_of()` takes the first hyphen-separated word and calls it a
drug, and the exclusion list was written from the topics I happened to look at. They are
not unassessable — they are **out of scope**, which is a different claim. Left as a
number they would have read as evidence the corpus resists checking, when they are
evidence the gate over-reached.

---

## Delivery, gated

**115 of 116.** The fifteen new infectious-disease verdict pages were built, pushed, and
verified live against their objects' own verdict text — 15 OK, 0 stale, 0 content failures.

The one outstanding remains `PREVNAR15_PNEUMO`, a confirmed content failure with an open
generator question.

Split by kind: **15 estimates, 100 sourced verdicts.** The ratio is not a failure rate — a
verdict established from the registrations is a complete outcome, and tonight fifteen
topics reached one.
