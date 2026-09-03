# FINDING 0 — the served headline came from a fit this page does not carry

**Status:** MEASURED. Confirmed from the served bytes, not from source.
**Date:** 2026-09-03.
**Page:** `HFREF_NMA_AUTO_FULL_REVIEW.html`.

This file exists because the identification below was held only in a session transcript,
and a finding that lives only in a transcript is one detached drive away from never having
happened. Everything here is re-derivable from the bytes named in it.

---

## The emitter, by file and line

```
scripts/hfref_relabel_and_strip_2026_08_28.py
    the RELABEL constant, lines 67-96

    line 72   the headline    RR 0.8619 (0.6915 to 1.0743)
    line 82   ACEI            0.8619 (0.6915 to 1.0743)
    line 84   ACEI+MRA        0.6985 (0.5060 to 0.9641)
    line 85   ACEI+BB         0.6393 (0.4831 to 0.8460)
    line 86   ARNI+BB         0.5476 (0.3623 to 0.8278)
    line 87   ACEI+BB+MRA     0.5181 (0.3594 to 0.7469)
    line 88   +SGLT2i         0.4588 (0.2956 to 0.7121)
```

Every one of those seven values is a **string literal** in the emitter. Nothing in that file
reads the page's own model object. The block was written on 2026-08-28 in commit `e3056de3f`,
whose message sources the vector to `multiverse-lookup.json` — a file present **at no path in
this repository**.

> ## THE SERVED HEADLINE WAS NEVER COMPUTED FROM ANYTHING WE HOLD. IT WAS TRANSCRIBED FROM A FILE THAT DOES NOT EXIST.

**This is not staleness.** Staleness implies the numbers were once right for some fit we can
name. These are **unsourced literals**, and the fact that they *look* like a plausible netmeta
output is the whole hazard — a reader, and every check that reads prose, sees six well-formed
estimates with plausible intervals in plausible rank order. **`ACEI+BB+MRA` is significant as a
string literal and not significant in the object below it.** That converts this from a
synchronisation bug into a **provenance void**: there is no artefact in this repository from
which the served numbers can be recomputed, checked, or defended, and the block asserted
otherwise in prose.

## What was measured, and how

The page was fetched from the deploy that serves it:

```
https://mahmood726-cyber.github.io/rapidmeta-finerenone/HFREF_NMA_AUTO_FULL_REVIEW.html
    938949 bytes
    sha256 06344a4fdec6b545553b4bed28860a94921886699bdd8d370d397d7c8dd2fc44
```

That is **byte-identical** to the file at `origin/main` `852b0478e`. The defect was live, not a
stale local tree.

The page renders six node-versus-placebo values in prose and separately embeds the fit they
claim to come from, in `<script id="hfref-fit-data" type="application/json">`. They disagree:

| node | SERVED PROSE | EMBEDDED `cells[tier=PRIMARY]` OURS-STRICT | point Δ |
|---|---|---|---|
| ACEI | 0.8619 (0.6915 to 1.0743) | 0.8937 (0.6252 to 1.2774) | +3.69% |
| ACEI+MRA | 0.6985 (0.5060 to 0.9641) | 0.6727 (0.4012 to 1.1279) | −3.69% **flips** |
| ACEI+BB | 0.6393 (0.4831 to 0.8460) | 0.6446 (0.4331 to 0.9593) | +0.83% |
| ARNI+BB | 0.5476 (0.3623 to 0.8278) | 0.5793 (0.3573 to 0.9391) | +5.78% |
| ACEI+BB+MRA | 0.5181 (0.3594 to 0.7469) | 0.5933 (0.3483 to 1.0109) | +14.52% **flips** |
| +SGLT2i | 0.4588 (0.2956 to 0.7121) | 0.5257 (0.2885 to 0.9580) | +14.58% |

**This is not rounding.** Two nodes are significant as served and do not exclude 1 on the fit
the page carries. The external review named `ACEI+BB+MRA` (served upper bound 0.7469 against a
stored 1.0109). **`ACEI+MRA` is a second instance, found by measurement and not reported**
(served 0.9641 against a stored 1.1279).

## Three independent confirmations, none needing an external source

1. **The page's own anchor refutes its own prose.** The embedded object carries
   `anchor.passed = true`, asserting
   `ACEI+BB = 0.64459765339 (0.43311383501, 0.95934625305)` and
   `ACEI+BB+MRA = 0.59333494564 (0.34826519892, 1.010857125)`.
   The prose beside it printed `0.6393` and `0.5181`.

2. **No cell on the page produces the served vector.** All four stored cells were checked:

   | cell | tier | tau2 | trials | ACEI |
   |---|---|---|---|---|
   | OURS-STRICT | PRIMARY | 0.023236089546 | 28 | 0.8937 |
   | OURS-INCLUSIVE | SENSITIVITY | 0.023796836474 | 31 | 0.8677 |
   | OURS-STRICT-7b | BRANCH | 0.024786314333 | 27 | 0.8856 |
   | OURS-STRICT-7c | BRANCH | 0.025658042059 | 26 | 0.8856 |

   `0.8619` is none of them.

3. **The live DOM printed both numbers to the same reader.** Loaded from the served URL on
   2026-09-03, a JS-rendered table titled *"All 14 nodes vs placebo"* carries
   `ACEI 0.894 (0.625–1.277)`, `ACEI+BB+MRA 0.593 (0.348–1.011)`, `+SGLT2i 0.526 (0.288–0.958)`
   — the embedded object's own values — roughly one screen below the static prose printing
   `0.8619`, `0.5181` and `0.4588` for the same three quantities. **One page served two
   different numbers for the same quantity, both visible, without opening any file.**

