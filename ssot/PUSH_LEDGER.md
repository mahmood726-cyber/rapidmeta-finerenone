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

### 2. covid19-vaccines

| | |
|---|---|
| commit | `dc28e4e0f4351642710d20f575d245d7cb0b7bba` |
| remote | `https://github.com/mahmood726-cyber/rapidmeta-finerenone.git` |
| branch | `main`, fast-forward `aff23101d..dc28e4e0f` (no force) |
| confirmed | `git ls-remote origin main` -> `dc28e4e0f...` |
| live | https://mahmood726-cyber.github.io/rapidmeta-finerenone/COVID19_VACCINES_SSOT.html -- HTTP 200, confirmed live 2026-08-06, byte-identical to the gated build |
| gated object | `dc4bb6d` -- byte-identical in the Codex staging and the Gemini worktree |
| provenance | `ssot/covid19-vaccines/` -- object, 11 source payloads, both verdicts verbatim |

**Result reported:** three COVID-19 vaccines, each as its own single-trial
estimate against placebo, **no combined figure**. Sputnik V RR 0.0845 (0.0488 to
0.1463); CVnCoV RR 0.5439 (0.4158 to 0.7115); BBIBP-CorV carries NO count-based
ratio, because its events come from the primary efficacy analysis while the only
per-arm denominators published are randomisation group sizes. k=3, `pooled: null`.

**Certification -- Codex (file-access, staged sources, nonce 4cfed46e):**
> "I found no source-backed object defect in the included trial cells, removal
> reasons, reference figures, no-pool decision, or completeness disclosure."

**Certification -- Gemini (file-access, staged sources, source leg run TWICE):**
> "No object or validator defects were identified." (run 1, VERDICT: PASS)
> "I found no included per-arm event count, per-arm denominator, NCT ID, PMID,
> enrolled/randomised count, registry enrolment, review figure, review analysis
> population, or trial-reported rate that was absent from its staged payload."

Both families' terminal tokens were DEFECTS-FOUND or PASS on the VALIDATOR track
only; every OBJECT section of the Codex verdict reads "No defect found".

**Two rounds of real object defects were fixed before this push, both found by
the gate rather than by us:** the BBIBP row asserted "The risk ratio shown here"
after round 10 had deleted that ratio, and three high-level prose fields still
told the reader every absence was a sourcing failure while the object's own
removal block recorded a units-of-analysis error and a wrong-disease trial --
one of them asserting "all existed and were in the right disease area" beside a
"wrong disease area" category.

**Standing VALIDATOR track, NOT fixed, deliberately not bundled into this push:**
`check_reference_consistency` matches a number anywhere in the 1.5M-character
review rather than in the row for this vaccine and outcome; identifiers (`nct`,
`pmid`) are not anchored to the staged payload identity;
`check_against_sources` binds only `enrolled`, leaving `registry_enrolment`,
`dosed`, `reference_analysis_population` and the `trial_reported_rate_*` fields
unchecked though all reach a reader; removal-disclosure never tests whether the
staged registration supports the stated reason; arm-completeness skips
abstract-sourced arms. Ten concrete reader-visible mutations pass clean across
the two families. Three were re-tested here rather than believed, and all three
reproduce. Fixing these changes what the gate reviews, so it is its own round.

**Hook:** pushed with `SKIP_REGRESSION=1` under standing authorization. The hook
was not modified; the two defects recorded below remain.

### 3. malaria-vaccines

| | |
|---|---|
| commit | `b998ac6e3503cc37f61f7f1eab993990559bd821` |
| remote | `https://github.com/mahmood726-cyber/rapidmeta-finerenone.git` |
| branch | `main`, fast-forward `f7cb32bdd..b998ac6e3` (no force) |
| confirmed | `git ls-remote origin main` -> `b998ac6e3…` |
| gated object | `3b28c93`, nonce `malaria-vaccines-079d19af`, round 9 |
| Pages build | **built** in 78s, no error — against a ~660s ceiling and a 657s predecessor |
| live | https://mahmood726-cyber.github.io/rapidmeta-finerenone/MALARIA_VACCINES_SSOT.html — HTTP 200 |
| provenance | `ssot/malaria-vaccines/` — object, 26 source payloads, both family verdicts verbatim |

**Result reported:** two vaccine-specific pooled efficacies, each estimand-homogeneous,
pooled on the log scale, and NO cross-vaccine figure.

  R21/Matrix-M, seasonal, Cox time-to-first at 12 months, k=2
      HR 0.2466 (0.2128 to 0.2857)   VE 75.34% (71.43 to 78.72)   I²=0
  RTS,S/AS01, boosted, negative-binomial all-episode rate, end of trial, k=2
      IRR 0.6372 (0.5967 to 0.6805)  VE 36.28% (31.95 to 40.33)   I²=0

Eight randomised cohorts from seven registrations, counted at the level of the
RANDOMISATION. Eight further published contrasts shown and deliberately pooled
into nothing, six of them because they share a control group with a contrast
already used.

**Certification — Codex (openai, file access, staged sources):**
> "No OBJECT findings. No VALIDATOR findings."
> "I found no cited section attached to a decision it does not support."

It recomputed all seventeen stored ratios from their quoted efficacies with
interval inversion, and checked every Handbook citation against the decision it
governs.

