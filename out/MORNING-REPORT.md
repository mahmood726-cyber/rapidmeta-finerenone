# Overnight gated pass — where it actually stands

**Lane:** `lane/per-page-2026-08-28` in `F:/fixwt/live`. **Base:** `origin/main` `e3a9c964b`.
**Nothing is pushed.** Everything below is committed on the lane branch and needs a merge decision.

---

## SHIPPED — landed, gates green, verified at served bytes

Three class-wide changes. Each has a gate7-derived radius acknowledged *before* the edit, a
plant that watched the defect return, a full 8-gate pass, and a served-bytes marker that did
not exist in the corpus beforehand.

| # | commit | class | file radius | behaviour | indexed pages touched |
|---|---|---|---|---|---|
| 1 | `269aa7051` | render recovered evidence (4 trials, in their own words) | 155 | 1 | 0 of 29 |
| 2 | `9e32a702b` | four pages concluded no trial exists when nothing recorded a search | 6 | 4 | 0 of 29 |
| 3 | `f3eed0702` | forest caption counted the object's rows, not the plot's | 155 | 1 | 0 of 29 |
| 4 | `6279e4885` | leave-one-out sentence counted every sensitivity row and read none | 5 | 2 | 2 of 29 |

**SERVED: 0.** All four are generator changes. They reach a reader only when the rebuild lane
rebuilds those pages. `fixed` is not `served` and this report will not blur them.

---

## HELD — investigated, not landed, with the reason

Seven class-wide items remain investigated and ready to decide, in `out/cw/ALL.json`: exact site,
gate7 radius, kinds in the behaviour set, intersection with the 29 indexed pages, a proposed
patch, three states where the defect is a two-state answer, a verified-absent marker, and
whether the *obvious* one-line fix would actually fire.

**Two are held specifically because of what they touch:**

- **GRADE certainty resolver** (`ssot/grade_authority.py`) — touches **19 of the 29 indexed
  pages**. That is the largest indexed blast radius in the queue and it deserves a rested
  reader, not a night shift.
- **`ceftazidime-avibactam` canonical-store note** — its site is `ssot/build_tabbed.py`, the
  real build entry point, radius 155, touching **27 of 29 indexed pages**. Held by instruction:
  `build_tabbed.py` is taken last and a per-page plant does not measure it.

**Also held:** `L2` (the screening-table suppression, same file), and `L5` — a one-off script,
`rerun_bookkeeping_with_lead_ins_2026_08_23.py:140`, which clears its own quarantine directory
before re-populating it, destroying the previous run's safety copy. Low severity, owned
elsewhere, escalated rather than fixed.

---

## WHAT WENT WRONG TONIGHT, IN MY OWN WORK

Recorded because the failures are more useful than the successes.

1. **I wrote an HTML entity into a caption** that is escaped downstream, so the page served the
   literal `&amp;mdash;`. The marker was present and the output was still wrong. **A marker
   proves a branch fired, never that what it produced is right.**
2. **My first plant probe could not match the defect it was testing for** — a `[^.]` class that
   stopped at a period. The re-planted defect reported as absent, and the plant would have
   "passed" while proving nothing.
3. **Byte-identity was the wrong restoration test** for a page carrying rasterised figures.
   Established rather than assumed: two builds from identical source *are* byte-identical, so
   the build is deterministic, but an intervening build regenerates `figs/`. Restoration is now
   proven on rendered-text hash.
4. **My blast-radius estimate was wrong by an order of magnitude** earlier in the run — I
   reported 15 where gate7 derives 155. A behaviour-change count is not a radius, and the
   smaller number is the reassuring one.

---

## CLASS 4 IS THE ONE THAT CHANGED AN INDEXED PAGE, AND IT IMPROVED TWO

Two pages were asserting robustness results they had not computed. `tigecycline-ciai` counted
all eight sensitivity rows when only three remove a study, and none carries an exclusion
verdict, so it printed "no refit excludes no difference" while its own table showed one that
does. `apixaban-vte-treatment` made the same definite claim from three rows holding a trial
name and nothing else -- no verdict, no interval, no result. Both are in the indexed 29 and
both now say something true; ARNI, BOCOCIZUMAB x2 and INCLISIRAN were verified unchanged.

The obvious one-line fix would have fixed one page and silently deleted a true sentence from
twelve, because only 1 of 13 page-outcomes uses the `leave-out` id convention and 12 use a
legacy `omitted` field.

---

## THE GRADE CLASS IS REFUSED, AND THAT IS THE MAIN RESULT OF THE NIGHT

I was authorised to stage it three pages at a time. **I landed none, because the finding is
wrong and the resolver is right.**

`_rob_state(sotagliflozin-hf)` computes `dual=true, adjudicated=false, n_assessors=2` — two
assessors read every contributing result and **nobody adjudicated the disagreement**. Two of the
three outcomes are assessed but unadjudicated; the third, `mace3_first`, **is not in
`outcomes_assessed` at all**. Each stored `grade.certainty` is `low`, and risk of bias is one of
the five domains that produced it. Publishing the level asserts that derivation is settled when
its input is not. The resolver says so itself: *"PENDING outranks RATED, and only RATED … it is
precisely the case where a level EXISTS and may not yet be published."*

**The abort condition was met before the first page was touched** — the change would move 19
indexed pages from PENDING to a published level, and the stored fields say the risk-of-bias
domain behind that level is contested. The proposed patch also had no exclusion for frozen
`gepotidacin`, which is 1 of its 20 behaviour pages.

**The real defect is the bookkeeping sentence**, which claims "grade per pool" is held. The
object holds a *level*; a level whose risk-of-bias input is unresolved is not a published
per-pool GRADE. Correct the sentence, not the resolver.

**The asymmetry is the argument.** If I am wrong, 19 indexed pages keep showing PENDING with a
stated reason — a page that under-claims and explains why. If I am right and it had landed, 19
indexed pages would publish a certainty rating resting on an unadjudicated risk-of-bias domain,
and one on an outcome never assessed at all. Recorded as `L6` in `out/ESCALATIONS_LANE.jsonl`.

Whether a GRADE certainty may be shown while its RoB domain is unadjudicated is a
**methodological ruling, not a code fix**, and it needs to be Mahmood's.
