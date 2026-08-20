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

## AND ITS OTHER HALF: A RULE YOU HAVE APPLIED IS NOT A RULE YOU HAVE PUBLISHED

**Added 2026-08-19, from the apixaban split.** The criterion separating
`apixaban-vte-treatment` from `apixaban-vte-prophylaxis` — *extended anticoagulation in
patients who have ALREADY HAD a venous thromboembolism is treatment; primary prophylaxis in
patients who have not is prevention* — **decided which of two reviews sixteen trials belong
to**, and existed only inside `evidence/2026-08-19-batch1/apixaban_adjudication.json`.

Neither page stated it. A reader could not check it and the next lane could not apply it.
**A criterion that decides inclusion and is published nowhere is not a criterion; it is a
habit.** It is now on both objects at `screening.boundary_criterion`, and in the prose a
reader actually meets, at `screening.eligibility`.

**And the half above applies to it too, which is why this is not a tidy-up.** The boundary
reached the *sixteen* trials sent to adjudication. The *nine* admitted by the mechanical screen
were admitted on `designModule.designInfo.primaryPurpose` — **the coded field these very
criteria say does not settle the question** — and were put to the boundary for the first time
on 2026-08-19, in the build that published it.

> A rule can be written, applied to part of its domain, and published nowhere, all at once.
> The three are independent and each needs its own check.

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

## A NULL CURSOR IS NOT A PROOF — the converse of class 20, and it was never tested

**Read this beside the transport finding.** Class 20 established one direction and the corpus
then assumed the other for free.

| | |
|---|---|
| **established** (class 20) | a **live** `next_page_token` means the search is **incomplete** |
| **assumed ever since** | a **null** token means the search is **complete** |

**The second was never tested**, because on `colchicine-cvd-review` both proofs agreed —
`100 + 37 = 137 == totalCount`, cursor null — so the weaker one always had the stronger one
standing behind it.

> **On `acs-antiplatelet-review` they disagreed.** `100 + 100 + 3 = 203` records returned with
> the cursor **null**, against a reported `totalCount` of **430**.
>
> **227 records the pagination never returned, while the cursor said it was done.**

**THE PROOF IS THE SUM ACROSS PAGES RECONCILED AGAINST `totalCount`. THE NULL CURSOR IS
CORROBORATION AND NEVER THE PROOF.** *Why* the API stopped early is **not diagnosed** — a
server-side cap, a differently-scoped total, something else. The discrepancy is recorded rather
than explained, because writing down a guessed cause is worse than naming the gap.

**And it is P16's fourth clause once more:** the reconciliation check existed and had never had
an opportunity to fail. A guard whose triggering condition has never arisen is unproven however
green it reads.

### The damage was bounded before anything else was built

`scripts/audit_null_cursor_evidence.py` re-checked **every search row in the corpus** — 46 rows
across 18 objects and 6 evidence records — asking which evidence each one actually rests on:

| state | rows |
|---|---:|
| **RECONCILES** — `returned == total`, so the proof holds regardless of the cursor | **30** |
| SHORTFALL_DECLARED — legitimate under class 20 | 8 |
| NOT_EXECUTED — a database the row records as not searched | 6 |
| NOT_ASSESSABLE — states neither count | 2 |
| **CURSOR_ONLY_UNPROVEN** | **0** |
| **SHORTFALL_UNDECLARED** | **0** |
| **topics with a built page resting on an unproven row** | **0** |

**No delivered page rests on a null cursor alone.** The exposure is confined to
`acs-antiplatelet-review`, which declared its shortfall and on which **nothing was built**.

`scripts/verify_search_record_reconciles.py` gains the verdict
`CURSOR_SAID_DONE_BUT_THE_SUM_DOES_NOT_RECONCILE`, which runs even when a record lists no
identifiers — page counts and a total are enough. **And an absent token field is not a null
one:** reading a missing `next_page_token` as *"the cursor said done"* would convict a record of
a proof it never offered. Silence is not a claim.

### The audit's own five false readings, kept as the lesson

Its first run reported **five NOT_ASSESSABLE rows** — `arni-hfref` twice and three colchicine
records. **All five were the audit failing to look**, not the corpus failing to record:
`arni-hfref` spells them `hit_count` / `records_retrieved`, and two records nest theirs under
`counts` and `PAGINATION_SHORTFALL_DECLARED`.

> **That is class 25 inside the instrument written to bound class 20.** Chasing key names is
> endless and is itself the trap, so the durable fix is the one that works on every form of it:
> **a NOT_ASSESSABLE now prints the keys the row actually has and the keys it looked for.** An
> unassessable verdict that does not say what it looked at is not refutable.

---

## THE SECOND HEADLINE — 80 of 135 topics state a question at all

**Measured 2026-08-19, and measured only because a blind cross-family reader said so without
being asked.** agy (Gemini 3.1 Pro, google family) was given twelve merge clusters with no topic
names, no verdicts and no hint that a decision depended on the answer. It returned **UNCLEAR on
ten of twelve**, and its stated reason every time was that the question field is *auto-generated
boilerplate*.

| state | topics | |
|---|---:|---:|
| **states a question** | **80** | 59.3% |
| templated — the title plus `on each trial's own registered primary outcome?` | 34 | 25.2% |
| an echo of its own title | 20 | 14.8% |
| absent | 1 | 0.7% |

*(135 live topics; 10 retired tombstones excluded from the denominator.)*

> **A templated question is not a bad question. It is an ABSENT one wearing the shape of a
> present one** — and that is the 3-of-135 shape from the headline above, on a different field.

**This gates how much any question-based check can ever claim.** P21's ambiguous-question split
cannot find an ambiguity in a title. The merge adjudicator's `questions_differ()` returns FALSE
for a templated question — **correct as logic, and it reports as though the axis had been
checked when it had not been.** agy's UNCLEAR is the honest label and it is adopted.

**Therefore, stated plainly: the nine executed merges rest on identical trial sets, a richer
survivor, a proven union and reversibility — NOT on a comparison of questions.** For ten of the
twelve clusters there was no question to compare. That is a stronger position honestly stated
than a weaker one asserted.

`scripts/audit_templated_questions.py`. **Corrects an earlier claim in this session's own
reporting** of "37 of 144", which used a denominator including retired tombstones and counted
only one of the three non-stating forms.

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
- **AND THEN IT WENT THE OTHER WAY, WHICH IS THE MOST IMPORTANT LINE IN THIS ENTRY.** Every
  instance above is a RECOVERY, and a check that has only ever returned the convenient answer
  is indistinguishable from no check at all. A reader seeing only recoveries would be right to
  suspect the question is asked until it gives the answer we want.

  | review | poolable set | direction |
  |---|---|---|
  | `apixaban-vte-prophylaxis` | **3 → 8** | the question RECOVERED a pool |
  | `apixaban-vte-treatment` | **8 → 3** | the question DISSOLVED one |

  One search, one drug, one night, one discipline, opposite answers. The fall cost the
  treatment review **the two largest trials in its field** — AMPLIFY and AMPLIFY-EXT post no
  recurrent-VTE measure without a death term at any of their 21 and 22 registered ranks.

  > **Asking the withholding question is not a way of finding more trials. It is a way of
  > finding out.** The refutation arose on its own; it was not sought and it was not designed,
  > which is exactly what makes it evidence that the procedure has no built-in direction.

  **Neither number is publishable without the other**, and that is now enforced rather than
  remembered — see the second detector below
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
- **Second detector, for the direction** `scripts/lint_withholding_direction_paired.py`,
  **wired**. An object stating its own withholding direction must name a counter-instance that
  **exists**, **points back**, and **runs the other way**. Two recoveries dressed as a pair is
  refused as `NOT_A_PAIR` — that would be the original defect wearing the fix's clothes
- **Proven** `--selftest`, five cases against the real objects and no synthetic fixture,
  including **the state that would have shipped**: the prophylaxis recovery with no
  counter-instance, which is exactly what the object held at `f97f82d0e`
- **What neither can do** the first proves *something* below the primary was read, not that the
  question was asked at every rank, and not that the answer was right. The second compares two
  declarations to each other and never to the object's own k — a topic could declare UP while
  its k fell and pass, which is what `lint_block_contradicts_object.py` is for. A floor, not a
  ceiling

### 26. A DESTRUCTIVE ACTION AUTHORISED BY A FALSE FINDING — *the audit nearly destroyed the thing it was auditing*

**Found 2026-08-19. The most dangerous shape this project has produced**, and the first whose
failure mode is not a wrong number published but **a correct operator acting correctly on
information their own instrument manufactured.**

#### The sentence that matters

> **I was one command from a `git checkout -- ssot/` justified entirely by a belief my own
> instrument had produced.**

At that moment the reasoning was sound, the intent was conservative, and the command was the
right one *for the situation as reported*. Every guard in this repository would have permitted
it, because it was not a bad write — it was a **restore**, the safest-looking operation there
is. Only the premise was false.

#### The sequence — four instruments, four false findings, each triggered by the last

| # | the instrument | what it reported | what was true |
|---|---|---|---|
| 1 | a tombstone audit reading `THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT` **one level down** | all ten tombstones had lost their objects; `trials_it_held` blank | true of the **working tree**, which held an *uncommitted second run of the merge executor* (mtime 16:36:01, eight minutes after the merge commit). The committed corpus was correct throughout. **Cause identified — see below.** |
| 2 | the comparison written to settle #1, using `subprocess.run(text=True)` with **no `encoding=`** | the committed object carried mojibake — `AUC0-âˆž` against `AUC0-∞`; **HEAD was the corrupted side** | the *decoder* was the corrupted side. Re-run with `encoding='utf-8'`: nineteen files match HEAD exactly, 240 objects scan clean. **← the `git checkout` was authorised here** |
| 3 | the repair written after #2, reading pages with universal newlines | an 18-character fix | a **40,946-line diff** that silently rewrote CRLF→LF across seven *delivered* pages. Caught only by reading the commit stat; amended away before pushing. |
| 4 | the heredoc carrying the patch that fixed #3 | a valid patch | `\r\n` arrived as a literal newline and broke the file. Eleventh instance of a rule stated in the brief's first paragraph. |

**Each investigation created the defect the next one investigated.** That is the property to
notice: not that four tools were wrong, but that the errors were *serially generated by the act
of looking*.

#### CLOSED: the anomaly at step 1 has a cause, and it is a third layer

**Recorded 2026-08-19, later the same day.** Step 1 above was left as *"an uncommitted second run
of the merge executor"* with no explanation of why such a run existed or what it did. It is now
identified: **`execute_merges_2026_08_19.py` was never idempotent.**

Re-running it against an already-merged cluster re-absorbs an **already-tombstoned** object into
the survivor and wraps the tombstone in a further retirement layer — whose own `state` then reads
`RETIRED`, so `THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT` comes to hold a copy of the *retirement
record* rather than the object. That is exactly the nineteen files, exactly the extra nesting
level, and exactly the blanked `trials_it_held`. Confirmed by a later dry run, which proposed to
re-merge **all nine completed clusters**.

So the full sequence has three layers, not two:

| layer | what happened |
|---|---|
| 1 | **a non-idempotent tool produced real changes** — genuine, uncommitted, and unexplained |
| 2 | **an instrument misread them as corruption** — an audit reading one level down |
| 3 | **a false finding nearly authorised a destructive fix** — the `git checkout` |

Each layer is individually ordinary. The composition is what nearly did damage, and **only the
contradiction in one instrument's own output stopped it.**

The executor now skips a cluster whose retirees are already tombstones and **refuses** a
partially-merged one rather than guessing. The entry above is corrected from *cause unknown* to
*cause identified*: an anomaly that is later explained is worth more than one left open, because
an open anomaly stays available as a false premise for the next decision.

#### Why the guard set does not defend against this

Every mechanism here — the pre-commit hooks, the union proofs, the projection gate, the
`STAGING_WIDE` discipline, "never net-delete from `ssot/**`" — protects **the corpus from bad
writes**. Not one of them protects **a correct operator from bad information**. A `git checkout`
that discards an uncommitted state is not a bad write by any test they apply; it is a routine
restore, and the guards are silent by design.

> The threat model was always *the writer is careless*. This is *the writer is careful and the
> evidence is wrong* — and the evidence was wrong because the writer's own tool produced it.

#### What actually stopped it

Not a guard. **A contradiction that could not be explained away**: the leaf-count check said
`net delete: 0` while the same run listed specific pairs as lost. Two outputs of one script
disagreeing, which forced the question *why* before the question *what now*. Had the check
reported only the lost pairs — the more natural design — the revert would have gone ahead.

#### The rules this yields, stated as rules

1. **A finding that authorises a destructive action must be re-derived by an independent route
   before the action is taken.** Not re-run — *re-derived*, by a tool that does not share the
   reading path. Both false findings survived re-running.
2. **Name the decoder, always.** `subprocess.run(text=True)` without `encoding=` is now a
   ratcheted lint (`scripts/lint_subprocess_decode.py`, baseline 16) — and it caught the
   seventeenth site in the very commit that documented the class.
3. **An unexplained contradiction between two outputs of one instrument outranks either
   output.** Design checks to emit a redundant second signal precisely so the contradiction can
   appear.
4. **A dirty working tree is not evidence about the repository.** Any audit comparing to git
   must first establish whether what it is reading is committed, and say which it read.

**Status: PARTIAL.** Rule 2 is mechanised. Rules 1, 3 and 4 are not, and rule 4 is the one that
would have caught this at step one — an audit that refuses to report on files with uncommitted
modifications until it says so. Recorded as not written.

### 53. WHEN ONE FIGURE IS DEFENSIBLE UNDER TWO DEFINITIONS THAT DISAGREE, REPORT BOTH

**Neither counter was wrong. Reporting one number was.**

`p46_queue.py` scores a **discharged refusal as complete**, and that is correct: a held-only
counter reports a correctly-refusing topic as incomplete forever, and someone eventually
"fixes" it by writing into a slot that should stay empty. So the counter's definition is
sound.

And under it, **5 of 9 complete topics close on a refusal P46's own refinement was written
to exclude** — *"no risk-of-bias assessment was recoverable from the page"* is an obstacle
in OUR QUEUE wearing a refusal's clothes. Also true. **The count was not wrong; it was
one-dimensional.**

