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

## Class 59 — A FORMATTER THAT DROPS UNKNOWN KEYS ERASES CORRECTION HISTORY SPECIFICALLY

Not "renderers should print all their keys". That is the remedy, and stating the class that
way loses what makes it dangerous.

**`_grade_step_words` handled five keys — `domain`, `levels`, `from`, `to`, `reason` — and
silently discarded every other.** On `alirocumab-lipid` one rating step carries
`reason_superseded_2026_08_20`:

> "k = 8 and the interval (−60.23 to −49.42) excludes the null."

That sentence, holding the pool's own interval, **vanished from the delivered page**, and it
vanished because of the fix written to make the page more readable.

### The keys at risk are, without exception, records of where we were previously wrong

Swept across the corpus, the unknown keys sitting at known-key render sites are:

| key | what it is |
|---|---|
| `reason_superseded_2026_08_20` | the reason a GRADE rating gave before it was corrected |
| `what_the_split_does_not_establish` | the bound written when one pool became two |
| `value_the_index_published` | the number the dashboard served before it was withdrawn |
| `value_withdrawn_reproduces_as` | what the withdrawn estimate refits to |
| `previous_values` | the estimates this block replaced |
| `i2_definition_evidence` | why this I² is defined the way it is |
| `k3_corrected_from` | the count before the arm-role correction |

**Every one is a record of a past error and its repair.** Nothing on that list is ordinary
data. The vocabulary of this project's corrections — `superseded`, `restated`, `previous`,
`corrected_from`, `withdrawn_note`, `_does_not_establish` — is by construction *unusual*, so
a formatter that knows the ordinary keys and drops the rest **removes precisely the
correction record and leaves the current claim standing.**

### That makes it self-concealing, and the selection effect runs the wrong way

A page that has lost `reason_superseded_2026_08_20` still shows its GRADE rating, its
interval, its downgrade reason. **It reads as complete.** What is missing is the evidence
that it was ever different — so the defect removes its own trace, and a reader has nothing to
notice the absence of.

**And it strikes hardest where the work has been best.** A thin, neglected object carries no
`superseded` keys because nothing about it has ever been corrected; it is *immune*. The
topics carrying the most such keys are `sglt2-hf`, `alirocumab-lipid`,
`apixaban-vte-prophylaxis`, `rivaroxaban-vasc-review`, `sotagliflozin-hf` — the four clean
topics and the ones most reworked. **Every quality signal we have points at the pages this
class damages most.**

### State of the sweep

`scripts/audit_projector_key_filters.py`. Predicted 6–10 renderers; **found 42**, of which
**27 print only the keys they name**, against **192 object-side hits**. The prediction was
wrong by a factor of five in the direction that understated the risk.

The count then came down again on the **sole-rendering discriminator** — a renderer is a
filter only where it is the node's *only* rendering. That test is sound and it is kept, but
**it was formulated after seeing 192 hits, not before**, which is exactly where motivated
reasoning enters. It is recorded as a judgement in the sweep's own docstring, not as a
measurement. **One renderer adjudicated, 27 unadjudicated.** Nobody should read "42, mostly
fine" until each has been read against the pages it produces.

Found by `prove_register_change_moved_no_content.py`, whose estimate invariant compares
every number on every page rather than sampling — and which found this on the one page in
the corpus where it could be found.

## Class 60 — A METRIC A DEGENERATE ARTEFACT MAXIMISES WILL, GIVEN A GUARD, DEFEND DEGENERACY

**Three instances tonight, and they only became one class on the third.**

| | the measure | what a degenerate artefact scores | what it did |
|---|---|---|---|
| **ACS / totals** | section count, word count | a page of headings scores full marks on both | SGLT2 and ARNI read as siblings — 27 sections against 29 — while one had 219 words in the four sections a reader opens |
| **P47 weighting** | manuscript length, section presence | a manuscript of refusals has every section and reasonable length | the page passed `manuscript_guard`, which knows delivered length and section count and said the two pages were siblings |
| **BOCOCIZUMAB** | machine-vocabulary count | **an empty page scores ZERO. A perfect score.** | the guard restored the empty tab over an 81-sentence manuscript, twice, in two independent checks |

The first two were reporting failures. **The third had a guard behind it, and that is the
difference that makes this a class.** `BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW` served the honest
absent-state banner — two sentences, no manuscript, zero machine vocabulary — and the
rebuild gave it a real paper. Both the rollout predicate and the invariance check read that
as a regression and **rolled the page back to blankness.**

> **A quality metric that a blank page maximises will, given a guard, actively defend
> blankness.**

And note what kind of error it is not. The stale-baseline fault and the concurrency fault
compared the **wrong values**. This one compared the right values correctly and reached the
wrong verdict, because **the metric assumed both sides were the same kind of thing.**

### The rule

**Before a metric guards anything, ask what a degenerate artefact scores on it.** An empty
page. A page of boilerplate. A page of pure refusals. If any of them beats a good page, the
metric will be enforced against the good page eventually — not as a possibility, but as the
thing that happens the first time a good page appears.

### Measured, not assumed

`scripts/audit_degenerate_artefact_scores.py` constructs the three degenerates and a real
page and calls the actual metric functions on them:

| artefact | sentences | machine | rate | flow paths |
|---|---|---|---|---|
| EMPTY | 2 | 0 | **0%** | 0 |
| BOILERPLATE | 7 | 0 | **0%** | 0 |
| REFUSALS | 8 | 0 | **0%** | 0 |
| **REAL** | 3 | 1 | **33%** | 0 |

**Three of the four rollout predicates defend all three degenerates.** Machine sentences,
machine-vocabulary rate, and field paths in the flow are all *maximised* by an empty page.

**The only one a blank page loses is sentence count** — which is why the gained-a-manuscript
branch is keyed on it rather than on any quality measure. **A count of things present is the
only one of these a degenerate artefact cannot win, and it is the crudest of them.** Even
that is beaten by boilerplate and by refusals.

### The uncomfortable case is the refusals page

Refusing by name is **required** behaviour here. A page that does nothing else is honest, it
carries no machine vocabulary, no unglossed statistics, no field paths in prose — it scores
at or near the top of every readability measure written tonight — and it is worthless to a
reader. P47 exists for exactly that reason. **These metrics do not know it**, and the check
says so in its own output rather than leaving it to be noticed.

## Class 61 — THREE INSTRUMENTS IN ONE NIGHT THAT PUNISH A PAGE FOR BEING HONEST

This is a pattern about **us**, not about the pages.

| instrument | the honest thing the page did | what the instrument did |
|---|---|---|
| `pool_broken` in `regression_check.py` | withdrew a pool **on purpose, with a stated reason** | scored it as a broken pool, in the BLOCKING set |
| a regex I wrote, and relayed to Mahmood | printed a **withdrawal notice** naming the numbers it was not serving | read `0.06` and `1.79` out of that notice and reported them as what the page serves |
| **P47**, written tonight to fix exactly this | refused four reader-facing sections **by name**, saying what is missing and why | failed the page — while **passing** a page of content-free filler |

Each page did the disclosed, careful thing and each instrument marked it down **for saying
so**. The general form was already in the registry as one line — *a checker that reads a
disclosure as the defect it discloses penalises a page in proportion to how honestly it
documents itself* — and three instances in one night promote it from an observation to a
directional bias in how this project builds instruments.

**The P47 inversion is the sharpest of the three and it is counterintuitive, so state it
exactly:**

> **P47 fails the honest page and passes the empty one.** The refusals page tells a reader
> precisely what is missing and why. The boilerplate page tells them nothing and looks
> complete. As written, the criterion **penalises disclosure and rewards padding.**

Measured, not argued — `scripts/prove_p47_against_degenerates.py` scores the real Section
shape against P47's real predicate:

| artefact | P47 |
|---|---|
| EMPTY (no sections) | FAILS |
| **REFUSALS** (all four correctly refused) | **FAILS** |
| **BOILERPLATE** (73 words/section, names no finding, estimate, trial or field) | **PASSES** |
| REAL | PASSES |

**Why this matters now rather than later:** P47 is in `PAGE-STANDARD.md`, it ratchets, and
**133 topics have not been built to it yet.** A topic author under pressure to clear P47 has
a cheap passing move available, and it produces something worse than the refusal it
replaces.

**NOT PATCHED, DELIBERATELY.** A word-count threshold cannot be repaired by raising the
threshold. The fix has to be a SPECIFICITY test — does the section name a finding, an
estimate, a trial, a field this object holds? — and designing that at five in the morning is
how a bad criterion gets ratcheted into the standard for 133 topics. The hole is recorded in
the standard itself so the next person to open it meets the known failing case rather than
trusting the criterion.

## Class 62 — THE CRASH IS THE LUCKY SYMPTOM, AND DEFENSIVE CODING WOULD HAVE REMOVED IT

`cangrelor-pci-review` holds a results block `corrected_composite_3component` that is
declared in **no** `outcomes[]` entry. A bare

```python
outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
```

raised `StopIteration` and killed the page build. It was fixed at the site where it
surfaced — and **the next bare `next()` downstream killed the build again.** The idiom
appears **ten times** across `build_tabbed.py` and `validate_v2.py`; repairing the crash
where it appeared was repairing a symptom.

**And the crash and the invisible estimate are the same defect.** That block carries a LIVE
pooled point — **0.9646, k=2, not withdrawn** — while the topic's `primary` is withdrawn. So
the object publishes an estimate the delivered page has never shown: `0.9646` appears
nowhere in the bytes. CANGRELOR was already on the open list as one of two pages serving
nothing for a pooled point its object holds, and **this is why** — reached from a completely
different route, an accidental sample while looking for something else.

> **A build that dies gets noticed inside a batch. An estimate that never renders is silent
> forever.**

**So the instinct to make the crash go away would have made this permanent.** Had that
lookup been written defensively from the start — a `.get()`, a `try/except`, a default —
there would have been no crash, a page still missing its estimate, and **nothing to
notice**. It is the same trade as `.get(k, default)` masking a present-but-null key, and the
same as a `k` that agrees while the trial set differs.

**Defensive coding on a lookup that should never fail converts a loud defect into a silent
one.**

The two paths are therefore fixed differently, on purpose:

- **the renderers** refuse the block **on the page**, so the silence becomes something a
  reader meets;
- **the validators** route through `_declared_outcome()`, which raises a **named** error
  listing the declared ids — explicitly **not** a default, because a default lets a
  validator run to completion on a block it cannot describe.

**Bounded, with its population stated so a singleton is not mistaken for a broken sweep:**
**1 orphan block across 155 objects.** Zero elsewhere, and the zero was measured.

## Class 63 — THE FILE WHOSE ENTIRE SUBJECT IS CHECKS THAT CANNOT FAIL, THAT COULD NOT FAIL

`scripts/prove_never_fired_by_graft.py` exists to resolve checks that have never fired: it
constructs an input each one must refuse and requires a non-zero exit. **It printed the exit
codes and returned 0 whatever they were.**

A graft that does not fire is the entire finding, and the file reported it as text.

**It was caught by `lint_gate_can_fail.py`, four hours after that rule was widened** from
the filename `*_gate.py` to the role — any file named `lint_`, `audit_`, `check_`,
`verify_`, `prove_`. Under the old scoping this file would not have been examined at all,
because it is named `prove_`. **The widening has now paid for itself twice**: it surfaced 45
verdict-returning files that cannot fail, and it caught the one written to prove that other
files can.

Recorded as its own instance rather than folded into class 48 — *the instruments are a
larger source of defects than the data* — because the specific shape is sharper than the
general one, and the general one is already too comfortable to be useful.

## Class 64 — A GREP FOR AN IDIOM IS A STRING MATCH ON A HABIT

`cangrelor-pci-review` killed **three** page builds on the same construct, and the
population was measured wrong twice:

| | |
|---|---|
| `grep 'next(o for o in canon["outcomes"]'` | **10 sites** |
| the third crash | at a site written `next(x for x in canon["outcomes"] ...)` |

**The loop variable was renamed and the string match missed it.** Each repair was then made
where the traceback pointed — three symptom repairs in a row, each one confident it was the
last, and the third cost a full batch cycle.

> **The habit varies and the idiom does not.** `next(<genexp>)` with no default is a
> *shape*; a shape is what an AST walk finds and what a grep cannot.

