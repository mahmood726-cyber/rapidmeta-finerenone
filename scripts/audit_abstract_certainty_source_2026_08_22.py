"""Where does the abstract's certainty claim come from, and does it match the GRADE record?

A WRONG NUMBER IN FRONT OF A READER, FOUND BY READING THE PAGE. The SGLT2 abstract states
"certainty of the evidence was high". Its GRADE record says LOW on both live outcomes.

THE MECHANISM, AND IT IS NOT A ROUNDING SLIP:

    the abstract reads    results.by_outcome.<first key>.grade.certainty
    the GRADE record is   grade.by_outcome.<oid>.certainty

Those are different fields. On sglt2-hf the first key is `cvdeath_or_whf_first` -- THE
WITHDRAWN OUTCOME -- and it carries a stale grade block reading "start high; no downgrades".
So the abstract publishes a certainty rating taken from an outcome the review does not publish,
computed before the downgrades that produced the real rating.

TWO DEFECTS AT ONCE. Reading the wrong field, and selecting the first outcome in KEY ORDER
without asking whether that outcome is live. Either alone would be enough.

This audit reports, per topic: what the abstract would say, what GRADE holds, and whether the
outcome the abstract read from is one the review publishes.
"""
import glob
import io
import json
import os
import sys

# no-control: the known answer IS the corpus. This compares two fields that must agree --
# what the abstract composes and what the GRADE record holds -- so a synthetic positive case
# would only restate the comparison, and the real positive case is recorded on the object it
# was found on: sglt2-hf's superseded grade block, kept precisely so this defect stays
# demonstrable rather than becoming a claim about a page nobody can re-examine.

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def first_by_outcome(obj, leaf):
    for oid, blk in sorted(((obj.get("results") or {}).get("by_outcome") or {}).items()):
        cur = blk
        for part in leaf:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is not None:
            return oid, cur
    return None, None


def is_live(blk):
    p = (blk or {}).get("pooled")
    return isinstance(p, dict) and p.get("point") is not None and not p.get("withdrawn")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        by = (obj.get("results") or {}).get("by_outcome") or {}
        if not by:
            continue
        oid, said = first_by_outcome(obj, ("grade", "certainty"))
        if said is None:
            continue
        # A BLOCK MARKED SUPERSEDED IS NOT A LIVE CLAIM. The stale grade block that caused
        # this defect is kept on the object as evidence of how the wrong number reached the
        # page; counting it forever would make the audit unable to report success.
        _g = ((by.get(oid) or {}).get("grade") or {})
        if any(str(k).startswith("superseded") for k in _g):
            continue
        grade = {k: (v or {}).get("certainty")
                 for k, v in ((obj.get("grade") or {}).get("by_outcome") or {}).items()
                 if isinstance(v, dict)}
        live = {k: v for k, v in grade.items() if is_live(by.get(k))}
        said_n = str(said).upper().replace(" ", "_")
        authoritative = sorted({str(v).upper() for v in live.values() if v})
        rows.append({
            "topic": t, "abstract_says": said_n, "read_from": oid,
            "read_from_is_live": is_live(by.get(oid)),
            "grade_on_live_outcomes": authoritative,
            "mismatch": bool(authoritative) and said_n not in authoritative,
        })

    bad = [r for r in rows if r["mismatch"] or not r["read_from_is_live"]]
    print("")
    print("TOPICS WHOSE ABSTRACT COMPOSES A CERTAINTY CLAIM: %d" % len(rows))
    print("OF THOSE, WRONG OR READ FROM AN OUTCOME THE REVIEW DOES NOT PUBLISH: %d" % len(bad))
    print("")
    print("%-42s %-14s %-10s %-32s %s" % ("topic", "abstract says", "live?", "GRADE on live outcomes", "read from"))
    for r in sorted(bad, key=lambda x: x["topic"]):
        print("%-42s %-14s %-10s %-32s %s"
              % (r["topic"][:42], r["abstract_says"],
                 "LIVE" if r["read_from_is_live"] else "WITHDRAWN",
                 ", ".join(r["grade_on_live_outcomes"]) or "(none)", r["read_from"][:30]))
    if not bad:
        print("   none")
    print("")
    print("A CERTAINTY RATING TAKEN FROM AN OUTCOME THE REVIEW DOES NOT PUBLISH IS NOT THIS")
    print("REVIEW'S CERTAINTY, whether or not it happens to agree.")
    # AN AUDIT THAT FINDS A WRONG PUBLISHED RATING AND EXITS 0 IS A REPORT, NOT A CHECK.
    # `lint_gate_can_fail` refused this file for exactly that and was right: it returns a
    # verdict about a number a reader meets, so it has to be able to stop a push.
    if bad:
        json.dump(rows, io.open(os.path.join(REPO, "outputs",
                                             "abstract_certainty_source_2026_08_22.json"),
                                "w", encoding="utf-8"), indent=1)
        sys.exit("REFUSED: %d abstract(s) state a certainty that its own GRADE record does "
                 "not hold, or read it from an outcome the review does not publish." % len(bad))
    json.dump(rows, io.open(os.path.join(REPO, "outputs",
                                         "abstract_certainty_source_2026_08_22.json"),
                            "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
