"""Prove the three P0s the laptop lane reported, against the real object.

All three came back as false positives on current disk. That result is only
worth anything because each was run as a mutation of the real canonical object
rather than a synthetic stand-in -- two of my own first attempts "reproduced"
a miss that did not exist, because the mutation landed on a dict the guard
never ledgers, and a mutation the guard cannot see is not a defect in the guard.

What the exercise did surface is a coupling that nothing was enforcing:

    check() line ~217:  if now is None or now == was: continue

A ledgered value that VANISHES or goes null is skipped by the value comparison
entirely. That is safe today only because every key written into `values` is
also added to the `cells` pointer set, and the pointer-set difference catches
the drop. Nothing states that dependency, and the day someone adds a value
without a matching pointer, nulling it becomes invisible -- which is exactly
the laundering the value comparison was added to stop.

So it is asserted here rather than assumed.
"""
import copy
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "scripts")
import regression_guard as R  # noqa: E402

OBJ = "ssot/arni-hfref/arni-hfref.json"
base = json.load(open(OBJ, encoding="utf-8"))
rows, allok = [], True


def run(tag, mut, expect):
    global allok
    b = copy.deepcopy(base)
    if mut(b) is False:
        rows.append((tag, "NO TARGET", expect, False))
        allok = False
        return
    led = {"apps": {}}
    R.update_ledger(led, R.state_of(copy.deepcopy(base)), kind="ssot")
    res = R.check(b, led)
    got = res["verdict"]
    ok = got == expect
    allok &= ok
    rows.append((tag, got, expect, ok))


def null_screening_ids(o):
    for r in (o.get("screening") or {}).get("records") or []:
        if isinstance(r, dict) and r.get("nct"):
            r["nct"] = None
            r["pmid"] = None
            return True
    return False


def null_arm_events(o):
    for t in o["inputs"]["trials"]:
        for _oid, bb in (t.get("by_outcome") or {}).items():
            c = bb.get("treatment")
            if isinstance(c, dict) and c.get("events") is not None:
                c["events"] = None
                return True
    return False


def move_ci_high(o):
    for t in o["inputs"]["trials"]:
        for _oid, bb in (t.get("by_outcome") or {}).items():
            e = bb.get("effect") or {}
            if e.get("ci_high") is not None:
                e["ci_high"] = 99.9
                return True
    return False


# The laptop lane's three P0 claims, as it stated them.
run("laptop-P0-3 screening nct/pmid -> null", null_screening_ids, "FAIL")
run("laptop-P0-2 effect.ci_high -> 99.9, point held", move_ci_high, "FAIL")
run("arm events -> null (vanish, not change)", null_arm_events, "FAIL")
run("control: object untouched", lambda o: True, "PASS")

print("%-46s %-9s %-9s" % ("case", "got", "expected"))
for tag, got, exp, ok in rows:
    print("%-46s %-9s %-9s %s" % (tag, got, exp, "correct" if ok else "*** MISS ***"))

# The coupling itself: every valued key must also be a pointer, or a null-out
# of that key is invisible to both halves of check().
st = R.state_of(base)
pointers = set(st["cells"]) | set(st["trials"]) | set(st["citations"]) | set(st["screened"])
orphans = sorted(set(st["values"]) - pointers)
print("\nvalued keys: %d   pointer-backed: %d   ORPHANS: %d"
      % (len(st["values"]), len(st["values"]) - len(orphans), len(orphans)))
for o in orphans[:10]:
    print("   ORPHAN (nulling this is invisible): %s" % o)
allok &= not orphans

print("\nall cases correct and no orphaned values: %s" % allok)
sys.exit(0 if allok else 1)
