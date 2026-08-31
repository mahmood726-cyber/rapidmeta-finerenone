# THE `ids` FIELD: what was measured, 2026-08-31

The prediction in `PREDICTION-BEFORE-MEASUREMENT.md` was written before any recoverability
scan ran. This file is the result.

## THE POPULATION, AND ITS KINDS

A search record in this corpus is one entry of `ssot/<topic>/<topic>.json ->
search.databases[]`. **40 entries across 18 objects, and not one carried an identifier list.**

The 40 are not one kind of thing, and counting them as one is how a denominator goes wrong:

    34   the search RAN
     6   the record states the source was NOT RUN (`tool: "NOT EXECUTED"`)

## THE BACKFILL

    predicted backfillable      6 / 40   (15%)
    ACTUAL                      8 / 40   (20%)

    BACKFILLED                  8    a set that records what that search RETURNED survives
    EXECUTED_NOT_CAPTURED      26    it ran; nothing on disk can recompute its set
    NEVER_EXECUTED              6    no set exists to recover
    --- sum                    40

**I MISSED LOW, AND I HAD NAMED THE OPPOSITE DIRECTION.** The prediction said the error would
be optimistic — thirteen consecutive ones here have been — and it was pessimistic by two.
The two are `ablation-af-heart-failure`'s pair: `ablation_split_search.json` carries query
identifier sets for a THIRD topic I had not opened when predicting. The named mechanism
(availability heuristic pulling the estimate up from the two files I had seen) was real; it
just ran the other way, because the file I had seen contained more than I had looked at.

All 8 recovered sets reconcile: `records_returned == len(ids) == len(set(ids))`.

## WHAT WAS REFUSED AS A RECOVERY SOURCE, AND WHY IT MATTERS

`evidence/2026-08-19-batch1/` holds 32 files containing identifier lists — cascade.json,
`*_screening.json`, reconcile.json, adjudication outputs. **Only three were admitted.** The
rest record DOWNSTREAM sets: what survived a screen, what an adjudication moved. Backfilling
`ids` from one would have written a smaller, tidier, wrong list and called it recovered —
and it would have broken the one identity the field exists to create, while looking
completely plausible.

Admitted: `ablation_split_search.json` (per-query `ids` + `k0`), `colchicine_surfaced_137.json`
(`page_1 + page_2`), `colchicine_pubmed_523.json` (`pmids`).

Matching required BOTH a length match against the record's own count AND ≥80% token
agreement between the recovery source's query and the record's `query_as_executed`. Count
equality alone is a coincidence detector: three ClinicalTrials.gov queries in this corpus
return 57 records for three different drugs.

## WHAT WAS NOT WRITTEN, AND STAYS IN THE DENOMINATOR

    entries written 38 + refused-because-staged 2 == candidates 40

`ssot/azilsartan-chlorthalidone-vs-olmesartan-hctz/…json` is held in the index by another
lane. Writing to it would have put an unstaged edit of mine underneath their staged content,
where their next `git add` would sweep it in. The backfill REFUSES such a path by name. Its
two entries are therefore honestly `FIELD_ABSENT`, and `scripts/check_search_ids.py` REFUSES
on them — visibly, in the count, rather than by shrinking the denominator.

## A FIELD-NAME ASSUMPTION, CAUGHT ON THE FIRST PASS

The first classifier keyed on `records_returned` and filed `arni-hfref`'s two searches as
never executed. They ran — 331 and 92 records — but that object spells the count `hit_count`
/ `records_retrieved`. Two unrecoverable records had been converted into two that needed no
recovery. The count is now read through every spelling the corpus actually uses, measured
rather than assumed.

## TWO THINGS THE FIELD MEASURED IMMEDIATELY

Live run, `python scripts/search_topic.py ser109-cdi`, 16.2 s:

    PubMed        77 returned,   1 unique
    Europe PMC   548 returned, 472 unique
    CT.gov         4 returned,   4 unique
    union        553

1. **A claim I had written into the code was false, and the first run said so.** I had
   recorded that a pair of sources in different id namespaces can only ever intersect in
   zero. PubMed and Europe PMC share 76. Europe PMC's bare-numeric accessions ARE MEDLINE
   records, so `europepmc` CONTAINS `pmid`. The rule is about containment, not difference,
   and is corrected in `search_topic.py`. PubMed's unique yield of 1 against Europe PMC is a
   real finding and would have been discarded as an artefact under the wrong rule.

2. **Topic 2 for the ClinicalTrials.gov arm question.** On dapivirine the intervention arm
   was a strict subset of the free-text arm and contributed nothing unique. On ser109-cdi
   the two arms are identical: 4 each, 0 unique either way. The stated condition for
   retiring the arm is `only_intervention == 0` on three or more topics of different drug
   classes. This is the second. The arm stays.

## PLANT EVIDENCE

`python scripts/check_search_ids.py --plant` — every limb planted in a REAL file in this
repo, watched to REFUSE, restored, restoration proved byte-identical by sha256, corpus
returned to its pinned baseline. SELFTEST PASSED.

    FIELD_ABSENT · NULL_WITHOUT_REASON · EMPTY_WITH_A_REASON
    COUNT_MISMATCH · DUPLICATE · NORMALISED_DESYNC

**AND THE PLANT CAUGHT A REAL DEFECT IN MY OWN WRITER.** The byte-identity limb failed: the
backfill was writing CRLF into LF files — the whole-file-rewrite class that `.gitattributes`
was added to remove yesterday, where five of seven merge conflicts became total and "take
ours" would have silently deleted another lane's work. The first fix (force LF) was the same
defect mirrored: five of these seventeen objects are CRLF in HEAD already. The rule that
adds nothing to any diff is to write back whatever the file already uses. Verified: **zero
of the seventeen changed line-ending style.**

Nothing else in this chain would have seen it. The gate scan passes either way, `git diff`
looked clean because `.gitattributes` normalises on the index side, and the corrupted bytes
were only in the working tree.
