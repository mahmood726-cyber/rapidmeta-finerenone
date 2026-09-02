# Defect Class Register

Opened 2026-09-02 and committed before any fix in this lane, so it could not be trimmed to
match what was achieved. Extended 2026-09-03 with reviews 9-15. Rows are added when a class
is identified and never removed when one turns out to be hard.

**Fifteen independent external reviews of fifteen different pages. The arithmetic
reproduced every time except once.** That once is why this register changed shape:
ceftaroline put a wrong number in a headline. Selection and description are still where
almost everything fails, but FIX α is no longer hygiene.

Every claim is marked **MEASURED** (a command was run; output committed under
`scripts/baselines/`), **INFERRED** (follows from code read, not executed), or **CLAIMED**
(asserted by a review, not yet checked here).

## Denominators

MEASURED, `scripts/measure_defect_classes.py`:

| population | n | is it the served surface? |
|---|---:|---|
| all HTML deployed by the Pages workflow | 2228 | published, reachable by URL |
| **root-level `*.html`** | **1464** | **yes -- the page denominator** |
| `out/` | 190 | adjudication + withdrawal artefacts |
| `outputs/` | 327 | of which **319 are `*backup*`: ARCHIVE** |
| other subdirectories | 247 | not reader pages |

1464 + 190 + 327 + 247 = 2228. Two further denominators: **152 topic objects** resolved by
`ssot/PAGE_MAP.json`, and **155 canonical objects** under `ssot/`. Of the 1464 served
pages, **19 carry the page-standard property table**.

## SCREEN is not CONFIRMED, and NOT-CHECKABLE is not a pass

A screen is an upper bound from string co-occurrence. It is not a finding. Both rules were
earned here. The first `not drawn` screen returned **151 pages** and every hit was
`GOSH plot -- not drawn at this k`, a **correct refusal**. And the first version of the
two-trial measurement below folded 128 objects that record no `k` into "checked", which
would have reported 146 checked against 13 contradicting -- reading 128 unreadable objects
as agreement.

---

# FAMILY 1 -- CHECKS WHOSE GREEN MEANS NOTHING

The most important family, and its members are one defect at four altitudes. Grouping them
is the point: it makes FIX β's justification structural rather than anecdotal.

| id | class | emitter | status | blast radius | date |
|---|---|---|---|---|---|
| B1 | A `P*` property ASSERTED `HELD`, computed from nothing that could contradict it | `ssot/build_to_standard.py` -> `ssot/page_properties.py` | **FIXED** | **MEASURED: 11 flips on 10 of the 18 served pages whose object resolves** | 2026-09-02 |
| B2 | `P1_executed_search` **HELD** on a page whose own prose says **"No systematic search was run"** | the banner at `ssot/projectors.py:545` reads `search.strategy`; P1 reads `search.databases` -- two keys on one block, nothing asserting they agree | OPEN | **MEASURED: 17 of the 19 marker pages (89%).** Reviewers named azilsartan and bempedoic; the corpus-wide figure is new here | 2026-09-03 |
| B3 | **A GATE THAT IS OPT-IN IS NOT A GATE.** Hooks run only where `core.hooksPath` is set by hand, so a fresh clone is ungated and the lanes that arm their hooks inherit the defects of the lanes that did not | `.githooks/README.md`, `gates/WHAT-REMAINS-DISCIPLINE.md:104` | OPEN -- trunk-clearing lane | CLAIMED by that lane: three sequential blockers in one day, none of them theirs | 2026-09-03 |
| B4 | **A CHAIN THAT SHORT-CIRCUITS AT THE FIRST REFUSAL** reports a property of its first check only | hook chain runner | OPEN -- same lane | caused two false "the sibling lane cleared it" reports | 2026-09-03 |
| B5 | **A GATE THAT WOULD REFUSE A COMMIT, ON A COMMIT ALREADY LANDED** -- the password class in infrastructure form | trunk | OPEN | the gate names the introducing shas itself: `e1ccb9f9c`, `66c1ed934` | 2026-09-03 |

