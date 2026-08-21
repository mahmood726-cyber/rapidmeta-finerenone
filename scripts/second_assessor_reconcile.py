"""Reconcile a blind second assessment against the first, PER DOMAIN.

WHY PER DOMAIN AND NOT A BARE RATE. Three topics in, the disagreements concentrated almost
entirely on ONE domain while the other four agreed everywhere. A bare agreement rate hides that
completely: 25% disagreement reads as noise, and "they diverge on D1 and converge on D2 through
D5" is a measurement. If the profile holds across the queue it says something publishable --
TWO INDEPENDENT MODEL FAMILIES GIVEN THE SAME REGISTRATION FACTS CONVERGE ON FOUR OF FIVE ROB 2
DOMAINS AND DIVERGE ON THE ONE WHERE THE GUIDANCE IS EXPLICIT AND THE FIRST ASSESSOR WAS WRONG.

DISAGREEMENT IS REPORTED, NEVER AGREEMENT. Two assessors given the same facts agreeing
authenticates nothing; the whole value of the second is in what it does not confirm.

AND THE SECOND ASSESSOR IS NOT AN APPEAL COURT. Three topics have now gone against the first
assessor on D1 and the RoB 2 guidance backed the second. The pressure from there is to defer on
everything, which would turn an independent assessment into a review and reproduce the
inheritance problem with the sign flipped. This file records a disagreement; it does not resolve
one. Where the first assessment is believed right, that belief is written down WITH ITS REASON
in the object, next to the disagreement, and both stand.
"""
import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMS = ["D1", "D2", "D3", "D4", "D5", "OVERALL"]
LINE = re.compile(r"^(\S+)\s+D1=(\S+)\s+D2=(\S+)\s+D3=(\S+)\s+D4=(\S+)\s+D5=(\S+)\s+"
                  r"OVERALL=(\S+)\s*$")
KEY = {"D1": "D1_randomisation_process", "D2": "D2_deviations_from_intended_intervention",
       "D3": "D3_missing_outcome_data", "D4": "D4_measurement_of_the_outcome",
       "D5": "D5_selection_of_the_reported_result"}


def norm(v):
    v = str(v).strip().upper().replace(" ", "_")
    return {"SOMECONCERNS": "SOME_CONCERNS", "NOINFORMATION": "NO_INFORMATION"}.get(v, v)


def first_assessment(topic):
    path = os.path.join(REPO, "ssot", topic, topic + ".json")
    obj = json.load(io.open(path, encoding="utf-8"))
    by = ((obj.get("risk_of_bias") or {}).get("by_outcome") or {})
    out = {}
    for oid, per in by.items():
        if not isinstance(per, dict):
            continue
        for rid, j in per.items():
            if not isinstance(j, dict):
                continue
            nct = (j.get("nct") or rid).split("::")[0]
            d = j.get("domains") or {}
            row = {}
            for short, full in KEY.items():
                dv = d.get(full) or d.get(full.split("_")[0])
                if isinstance(dv, dict):
                    row[short] = norm(dv.get("judgement"))
            row["OVERALL"] = norm(j.get("overall") or j.get("rating"))
            out["%s__%s" % (nct, oid)] = row
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sa = sys.argv[1] if len(sys.argv) > 1 else None
    if not sa or not os.path.isdir(sa):
        sys.exit("usage: second_assessor_reconcile.py <dir of *.reply.txt>")

    grand = {d: [0, 0] for d in DOMS}          # [disagree, compared]
    per_topic = []
    for f in sorted(glob.glob(os.path.join(sa, "*.reply.txt"))):
        topic = os.path.basename(f)[:-len(".reply.txt")]
        mine = first_assessment(topic)
        theirs = {}
        for line in io.open(f, encoding="utf-8", errors="replace"):
            m = LINE.match(line.strip())
            if m:
                theirs[m.group(1)] = dict(zip(DOMS, [norm(x) for x in m.groups()[1:]]))
        if not theirs:
            print("%-46s NO PARSEABLE REPLY -- reported, not counted" % topic[:46])
            continue
        dis = cmp = 0
        bydom = {d: [0, 0] for d in DOMS}
        missing = [k for k in theirs if k not in mine]
        for rid, row in sorted(theirs.items()):
            if rid not in mine:
                continue
            for d in DOMS:
                a, b = mine[rid].get(d), row.get(d)
                if not a or not b:
                    continue
                cmp += 1
                bydom[d][1] += 1
                grand[d][1] += 1
                if a != b:
                    dis += 1
                    bydom[d][0] += 1
                    grand[d][0] += 1
        per_topic.append((topic, dis, cmp, bydom, missing))

    print("")
    print("%-44s %-14s %s" % ("topic", "disagreement", "which domains"))
    for topic, dis, cmp, bydom, missing in per_topic:
        where = ", ".join("%s %d/%d" % (d, bydom[d][0], bydom[d][1])
                          for d in DOMS if bydom[d][0])
        print("%-44s %2d of %-3d %5.1f%%  %s"
              % (topic[:44], dis, cmp, (100.0 * dis / cmp) if cmp else 0.0,
                 where or "none -- every domain agrees"))
        if missing:
            print("     %d reply row(s) matched no first-assessment result and were NOT "
                  "counted: %s" % (len(missing), ", ".join(sorted(missing)[:3])))

    tot_d = sum(v[0] for v in grand.values())
    tot_c = sum(v[1] for v in grand.values())
    print("")
    print("PER-DOMAIN PROFILE across %d topic(s), %d judgement comparisons"
          % (len(per_topic), tot_c))
    for d in DOMS:
        dd, cc = grand[d]
        print("   %-8s %3d of %3d disagree   %5.1f%%" % (d, dd, cc,
                                                         (100.0 * dd / cc) if cc else 0.0))
    print("")
    print("   OVERALL DISAGREEMENT %d of %d -- %.1f%%"
          % (tot_d, tot_c, (100.0 * tot_d / tot_c) if tot_c else 0.0))
    print("")
    print("REPORTED AS DISAGREEMENT, NOT AGREEMENT. Two assessors given the same facts")
    print("agreeing authenticates nothing. And a disagreement here is not a correction: where")
    print("the first assessment is believed right, that is written down with its reason and")
    print("both stand.")


if __name__ == "__main__":
    main()
