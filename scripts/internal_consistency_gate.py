"""Three internal-consistency checks. No registry calls; everything is already on the object.

ALL THREE HAVE CONCRETE SPECIFICATIONS FROM AN OUTSIDE REVIEW. Codex, given four rebuilt
objects cold, found each of these by reading fields against each other -- which is the only
way any of them is visible, because every field involved is individually valid.

  ELIGIBILITY vs k
      cangrelor-pci-review: `eligible_but_not_contributing.note` says "All three included
      registrations contribute", and the corrected headline pool is k=2 having dropped
      CHAMPION-PHOENIX -- stated three fields away in the same object. A reader trusting the
      eligibility field is told nothing was dropped.

  COMPARATOR vs the object's own prose
      azilsartan: title and question say "against olmesartan medoxomil plus
      hydrochlorothiazide", `poolable_reason` says both trials "share BOTH arms", and
      `outcomes[0].comparator` is null with comparator_type "not applicable". I WROTE THOSE
      MARKERS MYSELF to get a build through. THE NULL COMPARATOR MAKES AN ACTIVE-COMPARATOR
      REVIEW LOOK NONCOMPARATIVE.

  SIBLING FIELDS, PROPERLY SCOPED
      The first attempt compared every object of a kind against every other and flagged 14
      when 3 were real -- because the schema GREW UNVERSIONED and older objects carry fields
      newer ones were never built to hold. Comparing across generations reports NEWER AND
      THINNER as DEGRADED. Scoping on the `built` date failed too: every object reads
      2026-08. THIS VERSION SCOPES ON SIBLINGS-IN-PURPOSE -- objects sharing a kind AND a
      generator signature -- and reports only fields carried by every sibling but one.

WHY THESE THREE AND WHY NOW. Three defects were found in same-day work tonight, each
invisible when built and obvious once its check existed. BUILDING THE NEXT COHORT AHEAD OF
ITS CHECKS GUARANTEES THE NEXT COHORT'S CHECKS FIND DEFECTS IN IT. These run as
PRECONDITIONS, not as a later sweep.

REPORTS ONLY. Every finding is a contradiction between two fields, and which one is wrong
is a reading, never a computation.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from text_match import norm  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NONE_MARKERS = ("not applicable", "none", "n/a", "")
ACTIVE_HINT = re.compile(
    r"\bversus\b|\bvs\.?\b|\bagainst\b|\bcompared with\b|\bcompared to\b", re.I)


def contributing(blk):
    rows = [r for r in (blk.get("per_trial") or []) if isinstance(r, dict)]
    return [r for r in rows
            if not str(r.get("trial_id", "")).startswith(("NULLED:", "EXCLUDED:"))]


def main() -> int:
    ss = os.path.join(REPO, "ssot")
    elig, comp, sib = [], [], []
    objs = {}
    for d in sorted(os.listdir(ss)):
        f = os.path.join(ss, d, d + ".json")
        if not os.path.exists(f):
            continue
        try:
            o = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        objs[d] = o

        for name, blk in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            k = blk.get("k")
            rows = contributing(blk)

            # 1. ELIGIBILITY vs k
            eb = blk.get("eligible_but_not_contributing")
            note = ""
            if isinstance(eb, dict):
                note = str(eb.get("note") or "")
                studies = eb.get("studies")
                n_named = len(studies) if isinstance(studies, list) else 0
            elif isinstance(eb, list):
                n_named, note = len(eb), ""
            else:
                n_named = None
            if n_named is not None and isinstance(k, int):
                claims_none = bool(re.search(r"all .{0,24}contribute|no trial is in this",
                                             note, re.I)) or n_named == 0
                total = len([r for r in (blk.get("per_trial") or [])
                             if isinstance(r, dict)])
                dropped = (total - k) if total >= k else 0
                # a page may legitimately seed more trials than it pools
                seeded = len(((o.get("inputs") or {}).get("trials") or []))
                if claims_none and (dropped > 0 or (seeded and seeded > max(k, total))):
                    elig.append((d, name, k, total, seeded, note[:60]))

            # 2. COMPARATOR vs prose
            prose = " ".join([str(o.get("title") or ""), str(o.get("question") or ""),
                              str(blk.get("poolable_reason") or "")])
            for oc in (o.get("outcomes") or []):
                if not isinstance(oc, dict):
                    continue
                c = norm(oc.get("comparator"))
                if c in NONE_MARKERS and ACTIVE_HINT.search(prose):
                    if (blk.get("pooled") or {}).get("point") is not None:
                        comp.append((d, oc.get("id"), prose.strip()[:70]))
                    break

    # 3. SIBLING FIELDS, scoped to siblings-in-purpose
    groups = {}
    for d, o in objs.items():
        bo = (o.get("results") or {}).get("by_outcome") or {}
        blk = bo.get("primary") or (list(bo.values())[0] if bo else {})
        if not isinstance(blk, dict):
            continue
        kind = "pooled" if (blk.get("pooled") or {}).get("point") is not None else "verdict"
        sig = "has_render" if "render" in o else "no_render"
        groups.setdefault((kind, sig), {})[d] = set(o.keys())
    for key, members in groups.items():
        n = len(members)
        if n < 5:
            continue
        counts = {}
        for fs in members.values():
            for f in fs:
                counts[f] = counts.get(f, 0) + 1
        # ONLY fields every sibling but one carries -- a single absence is a signal,
        # a scattered one is schema drift
        expected = {f for f, c in counts.items() if c == n - 1}
        for d, fs in sorted(members.items()):
            miss = sorted(expected - fs)
            if miss:
                sib.append((d, "%s/%s" % key, miss))

    print("=== 1. ELIGIBILITY FIELD CONTRADICTS k: %d" % len(elig))
    for d, name, k, total, seeded, note in elig:
        print("   %-38s %-14s k=%d rows=%d seeded=%d" % (d[:37], name[:13], k, total, seeded))
        print("        note: %r" % note)
    print()
    print("=== 2. NULL COMPARATOR ON AN ACTIVE-COMPARATOR REVIEW: %d" % len(comp))
    for d, oid, prose in comp:
        print("   %-38s outcomes[%s].comparator is null" % (d[:37], oid))
        print("        prose says: %r" % prose)
    print()
    print("=== 3. FIELD ABSENT FROM EXACTLY ONE SIBLING-IN-PURPOSE: %d" % len(sib))
    for d, g, miss in sib[:14]:
        print("   %-38s [%s] missing %s" % (d[:37], g, ", ".join(miss)[:44]))
    print()
    print("REPORTS ONLY. Each finding is two fields disagreeing, and WHICH ONE IS WRONG IS")
    print("A READING, NEVER A COMPUTATION. All three were specified by an outside review")
    print("that read fields against each other -- the only way any of them is visible,")
    print("because every field involved is individually valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
