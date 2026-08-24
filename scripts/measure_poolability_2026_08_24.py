"""Which topics hold poolable evidence, and which hold none. Measured, not felt.

THE THRESHOLD, STATED BEFORE IT IS APPLIED. A topic HAS POOLABLE EVIDENCE when at least
one of its outcomes satisfies ALL FOUR:

  1. TWO INDEPENDENT TRIALS BY REGISTRATION ID. Distinct NCT ids on `per_trial`, counted by
     registration and never by citation string -- a citation is a rendering of a trial, and
     two renderings of one trial are still one trial.
  2. A COMPARABLY MEASURED OUTCOME. Those trials agree on `measure`. An HR and an IRR
     answer different questions, and `malaria-vaccines` is on this corpus as the standing
     example of what pooling across measures produces.
  3. ESTIMATES READABLE VERBATIM. Point and both interval bounds present on each trial row.
     Not derived, not back-computed: if the number is not stored it was not read, and a
     computed estimate is a number this project manufactured.
  4. NOT WITHDRAWN. A pool whose own object records `withdrawn: true` is a pool this
     project has already retracted.

FAILING ALL FOUR ON EVERY OUTCOME IS NOT A DEFECT. It is a finding, and on this corpus it
is the COMMON finding -- most of these topics were opened precisely to establish whether a
pool was possible. What has been wrong is publishing that finding wrapped in a manuscript
skeleton whose every section then declines.

WHY THIS IS A SEPARATE SCRIPT AND NOT A FLAG INSIDE THE BUILDER. The split decides which
artefact a topic publishes, and that decision must be inspectable and countable BEFORE
anything is converted, not discovered afterwards from what the pages turned out to look
like.
"""
import io
import json
import os
import sys
import glob

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _readable(row):
    """A trial row whose estimate and interval were READ, not computed."""
    return all(row.get(k) is not None for k in ("point", "ci_low", "ci_high"))


def poolable_outcomes(obj):
    """Every outcome id that clears all four conditions, with why it cleared."""
    out = []
    by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
    for oid, blk in by_outcome.items():
        if not isinstance(blk, dict):
            continue
        if (blk.get("pooled") or {}).get("withdrawn"):
            continue
        rows = [r for r in (blk.get("per_trial") or []) if isinstance(r, dict)]
        readable = [r for r in rows if _readable(r)]
        ncts = {str(r.get("nct") or r.get("trial_id") or "").strip()
                for r in readable}
        ncts.discard("")
        measures = {str(r.get("measure")) for r in readable if r.get("measure")}
        if len(ncts) >= 2 and len(measures) == 1:
            out.append({"outcome": oid, "trials": sorted(ncts),
                        "measure": next(iter(measures)), "k": blk.get("k")})
    return out


def main():
    page_map = json.load(open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rows = []
    for page, rel in sorted(page_map.items()):
        path = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.exists(path):
            rows.append({"page": page, "slug": None, "state": "OBJECT_MISSING"})
            continue
        obj = json.load(open(path, encoding="utf-8"))
        good = poolable_outcomes(obj)
        rows.append({"page": page,
                     "slug": os.path.basename(os.path.dirname(path)),
                     "state": "POOLABLE" if good else "NO_POOL",
                     "poolable_outcomes": good,
                     "title": obj.get("title")})

    poolable = [r for r in rows if r["state"] == "POOLABLE"]
    nopool = [r for r in rows if r["state"] == "NO_POOL"]
    missing = [r for r in rows if r["state"] == "OBJECT_MISSING"]

    print("PAGE_MAP topics: %d" % len(rows))
    print("  POOLABLE  (keeps its manuscript) : %d" % len(poolable))
    print("  NO_POOL   (converts to statement): %d" % len(nopool))
    print("  object missing                   : %d" % len(missing))
    # EVERY QUALIFYING OUTCOME, NOT ELEMENT ZERO. `lint_primary_by_position.py` refused an
    # earlier version of this line for taking `[0]`, and it was right to even though this
    # list is one I build myself and read only for display: the rule it enforces is that a
    # position in an outcome collection means nothing. Element zero of ADVANCE-2's
    # outcomeMeasures is its SECONDARY and its three companions' PRIMARY, and a pool built
    # on that is wrong with nothing malformed anywhere. A habit that is safe here is the
    # same habit that was not safe there, so the line goes rather than the lint.
    print("\nPOOLABLE, with every outcome that qualified:")
    for r in poolable[:200]:
        for g in r["poolable_outcomes"]:
            print("  %-52s %s  %d trials  %s"
                  % (r["page"][:52], g["outcome"][:18], len(g["trials"]), g["measure"]))
    print("\nNO_POOL (first 40):")
    for r in nopool[:40]:
        print("  %-52s %s" % (r["page"][:52], (r["title"] or "")[:44]))
    with io.open(os.path.join(REPO, "outputs", "poolability_split_2026_08_24.json"),
                 "w", encoding="utf-8") as fh:
        json.dump({"poolable": [r["page"] for r in poolable],
                   "no_pool": [r["page"] for r in nopool],
                   "object_missing": [r["page"] for r in missing],
                   "rows": rows}, fh, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