> **B1 and B3-B5 are one shape.** A property that can only report HELD, a gate that runs
> only where someone opted in, and a chain that stops at its first refusal are all checks
> whose green is a statement about the checker rather than about the thing checked.

---

# FAMILY 2 -- FIX α: THE SOURCE HIERARCHY

**PRIMARY PUBLICATION -> SUPPLEMENT / SAP / PROTOCOL -> REGISTRY.** Landed for the value
question; the registry keeps precedence on pre-specification. Three rules sit under it, and
reviews 9-15 supplied the evidence for all three:

> ***THE SAME ENDPOINT TITLE IS NOT THE SAME ANALYSIS.***
> ***THE SAME COMPARATOR NAME IS NOT THE SAME COMPARATOR.***
> ***SEARCHING EVERY RANK WITHIN A REGISTRY IS NOT SEARCHING EVERY RELEVANT OUTCOME.***

| id | class | status | blast radius | date |
|---|---|---|---|---|
| A1 | `hasResults=False` read as "no results exist" | PARTIAL, gated | MEASURED: 2 dispositions on 1 of 152 topics | 2026-09-02 |
| A2 | An effect carries its endpoint NAME but not its ANALYSIS VARIANT | PARTIAL, gated | **MEASURED: 610 stored points on 51 topics declare no variant; ZERO declare one**, so variant mixing is NOT_FOUND, not ABSENT | 2026-09-02 |
| **A6** | **A NUMERATOR FROM ONE POPULATION OVER A DENOMINATOR FROM ANOTHER** | OPEN | **THE FIRST WRONG NUMBER TO REACH A HEADLINE.** ceftaroline FOCUS 2 stores `235/315` where the publication reports `235/289` -- 315 is the treated-arm total, 289 the MITTE denominator. `74.6%` stored against `81.3%` published. Correcting FOCUS 2 alone moves the headline `RR 1.1048 -> 1.0945` | 2026-09-03 |
| **A7** | **A FALSE UNRECOVERABILITY CLAIM** -- "not recoverable from aggregates" / "requires patient-level data" where the sources print it | OPEN | **2 sightings, both cost evidence.** cangrelor: PHOENIX's three-component result is subtraction from the FDA table (`230/5470` vs `286/5469` once ST is removed) -- an "it cannot be done" claim that discarded an 11,000-patient trial. ceftaroline: CE and MITTE are declared CO-PRIMARY and both are published | 2026-09-03 |
| **A8** | **COMPARATOR ROLE TAKEN FROM A LABEL, NOT THE PROTOCOL** | OPEN | **2 sightings.** CHAMPION-PLATFORM was cangrelor **vs PLACEBO** during PCI; our page says "cangrelor against clopidogrel on all three" and is titled that way. First sighting: apixaban, where enoxaparin 30 mg BD and 40 mg OD were treated as one comparator. Also ceftriaxone 1 g vs 2 g, and clarithromycin on day 1 in FOCUS 1 only. Populations differ too: stable angina ~15% / 5% / 58%; STEMI excluded from PLATFORM | 2026-09-03 |
| **A9** | **REGISTRY-RANK COMPLETENESS MISTAKEN FOR OUTCOME COMPLETENESS** | OPEN | bempedoic: CLEAR Serenity's registry lists no MACE; its **primary publication reports adjudicated MACE `9/234` vs `0/111` with components**, all nine meeting the four-component definition. Not a reconstruction | 2026-09-03 |
| **A10** | **REGISTRY-ONLY EXTRACTION SERVING OUTDATED EVENT DATA** | OPEN | CAB-LA: one infection in each pivotal trial was later adjudicated baseline-prevalent. `13/4` should be `12/3`; `RR 0.208 -> 0.176`. The publications and regulatory review carry corrected counts, person-years, HRs, randomisation, masking, adjudication and adherence -- all declined, then recorded as "no information" in RoB | 2026-09-03 |
| A3 | A REGISTRATION rendered as a PUBLICATION | NOT FIXED | not measured | 2026-09-02 |
| A4 | Blinded-adjudication facts missed by reading registry fields only | NOT FIXED | subsumed by A10 | 2026-09-02 |
| A5 | AMPLIFY `61/76` impossible reconstruction | NOT FIXED | 1 page CLAIMED | 2026-09-02 |

