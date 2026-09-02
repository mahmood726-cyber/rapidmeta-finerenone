# The gates: how to run them, what each refuses, and what each cannot see

Written 2026-08-15 at handover of the single-writer lock on
`F:\rapidmeta-finerenone` and `F:\rapidmeta-ssot-shell`.

These are the acceptance tests for the corpus programme. **Reuse them rather than
rewriting them** — most carry a fixture recovered from a real defect that cost
hours to find, and a rewrite loses the fixture.

Every gate has a `--selftest`. Run it before trusting a result; that is the point
of them, not a formality.

---

## Run everything

```
python scripts/run_all_checks.py --selftest          # every gate's own self-test
python scripts/run_all_checks.py \
    --object   ssot/<app>/<app>.json \
    --page     <built>.html \
    --docx     <manuscript>.docx \
    --docmodel manuscript_docmodel.json
```

Exit code is the number of failed checks, so a batch runner can sum it. A check
that cannot apply reports **SKIPPED**, never a pass it did not earn.

---

## The three-state verdict — `verdict.py`

`PASS` / `FAIL` / **`INVALID`**, and **a PASS is refused without a witness**.

`INVALID` means the check could not run in a state where it *could* have failed.
It never counts as a pass and it carries its own exit bit (+2), so a batch runner
can tell a broken instrument from a broken artefact.

Adopted because every false result in one run was a clean negative from a dead
instrument: a caption check reading the downloads block, a geometry check over
all-zero coordinates, an extractor that never unescaped XML, a liveness probe
querying a pool the seat never used. **None of those was a FAIL.**

---

## What each gate refuses

| Gate | Refuses | Blind to |
|---|---|---|
| `k_consistency_gate.py` | any k-carrying block or row-per-trial panel disagreeing with the outcome's k, unless declared `_STALE`; textual k in titles/prose | novel phrasings outside its noun list; subset phrases are *reported*, never failed |
| `identity_gate.py` | a pooled row with no registration, two rows sharing one, or a source document not containing the registration it is filed under | returns **INVALID** (not FAIL) when no staged document carries the registration — an unstaged trial is not a wrong one |
| `prose_claim_gate.py` | unhedged benefit claims against a null-containing interval; "X was not done" claims when the object contains X | fixed pattern lists — hedged wording passes *by design*, and a new way of asserting benefit will not be caught |
| `citation_year_gate.py` | an epub year recorded as the citation year; row/citation disagreement; an `epub_date` whose year equals the citation year | a wrong year with **no** `epub_date` recorded — it cannot check a year it has nothing to compare against |
| `figure_audit.py` | two figures sharing a normalised point pattern; a scatter not naming both axes; a caption promising a diagonal/null line/contours the SVG lacks | **the 1,217 Plotly corpus pages** — see below |
| `alignment_gate.py` | docmodel ↔ .docx ↔ page divergence in headings, captions, verbatim blocks, heading levels; and a presentation contract (serif body, line spacing, `tblHeader` on every table, no figure wider than the measure, no theme-accent table style) | anything with no docmodel — corpus pages have none |
| `denominator_axis_gate.py` | a page printing one denominator under another's name — the analysis set labelled "randomised", the enrolled total labelled "analysed" | a wrong number matching no stored axis (reported, never failed); a page with no `data-store` and no object path — **1,433 of 1,464 root pages**, so its zero there is NOT OBSERVED, not SAFE; a denominator claim with no person-noun in its sentence |
| `derived_recompute_gate.py` | a derived value that no longer follows from the current stored inputs — an NNT recomputed from a superseded risk difference, a leave-one-out block of the wrong arity, an estimator panel that does not reproduce its own headline | derivations absent from its declared table (**132 of 155 objects carry none**, so its zero there is NOT OBSERVED); a value stale in every surface at once; whether the authoritative operand is itself right |
| `contradicting_surfaces_gate.py` | two of our own surfaces asserting different values for one quantity — a trial pooled and recorded as excluded, an outcome both rated and pending, a search denied and held, an identifier both resolved and unresolved | prose contradictions sharing no identifier; **93 of 155 objects carry no screening block** so EXCLUDED_YET_POOLED is NOT_APPLICABLE there; k-vs-k, which is `k_consistency_gate.py`'s; both surfaces wrong the same way |
| `method_label_gate.py` | a method label the arithmetic does not support — a prediction interval labelled t on k-1 df and computed with a normal quantile, a review-level scale rendered over an outcome pooled on another | methods it cannot redo; a prediction interval with incomplete inputs (UNDETERMINABLE, never a pass); a page label naming no outcome when outcomes disagree. It detects a hand-typed label; it does not make the build emit one |
| `registration_chronology_gate.py` | screening decisions dated before the search that retrieved them, content dated before the protocol it claims prospectiveness from, and a prospective-registration claim over either — read from the object's own content, never from commit dates | a review recording no dates (**154 of 155**, so its zero is NOT OBSERVED); a date that is simply wrong — it checks ORDER, not truth; work done before any timestamp was written |
| `refusal_reads_outcome_groups_gate.py` | a refusal turning on arm identity that names no source table, names a trial-level one, or is contradicted by the object's own outcome-specific capture | refusals turning on anything but arm identity; whether the outcome-specific capture is itself right; **153 of 155 objects carry no such refusal**. It judges which table was read, not whether the contrast should pool |
| `lint_unordered_iteration.py` | `next`, `[0]`, and keyed `min`/`max` over a set, a glob or an `iterdir()` — a winner picked out of hash order. AST-based, so it sees the variable-bound form its regex predecessor reported `0 of 1407` on | a binding crossing a function boundary, a class attribute, a module global or a parameter; unordered sources not in its list; a file that will not parse (reported, never counted clean). Bare `min`/`max` with no `key=` is excluded and the exclusion is counted |
| `property_recompute_gate.py` | a page-standard `P*` property whose SERVED state disagrees with the same property recomputed from the object the page was built from | **only the 19 of 1,464 root pages carrying the property table**, and one of those (`ALIROCUMAB_LIPID_SSOT.html`) resolves to no object and is NAMED, never passed; it compares two states and does not decide which is right |
| `source_hierarchy_gate.py` | a disposition reading `hasResults=false` as an absence of RESULTS with no non-registry source named; a stored point declaring no analysis variant | it cannot see variant MIXING: **0 of 610 stored points declare a variant**, so that count is NOT_FOUND, not ABSENT. It chooses no sources and does not decide which variant is right |
| `refusal_reason_gate.py` | a non-pooling reason resting ONLY on grounds that do not hold — the unit being a pair, the direction inverted, a 99% interval | **17 reasons matched its key list across 152 objects**, so its reach is small and its zero is a statement about that reach; reasons phrased outside those keys; and it never fails a refusal that also names a valid ground — that case is reported instead, because failing it would push authors toward thinner reasons |
| `test_properties_can_refuse.py` | a `P*` property emitted so that no object could make it report anything but HELD; a property added with no planted defect | it proves each property CAN refuse, not that any particular refusal is correct |
| `test_source_hierarchy_refuses.py` | the registry outranking the primary publication for an effect VALUE; the registry losing precedence on pre-specification; a module unable to report registry-silence-as-absence | it tests the ordering, not any stored value — reversing an order re-extracts nothing |
| `.githooks/pre-push` → `regression_check.py` | 7 signals on the `*_REVIEW.html` pages the push touches | only pages the push changes; **no override exists and none should be added** |

