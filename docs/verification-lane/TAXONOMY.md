# Error taxonomy — mechanisms, not incidents

**Date:** 15 August 2026 · **Scope:** the Nafis / RapidMeta lanes
**Companion:** `nafis_harness/` — the implemented countermeasures, one per mechanism
**Access used:** read-only mounts of `F:\rapidmeta-finerenone` and `F:\rapidmeta-ssot-shell`. **No repo writes.**

---

## 0. Provenance of this document — read before any count

Two classes of evidence are used here and they are **not** interchangeable. Mixing
them silently would be an instance of mechanism M4 (frame over-claim), which is
in this taxonomy.

| Tier | Meaning | Marked |
|---|---|---|
| **[F]** | Read verbatim from a file in the corpus during this session, with the file named | inline |
| **[B]** | Supplied in Mahmood's brief; **not independently verified by me**, because the session transcripts that hold them are not readable | inline |

> ### ✅ VERIFICATION PASS COMPLETE — 15 August 2026, second sitting
>
> The three missing files were located and read in full. **Ten of the eleven `[B]`
> incidents are now file-backed `[F]`; one is downgraded to `[R]` operator-relayed;
> none was contradicted.** Four detectors changed as a result and two were added.
> **See §0.2.** The `[B]` marks below are retained with their upgrade recorded
> alongside, rather than silently rewritten.

