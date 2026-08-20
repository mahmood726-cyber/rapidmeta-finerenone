"""DRY RUN ONLY. What would re-keying the exclusion baseline cost, and would it collide?

WHY THIS IS NOT THE MIGRATION. `scripts/baselines/exclusion_by_absence_baseline.json` keys
130 guards on `file:line`. That key DOES NOT IDENTIFY THE THING IT NAMES: a six-line
docstring added above a guard shifts it, and the same unchanged guard re-reads as NEW while
its old key vanishes as HEALED. It happened to nine guards in one edit, and TWICE to me
tonight -- lines 67 -> 87 and 103 -> 109, neither a change of logic.

The stated remedy is to key on the GUARD TEXT plus its ENCLOSING FUNCTION. The risk of
doing that live is total: if the computed key differs at all from what a future run
computes, every entry re-reads as NEW and the gate blocks every commit. So this measures
the migration WITHOUT PERFORMING IT.

    WRITES NOTHING. Opens the baseline read-only, computes what the new keys would be, and
    reports how many entries would resolve, how many are already stale, and whether any two
    guards would collide onto one key.

RUN 2026-08-20, AND THE RISK DID NOT MATERIALISE. 130 of 130 entries resolve to a live
guard, 0 are stale, 130 live guards produce 130 distinct new keys, 0 collide, and 0 would be
forgotten. THE MIGRATION IS LOSSLESS ON TODAY'S CORPUS.

It is deliberately still unwritten. What this changes is that the next person meets a
MEASURED DECISION rather than an open question: the thing that made it risky was never the
work, it was not knowing whether the ratchet would silently shrink. It would not.

A COLLISION IS THE FAILURE THAT MATTERS. `file:line` is unique by construction; text plus
function is not. Two identical `if not x: continue` guards in one function would become one
key, and the baseline would silently forget one of them -- turning a ratchet into a smaller
ratchet, which is the direction that never announces itself.
"""
import ast
import io
import json
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402
import audit_exclusion_by_absence as AX                   # noqa: E402

BASELINE = os.path.join(REPO, "scripts", "baselines",
                        "exclusion_by_absence_baseline.json")


def enclosing_functions(path):
    """line number -> innermost enclosing function name, or '<module>'."""
    try:
        tree = ast.parse(io.open(path, encoding="utf-8").read())
    except Exception:                                      # noqa: BLE001
        return {}
    span = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                # innermost wins: a later, narrower span overwrites a wider one
                prev = span.get(ln)
                if prev is None or (node.end_lineno - node.lineno) < prev[1]:
                    span[ln] = (node.name, node.end_lineno - node.lineno)
    return dict((ln, v[0]) for ln, v in span.items())


def new_key(rel, fn, text):
    return "%s::%s::%s" % (rel, fn, " ".join(text.split()))


def main():
    require_controls(
        "dryrun_rekey_exclusion_baseline",
        positive=("two guards with the same text in the same function collide on one key",
                  new_key("a.py", "f", "if not x:") == new_key("a.py", "f", "if not  x:"),
                  True),
        negative=("guards in DIFFERENT functions collide",
                  new_key("a.py", "f", "if not x:") == new_key("a.py", "g", "if not x:"),
                  True))

    if not os.path.exists(BASELINE):
        print("NOT_ASSESSABLE: no baseline at %s." % os.path.relpath(BASELINE, REPO))
        return 2
    base = json.load(io.open(BASELINE, encoding="utf-8"))
    known = list(base.get("guards") or [])

    # Every guard the sweep sees RIGHT NOW, keyed both ways.
    subset = AX.corpus_wide_subset()
    fnmap = {}
    live_old, live_new = {}, {}
    for rel, lineno, _loop, text in subset:
        path = os.path.join(REPO, rel.replace("/", os.sep))
        if rel not in fnmap:
            fnmap[rel] = enclosing_functions(path)
        fn = fnmap[rel].get(lineno, "<module>")
        old = "%s:%d" % (rel, lineno)
        live_old[old] = new_key(rel, fn, text)
        live_new.setdefault(new_key(rel, fn, text), []).append(old)

    resolved = [k for k in known if k in live_old]
    stale = [k for k in known if k not in live_old]
    collisions = dict((k, v) for k, v in live_new.items() if len(v) > 1)

    print("")
    print("BASELINE ENTRIES:                 %d" % len(known))
    print("guards the sweep sees now:        %d" % len(subset))
    print("")
    print("entries that RESOLVE to a live guard at their line:  %d of %d"
          % (len(resolved), len(known)))
    print("entries ALREADY STALE -- no guard at that line now:  %d of %d"
          % (len(stale), len(known)))
    for k in stale[:12]:
        print("      %s" % k)
    if len(stale) > 12:
        print("      ... and %d more" % (len(stale) - 12))

    print("")
    print("WOULD ANY TWO GUARDS COLLIDE ONTO ONE NEW KEY?")
    print("distinct new keys for %d live guards: %d" % (len(subset), len(live_new)))
    print("colliding new keys:  %d" % len(collisions))
    for k, v in list(collisions.items())[:10]:
        print("      %-70s <- %s" % (k[:70], ", ".join(v)))

    print("")
    lost = len(subset) - len(live_new)
    print("GUARDS THE RATCHET WOULD SILENTLY FORGET UNDER THE NEW KEY: %d of %d"
          % (lost, len(subset)))
    print("")
    print("WRITES NOTHING. This is the measurement, not the migration. The decision it")
    print("informs is whether re-keying is trivial (no collisions, few stale) or whether it")
    print("would shrink the ratchet -- and shrinking is the direction that never announces")
    print("itself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