> **The case for FIX α in one sentence, from review 13:** one registry denominator mismatch
> propagated cleanly through perfectly correct meta-analytic arithmetic and produced a
> polished but wrong headline number.

---

# FAMILY 3 -- OUR CORRECTIONS ARE EMITTERS TOO

> ## ***A FIX IS AN EMITTER TOO. A WITHDRAWAL IS A CLAIM ABOUT OUR DERIVATION, NOT ABOUT THE WORLD.***

| id | class | status | blast radius | date |
|---|---|---|---|---|
| **W1** | **CONFLATING "OUR DERIVATION IS INVALID" WITH "THE EFFECT IS UNSUPPORTED"** | OPEN -- **template rule to be written before the next withdrawal** | cangrelor: we published "the correction reverses the conclusion" and "the trials' own primary outcomes do not establish a benefit". The stored 2x2 was corrupt -- mortality numerators over composite denominators -- and **the withdrawal was RIGHT**. But `OR 0.81 (0.71-0.91)` is independently correct and reproduces the prespecified patient-level Lancet analysis at n=24,910. **A false warning discredits the true ones** | 2026-09-03 |
| **W2** | **A CORRECTION THAT INTRODUCES A NEW ERROR** | OPEN | the same cangrelor fix replaced a corrupt k=3 with a k=2 pool that wrongly discards CHAMPION-PHOENIX, justified by A7 | 2026-09-03 |
| **W3** | **A CLEAN RESULT FROM AN UNVALIDATED HARNESS** | OPEN | the gate lane retracted a real diagnosis after a "clean" reproduction whose harness set an extra variable that MASKED the behaviour -- **the withdrawal was the error** -- and its diagnostic then flipped a clone to `core.bare`. **Rule: probes belong on a throwaway copy** | 2026-09-03 |
| **W4** | **A LESSON LEARNED AT THE INSTANCE AND NOT AT THE CLASS** | OPEN | bempedoic excluded CLEAR Harmony for "no MACE outcome", found the registry DOES list adjudicated MACE, corrected the reason to population -- **then repeated the identical error on Serenity by staying inside the registry** | 2026-09-03 |

---

# FAMILY 4 -- PRESPECIFICATION, THE THING WE SELL

| id | class | status | blast radius | date |
|---|---|---|---|---|
| **P1x** | **THE EXECUTED ANALYSIS DOES NOT FOLLOW OUR OWN STORED PROTOCOL** | OPEN -- **highest-value remaining gate; fully oracle-free, both sides in our repo** | CAB-LA: the protocol says log-HR scale, DerSimonian-Laird, HKSJ t(k-1) primary; the page serves crude risk ratios, REML, ordinary Wald primary with HKSJ demoted to sensitivity. **No amendment recorded for any of the four.** The estimand also drifted across our own git history: the benchmark records `HR 0.22, DL log-HR, two primary publications`; the page serves `RR 0.208, REML, registry-only` | 2026-09-03 |
| **P2x** | **THE LINKED PROTOCOL IS FOR A DIFFERENT QUESTION** | OPEN | ceftaroline's protocol covers "Adults registered for MRSA", allows placebo or any active comparator, any primary outcome, and includes an observational study. **Worse than P1x: there the protocol was ignored; here it is not this review's at all** | 2026-09-03 |
| **P3x** | **WE REPLACED THE TRIALS' PRESPECIFIED FRAMEWORK WITHOUT JUSTIFYING IT** | OPEN | all three ceftaroline trials are non-inferiority with a `-10 pp` risk-difference margin; we substituted a superiority-oriented risk-ratio headline. Corrected RDs: MITT `+8.48 pp (-1.82 to +18.77)`, CE `+7.85 pp (-1.21 to +16.91)` -- both lower limits above `-10 pp`. **The defensible statement is "non-inferiority is supported; superiority is not robust under our own conservative rule", and we said neither** | 2026-09-03 |
| **P4x** | **A DECLARED METHOD CONTRADICTED BY ITS OWN USE** | OPEN | ceftaroline: the house variance-floor rule gives `RR 1.1048 (0.9868-1.2371)`, **crossing 1**, while GRADE's "no imprecision downgrade" is justified on the UNFLOORED HKSJ `1.0356-1.1787`. A policy is a claim; reaching a verdict on a different variant is the same class as a refusal with a false reason | 2026-09-03 |
| **P5x** | **A PROTOCOL-PROVENANCE CONTRADICTION** | OPEN | **4 sightings.** A page says the object cannot establish linkage to a protocol or its prospective status, then speaks as though prespecification IS established. **Correct form: "no prespecified moderator is established in the current review record."** Related: CAB-LA says the protocol "was first committed later" when git shows review, protocol and benchmark in the SAME commit -- the honest statement is *"git history does not demonstrate prospective prespecification"* | 2026-09-03 |

