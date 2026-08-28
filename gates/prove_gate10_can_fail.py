# no-control: matches only its own captured stdout for the finding keys it planted a
# moment earlier, and reports no count over any corpus text. Stated rather than
# silently exempted, because an unexplained exemption is how a gate stops meaning
# anything.
"""Prove GATE 10 can fail, in BOTH directions, and that it refuses a fixture it cannot reach.

A gate that has only ever been seen to pass is not evidence. Three planted breakages, each
restored, each asserted:

  1 REGRESSION      a detector stops working  -> expect DETECTED, got ZERO  -> FAIL
  2 REGISTRY STALE  a known-zero starts firing -> expect ZERO, got DETECTED -> FAIL
  3 VACUUM          a probe never reaches its fixture -> VACUOUS, never PASS

Run from the repo root: python gates/prove_gate10_can_fail.py
"""
from __future__ import annotations

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import gate10_planted_regression as G10                                     # noqa: E402
import regression_plants as RP                                              # noqa: E402


def run_quiet(argv):
    """Run gate 10 and return its verdict without printing its report."""
    buf, real = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        return G10.main(argv), buf.getvalue()
    finally:
        sys.stdout = real


results = []

# -- 0. the baseline: it passes as shipped -----------------------------------------------
rc, _ = run_quiet([])
results.append(("baseline as shipped", rc, H.PASS))

# -- 1. REGRESSION: a working detector stops working -------------------------------------
orig = G10.PROBES["p_gate1_swap"]
G10.PROBES["p_gate1_swap"] = lambda: (False, "simulated: the detector no longer fires")
rc, out = run_quiet([])
results.append(("a detector stops working", rc, H.FAIL))
assert "REGRESSION-CLASS-NO-LONGER-DETECTED" in out, "the regression was not NAMED"
G10.PROBES["p_gate1_swap"] = orig

# -- 2. REGISTRY STALE: a known-zero starts being detected --------------------------------
orig2 = G10.PROBES["p_none"]
G10.PROBES["p_none"] = lambda: (True, "simulated: a new detector now reports this class")
rc, out = run_quiet([])
results.append(("a known-zero starts firing", rc, H.FAIL))
assert "REGISTRY-STALE-CLASS-NOW-DETECTED" in out, "the stale registry was not NAMED"
G10.PROBES["p_none"] = orig2

# -- 3. VACUUM: a probe that never reaches its fixture ------------------------------------
missing = dict(RP.PLANTS[0])
missing["id"] = "VACUUM-PROBE"
missing["probe"] = "p_does_not_exist"
RP.PLANTS.append(missing)
rc, out = run_quiet([])
results.append(("a probe never reaches its fixture", rc, H.BROKEN))
RP.PLANTS.pop()

# -- 4. restored -------------------------------------------------------------------------
rc, _ = run_quiet([])
results.append(("restored after all three", rc, H.PASS))

print("=" * 78)
print("CAN GATE 10 FAIL?")
ok = True
for what, got, want in results:
    good = got == want
    ok = ok and good
    print("  %-4s %-36s got %-8s want %s"
          % ("OK" if good else "BAD", what, H.VERDICT_NAME[got], H.VERDICT_NAME[want]))
print("  VERDICT: %s" % ("PROVEN -- it fails in both directions and refuses a vacuum"
                         if ok else "NOT PROVEN"))
print("=" * 78)
sys.exit(0 if ok else 1)
