r"""Plant the defect the SoF projector claims to catch, in a REAL object.

A green run over the corpus proves the projector ACCEPTS what is there. It
does not prove it would REFUSE what is wrong. Three plants, each in a real
store file, each reverted with the revert proven by sha256:

  A  CELLS REMOVED       an outcome that derives must stop deriving and
                         become NOT_DERIVABLE_NO_2X2 -- named, not blank.
  B  STORE REFUSAL       a withdrawn pool must render the store's own
                         reason, not an absolute effect computed on a pool
                         the store refused.
  C  IDENTITY BROKEN     if the sidecar's trials no longer share a
                         registration with the object, its cells must NOT be
                         used. A matching name is not an identity, and this
                         is the plant that stops that rule rotting.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

from sof_projector import sof_rows  # noqa: E402

results = []


def record(name, expect, ok):
    results.append((name, expect, ok))
    print("    %s: %s" % ("PLANT CAUGHT" if ok else
                          "PLANT MISSED (this check has one reachable "
                          "outcome)", expect))


def state_of(obj, outcome, sidecar=None):
    for r in sof_rows(obj, sidecar):
        if r["outcome"] == outcome:
            return r
    return {}


def load(topic):
    p = os.path.join(ROOT, "ssot", topic, topic + ".json")
    raw = open(p, "rb").read()
    return p, raw, json.loads(raw.decode("utf-8"))


def restore(path, raw):
    with open(path, "wb") as fh:
        fh.write(raw)
    ok = hashlib.sha256(open(path, "rb").read()).hexdigest() == \
        hashlib.sha256(raw).hexdigest()
    print("    restore: %s" % ("BYTE-IDENTICAL" if ok else "*** DIFFERS ***"))
    return ok


def find_derived():
    """FIND a topic/outcome that actually derives, rather than assume one.

    A first version hardcoded covid19-vaccines/symptomatic_covid, which is
    already DECLINED_BY_THE_STORE and never derived at all -- so the plant
    reported MISSED for a projector that was working. A plant must create
    the condition it tests, and here that means starting from a row that is
    genuinely in the state the plant intends to break.
    """
    import glob
    for path in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json"))):
        try:
            obj = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, dict) is False:
            continue
        for r in sof_rows(obj):
            if r["state"] == "DERIVED":
                return os.path.basename(os.path.dirname(path)), r["outcome"]
    return None, None


def main():
    TOPIC, OUTCOME = find_derived()
    if TOPIC is None:
        print("NO DERIVED ROW ANYWHERE -- this run measured the harness, not")
        print("the projector. NO VERDICT.")
        return 2
    print("PLANTING DEFECTS IN A REAL STORE OBJECT (%s / %s)" % (TOPIC, OUTCOME))

    # ---- A: cells removed
    path, raw, obj = load(TOPIC)
    print("\n[A] CELLS REMOVED from %s" % OUTCOME)
    before = state_of(obj, OUTCOME)
    print("    before: state=%s n_studies=%s" % (before.get("state"),
                                                 before.get("n_studies")))
    try:
        mutated = copy.deepcopy(obj)
        for t in mutated["inputs"]["trials"]:
            bo = t.get("by_outcome") or {}
            e = bo.get(OUTCOME)
            if isinstance(e, dict):
                e.pop("control", None)
                e.pop("treatment", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(mutated, fh, indent=1, ensure_ascii=False)
        after = state_of(json.load(open(path, encoding="utf-8")), OUTCOME)
        print("    after : state=%s" % after.get("state"))
        print("    reason: %s" % str(after.get("reason", ""))[:96])
        record("cells removed -> the row declines and NAMES why",
               "state becomes NOT_DERIVABLE_NO_2X2 with a reason and no "
               "participant count",
               before.get("state") == "DERIVED"
               and after.get("state") == "NOT_DERIVABLE_NO_2X2"
               and "n_participants" not in after)
    finally:
        restore(path, raw)

    # ---- B: store refusal
    path, raw, obj = load(TOPIC)
    print("\n[B] STORE REFUSAL planted on %s" % OUTCOME)
    try:
        mutated = copy.deepcopy(obj)
        e = mutated["results"]["by_outcome"][OUTCOME]
        if isinstance(e.get("pooled"), dict) is False:
            e["pooled"] = {}
        e["pooled"]["withdrawn"] = True
        e["pooled"]["withdrawn_reason"] = "PLANTED REFUSAL"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(mutated, fh, indent=1, ensure_ascii=False)
        after = state_of(json.load(open(path, encoding="utf-8")), OUTCOME)
        print("    after : state=%s reason=%r" % (after.get("state"),
                                                  after.get("reason")))
        record("a refused pool gets no absolute effect",
               "state becomes DECLINED_BY_THE_STORE carrying the store's own "
               "reason, with no baseline grid",
               after.get("state") == "DECLINED_BY_THE_STORE"
               and after.get("reason") == "PLANTED REFUSAL"
               and "baseline_grid" not in after)
    finally:
        restore(path, raw)

    # ---- C: identity broken
    print("\n[C] SIDECAR IDENTITY BROKEN")
    path, raw, obj = load(TOPIC)
    side = {"trials": [{"name": "X", "nct": "NCT99999999",
                        "tE": 5, "tN": 100, "cE": 10, "cN": 100},
                       {"name": "Y", "nct": "NCT99999998",
                        "tE": 6, "tN": 100, "cE": 11, "cN": 100}]}
    try:
        mutated = copy.deepcopy(obj)
        for t in mutated["inputs"]["trials"]:
            bo = t.get("by_outcome") or {}
            e = bo.get(OUTCOME)
            if isinstance(e, dict):
                e.pop("control", None)
                e.pop("treatment", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(mutated, fh, indent=1, ensure_ascii=False)
        obj2 = json.load(open(path, encoding="utf-8"))
        after = state_of(obj2, OUTCOME, side)
        print("    sidecar carries cells for 2 trials sharing NO registration")
        print("    after : state=%s" % after.get("state"))
        print("    reason: %s" % str(after.get("reason", ""))[:96])
        record("cells from a name-matched but trial-disjoint sidecar are refused",
               "state stays NOT_DERIVABLE_NO_2X2 and the reason says a "
               "matching name is not an identity",
               after.get("state") == "NOT_DERIVABLE_NO_2X2"
               and "not an identity" in str(after.get("reason", "")))
    finally:
        restore(path, raw)

    print("\n" + "=" * 66)
    print("PLANT SUMMARY")
    bad = 0
    for name, expect, ok in results:
        print("  %-52s %s" % (name[:52], "CAUGHT" if ok else "MISSED"))
        bad += (ok is False)
    print("  %d of %d caught" % (len(results) - bad, len(results)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
