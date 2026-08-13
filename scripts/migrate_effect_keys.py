"""One-time ledger migration: `::effect` -> `::effect_point`.

Cause, recorded because it is the kind that repeats: when state_of was extended
to capture the whole interval, the point estimate's key was RENAMED from
`::effect` to `::effect_point`. The ledger is monotonic by design -- it never
subtracts -- so 47 old-format keys stayed in it, the guard stopped emitting
them, and the pointer-set difference read every one as a vanished cell. Eight
apps went red, including arni-hfref. The gate was not wrong; it was reporting a
schema change nobody had told it about.

The migration is deliberately narrow. A key is renamed ONLY when the value it
holds still equals what the object emits today for the new key. Where they
differ, the rename would bury a real change underneath a schema fix -- which is
exactly the laundering the ledger exists to prevent -- so those are reported and
left alone for adjudication.

Run with --apply to write. Default is a dry run.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "scripts")
import regression_guard as R  # noqa: E402

LEDGER = "evidence/LEDGER.json"
APPLY = "--apply" in sys.argv

led = json.load(open(LEDGER, encoding="utf-8"))
renamed, mismatched, orphaned, collided = [], [], [], []

for app, a in led["apps"].items():
    vals = a.get("values") or {}
    cells = a.get("cells") or []
    old_keys = [k for k in vals if k.endswith("::effect")]
    if not old_keys:
        continue

    path = os.path.join("ssot", app, "%s.json" % app)
    if not os.path.exists(path):
        orphaned.extend((app, k) for k in old_keys)
        continue
    st = R.state_of(json.load(open(path, encoding="utf-8")))

    for k in old_keys:
        new = k + "_point"
        was = vals[k]
        now = st["values"].get(new)
        if new in vals:
            collided.append((k, vals[k], vals[new]))
            continue
        if now is None:
            orphaned.append((app, k))
            continue
        if now != was:
            mismatched.append((k, was, now))
            continue
        if APPLY:
            vals[new] = was
            del vals[k]
            a["cells"] = sorted(set(c for c in cells if c != k) | {new})
            cells = a["cells"]
        renamed.append((k, was))

print("renamed   : %d" % len(renamed))
print("mismatched: %d  (value moved -- NOT migrated, needs adjudication)" % len(mismatched))
print("orphaned  : %d  (no current counterpart -- left in place)" % len(orphaned))
print("collided  : %d  (both keys present -- left in place)" % len(collided))
for k, was, now in mismatched:
    print("  MISMATCH %s  ledger=%s  object=%s" % (k, was, now))
for app, k in orphaned[:8]:
    print("  ORPHAN   %s" % k)
for k, a_, b_ in collided[:8]:
    print("  COLLIDE  %s  old=%s new=%s" % (k, a_, b_))

if APPLY:
    if mismatched or collided:
        print("\nREFUSING to write: a mismatch or collision must be adjudicated first.")
        sys.exit(2)
    json.dump(led, open(LEDGER, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\nwrote %s" % LEDGER)
else:
    print("\ndry run; pass --apply to write")
