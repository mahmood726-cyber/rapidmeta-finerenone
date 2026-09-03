# Defect Class Register

Opened 2026-09-02 and committed before any fix in this lane, so it could not be trimmed to
match what was achieved. Extended 2026-09-03 with reviews 9-17. Rows are added when a class
is identified and never removed when one turns out to be hard.

**Twenty-five independent external reviews. The arithmetic reproduced
every time except once** — ceftaroline put a wrong number in a headline. Selection and
description are still where almost everything fails, but FIX α is no longer hygiene.

Every claim is marked **MEASURED** (a command was run; output committed under
`scripts/baselines/`), **INFERRED** (follows from code read, not executed), or **CLAIMED**
(asserted by a review, not yet checked here).

**Rows cite GATE FILENAMES, not commit shas.** This lane rebases onto a moving trunk before
every push, so a sha in a document is stale within the hour. A filename is not.

## Denominators

MEASURED, `scripts/measure_defect_classes.py`:

| population | n | is it the served surface? |
|---|---:|---|
| all HTML deployed by the Pages workflow | 2228 | published, reachable by URL |
| **root-level `*.html`** | **1464** | **yes — the page denominator** |
| `out/` | 190 | adjudication + withdrawal artefacts |
| `outputs/` | 327 | of which **319 are `*backup*`: ARCHIVE** |
| other subdirectories | 247 | not reader pages |

1464 + 190 + 327 + 247 = 2228. Two further denominators: **152 topic objects** resolved by
`ssot/PAGE_MAP.json`, and **155 canonical objects** under `ssot/`. Of the 1464 served
pages, **19 carry the page-standard property table**.

## SCREEN is not CONFIRMED, and NOT-CHECKABLE is not a pass

A screen is an upper bound from string co-occurrence. It is not a finding. Both rules were
earned. The first `not drawn` screen returned **151 pages** and every hit was
`GOSH plot — not drawn at this k`, a **correct refusal**. And the first version of the
two-trial measurement folded 128 objects recording no `k` into "checked", which would have
reported 146 checked against 13 contradicting — reading 128 unreadable objects as
agreement.

## What this lane got wrong first, and in which direction

An instrument with no measured error rate is an assumption wearing a number.

| predicate | wrong how | cost if shipped |
|---|---|---|
| `p2_k_cascade` | treated `k4_comparator` as a filter stage; it is a sibling role bucket | 6 correct pages refused, all at one transition |
| `p5_extraction_table` | required `derived_by`; refused a cell naming its method as an explicit formula | 2 correct pages refused |
| structural password test | regex flagged P6/P7/P8, which sit in an `if/else` with a REFUSING branch a regex cannot see | 3 correct emitters called passwords |
| `protocol_conformance_gate` v1 | returned NOT_ESTABLISHED as a DIFFERENCE | **127 of 127** reported drifting — a statement about the instrument |
| `protocol_conformance_gate` v2 | read the first estimator anywhere under `results`, including inside `the_pools_this_refusal_declines_to_report` | accused colchicine-cvd-coronary **for showing what it refused** |
| declared-skip narrowing in `audit_exclusion_by_absence.py` | a 5-line window read the NEXT guard's report as this one's | 119 baselined guards silently exempted — caught by its own negative proof |
| `test_no_invented_trial_count` v1 | searched source for a sentence split across a string concatenation | reported the protected disclosure as DELETED |

Six failed by **accusing correct code**; one by **excusing it**. Every gate this lane
landed now carries a negative control, and those controls are the cases these predicates
wrongly judged.

---

# FAMILY 1 — CHECKS WHOSE GREEN MEANS NOTHING

One defect at several altitudes. Grouping them makes FIX β structural rather than anecdotal.

| id | class | status | blast radius |
|---|---|---|---|
| B1 | A `P*` property ASSERTED `HELD`, computed from nothing that could contradict it | **FIXED** — `ssot/page_properties.py`, gate `property_recompute_gate.py`, plant `test_properties_can_refuse.py` | MEASURED: 11 flips on 10 of 18 pages at the time it landed |
| B2 | `P1_executed_search` **HELD** on a page whose own prose says **"No systematic search was run"** | **FIXED** — P1 now reads `search.strategy`, the same key the banner reads | **MEASURED: 17 of the 19 marker pages (89%)** |
| B3 | **A GATE THAT IS OPT-IN IS NOT A GATE** — hooks run only where `core.hooksPath` is set by hand | CLOSED on the CI half by the trunk-clearing lane's `hook-chain.yml`; **local auto-arming still outstanding** | that lane measured 68 checks enforced only by hooks a fresh clone leaves inert |
| B4 | **A CHAIN THAT SHORT-CIRCUITS AT THE FIRST REFUSAL** reports a property of its first check | **FIXED by the trunk-clearing lane** — `gates/run_hook_chain.py`, whose selftest plants a failing check FIRST and requires all three to still be reached | caused two false "the sibling lane cleared it" reports |
| B5 | **A GATE THAT WOULD REFUSE A COMMIT, ON A COMMIT ALREADY LANDED** | OPEN | the gate names the introducing shas itself: `e1ccb9f9c`, `66c1ed934` |
| B6 | **A GATE WHOSE VERDICT DEPENDS ON WHICH REFS THE CLONE HAPPENS TO HAVE** | OPEN | `scripts/check_correction_pins.py` `KNOWN_LANES` is a bare LOCAL branch name. gate20 returns BROKEN in a fresh clone and PASSED in a long-lived worktree the same day; 60 remote refs did not fix it, only a local ref did. **To its credit it refuses rather than reporting a false clean** |
| **B7** | **A GATE THAT NAMES ITS OWN GAP AND THEN EXITS 0** | OPEN | `lint_composite_by_components` prints `NOT_ASSESSABLE 26 … A gap, not a clean result` **and exits 0**. Three passes in the trunk suite are vacuous. This is the password class in the clearest possible form: the check says it did not check, and reports success |
| **B8** | **A PRISTINE CLONE CANNOT EXERCISE A STAGED-SCOPED CHECK** | OPEN, and it is an honest limit rather than a defect | `lint_recurring_traps --staged` passes VACUOUSLY where nothing is staged. **A green from an untouched clone proves the TREE-scoped gates pass and cannot prove the STAGED-scoped ones do** |
| **B9** | **A TREE-SCOPED RATCHET PUNISHES INTEGRATION** | OPEN | 23 of 28 push checks are tree-scoped, so a lane inherits every baseline its own tree carries and fixing `main` never clears it. This lane's own blockage was this, not a trunk defect |

---

