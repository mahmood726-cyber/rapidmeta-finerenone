# Defect registry — every class found on 2026-08-18/19, and what rejects it

Written to a single standard: **a class is closed only when a command rejects it.** Not when
it is documented, not when the rule is agreed, not when the author intends to remember.

The night's central finding is the reason this file exists:

> **The objects kept being right and the instruments kept being wrong.** Every substantive
> correction was to a reason, an attribution, or a check — never to a stored quantity. Six
> figures survived independent recomputation; six recorded limitations survived independent
> test. What failed, repeatedly, was the apparatus doing the checking.

So the exposures below are weighted toward instruments, and the proof standard is aimed at
instruments: an instrument that has never been observed to fail is not known to be able to.

---

## A RULE YOU HAVE WRITTEN IS NOT A RULE YOU HAVE APPLIED

Placed beside the transport finding, because it is the same argument demonstrated in a **second,
unrelated class** — and that is what turns it from an anecdote into the case for mechanism.

The transport instance: heredoc mangling recurred **eight times in one night** against an author
who had read the rule, written the rule, and committed the rule.

The second instance, 2026-08-19: `scripts/rob2_assess_2026_08_19.py`, run with a single topic
argument, **overwrote `rob2.json` with that one topic and silently discarded the other seven**.
Written by the author of the merge-never-write rule, **inside the instrument that enforces it**,
**one hour after writing it**. Nothing about understanding the rule prevented breaking it; only
re-reading the output caught it.

> **Understanding a rule does not execute it. A rule enforced by memory is enforced by nothing.**
> Both instances were committed by an author who could state the rule correctly at the moment of
> breaking it — so the failure is not knowledge, and no amount of further explanation addresses
> it. Only a command that refuses does.

- **Fix** the writer now merges with what is on disk and **refuses if the merge would drop any
  topic**. Proven by re-running full (8 recorded), then single (merged with 8, still 8)

### And a guard can be inverted: it blocked the disclaimer and passed the assertion

`sig_unsourced_two_human_claim` blocked a push by matching this sentence:

> "The two independent screens were performed by two MODEL FAMILIES, **not by two people**. A
> reader of 'screened in duplicate' would ordinarily assume **two human reviewers**, so this
> field says what was actually done."

That sentence exists to prevent *exactly* the misreading the signal guards against.

> **A guard that blocks the disclaimer while passing the assertion is inverted.** A signal built
> to catch a claim will catch the sentence **denying** the claim unless someone thinks about
> **polarity**. A mention is not a claim.

**Third instance of that family in one file**, and its own docstring already records the other
two: `"Submission readiness: READYISH"` containing `READY`, and `\bNone\b` matching the English
word mid-sentence.

- **Fixed in the guard, not by rewording the page.** The gate has no override, and **a gate with
  no override must never be satisfied by making a page less truthful** — the honest sentence was
  the one worth keeping
- **Proven in four parts**, part 3 load-bearing: the real claim must *still* fire, or the fix has
  disarmed the guard rather than corrected it

---

## THE LARGEST INSTANCE IN THIS FILE IS OURS — a delivery check that never left the machine

Found 2026-08-19, when Mahmood opened the live pages and saw nothing. Placed above every other
class because it invalidates the *reporting* of all of them.

`scripts/verify_served_bytes_2026_08_19.py` started a `SimpleHTTPRequestHandler` over the
repository, fetched each page from `127.0.0.1`, compared md5 to disk, and printed
**"All N pages confirmed in served bytes."** Every word true; none of it about delivery. It
served the build directory to itself, so `md5(served) == md5(disk)` was a **tautology** — the
limb could not fail for the reason anyone cared about.

| measured | value |
|---|---|
| live `SGLT2_HF_REVIEW.html` | md5 `ca872295…` — **identical to `origin/main`'s copy** |
| local build of the same page | md5 `d9164e1c…` |
| `origin/fix/ssot-tabbed-shell` | **unknown revision — never pushed** |
| GitHub Pages source | `{"branch":"main","path":"/"}` |
| divergence | **96 commits** ahead of `origin/main`, 0 behind |

> **The deployment is perfectly current with respect to `main`. What is stale is `main`,
> relative to a branch that was never pushed at all.**

**The general form, which is the part that generalises beyond this repository:**

> **A verification is only ever about the artefact it fetched. A check that does not name its
> host is not a delivery check.** Ninety-six commits of green "served bytes" verifications were
> true of a build and silent about the artefact a reader opens.

- **Detector** `scripts/verify_delivered_bytes.py`. It fetches the **public URL** (derived from
  `origin`, overridable by `RM_PUBLIC_BASE`); it **names the host on every line and in the
  summary**; it **fails closed** — an unreachable public URL is NOT_ASSESSABLE with a non-zero
  exit and it **never falls back to local and passes**; and it reports the **deploy ref**
  against the ref being verified, because a push to a branch the pipeline does not track
  produces a remote branch and no deployment
- **`--build-only` survives** because checking a build before deciding to deploy is a real
  need — but it prints `BUILD CHECK` on every line, never the word *delivered*, and **cannot
  return a delivery pass**. The mode is in the output, not only in the invocation
- **First run, against the public host** — 7 pages, **0 delivered**: the two ablation reviews
  built tonight return **HTTP 404** (they do not exist publicly at all), and five are **STALE**
  with each object's own k-cascade sentence **absent from the delivered bytes**
- **The old script is deleted, not kept.** An available broken instrument is a trap for whoever
  runs it next — the same reasoning that renamed four `*_gate.py` files that could only pass

---

## THE HEADLINE — 3 of 135 topics have ever been asked

Measured 2026-08-19, verified independently. Above every defect class in this file, because it
reframes all of them.

| | |
|---|---|
| topic objects in the corpus | **135** |
| topics carrying a `k_cascade` | **3** |
| topics that have **never had k counted at all** | **132** |
| topics with a nonzero unscreened remainder | **0** |

That last row is true, and read alone it is the most misleading number this project could
publish.

> **A corpus of 135 topics reporting "0 unscreened remainder" is not a clean backlog. It is 132
> topics that were never asked the question.**

