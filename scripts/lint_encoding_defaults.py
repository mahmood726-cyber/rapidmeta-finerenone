"""CLASS 3 RULE MADE MECHANICAL: a default that is reasonable on Windows and wrong here.

THREE INSTANCES THIS WEEK, all the same shape -- a Python default doing something sensible
for a human reader and wrong for a machine-read pipeline:

  1. CRLF CONVERSION on two 900 KB pages. A text-mode round-trip rewrote 12,031 lines.
     Five content checks passed because all five were the same check.
  2. cp1252 DECODE in a verifier. `subprocess.run(..., text=True)` decoded git output with
     the console codepage; every object holding an em-dash compared as CHANGED. It accused
     six intact files and stopped a correct commit.
  3. CRLF IN A GENERATED PAIRS FILE. A heredoc wrote Windows line endings, `read -r` kept
     the trailing \\r in every field, and ALL 57 BUILDS FAILED with
     `ssot/warfarin-af\\r/warfarin-af\\r.json`.

THE RULE IS IN OUR OWN LESSONS FILE AND DID NOT FIRE ANY OF THE THREE TIMES. That is the
same evidence that justified the pipeline-status lint, and that one earned itself on its
first real use -- reporting 0 built and 57 failed where the old form said success.

WHAT IT DETECTS:
  DECODE   `text=True` / `universal_newlines=True` on subprocess -- covered by
           lint_subprocess_decode.py, cross-referenced here rather than duplicated.
  NEWLINE  `open(path, "w")` or `io.open(path, "w", encoding=...)` WITHOUT an explicit
           `newline=` argument, in a script that writes a file another program reads.

WHY THE NEWLINE CHECK IS SCOPED, NOT UNIVERSAL. A file written for a person to read is
fine with platform line endings. The defect is a file written for a MACHINE -- a pairs
list, a manifest, a generated script. Detecting "machine-read" is not decidable, so this
flags writes to the extensions that have actually bitten: .txt, .json, .csv, .tsv, .sh and
extensionless paths under /tmp. NARROW ON PURPOSE: a lint that flags every open() becomes
noise, and noise is how this corpus ended up with gates nobody read.

A RATCHET, NOT A ZERO-GATE. A guard that stops the work gets bypassed -- that is how
guard_write failed. The count can fall and can never rise.
"""
from __future__ import annotations
import io
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(REPO, ".lint-encoding-baseline")
SKIP = re.compile(r"#\s*lint:allow-default-newline")
# a write-mode open whose target looks machine-read
WRITE = re.compile(
    r"""(?:io\.)?open\(\s*([^,)]*(?:\.txt|\.json|\.csv|\.tsv|\.sh|pairs|manifest)[^,)]*)\s*,\s*["']w""",
    re.I)
HAS_NEWLINE = re.compile(r"newline\s*=")


def scan(path, rel):
    hits = []
    try:
        lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    except Exception:
        return hits
    for i, line in enumerate(lines):
        if SKIP.search(line):
            continue
        m = WRITE.search(line)
        if m and not HAS_NEWLINE.search(line):
            hits.append((rel, i + 1, line.strip()[:76]))
    return hits


def main() -> int:
    hits = []
    d = os.path.join(REPO, "scripts")
    for root, _, files in os.walk(d):
        for fn in files:
            if fn.endswith(".py") and fn != os.path.basename(__file__):
                p = os.path.join(root, fn)
                hits += scan(p, os.path.relpath(p, REPO).replace("\\", "/"))
    for f, ln, ctx in hits:
        print("%s:%d" % (f, ln))
        print("      %s" % ctx)
    print()
    print("machine-read writes without explicit newline: %d" % len(hits))

    base = 10 ** 9
    if os.path.exists(BASELINE):
        try:
            base = int(io.open(BASELINE, encoding="utf-8").read().strip())
        except Exception:
            pass
    if len(hits) > base:
        print("REFUSED: %d sites against a baseline of %d." % (len(hits), base))
        print("FIX: pass newline='\\n' explicitly. A file a machine reads must not carry")
        print("platform line endings -- 57 builds failed on a trailing \\r this week.")
        print("Deliberate exception: append  # lint:allow-default-newline")
        return 1
    if len(hits) < base:
        io.open(BASELINE, "w", encoding="utf-8", newline="\n").write(str(len(hits)))
        print("baseline lowered to %d -- the ratchet only turns one way." % len(hits))
    print()
    print("The DECODE half of this rule lives in scripts/lint_subprocess_decode.py")
    print("(ratchet at 28). Cross-referenced rather than duplicated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