`scripts/audit_bare_next_over_generator.py` measures it as
`Call(func=Name('next'), args=[GeneratorExp])` with one argument. Its positive control is
the exact failing shape **with the loop variable renamed**, because a rename is what defeated
the grep.

**Result: 12 `next(<genexp>)` calls across the nine render and validate files, all 12
supplying a default, 0 bare.** The zero states its own denominator — *looked and found none,
12 such calls exist and every one supplies a default* — so it cannot be read as a search that
could not match. That is class 52 applied to this sweep's own clean result.


## Class 65 — A CORRECT OBJECT, A CORRECT REFUSAL, AND NO CONSUMER OBLIGED TO READ IT

Every other defect found on 2026-08-20 was an instrument or a projector saying something
**wrong**. This one is different in kind: **the object is right, the fields are right, the
refusal is right, and nothing is required to consult them.**

`sglt2-mace-cvot-review` publishes a pooled odds ratio of **0.9074 (0.831 to 0.9908)**. Beside
it, on the same object:

| field | value |
|---|---|
| `outcomes[0].name` | **"Multiple trial-declared outcomes:"** followed by four different registered titles concatenated with pipes |
| `estimand_established` | **false** |
| `estimand_id_means` | "not recorded on the page this object was extracted from" |
| `pool_uniformity.effect_measure` | "NOT ESTABLISHED" |

**Four fields, all honest, all saying the same thing, and the page published anyway.**

> **A declaration nobody is required to consult is documentation, and documentation has
> failed as a control every time this project has tested it.**

That is the same law as the heredoc rule — breached nine times by an author who had read it —
**arriving in the DATA layer rather than the code layer.** `estimand_established: false` is
breached by a renderer that was never told to ask.

### Measured

`scripts/audit_published_over_unestablished_estimand.py`, across 155 objects and the **34**
pooled estimates currently published with a point set and not withdrawn:

| `estimand_established` | count | meaning |
|---|---|---|
| TRUE | **7** | established and published |
| **FALSE** | **2** | **the object looked and said no, and a reader meets the number anyway** |
| NULL | 14 | never checked |
| field ABSENT | 11 | the question was never posed |

**Never summed.** A question nobody asked and a question answered NO are different states,
and the objects' own `estimand_established_means` says so explicitly.

The two FALSE are `rosuvastatin-auto-full-review` and `sglt2-mace-cvot-review` — **both
referred tonight, for exactly this.** So the firing set is small and known; the structural
gap is that nothing made it small.


## Class 66 — A REVIEW THAT SELECTS AMONG REGISTERED OPTIONS WITHOUT RECORDING THE SELECTION

**Three instances on 2026-08-20, across three drug classes, three sponsors and three
registries.** It is no longer a property of our topics; it is a finding about how reviews get
built.

| topic | what was registered | what the review used | what records the choice |
|---|---|---|---|
| `sglt2-mace-cvot` | DECLARE-TIMI 58 registers **two co-primaries** — CV death/MI/ischaemic stroke, and CV death/HHF | the MACE composite | **nothing** |
| `inclisiran-lipid-kidney` | ORION registers LDL-C change at **day 510** and a **time-averaged** change | day 510 | **nothing** |
| `icosapent-lipid` | MARINE and ANCHOR each register **three arms** — placebo, 2 g/day, 4 g/day | one dose arm | **nothing** |

**The mechanism is identical and so is the invisibility property.** The object holds one of
the registered options, correctly transcribed, so **nothing about it looks incomplete.** There
is no null, no refusal, no missing field — the absence is of a *record that a choice
occurred*, and an absent record of a choice is indistinguishable from there having been no
choice to make.

> **A review that selects among registered options without recording the selection has made
> an analytic decision that cannot be audited from its own output.**

**It is a sibling of the composite-endpoint class**, and the pairing is the useful part: that
one is *two trials measuring different things pooled as one*; this one is *one trial
measuring several things, one of which was silently kept.* Both produce a number whose
question is not the question anyone registered, and **neither is visible in heterogeneity** —
a silently selected co-primary or dose arm is internally consistent and pools beautifully.

**THE SELECTION RATIOS SPAN 1-OF-2 TO 1-OF-7, and the range is the finding.** One of two
co-primaries is a defensible convention badly recorded. **One of seven is a trial being
repurposed.**

| ratio | topic | what the other options were |
|---|---|---|
| 1 of 2 | `sglt2-mace-cvot` | the other co-primary, CV death or HHF |
| 1 of 2 | `inclisiran` | the time-adjusted change across the dosing interval |
| 1 of 3 arms | `icosapent` | the 2 g/day dose |
| 1 of 3 arms | `bococizumab` / SPIRE-SI | **an atorvastatin active-comparator arm** |
| **1 of 7** | `bococizumab` / **SPIRE-AI** | **six measures of whether an injection was successfully administered** |

**SPIRE-AI is what the class means.** Six of its seven registered primaries measure the
percentage of injections meeting a successful-assessment definition on a participant
assessment tool — **it is an auto-injector usability study**, and its lipid endpoint is
pooled into a meta-analysis of lipid lowering. Until 2026-08-20 nothing on the object or the
page said so.

**And the object already held the evidence twice over.**
`inputs.trials[NCT02458287].registered_primaries` listed all seven verbatim, and
`arms_as_the_registry_lists_them` held the correct four-arm dose-matched listing beside the
two-arm pairing in `arms` that contradicts it. **The object contradicted itself in two places
and nothing was obliged to read either** — class 65, again. The failure was never extraction
and never honesty.

**Direction is not asserted.** Nothing read shows a selection made after seeing the data.
What is asserted is that the selection is unrecorded, which is checkable and true.

## Class 67 — ESTIMAND MISMATCH ARRIVING THROUGH THE SUMMARY STATISTIC

The fourth instance of *the pooled quantity is not the quantity the trials estimated*, and
the first to arrive through the **summary statistic** rather than through the endpoint's
components.

MARINE and ANCHOR both register their primary as a **MEDIAN percent change** from baseline to
Week 12 in fasting serum triglycerides. `icosapent-lipid` stores and pools a **MEAN
DIFFERENCE**, −25.84.

**In these populations the two diverge by construction.** MARINE enrols on triglycerides
≥ 500 mg/dL and ANCHOR on ≥ 200 mg/dL — threshold-selected, right-skewed distributions, which
is precisely the case where a trialist reports a median. **So the pool answers a question
neither trial asked.**

The family now reads:

| instance | how the estimands differ |
|---|---|
| `attr-pn` | the **contrast** — patisiran as intervention in one row and comparator in another |
| `sglt2-mace-cvot` | the **components** — non-fatal stroke of any type against ischaemic stroke only |
| `rosuvastatin` | the **outcome** — a pooled estimand HOPE-3 does not hold |
| `icosapent-lipid` | the **summary statistic** — a registered median pooled as a mean |

**And none of the four is visible in I².** Each pools internally-consistent numbers that
answer different questions; heterogeneity measures dispersion among estimates, not whether
they estimate the same thing. `estimand_established` was written for this and, per class 65,
nothing was obliged to read it.

**Both findings render beside the estimate**, not only on the object — the standing test for
anything found: *does it reach a reader, or does it exist for us.*


## Class 68 — A PATH-KEYED COMPARISON CANNOT DISTINGUISH A RELOCATION FROM A DELETION

**Three instruments, all keyed on position or identity rather than on value, all reporting
movement as loss.** That is a class, not three notes.

| instrument | keyed on | what it reported |
|---|---|---|
| `scripts/baselines/exclusion_by_absence_baseline.json` | `file:line` | 8 guards "new", 9 "gone" after a six-line docstring shifted them. **Not one line of guard logic changed.** |
| `lint_self_describing_safety_claim` baseline | a **count** of claims | detects growth; **blind to substitution** — a claim replaced by a different claim reads as no change |
| the leaf-by-leaf object comparison | a **dotted path** | 5 values reported lost when they were **relocated** under `superseded_state_2026_08_20`, all five verified present by value |

**The key does not identify the thing it names.** A line number names a position, a count
names a quantity, a dotted path names a location — and in each case the thing being watched
is a *value* that can move. Every one of the three answers "did it move?" while being read as
"is it still there?"

**And the failure mode is asymmetric in the dangerous direction.** All three over-report
loss, which is noisy but safe. The *count* baseline additionally under-reports substitution,
which is silent — a claim swapped for a different claim leaves the number unchanged. **Of the
three, the count is the one to fix first**, and it is the one whose defect is invisible.

Not fixed tonight. Keying on the guard text plus its enclosing function, on the claims
themselves rather than their number, and on values rather than paths, would each survive the
movement they currently mistake for deletion.

## Class 69 — I BREACHED A STANDING RULE THAT WAS ENFORCED, AND THE GUARD HELD WHERE I DID NOT

**"Never net-delete from `ssot/**/*.json`" is one of the five genuinely enforced standing
instructions** — `scripts/ssot_net_deletion_check.py`, wired into pre-commit. Tonight I wrote
four appliers that each do:

```python
obj["risk_of_bias"] = { ... }
```

**A wholesale subtree replacement.** On `bococizumab-lipid-review` that removed five leaf
values — the prior tool, state, why, consequence-carried-into-grade and what-would-close-it —
which were the record of what the topic said *before* it was assessed.

**The guard held and the writer did not**, which is the heredoc lesson exactly: the rule was
known, written down, and enforced, and it was breached by the person who had spent the night
writing about it. What caught it was a **leaf-by-leaf comparison against HEAD**, not the
applier that did the deleting, and not the pre-commit hook — which would have caught it at
commit time, one step later.

**Measured across the four appliers**: the wholesale pattern is in all four; it caused a real
loss in **one**. The other three were spared by luck — two replaced an empty field and one
re-authored identical content. **Wholesale replacement is the natural way to write an applier
and it will be written again.**

The prior state is restored under `superseded_state_2026_08_20` with the reason on the
object: *a reader comparing the two learns something a single current value cannot tell them.*


## Class 70 — A GUARD THAT COMPARES AGAINST WHAT IS DELIVERED GOES BLIND ONCE A FIRST FAILURE HAS LOWERED THE BASELINE

> **A guard that compares new against delivered cannot fire on a second failure once a first
> has lowered the baseline, and it will report NOT_ASSESSABLE — a correct answer — while a
> page is written empty.**

**What happened.** All four risk-of-bias appliers wrote `risk_of_bias.ceiling` as a bare
STRING. `paper_projector` does `ceil.get("statement")`, so it raised `AttributeError` and the
whole manuscript collapsed to a 318-character *projector failed* banner — **17,012 characters
and 27 sections to nothing.**

| page | what the guard said | outcome |
|---|---|---|
| `INCLISIRAN` | **REFUSED** — "−98.13% text, −1 sections" | saved |
| `EMPAGLIFLOZIN` | **NOT_ASSESSABLE** — "the delivered copy carries no manuscript panel — nothing to destroy" | **written empty** |
| `ICOSAPENT` | same | **written empty** |

**The guard was correct at every step.** The delivered copies genuinely had no panel — because
an earlier broken build had already stripped them. **The first failure removed the evidence the
guard needed to catch the second**, and it reported the honest three-state answer while the
damage went through.

**And the blindness opens exactly when it is most needed:** a guard of this shape is at full
strength while everything is fine and switches off the moment something has already gone
wrong.

### Every guard we have is of that shape — measured, not assumed

| guard | compares against |
|---|---|
| `manuscript_guard.py` | **working tree** |
| `regression_check.py` | **working tree** |
| `prove_register_change_moved_no_content.py` | **working tree** |
| `rebuild_paper_corpus_2026_08_20.py` | **working tree** |
| `dashboard_projection_gate.py` | **working tree** |
| `durable_artefact_gate.py` | **working tree** |
| `ssot_net_deletion_check.py` | git **and** tree |
| `prove_no_value_lost.py` | git **and** tree |
| `generator_stamp_gate.py` | git **and** tree |

**Six of nine ask "is this worse than the file on disk" — a file that may itself be damaged.
Three ask "is this worse than a committed reference," which is the right question.** Git holds
a known-good state and six guards do not consult it.

### The corpus is currently clean, and that is a measurement not an assumption

**116 of 116 pages carrying a paper panel have ≥5 rendered sections. 0 show a projector-failed
banner, 0 have zero sections.** No page is presently sitting in the lowered-baseline state
where the guard would say "nothing to destroy". The two that were have been rebuilt: 27
sections each.

