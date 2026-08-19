# The page standard, versioned

**`PAGE_STANDARD_VERSION = "1.16.0-2026-08-19"`**

> **This line was `1.6.0` while the version log below already ran to `1.12.0` and
> `ssot/build_to_standard.py` stamped `1.13.0`.** The marker whose entire purpose is to make
> staleness visible was itself stale by seven minor versions, and every page built in that
> window carried the *code's* version, so nothing downstream was wrong — only this document
> was. Corrected 2026-08-19, and recorded rather than quietly fixed, because *the file that
> says what current means going out of date is the failure mode this file exists to prevent.*
> The single source of truth is `ssot/build_to_standard.py::PAGE_STANDARD_VERSION`; this
> heading must be kept equal to it, and nothing yet checks that they are.

Until tonight this standard existed only as practice and as one exemplary object
(`arni-hfref`). It had **no version marker anywhere in the repo** — `grep` for `build_stamp`
or `standard_version` across every object returns nothing, ARNI included. That is the gap
this file closes, and it closes it in the direction the ratchet requires: a page records the
standard version it was built to, so a page built to v1 while the standard is v3 is
**honestly labelled rather than silently stale**.

**No page is grandfathered, `arni-hfref` included.** ARNI is presently unstamped and is
therefore *unknown-version*, not *compliant*. That is a fact about the register, not a
criticism of the page.

---

## The properties

A page meets the standard when **every property below is either HELD or REFUSING WITH A
STATED REASON ON THE PAGE**. A refusal is a complete outcome. A blank is not.