> **A silent estimand drift with a protocol on file is worse than having no protocol.** It
> converts our central claim into the thing a reviewer can disprove fastest.

---

# FAMILY 5 -- ELIGIBILITY DEFECTS IN THE SCHEMA ITSELF

Design, not slips: each fires every time.

| id | class | status | blast radius | date |
|---|---|---|---|---|
| **E1** | **EFFECT MEASURE AS A POST-HOC ELIGIBILITY CRITERION** (`effect_measure = HR`) | OPEN | a randomised trial becomes ineligible for supplying arm-level events instead of a hazard ratio. **Effect measure determines the synthesis method, not whether a trial addresses the PICO.** This is M6 promoted into the schema, so it fires every time | 2026-09-03 |
| **E2** | **AN ELIGIBILITY CRITERION DERIVED FROM THE INCLUDED SET** | OPEN | bempedoic's two-arm design criterion was reverse-engineered from the already-included trial. Circular: it cannot exclude anything the set does not already exclude | 2026-09-03 |
| **E3** | **A QUERY FILTER ABSENT FROM THE DECLARED ELIGIBILITY** | OPEN | the registry query restricts to `PHASE3, PHASE4`; the declared eligibility contains no phase restriction | 2026-09-03 |
| **E4** | **THE DECLARED POPULATION IS NOT THE ANALYSED POPULATION** | OPEN | **AGYW is 15-24 by the UNAIDS definition; the two pooled trials enrolled 18-45**, and the estimate is dominated by women 25+ where efficacy is greatest. ASPIRE prespecified `<25: 10% (-41 to 43)` against `>=25: 61% (32-77)`, interaction p=0.02; WHO records efficacy NOT demonstrated at 18-24. Our public sentence says "about 30% less likely to get HIV" on a page named for AGYW. **Our own indirectness note is half right: it names the under-18 gap and misses that 25-45 is also outside AGYW and is driving the estimate.** THE ERROR FLATTERS US, which is the kind intuition will not catch | 2026-09-03 |
| E5 | Eligibility criteria absent, so an exclusion cannot be justified | OPEN | ceftaroline: the paediatric RCT `NCT01530763` cannot be justifiably excluded; on the literal PICO it is ELIGIBLE, and an all-age k=4 pool gives `RR 1.093 (1.021-1.170)`, `I² 52.6%` | 2026-09-03 |

---

# FAMILY 6 -- FALSE ABSENCE CLAIMS

Distinct from A7: these are absences asserted about documents **we ourselves hold**.

