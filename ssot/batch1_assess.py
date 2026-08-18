"""Run the seven preconditions over batch 1, produce the refusal list, and reconcile trials.

THREE OUTPUTS, and they are kept apart on purpose:

  1. PRECONDITION MATRIX -- 8 topics x 7 preconditions, every cell PASS / FAIL /
     NOT-ASSESSABLE with its reason. All three states are reported; none is collapsed.

  2. REFUSAL LIST -- a topic failing any precondition does not build. FAIL and
     NOT-ASSESSABLE are recorded SEPARATELY: a topic that cannot be assessed has not been
     judged, and merging it into the refused set is the substitution this whole session is
     about. Both block the build; only one is a finding about the topic.

  3. RECONCILIATION -- old k (registration ids in the object) against new k (ids the
     executed search surfaced and the cascade roled), keyed on NCT. Nothing silently added,
     nothing silently dropped. A candidate that DISAPPEARS because a check got stricter is
     reported with the same weight as one that appears, and with the reason it went.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import preconditions as P
from assessment import FAIL, NOT_ASSESSABLE, PASS

ROOT = os.path.dirname(os.path.abspath(__file__))
CASCADE = os.path.join(os.path.dirname(ROOT), "evidence", "2026-08-19-batch1", "cascade.json")

NCT = re.compile(r"\bNCT\d{8}\b")

BATCH1 = ["ablation-af-review", "alirocumab-lipid", "apixaban-vte", "attr-cm-review",
          "azilsartan-chlorthalidone-vs-olmesartan-hctz", "bempedoic-acid-review",
          "bococizumab-lipid-review", "bosentan-pah"]


def included_ncts(obj):
    """The INCLUDED set: inputs.trials[].nct. Not a regex over the document.

    THE FIRST VERSION OF THIS SWEPT EVERY NCT STRING ANYWHERE IN THE OBJECT, and that is
    wrong in a specific and instructive way: an object records the trials it REMOVED as well
    as the ones it included. `alirocumab-lipid` carries

        removed_citations.categories[] = {"reason": "placeholder registration",
                                          "detail": "NCT12345678 is not a registration
                                                     number. It resolves to nothing."}

    A whole-document regex counted that placeholder -- and five other already-removed
    citations -- as part of the object's old k, then reported them as trials that
    "disappeared". The object had done the removal correctly and documented it; the
    reconciliation was reading its audit trail as its contents.

    Same family as the unit-of-analysis error: the count ran over the wrong unit. An
    object's record of what it excluded is not what it included.
    """
    out = []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        nct = t.get("nct")
        if isinstance(nct, str) and NCT.fullmatch(nct.strip()):
            out.append(nct.strip())
    return set(out)


def removed_ncts(obj):
    """What the object says it REMOVED, reported separately so it is never a disappearance."""
    out = set()
    rc = obj.get("removed_citations")
    if isinstance(rc, dict):
        for cat in (rc.get("categories") or []):
            for v in (cat or {}).values():
                if isinstance(v, str):
                    out.update(NCT.findall(v))
    return out


def load_object(topic_dir):
    path = os.path.join(ROOT, topic_dir, f"{topic_dir}.json")
    if not os.path.exists(path):
        return None, f"object absent at {path}"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except (ValueError, OSError) as exc:
        # An unreadable object is NOT_ASSESSABLE for every precondition. It is never FAIL.
        return None, f"{type(exc).__name__}: {exc}"


with open(CASCADE, "r", encoding="utf-8") as fh:
    cascade = json.load(fh)

objects, unreadable = {}, {}
for d in BATCH1:
    obj, err = load_object(d)
    if obj is None:
        unreadable[d] = err
    else:
        objects[d] = obj

matrix, alarms = P.REGISTRY.run(objects)
alarms = alarms or []

report = {"authority_publishable": P.verdict_is_publishable(),
          "detector4_alarms": alarms, "topics": {}}

for d in BATCH1:
    entry = {"topic": d}
    if d in unreadable:
        entry["object_state"] = "UNREADABLE"
        entry["detail"] = unreadable[d]
        entry["verdicts"] = {n: [NOT_ASSESSABLE, f"cannot assess: {unreadable[d]}"]
                             for n in P.SEVEN}
    else:
        entry["object_state"] = "READ"
        entry["verdicts"] = {n: list(matrix[n][d]) for n in P.SEVEN}

    states = [entry["verdicts"][n][0] for n in P.SEVEN]
    entry["n_pass"] = states.count(PASS)
    entry["n_fail"] = states.count(FAIL)
    entry["n_not_assessable"] = states.count(NOT_ASSESSABLE)
    entry["failed_preconditions"] = [n for n in P.SEVEN
                                     if entry["verdicts"][n][0] == FAIL]
    entry["unassessable_preconditions"] = [n for n in P.SEVEN
                                           if entry["verdicts"][n][0] == NOT_ASSESSABLE]
    entry["builds"] = (entry["n_fail"] == 0 and entry["n_not_assessable"] == 0)

    # --- reconciliation, keyed on registration id ---------------------------------------
    old = included_ncts(objects[d]) if d in objects else set()
    already_removed = removed_ncts(objects[d]) if d in objects else set()
    c = cascade.get(d, {})
    roles = c.get("roles") or {}
    surfaced = set(roles)
    experimental = set(c.get("experimental_ids") or [])
    comparator = set(c.get("comparator_ids") or [])
    not_assessable_ids = set(c.get("not_assessable_ids") or [])

    disappeared = []
    for nct in sorted(old - experimental):
        if nct in comparator:
            why = "STRICTER CHECK: topic drug resolves to the COMPARATOR arm, not the intervention"
        elif nct in not_assessable_ids:
            why = "NOT_ASSESSABLE: role could not be located -- NOT excluded, unclassified"
        elif nct in surfaced:
            why = f"surfaced but roled {roles[nct]['role']}"
        else:
            why = "NOT SURFACED by the executed search under its named intervention"
        disappeared.append({"nct": nct, "reason": why})

    entry["reconciliation"] = {
        "old_k_by_nct": len(old),
        "old_ids": sorted(old),
        "already_removed_by_object": sorted(already_removed),
        "n_already_removed": len(already_removed),
        "new_k0_surfaced": c.get("k0_surfaced_raw"),
        "new_k3_experimental": c.get("k3_experimental"),
        "kept": sorted(old & experimental),
        "disappeared": disappeared,
        "appeared_experimental": sorted(experimental - old),
        "n_disappeared": len(disappeared),
        "n_appeared": len(experimental - old),
    }
    report["topics"][d] = entry

out = os.path.join(os.path.dirname(ROOT), "evidence", "2026-08-19-batch1", "assess.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)

# ---------------------------------------------------------------------------
print("PRECONDITION MATRIX -- P=pass F=fail N=not-assessable")
hdr = "".join(f"{n[:11]:>13}" for n in P.SEVEN)
print(f"{'topic':<46}{hdr}")
for d in BATCH1:
    e = report["topics"][d]
    row = "".join(f"{ {PASS: 'P', FAIL: 'F', NOT_ASSESSABLE: 'N'}[e['verdicts'][n][0]] :>13}"
                  for n in P.SEVEN)
    print(f"{d:<46}{row}")

print()
print("BUILD DECISION")
builds = [d for d in BATCH1 if report["topics"][d]["builds"]]
refused_fail = [d for d in BATCH1 if report["topics"][d]["n_fail"] > 0]
refused_na = [d for d in BATCH1
              if report["topics"][d]["n_fail"] == 0 and report["topics"][d]["n_not_assessable"] > 0]
print(f"  BUILD                     {len(builds)}  {builds}")
print(f"  REFUSED (a real FAIL)     {len(refused_fail)}")
print(f"  BLOCKED (NOT-ASSESSABLE)  {len(refused_na)}   <- not judged; a different state")

print()
print("WHICH PRECONDITION BIT, per topic")
for d in BATCH1:
    e = report["topics"][d]
    if e["failed_preconditions"]:
        for n in e["failed_preconditions"]:
            print(f"  {d:<46} FAIL {n}")
            print(f"  {'':<46}      {e['verdicts'][n][1][:120]}")
    if e["unassessable_preconditions"]:
        print(f"  {d:<46} N/A  {', '.join(e['unassessable_preconditions'])}")

print()
print("PER-PRECONDITION TALLY across the batch")
for n in P.SEVEN:
    st = [report["topics"][d]["verdicts"][n][0] for d in BATCH1]
    print(f"  {n:<30} PASS {st.count(PASS)}  FAIL {st.count(FAIL)}  N/A {st.count(NOT_ASSESSABLE)}")

print()
print("RECONCILIATION -- keyed on registration id")
print(f"{'topic':<46}{'old k':>6}{'kept':>6}{'gone':>6}{'new exp':>9}{'appeared':>10}")
for d in BATCH1:
    r = report["topics"][d]["reconciliation"]
    print(f"{d:<46}{r["old_k_by_nct"]:>6}{len(r['kept']):>6}{r['n_disappeared']:>6}"
          f"{r['new_k3_experimental'] or 0:>9}{r['n_appeared']:>10}")

print()
print("DISAPPEARANCES, each with its reason -- nothing silently dropped")
for d in BATCH1:
    for x in report["topics"][d]["reconciliation"]["disappeared"]:
        print(f"  {d:<40} {x['nct']}  {x['reason']}")

print()
print(f"detector-4 alarms: {alarms or 'none'}")
print(f"AUTHORITY PUBLISHABLE: {report['authority_publishable']}  "
      f"(False = no topic may be refused on Handbook grounds yet)")
print(f"\nwrote {out}")