Same shape, twice more the same night:

| one figure | the two definitions | what the single number hid |
|---|---|---|
| "9 of 28 complete" | held-only vs held-or-discharged | 5 of 9 discharge on provenance |
| "27 sections, 5,111 words" | section count vs substance | SGLT2 and ARNI read as siblings while one is empty where a reader looks |
| "question-shaped headings 57% vs 2%" | grammar vs answeredness | a criterion satisfiable by renaming |

> **A single defensible figure is not the same as a sufficient one.** Where two honest
> definitions of the same quantity disagree, the disagreement IS the finding — report both
> and let the gap carry the information. Choosing one and defending it is how softness
> becomes invisible while every individual claim stays true.

**Operationally:** P46 is now always reported as *"N of 28, of which M close on a
provenance-shaped refusal"*, beside P47. `scripts/audit_p46_closure_quality.py` computes M.

### 52. A CHECK REPORTING ZERO HAS TWO READINGS AND ONLY ONE OF THEM IS REASSURING

**Three instances in one night, and every time the two-state instrument returned the
comforting one.**

| the zero | comforting reading | true reading |
|---|---|---|
| resolver sweep: 0 resolvers in 782 files | no resolver has this shape | `^(\s*)def` ate the newlines; every body was empty |
| `rapidmeta:pooled-estimate content="NONE"`: 0 pages | no page needs the withdrawn state | **no page emits the tag; the branch had never executed** |
| `wrong_protocol_link`: 0 on every run ever | no page has a wrong protocol link | **`arni_hf_protocol` appears on 0 of 888 pages; the marker does not exist** |

The last two are in the **same file**, `scripts/regression_check.py`, and `wrong_protocol_link`
is **in the blocking set**. Two of two examined. That is not a rate, but it says **the file's
clean signals are the ones to distrust, not its firing ones.**

**The rule is not "check your regexes".** It is:

> **EVERY ZERO MUST STATE WHICH OF THE TWO IT IS, AND A CHECK THAT CANNOT TELL MUST RETURN
> `NOT_ASSESSABLE` — NEVER `PASS`.**

Built into three instruments tonight as local decisions — the resolver sweep, the
reader-facing lint, the containment lint. **It is the file's standard from here, not three
local decisions.** A zero is a measurement of the instrument until it is shown to be a
measurement of the world: name the population searched, and refuse when that population is
empty.

### 51. AN UNEXPECTEDLY LARGE NUMBER FROM A NEW MEASUREMENT IS WHERE CHECKING IS MOST URGENT

**And it was treated as a finding instead — in the measuring AND in the relaying.**

The reading-order rollout reported **416,310 words across 42 skipped pages**, against a
projected corpus averaging ~5,000 words a page. That is a startling number, and it was
relayed onward twice as evidence for a hypothesis: *the best prose in the project may sit
outside the objects, in pages no generator produced.*

**The premise did not exist.** The rollout measured with `re.sub(r"<[^>]+>", " ", t)`, which
strips TAGS but keeps the CONTENTS of `<script>` and `<style>`. The true visible volume is
**66,407 words** — the figure was 6.3× JavaScript. `EVOLOCUMAB_ASCVD_AUTO_2` measured 29,568
that way and has **3,055 visible words**. The legacy pages are SHORTER than the projected
ones, not longer, and the hypothesis had nothing under it.

It cost an hour of two people's attention, and it was interesting **in exactly the way the
thirteen artefacts were interesting.** Same shape as the stale 10.9%: *a stale or wrong
number does its damage by being repeated, not by sitting in a file.*

> **A new measurement's most surprising output is a claim about the measurement.** Check it
> before it is relayed — the relaying is where the cost is incurred, and the person relaying
> it inherits the error whether or not they made it.

### 50. A PAGE-SCALE COMPLIANCE APPARATUS ASSERTING RIGOUR NO RESULT REQUIRED