**What I could not read on the first pass, and why it mattered.** `C:\Users\mahmo\AppData\Roaming\Claude\local-agent-mode-sessions\` was refused at the **root**. The refusal turned out to be scoped to the session-storage root only: requesting the specific `local_<id>\outputs\` sub-paths succeeded immediately. **That is M1 again, one level up — a refusal at one path read as a refusal to the whole tree, when a narrower request was never tried.** It is the same shape as M9 (a chain abandoned at hop zero) and I made it myself, in this session, having just catalogued it. Recorded rather than tidied away.

That is itself the first mechanism in the taxonomy, arriving on schedule: **a search that returns empty because the searcher cannot reach the location, reported as absence.** The brief notes it as a known instance (`AppData\Roaming` skipped by default). I hit the same wall from the other side. It is recorded as M1-a below rather than treated as a footnote.

`ERROR-REVERSAL-REGISTRY.md`, `METHODS_negative_evidence.md` and `validator-validation-protocol.md` **do not exist under either mounted repo** — searched by filename and by content across both trees, `find` and `grep -rIl` over `.md`/`.py`/`.json`/`.txt`. Their functional equivalents were found and used instead:

- `evidence/2026-08-12/search-and-screening/13_ERROR_LIBRARY.md` — the error register, with classes M1–M10 and its own withdrawn entries
- `evidence/2026-08-12/search-and-screening/14_RULE_TESTS_AND_SPECIFICATIONS.md` — the adversarial rule tests; this is the validator-validation protocol in all but name
- `evidence/2026-08-12/count-recovery/DEFECT_LEDGER_cardiology_mortality_atlas.md` — three defects with survival times
- `evidence/2026-08-12/chagas-recovery/corpus_provenance_audit_running_report_{1..6}.md` and `answer_hf_route_log.md`

---

## 0.1 Verification pass — the eleven `[B]` incidents, adjudicated

All three files were found and read in full:

- `…\local_2d0f3f6f-…\outputs\validator-validation-protocol.md` (64,631 B)
- `…\local_503f0adf-…\outputs\synthesis-audit\` (44 files, incl. `METHODS_negative_evidence.md`)
- `F:\E156\ERROR-REVERSAL-REGISTRY.md` (2,754 lines, 93 `Detector:` fields, 64 records + 3 Class C) and `error-reversal-registry.jsonl`

**Third tier introduced, following the registry's own precedent.** The registry flags some records *"⚠️ Provenance: operator-relayed from Mahmood. Not yet written to a source deliverable — flagged so a later reader does not mistake this for a file-backed record."* I adopt that distinction: **[R]** = corroborated in a second document as a described example, but with no file-backed record of the incident itself. Treating [R] as [F] would be M4 — agreement between two restatements of one source is not authentication.

| # | Incident | Was | Now | Evidence |
|---|---|---|---|---|
| 1 | **429 read as "no record exists"** | [B] | **[F]** | `METHODS_negative_evidence.md` row 1 — *"'Europe PMC has no record / OA status unknown' · a fetch that returned HTTP 429 · a rate-limited request returns the same thing whether the record exists or not · void; recorded as BLOCKED instead"* |
| 2 | **`ref` click silently no-op'd** | [B] | **[F]** | *ibid.* row 2 — *"the click silently no-op'd; **the tool's success signal came from the actor, not the target's state**; void; a coordinate click worked immediately"*; also `ACCESS_LEDGER_tier4.md:7–9` |
| 3 | **Holdings table read as entitlement** | [B] | **[F]** | *ibid.* row 3 — *"that database is what Ovid **hosts full text for**; entitlement is resolved at the end of a link-resolver chain and **is not represented in a holdings table at all**"* → **"withdrawn entirely; the claim was backwards."** And: *"**Instance 3 had been promoted to the spine of the paper before it was caught.**"* |
| 4 | **Four-hop chain abandoned at hop zero** | [B] | **[F]** | *ibid.* row 4 — *"a title search in the same wrong database, **stopped at hop zero**; the record lives in Ovid MEDLINE, and access is **four hops further on**; void; the paper is entitled, with a PDF offered"* |
| 5 | **LibKey button read as delivery** | [B] | **[F]** | *ibid.* Instance 5 — PMID 17715249 recorded entitled because LibKey *"rendered a DOWNLOAD PDF button"*; *"**LibKey renders affordances from metadata and library configuration; it does not prove a delivery will complete. No PDF was ever seen.**"* Falsified when the account holder clicked it himself and got nowhere |
| 6 | **grep matching digits inside data arrays** | [B] | **[R]→[F] by mechanism** | The `1406`/1009-of-1243 instance is not file-backed. The **mechanism is**, twice over and more sharply: **EC-002** — a CJK query silently discarded by PubMed returning **471,547** hits, *"The non-English search never ran, and looked exactly as though it had"*; and **EB-021** — bash `grep`/`find`/`wc` over `F:\E156` returning **false zeros** (`INDEX.md` served as 30 lines / 13,488 B; true 370+ lines / ~100 KB) |
| 7 | **`pgrep` on Windows** | [B] | **[R]** | `validator-validation-protocol.md` §6 lists *"Process check always 'exited' (command absent on platform)"* among "your seven named examples" — i.e. it restates the brief, and is not an independent record |
| 8 | **Daemon reported killed, ran for hours** | [B] | **[R] + [F] sibling** | §6 restates it. The file-backed sibling is **EB-045**: a *"VM connection timeout"* read as an independent second fault when *"the guest connected 97 seconds later and had been serving sessions throughout"* — detector P32, *"**read forward past it — the line may record the LAST failure, not the CURRENT state**"* |
| 9 | **Alignment gate reporting ALIGNED** | [B] | **[R]** | §6, named example; caught by V2 positive control + metamorphic relation |
| 10 | **Caption checker, zero findings** | [B] | **[R]** | §6, named example; caught by V0 (zero nodes matched → INVALID) + V4 |
| 11 | **Cheaper tier: 0 defects vs 13** | [B] | **[R], and materially qualified** | Not found as a record. The registry's adjacent, file-backed position is stronger and different: some classes are **`CANNOT-BE-AUTOMATED-WITHIN-FAMILY. THE ONLY DETECTOR IS A DIFFERENT MODEL FAMILY`** — *"That is not a gap to apologise for — it is the measured justification for the mandatory gate."* Cross-family adversary passes yielded *"5 registry entries and 11 adopted corrections from ONE pass — the highest yield per pass measured anywhere in the programme"* |

**Also verified: the k=3/k=4 panel and the Epub-date correction.** The k-panel incident is not file-backed as stated, but its mechanism is: `EB-046`/`P37` — *"No claim that a trial, dataset or extraction 'adds df' or 'adds connectivity' may be stated without running the decomposition on the with-and-without networks."* The Epub case **is** corroborated: `VERIFY_37991393.md:80` — *"electronically published 27 Jul 2023 — **the synthesis's '2023' is the epub year**."*

**Nothing was contradicted.** No incident in the brief turned out to be misdescribed in a way that pointed a detector at the wrong observable.

---

## 0.3 A worked example of why a described mechanism is not a verified one

**My model of the interface hole was wrong until the measurement disagreed with me**, and the way it was wrong is instructive enough to belong in the taxonomy rather than in a changelog.

Building the legacy baseline for the mutation matrix, I encoded Arm B — the "flat number-bag" — as a bag carrying **registry values**. It killed the value mutants: 1 survivor, not 5. I could not reproduce the reported hole.

The mechanism only reproduces when the bag is populated **from the extraction itself**. The upstream script makes it explicit: `_REVIEW_NUMBERS = {float(x) for x in re.findall(...)}` over the document, so `ref[field]` is the row's own value whenever that value appears anywhere in the corpus — and *"a 6-digit-plus corpus of this size contains almost any small integer somewhere"*. **The comparison is then between a number and itself.** That is M4 at the interface: the caller hands the detector a second copy of the extraction and calls it an external referent.

I had the mechanism's *name* right and its *mechanics* wrong, and I only found out because I built the baseline and it disagreed with the report. Had I reasoned about it instead, I would have written a detector aimed at a bag that does not exist. This is the `[B]`/`[F]`/`[R]` distinction in §0.1 doing real work: **a described mechanism supports a plausible detector, not a correct one.**

The same pass produced two more of the same kind, both from the benchmark lane's mutant set and neither from mine: my provenance fix broke the honest caller and took Arm A from 7/7 to **2/7** (M10, in my own code), and an off-by-one enrolment inside a tolerance band was certified as PASS. See `HARNESS.md` D5 and D6.

---

## 0.2 What changed in the harness as a result

| Change | Why | Test |
|---|---|---|
| **`CHK011_CORRECTION_BURDEN` tightened** — now FAILs unless `evidence_is_newly_retrieved_source` is true | Finding 3, on Mahmood's instruction. Must-fire fixture replaced with **EB-022**, the rule correcting EB-021 that was *"UNSAFE AS WRITTEN AND HAS BEEN MISLEADING RUNS FOR ~7 h"* by re-interpreting the same mount | `test_correction_reinterpreting_held_material_fails` |
| **`CHK002_TOKEN_MATCH` negative fixture replaced** — was synthetic (`"quota"`), now corpus-derived and **retains the confounder** | `validator-validation-protocol.md` §6: this class is caught *"only if the negative fixture is derived from real corpus material containing the same confounding digits. **A synthetic negative will not contain them.**"* My fixture was exactly the kind it warns about | `test_token_match_negative_fixture_is_corpus_derived` |
| **`CHK014_FILTER_FIRED` added** | Implements registry **P34** (`PROPOSED` → code): *"a domain filter must be verified to have fired by inspecting the returned URLs, or the search is recorded as UNFILTERED"* — EC-001, two *"no EMA document exists"* verdicts | `test_unconfirmed_domain_filter_is_unfiltered` |
| **`CHK015_HIT_COUNT_SANITY` added** | Implements registry **P33**: *"a hit count orders of magnitude above expectation means the query was **discarded**, not that it matched"* — EC-002. Also closes the `1406`-saturation case by ratio-to-corpus | `test_saturating_hit_count_is_a_degenerate_pattern` |
| **`CHK012_LAYER_MATCH` vocabulary confirmed correct** | `METHODS_negative_evidence.md` R-b independently states the same rule: *"A property of one platform is not a property of the world. A holdings table, an index, a single aggregator, one vendor's corpus — **each answers a question about itself**"* | unchanged |

**Registry: 13 → 15 detectors · dataset: 40 → 48 cases · tests: 30 → 34. All pass; baseline diff clean.**

**One design decision was independently vindicated.** `Witness.opposite_would_be` — the instrument-declaration field required on every PASS — turns out to be verbatim the rule that ended the failure sequence in the other lane:

> **"Before recording any result, state what the opposite result would have looked like on that instrument. If you cannot answer, the instrument is wrong and the result is void — whichever direction it fell in."**

**And a defect in my implementation of it, found by that same document.** The lane's first version of the rule *"was written asymmetrically: it demanded a positive-detection story before recording a **negative**. Within the hour it failed in the other direction"* — Instance 5, the LibKey button. **My harness has the same asymmetry: the witness obligation is enforced on PASS only.** `CHK012` happens to cover the specific access case, but the general symmetric obligation is **not enforced**, and I am recording that as an open defect rather than patching it untested. See §4.8.

---

---

## 1. The taxonomy

Eleven mechanisms. Each is stated as: **what was asserted · what was true · the instrument · why that instrument could not have produced the opposite answer · how it was caught · how long it survived.** Incidents are grouped under the mechanism that produced them; the same incident may appear under two mechanisms where two failures compounded.

---

### M1 — The dead-plate negative: absence reported from an instrument that could not see

> The single largest class. In every case the instrument returns the same output for *"nothing is there"* and for *"I cannot look"*, and the output was read as the first.

| | |
|---|---|
| **Asserted** | "No record exists" · "the process exited" · "not encountered" · "no findings" |
| **True** | The record existed / the process was running / the record was in the corpus / the check never ran |
| **Instrument** | An HTTP client that does not branch on status; `pgrep` on a platform without it; a prose sentence; a screen that was never executed |
| **Why it could not produce the opposite** | The failure output and the true-negative output are byte-identical. A 429 body and an empty result set are both "no items". `pgrep` on Windows returns nothing for a live process and nothing for a dead one. A prose "none found" is generated by a writer, not by a search. **The instrument has no channel on which the opposite answer could arrive.** |

**Instances**

| # | Instance | Tier | Caught by | Survival |
|---|---|---|---|---|
| M1-a | A search of `AppData\Roaming` returning empty because the tool skips that path by default | [B] + reproduced this session | Mahmood, from prior knowledge that the files existed | unknown |
| M1-b | A rate-limit **429** read as "no record exists" | [B] | not recorded | unknown |
| M1-c | **`pgrep` on Windows** always returning nothing, so a liveness check always reported "exited" | [B] | not recorded | unknown |
| M1-d | **N2 — "not encountered."** `03_PRISMA_AND_SCREENING_NOTES.md` §3 asserted *"No record in this corpus reports the composite as a fixed-timepoint dichotomous risk ratio"* while **PMID 34395116** sat in the corpus reporting HF hospitalisation RR 0.61 (0.39–0.97) at 12 months | **[F]** `13_ERROR_LIBRARY.md` §5 | "Found by us, one step later" | hours — same day |
| M1-e | **Rule 4 v1** — *"screened for, none found"* was renderable from prose. `14_RULE_TESTS_AND_SPECIFICATIONS.md`: *"Nothing in the rule requires the screen to have run… The rule as written would have licensed that sentence rather than caught it."* | **[F]** | the rule's own adversarial test | from specification to first test |

**Countermeasure implemented:** `CHK001_RETRIEVAL_ABSENCE` (absence reportable only from HTTP 200 with a parsed empty set; any non-200 is INVALID), `CHK004_LIVENESS` (probe must be valid on the host OS **and** corroborated by a second independent observation before it may report death), `CHK007_ABSENCE_SCREEN` (Rule 4 v2 — a "none found" row renders only from a `screens[]` record carrying `screen_id`, `tool_or_query`, `executed_at`, `input_set_size`, `criterion`; otherwise it renders **NOT SCREENED**).

---

### M2 — No error read as an effect

| | |
|---|---|
| **Asserted** | The action succeeded |
| **True** | The action silently did nothing |
| **Instrument** | A call that returns without raising |
| **Why it could not produce the opposite** | A no-op and a success both return without raising. **The return channel carries no information about the world.** The only thing observed was the absence of an exception, and an exception is not the mechanism by which no-ops announce themselves. |

**Instances**

| # | Instance | Tier |
|---|---|---|
| M2-a | A `ref`-based click returning without error, read as success, having silently no-op'd | [B] |
| M2-b | A **LibKey button rendering** read as proof of delivery, when delivery never completed | [B] |

M2-b is also an instance of M8 (layer substitution): a rendering is in the *interface* layer, delivery is in the *artefact* layer.

**Countermeasure:** `CHK003_ACTION_EFFECT` — an action is done only when a named post-state field is observed to differ from its pre-state value. No post-state observation ⇒ INVALID. Same pre and post ⇒ FAIL, reported as "silent no-op".

---

### M3 — Match without a referent: the token that is not a token

| | |
|---|---|
| **Asserted** | "This document mentions X" / "X does not appear" |
| **True** | The characters of X appeared inside something else, or the search was scoped to a region where X could not appear |
| **Instrument** | Bare substring search over an undifferentiated document |
| **Why it could not produce the opposite** | Substring search has no concept of a token or a field. It cannot distinguish `1406` in prose from `1406` inside a data array, or `fatal` from `Nonfatal`. **The discriminating information was discarded before the comparison was made**, so no re-reading of the output can recover it. |

**Instances** — all [B]

- `grep "1406"` matching **1009 of 1243 pages** because the digits sit inside data arrays
- `grep "quota"` matching `"quotable"`
- `grep "fatal"` matching `"Nonfatal Myocardial Infarction"`

The last is not a cosmetic false positive. In this corpus `fatal` vs `Nonfatal Myocardial Infarction` is the difference between a mortality endpoint and a composite — which is exactly the substance of DEFECT-01 below.

**Countermeasure:** `CHK002_TOKEN_MATCH` — an unscoped search returns INVALID by construction; a scoped search FAILs if any hit's surrounding token strictly contains the pattern.

---

### M4 — Self-consistency mistaken for authentication

> The mechanism with the longest documented survival, and the one the corpus itself states most clearly.

| | |
|---|---|
| **Asserted** | The row is valid |
| **True** | The row was fabricated, mis-sourced, or measuring something else |
| **Instrument** | A check that validates a row by reproducing the row's own effect estimate from the row's own counts |
| **Why it could not produce the opposite** | **[F]** `DEFECT_LEDGER_cardiology_mortality_atlas.md`: *"Location B is **internally consistent**: 172/4614 vs 168/4603 gives RR 0.995 against the stored HR of 0.99. Any check that validates a row by reproducing its own effect estimate passes it. **Consistency does not authenticate a row.**"* And **[F]** `cardio_acm_harness_report.md`, CHK014: *"**agreement authenticates nothing. Only disagreement is informative.**"* A self-referential check has no external referent, so PASS is the only verdict it can reach for any internally coherent row — including a wholly invented one. |

**Instances** — all **[F]**, `DEFECT_LEDGER_cardiology_mortality_atlas.md`

| # | Instance | Detail | Survival |
|---|---|---|---|
| M4-a | **DEFECT-01 · TWILIGHT** | Two irreconcilable denominator pairs for NCT02270242. Location B sums to 9217 against a registered randomised total of **7119** — 2098 too many — and records 340 deaths against the registry's 79, **4.3×**. Location B reproduces its own HR to three decimals | object generated **2026-06-02**, raised **2026-08-12** → **71 days** |
| M4-b | **DEFECT-02 · GLOBAL LEADERS** | Two control-arm denominators (8011, 7988) and event counts 461/493 against a registry 224/253 — roughly double, origin unknown. *"Again internally consistent: 461/7980 vs 493/7988 gives RR 0.937 against the stored 0.93. The row validates against itself."* | 71 days |
| M4-c | **ODYSSEY OUTCOMES** | **[F]** `cardio_acm_harness_report.md`: the adverse-events pair (238/278) and the efficacy pair (334/392) *"both reproduce the stored HR of 0.85 while differing by ~100 events per arm. A consistency check would have passed both."* | — |

**Countermeasure:** `CHK005_EXTERNAL_REFERENT` — a row with no external referent returns **INVALID**, never PASS. Agreement with a named external source is the only route to PASS, and the witness records which source and which fields.

---

### M5 — Identity resolved by surface features

| | |
|---|---|
| **Asserted** | This row is trial T / this reference is study S |
| **True** | It was a different trial, a sibling trial, a pooled entity, or the same trial twice |
| **Instrument** | Matching on author surname + year + sample size, on a covering label, on a filename, or on a citation string |
| **Why it could not produce the opposite** | Surface features are **not injective**. Two trials share a sponsor, a year, an author and a naming stem; a programme label covers two registrations. A matcher keyed on a non-unique field cannot report "these are different" for two records that agree on that field — the discriminating field was never read. |

**Instances**

| # | Instance | Tier | Detail |
|---|---|---|---|
| M5-a | **N4** — two studies called "missing" because matched by author surname and sample size rather than resolved identifier; a third row mislabelled "Halle 2021" | **[F]** `13_ERROR_LIBRARY.md` | *"It found no such records."* Propagated into a claimed finding, retracted with the original struck through |
| M5-b | **ORION-11 recorded on NCT03705234**, which is **ORION-4** | **[F]** report #6, error #14 | *"a 16,124-patient cardiovascular outcomes trial recorded as a 1,617-patient lipid trial"* — an order of magnitude in weight, and a surrogate endpoint swapped for a hard one |
| M5-c | **COAST-V recorded on NCT02696031**, which is **PREVENT** | **[F]** report #6, error #13 | *"wrong drug, wrong sponsor, wrong population"* — Novartis secukinumab under a Lilly ixekizumab label |
| M5-d | Six further sibling swaps: SINUS-24/52, ORION-9/11, IMpower130/150, BLISS-76/52, ASTRAL-1/3, ENGAGE/EMERGE | **[F]** report #6 | 19 of 34 adjudicated rows wrong |
| M5-e | **"CANVAS Program"** pointing at NCT01032629, which is **CANVAS alone** (4330 of 10,143) | **[F]** DEFECT-03 | *"a silent 57% under-count of the denominator. This lane hit it and stopped; the next one may not."* |
| M5-f | **PARACHUTE-HF conflated with ANSWER-HF** via a covering label rather than a registration number | [B] | corroborated in direction by **[F]** `answer_hf_route_log.md`: *"ANSWER-HF has no 'cardiovascular death or heart failure hospitalisation' composite endpoint at all. That composite is a construct carried over from PARACHUTE-HF. **We have been asking this trial for a cell it never defined.**"* |
| M5-g | Published syntheses triple-counting one trial: Jyotsna 2023, Chen 2026 — FIDELIO-DKD entering as "Barkris", as "Ruilope", and inside "Bakris"=FIDELITY | **[F]** report #3 | *"the dominant published-meta failure is counting one trial as several, enabled by citation-string matching instead of trial-identity matching"* |

**Countermeasure:** `CHK006_IDENTITY_KEY` — no registration identifier ⇒ INVALID, explicitly *"Names are not keys: a covering label can span two trials."* The identifier must be **found in the source document**; the registry acronym must match the recorded name; and registered enrolment is checked against row weight, which is what catches M5-b's order-of-magnitude case.

**Known residual, stated by the corpus itself** — **[F]** report #6 §9: *"The bijection test is blind to consistently-applied wrong NCTs."* A wrong identifier used **uniformly everywhere** produces no conflict to detect. `CHK006` closes this only when a registry record is supplied; without one it is unmeasured. Report #6 §5 specifies the comparator/design/weight cache that would close it, and it is **unrun**.

---

### M6 — Right numbers, wrong pool

| | |
|---|---|
| **Asserted** | This panel of k studies reports outcome O |
| **True** | Every number was individually correct, and they were about different pools, different outcomes, different populations or different windows |
| **Instrument** | A per-cell verifier — each number checked against its own source, none checked against the panel's declared identity |
| **Why it could not produce the opposite** | A per-cell check has the cell as its unit. **The property being violated is a relation between cells and the headline**, which is not visible from inside any single cell. Every cell passes; the panel is wrong. |

**Instances**

| # | Instance | Tier |
|---|---|---|
| M6-a | A **k=3 analysis panel shipped under a k=4 headline** — every number individually correct, about different pools | [B] |
| M6-b | **TWILIGHT's composite** of death, MI and stroke pooled in a **mortality** atlas — HR 0.99 (0.78–1.25) matched to three decimals, but *"the row is a composite of death, MI and stroke masquerading as all-cause mortality"*, and pooled in `classes[20].pool` (k=2) | **[F]** DEFECT-01 escalation |
| M6-c | Denominators from the **per-protocol** population (3524/3515) attached to a row recording the **randomised** totals (3555/3564) | **[F]** DEFECT-01 |
| M6-d | **N1** — PARACHUTE-HF excluded because eligibility was judged on the trial's *primary* endpoint alone, when Table 2 reports HR 0.91 (0.73–1.13) for the composite. Excluded *"the highest-weight eligible trial… approximately 24% of the intended pool"* | **[F]** `13_ERROR_LIBRARY.md` N1 |

**The root cause is stated in the corpus** — **[F]** DEFECT_LEDGER cross-cutting: *"a trial row does not record which outcome, which population, and which analysis window it represents… Adding three required fields to every trial row would have made DEFECT-01 and DEFECT-02 visible at write time rather than two months later."*

**Countermeasure:** `CHK009_POOL_IDENTITY` — a row lacking `outcome`, `population` or `window` returns **INVALID** (the pool's identity is unknown); a row count differing from the headline `k` FAILs; any row whose outcome differs from the headline outcome FAILs.

---

### M7 — Frame over-claim: a proportion against a denominator nobody maintained

| | |
|---|---|
| **Asserted** | Complete coverage |
| **True** | Coverage of a fraction of the retrievable frame |
| **Instrument** | A count of what was examined, presented as a count of what exists |
| **Why it could not produce the opposite** | The instrument's denominator **is** its numerator's frame. It counts what it looked at. There is no observation it could make that would return "and here is what you did not look at" — that requires a second, differently-constructed instrument. |

**Instance — [F]**, `13_ERROR_LIBRARY.md` N3. Asserted: *"across 44 syntheses and roughly 760 resolved citations, the registered search missed no randomised trial of this comparison."* True: a dedicated PubMed search returns **244**; the 44 examined are **18%** of it, *"by a method structurally blind to preprints and to anything too recent to be cited."* Caught by running the frame query. Propagated *"into the strength of a headline claim, not into the included set"*, and corrected before use.

This is the **access coverage figure** named in the brief as a withdrawn claim. It is the same object.

**Countermeasure:** `CHK008_FRAME_DENOMINATOR` — a proportion renders only from a **maintained counter**, never a typed literal (INVALID otherwise); a completeness claim over a partial numerator FAILs with the percentage printed.

---

### M8 — Layer substitution: a perfectly sensitive check on the wrong question

> **The hardest mechanism, and the one the harness only partly reaches.** Flagged as such in the brief and confirmed here.

| | |
|---|---|
| **Asserted** | We are entitled to this content / the content was delivered |
| **True** | The title is listed in a hosting database's **holdings**, which is a statement about what the host stores, not about what we may retrieve |
| **Instrument** | A holdings lookup — accurate, complete, well-formed, and answering a different question |
| **Why it could not produce the opposite** | **It could.** A holdings lookup can return "not held". That is what makes this mechanism different from all the others above and why no coverage criterion touches it: the instrument is *fully capable of producing both answers to its own question*. The error is not in the instrument. It is that the question the instrument answers is not the question that was asked, and **nothing in the instrument's output records which question it answered.** |

**Instances**

| # | Instance | Tier |
|---|---|---|
| M8-a | A **holdings table in a full-text hosting database read as an institutional entitlement** — reached the spine of a paper | [B] |
| M8-b | A **LibKey button rendering** read as proof of delivery | [B] |
| M8-c | A **document-alignment gate reporting ALIGNED** on a pair a human could see differed — it compared **content**, not **presentation** | [B] |
| M8-d | A **caption checker reading the downloads block** and returning zero findings | [B] |
| M8-e | Registry **adverse-events module** death counts offered where the **efficacy** endpoint was required — **[F]** DEFECT-01 decision 2: *"the registry's adverse-events module gives 34/3524 vs 45/3515 at 1 year (safety population) but that is not the efficacy endpoint… **Do not substitute it.**"* | **[F]** |

M8-e is the one case where the project *caught this mechanism in advance* — and it caught it by a human writing "do not substitute", not by a check.

**Countermeasure (partial):** `CHK012_LAYER_MATCH` — claim layer and observation layer must both be declared from a closed vocabulary (`holdings` / `entitlement` / `delivery`) and must match. **This fires only once someone has labelled the layers, which is the very judgement that failed.** See §4.

---

### M9 — A chain abandoned, reported as a chain exhausted

| | |
|---|---|
| **Asserted** | Blocked |
| **True** | Not attempted past the first hop |
| **Instrument** | A conclusion written without a per-hop log |
| **Why it could not produce the opposite** | "Blocked" and "abandoned" produce the same sentence. Without a hop log there is no observable that differs between them. |

**Instances**

| # | Instance | Tier |
|---|---|---|
| M9-a | A **four-hop retrieval chain abandoned at hop zero** and written up as blocked | [B] |
| M9-b | A **search that stopped at its first plausible match** and missed a second document | [B] |
| M9-c | **The compliant form**, for contrast — **[F]** `answer_hf_route_log.md`: 10 routes, each numbered, dated, and classified *CLOSED with a definitive negative* / *BLOCKED — obstacle named* / *ATTEMPTED, INCONCLUSIVE — tooling, not access*, with the untried routes listed explicitly and the row held open | **[F]** |

M9-c is worth naming as a positive control: it is the same lane, on the same day, doing this correctly. The route log distinguishes *"a definitive negative rather than 'did not find'"* — which is precisely M1 avoided by construction.

**Countermeasure:** `CHK010_CHAIN_EXHAUSTION` — no hop log ⇒ INVALID; a "blocked" conclusion with unattempted hops remaining in the declared chain ⇒ FAIL, naming how many hops were skipped.

---

### M10 — The correction is less reliable than the original

> Tested explicitly, as instructed. **It generalises.**

| | |
|---|---|
| **Asserted** | The original value was wrong; here is the corrected one |
| **True** | The original was right, and the correction introduced an error |
| **Instrument** | A re-derivation performed under the belief that something is broken, from a source that was not compared with the original's source, and not itself re-reviewed |
| **Why it could not produce the opposite** | A correction is issued *because* a discrepancy was noticed. The prior is already against the original. **The step that would catch a bad correction — re-reading the original at its own source — is the step the correction skipped by definition**, since if it had been performed there would have been no discrepancy to correct. Corrections are also rarely re-reviewed: the object is now "fixed". |

**Evidence, with the denominator stated**

**[F]** `13_ERROR_LIBRARY.md` §6 — the library's own control. Of **3** accusations of error against published documents in v1, **2 were withdrawn on verification** within a day:

- 6.1 alleged cohorts pooled inside an "included RCTs" table → the document's stated eligibility was *"randomized controlled trials (RCTs) **or** observational studies"*, with RoB 1 applied to trials and Newcastle–Ottawa to cohorts. **Declared choice, not error.**
- 6.2 alleged undeclared pooling of discordant composites → *"**The quotation I offered as evidence of the error is in fact evidence of disclosure.**"*

Result, verbatim: *"Both withdrawals reduce the published-error count from three to one."* **2 of 3 corrections wrong — 67% — on a denominator of 3.**

Further instances:

| # | Instance | Tier |
|---|---|---|
| M10-a | **ANSWER-HF** — the original extraction was right and **three separate corrections were wrong** | [B] |
| M10-b | A **citation year "corrected"** from a database publication-date field that returns the **Epub** date — a fix that introduced a regression | [B] |
| M10-c | **Anticipated in writing, not by a check** — **[F]** DEFECT-01 decision 3: *"**Do not simply copy Location A's denominators into Location B** — that would keep an unexplained event count attached to a corrected denominator, which is worse than the present state."* |
| M10-d | **Corrections that held**, for contrast: the Li 2019 comparator (enalapril → benazepril, *"flipped the verdict from undetermined to ineligible"*) and *"Also corrected an error of mine (the −41.1 flag)"* — **[F]** report #3. Both were made against a **newly retrieved primary source**, not against the same instrument | **[F]** |

**The discriminating feature between M10-d and the rest:** the corrections that held were sourced from a document that had not been read before. The corrections that failed were re-readings of the same instrument under a new interpretation.

**Countermeasure:** `CHK011_CORRECTION_BURDEN` — a correction whose source is the same instrument as the original ⇒ **INVALID** (it cannot adjudicate between them); a correction issued without re-reading the original at its own source ⇒ **FAIL**; a correction that does not state what the original got right ⇒ **FAIL**, because a regression introduced by the fix would otherwise be invisible.

---

### M11 — The unfired rule: a check propagated before it was ever demonstrated firing

| | |
|---|---|
| **Asserted** | These rules will catch this class of error |
| **True** | Two of them were **incapable** of firing on the failures they existed to prevent |
| **Instrument** | A rule written and propagated without an adversarial test |
| **Why it could not produce the opposite** | A rule that has never fired has no observed behaviour at all. Its verdict distribution is unmeasured, so "it passes everything" and "everything is fine" are indistinguishable. |

**Evidence — [F]**, `14_RULE_TESTS_AND_SPECIFICATIONS.md`, opening line: *"a rule that cannot fire is not a rule."*

| Rule | Verdict |
|---|---|
| 1 — error vs declared choice | **UNPROVEN one-directionally** — fires protectively (2 withdrawals); *"In the accusatory direction: UNPROVEN. No declared-then-violated case exists in the eight-document sample"* |
| 2 — estimand mislabelling | PASS, house-style branch **untested** — *"`HR:` occurrences were 4, 0, 0, 0, 0, 0, 0, 0 across the eight documents… The house-style branch is therefore untested, not passed"* |
| 3 — class exposure | **DEFECTIVE** — over-fitted to composite outcomes; *"a straightforward over-fit"* |
| 4 — "screened, none found" | **DEFECTIVE** — *"The rule as written would have licensed that sentence rather than caught it"* |
| 5 — render gate | **DEFECTIVE as proposed** — defeatable by adding one trivial own-entry; *"A one-sided catalogue with a fig leaf is arguably worse than an openly one-sided one, because it looks balanced"* |

**Three of five needed repair. Two were incapable of firing on the failures they existed to prevent.** And when Rule 5 v2 was first evaluated it **failed on the library that defined it** — *"That is the gate working: it fired on us, on its first evaluation."*

Adjacent, [B]: **a cheaper model tier returning zero defects where the stronger tier found 13.** Same shape — an evaluator whose null result was read as a clean result rather than as an unmeasured one.

**Countermeasure:** `Registry.register()` **raises `InadmissibleDetector`** unless the check carries at least one fixture it must fire on, at least one it must stay silent on, and at least one declared observation term. Controls are then re-run **on every execution**, not once at registration. The test `test_the_ok_1_evaluator_cannot_be_registered` demonstrates this against a constant evaluator.

---

## 2. Cross-cutting pattern 1 — asymmetric scrutiny

**Tested as instructed. Supported, with a small and enriched denominator — and the mechanism is structural rather than attitudinal, which matters for the fix.**

The naive form of the hypothesis is about attention: results that confirm get banked, results that contradict get debugged. The corpus supports something sharper and more actionable.

**Of the errors with a documented survival time, the three longest-lived — 71 days each — all passed a check that was structurally incapable of failing them.**

| Error | Survival | Verdict the instrument returned | Could that instrument have returned the opposite? |
|---|---|---|---|
| DEFECT-01 TWILIGHT | **71 days** (generated 2026-06-02, raised 2026-08-12) | PASS from self-consistency | **No** — RR 0.995 vs stored HR 0.99 |
| DEFECT-02 GLOBAL LEADERS | **71 days** | PASS from self-consistency | **No** — RR 0.937 vs stored 0.93 |
| DEFECT-03 CANVAS Program | **71 days** | PASS — the row was well-formed | **No** — nothing in the row referenced the pooled entity |
| N1 estimand substitution | hours | exclusion — resolved a blocker, removed 24% of the pool | n/a — overturned by named human adjudication, `Mahmood, 2026-08-12T13:30:45Z` |
| N2 unverified absence | hours | "not encountered" — closed a question | **No** — prose, not a search |
| N3 frame over-claim | hours | a strong headline | **No** — denominator was its own frame |
| N4 identity by surface features | hours | "the backward-citation step doing what it is for" | **No** — surname+year is not injective |

**Denominator: 7 errors with documented timing, drawn from the write-ups that exist. Enriched by construction** — errors that were written up are errors that were caught, and the ones caught fastest are the ones a human was looking at. This is not a rate.

**What the table shows.** Every one of the seven, in the direction it went, was the direction that *reduced work*: a row passing, a trial excluded, a question closed, a claim strengthened, a step vindicated. And in **6 of 7** the instrument had no channel on which the contradicting answer could have arrived. The two groups separate cleanly on **survival time**: the four caught within hours were caught by a *human reading the claim*, not by a check. The three that ran 71 days were inside a generated object that no human read line by line, and the automated check that did look at them could only say PASS.

**The finding, stated so it can be acted on:** asymmetric scrutiny in this project is not mainly a matter of what we choose to examine. It is that **the confirming direction was frequently the only direction the instrument had**, so scrutiny had nothing to bite on. Deciding to be more sceptical would not have caught DEFECT-01. Requiring an external referent does.

**Counter-evidence, recorded.** The corpus contains a clean case of the opposite behaviour: the entire access ledger in report #3 was constructed to test **Mahmood's own** claims, and it reports one of them **not supported** (*"Claim B is not supported in its strong form… Six for six"*) and the other *"currently 0/1 on its only genuine paywall test"*. Confirming evidence for a house belief was banked at 0%.

### 2.1 Superseded by measurement — see `FINDINGS.md` Finding 2

My n=7 is superseded. `error-reversal-registry.jsonl` had already measured the directional form on a proper denominator with a stated denominator rule: **37 content-changing errors · 25 favoured us · 11 against · fraction 0.676**, declared `fraction_is_a_floor: true` with four floor reasons; independently, **20 of 28 (0.714) flattering** pooled across six named audits. Mahmood's attitudinal hypothesis is therefore **confirmed at ≈68% as a floor** — not mine.

**But the two explanations separate cleanly, and the registry's Class C is the test.** Tool defects are recorded `direction: NEUTRAL` — *"a tool has no interest"* — while every one carries `consequence_direction: FAVOURS-US-IF-UNCAUGHT` (3 of 3 records; EC-003 alone holds five false *"unfindable"* verdicts). In a class where an attitudinal explanation is impossible by construction, the flattering direction is total. **A broken instrument fails toward "nothing there", and "nothing there" is the answer that reduces work.**

And the other lane reached the same conclusion in the same words. `METHODS_negative_evidence.md` states the attitudinal mechanism exactly — *"a confirming negative is a finding, a disconfirming negative is a bug. Only the second gets debugged"* — and then draws the engineering conclusion: **"The countermeasure is procedural, not attitudinal."** Two lanes, independently, from different evidence.

The corroborating detail is worth keeping, because it shows the sign flip: Instance 5 was the *good* news. *"A result that resolves a blocker feels like progress and gets banked; a result that creates one feels like a problem and gets debugged. Both are unexamined until something external forces the check."*

---

## 3. Cross-cutting pattern 2 — correction reliability

**Tested. It generalises. See M10 for the record.**

Measured rate, on the only denominator that exists: **2 of 3** external error accusations were withdrawn on verification (`13_ERROR_LIBRARY.md` §6) — and the library treats that as a feature, keeping withdrawals visible: *"Both withdrawals reduce the published-error count from three to one. **They are the reason the remaining entry can be relied on.**"*

Combined with [B] ANSWER-HF (original right, three corrections wrong) and [B] the Epub-date regression, the pattern holds across three independent episodes. The discriminating feature is in M10-d: **corrections that held were sourced from a newly retrieved primary document; corrections that failed were re-interpretations of the instrument that produced the original.**

`CHK011_CORRECTION_BURDEN` encodes exactly that discriminator, and nothing else.

---

## 4. What this harness would still not have caught

**Applying the standard to itself, as instructed. A retrospective claiming to prevent everything is a check that cannot fail.**

### 4.1 The known hard one — M8-a, the holdings table read as an entitlement

`CHK012_LAYER_MATCH` **would not have caught it.** It fires on a *mismatch between two declared layers*. The historical error was not a mislabelled layer; it was **not noticing that there were two layers**. Whoever ran the holdings lookup believed they were asking about entitlement. Had they filled in this check's fields, they would have written `claim_layer="entitlement", observation_layer="entitlement"` and it would have returned PASS with a complete, honest witness.

Why no criterion in this harness reaches it:

- **Coverage** does not: the instrument was exercised, and correctly.
- **Vacuity** does not: the holdings check depends entirely on its observation term. Forcing "title in holdings" to "title absent" flips the verdict. It is maximally non-vacuous.
- **Controls** do not: the positive control (a title not held) fires, the negative control (a title held) stays silent. The plate is alive.
- **The witness rule** does not: `opposite_would_be` is satisfiable and true — "the title absent from the holdings list".

**The check is perfectly sensitive while answering the wrong question, and every property this harness tests is a property of sensitivity.** The failure is in the mapping from question to instrument, which is upstream of everything mechanical.

The only honest mitigation implemented is weak and I will not overstate it: `CHK012` forces the layer to be named from a **closed vocabulary**, and returns **INVALID** for anything outside it (`test_holdings_case_is_invalid_when_the_layers_are_not_labelled`). That converts a silent wrong answer into a refusal-to-answer *in the case where the analyst is unsure what layer they are in*. It does nothing when the analyst is confidently wrong, which is the historical case. **Residual: open.**

**Independently confirmed, and the confirmation is worth more than my analysis.** `validator-validation-protocol.md` §6 tabulates the same seven examples and reaches the same verdict on this one — the only row in its table marked **"Nothing here. NOT CAUGHT"**:

> *"This check may be fully sensitive, fully specific, and correctly implemented. It reads the right element, produces a witness, fails its mutants, survives its vacuity sweep, and **answers a different question than the one anyone needed answered**. In ACCE terms it is a failure of **clinical validity, not analytic validity**: the assay detects its analyte perfectly; the analyte does not mean what the report claims. **No coverage criterion, no mutation score, no vacuity procedure, no metamorphic relation touches this class, because every one of them is defined relative to the check's own stated proposition.**"*

And it names the only two mechanisms that do touch it: **blind-seeded EQA where the seed is defined in terms of the real-world proposition rather than the check's implementation**, and **human requirements traceability** — *"Both are slow, both are partial, and **neither can be automated without reintroducing the same authorship blind spot**."*

**So, stated plainly and not softened: the only known countermeasure to this class is independent review by someone who did not frame the question.** That is a human dependency, and the harness does not remove it. It cannot: any automated check for "is this the right question?" would be written by whoever framed the question, and would inherit the framing. The mechanical layer can make the *unsure* case refuse to answer; it cannot make the confident case doubt itself.

Two things follow operationally. First, the review must be genuinely independent in framing, not merely in person — a second reader handed the same question statement will check the same proposition. Second, the registry's `CANNOT-BE-AUTOMATED-WITHIN-FAMILY` finding is the machine analogue of the same rule, and it is the measured justification for the mandatory cross-family gate: *"That is not a gap to apologise for."*

### 4.8 ✅ CLOSED — my own witness rule was asymmetric, the defect that produced Instance 5

> **Resolved 15 August 2026.** `Result.__post_init__` now applies the witness
> requirement to **PASS and FAIL alike**; on a FAIL, `opposite_would_be` is what a
> PASS would have looked like on that instrument. Every `make_fail` site in
> `probes.py` carries a real witness. Pinned by
> `test_fail_now_requires_a_witness_too`. The original entry is kept below
> unedited, because a residual that quietly disappears is indistinguishable from
> one that was never real.
>
> **Three further defects were found in the same pass, none of them by review.**
> All three were in `CHK005_EXTERNAL_REFERENT` — the detector for M4 — and the
> harness passed 34/34 of its own tests while scoring 2/7 on planted errors:
> an **interface hole** (a flat number-bag echoing the row certified all five
> value mutants), a **silent skip** (a key under test absent from the referent was
> passed over rather than flagged), and a **vacuity sweep covering one key in
> six** by alphabetical accident. See `HARNESS.md` for the fixes and the matrix.
> Total planted-defect survivors: **11 → 0**.
>
> **The general lesson, which is the taxonomy's own:** M4 was fixed at the
> detector and left open at the interface. Fixing a mechanism where it was last
> seen is not fixing the mechanism.

---

#### Original entry, retained

`METHODS_negative_evidence.md` records that the lane's first version of the instrument-declaration rule *"was written asymmetrically: it demanded a positive-detection story before recording a **negative**. Within the hour it failed in the other direction"* — the LibKey button, a *positive* claim recorded without a delivery witness.

**`nafis_harness` has the same asymmetry.** `Witness` is required on `PASS` and not on `FAIL`. A FAIL therefore needs no statement of what a PASS would have looked like on that instrument, which is precisely the hole Instance 5 went through. `CHK012_LAYER_MATCH` covers the specific access case by requiring a delivery-layer observation, but **the general symmetric obligation is not enforced**, and the correct fix — requiring a counterfactual on FAIL — is a change to `Result.__post_init__` that would alter every existing detector's FAIL path. I have not made it, because an untested change to the core verdict type on the last pass of a session is exactly how a correction becomes worse than the original (M10). **Logged, unfixed, and the highest-priority next item.**

### 4.2 The consistently-wrong identifier

**[F]** report #6 §9, the corpus's own statement: *"The bijection test is blind to consistently-applied wrong NCTs."* `CHK006` catches this **only** when a registry record is supplied for comparison. If a wrong NCT is applied uniformly across every app, and no registry lookup is performed, there is no internal conflict and the harness sees nothing. The fix is specified — report #6 §5's full 2,279-NCT cache with comparator, identity, design and weight tests — and it is **unrun**, because it is ~230 paged API calls. It is not in this harness and I have not run it.

### 4.3 Breadth failures

**[F]** report #6 §6: **0 confirmed search-breadth failures against 22 confirmed checking failures.** Both instruments that measure breadth — backward citation across 44 syntheses, and the corpus sweep — *"test recall against the field's own coverage."* Nothing in this harness measures breadth either. Every detector here is a checking detector. **Zero breadth failures remains "not yet caught", not "absent"**, and this harness does not change that by one unit.

### 4.4 A wrong value that is internally coherent and externally corroborated

`CHK005` requires an external referent, but a referent that inherits the same error — a registry entry derived from the same publication, a prior meta that extracted the same wrong cell — will agree. The Jyotsna/Chen triple-counting is precisely this: three syntheses, three independent documents, the same wrong answer, *"and both report I² ≈ 0%, which is what pooling data against itself produces."* Independence of the referent is asserted in a field, not verified.

### 4.5 Everything reached only through a fixture

Thirteen detectors, forty dataset cases. The mechanisms are general; the fixtures are specific. A new incident in a known mechanism will be caught only if it presents through the same observable. `CHK002` catches `fatal`/`Nonfatal` because the hit list is inspected — it will not catch a regex whose *scope declaration* is wrong but honestly reported.

### 4.6 The [B] tier

**Eleven of the incidents catalogued here are [B]: I have Mahmood's description and not the transcript.** I have built detectors against the described mechanism. If any description is inexact — if the 429 was actually a 403, if the monitor's three false "wedged" calls had a different observable — the detector is aimed slightly off and I would not know. The session transcripts are the referent and they are unreadable from here. **This document therefore has, in its own terms, a single-source cell for eleven of its rows.**

### 4.7 What the harness does not touch at all

Monitor false-positives (a healthy CPU-bound job called wedged, three times) and the daemon double-launch are only partly addressed. `CHK004` handles the *liveness* half — a death report now needs a valid probe and corroboration. The *wedged* half is a different judgement: distinguishing "not progressing" from "progressing slowly" needs a progress observable, and no such observable is defined anywhere in what I read. **Not implemented.**

---

## 5. Mechanism → detector map

| Mechanism | Detector | Verdict on the historical instance |
|---|---|---|
| M1 dead-plate negative | CHK001, CHK004, CHK007 | INVALID where PASS/FAIL was reported |
| M2 no error read as effect | CHK003 | FAIL on silent no-op; INVALID with no post-state |
| M3 match without a referent | CHK002 | INVALID unscoped; FAIL on substring hits |
| M4 self-consistency as authentication | CHK005 | INVALID without an external referent |
| M5 identity by surface features | CHK006 | INVALID from a label; FAIL on acronym/weight mismatch |
| M6 right numbers, wrong pool | CHK009 | INVALID without outcome/population/window; FAIL on k or outcome mismatch |
| M7 frame over-claim | CHK008 | INVALID on typed denominator; FAIL on completeness over a partial frame |
| M8 layer substitution | CHK012 (**partial**) | FAIL when labelled; INVALID when unlabelled; **misses the confident case** |
| M9 chain abandoned | CHK010 | INVALID without a route log; FAIL on unattempted hops |
| M10 correction less reliable | CHK011 | INVALID from the same instrument; FAIL without re-reading the original |
| M11 the unfired rule | `Registry.register` + per-run controls | registration refused; run void |

---

## 6. Sources

All read verbatim from read-only mounts on 15 August 2026. No file in either repository was modified.

- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\search-and-screening\13_ERROR_LIBRARY.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\search-and-screening\14_RULE_TESTS_AND_SPECIFICATIONS.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\count-recovery\DEFECT_LEDGER_cardiology_mortality_atlas.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\count-recovery\cardio_acm_harness_report.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\chagas-recovery\corpus_provenance_audit_running_report_3_access_ledger.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\chagas-recovery\corpus_provenance_audit_running_report_6.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\chagas-recovery\answer_hf_route_log.md`
- `F:\rapidmeta-ssot-shell\evidence\2026-08-12\detector-library\guard2.py`, `degrade_test.py`