| # | property | held means |
|---|---|---|
| P1 | **Executed search** | query string verbatim, date, records returned, per database; PRISMA counts that reconcile arithmetically |
| P2 | **k cascade** | k reported at every stage, never as a single number |
| P3 | **Inclusion criteria** | a criteria block carrying `predefined:` on its face |
| P4 | **Preconditions** | every precondition with its verdict and its cited authority |
| P5 | **Extraction table** | verbatim source sentence per cell, resolvable link, and each cell labelled READ or DERIVED |
| P6 | **Analysis output verbatim** | the model call, estimate with CI, heterogeneity and package version, quoted. **If there is no quotable output, the absence is recorded as a finding** |
| P7 | **Published-meta comparison** | with a denominator, present in BOTH the page and the Word manuscript, charts aligned |
| P8 | **Registration identity** | every trial keyed to a registration id verified against the registry |
| P9 | **Build stamp** | naming this standard version |
| P10 | **Served-bytes verification** | the property is confirmed in bytes served over HTTP, not in a source file and not by an exit code — **and not by a hash alone**. `md5(served) == md5(disk)` proves the wire agrees with the disk and says nothing about whether the disk agrees with the object, because **a stale file matches its own disk copy perfectly**. A content check must accompany it, with its expected strings PROJECTED FROM THE OBJECT rather than typed into the verifier |
| P11 | **Coded field governs** | where the object holds BOTH a coded field and a free-text label for the same thing, the verdict is taken from the CODE; the text only corroborates. Where the code is absent and the verdict falls back to text, **the verdict says so on its face** |
| P12 | **The known-answer suite ran** | the suite executed and passed in this build. An import error is a BUILD FAILURE, not a skipped test |
| P13 | **Keyed by entity, never by module constant** | a function that accepts an identifier must REFUSE when it holds no record keyed to it. Per-entity data is keyed by entity; it is never reached for from whichever constant is in scope |
| P14 | **No substring matching over clinical text** | identity is decided by a declared, enumerated term set or a coded field. Registry text carries parenthetical abbreviations — `Cardiovascular (CV) Death` — so substring containment is a KNOWN-BROKEN method, not a shortcut |
| P15 | **A short-circuiting check reports all failing limbs** | a check that returns on first failure must report EVERY limb that fails, or state that the named limb is merely the first tested. A single reason drawn from an ordered sequence of tests is a fact about the sequence |
| P16 | **A guard is proven in three parts, and the case it guards against must have OCCURRED** | it **must be able to fire**; it **must not fire on the correct case**; and **neither can be established by the build reporting success**. All three are demonstrated, not assumed. **Added 1.6.0:** the triggering condition must have actually arisen in data the guard has run on — a guard whose condition has never occurred is *unproven, however green it reads*, and "it would have caught it" is a claim about an event that never happened |
| P17 | **Negative claims are computed, never asserted** | any field whose name implies a check — `shared_with_other_topics`, `conflicts`, `unresolved`, `discrepancies` — carries a computed value and names what it was computed against. A literal `false` or `[]` in such a field is a claim, not a result |
| P18 | **A restated quantity is reproducible by a command** | a number that has been corrected carries the COMMAND that re-derives it, and a gate that refuses the object when it stops reconciling. A `restated_*` note is a claim about a MOMENT and ages silently — its presence shows someone once looked, never that anyone looked last |
| P19 | **A promotion reaches every derived block, or it is not applied** | when k, the included set, or the headline estimate changes, every quantity DERIVED from them moves in the same pass — prediction interval, estimator sensitivity, PRISMA flow, cascade `k_included`, and the published-meta comparison. A page carrying two answers is worse than a page carrying the old one |
| P20 | **The cascade reconciles with itself** | `k2_role_located == k3 + k4 + k5`, and `k0 == k3 + k4 + k5 + kNA (+ kUNREACHABLE)`. A stage that does not reconcile with the stages beside it is a number the reader it was written for cannot check |
| P21 | **An ambiguous question is built as several reviews, never chosen between** | where a topic's question admits more than one legitimate reading, **each reading becomes its own review** with its own question, criteria, search, cascade and screening. Choosing one is a decision to withhold evidence from every reading that loses, and it leaves no trace in any object |
| P22 | **Deliberate trial sharing is recorded on both sides** | a trial legitimately appearing in more than one topic carries, on each object, **which other topics hold it and why**. Sharing is legitimate; unrecorded sharing is not. Every page that shares states that **a corpus-level k obtained by summing per-topic k double-counts** |
| P23 | **Recall is measured against the review's own included set** | every executed search reports how many of the trials this review includes it actually surfaced. A **design filter** (phase, status, study type) is a recall hazard: `NA` is not a phase, and enumerating phases drops every registrant who declared none. A query that misses is **recorded, not replaced** |
| P24 | **Every disposition in a taxonomy is demonstrably reachable** | each state a screen can assign must be reached by at least one real instance in the run, or be reported as **reached zero times and why**. *A disposition that cannot be reached is not a conservative default* — it looks cautious, so a zero there invites no suspicion at all |
| P25 | **A pipe never interprets output it has not proved was produced** | any filter over a subprocess must assert the subprocess **succeeded** before reading its output, and an **empty result from a filter is NOT_ASSESSABLE, never a negative finding**. *A filter over a subprocess's output converts a loud failure into a quiet one* |
| P26 | **An agreement rate is computed over independent answers only** | repetition by one instrument is not independence. Duplicate answers from a single seat are deduplicated before any agreement is counted, and a seat that returned nothing is **absent, not concurring** |
| P27 | **A reframed question travels to every site that asks it** | when a rule is reframed, the reframing must reach **every place the old question is put — including prompts to other models and to humans**, not only the code that was fixed. A fix applied at one site is not a fix of the class, and a question is a site |
| P28 | **A defective question invalidates every answer it produced, agreements first** | when a question is found unable to make a distinction, **every** answer to it is suspect — *especially the ones that agreed*, because agreement under a bad question is precisely what makes it look settled. A correction that stops at the cases that looked wrong is not a correction of the class |
| P29 | **A filter asserts an expected count, not merely a successful exit** | any pipe over a subprocess checks `exit == 0` **and** that the filter yielded the expected number of results. An expected-count assertion is the only thing that distinguishes an **empty** result from a **discarded** one |
| P30 | **Prose is not evidence; a report is not an artefact** | any number stated in a report, a commit message or a page must exist in a file something can recompute. **A claim that exists only in prose is indistinguishable from one that was computed** — until an arithmetic gate demands the parts sum |
| P31 | **Two correct readings of different questions look exactly like a disagreement** | before treating cross-instrument disagreement as evidence about the instruments, establish that both were asked the **same** question. Disagreement is a property of the question until shown otherwise |
| P32 | **An indicator must be able to move only if the diagnosis is right** | when a fix is proposed, name the quantity that will change **and could not change for another reason**. A number that merely *correlates* with the defect is not a test: a narrower identity set finds fewer things, so a rising `kNA` is consistent with the fix working *and* with it failing |
| P33 | **A keyword for the name of a thing is not a test for the thing** | detect a property by its structure, not by the word that names it. A composite endpoint is *a mortality term plus another clinical event in one endpoint* — CASTLE-AF's primary is unmistakably one and contains neither the word "composite" nor the phrase the rule searched for |
| P34 | **The gap between a code rate and a disposition rate measures the VOCABULARY, not the instruments** | codes that collapse onto one disposition inflate the gap; codes that fan out close it. **Comparing the gap across topics is meaningless unless the vocabularies are comparable**, and an agreement rate is reported with the vocabulary that produced it |
| P35 | **The primary outcome is read by matching its registered text, never by position** | `outcomeMeasures[0]` is not the primary. For ADVANCE-2 element zero is a **secondary**, and for its three companions it is the primary — so a positional read pools one trial's secondary against three trials' primaries **with nothing malformed anywhere** |
| P36 | **Heterogeneity can neither establish nor refute estimand coherence** | measured both ways in one night: two ablation reviews pooled **mismatched** estimands at I² of **0.0% and 3.9%**, and apixaban's mismatched primaries pooled at **83.6%** against **67.8%** for its matched estimand. **A low I² does not show trials measure the same thing; a high one does not show they don't.** Coherence is established by reading the definitions, never by a statistic |
| P37 | **Trials sharing a composite endpoint's NAME do not share its DEFINITION, and matching by name is a method that does not work** | this is a property of REGISTERED TRIALS, not of this corpus's topic selection: six instances across three drug classes and two specialties. The pair that settles it is **AMPLIFY and AMPLIFY-EXT** — same sponsor, same programme, sequential trials, names differing by a hyphenated suffix — where one counts *recurrent VTE or VTE-related death* and the other *recurrent VTE or ALL-CAUSE death*. A review must therefore decompose every endpoint into its components and compare the SETS, and must record the comparison, because a mismatch that is pooled deliberately and a mismatch that was never noticed look identical in the output |
| P38 | **A shared estimand does not make a shared comparator** | estimand coherence is NECESSARY and it is NOT SUFFICIENT. AMPLIFY and AMPLIFY-EXT both register *recurrent VTE or VTE-related death* — primary in one, secondary in the other — and pooling them is still wrong, because one randomises apixaban against enoxaparin/warfarin and the other against **placebo**. Every axis on which a pool can be incoherent gets its own verdict, and a trial that leaves a pool leaves it for a NAMED axis |
| P39 | **When matching by text returns more than one posted measure, choosing among the matches by position is P35 one level down** | AMPLIFY-EXT posts its primary composite **twice**, typed PRIMARY both times, under the same registered name, differing only in the trailing *"Randomized Population With Imputation" / "Without Imputation"* — and the arm counts are **32 against 19**. Nothing in the payload is malformed. The choice among matches is an ANALYSIS-POPULATION choice: it is made once, applied to every trial, stated on the page, and the pool is recomputed under the alternative so the choice's cost is measured rather than asserted to be small |
| P43 | **Anything that PARTITIONS before it JUDGES must have its partition checked against known members first** | a precedence rule applied first is the most damaging place to be wrong, because it **silently removes trials from every downstream reading before any of them gets to judge**, and each reading then looks internally consistent. `bosentan-pah` was partitioned into four readings by `minimumAge < 18`, which is not what a paediatric trial is: EARLY and COMPASS-2 admit adolescents from 12 and are adult trials. That single test **took reading A's anchor trial and reading B's own trial out of their reviews entirely**, and every downstream count inherited it. Before trusting a partition, assert its known members — one real instance per class, named in advance |
| P44 | **The distinction a reading turns on may be the one the registry does not encode** | COMPASS-2 declares exactly what EARLY declares — `armGroups: bosentan \| placebo`, `interventions: ['bosentan','placebo']` — because **background therapy is not a registered intervention**. Read from the arms alone, a combination trial and a monotherapy trial are indistinguishable, and the *only* declaration of the design is the official title. **A reader will assume monotherapy versus combination is a coded fact; it is not**, so a page whose reading depends on such a distinction states on its face that the distinction is not coded and names the field it was read from instead |
| P41 | **A search must not be built from its own answer** | a query assembled from the terms the included set already shares can only return that set, so it CANNOT DISCOVER and its recall of 100% is a tautology. `azilsartan-chlorthalidone-vs-olmesartan-hctz` asks about one fixed-dose combination against one other; a query naming azilsartan AND chlorthalidone AND olmesartan would have returned exactly the two trials already on the page. **The query is built from the DRUG and the CONTRAST is applied at SCREENING, where every limb is auditable and every exclusion names what it randomised instead.** 53 of 57 exclusions on that topic fail the comparator limb, which is a fact about a narrow question asked of a whole programme — not a criticism of the query, and only visible because the query was wider than the answer |
| P42 | **A coded field can be CORRECT and still not answer the question asked of it** | distinct from P11, which governs code-versus-text where both speak. Here the code speaks truly about something else. `conditions: ["Safety"]` names a study OBJECTIVE where the disease belongs; `conditions: ["Pulmonary Hypertension"]` names the SYNDROME on a trial titled *"in Sickle Cell Disease (SCD) Patients"*, where the review needs the WHO GROUP. Neither field is absent and neither is wrong. **A limb reading such a field must fall back to the declared text and RECORD WHICH READING THE VERDICT RESTS ON** — and the fallback must still exclude, or it is not a limb: a bioequivalence record whose title says *"in Chinese Healthy Volunteers"* stays out |
| P40 | **A rule you have APPLIED is not a rule you have PUBLISHED** | the complement of the registry's opening line. The criterion separating `apixaban-vte-treatment` from `apixaban-vte-prophylaxis` — *prior event means treatment* — decided which review sixteen trials belong to and existed only inside an adjudication file. A criterion that decides inclusion must appear on the page of **every review it decides**, or the reader cannot check it and the next lane cannot apply it. **And it was not applied everywhere either:** it reached the sixteen adjudicated trials and not the nine admitted by the mechanical screen on the coded field the criteria themselves say does not settle the question |