| id | class | status | blast radius | date |
|---|---|---|---|---|
| **N1** | **AN ABSENCE CLAIM CONTRADICTED BY OUR OWN OBJECT** | OPEN -- oracle-free | CAB-LA: "the protocol prespecifies no moderator" is FALSE -- it prespecifies subgroup and meta-regression by population and region; "no risk-of-bias assessment is recorded" is FALSE -- the page carries a complete two-assessor RoB table. "No RoB recorded" beside a full table: **3 sightings** | 2026-09-03 |
| **N2** | **A FALSE ABSENCE ABOUT THE LITERATURE** | OPEN | **5 sightings.** bempedoic claims no independent synthesis of its estimand exists -- three do. ceftaroline claims no synthesis pools its three trials -- a 1,916-patient IPD meta-analysis of exactly those registrations exists (`MITT OR 1.66`, `CE OR 1.65`), and our own corrected aggregate reproduces it. AGYW claims its estimate is unreplicated -- USPSTF pooled the same two RCTs at `RR 0.71 (0.57-0.89)`, `I²=0%` | 2026-09-03 |
| **N3** | **AN OMISSION BY THE REVIEW, REPORTED AS AN ABSENCE IN THE EVIDENCE** | OPEN | harms unsynthesised on **7 pages**; absolute effects called unavailable when every publication prints them, **4 sightings**. cangrelor: PHOENIX GUSTO bleeding `857/5529` vs `602/5527`, patient-level mild bleeding `16.8%` vs `13.0%`, and absolute `3.8%` vs `4.7%` are all published | 2026-09-03 |

---

# FAMILY 7 -- CONTRADICTORY AND STALE SURFACES

One shape: two surfaces from different sources with nothing asserting they agree.

| id | class | status | blast radius | date |
|---|---|---|---|---|
| C-shape | Two surfaces rendered from different sources, unreconciled | PARTIAL, gated | **MEASURED: 1 FAIL of 155 objects** | 2026-09-02 |
| **C7** | **A HARDCODED TOPIC-SPECIFIC SENTENCE EMITTED CORPUS-WIDE** | OPEN | **MEASURED: `ssot/projectors.py:545` writes "the included set is a named two-trial programme" onto 146 of 1464 served pages. 18 are checkable; 13 of those 18 contradict their own k** (k = 1, 3, 4, 5, 6, 7, 8). 128 record no `k_included_in_object` and are NOT CHECKABLE -- not passes. This is the "stated trial count contradicts actual k" class (**5 sightings**) with its emitter located | 2026-09-03 |
| **C8** | **INTERNAL LANE COMMENTARY ON A READER SURFACE** | OPEN | **4 sightings, running both ways.** CAB-LA carries model commentary about assessor behaviour across 22-23 other topics and about the gepotidacin review; ceftaroline carries "Class 94", AGYW/CAB text and 239/243 model-audit output. First sighting where INTERNAL DIAGNOSTIC OUTPUT reached a reader. **A different emitter from the ungated `else`** | 2026-09-03 |
| **C9** | **MUTUALLY EXCLUSIVE STATEMENTS OF THE SAME FACT ON ONE PAGE** | OPEN | AGYW carries three search statements at once: "No systematic search was run", a documented 30 Aug 2026 PubMed/Europe PMC/registry search of >1,400 records, and "No bibliographic search" -- plus source counts that disagree (Europe PMC 1000/1443 vs 1443; PubMed 374 vs 372). cangrelor carries four analysis states at once: a withdrawn k=3, an undeclared k=2, a forest-plot area, and text saying nothing is pooled | 2026-09-03 |
| **C10** | **A VISUAL FALSEHOOD** | OPEN | the ceftaroline forest plot draws all three study squares the SAME SIZE although the inverse-variance weights differ materially. **A figure that misrepresents weighting is a false statement a reader cannot check by reading the numbers** | 2026-09-03 |
| C1 | Certainty "pending" and graded at once | OPEN | 2 sightings, incl. LOW and VERY_LOW simultaneously, and a GRADE row contradicting the RoB summary directly beneath it | 2026-09-02 |
| C2 | "not drawn" beside a figure caption for THAT figure | OPEN | **6 sightings**, incl. funnel "not drawn" beside "Figure 2. Funnel plot". The page-level screen returns 151 and is WRONG -- those are protected refusals | 2026-09-02 |
| C4 | `NOT READY` beside `Publishable: True` | OPEN | 2 sightings, one with `criteria_predefined = FAIL` | 2026-09-02 |
| C6 | RoB "assessors disagree" beside a displayed agreement rate | OPEN | **4 sightings**: `15/15`, `8/10 = 80%`, `3/5 = 60%`, `9/15 = 60%` | 2026-09-02 |
| C11 | Canonical-object contradiction | OPEN | **5 sightings** | 2026-09-03 |
| C12 | Provenance contradiction on ONE ROW: "DERIVED by us" directly above "READ, not derived" | OPEN | **4 sightings**; the class our landed `e1ccb9f9c` targets | 2026-09-03 |

