#!/usr/bin/env python3
"""TRIAGE THE 205 TWO-REGISTRATION CANDIDATES -- cheapest first, and no classification by rule.

WHAT IS BEING ASKED. 205 publications are listed as their OWN report by exactly two
registrations. One of two things is true of each:

    PARENT_AND_SUBSTUDY    one trial, two registrations -> a registry-derived k is INFLATED
    TWO_TRIALS_ONE_REPORT  two separate trials reported together -> k is CORRECT

Only reading the paper settles it. This script does NOT classify; it orders the queue so the
cheapest reads come first, and it records the two cheap SIGNALS that make a read fast.

THE SIGNALS, AND WHY NEITHER IS A VERDICT:

    BOTH REGISTRATIONS COMPLETED. A pair where one is still recruiting is usually a parent that
    has reported and a companion that has not, which is a different situation and a slower read.

    ENROLMENT CONTAINMENT. In the confirmed instance the substudy enrolled 280 of the parent's
    714 -- a strict subset. In the confirmed two-trial cases the enrolments are independent
    (16,784 and 10,564). SO A LARGE RATIO IS SUGGESTIVE OF PARENT-AND-SUBSTUDY AND SETTLES
    NOTHING: two genuinely separate trials of very different size look identical on this signal,
    and a substudy enrolling nearly all of its parent looks like a twin.

        USING THE RATIO AS THE ANSWER WOULD BE READING A NUMBER AS AN ESTIMAND, which is the
        error this whole line of work exists to name. It orders the queue. It does not decide.

USAGE
    python scripts/triage_multi_registration_candidates_2026_08_19.py [--apply]
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                             # noqa: E402

EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")
SRC = os.path.join(EV, "multi_registration_publications.json")
OUT = os.path.join(EV, "multi_registration_triage.json")

DONE = {"COMPLETED", "TERMINATED", "WITHDRAWN"}


def reg(nct, cache):
    if nct in cache:
        return cache[nct]
    st, s, d = X.fetch_raw(nct, fields="protocolSection")
    if st != X.OK:
        cache[nct] = {"nct": nct, "state": "UNREACHABLE"}
        return cache[nct]
    ps = s.get("protocolSection") or {}
    idm = ps.get("identificationModule") or {}
    cache[nct] = {
        "nct": nct, "state": "READ",
        "acronym": idm.get("acronym"),
        "official_title": (idm.get("officialTitle") or idm.get("briefTitle") or "")[:180],
        "overall_status": (ps.get("statusModule") or {}).get("overallStatus"),
        "enrollment": ((ps.get("designModule") or {}).get("enrollmentInfo") or {}).get("count"),
        "lead_sponsor": (((ps.get("sponsorCollaboratorsModule") or {}).get("leadSponsor")
                          or {}).get("name")),
    }
    return cache[nct]


def run(apply_it):
    src = json.load(io.open(SRC, encoding="utf-8"))
    pairs = [h for h in src["hits_informative_stratum"]
             if h["n_listing_it_as_their_own_report"] == 2
             and h["classification"]["shape"] == "UNCLASSIFIED"]
    print("unclassified two-registration candidates: %d" % len(pairs))

    cache, rows = {}, []
    for i, h in enumerate(pairs):
        a, b = h["registrations_listing_it_as_their_OWN_report"]
        ra, rb = reg(a, cache), reg(b, cache)
        both_done = (ra.get("overall_status") in DONE and rb.get("overall_status") in DONE)
        ea, eb = ra.get("enrollment"), rb.get("enrollment")
        ratio = None
        if isinstance(ea, int) and isinstance(eb, int) and max(ea, eb):
            ratio = round(min(ea, eb) / max(ea, eb), 3)
        same_sponsor = (ra.get("lead_sponsor") and
                        ra.get("lead_sponsor") == rb.get("lead_sponsor"))
        rows.append({
            "pmid": h["pmid"], "registrations": [a, b],
            "acronyms": [ra.get("acronym"), rb.get("acronym")],
            "statuses": [ra.get("overall_status"), rb.get("overall_status")],
            "enrollments": [ea, eb],
            "enrolment_ratio_small_over_large": ratio,
            "same_lead_sponsor": bool(same_sponsor),
            "lead_sponsors": [ra.get("lead_sponsor"), rb.get("lead_sponsor")],
            "official_titles": [ra.get("official_title"), rb.get("official_title")],
            "both_registrations_completed": both_done,
            "read_priority": (0 if both_done else 1),
        })
        if (i + 1) % 40 == 0:
            print("   ...%d/%d pairs resolved" % (i + 1, len(pairs)))

    both = [r for r in rows if r["both_registrations_completed"]]
    print("\n  both registrations completed/terminated : %d" % len(both))
    print("  at least one still ongoing              : %d" % (len(rows) - len(both)))
    sub = [r for r in both if r["enrolment_ratio_small_over_large"] is not None
           and r["enrolment_ratio_small_over_large"] < 0.75]
    same = [r for r in both if r["same_lead_sponsor"]]
    print("  of the completed pairs, enrolment ratio < 0.75 : %d" % len(sub))
    print("  of the completed pairs, same lead sponsor      : %d" % len(same))

    doc = {
        "triaged_utc": "2026-08-19",
        "what_this_does_NOT_do": (
            "IT DOES NOT CLASSIFY. Enrolment ratio and sponsor identity ORDER THE QUEUE and "
            "settle nothing: two genuinely separate trials of very different size look "
            "identical on the ratio, and a substudy enrolling nearly all of its parent looks "
            "like a twin. Using the ratio as the answer would be reading a number as an "
            "estimand."),
        "counts": {
            "unclassified_two_registration_candidates": len(rows),
            "both_registrations_completed_or_terminated": len(both),
            "at_least_one_ongoing": len(rows) - len(both),
            "completed_pairs_with_enrolment_ratio_under_0_75": len(sub),
            "completed_pairs_with_the_same_lead_sponsor": len(same),
        },
        "queue": sorted(rows, key=lambda r: (r["read_priority"],
                                             r["enrolment_ratio_small_over_large"]
                                             if r["enrolment_ratio_small_over_large"] is not None
                                             else 1.0)),
    }
    print("\n  cheapest 12 to read:")
    for r in doc["queue"][:12]:
        print("     PMID %-9s %-27s ratio=%-6s sponsor_same=%-5s %s"
              % (r["pmid"], ",".join(r["registrations"]),
                 r["enrolment_ratio_small_over_large"], r["same_lead_sponsor"],
                 "/".join(str(x) for x in r["enrollments"])))
    if apply_it:
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(doc, indent=1, ensure_ascii=False))
        print("\nwrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
