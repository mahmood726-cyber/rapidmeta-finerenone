"""A commit message asserting the state of a file is checked against the file.

TWICE IN ONE DAY a commit message asserted something untrue:

  "all 19 CLEAN"   -- written from 17 visible lines of a 19-line job that was still running.
                      Two of the remaining pages were MISMATCH.
  "section 7 rewritten at n=300" -- the rewrite script raised ValueError: substring not
                      found, the document kept its old text, AND THE COMMIT WENT THROUGH,
                      because the failure was on stdout and the commit was a separate command
                      in the same chain.

The second is the mechanisable one, and the difference is the whole point: it asserted a
state of a FILE. `grep -c "n = 300"` returned 0. Prose about an artefact can be checked
against the artefact; prose about a running job cannot.

Prose is the only artefact in this repository with no verification. Every number on a page
traces to a field and every gate has a control, while commit messages -- where the claims are
actually made -- have neither. This is the narrow, cheap half of that gap closed.

HOW TO USE IT. Put lines of this shape in the commit message:

    VERIFY: path/to/file.md contains some exact substring
    VERIFY: path/to/file.py absent some exact substring

Each is executed against the working tree before the commit is allowed. A claim that fails
refuses the commit and prints what was expected and what was found.

DELIBERATELY NARROW, because a gate that blocks outside its scope teaches people to bypass
it, and this repository has already learned that the expensive way. It checks ONLY explicit
VERIFY: lines. It does not parse prose, guess at claims, or infer what a message means. A
commit with no VERIFY: lines passes untouched -- the point is to make verification POSSIBLE
and cheap, not to pretend every sentence can be machine-checked.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIM = re.compile(r"^\s*VERIFY:\s*(\S+)\s+(contains|absent)\s+(.+?)\s*$", re.M)


def check(path, mode, needle):
    full = os.path.join(REPO, path)
    if not os.path.exists(full):
        return False, "file does not exist"
    try:
        body = io.open(full, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return False, "unreadable: %s" % type(e).__name__
    found = needle in body
    if mode == "contains":
        return (found, "found" if found else "NOT FOUND in %d chars" % len(body))
    return ((not found), "absent" if not found else "PRESENT but claimed absent")


def main():
    msg_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not msg_path or not os.path.exists(msg_path):
        return 0
    msg = io.open(msg_path, encoding="utf-8", errors="replace").read()
    claims = CLAIM.findall(msg)
    if not claims:
        return 0

    print("commit-claim check: %d VERIFY line(s)" % len(claims))
    bad = []
    for path, mode, needle in claims:
        ok, why = check(path, mode, needle)
        print("  %-4s %s %s %r -> %s" % ("PASS" if ok else "FAIL", path, mode, needle[:60], why))
        if not ok:
            bad.append((path, mode, needle, why))
    if bad:
        print()
        print("REFUSED: %d claim(s) in this commit message are not true of the working tree."
              % len(bad))
        print("A commit message asserting a state of a file is checked against the file. This")
        print("has caught two untrue messages already; fix the file or fix the claim.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
