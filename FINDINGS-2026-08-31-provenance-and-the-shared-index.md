# Findings, 2026-08-30/31 — provenance typing, and what a shared worktree does to diagnosis

Written as a file rather than left in a commit message, because **a commit message is not a
header when it is the only record of why something is the way it is** — and tonight four
commits were in flight at once in one worktree, three of them without a pathspec, so which
message any given change lands under is not something a reader can rely on.

---

## 1. The two conversion failures, which are the deliverable

`ssot/claims.py` types a field's ORIGIN (`__derived_from`) and its CLAIM KIND (`__claim`),
and enforces a required shape per kind. Two writers were converted.

**`count_bases.py` — 2 validation failures, both real.** Each count basis is typed
`evidence_source`, which requires a `read_utc`. Both bases state their read date **inside
prose** — *"read 2026-08-30 via API v2"* — and neither declares it as a field.

⛔ **The date was NOT parsed out of the sentence.** Lifting it from free text would be the
module inventing a provenance field, which is the exact defect the primitive exists to
prevent. A validator error naming what the object must declare beats a green tick bought by
a regex.

**`regulatory_evidence.py` — 0 failures, and I predicted otherwise.** All 85 stored answers
already carry `retrieved_utc`; its `answer()` constructor already refused malformed
evidence. The module was disciplined before the vocabulary existed. Reported as a clean pass
rather than hunted for a failure to justify the prediction — **a module already obeying a
rule nobody had written down is evidence the rule describes something real.**

---

## 2. The regression the fixtures could not catch

`origins()` looked dotted paths up as FLAT KEYS. So `manuscript.introduction` resolved to
nothing, was treated as its own origin, and `corroborate("question",
"manuscript.introduction")` returned **TRUE** — a FALSE CORROBORATION on the single case the
module exists to catch, in the flattering direction.

⭐ **Every synthetic fixture passed.** Synthetic fixtures are FLAT, and a flat fixture cannot
exercise a path resolver. The corpus caught it; the controls never would have.

⇒ **A resolver that silently fails to resolve reports INDEPENDENCE.** Fixed with a
root-relative `resolve()` and planted as control `[1b]`.

---

## 3. The tab requirement drifted through four hands in one night

`ssot/page_format_v1.json` carries the chain, and it is the file's real justification:

1. Mahmood stated **ten** tabs.
2. Relay compressed to **eight**.
3. This lane **RATIFIED the eight** — on a relay, with no primary source. *The file created
   to stop lanes counting against remembered lists made a remembered list its first entry.*
4. This lane **un-ratified** after another lane's list showed **ten** — and reframed the
   6-of-8 vs 6-of-10 dispute correctly: **not two lanes miscounting one standard, but TWO
   DIFFERENT STANDARDS.** Neither lane fumbled the page.
5. Relay **ruled ten**.
6. Mahmood **ruled eight**. Final. `clinician`/`public` recorded as
   *considered-and-ruled-out*, which is not the same as absent.

⇒ **A declaration is only as good as the provenance of what it declares.** Four hands, two
reversals, one night, every participant acting in good faith on the best list they had.
Nobody was careless; the requirement simply had no primary record.

---

## 4. The presence-versus-authorship defect, found twice, in two fields, by two lanes

**This lane:** a naive "does `manuscript.introduction` exist" test passes on **138 of 152**
objects. Only **1** holds authored prose; 137 are a repair pass restating the generated
question. Fixing the false denial naively would have replaced a false denial on ONE page with
a false assertion on 137.

**The `rapidmeta-ssot-shell-b2` lane, independently, in a field this lane never looked at:**
`_estimand_rule` is carried by 44 objects with 16 distinct values, and the commonest — on 20
— is literally *"not recorded on the page this object was extracted from"*, scoring as a
declared judgement. Gated, its marks fell **67 → 42, a 37% over-count**, self-reported
against its own number.

