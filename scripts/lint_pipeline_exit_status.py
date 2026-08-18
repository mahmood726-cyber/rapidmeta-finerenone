"""CLASS 3 RULE MADE MECHANICAL: `$?` after a pipeline reads the LAST stage, not the first.

TEN INSTANCES. THREE THIS WEEK. Prose has failed on this every time, in a repository whose
own rules file documents the trap. That is conclusive, so it becomes a lint.

WHAT IT COSTS WHEN IT FIRES:
  - the original pre-push hook printed "Regression check PASS" at 0/1522 fully-ok, because
    STATUS=$? after `cmd | tail -15` read tail's exit code
  - the registry drift check reported exit=0 while the script exited 1, because the test
    piped through `tail -5`
  - a build loop reported six successes while EVERY build raised KeyError, because each
    iteration ended `| tail -1` and the loop reported tail's status

THE LAST ONE IS THE WORST: it would have had six pages reported as built and live when none
of them existed. A check that cannot fail reports success without having checked, and a
pipeline that swallows a status turns any check into that.

WHAT IT DETECTS, in .sh files and the hook directory:
  ASSIGN   `X=$?` or `echo $?` on the line after a command containing an unguarded pipe
  ECHO     `echo "... $? ..."` on a line that itself contains a pipe
  IF       `if cmd | grep ...; then` where the condition's status is the last stage's

THE FIX at each site: `set -o pipefail`, or `${PIPESTATUS[0]}`, or capture the status
BEFORE piping for display. In Python, check `subprocess.run(...).returncode` rather than
reading a shell's `$?` at all.

A RATCHET, NOT A ZERO-GATE, for the reason the decode lint gives: a guard that stops the
work gets bypassed, which is exactly how guard_write failed. The count can fall and can
never rise, so each new site is refused at the moment it is written.
"""
from __future__ import annotations
import io
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(REPO, ".lint-pipeline-baseline")
SKIP = re.compile(r"#\s*lint:allow-pipeline-status")
GUARDED = re.compile(r"pipefail|PIPESTATUS")
# a pipe that is not ||, not inside a bracket test, not a shell function pipe-to-nothing
PIPE = re.compile(r"[^|]\|[^|]")
STATUS = re.compile(r"\$\?")


def scan_file(path, rel):
    hits = []
    try:
        lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    except Exception:
        return hits
    if any(GUARDED.search(l) for l in lines[:40]):
        return hits            # file opts in to pipefail at the top
    for i, line in enumerate(lines):
        if SKIP.search(line):
            continue
        # ECHO: $? on a line that itself pipes
        if STATUS.search(line) and PIPE.search(line):
            hits.append((rel, i + 1, "status read on a line containing a pipe",
                         line.strip()[:70]))
            continue
        # ASSIGN: $? on a line whose PREVIOUS non-blank line piped
        if STATUS.search(line):
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0 and PIPE.search(lines[j]) and not GUARDED.search(lines[j]):
                hits.append((rel, i + 1, "status read after a piped command",
                             lines[j].strip()[:70]))
    return hits


def main() -> int:
    hits = []
    for base in (".githooks", "scripts"):
        d = os.path.join(REPO, base)
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for fn in files:
                if fn.endswith((".sh", ".bash")) or base == ".githooks":
                    p = os.path.join(root, fn)
                    if os.path.isfile(p):
                        hits += scan_file(p, os.path.relpath(p, REPO).replace("\\", "/"))
    for f, ln, why, ctx in hits:
        print("%s:%d  %s" % (f, ln, why))
        print("      %s" % ctx)
    print()
    print("pipeline-status hazard sites: %d" % len(hits))

    base = 10 ** 9
    if os.path.exists(BASELINE):
        try:
            base = int(io.open(BASELINE, encoding="utf-8").read().strip())
        except Exception:
            pass
    if len(hits) > base:
        print("REFUSED: %d sites against a baseline of %d. A NEW pipeline-status hazard "
              "was introduced." % (len(hits), base))
        print("FIX: set -o pipefail, or ${PIPESTATUS[0]}, or capture the status BEFORE "
              "piping for display.")
        print("Deliberate exception: append  # lint:allow-pipeline-status  on the line.")
        return 1
    if len(hits) < base:
        io.open(BASELINE, "w", encoding="utf-8").write(str(len(hits)))
        print("baseline lowered to %d -- the ratchet only turns one way." % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
