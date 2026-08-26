# Prepared work — Paper Studio lane

**Every entry below was verified by this lane.** Nothing here is second-hand. Entries from
the other two lanes belong in the merged list and are deliberately absent: transcribing
another lane's description as if I had checked it would produce a document that looks
authoritative and isn't.

---

## FIRST: two items prevent recurrence. Everything else repairs an instance.

That distinction decides what gets **built** rather than merely merged.

### R1 — split guard (NOT WRITTEN; design verified)
**Any object carrying `split_provenance` must have at least one page linked from
`index.html`.** Keys on the ARTEFACT, not the procedure, because there is no split script to
hook: splits are per-topic one-offs (`create_apixaban_split_objects_2026_08_19.py`,
`create_bosentan_four_2026_08_19.py`, `create_colchicine_coronary_2026_08_19.py`,
`create_ablation_hf_object_2026_08_19.py`) all written once and all dated the same day. A
guard on the property covers splits nobody has written yet.
**Calibration: fires on 10 of 10 split objects today.** That 100% is the finding — splitting
a topic has never once included linking the children; the step is in nobody's procedure.

### R2 — specialty field on 155 objects (NOT STARTED; cost measured)
Specialty exists **nowhere but `index.html`**, and `cardio_program_status.py` derives it by
parsing that file — the file the prune intends to rewrite. Until specialty is a stored field,
`index.html` cannot be projected, because it would be generated from itself.
**Cost: 122 direct from an index section, 6 inherited from an indexed parent slug, 27 by
hand = 128 of 155 (83%) mechanical.** The 27 are split children whose parent slug is not
itself indexed. They are obviously cardiology by name and I have **not** assigned them that
way: guessing specialty from a drug name is the matcher-that-agrees-with-itself trap, and 27
hand assignments is minutes against a field that will define the published corpus.
**Do it before the index is edited, not after.**

> The 27 unassignable and the 33 orphaned are largely the SAME pages, from the same omission.
> Adding orphan cards supplies specialty; assigning specialty identifies what to add.

---

## Repairs — applied to nothing yet

| # | patch | changes | calibrated against | unverified |
|---|---|---|---|---|
| P1 | caption derived from bounds (`projectors2.py`) | crossing sentence becomes a function of `ci_low`/`ci_high` | 2→0 on the built page; 27 of 36 captions were false corpus-wide | only ONE page rebuilt |
| P2 | leave-one-out derived from k (`projectors2.py`) | k=2 wording generalised to every k=2 pool | 2→0 on the built page; 6 of 12 sentences were self-falsifying | only ONE page rebuilt |
| P3 | per-outcome forest ids + `data-fw` CSS (`projectors.py`, `build_tabbed.py`) | 6 duplicate ids → 0; one radio group per plot | verified on built bytes | 17 other pages with ids/groups NOT rebuilt |
| P4 | `#search` → `#pn-search` | dead fragment resolves | 1→0 on the built page | 146 dead fragments remain corpus-wide |
| P5 | `Source object SHA-256` row (`build_tabbed.py`) | "is this current?" becomes a comparison | page hash == object hash on disk | only ONE page carries it |
| P6 | `lint_interactive_layer_2026_08_26.py` | duplicate ids, shared radio groups, dead fragments | 4 planted defects detected; clean page silent; **negative control pinned to a real single-quoted id** | refuses 144 of 149 pages — needs a baseline before entering the hook chain |
| P7 | `lint_scope_derivations_agree.py` WIDENED + baselined (`scratchpad/lint_scope_WIDE.py`) | all 22 specialties; adds the ORPHAN direction | orphan planted → refused by name; linked → silent; **ratchet proven by planting a 34th** | not applied; `MALARIA_VACCINES_REVIEW.html` refuses unbaselined and should stay refusing |

Also committed and live in the repo (not pending): `fe0374374` (P1–P5 generator + P6/P7 v1),
`4d6c18b35` (the one rebuilt page). Pushed to `fix/ssot-tabbed-shell`. **Not served.**

### Order
R2 → R1 → P7 → P6 → prune. P1–P5 are already committed; their value is unrealised until
pages are rebuilt.

---

## Debt this lane created

- **CRLF normalisation in `ssot/build_tabbed.py`** (`fe0374374`): 1,770 insertions /
  1,793 deletions for a ~15-line change. Content correct, output unaffected, **diff
  unreviewable.** Owed: restore CRLF and re-apply the ~15 lines.
- **The isolated-index workaround** protects a commit's contents and **corrupts every other
  reader of `git status` in the same worktree** — including the build stamp, which produced a
  page truthfully formatted and falsely claiming irreproducibility from a fully committed
  tree. A fix that creates a new false claim elsewhere.

---

## CODA — verified is not working

**None of this is applied, and most of it has been proven only on fixtures.** No page has
been rebuilt for the badge or generator patches beyond the single one. The prune has never
run in CI. The split guard is not written. Fixture-proven means the mechanism fires; it does
not mean the defect is gone from the corpus.

