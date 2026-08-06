# PUSHED ledger

Bar in force (option B): CERTIFIED = (1) both file-access families, reading the
staged sources, find NO defect in the ACTUAL object — a hypothetical mutation the
validator misses is not an object defect; (2) reconciliation against the best
published meta done and clean or explained; (3) the current validator runs clean
on the actual object. Validator hardening is a separate ongoing track and does
not gate a push.

## Pushed

### 1. alirocumab-lipid

| | |
|---|---|
| commit | `8d1025ba83025b7f970c0cfa548ca9523051faff` |
| remote | `https://github.com/mahmood726-cyber/rapidmeta-finerenone.git` |
| branch | `main`, fast-forward `9de3f2d1f..8d1025ba8` (no force) |
| confirmed | `git ls-remote origin main` → `8d1025ba8…` |
| live | https://mahmood726-cyber.github.io/rapidmeta-finerenone/ALIROCUMAB_LIPID_SSOT.html — HTTP 200 |
| provenance | `ssot/alirocumab-lipid/` — object, 6 CT.gov payloads, both verdicts verbatim |

**Result reported:** six alirocumab trials, percent change in calculated LDL
cholesterol at week 24, random-effects DerSimonian–Laird:
**MD −54.66 (−60.75 to −48.56)**, τ² 47.42, I² 87.9%, Q 41.41 on 5 df.

**Certification — Codex (file-access, staged sources):**
> "I found no included-trial numeric cell in the alirocumab object that was
> unsupported by the staged source payloads."
> "The alirocumab object is source-correct for the included cells and
> arithmetically correct. The defect is the validator over-claim."

**Certification — Gemini (file-access, staged sources):**
> "the object perfectly matches the source records. I verified every trial
> against its registry payload."
> "Yes, the arithmetic is flawless."

**Reconciliation:** vs Schmidt AF et al., Cochrane 2020 (CD011748.pub3). No
estimate comparison is possible — they pool clinical events, this pools a lipid;
a complete estimand difference, recorded rather than papered over. Their 18
alirocumab trials against these 6 is scope, not error: this object repairs one
app's citation list and is not a systematic review.

**Added, not substituted.** `ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html` is
untouched. The certified object covers one outcome; that app presents several,
so replacing it would silently narrow the review. Which survives is open.

**Hook:** pushed with `SKIP_REGRESSION=1` under explicit authorization from
Mahmood. See the follow-up below; the hook was not modified.

## Not yet eligible

| app | blocker |
|---|---|
| covid19-vaccines | needs fresh both-family object certification on the current commit |
| rivaroxaban-acs (golden) | never emitted a clean PASS token; predates bar B |
| MPOX, OBESITY, PREVNAR15, DDIMER | not yet built |

## Follow-up, deliberately NOT done as part of this push

`.githooks/pre-push` is broken in two ways and both should be fixed on their own
commit, by someone who is not trying to get their own push through:

1. `python "$SCRIPT" 2>&1 | tail -15` then `STATUS=$?` reads **tail's** exit
   code, which is always 0. The hook cannot block a push, whatever it finds.
   Fix: `${PIPESTATUS[0]}`, or `set -o pipefail`.
2. The docstring says "53 apps, ~60 seconds". `regression_check.py` globs
   `*_REVIEW.html`, which is now **1,449 apps** — roughly 27× the stated scope,
   and hours rather than a minute.

Evidence it is not merely slow but inert: the last `regression_results.json`
records `"fully_ok": []` and a failing `ZZZBROKEN_TEST_REVIEW` canary — its own
deliberate self-test failure — while pushes continued to pass.
