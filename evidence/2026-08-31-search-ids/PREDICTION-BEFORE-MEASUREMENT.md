# PREDICTION, WRITTEN BEFORE THE BACKFILL WAS MEASURED

Recorded 2026-08-31, before running any recoverability scan.

## The population, which is already counted and is not the prediction

40 search-record entries, at `ssot/<topic>/<topic>.json -> search.databases[]`, across 18
objects. NOT ONE carries an identifier list. That count is a measurement already made and is
stated here so the prediction below has a fixed denominator.

## THE PREDICTION

    backfillable from an identifier set already on disk    6 / 40   (15%)
    unrecoverable without re-running the query           34 / 40   (85%)

## THE DIRECTION I EXPECT TO MISS: OPTIMISTIC.

Thirteen consecutive predictions in this project missed optimistic. I have seen two
evidence files that carry identifier lists (`ablation_split_search.json` has per-query
`ids`; `colchicine-cvd-coronary` names an `identifiers_recorded_at` path) and the
availability heuristic will pull the estimate up from those two toward the rest of the
`evidence/2026-08-19-batch1/` directory, which I have NOT checked. The specific way this
goes wrong is that a referenced path is not the same thing as a present file, and a file
that carries ids for ONE query is not the same as one that carries them per-record.

So: if I am wrong, I expect the true figure to be BELOW 6, not above it.

## WHAT WOULD MAKE THE PREDICTION MEANINGLESS

A backfill that re-runs the query today. That is not a backfill -- registry contents change,
so a set retrieved on 2026-08-31 is not the set the record's 2026-08-19 count describes.
Any entry filled that way is a NEW record, not a recovered one, and is counted separately.