⇒ **`authored_judgement` refuses both by construction**, without having been shown either: it
rejects any field whose `__derived_from` records inputs, so a value carried in from an
extraction cannot score as a judgement someone made. **A primitive that rejects a defect it
was never shown is the only kind worth adopting**, and two independent instances beat one.

---

## 5. What a shared index does to diagnosis — the night's real lesson

Four `git commit` processes ran concurrently in this worktree at 02:29. **Three had no
pathspec.** A no-pathspec commit commits *whatever the index holds*, not your work.

**The hour-long misdiagnosis (b2's, self-reported).** Its commit failed twelve times. It
attributed this to lock contention. Its own loop output said otherwise:

    attempts 1-9    pathspec did not match (a file not yet added)
    attempts 10-12  REFUSED: a file named *_gate.py cannot fail
                    -> scripts/lint_gate_can_fail.py

**It was blocked by another lane's staged file, through the shared index.**

⚠️ **And this is the most durable kind of wrong diagnosis: one that arrives with a specific,
correct-looking error string.** The gate message named a real rule about a real file.
Everything about it looked like a fact about its own commit. Nothing in it was.

**Both lanes' retry loops were manufacturing the contention they were each measuring** — a
12s loop and a 13s loop against one index, each reading the other's traffic as evidence about
the other lane. *A self-generated signal read as evidence about someone else.*

### The rules

- **In a shared worktree, always commit with an explicit pathspec.** Without one you inherit
  every other lane's gate failures as if they were your own.
- **Corollary:** `git commit -- <paths>` accepts only TRACKED paths, so new files need
  `git add` first — **and that add is the moment your files enter the shared index and become
  sweepable by anyone else's no-pathspec commit.** Chain add and commit; never add, then think.
- **Never run a retry loop against a shared index.** You become the contention you measure.

---

## 6. `index.lock` calibration — three states, and a probe that lied

Observed in one night, all three ALIVE:

| state | when | what it looked like |
|---|---|---|
| frozen + alive | 01:42 | 1.6 MB lock, mtime unchanged for 21 minutes |
| growing + alive | 02:05 | 0 → 1.6 MB in under two minutes |
| absent + alive | 02:13 | no lock at all, three commits mid-hook-chain |

⇒ **Presence, absence, mtime and size are each insufficient, in both directions.** This lane
read a growing lock as a lane camping the index, then nearly read a frozen one as debris —
and a clear-the-lock authorisation had already been issued. What stopped the deletion was
enumerating live processes **by COMMAND LINE**: `git.exe` said nothing; `git commit -F
msg8.txt -- ssot/build_tabbed.py ...` identified the owner instantly.

⚠️ **AND THE RULE NEEDS ITS SECOND HALF.** Two turns after establishing that only the process
table settles it, the b2 lane's `ps -W | grep -c` probe returned **0** for a process
`Get-CimInstance` showed alive since 02:11 — and nearly treated a live writer's lock as
debris again. **The weaker probe was wrong, not the process.**

⇒ **Use the process table, AND use a probe you have checked against a known-alive case.** We
fixed *which signal to read* and then read it with an unchecked instrument. Same shape as the
whole night: [[a diagnostic signal must be calibrated on a known-good run before it is used
to declare a failure]].

---

## 7. Two numbers that were relayed and should not have been

**Provenance debt: 116,617, not 4,188.** The shallow top-level count understated the true
recursive field count by **27.8x**; **11,833** of those sit under `results.by_outcome.*`,
which is where the estimates, counts and certainty ratings live. Nobody should quote 4,188.

**Identity ceiling: 62%, not 100%.** Of 353 distinct corpus trials, **133 have no acronym and
no organisational study id in the registry at all** — no fetch produces a name for them. The
earlier *"one join away"* framing was right about the mechanism and wrong about the scale.

⇒ ***"One join away" is exactly the kind of sentence that gets relayed and becomes a plan.***
A mechanism that works says nothing about the population it works on, and the two get
conflated whenever the mechanism is the interesting part.
