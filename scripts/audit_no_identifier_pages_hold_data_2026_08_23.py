"""Of the pages that show a reader no trial id, how many HOLD trial-level data anyway?

# control: routed through require_controls. POSITIVE is ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW,
# read by hand: its `realData` payload holds NCT01343004 (the ACTIVE trial) with per-arm counts
# tE:4 tN:690 cE:30 cN:711, a PMID, a published HR and RoB judgements. NEGATIVE is that the
# TEMPLATE array `trialData=["NCT01035255","NCT01920711","NCT02924727"]` must NOT be counted as
# page data -- it is the same three LCZ696 trials on every page and counting it would report
# 100% of pages as data-bearing.

THE QUESTION THIS ANSWERS BEARS DIRECTLY ON WHAT "REPAIR" MEANS. The registry triage put 630 of
745 legacy pages in "no identifier shown to a reader". That is true and it is what a reader
meets. It is NOT the same as "no review was done", and conflating the two would misdescribe the
repair to the person authorising it:

    provenance LOST      the page holds per-arm counts and a computed estimate but never
                         names the trials -- the review exists, its sourcing is invisible.
                         A rebuild here is a PROJECTION of data that is already present.

    review NOT DONE      neither identifiers nor arm-level data. A rebuild here means DOING
                         THE REVIEW, which is not a repair at all.

Those are different orders of work and the counts differ by a lot, which is precisely why the
question had to be asked before anyone starts.

WHY THE READER-FACING COUNT AND THIS ONE ARE BOTH RIGHT. The identifiers live in the page's
JavaScript payload, not in its prose or tables, so an extraction keyed to what a reader meets
correctly reports zero -- and this one, keyed to what the page HOLDS, correctly reports data.
Two probes, two questions, both answers true. That is the shape that has read as a
disagreement four times tonight, so it is stated here rather than discovered again.
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIAGE = os.path.join(REPO, "outputs", "legacy_registration_triage_2026_08_23.json")
OUT = os.path.join(REPO, "outputs", "no_identifier_data_state_2026_08_23.json")

# The template array, excluded by name. These four are on 72-79% of legacy pages and are
# hardcoded engine defaults, not this page's trials.
TEMPLATE_IDS = {"NCT01035255", "NCT01920711", "NCT02924727", "NCT05901831"}

REALDATA = re.compile(r"realData\s*[:=]\s*\{")
NCT = re.compile(r"NCT\d{8}")
# per-arm counts: treatment events/N and control events/N
ARMS = re.compile(r"\btE\s*:\s*\d+.{0,80}?\btN\s*:\s*\d+.{0,120}?\bcE\s*:\s*\d+", re.S)
PMID = re.compile(r"pmid\s*:\s*[\"']?\d{6,9}")


def payload(text):
    """The realData object body, brace-matched. Empty string when there is none."""
    m = REALDATA.search(text)
    if not m:
        return ""
    i, depth = m.end(), 1
    while i < len(text) and depth:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    return text[m.end():i]


def state_of(path):
    t = io.open(path, encoding="utf-8", errors="replace").read()
    body = payload(t)
    ids = sorted(set(NCT.findall(body)) - TEMPLATE_IDS)
    arms = len(ARMS.findall(body))
    pmids = len(PMID.findall(body))
    return {"ids": ids, "arm_blocks": arms, "pmids": pmids,
            "payload_bytes": len(body)}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isfile(TRIAGE):
        sys.exit("REFUSED: %s missing -- run the registry triage first."
                 % os.path.relpath(TRIAGE, REPO))
    tri = json.load(io.open(TRIAGE, encoding="utf-8"))
    names = sorted(tri["buckets"].get("no_identifier", []))
    if not names:
        sys.exit("REFUSED: the no-identifier bucket is empty; nothing to characterise.")

    ctrl = os.path.join(REPO, "ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html")
    cs = state_of(ctrl) if os.path.isfile(ctrl) else {"ids": [], "arm_blocks": 0}
    require_controls(
        "no_identifier_data_state",
        ("ABALOPARATIDE_OSTEO holds NCT01343004 with per-arm counts in its realData payload "
         "(read by hand: tE:4 tN:690 cE:30 cN:711) -- got ids=%s arms=%d"
         % (cs["ids"][:3], cs["arm_blocks"]),
         "NCT01343004" in cs["ids"] and cs["arm_blocks"] >= 1, True),
        ("the template array is excluded -- no page reports ONLY the four hardcoded ids",
         bool(set(cs["ids"]) & TEMPLATE_IDS), True))

    buckets = collections.Counter()
    rows, byb = {}, collections.defaultdict(list)
    for n in names:
        p = os.path.join(REPO, n)
        if not os.path.isfile(p):
            buckets["not_on_disk"] += 1
            byb["not_on_disk"].append(n)
            continue
        s = state_of(p)
        rows[n] = s
        if s["ids"] and s["arm_blocks"]:
            k = "provenance_lost"          # ids AND arm data, just never displayed
        elif s["arm_blocks"]:
            k = "data_no_ids"             # arm data, no identifiers even internally
        elif s["ids"]:
            k = "ids_no_data"
        else:
            k = "no_review_done"
        buckets[k] += 1
        byb[k].append(n)

    tot = len(names)
    print("")
    print("THE %d PAGES THAT SHOW A READER NO TRIAL IDENTIFIER -- what do they HOLD?" % tot)
    print("")
    for k, lab in (("provenance_lost",
                    "identifiers AND per-arm counts, never displayed"),
                   ("data_no_ids", "per-arm counts, no identifiers even internally"),
                   ("ids_no_data", "identifiers, no per-arm counts"),
                   ("no_review_done", "neither -- no trial-level data at all"),
                   ("not_on_disk", "not on disk")):
        print("   %-48s %5d   %5.1f%%"
              % (lab, buckets[k], 100.0 * buckets[k] / max(1, tot)))
    s = sum(buckets.values())
    print("   %-48s %5d   == the bucket" % ("sum", s))
    if s != tot:
        sys.exit("REFUSED: does not close -- %d pages, %d placed." % (tot, s))

    ids_total = sorted(set(i for r in rows.values() for i in r["ids"]))
    print("")
    print("   distinct page-specific identifiers held but not shown   %5d" % len(ids_total))
    print("")
    print("A PAGE HOLDING PER-ARM COUNTS AND AN IDENTIFIER IS NOT A PAGE WHERE NO REVIEW WAS")
    print("DONE. Its sourcing is invisible to a reader, which is a display defect and a")
    print("PROJECTION away from being fixed. A page holding neither is a different order of")
    print("work entirely -- rebuilding it means doing the review -- and that is not a repair.")
    print("")
    print("Both counts are true of the same pages: the reader-facing probe reports no")
    print("identifier because none is rendered, and this one reports data because the payload")
    print("holds it. Neither refutes the other.")

    json.dump({"total": tot, "buckets": dict(buckets),
               "by_bucket": {k: v for k, v in byb.items()},
               "identifiers_held": ids_total,
               "rows": {k: v for k, v in list(rows.items())[:400]}},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
