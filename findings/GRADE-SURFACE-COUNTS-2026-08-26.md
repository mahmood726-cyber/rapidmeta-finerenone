# `grade_authority` claims every surface resolves through it. 19 of 141 topics do not.

Measured 2026-08-26 at `ssot-shell a87f10342`, over the **141 in-scope cardiology and
infectious-disease stores**. Committed because a falsified claim in a docstring stays true
to the next reader until someone can point at the number.

## The claim

`ssot/grade_authority.py:11` states that every surface now calls `resolve()`. It does not.
`paper_projector.py` has zero references to it and reads a different home from
`projectors2.py`:

* `projectors2.grade_section` reads **nested** `results.by_outcome.<oid>.grade`
* `paper_projector.py:2032` reads **top-level** `grade.by_outcome.<oid>`

## The counts

| | topics |
|---|---|
| no GRADE anywhere | 117 |
| **top-level only** — the paper tab rates it, the review page shows nothing | **18** |
| **nested only** — the review page rates it, the paper tab shows nothing | **1** (`sotagliflozin-hf`) |
| both homes populated | 3 |
| no store | 2 |

**19 of 141 topics are rated on exactly one surface.** A reader sees a certainty rating or
no rating depending on which tab they open.

Of the 3 populating both, **2 diverge in coverage**:

* `iv-iron-hf` — `hierarchical_primary` and `six_min_walk_24w` rated on the review page only.
* `sglt2-hf` — `cvdeath_or_whf_first` rated on the review page only; `harmonised_cvdeath_or_hhf`
  and `threecomp_cvdeath_hhf_urgent` rated on the paper tab only.

## The good news, which is the shape of the defect

**No outcome anywhere carries two different certainty values.** Where both surfaces rate the
same outcome, they agree. The divergence is *which outcomes get rated*, never *what rating
they get*.

That makes this a plumbing defect rather than an evidence defect — two readers of one store,
not two judgements about one body of evidence. It is a much cheaper thing to be, and it is
fixed by making both surfaces read the same home rather than by re-adjudicating anything.

## Method

Nested ratings read from `results.by_outcome.*.grade.certainty`; top-level from
`grade.by_outcome.*.certainty`. Both normalised for case and whitespace before comparison.
Structural, not phrase-keyed: the result does not depend on any wording and survives the
corpus rewording its own prose.