**Certification — Gemini (google, file access, staged sources):**
> "No discrepancies, misallocations, or calculation errors were found."

The source leg passed; its JUDGE pass raised one finding, that §4.6.1/4.6.2
should be §5.2.1/5.2.2. **Verified and NOT upheld:** 4.6.1 and 5.2.1 carry the
SAME TITLE in different chapters — the Handbook states the studies-not-reports
principle in both the selecting-studies and collecting-data contexts — and 5.2.2
is "Determining which sources might be most useful", not multiple reports. Codex
independently confirmed 4.6.1/4.6.2 in the same round. 5.2.1 is a legitimate
additional cross-reference and was NOT added, because changing the object after
certification would mean pushing something other than what was gated.

**Nine rounds to get here, and the shape of them is the finding.** The numbers
were right from round 1: the Gemini source leg has never faulted a value, an
inversion or an attribution in nine rounds. Every defect after round 3 was PROSE
about the object drifting from the object — a comparator called identical after
the table said otherwise, a count corrected in one field of two, "the Handbook's
actual test" surviving in a third place after being withdrawn from two. What
ended it was deleting the prose rather than correcting it: nothing a computed
field holds is restated in words. The last contradiction was fixed by changing
ONE value and letting three derived sentences follow.

**One error of mine worth recording.** In round 4 a reviewer said a hazard ratio
was mislabelled and should be a rate ratio. I changed it WITHOUT OPENING THE
PAYLOAD. In round 7 the same family read further into the same file and said the
opposite; the registry's analysis field settles it — `statisticalMethod:
"Regression, Cox"`. The original label was right. Both registry fields are now
staged side by side so the question cannot be decided again on half the record.
Never apply an adversary's asserted correction without reading the source.

**"Byte-identical" needs a qualifier on Windows.** The served page is 79,828
bytes and the local build is 80,371: 543 CRs, because Python's text-mode write
translates newlines. After normalisation both are 79,828 bytes with the same
SHA-256. The content is identical; the phrase "byte-identical" was loose in the
two entries above and is corrected here rather than there.

**Hook:** pushed with `SKIP_REGRESSION=1` under standing authorization. The hook
was not modified; the two defects recorded below remain.

## The gate now runs UNATTENDED, both legs, from this lane

As of the malaria round there is no paste step and no second machine. `codex
exec` takes the prompt on stdin and writes its verdict file; `agy --print` takes
the prompt as an argument and its stdout is captured. `gate_malaria.py` drives
both, and it refuses to skip three things:

  * **The seat is proved with a real exec first.** Both legs answer a nonce
    written to local disk seconds earlier, and agy is made to name its model so
    a wrong-pool answer is visible. Round one: codex LIVE in 15s, agy LIVE in
    13s naming `Gemini 3.1 Pro`. `login status` is never consulted.
  * **The previous round's verdicts are deleted before the run**, so a failed
    leg is an absence rather than a stale file read as this round's answer.
  * **A fresh nonce per round**, echoed as the first line of both verdicts and
    machine-checked before any push.

One trap worth recording: both CLIs are installed as shell shims, and a
list-form `subprocess` call fails on the POSIX `codex` script with a bare
file-not-found that reads exactly like the tool being absent. The `.cmd` wrapper
is the thing to launch. `_exe()` in `gate_malaria.py` resolves it.

## GitHub Pages is at its build ceiling -- read before the next push

The covid push landed correctly and the Pages build ERRORED anyway, so the page
was 404 for an hour while `git ls-remote` said everything was fine. Push is not
deploy, and this repo now proves it.

    dc28e4e0f  errored  662s   1046.4 MB  14,170 files
    f7cb32bdd  built    657s    896.5 MB   8,361 files

Untracking 150 MB of cache and audit data (commit f7cb32b) got the build through
with **five seconds of margin**. That is not a fix, it is a reprieve: the ceiling
is a build-time limit around 11 minutes, and 1,480 root HTML pages account for
712 MB of the remaining 896. The next page added is as likely to fail as not.

Do NOT treat a successful push as a live page. Check
`gh api repos/<owner>/<repo>/pages/builds --jq '.[0]'` and curl the URL.

Real fixes, in order of how much room they buy:
  1. Move the Pages source to /docs holding only the pages the site serves.
  2. Switch build_type from legacy to a GitHub Actions workflow that publishes
     only the HTML, so the data tree never enters the build at all.
  3. Untrack retired/ (62 MB, 118 HTML) and removed/ (38 MB, 74 HTML). This is
     the LAST resort of the three: those are served pages, not data, so it
     removes content rather than overhead.

## Not yet eligible

| app | blocker |
|---|---|
| rivaroxaban-acs (golden) | never emitted a clean PASS token; predates bar B |
| MPOX, OBESITY, DDIMER | not yet built |

`PREVNAR15` was listed here as "not yet built" while it was in fact pushed and
live at `aff23101d` -- the base this covid push fast-forwarded from. It has no
entry above. Recording it is a gap in this ledger, not a gap in the gate: the
verdicts exist under `ssot/prevnar15-pneumo/` in the pushed tree. Left for
whoever has that round's context, rather than reconstructed here from the tree.

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
