# Session state, 2026-08-24 — writer lane on `fix/ssot-tabbed-shell`

Written while the reports were still sharp, not at the end of the last batch. Everything
below was verified in the session that wrote it; where it was not, it says so.

---

## 1. The one line that matters most

**MERGED AND LIVE.** `main` fast-forwarded `8a8f12bf4..f615af55a`, 14 commits, 56 files,
10 delivered pages. Verified on SERVED bytes after the Pages deploy, not on the worktree.

The acceptance test was stated before the push and met after it, on the same URL:

| `AMOXICILLIN_AOM_AUTO_FULL_REVIEW.html` | before | after |
|---|---|---|
| `...at any rank on the clinical quantity this page pools` | 5 | **7** |
| `...register no clinical endpoint at any rank.` (unbounded) | **2** | **0** |
| served size | 487,636 | 489,343 |

All ten pages checked in BOTH directions -- the bounded form present at the same count
as the local file, AND the unbounded form absent. **10 of 10 LIVE. Non-movers: none.**
The deploy took four polls at 30-second intervals to appear; the first three served the
old bytes, which is why this is measured by polling to a stated condition rather than by
waiting a guessed interval and asserting.

*This section previously read `nothing from this session is live`. That was true when
written and false thirty minutes later. It is rewritten rather than annotated, because a
sentence that was true once and is now false -- with nothing in it saying which half aged
-- is precisely the decayed-citation class recorded in section 3, and a document that
commits that error while defining it is worth less than no document.*
---

## 2. What was established, with its evidence

### The estimand bound: seven confirmed, ten carrying

Ten withdrawal notices said `ALL 2 OF 2 SEEDED REGISTRATIONS REGISTER NO CLINICAL ENDPOINT
AT ANY RANK.` while the same objects said, in their own `question` field, the same thing
bounded — `...ON THE CLINICAL QUANTITY THIS PAGE POOLS`. The first is a claim about the
trials; only the second is one the object can support. NCT00377260 registers 21 secondary
outcome measures, among them a clinical-failure distribution.

Repaired as a **projection**: the bound is read from each object's own `question` and
appended to its own sentence. Two lines per file, 20 field occurrences, no key gained or
lost, all ten pages rebuilt, unbounded form now 0 and bounded form 2 on every one.

**Seven were confirmed by reviewer lanes; three — `menacwy-booster`, `thiamine-sepsis`,
`tigecycline-infection` — were found only by sweeping for the shape.** "Seven" was a count
of reviewer reach and I had been holding it as a count of the corpus.

**Not touched, and reported instead:** each trial carries `clinical_endpoint_at_any_rank`,
`False` on NCT00377260 while its registered secondaries include "The Distribution of
Clinical Failures". Whether a clinical-failure count is a clinical endpoint is a
definitional judgement that flag has already made. Re-deciding it is a judgement about the
evidence, not a projection.

### Rollout commit-pinning

The rollout now reads the eight generator files at launch, **refuses by name** if any is
dirty, and records the SHA every page in the run will carry. Planted: a line added to
`ssot/wysiwyg.py`, the rollout refused naming five dirty files including the plant;
reverted, it proceeded. Every page from a run is now reproducible from one commit — the
claim the reproducibility artefact has been making all along without being able to support.

---

## 3. Defect classes established tonight, with their instances

Each is a *class*, not an instance, and each has at least one measured example. They exist
so a claim of one kind is never summed with a claim of another.

### An assertion must hold at the RECEIVER
The same claim — *nothing is withheld* — failed three times in 24 hours, at three layers,
each invisible from the one above:
- **Assembly**: packet built from a chosen field list and certified complete → 11 reviewers
  rejected sound work reasoning correctly from what they were given.
- **Propagation**: producer fixed while 158 already-written prompts sat queued with the old
  form; **56** would have made a claim their author had retracted.
- **Delivery**: 487,175 bytes sent, `<truncated 295594 bytes>` in the reply, **191,581
  delivered** — identical on both affected lanes, so a cap, not a hiccup.

Rule: *do not assert completeness above the largest size observed to arrive whole.* A packet
over the line gets an honest warning, not a softened claim. `scripts/packet_transport.py`.

### A truncated input is met with REFUSAL, not a warning
An answer written over a cut packet is not a weak result, it is not a result. One of the two
truncated lanes contained `ACCEPT` further up its text and would have been banked as a clean
read. Control: two lanes of byte-identical text differing only in the marker → `CLEAN` vs
`INPUT_TRUNCATED`.

### CORRECT_BUT_REMEDY_REGRESSES
A charge that *holds* whose proposed fix makes things worse. `audit_exclusion_by_absence`:
a bare `pages` in the corpus-loop pattern also matches a local of the same name — true of the
regex; applied, it drops 36 entries, every one a genuine corpus pass. `healed=0` on the
rebaseline is the independent confirmation.

