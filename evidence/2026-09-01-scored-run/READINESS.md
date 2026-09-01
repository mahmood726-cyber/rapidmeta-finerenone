# Scored run — **READY on 2 of 4. Item 3 is blocked twice and I am not working around it.**

    REF.comparators  F:/rapidmeta-xsurface/TWENTY_COMPARATORS.json   sha 1f5807308cf5fabe
    REF.baseline     F:/rapidmeta-xsurface/gates/COMPARATOR_PAGES_CROSS_SURFACE_
                     BEFORE_2026-09-01.json                          sha ed40b1559b7515be
    REF.staged       F:/claude-temp/scored-run/texts   (outside the repo; manifest inside)

Both source files are owned by the surfaces lane, **read by explicit path and hashed** — read
across worktrees is fine, reading without recording *which version* is not.

---

# 1 ✅ COMPARATOR TEXTS STAGED **[MEASURED]**

    pairs 24  ->  DISTINCT comparator PMIDs 20

    oa_full_text   20
    abstract        0
    unavailable     0
    downgraded      0

Every record carries **`text_source` as a FIELD**, plus `abstract_chars`, `text_chars`,
`sha256`, `licence`, `pmcid`, `path`. ⛔ **`oa_full_text` and `abstract` may not be pooled in
any score** — this project has measured that substitution moving `MATCHED` from 6/20 to 16/20
with no rule change at all.

Licences: 8 × `cc by`, 5 × `cc by-nc`, 7 × `cc by-nc-nd`. All twenty are open access with a
machine-readable full text.

## 1.1 ⚠️ 20 of 20 clean is the kind of result my own rules say to distrust

The length control — a claimed full text must exceed **2.0×** its own abstract — **never
fired**, because the observed ratios were 9×–43×. An unexercised control is a guess, so it is
now proven with a synthetic probe through **the same function the run uses**:

    plant  'full text' shorter than 2x its abstract   -> DOWNGRADE   ✓
    plant  'full text' EQUAL to its abstract          -> DOWNGRADE   ✓
    sibling a genuine full text (17x)                 -> keep        ✓
    sibling exactly at the 2.0x threshold             -> keep        ✓
    edge    no abstract to compare against            -> cannot downgrade ✓

**[MEASURED] Prediction scored: I predicted 12–17 full texts and got 20 — a miss, high.** My
stated mechanism was *"OPEN_ACCESS means the article is free, not that Europe PMC holds
machine-readable full text"*. That is true in general and **false for this set**, because the
selection rule required PMC open access, which does guarantee it. **Fourth consecutive high
miss**, and the same shape as the last three: I modelled one term (OA ≠ full text) and missed
the other (the selection rule already forced it).

---

# 2 ✅ THE HARD GATE IS WIRED IN FRONT OF SCORING **[MEASURED]**

    SCOREABLE                            8
    NOT_SCOREABLE_SURFACE_DISAGREEMENT   3
    NOT_SCOREABLE_NO_BASELINE            0
    TOTAL                               11   sums to the pages: HOLDS

    ⛔ ARNI_HF_REVIEW.html              MEASURE_MISMATCH  index HR 0.8715 k=4 vs
                                        dashboard OR 0.851294 k=3
    ⛔ NIRSEVIMAB_INFANT_RSV_REVIEW.html MEASURE_MISMATCH  index RR 0.2605 k=2 vs
                                        dashboard OR 0.224222 k=3
    ⛔ SGLT2_MACE_CVOT_REVIEW.html       K_MISMATCH        index k=2 vs dashboard k=4

**Blocked in BOTH denominators, because the deliverable is counted in topics and the gate runs
over pages:** 3 of 11 pages · 3 of 14 topics (`arni-hfref`,
`nirsevimab-infant-rsv-review`, `sglt2-mace-cvot-review`).

⭐ **`NOT_SCOREABLE_NO_BASELINE` is a third state, not a tidy-up.** "Absent from the baseline"
and "present and clean" are different facts, and collapsing them is how a gate starts passing
what it never saw. It is observed 0 times and **proven reachable** by control.

**Controls, all three directions against the real baseline:** ARNI (known mismatch) refused ✓ ·
ABLATION_AF (known clean) scoreable ✓ · absent page → `NO_BASELINE` ✓. **The negative is what
makes this a measurement** — a gate proven only to refuse would block everything and still
pass its own positive control.

⛔ **The baseline is READ, never re-derived.** A second opinion from an instrument never
validated against the surfaces lane's would make any disagreement unattributable.

---

# 3 ⛔ BLOCKED, TWICE — and I am not working around either

**(a) `rubric.py` does not exist.** Searched this worktree, `git ls-files`, and the sibling
worktrees `rapidmeta-xsurface`, `-finerenone`, `-main-fix`, `-corpus-wave`. **Nothing.** The
only match anywhere is my own `PREDICTION-RUBRIC-V2.md`, which is about MeSH and unrelated.

**(b) AGYW is not in this comparator set.** The 14 topics are ablation ×3, arni, attr,
colchicine ×2, finerenone, iv-iron, lenacapavir, nirsevimab, sglt2 ×2, sotagliflozin. There is
no dapivirine topic and no AGYW page among the eleven.

⇒ **I cannot dry-run a rubric that does not exist, on a pair that is not in the list.** Rather
than write my own rubric and call that the dry run — which would score the run against an
instrument nobody specified — I am naming the block. **Point me at `rubric.py` and at the
AGYW pair's location and item 3 runs immediately;** both fetching and gating are already done,
so it is the only thing between here and ready.

⚠️ The requirement I *can* pre-commit to: **every scored row must carry
`file · offset · length · SPAN` and the rubric's own sha256**, so a disagreement can point at
a sentence. **If any row cannot, the rubric is not ready** — that is a gate on the rubric, and
it will be applied whatever the rubric turns out to be.

---

# 4 ⚠️ REPEAT-INSTABILITY — the number that must ship with every score

**[MEASURED] this session, on the same judge:**

    27%    of labels change when the rubric is tightened in a way that can only REFUSE
    ~6.5%  of labels flip on a straight repeat with NO rubric change at all

⛔ **A score without that attached is a point estimate pretending to be a fact.** And the
concrete warning: `5 of 7` was **identical across two runs** while a quarter of the underlying
labels changed and the surviving evidence was nearly disjoint. **Two runs agreeing on a count
is not two runs agreeing.**

---

# THE THREE CAVEATS THAT TRAVEL WITH ANY RESULT

**(a) The blind FAILS — 9/9, p = 0.00195.** The run is **OPEN-LABEL and must say so**. Staging
a blind that is known not to hold would be worse than not blinding.

**(b) Three denominators, never interchangeable: 20 comparators · 14 topics · 10 families ·
24 pairs · 11 pages.** The comparator file says it in its own header —
*"THE SUM IS THE WRONG NUMBER"* — because one comparator is eligible in two frames.

**(c) PMID 40998847 alone accounts for three pairs across three ablation topics.** One paper,
one drug family — **closer to one demonstration than three**.

⚠️ **A fourth, from the comparator file's own header and not in my brief:** its frame `doi`
field is **KNOWN WRONG** — the extractor walked into `ReferenceList` and kept the last match.
DOIs must come from the file's per-PMID resolved field, never from a frame. My manifest does
not carry DOIs at all, so nothing here inherits it.
