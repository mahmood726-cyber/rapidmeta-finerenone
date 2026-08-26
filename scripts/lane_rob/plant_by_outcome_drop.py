# -*- coding: utf-8 -*-
"""Plant a dropped `by_outcome` judgement and watch the merge refuse. Then restore and prove
the store never moved.

THE HAZARD THIS IS ABOUT, IN ITS OWN WORDS. The key-loss guard in
`merge_rob_grade_into_objects_2026_08_19.py` exempts `by_outcome` BY DESIGN AND BY NAME,
because a recomputed assessment legitimately replaces itself. That exemption is correct for
an assessment the script produced and catastrophic for one a person made: a re-run would
replace hand-made per-result judgements while PRESERVING the curated prose around them,
leaving an object that still looks hand-made. The regen and merge have been frozen on this
for days.

WHAT LIFTS A FREEZE IS A CONTROL, NOT AN ARGUMENT. Five cases, keyed to a real stored
assessment rather than a fixture, both directions:

  N1  a result DROPPED from the incoming assessment        -> must REFUSE
  N2  a judgement CHANGED in the incoming assessment       -> must REFUSE
  P1  incoming identical to stored                         -> must NOT refuse
  P2  incoming ADDS a new result, changes nothing          -> must NOT refuse
  P3  the topic named in --allow-overwrite                 -> must NOT refuse

P1 and P2 are what stop "always refuse" from passing. A guard that refuses everything is as
useless as one that refuses nothing, and it is the easier of the two to ship by accident.

READ-ONLY, AND PROVEN SO. The store's sha256 is taken before and after and asserted equal.
Nothing here writes to any object; the merge is exercised through `curated_refusal` on an
in-memory copy.
"""
import copy
import glob
import hashlib
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "scripts"))
os.chdir(REPO)
import merge_rob_grade_into_objects_2026_08_19 as M  # noqa: E402

fails = 0


def check(label, got, want):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print("   %-6s %-58s %s" % ("PASS" if ok else "FAIL", label, got))
    if not ok:
        print("            expected %r" % (want,))


def pick():
    """A real topic whose stored by_outcome holds at least two results with judgements."""
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        by = ((obj.get("risk_of_bias") or {}).get("by_outcome")) or {}
        n = sum(1 for per in by.values() if isinstance(per, dict)
                for rec in per.values()
                if isinstance(rec, dict) and (rec.get("domains") or {}))
        if n >= 2:
            return t, p, obj, by
    return None, None, None, None


topic, path, obj, stored = pick()
if not topic:
    sys.exit("REFUSED: no real topic carries two or more stored per-result assessments; "
             "there is nothing to key this control to.")
before = hashlib.sha256(open(path, "rb").read()).hexdigest()
oc0 = sorted(stored)[0]
rid0 = sorted(stored[oc0])[0]
dom0 = sorted((stored[oc0][rid0].get("domains") or {}))[0]
print("CONTROL TOPIC (real, stored): %s" % topic)
print("   store: %s" % path)
print("   %d outcome(s), first result %s / %s, first domain %s"
      % (len(stored), oc0, rid0, dom0))
print("   stored judgement there: %r"
      % (stored[oc0][rid0]["domains"][dom0].get("judgement")))
print("")


def refusal(incoming, allow=()):
    o = copy.deepcopy(obj)
    return M.curated_refusal(o, incoming, topic, allow_overwrite=allow)


# ---- N1: DROP a whole result --------------------------------------------------------
print("N1  a stored result DROPPED from the incoming assessment")
inc = copy.deepcopy(stored)
del inc[oc0][rid0]
r = refusal(inc)
check("the merge REFUSES", r is not None, True)
if r:
    check("the refusal names the dropped result", rid0 in str(r), True)
    print("      %s" % " ".join(str(r).split())[:150])
print("")

# ---- N2: CHANGE a judgement ---------------------------------------------------------
print("N2  a stored judgement CHANGED in the incoming assessment")
inc2 = copy.deepcopy(stored)
cur = inc2[oc0][rid0]["domains"][dom0].get("judgement")
inc2[oc0][rid0]["domains"][dom0]["judgement"] = (
    "LOW" if str(cur).upper() != "LOW" else "HIGH")
r2 = refusal(inc2)
check("the merge REFUSES", r2 is not None, True)
if r2:
    check("the refusal names the domain", dom0 in str(r2), True)
print("")

# ---- P1: identical -------------------------------------------------------------------
print("P1  incoming IDENTICAL to stored -- must not refuse")
check("no refusal", refusal(copy.deepcopy(stored)) is None, True)
print("")

# ---- P2: pure addition ---------------------------------------------------------------
print("P2  incoming ADDS a result and changes nothing -- must not refuse")
inc3 = copy.deepcopy(stored)
inc3.setdefault(oc0, {})["__NEW_RESULT_NOT_PREVIOUSLY_STORED"] = {
    "domains": {dom0: {"judgement": "LOW"}}}
check("no refusal", refusal(inc3) is None, True)
print("")

# ---- P3: explicit authorisation -------------------------------------------------------
print("P3  the drop, with the topic named in --allow-overwrite -- must not refuse")
check("no refusal when authorised", refusal(inc, allow=(topic,)) is None, True)
print("")

# ---- restoration ----------------------------------------------------------------------
after = hashlib.sha256(open(path, "rb").read()).hexdigest()
print("STORE UNMOVED")
check("sha256 before == after", before == after, True)
print("   %s" % before)
print("")
print("ALL CONTROLS HELD" if not fails else "%d CONTROL(S) FAILED" % fails)
if not fails:
    print("")
    print("The merge refuses a dropped judgement and a changed one, does NOT refuse an")
    print("identical or additive re-run, and yields to an explicit per-topic authorisation.")
    print("That is the by_outcome hazard watched failing, on a real stored assessment.")
    print("IT DOES NOT BY ITSELF LIFT THE FREEZE: lifting is Mahmood's call, and this is the")
    print("evidence for it, not the decision.")
raise SystemExit(1 if fails else 0)
