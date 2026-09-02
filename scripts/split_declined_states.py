r"""Split DECLINED_BY_THE_STORE: which refusals are CONTENT and which are HOLES.

THE RULING THIS IMPLEMENTS
    A decline because the studies do not address the same question is a
    FINDING -- and it is our dominant output, one no open-access
    meta-analysis publishes. A decline because a field was missing is a HOLE
    wearing a refusal's clothes. Counting them together would let a
    corpus-wide data gap render as corpus-wide achievement.

THE SPLIT IS MECHANICAL, NOT A READING OF THE PROSE
    Classifying 142 free-text reasons by keyword would be an unanchored
    substring match over prose, which is this repository's commonest defect.
    So the test is structural: DOES THE REASON CITE THE EVIDENCE?

      REFUSED_ON_A_STATED_METHODOLOGICAL_GROUND
          the reason names at least one trial registration (NCT########) or
          cites a named authority. A refusal that points at specific
          registered trials is a statement about the evidence, and a reader
          can go and check it.

      REFUSED_WITHOUT_A_RECORDED_REASON
          the stored reason is the fallback string. The refusal may be
          right; nothing is published about why. Not content.

      UNCLASSIFIED_DECLINE
          a substantive-looking reason that cites no registration and no
          authority. NOT counted as content, listed by name so a human can
          rule on each. Forcing these into either bucket is how a hole gets
          counted as a finding.

    Only the first is content. The other two are reported and NOT counted,
    and both metrics are printed side by side so neither travels alone.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

from absolute_effects import _file_kind  # noqa: E402
from sof_projector import sof_rows  # noqa: E402
from absolute_effects_sidecar import candidate_topics  # noqa: E402

# The projector takes the topic's sidecar as a fallback source of cells.
# Omitting it here reported DERIVED=2 where the projector gives 21 -- two
# different numbers for the same quantity, from the same module, in one
# session. The sidecar must be passed wherever sof_rows is called.
_SIDE = {os.path.basename(q)[:-5]
         for q in glob.glob(os.path.join(ROOT, "outputs", "r_validation",
                                         "*.json"))
         if os.path.basename(q).startswith("_") is False}


def _sidecar_for(topic):
    for s in _SIDE:
        if topic in candidate_topics(s):
            try:
                return json.load(open(os.path.join(
                    ROOT, "outputs", "r_validation", s + ".json"),
                    encoding="utf-8"))
            except Exception:
                return None
    return None

NCT = re.compile(r"NCT\d{7,8}")
# Authorities the corpus actually cites. Matched case-insensitively and as
# whole words, so "handbook" inside another word cannot trip it.
AUTHORITY = re.compile(r"\b(cochrane handbook|clinicaltrials\.gov|"
                       r"the registry|registry states|EU Clinical Trials|"
                       r"ISRCTN)\b", re.I)
NO_REASON = ("refused with no reason recorded",
             "pooled.withdrawn set with no reason recorded",
             "poolable false with no reason recorded",
             "pooled.withdrawn is set with no reason recorded",
             "poolable is false with no reason recorded")


def classify(reason):
    r = (reason or "").strip()
    if r == "" or r.lower() in [x.lower() for x in NO_REASON]:
        return "REFUSED_WITHOUT_A_RECORDED_REASON", 0
    n = len(NCT.findall(r))
    if n > 0 or AUTHORITY.search(r):
        return "REFUSED_ON_A_STATED_METHODOLOGICAL_GROUND", n
    return "UNCLASSIFIED_DECLINE", 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    states = Counter()
    declines = Counter()
    unclassified, rows_out = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json"))):
        kind, obj = _file_kind(path)
        if kind != "live_with_outcomes":
            continue
        topic = os.path.basename(os.path.dirname(path))
        for r in sof_rows(obj, _sidecar_for(topic)):
            states[r["state"]] += 1
            if r["state"] != "DECLINED_BY_THE_STORE":
                continue
            cls, ncts = classify(r.get("reason"))
            declines[cls] += 1
            rows_out.append({"topic": topic, "outcome": r["outcome"],
                             "class": cls, "registrations_cited": ncts,
                             "reason": str(r.get("reason", ""))[:400]})
            if cls == "UNCLASSIFIED_DECLINE":
                unclassified.append((topic, r["outcome"],
                                     str(r.get("reason", ""))[:110]))

    total_declines = sum(declines.values())
    print("EVERY SoF ROW BY STATE")
    for k, v in states.most_common():
        print("  %-24s %d" % (k, v))
    print("  total %d" % sum(states.values()))
    print("")
    print("THE 142 DECLINES, SPLIT -- only the first is CONTENT")
    for k in ("REFUSED_ON_A_STATED_METHODOLOGICAL_GROUND",
              "REFUSED_WITHOUT_A_RECORDED_REASON", "UNCLASSIFIED_DECLINE"):
        print("  %-46s %d" % (k, declines.get(k, 0)))
    print("  identity: %d == %d declines : %s"
          % (total_declines, states.get("DECLINED_BY_THE_STORE", 0),
             "HOLDS" if total_declines == states.get("DECLINED_BY_THE_STORE", 0)
             else "FAILS"))
    print("")
    derived = states.get("DERIVED", 0)
    method = declines.get("REFUSED_ON_A_STATED_METHODOLOGICAL_GROUND", 0)
    nodata = states.get("NOT_DERIVABLE_NO_2X2", 0)
    noreason = declines.get("REFUSED_WITHOUT_A_RECORDED_REASON", 0)
    uncl = declines.get("UNCLASSIFIED_DECLINE", 0)
    print("BOTH METRICS, SIDE BY SIDE -- neither travels alone")
    print("  rows carrying CONTENT                 %d"
          % (derived + method))
    print("      derived absolute effects          %d" % derived)
    print("      refusals on a stated ground       %d" % method)
    print("  rows carrying a HOLE                  %d"
          % (nodata + noreason + uncl))
    print("      no 2x2 cells held                 %d" % nodata)
    print("      refused with no reason recorded   %d" % noreason)
    print("      decline citing no evidence        %d" % uncl)
    print("  identity: %d + %d == %d rows : %s"
          % (derived + method, nodata + noreason + uncl, sum(states.values()),
             "HOLDS" if derived + method + nodata + noreason + uncl
             == sum(states.values()) else "FAILS"))
    print("")
    if unclassified:
        print("UNCLASSIFIED, BY NAME -- not counted either way, for a human")
        for t, o, r in unclassified[:20]:
            print("  %-30s %-24s %s" % (t[:30], o[:24], r[:60]))
        if len(unclassified) > 20:
            print("  ... and %d more" % (len(unclassified) - 20))
    if a.json_out:
        json.dump(rows_out, open(a.json_out, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print("\nwrote %s" % a.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