### CORRECT_IN_ISOLATION_WRONG_IN_CONTEXT
A reviewer reading a checker cannot see a defect living in the *relationship* between the
checker and its corpus. The lane that reviewed `double_escape_gate.py` cleared *a probe keyed
to the string a fix removes* as "no finding" — and running the gate found exactly that, six
times: it was matching `.replace(/&amp;mdash;/g, "&mdash;")`, **the search pattern of the
code that repairs the very thing it hunts**. Zero reader-visible. Nothing in the file was
wrong.

### A citation can DECAY
Earlier false-provenance defects were wrong when written. `propagate_pi_k1`'s "213 curated
dashboards (per `scan_stat_engine_violations.py`)" was **true once** — every component true,
the combination false, and nothing saying which half aged. A citation is a claim about a
*relationship* and fails if either side moves. `scripts/audit_citation_decay_2026_08_24.py`
finds them: 14 count-plus-source sentences, three states, two highest-risk named.

### An implausible proportion is about your INSTRUMENT
Four numbers caught this way, all mine, all in the accusing direction: **94%** (a `//`
stripper eating 49% of each minified page at the first `https://`), **745 pages** (a
`,async importReviewPack(event){` my regex could not read, though the gate's own `_DEFS`
reads it correctly), **8 of 156** and **7 of 156** from the truncation checks. Every time the
implausibility was the tell, not the arithmetic.

### Verification theatre, and its subtler twin

**`check_38_nesting_via_template_literal` is the cleanest instance anyone has produced.**
A P0 docstring, a loop, a counter — and **zero reachable appends**. It returns `[]` on
every input that has ever existed, and has been counted among "40 checks" ever since.
Its own comments say exactly why: the real test is *hard*, the cheap proxy *too noisy*,
so the author stopped. **Nobody lied. The artefact lied by remaining.** That is the whole
mechanism of verification theatre — it does not require an author who intended to
deceive, only an author who stopped and a reader who never opened the function.

**`check_14_invalid_pmid_format` is the subtler twin.** Its body tests
`if v and not v.isdigit()` — correct logic, unreachable, because `PMID_RE` captured
`\d*`. **A check written for a wider input than it was given.** Its docstring promises
to catch `pmid: 'NaN'`.

The pairing matters more than either alone: **from outside they are indistinguishable.**
Both have a docstring naming a real defect, both run, both return `[]`, both are counted.
Only reading the call site separates *never implemented* from *implemented against a
narrower feed*. A count of checks is not a count of coverage, and neither can be audited
from a list of names.

The output shape is the remedy for the first: `NOT_IMPLEMENTED` across 1,510 pages in
its own severity row — **neither a finding nor a pass**. That is the third time in this
session a gate has been made to say *I cannot tell*, after the double-escape `NOTE` and
the packet-transport refusal. Three states in a gate's output, not in a report about it.

### A control that fails for an unrelated reason is worse than no control

My own verification harness scored **three verdicts wrong** before I caught it. The
checks take a `Path` and read `p.name`; I passed the string `"x.html"`; the
`AttributeError` was swallowed by my own `try/except`; the wrapper returned `None`; and
**the harness scored `None` as CONFIRMED**.

It produced confident verdicts about nothing. One of them made a real defect read
COULD NOT DETERMINE — the dismissing direction, which is the expensive one, because it
retires a true finding instead of adding a false one. A control that can fail for a
reason unrelated to the property under test is not a weak control; it is an instrument
reporting on its own plumbing in the vocabulary of the thing it was pointed at.

### Act on a claim only with a MEASURED equivalence
The procedure that decides apply-vs-decline. Same gate, same night: quote-aware
`_realdata_block` **applied** on a corpus-wide proof (1,473 blocks byte-identical, 0
boundaries moved, 0 NCTs gained or lost); requiring `RapidMeta` binding **declined**, backed
only by a fixture and a regex that had already produced two false numbers. Second safe form:
*a change that can only merge, never split* — which is why normalising line endings before
comparing verdicts could ship without a corpus-wide before-and-after.

---

## 4. Gates repaired, each planted before trusting

| Gate | Defect | State |
|---|---|---|
| `audit_exclusion_by_absence` | `files == 0` unreachable (the sweep walks the directory the file lives in); `NEG_GUARD` could not cross a comma (+37); two-line exit window (+16) | fixed; sees **204** corpus-wide guards where it saw **152** |
| `double_escape_gate` | unreadable named path skipped silently, `scanned 0 page(s)`, exit 0; `&#X27;` unmatched; non-text payload → PASS; **six false FAILs on the repair code's own pattern** | fixed; FAIL / NOTE / PASS three states |
| `clone_contamination_gate` | single-quoted handlers invisible; **verdict comparison defeated by CRLF-vs-LF**; brace-in-string absorbing a foreign registry | fixed; corpus output byte-identical before and after |
| `audit_40_checks` | `check_38` P0 with **zero reachable appends**; `check_14`'s own `not v.isdigit()` unreachable; two regexes narrower than their docstrings | 4 of 8 fixed |

