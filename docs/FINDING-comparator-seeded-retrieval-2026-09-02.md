# Comparator-seeded retrieval: the adapter, and the first named missing trials

Branch `feat/comparator-seeded-retrieval`, cut from `origin/main` (`d6f36e202`).
Implements the PHASE-0 firewall (`docs/comparator_seed_firewall.md`, commit
**`f152fd5a5418bff6ffea2e33dcec122e912241f0`**), which was written and committed
**before a single reference list was fetched**.

Every claim below is marked **MEASURED**, **INFERRED** or **CLAIMED**. Nothing has been
ingested — Phase 3 is a report, by design.

---

## What this produces

**MEASURED.** For the first time we can name a trial a published review included and we
do not hold. `outputs/comparator_seed_phase3.md` lists **178 named missing trials across
32 of 40 comparators**, each with its ClinicalTrials.gov accession and PubMed id.

The first entry, as an example of the shape:

> **PMC8510986** — SGLT2 inhibitors for cardiovascular outcomes in type 2 diabetes.
> Their k (measured) 69 references / 63 distinct trials. Search closed 2019. We hold 6.
> Missing and named: Bailey 2010 (NCT00528879), Barnett 2014 (NCT01164501),
> Cefalu 2013 CANTATA-SU (NCT00968812), Fioretto 2018 DERIVE (NCT02413398),
> Frias 2016 DURATION-8 (NCT02229396), … 37 in total.

---

## Phase 0 — the firewall, committed first

| | |
|---|---|
| firewall commit | **`f152fd5a5418bff6ffea2e33dcec122e912241f0`** |
| first `efetch` of any comparator | after it, in a later shell |
| scored topics, excluded from seeding (MEASURED) | **238** |
| scored comparator DOIs, excluded as seeds (MEASURED) | **194** |
| corpus topics / seedable (MEASURED) | 936 / **778** |

**The DOI check is only half the rule, and the missing half is the interesting half.**
Blocking a comparator by DOI stops us re-using a work we already score against. It does
**not** stop us seeding a scored *topic* from a different review of the same subject —
and that collision lives in the subject matter, not in any identifier, so no identifier
check can see it. A topic-side screen was added: a distinctive token (≥5 chars) shared
between a scored topic key and the comparator title flags the pair.

- **MEASURED: the DOI check dropped 1 of the 41 otherwise-eligible candidates**
  (`10.1186/s12936-026-05954-5`, an RTS,S / R21 malaria-vaccine review — `MALARIA_VACCINE`
  is a scored topic).
- **MEASURED: the topic screen flags 22 of the 40 selected** as
  `BLOCKED_PENDING_PICO_ADJUDICATION`.

The token screen is over-inclusive and produces false flags (a cardiology review flagged
against `CRYPTOCOCCAL_MENINGITIS_AFRICA` on a shared generic token). Over-inclusive is the
right failure direction for a firewall — but see the addendum: **being over-inclusive did
not make it safe**, and its first version silently missed two real collisions while
flagging fourteen false ones. **None of the 40 is cleared for ingest by this run**, and
that is the intended state at the end of Phase 3.

---

## Phase 1 — 40 open-access comparators, 20 cardiology / 20 infectious disease

**MEASURED.** `scripts/comparator_seed/harvest.py`, PMC Open Access subset via
E-utilities only, `"open access"[filter]` on `db=pmc`, 36 topic terms (18 + 18),
2016–2026, title-restricted to meta-analysis or systematic review.

| | |
|---|---|
| distinct PMC candidates enumerated | 331 |
| `efetch` returned no article element | **0** |
| XML parse errors | **0** |
| included-study list extracted (`TABLE` / `SECTION`) | **187** |
| no list found (`NOT_FOUND`) | **144** |
| pool after k ≥ 4 and the DOI firewall | 167 |
| **selected** | **40** (20 / 20) |

The 144 `NOT_FOUND` are reported, not dropped into a smaller denominator. Selection was
**at most 2 per search term, then by descending k** — chosen for topic spread and seed
yield, so the 40 are the *largest* reviews per topic and are **not** a representative
sample of the 187. Stated rather than corrected.

The full 187-comparator pool is committed as `outputs/comparator_included_studies.json`;
the 147 not selected are ready to use without re-fetching.

