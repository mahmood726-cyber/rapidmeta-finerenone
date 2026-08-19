#!/usr/bin/env python3
"""HOW MANY SHIPPED SCREENING REASONS SAY "ITS REGISTERED PRIMARY IS" ABOUT A SECONDARY?

The positional-read lint (scripts/lint_primary_by_position.py) found two screeners that build
`outcomes` as PRIMARY + SECONDARY + OTHER and then quote `outcomes[0]` in an exclusion reason as
"Its registered primary is ...". Concatenation in that order means element zero IS a primary --
FOR ANY TRIAL THAT REGISTERS ONE. For a trial with no `primaryOutcomes`, element zero is a
SECONDARY, and the reason text asserts something false about it in a record we ship as evidence.

    A FINDING IS NOT A MEASUREMENT. The lint proves the shape exists; only this proves whether
    it ever fired, and the honest answer might be zero.

Read from the LOCAL TRANSPORT CACHE only. Trials whose payload is not cached are reported as
NOT_ASSESSABLE and counted separately -- never as clean.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, os.environ.get("RM_CTGOV_CACHE", ".ctgov-raw-cache"))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    # The transport cache is transient and is usually absent; the committed per-topic source
    # snapshots are not. Both are read, and if NEITHER exists the answer is NOT_ASSESSABLE.
    paths = []
    if os.path.isdir(CACHE):
        paths += [os.path.join(CACHE, n) for n in sorted(os.listdir(CACHE))
                  if n.endswith(".json")]
    ssot_dir = os.path.join(REPO, "ssot")
    for topic in sorted(os.listdir(ssot_dir)):
        src = os.path.join(ssot_dir, topic, "sources")
        if os.path.isdir(src):
            paths += [os.path.join(src, n) for n in sorted(os.listdir(src))
                      if n.endswith(".ctgov.json")]
    if not paths:
        print("NOT_ASSESSABLE: no transport cache and no committed source snapshots.")
        print("An absent corpus is NOT a clean one.")
        return 0
    no_primary, with_primary, unreadable = [], 0, 0
    for p in paths:
        name = os.path.basename(p)
        try:
            with io.open(p, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            unreadable += 1
            continue
        ps = (d.get("protocolSection") or {})
        om = ps.get("outcomesModule") or {}
        if not isinstance(om, dict):
            unreadable += 1
            continue
        prim = om.get("primaryOutcomes") or []
        sec = om.get("secondaryOutcomes") or []
        oth = om.get("otherOutcomes") or []
        if not (prim or sec or oth):
            continue                          # no outcomes at all: the screeners short-circuit
        nct = (ps.get("identificationModule") or {}).get("nctId") or name.split("_")[0]
        if prim:
            with_primary += 1
        else:
            no_primary.append((nct, (sec or oth)[0].get("measure", "")[:80]))

    print("TRIALS IN THE TRANSPORT CACHE WITH OUTCOMES REGISTERED")
    print("  with a registered PRIMARY      %5d   element zero IS a primary -- text is true"
          % with_primary)
    print("  with NO registered primary     %5d   element zero is a SECONDARY -- text is FALSE"
          % len(no_primary))
    print("  unreadable / NOT_ASSESSABLE    %5d" % unreadable)
    for nct, m in no_primary[:20]:
        print("     %s  first non-primary rank: %r" % (nct, m))
    if not no_primary:
        print("\nEXPOSURE ZERO IN THE CACHE. The defect shape is real and it did not fire here.")
        print("That is a measurement, not an absolution: the fix stands because the next trial")
        print("with no registered primary would produce a false statement in shipped evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
