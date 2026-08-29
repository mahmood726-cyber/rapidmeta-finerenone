# no-control: this module matches no document text. It runs other gates as subprocesses and
# compares their exit codes, which are integers. There is nothing to be a false positive about.
"""A gate that has only ever said PASS has not been shown to discriminate.

Every gate here now PASSES on the corpus, because its pre-existing findings are frozen by name.
That is exactly the state in which a broken gate is invisible: green, installed, seeing
nothing. This module plants a defect in each gate's input, asserts the gate FAILS, removes the
defect, and asserts it PASSES again -- and it asserts the RESTORATION, not just the failure,
because a gate that fails and then keeps failing is also broken.

It runs in CI beside the gates themselves. A gate whose plant no longer trips it has stopped
working and says so here rather than in six weeks.

Each row is (gate module, plant args, what the plant is). The plants are IN MEMORY or in a
scratch file this module deletes; none writes to the store, and none touches a shared output.
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

REPO = H.repo_root()
GATEDIR = os.path.join(REPO, "gates")

PLANTS = [
    ("gate1_trial_identity", ["--plant"],
     "swap the ceftaroline labels, a pair the gate currently confirms"),
    ("gate2_textmatch_control", ["--plant"],
     "a new text-matching check with no known-negative control"),
    ("gate3_one_reason_field", ["--plant"],
     "a contradictory withdrawn_reason on a clean outcome"),
    ("gate4_judgement_reference", ["--plant"],
     "a new judgement carrying no reference to its subject"),
    ("gate5_absence_defined_set", ["--action"],
     "an actual removal attempted on the absence-defined set"),
    ("gate6_nct_beside_name", ["--plant"],
     "a generator site emitting a bare trial name"),
    ("gate7_blast_radius", ["--plant"],
     "an unacknowledged edit to a file 155 topics build through"),
    ("gate8_caller_and_wiring", ["--plant"],
     "a removal-shaped script in neither the registry nor wired to the precondition"),
    ("gate9_shared_scratch", ["--plant"],
     "a new generic name in the shared scratch root"),
    # ADDED 2026-08-29 with the gates themselves. Both were verified to fail on a
    # plant by hand when they were written; a hand check proves it once, and this
    # is what proves it on every push.
    ("gate11_one_statistic_one_value", ["--plant"],
     "an object whose stored heterogeneity field disagrees with its own R output"),
    ("gate12_planned_shown_as_observed", ["--plant"],
     "a page showing a registered planned duration under an observed label"),
]

# GATES WITH NO PLANT HERE, NAMED RATHER THAN OMITTED. gate5 is exercised through
# --action rather than --plant and is in the table above; gate10 has no entry, so
# NOTHING asserts that it can still fail. It was added by another lane and this lane
# will not write a plant for a detector it does not own -- but an uncovered gate is
# a hole, and a hole nobody has written down is indistinguishable from coverage.
UNPLANTED = ["gate10_noninferiority_pooled_as_superiority"]


def run(mod, args):
    r = subprocess.run([sys.executable, os.path.join(GATEDIR, mod + ".py")] + args,
                       cwd=REPO, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main(argv):
    gate = H.Gate("0  GATES CAN FAIL",
                  "every gate is planted with its own defect, watched to fail, restored, and "
                  "the restoration asserted")
    kinds = {"gates registered in run_all": len(PLANTS) + len(UNPLANTED),
             "gates under test here": len(PLANTS),
             "gates with NO plant -- unproven, not passing": len(UNPLANTED),
             "plants that tripped their gate": 0,
             "plants that did NOT trip their gate": 0,
             "gates that returned to PASS after restoration": 0,
             "gates that did NOT return to PASS": 0}

    for mod, args, what in PLANTS:
        gate.expect_case(mod, what)

        planted_rc, _ = run(mod, args)
        restored_rc, _ = run(mod, [])

        tripped = planted_rc != H.PASS
        restored = restored_rc == H.PASS
        if tripped:
            kinds["plants that tripped their gate"] += 1
        else:
            kinds["plants that did NOT trip their gate"] += 1
        if restored:
            kinds["gates that returned to PASS after restoration"] += 1
        else:
            kinds["gates that did NOT return to PASS"] += 1

        if tripped and restored:
            gate.saw(mod)
            gate.note("%-28s plant -> %-7s   restored -> PASS   (%s)"
                      % (mod, H.VERDICT_NAME[planted_rc], what))
            continue

        if not tripped:
            gate.finding("PLANT-DID-NOT-TRIP-THE-GATE",
                         "%s returned PASS with %s planted (%s). The gate no longer sees the "
                         "defect it was built for." % (mod, " ".join(args), what))
        if not restored:
            gate.finding("GATE-DID-NOT-RESTORE",
                         "%s returned %s with nothing planted. A gate that fails on a clean "
                         "input cries wolf, and a gate that cries wolf gets bypassed."
                         % (mod, H.VERDICT_NAME[restored_rc]))

    gate.kinds(kinds)
    gate.note("a plant is in memory or in a scratch file this module removes; none writes to "
              "the store and none touches a shared output path.")
    return gate.report(denominator="%d gates" % len(PLANTS))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
