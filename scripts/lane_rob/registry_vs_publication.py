# -*- coding: utf-8 -*-
"""SWEEP: does the registry's arm size appear in the trial's own publication?

THE CASE THAT PROMPTED IT. We store the Ring Study as 82/1302 versus 61/650, taken from the
registry. Its adjudicated primary publication reports 77/1300 versus 56/650. Pooling the
PUBLICATION counts reproduces the published systematic-review result exactly, 0.71 (0.57-0.89);
pooling ours gives 0.703. The two sources disagree, one of them is adjudicated, and NOTHING ON
THE PAGE RECORDS WHICH WE USED OR WHY.

⇒ That is the partial-repair class one layer up: not a wrong number, but an UNRECORDED CHOICE
between two sources that disagree.

WHAT THIS SWEEP DOES, AND DELIBERATELY DOES NOT DO. It asks one mechanical question per trial:
do the registry's per-arm participant counts appear, as whole numbers, in the publication we
hold? It does NOT decide which source is right, does not re-pool anything, and does not touch a
store. A trial where every registry arm size appears in its paper is consistent on that field;
a trial where one does not is a READING TASK, named.

⚠️ IT IS A SCREENING INSTRUMENT AND ITS FALSE-POSITIVE DIRECTION IS KNOWN. A registry N can be
absent from a paper for innocent reasons -- the paper reports a modified ITT set, a per-protocol
set, or rounds a total -- so ABSENT means "these two documents do not state the same number",
never "the number is wrong". That distinction is the whole point: today we do not even know
which trials disagree.

⛔ THREE KINDS, and every trial lands in exactly one, because a sweep that silently drops the
trials it cannot read reports its own reach as coverage:
  CONSISTENT      every registry arm size appears verbatim in the publication
  DISCREPANT      at least one does not
  NO_REGISTRY_NS  the registry record carries no per-arm counts to compare
"""
import collections
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
import document_kind as DK  # noqa: E402

REG_DIR = r"F:\claude-temp\pend\out\registry_full"
FT_DIR = r"F:\claude-temp\pend\out\fulltext"
OUT = r"F:\claude-temp\pend\out\registry_vs_publication.json"

# Arm sizes below this are not distinctive enough to match on: a two-digit number appears in
# any paper by accident. Reported as a separate arm rather than silently dropped.
MIN_DISTINCTIVE = 100


