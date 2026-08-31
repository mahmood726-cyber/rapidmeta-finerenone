#!/usr/bin/env python
"""Planted-defect proof for scripts/gate_unpoolable_override.py.

A gate whose entire population is already baselined is indistinguishable from a
gate that does nothing: it passes today because everything it can see is on the
list. So this takes a REAL override that is currently NOT served, makes it
served by adding one row to the real portfolio_pools.html, and asserts the gate
refuses BY NAME. Then restores the file and asserts the gate passes again and
the bytes are unchanged.

The plant is deliberately the regression the ratchet exists to stop: a NEW page
appearing among the served overrides while the total could otherwise look
unremarkable.

Exit 0 = the gate refused the plant and recovered. Exit 1 = it did not.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import gate_unpoolable_override as gate  # noqa: E402

POOLS = os.path.join(HERE, "portfolio_pools.html")
BASELINE = os.path.join(HERE, "outputs", "override_gate_baseline.json")
ok = True


def assert_(cond, msg):
    global ok
    print("  %s %s" % ("PASS" if cond else "FAIL", msg))
    if not cond:
        ok = False
    return cond


def verdict():
    """(served pages, all overrides) from a full sweep."""
    refusals, overrides = gate.find_overrides(
        "ssot/PAGE_MAP.json", "portfolio_pools.html",
        "outputs/portfolio_index.json", "outputs/r_validation")
    return sorted(o["page"] for o in overrides if o["served"]), overrides


def main():
    print("planted-defect proof - unpoolable-override gate")
    print("=" * 72)
    original = open(POOLS, "rb").read()
    sha_before = hashlib.sha256(original).hexdigest()
    base = json.load(open(BASELINE, encoding="utf-8"))
    print("baseline : %d served (%s)" % (base["n_served"], base["status"]))
    print("pools    : %d bytes, sha256 %s" % (len(original), sha_before))

    print("\n[1] BASELINE SWEEP")
    served, overrides = verdict()
    assert_(sorted(served) == sorted(base["served_pages"]),
            "served set matches the baseline exactly: %s" % served)

    # pick a real override that is NOT currently served
    unserved = [o for o in overrides if not o["served"]]
    if not unserved:
        print("ABORT: no unserved override to plant with.")
        return 1
    target = sorted(unserved, key=lambda o: o["topic"])[0]
    print("      %d overrides total, %d unserved; planting with %s"
          % (len(overrides), len(unserved), target["topic"]))

    try:
        print("\n[2] PLANT - make %s SERVED by adding one pools row" % target["topic"])
        stem = target["topic"].lower()
        row = ('<tr data-stem="%s" data-scale="OR" data-k="%s" class="">'
               '<td><a href="%s">%s</a></td><td class="scale">OR</td>'
               '<td class="k">%s</td><td class="pool">%s</td><td class="ci">planted</td>'
               '<td class="pi">planted</td><td class="i2">0.0%%</td><td class="qp">1.000</td>'
               '<td class="tau2">0.0000</td><td class="floor">-</td></tr>'
               % (stem, target["sidecar_k"], target["page"], target["topic"],
                  target["sidecar_k"], target["sidecar_pooled_OR"]))
        text = original.decode("utf-8", "replace")
        planted, n = re.subn(r"</tbody>", row + "</tbody>", text, count=1)
        assert_(n == 1, "exactly one row inserted")
        open(POOLS, "w", encoding="utf-8", newline="").write(planted)
        assert_(len(planted) > len(text), "file grew by one row, still well-formed HTML")

        print("\n[3] GATE ON THE PLANTED FILE")
        served2, _ = verdict()
        assert_(target["page"] in served2,
                "%s is now among the served overrides" % target["page"])
        rc = gate.main(["--baseline", BASELINE])
        assert_(rc == 1, "gate REFUSED (exit 1)")
        assert_(set(served2) - set(base["served_pages"]) == {target["page"]},
                "exactly one NEW served page, no collateral")

    finally:
        print("\n[4] RESTORE")
        open(POOLS, "wb").write(original)
        sha_after = hashlib.sha256(open(POOLS, "rb").read()).hexdigest()
        assert_(sha_after == sha_before, "restored byte-for-byte (%s)" % sha_after)

    print("\n[5] GATE ON THE RESTORED FILE")
    served3, _ = verdict()
    assert_(sorted(served3) == sorted(base["served_pages"]), "served set back to baseline")
    assert_(gate.main(["--baseline", BASELINE]) == 0, "gate PASSES again (exit 0)")

    print("\n" + "=" * 72)
    print("PROVEN: the gate refused a new served override and recovered on restore."
          if ok else "NOT PROVEN - see FAIL lines.")
    return 0 if ok else 1


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
