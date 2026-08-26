# -*- coding: utf-8 -*-
"""Split every NO_INFORMATION domain judgement into two kinds, per domain, per result.

THE DISTINCTION THE WHOLE EXERCISE EXISTS TO MAKE, and it is currently unrecorded:

  REPORTED_ABSENT_BY_TRIAL   the source we read covers this domain and says nothing that
                             answers it. That is a risk-of-bias finding ABOUT THE TRIAL.
  NOT_RETRIEVED_BY_US        the document that would answer it was never fetched. That is a
                             finding ABOUT US, and publishing it as the first is how 870
                             legacy pages came to make adverse claims about other people's
                             trials out of gaps in our own object.

WHAT DECIDES WHICH. Not the judgement text -- an assessor's prose is an opinion about the
evidence, and reading intent out of it would be inference wearing a field name. What decides
it is whether the SOURCE THAT ANSWERS THAT DOMAIN is held:

  D1 sequence generation, allocation concealment -> protocol / full report. Registry does
     not carry it, so registry-only is NOT_RETRIEVED.
  D2 deviations from intended intervention       -> full report / SAP.
  D3 missing outcome data                        -> full report / posted results flow.
  D4 measurement of the outcome                  -> registry masking IS informative here, so
     a held registry record with a masking field can support REPORTED_ABSENT.
  D5 selection of the reported result            -> registry outcome list IS the instrument,
     so a held registry record supports REPORTED_ABSENT.

READ-ONLY. This measures and reports; it writes nothing, because the RoB regen and merge
are frozen and `by_outcome` is assigned wholesale.
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
REPO = r"F:\rapidmeta-ssot-shell"
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "ssot"))
from rob_block import rob_block  # noqa: E402

CACHE = ".ctgov-raw-cache"
cached = set()
for f in os.listdir(CACHE):
    m = re.match(r"(NCT\d+)_", f)
    if m:
        cached.add(m.group(1))

# which held source can answer each domain
REGISTRY_ANSWERS = {"D4", "D5"}


def paper_held(topic, nct):
    """Is a full report or protocol staged for this trial in this topic?"""
    d = os.path.join("ssot", topic, "sources")
    if not os.path.isdir(d):
        return False
    names = os.listdir(d)
    for n in names:
        low = n.lower()
        if nct and nct.lower() in low:
            if low.endswith((".pdf", ".txt")) and "ctgov" not in low:
                return True
        if any(k in low for k in ("protocol", "_sap", "fulltext", "full_text")):
            return True
    return False


rows = []
for p in sorted(glob.glob("ssot/*/*.json")):
    topic = os.path.basename(os.path.dirname(p))
    if os.path.basename(p) != topic + ".json":
        continue
    try:
        obj = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    b = rob_block(obj)
    if not b:
        continue
    for tr in b["trials"]:
        nct = None
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            if isinstance(t, dict) and (t.get("id") == tr.get("id")
                                        or t.get("nct") == tr.get("id")
                                        or t.get("name") == tr.get("trial")):
                nct = t.get("nct")
                break
        for d in tr["domains"]:
            for i, j in enumerate(d.get("judgements") or []):
                if str(j or "").upper().replace(" ", "_") != "NO_INFORMATION":
                    continue
                dom = (d.get("domain") or "?")[:2]
                if dom in REGISTRY_ANSWERS and nct in cached:
                    kind = "REPORTED_ABSENT_BY_TRIAL"
                    why = ("the registry record is held and is the instrument for this "
                           "domain; it carries nothing that answers it")
                elif paper_held(topic, nct):
                    kind = "REPORTED_ABSENT_BY_TRIAL"
                    why = "a full report or protocol is staged for this trial"
                else:
                    kind = "NOT_RETRIEVED_BY_US"
                    why = ("the document that answers this domain -- protocol, statistical "
                           "analysis plan or full report -- was never retrieved")
                rows.append({"topic": topic, "trial": tr.get("trial"), "nct": nct,
                             "outcome": tr.get("outcome"), "domain": dom,
                             "assessor": i + 1, "kind": kind, "why": why})

print("=" * 92)
print("NO_INFORMATION JUDGEMENTS, SPLIT BY WHOSE GAP IT IS")
print("=" * 92)
print("  NO_INFORMATION domain judgements          %4d  == the denominator" % len(rows))
c = collections.Counter(r["kind"] for r in rows)
for k, v in c.most_common():
    print("     %-38s %4d  (%.1f%%)" % (k, v, 100.0 * v / len(rows) if rows else 0))
print("")
print("BY DOMAIN")
by = collections.Counter((r["domain"], r["kind"]) for r in rows)
for dom in sorted({r["domain"] for r in rows}):
    a = by[(dom, "REPORTED_ABSENT_BY_TRIAL")]
    u = by[(dom, "NOT_RETRIEVED_BY_US")]
    print("  %-4s about the trial %4d   about us %4d" % (dom, a, u))
print("")
print("BY ASSESSOR")
ba = collections.Counter((r["assessor"], r["kind"]) for r in rows)
for i in (1, 2):
    print("  assessor %d: about the trial %4d   about us %4d"
          % (i, ba[(i, "REPORTED_ABSENT_BY_TRIAL")], ba[(i, "NOT_RETRIEVED_BY_US")]))
print("")
tops = collections.Counter(r["topic"] for r in rows if r["kind"] == "NOT_RETRIEVED_BY_US")
print("  topics with the most OUR-GAP judgements:")
for k, v in tops.most_common(8):
    print("     %-46s %3d" % (k, v))
json.dump(rows, io.open(r"F:\claude-temp\pend\ni_provenance.json", "w",
                        encoding="utf-8"), indent=1)
print("")
print("  detail -> ni_provenance.json   (READ-ONLY: nothing written to any store)")
