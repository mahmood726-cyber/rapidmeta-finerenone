# Blinded external-review harness — calibration and full-corpus sweep

> ## Read this before any number below
>
> **All four false-positive families found in this harness ran toward accusing the page.**
>
> Not one of them failed toward "the corpus is fine". An instrument built to find defects fails
> toward finding them: the bias follows the builder's intent, not the data. This is the mirror
> image of the failure mode we have been hunting all week, where broken instruments return good
> news — and it is harder to notice, because a check that is wrong in the direction of accusing
> its subject reads as the harness working.
>
> **Therefore: no detector's count is quotable until its precision has been measured against
> hand-read cases, and the direction of its errors recorded.** Every count in this report carries
> that measurement or is explicitly marked as not carrying one.

Harness `sweep-2026-08-27`. All verdicts measured against **served bytes** from
`https://mahmood726-cyber.github.io/rapidmeta-finerenone/` (Pages source = `main`, path `/`).
Every record carries the page's HTTP `Last-Modified` and a sha256 of exactly the bytes read.

**Denominator: 141 topic objects. 141 resolved to a delivered page and CONFIRMED by served bytes.
141 examined. 0 fetch failures. 0 dropped.**

Resolution was confirmed, never guessed — a candidate page was accepted only if the served bytes
declared the object's `app_id`, topic id, or exact title. Naming conventions do not resolve this
corpus (`arni-hfref` ships as `ARNI_HF_REVIEW.html`, `colchicine-intracerebral-haemorrhage` as
`COLCHICINE_ICH_REVIEW.html`), and guessing names is how a resolver silently shrinks its denominator.

---

## 1. Calibration against the three external reviews — MISSES FIRST

### Still missed (2 of 7)

| # | Review finding | Why still missed |
|---|---|---|
| 4 | **A denominator that survived the withdrawal of the analysis it described** | No detector built. Needs the visual-abstract N tied to the specific pool that produced it; the VA participant count is not machine-linked to a pool on these pages. |
| 6 | **"Four trials versus our two" — `k` conflated review-level with outcome-specific** | No detector built. Needs the published-comparison block parsed per outcome and matched to the same outcome in our own results. |

### Miss closed by the Codex/agy lane (1 of 7)

| # | Review finding | Result |
|---|---|---|
| 5 | Sources called unavailable whose full text is open | **CLOSED — 7 confirmed instances across 3 topics** (the reviews found 3). Marked abstract-only, full text open in PMC, three fetched and verified readable. Full method and denominators in §7. |

### Caught (3 of 7)

| # | Review finding | Verdict |
|---|---|---|
| 1 | Pooled estimates reproduce | **CONFIRMS — with a reach caveat.** 10 of 10 assessable pools reproduce exactly. Only 10 pools corpus-wide expose per-trial log-scale inputs in a parseable form; 160 are NOT-ASSESSABLE. This is *not* "arithmetic verified corpus-wide". |
| 2 | KCCQ axis said "lower is better" | **CAUGHT, already fixed** (`463c6d625`, 2026-08-26). Pinned as an immutable fixture pair. |
| 3 | "HKSJ" labels a modified interval | **CAUGHT, and the review overstated it.** Downgraded to QUALIFIED: the flooring *is* disclosed. 9 QUALIFIED, 0 FAIL corpus-wide. |

### Refuted by two independent families (1 of 7)

| # | Review finding | Verdict |
|---|---|---|
| 7 | Recurrent-event totals pooled with first-event times | **REFUTED for sotagliflozin.** Codex (openai) and agy (google), independently blinded on the same payload, both answered CROSS-POOL: YES *and* both said the distinction is stated plainly. The page keeps them as separate pools. |

