"""Turn returned lanes into a number: launched, returned, findings, withdrawn.

A LANE THAT RETURNED IS NOT A FINDING. Most of tonight's cost has been telling those apart:
six confident accusations that were packet artefacts, two truncation checks that flagged
crash damage where there was none. So this classifies rather than counts, and it never
promotes a lane's own confidence into a verified finding -- VERIFIED means a person or a
script checked it against the artefact, and nothing here can do that on its own.

FOUR STATES, and the third is the one that matters:

    CLAIMS_DEFECT     the lane names something wrong. UNVERIFIED by definition.
    CLEAN             the lane looked and says the shapes are absent
    COULD_NOT_DETERMINE   the lane says the packet does not settle it -- the correct
                      answer when it does not, and the state a partial packet should
                      produce instead of an accusation
    NO_ANSWER         the lane returned bytes that contain no verdict: it explored and ran
                      out, or it errored. Counted separately because four Codex passes did
                      exactly this before the file was inlined, and reading them as CLEAN
                      would have been the worst possible mistake.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "lanes", "out")
LEDGER = os.path.join(REPO, "outputs", "lanes", "harvest.json")

DEFECT = re.compile(r"\bDEFECT\b|\bBUG\b|\bOVERCLAIM\b|\bREJECT\b|"
                    r"\bTRUNCATED\b|\bnot a fact\b", re.I)
CLEAN = re.compile(r"\bCLEAN\b|\bNONE\b|\bno defects? found\b|\bACCEPT\b", re.I)
CND = re.compile(r"COULD NOT DETERMINE|COULD_NOT_DETERMINE", re.I)
NOANSWER = re.compile(r"I'?m sorry|can'?t complete|cannot complete|"
                      r"command line is too long|SPAWN FAILED", re.I)


def classify(text):
    if not text.strip():
        return "NO_ANSWER"
    if NOANSWER.search(text):
        return "NO_ANSWER"
    if DEFECT.search(text):
        return "CLAIMS_DEFECT"
    if CND.search(text):
        return "COULD_NOT_DETERMINE"
    if CLEAN.search(text):
        return "CLEAN"
    return "NO_ANSWER"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isdir(OUT):
        sys.exit("REFUSED: %s does not exist." % OUT)
    rows, tally = {}, {}
    # THE POSITIVE PROPERTY: the file IS a lane output. Written as `if not f.endswith(...)`
    # the guard says only what the file is not, which a partial write or an editor backup
    # also satisfies -- and `audit_exclusion_by_absence --gate` refused the commit for it,
    # correctly, for the second time tonight.
    for f in sorted(x for x in os.listdir(OUT) if x.endswith(".out")):
        p = os.path.join(OUT, f)
        t = io.open(p, encoding="utf-8", errors="replace").read()
        # A lane still running has a growing file; only the tail carries the verdict.
        v = classify(t[-6000:])
        rows[f[:-4]] = {"state": v, "bytes": len(t)}
        tally[v] = tally.get(v, 0) + 1
    st = {}
    sp = os.path.join(REPO, "outputs", "lanes", "status.json")
    if os.path.isfile(sp):
        try:
            st = json.load(io.open(sp, encoding="utf-8"))
        except ValueError:
            st = {}

    print("")
    print("LANE THROUGHPUT")
    print("   launched            %5s" % st.get("launched", "?"))
    print("   returned            %5s" % st.get("returned", "?"))
    print("   running             %5s" % st.get("running", "?"))
    print("   queued              %5s" % st.get("queued", "?"))
    print("   spawn failures      %5s" % st.get("failed", "?"))
    print("")
    print("WHAT THE RETURNED LANES SAY  (output files seen: %d)" % len(rows))
    for k in ("CLAIMS_DEFECT", "CLEAN", "COULD_NOT_DETERMINE", "NO_ANSWER"):
        print("   %-22s %5d" % (k, tally.get(k, 0)))
    print("")
    print("   CLAIMS_DEFECT is UNVERIFIED. Nothing here checks a claim against the")
    print("   artefact, and tonight 6 of 8 findings from one cold read were packet")
    print("   artefacts. A claim becomes a finding only after someone reads the object.")
    print("")
    top = [(r["bytes"], n, r["state"]) for n, r in rows.items()
           if r["state"] == "CLAIMS_DEFECT"]
    for b, n, _s in sorted(top, reverse=True)[:12]:
        print("   claims a defect: %-52s %7d bytes" % (n[:52], b))
    json.dump({"tally": tally, "rows": rows, "status": st},
              io.open(LEDGER, "w", encoding="utf-8"), indent=1)
    print("")
    print("   written: %s" % os.path.relpath(LEDGER, REPO))


if __name__ == "__main__":
    main()