# FAMILY 2 — FIX α: THE SOURCE HIERARCHY

**PRIMARY PUBLICATION → SUPPLEMENT / SAP / PROTOCOL → REGISTRY**, landed for the value
question; the registry keeps precedence on pre-specification. Three rules sit under it:

> ***THE SAME ENDPOINT TITLE IS NOT THE SAME ANALYSIS.***
> ***THE SAME COMPARATOR NAME IS NOT THE SAME COMPARATOR.***
> ***SEARCHING EVERY RANK WITHIN A REGISTRY IS NOT SEARCHING EVERY RELEVANT OUTCOME.***

| id | class | status | blast radius |
|---|---|---|---|
| A1 | `hasResults=False` read as "no results exist" | PARTIAL, gated `source_hierarchy_gate.py` | MEASURED: 2 dispositions on 1 of 152 topics |
| A2 | An effect carries its endpoint NAME but not its ANALYSIS VARIANT | PARTIAL, gated | **MEASURED: 610 stored points on 51 topics declare no variant; ZERO declare one** — so variant mixing is NOT_FOUND, not ABSENT |
| **A6** | **A NUMERATOR FROM ONE POPULATION OVER A DENOMINATOR FROM ANOTHER** | OPEN | **THE FIRST WRONG NUMBER TO REACH A HEADLINE.** ceftaroline FOCUS 2 stores `235/315` where the publication reports `235/289`. `74.6%` against `81.3%`. Correcting that row alone moves `RR 1.1048 → 1.0945` |
| **A7** | **A FALSE UNRECOVERABILITY CLAIM** | OPEN | **2 sightings, both cost evidence.** cangrelor: PHOENIX's three-component result is subtraction from the FDA table (`230/5470` vs `286/5469`) — an "it cannot be done" claim that discarded an 11,000-patient trial, **rendered verbatim on the served page**. ceftaroline: CE and MITTE are declared CO-PRIMARY and both published |
| **A8** | **COMPARATOR ROLE TAKEN FROM A LABEL, NOT THE PROTOCOL** | OPEN | **3 sightings.** rosuvastatin says "Rosuvastatin versus **candesartan/HCT**"; HOPE-3 is 2x2 FACTORIAL and the `6,361 vs 6,344` contrast IS rosuvastatin against placebo. CHAMPION-PLATFORM was cangrelor **vs PLACEBO**; our page says "against clopidogrel on all three". First sighting apixaban (enoxaparin 30 mg BD and 40 mg OD as one comparator). Also ceftriaxone 1 g vs 2 g; clarithromycin day 1 in FOCUS 1 only |
| **A9** | **REGISTRY-RANK COMPLETENESS MISTAKEN FOR OUTCOME COMPLETENESS** | OPEN | bempedoic: CLEAR Serenity's registry lists no MACE; its publication reports adjudicated MACE `9/234` vs `0/111` with components |
| **A10** | **REGISTRY-ONLY EXTRACTION SERVING OUTDATED EVENT DATA** | OPEN | CAB-LA: `13/4` should be `12/3` after baseline-prevalent adjudication; `RR 0.208 → 0.176` |
| **A11** | **A DIRECTLY COMPATIBLE RCT OMITTED** | OPEN | icosapent: `CTR20170362` (June 2023), IPE 4 g/day vs placebo, HL median difference `-19.9%`. Ours `k=2` `-25.84`, `I² 64.2%`; with it `k=3` `-22.79`, `I² ≈ 36.6%` |
| **A12** | **A SOURCE-RETRIEVAL FAILURE RECORDED AS A TRIAL-CONDUCT JUDGEMENT** | OPEN | empagliflozin: RoB downgraded **because the NEJM methods were not in PMC**. The trials are randomised, double-blind, placebo-controlled, ITT-followed, centrally adjudicated, with published protocols and SAPs. Our reach became their risk of bias |
| **A13** | **A CONTINUOUS TIME MEASUREMENT INGESTED AS A COUNT** | OPEN — **gate specified, sweep corpus-wide** | rosuvastatin's object labels JUPITER's `1,646.4` and `1,578.3` as counts or rates. ClinicalTrials.gov declares them **parameter type MEAN, unit DAYS, measure "Kaplan-Meier estimate of time to event/censoring"**. A generic registry-extraction defect that is **silent wherever it fires**. GATE: assert the registry's declared `param_type` and `unit` against the field we ingest into — oracle-free |
| **A14** | **OUTCOME-DEFINITION INCOMPATIBILITY READ AS HETEROGENEITY** | OPEN | JUPITER's `142/251` is its **FIVE-component** primary (CV death, nonfatal MI, nonfatal stroke, hospitalisation for unstable angina, **arterial revascularisation**); HOPE-3's `235/304` is its **THREE-component** first co-primary. A patient revascularised or admitted with unstable angina enters the JUPITER numerator with no HOPE-3 first-primary event. The stored label omits revascularisation and is truncated mid-parenthesis |
| **A15** | **A WRONG PMID, POINTING AT AN UNRELATED PAPER** | OPEN — **gate is trivially oracle-free; sweep corpus-wide** | finerenone cites FIDELIO as `PMID 33034526`. That PMID is *"Variability in antemortem and postmortem blood alcohol concentration"*. The correct one is `33264825`. **The portfolio index explicitly ADVERTISES identifier and provenance checking, and a citation pointing at a paper about blood alcohol survived it** — so the blast radius is the advertised claim itself, not one page. GATE: fetch every stored PMID and assert its title and authors against the trial it is attached to |
| **A16** | **A SOURCE SET TREATED AS AN EVIDENCE GAP** | OPEN — **and this register stated it the wrong way round** | see the correction below |
| **A17** | **REGISTRY COUNTS USED WHERE THE PUBLICATION'S ADJUDICATED COUNTS EXIST** | OPEN | **5th instance, and it moves our number.** AGYW: page has Ring `82/1302` vs `61/650` and an ASPIRE placebo denominator of 1313; the publications' adjudicated figures are `77/1300` vs `56/650` and 1316. `0.703` → corrected `0.7127` → published HR pool `0.713`. **The page itself recognises that adjudication explains the difference and uses the pre-adjudication counts anyway**, which makes it W6 as well as FIX α |
| A3 | A REGISTRATION rendered as a PUBLICATION | NOT FIXED | not measured |
| A4 | Blinded-adjudication facts missed by reading registry fields only | NOT FIXED | subsumed by A10 |
| A5 | AMPLIFY `61/76` impossible reconstruction | NOT FIXED | 1 page CLAIMED |

