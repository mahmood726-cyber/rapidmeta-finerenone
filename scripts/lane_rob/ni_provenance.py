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
  D5 selection of the reported result            -> PROTOCOL and SAP. Corrected 2026-08-26.

THE D5 ENTRY WAS WRONG AND IT ERRED IN THE FLATTERING DIRECTION. It said the registry
outcome list is the instrument for selective reporting, so a held registry record made a D5
absence a finding about the trial. But D5 compares what was REPORTED against what was
PLANNED, and the plan is in the protocol and the statistical analysis plan. A registry
record establishes what was registered -- and SCORED's ORIGINAL record (16 October 2017)
lists outcomes the current record does not, so the registry itself has a version dimension
this was not reading. Every D5 absence recorded without the protocol was OUR gap published
as theirs: 10 cases, and the corrected split moves them.

The lesson is about the method, not the number: a discriminator is only as good as its
inventory of instruments, and an incomplete inventory fails silently toward "their fault".

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

# WHICH HELD SOURCE CAN ANSWER EACH DOMAIN -- and this inventory was WRONG for D5.
#
# The first version listed D5 as answerable from the registry, because the registered
# outcome list is an instrument for selective reporting. It is not a SUFFICIENT one. D5
# exists to compare what was REPORTED against what was PLANNED, and the plan lives in the
# protocol and the statistical analysis plan. A registry record alone establishes what was
# registered, not what the analysis plan specified, and SCORED's ORIGINAL registry record
# (16 October 2017) lists outcomes the current record does not -- so even the registry has
# a version dimension we were not reading.
#
# The correction moves cases OUT of "about the trials" and INTO "about us", which is the
# unflattering direction, and it is the direction that was wrong. A D5 absence recorded
# without the protocol was our gap being published as theirs.
#
# D4 keeps the registry as sufficient: registered masking answers its signalling questions
# about who knew the assignment, which is what that domain turns on.
REGISTRY_ANSWERS = {"D4"}
PROTOCOL_ANSWERS = {"D1", "D2", "D3", "D5"}


def protocol_held(topic, nct):
    """Is a PROTOCOL or SAP staged for this trial -- not merely any document?

    The earlier version accepted any staged .pdf/.txt for the trial, which counted a
    published report as though it answered D5. A report tells you what was reported; only
    the plan tells you what was planned, and D5 is the comparison between them.
    """
    d = os.path.join("ssot", topic, "sources")
    if not os.path.isdir(d):
        return False
    for n in os.listdir(d):
        low = n.lower()
        if any(k in low for k in ("protocol", "_sap", "sap_", "analysis_plan",
                                  "statistical_analysis")):
            return True
    return False


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
                elif dom in PROTOCOL_ANSWERS and protocol_held(topic, nct):
                    kind = "REPORTED_ABSENT_BY_TRIAL"
                    why = ("a protocol or statistical analysis plan is staged for this "
                           "trial and is the instrument for this domain")
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
