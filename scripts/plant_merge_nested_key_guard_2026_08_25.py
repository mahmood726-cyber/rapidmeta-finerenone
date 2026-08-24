#!/usr/bin/env python3
"""PLANT THE DEFECT THE MERGE GUARD EXISTS TO CATCH, AND WATCH IT FAIL.

The guard being tested replaces one whose promise was wider than its comparison: it said
"refuses if the object loses any key" and compared `set(obj.keys())`, the top level only,
while the merge rewrote `obj["risk_of_bias"]` wholesale. It passed every run and would
have dropped 18 nested keys across 8 objects.

  A REPLACEMENT GUARD INHERITS NO CREDIT FROM THE ONE IT REPLACES. This runs entirely on
  IN-MEMORY FIXTURES and touches no corpus file, so it cannot be made to pass or fail by
  the state of the tree it is meant to protect -- the control-keyed-to-corpus-state trap
  that has expired six controls in this project.

THE KNOWN POSITIVE IS THE POINT. Test 1 reconstructs the OLD guard and requires it to
MISS the exact loss that was measured in the corpus. A new guard that catches a defect
nobody has watched the old guard miss is a guard with no demonstrated reason to exist.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_rob_grade_into_objects_2026_08_19 import key_paths, nest_merge  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A fixture shaped like the real thing: the seven derived keys, plus the enrichment keys
# that the old merge destroyed. Named after the real ones so a reader can match them up.
FIXTURE = {
    "title": "fixture",
    "risk_of_bias": {
        "tool": "RoB 2", "version": "old", "by_outcome": {"o1": {"NCT1": {"overall": "LOW"}}},
        "SECOND_ASSESSOR_2026_08_21": {"assessor_2": "a second family", "DISAGREEMENT_RATE": "2 of 5"},
        "ONE_ASSESSOR_ONLY": "only one assessor saw this",
        "sources_read": ["a"], "sources_NOT_read": ["b"],
    },
    "protocol": {"prespecified": False},
}
DERIVED = {"tool": "RoB 2", "version": "new", "unit_of_assessment": "a result",
           "by_outcome": {"o1": {"NCT1": {"overall": "SOME_CONCERNS"}}}}

ENRICHMENT = ("risk_of_bias.SECOND_ASSESSOR_2026_08_21", "risk_of_bias.ONE_ASSESSOR_ONLY",
              "risk_of_bias.sources_read", "risk_of_bias.sources_NOT_read")


def old_guard(before_obj, after_obj):
    """The guard as it stood: top-level keys only."""
    return sorted(set(before_obj.keys()) - set(after_obj.keys()))


def new_guard(before_paths, after_obj):
    """The guard as it now stands: every key path, `by_outcome` exempt by name."""
    return sorted(q for q in (before_paths - key_paths(after_obj))
                  if ".by_outcome" not in q and not q.endswith("by_outcome"))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    # ---- TEST 1: the KNOWN POSITIVE. Old behaviour loses the keys; old guard misses it.
    before = json.loads(json.dumps(FIXTURE))
    bpaths = key_paths(before)
    after = json.loads(json.dumps(FIXTURE))
    after["risk_of_bias"] = dict(DERIVED)                 # <- the old REPLACE
    lost_old = old_guard(before, after)
    lost_new = new_guard(bpaths, after)
    missing = [e for e in ENRICHMENT if e not in key_paths(after)]
    ok1 = (len(missing) == 4 and lost_old == [] and len(lost_new) >= 4)
    print("%-5s KNOWN POSITIVE: wholesale replace drops %d enrichment key(s); "
          "OLD guard reports %d (must be 0 -- it MISSES); NEW guard reports %d"
          % ("PASS" if ok1 else "FAIL", len(missing), len(lost_old), len(lost_new)))
    if not ok1:
        fails.append("known positive")

    # ---- TEST 2: the repaired merge keeps them, and the new guard is silent.
    after2 = json.loads(json.dumps(FIXTURE))
    nest_merge(after2.setdefault("risk_of_bias", {}), DERIVED)
    kept = [e for e in ENRICHMENT if e in key_paths(after2)]
    lost2 = new_guard(bpaths, after2)
    ok2 = (len(kept) == 4 and lost2 == [])
    print("%-5s REPAIRED MERGE: keeps %d of 4 enrichment keys; new guard reports %d loss"
          % ("PASS" if ok2 else "FAIL", len(kept), len(lost2)))
    if not ok2:
        fails.append("repaired merge keeps enrichment")

    # ---- TEST 3: the derived values actually update (a merge that changed nothing is
    #      not a fix, it is a no-op wearing one).
    ok3 = (after2["risk_of_bias"]["version"] == "new"
           and after2["risk_of_bias"]["unit_of_assessment"] == "a result"
           and after2["risk_of_bias"]["by_outcome"]["o1"]["NCT1"]["overall"] == "SOME_CONCERNS")
    print("%-5s DERIVED VALUES UPDATE: version->new, unit added, by_outcome replaced"
          % ("PASS" if ok3 else "FAIL"))
    if not ok3:
        fails.append("derived values update")

    # ---- TEST 4: the NEGATIVE control. A guard that fires on everything is not a guard.
    #      An untouched object must report zero loss.
    after3 = json.loads(json.dumps(FIXTURE))
    lost3 = new_guard(bpaths, after3)
    ok4 = (lost3 == [])
    print("%-5s NEGATIVE CONTROL: untouched object reports %d loss (must be 0)"
          % ("PASS" if ok4 else "FAIL", len(lost3)))
    if not ok4:
        fails.append("negative control")

    # ---- TEST 5: by_outcome churn must NOT be reported. Its record keys legitimately
    #      change between runs; a guard that refuses on that can never merge anything.
    after4 = json.loads(json.dumps(FIXTURE))
    nest_merge(after4.setdefault("risk_of_bias", {}),
               {"by_outcome": {"o1": {"NCT_DIFFERENT": {"overall": "HIGH"}}}})
    lost4 = new_guard(bpaths, after4)
    ok5 = (lost4 == [])
    print("%-5s by_outcome EXEMPTION: replacing every record reports %d loss (must be 0)"
          % ("PASS" if ok5 else "FAIL", len(lost4)))
    if not ok5:
        fails.append("by_outcome exemption")

    # ---- TEST 6: a loss ANYWHERE ELSE must still be caught, or the exemption is a hole.
    after5 = json.loads(json.dumps(FIXTURE))
    del after5["protocol"]["prespecified"]
    lost5 = new_guard(bpaths, after5)
    ok6 = ("protocol.prespecified" in lost5)
    print("%-5s EXEMPTION IS NOT A HOLE: deleting protocol.prespecified is caught (%s)"
          % ("PASS" if ok6 else "FAIL", ", ".join(lost5) or "nothing reported"))
    if not ok6:
        fails.append("exemption is not a hole")

    print()
    if fails:
        print("PLANT FAILED: %s" % "; ".join(fails))
        return 1
    print("PLANT PASSED: 6 of 6. The old guard is shown MISSING the real loss, the new "
          "guard catches it, stays silent on an untouched object and on legitimate "
          "by_outcome churn, and still catches a loss outside the exemption.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