---

# FAMILY 8 -- DENOMINATORS AND UNITS

| id | class | status | blast radius | date |
|---|---|---|---|---|
| D1/D4 | Randomised / analysed axis conflated | PARTIAL, gated | MEASURED: 1 FAIL of 1464; 4 pages NAMED as unjudgeable | 2026-09-02 |
| **D6** | **ENROLLED / RANDOMISED / TREATED / mITT CONFLATED** | OPEN | **6 sightings.** cangrelor: the regulatory summary gives PCI 8,846 / PLATFORM 5,346 / PHOENIX 11,145 randomised; publications say 8,877 enrolled and 5,362 randomised. Carrying `8,882` / `5,364` under "Randomised" is undefensible without reconciliation | 2026-09-03 |
| **D7** | **UNIT MIXING IN ABSOLUTE EFFECTS** | OPEN | AGYW applies a CUMULATIVE risk ratio to a baseline expressed as `4.5 infections per 100 woman-years` and derives an annual `NNT ~ 75`. **Incidence rates and cumulative risks are not interchangeable** -- the same family as the HR-as-RR defect | 2026-09-03 |
| **D8** | **HARMS COUNTS THAT DO NOT MATCH THE PUBLICATIONS, AND A CAUSAL CLAIM INFERRED FROM THE RATES** | OPEN | AGYW reports ASPIRE SAEs `116/1313` vs `130/1316`; the paper reports participants with any SAE `52/1313` vs `48/1316`. Ring: registry `41/1306` vs `9/652`, published `38` vs `6`. **The page then infers "a difference in what was counted, not in what happened" FROM THE RATES ALONE** -- an unsupported causal claim about provenance | 2026-09-03 |
| D5 | A missing denominator filled with a ZERO | NOT FIXED | SCREEN: 12 served pages | 2026-09-02 |

---

# FAMILY 9 -- METHOD AND JUDGEMENT

| id | class | status | blast radius | date |
|---|---|---|---|---|
| M-label | A method LABEL naming an analysis the numbers were not produced by | PARTIAL, gated | MEASURED: 3 FAIL of 155 | 2026-09-02 |
| M-derived | A derived value that is a SNAPSHOT of superseded operands | PARTIAL, gated | MEASURED: 2 FAIL of 155 | 2026-09-02 |
| M3 | Imprecision downgraded on STUDY COUNT | OPEN | **4 sightings** | 2026-09-02 |
| **M7** | **A METHOD ARTEFACT READ AS A FACT ABOUT THE EVIDENCE** | OPEN | CAB-LA: HKSJ at df=1 gives `RR 0.0002-212`, and the page reads that as the trials "carrying no information at all". **It is a pathology of the method, not a property of the trials** | 2026-09-03 |
| **M8** | **`I²` AS A PROPERTY OF THE EXTRACTION, NOT OF THE TRIALS** | OPEN | **4 demonstrations.** inclisiran: mixed analysis variants manufacture `I²=74%`; harmonised, `tau²=0`. ceftaroline: mixed-population rows give `I²=0%`; the corrected MITT pool `~37%`, corrected adult MITT `45.5%`, all-age k=4 `52.6%` | 2026-09-03 |
| **M9** | **A CORRECT REFUSAL WITH A WRONG REASON** | PARTIAL, gated | **2 sightings.** IV-iron's win ratio names three false grounds beside one valid `k=1`. bempedoic defers GRADE because "k=1 means there is no combined result" -- **GRADE does not require a meta-analysis**; the defensible reason is incomplete RoB and incomplete evidence identification | 2026-09-03 |
| **M10** | **GRADE RATIONALES THAT DO NOT SURVIVE READING** | OPEN | CAB-LA: indirectness downgraded because the two populations differ, when the protocol's target population IS those populations; domain-2 RoB conflated with non-adherence, when for an effect-of-assignment estimand non-adherence is part of the effect. **WHO rates the same two trials HIGH with no downgrades; our path runs to VERY LOW, and the discordance is mostly built from defective rationales** | 2026-09-03 |
| **M11** | **THE WRONG EFFECT MEASURE FOR THE DATA TYPE** | OPEN | CAB-LA is time-to-event with person-time and early stopping; Cochrane directs pooling HRs by generic inverse variance. Pooled `HR ~ 0.186` | 2026-09-03 |
| M5 | Multi-arm contrasts sharing one control pooled as independent | NOT FIXED | the off-diagonal covariance is `tau²/2` | 2026-09-02 |