## Reading the remainder — the same number, opposite diagnoses

**Added 2026-08-19, from screening three topics' remainders to zero.** A `k_unscreened_remainder`
is not just a backlog count. Once screened, **the shape of its dispositions diagnoses the
search**, and two topics with identical remainders can mean opposite things:

| remainder dominated by | diagnosis | what to do |
|---|---|---|
| **POPULATION failures** | the surfacing query is **too broad** — it is reaching outside the review's own population | narrow the query; the cost is reviewer time spent excluding trials that were never candidates |
| **ESTIMAND failures** (eligible, not poolable) | the query is well-aimed and the **evidence base is genuinely fragmented** | nothing to fix in the search; the limit is real and belongs in the interpretation |
| **NOT-YET-REPORTED** | the query is well-aimed and the **field is still in flight** | name the largest pending trials — they are what will change the answer |
| **COMPARATOR failures — few trials declare a control arm at all** | the query is well-aimed and **the field has produced few controlled trials**. This is a fact about the literature, not about us | say so plainly; the limit is the evidence that exists, and no better query recovers it |

Observed, on the same night, on two topics with the same criteria discipline:

- `iv-iron-hf` — 29 screened, **16 of 29 ELIGIBLE**. Only 13 failed a criterion. The base is
  limited by estimand match and by trials that have not reported.
- `sglt2-hf` — 10 screened, **7 excluded, six of those on POPULATION**: acute myocardial
  infarction, heart transplant, diabetic nephropathy, congenital heart disease, acute
  decompensation. The surfacing query reaches well beyond its own population.
- `attr-cm-review` — 46 screened, 31 excluded, and **only 6 of the 46 declare a placebo arm at
  all**. A drug programme dominated by open-label extension and single-arm studies. No better
  query recovers randomised evidence that was never generated.

**"Few controlled trials exist" is a different finding from "our query was too broad", and a
reader must be able to tell them apart.** Both produce a large excluded count; only one is a
criticism of the search.

> **This is a fact about our search, not about the evidence — and it was invisible while the
> remainder was carried as a number rather than screened.** A remainder is not a queue to be
> drained; it is unread evidence *about the query that produced it*.

**Therefore P1 is not fully held by a search that merely reconciles.** Where a remainder has
been screened, the disposition split belongs on the page beside the count, because
`remainder: 29` and `remainder: 10` tell a reader nothing about which of the three situations
above they are in.

## The ratchet

Each topic must meet everything learned **up to the moment it is built**. The version string
is what makes staleness visible instead of silent. When a lesson is added, the version rises
and every page below it is *known* to be below it.

## What a refusal must carry

A refusing property states **which** property, **why**, and **what would change it**. "Not
applicable" is not a reason; "k=1, so there is no between-study variance to estimate" is.

Nothing is generated to fill a slot. A tab with nothing to render keeps refusing.

---

## Version log

### 1.16.0-2026-08-19
Adds P43 and P44, both from splitting `bosentan-pah` into four reviews.

**P43 — anything that partitions before it judges must have its partition checked against known
members first.** The four readings were assigned by a precedence rule, and its first step tested
`minimumAge < 18` for "is this a paediatric trial". It is not:

| trial | `stdAges` | `minimumAge` | what it is |
|---|---|---|---|
| EARLY `NCT00091715` | `[CHILD, ADULT, OLDER_ADULT]` | 12 Years | an **adult** trial admitting adolescents |
| COMPASS-2 `NCT00303459` | `[CHILD, ADULT, OLDER_ADULT]` | 12 Years | an **adult** trial admitting adolescents |
| FUTURE-2 `NCT00319020` | `[CHILD]` | 2 Years | paediatric |

The rule pulled the first two into the children's reading — **reading A's anchor trial and
reading B's own trial, removed from their reviews before either review could judge them.** Every
downstream count inherited it, and each reading still looked internally consistent.

