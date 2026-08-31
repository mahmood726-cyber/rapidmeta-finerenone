# no-control: this module matches no document text. It runs other scripts as subprocesses and
# reports their exit codes, which are integers. There is nothing to be a false positive about.
"""Run the checks this repository already owned and nobody called.

THE NUMBER THIS EXISTS FOR. Of 200 scripts here named like a gate that CAN fail, 156 were
called by nothing; 44 were wired. A further 59 are named like a gate and have no failing exit
at all. **17% of the check-shaped scripts in this repository were operative.** Knowledge
recorded, connected to nothing.

MEASURED, NOT LABELLED. A first pass sorted the 156 by keyword and put 48 in "should run on
every build". Running all 48 gave a different answer, and the difference is the point:

    24  GREEN and FAST (<=10s)   -> wired here, 32 seconds for all of them
     8  GREEN but SLOW (13-112s) -> CI only
    12  RED, fails on the corpus today -> a FINDING to read, not yet a gate
     4  TIMEOUT >120s            -> needs scoping before it is anything

Wiring the labelled 48 would have produced a pre-push hook that always fails and takes an
hour, which is how a gate becomes a bypass. The manifest records the exit code and wall time
behind every entry.

ONE OBSERVATION EACH, ON ONE TREE. A check green today can be red after another lane lands,
so failures are reported PER CHECK with the script named -- never as a single opaque
non-zero. A group gate whose failure you cannot read is a group gate that gets skipped.

`--list` prints what would run and exits 0.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

MANIFEST = "WIRED_REPO_CHECKS.json"
BUDGET_SECONDS = 120


def main(argv):
    repo = H.repo_root()
    manifest = H.load(os.path.join(repo, "gates", MANIFEST))
    entries = manifest["pre_push"]

    if "--list" in argv:
        print("%d checks, measured total %.1fs"
              % (len(entries), sum(e["secs"] for e in entries)))
        for e in entries:
            print("   %-58s %5.1fs" % (e["script"], e["secs"]))
        return H.PASS

    print("")
    print("=" * 78)
    print("REPO CHECKS THIS REPOSITORY ALREADY OWNED (%d, measured %.1fs)"
          % (len(entries), sum(e["secs"] for e in entries)))
    print("-" * 78)

    failed, missing, slow, indeterminate = [], [], [], []
    t0 = time.time()
    for e in entries:
        script = e["script"]
        path = os.path.join(repo, script)
        if not os.path.exists(path):
            missing.append(script)
            print("  MISSING  %s" % script)
            continue
        s0 = time.time()
        try:
            proc = subprocess.run([sys.executable, path], cwd=repo,
                                  capture_output=True, timeout=BUDGET_SECONDS)
            rc = proc.returncode
            tail = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip()
            tail = tail.splitlines()[-1][:110] if tail else ""
        except subprocess.TimeoutExpired:
            rc, tail = None, "timed out after %ds" % BUDGET_SECONDS
        dt = time.time() - s0
        if dt > 15:
            slow.append((script, dt))
        if rc == 0:
            print("  ok       %-56s %5.1fs" % (script, dt))
        elif rc is None:
            # ⛔ A TIMEOUT IS NOT A REFUSAL. `rc is None` means the check REACHED NO VERDICT --
            # it did not examine the diff and find it wanting, it ran out of clock. Recording
            # that identically to a non-zero exit is the exact class this project has spent a
            # day hunting: A CHECK WHOSE INABILITY TO ANSWER IS INDISTINGUISHABLE FROM ITS
            # NEGATIVE RESULT IS NOT A CHECK.
            #
            # ⚠️ IT HAS ALREADY BLOCKED A REAL PUSH ON A JUDGEMENT NOBODY MADE.
            # `gate_layer_vs_defect_layer_2026_08_26_audit.py` hit the 120s cap on a contended
            # disk and printed `FAILED ... exit=None`. Run uncapped immediately afterwards it
            # returned rc=0 -- it is an inventory audit that classifies 624 modules and objects
            # to nothing. The suite was 23 ok, 1 "FAILED", and the one had no verdict at all.
            #
            # ⭐ WHETHER AN INDETERMINATE GATE SHOULD BLOCK A PUSH IS A POLICY QUESTION AND IT IS
            # LEFT OPEN HERE -- they are still counted against the push, deliberately, because a
            # check that cannot run is not evidence of safety either. What is fixed is the
            # CONFLATION: the operator is now told which of the two happened, and how long it
            # waited, so "slow tonight" can never again be read as "found a defect".
            indeterminate.append((script, dt, tail))
            print("  INDETERMINATE %-51s %5.1fs  NO VERDICT REACHED" % (script, dt))
            print("             %s -- the check did not judge this diff; it ran out of clock."
                  % tail)
            print("             Re-run it uncapped before treating this as a finding.")
        else:
            failed.append((script, rc, tail))
            print("  FAILED   %-56s %5.1fs  exit=%s" % (script, dt, rc))
            if tail:
                print("             %s" % tail)

    total = time.time() - t0
    print("-" * 78)
    print("  %d ok, %d FAILED, %d INDETERMINATE, %d missing, %.1fs total" %
          (len(entries) - len(failed) - len(missing) - len(indeterminate),
           len(failed), len(indeterminate), len(missing), total))
    if indeterminate:
        print("")
        print("  ⛔ %d check(s) REACHED NO VERDICT. They did not judge this diff; they ran out"
              % len(indeterminate))
        print("     of clock at %ds. A TIMEOUT IS NOT A REFUSAL." % BUDGET_SECONDS)
        for s, dt, _ in indeterminate:
            print("       %-56s %5.1fs" % (s, dt))
        print("     ⚠️ Before treating any of these as a finding, RUN IT UNCAPPED. And before")
        print("        moving one out of the manifest, note that 'it was slow tonight' is not")
        print("        evidence the check is unsound -- that is a bypass wearing a reason.")
    if slow:
        print("  slower than measured (>15s), consider moving to CI:")
        for s, dt in slow:
            print("     %-56s %5.1fs" % (s, dt))
    if missing:
        print("  A check in the manifest that is GONE is not a pass -- it is a check that")
        print("  stopped existing without anyone noticing.")
    print("=" * 78)

    # ⛔ INDETERMINATE STILL BLOCKS, AND THAT IS DELIBERATE. Splitting the state out of FAILED
    # was a REPORTING fix, not a licence: a check that could not run is not evidence of safety
    # either, and quietly letting timeouts through would turn a contended disk into a silent
    # bypass for the whole suite.
    #
    # ⚠️ THE FIRST DRAFT OF THIS FIX DID EXACTLY THAT. Removing timeouts from `failed` without
    # touching this line would have made every timed-out gate PASS the push -- weakening the
    # gate while appearing to improve its reporting, and doing it in the very edit that
    # unblocked my own work. That is the shape a bypass takes when it is not intended as one.
    if failed or missing or indeterminate:
        return H.FAIL
    return H.PASS


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
