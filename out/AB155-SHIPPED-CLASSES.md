# The 155-page check on the two classes shipped at an understated radius

**Method.** Arm A = HEAD with **only** `statement.py` and `projectors2.py` reverted to their
pre-change versions. Arm B = HEAD. Everything else held constant, so a difference is
attributable to those two files and nothing else. Rendered text, one output directory per
page so no two parallel builds race on `figs/`.

## Coverage, kinds before counts

| kind | n |
|---|---|
| topic objects | 155 |
| refused — *"no title and no results, so there is no paper to project"* | **14**, named in `out/ab155_A.json` |
| built in both arms, comparable | **141** |
| built in one arm only | 0 |

The 14 are a designed refusal on empty objects, not failures. They were never assessed either
way and are not counted as clean.

## `statement.py` — CORRECT. The acknowledgement was wrong; the change was not.

All **4** predicted pages moved, **0** unpredicted pages moved. `caspofungin-fungal`,
`emtricitabine-hiv`, `etesevimab-covid`, `men-acwy` each replaced *"…was identified for
[this] question"* with the honest *"no trial records are held on this object, and no search
record is held either."* Radius 155 was the right number to acknowledge and 6 was wrong, but
**nothing outside the 4 changed.** No action needed beyond the corrected acknowledgement.

## ⛔ `projectors2.py` — A LIVE DEFECT. One page fixed, one regressed from TRUE to FALSE, one unpredicted.

| outcome | before | after (shipped) | truth |
|---|---|---|---|
| `tigecycline-ciai` | "no refit excludes" ❌ | **"1 of 3 refits still exclude"** ✅ | 1 of 3 |
| `apixaban-vte-treatment` | **"no refit excludes"** ✅ | "cannot be read here" ❌ | **0 of 3** |
| `malaria-vaccines` ×2 | "0 of 2 single-trial refits exclude" ❌ | "cannot be read here" ❌ | **2 of 2** |

**Root cause, one expression.** `_excludes_null` reads the interval only from a nested block:

```python
r = a.get("result") or a.get("refit") or {}
lo, hi = r.get("ci_low"), r.get("ci_high")
```

The corpus holds **two shapes**. `tigecycline-ciai` nests under `result`; **every other object
stores `ci_low`/`ci_high` at the top level of the analysis dict.** So for the flat shape the
function returns `None`, the undecidable branch fires, and the page tells the reader the rows
*"store neither an exclusion verdict nor an interval"* — **which is checkably false. The
intervals are right there.** `apixaban` holds `(0.0105, 99.3808)`; `malaria-vaccines` holds
`(0.16, 0.27)` and `(0.5, 0.81)`.

**I fixed one shape and refused the other, having looked at one page.**

### Three corrections to what I told you last night

1. **"CLASS 4 … improved two."** It improved **one**. `apixaban-vte-treatment`'s old sentence
   was **true** — 0 of 3 refits do exclude — and the change replaced a true sentence with a
   false refusal.
2. **"apixaban … three rows holding a trial name and nothing else — no verdict, no interval,
   no result."** False. Those rows hold `ci_low`, `ci_high`, `i2_pct`, `k`, `omitted`, `point`.
   I asserted an absence I had not checked.
3. **`malaria-vaccines` also lost a caveat** the old code emitted and the new branch skips:
   *"with two trials each refit is simply the other trial, so this is not robustness evidence."*
   That sentence was correct and is now gone.

### Containment

**Not served. Zero pages in the corpus carry the false refusal** — the affected pages were last
built 2026-08-28 12:41–12:42, before the change. The defect is in the generator only. The two
pages I did rebuild and serve today, `sotagliflozin-hf` and `iv-iron-hf`, carry
`still_excludes_null` booleans on every row and are unaffected in both arms.

## What my instrument could not see, said plainly

`loo` is rendered into `visual_abstract_svg`, so on pages where that figure is rasterised the
sentence is **not in the rendered text at all**. The rendered-text A/B therefore
**under-detects this class**, and the 3-page figure above comes from evaluating the two code
versions against all 155 objects directly, not from the page diff. The page diff found
`malaria-vaccines` and `tigecycline`; it did **not** surface `apixaban` as changed.

## Two defects in my own instruments, found on the way

- **The comparison first reported 141 of 141 pages changed.** Two provenance artifacts I
  created: the build clock, and the git-dirty stamp (arm A ran with two files overwritten, so
  every page correctly said *"uncommitted generator changes — NOT REPRODUCIBLE"*).
- **Then it reported 135 changed, and that was a control character.** Writing the normaliser
  through a heredoc turned `\1` backreferences into literal `\x01`, so the punctuation rule
  **deleted** punctuation asymmetrically. Rewritten with lambda replacements, which have no
  escape layer to survive. This repo has `scripts/lint_escape_hazards.py` for exactly this.
- **My PREDICTED set was fabricated from memory.** I listed four prep/lipid topics; the
  statement.py commit's own evidence file `out/zero_trial_live.json` names four different ones.
  Comparing against a remembered prediction would have produced 4 false "not predicted" and 4
  false "did not move".

## Recommendation

Do not revert `projectors2.py`. **Fix `_excludes_null` to read the flat shape as well as the
nested one, restore the k=2 caveat, and re-derive all 14 outcomes** — the correct sentence is
computable for every one of them from stored intervals. Then re-run this A/B, and add the
function-level check to the gate suite, because the page-level one structurally cannot see it.

Holding for your instruction.