> A partition applied first is the most damaging place to be wrong, because *nothing downstream
> can see what it removed.* Assert one real known member per class, named in advance, before
> trusting any assignment the partition produces.

Corrected to *no adult stratum at all, or `maximumAge` under 18*.

**P44 — the distinction a reading turns on may be the one the registry does not encode.**

```
EARLY     armGroups: EXPERIMENTAL 'bosentan' | PLACEBO_COMPARATOR 'placebo'
          interventions: ['bosentan', 'placebo']
COMPASS-2 armGroups: EXPERIMENTAL 'A' [bosentan] | PLACEBO_COMPARATOR 'B' [placebo]
          interventions: ['bosentan', 'placebo']
```

EARLY is bosentan monotherapy against placebo. COMPASS-2 is bosentan **added to sildenafil**
against sildenafil alone. **Background therapy is not a registered intervention**, so the two
declare the same thing, and the sildenafil that defines the entire reading appears in no arm
field — only in the official title.

> **A reader will assume monotherapy versus combination is a coded fact.** It is not. A page
> whose reading depends on such a distinction says so on its face and names the field the
> distinction was actually read from.

Same family as P42 one step further out: P42 is a coded field answering a different question;
this is a coded field with **no** answer to the question, where the design exists only in prose.


### 1.15.0-2026-08-19
Adds P41 and P42, both from executing searches on topics that had never had one.

**P41 — a search must not be built from its own answer.** `azilsartan-chlorthalidone-vs-olmesartan-hctz`
asks about one fixed-dose combination against one other. A query naming all three agents would
have returned exactly the two trials already on the page, and reported **recall 2/2** while
being incapable of discovering anything.

> A query assembled from what the included set already shares cannot discover. Its perfect
> recall is a tautology, and a search that can only confirm the included set is not a search.

The query is built from the **drug** — the whole 57-record programme — and the contrast is
applied at **screening**, where every limb is auditable. All 53 exclusions fail the comparator
limb, because only four registrations in the entire programme carry an
olmesartan-plus-hydrochlorothiazide arm at all. That is a fact about a narrow question asked of
a whole programme, and it is **only visible because the query was wider than the answer**.

**P42 — a coded field can be correct and still not answer the question asked of it.** Three
instances in one day, none of them a wrong field:

| record | coded field | what it says | what the review needed |
|---|---|---|---|
| `NCT01309828` | `conditions: ["Safety"]` | a study **objective** | the disease |
| `NCT00310830` | `conditions: ["Pulmonary Hypertension"]` | the **syndrome** | the WHO group |
| `NCT00313196` | `conditions: ["Pulmonary Hypertension"]` | the **syndrome** | the WHO group |

Each is true. Read literally, the first excluded a head-to-head this review wanted and the other
two put sickle-cell trials into a WHO-group-1 monotherapy reading. **This is not P11** — P11
governs code against text where both speak to the same thing and the code wins. Here the code
speaks truly *about something else*.

The remedy is the same shape as P11's: fall back to the declared text, and **record which
reading the verdict rests on**. And the fallback must still exclude, or it is not a limb — a
bioequivalence record whose title reads *"in Chinese Healthy Volunteers"* stays out on the text.


### 1.14.0-2026-08-19
Adds P37, P38, P39 and P40, all four from re-pooling `apixaban-vte-treatment` — and corrects
this document's own version heading, which was seven minor versions stale.

**P37 — the composite finding stops being a per-topic note and becomes a property.** It has
been recorded in commit messages five times and in no standard. It is not a fact about which
topics this corpus chose; it is a fact about registered trials:

| review | trials | distinct primary component sets |
|---|---:|---:|
| `ablation-af-heart-failure` | 2 | 2 |
| `ablation-af-medical-therapy` | 3 | 3 |
| `early-rhythm-control-af` | 4 | 4 |
| `apixaban-vte-prophylaxis` | 4 | 4 |
| `apixaban-vte-treatment` | 11 | **5** |

The pair that settles it is AMPLIFY (NCT00643201) and AMPLIFY-EXT (NCT00633893): one sponsor,
one programme, sequential trials, names differing by a hyphenated suffix — and *VTE-related
death* against *all-cause death*.

> If two trials from one programme with almost the same name do not share a definition, a
> reviewer matching endpoints across independent sponsors by name is not making an occasional
> error. They are using a method that does not work.

**P38 — and coherence on the estimand is not coherence.** AMPLIFY and AMPLIFY-EXT *do* share
*recurrent VTE or VTE-related death*. Pooling them gives RR 0.53 (0.21 to 1.31) at **I² 93.5%**,
and it is refused — not on the heterogeneity, on the **comparator**: enoxaparin/warfarin against
placebo. The eight-trial name-matched pool, whose estimands agree on nothing, comes out at
**I² 76.4%**.

> **The pool where the estimand IS shared is the MORE heterogeneous one.** This was stated as a
> prediction before the run, with the comparison chosen as the indicator precisely because a
> single high I² could not test anything (P32). P36 said heterogeneity cannot establish
> coherence; this is the first page on which the two point in *opposite* directions at once.

**P39 — a text match can return two answers.** P35 says never read the primary by position.
AMPLIFY-EXT shows the next layer: the registered text matches **two** posted measures, both
typed PRIMARY, differing by imputation, with counts of 32 and 19 on the same arm. Taking the
first is positional reading with a text match in front of it.

**P40 — publishing the rule.** See the table. The boundary criterion is now on both apixaban
pages, in `screening.eligibility` where a reader meets it and in
`screening.boundary_criterion` where a machine can read it.

**And a prediction refuted, which is the finding it produced.** HI-PRO (NCT04168203) was
predicted to fail that boundary: its arm is labelled *Extended Duration Thromboprophylaxis*,
its title says *to Prevent Recurrence*, and it is placebo-controlled — four surfaces reading
prophylaxis. Its eligibility requires *"Objectively-confirmed provoked DVT and/or PE"* already
*"treated for at least 3 months"*. **The arm label said prophylaxis and the population said
treatment, and the population governs.** P33 says a property is not the presence of its own
name; this is the other foot — *a property is not absent because a different name is present.*

