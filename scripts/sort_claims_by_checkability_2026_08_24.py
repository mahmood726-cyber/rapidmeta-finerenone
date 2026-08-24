"""Sort the unverified lane claims by HOW they are checkable, because that predicts yield.

THE OBSERVATION THIS ENCODES. Two batches were worked tonight with very different results:

    claims about CODE      7 confirmed of 7, 1 of them inverting on its remedy
    claims about INSTANCES 7 upheld of 94

That is not a difference in reviewer quality. It is a difference in what the claim is ABOUT.
A claim about a function's behaviour is checkable by READING THE FUNCTION -- the whole
artefact is in front of you, the check is mechanical, and a cold reader working from the
complete source is on equal footing with the author. A claim that a particular page
overstates is checkable only by reading the page AND the object AND deciding whether the
wording reaches past the evidence, which is a judgement, needs both artefacts, and is
exactly where an incomplete packet manufactures confident nonsense.

So the sort order is a yield forecast, not a filing convenience:

    CODE_BEHAVIOUR     a named line, function, regex or exit path. Check by executing or
                       reading it. Highest yield, cheapest check.
    ARTEFACT_STATE     a claim about what a file or object contains. Check by looking.
                       Mechanical, but needs the right artefact in hand.
    INSTANCE_JUDGEMENT a claim that some wording overstates, understates or misleads.
                       Needs two artefacts and a judgement. Lowest yield, dearest check,
                       and the class where a partial packet does its damage.

WHAT THIS IS NOT. It is not a ranking of importance. An instance judgement that holds is
worth more to a reader than a regex that misses a form nobody writes -- the estimand-contrast
caveat was an instance judgement. It is a ranking of COST PER CONFIRMED FINDING, for
deciding what to work at four in the morning with a finite queue.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "lanes", "out")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402
import packet_transport as pt  # noqa: E402

CODE = re.compile(
    r"\bline\s+\d+|\blines\s+\d+\s*-\s*\d+|\breturn(?:s|ed)?\s+(?:value|None|0|\[\])|"
    r"\bregex\b|\bpattern\b|\bexit\s+code|\bsys\.exit|\bimport\b|\braises?\b|"
    r"\bnever\s+(?:fires?|matches?|executes?)|\boff.by.one\b|\.py:\d+", re.I)
ARTEFACT = re.compile(
    r"\bthe\s+(?:file|object|page|json|packet)\b|\bfield\b|\bkey\b|\bpath\s+`|"
    r"\bcontains?\b|\bis\s+(?:absent|missing|present)\b|\bbytes?\b", re.I)
JUDGE = re.compile(
    r"\boverstat|\bunderstat|\bmislead|\bimpl(?:ies|ied)\b|\bclaims?\s+more\b|"
    r"\breads?\s+as\b|\bsuggests?\b|\bthe\s+reader\b|\bwording\b|\bought\b|\bshould\s+say",
    re.I)


def claims():
    rows = []
    for f in sorted(x for x in os.listdir(OUT) if x.endswith(".out")):
        p = os.path.join(OUT, f)
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        # THE POSITIVE PROPERTY: this answer was written over a COMPLETE input, so its
        # text can be classified. The other branch is not a skip -- the lane is kept and
        # given its own axis, because a truncated input is a fact about the lane and not
        # an absence to route around. Written as `if not ok: continue` the gate refused
        # it, and it was right to twice over: the guard stated only what the answer is
        # not, and `continue` would have dropped the lane from the denominator entirely.
        ok, dropped = pt.output_is_trustworthy(t)
        if ok:
            tail = t[-6000:]
            c, a, j = (len(CODE.findall(tail)), len(ARTEFACT.findall(tail)),
                       len(JUDGE.findall(tail)))
            if c == a == j == 0:
                axis = "UNCLASSIFIED"
            elif j >= max(c, a):
                axis = "INSTANCE_JUDGEMENT"
            elif c >= a:
                axis = "CODE_BEHAVIOUR"
            else:
                axis = "ARTEFACT_STATE"
            rows.append({"lane": f[:-4], "axis": axis, "bytes": len(t),
                         "code": c, "artefact": a, "judge": j})
        else:
            rows.append({"lane": f[:-4], "axis": "INPUT_TRUNCATED",
                         "bytes": len(t), "dropped": dropped})
    return rows


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # CONTROLS ON FIXTURE TEXT, not on the corpus this run reads.
    pos = "The regex at line 61 never matches, so the check cannot fail."
    neg = "The notice overstates what the evidence supports and misleads the reader."
    pos_ok = len(CODE.findall(pos)) >= len(JUDGE.findall(pos)) and CODE.search(pos)
    neg_ok = len(JUDGE.findall(neg)) >= len(CODE.findall(neg))
    require_controls(
        "sort_claims_by_checkability",
        ("a sentence naming a line and a regex sorts as CODE_BEHAVIOUR: %s" % bool(pos_ok),
         bool(pos_ok), True),
        ("a sentence about overstating and misleading must NOT sort as CODE_BEHAVIOUR; "
         "it does: %s" % (not neg_ok), not neg_ok, True))

    rows = claims()
    tally = {}
    for r in rows:
        tally[r["axis"]] = tally.get(r["axis"], 0) + 1

    print("")
    print("UNVERIFIED CLAIMS, SORTED BY HOW THEY ARE CHECKABLE")
    print("")
    print("   measured yield tonight: 7 of 7 on code claims, 7 of 94 on instance claims.")
    print("   the sort is a cost-per-confirmed-finding forecast, not a ranking of worth.")
    print("")
    for k in ("CODE_BEHAVIOUR", "ARTEFACT_STATE", "INSTANCE_JUDGEMENT",
              "UNCLASSIFIED", "INPUT_TRUNCATED"):
        print("   %-20s %4d" % (k, tally.get(k, 0)))
    print("   %-20s %4d" % ("total", len(rows)))
    print("")
    print("   WORK ORDER -- largest CODE_BEHAVIOUR lanes first:")
    code = sorted((r for r in rows if r["axis"] == "CODE_BEHAVIOUR"),
                  key=lambda r: -r["bytes"])
    for r in code[:18]:
        print("     %-56s %7d bytes  code=%d" % (r["lane"][:56], r["bytes"], r["code"]))
    json.dump(rows, io.open(os.path.join(REPO, "outputs",
                                         "claims_by_checkability_2026_08_24.json"),
                            "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
