# Source search: which documents carry the data for THIS trial

**Built. `scripts/source_finder.py`. One call per trial, and it inverts the problem.**

The corpus had only the evidence search — *what trials exist for this question*. This is the
other one: *what documents carry the data for this trial*. The query is the registration id
in full text.

## Run over 16 HFrEF trials

```
candidates found by the NCT full-text query   1050
documents examined (capped at 40 per trial)    468
NOT examined -- not clean, NOT LOOKED AT       582

  CARRIES_DATA      206   44% of examined
  MENTIONS_ONLY     176   38%
  NOT_ASSESSABLE     86   18%
```

**Every one of the 16 trials has at least one document carrying data for it; the median is
16 such documents per trial.** EMPA-REG's id alone returns 217 candidates.

### By source class

| class | n |
|---|---|
| MENTIONS_ONLY | 176 |
| CARRIES_DATA (unclassified type) | 124 |
| **META_ANALYSIS_CONTAINING_IT** | **67** |
| CANDIDATE_PRIMARY_REPORT | 45 |
| SECONDARY_ANALYSIS | 25 |
| UNCLASSIFIED | 24 |
| DESIGN_OR_PROTOCOL | 7 |

⭐ **67 meta-analyses that already extracted these trials, found per trial rather than
hoped for per topic.** Mahmood ruled prior metas the best source; this is how you locate
them reliably.

## MENTIONS_ONLY is real, and it is 38%

**176 of 468 documents name the trial and carry no data for it.** You predicted this from
the dose-selection paper that named both trials and reported neither; measured, it is more
than a third of everything the query returns.

The class is decided by **content**, never by title: the id must have a count, an estimate,
an interval, or a methods statement within 600 characters of it in the full text. A
meta-analysis is full of numbers — the question is whether any of them is attached to *this*
trial.

## ⛔ NOT_ASSESSABLE is a separate class and must never be merged into MENTIONS_ONLY

**86 documents (18%) have no open full text**, so whether they carry data cannot be decided.
Calling those "mentions only" would infer absence from our own inability — the same error as
recording a 503 as "no new records". They are counted apart and always will be.

## Three defects found while building this, all mine, all caught by disbelieving a clean number

**1. `NOT_ASSESSABLE 40 of 40`.** The first run reported that every candidate lacked full
text. That reads as a fact about open-access coverage and was a fact about my URL: Europe
PMC's `/{source}/{id}/fullTextXML` 404s here for everything. **Testing it against a
long-standing open-access article whose full text certainly exists** is what separated "the
endpoint is wrong" from "these articles have no text". NCBI's PMC efetch returns 90KB for
the same article. Without that known-good control I would have published a broken fetch as
a finding.

**2. Six trials reported `candidates=None, examined=0`.** HTTP 503 — my own request rate,
for the third time this session. Six trials that look sourceless in that output have 8 to 70
candidates each. Retry-with-backoff now lives **inside the function**, because the fix
cannot depend on remembering to retry. Pass 1 is preserved beside the merged result as
`source-finder-run-pass1.json`.

**3. The cap is disclosed, not silent.** 582 of 1050 candidates were never examined. They
are **not clean and not absent** — they were not looked at, and the output says so on every
trial that was capped.

## What this does NOT establish

- **It is not a recall measurement yet.** Mahmood obtained the data for every HFrEF RCT from
  open sources **by hand**, and that list is the ground truth this should be scored against.
  **I do not have it.** Running the ladder and reporting what it finds is not the same as
  knowing what it missed, and I will not present the first as the second. Give me the hand-
  collected set and the comparison is one script.
- **`CANDIDATE_PRIMARY_REPORT` is a candidate, not an identification.** It rests on
  publication type, which is a weak signal for "this is the trial's own report".
- **The content test is evidence, not proof.** A number near an id is not certainly *about*
  that id.

## The rest of the ladder, not yet built

| rung | state |
|---|---|
| 1. NCT-in-full-text | **built and measured** |
| 2. citation chaining (references ↔ cited-by) | not built |
| 3. registry `referencesModule` | not built — and per the ruling, use it to FIND, never to CLASSIFY: `DERIVED` is a PubMed auto-link and `RESULT` is a sparse hand flag, 29 of 79 of which were systematic reviews |
| 4. regulatory discovery (FDA reviews, labels, EMA EPARs) | not built — where the hard-to-get data lives |
| 5. guideline bodies from GIN | 17 of 136 queryable, separately reported |