**Back-filled, and the gate is what found it.** `scripts/standard_version_agreement_gate.py`
was written to close the drift above, and on its first live run it refused — reporting **ten
properties listed in the table and named in no version-log entry**: P1–P9, the original set,
and **P30**. P1–P9 are now named in the 1.0.0 entry where they belong. P30 — *prose is not
evidence; a report is not an artefact* — entered the table between 1.10.0 and 1.11.0 with no
entry of its own, and is dated here rather than back-dated to a version it cannot be shown to
have shipped in.

> A gate written to catch one drift found a second on its first run, in the same file, of the
> same kind. That is the ordinary return on writing the check instead of the sentence, and it
> is why *"nothing yet checks that they are equal"* is never a finished thought.

### 1.13.0-2026-08-19
Adds P35 and P36. Recorded here on 2026-08-19; the properties reached the table and the
stamped version when `apixaban-vte-prophylaxis` was re-pooled, and this log entry did not.

**P35 — the primary outcome is read by matching its registered text, never by position.**
`outcomeMeasures[0]` is the MAJOR-VTE **secondary** for ADVANCE-2 and the **primary** for its
three companions, so a positional read pools one trial's secondary against three trials'
primaries with nothing malformed anywhere — no parse error, no null, no missing key, four
numbers of the right shape.

**P36 — heterogeneity can neither establish nor refute estimand coherence.** Measured both ways
in one night: mismatched estimands pooled at I² **0.0%** and **3.9%** on the two ablation
reviews, and at **83.6%** against **67.8%** for the matched estimand on apixaban prophylaxis.

### 1.12.0-2026-08-19
Adds P34, from a measurement across two adjudications of the same night.

**P34 — the gap between a code rate and a disposition rate measures the vocabulary.** Two blind
cross-family adjudications, same two seats, same method, same corrected question form:

| topic | code rate | disposition rate | gap |
|---|---|---|---|
| `ablation-af-medical-therapy` (45 trials) | 66.7% | 80.0% | **13.3 pts** |
| `early-rhythm-control-af` (44 trials, first chunk) | 81.8% | 81.8% | **0 pts** |

Read naively, the second run looks better on both numbers and dramatically more consistent.
**It is not a fact about the trials or the instruments.** The ablation vocabulary has two codes
— `ABLATION_IN_ALL` and `ABLATION_VS_ABLATION` — that are two readings of *why* a trial is out
and **both mean EXCLUDED**, so two seats could disagree on the code while agreeing on the
verdict. The rhythm vocabulary's codes fan out onto four distinct dispositions, leaving almost
no room for that.

> **A vocabulary whose codes collapse onto one disposition inflates the gap; one whose codes
> fan out closes it.** The gap is a property of the coding scheme, not of the readers.

So: report an agreement rate **with the vocabulary that produced it**, and never compare gaps
across topics whose vocabularies differ. Reporting "66.7% then 81.8%" as improvement would be
comparing two different measuring instruments and calling it progress.

This is the same family as P31 — disagreement is a property of the question until shown
otherwise — one level up: *agreement statistics* are a property of the coding scheme until
shown otherwise.

### 1.11.0-2026-08-19
Adds P32 and P33, and records the seventh contamination route.

**P32 — an indicator must be able to move only if the diagnosis is right.** Four predictions
were stated before their runs in this stretch and all four were wrong; each correction was the
real finding. The fourth is the subtlest and produced this property.

`early-rhythm-control-af` carried `kNA = 202` against a sibling's 45, and that was named as the
symptom of asking an ablation question of strategy trials. The symptom was real. **The number
was the wrong indicator.** Under the corrected identity set kNA went **202 → 258** — it rose,
because that set deliberately excludes bare `ablation` and **a narrower, more precise identity
set finds fewer things**. A rising kNA is consistent with the fix working *and* with it
failing, so it could never have tested the claim.

> The indicator that worked was the one that could not move for any other reason: **do the
> review's own included trials classify correctly?** Three of four became four of four.

Name the quantity that changes *and could not change otherwise*. A number that merely
correlates with the defect is not a test.

**P33 — a keyword for the name of a thing is not a test for the thing.** CASTLE-AF's registered
primary is *"All-cause mortality or worsening heart failure requiring unplanned
hospitalization"* — unmistakably a composite, containing neither the word "composite" nor the
phrase the rule searched for. The ESTIMAND limb **failed**, toward NOT-POOLABLE, on this
review's own included trial. Detect the property structurally: a composite is *a mortality term
plus another clinical event term in one endpoint*, which is what a composite **is**.

This is P14 one level up. P14 says identity is not substring containment over clinical text;
P33 says a *property* is not the presence of its own name.

**And the seventh contamination route, through a COPY.** The first version of this topic's
screener was a `sed`-rename of the sibling's. It parsed, ran, and produced a complete set of
551 verdicts — all answering the sibling's question, because those rules ask whether *ablation*
is the contrast. **An antiarrhythmic-drug arm is the INTERVENTION for one review and the
COMPARATOR for the other**, so the verdicts were not merely wrong, they were *invertible*.

> **"I adapted the neighbouring topic's screener" is the single most natural thing anyone will
> do at scale, and it is the one shape that produces a full, confident, wrong answer set.**

No guard covers it: the file is new, the filename right, the topic key right, and every
existing contamination check passes. Recorded in DEFECT-REGISTRY as route 7b with the
detector that would catch it named and not built.

### 1.10.0-2026-08-19
Adds P28 and P29. **P28 records a correction to an instruction from the orchestrator, and the
lane was right to refuse it.**

**P28 — a defective question invalidates every answer it produced, agreements first.** The
standing instruction for the cross-family adjudication was: *where both seats agree and a coded
field settles it, spot-check rather than re-read.* That is sound in general and **wrong here**,
because the question itself had already been shown defective.

Sixteen of the sixty-two agreements were `A=YES, B=YES`, mapped ELIGIBLE. An **adjunct** trial
with a `NO_INTERVENTION` control answers exactly that way — *"mental training vs no
intervention, in patients who all had an ablation"* has an arm delivering ablation and an arm
that is not itself an ablation. **The old question cannot distinguish that from
ablation-against-usual-care**, and it fails in the direction that *admits* trials.