**Not fixed tonight.** Converting six guards to a committed reference changes what every one
of them means on an uncommitted working tree, which is the state most of this project's work
happens in. That is a design decision for daylight.


### Class 70, second instance — A SENTENCE CARRIED BETWEEN ARTEFACTS BY RETYPING

Converting `risk_of_bias.ceiling` from a bare string to a dict — the class-70 fix itself — I
**retyped** the house-rule sentence into four appliers and wrote `the sources read` where the
authored text said `the sources READ`. One word, one letter's case, in the sentence that
states the project's own no-low-by-default rule.

`prove_no_value_lost.py` caught it, **and only by luck**: the shape changed from string to
dict, so the old scalar path vanished and the value went missing with it. Had `ceiling`
stayed a string, a retyped word would have passed both the path-keyed and the value-keyed
check in silence — which is the gap that instrument's own docstring already names.

> **A sentence carried from one artefact to another should be MOVED, never retyped.**

Corrected in four appliers and four objects, and the three delivered pages rebuilt so the
page renders what the object holds. The rebuild is the point: for a few minutes the object
said `READ` and the delivered page said `read`, which is a field-versus-page disagreement of
exactly the shape this project treats as serious, arriving from a one-character edit.

### Class 70, third instance — O2 REPRODUCED IN A NEW INSTRUMENT THE SAME NIGHT

`prove_no_value_lost.py` skipped, with a bare `continue`, any object with no committed copy
at HEAD — then printed `OBJECTS COMPARED AGAINST HEAD BY VALUE: 155` as though 155 were the
population. **That is open item O2 of this file**, written here about the pre-push regression
check, reproduced by the same author in a new instrument on the same night, and a number was
quoted from it.

Found by `audit_exclusion_by_absence.py --gate`, which refused the commit.

**Measured, the exclusion was LATENT rather than realised: 155 on disk, 155 compared, 0
excluded.** The reported figure was over the whole population. It was true, and it was not
*known* to be true, and those are different things. The output now prints all three numbers
so a reader can reconcile them, and the guard is baselined with the reason.


## Class 71 — A FUNCTION WHOSE NAME PROMISES ONE THING AND WHOSE RETURN VALUE IS ANOTHER

`projectors.forest_svg(res, outcome)` does **not** return an SVG. With no `window` it
returns `fig(...)` — a complete Analysis-tab **card** carrying its own `<h3>`, download
links and explanatory note. Only the `window is not None` branch returns the image.

Wiring the manuscript projector's figure slot, I called it and wrapped the result in a
numbered `<figure>` with a `<figcaption>`. The reader got the heading **"Forest plot" twice
with two different captions**, and a whole Analysis-tab card nested inside a manuscript
figure — in the one session whose standing instruction is:

> **Take the logic, never the template.**

**THE LOGIC AND THE PRESENTATION WERE FUSED IN ONE FUNCTION AND THE NAME DISCLOSED
NEITHER.** The instruction is usually read as being about other people's code — allmeta,
the MITRAL html. It applies just as hard inside our own module, and it is harder to obey
there, because a name like `forest_svg` reads as a promise that the fusion has already been
undone.

**This is the sibling of the field-name-is-not-an-address class.** There, a name that looks
like a path is not one. Here, a name that states a return type does not state it. Both are
the same failure: *an identifier read as a contract it never carried.* And both are
invisible at the call site — the call compiles, runs, and returns something truthy.

**The fix is the shape to copy:** add `bare=True` as a keyword **defaulting to False**, so
no existing caller changes behaviour, and document the trap on the function itself rather
than in the caller that tripped over it. Changing the default would have been the tidier
API and would have silently altered every Analysis tab in the corpus.

*Caught on the first SGLT2 build by reading the rendered headings, not by any gate. No
check in this project asserts that a function's return shape matches what its name claims,
and none is proposed here — the honest remedy is the docstring and the keyword.*


## Class 72 — A REFUSAL NAMES WHAT COULD NOT BE DONE, NOT WHY, AND THE READER BLAMES THE INPUT

**The largest measurement error of the run: "the projector reproduces ~11% of ARNI" was
quoted for a week. Measured, it is 26.2%.**

ARNI's projected Discussion and Conclusions carried this refusal:

> *"the Discussion — this is a CONTENT gap. **The object records no interpretive text**, and
> none is generated here."*

The object held **seven authored paragraphs and a 534-character conclusion.** They refused
because their text carried `[[k]]`-style substitution tokens the projector could not
resolve — a limit of the renderer, stated as a fact about the object.

### The general form

> **A refusal names the thing that could not be done. It does not, unless written to, name
> the REASON — and a reader, including us, will attribute a blank section to the input.**

    "no discussion is recorded on this object"        <- a fact about the input
    "this discussion cannot be rendered by this tool" <- a limit of the renderer

**They produce the same blank section and they are opposite findings.** One says *go and
write it*; the other says *go and fix the renderer*. We read the first for a week and drew a
conclusion about the corpus from an artefact of our own code.

**This is the withdrawal-notice class arriving from the producing side.** There, an
instrument read our honest disclosure as the defect it disclosed. Here, we read our own
honest refusal as a fact about the input. Both are correct output, misread — once by an
instrument, once by us. The consuming-side fix was to teach the reader; **the producing-side
fix is to make the output unmisreadable**, because you cannot patch every future reader.

### The sweep, and what it does and does not catch

`scripts/audit_refusal_names_object_or_renderer.py` reads every refusal literal in the
projector and classifies its attribution. Bounded, and run:

| | count |
|---|---|
| names a fact about the **object** | 9 |
| names a limit of the **renderer** | 0 |
| names **both** | 2 |
| **UNMARKED** — says something is absent without saying which side is at fault | **29 of 40** |

**29 of 40 are read as OBJECT by default and say nothing to earn that reading.**

**And the sweep would not have caught the founding case.** That refusal did name the object,
explicitly and *wrongly*. Detecting a FALSE attribution needs evaluation against the object;
reading the string can only find an ABSENT one. The founding case is pinned as a
known-answer control so the instrument cannot quietly stop measuring the incident it was
written for — it classifies as BOTH, which is exactly why string-reading was insufficient.

WARN, not BLOCK: whether an UNMARKED refusal is wrong depends on the object it fires
against, which a file reader cannot know.

### The mapper measured its own assumption

The F1000 mapping reported ARNI's Introduction as an unread address. It was rendering at
**1,617 characters and had been for hours.** The mapper keyed on ONE candidate address
(`protocol.rationale`) and ignored the fallback the projector actually uses, so it reported
a working fix as missing. **A known-answer instance from the corpus would have caught it
immediately** — ARNI's introduction was on the page while the mapper called the address
unread. An instrument that checks one address for a consumer that checks two is measuring
its own assumption, not the consumer.


## Class 73 — AN OPEN-LIST ENTRY THAT MISDESCRIBES ITS OWN ITEM

Four entries on the open list were checked against their artefacts on 2026-08-20 before
being worked. **Three did not survive contact**, and the errors run in both directions:

| entry says | artefact says | direction |
|---|---|---|
| 12 unread resolver bodies | **15**, and 9 of them are not resolvers at all | larger, then much smaller |
| lint 50 stores a COUNT of claims | **no lint in this repo stores a count** — all six baselines store lists keyed by identity | the item does not exist |
| 23 mislabelled `registration_primary_counts`, 2 fixed → 21 | **7** are arm-order inversions; 15 more differ on denominators; and **56 of 107 hold a fractional value in a field named `_events`** | smaller, beside a much larger unnamed one |
| 18 unprovenanced percentages in `PAGE-STANDARD.md` | **41 of 42** name no artefact that produced them | more than double |

**This is class 72 arriving in the record rather than in the output.** There, a refusal
named what could not be done and a reader supplied the wrong cause. Here, an entry names an
item and a reader — us — supplies the wrong scope. Both are **our own honest record read as
a fact about the thing it describes**, and in both cases the misreading survived because
nobody put the text beside the artefact.

> **A list that drifts from what it describes stops being a list of open work and becomes a
> list of remembered impressions.**

The pattern in the errors is not random: **every one of the three wrong entries was wrong in
a way that made the work look smaller or simpler than it is.** An estimate that is wrong in
both directions is noise; estimates that are consistently optimistic are a bias, and this
project has now measured that bias in its own record four times in one night — the 77
forests read as 74, the 155-object value check quoted against pages, the 134 topics that
are 154, and these.

**The remedy is cheap and was not being done: read the entry against the artefact before
working from it, and correct the entry in place as part of the work.** Not fixed as a
process; recorded here so the next reader checks rather than trusts.


## Class 74 — OUR ESTIMATES OF OUR OWN REMAINING WORK ARE BIASED, NOT NOISY

**Five measured instances in one night, every one in the same direction.**

| we said | it was | ratio |
|---|---|---|
| 74 further forests | **46** | 0.6× |
| "0 values lost across 155 objects" — quoted against *pages* | 155 was the object population; the page population is 116 | wrong denominator |
| 134 topics need reader-facing prose | **154 of 155** | 1.15× |
| 12 unread resolvers · 21 mislabelled rows · 18 unprovenanced percentages | **15 · 7-beside-56 · 41** | all understated their scope |
| 2 `measure: null` rows on EMPEROR | **40 of 170** declare the measure only through `derived_from`; the literal `measure: null` does not occur | 20× |

> **An estimate wrong in both directions is noise. Estimates consistently wrong in one
> direction are a bias — and this one is now measured rather than suspected.**

**It belongs beside the silence thesis as its sibling.** Both are asymmetries nobody designed
and neither was found by reasoning about the system: both were found *by counting*. The
silence thesis says a system fails quietly in a preferred direction; this says our
*description* of that system errs in a preferred direction too. The second is worse in one
respect — a silent failure waits to be found, while an optimistic estimate is actively
quoted into decisions. **The 134 went to Mahmood as the cost of tier 3.**

### The operational consequence

> **Any figure of ours describing REMAINING WORK is a floor until measured.**

Not an estimate, not an approximation — a **floor**. It applies to the tier-3 cost already
put in front of Mahmood, and to whatever the prose-walker scan and the 39 legacy pages come
back with. A remaining-work figure that has not been re-derived should be reported as "at
least N", and the sentence should say it has not been measured.

### And the reason these survive: a date is not provenance

Measured in `PAGE-STANDARD.md`: **41 of 42 percentages name no artefact that produced them.**
Nearly every one carries a date instead.

> **A date says when somebody looked, not what they ran, and you cannot re-run a date.**

That is why `10.9%` survived a week of quotation. `scripts/audit_standard_percentages_provenanced.py`
reports the count at two units — cell and row — because the unit changes the answer, and an
unstated unit is the denominator defect in another form.


## Class 75 — A MEASURE ESTABLISHED IN A QUOTE AND ABSENT FROM EVERY FIELD

Measured across 155 objects: **170 trial-outcome effect blocks.**

| | of 170 |
|---|---|
| name the measure explicitly on the effect | **129** |
| declare it ONLY through `derived_from` | **40** |
| nothing declares it at all | **1** |

The 40 are not equally opaque, and the distinction is the finding: **24 are unambiguous**
(`published_hazard_ratio` 13, `published_vaccine_efficacy_percent` 11) while **16 say only
`published_ratio` or `published_ratio_and_its_interval` — "a ratio", without saying which.**
All sixteen are `iv-iron-hf` recurrent-event outcomes, where a rate ratio and a hazard ratio
are both plausible readings and **pooling one with the other is an estimand mismatch.**

The single block with nothing is `cryptococcal-meningitis / COAT / coat_26wk_mortality`. Its
measure **is** established — inside `provenance.source_quotes`: *"hazard ratio for death,
1.73; 95% confidence interval, 1.06 to 2.82"*. **Recoverable by a reader, invisible to every
consumer**, because no renderer reads a quotation looking for an estimand. That is the
field-name-is-not-an-address family inverted: the fact is present and unaddressable.

*The open-list entry for this said "the `measure: null` rows on both EMPEROR entries". There
is no literal `measure: null` anywhere in that object, and it is four trials there, forty
corpus-wide — the fifth entry tonight to understate its own scope.*


## Class 74, continued — THE BIAS REACHED THE HEADLINE NUMBER, AND THE FIRST COUNTER-INSTANCE

**Sixth instance, and it is the number every message of the night opened with.**

Reported all night: *"P46 10 of 28, of which **2** rest on a provenance-shaped refusal."*
Measured by `scripts/audit_p46_closure_quality.py`: **3** — `apixaban-vte-prophylaxis`,
`bempedoic-acid-review`, `bococizumab-lipid-review`, all three on the comparison limb.

