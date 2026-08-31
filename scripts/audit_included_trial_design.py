# -*- coding: utf-8 -*-
"""Is every trial a review POOLS actually a randomised trial?

⛔ THE DEFECT THIS EXISTS FOR. A registry screen tested

    if alloc and alloc != "RANDOMIZED": exclude

so an ABSENT allocation field passed. An observational study has no allocation
field because it HAS no allocation, and the test read that absence as consent.
On the dapivirine topic it admitted NCT01618058 -- MTN-015, an observational
cohort of participants who seroconverted during the ring trials -- into a screen
whose declared criterion is "randomised".

⭐ AN ABSENT ALLOCATION IS NOT EVIDENCE OF RANDOMISATION. And it is the MIRROR
of the phase rule rather than a contradiction of it:

    registry phase NA          a LABELLING gap. The sponsor left a field
                               blank; the trial is still a trial. KEEP.
    absent allocation on an    a DESIGN FACT. The study has no allocation
    observational study        because it randomises nobody. EXCLUDE.

Two absent fields, opposite treatment, and what decides it is WHAT THE ABSENCE
DESCRIBES -- not whether the field is empty.

⚠️ AND IT WAS FOUND BY A COUNT DISAGREEING WITH A HELD SET, NOT BY A CHECK.
The screen returned 3 INCLUDEs where the review holds 2. Had it returned 2 by
luck it would have shipped. So the question this module answers is the one that
follows: IF AN ABSENT ALLOCATION PASSED HERE, IT PASSED ELSEWHERE. An
observational cohort inside a randomised-evidence synthesis is a correctness
defect, not screening tidiness.

WHAT IT DOES. For every trial every object POOLS, read the registration and
report its studyType and allocation. Names every contributing trial that is not
recorded as INTERVENTIONAL + RANDOMIZED.

    python scripts/audit_included_trial_design.py [--limit N] [--json OUT]

Network: ClinicalTrials.gov API v2, one call per distinct NCT, cached in memory.
"""
import argparse
import glob
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"

_CACHE = {}


def fetch(nct):
    if nct in _CACHE:
        return _CACHE[nct]
    u = ("https://clinicaltrials.gov/api/v2/studies/%s"
         "?fields=NCTId,StudyType,DesignAllocation,BriefTitle,OverallStatus" % nct)
    r = subprocess.run(["curl", "-sL", "--max-time", "45", "-A", UA, u],
                       capture_output=True)
    try:
        d = json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        d = None
    _CACHE[nct] = d
    return d


def design_of(d):
    ps = (d or {}).get("protocolSection") or {}
    des = ps.get("designModule") or {}
    idm = ps.get("identificationModule") or {}
    st = ps.get("statusModule") or {}
    return {
        "title": idm.get("briefTitle") or "",
        "study_type": (des.get("studyType") or "").upper(),
        "allocation": ((des.get("designInfo") or {}).get("allocation") or "").upper(),
        "status": (st.get("overallStatus") or "").upper(),
    }


def contributing_ncts(canon):
    """Every registration a review actually POOLS, with where it was read from.

    ⚠️ inputs.trials is NOT the same set as the per-trial rows that contribute
    to a pool. A review can hold a trial and not pool it. Both are collected and
    the source is recorded, so a finding can be attributed to the right list."""
    out = {}
    for t in ((canon.get("inputs") or {}).get("trials") or []):
        if isinstance(t, dict) and t.get("nct"):
            out.setdefault(t["nct"], set()).add("inputs.trials")
    bo = ((canon.get("results") or {}) if isinstance(canon.get("results"), dict)
          else {}).get("by_outcome") or {}
    if isinstance(bo, dict):
        for oid, res in bo.items():
            if not isinstance(res, dict):
                continue
            for r in (res.get("per_trial") or []):
                if isinstance(r, dict) and r.get("nct"):
                    out.setdefault(r["nct"], set()).add("per_trial[%s]" % oid)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    files = [f for f in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json")))
             if not f.endswith(".striptest")]
    per_obj = {}
    all_ncts = {}
    for f in files:
        try:
            canon = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(canon, dict):
            continue
        got = contributing_ncts(canon)
        if got:
            per_obj[os.path.basename(f)] = got
            for n, where in got.items():
                all_ncts.setdefault(n, set()).update(where)

    ncts = sorted(all_ncts)
    if a.limit:
        ncts = ncts[:a.limit]
    print("objects with contributing registrations : %d" % len(per_obj))
    print("distinct NCTs to check                  : %d" % len(ncts))
    print()

    designs, unresolved = {}, []
    for i, n in enumerate(ncts, 1):
        d = fetch(n)
        if not d:
            unresolved.append(n)
            continue
        designs[n] = design_of(d)
        if i % 25 == 0:
            print("  %d/%d" % (i, len(ncts)))
        time.sleep(0.12)

    # A contributing trial is SOUND only if the registry records it as an
    # interventional study with a RANDOMIZED allocation. Anything else is named.
    flagged = []
    for name, got in sorted(per_obj.items()):
        for n in sorted(got):
            dz = designs.get(n)
            if not dz:
                continue
            if dz["study_type"] != "INTERVENTIONAL" or dz["allocation"] != "RANDOMIZED":
                flagged.append({
                    "object": name, "nct": n,
                    "where": sorted(got[n]),
                    "study_type": dz["study_type"] or "NOT RECORDED",
                    "allocation": dz["allocation"] or "NOT RECORDED",
                    "status": dz["status"], "title": dz["title"][:110],
                })

    checked = sum(1 for name, got in per_obj.items() for n in got if n in designs)
    print()
    print("REGISTRATIONS CHECKED : %d contributing rows across %d objects"
          % (checked, len(per_obj)))
    print("UNRESOLVED            : %d (named below, not counted as sound)"
          % len(unresolved))
    print()
    print("⛔ CONTRIBUTING TRIALS NOT RECORDED AS INTERVENTIONAL + RANDOMIZED")
    print("   %d of %d" % (len(flagged), checked))
    print()
    objs = sorted({f["object"] for f in flagged})
    for f in flagged:
        print("  %-40s %s" % (f["object"][:40], f["nct"]))
        print("      studyType=%-14s allocation=%-14s %s"
              % (f["study_type"], f["allocation"], f["status"]))
        print("      %s" % f["title"])
        print("      appears in: %s" % ", ".join(f["where"]))
    print()
    print("  OBJECTS AFFECTED: %d of %d" % (len(objs), len(per_obj)))
    for o in objs:
        print("    %s" % o)
    if unresolved:
        print()
        print("  UNRESOLVED (registration not fetched): %s"
              % ", ".join(unresolved[:20]))

    if a.json:
        json.dump({"objects_with_contributing_ncts": len(per_obj),
                   "distinct_ncts": len(ncts),
                   "rows_checked": checked,
                   "unresolved": unresolved,
                   "flagged": flagged,
                   "objects_affected": objs},
                  open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("\n  written %s" % a.json)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