Re-asked under the corrected question: **5 of the 16 flipped to EXCLUDED**, 3 held, 8 disputed.

> **Agreement under a question that cannot make the distinction is not evidence about the
> distinction.** It is the strongest-looking evidence available and it is worth nothing, which
> is what makes it dangerous: the sixty-two were the answers nobody would have thought to
> check.

So: **a correction that stops at the cases that looked wrong is not a correction of the class.**
When a question is found defective, its agreements are re-asked first, not last.

**P29 — a filter asserts an expected count.** Third instance in one session of one shape. The
`rc == 0` guard added an hour earlier **worked correctly** and the run still yielded nothing:
Codex answered without the pipe separators the `grep` required, so a complete, correct answer
set was discarded by the filter.

| # | what happened | what it looked like |
|---|---|---|
| 1 | `codex exec` refused — untrusted directory | zero matching lines |
| 2 | `ELIGIBLE_NOT_POOLABLE` branch unreachable | a disposition legitimately never used |
| 3 | answers emitted in an unmatched format | a seat that returned nothing |

> **Something that did not happen looks exactly like something that happened and found
> nothing.** That names the class more precisely than "silence" does, and it is why an
> expected-count assertion — not an exit code — is the discriminator.

**And two device names read as the intervention.** Codex read `Device: EPICOR` (an *epicardial
ultrasound* ablation system) and an oesophageal deviation catheter used *during* an ablation as
the ablation itself. **A device used during an ablation is not the ablation, and the coded arms
do not say so.** Same shape as the substring findings, now in device names.

### 1.9.0-2026-08-19
Adds P27, and records an empirical asymmetry worth keeping.

**P27 — a reframed question travels to every site that asks it.** On 2026-08-19
`topic_identity.locate()` was reframed from *"where does the drug appear"* to **"what exactly
was randomised"**, and two defects dissolved under it. Hours later a blind adjudication packet
was sent to two other model families asking, of 130 trials, *"does any arm deliver catheter
ablation"* — **the discarded form of the same question**.

Twenty of the 25 hard contradictions are trials where **the ablation is the setting and an
adjunct is the contrast**: sedation versus anaesthesia *for* an ablation, oesophageal cooling
*during* one, transseptal technique, haemostasis, monitoring, nurse-led follow-up. To the
discarded question the honest answer is **yes, an arm delivers ablation** — every arm does,
which is precisely what makes it background.

> **A fix applied at one site is not a fix of the class, and a question is a site.** The
> reframing reached the classifier and not the prompt, so a rule this project already held was
> re-learned at scale the moment the old question travelled to another instrument.

The measured cost: an agreement rate of 47.7% that is substantially a measurement of the
question's ambiguity rather than of the trials. Two independent seats were not disagreeing so
much as answering two different readings of a question that had two.

**The asymmetry, kept as a measurement.** Over the same 130 trials, asked as two limbs:

| limb | contradictions | refusals |
|---|---:|---|
| *is there an ablation arm* (positive) | **1** | agy 37 / codex 18 |
| *is there a non-ablation control* (negative) | **24** | **agy 37 / codex 0** |

Identifying what something **is** and identifying what it **is not** are different orders of
task, and two independent instruments had **opposite calibration on the negative** — one
refused thirty-seven times, the other never once. This is the empirical version of the standing
rule that *a negative claim is the one most worth computing*.

### 1.8.0-2026-08-19
Adds P25 and P26, both found in the **harness** of a cross-family adjudication rather than in
its results — which is the worst place for them, because the harness is what makes the results
mean anything.

**P25 — a pipe never interprets output it has not proved was produced.** `codex exec` refused
with *"Not inside a trusted directory and --skip-git-repo-check was not specified"*, and the
`grep` filtering its output turned that refusal into **zero matching lines**.

> **A filter over a subprocess's output converts a loud failure into a quiet one.**

And the specific damage here is the worst available: **zero answers is indistinguishable from
zero disagreements.** A dead seat would have read as a concurring one, turning an *absent
check* into *evidence of agreement* — in a procedure whose entire value is that the second seat
can dissent. So: assert the exit status before reading, and treat an empty filter result as
NOT_ASSESSABLE rather than as a negative finding. This is the same family as the pipeline
`$?` lesson already in the operating rules, arriving through a filter instead of a pipeline.

**P26 — an agreement rate is computed over independent answers only.** Codex emitted every
answer twice. The duplicates were verified self-consistent (33 distinct trials, 0 answered
differently between copies) and then **deduplicated**, because counting one model's repeated
answer as two votes **manufactures agreement out of verbosity**. Repetition by one instrument
is not independence, and a seat that returned nothing is absent rather than concurring.

### 1.7.0-2026-08-19
Adds P24, and records two method lessons from the screen that produced it.

**P24 — every disposition must be demonstrably reachable.** The 621-trial screen of
`ablation-af-medical-therapy` returned `ELIGIBLE_NOT_POOLABLE: 0`. That was not a finding about
the evidence base; the branch **could not be reached**. `ctgov_transport.fetch_raw` defaults to
`fields="protocolSection"`, so `hasResults` is absent from every cached record and
`not doc.get("hasResults")` was always true — every eligible trial routed to "no results yet",
including trials that had posted results and could have been assessed.

> **A disposition that cannot be reached is not a conservative default.** That is why it hides:
> the branch looks cautious, so a zero sitting in it invites no suspicion at all. A wrong
> *large* number gets argued with. A wrong *zero* in a careful-looking cell gets read as
> diligence.

**The tell was the zeroes, not the big number.** The same run reported `EXCLUDED: 556` and
`NEEDS_ADJUDICATION: 0`, and 135 of those exclusions were wrong. What broke through was not the
implausible 556 — it was **two implausible zeros sitting beside it**. A count that *should
sometimes be non-zero and never is* says more than a count that is merely surprising, because
the first is a statement about the instrument and the second only about the data.

