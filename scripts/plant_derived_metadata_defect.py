"""Plant a defect in the derived dashboard metadata and watch it fail.

A counter that is DERIVED cannot be trusted merely because it is derived. The
question is whether it MOVES when the rows move, and by how much. A derivation
that silently ignored ssot_state would print 19 for every input and look
identical to a correct one on the clean case.

So each plant states the expected delta BEFORE perturbing, and the clean
sibling must return the original value. Nothing is written to disk: the
snapshot is loaded, copied, and perturbed in memory.
"""
import copy
import importlib.util
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "pdi", os.path.join(REPO, "scripts", "project_dashboard_index.py"))
pdi = importlib.util.module_from_spec(spec)
src = open(spec.origin, encoding="utf-8").read().split("\nif __name__")[0]
exec(compile(src, spec.origin, "exec"), pdi.__dict__)

with io.open(pdi.SNAP, "r", encoding="utf-8") as fh:
    ORIGINAL = json.load(fh)
with io.open(pdi.PMAP, "r", encoding="utf-8") as fh:
    PMAP = json.load(fh)


def measured(snap):
    s = copy.deepcopy(snap)
    pdi.project(s, PMAP)
    derived, _ = pdi.derive_metadata(s)
    return derived


BASE = measured(ORIGINAL)
print("CLEAN SIBLING (the unperturbed snapshot)")
for k in pdi.DERIVED_KEYS:
    print("   %-24s %4d" % (k, BASE[k]))

fails = []


def plant(name, mutate, key, delta):
    """mutate() perturbs a copy; key must move by exactly delta and nothing else."""
    s = copy.deepcopy(ORIGINAL)
    mutate(s)
    got = measured(s)
    want = BASE[key] + delta
    ok = got[key] == want
    other = [k for k in pdi.DERIVED_KEYS
             if k != key and got[k] != BASE[k]]
    print("\nPLANT %s" % name)
    print("   %-24s %4d -> %4d   expected %d   %s"
          % (key, BASE[key], got[key], want, "PASS" if ok else "FAIL"))
    if other:
        print("   also moved (stated, not hidden): %s"
              % ", ".join("%s %d->%d" % (k, BASE[k], got[k]) for k in other))
    if not ok:
        fails.append(name)
    return got


def flip_one_live_to_unmapped(s):
    """A live row loses its object. n_total must fall by exactly one."""
    for r in s["rows"]:
        page = r.get("file")
        st, _ = pdi.object_state(page, PMAP)
        if st == pdi.LIVE:
            # remove it from the page map so the projector re-derives UNMAPPED
            PMAP.get("pages", PMAP).pop(page, None)
            r["_planted"] = page
            return
    raise SystemExit("no LIVE row to plant against")


def add_synthetic_nma(s):
    """A synthetic LIVE NMA row. n_nma is 0 on the real corpus, so a counter
    that hardcoded or mis-keyed it would still read 0 here."""
    live = next(r for r in s["rows"] if pdi.object_state(r.get("file"), PMAP)[0] == pdi.LIVE)
    clone = copy.deepcopy(live)
    clone["file"] = live["file"]
    clone["type"] = "NMA"
    clone["topic"] = "__CONTROL_synthetic_nma"
    s["rows"].append(clone)


def drop_a_row(s):
    s["rows"] = [r for r in s["rows"]
                 if pdi.object_state(r.get("file"), PMAP)[0] != pdi.LIVE][:] + \
                [r for r in s["rows"]
                 if pdi.object_state(r.get("file"), PMAP)[0] == pdi.LIVE][1:]


plant("synthetic LIVE NMA row appended", add_synthetic_nma, "n_nma", +1)
plant("one LIVE row removed", drop_a_row, "n_total", -1)

# this one mutates PMAP, so it runs last and PMAP is reloaded afterwards
saved = copy.deepcopy(PMAP)
plant("a LIVE page loses its SSOT object", flip_one_live_to_unmapped, "n_total", -1)
PMAP.clear()
PMAP.update(saved)

print("\nRESTORE")
again = measured(ORIGINAL)
same = all(again[k] == BASE[k] for k in pdi.DERIVED_KEYS)
print("   clean sibling reproduces after every plant: %s" % ("PASS" if same else "FAIL"))
if not same:
    fails.append("restore")

on_disk = json.load(io.open(pdi.SNAP, "r", encoding="utf-8"))
untouched = on_disk == ORIGINAL
print("   snapshot on disk untouched by this script:  %s"
      % ("PASS" if untouched else "FAIL"))
if not untouched:
    fails.append("disk")

print("\n%s" % ("ALL PLANTS FAILED THE DERIVATION AS INTENDED, AND THE CLEAN CASE PASSED"
                if not fails else "PLANTS DID NOT BEHAVE: %s" % fails))
sys.exit(1 if fails else 0)
