# The legacy-provenance migration is not performable, and the schema has no state for it

**Status:** MEASURED, by running the validator and the registry, not by reading the code.
**Date:** 2026-09-03.
**Blocks:** any push to `main` from a clone with `core.hooksPath=.githooks` armed, via
`.githooks/pre-push` → `scripts/gate_stored_estimate_declares_provenance_2026_08_27.py`.

## The seven rows, named

All seven carry the identical string `'REGISTRY -- ClinicalTrials.gov posted results'`:

```
apixaban-vte-prophylaxis|results.by_outcome.major_bleeding.per_trial[0]   NCT00457002  2.5259
apixaban-vte-prophylaxis|results.by_outcome.major_bleeding.per_trial[1]   NCT00423319  1.2158
apixaban-vte-prophylaxis|results.by_outcome.major_bleeding.per_trial[2]   NCT00371683  0.4975
apixaban-vte-prophylaxis|results.by_outcome.major_bleeding.per_trial[3]   NCT00452530  0.6459
apixaban-vte-treatment  |results.by_outcome.major_bleeding.per_trial[0]   NCT03266783  0.1574
apixaban-vte-treatment  |results.by_outcome.major_bleeding.per_trial[1]   NCT01780987  0.1950
apixaban-vte-treatment  |results.by_outcome.major_bleeding.per_trial[2]   NCT02829957  0.7273
```

They are NEW against `scripts/baselines/estimate_provenance_baseline.json`, which holds 313
rows and is **byte-identical at `852b0478e` and at current `origin/main`**. The baselined
apixaban rows are for `major_vte` and `recurrent_vte`; `major_bleeding` was added to both
objects after the freeze, bringing these seven with it. So the ratchet is behaving correctly:
the count rose.

## Reason 1 — the conversion does not clear the gate. Measured, not argued.

`ssot/provenance_tier.py::TIERS["REGISTRY_POSTED_RESULT"]` requires
`("registry", "accessed_utc", "table", "row_identifier")`. The string supplies `registry` and
nothing else. Running `provenance_tier.validate` on the candidate blocks:

| candidate block | `validate` returns |
|---|---|
| `tier=REGISTRY_POSTED_RESULT` + `registry` + the verbatim legacy string kept | **3 problems**: `accessed_utc`, `table`, `row_identifier` empty |
| `tier=REGISTRY_POSTED_RESULT` + `registry` only | **3 problems**, same |
| `tier=COULD_NOT_DETERMINE` | valid — gate accepts |
| `tier=NOT_YET_RECORDED` | valid — gate accepts |
| the legacy string, as it stands today | 1 problem: legacy STRING, declares no tier |

**A faithful conversion does not pass. The two that pass are not faithful.**
`NOT_YET_RECORDED` asserts nobody looked — false, someone looked and wrote a sentence.
`COULD_NOT_DETERMINE` asserts someone looked and failed — also false. Either would be a
statement about who did what, inserted to clear a gate.

## Reason 2 — the schema's author already ruled against inferring the tier, in code

`validate`, at the legacy-string branch, verbatim:

> *"It gets its own state rather than being crashed on, silently accepted, or promoted.
> Promoting it would be the exact defect this schema exists to prevent — a string containing
> the word "registry" is not evidence that the number came from a posted results table, and 43
> rows would have been upgraded on a substring match."*

and the message it returns ends: *"Migrate it to a tier block; do NOT infer the tier from the
words in the string."*

## Reason 3 — the honest path exists, and it stops at `row_identifier`

The string can be checked rather than trusted. All seven registrations were fetched from
ClinicalTrials.gov API v2 on 2026-09-03. **All seven post results, and all seven post a
major-bleeding outcome** — so the string is not false.

But `row_identifier` is not determined by it, because four of the seven post **more than one**
major-bleeding outcome:

| NCT | posted outcomes | bleeding/haemorrhage-titled | of which "major" |
|---|---|---|---|
| NCT00457002 | 32 | 6 | **4** |
| NCT00423319 | 14 | 5 | 1 |
| NCT00371683 | 24 | 4 | **3** |
| NCT00452530 | 7 | 2 | 1 |
| NCT03266783 | 10 | 3 | **2** |
| NCT01780987 | 6 | 3 | **2** |
| NCT02829957 | 9 | 2 | **2** |