**And the reader-facing surface is unchanged: the build of 2026-08-25 10:18 UTC, generator
`2c0cf3bf0`.** One page was fixed, verified 11 of 11, committed and pushed. It is not served,
because GitHub Pages deploys only from `main` and `main` has not moved.


---

## SHIPPED — two deploys, both verified on served bytes

**Deploy 1 (`4d6c18b35`)** — SOTAGLIFLOZIN rebuilt. 11 of 11 checks on the built file,
served sha matched the committed blob, bytes 3,651,809 -> 4,448,677 and rendered characters
124,079 -> 148,456. Both measures moving is what showed the PROSE fixes reached a reader and
not only the markup ones. External reviewer, independently, with a browser: crossing text
gone, false leave-one-out gone, forest plots click-tested (changing one outcome no longer
changes the others), `#search` fixed, source-object SHA present. **3-4/10 -> 5/10.**

**Deploy 2 (`1cae61868`)** — push one: my split guard, orphan gate and specialty field; the
RoB lane's raster patch, five panel fixes and 25 rebuilt pages. 25 of 25 rebuilt pages serve
their committed bytes; shells and the untouched negative control byte-identical as predicted;
four panel fixes verified ABSENT in served bytes and the fifth verified PRESENT in its
corrected form.

**The auto-trigger did NOT fire for deploy 2.** Deploy 1 published on push to `main`;
deploy 2 needed a manual `workflow_dispatch`. Recorded because afterwards the two look
identical: **"pushing to main deploys" is a SOMETIMES, not a fact.**

**`head_sha` in the GitHub Actions runs API is not a reliable identifier of what a run
built** -- a historical run's `head_sha` had drifted to the ref's current SHA. Match runs on
`id`; treat `head_sha` as descriptive.

---

## RETIRED ON EVIDENCE — and its successor

**RETIRED: "scope the pre-commit hooks to staged paths."** I ranked this first. A fortnight
test killed it: **33% of real refusals were inherited from other lanes rather than staged by
their author**, so narrowing reach loses coverage that matters. I had also miscounted the
cost -- I read an unbaselined corpus-wide guard blocking every commit as blast-radius damage
when it was **the gate working exactly as designed.**

**SUCCESSOR, which the test never examined: gate REACH and gate DURATION are separate
problems.** Reach is fine. Duration is not -- a fifteen-minute window cost four commit
attempts today, because every retry re-enters it. Candidate fixes: cache unchanged files,
move expensive checks to per-push, or **one branch per lane**, which is free and also fixes
the staging sweep and the shared-index staleness. One change, three failure classes.

Recorded as retired-with-successor rather than deleted: a withdrawn item that vanishes reads
as "we looked and there was nothing there", and there was something there.

---

## THREE RULES FROM THE LAST HOURS

**A verdict without its scope is not readable evidence.** The manuscript guard passed 25 of
25 -- on 1,266 characters of a 553,676-byte page, 0.2% of it -- and could not have caught any
of the five defects shipped that morning, because they were in a panel it does not examine. A
real check, working correctly, of something else. **Every gate should emit the fraction of the
artefact it examined beside its verdict.** Mine fail this: my split guard prints `10
(baseline 10)` and never says it walked 155 objects. It also indicts a measurement of mine --
I reported the QA leak as 25 instances corpus-wide when one page alone carries 39, because I
scoped to the paper tab and reported it as a corpus figure.

**Predict a deploy's effects from what the BUILD touches, not from what the commit list
says.** I predicted sotagliflozin unchanged in deploy 2; it moved and got 880 KB lighter. The
raster patch is a GENERATOR change and has no commit-list footprint on the pages it alters.
Confirmed by mechanism, not accepted as a pleasant surprise: embedded PNGs 24 -> 21,
3,973 KB -> 3,113 KB, exactly the traffic-light raster at three views, rendered text +214
characters.

**A count is not a finding until you know which sentence it appears in.** "no information
appears 61 times" looked like a missed fix; it is 61 occurrences across 54 distinct contexts
in the NEW wording -- the panel populating across nine results by five domains. The fix
working, not failing.

---

## THE THREE WAYS A GREEN RESULT MISLED US TODAY

Different diagnoses, different remedies, and only the third looks healthy the whole way:

- **cannot fail** -- no reachable non-zero exit. Remedy: rewrite.
- **can only fail once** -- a one-shot migration check left wired in. Remedy: REMOVE.
- **control expires on its own success** -- pinned to the artefact it guards, valid until the
  fix lands. Remedy: re-pin the control to a fixture; the check itself is fine.

The 24 "vacuous" gates were classified by a static read that can only see the first. **Open
question for tomorrow**, answerable mechanically: does it have a reachable exit; is its
condition pinned to something still present; is its control synthetic or corpus-pinned.

My two new gates are **re-runnable**: their controls are synthetic fixtures in a temp tree,
so no corpus change retires them. Only their baselines track corpus state, and those are
ratchets meant to fall. **The prune is single-use by construction** and its file must say so.

---

## FIXING A READER IS NOT FIXING A CLAIM