---

# FAMILY 10 -- INSTRUMENTS THAT REPORT THEIR OWN REACH AS COVERAGE

| id | class | status | blast radius | date |
|---|---|---|---|---|
| **T1** | **A TEST THAT SILENTLY SKIPS WHAT IT CANNOT PARSE REPORTS "ALL CLEAN" ON A CORPUS IT DID NOT EXAMINE** | OPEN | `if not isinstance(bo, dict): continue` inside a corpus-wide loop, in a test fixture. Same family as `continue`-on-a-failed-lookup and the self-suppressing negation guard. **The remedy is always the same shape: COUNT THE SKIPS AND ASSERT ZERO** | 2026-09-03 |
| **T2** | **A SCREENING RECORD THAT CONTRADICTS ITSELF** | OPEN | ceftaroline: "42 records matched, 42 read ... one appraised; the rest were not read" | 2026-09-03 |
| **T3** | **A VALIDATION THAT DOES NOT VALIDATE THE DENOMINATORS** | OPEN | CAB-LA calls Wang 2023 an independent validation on matching RR and I², **while the page itself notices a ~1,250/arm denominator discrepancy** (`5161/5129` against our ~3,900/arm) and still calls it validation | 2026-09-03 |

---

## What is NOT fixed

- **Of the ~46 rows above, one is FIXED (B1) and nine are PARTIAL-and-gated. The rest are
  OPEN.**
- **No page is regenerated and no stored value is repaired.** Every FAIL sits in a baseline.
- **A6 -- the wrong headline number -- is not corrected**, because correcting it means
  re-extracting from the publications, not editing code.
- **The withdrawal template (W1) is not written yet**, and it must exist before this lane
  issues withdrawals at scale.
- **Detection is not built here.** A sibling lane owns the oracle-free suite.
- **B3-B5 are not this lane's to fix** -- a dedicated lane is clearing the trunk.

## Blockers recorded rather than fought

Per standing orders, reds that are not this lane's are recorded, not worked around:

| gate | reason | introducing sha |
|---|---|---|
| `scripts/lint_recurring_traps.py` | `scripts/comparator_seed/phase3_measure.py:414`, `unanchored_substring`. **FALSE POSITIVE** -- `held_pmid` is a `set`, so `in` is membership, not a substring test. The value reaches that line through a tuple-unpacked subscript, so no sound static narrowing was available and this lane will not stamp an exemption on another lane's file | not named by the gate |
| trunk gate chain | two guards on the trunk that their own gate refuses (class B5) | `e1ccb9f9c`, `66c1ed934` |

## Refusals that are right

Enumerated separately in `PROTECTED-REFUSALS-2026-09-02.md` **before anything was edited**,
because on the page a correct refusal and a defect look alike. Fifteen reviewers have now
repeatedly praised the same things: declining funnel, GOSH, meta-regression and TSA at small
k; refusing a RoB figure with no judgements; keeping co-primaries separate; flagging LDL-C
as a surrogate; every `NOT READY` flag being correct; and -- added 2026-09-03 -- **the
"No systematic search was run" banner itself, which is honest and correct and is
contradicted by our own marker, not the other way round** (B2).
