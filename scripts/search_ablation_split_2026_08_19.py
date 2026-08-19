"""EXECUTED SEARCH for the three topics `ablation-af-review` was split into.

ONE SEARCH RUN, THREE TOPICS, AND THE QUERIES ARE NOT SHARED. Each topic below carries its own
query string, its own recall target, and its own counts. They are executed in one file because
they run against one registry on one date; nothing is copied between them, and no topic's counts
are derived from another's.

EVERY QUERY IS RECORDED, INCLUDING THE ONES THAT MISS. The historical query for this topic --
cond="atrial fibrillation", intr="catheter ablation OR pulmonary vein isolation OR cryoballoon
ablation", phase=[PHASE3,PHASE4] -- returned 143 records and MISSED TWO OF THE THREE TRIALS
`ablation-af-medical-therapy` includes. It is run here anyway, and its recall is measured rather
than assumed, because a query's failure is a finding about the search.

    THE CAUSE IS THE PHASE FILTER, AND IT IS A FOURTH SHAPE OF A RECALL DEFECT THIS PROJECT
    HAS NOW SEEN FOUR TIMES.
        sglt2-hf     lost DELIVER                to a CONDITION term one word too narrow
        iv-iron-hf   lost AFFIRM-AHF, HEART-FID  to a CONDITION term one word too narrow
        apixaban-vte lost NCT02366871            to phase=[PHASE3,PHASE4] on a PHASE2 trial
        here         lost CABANA and RAFT-AF     to the same filter on trials registered
                                                 `phases: ["NA"]`
    NA IS NOT A PHASE. A design filter that enumerates phases silently excludes every trial
    whose registrant declined to declare one -- and here that is 2 of the 3 pivotal trials,
    including the largest (CABANA, n=2204).

Pagination is checked, not assumed: returned == totalCount and nextPageToken null, per query.
"""
import io
import json
import os
import sys
import urllib.parse
import urllib.request

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X          # noqa: E402

SEARCH_DATE = "2026-08-19"
API = "https://clinicaltrials.gov/api/v2/studies"

# The three topics' included sets, from the decision recorded in
# DECIDED-ablation-af-review-2026-08-19.md. Each trial id was read from the source object's
# inputs.trials, never recalled.
TOPICS = {
    "ablation-af-medical-therapy": {
        "recall_target": ["NCT00643188", "NCT00911508", "NCT01420393"],
        "queries": [
            {"label": "Q1 HISTORICAL, WITH THE PHASE FILTER -- recorded because it MISSES",
             "expr": {"query.cond": "atrial fibrillation",
                      "query.intr": ("catheter ablation OR pulmonary vein isolation OR "
                                     "cryoballoon ablation"),
                      "filter.advanced": ("AREA[StudyType]INTERVENTIONAL AND "
                                          "AREA[Phase](PHASE3 OR PHASE4)")}},
            {"label": "Q2 SAME TERMS, PHASE FILTER DROPPED",
             "expr": {"query.cond": "atrial fibrillation",
                      "query.intr": ("catheter ablation OR pulmonary vein isolation OR "
                                     "cryoballoon ablation"),
                      "filter.advanced": "AREA[StudyType]INTERVENTIONAL"}},
            {"label": "Q3 INTERVENTION WIDENED TO THE STRATEGY WORDS THE REGISTRY USES",
             "expr": {"query.cond": "atrial fibrillation",
                      "query.intr": ("catheter ablation OR pulmonary vein isolation OR "
                                     "cryoballoon ablation OR left atrial ablation OR "
                                     "radiofrequency ablation OR rhythm control"),
                      "filter.advanced": "AREA[StudyType]INTERVENTIONAL"}},
        ],
    },
    "early-rhythm-control-af": {
        "recall_target": ["NCT00643188", "NCT00911508", "NCT01288352", "NCT01420393"],
        "queries": [
            {"label": "Q1 RHYTHM-CONTROL STRATEGY, not a procedure",
             "expr": {"query.cond": "atrial fibrillation",
                      "query.intr": ("rhythm control OR early rhythm control OR rate control "
                                     "OR catheter ablation OR antiarrhythmic"),
                      "filter.advanced": "AREA[StudyType]INTERVENTIONAL"}},
        ],
    },
    "ablation-af-heart-failure": {
        "recall_target": ["NCT00643188", "NCT01420393"],
        "queries": [
            {"label": "Q1 BOTH CONDITIONS REQUIRED -- the population IS the topic",
             "expr": {"query.cond": "atrial fibrillation AND heart failure",
                      "query.intr": ("catheter ablation OR pulmonary vein isolation OR "
                                     "radiofrequency ablation OR rhythm control"),
                      "filter.advanced": "AREA[StudyType]INTERVENTIONAL"}},
            {"label": "Q2 CONDITION TERM WIDENED -- 'heart failure' alone missed nothing here, "
                      "checked rather than assumed",
             "expr": {"query.cond": ("atrial fibrillation AND (heart failure OR ventricular "
                                     "dysfunction OR cardiomyopathy)"),
                      "query.intr": ("catheter ablation OR pulmonary vein isolation OR "
                                     "radiofrequency ablation OR rhythm control"),
                      "filter.advanced": "AREA[StudyType]INTERVENTIONAL"}},
        ],
    },
}


