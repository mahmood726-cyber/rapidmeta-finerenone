# Adversarial tests of the five rules, and their specifications

2026-08-12. Tested before propagation, on the principle that **a rule that cannot fire is not a rule**.

Each rule below reports: what it catches, what it misses, false-positive and false-negative behaviour, and whether a **known-bad input it demonstrably fires on** exists. Where no such input exists, the rule is marked **UNPROVEN** and must not be relied on in that direction.

**Headline of the testing: two of the five rules pass, two are defective as written and are respecified, and one is unproven in its dangerous direction.**

---

## Test corpus

Eight open-access syntheses of this comparison, read at the level of stated eligibility criteria and actual included-study designs, plus the two documents already in the error library.

| PMCID | PMID | Declares | Includes | Consistent? |
|---|---|---|---|---|
| PMC11883387 | 39970741 | *"randomized clinical trials… compared SAV to ACEI or ARBs"* | RCTs only | yes |
| PMC7705560 | 33257469 | *"randomised clinical trials irrespective of trial design, setting, publication status, publication year and language"* | RCTs only | yes |
| PMC12773504 | 40689605 | *"All randomized controlled trials (RCTs)"*, with explicit exclusion of *"cohort studies, case-control studies… single-arm and non-randomized trials"* | RCTs only | yes |
| PMC10405977 | 37554618 | *"only double-blind, randomized controlled tri[als]"*; observational designs explicitly excluded | RCTs only | yes |
| PMC9758945 | 36527023 | *"We included RCTs of adults"* | RCTs only | yes |
| PMC12950259 | 41773097 | *"randomized controlled trials (RCTs) **or observational studies**"* | 10 RCTs + 2 cohorts | yes (declared) |
| PMC10710849 | 38084196 | *"observational studies (retrospective cohorts and prospective cohorts) **or** RCTs"* | both | yes (declared) |
| PMC8754592 | 35035857 | "systematic review and meta-analysis"; describes its own analysis twice as *"this retrospective analysis"*; **retracted** | 5 "clinical trials" | **ambiguous** |

**Result: zero clean declared-then-violated cases in eight documents.** That is a finding about the sample, and it is the reason Rule 1 is marked unproven in one direction below.

---

## RULE 1 — Error versus declared choice

### Statement (as tested)

> A discrepancy is **not** an error if the document declares, in its own methods, the practice that produces it. A declared permissive eligibility criterion, a declared language restriction, a declared analytic choice — each is a decision, not a mistake, however much it affects the result.

### What it catches

Reviews that admit designs a reader might not expect, having said so. It fired correctly twice today, both times **protecting** a document:

- **PMC12950259** — alleged to have pooled cohorts inside a table captioned "included RCTs". Its eligibility criteria say *"randomized controlled trials (RCTs) or observational studies"*, its abstract says *"10 RCTs and two prospective cohort studies"*, and it applies RoB 1 to trials and Newcastle–Ottawa to cohorts as separate instruments. **Declared. Entry withdrawn.**
- **PMC12773504** — alleged to have pooled discordant composites. It states *"The definition of the primary composite endpoint… varied across the included trials"* and enumerates the differences. **Declared. Entry withdrawn.**

It also correctly **passed** E1 to publication: a cell labelled `HR` for an NT-proBNP ratio is not a declared choice anywhere in that document.

### What it misses — the dangerous direction

**False negatives are the risk**, because the rule now protects documents from being named. Two failure modes found:

**1.1 — Scope leakage (DEFECT, respecified below).** The rule as written asks "does the document declare this practice?" A document can declare permissive eligibility in its methods while its abstract's conclusion asserts the restrictive claim. The declaration protects the whole document, including the misleading summary sentence. The rule should be scoped to **the specific claim being challenged**, not to the document.

**1.2 — Declaration location.** All eight test documents declare in the methods section. A declaration buried in a supplementary file would not be found by a methods-section read, producing a **false accusation**. Every test here read full text; none tested supplementary-only declaration. **Untested branch.**