**The 52 newly visible guards are admitted as UNEXAMINED under their own baseline key**, not
merged into `guards` beside 44 entries carrying written reasons. Merging would promote *never
looked at* to *known and accepted* — the SKIP-as-pass shape. The ratchet is unaffected.

---

## 5. What is NOT established, named rather than resolved

- **Whether 19 large-prompt lanes were truncated silently.** COULD NOT DETERMINE. The
  776,959-byte lane cites a path at byte 755,310, past any cap — but that path is composable
  from my own prompt header, so it is evidence in neither direction. **The canary probe is
  written and blocked behind agy's quota.**
- **The per-band BEFORE table does not exist.** The audit's JSON was never committed, so
  only three totals are held: 858 → 890 → **959 of 1,537 (62.4%)**. A reconstructed
  before-table would be an invention with a table's authority. The JSON is now committed so
  the next comparison has a baseline.
- **`CLAIMS_DEFECT` remains UNVERIFIED, permanently.** 138 claims at last count. Nothing in
  the harvester checks a claim against the artefact.
- **295 hard contamination findings** in `clone_contamination_gate` are pre-existing and
  untouched (HEAD's copy produces the identical number).
- **156 of 157 pages never emit `</html>`/`</body>`** — pre-existing, unrepaired.

---

## 6. Owed, in order

1. ~~Merge to `main`, push, verify on served bytes.~~ **DONE** — `8a8f12bf4..f615af55a`,
   10 of 10 pages verified live on served bytes, non-movers none. See section 1.
2. **The canary**, when agy's window reopens — an early and a late marker either side of
   191,581 bytes, both requested back. Settles §5's first item.
3. **RoB 2's two items**, when the other lane hands over:
   - **11 of 37 GRADE outcomes downgraded on RoB judgements with no answers behind them.**
   - **`_d5` understates on 4 of 29 records in `iv-iron-hf`.** ⚠️ **Do not patch the return
     value — it never collects 5.3 at all.** Patching the return would paper over a missing
     input.
4. **`audit_40_checks` claims 5–8**, all confirmed, none fixed: `check_10` (id mentioned
   inside a value passes as a key), `check_16` (img-src host accepted as script source),
   `check_31` (`RapidMetadata` satisfies `RapidMeta.init()`), `check_39` (icon-only buttons).
   Each needs real logic, not a wider pattern, and none has a measured equivalence.
5. **The remaining lane queue**, in checkability order: 294 `CODE_BEHAVIOUR`, 147
   `ARTEFACT_STATE`, 10 `INSTANCE_JUDGEMENT` last. Measured yield: code claims ~7 in 8,
   instance claims ~1 in 10.
6. **Brief items 8–18**, never started (duplicate key names, screening paths, single-arm
   gate, `protocol v1.0` rows, `emit_sidecar` refusals, v13 gate coverage, TEMPLATE_PATH
   freeze, PRISMA-NMA block, topology disclosure, the 111 pages claiming NMA with no
   network). **Item 1 was refused on a false premise** — the 17 objects said to "hold
   nothing" all hold something.
7. **DO NOT START:** the 480-page legacy conversion.

---

## 7. Honest limits of this session

- **Three commits were reported as landed and had not landed.** I read a background task's
  "exit code 0" — my own wrapper's exit, since the command ended `; echo EXIT=$?; tail -4`.
  That is *a status code reporting the wrapper rather than the work*: the shape on our own
  hunt list, occurring twice in one night, the second time corrupting a report rather than a
  measurement. **Every commit claim is now backed by a `git log` line in the same command.**
- **My own instruments produced at least six false numbers**, all in the accusing direction,
  every one caught by measurement rather than by review: 94%, 745, 8 of 156, 7 of 156, 11,024
  in-comment definitions, and three verdicts distorted by a harness passing a `str` where the
  code reads `p.name`.
- **Heredoc escape mangling recurred three times** despite a standing rule against it.
  Patches carrying regexes must be written with the file tools, never through a shell.
- **`sys.stdout` reassignment at module level** killed three verifiers three ways — plain
  import, re-wrap (the second wrapper shares the buffer; the first's collection closes it),
  and `exec` of a patched copy. `lessons.md` widened past pytest.

---

## 8. Pool at the time of writing

Codex 4 running, agy 0 of 2 standing down **11,569 s** of a vendor-stated 4h31m window —
parsed from the refusal text, not guessed, and confirmed firing on a live quota event.
**255 lanes launched, 251 returned, 1 failed, 663 queued.**

Session verification totals: **~23 claims verified against the artefact, 3 declined as
regressive or unproven, 6 of my own instrument errors caught and withdrawn.**