## Why it survived six days: a sentence that asserted its own provenance

The block rendered:

> "All six read from the stored node vector and mapped to the fit's own `head6` label array,
> not restated from memory: the vector has ten slots matching ten `contenders`, and slot 0 is
> ACEI."

**MEASURED: the token `head6` occurred EXACTLY ONCE in the 938949 served bytes — inside that
sentence.** There is no `head6` array on the page or anywhere in this repository. The sentence
describes an out-of-repository lookup file as though it were the page's own object.

**A SENTENCE ASSERTING PROVENANCE IS NOT PROVENANCE.** It reads as though the check had already
been done, which is precisely why nobody did it.

## The refusal that was recorded and not acted on

`scripts/check_cross_surface_consistency.py` had already looked at this page.
`out/card_vs_object_2026_08_28.json` records `n_pages 26`, `agree 24`, and this page in **two
refusal lists at once**:

```
"no_object":        {"page": "HFREF_NMA_AUTO_FULL_REVIEW.html",
                     "reason": "absent_from_PAGE_MAP"}
"unparseable_card": {"page": "HFREF_NMA_AUTO_FULL_REVIEW.html",
                     "pub": "ACEI versus Placebo for all-cause mortality -- RR 0.8619
                             (0.6915 to 1.0743) ...",
                     "reason": "pub_pattern_not_matched"}
```

The existing check held the wrong number in its hand and could not compare it, because this page
keeps its model object **embedded** rather than in `ssot/PAGE_MAP.json`. It said so honestly and
nothing consumed the saying.

## What was landed

1. `scripts/hfref_headline_regenerate_from_object_2026_09_03.py` rebuilds the block with values
   **read from the embedded object at run time**. No estimate in the emitted block is a literal.
   Planted both ways: 6 of 6 stale literals asserted present before and absent from the claim
   positions after; 6 of 6 regenerated values asserted present after; the false `head6` token
   asserted absent (page-wide count 1 → 0).
2. The block now carries a dated correction naming the old vector, the two flipped verdicts, and
   the fact that it regenerates from none of the four stored cells.
3. `scripts/gate_rendered_regenerates_from_embedded_object.py` — a new oracle-free detector.
   Where a page carries **both** a rendered estimate **and** an embedded object storing it under
   the same label, the two are one claim written twice: no estimator, no subset search, no
   tolerance beyond the rendered precision.

## Corpus sweep — reach stated as reach, never as coverage

Denominator: **every `*.html` at the repository root, named by glob, 1464 files.**

| state | n | meaning |
|---|---|---|
| ok | 1 | `HFREF_NMA_AUTO_FULL_REVIEW.html`, 6 labels compared, all agree after the fix |
| FAILED | 0 | — |
| NOT_RENDERED | 1 | `FINERENONE_ARTS_DN_DOSE_RESP_REVIEW.html`: 8 stored estimates, none printed in a findable form |
| NO_LABELLED | 15 | object stores per-arm inputs only; nothing to contradict |
| NO_OBJECT | 1447 | page embeds no `application/json` block |

**CHECKED = 1 of 1464.** `NO_OBJECT`, `NO_LABELLED` and `NOT_RENDERED` are **not passes** — they
are this gate's reach running out, counted so the reach cannot read as coverage. The corpus keeps
almost all of its model objects outside the page; that is the gate's limit today.

### And the gate's reach *within* a checked page is 3.70%

| surface | size |
|---|---|
| static text the gate reads (tags stripped, script/style removed) | 21,072 chars |
| text a browser renders (`document.body.textContent`, script/style removed) | 568,879 chars |

It caught this defect because this defect happened to be static. On this page the JS-rendered
surface is the **correct** one. Comparing prose against the embedded object is equivalent to
comparing it against the JS table, because the table is built from the object — which is why a
3.70% gate is useful here, and it is still 3.70%.

## Controls, planted both ways

Selftest **9 of 9**:

- the real 2026-09-03 vector against the real object must **FAIL**
- the fix must pass
- two-decimal rounding must pass (rounding is not a defect)
- `ACEI` must not be scored against `ACEI+MRA`'s triple (prefix labels)
- en-dash intervals read as "to"
- a page with no object is UNCHECKED, not clean
- an inputs-only object is `NO_LABELLED`
- an unprinted estimate is `NOT_RENDERED`, not ok
- a value inside `<script>` is not rendered text

Run against the **real** pre-fix page from git it reports FAILED on all 6 nodes and marks the 2
that change the verdict — so the control is the historical artefact, not only a fixture.

## Wiring

Registered in `gates/WIRED_REPO_CHECKS.json` `pre_push` (25 entries, 6.9s measured) **and named
by two explicit steps in `.github/workflows/hook-chain.yml`** — the selftest first, then the
corpus run. `gates/gate8_caller_and_wiring.py` refused the first push because the JSON registry
is read at run time and its caller scan cannot see it: *"a gate written and left inert."* That
was correct and was fixed by wiring, not by widening gate8.

## What this does NOT establish, written in advance

- **NOT** that the embedded object is correct. The page now says what its own stored fit says.
  Whether that fit should exist in this shape is Findings 1–10 of the external review and is a
  rebuild, not a repair.
- **NOT** that an agreeing page is correct. The object can store the wrong trials, the wrong arms
  or the wrong estimand and the prose will agree with it perfectly.
- **NOT** that pages with no embedded object are clean. They are UNCHECKED, and the table above
  names them rather than omitting them.
- The netmeta fitting code is untouched.