**New finding from that lane, on which both families converged:** pool 1 (time-to-first) is not
established as estimand-uniform. Codex: NOT-UNIFORM ("the larger trial had the first-occurrence
composite as an exploratory endpoint, while the worsening-heart-failure trial had it as a regulator
analysis only"). agy: CANNOT-TELL, quoting the page's own "have not been shown to measure the same
quantity". The page discloses this — and still displays a pooled estimate for it.

---

## 2. The finding to lead with

Four pages state a value and, in the same continuous passage, state that the value was never
recorded. Verbatim, as a reader receives it on `SGLT2_MACE_CVOT_REVIEW.html`:

> **"Favours: the intervention (lower is better) not recorded on the page this object was extracted from"**

A confident directional claim, immediately followed by a statement that the direction was never
recorded. **Nothing in our checks would ever have flagged this, because both halves are individually
true.** Only adjacency makes it a defect.

Topics: `icosapent-lipid-auto-full-review`, `rosuvastatin-auto-full-review`,
`rotavirus-vaccine-africa-review`, `sglt2-mace-cvot-review`.

### A fixed renderer is not a fixed page

The root-cause fix `7f18a5da2` ("derive the direction-of-benefit label, never default it") **is on
`main` and is correct** — it maps every spelling and refuses when unknown. But the pages are
committed HTML. Of 19 topics whose object records no direction, **6 live pages still assert one**;
13 render none. The generator is fixed; six artefacts a reader receives were never regenerated.

Live inversions: **0**. `mavacamten-ohcm` is latent, not reader-facing — object says
`'higher is better'`, its result carries no `favours`, the render guard is `if res.get("favours")`,
and the live page contains zero occurrences of "Favours".

---

## 3. Full-corpus results, ranked by severity

Reader-facing falsehood outranks incompleteness. **82 FAIL/FLAG findings across 141 topics.**

| severity | check | topics | what it means |
|---|---|---|---|
| 100 | `self_refuting_claim` | **4** | states a value and denies it in the same passage |
| 95 | `arithmetic` | **0** of 10 assessable | every displayed pooled estimate that can be checked, reproduces |
| 90 | `rob_no_information` | **21** | "No information" rendered as a RoB 2 *domain judgement*, often with "Agreed: yes" |
| 85 | `falsy_render` | **21** | empty link + colon, empty link text, `?` as a value |
| 80 | `three_surfaces` | **3** | trials in the contributing table carry no displayed input |
| 70 | `nct_links` | **2** | NCT label links to an FDA PDF or PubMed, not the registry |
| 60 | `default_asserted` | **6** (FLAG) | page renders a direction the object does not hold |
| 50 | `method_label` | **9** (QUALIFIED) | floored HKSJ under a bare "HKSJ" row label; disclosed in prose |
| 45 | `rob_outcome_column` | **21** | RoB table lacks the result/outcome column; RoB 2 is per-result |
| 30 | `page_stamped` | **4** | no SHA-256 source stamp and no generation stamp |

`rob_no_information` (21) and `rob_outcome_column` (21) are **not** the same set — they differ by one
each way (`sotagliflozin-hf` only in the first, `arni-hfref` only in the second), so this is two
detectors agreeing on a real population, not one detector double-counted.

Largest single instances: `sglt2-hf` and `bococizumab-lipid-review` at 42 "No information" judgement
cells each; `iv-iron-hf` at 38.

---

## 4. Instrument honesty — four false-positive families caught by hand, not by the harness

Every one ran in the direction of **accusing the page**. That is the dangerous direction, because a
check that is wrong toward "the subject is defective" reads as the harness working.

1. **`direction_label` — retired from corpus reporting.** Measured precision **0 of 2**: both corpus
   FAILs were false positives. The first was a hierarchical win ratio, where the page correctly says
   *"values above one favour treatment — the opposite of every other ratio in this object."* **The
   second was caused by my fix for the first**: a passing mention of a different trial's win ratio,
   2500 characters away in the discussion, flipped the polarity override on `arni-hfref`, whose
   outcome is "Cardiovascular death or hospitalization for heart failure... as a hazard ratio" —
   where lower genuinely is better. A fix that reduced one class created an instance of it. The check
   is now ADVISORY and keeps its pinned control, which still proves it catches the real inversion.
2. **`falsy_render` — 33 → 21.** Twelve topics were pure false positives: the `?` characters were SVG
   risk-of-bias traffic-light glyphs (`<text>?</text>` in an amber circle), the conventional "unclear"
   marker, not values that failed to render. Counting them also *conflated a rendering defect with a
   methodological one* — RoB 2 has no "unclear" category, which is a different check's job.
3. **`method_label` — 2 FAIL → 0.** `malaria-vaccines` says *"This project's **floored**
   Hartung-Knapp interval at k = 2 is 0.0548 to 0.8566, on t = 12.7062 with 1 degree of freedom"* —
   a better disclosure than the reference page, because the caveat travels with the number. My
   phrase list missed it and read a correctly-disclosed page as a fabrication.
4. **My own gate manufactured its observation condition.** The first `direction_gate` hardcoded
   `res = {"favours": "treatment"}`, forcing the render condition for every outcome, and reported
   **104** defects. Keying it to the renderer's real guard gave 104 → 19 candidates → **6 actually
   reader-facing**. Reach reported as population, inside the script written to catch that error.

A fifth, caught only because two numbers disagreed: `run.py` crashed on a newly added status
**before** writing its output, so I tallied a **stale** `calibration.json` from the previous run. It
now deletes the output up front — absent beats silently-old.

---

## 5. Proof the instruments work in both directions

- **44 tests** across `test_bh.py` and `test_claims.py`. Every check PASSES on a clean fixture and
  FAILS on one carrying its own defect; planting one defect trips no unrelated check; a degeneracy
  guard asserts raw and floored HKSJ actually differ so the planted defect is plantable.
- **Mutation-tested.** Forcing `method_label` to always PASS, forcing `falsy_render` to always FAIL,
  and widening the arithmetic tolerance to 99 each turn the suite red.
- **Two real renderers, opposite exit codes.** `direction_gate` exercises the real
  `_favoured_arm` — it does not re-implement it. Against `origin/main` it exits **0**
  (21 PASS + 19 PASS-REFUSED); against the stale worktree it exits **1** (1 inverted + 19
  assert-from-absence). Same gate, same objects.
- **Positive controls keyed outside this system**: the KCCQ instrument definition, the
  ClinicalTrials.gov registered outcome text, and a verbatim passage a reader receives on a live page.
- Fixtures are synthetic or pinned to immutable git blobs, and built in memory. No control writes to
  a shared output path.
- `$?` was never read through a pipe. Every exit status quoted here is the real one.

---

## 6. Rubric additions adopted

- **Served bytes, always.** Every reader-facing claim is measured against the bytes a reader
  receives. A branch is not a deployment.
- **Regeneration.** For every fix claimed, is the artefact a reader receives actually regenerated?
  A fixed generator is not a fixed page.
- **Default-as-assertion.** A default is an assertion the object never made. Refusing to state a
  value is a first-class correct answer (`PASS-REFUSED`), not a gap.
- **Instrument self-check.** Does this instrument construct the condition it claims to observe?
- **Kinds before counts.** Enumerate the kinds of item in a population before reporting its size.

---

## 7. Availability sweep — the largest remaining review miss, now closed

**Result: 7 distinct sources across 3 topics are recorded as read from the ABSTRACT ONLY while
their full text is openly available in PubMed Central.**

| topic | PMID | open full text |
|---|---|---|
| covid19-vaccines | 33306989 | PMC7723445 |
| covid19-vaccines | 33545094 | PMC7852454 |
| covid19-vaccines | 34037666 | PMC8156175 |
| covid19-vaccines | 34826381 | PMC8610426 |
| iv-iron-hf | 37632415 | PMC10733736 |
| iv-iron-hf | 40159390 | PMC11955906 |
| sotagliflozin-hf | 39257196 | PMC11911574 |

The external reviews found three such instances. This sweep finds seven — same class, larger count.

**Verified, not inferred.** A PMCID alone can be an embargoed author manuscript, so three were
fetched directly: PMC11911574, PMC10733736 and PMC7723445 all return HTTP 200 with full
Methods/Results/Discussion sections present.

### Denominators, and what is NOT assessable

- **107** availability claims across **17 of 141** topics.
- **58** carry a PMID or DOI. **49 do not** — those are NOT-ASSESSABLE by this method, not clean.
- **26** distinct PMIDs resolved against the NCBI ID converter; 12 are in PMC.
- Marker kinds separated before counting, because they are three different things:
  - `ABSTRACT-ONLY` + in PMC → **14 claim occurrences, 7 distinct sources — the defect**
  - `ABSTRACT-ONLY` + not in PMC → 31 occurrences — **sound**, no open full text existed
  - `USED-FULL-TEXT` → 11 occurrences — **not a defect**; the page already used it

An earlier tally of this sweep said 18 because it counted `(abstract and full text, open)` as
abstract-only and did not deduplicate repeated PMIDs within a page. Enumerating the kinds before
reporting the number is what corrected it.

### Cross-family adjudication

Five blinded Codex jobs, one per topic, all foreground with stdin closed, all exit 0 with verified
bytes (530–2432). Codex independently reached SHOULD-HAVE-USED-FULL-TEXT on the same sources the
deterministic check flags.

**Caveat on the model's rationales, not its verdicts:** the payload truncated each page quotation at
230 characters, mid-word — Codex quoted fragments such as "The drug-spe,". The verdicts are driven
by the supplied PMC fact and stand; the quoted reasoning is degraded and should not be published.
This is the same defect class as showing a verifier different bytes from the ones it is judging.

---

## 8. The two remaining misses are a STRUCTURAL GAP, not a missing detector

`self_refuting_claim` works because the claim and its refutation are **adjacent in the rendered
text**. The two outstanding review findings have no such adjacency:

- **a denominator that survived the withdrawal of the analysis it described** — requires the visual
  abstract's participant count to be attributable to the specific pool that produced it;
- **`k` conflated between review-level and outcome-specific counts** — requires the published
  comparison to be attributable to a named outcome.

**These pages do not emit a link between a stated number and the pool it came from.** Any detector
built on proximity, ordering, or "the nearest table" would be a proxy, and tonight already showed
what proxies do: `direction_label` retired at precision 0 of 2, its second false positive caused by
the patch for its first.

**Design requirement, offered instead of a fragile detector:**

> Every reader-facing number that derives from a pool must carry that pool's identifier in the
> markup — e.g. `data-pool="hfcv_total"` on the visual-abstract N, the index-card k, and the
> published-comparison k.

With that one attribute, both classes become exact, mechanical checks with no natural-language
inference at all. Without it, they are not checkable, and saying so is worth more than a detector
at 50% precision.

---

## 9. Three sentences that must travel with the numbers

1. **"Arithmetic: zero failures" is true of 10 pools, not of the corpus.** Only 10 pools corpus-wide
   expose per-trial log-scale inputs in a parseable form; 160 are NOT-ASSESSABLE. Ten of ten
   reproducing exactly is a real and welcome result. *"Our arithmetic is verified corpus-wide"* is
   not what it says.
2. **`rob_no_information` (21) and `rob_outcome_column` (21) are not the same 21.** They differ by
   one each way — `sotagliflozin-hf` appears only in the first, `arni-hfref` only in the second. Two
   detectors agreeing on a real population is evidence; one number double-counted is an error, and
   in a table they look identical.
3. **The estimand refutation is a finding, not a null.** Codex (openai) and agy (google), blinded
   independently on the same payload, both found the recurrent-event and first-event pools kept
   SEPARATE and the distinction stated plainly. **Our estimand separation survives cross-family
   scrutiny.** Their convergent new finding is the more interesting half: pool 1 is not established
   as estimand-uniform, and the page pools it anyway *while saying so*. **A disclosed weakness is
   still a weakness; disclosure is not a fix.**

---

## 10. The general "does the object hold the value the page claims" sweep

Attacked at the root rather than the surface: an AST scan of the projector for every site where a
rendered value is **defaulted on absence**. `_favoured_arm` was one instance of a shape, not a
one-off.

**Scanner validated by the same two-tree proof as the direction gate.** Against the stale worktree
it finds `build_app_v2.py:269 field='direction_of_benefit'` — the known bug — and against `main` it
is silent, because the bug is fixed. It can both fire and stay silent on real inputs.

**113 python files scanned, 0 unparseable, 35 sites in three kinds.** A site is not a defect; a site
becomes a defect only when a reader receives its output.

| kind | n | shape |
|---|---|---|
| `OR-DEFAULT-CLAIM` | 20 | `get(F) or "a claim"` — absence *and every falsy value* render as the claim |
| `GET-DEFAULT-CLAIM` | 14 | `get(F, "a claim")` |
| `EXACT-TOKEN-ELSE-CLAIM` | 1 | the `_favoured_arm` shape, now only in `build_tabbed.py:1165` |

### Confirmed reader-facing defect: 1

**`sglt2-hf`, outcome `harmonised_cvdeath_or_hhf`.** The object stores `measure: "HR"` and **no**
`effect_scale`. The served page renders:

> **"Effect scale reported on the natural scale; nothing is pooled on this outcome"**

A hazard ratio is a log-scale quantity. The object never said "natural" — `outcome.get(
'effect_scale', 'natural')` supplied it. Both sibling outcomes on the same page, same measure,
store `'log'`.

**The default is the minority value.** Across the corpus the stored field is `log` 70, `natural` 10,
`linear` 2, `none` 1. So absence renders as the *less likely* truth, which is the worst possible
choice of default for a statistical claim.

### Denominators, and the error I made getting to them

- 174 outcomes; **91 lack `effect_scale`**.
- But only **2 topics** with a missing `effect_scale` render a scale claim at all; 86 render none.
- Of those 2, **1** renders a false one. `fcm-hf-review` renders only a `log` claim, which the
  default cannot produce.

My first measurement said **861 blocks across all 141 topics**. It was counting effect-like dicts,
while the code reads `outcome.get(...)` — the *outcome* dict. I caught it by reading the call site
before publishing the number. Same self-check as before: does this instrument construct the
condition it claims to observe?

### Latent sites worth a generator fix, ranked

None of these are confirmed reader-facing; they are loaded guns.

1. **`apply_breadth_and_tigecycline_disclosure.py:183`** — `get('ci_low', '0.8327')` and
   `get('ci_high', '1.0501')`. **A numeric confidence interval defaulted to hardcoded bounds.** If
   the field is ever absent, a reader receives a specific interval that came from nowhere.
2. **Mutually inconsistent estimator defaults for the same concept.** `validate_v2.py:1834/1839`
   default `estimator_used` to `'DerSimonian-Laird'`; `validate_v2.py:3564` defaults it to
   `'REML'`; `build_app_v2.py:126` defaults `estimator` to `'Hartung-Knapp'`. Three answers to one
   question, all produced by absence.
3. **`apply_reml_corpus.py:335/382`** — `get('environment') or 'R version 4.6.0 (2026-04-24 ucrt);
   metafor 5.0.1'`. A **provenance** claim — the exact software that produced a number — manufactured
   from an absent field. Only 24 objects carry `environment` at all.
4. **`build_app_v2.py:1125`** — `get('subgroup_heading', 'By age stratum')` asserts *what a subgroup
   is* when unknown. Exactly one object in the corpus carries the field.

Honest placeholders were excluded before counting, not after: `get('k', 'an unstated number of')`,
`get('checked_utc') or 'an unrecorded date'` and `get('quote') or '[nothing to quote: the item is
absent from the paper]'` all say plainly that they do not know, and are not defects.

### Why this class needed the root-cause attack

Every instance is invisible to a store-reading check by construction — the store is *correct*, it
records that it does not know. And it is nearly invisible to a page-reading check too, because the
rendered sentence is grammatical, plausible, and in the majority of cases even true. Only the
projector source shows where a claim can be born from nothing.

---

## 11. The reverse scan — values that look configurable but have one possible outcome

Same file set, same parse, opposite shape. `projector_defaults.py` finds values *supplied* where the
object holds none; `frozen_literals.py` finds seams that cannot vary.

**FROZEN-PARAM: 0 across 113 files** — no claim-bearing parameter default that no caller overrides.

**That zero is trustworthy because the detector is proven to fire.** Planted a function whose
`estimator` parameter defaults to `"DerSimonian-Laird random-effects model"` with callers that never
override it → the scan reports it. Added a caller that passes `estimator=obj["estimator"]` → the
scan goes silent. A detector that has only ever said PASS is not a detector; this one has said both.

**HARDCODED-CLAIM: 76**, and the kinds were enumerated before the number was read:

| kind | n |
|---|---|
| one-off `apply_*` / `add_*` migration scripts | 61 |
| other tooling | 8 |
| **live projector** | **6** |
| regex literal (false positive) | 1 |

Of the 6 in the live projector, **4 are docstrings** and **2 are correct branches** of a model-name
normaliser (`"a random-effects model"` / `"a fixed-effect model"`), driven by the stored `model`
value and falling through to `return t` on anything unrecognised.

**No frozen literal reaches a reader.** This is a clean negative, and it is worth as much as a
finding because it was earned by a detector that can fail.

### 35 sites is not 35 defects

Honest placeholders were excluded **before** counting, not after — `get('k', 'an unstated number
of')`, `get('checked_utc') or 'an unrecorded date'`, `get('quote') or '[nothing to quote: the item
is absent from the paper]'`, `get('started_at') or 'a starting level this review does not record'`.
Each says plainly that it does not know. **A default that declines to assert is the system working.**

Converting the 35 sites to reader-facing defects gives **2**: the `effect_scale` falsehood on
`sglt2-hf`, and the unmade `subgroup_heading` claim on `prevnar15-pneumo`.

### A correction to my own ranking

I ranked `get('ci_low', '0.8327')` / `get('ci_high', '1.0501')` as the most dangerous item in the
corpus — a confidence interval defaulting to hardcoded bounds, undetectable downstream.

**It is inside a `print()`.** It reaches an operator's console, never a page. The script is a
one-off migration, already applied, referenced by nothing. Not reader-facing, not a loaded gun.

That makes **five** inflated first-counts I have caught in my own work tonight — 104→6, 861→1,
33→21, 18→7, and this one — every single one in the direction of accusing the page, and every one
caught by reading the call site or the served bytes before publishing. The header of this report is
not a general observation. It is a description of this harness's specific failure mode.

---

## 12. Visual-abstract denominators — and a third class blocked by the same missing surface

### `data-pool` is genuinely unmet

Checked before proposing it again: across all 141 served pages there is exactly **one** `data-*`
attribute in use — `data-fw="fit"`, a formatting hook, 240 occurrences. **Zero pages carry an
attribute whose value equals an outcome id.** 64 pages produce a substring match, and all 64 are
coincidental. Nothing equivalent already exists.

### CONFIRMED reader-facing falsehood: `iv-iron-hf`

The page carries **four** visual abstracts, one per outcome — recurrent HHF with CV death, time to
first CV death or HHF, recurrent HHF alone, and all-cause death. **Every one states "2 trials,
6,716 participants".**

6,716 is the sum across **all six pools**: 2,245 + 1,105 + 0 + 0 + 3,065 + 301. The 2-trial pool
each visual abstract actually names holds **2,245** (AFFIRM-AHF 558/550, IRONMAN 569/568) or
**1,105**. The total silently absorbs HEART-FID (3,065) and CONFIRM-HF (301) — single-trial pools
for entirely different outcomes.

This is the rubric's named class, verbatim: *the participant count must equal the sum of analysed N
over the trials contributing to THAT outcome, not a page-level total across all trials on the page.*
It tells a reader that a two-trial result rests on three times the evidence it does, four times over.

The claim is also self-inconsistent on its face: two heart-failure trials totalling 6,716 analysed
participants would be remarkable, and AFFIRM-AHF plus IRONMAN is 2,245.

### FLAG, not FAIL: `bococizumab-lipid-review`

VA states 6 trials / 4,252 participants; the 6-trial pool sums to **3,969** analysed. A 283
difference. The visual abstract does not say whether its count is randomised or analysed, and those
legitimately differ — so this is reported as **FLAG**. Asserting a defect I cannot establish is the
accusatory direction this harness fails in, and it is not worth another instance.

### Denominators

| status | n | meaning |
|---|---|---|
| PASS | 9 | VA count equals the analysed N of the pool it names |
| FAIL | 4 | all four `iv-iron-hf` visual abstracts |
| FLAG | 1 | `bococizumab-lipid-review`, reason undetermined |
| NOT-ASSESSABLE | 132 | **the page carries no VA participant count at all** |

**Only 11 of 141 pages carry the surface this check reads.** Nine of eleven are correct.

Proven both ways in `test_surfaces.py` (8 tests): a VA matching its own pool passes; a VA carrying
the all-pool total fails with the defect named in the message; a plain mismatch is FLAG not FAIL; a
VA naming a trial count no pool has is NOT-ASSESSABLE.

### Three-surface set equality: NOT BUILT, and why

Two attempts, both fragile proxies, neither shipped:

1. matching a plot to a pool by **label overlap** matched every plot to pool 0, then reported the
   mismatch it had itself created;
2. matching by **document position** collapsed every plot onto the nearest table, which on a
   multi-pool page is the last one.

The obstacle is not the matching rule. Forest plots key rows on a trial short name
(`soloist-whf`) on some pages and a registration id (`NCT02540993`) on others, while
contributing-table cells carry the trial name followed by explanatory prose (`CONFIRM-HF the
trial's own primary …`). No normalisation reconciles them without guessing, and **nothing on the
page states which pool a plot belongs to.**

I stopped after two rather than tuning a third time. `direction_label` retired at precision 0 of 2
is what a proxy costs, and its second false positive was caused by the patch for its first.

**The weaker two-surface form is built and does work** — `bh.chk_three_surfaces`, contributing table
versus pooled computation, which found 3 real failures.

**So the `data-pool` requirement now unblocks three classes, not two:** the withdrawn-analysis
denominator, outcome-specific `k`, and three-surface set equality.

### New rubric class: correct-by-coincidence defaults

`subgroup_heading → 'By age stratum'` on `prevnar15-pneumo` is **accurate today by luck**. The
object never declared the stratification; the strata simply happen to be age bands. It produces no
wrong page and no alarm, and it will become wrong silently the first time a non-age subgroup
arrives. **Undetectable by any output-based check by definition** — the output is correct. Only the
projector source shows the claim was never made.

---

## A `<script>` block is not page content

Two independent lanes produced a headline finding from one unstripped tag on the same night:

- **here** — "six DTA reviews carry genuine results". The matches were template source:
  `'+pct(pooled`, `"+fmtNum(qSpec`, `'+chip+'`.
- **the store-side lane** — "870 pages publish adverse claims about other people's trials",
  which nearly bought a mass deletion. Also strings inside `<script>` that render nowhere.

**Any instrument that reads served bytes must strip `<script>` and `<style>` bodies and HTML
comments before counting anything.** Stripping tags alone leaves JavaScript in the text.

### And the second cause, which the first fix hides

Stripping `<script>` here **did not move the count**. The pattern still matched narrative
prose — *"Sensitivity ~96-100%"* — while the result table beneath read an em dash.

**A defect can have two independent causes that each look like the whole cause. Fixing one
leaves the number unchanged, which reads as confirmation.** That is nastier than either bug
alone, and the only defence is to hand-check the survivors rather than trust the pass.

The verdict now requires both: **a value WITH AN INTERVAL, and NO EMPTY RESULT SLOT.** A page
can carry a real interval in its narrative while its own result table reads `-`, and the `-`
is what a reader meets where the answer belongs. The reader's position is the vantage.

### A number with a known one-sided error is worth more than one that happens to be right

Across three revisions of the instrument and three revisions of the other lane's input, the
hollow-subject count moved 727 -> 727 -> **733**. It only ever rose, because both bugs moved
pages OUT of the hollow column and never into it. **That is why it stayed quotable while
every figure around it changed.**

---

## FINAL — the honest size of the corpus

Of **792 legacy pages a reader can reach, 2 survive a verdict that requires a real reported
result** — and both are furniture: a withdrawal log, and one other. Six diagnostic-accuracy
pages that I reported as "the real audit gap" carry **4 empty result slots each and 0 interval
estimates**; that claim is **withdrawn**.

**733 of 755 subjects appear covered and are not.**

**The honest size of the corpus is ~141 attributed reviews. Everything outside them is
furniture.**
