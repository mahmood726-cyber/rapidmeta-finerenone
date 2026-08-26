"""The certainty column has five states. This refuses any page that shows a sixth.

THE FIFTH WAS ADDED 2026-08-26: PENDING. A rating that reads an unadjudicated risk-of-bias
assessment is not published as a level. It is NOT folded into "See comment" -- the three
non-rated states all mean nothing was assessed, and this one means the opposite.

# control: the POSITIVE is `sglt2-hf`, whose three outcomes were read by hand off the object
# and whose required rendering was specified before this gate existed: Low, Low, See comment.
# It is keyed to the OBJECT's arrangement, which this work does not change -- the withdrawal,
# the two pooled estimates and the stranded "high" are all still there. The NEGATIVE is a
# SYNTHETIC OBJECT built in this file, so it cannot expire when the corpus is repaired.

THE FIFTH STATE WAS AN EM DASH AND IT MEANT NOTHING. `results.*.grade.certainty` holds 7
ratings across 34 pooled outcomes; `grade.by_outcome` holds 26. The column read the first
and printed `&mdash;` when it was empty, so 21 assessed outcomes showed a dash. An em dash
is not a value in Cochrane's certainty scheme and zero of nine published reviews checked
use one. A dash says nothing, and "nothing" reads as "nothing to report" rather than "not
assessed" -- the one confusion this column must not permit.

THE FOUR, AND WHAT EACH MUST CARRY:

    RATED, HIGH        the level. No footnote is required; nothing was downgraded.
    RATED, BELOW HIGH  the level AND a footnote. A downgrade whose reason is not shown is a
                       grade with its reason removed.
    NOT ASSESSED       "See comment", the project's own absent-state string, AND the
                       declared-departure sentence. Never a level, never a dash.
    WITHDRAWN POOL     "See comment". Never a level, EVEN WHERE A LOCATION HOLDS ONE.

THE ONE ARRANGEMENT THAT IS INDEFENSIBLE UNDER EITHER ANSWER, and the reason the withdrawn
state outranks a held rating: `sglt2-hf` rates its WITHDRAWN outcome "high" in the table
and rates neither of its two published estimates there. Before this, the page showed High
beside "not pooled" and a dash beside both real estimates -- the exact opposite of the
truth on all three rows, and the abstract then quoted the rating beside the estimates it
was not about.

A FIFTH STATE THIS GATE ALSO REFUSES: a superscript with no note under it. "See comment"
with no comment is worse than the dash it replaced, because it promises one.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, HERE)

import grade_authority as ga  # noqa: E402
from instrument_controls import require_controls  # noqa: E402

STATES = {"RATED", "NOT_ASSESSED", "WITHDRAWN_POOL", "DISAGREEMENT", "PENDING"}
CELLS = set(ga.LEVELS.values()) | {ga.CELL_SEE_COMMENT, ga.CELL_PENDING}

# sglt2-hf, read by hand off the object before this gate existed.
#
# THE TWO RATED ROWS MOVED TO PENDING ON 2026-08-26, AND THE EXPECTATION WAS NOT SIMPLY
# EDITED TO MATCH THE NEW OUTPUT -- which is how a control stops being one. What changed is
# the MODEL, not the code's behaviour on a fixed model: a certainty rating that reads an
# unadjudicated risk-of-bias assessment is no longer published as final. The move is
# checkable independently of this file: sglt2-hf holds two assessors, nine result-pairs,
# nine disagreements and no adjudication record, and its GRADE rates risk of bias serious.
# The WITHDRAWN row is untouched, and it is the row this control was really built to
# protect -- "High" printed beside "not pooled".
#
# A CONTROL PINNED TO A LIVE OBJECT RETIRES ITSELF THE DAY THE OBJECT IS REPAIRED. That is
# why the real control for the new state is SYNTHETIC, below, and cannot expire.
ACCEPTANCE = ("sglt2-hf", {
    "cvdeath_or_whf_first": ("WITHDRAWN_POOL", ga.CELL_SEE_COMMENT),
    "harmonised_cvdeath_or_hhf": ("PENDING", ga.CELL_PENDING),
    "threecomp_cvdeath_hhf_urgent": ("PENDING", ga.CELL_PENDING),
})

# THE PENDING STATE'S OWN CONTROLS, BOTH SYNTHETIC AND BOTH REQUIRED.
#
# The positive alone would pass a module that returned PENDING unconditionally, which is a
# real risk: "withhold everything" satisfies every honesty check ever written and is
# useless. The NEGATIVE is the one that matters -- the same object WITH an adjudication
# record must come back RATED. It proves the predicate reads the record rather than the
# calendar, and it is what will fail loudly if someone later hardcodes the answer.
def _rob_fixture(adjudicated):
    rb = {
        "by_outcome": {"x": {"T1": {"trial": "T1", "overall": "HIGH", "domains": {
            "D5_selection_of_reported_result": {"judgement": "HIGH"}}}}},
        "SECOND_ASSESSOR_FIXTURE": {
            "assessor_1": "reader one", "assessor_2": "reader two",
            "verbatim_reply": "T1__x D5=LOW OVERALL=LOW"},
    }
    if adjudicated:
        rb["ADJUDICATION"] = {"adjudicator": "a third reader",
                              "resolved": "D5 HIGH on T1"}
    return {"risk_of_bias": rb,
            "results": {"by_outcome": {"x": {
                "pooled": {"point": 0.8},
                "grade": {"certainty": "LOW",
                          "domains": {"risk_of_bias": {"rating": "serious"}}}}}},
            "grade": {"by_outcome": {}}}


FIXTURE_PENDING = _rob_fixture(False)
FIXTURE_ADJUDICATED = _rob_fixture(True)

# The synthetic negative: an object where nothing is rated anywhere. It must come back
# NOT_ASSESSED with a comment -- never RATED, and never with an empty comment.
FIXTURE_UNRATED = {
    "results": {"by_outcome": {"x": {"pooled": {"point": 0.8}}}},
    "grade": {"by_outcome": {}},
}


def acceptance():
    p = os.path.join(REPO, "ssot", ACCEPTANCE[0], ACCEPTANCE[0] + ".json")
    if not os.path.isfile(p):
        return None, "object not on disk"
    obj = json.load(io.open(p, encoding="utf-8"))
    got = {}
    for oid in ACCEPTANCE[1]:
        r = ga.resolve(obj, oid)
        got[oid] = (r["state"], r["cell"])
    return got, None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    got, err = acceptance()
    if err:
        sys.exit("REFUSED: the positive control is unavailable (%s). A gate with no "
                 "established answer to reproduce passes everything." % err)
    fx = ga.resolve(FIXTURE_UNRATED, "x")
    fp = ga.resolve(FIXTURE_PENDING, "x")
    fa = ga.resolve(FIXTURE_ADJUDICATED, "x")
    require_controls(
        "certainty_column_five_states",
        ("sglt2-hf renders See comment / Pending / Pending -- read by hand off the object; "
         "got %r" % (got,), got, ACCEPTANCE[1]),
        ("the synthetic all-unrated fixture must not come back RATED; it came back %r"
         % fx["state"], fx["state"], "RATED"))
    # THE NEW STATE'S OWN PAIR. The negative is the one that carries the weight: "withhold
    # everything" passes every honesty check ever written, so a module that returned
    # PENDING unconditionally would satisfy the positive alone and be worthless.
    require_controls(
        "certainty_pending_state",
        ("a dual, unadjudicated assessment behind a risk-of-bias downgrade must come back "
         "PENDING; it came back %r" % fp["state"], fp["state"], "PENDING"),
        ("the SAME fixture with an adjudication record must NOT come back PENDING; it "
         "came back %r" % fa["state"], fa["state"], "PENDING"))

    bad, pools, by_state = [], 0, {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            pooled = blk.get("pooled") or {}
            if pooled.get("point") is None and not pooled.get("withdrawn"):
                continue
            pools += 1
            r = ga.resolve(obj, oid)
            by_state[r["state"]] = by_state.get(r["state"], 0) + 1
            if r["state"] not in STATES:
                bad.append((t, oid, "state %r is not one of the four" % r["state"]))
            if r["cell"] not in CELLS:
                bad.append((t, oid, "cell %r is not a certainty value" % r["cell"]))
            if "—" in r["cell"] or "&mdash;" in r["cell"]:
                bad.append((t, oid, "the cell is an em dash, which means nothing"))
            if r["state"] == "RATED" and r["level"] != "HIGH" and not r["comment"]:
                bad.append((t, oid, "rated %s with no footnote -- a downgrade with its "
                                    "reason removed" % r["level"]))
            if r["state"] == "WITHDRAWN_POOL" and r["level"] is not None:
                bad.append((t, oid, "a withdrawn pool carries a level in the cell"))
            # A PENDING RATING THAT STILL CARRIES A LEVEL HAS WITHHELD NOTHING. The whole
            # move is to publish no level; a `level` left populated would be read by the
            # next consumer that asks for one, which is how the stored rating reached the
            # manuscript in the first place.
            if r["state"] == "PENDING":
                if r["level"] is not None:
                    bad.append((t, oid, "a PENDING rating still carries a level"))
                if not r.get("pending_because"):
                    bad.append((t, oid, "PENDING without saying what it is waiting on"))
                if "risk-of-bias" not in r["comment"]:
                    bad.append((t, oid, "PENDING without naming what the rating rests on"))
            if r["state"] != "RATED" and not r["comment"]:
                bad.append((t, oid, "\"See comment\" with no comment"))
            if r["state"] == "NOT_ASSESSED":
                if ga.DEPARTURE_SECTION not in r["comment"]:
                    bad.append((t, oid, "not assessed without the declared-departure "
                                        "reference"))
                if "not been rated" not in r["comment"]:
                    bad.append((t, oid, "not assessed without the absent-state string"))

    print("")
    print("THE CERTAINTY COLUMN, over %d outcome(s) that publish or withdraw an estimate"
          % pools)
    print("")
    for s in sorted(by_state):
        print("   %-18s %4d" % (s, by_state[s]))
    print("   %-18s %4d   == the population" % ("sum", sum(by_state.values())))
    print("")
    if bad:
        for t, oid, why in bad[:20]:
            print("   %-34s %-30s %s" % (t[:34], oid[:30], why))
        sys.exit("REFUSED: %d certainty cell(s) are outside the four-state spec." % len(bad))
    print("Every cell is one of the five. No em dash, no rated-without-reason, no withdrawn")
    print("pool carrying a level, and no \"See comment\" without a comment.")


if __name__ == "__main__":
    main()