> **The case for FIX α in one sentence, from review 13:** one registry denominator mismatch
> propagated cleanly through perfectly correct meta-analytic arithmetic and produced a
> polished but wrong headline number.

---

# FAMILY 3 — OUR CORRECTIONS AND WARNINGS ARE EMITTERS TOO

> ## ***A FIX IS AN EMITTER TOO. A WITHDRAWAL IS A CLAIM ABOUT OUR DERIVATION, NOT ABOUT THE WORLD. AND A WARNING CARRIES A FINDING'S EVIDENTIAL BURDEN.***

The family now has all three failure directions: a warning that is **false about the
world** (W1), a warning that is **false about our own work** (W5), and a warning issued
**instead of a fix** (W6).

| id | class | status | blast radius |
|---|---|---|---|
| **W1** | **CONFLATING "OUR DERIVATION IS INVALID" WITH "THE EFFECT IS UNSUPPORTED"** | **PARTIAL** — object side gated by `withdrawal_states_both_halves_gate.py`; **the projector half is OPEN** | **MEASURED: 151 withdrawal reasons read, 111 on 98 topics say nothing about what survives, 2 of those also assert the effect is gone** (anidulafungin-candida, olmesartan-htn). See the correction below |
| **W2** | **A CORRECTION THAT INTRODUCES A NEW ERROR** | OPEN | the cangrelor fix replaced a corrupt k=3 with a k=2 pool that wrongly discards CHAMPION-PHOENIX, justified by A7 |
| **W3** | **A CLEAN RESULT FROM AN UNVALIDATED HARNESS** | OPEN | the gate lane retracted a real diagnosis after a "clean" reproduction whose harness set an extra variable that MASKED the behaviour — **the withdrawal was the error** — and its diagnostic flipped a clone to `core.bare`. **Rule: probes belong on a throwaway copy** |
| **W4** | **A LESSON LEARNED AT THE INSTANCE AND NOT AT THE CLASS** | OPEN | bempedoic corrected CLEAR Harmony's exclusion reason after finding the registry DOES list adjudicated MACE — **then repeated the identical error on Serenity by staying inside the registry** |
| **W5** | **A SELF-CRITICISM WHOSE PREMISE IS FALSE, AND A DOWNGRADE WHOSE STATED REASON IS THAT PREMISE** | OPEN | **Two on the icosapent page, both load-bearing.** (a) *"the registered primary is a MEDIAN … this pool is a MEAN difference … it answers a question neither trial asked"* — FALSE: the stored `-33.1` and `-21.5` ARE Hodges-Lehmann placebo-adjusted median differences, which the FDA statistical review labels "Estimated Median" and names the method for. **We mistook the meta-analysis software's generic `MD` label for the quantity entered.** (b) *"a dose arm was selected and the selection is recorded nowhere"* — FALSE: the PICO reads **AMR101 4 g/day versus placebo**, and the numbers uniquely identify the 4 g arm. **Both drive RoB-2 D5, the GRADE indirectness downgrade, part of imprecision, and manuscript prose** |
| **W6** | **A DEFECT DETECTED, DISCLOSED, AND THEN NOT ACTED ON** | OPEN — **cheap and unambiguous, flagged as a good early landing** | empagliflozin states plainly that the endpoint is time-to-first-event while the pool uses **odds ratios from cumulative counts**, correctly notes an OR over unequal follow-up is not a hazard ratio — **and then prints `OR 0.758` in the headline, abstract, results, SoF table, forest plot and GRADE calculations.** Correct synthesis from the published HRs: `HR 0.771 (0.700-0.849)`, `I²=0`, `τ²=0`. Median follow-up 16 vs 26.2 months is exactly why the OR is inadmissible |

> ## ***ONCE A DEFECT IS IDENTIFIED, ADDING A WARNING IS NOT A FIX. A DISCLOSED WRONG NUMBER IS STILL THE NUMBER A READER TAKES AWAY.***

| **W8** | **THE PRINCIPLE IS IN THE PROSE AND NOT IN THE PIPELINE** | OPEN | **2 instances.** AGYW states, correctly, that a participant leaving at six months **contributes follow-up and is censored, not simply "missing"** — then pools a crude binary RR, discarding person-time, on two trials that both analysed TIME TO HIV INFECTION. SGLT2 prints *"refused: the measure is HR, not a risk ratio"* a few hundred bytes from two tables that violate it. **The page knows the rule and the code does not consult it** |
| **W7** | **W6 ON THE POPULATION — THE WORST SURFACE IT CAN HIT** | OPEN | rosuvastatin's title, abstract, visual abstract, introduction and figures all say **"adults with stroke"**. **JUPITER and HOPE-3 are PRIMARY PREVENTION trials in people WITHOUT cardiovascular disease; neither recruited a stroke population.** The page carries a BURIED corrected question — "adults without established cardiovascular disease, at elevated risk" — **that reached no reader-facing surface.** The visual abstract attaches `30,507 participants` to it, lending authority to a pool that is not coherent |


**GATES TO BUILD.** For W5: every RoB and GRADE downgrade reason must name a **checkable
fact**, and that fact must be asserted — a downgrade whose reason is a claim about our own
record is the cheapest of all to check and the least often checked. For W6: *"effect
measure: ESTABLISHED"* must assert the measure against the **endpoint type**, not against
agreement between rows — empagliflozin's Table 7 says ESTABLISHED because both stored
estimates are ORs, which establishes only that **the same wrong transformation was applied
twice**.

### A correction to the brief, on W1

**The cangrelor OBJECT does not have this defect.** It carries a `withdrawn_note` headed
"WHAT IS CONFIRMED, STATED AS PROMINENTLY AS WHAT IS WRONG", and records that the withdrawn
`OR 0.81 (0.71-0.91)` reproduces Steg et al. 2013 — a prespecified pooled analysis of
patient-level data from all three CHAMPION trials, n=24,910. The served page carries that
reproduction too.

What the page does NOT carry is the "WHAT IS CONFIRMED" framing, and what it does carry —
early and unqualified — is "the correction reverses the conclusion". **So the defect is a
missing QUALIFICATION on the strongest sentence, not a missing fact, and it lives in the
projector's SELECTION rather than in the object.** The gate reports cangrelor as "flagged:
no, as expected" each run; the projector half stays OPEN.

---

# FAMILY 4 — PRESPECIFICATION, THE THING WE SELL

