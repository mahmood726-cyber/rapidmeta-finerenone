# Archived fix scripts

These scripts were one-shot cloner-residue fixes applied to the 50 apps that
inherited template residue from the ARNI_HF original. All three were applied
in commit `b929e52` (2026-04-20) and have been superseded by the patched
`clone_review.py` (commit `2b34de0`) which now propagates drug-class terms to
all 6 living-MA locations at clone time. These scripts are preserved for
reference only.

## Contents

| Script | Commit | Scope |
|---|---|---|
| `fix_living_ma.py` | b929e52 | Pass 1: 49 apps updated. Replaces `sacubitril valsartan` in OpenAlex URL, Europe PMC fallback, check-for-updates URL, auto-screener regex, arm-matching regex, banner text. |
| `fix_living_ma_v2.py` | b929e52 | Pass 2: 35 apps updated. Generic cleanup of user-visible summary strings and stale comments that mentioned sacubitril/valsartan in template-literal code paths. |
| `fix_living_ma_v3.py` | b929e52 | Pass 3: 20 apps updated. Catches collapsed-form `/sacubitril/i` auto-screener regex and the Europe PMC MAIN query (with TITLE:randomized filter) in newer clones where pass 1's OLD strings didn't match. |

## Why preserved, not deleted

1. Audit trail: the three passes document exactly what was broken and what was
   fixed, in case a future regression surfaces in any of the 50 apps.
2. Idempotency markers: the scripts emit `LIVING_MA_FIX_APPLIED` and
   `LIVING_MA_FIX_V3_APPLIED` HTML comments into each fixed app; the scripts
   themselves tell you what those markers mean.
3. Re-use as a pattern: if a future template residue is discovered, the same
   derive-from-ctgov-URL + multi-location-substitute pattern is the right fix
   shape.

## Do NOT re-run

The patched `clone_review.py` (in the user's home dir) already
propagates drug-class at clone time, and all existing apps are already fixed.
Re-running these scripts would be a no-op (they are idempotent) but is not
necessary for any current or future clone.