def raw_search(expr, page_size=1000):
    """(state, ids, detail). Paginates, and reads totalCount FROM THE FIRST PAGE ONLY.

    THE FIRST VERSION READ IT FROM THE LAST PAGE AND REPORTED A FALSE MISMATCH.
    `countTotal=true` populates `totalCount` on the FIRST response; later pages return it as
    null. Q3 below spans two pages and the check printed
    `totalCount=None, returned==totalCount: False` on a query that had in fact returned
    everything.

        A PAGINATION GUARD THAT READS ITS EVIDENCE FROM THE WRONG PAGE REPORTS A MISMATCH
        THAT IS AN ARTEFACT OF WHERE IT LOOKED.

    It failed toward ALARM here, which is why it was visible at all -- and the same code is in
    scripts/regate_cascade_2026_08_19.py, where every query happened to fit in one page so the
    last page WAS the first and the defect could not show. A guard that has only ever run on
    single-page inputs has not been tested on the case it exists for.
    """
    ids, token, pages, total = [], None, 0, None
    while True:
        params = dict(expr)
        params["fields"] = "NCTId"
        params["pageSize"] = str(page_size)
        params["countTotal"] = "true"
        if token:
            params["pageToken"] = token
        url = "%s?%s" % (API, urllib.parse.urlencode(params))
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                if resp.status != 200:
                    return X.UNREACHABLE, ids, "HTTP %d on page %d" % (resp.status, pages + 1)
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:                       # noqa: BLE001 - transport, reported
            return X.UNREACHABLE, ids, "%s: %s" % (type(exc).__name__, exc)
        for s in payload.get("studies") or []:
            nct = (((s.get("protocolSection") or {}).get("identificationModule")
                    or {}).get("nctId"))
            if nct:
                ids.append(nct)
        pages += 1
        token = payload.get("nextPageToken")
        if pages == 1:
            total = payload.get("totalCount")
        if not token:
            return (X.OK, ids,
                    "%d ids over %d page(s), totalCount=%s, nextPageToken=null, "
                    "returned==totalCount: %s" % (len(ids), pages, total, len(ids) == total))
        if pages > 30:
            return X.MALFORMED, ids, "pagination did not terminate in 30 pages"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out = {}
    for topic, spec in TOPICS.items():
        target = spec["recall_target"]
        print("=" * 88)
        print("%s   recall target %d: %s" % (topic, len(target), ", ".join(target)))
        recs = []
        for q in spec["queries"]:
            state, ids, detail = raw_search(q["expr"])
            ids = sorted(set(ids))
            found = [t for t in target if t in ids]
            missed = [t for t in target if t not in ids]
            recs.append({"label": q["label"], "expr": q["expr"], "state": state,
                         "detail": detail, "k0": len(ids),
                         "recall": "%d/%d" % (len(found), len(target)),
                         "missed": missed, "ids": ids})
            print("   %s" % q["label"])
            print("      %s" % json.dumps(q["expr"]))
            print("      %s -- %s" % (state, detail))
            print("      k0 = %d   RECALL %d/%d%s"
                  % (len(ids), len(found), len(target),
                     "   MISSED: " + ", ".join(missed) if missed else "   FULL RECALL"))
        out[topic] = {"search_date": SEARCH_DATE, "recall_target": target, "queries": recs}
        full = [r for r in recs if not r["missed"]]
        if not full:
            print("   !! NO QUERY ACHIEVES FULL RECALL. The cascade must not be counted from a "
                  "surfaced\n      set that is known to be missing included trials.")
        else:
            best = min(full, key=lambda r: r["k0"])
            out[topic]["chosen"] = best["label"]
            print("   CHOSEN: %s (k0=%d) -- the SMALLEST surfaced set achieving full recall, "
                  "so the\n      remainder to be screened is not inflated by terms the review "
                  "does not need." % (best["label"], best["k0"]))
        print()

    dest = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_split_search.json")
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
