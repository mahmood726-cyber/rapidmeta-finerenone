# -*- coding: utf-8 -*-
"""Write the search that RAN, in the schema this repository already has.

WHY THIS EXISTS. 124 delivered pages carry an empty Search tab, and the reason is not that
the tab is broken: NO EXECUTED SEARCH WAS EVER RECORDED for them. Eight records exist under
evidence/, all hand-written, all for topics built by hand. The autodiscovery path -- which
produced the bulk of the corpus -- has never written one.

    A SEARCH NOBODY RECORDED IS NOT A SEARCH WITH A MISSING NOTE. From outside it is
    indistinguishable from a search that never happened, and the tab that renders it is
    correct to be empty.

NO NEW SPELLING. The schema is the one already in evidence/: `topic`, `executed_utc`,
`state`, `database`, `tool`, `query_as_executed`, `pages`, `records_returned_total`,
`total_reported`, plus an identifier list. It is chosen so that the EXISTING checker,
scripts/verify_search_record_reconciles.py, can read these records without being taught
anything -- a second vocabulary for one concept is how a concept ends up with two
half-maintained checkers and no working one.

WHAT `nct_ids` HOLDS, AND WHY IT IS THE POOL AND NOT THE INGESTED SET. It holds every
registration the search returned -- the ELIGIBLE pool, before the ingestion bound. The bound
is an ingestion decision, recorded beside it in `bound`, not a property of the search.
Listing only the ingested head would make `records_returned_total` a reach figure and would
make the record reconcile against a number that was never the answer, which is precisely the
defect this lane exists to remove.

    THE CONSEQUENCE IS DELIBERATE: a topic whose bound bit now SERVES the pool it cut from,
    so the discarded candidates are nameable from the record rather than gone.

WHAT THIS RECORD DOES NOT ESTABLISH. Not that the query was well aimed, not that the pool is
the right pool, and nothing at all about screening: no candidate here has been dispositioned.
`screening` is written as NOT_RUN rather than omitted, because an absent field reads as
"nothing to report" and the true state is "nobody has looked yet".
"""
from __future__ import annotations

import io
import json
import time
from pathlib import Path

# The gate order as `find_ncts` actually applies it. Written out so the record says what
# ran rather than what a docstring elsewhere claims runs.
GATES_IN_ORDER = ("trial_identity(_studies_subject: experimental-arm, non-combination)",
                  "condition(_match_blob token_subset + COND_SYNS)",
                  "study_type(not explicitly non-interventional)")

# The ranking `find_ncts` applies before the bound. TOTAL, not merely stable: the NCT id
# breaks every remaining tie, so the head the bound keeps is determined by the data and not
# by dictionary iteration order.
SORT_ORDER = "-pivotal_score, then -enrollment, then nct_id ascending (total ordering)"


SNAPSHOT_TABLES = ("interventions.txt", "conditions.txt", "studies.txt",
                   "design_groups.txt", "design_group_interventions.txt")


def snapshot_identity(aact_dir):
    """Name a snapshot by what is IN it, never by where it is mounted.

    NO DRIVE LETTERS IN A COMMITTED RECORD. `F:/AACT-storage/AACT/2026-08-30` identifies a
    directory on one machine and nothing at all to anyone else, and the drive it names is
    the one this project already treats as unreliable. The snapshot is identified by its
    directory NAME plus the size and mtime of every table read, which is what actually makes
    a reading re-takeable: two people with the same fingerprints are reading the same bytes,
    wherever either has mounted them.
    """
    from pathlib import Path as _P
    import time as _t
    d = _P(aact_dir)
    tables = {}
    for t in SNAPSHOT_TABLES:
        f = d / t
        if f.exists():
            st = f.stat()
            tables[t] = {"bytes": st.st_size,
                         "mtime_utc": _t.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                  _t.gmtime(st.st_mtime))}
        else:
            tables[t] = {"state": "NOT_READ"}
    return {"snapshot": d.name, "tables": tables}


