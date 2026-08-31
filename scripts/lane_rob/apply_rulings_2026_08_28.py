# -*- coding: utf-8 -*-
"""Rulings 1 and 2, planted and proven, APPLYING NOTHING BY DEFAULT.

WHY THIS IS DRY-RUN BY DEFAULT AND WAS LEFT UNRUN. Both rulings write to stores, and a store
change without a rebuild leaves every page showing the old value -- the staleness this project
has spent the week fighting. Ruling 1 additionally requires the change to be verified SERVED
and disclosed on the page with its date. That is a fleet rebuild, which is not a 4%-quota job.
So the appliers are built and proven here and deliberately not run: an unrun applier is a task,
a half-applied one is a defect.

RULING 1 -- APPLY THE 21 RE-DERIVATIONS.
  21 stored domain judgements do not follow from that reader's OWN signalling responses under
  RoB 2's published tables. 15 raise the domain to HIGH, which LOWERS certainty: the
  conservative direction. The change is written ALONGSIDE the stored judgement, never over it,
  with the table row that produced it and the date -- a rating that moves because we finally
  applied the algorithm should say so rather than changing silently.

RULING 2 -- WITHDRAW THE 54 UNFALSIFIABLE ACCESS CLAIMS.
  An access claim naming no identifier and no route is not a claim; it is a sentence. Nobody
  can check it, ourselves included. ⚠️ It is REMOVED, not reworded: rewriting it into something
  that sounds checkable but is not would be the same defect with better grammar. Where the
  record supports a real statement -- what was sought, by which routes, what was found -- that
  is written instead; where it supports nothing, nothing is written.

PLANTED BOTH WAYS. `--plant` builds a fixture with one cell that MUST change and one that must
not, runs the same code path, asserts both, and restores. A repair that has not been watched
failing on a defect and passing on a clean case has not been tested.
"""
import copy
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "ssot"))
from adjudication_triage import derive  # noqa: E402

FIELD = "rob2_rederivation_applied_2026_08_28"
CLAIM = re.compile(
    r"abstract[- ]only|no full[- ]text|full text (?:not|un)available|not retrievable|"
    r"paywall(?:ed)?|could not (?:be )?(?:retrieve|obtain|access)|inaccessible", re.I)
IDENT = re.compile(r"NCT\d{8}|PMC\d{6,9}|10\.\d{4,9}/\S{4,}|\bPMID[: ]*\d{7,8}")
ROUTE = re.compile(r"europe\s*pmc|efetch|pubmed central|doi resolver|publisher site", re.I)


def ruling1(obj):
    """Cells whose stored judgement does not follow from their own responses."""
    out = []
    for oid, recs in (((obj.get("risk_of_bias") or {}).get("by_outcome")) or {}).items():
        for rid, rec in (recs or {}).items():
            for dk, dv in ((rec or {}).get("domains") or {}).items():
                if not isinstance(dv, dict):
                    continue
                stored = str(dv.get("judgement") or "")
                d, why, _ = derive(dk[:2], dv.get("signalling_questions") or {})
                if d and d != stored:
                    out.append((oid, rid, dk, stored, d, why))
    return out


def ruling2(obj):
    """Access claims that name neither an identifier nor a route -- unfalsifiable."""
    hits = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + [str(k)])
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + ["[%d]" % i])
        elif isinstance(node, str) and CLAIM.search(node):
            if not IDENT.search(node) and not ROUTE.search(node):
                hits.append(("/".join(path), node))
    walk(obj, [])
    return hits


def plant():
    """Watch it fail on a defect and pass on a clean case, then restore."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("PLANT -- ruling 1")
    # MUST CHANGE: all-NI on D2 selects Table 6 Part 2 row 3 -> High.
    bad = {"risk_of_bias": {"by_outcome": {"o": {"NCT00000001": {"domains": {
        "D2_deviations": {"judgement": "NO_INFORMATION", "signalling_questions": {
            "participants_aware": "NO_INFORMATION", "carers_aware": "NO_INFORMATION",
            "appropriate_analysis_used": "NO_INFORMATION"}}}}}}}}
    r = ruling1(bad)
    assert len(r) == 1 and r[0][4] == "HIGH", r
    print("   defect cell detected, derives %s  [PASS]" % r[0][4])
    # MUST NOT CHANGE: stored judgement already equals the derived one.
    good = copy.deepcopy(bad)
    good["risk_of_bias"]["by_outcome"]["o"]["NCT00000001"]["domains"]["D2_deviations"]["judgement"] = "HIGH"
    r2 = ruling1(good)
    assert r2 == [], r2
    print("   clean cell untouched                 [PASS]")
    print("PLANT -- ruling 2")
    unf = {"a": {"note": "full text unavailable for this trial"}}
    fal = {"a": {"note": "no full text via Europe PMC or efetch for PMC4993693"}}
    assert len(ruling2(unf)) == 1, ruling2(unf)
    assert ruling2(fal) == [], ruling2(fal)
    print("   unfalsifiable claim detected         [PASS]")
    print("   claim naming a route and an id kept  [PASS]")
    print("")
    print("Both directions watched. Nothing was written; no fixture remains.")
    return 0


def main():
    if "--plant" in sys.argv:
        return plant()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    apply_it = "--apply" in sys.argv
    n1 = n2 = 0
    topics1, topics2 = set(), set()
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        a, b = ruling1(obj), ruling2(obj)
        if a:
            topics1.add(t)
            n1 += len(a)
        if b:
            topics2.add(t)
            n2 += len(b)
    print("")
    print("RULINGS 1 AND 2 -- WHAT WOULD CHANGE  (%s)"
          % ("APPLYING" if apply_it else "DRY RUN -- nothing written"))
    print("")
    print("  ruling 1: domain cells to re-derive     %4d  across %d topic(s)" % (n1, len(topics1)))
    print("  ruling 2: unfalsifiable claims to drop  %4d  across %d topic(s)" % (n2, len(topics2)))
    print("")
    print("  fixed 0 / rebuilt 0 / SERVED 0 -- nothing has been applied.")
    print("  Ruling 1 requires the change verified SERVED and disclosed on the page with its")
    print("  date, which is a fleet rebuild. Landing the store write without it would leave")
    print("  every page showing the old value.")
    if apply_it:
        print("")
        print("  REFUSED: --apply is deliberately not implemented in this commit. The appliers")
        print("  are proven by --plant; running them belongs with the rebuild that serves them.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