**Declared search close date: INFERRED, found for 29 of 40**, bounded to the methods
section and with the matched sentence quoted in the JSON. The 11 not found are marked
`NOT_FOUND` with the reason.

---

## Phase 2 — the extraction, and what the planted case caught

**MEASURED.** An included study is a reference **cited from the study-characteristics
table** (route `TABLE`, 158) or from an included-studies section (route `SECTION`, 29).
Both are positions in the XML tree. No prose regex is used to find studies.

`--selftest` runs a planted document the extractor **must** match (3 studies via `TABLE`,
a background reference that must not leak, identifier fields that must be lifted) and a
negative document it must report `NOT_FOUND` rather than as an empty success. **It failed
twice before passing, and both failures were real:**

1. **`\bNCT\d{8}\b` misses the id whenever it abuts a digit.** Citation text runs
   together as `…2019NCT12345678`; there is no word boundary between `9` and `N`, so the
   accession is silently dropped. My first fix — `(?<![A-Za-z0-9])` — was wrong in the
   other direction and rejected exactly the run-together case it was meant to catch. The
   correct anchor excludes a preceding **letter** only. The self-test now carries both the
   traps (`NCT123456789`, `XNCT12345678`) and the cases that must match.
2. **`article-id[@pub-id-type="pmc"]` nulls the provenance field on half the corpus**,
   because publishers deposit the id under `pmc` *or* `pmcid`. `seed_source_pmcid` was
   `null` on those records — a provenance field that silently fails is worse than none.

**Real-case must-match, verified by eye before any zero was trusted.** PMC5844104
(antiplatelet therapy in ARDS): Table 1 has **10 rows — 1 header + 9 studies** — and the
extractor returns exactly those 9, in table order, with correct authors, years and PMIDs.
It does **not** take the adjacent 43-row Table 2 (a subgroup summary).

Per included study: first author · year · acronym · NCT · PMID · DOI, each present or
`null`, with **`fields_not_found` naming every field that was looked for and not found**,
so `null` can never be read as "does not apply".

### Where a model belongs, and where it does not

