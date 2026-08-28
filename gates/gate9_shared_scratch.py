"""GATE 9 -- make the shared-scratch lint OPERATIVE, and ratchet what it finds.

THE LINT ALREADY EXISTED. `scripts/lint_shared_scratch_path_2026_08_24.py` was written on
2026-08-24, four days before this lane needed it. Its docstring records a lane committing 220
files under another lane's message because both chose `/tmp/msg.txt`, and a live 4,600-line
generator nearly being restored from a shared path another lane could have overwritten. It
names `/tmp` as `F:/claude-temp` on this machine — a shared root with tens of thousands of
loose files — and it carries its own positive and negative controls.

**AND NOTHING CALLED IT.** So it did not fire when this lane wrote `/tmp/f1.txt` and
`/tmp/f2.txt` and truncated another lane's verification log. Available, not operative — the
THIRD instance of that shape in one day, after `absence.py` and `subject_ref`, and the sharpest
of the three: the check that would have caught the mistake was written before the mistake and
was inert while it happened.

WHY A WRAPPER RATHER THAN AN EDIT. The lint belongs to another lane's work and is correct as
written. This gate EXERCISES it — the real script, as a subprocess, not a copy — and ratchets
its findings so it can land: 33 pre-existing violations are frozen by name, and a NEW one
fails. Editing someone else's script to add a ratchet would be the larger change and the
riskier one.

WHAT THIS DOES NOT DO. It does not fix the 33. They are named in the freeze file, several
belong to other lanes, and an unfixed finding with a stated reason is closed while one without
a reason is a backlog.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

LINT = "scripts/lint_shared_scratch_path_2026_08_24.py"
BACKLOG = "SHARED_SCRATCH_BACKLOG.json"
FINDING = re.compile(r"^\s+(\S+\.py):(\d+)\s+->\s+(.*)$")
CONTROLS_HELD = "both controls held"


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("9  SHARED SCRATCH",
                  "no script may use a generic name in the shared scratch root, and the lint "
                  "that says so must actually run")
    gate.requires_control()

    path = os.path.join(repo, LINT)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate exists to run it and will not substitute a copy."
                    % LINT)
        gate.kinds({"lint absent": 1})
        return gate.report()

    gate.expect_case("lint-runs", "the shipped lint executes and reports its own controls")

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")

    # THE LINT CARRIES ITS OWN POSITIVE AND NEGATIVE CONTROLS AND PRINTS WHETHER THEY HELD.
    # Reading that line is how this gate knows the instrument worked, rather than assuming a
    # non-zero exit means what it hopes.
    if CONTROLS_HELD in out:
        gate.saw("lint-runs")
        gate.control(1, 0, [])
    else:
        gate.control(1, 1, ["the lint did not report that its own controls held"])
        gate.broken("the shipped lint did not print %r. Its verdict is not usable."
                    % CONTROLS_HELD)

    found = []
    for line in out.splitlines():
        m = FINDING.match(line)
        if m:
            found.append("%s:%s -> %s" % (m.group(1).replace(os.sep, "/"), m.group(2),
                                          m.group(3).strip()))

    if "--plant" in argv:
        found.append("scripts/__planted.py:1 -> msg.txt")
        gate.note("PLANTED: a new shared-scratch path")

    new = H.ratchet(gate, BACKLOG, found,
                    "scripts using a generic name in the shared scratch root, which another "
                    "lane could independently choose and overwrite.")

    gate.kinds({"shared-scratch paths the lint found": len(found),
                "of those, NEW since the freeze": len(new),
                "lint exit code": proc.returncode})
    gate.note("the lint was written 2026-08-24 and called by nothing until now; it did not "
              "fire when this lane truncated another lane's file in the shared root.")

    for f in new:
        gate.finding("NEW-SHARED-SCRATCH-PATH",
                     "%s uses a generic name in the shared scratch root. Another lane will "
                     "choose the same name; write to the session scratch directory or add a "
                     "unique suffix." % f,
                     numerator=len(new), denominator=len(found))

    return gate.report(denominator="%d shared-scratch paths, %d frozen" % (len(found),
                                                                          len(found) - len(new)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
