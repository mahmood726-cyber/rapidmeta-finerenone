"""REBUILD GUARD -- a rebuild that DELETES more than it ADDS refuses by default.

WHY THIS EXISTS
    On 2026-08-18 a rebuild of `bococizumab-lipid-review` wrote 152 lines over 1,626.
    It destroyed the withdrawn `primary` outcome WITH ITS REASON, the sources block,
    the screening record and the risk-of-bias verdict -- and produced a perfectly
    valid object that every gate would have passed, because everything it kept was
    internally consistent.

    THE MATERIAL A REBUILD DESTROYS IS EXACTLY THE MATERIAL THAT MAKES A PAGE
    CHECKABLE. A withdrawal reason, a source list, a RoB verdict and a screening
    record are not outputs -- they are the evidence that the outputs were earned.
    An object stripped of them still validates.

    Same family as the idempotency failure already in the ledger: validity and delta
    are different questions, and every gate in this repository asks the first one.
    The defence is the same and it is now mechanical rather than remembered.

WHAT IT CHECKS
    For a file about to be written: count the lines being removed against the lines
    being added, relative to git HEAD. If removals exceed additions, REFUSE unless
    the caller passes an explicit override naming the reason.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a rebuild which ADDS more than it removes is safe. A patch can add a
      hundred lines and quietly change one value; that is the delta check's job and
      this guard is blind to it.
    - NOT that the deleted lines were valuable. It is a line count, not a reading. A
      genuine consolidation will trip it, and is meant to -- the override exists so
      that the person doing it says so out loud.
    - NOTHING about a file not tracked in git. Untracked means no baseline, and that
      returns NO_BASELINE, never a pass.

USAGE
    from rebuild_guard import guard_write
    guard_write(path, new_text)                       # refuses on net deletion
    guard_write(path, new_text, allow_net_deletion="consolidating three blocks into one")
"""
from __future__ import annotations
import io
import os
import subprocess
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


class RebuildRefused(Exception):
    pass


def _head_text(path):
    """The file as git HEAD has it, or None if it is not tracked."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rel = os.path.relpath(os.path.abspath(path), repo).replace(os.sep, "/")
    p = subprocess.run(["git", "-C", repo, "show", "HEAD:" + rel],
                       capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8", "replace")


def assess(path, new_text):
    """(verdict, added, removed, note)."""
    old = _head_text(path)
    if old is None:
        return "NO_BASELINE", 0, 0, ("not tracked at HEAD, so there is no baseline to "
                                     "compare against. Not a pass")
    old_lines = old.splitlines()
    new_lines = new_text.splitlines()
    import difflib
    sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    added = removed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            removed += i2 - i1
        if tag in ("replace", "insert"):
            added += j2 - j1
    if removed > added:
        return ("REFUSE", added, removed,
                "this write REMOVES %d line(s) and ADDS %d. A rebuild that deletes more "
                "than it adds destroys the material that makes a page checkable -- "
                "withdrawal reasons, sources, risk-of-bias verdicts -- and leaves an "
                "object that still validates" % (removed, added))
    return "OK", added, removed, "net addition"


def guard_write(path, new_text, allow_net_deletion=None, encoding="utf-8"):
    """Write only if the delta is a net addition, or the caller says why not."""
    verdict, added, removed, note = assess(path, new_text)
    if verdict == "REFUSE" and not allow_net_deletion:
        raise RebuildRefused(
            "REFUSING to write %s: %s. If this is deliberate, pass "
            "allow_net_deletion='<why>' and the reason will be printed with the write."
            % (os.path.basename(path), note))
    io.open(path, "w", encoding=encoding, newline="").write(new_text)
    if verdict == "REFUSE":
        print("  OVERRIDE: wrote %s (-%d/+%d) -- %s"
              % (os.path.basename(path), removed, added, allow_net_deletion))
    else:
        print("  wrote %s (-%d/+%d) %s" % (os.path.basename(path), removed, added,
                                           "" if verdict == "OK" else "[" + verdict + "]"))
    return verdict


def selftest() -> int:
    ok = True
    import tempfile
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # a tracked file with a known baseline
    target = os.path.join(repo, "ssot", "PAGE_MAP.json")
    base = _head_text(target)
    if base is None:
        print("  SKIP: no tracked baseline available for the fixture")
        return 0
    lines = base.splitlines()

    cases = [
        ("a write that ADDS lines is allowed",
         "\n".join(lines + ["  \"__fixture__\": \"x\""]), "OK"),
        ("a write that REMOVES more than it adds REFUSES",
         "\n".join(lines[:max(1, len(lines) // 2)]), "REFUSE"),
        ("an untracked path has NO BASELINE and is not a pass",
         "anything", "NO_BASELINE"),
    ]
    for i, (label, text, want) in enumerate(cases):
        p = target if want != "NO_BASELINE" else os.path.join(
            tempfile.gettempdir(), "definitely-not-tracked-%d.json" % i)
        v, a, r, note = assess(p, text)
        good = v == want
        ok &= good
        print("  %-58s -> %-12s (want %-12s) %s  (-%d/+%d)"
              % (label[:58], v, want, "correct" if good else "WRONG", r, a))

    print()
    print("WHAT A FAILURE WOULD LOOK LIKE: the halving case returning OK. That is the")
    print("bococizumab shape exactly -- 152 lines written over 1,626, every gate green.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())