The PICO-mapping decision — does this trial belong to one of our topics — is the one
place a model is warranted. **The per-trial version has not been run** (see "Explicitly
not done"); the comparator-level version has, and is in
`outputs/comparator_seed_topic_adjudication.json`. Nothing else in this lane needed a
model: extraction is tree position, identifier resolution is a PubMed databank record.
Codex was intended for the bulk parsing and was not used, because after the structural
route there was no bulk parsing left that a parser could not do exactly.

---

## Phase 3 — measure, before ingesting anything

**The join key is the whole difficulty, and it is the finding.** Their included studies
carry PMIDs; our holdings are keyed by NCT. PMIDs were resolved to accessions from
**PubMed DataBank `ClinicalTrials.gov` records** (MEASURED, 1,077 PMIDs).

Holdings are the union of `outputs/nct_to_apps.json`, `outputs/corpus_ncts.txt` and
`outputs/pubmed_nct_linkage.csv` — **2,610 NCTs and 489 PMIDs**. 16 NCTs mapped to more
than 20 apps each (up to 591) are clone contamination, not evidence of holding, and are
excluded by name. **A positive control runs before any status is assigned**: three NCTs we
certainly hold must report `HELD` and two synthetic accessions must not. A join that can
only say "no" is not a join.

**MEASURED, over 1,275 included references / 1,258 distinct trials across the 40:**

| status | n | meaning |
|---|---|---|
| `HELD` | **28** | accession in our holdings |
| `NOT_HELD` | **178** | resolved to an accession, absent from holdings — **these are the named missing trials** |
| `OUT_OF_SCOPE_DESIGN` | 106 | the comparator's *own* characteristics row calls it a cohort / case-control / observational study; the row is quoted |
| `COMPANION_PAPER` | 17 | a second reference to a trial already counted |
| `UNRESOLVABLE_NO_REGISTRY_ID` | 794 | PubMed knows the record and it carries **no** ClinicalTrials.gov accession |
| `UNRESOLVABLE_NO_PMID` | 152 | no NCT in the citation and no PMID PubMed would resolve |

**Of the 206 studies the instrument can actually answer, we hold 28 — 13.6%.**

The 946 `UNRESOLVABLE` are the load-bearing number. **Calling them "not held" would have
manufactured 946 missing trials out of a key mismatch**, and the first version of this
script did exactly that: it reported `NOT_HELD 984`. An NCT-keyed store cannot answer a
question about a trial that has no NCT — mostly pre-2005 trials, which registration
predates. That is a property of our holdings design, not a retrieval failure, and it is
reported as its own state rather than folded into either arm.

### Their declared k is not usable, and the reason is instructive

**INFERRED, LOW CONFIDENCE.** A prose `declared_k` was extracted from the abstract as a
cross-check. It agrees with the structural count exactly **13 of 33 times**, within 5
**16 of 33**. It is reported with every candidate value and the quoted sentence, and it is
**not** used as anyone's k.

Its first version was worse, and the bug is the same family as the NCT one: **`\b` fires
inside a hyphenated number-word**, so *"Sixty-four trials … were included"* matched
`four` and reported **k = 4** for a review of 64. The remaining disagreement is real
ambiguity — an abstract states subgroup counts in the same grammar as its total
(*"four trials with metformin"*) — which is precisely why the study list is taken from
tree position and not from the sentence.

---

## What I did not touch

**The retrieval-side `hasResults=False` defect is untouched and handed over.** Registry
results are not publication; a trial with no posted results can still have a published
paper a review includes. It would bite exactly here: any future step that ingests these
178 named trials by querying the registry would drop the ones with no posted results, and
the drop would look like "not found" rather than "filtered". Noted, not fixed.

**CLAIMED, not measured here:** the 10.4% search-recall headline. The lane at
`F:/wt-retrieval` established that its seed file was never vendored, so that figure is an
assertion rather than a measurement; it is used as a comparator for nothing in this lane.

---

## Re-running it

```
python scripts/comparator_seed/build_firewall.py            # fails closed if the scored set is absent
python scripts/comparator_seed/extract_included.py --selftest
python scripts/comparator_seed/harvest.py                   # PMC OA subset -> C:/…/xml
python scripts/comparator_seed/extract_included.py
python scripts/comparator_seed/phase3_measure.py --repo <repo>
python scripts/comparator_seed/render_phase3.py
```

Adding a field is adding rows to `TOPICS` in `harvest.py`. Nothing else changes — that is
the test the adapter was built to pass. All scratch, caches and XML live on `C:`;
`F:` had 255 MB free.

---

## Addendum — adjudicating the topic-side flags, and the hole the screen had

**MEASURED.** The exact-token screen was replaced with a stemmed one (drop digits,
singularise) after adjudication showed it had a hole, not just noise:

| | exact-token screen | stemmed screen |
|---|---|---|
| comparators flagged of 40 | 18 | **22** |
| true collisions caught (of 5) | **3** | **5** |

The two it missed are the load-bearing ones. `COVID19_VACCINES` was missed for a review
of *"heterologous and homologous covid-19 vaccine regimens"* — the scored key spells it
`COVID19` (digit) and `VACCINES` (plural), the title yields `COVID` and `VACCINE` — while
the **same generic token `VACCINE` flagged that review against five unrelated vaccine
topics**. And `SGLT2I_HF` was missed entirely for PMC8510986, the highest-yield comparator
in the whole set. **A screen that over-flags on a generic token while under-flagging the
exact collision is not failing closed; it has a hole, and the over-flagging is what makes
it look conservative.**

`outputs/comparator_seed_topic_adjudication.json` records one decision per flagged pair,
written as data:

| verdict | n | effect |
|---|---|---|
| `COLLISION` | 5 | may not seed that topic |
| `REVIEW` | 3 | intervention family overlaps, question differs — blocked, fail closed |
| `NO_COLLISION` | 14 | flag is an artefact of a generic shared token (`AFRICA`, `TARGETED`, `FAILURE`, `DRUG`) |

**MEASURED consequence: 57 of the 178 named missing trials (32%) sit on blocked
comparators and cannot seed anything. 121 remain seedable** once the per-trial PICO
mapping runs.

### Explicitly not done

**The per-trial PICO mapping (Phase 2's one model decision, 1,258 trials) has not been
run.** It is the gate to ingest, and Phase 3 forbids ingest, so nothing downstream is
blocked by its absence — but it is scope from the brief that is not delivered, and the
`REVIEW` verdicts above are exactly what it would resolve. Codex was probed for the bulk
work and returned nothing within 90 s on a single `codex exec` with stdin closed; one
timeout is not proof a tool is dead, so it is recorded as unprobed rather than unavailable.