**1.3 — The ambiguous case.** PMC8754592 calls itself a systematic review and meta-analysis, and twice describes its own analysis as *"this retrospective analysis"*. Is that a declaration of design, or loose prose in a review of trials? The rule gives no answer. It is also a **retracted publication**, which is an independent signal the rule does not consider at all.

### Known-bad input it demonstrably fires on

**In the protective direction: yes** — PMC12950259 and PMC12773504, both withdrawn.
**In the accusatory direction: UNPROVEN.** No declared-then-violated case exists in the eight-document sample, so the rule has never been shown to correctly *refuse* protection to a document that declared one thing and did another. Until such a case is found and the rule fires on it, **Rule 1 must be treated as a filter of unknown strictness**, and any review relying on it should say so.

### Respecification

> **Rule 1 (v2).** For a challenged claim C in document D:
> 1. Identify the specific practice P that produces C.
> 2. Search D's methods, abstract, and supplementary materials for a declaration of P. Record where it was found, or that all three were searched and none was found.
> 3. If P is declared **and** C is consistent with the declaration → **not an error**; record as a declared choice with the quotation.
> 4. If P is declared **but C misstates the declaration** (e.g. a caption or conclusion asserting a narrower design than was used) → **error, scoped to C**, not to D's eligibility. The declaration protects the practice, not every sentence about it.
> 5. If no declaration is found after searching all three locations → **error**, and the record must state that supplementary materials were checked.
> 6. Retraction status is recorded on every entry and never substitutes for the analysis.

Step 4 is the fix for 1.1 and would have produced a *scoped* caption entry for PMC12950259 rather than an all-or-nothing withdrawal.

---

## RULE 2 — Estimand mislabelling (class M1)

### Statement (as tested)

> A quantity recorded under the name of a different quantity is an error, established by showing the document uses the correct labels elsewhere.

### What it catches

E1. PMC11883387's PIONEER-HF cell reads *"Greater time-averaged reduction in NT-proBNP in SAV group (HR: 0.71; 95% CI: 0.63-0.81)"*. The internal-inconsistency argument is strong there because the same table labels other ratio quantities **correctly and differently**: *"GMR: 0.84"*, *"ratio of change 0.85"*, *"rate ratio: 0.87"*, *"AUC ratio 0.95"*, and uses `HR` correctly for PARALLEL-HF (*"HR: 1.09; 95% CI: 0.65-1.82"*) and PARADISE-MI (*"HR: 0.90"*).

### What it misses — the house-style attack

The internal-inconsistency argument **fails completely** against a document that uses `HR` loosely for everything. If a paper labels twenty quantities `HR` and never uses `GMR` or `ratio of change`, there is no internal contradiction to point at, and the rule as written produces no entry — a **false negative on exactly the sloppier document**.

Measured in the test corpus: `HR:`/`HR=` occurrences were **4, 0, 0, 0, 0, 0, 0, 0** across the eight documents; "hazard ratio" appeared 1, 0, 0, 0, 1, 0, 0, 0 times. **No document in this sample uses HR uniformly loosely.** The house-style branch is therefore **untested**, not passed.

### Respecification

> **Rule 2 (v2).** To establish M1 for a labelled quantity Q in document D:
> - **Primary test (internal):** D uses distinct, correct labels for other quantity types. If so, the inconsistency is sufficient.
> - **Fallback (mandatory when the primary test is unavailable):** an **external resolvable source** establishes what the quantity is — the trial's registry outcome-measure definition, its publication, or its posted results. The entry must cite it.
> - An entry may not rest on the reader's expectation of what `HR` should mean.

E1 satisfies both branches: internally inconsistent, **and** NCT02554890's sole primary outcome measure is *"N-terminal Pro-brain Natriuretic Peptide (NT-proBNP) Values and Time-averaged Change From Baseline"*. It survives the house-style attack. It is the only entry that has been tested against it.

---

## RULE 3 — Class exposure / the "if applicable" test

### Statement (as tested)