This is **E4 at project scale** — withholding by an entire pipeline rather than by one
classifier. Every "complete" claim in this repository must be read against it: three topics
complete is **three of a hundred and thirty-five**, and the other 132 look complete only because
nothing has interrogated them.

**What stopped this becoming a false all-clear** is that the census reports `NO_CASCADE`,
`REMAINDER_ABSENT` and `remainder: 0` as **three distinct states**. Folded together, the corpus
reads as fully screened.

### These three states must never be summed

**Binding on every summary, dashboard, page and report in this corpus.** A count of "topics with
no remaining work" may include `remainder: 0` and must **exclude** `NO_CASCADE` and
`REMAINDER_ABSENT`, which are *unknown*, not *zero*. Enforced by
`scripts/lint_no_false_allclear.py`; a summary that adds them is a false all-clear, and the
difference here is 3 versus 135.

---

## The transport finding — read this before anything else here

**The single most useful result of the night, because it explains eight separate instances at
once and overturns every previous account of them.**

Heredoc mangling had been recorded eight times as an *author* failure: someone wrote `\b`
through a shell, the shell ate the escape, the rule says don't do that. Every previous write-up
of this class — including ones written by the author who then breached it again — located the
fault in the person.

That account is **wrong**, and it was tested rather than argued:

| What was written | How | Bytes that arrived |
|---|---|---|
| `\\b` inside `<<'PY'` — a **quoted** heredoc, which **cannot shell-expand** | shell transport | `0x08` — mangled |
| the same two characters | file-writing tool | `\` `b` — intact, confirmed by `od -c` |

**The corruption is in the transport, not in the shell.** A quoted delimiter is the standard
remedy for escape mangling and it does not work here, because expansion was never the mechanism.

Three things follow, and they are the reason this sits at the top:

1. **It explains the recurrence.** The class kept being breached by people who knew the rule
   because knowing the rule did not help — the remedy everyone reaches for (quote the
   delimiter) is ineffective against the actual mechanism.
2. **It converts a discipline into a mechanism.** "Write files directly" was previously advice,
   and advice failed eight times. It is now the only transport observed to preserve the bytes,
   which is a *fact about the tools*, not a request for care.
3. **It relocates the blame correctly.** Eight instances were recorded against authors who had
   done nothing wrong except use a channel that silently corrupts. Any registry entry that
   blames an author for this class is misfiled.

The class reproduced itself **live, in this repo, while the detector for it was being written**
— which is how the diagnosis was obtained at all.

### The ninth instance — the argument for mechanism, made against its own author

**Twenty minutes after this section was written and promoted to the top of this file, its author
wrote a regex through a shell heredoc.** The pattern was the fix for E1. Its `\b` arrived as a
literal `0x08`.

`scripts/lint_control_chars.py` caught it immediately:

```
ssot/topic_identity.py:90  0x08 BACKSPACE (the heredoc \b signature)
```

Two things about that are worth more than any argument this file could make:

1. **The detector fired in production, on a live instance, not a planted one.** Every other proof
   in this registry is a defect someone reconstructed on purpose. This one was real, unnoticed,
   and would have shipped a pattern that could never match — inside the very fix written to stop
   evidence being withheld.
2. **Knowing the rule, writing the rule, and promoting the rule to the top of the registry did
   not prevent breaching it within half an hour.**

> If the person who diagnosed the transport, wrote the detector for it, and placed it above every
> other finding in this file still breached it twenty minutes later, then no amount of
> understanding was ever going to be the control. **The mechanism is the control.** That is the
> whole case for this document, demonstrated against the one author with the least excuse.

Repaired through a written file — the transport observed to preserve bytes.

**And then a tenth instance, in the paragraph above.** Writing *this section* — the account of
the ninth breach — through a heredoc put two more `0x08` bytes into the registry, inside the
sentences describing that exact byte.

The difference is the one that matters: **the pre-commit hook refused the commit.** The tenth
instance never entered history. Instances one through nine were all found after the fact, by
reading; this one was stopped at the gate.

> Ten breaches by an author who understood the mechanism completely. Zero of the first nine were
> prevented by understanding. The tenth was prevented by a hook that does not care whether
> anyone understands it.

Detectors §1 and §2 below cover the two halves of what this transport produces.

## The proof standard

Every entry claiming a detector must satisfy three parts, **each a command someone else can
run**, because the third exists precisely to stop the first two being asserted:

1. **It can fire.** Run against a known-bad input, observe rejection.
2. **It does not fire on the correct case.** Run against the corpus, observe silence.
3. **Neither is established by the build reporting success.** A build prints success when a
   guard is present but broken — that is how the foreign-id guard printed `HELD 7 / REFUSING 1`
   while incapable of matching a single identifier. Exit codes from the detector itself,
   with counts, or it does not count.

Status vocabulary, used strictly:

| Status | Meaning |
|---|---|
| **CLOSED** | Detector exists, all three parts demonstrated, wired into `.githooks/pre-commit`. |
| **CLOSED (unwired)** | All three parts demonstrated, but must be invoked deliberately. |
| **PARTIAL** | A detector exists and fires on some of the class; the uncovered part is named. |
| **OPEN** | No mechanical detector. The reason is named. Prose only. |

---

## CLOSED

### 1. Heredoc mangling — control characters in source
`\b` written through a shell heredoc arrives as a literal `0x08`. The file parses, imports,
runs, and the build reports success while the pattern can never match.

**Eight instances in one night**, by an author who had read the rule, written the rule, and
committed the rule. The worst destroyed the foreign-registration-id guard. The eighth was
`PAGE-STANDARD.md`'s own sentence *describing* the mangling class, mangled by the class.

- **Detector** `scripts/lint_control_chars.py`
- **Fires** a byte-for-byte reproduction of the historical corruption → REFUSED
- **Silent** clean repo → exit 0
- **Independent** its own exit code; excluded `sources/*.extract.txt` files are **counted and
  reported every run**, because a silent exclusion is how a guard becomes a formality

**Root cause, established by experiment rather than assumed.** The first probe was written
through a *quoted* heredoc (`<<'PY'`), which cannot shell-expand — and `\\b` still arrived as
`0x08`. The same two characters written with the file-writing tool produced `\` `b` as separate
bytes (`od -c`). **The mangling is in the transport, not in the shell.** That is why quoting
the delimiter never helped, and why the class recurred eight times against someone who knew
the rule.

### 2. Escape hazards — control characters in *values*, with clean source
The sibling of §1, and invisible to it. In a non-raw Python literal `\b` is a **valid** escape:
the source stays clean ASCII, the compiled value becomes `0x08`.

```python
re.compile("\bNCT\d{8}\b")     # source byte-clean; value is \x08NCT\\d{8}\x08
re.compile(r"\bNCT\d{8}\b")    # correct
```

Found by tracing a `SyntaxWarning` at commit rather than reading past it.

- **Detector** `scripts/lint_escape_hazards.py` — both halves, which fail differently:
  unrecognised escapes (`\s`, `\d`) that Python already warns about and which work *by
  accident*; and recognised escapes yielding control characters, for which **no warning
  exists** — silent today, wrong today
- **Fires** planted `re.compile("\bNCT\d{8}\b")`, source verified byte-clean by `od -c` →
  REFUSED, naming line and `\b BACKSPACE`. The byte scanner of §1 is correctly **silent** on
  the same file, which is the point of the entry
- **Silent** 694 Python files → 0 and 0, exit 0
- **Independent** the hook itself run against the planted hazard → REFUSED; against clean → 0

### 3. Identifiers from recall
A registration id written beside a trial acronym is **two** claims: the id, and the pairing.
The id gets checked; the pairing reads as a label rather than as an assertion, and does not.

Auditing `iv-iron-hf` I recalled the mapping and got **three of five wrong**. The object was
correct throughout.

> A recalled identifier in a **build** produces a wrong value that later checks may catch.
> A recalled identifier in an **audit** produces an **accusation**, and nothing audits the auditor.

- **Detector** `scripts/lint_identifier_pairing.py`. Closed vocabulary — only acronyms the
  registry itself published (751 over 765 ids, from the local cache, offline, ~3s). It does not
  guess which token is an acronym; guessing needs a stopword list, and a stopword list is a
  permanent argument
- **Fires** `--positive-control` → REFUSED. The three documented mispairings in its own
  docstring carry `# lint:known-mispairing` and are therefore a **permanent** positive control
- **Silent** 2085 authored files → 0, exit 0
- **Independent** a *freshly planted* swap (not a rerun of the control) → REFUSED
- **Empty vocabulary returns exit 2 and the hook refuses**, because a check with nothing to
  check against passes everything

**Its own false-alarm history is kept in its docstring, because a detector that has never been
wrong has never been tested.** Four versions, each corrected by evidence:

| v | Approach | Result |
|---|---|---|
| 1 | compare `trial_id` to registry | `trial_id` is `None` on **every trial in the corpus**; fell back to `name` and compared a **title** to an **acronym**. 2 false alarms against a correct topic. The unit-of-analysis defect in new clothes |
| 2 | prose, 140-char window | **1277 alarms, essentially all correct text** — this corpus lists four trials per sentence, so every id sat near its *neighbour's* acronym. Proximity is not a claim of identity. Also took minutes |
| 3 | require apposition | 13 alarms, all correct text — `{"NCT…": "CONFIRM-HF", "NCT…": …}` makes one key's **value** adjacent to the **next key** |
| 4 | three structural discriminators | no comma (separate elements), no `":` (a mapping key), no newline (a trailing comment labels *its own* line) → 0 |

**Cost named rather than hidden:** the form `NCT01453608, EFFECT-HF` is now invisible. Accepted
deliberately, because a check with 13 false alarms and 0 true ones is switched off within a week
and then catches nothing at all.

### 4. Net deletion from an SSOT object
- **Detector** `.githooks/pre-commit` → `scripts/ssot_net_deletion_check.py`
- **Fires** staged a real net deletion on `iv-iron-hf` (5 trials → 1) → exit 1
- **Silent** clean tree → exit 0
- Override requires a stated reason on the record (`SSOT_ALLOW_NET_DELETION="why"`)
- **Why a hook and not a helper:** `scripts/rebuild_guard.py` was written for this exact defect
  and committed *the day before it recurred*. It did not fire, because the offending script used
  a different write path. **A guard that must be remembered is not a guard.**

### 5. `git add -A` staging
The rule was broken in the commit immediately after it was written.
- **Detector** `.githooks/pre-commit-staging` — refuses staged paths outside the declared set
- **Fires** staged `figs/_probe_stage.html`, outside the set → exit 1, naming the path
- **Silent** clean tree → exit 0
- Deliberate override `STAGING_WIDE=1`

Entries 4 and 5 pre-date tonight and were listed here as CLOSED before either had been observed
to fail. Both were then planted against, and both fired. **That gap — between believing a gate
works and having seen it refuse — is the one this file exists to close, and it opened inside
this file while it was being written.**

### 6. Subprocess decode hazard (`text=True` under cp1252)
- **Detector** `scripts/lint_subprocess_decode.py`, a **ratchet** (18 baselined sites), so it
  blocks *new* hazards without demanding an unrelated 18-site cleanup
- **Fires** verified tonight by planting one new hazard → exit 1; removed → exit 0. Verified by
  **planting, not by reading the comparison**, which is the distinction this file is about
- **2026-08-19 — the detector counted its own documentation.** The final loop was a raw line
  scan, so a COMMENT containing `text=True` counted as a site. **Two of the eighteen baselined
  entries were exactly that** — prose in `lint_encoding_defaults.py` describing the hazard.
  They had been absorbed into the baseline rather than recognised, and the ratchet then made
  every future comment about the rule cost a refusal. *A lint that counts its own
  documentation as a violation taxes writing the rule down.* The AST was already being walked
  for the safe case; asking it which lines carry a real keyword removed the class.
  **Baseline 18 → 16.** Fires-proof observed live: it refused the five new hazards introduced
  by the re-gate scripts before they were fixed

### 11. A cascade that does not reconcile with itself
- **Found** 2026-08-19, re-gating five completed topics. Three of five stored `k0` in
  `k2_role_located`, so **the stage named "role located" counted the records whose role could
  not be located** and `kNA` was added twice — once as itself, once inside the count saying it
  was resolved. alirocumab 99 vs 98, attr-cm 55 vs 52, iv-iron 47 vs 45
- **Why it survived** it is invisible where `kNA = 0`, which is two of the five. *A sum that is
  right whenever the thing it omits is zero has not been tested*
- **Detector** `scripts/lint_cascade_arithmetic.py` — five limbs, every failing one reported;
  `NO_CASCADE` and `NOT_ASSESSABLE` are distinct states and neither is a pass
- **Also a property** PAGE-STANDARD **P20**, evaluated by `build_to_standard.py` so a page
  states it rather than only a lint knowing it
- **Fires** proven in `scripts/prove_regate_guards.py` by planting the **real shipped value**
  read from git `21e9cfcf3`, not a fixture

### 12. A superseded estimate surviving in a field named `ours`
- **Found** 2026-08-19. `alirocumab-lipid` was restated k=6 → k=8; its
  `published_comparison.divergence_decomposed.ours` still read *"−54.66 … k=6 … PREDICTION
  INTERVAL −74.1 to −35.2, which is the number to quote."* A gated page carrying two estimates
  for its own review, with the superseded one in the table a reader consults to compare us
  against the literature
- **Why the existing detector could not see it** `lint_block_contradicts_object.py` scopes
  `published_comparison` out **entirely** as a FOREIGN_SUBJECT, because it describes other
  people's reviews and that exclusion killed one of its two false-alarm families. **The
  scope-out is at block level; the first person is at field level.** *A block excluded because
  it describes other work is exactly where a field named `ours` hides*
- **Detector** `scripts/lint_ours_matches_pool.py`. The subject is decided by the **key**
  (`ours`, `our_*`, `this_review`), never by parsing a sentence, so this is not the removed
  prose check returning. Three limbs: the point at the precision the field itself quotes, a
  `k=N` claim, and `our <decimal>` in prose
- **Two false alarms fixed, not baselined** `incretin-hfpef-review`'s first-person field holds
  an **NCT-id list**; `NCT04847557` was read as a number. *A field can be first-person and not
  be a numeric claim.* Identifiers are stripped and limb 1 needs a decimal to be assessable —
  the conservative direction is stated, not hidden
- **Limb 3 promoted from advisory only after every hit was read** 3 occurrences, 3 true, 0
  baselined

### 13. A restatement block that ages silently
- **Found** 2026-08-19. `sglt2-hf`'s stored cascade reproduces at **exactly one** classifier
  revision (`f2bf16022`) and at no other; two later commits shipped the same night and were
  never carried back. The surfaced set re-executed to the same size, so it is a **missed
  re-run, not changed data**
- **What made it look current is that it carried a correction note.** *A restatement is a claim
  about a moment. Its presence shows someone once looked, never that anyone looked last*
- **Detector** `scripts/regate_across_revisions.py <topic>` — re-executes the topic's own query,
  loads **every** commit that touched the classifier from git, and reports at which of them the
  stored cascade reproduces. Exit 1 when the newest revision is not among them
- **Also a property** PAGE-STANDARD **P18**
- **And it found a second defect of its own class** `bempedoic-acid-review`'s legacy block said
  the placebo-discriminator "moved one to comparator and two to background". It caused
  **neither**: the two-to-background move belongs to `92d84da72`, and its own single move ran
  in the **opposite direction** (comparator → experimental). *The number 16 was right and the
  story of how it got there was wrong* — P15 one stage later

### 14. A promotion that reaches the headline and not the derived blocks
- **Found** 2026-08-19. The k=6 → k=8 recovery moved the headline and `results.by_outcome` and
  left behind: `prisma_flow.included` (6, with six NCTs, against eight in `inputs.trials`),
  `k_cascade.k_included_in_object` (6), the entire published-meta comparison, the
  estimator-sensitivity table, and **the prediction interval — whose own text calls it "the
  number to quote"**
- **Detector** PAGE-STANDARD **P19**, evaluated in `build_to_standard.py`: `inputs.trials`,
  `k_cascade.k_included_in_object` and `prisma_flow.included` must agree, and no first-person
  field in `published_comparison` may declare a `k` the pooled outcomes do not
- **Recompute gate** `scripts/recompute_alirocumab_k8.py` refuses to emit anything derived
  unless the stored headline first reproduces from the object's own per-trial values, and
  checks its REML against metafor's result already stored on the object

### 15. The primary outcome read by position rather than by registered text
- **Found** 2026-08-19, re-pooling apixaban prophylaxis. `outcomeMeasures[0]` is the MAJOR-VTE
  **secondary** for ADVANCE-2 (NCT00452530) and the **primary** for its three companions, so a
  positional read pools one trial's secondary against three trials' primaries — **with nothing
  malformed anywhere**. No parse error, no null, no missing key, four numbers of the right
  shape. There is no downstream symptom, which is why prose could never have held it
- **Detector** `scripts/lint_primary_by_position.py`, **wired**. AST, not regex: a constant
  integer subscript of a collection whose name says it holds outcomes. Slices and variable
  indices are not flagged — iteration is not a positional claim
- **Proven** `scripts/prove_position_and_withholding.py`, four parts, including the load-bearing
  one: the same read done **by rank** must pass, or the detector discriminates nothing
- **What it found on first run** twelve sites, of which six are `primary = outcomes[0]` in
  `populate_nma_benchmarks_batch_E..J.py`, which name element zero `primary` and ship it as the
  dashboard default outcome (commit de3cf9b1e). And `retire_mace_hardcode.py` deliberately
  **replaced a text match** with `(outcomes && outcomes[0])`, arguing in its own docstring that
  the array is ordered primary-first *by convention*. Checked, not assumed: no tracked page
  carries the replacement today. Baselined sites are printed every run and **are not absolved**
- **Fixed at the root, in two places** `ssot/screen_remainder.py` and
  `ssot/screen_sglt2_remainder.py` built `outcomes` as PRIMARY + SECONDARY + OTHER and then
  quoted element zero in a shipped exclusion reason as *"Its registered primary is …"* — true
  for any trial that registers a primary, **false for one that does not**. Both now select by
  rank. Exposure measured rather than assumed
  (`scripts/measure_primary_by_position_exposure.py`): **0 of 47** locally-snapshotted trials
  lack a registered primary, so the shape never fired. A measurement, not an absolution

### 16. Composite endpoints compared by name rather than by components
- **Found** three times in one night, in two disease areas. `total VTE + VTE-RELATED death`
  against `VTE + ALL-CAUSE death` is one name and two endpoints; the three ablation composites
  are "composite of mortality and events" three times over and decompose into
  `{death, hf_event}`, `{death, stroke, bleeding, cardiac_arrest}`, `{death, hf_event}`
- **And heterogeneity settled none of them** — mismatched estimands pooled at I² **0.0%**,
  **3.9%** and **83.6%**, matched ones at **67.8%**. Both directions, so the statistic is not a
  test in either. That is P36
- **Detector** `scripts/lint_composite_by_components.py`, **wired**. Structural decomposition,
  specific-mortality-before-general so `VTE-related death` is never collapsed into bare `death`
  — the collapse *is* the defect. It blocks on an **unrecorded** mismatch, never on a mismatch:
  pooling mismatched endpoints is sometimes right, and both ablation reviews argued for exactly
  that. Doing it silently never is
- **Proven** `scripts/prove_composite_by_components.py`, four parts, against the pool apixaban
  prophylaxis actually **declined** — the four different primaries, RR 0.658, I² 83.6%. Part 3
  is the load-bearing one: four *different strings* naming the *same* endpoint must pass
- **Two limits stated** endpoints matching no component pattern compare EQUAL on both sides, so
  every one is counted and printed (48 today); and the comparison runs only where the object
  states it pools each trial's own registered primary, because **the corpus does not record,
  per trial per pooled outcome, which registered endpoint supplied the number** — 28 topics are
  NOT_ASSESSABLE for that reason, which is a gap and not a clean result

### 17. A refusal to pool that never looked below the primary
- **Found** twice, and both times the answer was there. sglt2-hf's harmonisable estimand was a
  **secondary**; apixaban prophylaxis's shared estimand is a **secondary in all four trials**,
  and finding it replaced a k=1 figure measuring *bleeding* with a pool of four trials and
  13,570 participants on the review's actual question
- **Why it is the hardest class here** every other defect leaves a trace. **Withholding leaves
  none.** A review that stopped at the primaries produces an object that is internally
  consistent, arithmetically sound, and silently missing its own evidence base — so the guard
  has to be about the process, not the result
- **Detector** `scripts/lint_withholding_asked.py`, **wired**. A topic declining any outcome
  must carry, on at least one trial, evidence that ranks below the primary were read. Exit 2 if
  *no* topic declines anything — that is a broken vocabulary, not a clean corpus
- **Proven** `scripts/prove_position_and_withholding.py`, four parts, including that a topic
  which **pools** without rank evidence must pass: the property is about refusals
- **What it found on first run** 115 of 137 topics decline at least one outcome; **46 carry no
  evidence, anywhere, that anything below the primary was ever read**. Baselined and printed,
  not absolved — each is a candidate recovery of the two shapes above
- **What it cannot do** it proves *something* below the primary was read, not that the question
  was asked at every rank, and not that the answer was right. A floor, not a ceiling

---

## PARTIAL — a detector exists, and what it misses is named

### 7b. Cross-topic contamination — ROUTE 7, THROUGH A COPY, AND THE MOST ORDINARY YET
- **Found** 2026-08-19, writing the screener for `early-rhythm-control-af`. The first attempt
  was a `sed`-rename of the sibling's `screen_ablation_medical_remainder`. **It parsed cleanly,
  ran, and produced a complete set of 551 verdicts.** Every one answered the *sibling's*
  question, because its rules ask whether **ablation** is the contrast
- **Why it is the worst-looking of the seven** the six earlier routes carried one topic's data
  into another (a module constant, a dict-literal ordering, a prose string, an extraction
  table). This carries one topic's **criteria**, and the output is not corrupt, empty, or
  malformed — it is *complete, plausible and confidently wrong*
- **And the verdicts were invertible, not merely wrong.** An antiarrhythmic-drug arm is the
  **INTERVENTION** for the rhythm-control review and the **COMPARATOR** for the ablation one.
  The same arm text means opposite things to the two reviews — which is precisely why they are
  two reviews

  > **"I adapted the neighbouring topic's screener" is the single most natural thing anyone
  > will do at scale, and it is the one shape that produces a full, confident, wrong answer
  > set.**

- **Caught by** writing the known-answer check first and reading what the rules actually asked
  — not by any detector. **No guard covers this route**, and that is stated rather than
  implied: the file is new, the filename is right, the topic key is right, and every existing
  contamination guard passes
- **What would catch it** a per-topic criteria fingerprint — the screener asserting which
  review's question it implements and the runner refusing a mismatch. Named, not built

### 7. Cross-topic contamination
Five distinct routes found: `search`, `prisma`, `extraction`, prose-inside-the-duplicate-check,
and **dict-literal ordering** — literal counts placed *below* `**spec["k_cascade"]` in the same
literal silently overrode it, writing one topic's cascade onto another.

- **Detector** `_identical_output_alarm()` in `ssot/build_to_standard.py` (eight CORE cascade
  keys) plus a module-level foreign-NCT guard
- **Fires / silent** demonstrated; the fifth instance was caught *by* the identical-output
  signature
- **MISSES** contamination that changes numbers *without* making two topics identical. The
  alarm's premise is that contamination produces identical output; a partial copy that alters
  one field defeats it. **The alarm was itself defeated once tonight** by a single extra key
  (`k3_corrected_from`) making two dicts unequal while the substance was copied — fixed by
  comparing eight declared CORE keys instead of all integers
- **And my first test of it was wrong**: I planted the defect on the *object* rather than the
  *spec*, so the test passed for the wrong reason. A test that has not been shown to fail when
  the thing it tests is broken is not evidence

### 8. Wholesale-write regression
Five instances of one class: `precondition_verdict`, `k_cascade`, `prisma_flow`,
`registration_identity`, `r_output` — each written **wholesale**, each silently dropping
enrichment the object had gained since the last build. **A builder that writes wholesale
regresses every enrichment since the last build**, silently, because each block it writes is
complete and correct *in itself*.

- **Fixed systemically** with `_deep_merge` plus list-merge keyed on registration id, rather
  than per-block for a fifth time
- **Detector** the additive guard, which made it visible — **four separate times, each one
  block late**
- **MISSES** it detects the regression *after* the write. The structural fix — *every per-topic
  block is declared, merged, and verified present after write* — is designed and endorsed but
  **not yet implemented**. Until it is, the coverage is per-block and reactive

### 8b. A placeholder overwriting a resolution — the shape `_deep_merge` does not cover
**Found after this file was written, while building `iv-iron-hf`**, which is the sixth instance
of §8 and the first the merge fix could not have caught.

`_deep_merge`'s rule is *new values win*. That protects keys the spec does not mention — but
**a placeholder is a value**:

```python
_deep_merge(<resolved dict>, None)   # -> None, because the two are not both dicts
```

The builder wrote `published_comparison` wholesale as `PENDING_EXTERNAL_RESOLUTION` with
`denominator: None`. The object carried a **resolved** comparison: 11 checks, a stated
denominator (8 confirmed, 0 errors, 1 absent, 2 unresolved), a symmetry statement.

**Reporting finished verification as pending is worse than reporting nothing** — it invites the
work to be redone and silently discards the first result.

- **Detector** the additive guard fired, aborted, and restored — **one block late**, again
- **Fix** a placeholder is written only where no resolution exists
- **The lesson generalises past this field:** the fix written after four instances of a class
  was insufficient for the fifth *shape* of it. **A systemic fix is only systemic over the
  shapes you had seen when you wrote it.**

### 8c. A verdict that cannot report anything but refusal
`P7_published_comparison` was **hardcoded** to `REFUSING` with a fixed message, so it could not
report anything else no matter what the object held.

> A property that can only ever refuse is not a check, in the same way that a liveness probe
> that can only report "alive" is not a check.

Notable because it failed in the **under-reporting** direction — the page announced as pending
a piece of verification that was complete. Every guard in this repo was built against
overclaiming; this one quietly understated the work. See E4.

- **Fix** the verdict is computed from the object
- **Verified not a loosening**, and checked rather than assumed: `sglt2-hf` and
  `bempedoic-acid-review` have no denominator and no checks, and both **stay REFUSING**.
  Exactly one topic moved, and it is the one carrying the evidence
- **MISSES** no detector enumerates property verdicts that are literal constants rather than
  functions of the object. **Buildable** — an AST walk for `prop(<CONST>, "...")` with no
  branch on object state. Related to detector 5b (verdict unit). Not built; see E7

### 9. Stale artefact passing a freshness gate
A build failed with `KeyError`; `curl` returned **200** for a five-hour-old file; the gate
passed. **An exit code cannot distinguish "ran and passed" from "never ran".**

- **Detector** served-bytes verification with md5 compared against on-disk, plus
  `scripts/known_answer_gate.py`, which requires **positive evidence of execution** (a floor on
  observed `[ok ]` lines) rather than a zero exit
- **MISSES** it verifies the *served* artefact matches disk. It does not verify that what is on
  disk was produced by the *current* inputs — a build that succeeds while reading a stale cache
  still passes

### 10. Hardcoded vocabulary that the corpus does not use
A check hardcoded `"experimental"` while the corpus writes `treatment`/`control` → **five false
FAILs on live topics**.

- **Fixed** by declaring the vocabulary explicitly (`TOPIC_ARM_ROLES`/`CONTROL_ARM_ROLES`, with
  ambiguous `"active"`/`"intervention"` removed so they resolve to unknown → `NOT_ASSESSABLE`)
- **The lesson is the durable part:** *the known answer must come from the data, never from a
  fixture the author invented.* A fixture written by the author of the check tests the author's
  belief, not the corpus
- **MISSES** no detector enumerates vocabularies used by checks and diffs them against values
  actually present in `ssot/**/*.json`. **That is a buildable detector and it is not built.**
  See exposure E3

---

## OPEN — named, with the reason

### E1. Substring is not identity — **FIRED. No longer hypothetical.**

> **An exposure written down and left open is not a managed risk. It is a defect waiting for
> its turn.**

This entry was recorded as OPEN and "not lintable" — and then caused a real defect **on the very
next topic built**, in the withholding direction, on **five of six** included trials of a
canonical drug-versus-placebo review.

`alirocumab-lipid`'s ODYSSEY registrations name the placebo arm's intervention
`Drug: Placebo (for alirocumab)`. The substring matched, `_drug_named_in_arm` reported the drug
in **both** arms, and `locate()` classified the randomised contrast as background therapy.

**Worse than the arm-type defect, and the reason is the scale of the convention rather than the
size of the topic:** 49 of 582 intervention records to hand (**8.4%**) name the drug their
placebo substitutes for. That is an industry naming convention, not one registry's data entry,
so the exposure was corpus-wide the whole time it sat in this file marked OPEN.

**Now PARTIAL.** Not lintable in general — deciding whether two strings denote the same entity is
semantic judgement. Decidable *here*, because a placebo **declares itself in the same field**:
its name begins with `placebo`/`sham`/`vehicle`/`dummy`. The pattern is **anchored**, so
`empagliflozin plus placebo` is untouched — there the drug genuinely is present.

- **Fires** alirocumab included set 1/6 → **6/6**; k0 99, experimental 74 → 87, background 18 → 6
- **Not a loosening**, tested the same way the arm-type fix was: `iv-iron-hf` **unmoved** at
  34/6/5/2, and EASi-HF still returns BACKGROUND — it really does give empagliflozin in both
  arms, under its own name, which is what the both-arms rule exists for
- **Still residual:** the general class. A topic whose drug name is a substring of an unrelated
  one remains unguarded

**What this entry now means for the rest of the file.** Every OPEN entry below should be read as
a live hazard with an unknown fuse, not as a risk that has been accepted. This one's fuse was
one topic long.

### E2. Citation from recall — the §1–§3 class applied to methodological authority
Handbook citations were wrong in three ways at once: two sections misnumbered, one box
(`Box 10.10.a`) **nonexistent**, and the stated rule **backwards**.

Currently held by `HANDBOOK_AUTHORITY` failing closed plus `SECTION_VERIFIED_ON = "2026-08-19"`
— a date, verified by a person, that goes stale silently.

**Why it is open rather than closed:** the identifier detector works because ClinicalTrials.gov
publishes a machine-readable record to check against. The Handbook does not. A detector would
need a licensed local corpus of section headings; **without one, "cite only what you have
opened" is a convention.** A section cited from recall is the identifier-by-recall defect
wearing methodological clothes, and it is the **highest-value open exposure** because it is the
same class as the two prioritised tonight, with no registry behind it.

### E3. A check whose vocabulary does not match the corpus
The general form of §10. No detector cross-references the literal values a check tests for
against the values present in the corpus, so a check can be silently vacuous — testing for a
string nothing ever writes and passing everything forever.

**This is mechanically detectable and is the clearest next build**: extract string literals
compared against object fields, and report any that appear zero times in `ssot/**/*.json`.
Not built tonight; named rather than implied.

### E4. Withholding — **now PARTIAL, no longer open**
> **Every guard we have catches overreach; nothing catches restraint.**

That sentence was written as a limitation. `scripts/lint_restraint.py` is the attempt to stop it
being one, built on the only method that has actually worked against this class: **two
independent instruments over the same object, where a refusal by one and a decision by the
other is a candidate for review rather than a safe default.**

`NOT_ASSESSABLE` remains the correct third state. The claim is narrower: a refusal is safe only
where *nothing else can decide*. Where something else **has** decided, the refusal is a
disagreement, and an unexamined disagreement is indistinguishable from a silent loss.

- **Lane 1** the object *includes* a trial (a recorded screening decision); `locate()`
  independently classifies the same registration from the raw payload. Anything but
  `experimental` is the AFFIRM-AHF/HEART-FID signature
- **Lane 2** a precondition returns `NOT_ASSESSABLE` citing absence while the field it names is
  present and non-empty — a read failure wearing the third state's clothes, which is how §8c
  happened
- **Fires** the discriminator was disabled to restore the *historical* classifier, and the
  detector returned exactly **NCT02937454 (AFFIRM-AHF)** and **NCT03037931 (HEART-FID)** — the
  two trials that were in fact being withheld. **The known answer came from the data, not from
  a fixture the author invented**, which is the standard §10 exists to enforce
- **Silent** current corpus → 0 candidates, exit 0
- **Ratchet, and the reason is stated**: findings are disagreements, not proven defects — some
  will be the classifier right and the inclusion wrong, which is equally worth having. Blocking
  on nonzero would force every one to be adjudicated before any unrelated commit

**WHAT IT DOES NOT COVER, AND IT IS THE LARGER HALF.** Lane 1 reads a topic's *included* trials.
It reproduces the `iv-iron-hf` shape exactly and would **not** have caught the `sglt2-hf` ten —
those were withheld at the *surfaced* stage, so they never entered the included set.

> **The larger half of a withholding defect is invisible to a check that reads the object,
> because withholding is precisely what keeps things out of the object.**

Closing it needs the executed search payload per topic as instrument A (surfaced set vs
classifier verdict); that payload is currently stored for one topic. And coverage is small and
says so: **2 topics checked, 133 unchecked**, each unchecked topic named rather than skipped.

The original limitation, which stands as the reason this entry is PARTIAL and not CLOSED:

The arm-role classifier read registry arm types literally and was silently *shrinking* evidence
bases corpus-wide — ten trials on `sglt2-hf` alone. It was found only because two instruments
cross-checked: the executed search surfaced a topic's *own included trials*, and the classifier
then refused to recognise two of them. **Neither instrument found it alone**, and this was the
first defect all night found in the withholding direction by an instrument rather than a person.

A guard cannot easily fire on evidence that was never admitted, because the missing thing leaves
no trace in the object. The partial mitigation is the cross-check pattern above, which is a
*procedure*, not a detector. **Structurally the hardest open exposure**, and the one most likely
to be silently costing accuracy right now.

### E5. Warnings treated as output
A warning from an interpreter or tool is an instrument declaring itself broken; reading past it
treats a broken instrument's output as data. Held by rule, not by mechanism — and it paid
tonight: following one `SyntaxWarning` at commit produced detector §2. **Not lintable in
general** (it depends on which tool emits what, in which context), but see E6.

### E6. Gates whose warnings are discarded
`.githooks/pre-commit` sends detector stdout to `/dev/null`. `stderr` leaks, which is the **only
reason** the `SyntaxWarning` behind §2 was ever seen. A gate whose diagnostic output is silently
discarded can degrade without anyone noticing.
**Buildable and not built:** run each gate with `-W error::SyntaxWarning` and refuse on any
warning. Named because the alternative is discovering it by luck a second time.

---

### E8. A build path nobody can name
Two pages were rebuilt and re-gated in served bytes on 2026-08-19. Hours later, in the same
session, **the route used to build them could not be stated** — `project_topic_page.py` refused
(no `render` list on the object) and `build_to_standard.py` writes only JSON. The path had to be
recovered from the commit diff by identifying which module emits the `Page standard` card.

> **A build path nobody can name is a build path nobody can audit.** It is also one nobody can
> reproduce, which makes every artefact it produced unverifiable in principle.

The route is:

```sh
python ssot/build_tabbed.py <object.json> <out.html>      # object -> page
python ssot/build_to_standard.py <topic>                  # object only, no HTML
python scripts/project_topic_page.py <page> <object>      # REFUSES without a `render` list
```

**Now PARTIAL — `scripts/generator_stamp_gate.py`.** `build_tabbed.py` already emitted an honest
stamp (it reports DIRTY for uncommitted generator code and UNKNOWN when git is unavailable,
rather than guessing), so the recording was never the gap. **The gap was the assertion**: nothing
checked that the stamp on a shipped page named anything real.

The gate asserts, on the page's actual bytes: the stamp is present; the commit it names
**resolves** via `git cat-file -e`; it is not `UNKNOWN`; and a DIRTY stamp **blocks** rather than
merely warning — a page built from uncommitted generator code cannot be reproduced from its
stamp, and that sentence should be a gate, not prose a reader may or may not notice.

- **Fires** on all four failure modes, each planted separately: no stamp; a stamp naming a
  nonexistent commit (`deadbeef1`); `UNKNOWN`; and built-from-uncommitted
- **Silent** the 3 gated pages → OK, exit 0
- **MISSES, named rather than implied:** it asserts the stamp is **traceable**, not that it is
  **true**. Re-running the generator and comparing bytes would settle it and costs a full page
  build per page. That is the residual half of E8.

### E7. Asserted verdicts — a property whose value is a constant

**Swept corpus-wide by Codex (openai family) on 2026-08-19, independent of the lane that found
the class.** 580 files, 0 parse failures, **28 findings**: 6 of signature (a) `prop(<CONST>,…)`,
2 of (b) same verdict on every path, 14 of (c) hardcoded verdict payload, 6 of (d) a validation
command with no failing process outcome. Two categories it was asked about returned **zero**
(`passed` / `valid` literal keys), and it said so rather than filling them.

**Verified rather than accepted — a sample of 5, all 5 confirmed as described.** Agent findings
have a history in this project of flagging correct code, so the sweep's output is evidence to
check, not a result to adopt.

**And the honest severity is lower than the count suggests, which is the part worth recording.**
Four files *named* `*_gate.py` — `internal_consistency_gate`, `arm_role_gate`,
`metric_consistency_gate`, `subject_role_gate` — have **no failing exit at all**: confirmed
independently, they can only ever pass. But none is wired into `.githooks/pre-commit` or any
runner, so **nothing currently gates on them**. They are dormant reports carrying gate names.

> A file named `*_gate.py` that cannot fail is not presently a defect — it is a **trap for
> whoever wires it in next**, who will reasonably assume a thing called a gate can block.

Likewise `r_validate.py` counts failures, prints `Failed: N`, and exits 0 — defensible for a
reporting tool, and it is not wired as a gate either. Codex's category (d) is broader than the
defect, and that is recorded here rather than quietly dropped.

**Still OPEN, and deliberately.** The sweep produced a list; it did not produce a detector. The
buildable form remains an AST walk for `prop()` calls whose verdict argument is a constant and
whose enclosing block never references the object, plus a check that any file matching
`*_gate.py` contains a reachable non-zero exit. Findings on file, detector not written.

The general form of §8c: a `prop(REFUSING, …)` with no branch on object state is a verdict
**decided when the code was written**, not derived from what is on the page.

**This entry exists because two new classes (8b, 8c) were found within the hour after this file
was written, while doing ordinary build work.** The registry is a snapshot of what has been
noticed, not a proof of what remains — and the honest form of that is to keep adding to it
rather than to present it as complete.

---

### E9. Absence of a count is not a count of zero — **corpus-wide, and large**

**Codex census, 2026-08-19, verified independently: of 135 topic objects, 3 carry a
`k_cascade`. 132 do not.**

The census also reports **0 topics with a nonzero unscreened remainder** — which is true, and
which read alone is one of the most misleading numbers this project could publish. It is zero
because 132 topics **never counted k at all**. The three that do are exactly the three built to
the standard tonight.

> **A corpus of 135 topics reporting "0 unscreened remainder" is not a clean backlog. It is 132
> topics that have never been asked the question.**

The census earns its keep precisely by refusing to conflate the two: `NO_CASCADE` is reported as
a distinct state from `remainder: 0`, and `REMAINDER_ABSENT` as a third. Had it folded them, the
corpus would appear fully screened.

This is E4 wearing corpus clothing — withholding at the level of the whole project rather than
one classifier. **No detector is needed to find it; it is now measured.** What is open is the
work: 132 topics owe a cascade. Recorded here so the number cannot quietly become "we screened
everything".

Also verified: 0 topics where `k_included_in_object > k3_experimental` (arithmetically
impossible), and 0 parse errors across 135 objects.

### E10. Classes an outside critic named that this registry did not have
**agy / Gemini 3.1 Pro, asked to name what is MISSING rather than to review what is present.**
Eight returned; these are the ones this repo can neither rule out nor currently detect:

| class | why it is invisible to everything above |
|---|---|
| **Pagination cursor abandonment** | a fetcher takes page 1 and stops, omitting evidence **without raising** — silent omission, the withholding family, at the retrieval layer *before any object exists* |
| **Order-dependent processing** | a pool that changes with input order; every existing check reads one final state and cannot see it |
| **Denominator mismatch** | a rate divided by enrolled rather than ITT — every field involved is individually valid |
| **Float precision loss in log-pooling** | underflow/rounding in intermediate transforms; the output is a plausible number |
| **Implicit type coercion** | an identifier cast to numeric, stripping leading zeros — would defeat the identifier detector, which assumes the id survived as text |

Pagination abandonment is the one to build first, because it sits at **the surfacing stage** —
the place E4's own statement identifies as where the remaining withholding exposure lives, and
the one place nothing in this repository currently looks. Tonight's own searches are clean by
inspection (`totalCount 47`, 47 returned), but that is one topic checked by hand, not a check.

**None of these is detected. They are listed because a registry that only contains classes its
authors thought of is a measure of imagination, not of exposure** — and asking a different model
family what was missing cost one call.

## What this file does not claim

It does not claim the corpus is free of these defects. It claims that for **CLOSED** entries a
new instance is rejected at commit, and that for every other class the gap is named with its
reason rather than left to be rediscovered.

Six classes are closed, six are partial with the uncovered part stated, and seven are open.
**Three of the open seven (E3, E6, E7) are mechanically buildable and were simply not built** —
they are listed as exposures rather than as future work, because "we wrote it down" is the
status this file exists to refuse.

Nor does it claim to be finished. Two classes (§8b, §8c) were found **within the hour after it
was written**, during ordinary build work, and one of them defeated a fix authored earlier the
same night specifically to close its family. The count above will be wrong again.

*Verified 2026-08-19. Every command in this file was run; every count is an observed output.*
