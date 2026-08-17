# TOOLING QUEUE

Work on the instruments rather than on the pages. **The estimand gate is first**
and everything below it is ordered behind that.

The admission rule that governs every entry here is the one in
`scripts/standard_manifest.py`: **no property enters the standard without a
constructible failing input and a real defect it would have caught.** An item on
this queue is not done when the code runs; it is done when the failing input
exists, has been run, and blocked.

---

## 1. THE ESTIMAND GATE — unreliable in both directions

`scripts/estimand_definition_gate.py`. It over-read ARNI and under-read
SOTAGLIFLOZIN. Both directions are already logged, and neither is fixed.

**It tells you where to look. It never tells you what you will find.** Every
verdict has to be checked against the registry text by hand, which means today
the gate is a search aid wearing a gate's costume.

The under-read direction is the dangerous one and the ledger says why:

> Six separate under-reads in one component canon ALL pushed toward withdrawal.
> Five of the six failed toward alarm — and were still dangerous, because the
> action each argued for was destructive. Withdrawing a correct estimate destroys
> a true finding and publishes the destruction as a discovery.

**What is owed, in order:**

1. A **fixture set of registry endpoint texts** with the correct component
   decomposition recorded beside each, taken from the six under-reads already in
   the ledger (`CV mortality`; `hospitalisation for worsening heart failure`;
   `worsening heart failure requiring unplanned hospitalization`;
   `cardiovascular (CV) death`; a bare TITLE with components in the DESCRIPTION;
   `Total Mortality, Disabling Stroke, Serious Bleeding, or Cardiac Arrest`).
   Every one of those is a real string this gate mis-read. Replay them.
2. **Widening the finder without widening the classifier is not a partial fix.**
   A phrase matched and then assigned to no key is indistinguishable from never
   matching it. Two places, one fact — assert that every phrase the finder
   matches lands in a key, and fail when it does not.
3. **A third verdict for "the registry record carries no endpoint definition"**,
   distinct from "the definitions differ". Those are different facts and one of
   them is not the trials' fault.

---

## 2. `card_matches_page` corpus-wide — 507 of 514 unmeasured

Fixed on 2026-08-18 so that a withheld card is checked rather than skipped
(see `STATUS.md`), but the corpus figure barely moved: **5 comparable, 2 agreeing
by withholding, 507 unmeasured.**

The unmeasured 507 are almost all `Audit-first build` cards, which are
UNCHECKABLE by construction — and 13 of those cards contain a self-contradiction
(`2 trials` and `k>=3` in one string) that no gate can currently see.

The real fix is the one the gate's own header names: **cards are authored, not
projected.** A generator that emits the card from the object retires this entire
class rather than measuring it.

---

## 3. `sections_in_both_surfaces` — NOT RUN on 7 of 7 objects

`section_manifest_gate` needs a docmodel and correctly exits 2 rather than
tracebacking when there is none. Correct behaviour, zero coverage: the property
is unestablished on every v1 object including the flagship.

Either produce a docmodel per object, or move the property to DECLARED in
`standard_manifest.ENFORCEMENT` and stop implying it is watched.

---

## 4. `self_contained` — measured corpus-wide, wired per page nowhere

`external_dependency_census` measures it; `checkbuild` enforces it on new builds
only; nothing checks a page that already exists. 19 of 21 sampled pages issue
third-party requests on load and all 19 got HTTP 429 from `api.openalex.org` in
one run. ~874 pages fetch the R runtime from a CDN at read time, so a
reproducibility claim degrades silently to whether someone else's CDN is up.

Wire the census per page so the property has a per-object verdict.

---

## 5. `tabbed_build` and `estimate_preserved` — checked only inside the build path

Both are marked ENFORCED and both are "checkbuild-equivalent", which means they
are established for pages built THROUGH the build path and unestablished for
every page already on disk. `v1_coverage_audit` reports them `NOT WIRED HERE`,
which is honest and is not coverage.

---

## 6. `display_change_announced` — UNENFORCEABLE, and correctly so

No artefact can show that a change was announced; the evidence is a message to a
reader, outside every file we control. Kept as a rule with a named owner rather
than a checker that could not fail. **Do not "fix" this by adding a checker that
inspects a changelog** — that would check that a file was written, which is a
different claim and the exact substitution this project keeps making.

---

## 7. Untracked SSOT objects — 20 of them exist in no clone

Twenty objects under `ssot/*/` were written on 17 Aug and never added. They are
ledger failure mode #4: a register written into a place git does not carry.
`durable_artefact_gate` runs unscoped on every push for precisely this class but
does not know about these paths.

Either commit them or add them to the gate's watch list. Writing a file is not
preserving it.

---

## Closed

- **2026-08-18 — `card_alignment_gate` reads the wrong tree by construction.**
  `SSOT` was a hardcoded absolute path; run from a sibling clone the gate graded
  another working tree and reported green. Now derived from `__file__`. This is
  the ledger's matched-pair false-life defect and it was still live in a gate.
- **2026-08-18 — a withheld card stopped the gate reading the page.** Replayed
  against SGLT2_HF at `7124fdbed^`, which went live with a card announcing a
  withdrawal the page had not performed. Old gate: UNCHECKABLE. New gate: FAIL.
- **2026-08-18 — `v1_coverage_audit` over-matched a substring, third instance.**
  It grepped gate output for blind-words BEFORE reading the exit code, so prose
  containing "UNCHECKABLE" overrode a deliberate exit 3. Two previous patches to
  that regex had already failed; the fix was precedence, not a third pattern.
  **A declared field beats an inferred one.**
