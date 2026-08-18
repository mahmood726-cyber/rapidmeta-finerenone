"""Refuse a commit whose STAGED diff net-deletes from an SSOT object.

WHY THIS IS A HOOK AND NOT A HELPER
    scripts/rebuild_guard.py was written for exactly this defect and committed the day
    before it recurred. It did not fire, because the offending script called
    `io.open(...).write()` instead of `guard_write()`.

        A GUARD THAT MUST BE REMEMBERED IS NOT A GUARD.

    That is the same shape as a harness nothing invokes, a detector no build calls, and
    a repair applied in one of twelve clones: AN AVAILABLE MECHANISM IS NOT AN OPERATIVE
    ONE. A helper anyone can bypass is a suggestion; a hook on the commit path is
    enforcement, and only the second cannot be forgotten.

DETECTION IS A HABIT; PREVENTION IS A FUNCTION CALL; ONLY ONE IS ENFORCEABLE
    Both instances of this defect -- bococizumab, then prevnar15 -- were caught by a
    human reading `git show --stat` and noticing an absurd deletion count. That
    discipline holds exactly as long as attention does. This does not.

WHAT IT CHECKS
    For every staged `ssot/**/*.json`: if the diff removes more lines than it adds, the
    commit is refused. An SSOT object is an accumulating record -- registry reads,
    withdrawal reasons, sources, risk-of-bias verdicts -- and a write that shrinks one is
    almost always a rebuild that replaced it rather than a patch that changed it.

OVERRIDE, deliberately awkward
    Set SSOT_ALLOW_NET_DELETION to a non-empty REASON. It is printed with the refusal
    that it overrides, so the reason is on the record rather than in someone's head.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a net-adding write is correct. A patch that adds a hundred lines and
      quietly changes one value passes this. That is the delta check's job.
    - NOT that every net deletion is wrong. A genuine consolidation trips it, and is
      meant to, so that the person doing it says why out loud.
    - NOTHING about files outside ssot/. Pages, scripts and documents are not covered.

USAGE
    python scripts/ssot_net_deletion_check.py            # check the staged diff
    python scripts/ssot_net_deletion_check.py --selftest
"""
from __future__ import annotations
import io
import os
import subprocess
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def staged_numstat():
    """[(added, removed, path)] for staged ssot json files."""
    out = subprocess.run(["git", "-C", REPO, "diff", "--cached", "--numstat", "--",
                          "ssot/**/*.json", "ssot/*.json"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, r, p = parts
        if a == "-" or r == "-":          # binary
            continue
        rows.append((int(a), int(r), p))
    return rows


def check(rows):
    return [(a, r, p) for a, r, p in rows if r > a]


def main() -> int:
    if "--selftest" in sys.argv:
        cases = [
            ("a net addition passes", [(2471, 42, "ssot/x/x.json")], 0),
            ("a net DELETION refuses", [(203, 2422, "ssot/prevnar15/prevnar15.json")], 1),
            ("equal counts pass", [(5, 5, "ssot/y/y.json")], 0),
            ("mixed: one offender is enough to refuse",
             [(100, 1, "ssot/a/a.json"), (1, 100, "ssot/b/b.json")], 1),
        ]
        ok = True
        for label, rows, want in cases:
            got = 1 if check(rows) else 0
            good = got == want
            ok &= good
            print("  %-52s -> %s (want %s) %s"
                  % (label[:52], got, want, "correct" if good else "WRONG"))
        print()
        print("WHAT A FAILURE WOULD LOOK LIKE: the 203-over-2422 case passing. That is")
        print("the prevnar15 write exactly, and the guard that existed did not stop it")
        print("because it was never called.")
        print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
        return 0 if ok else 1

    offenders = check(staged_numstat())
    if not offenders:
        return 0

    reason = os.environ.get("SSOT_ALLOW_NET_DELETION", "").strip()
    print()
    print("=" * 78)
    print("SSOT NET-DELETION CHECK -- %d staged object(s) shrink" % len(offenders))
    print("=" * 78)
    for a, r, p in offenders:
        print("   -%-6d +%-6d %s" % (r, a, p))
    print()
    print("An SSOT object is an ACCUMULATING record -- registry reads, withdrawal")
    print("reasons, sources, risk-of-bias verdicts. A write that shrinks one is almost")
    print("always a rebuild that REPLACED it rather than a patch that changed it, and")
    print("the material it destroys is exactly what makes the page checkable.")
    print()
    if reason:
        print("OVERRIDDEN: SSOT_ALLOW_NET_DELETION=%r" % reason)
        print("Proceeding, and the reason is on the record.")
        return 0
    print("REFUSED. If this is deliberate, re-run with a reason on the record:")
    print('    SSOT_ALLOW_NET_DELETION="consolidating three blocks into one" git commit ...')
    print()
    print("This happened twice in two days -- bococizumab and prevnar15 -- both times to")
    print("an object holding a day of registry reading, and both times the guard that")
    print("existed was simply not called. Hence a hook rather than a helper.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