**A known-answer file must not smuggle in knowledge from outside the instrument's inputs.**
The screener was told RAFT-AF must clear the intervention limb, because RAFT-AF *is*
ablation-based — its TITLE says so. Its `armGroups` do not; they declare `Procedure: Rhythm
control`. **The instrument was right and the expectation was contaminated by knowing the
answer.** Second occurrence here: the placebo-naming file expected ADVANCE-3 to behave like
ADVANCE-2 and the registry disagreed. An expected answer must be derivable from the same fields
the rule reads, or it tests the author rather than the code.

**And a hand-written vocabulary cannot be complete.** `Device: Catheter Ablation` vs
`Drug: Drug Treatment` was excluded on the comparator limb because the term list held "drug
therapy" and not "drug treatment". Every gap in such a list failed toward EXCLUSION — the
withholding direction, in the most banal possible mechanism. Where a coded field exists
(`Drug:` / `Procedure:` / `Device:` intervention types), it governs; and where the vocabulary
simply cannot say, the verdict is **UNSETTLED, never "not found"**.

### 1.6.0-2026-08-19
Extends P16 with its missing fourth clause, and adds P23. Both come from **a guard that was
green because the case it existed for had never happened.**

**P16, fourth clause — the guarded case must have OCCURRED.** The pagination guard reads
`returned == totalCount` to confirm a fetch was not truncated at a page boundary. It read
`totalCount` from the **last** page, where the API returns null; `countTotal` populates it on
the **first**. Every query this project had ever run fit in a single page, so the last page
*was* the first, and the defect could not appear. It shipped that morning inside
`regate_cascade_2026_08_19.py` and was exercised, correctly, on five topics — proving nothing.
It surfaced within hours on the first two-page query ever run here.

> **A guard whose triggering condition has never occurred in the data it has run on is
> unproven, however green it reads.** Three parts were satisfied — it could fire, it was silent
> on the correct case, and the build's success was not the evidence. What was missing is that
> the *world* had never presented the case. "It would have caught it" is a claim about an event
> that never happened.

This generalises well past pagination. Any guard written for a rare condition — a truncated
fetch, an empty result set, a missing baseline, a second page, a duplicate id — is untested
until that condition is *present in a run*, and a synthetic input is the weaker substitute the
known-answer rule already warns about.

**And the direction is why it was recoverable.** It printed `returned==totalCount: False` on a
complete fetch — a false ALARM, on a screen someone was reading.

> **A guard that fails loud is recoverable. A guard that fails quiet is the class this project
> has spent two nights on.** When choosing how a check behaves under its own failure, choose
> the noisy wrong answer over the silent one.

**P23 — a design filter is a recall hazard, and its cost is measured, not assumed.** Four
distinct shapes of one defect are now on record, all in the withholding direction:

| topic | lost | to |
|---|---|---|
| `sglt2-hf` | DELIVER | a CONDITION term one word too narrow |
| `iv-iron-hf` | AFFIRM-AHF, HEART-FID | a CONDITION term one word too narrow |
| `apixaban-vte` | NCT02366871 | `phase=[PHASE3,PHASE4]` on a PHASE2 trial |
| `ablation-af-medical-therapy` | **CABANA (n=2204), RAFT-AF** | the same filter on trials registered `phases: ["NA"]` |

**NA is not a phase.** A filter that *enumerates* phases silently drops every registrant who
declined to declare one — and on the ablation topic that was two of the three pivotal trials,
including the largest. Recall against the review's own included set is therefore **measured for
every executed search**, and a query that misses is **recorded rather than replaced**.

### 1.5.0-2026-08-19
Adds P21 and P22, from Mahmood's decision on `ablation-af-review` — **and the decision was
better than any of the three options the packet offered.**

**P21 — an ambiguous question is built as several reviews.** The packet framed the ablation
question as a choice between three restatements, and tabulated each by *which trials it drops*:
A drops EAST, B drops none but makes the topic name wrong, C drops CABANA and EAST. Every row of
that table is a count of evidence discarded.

> **The packet was well-built and it framed the problem the wrong way round.** All three
> questions are legitimate, and each trial genuinely belongs to at least one of them. There was
> no good answer because the question "which do we keep" had no good answer — **choosing is a
> decision to withhold, and nothing in this guard set catches it.** Three reviews discard
> nothing and give each question its honest answer.

This is why it is a property and not a note on one topic: the same shape is already queued.
`apixaban-vte` was blocked on TREATMENT versus PREVENTION over pools of 34 and 33 — **two
legitimate questions with nearly equal evidence, where choosing discards one for no reason but
tidiness.** Both are now to be built. `bococizumab-lipid` gets the same treatment if its
truncation resolves into more than one real question, and a packet only if the question cannot
be recovered from source at all.

The rule does **not** license inventing readings. A reading qualifies when it traces to named
registry fields of trials the corpus already holds, exactly as the three ablation candidates
did.

**P22 — deliberate sharing is recorded on both sides.** Splitting one topic into several makes
cross-topic trial sharing intentional rather than accidental: CASTLE-AF and RAFT-AF will each
appear in all three ablation reviews by design. Roughly a fifth of the corpus's registration
identities are already shared across topics, so the rule was already needed and is now
unavoidable. **Sharing is legitimate; unrecorded sharing is not**, and any corpus-level count
computed by summing per-topic k double-counts — which every sharing page must say on its face.

### 1.4.0-2026-08-19
Adds P18, P19, P20 and strengthens P10. All four come from **re-gating five topics that were
already complete**, and every one of them was invisible on a page that read as finished.

**P18 — a restated quantity is reproducible by a command.** `sglt2-hf`'s stored cascade
reproduces at exactly one classifier revision (`f2bf16022`) and at no other. Two later commits
shipped the same night and were never carried back. **What made the page look current is that
it carried a correction note** — a `restated_2026_08_19_placebo_discriminator` block naming its
own 36 → 46 delta, dated the same day as the commits that superseded it. The same PRISMA
sentence has now said 43, then 36, then 46, then 49; each was true when written. A fifth
correct number is not the fix. The fix is that the number is produced by a command and refused
by a gate.

**P19 — a promotion reaches every derived block.** `alirocumab-lipid` was restated from k=6 to
k=8 in its headline and results. Left at k=6: `prisma_flow.included`, `k_cascade.k_included_in_object`,
the whole published-meta comparison including a field named `ours`, the estimator-sensitivity
table, and **the prediction interval — whose own text calls it "the number to quote"**. One
page, two answers, and the superseded one in the table a reader consults to compare us against
the literature.