Swept my own fixes for sibling readers, after the protocol row turned out to key on a
different field from a fix already made in `paper_projector.py:3585`:

- **source-SHA / "is this current"** -- FOUR other readers, two of them named gates
  (`build_stamp_gate.py`, `generator_stamp_gate.py`). I added a hash to the page and never
  asked whether the gates that already judge staleness would read it.
- **duplicate element ids** -- one sibling, `audit_40_checks.py`, agreement unchecked.
- **page population** -- **81 scripts read `PAGE_MAP`.** I built an instrument to detect this
  exact class and scoped it to two of eighty-one.

**"The corpus" is a phrase eighty-one scripts each define for themselves**, and two of them
disagreeing cost us two unreviewed manuscripts today.

---

## STOPPED DELIBERATELY, NOT UNFINISHED

The prune is ready and is NOT shipped. 950 MB, ~1,067 pages, a hand-edited index, and a
blast-radius model that just proved incomplete. Its conditions stand: delete THEN regenerate
the sitemap; index cards in the same commit; its own deploy with its own verification;
post-deletion checksum against the retain-list before committing, because verifying a list
and shipping a deletion are two artefacts.


---

## THE PRUNE — RAN, REFUSED ITSELF, NOT COMMITTED

It executed end to end and **declined to certify its own result**. Nothing committed, tree
restored, 1,254 files moved back, 0 lost.

    moved 1254  surviving 259  cards 226  dead-cards 74  uncarded 106  sitemap 258  stale 0

**One clean success: the sitemap regenerated to 258 entries with ZERO stale.** Delete-then-
regenerate works exactly as designed, on what was the highest-risk item on the list — 1,191
of the old sitemap's 1,309 entries were pages the prune removes, and none survived into the
new one.

### Blockers — two are bugs in MY code, one is a corpus fact

**1. The card strip is a PATTERN problem, not a coverage problem. DO NOT RE-RUN ASSUMING
OTHERWISE.** It removed 404 of 478; **74 cards survived pointing at moved files.** The regex
`<a href="…" class="card…">.*?</a>` does not match every card shape in `index.html`. The
markup variants must be ENUMERATED before the strip is trusted — 404 of 478 looks like an
edge case and is actually an unknown number of unmatched shapes.

**2. The byte assertion compared unlike things, and the cause deserves its own name:
I TREATED A SCRIPT AS ITS FIRST NOUN.** `add_meta_description_and_sitemap.py` does both
things it says: it regenerates the sitemap **and rewrites pages**, inserting 71,912 bytes of
meta tags into 52 files — *after* my plan had counted them. A name listing two behaviours,
read as one. The assertion was right to fire and wrong about why.

**3. 106 retained pages have no card**, and this one is real. Retaining the unclassified
means retaining pages that cannot be honestly placed in a specialty section, because they
have no `specialty` and no classification. **That is the price of "when a classifier cannot
tell, KEEP"**, and it is the correct price — but it must be visible rather than discovered.

### Why it stopped rather than shipped

Four incidents tonight — a partial deletion into another lane's open file handle, a
classifier that condemned `index.html`, a script that rewrote 52 pages unasked, and a strip
that missed 74 cards. **Every one was caught by a check or by the orchestrator. None by me.**
That is a reliable signal about the hour, not about the work. The site has been promising 464
pages it does not have all day; it is not worse for waiting.

---

## RULES FROM THE LAST HOURS

**A drop list is as dangerous as a retain list, and I only audited one of them.** Every
classification today checks that what we KEEP is right and never that what we DISCARD is
wrong. The retained-links check, the chip states, the card counts — all interrogate the
survivors. Nothing interrogated the condemned, which is how a rule written for review pages
came to classify the site's front door as legacy: **`Canonical object` is a review-page
marker, evaluated over every file in the root.** The homepage has no reproducibility table
because it is not a review, and the rule read that as evidence it was old.

**When a classifier cannot tell, KEEP.** An unknown retained costs bytes; an unknown dropped
may be a page someone needs, and nobody finds out until a reader does. Measured: retaining
108 unclassified files cost **6.2 MB of a 605 MB saving — about 1%**. Dropping on uncertainty
buys almost nothing and is the flattering default in new clothes.

**Derive the allow-list from the build, not from judgement.** Anything named by `pages.yml`,
`pages_preflight.py` or the sitemap generator is furniture by definition. My own inspection
produced seven names and **missed two the build names explicitly** — `what_changed.html` and
`cardiology_mortality_atlas.html`.

**A client-side change cannot be confirmed OR refuted by grepping served bytes.** The badge
chips are runtime-injected. I read a served card, saw two spans, and reported the chips
missing; they are appended as a third span at load. My phrase counts were **string literals
inside the injecting script** — the fingerprint of a script that is present and about to
populate 532 cards, counted as though it were output. Any sweep over badges, chips or
indicators needs a browser.

**`writers: 0` means no process is running now, not that no operation is in flight.** A lock
outlives its process. The quiet check must be: no live writer, no lock, AND stable across a
re-read after an interval.
