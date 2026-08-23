"""GRADE per POOLED OUTCOME, not per page -- and the two grade locations that disagree.

# no-control: the known answer is the corpus itself. This counts a ratio whose numerator and
# denominator are both read from the same objects, so a synthetic case would only restate the
# arithmetic; the real controls are the two named topics below, whose disagreement was found by
# a person reading pages and is reproduced by this script every run.

P46'S GRADE LIMB ASKED "DOES THIS OBJECT HOLD A GRADE RATING" AND ANSWERED PER PAGE. On
sglt2-hf that answered yes on the strength of a rating attached to an outcome that was never
pooled, so the 28-of-28 possession figure counted a page whose two published estimates carry no
assessment at all. The question a reader's estimate depends on is per POOL.

AND THERE ARE TWO PLACES A RATING CAN LIVE, which is why the surfaces disagreed:

    results.by_outcome.<oid>.grade.certainty     what the Summary of findings table renders
    grade.by_outcome.<oid>.certainty             the structured record, with domains and steps

    sglt2-hf          results.*.grade  rates ONLY the withdrawn outcome, "high"
                      grade.by_outcome rates BOTH pooled outcomes, "LOW"
    sotagliflozin-hf  results.*.grade  rates all three "low"
                      grade.by_outcome is EMPTY

So on one topic the table under-reports and on the other the structured record does. Neither
location is consistently authoritative, and a reader met whichever one the surface they were
looking at happened to read.

THIS COUNTS BOTH, SEPARATELY, AND NAMES THE DISAGREEMENTS. It does not pick a winner: which
location is authoritative is a decision about the evidence, and back-filling either from the
other is exactly the silent synthesis this project refuses.
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_pooled(blk):
    p = (blk or {}).get("pooled")
    return (isinstance(p, dict) and p.get("point") is not None
            and not p.get("withdrawn"))


def norm(v):
    if v is None:
        return None
    t = str(v).strip().upper().replace(" ", "_")
    return t or None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    pools = rated_struct = rated_table = rated_either = 0
    topics = 0
    disagree, unrated_topics, stranded = [], [], []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        res = (obj.get("results") or {}).get("by_outcome") or {}
        gbo = (obj.get("grade") or {}).get("by_outcome") or {}
        mine = [(oid, b) for oid, b in res.items() if is_pooled(b)]
        if not mine:
            continue
        topics += 1
        t_rated = 0
        for oid, blk in mine:
            pools += 1
            struct = norm((gbo.get(oid) or {}).get("certainty")
                          if isinstance(gbo.get(oid), dict) else None)
            table = norm((blk.get("grade") or {}).get("certainty")
                         if isinstance(blk.get("grade"), dict) else None)
            rated_struct += bool(struct)
            rated_table += bool(table)
            if struct or table:
                rated_either += 1
                t_rated += 1
            if struct and table and struct != table:
                disagree.append((t, oid, "values differ", struct, table))
            elif bool(struct) != bool(table):
                disagree.append((t, oid, "one location only", struct, table))
        if t_rated == 0:
            unrated_topics.append((t, len(mine)))
        # the stranded-rating shape, checked per location
        pooled_ids = {oid for oid, _b in mine}
        for oid, blk in res.items():
            if oid in pooled_ids:
                continue
            for loc, val in (("results.*.grade",
                              norm((blk.get("grade") or {}).get("certainty")
                                   if isinstance(blk.get("grade"), dict) else None)),
                             ("grade.by_outcome",
                              norm((gbo.get(oid) or {}).get("certainty")
                                   if isinstance(gbo.get(oid), dict) else None))):
                if not val:
                    continue
                same_loc_pooled = [
                    norm((b.get("grade") or {}).get("certainty")
                         if loc == "results.*.grade" and isinstance(b.get("grade"), dict)
                         else (gbo.get(o) or {}).get("certainty")
                         if loc == "grade.by_outcome" and isinstance(gbo.get(o), dict)
                         else None)
                    for o, b in mine]
                if not any(same_loc_pooled):
                    stranded.append((t, oid, loc, val))

    print("")
    print("GRADE PER POOLED OUTCOME, across %d topic(s) that publish at least one pool"
          % topics)
    print("")
    print("   pooled outcomes                       %4d" % pools)
    print("   rated in grade.by_outcome (structured) %3d   %5.1f%%"
          % (rated_struct, 100.0 * rated_struct / max(1, pools)))
    print("   rated in results.*.grade (the table)   %3d   %5.1f%%"
          % (rated_table, 100.0 * rated_table / max(1, pools)))
    print("   rated in EITHER location               %3d   %5.1f%%"
          % (rated_either, 100.0 * rated_either / max(1, pools)))
    print("")
    print("TOPICS WHOSE PUBLISHED POOLS CARRY NO RATING IN EITHER PLACE: %d"
          % len(unrated_topics))
    for t, n in unrated_topics[:14]:
        print("   %-46s %d pooled outcome(s), 0 rated" % (t[:46], n))
    print("")
    print("POOLS WHERE THE TWO LOCATIONS DISAGREE: %d" % len(disagree))
    for t, oid, kind, a, b in disagree[:16]:
        print("   %-30s %-30s %-18s structured=%-6s table=%s"
              % (t[:30], oid[:30], kind, a, b))
    print("")
    print("A RATING IN ONE LOCATION AND NOT THE OTHER IS NOT A RATING A READER RELIABLY MEETS.")
    print("Which location is authoritative is a decision about the evidence; nothing here")
    print("back-fills one from the other.")
    # A RATING ON AN OUTCOME THAT WAS NOT POOLED, BESIDE POOLED OUTCOMES WITH NONE, IS WRONG
    # WHICHEVER LOCATION IS AUTHORITATIVE. That is the sglt2 shape: the Summary of findings
    # rated only the row marked "not pooled" and both published estimates showed a dash, and
    # the abstract then reported the two estimates and quoted the rating. This does not take a
    # side on which location wins -- that decision is not this script's -- it refuses the one
    # arrangement that is indefensible under either answer.
    if stranded:
        print("")
        print("A RATING ON A NOT-POOLED OUTCOME WHILE THIS TOPIC'S POOLED OUTCOMES CARRY NONE,")
        print("IN THE SAME LOCATION: %d" % len(stranded))
        for t, oid, loc, val in stranded:
            print("   %-40s %-28s %s=%s" % (t[:40], oid[:28], loc, val))
        sys.exit("REFUSED: %d topic(s) rate an outcome they did not pool while the outcomes "
                 "they did pool carry no rating in that same location. A reader meets the "
                 "rating beside the estimates it does not belong to." % len(stranded))
    json.dump({"pools": pools, "rated_structured": rated_struct,
               "rated_table": rated_table, "rated_either": rated_either,
               "disagreements": [list(d) for d in disagree],
               "unrated_topics": [list(u) for u in unrated_topics]},
              io.open(os.path.join(REPO, "outputs", "grade_per_pool_2026_08_23.json"),
                      "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