**P20 — the cascade reconciles with itself.** Three of five objects stored `k0` in
`k2_role_located`, so **the stage named "role located" counted the records whose role could not
be located** and `kNA` was added twice. It is invisible on the two objects whose `kNA` is 0 —
*a sum that is right whenever the thing it omits is zero has not been tested.*

**P10 strengthened.** The served-bytes verifier's first run returned `md5 served == disk: OK`
on a page that was stale, because that topic's pooled estimates had not changed and only its
cascade sentence had. A hash cannot detect staleness; only content projected from the object
can.

Two further lessons from the same night, recorded here because they are about instruments
rather than pages:

- **A round trip through a parser is not a copy.** A reproduction gate failed because SEs were
  re-derived from per-trial CIs rounded to 2 dp for display; a guard-proof restored a planted
  object by re-serialising a parsed copy and left the tree in a state neither the builder nor
  git had produced. Where the original bytes exist, restore those.
- **A lint that counts its own documentation as a violation taxes writing the rule down.**
  `lint_subprocess_decode.py` read a comment saying `text=True` as a hazard site; two of its
  eighteen baselined entries were prose describing the rule.

### 1.3.0-2026-08-19
Adds P15, P16, P17 — all three from defects that produced *correct-looking output*.

**P15 — short-circuit attribution.** bempedoic's screen reported 13 of 16 trials failing on
the OUTCOME limb. Restated on two axes, only **2** are genuinely eligible-but-unpoolable; the
rest fail population or comparator anyway. The screener checked outcome FIRST and returned on
first failure, so **the limb it named was decided by the order the checks were written in**.
Sixteen verdicts, sixteen right answers, attributed reason wrong throughout — and nothing
downstream could detect it, because everything downstream reads verdicts. That number was
relayed onward before it was corrected.

**P16 — a guard is proven in three parts.** The foreign-registration-id guard, written against
the cross-contamination class, was destroyed by the heredoc-mangling class: its `\b` became a
literal BACKSPACE byte. It compiled, imported, ran, and the build printed `HELD 7 / REFUSING 1`
and success — while unable to match anything. Exposed only by planting a fake id. Repaired, it
then fired on a *correct* object. **The last clause is the one people skip**: a build reporting
success is not evidence a guard within it can fire.

**P17 — negative claims are computed.** `duplicate_seeding_check` asserted
`shared_with_other_topics: false`. Computed, it is **true** — two of sglt2-hf's trials are also
seeded by another topic. "Not shared", "no conflicts", "none found" all read as diligence and
are free to assert.

### 1.2.0-2026-08-19
Adds P13 and P14. Both are the same family as P11: the check ran, and it ran on the wrong
thing.

**P13 — keyed by entity.** `build_to_standard.py` accepted a topic argument and held
bempedoic-acid-review's executed queries, dates and record counts as MODULE CONSTANTS,
assigning them to whatever topic was passed. Run on another topic it would have written one
topic's executed search onto another — a **fabricated provenance record, on the property whose
entire purpose is provenance**. It did not ship only because it crashed first on an unrelated
hardcoded key and because the write happens at the end. **Luck, not design.** A parameter a
function does not honour is worse than no parameter: the signature advertises a generality the
body lacks, and it fails silently wherever the shapes happen to line up.

**P14 — no substring matching over clinical text.** Screening sglt2-hf's trials for a
two-component endpoint by substring returned ZERO for both EMPEROR trials, whose primaries ARE
that endpoint, because the registry writes `Cardiovascular (CV) Death` and the matcher wanted
contiguous `cardiovascular death`. It produced the right answer for one trial for the wrong
reason and the wrong answer for two others; trusted, it implies the pool was k=1 rather than
k=3. Parenthetical abbreviations are ubiquitous in registry outcome names.

### 1.1.0-2026-08-19
Adds P11 and P12, both from live defects on 2026-08-19.

**P11 — the coded field governs.** `comparators_identified_and_consistent` FAILed `sglt2-hf`
on `'placebo added to background heart failure therapy'` vs `'placebo'`, while
`comparator_type` read `'placebo'` on both and every control arm was labelled exactly
`placebo`. Routing through `text_match` was necessary and NOT sufficient: the strings really
are different and `text_match` was right to say so. **The error was asking a text question at
all**, when the semantic answer was recorded in the coded field beside it. This will recur
anywhere the corpus holds both a code and a label, so it is a property rather than one
assessor's fix.

**P12 — the suite ran.** The `criteria_stated` / `criteria_predefined` split was committed
without re-running `known_answer_preconditions.py`, which had been erroring on import since
the rename. It was "verified" by running the batch assessment and reading the matrix — which
is checking VERDICTS, not REASONING, for the third time in one night, and done to the suite
whose entire job is to catch that. **A green matrix is not evidence the suite ran.**

### 1.0.0-2026-08-19
First versioned statement. Introduces **P1 executed search, P2 k cascade, P3 inclusion
criteria, P4 preconditions, P5 extraction table, P6 analysis output verbatim, P7 published-meta
comparison, P8 registration identity, P9 build stamp** and **P10 served-bytes verification** —
the original ten. *The property numbers were added to this entry on 2026-08-19, when
`scripts/standard_version_agreement_gate.py` was written and immediately reported that ten of
the forty properties were listed in the table and named in no entry.*

Encodes the lessons established through 2026-08-19:

- absent / empty / unreadable input is NOT_ASSESSABLE, never FAIL
- an instrument asserts the shape of its input and **raises** rather than returning a verdict
- a cross-instrument disagreement is evidence about the instruments only if both were asked
  the same question
- the known answer must come from the data, never from a fixture the author invented
- an object's record of what it EXCLUDED is not what it INCLUDED
- a Handbook section cited from memory is a registration number cited from memory
- a correct verdict reached by broken reasoning passes every outcome-based test; verdict and
  reason are two outputs and both need testing
- defects can run toward noise as well as toward silence — a check that fires on most of the
  corpus is more likely broken than the corpus is