| id | class | status | blast radius |
|---|---|---|---|
| **P1x** | **THE EXECUTED ANALYSIS DOES NOT FOLLOW OUR OWN STORED PROTOCOL** | **GATED** — `protocol_conformance_gate.py`, fully oracle-free | **MEASURED: 127 topics comparable, NINE differ from their own protocol with 0 dated amendments** — arni-hfref, cab-prep-hiv-review, doac-af-review, finerenone-cv, incretin-hfpef-review, iv-iron-hf, nirsevimab-infant-rsv-review, sglt2-hf, sglt2-mace-cvot-review. 119 have an axis NOT ESTABLISHED, counted not passed; 25 not comparable and named. CAB-LA differs on all three axes: DL→REML, log-HR→RR, HKSJ-primary→HKSJ-alongside |
| **P2x** | **THE PROTOCOL RELATIONSHIP FAILS IN THREE DISTINCT FORMS** | OPEN | (1) CAB-LA: protocol present and IGNORED. (2) ceftaroline and rosuvastatin: protocol for a DIFFERENT QUESTION, and rosuvastatin's names different trials entirely. (3) **lefamulin, and it inverts the obvious fix:** the protocol is present, linkable, specifies DerSimonian-Laird + HKSJ with the trial-published metric, and the review runs REML with RR. **ATTACHING IT WOULD NOT DEMONSTRATE ADHERENCE — IT WOULD DOCUMENT DEVIATION. "Link the protocol" is not the remedy;** reconciliation with a dated amendment, or a clean prospective protocol before a rerun, is | **2 sightings, the second worse.** rosuvastatin's protocol specifies trials registered "for Coronary", an active-or-placebo comparator, DL+HKSJ, and names **LANCE and SATURN** — SATURN compared rosuvastatin with **atorvastatin** on atheroma volume and LANCE measured LDL-C, so it is not this review's protocol and not even this review's trials. | ceftaroline's protocol covers "Adults registered for MRSA", allows placebo or any active comparator, any primary outcome, and includes an observational study. **Worse than P1x: there the protocol was ignored; here it is not this review's at all** |
| **P3x** | **WE REPLACED THE TRIALS' PRESPECIFIED FRAMEWORK WITHOUT JUSTIFYING IT** | OPEN — **now a RULE, not a coincidence: 3 pages** (ceftaroline, apixaban prophylaxis, lefamulin). **And the corrected framing is STRONGER for us, not weaker.** LEAP 1 `-2.9 (-8.5 to +2.8)` against a `-12.5%` margin; LEAP 2 `~+0.1` against `-10%`; our own pooled RD `-1.07 (-4.34 to +2.20)` reproduces the published programme RD `-1.1 (-4.4 to +2.2)`. *"The pooled interval comfortably excludes the -10% margin"* is clearer and more favourable than *"RR 0.988, CI crosses 1"* — **we are publishing the weaker version of our own result.** GATE: where every contributing trial declares a non-inferiority margin, the RD-vs-margin framing is primary and the ratio secondary | all three ceftaroline trials are non-inferiority with a `-10 pp` margin; we substituted a superiority-oriented risk-ratio headline. Corrected RDs MITT `+8.48 pp (-1.82 to +18.77)`, CE `+7.85 pp (-1.21 to +16.91)` — both above `-10 pp`. **The defensible statement is "non-inferiority is supported; superiority is not robust under our own conservative rule", and we said neither** |
| **P4x** | **A DECLARED METHOD CONTRADICTED BY ITS OWN USE** | OPEN | ceftaroline: the house variance-floor rule gives `RR 1.1048 (0.9868-1.2371)`, **crossing 1**, while GRADE's "no imprecision downgrade" is justified on the UNFLOORED HKSJ `1.0356-1.1787` |
| **P5x** | **A PROTOCOL-PROVENANCE CONTRADICTION** | OPEN | **5 sightings.** A page says it cannot establish protocol linkage, then speaks as though prespecification IS established. Correct form: *"no prespecified moderator is established in the current review record."* CAB-LA says the protocol "was first committed later" when git shows review, protocol and benchmark in the SAME commit — the honest statement is *"git history does not demonstrate prospective prespecification"* |

> **A silent estimand drift with a protocol on file is worse than having no protocol.** It
> converts our central claim into the thing a reviewer can disprove fastest, using only our
> own files.

---

# FAMILY 5 — ELIGIBILITY DEFECTS IN THE SCHEMA ITSELF

Design, not slips: each fires every time.

| id | class | status | blast radius |
|---|---|---|---|
| **E1** | **EFFECT MEASURE AS A POST-HOC ELIGIBILITY CRITERION** (`effect_measure = HR`) | OPEN | a randomised trial becomes ineligible for supplying arm-level events instead of a hazard ratio. **Effect measure determines the synthesis method, not whether a trial addresses the PICO** |
| **E2** | **AN ELIGIBILITY CRITERION DERIVED FROM THE INCLUDED SET** | OPEN | bempedoic's two-arm design criterion was reverse-engineered from the already-included trial. Circular: it cannot exclude anything the set does not already exclude |
| **E3** | **A QUERY FILTER ABSENT FROM THE DECLARED ELIGIBILITY** | OPEN | the registry query restricts to `PHASE3, PHASE4`; the declared eligibility has no phase restriction |
| **E4** | **THE DECLARED POPULATION IS NOT THE ANALYSED POPULATION** | OPEN | **AGYW is 15-24 by UNAIDS; the pooled trials enrolled 18-45**, and the estimate is dominated by women 25+ where efficacy is greatest. ASPIRE prespecified `<25: 10% (-41 to 43)` against `>=25: 61% (32-77)`, interaction p=0.02; WHO records efficacy NOT demonstrated at 18-24. Our indirectness note names the under-18 gap and **misses that 25-45 is also outside AGYW and is driving the estimate**. THE ERROR FLATTERS US |
| **E7** | **THE COMPOSITE IS PARTLY A PRODUCT OF SURVEILLANCE INTENSITY** | OPEN | apixaban prophylaxis: ADVANCE-1, -2 and -3 used **MANDATORY SYSTEMATIC BILATERAL VENOGRAPHY**, so "proximal DVT" in the pooled composite includes clots found only because the trial went looking — while the PICO says **symptomatic** VTE. This is no longer "the composite includes asymptomatic events"; it is that **the composite depends on how hard each trial searched, and that differs by trial** |
| E5 | Eligibility criteria absent, so an exclusion cannot be justified | OPEN | ceftaroline: `NCT01530763` is ELIGIBLE on the literal PICO; all-age `k=4` gives `RR 1.093 (1.021-1.170)`, `I² 52.6%` |
| **E6** | **A CIRCULAR PICO — THE OUTCOME CLAUSE DEFINED BY THE INCLUDED SET** | OPEN | **2nd sighting.** empagliflozin asks for "the outcome **both trials register as their primary**" — **no trial can ever fail that.** Rosuvastatin does the mirror: "the outcome each trial registered as its primary, **which differ across the 2 trials here**". Same family as E2 |