> An error-library section is included when an entry concerns the review's own question, **or** when the review's own data could exhibit a class in the taxonomy.

### Adversarial inputs — the rule is DEFECTIVE as written

| Input | What the rule as written does | What it should do |
|---|---|---|
| A review pooling **no composite outcome** | My §8 text ties M1/M2/M8 exposure to composites, so it reports **nothing** | M1 (estimand mislabelling) applies to **any** extracted effect estimate. Every review is exposed. The composite framing was a generalisation from this review's own question — a straightforward over-fit. |
| An **individual-patient-data** review | Not mentioned at all | Heavily exposed to M9 (unit of analysis) and M6 (trial identity); *less* exposed to M1, since estimates are computed rather than transcribed. Exposure profile differs by data type and must be stated. |
| A review of a **single trial** | "No pooling" reads as low exposure | Still exposed to M6 (is it one trial or two reports?) and M10 (numerical integrity). Duplicate inclusion M7 is genuinely not exposed. |

### Respecification

> **Rule 3 (v2).** Exposure is evaluated **per class, by trigger**, not by review type:
>
> | Class | Exposure trigger |
> |---|---|
> | M1 estimand mislabelling | the review transcribes any effect estimate from a source document → **always** |
> | M2 estimand substitution | eligibility depends on what a study reports |
> | M3 unverified absence | the review asserts any absence |
> | M4 frame over-claim | the review reports a recall, completeness or coverage statistic |
> | M5 identity by surface features | the review matches records across documents |
> | M6 trial identity | more than one report per study is possible → **almost always** |
> | M7 duplicate inclusion | two or more studies pooled |
> | M8 comparator mismatch | two or more comparators across pooled studies |
> | M9 unit of analysis | recurrent events, multi-arm trials, or IPD |
> | M10 numerical integrity | any reported summary statistic |
>
> A class with a triggered exposure must appear in the projection, found or not.

---

## RULE 4 — "Screened for, none found, here is the screen"

### The attack, and it succeeds

A paper writes: *"M10: screened for, none found."* Nothing in the rule requires the screen to have run. The line is prose, and prose is not evidence.

**This is not hypothetical — it is precisely error N2 in our own library.** `03_PRISMA_AND_SCREENING_NOTES.md` asserted the fixed-timepoint risk-ratio class was *"not encountered"* while PMID 34395116 sat in the corpus reporting exactly that. An unverified absence was published as a verified one, by me, in this review, today. **The rule as written would have licensed that sentence rather than caught it.**

### Respecification

> **Rule 4 (v2).** A "none found" row may not be rendered from prose. It renders only if the object carries an execution record with **all** of:
> - `screen_id` and the tool, script or query that ran;
> - `executed_at` (UTC);
> - `input_set_size` — how many items were screened;
> - `criterion` — the exact test applied.
>
> If any field is missing, the row renders as **"not screened"**, never as "none found". Absence of a screen and absence of a finding are different statements and must not share a cell.

This is the single most important respecification in this document, because it is the one whose failure we can already demonstrate on ourselves.

---

## RULE 5 — The render gate on `origin: own|external`

### The attack, and it succeeds

Gate as proposed: *block a projection that emits external entries with no own entries.*

Adversarial input: **add one trivial own-entry** — "we mistyped a filename" — and unlock forty external entries. The letter is satisfied; the purpose is defeated entirely. A one-sided catalogue with a fig leaf is arguably worse than an openly one-sided one, because it looks balanced.

A naive fix — requiring own-entries to be some fraction of the total — fails in the other direction: it would suppress a legitimate large external finding simply because the review happened to make few mistakes, and it creates an incentive to pad one's own list.

### Respecification

