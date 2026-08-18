# Delivery position, close of 2026-08-18

**This is the state, not the narrative.** A lane picking this up should be able to read
this file and know where everything stands.

---

## The number

**98 of 101 mapped topics deliver.** Verified mechanically against the **served** bytes,
one topic at a time, by a gate that refuses input it cannot evaluate.

**This morning the figure was 44 and nobody knew it.** Every count reported as progress
before today — "26 of 53", "47 of 62" — was counting **objects built**, which is a
different number and was never equal to this one.

## The split — and it is the corpus's actual character

| | n |
|---|---|
| publish a **pooled estimate**, values confirmed live | **15** |
| publish a **sourced verdict**, reason text confirmed live | **83** |
| **delivered** | **98** |
| open | 3 |

**Roughly one topic in seven publishes an estimate. Six in seven publish a reasoned
account of why a synthesis is not possible**, with the registrations read, the ranks
stated and the date recorded.

**That is the product.** Not a collection of meta-analyses with some gaps — **a
well-evidenced account of what cannot be synthesised, with a minority of cases where it
can.** Unusual, defensible, and now measured rather than assumed.

---

## The three open topics, each understood

| topic | state |
|---|---|
| **`PREVNAR15_PNEUMO`** | **CONFIRMED CONTENT FAILURE.** Four outcome blocks; none of their reasons reaches the page after a clean rebuild. The generator is not rendering `poolable_reason` for this object's block shape. A generator question, not an object or deploy one — established by reading the **built** file, not the served one. |
| `EVOLOCUMAB_MIXED_DYSLIPIDEMIA` | cleared earlier in the run; re-gate to confirm |
| `MITRAL_FUNCMR` | cleared earlier in the run; re-gate to confirm |

**No unknowns.** Every remaining item has a stated cause.

---

## What changed today at the level that matters

**The corpus can now answer "does this page reach a reader with content we have verified"
mechanically, for every mapped topic.** It could not this morning.

Two gates do it, and both **refuse input they cannot evaluate** rather than passing it:

- `scripts/content_gate.py` — asserts the object's pooled point, interval and I-squared
  appear as literal text in the served bytes; V2 markers absent; served byte count matches
  the built file, so a stale deploy cannot pass.
- `scripts/verdict_gate.py` — asserts the object's own recorded reason text appears on the
  page, so a page carrying **some other topic's** verdict fails.

Both distinguish **STALE DEPLOY (wait)** from **CONTENT MISSING (stop)** — those look
identical from outside and need opposite responses.

**The individual pages will be rebuilt many times. The ability to tell whether they worked
will not need building again.**

---

## Where the tools are

**Generators live in `ssot/`, not `scripts/`** — see `scripts/WHERE-THE-GENERATORS-LIVE.md`.
Four searches over four rounds concluded no generator existed because every one looked in
`scripts/`.

    python ssot/build_tabbed.py <object.json> <out.html>     # ~90s, rasterises via Chrome
    python scripts/content_gate.py <PAGE.html> <object.json> # pooled topics
    python scripts/verdict_gate.py <PAGE.html> <object.json> # verdict-only topics
    python scripts/consumer_derived_schema.py                # what the generator requires
    python scripts/text_match.py                             # the shared normaliser, 9/9

`ARTEFACT-MANIFEST.json` indexes 603 artefacts **by kind** — `generator`, `gate`, `screen`,
`library`, `document` — so "where are the generators" has an answer that does not depend on
guessing a directory.

---

## Queued, not started

- **Fifteen infectious-disease objects** — new topics, currently unopenable by a reader.
  They sit behind the same schema wall `AZILSARTAN` hit; run
  `consumer_derived_schema.py` first and fix each in one pass rather than one build cycle
  per defect.
- **Recovery candidates** — ~20 withdrawn topics where a shared outcome may exist at some
  rank. Three read so far: **all three withdrawals correct**, one recovered by correcting
  data. `SGLT2_HF` remains the single confirmed disproportionate remedy.
- **Two provenance mismatches** and `finerenone-review`'s per-trial entry with **no NCT** —
  identity before numbers.
- **Blinded cross-family reviews** — Codex found ARNI's internal contradiction, Gemini found
  the SGLT2 disproportion. Both found things a week of single-family review had not.