**GATE TO BUILD:** a PICO outcome clause may not be defined by reference to the included set.

---

# FAMILY 6 — FALSE ABSENCE CLAIMS

Distinct from A7: these are absences asserted about documents **we ourselves hold**.

| id | class | status | blast radius |
|---|---|---|---|
| **N1** | **AN ABSENCE CLAIM CONTRADICTED BY OUR OWN OBJECT** | OPEN — oracle-free | **4 sightings.** CAB-LA: "the protocol prespecifies no moderator" is FALSE, and "no risk-of-bias assessment is recorded" is FALSE beside a complete two-assessor table. icosapent: "no endpoint definition is recorded" while the page identifies it precisely. empagliflozin: the same, **while elsewhere stating the two registered endpoint strings were checked word-for-word and differ only by "the"** |
| **N2** | **A FALSE ABSENCE ABOUT THE LITERATURE** | OPEN | **5 sightings.** bempedoic (three syntheses exist), ceftaroline (a 1,916-patient IPD meta-analysis of exactly those registrations; `MITT OR 1.66`, `CE OR 1.65`), AGYW (USPSTF pooled the same two RCTs at `RR 0.71 (0.57-0.89)`, `I²=0%`) |
| **N3** | **AN OMISSION BY THE REVIEW, REPORTED AS AN ABSENCE IN THE EVIDENCE** | OPEN | harms unsynthesised on **9 pages**; absolute effects called unavailable when every publication prints them. cangrelor GUSTO bleeding `857/5529` vs `602/5527`; icosapent Chinese RCT serious TEAEs `3.2%` vs `2.4%` |

---

# FAMILY 7 — CONTRADICTORY AND STALE SURFACES

One shape: two surfaces from different sources with nothing asserting they agree.

| id | class | status | blast radius |
|---|---|---|---|
| C-shape | Two surfaces rendered from different sources, unreconciled | PARTIAL, gated `contradicting_surfaces_gate.py` | MEASURED: 1 FAIL of 155 objects |
| **C7** | **A HARDCODED TOPIC-SPECIFIC SENTENCE EMITTED CORPUS-WIDE** | **FIXED** — the count is read from `k_cascade.k_included_in_object`; a topic recording no k renders no number. Negative test `test_no_invented_trial_count.py` | **MEASURED: 146 of 1464 served pages rendered "a named two-trial programme". 18 checkable; 13 contradict their own k** (1, 3, 4, 5, 6, 7, 8); 5 agree; 128 record no k and are NOT CHECKABLE. 5+13=18, 18+128=146 |
| **C8** | **INTERNAL LANE COMMENTARY ON A READER SURFACE** | OPEN | **5 sightings, running both ways.** CAB-LA carries model commentary about 22-23 other topics and about gepotidacin; ceftaroline carries "Class 94", AGYW/CAB text and model-audit output; icosapent's scope field reads *"all long-chain omega-3 and alpha-linolenic acid, every dose, supplements and diet"* on a page about AMR101 4 g/day |
| **C9** | **MUTUALLY EXCLUSIVE STATEMENTS OF THE SAME FACT ON ONE PAGE** | OPEN | AGYW carries three search statements at once; cangrelor carries four analysis states; icosapent and empagliflozin both carry PRISMA self-contradictions ("no screening record recoverable" vs "a screening record is held on this object") |
| **C10** | **A VISUAL FALSEHOOD** | OPEN | the ceftaroline forest plot draws all three study squares the SAME SIZE although the inverse-variance weights differ materially. **A figure that misrepresents weighting is a false statement a reader cannot check by reading the numbers** |
| C1 | Certainty "pending" and graded at once | OPEN | **5 sightings** (LOW, VERY_LOW, and a GRADE row contradicting the RoB summary beneath it) |
| C2 | "not drawn" beside a figure caption for THAT figure | OPEN | **8 sightings.** The page-level screen returns 151 and is WRONG — those are protected refusals |
| C3 | Stale relative-effect boilerplate on an absolute outcome | OPEN | **3 sightings**, incl. a percentage-point outcome |
| C4 | `NOT READY` beside `Publishable: True` | OPEN | 2 sightings, one with `criteria_predefined = FAIL` |
| C6 | RoB "assessors disagree" beside a displayed agreement rate | OPEN | **6 sightings**: `15/15`, `8/10`, `3/5`, `9/15`, `7/10`, `8/10` |
| C11 | Canonical-object contradiction | OPEN | **7 sightings** |
| C12 | Provenance contradiction on ONE ROW: "DERIVED by us" above "READ, not derived" | OPEN | **4 sightings** |

---

# FAMILY 8 — DENOMINATORS AND UNITS

| id | class | status | blast radius |
|---|---|---|---|
| D1/D4 | Randomised / analysed axis conflated | PARTIAL, gated `denominator_axis_gate.py` | MEASURED: 1 FAIL of 1464; 4 pages NAMED as unjudgeable |
| **D6** | **ENROLLED / RANDOMISED / TREATED / mITT CONFLATED** | OPEN | **6 sightings.** cangrelor: regulatory summary gives 8,846 / 5,346 / 11,145 randomised; publications say 8,877 enrolled and 5,362 randomised; we carry `8,882` / `5,364` under "Randomised" |
| **D7** | **UNIT MIXING IN ABSOLUTE EFFECTS** | OPEN | AGYW applies a CUMULATIVE risk ratio to `4.5 infections per 100 woman-years` and derives an annual `NNT ~ 75`. **Incidence rates and cumulative risks are not interchangeable** |
| **D8** | **HARMS COUNTS THAT DO NOT MATCH THE PUBLICATIONS, AND A CAUSAL CLAIM INFERRED FROM THE RATES** | OPEN | AGYW reports ASPIRE SAEs `116/1313` vs `130/1316`; the paper reports `52/1313` vs `48/1316`. **The page then infers "a difference in what was counted, not in what happened" FROM THE RATES ALONE** |
| **D9** | **GRADE IMPRECISION COUNTING WHOLE MULTI-ARM POPULATIONS** | OPEN | **2 sightings** (azilsartan 1st). icosapent counts `229` and `702` where the 4-g-vs-placebo contrast is `151` and `453` — **and complains there were three arms while counting the unused one toward its own information size** |
| **D10** | **THE FULL ANALYSIS SET LABELLED "ALL RANDOMISED PARTICIPANTS"** | OPEN | **sightings 8, 9 and 10.** FIDELIO 5,734 randomised, 60 excluded for GCP violations, FAS 5,674; FIGARO 7,437 randomised, 85 excluded, FAS 7,352 — **and the page separately states FIGARO "Randomised: 7352", which is the ANALYSED n.** apixaban VTE treatment prints `78 / 1155 / 2700` as randomised when those are analysed (`80 / 1170 / 2760`); apixaban prophylaxis prints `2481/4394/2394/4494` against actual `3195/5407/3057/6528`. **Randomised, FAS and analysed must be three fields and the exclusion count must be recorded.** The estimates are right; the LABEL is wrong |
| **D11** | **THE TOPIC TOTAL PROJECTED INTO EVERY OUTCOME TABLE REGARDLESS OF CONTRIBUTORS** | OPEN — **cause identified from two directions at once** | SGLT2_HF labels its `k=3` harmonised analysis `20,725 participants`, which is exactly DAPA-HF 4,744 + EMPEROR-Reduced 3,730 + EMPEROR-Preserved 5,988 + **DELIVER 6,263**. The correct n for its three studies is `14,462`. **IT COUNTED DELIVER'S PARTICIPANTS WHILE OMITTING DELIVER'S EFFECT — the wrong number is the evidence that DELIVER was meant to be in the analysis and its row failed to propagate.** The `k=2` table gets `20,725` too, where DAPA-HF + DELIVER is `11,007`. See the convergence note below |
| D5 | A missing denominator filled with a ZERO | NOT FIXED | SCREEN: 12 served pages |

