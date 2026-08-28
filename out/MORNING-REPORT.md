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

**SERVED: 0.** All three are generator changes. They reach a reader only when the rebuild lane
rebuilds those pages. `fixed` is not `served` and this report will not blur them.

---

## HELD — investigated, not landed, with the reason

Nine class-wide items are investigated and ready to decide, in `out/cw/ALL.json`: exact site,
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

## THE ONE THING TO DECIDE FIRST

**The GRADE class touches 19 of 29 indexed pages.** Everything else in the queue touches 0 or 1.
If any single item is going to break the front page of the site, it is that one, and it should
be run with someone watching rather than merged on a green suite alone — a planted-error test
tonight returned **18 classes, 40 plants, zero detected**, and 14 classes have no instrument at
all. The plant and the marker are the entire safety net.
