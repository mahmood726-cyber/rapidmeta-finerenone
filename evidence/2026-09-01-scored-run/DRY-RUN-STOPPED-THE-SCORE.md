# The dry run stopped the score. **My harness was asymmetric while I believed it was not.**

    REF.rubric   rubric-1.0.0-2026-08-31   sha 1ef22ec92775a6ee   selftest 14/14
    REF.harness  scoring-harness-1.0.0-2026-09-01  sha e5689f6108742a67
    REF.pair     ablation-af-heart-failure  vs  PMID 40998847
    REF.runner   scripts/rekey20/score_pairs.py   --dry-run

⛔ **NO PAIR IS SCORED FOR PUBLICATION. The eight are not run.**

---

# 1 WHAT THE HAND-READ FOUND

    ours   k=4   NCT00643188 NCT00911508 NCT01288352 NCT01420393
    theirs k=2   NCT05508256 NCT06125925

**[MEASURED]** what those two identifiers are, in the comparator's own words:

> *"Ongoing RCTs, such as the comparison of CA for AF in HFpEF patients with conventional
> treatment (CABA-HFPEF; **NCT05508256**) and CA for AF in HFpEF patients (STABLE-SR IV;
> **NCT06125925**), may provide more definitive evidence…"*

**They are trials the comparator explicitly does NOT include.** Its actual included studies
are named by acronym and carry no registry ids anywhere in the text:

    CASTLE 5 mentions · AATAC 3 · CABANA 3 · RAFT 3 · AMICA 1

⇒ Every label-dependent verdict on their side is an artefact. S3 reported *"no numeric row
within 600 chars of NCT05508256"* — of course not; it was never an included study.

---

# 2 ⛔ THE DEFECT, AND IT IS THE ONE I WAS EXPLICITLY WARNED ABOUT

Our pages are built from an SSOT that prints an NCT id per included trial. Their papers print
registry ids only for trials they are **not** including. So:

> **Our side got real included-study labels. Their side got incidental mentions.**

That is the asymmetry `SCORING-HARNESS.md`'s binding clause forbids, and **I built it while
believing I had prevented it.**

⭐⭐ **"THE SAME RULE MUST EXTRACT BOTH SIDES" IS NOT SATISFIED BY RUNNING THE SAME CODE ON
BOTH SIDES.** I did run one function on both. It extracted **different kinds of thing** from
each, because the two document families print registry ids for different purposes. **Same
code ≠ same rule.**

⭐ And it is the programme's own ruling, re-committed by me in a new place.
`TWENTY_COMPARATORS.json._join` records that a trial ACRONYM "was measured to find MENTIONS
rather than INCLUSIONS and was ruled out". **I inherited that ruling for acronyms and then
made the identical error with registry ids** — the fourth instance this session of *a
confident authority answering a different question*, after `SGLT2`→the protein,
`Intravenous`→the route, `supraventricular`→a ventricular arrhythmia.

## 2.1 A second defect, mine, in the same run

`topic_terms` was built by replacing hyphens in the topic slug —
`{'pop': ['ablation af heart failure']}`. The harness spec says **"from the FROZEN topic
definition, not re-derived per pair"**, and I re-derived it per pair. S2 returned
`NOT_SATISFIED` on both sides with no evidence span, which is that defect surfacing rather
than a property of either document.

---

# 3 WHY THE HAND-READ WAS THE ONLY THING THAT COULD CATCH IT

The summary looked **entirely plausible**:

    S2 TIE_NEITHER_SATISFIES · S3 OURS_BETTER · S4 NOT_SCOREABLE
    S5 TIE_NEITHER_SATISFIES · S6 NOT_SCOREABLE · S7 TIE_NEITHER_SATISFIES

A believable spread with one win for us. Nothing in it says the comparator's labels were
ongoing trials. **Only the SPANS said so** — which is precisely why the rubric requires
`file · offset · length · span` on every row, and why reading them was the acceptance test
rather than reading a total.

⇒ **The dry run cost one pair and caught a defect that would have silently biased all 24.**

---

# 4 WHAT IS NEEDED, AND IT CHANGES THE FROZEN SPEC — SO IT IS NOT MINE TO CHOOSE

An extraction rule that finds **included** studies symmetrically, where one side declares
registry ids and the other declares acronyms. The honest options:

**(a) Require registry-id enumeration on both sides.** Anything else →
`NOT_SCOREABLE_NO_STUDY_LIST`. Symmetric and conservative, and it would make most comparators
unscoreable on S3/S4/S7 — **which is a real finding about them under PRISMA 2020 item 17**,
not a failure of ours. The published frames already measure 136 of 289 assessed papers
enumerating nothing.

**(b) Use `opencomp`'s `included_studies_table` path.** It yields a row COUNT and no label
strings, so it can feed `k` (S5) but **cannot** feed S3/S7, which search each label as a
literal string.

**(c) Extract acronyms from an included-studies table only** — not from free text. This is
narrower than the ruled-out acronym match, because a table row is an enumeration rather than
a mention. It is the only option that would score S3/S7 on both sides, and it is a genuine
change to a frozen ruling.

⛔ **I am not choosing.** Picking (c) would relax a ruling the programme made deliberately;
picking (a) would report a large `NOT_SCOREABLE` count that is a headline in its own right.
Both are decisions about what the comparison MEANS, not implementation details.

---

# 5 WHAT STANDS

* `rubric.py` released, selftest **14/14**, `--score` no longer refusing, file sha recorded
  before and after.
* `SCORING-HARNESS.md` frozen and committed **before** any pair was scored — and it did its
  job: the spec was right and my implementation of it was not, which is exactly the failure a
  written spec is supposed to make visible.
* Gate: **8 SCOREABLE**, 3 named `NOT_SCOREABLE_SURFACE_DISAGREEMENT`.
* Texts: **20/20 open-access full text**, `text_source` a field, length control probed 5/5.
* Repeat-instability **27% / 6.5%** wired into the result header, not an appendix.
