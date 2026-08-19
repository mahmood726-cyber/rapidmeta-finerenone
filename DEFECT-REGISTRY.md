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

---

## PARTIAL — a detector exists, and what it misses is named

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

### E1. Substring is not identity
Matching a topic drug by substring conflates distinct entities. **Not lintable**: deciding
whether a match is the same entity is a semantic judgement, which is exactly the property that
makes §1–§3 lintable and this one not. Handled by explicit synonym sets in
`ssot/topic_identity.py` with the ambiguity declared, and by regression guards pinning the
negative cases (apixaban-vs-rivaroxaban, both-arms background).
**Residual risk: a new topic whose drug name is a substring of an unrelated one, with no guard
written.** Mitigation is a convention, not a mechanism.

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
The general form of §8c. A `prop(REFUSING, "...")` or `prop(HELD, "...")` with no branch on
object state is a verdict that was **decided when the code was written**, not derived from what
is on the page.

**Mechanically detectable and not built**: walk the AST for `prop(...)` calls whose verdict
argument is a module-level constant and whose enclosing block contains no reference to `obj`.
Listed as an exposure rather than as future work, per this file's own standard.

**This entry exists because two new classes (8b, 8c) were found within the hour after this file
was written, while doing ordinary build work.** The registry is a snapshot of what has been
noticed, not a proof of what remains — and the honest form of that is to keep adding to it
rather than to present it as complete.

---

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
