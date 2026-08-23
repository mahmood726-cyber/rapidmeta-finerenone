"""Does the certainty resolver survive every object shape the corpus actually holds?

The cold review was asked for this and ran out of turn twice, so it is done here instead
and the result is reported as mine, not as a review's.
"""
import glob
import io
import json
import os
import sys
import traceback

sys.path.insert(0, "ssot")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import grade_authority as ga  # noqa: E402

shapes = {}
fails = []
n_obj = n_out = 0
for p in sorted(glob.glob("ssot/*/*.json")):
    t = os.path.basename(os.path.dirname(p))
    if os.path.basename(p) != t + ".json":
        continue
    try:
        o = json.load(io.open(p, encoding="utf-8"))
    except ValueError:
        continue
    n_obj += 1
    # characterise the shape
    has_grade = "grade" in o
    res = (o.get("results") or {}).get("by_outcome")
    shape = ("grade" if has_grade else "no-grade",
             "results" if isinstance(res, dict) else "no-results",
             o.get("state") or "live")
    shapes[shape] = shapes.get(shape, 0) + 1
    for oid, b in (res or {}).items():
        n_out += 1
        try:
            r = ga.resolve(o, oid)
            assert r["state"] in ("RATED", "NOT_ASSESSED", "WITHDRAWN_POOL",
                                 "DISAGREEMENT"), r["state"]
            assert isinstance(r["cell"], str) and r["cell"], repr(r["cell"])
        except Exception:
            fails.append((t, oid, traceback.format_exc().strip().split("\n")[-1]))

print("objects walked        :", n_obj)
print("outcomes resolved     :", n_out)
print("distinct object shapes:", len(shapes))
for s, n in sorted(shapes.items(), key=lambda x: -x[1]):
    print("   %-34s %3d" % (" / ".join(str(x) for x in s), n))
print("")
print("resolver failures     :", len(fails))
for f in fails[:10]:
    print("   ", f)

# The awkward synthetic shapes, built here rather than hoped for in the corpus.
EDGE = {
    "no results key at all": {},
    "results present, by_outcome missing": {"results": {}},
    "outcome is not a dict": {"results": {"by_outcome": {"x": "nonsense"}}},
    "pooled missing": {"results": {"by_outcome": {"x": {}}}},
    "pooled is not a dict": {"results": {"by_outcome": {"x": {"pooled": 7}}}},
    "grade is not a dict": {"results": {"by_outcome": {"x": {"pooled": {"point": 1},
                                                            "grade": "high"}}}},
    "certainty is a number": {"results": {"by_outcome": {"x": {"pooled": {"point": 1},
                                                               "grade": {"certainty": 3}}}}},
    "grade.by_outcome is a list": {"results": {"by_outcome": {"x": {"pooled": {"point": 1}}}},
                                   "grade": {"by_outcome": []}},
    "both locations, DIFFERENT levels": {
        "results": {"by_outcome": {"x": {"pooled": {"point": 1},
                                         "grade": {"certainty": "high"}}}},
        "grade": {"by_outcome": {"x": {"certainty": "very low"}}}},
    "hyphenated level": {"results": {"by_outcome": {"x": {"pooled": {"point": 1},
                                                          "grade": {"certainty": "very-low"}}}}},
}
print("")
print("SYNTHETIC EDGE SHAPES")
for label, obj in EDGE.items():
    try:
        r = ga.resolve(obj, "x")
        print("   %-38s -> %-16s %r" % (label, r["state"], r["cell"]))
    except Exception as exc:
        print("   %-38s -> RAISED %s: %s" % (label, type(exc).__name__, exc))