**And a fourth thing was being counted as clean: 1 REFUSED/unclassified** (apixaban's
risk-of-bias), which is established as neither evidence-shaped nor provenance-shaped.

> **The headline is: 10 of 28, of which 3 provenance-shaped and 1 unclassified.**

Uglier, and the true shape. **An unclassified refusal is a third state and folding it into
either bucket is the reporting-layer failure** the three-state rule exists to prevent —
committed in the summary line of a project whose subject is that rule.

This one was relayed to Mahmood a dozen times.

### Two framing errors in the same report

**`acs-antiplatelet` was never in the denominator.** It was described as *blocked* on 227
unexamined records; it publishes no pooled estimate, so it is not among the 28 topics P46
scores at all. **Another unstated population** — a topic reported as blocked work inside a
count it was never in.

**AND THE FIRST PESSIMISTIC ERROR OF THE NIGHT: 8 topics sit at 0/4, not twelve.** Every
prior instance ran optimistic. This one runs the other way, and it matters methodologically:
**a bias measured only in one direction is a claim not yet tested against a counter-instance.**
Now there is one. The pattern is *estimates are unreliable and skew optimistic*, not
*estimates are always low* — and the operational rule is unchanged, because a floor is the
safe reading under either.

**Measured P46 remainder: 18 topics, 47 absent limbs** — 6 topics need one limb, 3 need two,
1 needs three, 8 need four. By limb: comparison 15, risk of bias 11, model output 11, GRADE
10. **Comparison first**: scarcest, and it is where all three soft closures sit, so one
method touches 18 limbs rather than 15.


## Class 76 — GIVEN THE SAME TRIALS, THE PUBLISHED SYNTHESIS CHOSE THE BETTER TARGET

**Four instances. This is the counterweight to the house thesis and it belongs at the same
weight as our findings against published work.**

This project's audits have found real errors in published syntheses — wrong trial sets,
uncorrected multiplicity, estimates that do not reproduce. That record stands. **So does
this one, and it runs the other way: four times now, given the same or overlapping trials,
published work chose a more defensible target than this corpus did.** Our estimate was not
wrong so much as **answering a worse question.**

| our object | the published work | what they did that we did not |
|---|---|---|
| `attr-pn-review` pools mNIS+7 across **three different drugs** → −25.11 | Samjoo 2020, PMID 32011182 | Assessed the network's **feasibility first** and declined it: *"An NMA of ATTR-PN treatments was not feasible, given the observed cross-trial heterogeneity"* — naming that *"neuropathy outcomes were not evaluated consistently between trials."* |
| `rosuvastatin-auto-full-review` pools **each trial's own differing primary** → OR 0.656 | Joseph 2022, PMID 33705531 | Pooled the **same two trials** on **one harmonised outcome**, with individual participant data. |
| `sglt2-mace-cvot-review` pools EMPA-REG + DECLARE → OR 0.907 | Kluger 2018, PMID 31032602 | Reviewed the **same trials** and **did not pool them**: *"a truly direct comparison"* would need matching criteria. **99.2% vs 40.6%** established CVD. |
| the earlier ATTR network | — | Refused to pool across drugs. |

**The common shape: they asked whether the pool should exist before computing one; we
computed one and asked afterwards.** In three of the four the published authors did the
feasibility assessment *as the study* and published the refusal as the result.

> **A synthesis that declines to pool, and says why, is a finding. We have been treating our
> own refusals that way for weeks and did not extend the same reading to theirs.**

**Symmetric standards, stated:** our audits found their errors; our comparisons found this.
Both are in the record, both measured, neither summarised away. **An asymmetry in which
direction we look is the one bias no instrument here can detect**, because every instrument
was written by the side doing the looking.

*None of the four changed a stored estimate. Whether to withdraw or restate a pool is a
content decision.*


## Class 77 — AN INSTRUMENT NARROWS ITS POPULATION BY THE ASSUMPTION THAT MADE IT NECESSARY

**Six instances in one run, and in every one the excluded region WAS the target region.**

| instrument | what it narrowed | what the narrowing excluded |
|---|---|---|
| `audit_path_resolvers.py` | `^(\s*)def` under `re.M` ate the newlines | **every body** — 0 resolvers across 782 files, from the file written to find resolvers |
| the `str(dict)` sweep | matched one repr shape | the container reprs actually on the page |
| the paper-panel extractor | read the first 400,000 chars | the panel, which sits past that offset — reported **0 of 116** |
| the F1000 mapper | keyed on ONE candidate address | the fallback the projector actually uses — called a working fix "missing" |
| `prove_never_fired_by_graft` | grafted at one site | the site the check reads |
| `audit_outcome_paths_call_both.py` | keyed on the literal `by_outcome`, then a 40-line window | **the `reported` and `declined` branches** — the two paths it existed to check — then the correct one, **by a single line** |

### Why it is one mechanism and not six accidents

> **A population is narrowed by the same assumption that made the instrument seem necessary,
> so the excluded region and the target region are the same region.**

The assumption that a resolver looks a certain way is what motivates a resolver sweep *and*
what its regex encodes. The belief that a field lives at one address is what makes a mapper
worth writing *and* what makes it check one address. **The instrument inherits the blind spot
it was built to cover** — which is why the failure is never random and never lands somewhere
harmless.

**And every one of the six reported an all-clear or a near-zero.** That is the signature: a
narrowed sweep does not error, it *reassures*.

### The rule, as a rule and not six local decisions

> **EVERY SWEEP CARRIES A FLOOR DERIVED FROM A CRUDER COUNT, AND EXITS `PROOF FAILED` RATHER
> THAN ALL-CLEAR WHEN IT FALLS BELOW IT.**

The floor must come from a **cruder** instrument than the sweep — a plain `grep`, a file
count, a known-answer instance from the corpus — precisely because a cruder count does not
share the sweep's assumption. Three forms, all now in use:

- **A crude-count floor.** `audit_manuscript_prose_doors.py`: fewer than a third of the raw
  `grep -c 'manuscript\.'` mentions and it exits `PROOF FAILED`.
- **A known-answer floor.** `audit_outcome_paths_call_both.py`: if it cannot find `in
  reported:` and `in declined:`, it exits — those are known to exist.
- **A named-exclusion floor.** `prove_no_value_lost.py` and others: print the population, the
  compared count, and the excluded count as three reconcilable numbers.

**A sweep with no floor is not evidence.** Its zero and a genuinely clean corpus are the same
output, and this run produced six of the former.


## Class 78 — THE ANALYSIS POPULATION IS PART OF THE ESTIMAND, AND A POOL CAN CROSS IT

**The composite-endpoint law rotated.** There the *components* of the outcome differed
between trials; here the *denominator population* does. **Both are invisible to heterogeneity
for the same reason:** a population shift moves every trial's estimate in the same direction,
so it inflates neither Q nor I².

In infection trials the population is named **inside the registered primary-outcome text**.
`CE` (clinically evaluable) excludes protocol violators and indeterminate responses; `ME`
also excludes patients without a qualifying pathogen. **Both are selected subsets of ITT and
systematically yield higher cure rates.**

### Swept corpus-wide, and it is not larger than the two — but the reason matters

| | |
|---|---|
| trial rows asked about | **403** |
| registrations read | **402** (1 not returned, named: `ceftolozane-infection` / `NCT01445665`) |
| pooled outcomes carrying a point | **34** |
| **cross an analysis-population boundary** | **2 of 34** |
| name exactly one population | 2 of 34 |
| **name NONE — population unstated in the registered text** | **30 of 34** |

The two: **`ceftaroline`** (`CE` pooled with `MITTE`, k=3) and **`tigecycline-ciai`** (`CE`
with `ME` and `mITT`, k=3).

> **30 of 34 is the number that matters, and it is not a clean bill — it is unexamined.**
> Where the registered text names no population, the estimand is not established either, and
> this sweep cannot distinguish "consistent" from "unknown". It reports the three states
> rather than folding the third into the first.

### And a trial with NO registered primary outcome is a different defect

Not a mismatch — **unverifiable**. There is nothing to check the extracted result against, so
the estimand cannot be established for that row at any level.

**3 distinct registrations, 4 topic-rows:** `NCT00034645` and `NCT00044486`
(`posaconazole-fungal`), and **`NCT00081744`**, which appears in both `tigecycline-ciai` and
`tigecycline-infection` and contributes to a published pooled estimate in each.


## Class 79 — WE PREDICTED FROM A NAME INSTEAD OF FROM THE ARTEFACT. THIRD TIME TONIGHT.

I named `malaria-vaccines` in advance as a likely class-76 instance **because its title
implies it pools RTS,S with R21.** It does not. Its question reads *"for each of the two
malaria vaccines separately"* and its pools are keyed `r21_*` and `rtss_*` — **the object
already holds the vaccines apart, correctly.**

**The prediction was made from the label, not from the object.**

That is the same mechanism as:

- the **mapper** that keyed on one candidate address instead of the accessor the projector uses;
- the **topic-identity** defect, where two objects for one subject were treated as two subjects;
- the **citation-string** defect, where a reference was matched on rendered text rather than identity;
- and, from the other side, **one trial counted several times** across published syntheses because names differed.

> **We audit published work for matching on names instead of identities. Three times tonight
> one of us did the same thing.** The mechanism does not care which side of the audit it is
> on, and a project that has built five instruments against it in others has now produced
> three instances of it in a single run.

### The running prediction score, recorded WITH class 76

Twelve comparison limbs, four predicted to yield a class-76 instance, **five tested:**

| topic | predicted | outcome |
|---|---|---|
| `finerenone-cv` | not an instance | **right** — reproduced an IPD analysis exactly |
| `cangrelor-pci` | not an instance, likely agrees | **half** — not an instance, but it disagreed materially |
| `incretin-hfpef` | an instance | **wrong** — they pooled the same mix, more broadly |
| `rotavirus-vaccine-africa` | an instance | **right** |
| `malaria-vaccines` | an instance | **wrong**, and predicted from the name |

**2 right, 1 half, 2 wrong of 5.**

> **A class whose predictions run at chance is a description, not a mechanism.** Stating that
> is what makes the two confirmed instances worth anything — and what stops class 76 being
> quoted as though four cases established a law.


## Class 80 — A FIELD THAT WOULD MAKE A TRUE-SOUNDING CLAIM ABOUT A PROCEDURE THAT DID NOT HAPPEN MUST STAY ABSENT

`gepotidacin` and `lefamulin` received full RoB 2 assessments per result on 2026-08-21, from
one assessor. The schema has a slot — `rob2.assessors` — and `lint_method_claim_has_a_field`
resolves the two-assessor claim against it. **Writing it would have cleared the check.**

**It was left absent, and that is the rule:**

> **A field whose presence would assert a procedure that did not occur must stay empty, even
> when the schema invites it, even when filling it clears a check, and even when the value
> would be literally true of *something* that happened.**

`rob2.assessors` does not mean "somebody assessed this". It means **the two-assessor
procedure was followed**, because that is what the manuscript sentence it feeds says. One
assessor recorded in a two-assessor field is the **un-tokened method claim in its live
form** — the thing this project spent a night refusing to inherit from ARNI's *"Two assessors
worked independently, drawn from different model families."*

**The difference between avoiding that sentence and earning it is the whole point.** ARNI
earned it: two entries, `openai / GPT-5` and `google / Gemini 3.1 Pro`, both flagged
`is_object_assembler: false`. Until a second family has assessed these results blind, the
field stays absent and each object carries `ONE_ASSESSOR_ONLY` saying so in its own words.

**The second-assessor queue is now SIX topics:** `empagliflozin-hf`, `icosapent-lipid`,
`inclisiran-lipid-kidney`, `bococizumab-lipid` from 2026-08-20, plus `gepotidacin` and
`lefamulin`.


## Class 81 — THE MODEL-OUTPUT LIMB IS EVIDENCE, NOT BOOKKEEPING

Both closures on 2026-08-21 needed a fit that did not exist. **Running it produced a finding
the stored value concealed, in both cases and in opposite directions:**