> **Rule 5 (v2).** A projection emitting external entries renders only if **all three** hold:
>
> 1. **Severity matching.** If any external entry has `propagated: yes`, at least one own entry must also have `propagated: yes`. You may not pair "their error changed their result" with only "our typo".
> 2. **Class matching.** For every class in which an external entry is emitted, the projection must also emit the review's own row for that class — an entry, or a Rule-4-compliant "screened, none found".
> 3. **Floor.** At least one own entry, as a blunt backstop for classes that do not apply.
>
> Counts are deliberately **not** proportional. Proportionality invites padding and punishes accuracy; severity and class matching cannot be satisfied by triviality.

Tested against today's library: 1 external entry (E1, class M1, `propagated: no`) and 4 own entries including N1 (class M2, `propagated: yes`). Condition 1 holds vacuously, condition 3 holds, **condition 2 fails** — we emit an external M1 but have no own M1 row. Under Rule 5 v2 the current library **would not render**, and the correct remedy is to run an M1 screen on our own extractions and record the result either way.

**That is the gate working: it fired on us, on its first evaluation.**

---

## Summary of test outcomes

| Rule | Fires? | Verdict |
|---|---|---|
| 1 — error vs declared choice | protective direction **yes** (2 withdrawals); accusatory direction **no case in sample** | **UNPROVEN one-directionally.** Respecified v2 to scope to the claim, search three locations, and record retraction status |
| 2 — estimand mislabelling | **yes** (E1) | **PASS**, with the house-style branch untested; respecified v2 to make the external fallback mandatory |
| 3 — class exposure | n/a | **DEFECTIVE** — over-fitted to composite outcomes; respecified v2 as a per-class trigger table |
| 4 — "screened, none found" | **fails against our own N2** | **DEFECTIVE** — respecified v2 to require a machine-checkable execution record |
| 5 — render gate | **yes, on us** | **DEFECTIVE as proposed** — respecified v2 with severity and class matching; current library fails condition 2 |

Three of five needed repair, and two of the repairs were found by pointing the rule at our own work rather than at anyone else's. Rules 4 and 5 in their v1 form were incapable of firing on the failures they existed to prevent.

---

## Specification for the build lane — `errors[]`

Stress-tested version. Field set:

```
errors[]:
  id
  origin              own | external
  class               M1..M10
  document            { doi?, pmid?, pmcid?, internal_path? }
  location            free text, must identify table/row/section
  quote_verbatim      exact text at issue
  correct_value       the corrected value or characterisation
  correcting_source   { resolvable identifier, location }
  date_verified       ISO-8601 UTC
  propagated          yes | no | unknown   + evidence
  status              active | withdrawn
  withdrawal_reason   required when status = withdrawn
  declared_choice_check:
      practice_identified
      searched_methods    bool
      searched_abstract   bool
      searched_supplement bool
      declaration_found   { location, quote } | null
      scope               claim | document
  retraction_status   retracted | not_retracted | unknown
  scope[]             review IDs to which the entry is relevant

screens[]:
  screen_id
  class               M1..M10
  criterion
  tool_or_query
  executed_at         ISO-8601 UTC
  input_set_size
  findings[]          error ids, possibly empty
```

Gates:

1. **Rule 4 gate** — a "none found" row renders only from a `screens[]` record with all fields populated. Otherwise render "not screened".
2. **Rule 5 gate** — severity matching, class matching, floor of one. Currently **failing** on class matching, correctly.
3. **Denominator gate** — no proportion renders unless `documents_examined_at_extraction_level` is a maintained counter, not a typed literal.
4. **Novelty gate** — no entry asserts novelty until the meta-research mapping in `13_ERROR_LIBRARY.md` §7 is populated.

---

## Open items

- **Rule 1 accusatory direction remains unproven.** Finding a real declared-then-violated case is now a named task; until then the rule's strictness is unknown.
- **Rule 2's house-style branch is untested.** No document in the sample uses `HR` uniformly loosely.
- **Rule 1.2 untested:** supplementary-only declarations.
- **The current error library fails Rule 5 v2 condition 2** and needs an own-M1 screen before it can render.
- **The 201-synthesis diff stays queued** for the OpenAlex reset at 00:00 UTC. The zero-breadth-failures null still rests on 18% of the frame.
