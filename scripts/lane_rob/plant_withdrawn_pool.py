# -*- coding: utf-8 -*-
"""Plant a withdrawal and prove two claims about it, on a real object.

TWO CLAIMS WERE MADE TONIGHT AND NEITHER HAD BEEN TESTED:

  1  "a withdrawn pool cannot contribute its trials to a surviving one" -- asserted when the
     visual-abstract participant count was changed from a page-level sum to a per-outcome
     one. The arithmetic was checked; the WITHDRAWAL case was not.
  2  "a withdrawn pool publishes no certainty level" -- the grade_section fix that keys on
     state != RATED rather than on the PENDING subset.

sglt2-hf is the fixture because it really carries a withdrawn pool (cvdeath_or_whf_first)
alongside two surviving ones, so nothing here is simulated.

BOTH DIRECTIONS. Withdrawing a pool must not change any OTHER pool's count -- and must not
leave the withdrawn pool contributing either. A check that only watched the withdrawn pool
would pass a bug that silently moved its trials somewhere else.

READ-ONLY, ASSERTED: the object's sha256 is taken before and after and required to match.
Every count is printed with its numerator and denominator, because a verdict alone cannot be
debugged -- "matched 2 of 4" caught one broken guard tonight and "denominator 0" caught
another.
"""
import copy
import hashlib
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "ssot"))
import projectors2 as p2          # noqa: E402
import grade_authority as ga      # noqa: E402

OBJ = os.path.join("ssot", "sglt2-hf", "sglt2-hf.json")
fails = 0


def check(label, got, want):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print("   %-6s %-58s %s" % ("PASS" if ok else "FAIL", label, got))
    if not ok:
        print("            expected %r" % (want,))


def counts(obj):
    out = {}
    for oid, res in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        n, m, w = p2._analysed_n_for_outcome(obj, res)
        out[oid] = (n, m, w, ga.resolve(obj, oid)["state"])
    return out


def main():
    before_sha = hashlib.sha256(open(OBJ, "rb").read()).hexdigest()
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    base = counts(obj)
    print("BASELINE -- sglt2-hf as stored")
    for oid, (n, m, w, st) in sorted(base.items()):
        print("   %-30s N=%-6d matched %d of %d   state=%s" % (oid, n, m, w, st))
    withdrawn = [o for o, v in base.items() if v[3] == "WITHDRAWN_POOL"]
    survivors = [o for o, v in base.items() if v[3] != "WITHDRAWN_POOL"]
    print("")
    check("the fixture really carries a withdrawn pool", bool(withdrawn), True)
    check("and at least one surviving pool", bool(survivors), True)
    if not (withdrawn and survivors):
        sys.exit("REFUSED: this fixture cannot exercise the claim.")

    # ---- claim 2, as stored -----------------------------------------------------------
    print("")
    print("CLAIM 2 -- a withdrawn pool publishes no certainty level")
    for oid in withdrawn:
        r = ga.resolve(obj, oid)
        check("%s resolves to a withheld state" % oid[:26], r["state"] != "RATED", True)
        check("%s carries no level" % oid[:26], r.get("level"), None)

    # ---- claim 1: PLANT a withdrawal on a surviving pool -------------------------------
    victim = sorted(survivors)[0]
    others = [o for o in survivors if o != victim]
    print("")
    print("CLAIM 1 -- PLANTED: withdrawing %s must not move its trials anywhere" % victim)
    planted = copy.deepcopy(obj)
    planted["results"]["by_outcome"][victim].setdefault("pooled", {})["withdrawn"] = True
    after = counts(planted)

    check("the withdrawn pool now resolves as withdrawn",
          after[victim][3], "WITHDRAWN_POOL")
    for oid in others:
        check("%s count is UNCHANGED (%d)" % (oid[:24], base[oid][0]),
              after[oid][0], base[oid][0])
    total_before = sum(v[0] for v in base.values())
    total_after = sum(v[0] for v in after.values())
    check("no trial was absorbed elsewhere: summed N unchanged",
          total_after, total_before)
    check("the withdrawn pool's own N is not added to any survivor",
          sum(after[o][0] for o in others), sum(base[o][0] for o in others))

    # ---- restore and assert ------------------------------------------------------------
    print("")
    print("RESTORATION")
    restored = counts(obj)
    check("in-memory baseline is unchanged after the plant", restored, base)
    after_sha = hashlib.sha256(open(OBJ, "rb").read()).hexdigest()
    check("the object on disk never moved", after_sha, before_sha)
    print("   sha256 %s" % after_sha[:32])

    print("")
    print("ALL CONTROLS HELD" if not fails else "%d CONTROL(S) FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
