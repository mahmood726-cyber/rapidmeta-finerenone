# -*- coding: utf-8 -*-
import io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
from gate_label_vs_reason import check

scan = json.load(io.open("scan_result.json", encoding="utf-8"))
J = json.load(io.open("judgements.json", encoding="utf-8"))

rowtext, pairs = {}, set()
for t in scan:
    for b in t["arms"]["AuB"]["verified_bases"]:
        rowtext[(t["app_id"], b["cd_base"])] = (b["title"] or "") + " " + (b["objectives_verbatim"] or "")
        pairs.add((t["app_id"], b["cd_base"]))

judged = {(j["app_id"], j["cd_base"]) for j in J}
missing = pairs - judged
extra = judged - pairs
if missing or extra:
    print("REFUSING: judgement set does not cover the verified set exactly.")
    for m in sorted(missing): print("   unjudged verified pair: %s / %s" % m)
    for m in sorted(extra):   print("   judgement with no verified pair: %s / %s" % m)
    sys.exit(1)
print("coverage: %d verified pairs, %d judgements, exact match" % (len(pairs), len(J)))

ref = check(J, rowtext)
print("")
if ref:
    print("=== GATE REFUSED %d JUDGEMENT(S) -- no count printed ===" % len(ref))
    for r in ref: print(r); print("")
    sys.exit(1)
print("=== GATE: %d/%d judgements pass. Every label is supported by a span quoted from the "
      "row's own title+objectives. ===" % (len(J), len(J)))

from collections import Counter, defaultdict
lab = {(j["app_id"], j["cd_base"]): j["label"] for j in J}
print("")
for k, v in Counter(j["label"] for j in J).most_common():
    print("   %-22s %d" % (k, v))

# topics carrying >=1 COUNTERPART, per arm, counting only judged-true pairs
print("")
print("=== candidates -> verified -> judged, per arm ===")
res = {}
for arm in ("A_drug", "B_class", "AuB"):
    cd = vf = 0
    tj, tv = set(), set()
    nc = und = 0
    for t in scan:
        a = t["arms"][arm]
        cd += a["candidates"]; vf += a["verified"]
        if a["verified"]: tv.add(t["app_id"])
        for b in a["verified_bases"]:
            L = lab[(t["app_id"], b["cd_base"])]
            if L == "COUNTERPART":
                tj.add(t["app_id"])
            elif L == "NOT_COUNTERPART":
                nc += 1
            else:
                und += 1
    res[arm] = (cd, vf, len(tv), len(tj), nc, und)
    print("   %-8s candidates %3d -> verified %3d -> judged COUNTERPART on %2d/20 topics "
          "(refuted pairs %d, undecidable %d)" % (arm, cd, vf, len(tj), nc, und))
print("")
print("=== THE MEASUREMENT ===")
print("   original arm  (drug-keyed) : %d / 20 topics with a judged counterpart" % res["A_drug"][3])
print("   re-keyed arm  (drug+class) : %d / 20 topics with a judged counterpart" % res["AuB"][3])
print("   class-only arm (replace)   : %d / 20" % res["B_class"][3])
print("   DIFFERENCE, original -> re-keyed: %+d topics" % (res["AuB"][3] - res["A_drug"][3]))
print("")
print("   The absolute counts are NOT quotable: shortlist noise and the frame's 80.3% recall")
print("   contaminate both arms equally, so the DIFFERENCE is the measurement.")
json.dump({k: {"candidates": v[0], "verified": v[1], "topics_verified": v[2],
               "topics_judged_counterpart": v[3], "pairs_refuted": v[4], "pairs_undecidable": v[5]}
           for k, v in res.items()}, io.open("measurement.json", "w", encoding="utf-8"), indent=1)