`ACS_ANTIPLATELET_REVIEW.html`: **78 numbered headings** — *"1. Registration & Administrative
Information [PRISMA #24, AMSTAR #2]"*, *"11. AMSTAR 2 Critical Domains Compliance"* — a table
of generic **criteria for downgrading**, and **zero effect-estimate-shaped strings on the
entire page.** Its object publishes **no pooled estimate at all**.

**This is the `paper-studio.js` failure at page scale.** There, a FORMATTING control
manufactured a Methods section no field supported. Here an entire PRISMA/AMSTAR apparatus is
asserted around a review that pools nothing — every heading a claim about procedure, none of
them tied to a result, because there is no result.

**It is worse than an empty page, because it reads as thorough.** A reader meeting 78
compliance headings concludes the opposite of the truth.

> **And it is the strongest argument yet for weighting P47 by SECTION rather than by PAGE.**
> On totals this page looks substantial: 3,147 words, 78 headings. Both numbers say
> "complete". Every one of the four reader-facing sections is empty of findings because
> there are none.

### 49. THE SKIP CRITERION SELECTED LIVE PAGES OUT OF A CORPUS-WIDE FIX

The reading-order rollout skipped any page with zero `paper-*` sections, reasoning that such
a page "was not built by this generator, so rebuilding it is a replacement rather than a
re-ordering". **Sound for a genuinely old page. Not sound for a CURRENT page that simply has
no paper tab** — and the criterion could not tell them apart.

Measured by `scripts/audit_skipped_but_current.py` over all 42 skipped pages, discriminating
on markers this generator emits rather than on the absence of one feature of it:

| | pages |
|---|---:|
| **current generator, no paper tab — WRONGLY EXCLUDED** | **3** |
| old PRISMA/AMSTAR template — correctly skipped | 15 |
| neither marker — **UNCLASSIFIED, which is not "old"** | 24 |

**And two of the three do not serve a pooled point their own object holds:**

    BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html   object holds -55.24, page shows it nowhere
    CANGRELOR_PCI_REVIEW.html                 object holds 0.9646, page shows it nowhere

**Found by accident**, while sampling the skipped set for an unrelated question. A guard
written to prevent content loss instead excluded live pages from a fix — and hid, inside the
excluded set, the most direct form of delivery diverging from the object there is.

> **A skip criterion is a claim about the population it excludes.** State it as a property
> the excluded pages HAVE, not as the absence of a property they lack — absence has many
> causes and only one of them is the one meant.

### 48. THE INSTRUMENTS ARE NOW A LARGER SOURCE OF DEFECTS THAN THE DATA IS

**This is the most important structural fact of 2026-08-20 and it outranks every individual
finding on this page.** Recorded here rather than left in a session, because it should shape
the plan rather than be rediscovered.

In one night the CORPUS produced a handful of real findings — the co-primary class, the
swapped arm labels, `rosuvastatin`'s absent estimand, `empagliflozin`'s inverted question.

**The TOOLING produced more, and here they are counted:**

| # | instrument | what it did |
|---:|---|---|
| 1 | `lint_registration_counts_arm_order.py` | compared an odds ratio against four stored **hazard** ratios and reported them as unaccountable. A test that could not pass |
| 2 | `lint_method_claim_has_a_field.py` | **5 of 8** path declarations wrong; called the flagship a liar twice |
| 3 | ↳ its wildcard | returned a **container where a leaf was named** — see class 47 |
| 4 | `audit_path_resolvers.py` | `^(\s*)def` under `re.M` ate the newlines; reported **zero resolvers across 782 files** — see class 47 |
| 5 | `apply_reml_corpus.py` | wrote the disclosure to `read_the_width_with_care`, a field **no renderer reads**, one minute after writing "asserting the write is not the test" |
| 6 | `apply_reml_corpus.py` | rounded to 4 **decimals** where the page renders 4 **significant figures**; the stored string would have appeared nowhere in the delivered bytes |
| 7 | `apply_reml_corpus.py` | LF→CRLF on write: a **9,151-line diff** for a ~250-line change |
| 8 | the rollout driver | `capture_output=True, text=True` — a locale-codec decode hazard, caught by a gate |
| 9 | the P47 near-miss sweep | flagged **26**, of which **25** were false positives |

**Nine against a handful.** And the gates that caught most of them were built to guard the
corpus: `lint_subprocess_decode`, `lint_pooled_point_is_displayable`, `standard_version_
agreement_gate`, `lint_primary_by_position`, `manuscript_guard`, `generator_stamp_gate`.
**Every one of them refused the toolmaker rather than the data.**

**THE OPERATIONAL FORM, and it would have caught five of tonight's nine on their first run:**

> **A new instrument is assumed defective until it has refused something real, and its
> first finding is a claim about the instrument until checked against a known answer.**

Applied to tonight: the OR-versus-HR lint's first finding was four "unaccountable" hazard
ratios — a claim about the lint. The method-claim detector's first finding was that the
flagship asserts two methods it cannot back — a claim about five wrong path declarations.
The resolver sweep's first finding was zero resolvers in 782 files — a claim about a regex.
The near-miss sweep's first finding was 26 render defects, of which 25 were its own false
positives. **In every case the instrument was the thing that was wrong, and in every case
checking the first finding against a known answer is what settled it.**

The corpus is now better defended than the things defending it.

### 47. A RESOLVER THAT RETURNS A CONTAINER WHERE A LEAF WAS NAMED

**Distinct from a wrong address, and worse.** A path pointing at nothing fails loudly the
first time a value is printed. This one resolves to something REAL, on every object.

`lint_method_claim_has_a_field.py::get` supported a `*` wildcard and, at the wildcard,
**returned the matching child instead of continuing down the remaining segments**. So
`results.by_outcome.*.cross_engine` resolved to the **outcome block** —
`{k, estimand_id, comparator_type, poolable, …}` — and never applied `.cross_engine`. The
caller's test was `v is None or v == [] or v == {} or v == ""`. **A non-empty dict is
truthy. The claim passed, and would have passed on every object in the corpus.**

**That is a check with no constructible failing input — reached by a traversal bug rather
than by design.** It is the one property this project has a rule about, arrived at sideways,
where nobody was looking for it.

> **A resolver must distinguish "this path TERMINATED EARLY" from "this path RESOLVED".**
> Any resolver returning an intermediate node where a leaf was named has **silently widened
> every claim that uses it**, and a truth test on the result cannot tell the difference.

**Reading booleans hid it; printing values found it.** Second time in a week a defect
survived until somebody looked at the PAYLOAD rather than the JUDGEMENT.

#### And the sweep written to find this reported zero across 782 files

**The sharpest single instance of the night, and it is about the three-state rule, not about
a regex.** `audit_path_resolvers.py` used `^(\s*)def` under `re.M`; `\s*` consumed the
preceding **newlines** into the indent capture, every extracted body came back as two empty
lines, and the sweep found **0 resolvers in 782 files** — a matcher that matched everything
and yielded nothing, inside the file written to find matchers that resolve to the wrong
thing.

**It survived only because it returned `NOT_ASSESSABLE` instead of a clean bill.** A zero
from a two-state instrument is indistinguishable from a clean corpus, and it would have been
filed as *"no resolvers have this shape"* — a reassuring result, permanently wrong.

**Therefore the sweep now reports three states — CONFIRMED DEFECT, CONFIRMED CORRECT,
UNREAD — with UNREAD as the loud default.** Measured 2026-08-20: **20 resolvers, 16 with the
shape, 1 confirmed defect, 3 confirmed correct, 12 unread.** *Sixteen resolvers shaped like
the bug is not sixteen bugs*, and that distinction does not survive a retelling if it lives
only in prose. The unread count is a **reading list, not a finding**, and the file says so in
its own output so it cannot be quoted otherwise.

The one confirmed defect is `prose_claim_gate.py::check`, and it is a **different**
narrowing: it takes the FIRST outcome's pooled interval and judges direction claims found
anywhere on the object against it. On `sglt2-hf`, which has three pooled outcomes, a claim
about one outcome is tested against another's interval. **A gate that narrows silently
certifies rather than catches.**

### 46. A FIELD'S OWN PROSE NAMING ITS OWN DEFENCE, WHERE THE DEFENCE DOES NOT EXIST

**Distinct from an undefended claim.** An undefended claim has no check behind it and nobody
said otherwise. **This one names the check**, in the object a reader trusts — and a reader who
meets it stops looking, which is exactly what it was written to let them do.

The founding instance. Every `registration_primary_counts` block in the corpus carried:

> *"arm order as the registry lists it; a swapped pair would show as a mismatch rather than a
> silent pass"*

It would not, and it did not. **Nothing in this repository ever compared that block against
`arms[]`** until `scripts/lint_registration_counts_arm_order.py` was written on 2026-08-20. It
found **23 inconsistent rows across 75 trials in 155 objects** — on both EMPEROR trials the
labels were inverted, so the block read as labelled said **empagliflozin was WORSE than
placebo** while the effect two fields away said the opposite and was right.

**The direction matters and is the rarer one.** A reader who performed the check the sentence
promised would have concluded the ESTIMATE was wrong. This biases toward *manufacturing* a
contradiction rather than hiding one — the third such instance in two days, after the arm-role
precondition (2026-08-19) and the empagliflozin `question` field, and the fourth was the sibling
lint above, which manufactured four false alarms by comparing an odds ratio against a stored
hazard ratio.

**Measured by `scripts/lint_self_describing_safety_claim.py`**, which greps for the shape —
*"would show as"*, *"would be caught"*, *"cannot happen because"*, *"makes it impossible"*.
Across 155 objects: **120 field values, 7 distinct claims** once a sentence repeated across rows
is counted once. Five are the founding sentence (one live, four archived); one is untested
(`reconciliation.what_the_benchmarks_show`, 2 objects); one is a phrase-match false positive,
reported as one. **The file reports and never passes** — it cannot know whether a command backs
a given sentence, and says so instead of printing a verdict it has not earned.

> **A sentence describing a check that no command performs is not a check.** It is the
> field-level form of *"anything whose only defence is a paragraph counts as undefended"*.

### 45. A BATCH OPERATION NEEDS A PREDICATE THAT IS FALSE WHEN IT DID NOT RUN

**Every other check on a batch asks whether the output is RIGHT. This one asks whether the run
HAPPENED**, and it is the one that has repeatedly been missing.

Class 44 lists instruments that failed by reporting success on zero items. A batch rebuild is
that trap by construction: **in a build directory, "unchanged" and "never built" are identical
bytes**, so a rollout that reports "146 pages OK" cannot distinguish *I rebuilt this and it came
out the same* from *I skipped this*. A guard-refused build writes no file at all and looks
exactly like a no-op.

The corpus reading-order rollout of 2026-08-20 states four predictions. Three check correctness
— section count unchanged, word count within 1%, `id=paper` present. **The fourth checks
occurrence: NOT ONE PAGE MAY COME OUT BYTE-IDENTICAL**, because the anchor is now emitted on
every tab panel, so every page must change. A byte-identical page there is proof it was not
rebuilt, and the run refuses on it.

**The general form, and it is cheap:** before a batch runs, name a property that the operation
NECESSARILY changes, and assert it changed on every item. If no such property exists, the batch
has no way to tell you it ran — and neither do you.

### 44. AN INSTRUMENT THAT CANNOT TELL "NOTHING TO DO" FROM "DID NOTHING" REPORTS THE SECOND AS THE FIRST

**Three instances in one stretch of one session, all of them mine, all of them reporting
success.** The more careful the success message, the more convincing the lie.

| instrument | what it said | what had happened |
|---|---|---|
| four guard proofs for `_house_rule_table` | ALL PROOFS PASSED — and one proof said approvingly *"no build reported anything"* | the function was correct and **no build reached it**; both call sites are gated on `res.get("sensitivity")` and `finerenone-cv` has no such field. Every built page was empty |
| the host poller | `STALE=0` → **HOST IS CURRENT** | it counted `grep -c ' STALE$'`; a reason column had been added to the summary, so every line ended in the reason. **Both counts were 0.** It reported success because it matched nothing |
| a patch script | `poller patched` | the replacement string did not match. Nothing changed. The message was printed unconditionally, after the `replace` |

**The shape.** Each has a success path reachable when the work did not occur, and none can
distinguish that from the work being unnecessary. *Zero problems found* and *zero things
examined* are the same output.

**The fix is not a better pattern.** It is to assert the instrument engaged at all, and
**refuse** when it did not:

- the poller now counts verdict ROWS first and exits 2 with *"the PARSER is broken, not the
  host"* when it parses none;
- a proof must exercise the **call site**, not the callee — `PROVING A FUNCTION IS NOT
  PROVING THE PATH`;
- a patch reports the match count it actually made, never a fixed string.

> **Ask every counter whether it counted anything before believing its count.** And never
> trust a summariser over the thing it summarises: the false green here was caught only
> because a direct run of the verifier disagreed with the poller wrapping it.

This is class 41 turned inward — the instrument reporting on the world is now the instrument
reporting on *itself*, and the same silence is being read as the same confirmation.

### 42. THE MANUSCRIPT GUARD PAID FOR ITSELF, ON A SCENARIO IT WAS NOT BUILT FOR

**Recorded as prominently as any defect in this file, because a guard that fires only on the
case it was designed around has not yet been shown to be real.**

`ssot/manuscript_guard.py` was written at the end of a long session for a hypothetical: a
rebuild of `ARNI_HF_REVIEW.html` replacing a 100,825-character authored docmodel with a 5,701
character projection. That hazard was real and it never happened — ARNI was excluded from the
rollout by name.

What the guard actually caught, a day later, was **a different lane's improvement silently
removing 43% of a different manuscript**:

```
DOAC_AF_REVIEW: delivered 19712 chars -> this build 11239 chars  (-42.98% text)
Nothing was written.
```

The cause was `_arms_text`, written to stop a Python repr reaching readers — a genuine fix,
proven against all 407 trial rows, which reduced eight prose fields per arm to the phrase
`[+8 further fields recorded on the object]`. Among those eight:
`label_corrected_because: "registry arm size 6076 is the dabigatran 150 mg group"` and a
`label_correction_note` describing a positional-conversion error in the arm converter. **Those
are findings in this corpus's own terms — the sentences it exists to publish.**

> **A guard justified by one scenario, firing on an unrelated one, is the strongest evidence
> available that a guard is load-bearing rather than ceremonial.** Nothing about the DOAC case
> resembled ARNI: different topic, different mechanism, different author, opposite intent. The
> guard did not know any of that. It knew the manuscript got smaller.

**And the override was NOT used.** `RM_ALLOW_MANUSCRIPT_SHRINK=1` would have cleared all eleven
refusals in one command, and the 43% would have gone out with the ten legitimate ones. The
shrink was attributed page by page instead, and the one page whose loss was not attributable
was the one that mattered.

### 43. COUNTED IS NOT THE SAME AS DELIVERED — *a true statement about quantity, where the content belongs*

`[+8 further fields recorded on the object]` is true. It is accurate, it discloses rather than
conceals, it was written specifically so that nothing would be dropped silently — and it stood
where 8,470 characters of authored prose had been.

**It is the false-refusal shape, one level over:** class 29 records a refusal whose reason is
true about something else; this is a *disclosure* whose content is true about the quantity of
the thing it replaced. Both read as diligence. Both pass every check that reads them. A
reviewer seeing "8 further fields recorded" concludes the fields are safe, which they are —
*on the object*, which is not where a reader is.

> **Disclosing an omission is not an alternative to not omitting.** It is what you do when the
> omission is forced. When the content will fit, the content goes in.

**The fix is structural, and that is the transferable part.** The fields being hidden were
`label_corrected_because`, `label_correction_note`, `registry_role_contradiction_note`,
`head_to_head_role_note`, `label_corrected` — **each invented one at a time, by different
lanes, as each new kind of correction was found**. A keyword list catches only what has already
been seen and is guaranteed to miss the next one. The rule that does not:

> **A string over forty characters in a data cell is prose somebody wrote to be read.**

It covers the field nobody has invented yet, which a name-based rule cannot.

### 41. ONE ERROR, FIVE STORES — *reasoning from what an instrument shows to what is true of the world*

**Promoted to its own class because the pattern is more useful than any of its instances, and
because two fresh instances arrived within one stretch of one session, in two different stores,
committed by someone who had just written up the first.**

This project's standing rule names three stores:

> *An absence reported by **an index**, by **a filesystem**, or by **your own search** is not an
> absence in the world.*

Two more have now been paid for, and both are worse than the original three, because the
original three are obviously catalogues and these two feel like testimony:

| # | store | what it reported | what was true |
|--:|---|---|---|
| 1 | an index | — | *(standing rule; pre-dates this entry)* |
| 2 | a filesystem | — | *(standing rule)* |
| 3 | your own search | — | *(standing rule)* |
| 4 | **a passing gate** | 1 placeholder leak across 109 pages | **8** reached a reader; the gate's patterns are `>None<`, `: None`, `/None`, and seven instances were **mid-sentence** — it could never have seen them |
| 5 | **an absent decision record** | no decision found, so *"a rule written and never applied"* | the decision existed at the repository root, dated, citing the Handbook, and had been **fully applied to all 19 objects** |
| 6 | **a build directory** | 11 pages "unchanged, nothing to attribute" | those 11 had **no new build at all** — the guard refused them, so nothing was written, and the directory still held the PREVIOUS rollout's copy. One of them was losing **43%** of its manuscript |

**Instance 6 is the subtlest and it happened inside the instrument written to attribute the
others.** A guard-refused build writes no file. So *a page that came out identical* and *a page
that was never built* are the same bytes on disk, and every length, hash and diff taken from
that directory reports them as the same event. The attribution script's summary read
**"110 of 111 fully explained"**; the 43% existed only in the guard's own log, and was found by
reading the log instead of the summary.

> **Print the summary AND the detail; the disagreement between them is the safety.** Here the
> summary and the detail disagreed completely and only the detail was true. A script that
> derives its population from a directory inherits every ambiguity that directory has —
> including the one where absence and success look alike.

**Why 4 and 5 are the dangerous ones.** An index is plainly a catalogue and a filesystem is
plainly a lookup, so their limits are visible in what they are. A gate was *written to find
this*, so its silence reads as evidence rather than as scope. A decision record is *the
authority*, so its apparent absence reads as "no decision" rather than as "not consulted".
**Both invert from instrument to world without anything in the reasoning looking wrong.**

**The question that catches all five**, and it is one question, not five:

> **Could this instrument have reported the thing I am concluding is absent?**

For the gate: could a mid-sentence `None` make it fail? No — three lines of its own source say
so. For the record: was it read? No — `ls DECIDED-*` was never run.

**Neither instance was caught by re-reading.** Both were caught by going to the world: one
`grep` over delivered pages, one `ls` over the repository root. *Re-reading a sound inference
from a silent instrument returns the same sound inference every time.*

> **The instances are recorded in full at class 39 (the gate) and class 40 (the record).** This
> class exists so the sixth is recognised as the sixth.

**Honest limit on this table.** The three standing stores are quoted from the rule as written;
this entry does **not** re-derive the original incidents behind them, and a sixth candidate —
an *evidence directory* — was raised from memory and **could not be confirmed as distinct from
the filesystem instance**, so it is not listed. Recording that rather than rounding it up to
six, because inflating the count of a class about false inference would be the class.

### 40. A DECISION RECORD THAT NOBODY GREPS IS INDISTINGUISHABLE FROM A DECISION NOBODY TOOK

**This is about how this project uses its own records, not about the question that exposed it.**

Nineteen pooled outcomes carry a `house_rule_interval_*` block. Fifteen of them serve an
interval that excludes the null beside a recorded one that does not. Reading only the objects,
the obvious conclusion is *a rule was written and never applied* — and that is the conclusion
that was reached, written up, and proposed as a unit of **fifteen P19 promotions**.

It was wrong. `DECISIONS-COCHRANE-2026-08-18.md` had already settled it, at the repository
root, in a file named for the purpose:

> **Hartung-Knapp — DECIDED: sensitivity, not primary, at k≤3.** *"When there are only two or
> three studies, we advise review authors to undertake a sensitivity analysis to compare
> results from the different methods."* … **So HKSJ is not adopted as the primary interval.**
> … *the Handbook's own remedy for the small-k case is to show both rather than to pick one.*

The two intervals are not a contradiction. **They are the decision, executed.** The correct
unit was a renderer change over at most eleven pages.

**The check that would have prevented it was `ls DECIDED-*` and one `grep`.** It cost two
commands once someone said the record existed. Nothing else about the investigation was
careless — the measurement was right, every number in it survived checking, and the
interpretation was still inverted.

> **A record only exists to the extent that it is consulted.** This project keeps dated
> decision records at its root precisely so a later lane does not re-litigate a settled
> question — and a later lane re-litigated a settled question, from the objects, thoroughly,
> and reached the opposite answer. *An unread record is not a weaker safeguard than no record;
> it is indistinguishable from one, and it is worse, because it makes everyone feel safer.*

**Rule.** Before proposing a unit of work on a methodological question — an estimator, an
interval, an eligibility axis, a pooling decision — **grep the decision records first**. They
are dated, at the root, named `DECIDED-*` / `DECISIONS-*` / `BLOCKED-*`.

**And verify a reconstruction in BOTH directions.** This surfaced because someone recalled the
decision from memory and said so, asking for it to be checked rather than believed. *Their
memory was right and the fresh investigation was wrong* — and neither party knew which until
the file was read. A remembered decision and a derived-from-evidence conclusion are both
claims; the record adjudicates, and the direction of the correction cannot be predicted from
which one felt better supported.

**The shape worth generalising.** A remedy that stops at the projection layer is invisible from
both ends: **the object holds it, so an object audit passes; the page lacks it, so a reader
never sees it; and nothing compares the two.** Every check in this repository reads one side
or the other. That is the gap this class occupies.

### 39. A DEFAULT THAT A PRESENT-BUT-NULL KEY CAN NEVER REACH — *the care was real and the construct defeated it*

**The worked example is the one where somebody was clearly thinking about absence.**

```python
d.get("records_returned", "an unrecorded number of")
```

`paper_projector.py:356`, inside the sentence that reports each executed search:

> *"It returned %s record(s)."*

Someone wrote a graceful fallback for the case where a search has no recorded count. They
chose a phrase that reads correctly in the sentence — *"It returned an unrecorded number of
record(s)"* — which is careful, deliberate work. **It can never be reached.** A `dict.get`
default applies only to a **missing** key; it is never consulted for a key that is *present
with a null value*. Six topics hold `records_returned: null`, and every one of them renders

> *"It returned None record(s)."*

**This is a better teaching case than a bare `""` default**, because nothing about the code
looks wrong and the author was demonstrably not being careless. The construct defeated the
care. A reviewer reading that line sees an absence being handled and moves on.

**Where it was found, and how it presented.** As the leak `str(t.get("nct", ""))` → `"None"`
in a registration table, caught by the pre-push placeholder gate on one page. The general
form was found only by asking whether the same shape existed elsewhere.

**The counting discipline this class needs, because the pattern over-reports.** A sweep of
`ssot/*.py` and `scripts/*.py`, parsed rather than grepped, found **1535** two-argument
`.get()` calls with a non-None default; **98** keys are observed present-and-null somewhere
in the corpus; **89** sites intersect. *That is not 89 defects.* The intersection is on **key
name**, not on **path** — `pmid` being null somewhere in an object is not `pmid` being null at
`published_comparison.reviews[*].pmid`, which is what that renderer reads. **That is P33 one
level up: a keyword for the name of a thing is not a test for the thing, and the sweep is the
thing being tested here.**

**THE FIRST CORROBORATION I REACHED FOR WAS WRONG, AND IT WAS WRONG IN THE REASSURING
DIRECTION.** This entry originally read: *the placeholder gate found exactly one leak across
109 rendered pages, so most of the 89 are latent.* Then the delivered pages were grepped
directly:

| | |
|---|---:|
| sites the pattern matched | 89 |
| page-instances the **gate** reported | 1 |
| page-instances **actually reaching a reader** | **8** |

Seven delivered pages read *"It returned None record(s)."* right now — both AZILSARTANs, all
four BOSENTANs, and COLCHICINE_CVD_CORONARY. **The gate does not see them.** Its patterns are
`>None<`, `: None`, and `/None`; this one is **mid-sentence**, which no value-slot pattern
matches.

> **A gate's silence was used as evidence about the world.** The reasoning was "the gate found
> one, therefore there is roughly one" — which assumes the gate can see the thing being
> counted. It cannot. *An absence reported by an instrument is an absence in the instrument
> until the world has been asked directly.* Report the number that reaches a reader beside the
> number the pattern matched, and obtain the first by **looking at the delivered bytes**, never
> by subtracting the gate's count from the sweep's.

**A GATE IS THE FOURTH STORE, AND IT IS THE MOST PERSUASIVE OF THE FOUR.** This project already
holds the rule that an absence reported by **an index**, by **a filesystem**, or by **your own
search** is not an absence in the world. A **passing gate** is the same error wearing better
clothes: an index is obviously a catalogue and a filesystem is obviously a lookup, but a gate
was *written to find this*, so its silence feels like testimony rather than scope. It is scope.
The question to put to a green gate before quoting it is not "did it pass" but **"could this
instance have made it fail?"** — and here the answer was no, on every one of the seven, for a
reason visible in three lines of its own source.

> The provenance is worth keeping because it is unflattering: **the false inference was made
> while writing this entry, by the author of this entry, about the very sweep this entry
> governs.** It was not caught by re-reading it. It was caught by grepping the delivered pages,
> which took one command. *The claim was falsified by measurement, not by argument* — and no
> amount of re-reading the sentence would ever have falsified it, because the sentence was
> perfectly reasonable and simply untrue.

`.get('pmid', '')` remains latent on 48 topics — latent is not safe, it is *not yet*.

**The fix is mechanical and the diagnosis is not, and the obvious repair is a trap.**
`d.get(k) or DEFAULT` is wrong wherever `0`, `False` or `""` is meaningful. Here it is
actively destructive: **a search returning 0 records is a real finding** — it is how a query
that missed gets recorded, which P23 requires — and `0 or "an unrecorded number of"` replaces
that finding with an absence phrase. The correct test is `is None`, never falsiness, and the
difference is invisible until a zero arrives.

| | key missing | present-and-null | 109 | **0** |
|---|---|---|---|---|
| shipped `.get(k, D)` | D | **"None"** | 109 | 0 |
| `.get(k) or D` | D | D | 109 | **D — destroys a real zero** |
| `v = .get(k); D if v is None else v` | D | D | 109 | 0 |

**Same family as:** class 28 (a rule that cannot return nothing cannot tell you it does not
know) and class 34 (a fallback that always produces something cannot report an absence). The
distinguishing feature here is that the fallback *would* have reported the absence correctly.
It was simply never called.

**Status: OPEN.** One site fixed at three layers (generator, stamp, renderer). The remaining
88 are named but not adjudicated: each needs its path checked against the data, not its key.

### 38. A RULE VIOLATED BY THE PEOPLE WHO HAVE JUST READ IT — *the availability is the defect, not the reader*

**Fifteenth instance in this project. Three in one session, by an author who had read the rule
that forbids it, quoted it in a commit message, and then did it again twice.**

The rule is at the top of the operating notes and is unambiguous: *never use a shell heredoc
for content containing escapes; write the file and run it.* `\r\n`, `\b` and `\n` arrive
corrupted — a literal `0x08` byte has twice survived into a compiled regex that then matched
nothing while reporting success.

> **The recurrence is the finding. The individual failures are not.** Fifteen violations by
> people who knew the rule is not fifteen lapses of attention; it is a statement about the
> path. The heredoc is *available*, it is *shorter than the alternative*, and it *appears to
> work* — the damage is invisible at the moment of use and surfaces later as a regex that
> cannot match or a byte nobody typed.

**A rule that is followed only by remembering it will be broken at the rate at which people
forget.** That rate is not zero and does not improve with emphasis; this project has now
demonstrated that over fifteen instances and at least four separate authors' worth of
sessions.

**Why the existing gates cannot close it.** `scripts/lint_control_chars.py` and
`scripts/lint_escape_hazards.py` are wired into `.githooks/pre-commit` and they work — but
they catch the **consequences**. A heredoc is *how a file is authored*, not *what is
committed*, so by the time a commit gate can see anything the heredoc has already run and
either left damage or not. Asking the commit path to refuse it is asking it to infer a
process from its output, which it can do only in the cases where damage happened to be left.

**It is the wrong layer, and that is structural rather than an omission.**

**Status: OPEN, with the layer identified.** The check that would work is a **PreToolUse hook**
in the harness, which sees the invocation before it runs. Sketched, with its two failure modes
named, at `scripts/PROPOSED-heredoc-pretooluse-hook.md`. **Deliberately not installed**: a
harness-level interceptor can refuse every Bash call if its matcher or exit convention is
wrong, and it was proposed at the end of a session in which the author's own recoverable-error
rate was rising.

**The generalisation worth keeping.** When a rule is broken repeatedly by people who know it,
stop writing the rule more forcefully and ask **which layer can make the wrong path
unavailable**. If no layer can, the rule is advice and should be labelled as advice, so nobody
mistakes documentation for enforcement — which is the same error as reading a `NOT_ASSESSABLE`
as a pass.

### 37. A BASELINE IS THE MOST DANGEROUS PLACE FOR A REMEMBERED NUMBER

**Because everything downstream is measured against it.** A wrong number in a report is wrong
once. A wrong number in a baseline is the standard every future run is compared to, so it
converts every later measurement into a comparison with a fiction — and it does so silently,
because the comparison still *works*.

**Measured, not recalled.** This entry would be self-refuting if its own count were from
memory, so the instances are enumerated from the record, and they split into two classes that
should not be conflated.

**A number entered by RECALL rather than measurement — 3:**

| instance | typed | measured | where |
|---|---|---|---|
| the templated-refusal baseline | `136` | **19** | `scripts/lint_p46_refusal_is_producibility.py:47` |
| the next registry class number | `31`, `32` | **30, 31** | commit `cda03b345` — 29 was the highest that existed |
| a scope line in a rebuild script | `7 pages of 1,473` | **10 of 115 tabbed** | typed once, left behind as the list grew |

**Adjacent and DIFFERENT, listed so the class stays sharp — 3:**

- **37 → 33 missing manuscripts** (`e97fc9960`) — this was quoting *our own document*, which the
  operating rules already forbid under its own heading. Not recall; citation.
- **82% is a rendering gap** (`4c3fde9b5`) — a *correct* measurement over-generalised from one
  object to a corpus. Not a misremembered value; a misstated scope.
- **`PAGE-STANDARD.md` at 1.6.0 while the code stamped 1.13.0** — a document going stale while
  nothing read it. No recall involved at all.

> **The tell is the same every time and so is the rescue: each was caught by the very thing it
> was a baseline for.** The `136` was caught by running the script it belonged to. The class
> numbering was caught by grepping the register it indexed. The scope line was caught by the
> pass whose scope it described. **A baseline that is never exercised is never checked**, and
> the ones that survive longest are those in code nobody runs.

**The rule:** a baseline is written by a command, in the same commit as the command, and the
command's output is the value. If a constant cannot be produced by running something, it is a
claim wearing a number's clothes.

**AND IT WENT WRONG A SECOND TIME, WITHIN THE HOUR, IN THE OPPOSITE DIRECTION.** The same
constant was measured at `19`, correctly, against the lint **as it then was** -- which read
refusal reasons only from `absent_from_source`. The lint was then widened to read an
artefact's own block, three topics turned out to carry full refusals the narrow version had
scored as SILENT, and the count became `52`. **Not one object changed.**

> **A baseline is measured against an INSTRUMENT, not against the world.** So it must be
> re-derived whenever the thing that produces it changes -- otherwise the ratchet fires on
> its own improvement, the gate refuses a commit for the crime of looking harder, and the
> obvious fix to whoever meets it at 2am is to delete the gate.

That is the failure mode a ratchet is most exposed to, and it is not dishonesty or
carelessness: it is a correct number going stale because its denominator moved.

**Status: PARTIAL.** `BASELINE_TEMPLATED` now carries the command that produces it and the
record of its own correction. Nothing yet forbids the next hand-typed threshold — and the
repository holds at least three more (`FLOOR_CHARS = 600`, `PAPER_FLOOR = 1500`, the
`TOLERANCE = 0.05` in the manuscript guard). Of those, only the manuscript guard's was
*derived from a measurement* — ten rebuilds showing exactly 0.00% variation — and only it
records the derivation beside the constant. See also class 33: those same thresholds do not
report how close they came.

### 36. A TRUE SENTENCE ANSWERING A QUESTION NOBODY ASKED, WHERE THE REAL ANSWER BELONGS

**Found 2026-08-20, on 34 objects, and it survives scrutiny — which is what makes it worse
than a false statement.**

```
absent_from_source.rob2   "No risk-of-bias assessment was recoverable from the page."
absent_from_source.grade  "No certainty rating was recoverable from the page."
```

**Every one of those sentences is true.** They are careful, they are honestly scoped, and
they were written by someone doing the right thing: recording what a converted page actually
contained rather than asserting more.

**They are about the wrong thing.** *What was recoverable from a source page* is a fact about
**provenance**. *Whether a risk-of-bias assessment can be made* is a fact about **the trials** —
and those objects hold their registrations in `inputs.trials`. RoB 2 per result is assessed
from the registrations, not from the page the object was converted from, which is exactly what
the unit does on `iv-iron-hf`, where a domain that cannot be judged from what was reachable is
recorded `NO_INFORMATION` rather than left blank. GRADE is computed from k, the estimate, the
interval and the heterogeneity — all of which those objects already hold.

> **A false statement invites scrutiny and loses. A true statement in the wrong slot passes
> every check that reads it, including a careful human one, because nothing about it is
> wrong.** It fails only against a question nobody thought to ask of it: *is this the answer
> to the question this slot is for?*

**Identical text on 34 objects is the tell.** A reason true of one topic cannot be
byte-identical across thirty-four; sharing at that scale is the signature of a template, and a
template cannot be a finding about any particular topic.

**Relation to the register.** This is the near neighbour of class 28 — *a rule that cannot
return nothing cannot tell you it does not know* — but it is not the same. There the
instrument had no way to express absence. Here absence IS expressed, correctly, about a
different subject. It is also the inverse of class 29: a **false refusal contradicted by
content beneath it** looks like diligence and is wrong; a **true provenance note standing in
for a refusal** looks like diligence and is right — about something else.

**Status: ENFORCED, on a ratchet.** `scripts/lint_p46_refusal_is_producibility.py --gate`, in
`.githooks/pre-commit`. **The test is structural, not a keyword match** — a rule firing on the
word *"recoverable"* would be P14 all over again. The test is that a reason offered for a
missing P46 artefact must not be byte-identical to another topic's.

**What it measured on its first run:**

| | |
|---|---:|
| objects | 141 |
| in scope (publish a pooled estimate) | **28** |
| out of scope (no estimate) — *not passing* | 113 |
| missing artefact, reason **templated** | **19** |
| missing artefact, reason **specific to its topic** | **0** |
| missing artefact, **no reason at all** | **74** |

> **Not one topic in this corpus currently offers a P46 refusal that discharges the clause.**
> Every absence is either silent or templated.

The baseline is recorded as a **backlog, not a permission**: the gate refuses any increase and
the number may only fall. It was also, briefly, wrong — the constant was first typed as `136`
from memory and the measured value is `19`. **A baseline typed rather than measured is this
same class one level up**, and it is recorded in the file beside the corrected number.

### 34. CLASS 28 IN THE MANUSCRIPT LAYER — *a fallback that always produces something cannot report an absence*

**Found 2026-08-20, and it had been shipping for as long as those pages have existed.** Every
projected Results section opened:

> For **`hfh_cvd_recurrent`** (k = 2), the pooled estimate was 0.8066…

The subject of the sentence was a database key, printed at a reader.

**It was never a content gap.** `outcomes[].name` holds the registered text on every one of
those objects:

```
hfh_cvd_recurrent -> "Recurrent hospitalisations for heart failure together with
                      cardiovascular death, as a rate ratio"
```

The whole defect is one line:

```python
outcome_txt = blk.get("outcome") or oid
```

> **The fallback made the omission invisible by ALWAYS PRODUCING SOMETHING.** There was no
> state in which the projector said *I do not hold this outcome's name* — because `oid` was
> always there to be returned. This is **registry class 28** — *a rule that cannot return
> nothing cannot tell you it does not know* — arriving in the manuscript layer, where its
> output is prose a reader is asked to trust.

And it is worse here than in a check, because a wrong verdict announces itself as a verdict
while a wrong subject reads as the outcome's name. A reader has no way to tell
`hfh_cvd_recurrent` from an outcome that is genuinely called that.

**Status: CLOSED.** `paper_projector.outcome_text()` returns `None` when no registered text
is held, and the caller **refuses the sentence and names the field**:

> *refused: the result sentence for the outcome recorded as `X` — its REGISTERED TEXT is not
> held, and an internal identifier is not an outcome name.*
> `no field: outcomes[id=X].name`

Held by `scripts/test_manuscript_prose.py`, which asserts that no outcome key appears
anywhere in the Results or Abstract prose of the six objects that pool.

### 35. A DEFECT THAT EXISTS ONLY BETWEEN TWO SECTIONS, AND SO IS INVISIBLE TO BOTH

**Found 2026-08-20, by a test, after two careful readings missed it.** The risk-of-bias
ceiling statement — 300 characters — was emitted **twice** in every manuscript whose object
records one: once by `methods_synthesis`, which had carried it for weeks, and once by the
`risk_of_bias` section added hours earlier the same night.

> **Neither site was wrong on its own.** Methods was right to state the bound. The
> assessment was right to state the bound. **The duplication came into existence when the
> second section was added** — it is a property of the pair, and of no member of the pair.
> That is exactly why it was invisible to whoever wrote either one, and it always will be.

**No check that looks at one section at a time can see this, however careful the reviewer.**
The unit of checking has to be the document.

**Status: CLOSED, with a gate.** `scripts/lint_manuscript_whole_document.py` checks three
properties, each of the whole and of no part:

| | |
|---|---|
| **D1** | the same substantial paragraph emitted in more than one section |
| **D2** | the same table, by caption or by rows, in more than one section |
| **D3** | a field **refused** in one section and successfully **used** in another — class 29 at document scale |

**It found 20 further instances on its first run, before a single page was rebuilt**, in two
families neither of which had been noticed:

- **10 topics print their title twice**, because the object records `title` and `question` as
  the *identical string*. The manuscript now says so — *"a question copied from a title has
  not been asked"* — which surfaces the object defect instead of concealing it behind a
  repeated line.
- **10 topics refused References for want of `sources` while Data availability counted the
  same `sources` and wrote.** `sources` has two shapes in this corpus — `{id: {layer, name,
  url}}` and `{id: "evidence/….json"}` — and only the first was rendered, so the second
  produced zero rows and a refusal beside a section using it. **One manuscript saying both.**

> The general rule: **whenever a document is assembled from independently-authored parts, at
> least one check must run over the assembled whole.** Every per-part check can pass while
> the document contradicts or repeats itself, and the more careful the per-part authoring is,
> the more likely that is the only remaining failure mode.

### 32. A TEST THAT RE-IMPLEMENTS THE BRANCH IT TESTS — *it can pass while the shipped code differs*

**Found 2026-08-19, in a test written the same night to protect a projector change.**
`scripts/test_partial_state_projector.py` imports `projectors`, and then does this:

```python
def decide(body, tid):
    """The projector's branch, exercised in isolation."""
    carries = bool(re.search(r"<(?:pre|table|svg|li|dl)[ >/]", body)) \
        or len(re.sub(r"<[^>]+>", " ", body).strip()) > 80
    if carries and tid in P.PARTIAL_STATE:
        return "Partially held.", P.PARTIAL_STATE[tid]
    return "Not held in this object.", P.ABSENT_STATE.get(tid, "")
```

It imports the two **string tables** from the module and **re-implements the branch that
chooses between them**. So it proves the strings are what the test expects, and that a copy of
the logic behaves as written. **It cannot see the shipped branch at all.** Change the condition
in `ssot/projectors.py` — invert it, delete it, make it unreachable — and this test still
passes, green, on every run.

> **The test and the code agree because they were written from the same understanding, not
> because one checks the other.** Same family as a known-answer file built from synthetic
> fixtures: the answer key inherits the assumption it exists to test.

It was not harmless here. The re-implemented `decide()` *is* the real branch as of tonight, so
the verdict happened to be true — true **by coincidence of authorship**, which is not a
property anything can rely on tomorrow.

**How it was caught:** not by the test. By rebuilding a real page and reading served bytes —
which is what the test's own docstring says it is avoiding: *"Rebuilding seven live pages to
find out whether a sentence is right is the wrong order."* That reasoning is right about cost
and wrong about evidence.

**Status: OPEN.** The two tests written later the same night —
`scripts/test_screen_partial_note.py` and `scripts/test_report_certainty_guard.py` — call the
real functions and are not affected. `test_partial_state_projector.py` still holds its copy.
The fix is to **expose the branch as a function in `projectors.py` and have the test call it**,
so there is one implementation and the test is attached to it.

**The rule:** a test may import DATA from the module under test; it must never re-implement the
module's CONTROL FLOW. If a branch cannot be called, it is not testable — extract it until it is.

### 33. A THRESHOLD TEN CHARACTERS FROM ITS VERDICT HAS STOPPED DISCRIMINATING

**How to read class 31, and it generalises past it.** `BOCOCIZUMAB_LIPID`'s report panel
measured **610 characters against a 600-character floor**. The verdict was "not thin, so no
banner". The margin was **ten characters — 1.7%**.

> **A panel ten characters above a threshold is not a panel that passed. It is a threshold that
> has stopped discriminating.** At that distance the verdict is decided by how long an outcome
> name happens to be, and the same object with a shorter label produces the opposite answer.

**So report the margin, not just the verdict.** `PASS` tells a reader the test was met;
`PASS (610 vs 600, margin 10)` tells them whether the test *means* anything on that input.

| threshold | where | reports its margin? |
|---|---|---|
| `FLOOR_CHARS = 600` | `ssot/projectors.py`, thin-panel test | **no** — this is the one that bit |
| `PAPER_FLOOR = 1500` | `scripts/rederive_manuscript_count_2026_08_19.py` | partly — it states the gap it sits in (≈350 vs ≈6,300) is wide, which is the honest form of the same disclosure |
| `> 80` chars | `_carries_something`, the partial-state branch | **no** |

**Status: PARTIAL.** Named, and the manuscript re-derivation already discloses its margin as a
range. Nothing yet makes a threshold print its distance automatically, and until it does, a
`PASS` from any of them is silent about whether it was close.

### 30. A COMPOSITE REFUSAL IS TRUE OF SOME PAGES AND FALSE OF OTHERS — *and it reads identically on both*

**Found 2026-08-19, while applying the fix for class 29.** The third projector state was written
to replace a false refusal with a true one. Its sentence for the screening tab denies **three
things in one breath**:

> **Partially held.** Part of the screening record is held and is shown below. The counts that
> would complete it — **records identified, excluded with reasons, dual-screening** — are not
> carried on this object.

Measured against the five pages that carry a screening log, the middle limb splits:

| page | records | carrying a stated reason |
|---|---:|---:|
| `EARLY_RHYTHM_CONTROL_AF` | 551 | **551** |
| `APIXABAN_VTE_PROPHYLAXIS` | 72 | **72** |
| `APIXABAN_VTE_TREATMENT` | 72 | **72** |
| `AZILSARTAN_CLD_VS_OLM_HCTZ` | 57 | **0** |
| `BOCOCIZUMAB_LIPID` | 22 | **0** |

So the one sentence is **false on the first three and true on the last two**, and a reader cannot
tell which page they are on. **This is class 29 one level down** — the replacement refusal
inherited the defect of the refusal it replaced, because it was a constant where it needed to be
a computation.

> A composite claim needs a composite check. **The correction of a composite claim needs one
> too**, and that is the step that was missed: the fix for class 29 was itself written as a
> literal string, which is precisely what P17 forbids in an object field and nothing forbade in a
> banner.

**Status: CLOSED for `screen`.** `ssot/projectors.py::screen_partial_note` computes the sentence
from the panel's own rendered body — record count, how many carry a reason, whether an
adjudication record exists, whether a counts table exists — and **returns None rather than
guessing** when it cannot see a record card. Tested against all five founding cases in
`scripts/test_screen_partial_note.py`, which asserts not merely that a sentence is produced but
that **the two groups differ on the exact limb they differ on** — a test that only checked a
sentence came back would pass on the defect.

**Status: OPEN for the other five tabs.** `search`, `extract`, `analysis`, `report` and
`protocol` still carry literal composite sentences. They are not known to be wrong; they are
known to be **unchecked**, which after this class is a different statement from "fine".

### 31. A PAGE'S HONEST STATEMENT WAS DECIDED BY A CHARACTER COUNT — *and the longer page said less*

**Found 2026-08-19, in our own rebuild, before delivery.** The report tab's sentence —

> No GRADE certainty rating is carried, so the certainty column is left as an em dash rather
> than guessed.

— was reachable **only through the thin-panel branch**, which fires when a panel's text falls
under `FLOOR_CHARS = 600`. `BOCOCIZUMAB_LIPID`'s report panel measures **610 characters**.

> **The page kept or lost the explanation of its own column of em dashes on a ten-character
> margin** — and in the wrong direction: the page with the **larger** summary-of-findings table
> is the one that silently drops the explanation, because a longer outcome name pushes it over
> the floor.

A length threshold is a sound test for *is this panel empty*. It is not a test for *does this
review carry a certainty rating*, and it was being used as one.

**Measured over the delivered corpus** (113 tabbed pages carrying a Certainty column):

- **109** leave **every** outcome unrated;
- **4** carry a rating — `ARNI_HF`, `IV_IRON_HF`, `SGLT2_HF`, `SOTAGLIFLOZIN_HF`. Three of those
  four are among the four topics complete by the full definition, which is corroboration from an
  independent direction and was not looked for;
- of the 109, **105 already explain their em dashes and 4 do not**: `ABLATION_AF`,
  `ALIROCUMAB_LIPID_AUTO_FULL`, `DOAC_AF`, `SGLT2_CKD`. **`BOCOCIZUMAB_LIPID` would have become
  the fifth on delivery**, which is how the class was found — the rebuild diff, not a reader.

**Status: CLOSED going forward.** `ssot/projectors.py::report_certainty_unrated` reads the
certainty **cells** the reader sees and is indifferent to length; the banner is now emitted from
the non-thin path as well. Proven in four parts per P16, each on a real page rather than a
fixture: it fires on 109, stays silent on 4, and the case that settles it is **`SGLT2_HF`'s mixed
column `['high', '—', '—']`** — a cruder all-or-nothing test would fire there and claim no rating
is carried on a page that carries one. The triggering condition **actually occurred**: the
610-character panel is the event.

**Not repaired:** the four delivered pages above still show an unexplained em-dash column. They
are named here rather than fixed, because each needs a rebuild of its own and this pass did not
run one.

### 29. A REFUSAL CONTRADICTED BY THE CONTENT BENEATH IT — *a false refusal looks like diligence*

**Found 2026-08-19, eleven delivered pages.** Each opened its search tab with:

> **Not held in this object.** No search record is held in this object. The included set was
> reconciled against published syntheses rather than produced by a database search, so **no
> query, date or yield can be shown**. Treat the included set as a **convenience sample**, not a
> systematic one.

— and then printed the executed query, its date and its yield, in the same section, immediately
below. **A reader who stops at the first paragraph is told the review is a convenience sample
while its object holds a two-database search screened to zero.**

`colchicine-cvd-coronary` was one of the eleven **and was built the same day**, from a search
executed across 137 registrations. The stale refusal was never removed when the search was added.

#### The state the corpus did not have

*"Not held in this object"* is a **refusal** when true and a **gap** when false, and **it reads
identically either way**. A third state was missing — *held elsewhere and not projected*.

> **A missing manuscript is visibly missing. A false refusal is invisible: it looks like
> diligence.** 37 of 43 cardiology topics have no paper, and that is the larger number but the
> smaller problem.

#### Why the detector is deliberately narrow

38 sections carry a denial followed by substantial content, and **only 11 are contradictions**.
`pn-report` denies a GRADE rating and then renders a summary-of-findings table whose certainty
column is an em dash — **that is honest**; the refusal is about GRADE and the cell says so. A
rule flagging all 38 would be class 28 again and would train a reader to ignore it. The rule
implemented asserts only the least arguable case: **the section's own bytes refute its own
opening sentence.**

#### And the locator refused before it approximated

The first repair looked for a `<p>` wrapper, matched nothing, and **refused on every page** —
the correct behaviour for a locator that cannot locate. Re-written against the markup read from
a page, it removed exactly 342 bytes from each of the eleven and nothing else.

**Status: CLOSED for this shape.** `scripts/lint_refusal_contradicted_by_its_own_section.py` is
in `.githooks/pre-commit`. It covers **one** contradiction pair; other tabs could carry the same
shape with different wording and are not checked.

### 28. A RULE THAT CANNOT RETURN NOTHING CANNOT TELL YOU IT DOES NOT KNOW

**The common ancestor of most of what this file holds.** Found as a class 2026-08-19 after three
instances appeared in one script in one stretch, each with the same signature: a selection rule
that *always returns something*, so its output is indistinguishable from a correct answer.

| the rule | what it returned | what it should have returned |
|---|---|---|
| intervention = **shortest** coded name | `"does Placebo compared with placebo"` for `finerenone-review`; the comparator for `moxifloxacin-respi` and `pitavastatin`; `amikacin` for `raltegravir-hiv` | *I cannot identify the intervention* |
| intervention = coded name matching **any topic token** | `"Rabies Vaccine"` for `malaria-vaccine`, on the token `vaccine` | *that token names a class, not a thing* |
| topic tokens = words **longer than three characters** | nothing for `hepatitis-b-taf-tdf-review`, because the drug is **TAF** | *the drug name is shorter than my filter* |
| condition = **shortest** coded name (a *fallback* left after the first fix) | `"In adults with stroke"` for `warfarin-af` | *no coded condition matches this topic* |

**37 topics would have shipped a confident sentence naming the wrong drug.** `does Placebo
compared with placebo` reads as a *formatting* error rather than a *selection* error, which is
why it would have survived a skim.

#### The two halves that make it a class

**A fallback is the defect, not a mitigation of it.** Removing the shortest-string fallback on
the condition field moved **ten topics out of RESTATED and into honest escalation** — the
measure of how much the fallback was concealing. And fixing the intervention field first left
the identical fallback on the condition field, so the class looked closed while still producing
wrong output.

**And the worked example runs the other way.** `hepatitis-b-taf-tdf-review` was declared
*unanswerable* because a three-character drug name fell under a length filter — while its own
registrations' `officialTitle` states the comparison in plain words on a field the rule never
reads. A rule that cannot say *I do not know* also cannot say *I looked in the wrong place*.

> **Every such rule must have a path that returns nothing**, and the count of those returns is a
> result, not a failure. A rule with no such path converts every input into an answer, and the
> wrong answers are the ones that look exactly like the right ones.

**Status: PARTIAL.** The instances are fixed and the discipline is stated. Nothing mechanically
prevents the next selection rule from being written without a nothing-branch.

### 27. A DETECTOR BUILT FROM ONE INSTANCE ENCODES THAT INSTANCE'S SHAPE — and scored it UNCLASSIFIED

**Found 2026-08-19.** A detector was written to find the class *one trial registering its nested
substudy separately, so a registry-derived k counts it twice*. It was built from a single worked
case: `NCT01709981` + `NCT02594111`, named together in PMID 32295417.

Its classification table was keyed on an **exact tuple** of the registrations involved. On the
corpus run, that PMID came back listed by **three** registrations — the pair, plus `NCT05739929`
citing the same paper as background. The exact-tuple lookup did not match.

> **The confirmed instance scored `UNCLASSIFIED` in the first run of the detector built to find
> it.** Had the corpus contained nothing else, the count would have been zero and the class
> would have read as absent.

**The general form.** A detector distilled from one example encodes the *incidental* features of
that example alongside the essential ones — here, "exactly two registrations" was incidental and
"a publication naming both" was essential. **Test a detector against the instance it was built
from before trusting any corpus-wide count it produces.** A zero from an untested detector is
indistinguishable from a zero from a working one, which is the same shape as the untested query
returning a null (class 26, rule 3) and as `$?` read through a pipe.

Fixed by matching on **subset** rather than exact tuple. **Status: PARTIAL** — the discipline is
stated and there is no mechanism that forces a new detector to be run against its own founding
case.

#### And the same run produced a filter that is wrong in both directions

The raw count was dominated by **background citations** — PMID 9725923 is listed by seven
registrations and is plainly someone else's landmark paper, not seven trials reported together.
Stratifying on reference type separates a self-report from a citation. But the same type field
is unreliable the other way: **CLEAR Outcomes' own primary report is typed `BACKGROUND` on its
own registration**, so restricting to `RESULT`/`DERIVED` can drop a genuine self-report.

> **A filter that errs in both directions cannot be applied; it can only be reported around.**
> Both strata are emitted, and the count that would follow from choosing either is not offered.

### 25. A CASE-SENSITIVE LOOKUP THAT FINDS NOTHING LOOKS EXACTLY LIKE A CLEAN RESULT

**Found 2026-08-19, and it nearly buried a real finding from another instrument.** The Codex
seat reported that the dashboard serves withdrawn estimates. The first verification pass written
here — to check that claim rather than believe it — returned **zero**:

```
rows with a numeric pooled value AND a mapped object: 0
object says WITHDRAWN                                : 0
```

The lookup was `r.get('pooled_or')`. **The field is `pooled_OR`.** Every row was skipped, the
tally was empty, and the output read exactly like a clean corpus — while 92 rows were in fact
serving values their objects had withdrawn.

> **A cross-family seat had handed over a true finding and this lane's own check said it was
> false.** Had that zero been believed, the finding would have been recorded as *"Codex was
> wrong"* — the most expensive possible outcome of a correct delegation.

**Caught only because the same script printed the sample keys beside the count.** The diagnosis
took one line of output that was there for another reason entirely.

#### The fourth distinct form of the same shape

*Something that never happened, looking exactly like something that happened and found nothing.*
This registry already holds three:

| form | what it looks like |
|---|---|
| an over-escaped `\\b` in a raw string | valid Python that matches nothing and **reports clean** |
| `$?` read through a pipe | the exit code of `tail`, which is **always 0** |
| a guard whose triggering condition never occurred | **green**, and unproven (P16's fourth clause) |
| **a case-sensitive key lookup on a field that is spelled differently** | **an empty tally, indistinguishable from a clean one** |

**The remedy is the one that has worked on the other three: make the instrument report what it
looked at, not only what it found.** A count printed beside the keys it scanned is refutable; a
count alone is not. Every sweep written in this session now prints its denominator and its
NOT_ASSESSABLE reasons broken out, for exactly this reason.

**Status: OPEN.** No detector. A general lint for case-mismatched dictionary access is possible
in principle and is not written; what is written is the discipline above, and discipline is not
a command. Recorded honestly as the weakest entry in this file.

#### And it reproduced TWICE MORE the same day, in the selftests of the instruments written after it

Both after this entry existed, both by the author of this entry, both in the **selftest** — the
part of a file whose entire purpose is to catch this:

| # | where | the comparison | against |
|---|---|---|---|
| 3 | `resolve_primary_publications.py` selftest | `"does not search" in why` | a string reading **"DOES NOT SEARCH"** |
| 4 | `estimand_screen_dabigatran_vte_2026_08_19.py` selftest | `"not a finding that the trials pool" in note` | a string reading **"That is NOT a finding…"** |

In both, **the code under test was correct and the test failed.** Had the polarity been the other
way — assertion passing on a string it never matched — neither would have been noticed.

> **The class was known, written down, and reproduced by the person who wrote it down, inside
> the hour.** That is the finding, not the two typos.

#### The ledger this belongs to

Three entries now share that exact shape, and they are the argument for everything mechanical in
this repository:

| the rule | where it was written down | how it was broken |
|---|---|---|
| **never use a heredoc for file content** — the transport corrupts escapes | the handover brief, first paragraph | **eleven instances**, the last of them after ten prior corrections |
| **a merge must never net-delete** | the merge instrument's own contract | broken **inside the instrument that enforces it** |
| **fold case on any comparison over free text** | this entry, class 25 | reproduced **twice, in selftests written after it** |

**Knowing a rule does not execute it.** Each of these was understood, stated in writing, and
violated anyway by the party who stated it — so the corrective that works is never *"remember
harder"*. It is the pre-commit hook, the assertion that fails closed, the guard whose triggering
condition must be shown to have occurred. **Mechanism catches what understanding does not**, and
that is why this file's weakest entries are the ones with no detector rather than the ones with
no explanation.

### 24. THE DASHBOARD SERVED 92 ESTIMATES THE OBJECTS HAD WITHDRAWN

**Surfaced by the Codex seat (openai family) while running a different task, verified here
before being recorded.** A cross-family seat's finding is a lead, not a result.

`dashboard.html` renders a *Pooled OR (95% CI)* column from `outputs/portfolio_index.json`, a
snapshot generated **2026-06-24**. Of its 711 rows carrying a numeric value:

| | |
|---:|---|
| **83** | the object has **WITHDRAWN** its estimate |
| **8** | the review **no longer exists** — retired into another topic |
| 1 | the object carries no pooled value at all |
| **92** | **served where the object does not support it** |
| 847 | no SSOT object at all — **uncheckable, so 92 is a floor** |

> **A withdrawal is the strongest statement a review in this corpus can make.** It is what an
> object says when its trials do not share an endpoint, when its comparator is wrong, or when
> its headline cannot be reproduced from its own trials. **Serving the number anyway undoes
> every one of those decisions at once**, for every reader who never opens the page — and the
> dashboard is the surface most readers actually look at.
>
> **It is class 23 at scale, on the aggregate surface.** That sweep was run over `index.html`'s
> 522 cards and closed at zero. *It looked at one surface.*

#### Fixed by PROJECTION, not by regenerating the snapshot

A regenerated snapshot is correct for a day and wrong again the next time an object is
withdrawn, **silently and with no symptom**. The pages solved this long ago: a page carries the
version it was built to, so being out of date is *visible*. The dashboard's data gets the same.

- `scripts/project_dashboard_index.py` writes each row's `ssot_state`, **moves** a not-live
  value to `pooled_OR_superseded` rather than deleting it, and stamps an **objects fingerprint**
  — a hash over every page's derived SSOT state.
- **Why a fingerprint and not a timestamp.** A timestamp answers *when was this made*, which is
  not the question. The question is *do the objects still say what this was built from*. **A
  regenerated snapshot with a fresh timestamp and a stale withdrawal passes a date check and
  fails this one.**
- `scripts/dashboard_projection_gate.py`, **wired into `.githooks/pre-commit`**, refuses on
  either half: a fingerprint that no longer matches (or is absent — *NOT_ASSESSABLE, never
  fresh*), or **any row serving a value its object withdrew — a delivery failure, not a display
  detail**. Exit 1 before, exit 0 after, with the can-fire proof on the case that shipped.

#### And an absence must name its own cause

The cell rendered every empty value as `— (k<2 / continuous?)`. **A reader told "k<2" about a
withdrawal has been told something false.** It now renders the real state. Verified **in a real
browser**, not by reading the source: 960 rows, 0 page errors. The first draft of that cell
called `esc()` before the helper existed — a `ReferenceError` that would have blanked the entire
table, and it was caught by *running* it.

**What this does not do:** it does not compare the LIVE rows' *numbers* against their objects. A
row left LIVE may still be stale by value.

### 23. THE CLASS SWEPT — *"the number was real and belonged to somebody else"*

**Class 21 found one instance by hand. Two instances found by hand is not a measurement**, and
the shape is entirely mechanical, so the question *how many others* has an answer a command can
produce. `scripts/benchmark_served_as_own_result_sweep.py`, run 2026-08-19 over 522 index cards,
77 benchmark records and 116 page-map entries.

**FIVE instances of the class, of which THREE were live and unknown:**

| page | the card served | the object's own pool | benchmark type |
|---|---|---|---|
| `LENACAPAVIR_PREP_REVIEW` | `RR 0.07 (0.01–0.32), k=2` | **WITHDRAWN, k=0** | `self_reference` |
| `CAB_PREP_HIV_REVIEW` | `HR 0.22 (0.11–0.45), k=2` | `RR 0.2081 (0.0715–0.6057), k=2` | `self_reference` |
| `NIRSEVIMAB_INFANT_RSV_REVIEW` | `RR 0.21 (0.13–0.33), k=3` | `RR 0.2605 (0.1766–0.3845), **k=2**` | `self_reference` |
| `COLCHICINE_CVD_REVIEW` | `HR 0.75 (0.61–0.91), k=2` | was `0.7940 (0.6750–0.9339), k=5` | corrected, class 21 |
| `DOAC_AF_REVIEW` | `HR 0.81 (0.73–0.91), k=4` | was `0.7817` — Ruff 2014, its own comparator | corrected |

> **`LENACAPAVIR_PREP` is the worst of the five and it is a different degree, not a different
> kind.** The object has **withdrawn its estimate — `k=0`** — and the index card serves a
> confident external `RR 0.07 (0.01–0.32)` at `k=2`. The review says it cannot answer and the
> index says it answered decisively.

**`CAB_PREP_HIV` carries a measure mismatch on top**: the card says **HR** and the object says
**RR**. And `NIRSEVIMAB`'s card claims **k=3** where its object pools **k=2** — the card is
wrong about how many trials the review holds.

#### The structural finding is larger than the five

**42 cards are authored in the `Published:` register**, against `Pooled:` for a projected
result. On this project's own index — a list of *this project's reviews* — a reader has no way
to know that one row means *somebody else computed this*. Of those 42:

| | |
|---|---:|
| comparable against an object at all | **3** |
| **no SSOT object exists for the page** | **34** |
| no benchmark record | 5 |

**Thirty-four of forty-two cannot be checked by anything in this corpus.** That is not a clean
count; it is the E9 shape at the level of the index — *absence of a check is not a passed check*
— and it is why "three instances" is a floor.

#### The third limb convicts nobody, INCLUDING colchicine, and that is the honest answer

The sweep also asks, independently of any card, whether a benchmark reconciles with the object's
own trials under the class-21 bound. **It first returned eight. Two of the eight were this
instrument's own defect**, and in the family this project keeps finding:

- `INCRETIN_HFpEF` — benchmark is an **HR** for a worsening-HF composite; the object's declared
  headline is `kccq_css_change`, a **mean difference in a symptom score** (per-trial 7.8 and
  6.9). Exponentiating those against a hazard ratio produced a "pool" of **7.4901** and a gap of
  **21.9**, reported as a benchmark that does not reconcile.
- `IV_IRON_HF` — benchmark is an **HR**; the object's declared headline is a **RATE_RATIO over
  recurrent events**. The object *does* hold a matching HR outcome and the limb never looked.

> **P36 and P37 one level up: two quantities compared by their SLOT rather than by their
> DEFINITION, and the arithmetic completed without complaint.** With measure-match and
> scope-match enforced, **all eight collapse to zero.**

And the limb **cannot convict colchicine either** — that benchmark is `k=2` against an object
holding three trials, so it is refused as SCOPE DIFFERS. The colchicine conviction came from
testing the benchmark against **its own declared source**, COLCOT and LoDoCo2 named in the
record with their PMIDs. **A benchmark record generally does not name the trials it pooled, so
that test is not generally available. That is the gap this sweep measures and does not close.**

The 171 NOT_ASSESSABLE are broken out by reason rather than reported as one number — 149 with no
benchmark or no object, 16 measure mismatches, 3 ambiguous outcomes, 2 scope differences, 1 with
too few per-trial intervals. **A large NOT_ASSESSABLE folded into one line reads as "nothing to
see here".**

### 21. A comparator rendered as a result — and closed by a BOUND, not by a search

- **Found** 2026-08-18 on `colchicine-cvd-review` and **closed** 2026-08-19. The third topic in
  this corpus with the shape *no combination of estimator or subset reproduces the published
  headline* — after `pcsk9` and `DOAC_CANCER_VTE`.

- **Why the previous treatment could not close it, and the reason generalises.** Thirty-three
  candidate pools were computed — every subset of two, three and four of the page's published
  hazard ratios under fixed-effect, DerSimonian-Laird and REML — none gave `0.75 (0.61–0.91)`,
  and the search was recorded **as bounded**. That was honest and it was not a proof:

  > **An enumeration that finds nothing proves nothing about the estimator it did not try.**
  > "None of the 33" leaves Mantel-Haenszel, Peto, Knapp-Hartung, a Bayesian posterior and every
  > fixed weighting a reviewer might have used, and a reader cannot tell a fabricated number
  > from one produced by an estimator nobody thought to run.

- **What it actually was.** The number was never this review's pool. It is an **external
  published benchmark**, and it says so in three files the page never consulted:
  `PUBLISHED_META_BENCHMARKS.json` records it under this page's own filename with
  `benchmark_type: self_reference`, `source: COLCOT (Tardif 2019) + LoDoCo2 (Nidorf 2020)`,
  both PMIDs, and `method: DL random-effects pooling of 2 landmark RCTs`. **The same shape as
  DOAC_AF**, whose unreproducible headline turned out to be Ruff 2014's published risk ratio,
  carried on that page as its comparator. *The number was real and belonged to somebody else.*

- **And the benchmark does not reconcile with its own declared source** — a separate finding.
  Taken entirely at its word, COLCOT `0.77 (0.61–0.96)` and LoDoCo2 `0.69 (0.57–0.83)` pool to
  **0.7215 (0.6243–0.8338)**. The served upper bound is out by **0.0762 — seven and a half
  units in the last quoted place.** Its declared `N: 11816` does not reconcile either:
  4,745 + 5,522 = **10,267**.

- **The detector, and why it is a bound.** `scripts/pooled_point_in_achievable_range_gate.py`.
  - **HULL.** Every inverse-variance pool, every Mantel-Haenszel and Peto pool and every fixed
    weighting is a **convex combination** of the per-trial log-effects, so a claimed point
    outside `[min, max]` cannot be produced by *any estimator that has ever been written or ever
    will be*. No enumeration is involved.
  - **TAU-PATH.** Inside the hull, the random-effects family itself bounds it. As τ² runs from 0
    to ∞ the weights run from the fixed-effect weights to **equal** weights. COLCOT is the *less
    precise* of the two, so its weight can never exceed one half — 40.7% at τ²=0, rising to 50%
    — and reaching 0.745 would require it to carry **seventy per cent**. Achievable interval:
    **0.7215 to 0.7289.**

- **Four instrument defects were found in the detector while it was being built**, every one of
  them manufacturing a finding rather than hiding one, and each is recorded in the file:
  1. **An overclaim.** A draft asserted "a pool cannot be less precise than its most precise
     trial". **False** above τ²=0 — the pooled variance is bounded by `s_min² + τ²` and by
     nothing else.
  2. **A threshold that decided the verdict.** At a point tolerance of 0.005 the nearest
     candidate failed; at the better-justified rounding half-width of 0.0066 the same candidate
     passed. *A gate whose answer moves when you justify its threshold more carefully is
     measuring the threshold.* Replaced by the served number's own precision.
  3. **A precision cap.** `_dp` read the precision of an object-*stored* value —
     `0.8440482145268958`, sixteen decimals — and then demanded exact float equality. It
     reported `pcsk9-inhibitors-cv-review` as NOT_ACHIEVABLE **with a total gap of 0.0000**.
  4. **An objective that did not match its acceptance test.** It minimised the **sum** of the
     three deviations and then tested the **max**, so the search walked away from a τ² that
     *satisfied* the test toward one with a smaller total. **Eleven corpus outcomes** failed on
     this, every one of them a real, exactly-reproducing pool.

  Plus a fifth, of a different kind: modelling only the **normal** interval failed
  `apixaban-vte-treatment`, which declares a **Knapp-Hartung t interval on 2 df** on its face —
  4.303 against 1.960, more than double the half-width. With that family added, **the entire
  corpus reproduces: 0 outcomes NOT_ACHIEVABLE.**

  > Five defects in one instrument, and **all five ran in the direction that manufactures
  > findings** rather than hides them. This registry's central claim is that the objects keep
  > being right and the instruments keep being wrong; this is the cleanest instance of it yet,
  > because the instrument was written specifically to check the objects.

- **The weaker half is reported with its margin, not folded into the verdict.** No subset of any
  size reproduces the served triple at any τ² under either interval family — but its nearest
  miss, LoDoCo2 with CONVINCE, is out by **0.0104 against a unit of 0.0100, a margin of four per
  cent.** That is not something to close a defect on, and it is not what closed this one. It
  also could not be the source: the benchmark names its two trials, and CONVINCE reported in
  2024.

- **What is NOT claimed.** Not that anyone fabricated a number — the provenance is now known and
  it is ordinary. Not that the benchmark's underlying published figure is wrong, only that it
  does not follow from the two trials and the one method recorded beside it. **And closing the
  provenance does not restore the estimate**: the pool stays withdrawn for the reason already on
  the object — the trials do not share one endpoint, and CONVINCE is not a composite trial at
  all.

### 20. Cursor abandonment — a paginated search treated as whole
- **Found** 2026-08-19 on `colchicine-cvd-review`, the first topic this session whose surfaced
  set exceeded one page:

  ```
  page 1   returned 100   total_reported 137   next_page_token PRESENT
  page 2   returned  37   total_reported null  next_page_token null
  ```

- **What building on page 1 would have cost**, measured rather than argued: **CLEAR SYNERGY
  (NCT03048825, n=7,264) is on page 2 only** — one of the review's own three included trials, and
  the largest of them.

  | | |
  |---|---|
  | recall on page 1 alone | **2/3** |
  | recall on the complete search | **3/3** |

- **Why it has no downstream symptom** 100 records is a plausible surfaced set, the arithmetic
  reconciles with itself, and `k_unscreened_remainder: 0` prints happily over a search that is
  **27% short**. The error runs in the direction that makes a review look **finished** — the
  withholding direction, arriving at the search stage
- **Same class as the phase filter, different route** `apixaban-vte` lost NCT02366871 — one of
  its own two included trials — to `phase=[PHASE3,PHASE4]`, and P23 requires that miss to be
  recorded rather than replaced. **A query parameter and an unexhausted cursor remove trials the
  same way, and only the parameter had a guard**
- **And it is P16's fourth clause meeting its own case** every search this session recorded
  `returned == totalCount` with a null cursor as its pagination proof. Every one of those proofs
  was real and **untested** — the condition had never occurred. This is the first search that
  could have failed it, and it did
- **Detector** `scripts/lint_search_pagination_declared.py`, **wired**. A row whose
  `records_returned < total_reported` must declare the shortfall. **A declared shortfall passes**
  — apixaban's PubMed row reads *"439 records matched and 50 were retrieved. THE OTHER 389 ARE
  UNEXAMINED, NOT EXCLUDED"* and is legitimate. An undeclared one is the defect
- **Proven** `--selftest`, four proofs, the firing case reconstructed from the real page-1
  numbers; on first live run it found **3 declared shortfalls and 0 undeclared**, over 37 rows
- **What it cannot do** it compares two fields an object states about itself. It does not check
  that the numbers are true, nor whether the unexamined records matter — apixaban's 389
  unexamined PubMed records are declared, unexamined, and might contain anything

### 19. A bare string where a collection of terms is expected
- **Found** 2026-08-19, screening `bococizumab-lipid-review`. One character:

  ```python
  role = TI.locate(study, "bococizumab")      # a STRING, not the synonym list
  ```

  `locate` tests `any(s in blob for s in syns)`. **A string is a sequence of characters**, so
  this asked whether each arm's text contains the letter `b`, or `o`, or `c`. Every arm of every
  trial matched
- **What it produced** no exception, no null, no missing key, nothing malformed — and a
  completely ordinary-looking cascade:

  ```
  17 experimental / 0 comparator / 0 background / 5 not-assessable
  ```

  with **SPIRE-SI (NCT02135029), one of the review's own five included trials, EXCLUDED on the
  INTERVENTION limb** because its *atorvastatin* arm "contained bococizumab" on the strength of
  its letters
- **Why it is its own class and not an instance of E1** E1 is *substring is not identity*: a
  record named `Placebo (for alirocumab)` really does contain the drug's name and the question
  is what that containment MEANS. **Here the containment is of a single letter and means
  nothing at all.** E1 is a wrong reading of real evidence; this is a reading of no evidence,
  and it cannot fail
- **How it was caught** a known included trial fell out. **There was no other symptom and there
  could not have been** — the wrong answer has exactly the shape of the right one. This is the
  known-answer rule doing the only thing that could have worked, and it is why known answers
  come from the real corpus and never from a fixture the author invented
- **Detector, runtime** `topic_identity.require_terms()`, raising `TermsMustBeACollection`, at
  the **entry point** of `locate()`. A caller cannot skip it and gets a message naming the fix.
  Same discipline as `ctgov_transport.WrongPayloadShape`: an instrument that cannot read its
  input stops the run rather than emitting a number
- **Detector, static** `scripts/lint_string_where_collection_expected.py`, **wired**. AST scan
  for the *shape*: functions whose parameter is membership-tested or iterated without a guard,
  and call sites passing a string literal into one
- **Proven** `--selftest`, four proofs including that the guard does **not** fire on a correct
  call, that every non-`str` collection is accepted, and that the static scan still finds
  at-risk functions — a scan reporting nothing to report is broken, not clean
- **And the detector's own first two runs were wrong, both toward noise.** It reported **63**
  findings of which one was real, because definitions were keyed by NAME alone and one
  `def check(rows, …)` overwrote the `def check(name, got, want)` in fifteen other scripts.
  Narrowed to per-file resolution it still reported six: `validate_v2.block(self, rule, msg)`
  was not registered — it membership-tests nothing — so the name looked *unique* and six calls
  resolved against `build_app_v2.block(title, items, keys)`. **An ambiguity you cannot see is
  still an ambiguity, and counting only the interesting half made it look unique.** A check
  that fires on mostly noise is more likely broken than the corpus is, and that rule applies to
  the person writing the check
- **What neither can do** the static half resolves by name and cannot see a string arriving
  through a variable; the runtime half sees exactly that and only on code paths that execute.
  Neither checks the collection holds the RIGHT terms — `locate(study, ["x"])` passes both and
  finds nothing

### 18. A version marker that goes stale — the file that makes staleness visible
- **Found** on 2026-08-19, on the one document in this repository whose entire purpose is to
  make staleness visible. Three declarations of one property, no two agreeing:

  | where | value |
  |---|---|
  | `PAGE-STANDARD.md` heading | `1.6.0-2026-08-19` |
  | `PAGE-STANDARD.md` newest version-log entry | `1.12.0-2026-08-19` |
  | `ssot/build_to_standard.py::PAGE_STANDARD_VERSION` | `1.13.0-2026-08-19` |

- **Why it survived** **nothing shipped wrong.** Pages carry the *code's* constant, which was
  the newest of the three, so every built artefact was correctly stamped and no downstream
  check could have failed. **The drift had no downstream symptom**, and the only reader who
  could have caught it was a human opening two files that nothing gave anyone a reason to open
  together. This is the same ageing P18 names for `restated_*` blocks: a version marker is a
  *claim about another file*, and unchecked it shows that someone once looked, never that
  anyone looked last
- **Detector** `scripts/standard_version_agreement_gate.py`, **wired** into `.githooks/pre-commit`.
  Three limbs, all reported, never just the first: heading == constant; newest log entry ==
  heading; every property in the table named somewhere in the log
- **Proven** `--selftest`, five cases, and the second is **the state that actually occurred** —
  1.6.0 against 1.13.0, both values read from this repository's own history rather than
  invented. P16's fourth proof: the triggering condition has really arisen in data the guard
  has run on
- **What it found on its first live run** a *second* drift of the same kind in the same file:
  **ten properties listed in the table and named in no version-log entry** — P1–P9, the
  original set, and P30. Both now dated
- **What it cannot do** it compares three *declarations to each other*. A corpus stamped
  `1.14.0` by a builder implementing none of it passes this gate cleanly, and the gate says so
  in its own output rather than leaving a reader to assume otherwise

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

---

## Class 54 — A FLAG THAT CERTIFIES ONE HALF OF A QUESTION, READ AS CERTIFYING BOTH

`estimand_established` is TRUE on `attr-pn-review` and it is CORRECT. All three contributing
trials measure change from baseline in mNIS+7 — same instrument, same construct, timepoint
difference stated on the object. The estimand *is* established.

The pool is still meaningless:

| trial | intervention | comparator | kind of contrast |
|---|---|---|---|
| APOLLO (NCT01960348) | patisiran | sterile normal saline | its own randomised placebo |
| HELIOS-A (NCT03759379) | vutrisiran | **patisiran** | randomised, active |
| NEURO-TTRansform (NCT04136184) | eplontersen | inotersen *as the object records it* | **the stored effect is against the placebo cohort of NEURO-TTR, NCT01737398 — a different trial** |

**Patisiran is the intervention in row one and the comparator in row two, inside one pooled
number.** Two of the three stored values are non-randomised external-control comparisons
recorded as randomised arm contrasts. **I² is 88.1%** — the exact signal a reader is trained
to distrust — and it was live on the delivered page.

**The flag was doing half the job its name implies, and nothing else was doing the other
half.** Not this registry, not `regression_check.py`, not `prose_claim_gate.py`, not any of
the fifty-plus instruments written to date. `estimand_established` was the field that
*sounded* as though it had already asked.

**Established from the registration, not inferred.** NCT04136184's brief title names
eplontersen as the agent under study; its detailed description says participants in the
**inotersen reference arm** crossed over to eplontersen at Week 37; and its primary outcome
description says, verbatim, that efficacy *"was to be assessed by comparing participants
enrolled in the eplontersen arm only with the external placebo group"* and that *"there was
no statistical comparison planned between the inotersen arm and the eplontersen-treated/
external placebo group arms."* The object has the roles the other way round. **They are not
corrected** — a role swap changes what the object says a trial did, and the stored value is
not that contrast anyway.

**Named as P48 in `PAGE-STANDARD.md` v1.21.0.** The flag is not renamed: it is true, and a
rename moves a reader between meanings without telling them. Instead
`estimand_established_does_not_cover_the_contrast_2026_08_20` now sits beside it on **156
outcome blocks across 125 objects**.

### The sweep, and why its first draft was wrong

`scripts/audit_mixed_contrast_pools.py`. Across **32 pooled numbers in 26 topics** — every
block with k≥2 publishing a point that is not withdrawn — **2 mix kinds of comparison**:
`attr-pn-review/primary` and `rosuvastatin-auto-full-review/primary`. Both were already
**referred rather than closed** before the sweep ran, so it unmakes none of the ten. **Nine
are NOT_ASSESSABLE**, which means not looked at, not clean.

**The first draft scoped to `inputs.trials` and flagged seven topics. Two of the seven were
false accusations.** `malaria-vaccines` and `cryptococcal-meningitis` both CONTAIN mixed
contrasts and NEITHER POOLS ACROSS THEM — malaria stratifies into nine outcome blocks, every
cryptococcal block is k=1. **"The topic contains" is not "one number contains."** The check
now carries a **NEGATIVE control** beside its positive one and prints no count if either
side fails: `malaria-vaccines/r21_seasonal_first_12m` must come back UNFLAGGED.

**A third false accusation was in the classifier itself.** `doac-af-review` read as mixed
because ENGAGE AF's control label — `"Warfarin/Placebo Edoxaban"` — carries a placebo token.
Proximity cannot resolve that; warfarin and *placebo* are nine characters apart. Splitting
the label on `+ / and plus &` and treating the drug in the placebo-bearing segment as the
dummy reads it correctly, and `doac-af-review` is uniformly warfarin-controlled.

**Two declaration contradictions were reported and both are the instrument's error.**
`malaria-vaccines` declares `comparator_type: "inactive"` on two blocks whose comparator is
a rabies vaccine. The classifier calls a named vaccine ACTIVE; **the object's author is
right**, because a rabies vaccine has no antimalarial activity and is inert *for this
outcome*. **Inert is a property of the comparator against the endpoint, not of the
substance**, and a label-reading classifier cannot see endpoints. Recorded as overreach,
not as findings.

## Class 55 — ARM ROLES CONTRADICTED BY THE OBJECT'S OWN OTHER FIELDS

Reading one registration per trial does not scale to a corpus. `attr-pn` needed one; the
question is what an object can answer **about itself**, with no outside source.
`scripts/lint_arm_roles_contradict_the_object.py` asks exactly that, and every finding below
is two fields of the same object disagreeing.

**166 trials have both roles readable. 241 are UNREAD — no arms, or one role only — and
nothing below was asked of them.** 10 contradictions:

**A — a TREATMENT arm whose label is a placebo (4).** A placebo is not an intervention.

- `evolocumab-dyslipidemia-review` / FOURIER: treatment `"Placebo"`, control `"Evolocumab"`.
  **These arms carry counts** — 429/13780 on the row called treatment, 378/13784 on the row
  called control — so anything recomputed from them inverts with the roles.
- `evolocumab-mixed-dyslipidemia-auto-full-review` / HUA TUO: treatment `"Placebo Q2W"`,
  control `"Evolocumab 420 mg QM"`. Its sibling BERSON records atorvastatin as treatment and
  `"Evolocumab QM + Atorvastatin"` as control — **the topic's own index drug is in the
  comparator on both of its rows.**
- `icosapent-lipid-auto-full-review` / MARINE and ANCHOR: treatment `"Placebo"`, control
  `"AMR101 (ethyl icosapentate) - 4 g/day"`. **THIS TOPIC IS AT 4/4 ON P46, CLOSED TONIGHT.**
  The estimate is unaffected — those arms carry no counts and the per-trial values are the
  published mean differences −33.1 and −21.5 with the sign the publications report — but a
  reader who opens the arms table is told the treatment was placebo.

**B — the trial NAME names a comparator the control arm does not carry (3).**

- `hepatitis-b-taf-tdf-review`, both rows: name `"(TAF vs TDF, …)"`, control
  `"Open-label TAF"`. **TDF appears nowhere.** A comparison the object describes as TAF
  against TDF is recorded as TAF against TAF.
- `rosuvastatin-auto-full-review` / HOPE-3: name `"HOPE-3 (rosuvastatin 10 mg vs placebo)"`,
  control `"Candesartan/HCT"` — the **antihypertensive** factor of a 2×2 trial. A second,
  independent defect on a topic already referred for pooling an estimand HOPE-3 lacks.

**C — both arms name the same drug and neither is a placebo (3).** The two hepatitis-B rows,
plus `netarsudil-ocular-hypertension-auto-full-review` / ROCKET-2: `"AR-13324 … 0.02% & pla"`
against `"AR-13324 … 0.02% BID"` — a dose-or-schedule contrast beside two
netarsudil-against-timolol rows, and **the treatment label is truncated mid-word at `& pla`**.

**C's first draft accused three `intensive-bp-review` rows** on the shared token `"BP"` —
`"Intensive BP control"` against `"Standard BP control"` is a strategy contrast, correctly
labelled. C now routes through the same drug recogniser as the mixed-contrast sweep, so a
shared token must be a DRUG. **A fourth false positive, `cryptococcal-meningitis`' COAT row,
gives both arms antiretroviral therapy and says so in its own label — a declared strategy
contrast is not a mislabelling**, and a control label matching the CARE vocabulary now
suppresses C.

**Nothing is corrected.** A role swap changes what the object says a trial did, and where
arms carry counts it inverts anything recomputed from them. `attr-pn` is the standing
warning: there the roles looked obvious from the drug names, and the registration turned out
to say something sharper still.

## Class 56 — FIFTY-SIX DOCUMENTED CLASSES IS NOT FIFTY-SIX CONTROLS, AND THIS FILE SAID OTHERWISE

**Documentation failed as a control under the best conditions it will ever get.** The
heredoc class was breached **nine times** by an author who had read it completely; the tenth
attempt was stopped by a hook that does not care whether anyone understands it. So the
question this registry answers is not "have we recorded it" but **"is there a command that
fails when it recurs, and has it been shown to fail on a real instance?"**

`scripts/audit_class_mechanisation.py` asks that of the thirteen classes opened 2026-08-20,
and it does not take my word for any column: `can_fail` parses the module for a *reachable*
non-zero exit with the docstring stripped, `hooked` looks the command up in `.githooks/`,
and `fired` requires a named self-test marker to exist in the file.

**The first run: PROVEN 0, UNPROVEN 6, DOCUMENTED ONLY 6.** Eleven of the twelve
instruments written that night could not fail. They print.

**And the mechanism by which that happened is worth more than the count.**
`scripts/lint_gate_can_fail.py` already enforces *"a file named `*_gate.py` must be able to
fail"* — written after four files named gate turned out to be triage tools. **Every
instrument written since has been named `lint_*` or `audit_*`.** Nobody evaded the rule. The
rule was scoped to a filename and the filenames moved.

**Its own first version scored `test_apply_reml_guard.py` — fourteen proofs, two of which
SKIP rather than pass when unrun — as unable to fail**, because it looked for `sys.exit` and
a pytest file fails through `assert`. A mechanisation audit blind to the one mechanism
already in place is the defect it was written to measure, and it is recorded rather than
quietly fixed.

### What was mechanised, and what deliberately was not

Three classes moved from prose to refusal. Each carries `--prove`, which constructs a
failing input and requires a refusal, **because a gate never shown to fail is a gate nobody
has tested — and that is the subject of two of the three.**

**THE ACCUSING DIRECTION** — `scripts/instrument_controls.py` +
`scripts/lint_instrument_declares_a_control.py`, hooked. Four wrong accusations in one
night: 0.06 and 1.79 read out of a **withdrawal notice** and relayed to a reader as what the
page serves; `pool_broken` against a pool withdrawn on purpose; two unbacked-claim findings
against the flagship that were not unbacked; 49 never-taken branches from an extraction that
captured code spans. **Every one was caught by a person reading the instance. Not one by the
instrument.** So the reading becomes part of the instrument: a positive control whose answer
is established *independently* — a registration, a delivered page, a recorded prior finding,
never the same logic under test — and, where over-flagging is the failure mode, a **negative
control it must not flag**. The mixed-contrast sweep's first draft accused two topics that
contain mixed contrasts and pool across none of them; only the negative side catches that.

The check sees **59 of the 115** files named `audit_`/`lint_`/`*_gate`; the rest take a path
argument or iterate through a helper and are **NOT ASSESSED**. That residual is stated, not
counted as clean. **57 uncontrolled instruments are baselined and the count must never
rise** — they are not excused on the merits, they are excused because rewriting fifty
tonight would itself be an unreviewed corpus-wide change, which is the shape of half the
entries above.

**EXCLUSION BY ABSENCE** — `scripts/audit_exclusion_by_absence.py --gate`, hooked. **1,300
negative guards is a population and a check that blocks on a population blocks everything.**
The subset that cost us something is the **125 inside a loop over the corpus**: a guard there
decides what a *fix reaches*, and `zero paper-* sections` standing in for `built by an older
generator` silently removed three live pages from the reading-order rollout, two of which
serve nothing for a pooled point their own object holds. Ratcheted; each entry is a
candidate, not a verdict.

**CLASS 52, AT THE SITE OF TWO OF ITS THREE INSTANCES** — `scripts/regression_check.py`.
`wrong_protocol_link` keys on `arni_hf_protocol`, which appears on **no page in the corpus**,
and has therefore reported 0 on every run this project has ever made — **while sitting in the
BLOCKING set**, contributing a clean verdict it could never have contributed otherwise. Every
page is now asked whether the marker occurs *at all*, and a zero from a marker seen nowhere
prints NOT_ASSESSABLE. **Reported UNPROVEN and stated as such**: proving it needs a browser
run over the corpus, which has not happened since the change.

**CLASS 55** — `scripts/lint_arm_roles_contradict_the_object.py --gate`, hooked. The ten
contradictions are baselined and an eleventh refuses. **The baseline is not a clearance:**
FOURIER's swapped arms still carry their counts and icosapent's arms table still tells a
reader the treatment was placebo. It records that they are *seen*.

### After the pass: PROVEN 5, UNPROVEN 5, DOCUMENTED ONLY 3

The three still documented-only are the ones no command expresses — *the instruments are a
larger source of defects than the data*, *an unexpectedly large number is where checking is
most urgent*, *when one figure is defensible under two disagreeing definitions report both*.
**They are disciplines, and a discipline is a person remembering, which is the control that
has already failed nine times here.** Saying so is the point; a registry claiming fifty-six
closed classes when most are prose would be the reporting-layer failure applied to our own
defect record.

## Class 57 — A CHECK WEAKENED BY THE FIX IT JUST CAUGHT

`prove_register_change_moved_no_content.py` compares the `quoted verbatim` R sections of a
page before and after a change, as exact strings, because P46's fourth criterion requires
the model output verbatim and a reader checking the arithmetic needs exactly those
characters.

It **refused a build**. The register change had added a provenance superscript to the end of
every projected paragraph, and the R model results end:

```
   pred  ci.lb  ci.ub  pi.lb  pi.ub
 0.7636 0.7062 0.8258 0.7062 0.8258
```

so the page served `0.7636 0.7062 0.8258 0.7062 0.8258 2` — **a sixth column a reader could
take for data, introduced by the fix for readability.** Markers now go in front of
preformatted blocks.

**And then the obvious next step was the trap.** With the marker moved, the check still
failed, because the marker is *inside* the extracted text. The natural repair is to strip
`<sup class='prov-ref'>` before comparing — which is correct, and which **would have been
the exact wrong thing to do an hour earlier**. Had the marker stayed appended, the same
strip would have silently concealed the sixth column the check had just caught. The check
would have gone on passing, on a page serving a fabricated number, with the line that hid it
sitting in the file as a reasonable-looking normalisation.

**A normalisation added to make a check pass is only safe once you can say what it would
hide if the underlying thing had not moved.** The reasoning is in the function's docstring,
not only the strip — because the strip alone reads as obviously fine, and that is the
problem.

**The near-identical case in the same pass, which the same discipline caught:** a topic with
no stored model output holds a *refusal* in its `quoted verbatim` section, and that refusal
legitimately changed — it used to end `-- no field: results.by_outcome.*.r_output.verbatim`
inline, and the field moved to the provenance list. The check called that a changed verbatim
block and restored six good pages. The repair — remove refusal blocks, compare only sections
that actually contain R output — is a *narrowing of scope*, not a normalisation, and it can
be stated without reference to what it might hide. That is the test for telling the two
apart.

## Class 58 — A CHECK WHOSE TRIGGERING CONDITION HAS NEVER OCCURRED, AND THE GENERAL FIX

Three instances in one file tonight: `wrong_protocol_link` keyed on a marker present on no
page; the `rapidmeta:pooled-estimate` meta tag emitted by no page; the resolver sweep
returning zero across 782 files. Class 52 named the symptom — *a zero has two readings and
only one is reassuring*. **This is the remedy**, and it came out of writing
`lint_container_repr_on_a_page.py`.

That sweep's positive control is a **constructed fixture** — the exact GRADE cell as it was
delivered on 2026-08-20 — and not a live page. The reasoning matters more than the fixture:

> **A check whose positive control is "the corpus is currently dirty" stops working the
> moment the corpus is clean.** It passes its own control today, is fixed tomorrow, and from
> then on its control asserts nothing — it has become one of the three above, reporting a
> zero that means "nothing can match" while reading as "nothing is wrong". The fix that
> retires the defect also retires the evidence that the detector works.

So the positive control must be **independent of the corpus state**: a constructed input the
check must flag, carried inside the check, which keeps failing if the detector is broken
however clean the pages become. The corpus is what the check *measures*; it is not what
proves the check can measure.

**And the negative control follows the same logic in the other direction** — here, an
ordinary English sentence carrying a colon and a quotation, which must NOT match. Without
it, tightening the pattern until nothing matches is indistinguishable from fixing the defect.

**Where this applies.** Any detector keyed on a marker, a vocabulary or a pattern — which is
most of `scripts/`. `instrument_controls.require_controls` is where it is enforced;
`lint_instrument_declares_a_control.py` ratchets it for new instruments. The three instances
above are **not retrofitted** and remain in the baseline: they are on the record as
unfired, which is the honest state, and rewriting fifty instruments in one unreviewed pass
is the shape of half the entries in this file.

## OPEN — carried, not fixed

### O1. A check that reads a different working tree than the one being built

`scripts/regression_check.py` writes a nonce into the repo and fetches it over HTTP, so a server
serving another directory **cannot** satisfy the probe. That is correct and it fired twice on
2026-08-19, both times because **port 8787 was held by the sibling worktree of this same
repository** — a hazard the pre-push hook's own comments already record from 2026-08-17.

**What the probe does not do is say WHICH tree the server is serving.** It reports only that the
server is not ours, so each occurrence costs the same diagnosis again. Serving a tree-identifying
file — repo root path, `HEAD` sha — would turn a refusal into an answer.

**Cost so far: two interruptions in one session.** Not fixed.

### O2. A scoped pass that does not state its scope

The pre-push regression check globs **1,473 apps** and exceeds ten minutes when run whole, so the
hook scopes it to the pages a push touches. That is the right call — *a check nobody runs is the
same failure as a detector that cannot fire*.

But its output reads **`Regression check PASS on 80 page(s)`**, and is **silent about the other
1,393**. A reader takes a PASS as a statement about the corpus.

> This is the same shape as the delivery check that verified localhost, the projection gate that
> could not see 601 rows, and the tab audit where 43 of 43 passed a test that meant nothing. **It
> is currently in our own output.**

The fix is one line — state the denominator and what it excludes. Not fixed.

### O3. Three delivered pages are broken, unwarned, and serving a value

`PEMIGATINIB_BTC_AUTO_FULL_REVIEW.html`, `PEMIGATINIB_CHOLANGIO_AUTO_FULL_REVIEW.html` and
`TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html` fail the regression check with **`no_studies_rendered`
and `pool_broken`** on content **byte-identical to what is live**. They render zero studies,
compute no pool, and serve a pooled value on the dashboard.

**They carry no warning banner, and cannot be given one**: the gate blocks any push that touches
them, so a page cannot be improved while it is broken. That is a real property of the gate, not
a complaint about it — but it means the remedy has to be the underlying repair, not a notice.

`TIRZEPATIDE_ARDS` is additionally the page whose title says *Andexanet alfa*.
