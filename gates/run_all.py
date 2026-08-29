# no-control: this module matches no document text. Its only `in` test is a substring check
# against the --only argument to select which gates to run, which reports nothing and decides
# no finding. Stated rather than silently exempted, because an unexplained exemption is how a
# gate stops meaning anything.
"""Run every gate. Print the numerator and the denominator. Never summarise to a tick.

EXIT CODE IS THE WORST OF THE GATES, and VACUOUS is worse than FAIL on purpose: a gate that
could not see is more dangerous than one that saw and objected, because it reads as a pass.

  0 PASS     every gate saw its named cases and found nothing
  1 FAIL     at least one gate found something
  2 VACUOUS  at least one gate never reached a case it was built to find
  3 BROKEN   at least one gate could not run

`--fast` skips the gates that read all 1,426 delivered pages (5 and 6), for use where a
sub-minute check is wanted. It prints WHICH gates it skipped, because a scoped pass that does
not name its scope is how "53 apps" turned out to be 1,522.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

GATES = [
    ("gate1_trial_identity", "trial identity: a name beside a registration", "fast"),
    ("gate2_textmatch_control", "text matching carries a measured precision", "slow"),
    ("gate3_one_reason_field", "one authoritative reason for not pooling", "fast"),
    ("gate4_judgement_reference", "a judgement references what it judged", "fast"),
    ("gate5_absence_defined_set", "no irreversible action on an absence", "slow"),
    ("gate6_nct_beside_name", "NCT beside every trial name", "slow"),
    ("gate7_blast_radius", "blast radius counted before a class-wide edit", "fast"),
    ("gate8_caller_and_wiring", "every gate has a caller; every removal a precondition", "fast"),
    ("gate9_shared_scratch", "the shared-scratch lint actually runs", "fast"),
    # ADDED 2026-08-29. The class was undefended: 35 pooled topics contain a registered
    # non-inferiority trial, 9 pool nothing else, and ZERO pages state a margin. Registering it
    # here is what makes the detector operative -- a detector nothing calls is the
    # available-not-operative shape these gates exist to expose, and this suite was itself
    # sitting unmerged when the class was found.
    ("gate10_noninferiority_pooled_as_superiority",
     "non-inferiority pooled as superiority", "fast"),
]


def main(argv):
    fast = "--fast" in argv
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1].split(",")

    results, skipped = [], []
    for mod, what, speed in GATES:
        if only and not any(o in mod for o in only):
            continue
        if fast and speed == "slow":
            skipped.append(mod)
            continue
        t0 = time.time()
        m = importlib.import_module(mod)
        try:
            rc = m.main([a for a in argv if a not in ("--fast",)])
        except Exception as exc:            # a gate that crashes is BROKEN, never a pass
            print("GATE %s CRASHED: %r" % (mod, exc))
            rc = H.BROKEN
        results.append((mod, what, rc, time.time() - t0))

    print("")
    print("#" * 78)
    print("GATE SUMMARY")
    for mod, what, rc, dt in results:
        print("  %-9s %-32s %-28s %5.1fs" % (H.VERDICT_NAME[rc], mod.split("_", 1)[0], what, dt))
    if skipped:
        print("  SKIPPED (--fast): " + ", ".join(skipped))
        print("  A scoped pass names its scope. These gates read all delivered pages and were")
        print("  NOT run; this run says nothing about what they check.")
    worst = max([r for _, _, r, _ in results] or [H.BROKEN],
                key=lambda r: {H.PASS: 0, H.FAIL: 1, H.VACUOUS: 2, H.BROKEN: 3}[r])
    print("  OVERALL: %s" % H.VERDICT_NAME[worst])
    print("#" * 78)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