---

## The blind spot that matters most for the 160-page programme

**`figure_audit.py` cannot audit the corpus pages.** They render with a local
Plotly bundle into `.chart-container` divs that measure **0×0** under headless
`file://`. The charts exist — three `<svg>` layers deep — and every coordinate
the audit would read is zero. A geometry check over zeros returns "0 collisions",
which is a pass produced by measuring nothing.

It therefore **refuses**:

```
UNAUDITABLE: 20 chart containers found, 19 have drawn SVG, and NONE has a
non-zero width ... Refusing to report a result rather than returning a clean one.
```

That is the correct behaviour, and it means **figure auditing of the 83
cardiology and 77 infectious-disease pages is not yet possible headlessly.**
Solving the 0×0 layout is the unlock. Do not "fix" it by relaxing the refusal.

Scope note, measured not assumed: the two shared-projector bugs fixed on ARNI
(the shifted `scatter_svg` argument tuple, the contourless funnel) do **not**
affect the corpus pages — 0 of 1,217 carry the signature. They affect pages built
by `ssot/projectors.py`, currently 12 SSOT objects, of which only ARNI is rebuilt.

---

## Publishing

- **Pages source:** branch `main`, path `/`, `build_type: workflow`.
  Confirm with `gh api repos/<owner>/<repo>/pages`, never assume.
- **Procedure that worked:**
  1. Build, run the full suite, and verify a corrected value **in the file you
     are about to publish** — not by filename.
  2. Copy the build to its served path (e.g. `ARNI_HF_REVIEW.html` at repo root).
  3. `git push origin HEAD:main` — a fast-forward; check
     `git rev-list --count HEAD..origin/main` is 0 first.
  4. **Fetch the live URL and quote a corrected value from the served page.**
     Deploys are asynchronous and took ~2 minutes here. A push that succeeded is
     not a page that updated.
- Placeholders must render honestly: the data-availability section shows
  `[persistent identifier not yet minted]`, never an empty field or a fake DOI.

---

## Supporting scripts

- `recompute_panels.R`, `recompute_counts.R`, `recompute_secondary.R` — metafor
  recomputation, each **gated on reproducing the stored values** for the withheld
  case; they refuse to write if they cannot.
- `make_prisma_checklist.py` — the completed PRISMA 2020 checklist as a
  deposit-ready artefact, item text quoted verbatim from BMJ 2021;372:n71.
- `scan_k_statements.py` — deliberately over-broad inventory of count statements;
  use for discovery, use the k gate for judgement.
- `DEFECT_CLASSES.md` — the four portable defect classes and the meta-lesson.

---

## The one rule behind all of it

**A check that cannot fail is not a check.** Before recording a pass, state what a
failure would have looked like on that instrument, then produce one. Every gate
here was falsified against a real broken artefact before being trusted — and the
pre-push regression gate had to be fixed twice: once because it could never fail,
and once because it failed on success.