| topic | stored | what the fit showed |
|---|---|---|
| `gepotidacin` | RR 1.2007 (0.9668–1.4912) | τ² 0.0172, **I² 70.48%** — the two trials disagree in *conclusion*: 1.0762 (0.9138–1.2676) includes no difference, 1.3426 (1.1334–1.5904) excludes it |
| `lefamulin` | RR 0.9884 (0.9530–1.0250) | **τ² exactly 0**, Q 0.7316 on 1 df, p 0.3924 — the two trials agree closely |

Both refits reproduced the stored point to four decimal places, so **neither finding was an
error in the number** — they were properties of the pool that the point estimate cannot
express and that nothing on the page said.

> **P46 limb 4 has now twice paid for itself in evidence rather than in compliance.**

**And "no R output is stored" is a fact about our pipeline, not about the evidence**, so a
refusal citing it is provenance-shaped and does not discharge. Where a fit is possible, fit;
where k cannot support the model the page claims, say so **in the evidence's terms** — *two
trials cannot inform a between-study variance* is a statement about the trials, not about us.


## Class 82 — THE BREADTH FAILURE IS OURS. THIS REVISES `access-was-never-the-binding-constraint`.

**The founding proposition was that published syntheses fail on SEARCH BREADTH and on
CHECKING.** After a full run the evidence is:

- **Their checking:** three confirmed failures — wrong trial sets, uncorrected multiplicity,
  estimates that do not reproduce. **The thesis holds here.**
- **Their breadth:** **zero confirmed failures.** Not one published synthesis has been shown
  to have missed a trial we carried.
- **Our breadth:** measured below, and **it is where the gap is.**

### The table, from `scripts/audit_our_k_against_theirs.py`

18 topics carry a published comparison. **9 of the 18 appraised reviews do not state a trial
count**, so the comparable denominator is 9:

| | of 9 stated |
|---|---|
| **ours LOWER** | **4** |
| equal | 5 |
| **ours HIGHER** | **0** |

**We are never ahead.** `sglt2-mace-cvot` 2 against 3 · `incretin-hfpef` 2 against 4 ·
`nirsevimab` 2 against 6 · `attr-pn` 3 against 10.

### And the standard that keeps this honest

> **A count that exceeds ours is not the same as named trials we missed.**