---

# FAMILY 9 — METHOD AND JUDGEMENT

| id | class | status | blast radius |
|---|---|---|---|
| M-label | A method LABEL naming an analysis the numbers were not produced by | PARTIAL, gated `method_label_gate.py` | MEASURED: 3 FAIL of 155 |
| M-derived | A derived value that is a SNAPSHOT of superseded operands | PARTIAL, gated `derived_recompute_gate.py` | MEASURED: 2 FAIL of 155 |
| M3 | Imprecision downgraded on STUDY COUNT | OPEN | **4 sightings** |
| **M7** | **A METHOD ARTEFACT READ AS A FACT ABOUT THE EVIDENCE** | OPEN | CAB-LA: HKSJ at df=1 gives `RR 0.0002-212` and the page reads that as the trials "carrying no information at all". **It is a pathology of the method, not a property of the trials** |
| **M8** | **`I²` MOVES WITH OUR EXTRACTION AND OUR INCLUSIONS -- BUT IT IS NOT ONLY AN ARTEFACT** | OPEN | **6 demonstrations.** inclisiran: mixed variants manufacture `I²=74%`, harmonised `τ²=0`. ceftaroline: mixed populations give `0%`, corrected `~37%`, adult MITT `45.5%`, all-age k=4 `52.6%`. icosapent: adding the omitted trial HALVED it, 64.2% → 36.6%. **rosuvastatin: correcting to a COMMON endpoint and pooling the published HRs gives `HR 0.645 (0.453-0.917)` with `I² = 78.9%`, `Q 4.74`, `p 0.0295` -- THE HETEROGENEITY SURVIVES THE FIX.** See the correction below |
| **M9** | **A CORRECT REFUSAL WITH A WRONG REASON** | PARTIAL, gated `refusal_reason_gate.py` | **2 sightings.** IV-iron's win ratio names three false grounds beside one valid `k=1`. bempedoic defers GRADE because "k=1 means there is no combined result" — **GRADE does not require a meta-analysis** |
| **M10** | **GRADE RATIONALES THAT DO NOT SURVIVE READING** | OPEN | CAB-LA: indirectness downgraded because the two populations differ, when the protocol's target population IS those populations; domain-2 RoB conflated with non-adherence, when for an effect-of-assignment estimand non-adherence is part of the effect. **WHO rates the same two trials HIGH with no downgrades; our path runs to VERY LOW** |
| **M11** | **THE WRONG EFFECT MEASURE FOR THE DATA TYPE** | OPEN | CAB-LA is time-to-event with person-time and early stopping; Cochrane directs pooling HRs by generic inverse variance. Pooled `HR ~ 0.186`. **Hazard ratios replaced by odds ratios from cumulative counts is now 2 sightings** — empagliflozin (16 vs 26.2 months) and rosuvastatin (1.9 vs 5.6 years). See also W6 |
| **V1** | **A MANUFACTURED SYMMETRIC CI WHERE THE PUBLISHED ASYMMETRIC ONE IS AVAILABLE** | OPEN | icosapent MARINE displayed as `-33.1 (-45.65 to -20.55)`, reconstructed from a stored variance; the published Hodges-Lehmann interval is `-33.1 (-46.6 to -21.5)`. **HL intervals are non-parametric and need not be symmetric** |
| **R1x** | **INTERVENTION AND COMPARATOR REVERSED IN THE OBJECT** | OPEN | both icosapent trials record **placebo as treatment** and **AMR101 4 g/day as control**. The signs happen to be consistent so the pooled number is not reversed — **but any downstream step reading the LABELS rather than the signs would invert it.** A latent defect is still a defect. **GATE: arm-role labels asserted against the direction of the stored effect** — oracle-free |
| **M12** | **`no information` USED AS A RoB-2 DOMAIN JUDGEMENT** | OPEN | **5 pages.** RoB-2 domain judgements are Low / Some concerns / High. *"No information"* is an answer to a SIGNALLING QUESTION, not a domain verdict. finerenone recognises this for the OVERALL judgement and not at domain level, **so the fix is one level deeper than the page already knows** |
| **M13** | **A FALSE-PREMISE DOWNGRADE — "SECONDARY OUTCOME = SOME CONCERNS"** | OPEN | **2nd sighting after icosapent (W5).** FIDELIO is driven to D5 *some concerns* largely because its CV composite was a SECONDARY outcome. **D5 asks whether the reported result was SELECTED from multiple eligible measurements or analyses ON THE BASIS OF RESULTS.** FIDELIO's composite was a prespecified key secondary reported in the primary paper. *Secondary outcome = some concerns* is not a RoB-2 rule |
| **M14** | **"OPEN LABEL" CONFLATED WITH UNBLINDED OUTCOME ASSESSMENT** | OPEN | apixaban VTE treatment: all three trials had blinded adjudication — CARAVAGGIO blinded central adjudication, COBRRA explicitly PROBE, AMPLIFY-J adjudicated blind to assignment. **This directly mis-scores RoB-2 Domain 4** |
| M5 | Multi-arm contrasts sharing one control pooled as independent | NOT FIXED | off-diagonal covariance is `τ²/2` |

