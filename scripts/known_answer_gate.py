#!/usr/bin/env python3
"""P12 MADE MECHANICAL: an import error in the known-answer suite is a BUILD FAILURE.

WHY THIS EXISTS. On 2026-08-19 the `criteria_stated` / `criteria_predefined` split was
committed without re-running `known_answer_preconditions.py`. The suite had been erroring on
IMPORT since the rename -- `AttributeError: module 'preconditions' has no attribute
'inclusion_criteria_auditable'` -- so it produced no failures because it produced nothing at
all. The split was "verified" instead by running the batch assessment and reading the verdict
matrix.

That is checking VERDICTS, not REASONING, for the third time in one night -- and it was done
to the suite whose entire job is to catch exactly that.

THE DISTINCTION THIS GATE ENFORCES:
    exit 0 with assertions run and passed   -> the suite ran
    exit non-zero from a failed assertion   -> the suite ran and found something
    exit non-zero from ImportError/Attribute/Syntax  -> THE SUITE DID NOT RUN
The third case is the dangerous one, because in a pipeline that only reads exit codes it is
indistinguishable from the second, and in a pipeline that ignores non-zero it is
indistinguishable from the first.

So this gate does not trust the exit code alone. It requires POSITIVE EVIDENCE OF EXECUTION:
a minimum number of `[ok ]` lines on stdout. A suite that ran and passed says so many times;
a suite that never started cannot.
"""
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each entry: (path, minimum number of executed checks that must be observed).
# The minimum is a FLOOR ON EXECUTION, not on coverage. It exists so a suite that silently
# stops emitting -- an early return, a swallowed exception, a renamed symbol -- is caught.
SUITES = [
    (os.path.join("evidence", "2026-08-19-batch1", "known_answer_preconditions.py"), 40),
    (os.path.join("evidence", "2026-08-19-batch1", "known_answer_transport.py"), 8),
]

NOT_RUN = ("ImportError", "ModuleNotFoundError", "AttributeError", "SyntaxError",
           "NameError", "IndentationError")


def run(rel, floor):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return False, f"{rel}: SUITE ABSENT -- a missing suite is not a passing suite"
    proc = subprocess.run([sys.executable, "-W", "error", path],
                          cwd=REPO, capture_output=True,
                          encoding="utf-8", errors="replace", timeout=600)
    out = (proc.stdout or "") + (proc.stderr or "")
    ok_lines = out.count("[ok ]")

    # THE SUITE DID NOT RUN. This is checked BEFORE the exit code, because it is a different
    # failure from a failing assertion and must not be reported as one.
    for exc in NOT_RUN:
        if exc in out:
            return False, (f"{rel}: SUITE DID NOT RUN -- {exc} before/while collecting. "
                           f"This is a BUILD FAILURE, not a skipped test. Observed "
                           f"{ok_lines} executed checks.")
    if ok_lines < floor:
        return False, (f"{rel}: only {ok_lines} executed checks observed, floor is {floor}. "
                       f"A suite that stops emitting has stopped running.")
    if proc.returncode != 0:
        return False, f"{rel}: ran ({ok_lines} checks) and FAILED, exit {proc.returncode}"
    return True, f"{rel}: ran and passed, {ok_lines} executed checks observed"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad = 0
    for rel, floor in SUITES:
        ok, msg = run(rel, floor)
        print(("[ok  ] " if ok else "[FAIL] ") + msg)
        bad += (not ok)
    print()
    if bad:
        print(f"REFUSED: {bad} suite(s) did not run or did not pass. "
              f"A green matrix is not evidence the suite ran.")
        return 1
    print("P12 held: every known-answer suite executed and passed in this build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