| where ours is lower and the trials are **IDENTIFIED** — a nameable gap | **1** — `sglt2-mace-cvot` (CANVAS, named in Kluger's title) |
|---|---|
| where ours is lower and the set was **NOT READ** — counted only | **3** — `attr-pn`, `incretin-hfpef`, `nirsevimab` |

**Exactly one nameable missing trial across the whole corpus.** The other three are a
difference in stated counts and nothing more **until somebody opens the included-study
table** — and nobody has.

### Why this revises the memory rather than adding to it

`access-was-never-the-binding-constraint` recorded that we could reach the evidence we
needed. **That remains true and is now beside the point.** Reaching evidence and *searching
for* it are different capabilities, and this corpus has the first without having
demonstrated the second. A two-trial pool assembled from trials we already knew about is not
a search; **on nine topics where a published count exists, ours never exceeded it.**

> **The thesis was half right, and the wrong half was about us.**

*Not a defect in any single object. Whether these searches should be widened is a content
decision, and the one nameable case — CANVAS — is a decision about `sglt2-mace-cvot`
specifically.*


## Class 83 — WE SPENT THE RUN WRITING LIMB 3 AND DELIVERED IT TO NOBODY

**A reader met a table headed `Citation | PMID | Their k | Scope | How it differs from ours`
containing one identifier and FOUR EMPTY CELLS.** Not a refusal. A table asserting that a
comparison had been made, with nothing behind it — *strictly worse than the refusal the same
section emits when no comparison exists*, because the refusal at least tells the truth.

**The cause is two vocabularies and one reader.** `paper_projector` asked each record for
`citation`, `their_k`, `scope`, `how_it_differs_from_ours`. Every applier written during this
run stored `title`, `journal`, `year`, `outcome_pooled`, `agreement` instead.

| rows | vocabulary | what the reader got |
|---|---|---|
| 22 | the projector's | rendered |
| **16 across 13 topics** | **the appliers'** | **a PMID and four blanks** |

And the conclusion of each comparison — written to `THE_FINDING_OF_THIS_COMPARISON_<stamp>` —
**was read by nothing at all.** It reached readers only on the topics where the same sentences
happened to be copied into the outcome block as well. Limb 4 was the same: `model_output.verbatim`
was written by this run's appliers and the projector read `results.by_outcome.*.r_output.verbatim`,
so a refit that had been captured, stored and checked against the delivered point still produced
the refusal *"no analysis output is stored on this object"*.

> **This is class 65's mechanism landing on the limb we spent the night writing.** Limb 3 was
> counted as held on thirteen topics on the evidence that the object carried it. **Nobody opened
> the rendered table.** The P46 count I have been reporting measured objects, and P50 already
> says a referral must render where the estimate renders — the same test was never applied to
> the limbs themselves.

**Fixed at both ends, 2026-08-21.** The projector reads either vocabulary, renders the finding
and the identity basis, and reads top-level `model_output`; `add_table` now DROPS a row carrying
content in one column only and refuses a table left with none — *an empty cell under a filled
header asserts more than the object holds*. The objects are repaired additively so neither end
depends on the other being right.

### 83a. The count that was written as a word

Repairing the rows forced a second reading of `audit_our_k_against_theirs.py`: it derives their
trial count from the LENGTH of a stored list, so a count stated inside a sentinel string —
*"NOT NAMED — **fifteen studies**"*, *"**twelve trials**"*, *"**six** RCTs"* — was recorded as
**THEIR COUNT NOT STATED**. Six such counts existed. Class 82's comparable denominator was
therefore too small and its table understated how often ours is lower.

> **Third instance of the same shape.** A number spelled out is invisible to a check that looks
> for a number — the memory `grep-prose-copies-not-just-numeric` records the first.

The six are transcribed into the objects **by hand**, each carrying the sentence it came from and
each marked *counted, not identified*, rather than parsed out of prose at render time.


## Class 84 — THE OPTIMISM BIAS APPEARED IN CODE. THE DEFECT AND ITS REPAIR RAN THE SAME WAY.

Class 74 recorded that our estimates of our own remaining work are **biased, not noisy** —
they run short, and every figure describing remaining work is a floor until measured. That was
about *numbers we state*. This is the same bias **inside an instrument and inside its fix**.

`audit_our_k_against_theirs.py` decides how many trials a published synthesis carried. It had
three defects, and **all three ran in the direction that flatters us**:

| defect | effect |
|---|---|
| `NUM_WORDS` stopped at *ten* | "twelve trials", "fifteen studies" → **their count NOT STATED** |
| the noun list omitted `CVOT` | "ten CVOTs" → **NOT STATED** |
| any prose entry without "NOT READ"/"NOT NAMED" counted as one **named** trial | a sentence became **k = 1, IDENTIFIED** — a false *equal*, or a false *ours higher* |

Its positive control asserted that *"six RCTs"* reads as 6 — **a word inside the range and a
noun inside the list**. It could not have caught any of the three.

**Then the repair ran the same way.** The replacement named-trial test rejected entries over
40 characters. `CANVAS Program -- NOT pooled by this object` is **42**. The fix dropped the
corpus's only nameable missing trial — *the single case the whole instrument exists to
surface* — **by two characters**, inside a correction to an instrument that was already
flattering us.

> It was caught for one reason: the summary printed a nameable count of **0** where **1** was
> already established, and the discrepancy was looked at instead of accepted.

**Why this is its own class and not class 74 again.** Class 74 is a bias in a *stated
estimate*, correctable by measuring. This is a bias in a *measuring device* and then in its
*calibration* — so measuring harder does not help, because the instrument is the thing
leaning. The only defence that worked was a **known answer the instrument had to reproduce**,
and the only reason a known answer existed was that CANVAS had been established by hand on a
previous night.

Now a hard exit rather than a control: Kluger's stored three-trial set must read as
`(3, True)` or the file refuses to print anything. **A named-trial test is judged on the name
before the separator, never on the length of the whole entry.**

*Third recorded instance of the general shape — see also
`grep-prose-copies-not-just-numeric`: a number written as a word is invisible to a check that
looks for a number.*


## Class 85 — LIMB 4 QUOTES A TOOL VERBATIM, SO A DEFECT IN THE TOOL IS PUBLISHED AS EVIDENCE

`ssot/fit_from_per_trial.R` printed **metafor's raw `knha` interval**, which **narrows below
the unadjusted interval** whenever the Hartung-Knapp standard error is smaller than the
random-effects one. On `malaria-vaccines / rtss_recurrent_children_final`, Q = 0.0013 against
1 df and the raw interval is **0.6273 to 0.6473** against an unadjusted **0.5967 to 0.6805** —
four times narrower.

> **P46 limb 4 stores that output VERBATIM.** A reader would have met, quoted as our own model
> output, an interval this project's own floor rule exists to forbid. Every other limb is
> prose we wrote and can be held to; this one is a machine's words, and *quoting faithfully is
> not the same as quoting safely*.

The script now prints the **house interval first** and labels metafor's raw value separately,
flagging it when it is narrower.

### 85a. And the first version of the fix used the wrong factor

The floor was implemented as `max(1, sqrt(Q/(k-1)))` — the textbook expression. **It does not
reproduce what this corpus stores.** On `cab-prep-hiv-review` it gives 1.7910 where the object
holds `variance_inflation_applied: 1.0`, and the interval came out **0.0000 to 50888.9**
against the stored **0.0002 to 211.78** — because metafor has already absorbed the adjustment
into its `knha` standard error, so multiplying again **double-counts it**.

The factor this project actually applies is `max(1, SE_knha / SE_unadjusted)`. It reproduces
every stored value checked: agyw `0.3918 → 1`, cab `1.0000`, both malaria pools floored to 1.

**Caught only by comparing the computed interval against what the objects already held.** A
wrong statistical formula was one commit from being stored as limb 4 on three topics — and it
would have been quoted, verbatim and unchallengeable, as the output of our own engine.

### 85b. The number attributed to us was not ours

The same confusion had already reached a delivered page. `agyw-hiv-prep-review`'s finding and
its GRADE imprecision step both cited **"this project's Hartung-Knapp interval … 0.4054 to
1.2191"**. That is metafor's **raw unfloored** value. This project's interval is **0.1725 to
2.8655** — *three times wider* — and it was sitting in the object's own
`pooled_hartung_knapp` field the whole time.

The conclusion is unchanged: both intervals include no difference. **But a reader was told an
interval was ours that our own method does not produce, and the one we published was the
narrower of the two.** Corrected, with the correction announced.


## Class 86 — OUR INSTRUMENTS ARE UNRELIABLE IN WHICHEVER DIRECTION THEIR AUTHOR LEANED

**Correcting the record, which currently reads as a one-directional claim.** Class 84 measured
an optimism bias *in code* — three defects in `audit_our_k_against_theirs`, all running in the
direction that flattered us, and a repair that dropped CANVAS the same way. Read alone it says
*we flatter ourselves*. **That is not what the night's evidence shows.**

`audit_p46_limbs_reach_a_reader` has been corrected **three times**, and **every correction
lowered the defect count**:

| correction | reported | actual |
|---|---|---|
| probed `r_output`'s prose siblings instead of `verbatim` | 11 topics "limb 4 reaches no reader" | one of them had been confirmed on the public host an hour earlier |
| probed the single longest stored string for RoB — the `NO_INFORMATION` reason, which the projector deliberately skips | `alirocumab` ×2, `iv-iron-hf` held-but-undelivered | all three rendered fine |
| recognised a refusal only by the `Refused:` marker | `apixaban-vte-prophylaxis` REFUSAL LOST | its refusal had started rendering **in full** minutes earlier |

And the interval sweep's first run reported **two** raw-vs-house defects on a 2-decimal match;
**both were false**, matching `0.74` and `0.86` from unrelated numbers a megabyte apart.

> **So: an optimism bias measured in estimates (class 74), an optimism bias measured in one
> instrument's code (class 84), and a pessimism bias measured in another's — the second
> instrument accusing our own work, three times running.**

**The honest summary is not "we flatter ourselves".** It is that *an instrument inherits the
direction of whatever its author assumed while writing it*, and the assumption is invisible to
the author precisely because it felt like the obvious way to write the check. Optimism and
pessimism are the same defect wearing different signs.

The only defence that has worked either way is the same one: **a known answer the instrument
must reproduce, established independently of the instrument.** Every one of these six was caught
by comparing output against something already established — a public-host verification, a stored
field, a count established by hand on a previous night.


## Class 87 — THE MERGE GUARD IS NOT DEEP, AND THE APPLIER DID NOT CATCH IT AGAIN

`atomic_write.merge_not_overwrite` exists because `obj["risk_of_bias"] = {...}` deleted five
leaves on `bococizumab-lipid-review`. It preserves any key the **new** value does not carry.

**It does not look inside a key that IS carried.** Writing two new outcomes into
`risk_of_bias.by_outcome` on `sglt2-hf` displaced `cvdeath_or_whf_first` and its **four
result-level assessments** — the guard saw `by_outcome` present in both and kept nothing.

> **That is the bococizumab defect one level down**, committed by the author who had spent the
> night writing about it, in the applier that closed the last open topic.

And a second loss the same write caused, which no key-level guard could ever see: the applier
wrote a **generic house `ceiling`** over this object's own, which carried
`no_result_can_reach_LOW`, `what_would_change_it`, and an explicit statement of why the ceiling
is stated rather than left implicit — **all richer than what replaced them**. Four sibling keys
were recoverable from `superseded_state`; the ceiling was not, because the replacement carried
that key too.

**An applier that writes a house-standard block over a topic's own better one is a net deletion
even where every field name survives.**

Caught by the **leaf-by-leaf comparison against HEAD before commit** — the same check that
caught it the first time, and again *not* by the applier, *not* by the merge guard, and *not*
by the pre-commit hook. 130 changed leaves on two files; 126 of them were this.

*The remedy is not another guard at the same level.* A deep merge would need to know which
subtrees are additive and which are replacements, and that is a per-key judgement. What holds
is the routine: **compare leaves against HEAD before every commit that touches an SSOT
object**, which is now the third time it has been the only thing standing between an applier
and a silent deletion.


## Class 88 — A PAGE WRITTEN TO A GUESSED PATH IS INVISIBLE TO EVERY CHECK KEYED ON THE REAL ONE

`alirocumab-lipid` is delivered as **`ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html`**. I built
**`ALIROCUMAB_LIPID_REVIEW.html`** — a filename I inferred from the topic name rather than read
from `PAGE_MAP.json`. The file did not exist; **my commit created it.**

Three consequences, and the third is the one that matters:

1. The re-stored model output went to a page no reader reaches.
2. The delivered page kept the old DerSimonian-Laird quotation.
3. **A page appeared where a reader expected nothing** — the tombstone problem, committed on the
   night the rule was written down, by the author who holds a memory note titled
   *one-object-two-delivered-pages*.

**It was caught only by accident of shape.** The delivery audit reported `alirocumab` HELD-ONLY
on limb 4, and the probe was demonstrably present in the file I had just built. The file was
right; it was **the wrong file**. Nothing else would have found it: the build succeeded, the
manuscript guard passed, the commit passed every hook, and the page was byte-correct.

> **A name is not an address, and a guessed address fails silently in both directions** — the
> real page keeps its stale content, and the guessed page becomes content nobody asked for.

Audited every HTML file in the last 25 commits against `PAGE_MAP`: **25 files, one stray, this
one.** Removed; the mapped page rebuilt; the host returns 404 for the stray.


## Class 89 — WE SCORED D1 LOW ON EVIDENCE THE TOOL NAMES AS "NO INFORMATION"

Not a tie between two assessors. **The RoB 2 guidance names our exact situation and prescribes
the answer**, so this is a rule the project already holds, applied.

From *Revised Cochrane risk-of-bias tool for randomized trials (RoB 2)*, 2019 guidance, Box 4,
signalling question **1.1 Was the allocation sequence random?** —

> **"Answer 'No information' if the only information about randomization methods is a statement
> that the study is randomized."**

That is precisely what a ClinicalTrials.gov design module gives: `allocation: RANDOMIZED`, and
nothing about the method. And section **4.4**:

> **"A judgement of low risk of bias requires that the trial has an adequate method of
> concealing the allocation sequence from those involved in enrolling participants, and there
> are no concerns about generation of the allocation sequence."**

We read no concealment method on any trial, and every D1 entry we wrote **says so in its own
words** before scoring LOW. Handbook 8.3 states the domain's three components — sequence random,
sequence concealed, baseline imbalance — and a registry allocation field speaks to none of them.

**IT REFINES BOTH ASSESSORS.** Assessor 1 said LOW: wrong. Assessor 2 said NO_INFORMATION at the
*domain* level; the tool's algorithm maps NI on 1.1 and 1.2 with no baseline concern to **Some
concerns**, not to a no-information verdict. The house convention writes NO_INFORMATION for an
unjudgeable domain and caps the overall at SOME_CONCERNS, which lands in the same place.

### The consequence, measured before the decision

| | |
|---|---|
| D1 judgements in the corpus | 84 |
| scored **LOW** on a bare `allocation: RANDOMIZED` | **51**, across 15 topics |
| of those 51, currently sitting under an **overall of LOW** | **0** |
| of those 51, already carrying another NO_INFORMATION domain | **51 of 51** |
| **overall ratings that would change** | **0** |
| **GRADE ratings that would move a level** | **0** |

Every one of the 51 already sits under SOME_CONCERNS (48) or HIGH (3), because the house ceiling
had already capped them on D2/D3. **The correction is a domain-level accuracy fix with no
downstream consequence** — it changes what a reader is told about one domain on 51 results, and
changes no rating, no certainty and no estimate.


## Class 86, fifth instance — A SWEEP WHOSE TWELVE HITS WERE ALL THE OBJECTS DOING THEIR JOB

`sweep_stored_scalar_contradicts_own_prose` was written because `incretin-hfpef` stored `k: 1`
while its own sentences said `k=2` twice. Over **63 checkable blocks it flagged 12. All twelve
were read. NONE is a defect.**

| what the prose was actually doing | n |
|---|---|
| naming a **superseded** value beside the current one (`arni`, `sglt2-hf` I²) | 2 |
| naming a **sibling outcome's** k (`sglt2-hf`, `fcm-hf`, `hiv-prep-injectable`) | 3 |
| stating *"k = 1 for the question the title asks"* as a **scope finding** | 5 |
| **already documenting the contradiction itself** — *"Three different counts on one page, and nothing reconciles them"* (`colchicine`, `intensive-bp`) | 2 |

The last two are the sharpest: the instrument flagged as a defect the objects' own record of a
defect they had found first.

**The shape is real and rare — one confirmed instance in the corpus, already fixed.** The sweep
cannot distinguish *contradicting itself* from *documenting a contradiction*, and in this corpus
the second is twelve times more common. Kept as a reader, never a gate, with its false-positive
rate stated in its own output: **12 of 12.**

*Fifth instance tonight of an instrument running in the accusing direction. The tally now stands
at optimism bias in estimates (74), optimism bias in one instrument (84), and pessimism bias in
five separate checks — every one of which accused our own work and was wrong.*


## Class 90 — THE PROJECTOR READS A FIXED LIST OF KEYS, SO EVERY NEW FIELD IS SILENT BY DEFAULT

Class 83 has now recurred **five times**, and the fifth landed on the one artefact Mahmood's
specification names by name: three topics carried a blind cross-family second risk-of-bias
assessment, with its verbatim reply and its disagreement rate, **and none of it rendered.**

> **This is not a bug that was fixed four times. It is a design whose default is silence.**

`paper_projector` renders by asking the object for a hardcoded list of key names. A field the
object holds and the list does not name is invisible — and **the only person who knows the field
exists is the author who just wrote it**, who is also the only person who would think to check.
Every instance has the same shape and a different key:

| what was written | what read it | what a reader got |
|---|---|---|
| `title`, `agreement` on a comparison record | nothing | a PMID and four blank cells |
| `model_output.verbatim` | nothing | *"no analysis output is stored on this object"* |
| `POOL_FINDINGS_<stamp>` | the paper only | the qualification a megabyte from its estimate |
| a refused `risk_of_bias` with `state`/`why` | nothing | *"Risk of bias was assessed with RoB 2"*, asserting an assessment that was refused |
| `SECOND_ASSESSOR_<stamp>` | nothing | no sign a second assessor existed or disagreed |

*Whether the projector should render declared keys rather than a hardcoded list is an
architecture question and it is NOT started here.* Noted for daylight. What is fixed is the
fifth instance.


## Class 91 — A BLIND ASSESSMENT GIVEN FEWER FACTS IS NOT A COMPARABLE ASSESSMENT

**This is the methodological result of the whole second-assessor exercise and it leads.**

An inter-rater disagreement rate between two models is **conditional on the facts both were
shown**, and if the second assessor sees fewer facts than the first used, the rate is not a
measurement of two assessors — **it is a measurement of one prompt.**

**Established by test, not by argument.** The prompt builder emitted 9 registry fields. The
first assessor's stated reason on `ceftaroline` D5 is *"two register MITTE and one registers
CE"* — an analysis-population split held in `registered_analysis_population`, which was **not on
the list**. Widening the list from 9 fields to 14 and re-running three topics:

| topic | 9 fields | 14 fields | |
|---|---|---|---|
| `gepotidacin` | 4 of 12 | **2 of 12** | its *entire* D5 divergence was the prompt |
| `ceftaroline` | 12 of 18 | 12 of 18 | unmoved — the disagreement is real |
| `tigecycline` | 11 of 18 | 11 of 18 | unmoved — real |

**So the allow-list is stated wherever the rate is quoted, the way a denominator is stated.**
Every published claim about inter-rater agreement between models has this problem whether or not
its authors noticed it.

*Fields emitted: trial, cohort, registered enrolment, registered masking, registered sites,
registered comparator, number of registered arms, number of registered primary outcomes,
registered primary outcome, registered analysis population, the rank the pooled result holds,
the result being assessed, participants pooled, enrolment minus participants pooled.*

### 91a. And twelve topics could not be prompted at all until the registrations were re-read

Their risk-of-bias entries recorded a judgement and a reason and **not the registry fields the
judgement was made from**. Building a thinner prompt would have measured the gaps in our own
records. `scripts/backfill_registry_facts_2026_08_21.py` re-read 24 registrations and wrote
**35 entries across 10 topics — additions only, zero leaves changed, no judgement revisited.**
Three entries on `arni-hfref` carry no `nct` and were **refused by name** rather than filled
from a result id.


## Class 92 — THE CLEAN PROFILE AT n=3 DID NOT SURVIVE n=22, AND WE NEARLY REPORTED IT

**Record this with the prediction score, not in a domain table.** It is the best argument in
this project's record for not reporting from small samples, and it was ours.

**At n = 3** the disagreements sat almost entirely on D1 while D2–D5 agreed nearly everywhere.
The claim that suggested itself: *two independent model families given the same registration
facts converge on four of five RoB 2 domains and diverge on the one where the guidance is
explicit.* Tidy, publishable, and false.

**At n = 22 topics and 432 judgement comparisons:**

| domain | disagree | |
|---|---|---|
| **D1** randomisation | 59 of 66 | **89.4%** |
| D2 deviations | 17 of 66 | 25.8% |
| D3 missing data | 24 of 66 | 36.4% |
| D4 measurement | 25 of 66 | 37.9% |
| **D5** selection | 42 of 66 | **63.6%** |
| OVERALL | 49 of 66 | 74.2% |
| **total** | **216 of 396** | **54.5%** |

*(plus the three topics reconciled inline earlier: 9 of 36, 25.0%)*

**There is no clean profile.** Two model families given identical registration facts disagree on
more than half of all judgements, on every domain, most on D1 and D5 and least on D2. That is
weaker, less quotable and more honest than the version that nearly went out.

### 92a. The n=3 result was itself partly an instrument artefact — the third of three

The first three topics were assessed against a **9-field** prompt, and their apparent D2–D5
agreement partly reflects the second assessor having less to disagree with. Three separate
measurements in this exercise turned out to be of the instrument rather than of the assessors:

1. the **too-narrow fact allow-list** (9 fields, above),
2. the **n = 3 profile** itself,
3. **domain-key matching** — this corpus spells the same domain several ways
   (`D1_randomisation` on 28 results, `D1_randomisation_process` on 5; three spellings of D5).
   Exact-name matching compared **only D3** on 28 of 33 results, and printed *"D3 disagrees
   60%"* while D1, D2, D4 and D5 were never compared at all. Fixed by matching the domain
   prefix, which is the part that is actually stable.


## Class 91b — THE SECOND ASSESSOR'S DISAGREEMENT PROFILE, AND WHY THE CLEAN VERSION IS FALSE

Twelve topics now carry a blind cross-family second RoB 2 assessment. **The result after three
topics looked publishable and it did not survive the other nine.**

**After 3 topics** — disagreements concentrated on D1, with D2–D5 agreeing almost everywhere.
The tempting claim: *two independent model families given the same registration facts converge
on four of five domains and diverge on the one where the guidance is explicit.*

**After 12 topics, 204 judgement comparisons, that claim is false:**

| domain | disagree | |
|---|---|---|
| **D1** randomisation | **34 of 34** | **100%** |
| D2 deviations | 0 of 34 | **0%** |
| D3 missing data | 0 of 34 | **0%** |
| D4 measurement | 7 of 34 | 21% |
| D5 selection | 16 of 34 | 47% |
| OVERALL | 20 of 34 | 59% |

D1 and D2/D3 are the clean results — **total disagreement and total agreement respectively.**
D4 and D5 are neither, and the honest statement is that **two model families given identical
registration facts disagree about how to score measurement and selection roughly half the
time.** That is a weaker and more interesting finding than the one that nearly got reported.

### 91a. And part of the first measurement was the prompt, not the assessors

Reconciling the replies showed several D4/D5 disagreements were **not judgement differences**:
the first assessment's stated reason rested on facts the prompt did not carry. On `ceftaroline`
the D5 reason is *"two register MITTE and one registers CE"* — an analysis-population split held
in `registered_analysis_population`, which was **not on the prompt's allow-list**. The second
assessor could not have known.

**A blind assessment given fewer facts is not a comparable assessment, and a disagreement rate
computed over one is measuring the prompt.** The allow-list went from 9 registry fields to 14
and one topic was re-run: `gepotidacin` fell from 4 of 12 to **2 of 12** — its entire D5
disagreement was the prompt. `ceftaroline` and `tigecycline` did not move, so theirs are real.

### 91b. The mirror bias, guarded explicitly

Three topics went against the first assessor on D1 and the guidance backed the second. The
pressure from there is to defer on everything — **which would make the second assessor a
reviewer rather than an independent one and reproduce the inheritance problem with the sign
flipped.**

Where the first assessment is believed right, that is written down with its reason and both
stand. `gepotidacin` D5 is the case: two registered primary outcomes both named *"Therapeutic
Response"*, one pooled with no recorded reason for the choice. That is a textbook selection
concern and the first assessor keeps it.

And in the other direction — **`tigecycline` D4 is an error of the first assessor's**, found by
the same reconciliation: it scored HIGH on `NCT00081744` with a reason about `NCT00136201` being
open-label. RoB 2 assesses *this result in this trial*; another trial's masking is not a bias in
this one. Recorded as a disagreement the first assessor loses.


## Class 93 — THE TWO ASSESSORS DISAGREE ABOUT WHERE THE EVIDENCE RUNS OUT, NOT ABOUT WHAT IT SHOWS

The 54.5% rate hid a completely systematic structure. Across 22 topics, **every disagreement
runs one way within a domain, and the direction flips between two groups of domains:**

| domain | direction of disagreement | n |
|---|---|---|
| **D1, D2, D3** | assessor 1 judged; **assessor 2 said NO_INFORMATION — 100 of 100** | 100 |
| **D4, D5** | assessor 1 found a concern; **assessor 2 said LOW — 51 of 67** | 67 |

**Assessor 2 declines to judge the three domains a registry cannot address and scores LOW on
the two it can. Assessor 1 does the exact opposite** — it judges the invisible ones and finds
concerns in the visible ones.

> **Neither is being careless. Each defaults in its own direction on the domains where it is
> not looking** — which is class 86 appearing *between* two assessors rather than inside one
> instrument.

And the adjudication goes both ways, which is what makes it an adjudication:

- **D1 — assessor 2 is right, and it is settled by guidance rather than by preference.** RoB 2
  Box 4 q1.1: *"Answer 'No information' if the only information about randomization methods is a
  statement that the study is randomized."* 51 judgements, one command, held for Mahmood.
- **D5 — assessor 1 is right 3 times and WRONG 29 times.**

### 93a. The D5 adjudication, on a registry fact both assessors cite

The discriminator is **the registered primary-outcome count** — a field on the registration, not
a matter of judgement. 42 disagreements, **32 resolved**:

| | n | |
|---|---|---|
| **two or more** registered primaries → a set exists to select from | **3** | assessor 1 right |
| **one** registered primary → no set to select from, LOW is correct | **29** | **assessor 1 wrong** |
| count not on the entry | 10 | unresolved; both judgements stand and both render |

**Assessor 1 was over-cautious on D5 exactly as it was over-confident on D1.** Declining to
judge a domain the registry *does* answer is the mirror of scoring LOW on one it does not — the
same error with the sign reversed, by the same assessor, in the same corpus.

### 93b. And the discriminator could not be applied until assessor 2 was asked for reasons

**A protocol flaw of mine.** The blind prompt asked for verdicts only, so *"which assessor's
reason cites a registry fact"* was answerable for one side. A second blind round asked assessor 2
for the single fact each D5 judgement rested on, and its answers settle the 3 in assessor 1's
favour **out of its own mouth**:

> `NCT04020341 BASIS=The assessed therapeutic response was **one of two registered primary
> outcomes**.` — and it scored that **LOW**.

Naming the selection situation and then scoring LOW is internally inconsistent, and it is a
stronger resolution than any assertion of mine could be. *An assessor asked only for verdicts
cannot be adjudicated against; ask for the basis in the same round.*


## Class 94 — TWO SYSTEMATIC PRIORS MEETING LOOK EXACTLY LIKE UNRELIABILITY

**Generalises well past risk of bias.** Give two assessors the same facts and let each default in
its own direction on the questions where it has no evidence, and you get a disagreement rate
that reads as noise and is nothing of the kind: **both are perfectly consistent, and opposed.**

| domains a registry **cannot** answer | domains a registry **can** answer |
|---|---|
| D1, D2, D3 | D4, D5 |
| assessor 1 judged anyway | assessor 1 found specific concerns |
| assessor 2 said NO_INFORMATION — **100 of 100** | assessor 2 said LOW — **51 of 67** |

> **The rate is not the finding. The direction within each domain is.**

#### Corrected 2026-08-21 — the `100 of 100` was measured on one prompt build

Acting on this class is what falsified part of it. Moving D1 from LOW to NO_INFORMATION should
have taken every D1 disagreement to zero if assessor 2 always said NO_INFORMATION; on
`agyw-hiv-prep-review` and `cab-prep-hiv-review` it did not, because **assessor 2 said
SOME_CONCERNS there.** Counted across all 23 topics now stored:

| | assessor 2 said NO_INFORMATION |
|---|---|
| D1 | **77 of 81** — four exceptions, all SOME_CONCERNS |
| D2 | 81 of 81 |
| D3 | 81 of 81 |
| **D1+D2+D3** | **239 of 243**, not 100% |

**All four exceptions sit in the EARLIER prompt build** — the one whose reply ids are bare NCTs,
used on three topics before `__<outcome>` was appended. Under that build: **4 of 6.** Under the
later build: **0 of 75.** The `100 of 100` was true of the topics it was measured on and was
generalised past them.

*The mechanism stands; its universality does not — and the thing that varies with it is the
**prompt**, which is the finding this run has now reached from three directions.* And the third
direction is that a domain's disagreements can run **both ways at once**: after the move,
`sglt2-hf` has 4 where this review says SOME_CONCERNS and assessor 2 says NO_INFORMATION, while
`agyw-hiv-prep-review` has 2 the other way round. Both are the same vocabulary gap — RoB 2's
algorithm answers SOME CONCERNS where this project writes NO_INFORMATION — seen from each side.

**An agreement rate would have concealed this entirely.** 45% agreement reads as poor
inter-rater reliability and invites a kappa and a shrug. What is actually happening is that each
assessor is applying a stable rule about what to do with absent evidence, and the two rules
point opposite ways. *That is the sharpest instance yet of "agreement authenticates nothing" —
here, the agreement statistic would have actively hidden the mechanism.*

### 94a. What it implies for the specification

Mahmood asked for two AIs. **This shows two AIs do not converge on truth. They converge on
nothing** — and the whole value is in the adjudication, which needs a third thing neither
assessor supplies:

| domain | what settled it | outcome |
|---|---|---|
| D1 | **the RoB 2 guidance text** | assessor 2, 51 judgements |
| D5 | **the registered primary-outcome count** | assessor 2 ×29, assessor 1 ×3 |
| 10 D5 cases | *no field to appeal to* | **unresolved; both render** |

**THE OPERATING RULE: a disagreement is resolvable exactly when a field can settle it.** Two
assessors is not a stamp; it is a disagreement to be adjudicated against a registry fact or a
guidance sentence, and where neither exists the honest output is both judgements and the split.
That rule carries to every specialty after this one.

### 94b. And the one topic that disagreed on everything is the purest case of the prompt problem

`arni-hfref` disagrees **18 of 18 — 100%, the highest on the corpus** — and it is not a measure
of the assessors. It is the authored docmodel topic: its risk-of-bias entries were written as
prose judgements with bare `D1`..`D5` keys and **no registry fields at all**, backfilled only
today, *after* those judgements were made. Assessor 1 judged from sources this comparison cannot
see; assessor 2 judged from the registry alone. **The fact-allow-list problem in its purest
form, on the one topic where the first assessment did not come from the registry.**

### 94c. Six lookups, one shape

Counted across this run, six separate lookups under-counted their own population by reading one
spelling where the corpus uses several:

| # | what it read | what it missed |
|---|---|---|
| 1 | number words to *ten* | "twelve trials", "fifteen studies" |
| 2 | a 9-field fact allow-list | `registered_analysis_population` |
| 3 | one fixed D1 phrase | 21 entries saying it in other words |
| 4 | exact domain key names | `D1_randomisation` vs `D1_randomisation_process` |
| 5 | `nct` on the entry only | `inputs.trials` and `per_trial` held the mapping |
| 6 | a `D1_` **prefix** | `arni-hfref` keys them bare `D1` |

*Every one of the six under-counted. None over-counted.* A lookup written against the spelling
in front of you inherits that spelling as an assumption — class 86's mechanism, in string
matching rather than in judgement.


## Class 95 — THE P47 GAP, MEASURED ON ONE TOPIC, AND BOTH PREDICTIONS WERE WRONG

P47 has stood at **0 of 141** all run, and the tier-3 estimate has **moved up twice and never
down** — currently "at least 154 topics" with no per-topic cost. `scripts/measure_p47_gap_iv_iron_2026_08_21.py`
enumerates the claims a reader-facing Introduction, Discussion and Conclusions must assert, per
**PRISMA 2020 items 4, 5, 23a, 23b, 23c and 23d**, and puts a field path beside each.

**Topic: `iv-iron-hf`** — the richest object in the corpus that carries **no authored prose**
(3,719 leaves, six outcomes, holding `published_comparison`, `grade`, `risk_of_bias`,
`prisma_flow`, `search`, `screening`, `protocol`, `registration_identity`). `arni-hfref` is
richer at 12,145 leaves and was **rejected**: it is the one object in 155 holding
`manuscript.discussion`, so measuring it would count argument somebody already wrote as argument
the object can derive.

### The three numbers, over 37 claims

| | n | |
|---|---|---|
| **DERIVABLE** — a field backs it as it stands | **22** | **59.5%** |
| **FETCHABLE** — no field, but a named reachable source would | **3** | **8.1%** |
| **ARGUMENT** — irreducibly a person's | **12** | **32.4%** |

| section | claims | derivable | argument |
|---|---|---|---|
| Introduction | 10 | 6 — 60% | 2 — 20% |
| Discussion | 22 | **15 — 68%** | 6 — 27% |
| **Conclusions** | 5 | 1 — 20% | **4 — 80%** |

### Both predictions were wrong, in opposite directions

| | Introduction | Discussion |
|---|---|---|
| Mahmood | *largely derivable* | *not derivable* |
| this author | ~40% derivable | ~50% derivable |
| **measured** | **60%** | **68%** |

**Mahmood was right about the Introduction and wrong about the Discussion. I was wrong about
both, and wrong low on both.** The Discussion is the *most* derivable section, not the least —
because PRISMA 23b and 23c are almost entirely bookkeeping this corpus already holds: risk of
bias per result and what drove it, whether publication bias was assessable, the search, the
screening counts, the registration, which limbs the review refuses, and now the second
assessor's disagreement rate.

**The argument is concentrated, not spread.** It sits almost entirely in the Conclusions (80%)
and in four Discussion claims — *why* results differ, whether heterogeneity is clinically
important, whether the effect is clinically meaningful, whether the evidence base is adequate.
Those are the sentences that select and weight what the fields already say.

> **The gap is not "write a Discussion". It is "write four sentences of interpretation and a
> Conclusions paragraph", on top of a section that is two-thirds projectable today.**

*This is one topic and it is deliberately a floor, not a mean. A topic holding no
`published_comparison`, no second assessor and no PRISMA flow would derive far less.*

### 95a. And the measuring instrument was instances eight, nine and ten

Three claims were first reported unbacked and **all three were the resolver, not the object**: a
`" + "` compound path thrown away whole, a `KEY_*` wildcard on a stamped key name treated as a
literal, and a leading dot. A fourth needed a wildcard to span two levels rather than one.

**Ten lookups this run under-counted their own population. None over-counted.** The three
numbers above moved from 48.6% derivable to 59.5% purely by fixing the thing doing the counting.


## Class 96 — I CHOSE THE RICHEST OBJECT AND CALLED IT A FLOOR. IT WAS THE CEILING.

`iv-iron-hf` was picked as *"the richest object that carries no authored prose, so the answer is
a floor rather than a typical case"*. **Richest means best-derived. Choosing an extreme bounds
the side it is extreme on, and I named the wrong side.**

Across all 28 topics carrying a pooled outcome:

| | claims of 37 | |
|---|---|---|
| **worst** — `attr-pn-review` | **12** | **32.4%** |
| median | 17 | 45.9% |
| mean | 17.1 | 46.2% |
| **best** — `iv-iron-hf` | **22** | **59.5%** |
| spread | 10 claims | **27.0 points** |

**0 of 28 topics derive more than the "floor". 27 derive the same or less.** Mahmood's
expectation — *the floor holds and the mean is higher* — was reasonable against my framing and
wrong because the framing was wrong.

**Tier 3 is not one job.** Six topics derive 12 of 37 where one derives 22, and a per-topic cost
quoted from the best case understates the worst by 27 points.

### 96a. But the gap is bookkeeping, not research

Every claim that fails most often is **FETCHABLE, not ARGUMENT** — a field the schema can hold
and the object does not:

| claim | missing on |
|---|---|
| which limbs the review refuses (`build_stamp.refusing`) | **20 of 28** |
| the search, with its date and databases | 19 of 28 |
| whether the review was prospectively registered | 19 of 28 |
| that two assessors disagreed, and where | 12 of 28 |
| which risk-of-bias domains drove the judgements | 9 of 28 |

> **Closing the fetchable gap would move the worst topic from 32.4% to near 59.5% without
> writing one sentence of argument.**

And `ARGUMENT` is **a constant 12 of 37 on every topic** — whether an effect is clinically
meaningful is not something an object can come to hold. *The irreducible writing is identical
across the corpus; only the bookkeeping varies.*


## Class 86, RESTATED — REPLACING EVERY ONE-DIRECTIONAL VERSION IN THIS FILE

Five measured instances, and **the fifth runs the other way**, which settles the shape:

| instance | direction | corrected by |
|---|---|---|
| class 74 — our estimates of our own remaining work | **optimistic** | measuring |
| class 84 — `audit_our_k_against_theirs` and its repair | **optimistic** | a known answer |
| class 86 — five checks that accused our own work | **pessimistic** | reading the flagged case |
| class 92 — the n=3 disagreement profile | **optimistic** (tidy, quotable) | n=22 |
| **class 95 — the P47 derivability estimate** | **PESSIMISTIC** — both predictors guessed low | measuring |

> **It is not "we flatter ourselves". It is not "our instruments accuse us". An unmeasured
> estimate is unreliable in whichever direction its estimator's assumption leaned, and the only
> remedy that has worked all night is measuring.**

Class 95 is the first estimate whose correction moved the headline **up** — 48.6% to 59.5% by
fixing the resolver — and then widening to the corpus moved the *planning* number **down** to
32.4%. Same measurement, corrections in both directions.

### The resolver family has a systematic direction, and it is toward absence

**Ten lookups this run under-counted their own population. None over-counted.** Not chance:
**a path that fails to resolve reads as "the object does not hold this"**, indistinguishable
from the object genuinely not holding it. Same shape as a refusal misattributing its own cause —
class 73 — and it cost a wrong conclusion six or seven times tonight: 21 D1 entries called
"other evidence"; three `arni` registrations called unidentifiable; *"D3 disagrees 60%"* when
four domains were never compared; four P47 claims called unbacked while the fields sat there.

**That is why fixing the resolver rather than the paths was the right call.** Rewording a path
hides a resolver that will fail the same way on the next one, and the failure is silent and
always points at the data.


## OPEN — carried, not fixed

### O4. The delivered malaria verdict rests on a premise its own registrations contradict

**VERIFIED DIRECTLY FROM ClinicalTrials.gov ON 2026-08-21, second reading:**

- `NCT03896724` primary 1 — *"**The protective efficacy** (number of cases) **against clinical
  malaria** of R21 adjuvanted with Matrix-M in 5-17 month old children…"*
- `NCT04704830` primary 1 — *"Efficacy: To assess **the protective efficacy** of R21/Matrix-M
  **against clinical malaria** caused by Plasmodium falciparum, in 5-36 month old children…"*

> **THE ONE SENTENCE TO ACT ON.** `malaria-vaccine` is delivered to readers declaring this
> topic NOT POOLABLE because *"no two share a registered primary outcome family"* — and two of
> the three trials it read are both R21 trials whose registered primaries **both name
> protective efficacy against clinical malaria**. That ground is false as written.

**MY VIEW, STATED RATHER THAN LEFT TO THE FILES.** The singular object's *verdict* is defensible
and its *ground* is not, and the distinction is the whole decision:

- It asked **can these three be pooled together** — across RTS,S and R21, across an efficacy
  measure and a rate. The honest answer to that is no, and `malaria-vaccines` **agrees**: it
  pools R21 with R21 and RTS,S with RTS,S and never across the two.
- It did **not** ask whether the within-vaccine pools hold, so **its verdict does not reach
  them.** It also read **3 of the 7** registrations the plural object carries.
- The true objection is *"no two share a VACCINE"* — a narrower claim that leaves both of the
  plural object's pools untouched.

**I believe `malaria-vaccines` is the correct object to deliver**, and that the singular's
NOT POOLABLE finding should survive only as a statement about pooling ACROSS vaccines, which is
something neither object does. *This is a publication decision and nothing has been mapped.*

The plural object now holds all four limbs — risk of bias on 12 results across 9 outcomes,
GRADE on both pooled outcomes, a comparison over 28 records, and the R output for both pools.

### O4a. A READING FAILURE — the only one tonight with no mechanical remedy

Not a newly found duplicate. `evidence/2026-08-19-batch1/corpus_duplication.json` **at commit
`9f9121193`** — *"merge(9 clusters): 10 topics RETIRED"* — already contained:

```
{"subset": "malaria-vaccine", "superset": "malaria-vaccines",
 "n_shared": 3, "n_superset": 7}
```

It was listed, and no cluster was opened for it. **Third duplicate pair surviving a merge round
that was closed on the understanding none remained** — after `attr-pn`/`attr-cm` and the
apixaban split. The instrument was right and nobody read its output to the end.

*Cluster to open:* `malaria-vaccine` (3 trials, verdict-only, **mapped**) and `malaria-vaccines`
(7 trials, 9 outcome blocks, **unmapped**). Same subject, opposite conclusions, and the reader
gets the one built on the false premise.

**AND NO CHECK IS PROPOSED HERE, BECAUSE NONE WOULD HAVE HELPED.** This is the worst of the
three duplicate findings and it is worth being precise about why:

- It is **not a detection failure.** The instrument ran, and it was right.
- It is **not a tooling failure.** Its output named the pair, with the shared count and the
  superset count, in the correct field of the correct file.
- The file was **committed in the same commit that closed the merge round.**

**It is a reading failure.** Every other class recorded tonight ends in a check — a gate, a
control, a known-answer floor, a probe. *This one ends in "somebody must read the output to the
end."* Proposing a detector here would be worse than proposing nothing, because it would imply
the miss was mechanical and let the actual cause stand: an instrument's output was generated,
committed, and not read past the part that confirmed the work was done.

The two other survivors — `attr-pn`/`attr-cm` and the apixaban split — were at least arguable
on their evidence. This one was written down.

### O4b. The original framing, kept

| | `malaria-vaccine` (singular) | `malaria-vaccines` (plural) |
|---|---|---|
| built | **2026-08-18** | 2026-08-08 |
| in `PAGE_MAP` | **yes** — `MALARIA_VACCINE_REVIEW.html` | **no** — reaches nobody |
| registrations read | **3** | **7**, across 8 randomised cohorts |
| verdict | **NOT POOLABLE**, MECIR C62 | nine outcome blocks, two pooled estimates |

The singular object's stated ground is: *"3 TRIALS, AND NO TWO SHARE A REGISTERED PRIMARY
OUTCOME FAMILY."* But two of the three it read are **both R21 trials**, and on its own
recorded `registered_primaries` both register *protective efficacy against clinical malaria*:

- `NCT03896724` — "The protective efficacy (number of cases) against clinical malaria of R21
  adjuvanted with Matrix-M…"
- `NCT04704830` — "Efficacy: To assess the protective efficacy of R21/Matrix-M against
  clinical malaria…"

It compared **across vaccines**, which is a comparison the plural object deliberately never
makes — that object pools R21 with R21 and RTS,S with RTS,S and never across the two.

**What has been done:** the plural object now holds all four P46 limbs — risk of bias on 12
results across 9 outcomes, GRADE on both pooled outcomes, a published comparison over 28
records, and the R output for both pools. **It has NOT been mapped**, because publishing a
pooled estimate would contradict a later recorded decision that this topic is not poolable,
and *which of the two objects is right is a content decision*.

**What is needed:** Mahmood's decision on whether the NOT POOLABLE verdict survives being
re-read against seven registrations instead of three, and against a within-vaccine rather
than across-vaccine question.

### O0a. `NCT00081744` — a trial contributing to two published pools with no registered primary outcome

**On `tigecycline-ciai` and on `tigecycline-infection`, by name.**

The registration carries **no primary outcome at all**. Not a mismatch between what was
registered and what was extracted — **there is nothing to check the extracted result
against.** The estimand for that row cannot be established at any level.

Both topics publish a pooled estimate to which it contributes: `tigecycline-ciai`'s
`cure_toc_me` is RR 0.9351 (0.8885–0.9842) on k=3.

**Stated as UNVERIFIABLE, not as wrong.** If a reader asks what that row's result is checked
against, the honest answer is nothing. Two other registrations are in the same state —
`NCT00034645` and `NCT00044486` on `posaconazole-fungal` — making **3 distinct registrations
across 4 topic-rows** of 402 read.

### O0. `cangrelor-pci-review` — a withdrawal note that overstates its own defect

**The honesty-penalty class, applied by us to ourselves.**

The withdrawn card published **OR 0.81 (0.71–0.91)**. The withdrawal note tells a reader the
page *"reported a significant benefit where the trials' own primary outcome does not support
it."*

**Steg et al., Lancet 2013 (PMID 24011551) — a prespecified pooled analysis of patient-level
data from all three CHAMPION trials, 24,910 patients — reports the primary composite at OR
0.81 (0.71–0.91).** The same value and the same interval, independently.

So the withdrawn headline appears to have been **right**. What was wrong was its
**provenance**: the object establishes that the card's stored numerators were all-cause
mortality counts set against the primary composite's denominators, on all three trials. **A
correct number standing on arithmetic that cannot produce it is a provenance failure, not an
accuracy one** — and the note as written says the benefit is unsupported when the best
available evidence supports it.

**Disclosed, not resolved.** The agreement now renders where a reader meets the withdrawal,
via `POOL_FINDINGS_` on the declared `primary` outcome: same value, same interval,
independently reported, provenance unresolved. **Restating the withdrawal is a content
decision about a published number and belongs to Mahmood.** Disclosing the agreement is not.

*Two errors of mine on the way to this, both recorded in class 74's second half and both in
a new direction: they accused our own corpus of carelessness it had not committed.*

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