Choosing which of four rows a stored number came from is precisely the judgement the
instruction forbids.

**Two of the seven can be pinned by reproduction, exactly:**

- `NCT00452530` → *"Rate of Major Bleeding, Clinically Relevant Nonmajor Bleeding (CRNM), and
  Major Bleeding or CRNM"*, class `Major bleeding (n=9, 14)`:
  (9/1501) ÷ (14/1508) = **0.6459**, against a stored 0.6459.
- `NCT03266783` → *"Number of Participants With Adjudicated Major Bleeding Events"*:
  Apixaban 5/1345 ÷ Rivaroxaban 32/1355 = **0.1574**, against a stored 0.1574.

**The other five are NOT_ASSESSABLE, which is not the same as "did not come from the
registry".** My reproducer found nothing for them, and my reproducer is **unvalidated** — it
had already missed `NCT02829957`'s *"Number of Participants With Major **Hemorrhage**"* because
its first pass searched for `bleed` and not for `h(a)?emorrhag`. An instrument with a known
miss and no measured error rate cannot be used to assert an absence.

## Verdict

**STOP.** Five of the seven are ambiguous, so the standing condition — *"if even one of the
seven is ambiguous, stop and report rather than deciding"* — is met five times over. The
correct repair is per-row tracing by whoever owns those pools: open each registration, name the
posted outcome row the value was read from, and record `accessed_utc`, `table` and
`row_identifier`. That is evidence work, not a schema conversion, and it touches another lane's
science.

## Two findings that fell out of this, recorded not acted on

**(a) The tier vocabulary has no state for a legacy string.** `validate` names them as their own
state in prose, and `TIERS` has no member for it. Across `ssot/*/*.json` — **161 store objects,
40 distinct legacy provenance strings, 95 rows** (27 of them on point-carrying estimates, which
is the gate's `(legacy string) 27`). They do not share a meaning: 20 rows say
`'REGISTRY -- ClinicalTrials.gov posted results'`; **12 rows say the opposite** — *"NOT SUPPLIED
BY THE REGISTRY. NCTxxxxx posts NO RESULTS SECTION… what did?"*; one says *"PUBLICATION ABSTRACT
— NOT the registry"*; 17 are an object-root sentence attached to no estimate; ~14 are
*"COMPARED AGAINST the posted outcome measure … Derived from a comparison that was run"*, which
sits between `REGISTRY_POSTED_RESULT` and `DERIVED_HERE`; and one, in
`sglt2-hf|.scope_decisions.…`, is *"Written after the trials were known. RETROSPECTIVE"* — not a
provenance at all, under a `provenance` key. **A single mapping cannot be exhaustive over that
set, and a mapping over the one string would falsify the twelve that deny it.**

**(b) The seven repo gates wired on 2026-08-31 are skipped on most pushes.**
`.githooks/pre-push` line 229 is `if [ -z "$CHANGED" ]; then … exit 0`, where `$CHANGED` is the
`*_REVIEW.html` pages in the push. The hook's own comment at lines 136–145 records this exact
defect and says *"ORDER IS LOAD-BEARING: THESE RUN BEFORE THE SCOPED EARLY EXIT"* — the nine
executable-rule gates and the 24 repo checks were moved above it. **The seven gates at line 431,
including this provenance gate, are still below it.** Measured here tonight: three pushes
carrying only scripts and markdown passed; the one push carrying a modified `*_REVIEW.html` was
refused by a gate that exits 1 deterministically on the same tree. **The fix was partial and the
same class recurred in the same file.** Not repaired here: repairing it would make this lane's
own pushes harder, which is exactly why it should be repaired by someone else.

**(c) Scope note, for the owning lane only.** `NCT02829957` is *RAMBLE — "Randomized Trial to
Test the Effect of Rivaroxaban or Apixaban on Menstrual Blood Loss in Women"*, **n=19**, and
`NCT03266783` is *"Comparison of Bleeding Risk Between Rivaroxaban and Apixaban"*. Both are
apixaban-versus-rivaroxaban; the prophylaxis rows are apixaban-versus-enoxaparin. Recorded
because it was seen, not assessed.
