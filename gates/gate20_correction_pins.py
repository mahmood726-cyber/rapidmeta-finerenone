"""GATE 20 -- a correction must describe bytes a reader can still obtain.

A correction record says WHAT WAS PUBLISHED and WHAT THE CORRECTED ESTIMATOR
GIVES. Both halves are unverifiable unless the reader can obtain the bytes the
record is about, so each record pins a sha256 and states its own rule:

    "the sha256 pins WHICH bytes this correction is about. If the file changes,
     this correction is about the old bytes and must be re-derived, not amended."

THIS GATE RUNS THE DETECTOR RATHER THAN REIMPLEMENTING IT, and reads the JSON it
writes rather than its prose. A second copy of the matching logic is how two
surfaces start disagreeing about one artefact; counting verdict words in stdout
is how a denominator stops matching its population. The first draft of this gate
did the second and reported 8 records where there are 5, because each CONTROL
line contains a verdict word twice.

WHY IT EXISTS: scripts/check_correction_pins.py was written, worked, and was
called by nothing. Gate 8 caught it the same night -- "named like a gate, can
fail, and nothing runs it". A correct, tested, inert check is worth zero, and
being its author is no protection against writing one.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

DETECTOR = os.path.join("scripts", "check_correction_pins.py")
STATUS = os.path.join("corrections", "PIN_STATUS.json")


def main(argv):
    gate = H.Gate("20 CORRECTION PINS",
                  "a correction must pin bytes that can still be obtained")
    # SYNTHETIC, not anchored to a live record. A named positive pointing at a real
    # unverifiable correction retires itself the day that correction is fixed,
    # leaving a gate that passes because nothing is left to find.
    gate.expect_case("discriminates",
                     "a pin matching the bytes is HOLDS and a pin matching nothing "
                     "is BROKEN, measured on synthetic probes every run")
    gate.requires_control()

    repo = H.repo_root()
    path = os.path.join(repo, DETECTOR)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate RUNS the detector rather than "
                    "reimplementing it." % DETECTOR)
        gate.kinds({"detector present": 0, "detector absent": 1})
        return gate.report(denominator="0 records -- the detector could not run")

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    if proc.returncode == 2 or "REFUSED:" in out:
        gate.broken("the detector refused its own controls, so no verdict it prints "
                    "is trustworthy: %s" % out[-260:].replace(chr(10), " "))
        gate.kinds({"records reached": 0})
        return gate.report(denominator="the detector refused rather than reporting")

    if "both controls held." in out:
        gate.control(2, 0, [], accuses=True)
        gate.saw("discriminates")
    else:
        gate.control(2, 2, ["the detector's own controls did not hold"], accuses=True)
        gate.broken("the detector did not report both controls holding")

    sp = os.path.join(repo, STATUS)
    if not os.path.exists(sp):
        gate.broken("the detector wrote no %s, so there is nothing to count" % STATUS)
        gate.kinds({"records reached": 0})
        return gate.report(denominator="no status file")
    with open(sp, encoding="utf-8") as fh:
        st = json.load(fh)
    recs = st.get("records") or []
    k = st.get("kinds") or {}
    holds = k.get("HOLDS", 0)
    ahead = k.get("AHEAD_OF_BRANCH", 0)
    broken = k.get("BROKEN", 0)
    absent = k.get("ABSENT", 0)
    nopin = k.get("NO_PIN", 0)
    total = len(recs)
    if holds + ahead + broken + absent + nopin != total:
        gate.broken("the kinds sum to %d over %d records -- a count that disagrees "
                    "with its own population is not usable"
                    % (holds + ahead + broken + absent + nopin, total))
        gate.kinds({"correction records": total})
        return gate.report(denominator="%d records, kinds inconsistent" % total)

    gate.kinds({
        "correction records": total,
        "  HOLDS -- pinned bytes are the bytes here": holds,
        "  AHEAD_OF_BRANCH -- pinned bytes exist on another lane": ahead,
        "  BROKEN -- no known lane produces them": broken,
        "  ABSENT -- the artefact named is gone": absent,
        "  NO_PIN -- nothing to check, never clean": nopin,
    })
    gate.coverage(total - nopin, total,
                  "correction records carrying a file+sha256 pair")
    gate.note("AHEAD_OF_BRANCH is neither pass nor fail: the record is correct and "
              "this branch is behind. It names the lane and the commit, so the "
              "remedy is a merge and never an edit to a hash.")
    gate.note("a pin is NEVER amended. A changed artefact means the record is about "
              "the old bytes and must be re-derived.")
    if ahead:
        gate.note("%d record(s) await a merge and are NOT counted as verified." % ahead)

    for kind, n in (("BROKEN", broken), ("ABSENT", absent), ("NO_PIN", nopin)):
        if n:
            gate.finding("CORRECTION-PIN-%s" % kind,
                         "%d correction record(s) are %s -- the record cannot be "
                         "checked against any bytes we hold." % (n, kind))
    return gate.report(denominator="%d correction records; %d verifiable here, "
                                   "%d awaiting a merge" % (total, holds, ahead))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
