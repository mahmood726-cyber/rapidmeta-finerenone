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

    failed, missing, slow = [], [], []
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
        else:
            failed.append((script, rc, tail))
            print("  FAILED   %-56s %5.1fs  exit=%s" % (script, dt, rc))
            if tail:
                print("             %s" % tail)

    total = time.time() - t0
    print("-" * 78)
    print("  %d ok, %d FAILED, %d missing, %.1fs total" %
          (len(entries) - len(failed) - len(missing), len(failed), len(missing), total))
    if slow:
        print("  slower than measured (>15s), consider moving to CI:")
        for s, dt in slow:
            print("     %-56s %5.1fs" % (s, dt))
    if missing:
        print("  A check in the manifest that is GONE is not a pass -- it is a check that")
        print("  stopped existing without anyone noticing.")
    print("=" * 78)

    if failed or missing:
        return H.FAIL
    return H.PASS


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