---

### A correction to M8, which this register previously overclaimed

The earlier wording — *"`I²` as a property of the extraction and of what we included"* —
framed heterogeneity as something our own choices determine. **Rosuvastatin refutes the
strong form.** Correcting JUPITER and HOPE-3 to a common endpoint and pooling the published
hazard ratios leaves `I² = 78.9%` (`Q 4.74`, `p 0.0295`). The trials genuinely disagree:
20 mg against 10 mg, hsCRP-selected against intermediate-risk, 1.9 against 5.6 years, and
one stopped early.

**The defensible claim is narrower and still worth having:**

> Extraction and inclusion can MANUFACTURE heterogeneity that is not there and MASK
> heterogeneity that is. So `I²` must be re-read after any correction, and an inconsistency
> downgrade is interpretable only once the pool is known to be coherent. It does not follow
> that a high `I²` is always our doing.

Recording this because the previous wording is the W5 class — a claim of ours that does not
survive checking — and leaving it would make the register an instrument that overclaims.

---

# FAMILY 10 — INSTRUMENTS THAT REPORT THEIR OWN REACH AS COVERAGE

| id | class | status | blast radius |
|---|---|---|---|
| **T1** | **A TEST THAT SILENTLY SKIPS WHAT IT CANNOT PARSE REPORTS "ALL CLEAN" ON A CORPUS IT DID NOT EXAMINE** | OPEN | `if not isinstance(bo, dict): continue` inside a corpus-wide loop, in a test fixture. **The remedy is always the same shape: COUNT THE SKIPS AND ASSERT ZERO** |
| **T2** | **A SCREENING RECORD THAT CONTRADICTS ITSELF** | OPEN | **2 sightings.** ceftaroline: "42 records matched, 42 read … one appraised; the rest were not read". rosuvastatin renders `"? record(s)"`, `114 matched`, `8 appraised` and `2 appraised` on one page — and **our own screening file says 114 matched, 8 candidates, only 2 abstracts appraised, 6 unread, 106 rejected on title, so "eight appraised" is FALSE**. A reviewer independently reran our PubMed query and got **114**, which is an external positive control on one of our own counts |
| **T7** | **A "VERBATIM" TRANSCRIPT STITCHED FROM TWO DIFFERENT MODEL FITS** | OPEN — **gate specified** | apixaban prophylaxis stores an R transcript claiming `rma(..., method="REML", test="knha")` and then prints a **z statistic with an ordinary normal CI** `0.7433 (0.4371-1.2639)`; below it, *"SAME FIT WITH HARTUNG-KNAPP"* prints the genuine t-based `0.7433 (0.3067-1.8013)`. **Both cannot be output of one `test="knha"` call — the first block is the UNADJUSTED model presented under a knha call line.** The numbers are fine and the PROVENANCE IS FABRICATED BY ASSEMBLY. **This page's selling point is verbatim reproducibility, so it is the password class in the one layer supposed to be beyond doubt.** GATE: assert a displayed transcript's printed statistic type against the call line above it; sweep for stitched blocks |
| **T8** | **A MISSING REGISTRY DESCRIPTION FIELD READ AS AN ABSENT ENDPOINT DEFINITION** | OPEN — **a named emitter shape, go find it** | finerenone's endpoint table says *"No endpoint definition is recorded … its effect was pooled without one"* while the same page prints the exact four components verified word for word. **The renderer confuses a missing registry DESCRIPTION field with absence of an endpoint DEFINITION**, and this will explain several "no endpoint definition" false absences across the corpus |
| **T6** | **CORRECTNESS BY COINCIDENCE IS NOT ADEQUATE PROVENANCE** | OPEN | *"The recovered event counts happen to match the publications, but correctness by coincidence is not adequate provenance."* The same shape as the `156.70` / `156.67` coincidence on SGLT2: **a right answer reached by a route that cannot be relied on.** A number that is correct today by luck will be wrong tomorrow by the same mechanism, and nothing in the record distinguishes the two cases |
| **T3** | **A VALIDATION THAT DOES NOT VALIDATE THE DENOMINATORS** | OPEN | CAB-LA calls Wang 2023 an independent validation on matching RR and I², **while the page itself notices a ~1,250/arm denominator discrepancy** and still calls it validation |
| **T4** | **A BASELINE THAT CANNOT SAY WHY IT MOVED** | **FIXED** in this lane's gates | `--write-baseline` refuses a rise without `--reason` and writes the reason beside the number. Earned: a failed patch anchor let it run twice and silently write a `21` over a committed `11`. **"Records its own reason" is a property of the write, not a habit of the operator** |
| **T5** | **A DIVERGENCE BELIEVED BEFORE IT WAS DIAGNOSED** | **avoided, and recorded** | Re-measuring C7, a word-boundary escape written through a shell heredoc became a literal `0x08` byte; the pattern matched nothing and the count read **0 against a pinned 146**. That is a divergence by this lane's own rule and would have been chased. `lint_recurring_traps.py` caught it as `control_bytes`. **A number that disagrees can disagree because the tooling broke; neither reading is free.** It then happened a SECOND time, inside the write-up of the first |

---

### A16 — a correction this register owes, and it inverts an earlier statement

The SGLT2 lane reported DELIVER's two-component value absent from the sources we hold, and
the finding was recorded as **"an evidence blocker, not an effort one"**. That is wrong.

**DELIVER's own publication reports the two-component endpoint directly: `475/3131` against
`577/3132`, `HR 0.80 (0.71-0.91)`.**

> ***IT WAS A BLOCKER GIVEN OUR SOURCE SET, AND THE SOURCE SET WAS THE DEFECT. That is
> FIX α, not an evidence gap, and the earlier wording put it the wrong way round.***

Corrected harmonised pool: **`HR 0.774 (0.724-0.827)`, k=4, N=20,725, I² = 0%**, externally
confirmed by the 2022 Lancet prespecified synthesis over the same two-component endpoint and
the same trials, `HR 0.77 (0.72-0.82)`. The withdrawn mixed-primary derivation was `0.7785`
— numerically almost identical, **so the endpoint error had little consequence and the
withdrawal was still right**. Both halves of that are stated because W1 exists.

