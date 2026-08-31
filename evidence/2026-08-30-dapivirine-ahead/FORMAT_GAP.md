# The format gap on AGYW_HIV_PREP_REVIEW.html

Measured from the **built bytes** of `AGYW_HIV_PREP_REVIEW.html` (1,313,137
bytes), not from the generator's intent. Nothing here is fixed — this is the
measurement, written before any repair, because the honest shape is worth more
tonight than a partial fix.

## 1. The tab set — 6 of 10

The required set is **Protocol · Search · Screening · Extraction · Analysis ·
Paper Studio · HTA · Guideline · clinician · public**.

The file carries **8 tabs**, of which **6 are on the required list**:

| required | present? | tab id |
|---|---|---|
| Protocol | ✅ | `rt-protocol` — "1. Protocol" |
| Search | ✅ | `rt-search` — "2. Search" |
| Screening | ✅ | `rt-screen` — "3. Screening" |
| Extraction | ✅ | `rt-extract` — "4. Extraction" |
| Analysis | ✅ | `rt-analysis` — "5. Analysis Suite" |
| Paper Studio | ✅ | `rt-paper` — "7. Paper Studio" |
| **HTA** | ⛔ **NOT A TAB** | — |
| **Guideline** | ⛔ **NOT A TAB** | — |
| **clinician** | ⛔ **NOT A TAB** | — |
| **public** | ⛔ **NOT A TAB** | — |

Two tabs exist that are not on the list: `rt-report` ("6. Scientific Output")
and `rt-statistics` ("Statistics").

**Where the four missing readers actually are.** They are not absent from the
file — they are **buried as one card inside `6. Scientific Output`**, emitted
into the `removal` slot by `projectors_reader_layers.reader_renderings_card`.
A reader looking for the HTA view has no tab to click and no reason to expect
it three levels down inside a tab called Scientific Output.

**How the tab set is defined.** `ssot/projectors.py::TABS` — an 8-entry tuple.
Adding a tab is a change to that tuple, which is corpus-wide: every page in the
corpus would gain the tab, and every page without content for it would render
`ABSENT_STATE` prose. That is the correct behaviour and it is also why this is
not a five-minute change.

## 2. Screening — a count where a list belongs

**This is the sharpest failure of the format, and it is on the tab whose whole
purpose is to show the working.**

| | |
|---|---|
| Screening tab size | **8,947 bytes** |
| `<tr>` rows in the tab | **14** |
| distinct PMIDs rendered | **3** |
| records the screen actually decided | **1,443** |

The tab renders a **decision-count table** — `EXCLUDE 1238`, `UNDECIDABLE 107`,
`PASS_NO_ID 61`, and so on — plus the two resolved candidate misses and the
negative test. Every one of those is a *summary statistic over* the screen.

**The per-record ledger — one row per record, with the decision, the rule id
that decided it, and the field the rule read — is at:**

```
evidence/2026-08-30-dapivirine-ahead/BIBLIOGRAPHIC_SCREEN.json   (1,443 rows)
```

⛔ **That file is not in the downloadable HTML.** A reader who downloads the
review gets the counts and a pointer to a path they do not have. The one thing
that made this a moat — *a reader in Uganda can pull any record and check the
exclusion* — is the thing that did not ship.

The card even says so, in the file, in a line I wrote:

> *"Full ledger, one row per record with the rule that decided it and the field
> the rule read: evidence/2026-08-30-dapivirine-ahead/BIBLIOGRAPHIC_SCREEN.json"*

**A citation to a file the reader cannot open is not transparency; it is a
receipt for transparency.**

### What the format requires instead

Every one of the 1,443 records, in the file, with: record id (PMID or source
id), title, decision, rule id, and the field the rule read. At roughly 180 bytes
a row that is ~260 KB — **entirely feasible inside a 1.3 MB page**, and it is
the difference between publishing the screen and publishing a summary of it.

The same applies to the **63 registry candidates**: `search_executed_2026_08_30.
screen` reports `candidates_screened: 63, excluded_not_dapivirine: 16,
excluded_not_a_ring: 20 …` — counts by reason, with only the two withdrawn
trials named. **61 of 63 registry exclusions are not individually shown.**

## 3. Extraction — nothing links to its source

| | |
|---|---|
| Extraction tab size | 32,099 bytes |
| `<tr>` rows | 57 |
| **outbound `href="http…"` links** | **0** |

Not one extracted datum links to where it came from. The tab carries the
participant flow, the arm-code inversion finding, the verbatim analysis
populations and the RoB answers — all of which name their source *in prose*
("ClinicalTrials.gov posted results, resultsSection.outcomeMeasuresModule") —
but **no row is clickable**.

The whole page carries **2 outbound links**, both to clinicaltrials.gov, and
neither is attached to a data row.

This is the same defect as the corpus finding of **403 identifiers stored with
76.4% of pages rendering none** — an extracted number without a link to its
source does not belong in an Extraction tab.

## 4. Two tabs are effectively empty

| tab | bytes | rows | headings |
|---|---|---|---|
| **Search** | **343** | 0 | 0 |
| **Statistics** | **137** | 0 | 0 |

The Search tab is 343 bytes on a topic whose object holds a fully executed
six-source search with reported-against-retrieved counts, a concept block, an
adjudication rule, and four named limits. **None of it renders.** The
`search_executed_2026_08_30` block has no projector, exactly as the
bibliographic screen had none before this session.

## What this does to the regeneration and bespoke numbers

**A 13-of-13 regeneration score on a page in this state is measuring the wrong
artefact.** The page regenerates; the format does not survive the regeneration,
because the tabbed shell is not in the SSOT generator — `TABS` is a constant in
a projector, and per-tab content depends on whether a projector happens to
exist for each store block.

So the bespoke fraction — **55%**, 2,541 of 5,602 lines running unmodified on
untouched topics — must always be reported with:

1. it improved by **adding** general code, not retiring bespoke code; all 3,061
   bespoke lines are still on disk;
2. **it measures the wrong artefact** — 6 of 10 tabs, Screening showing 14 rows
   against a 1,443-record ledger that lives outside the file, Extraction with
   zero outbound links;
3. **LISTED is failing** — the index tile names HPTN 082 and FACTS-001, two
   trials with zero occurrences in this object.

## The order these should be fixed in, when they are

1. **Screening as a list.** Highest value, lowest risk, no corpus-wide change —
   it is one projector rendering rows it already has in a JSON file beside it.
2. **Extraction links.** Every per-trial row already carries `source_url`; the
   projector does not emit it as an anchor.
3. **Search tab projector.** The block exists and renders nowhere.
4. **The four reader tabs.** Requires changing `TABS`, which is corpus-wide and
   should be done deliberately, not as a side effect of one topic.