def registry_arm_counts(nct):
    """Per-arm participants from the flow module. None when the record carries none."""
    p = os.path.join(REG_DIR, nct + ".json")
    if not os.path.exists(p):
        return None
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return None
    flow = ((d.get("resultsSection") or {}).get("participantFlowModule") or {})
    groups = {g.get("id"): g.get("title") for g in (flow.get("groups") or [])}
    counts = {}
    for period in (flow.get("periods") or []):
        for ms in (period.get("milestones") or []):
            if str(ms.get("type", "")).upper() not in ("STARTED", "RANDOMIZED"):
                continue
            for a in (ms.get("achievements") or []):
                gid = a.get("groupId")
                v = a.get("numSubjects")
                if gid and str(v).isdigit():
                    counts.setdefault(gid, int(v))
        if counts:
            break
    if not counts:
        return None
    return [{"group": groups.get(g, g), "n": n} for g, n in sorted(counts.items())]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    fts = {}
    for f in glob.glob(os.path.join(FT_DIR, "*.xml")):
        m = re.match(r"(NCT\d+)_", os.path.basename(f))
        if m:
            fts[m.group(1)] = f
    rows = []
    kinds = collections.Counter()
    for nct in sorted(fts):
        arms = registry_arm_counts(nct)
        if not arms:
            kinds["NO_REGISTRY_NS"] += 1
            rows.append({"nct": nct, "kind": "NO_REGISTRY_NS"})
            continue
        try:
            text = DK.rendered(io.open(fts[nct], encoding="utf-8", errors="replace").read())
        except OSError:
            kinds["NO_REGISTRY_NS"] += 1
            continue
        nums = set(re.findall(r"\b\d{2,7}\b", text.replace(",", "")))
        checked, missing, small = [], [], []
        for a in arms:
            if a["n"] < MIN_DISTINCTIVE:
                small.append(a)
                continue
            checked.append(a)
            if str(a["n"]) not in nums:
                missing.append(a)
        if not checked:
            kinds["NO_REGISTRY_NS"] += 1
            rows.append({"nct": nct, "kind": "NO_REGISTRY_NS",
                         "why": "all registry arm sizes below the distinctive floor"})
            continue
        # ⚠️ STRATIFY BY WHAT THE DOCUMENT IS, OR THE SWEEP MEASURES THE WRONG THING. The
        # first run reported 84.1% DISCREPANT, which is not credible: ARISTOTLE's arm sizes
        # (9120 / 9081) certainly appear in ARISTOTLE's paper. They are absent from the
        # document WE HOLD because that document is a SECONDARY ANALYSIS, and a secondary
        # analysis does not restate the parent trial's randomisation counts.
        #
        # So an "absent" arm size was conflating two entirely different facts: the registry and
        # the publication disagree, versus we are not holding the publication. Only the first
        # is a finding about the trial; the second is a finding about our retrieval, and it is
        # the one this corpus is full of. Caught by implausibility, not by reading the code.
        dk = DK.assess(text)
        if dk["kind"] != "PRIMARY_REPORT":
            kinds["NOT_THE_PRIMARY_REPORT"] += 1
            rows.append({"nct": nct, "kind": "NOT_THE_PRIMARY_REPORT",
                         "doc_kind": dk["kind"], "doc": os.path.basename(fts[nct]),
                         "arms_checked": len(checked), "arms_missing": len(missing)})
            continue
        kind = "DISCREPANT" if missing else "CONSISTENT"
        kinds[kind] += 1
        rows.append({"nct": nct, "kind": kind, "arms_checked": len(checked),
                     "arms_missing": len(missing),
                     "missing": [{"group": m["group"], "registry_n": m["n"]} for m in missing],
                     "arms_below_floor": len(small),
                     "doc": os.path.basename(fts[nct])})
    tot = sum(kinds.values())
    print("")
    print("REGISTRY VERSUS PUBLICATION -- does the registry's arm size appear in the paper?")
    print("")
    print("  trials with a publication we hold        %4d  == the denominator" % tot)
    for k in ("CONSISTENT", "DISCREPANT", "NOT_THE_PRIMARY_REPORT", "NO_REGISTRY_NS"):
        print("     %-16s %4d   %5.1f%%" % (k, kinds[k], 100.0 * kinds[k] / tot if tot else 0))
    npr = kinds["NOT_THE_PRIMARY_REPORT"]
    print("")
    print("  NOT_THE_PRIMARY_REPORT is a finding about our RETRIEVAL, not about the trial:")
    print("  we hold a document for the trial, but not the one that reports its randomisation.")
    comp = kinds["CONSISTENT"] + kinds["DISCREPANT"]
    print("")
    print("  comparable trials                        %4d" % comp)
    if comp:
        print("  of those, DISCREPANT                     %4d   %5.1f%%"
              % (kinds["DISCREPANT"], 100.0 * kinds["DISCREPANT"] / comp))
    print("")
    print("  DISCREPANT trials -- the registry states a number the paper does not:")
    for r in [x for x in rows if x["kind"] == "DISCREPANT"][:20]:
        det = ", ".join("%s=%d" % (m["group"][:22], m["registry_n"]) for m in r["missing"][:3])
        print("     %-14s %d of %d arms absent   %s" % (r["nct"], r["arms_missing"],
                                                        r["arms_checked"], det))
    json.dump(rows, io.open(OUT, "w", encoding="utf-8"), indent=1)
    import provenance as pv
    pv.stamp(OUT, note="registry arm sizes checked against the publication text")
    print("")
    print("  detail -> registry_vs_publication.json")
    print("  ⚠️ ABSENT means the two documents do not state the same number -- never that the")
    print("     number is wrong. Each is a reading task, not a correction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