Two consequences follow. *"Published-meta comparison pending"* is resolvable now: the Lancet
paper names DELIVER, EMPEROR-Preserved, DAPA-HF, EMPEROR-Reduced and SOLOIST and publishes
the trial-level estimates `0.80 · 0.79 · 0.75 · 0.75 · 0.71`, so no registration-identity
mystery remains. And the SOLOIST exclusion wording is wrong as written — those patients did
have chronic heart failure; the distinguishing feature is randomisation AT a worsening
episode, and DELIVER itself randomised 654 patients (10.4%) during or within 30 days of a
heart-failure hospitalisation, so "recent hospitalisation" is not a clean binary criterion.

### A convergent diagnosis, which is the strongest confirmation a defect class can get

**D11 was reached twice, from opposite directions, by parties who could not see each
other's work.**

- **From the inside**, by reading our own code: `contributing_n()` returns `None` because the
  store holds no `inputs.trials[*].by_outcome` rows, so the renderer falls back to the topic
  total.
- **From the outside**, by checking a printed number: `20,725` is arithmetically DAPA-HF +
  EMPEROR-Reduced + EMPEROR-Preserved + DELIVER, on a page whose analysis contains three of
  those four.

One diagnosis from source, one from output, same cause. Neither party had the other's
evidence. **That is worth more than either finding alone**, and it is the pattern to look
for when deciding whether a class is real: a defect that can be found from two independent
starting points is not an artefact of how you looked.

### The validation suite — six known-answer cases, pinned

Several topics have a **prespecified patient-level or published pooled counterpart**. On
those, the pipeline is not discovering anything; it is reconstructing a known answer, and
agreement is a measurement of the pipeline.

| topic | published counterpart | published | ours |
|---|---|---|---|
| finerenone | FIDELITY prespecified IPD pooling | `HR 0.86 (0.78-0.95)` | `0.8655 (0.7877-0.9510)` |
| bococizumab | 2017 NEJM SPIRE | `-55.2 (-57.9 to -52.6)` | `-55.24` |
| SGLT2 heart failure | 2022 Lancet prespecified synthesis | `HR 0.77 (0.72-0.82)` | `0.774 (0.724-0.827)` corrected |
| apixaban prophylaxis | published patient-level pool of ADVANCE-2 + ADVANCE-3 | crude `RR 0.451` | `RR 0.453 (0.277-0.739)`, τ²=0 |
| lefamulin | published pooled LEAP development programme | `RD -1.1 (-4.4 to +2.2)` | `-1.07 (-4.34 to +2.20)` |
| AGYW | USPSTF pooled the same two RCTs | `RR 0.71 (0.57-0.89)`, I²=0% | `0.713` corrected |

> ***THESE PAGES ARE WEAK AS NOVEL CLINICAL META-ANALYSES AND STRONG AS KNOWN-ANSWER
> VALIDATION CASES.*** That set is the validation suite, not the discovery set.

**And every one of them currently hides the match behind a "pending external comparison"
flag or an "unreplicated" claim.** The most defensible thing these pages do is the thing
they do not say.

## Refusals that are right

Enumerated in `PROTECTED-REFUSALS-2026-09-02.md` **before anything was edited**. Seventeen
reviewers have praised the same things: declining funnel, GOSH, meta-regression and TSA at
small k; refusing a RoB figure with no judgements; keeping co-primaries separate; flagging
LDL-C as a surrogate; every `NOT READY` flag being correct; and the
**"No systematic search was run" banner**, which is honest and is contradicted by our own
marker rather than the reverse (B2).

Two unusual ones from reviews 16-17 that must also be defended:

- **empagliflozin already WITHDREW its own false "no published synthesis pooled these two
  trials" claim and named EMPEROR-Pooled.** A self-correction that landed. Given W5 and W6,
  it is worth saying plainly that this project does sometimes correct itself correctly.
- **The k=2 HKSJ penalty is particularly inappropriate on empagliflozin.** EMPEROR-Reduced
  and -Preserved were built as parallel sister trials with a patient-level pooling plan
  finalised in March 2017, before either enrolled anyone — same drug, dose, committees,
  randomisation, schedule, adjudication and endpoints. **9,718 randomised, 1,749 primary
  events, both individual HRs excluding 1**, and `df=1` gives `t = 12.706`. That interval is
  a property of having exactly two studies, not of sparse information, and a mechanical
  HKSJ width must not drive certainty without that design fact recorded beside it.

## A method caveat to adopt, not a defect

Converting a **non-parametric Hodges-Lehmann interval into a normal standard error is an
approximation.** The icosapent arithmetic reproduces exactly under that assumption, and a
definitive synthesis needs a method appropriate to the estimator. Recorded as a stated
limitation, because it is a modelling choice and not an error.

## Twenty-five reviews, one verdict shape

Lefamulin is one of the BETTER pages: the trials are right, the counts are right, the
arithmetic is exact, FDA confirms LEAP 1 + LEAP 2 are the complete pivotal CABP evidence
base at 1,289 randomised, and the reviewer would KEEP the synthesis. **Every defect found on
it is in the machinery.**

> ***That is the finding now. Twenty-five reviews, and the shape does not vary: the
> arithmetic reproduces, the selection and the description fail. A defect distribution that
> stable is a statement about where the fragility lives, and it is not in the statistics.***

## What is NOT fixed

- **Of ~60 rows, 5 are FIXED, 10 are PARTIAL-and-gated, and the rest are OPEN.**
- **No page is regenerated and no stored value is repaired.** Every FAIL sits in a baseline.
- **A6, the wrong headline number, is not corrected** — that means re-extracting from
  publications, not editing code.
- **W6 is not fixed**, and it is the cheapest correction available (`0.758 → 0.771`, the
  conclusion does not reverse).
- **The whole S family stands**: the pages are still not wired to `registry_adapter.py`.
- **Detection is not built here.** A sibling lane owns the oracle-free suite.
- **B5, B7, B8, B9 are not this lane's to fix**, and B3's local half is outstanding.

## Blockers recorded rather than fought

| gate | reason | introducing sha |
|---|---|---|
| `scripts/lint_recurring_traps.py` | `scripts/comparator_seed/phase3_measure.py:414`, `unanchored_substring`. **FALSE POSITIVE** — `held_pmid` is a `set`, so `in` is membership. The value arrives through a tuple-unpacked subscript, so no sound static narrowing was available, and this lane will not stamp an exemption on another lane's file | not named by the gate |
| `gates/gate20_correction_pins.py` | BROKEN in any clone lacking a LOCAL `paper-studio/manuscript-review` ref (class B6). Worked around here with `git update-ref` — an ENVIRONMENT fix, not a code change | not named by the gate |
| trunk gate chain | two guards on the trunk that their own gate refuses (class B5) | `e1ccb9f9c`, `66c1ed934` |