def build(topic, drug_patterns, condition_patterns, ledger, snapshot,
          eligible_ncts, executed_utc=None):
    """One executed-search record.

    `ledger` is the dict find_ncts filled. `snapshot` is the mapping returned by
    `snapshot_identity` -- a name and table fingerprints, not a path.
    """
    eligible = list(eligible_ncts)
    stamp = executed_utc or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    bit = bool(ledger.get("discarded_by_cap"))
    return {
        "topic": topic,
        "executed_utc": stamp,
        "state": "EXECUTED, WHOLE SNAPSHOT SCANNED, NO CURSOR TO EXHAUST",
        "database": "AACT %s (local snapshot, full-table scan)"
                    % (snapshot.get("snapshot") if isinstance(snapshot, dict)
                       else snapshot),
        "database_fingerprint": (snapshot.get("tables")
                                 if isinstance(snapshot, dict) else None),
        "tool": "scripts/add_topic_autodiscover.py::find_ncts",
        # THE QUERY AS SENT. There is no query string to quote -- this is a scan over local
        # tables -- so what is recorded is the predicate that actually ran, in the order it
        # ran, naming the synonym tables it expanded through.
        "query_as_executed": (
            "scan interventions.txt x conditions.txt x studies.txt; "
            "drug_patterns=%r expanded through DRUG_SYNS; "
            "condition_patterns=%r expanded through COND_SYNS; "
            "gates applied in order: %s"
            % (list(drug_patterns), list(condition_patterns), " -> ".join(GATES_IN_ORDER))),
        # THE PATTERNS AS FIELDS, not only inside the query prose. A later reader that
        # needs the predicate must not have to parse it back out of a sentence -- that
        # is how a record ends up being read with a regex and an eval.
        "drug_patterns": list(drug_patterns),
        "condition_patterns": list(condition_patterns),
        "sort_order": SORT_ORDER,
        # A SNAPSHOT SCAN HAS NO PAGINATION, and that is stated rather than left for a
        # reader to infer from a missing field. Class 20 is about a cursor abandoned early;
        # here every row of every table was read, so there is no cursor and no shortfall.
        "pages": [{"page": 1, "returned": len(eligible),
                   "total_reported": len(eligible),
                   "next_page_token": "NONE -- full-table scan, not a paged API"}],
        "records_returned_total": len(eligible),
        "total_reported": len(eligible),
        "distinct": len(set(eligible)),
        "duplicates_across_pages": len(eligible) - len(set(eligible)),
        "nct_ids": eligible,
        # THE FUNNEL, with each stage's input and a named reason for the difference.
        "enumeration": {
            "retrieved": ledger.get("retrieved"),
            "identity_rejected": ledger.get("identity_rejected"),
            "identity_reasons": ledger.get("identity_reasons"),
            "dropped_condition": ledger.get("dropped_condition"),
            "dropped_study_type": ledger.get("dropped_study_type"),
            "eligible": ledger.get("eligible"),
        },
        # THE BOUND, SERVED. A cap is an operational choice only while the number it
        # discarded is on the record; below it is a silent loss.
        "bound": {
            "applied": ledger.get("cap_applied"),
            "source": ledger.get("cap_source"),
            "bit": bit,
            "ingested": ledger.get("ingested"),
            "discarded": ledger.get("discarded_by_cap"),
            "discarded_ncts": ledger.get("discarded_ncts", []),
            "note": ("the bound cut the ranked pool; the discarded ids are listed here so "
                     "the pool remains recoverable from this record"
                     if bit else
                     "the bound did not bite: every eligible candidate was ingested"),
        },
        "screening": {
            "state": "NOT_RUN",
            "reason": ("no candidate in this record has been dispositioned. This is a state, "
                       "not a silence: zero screened is not zero excluded, and an omitted "
                       "field would read as nothing to report."),
            "included": None,
            "excluded": None,
            "undecidable": None,
        },
    }


def write(out_dir, record):
    """Write one record as evidence/<out_dir>/<TOPIC>.json and return the path."""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / ("%s.json" % record["topic"])
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return p
