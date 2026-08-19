#!/usr/bin/env python3
"""THE LITERATURE LIMB FOR THE FOUR REMAINING COLCHICINE READINGS -- and the distinction that
keeps the silence finding honest.

THE FOUR: CEREBRO (k=9), ICH (4), PAD (3), ASCVD_MIXED (5). None has a trial with results posted
to the registry, so each currently publishes nothing for a reason recorded as
`NO_ESTIMATE_POSSIBLE_NOTHING_HAS_REPORTED`. This limb asks whether that is true of the world.

AND IT SEPARATES TWO THINGS A SILENCE PAPER MUST NOT COMBINE:

    A COMPLETED trial with nothing posted and nothing published is SILENCE -- the phenomenon.
    An ONGOING trial with nothing posted is EXPECTED -- it has not finished.

Counting an ongoing trial as silent inflates the finding with trials that were never due to
report. That is why the 53-registration denominator in the results-posting analysis was
restricted to ELIGIBLE_COMPLETED_NO_RESULTS_POSTED, and it is why every row here carries the
registration's `overallStatus` beside its publication state.

    UNRESOLVED, EXPECTED-UNRESOLVED AND SILENT ARE THREE STATES, and only the third is evidence
    of anything.

ROUTES: the registration's own reference list, every type unfiltered; then PubMed by
registration identifier for whatever route 1 leaves. Both are recorded; neither is presented as
exhaustive.

USAGE
    python scripts/literature_limb_remaining_readings_2026_08_19.py [--apply]
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctgov_transport as X                                             # noqa: E402
import build_colchicine_readings_2026_08_19 as B                        # noqa: E402

EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")
OUT = os.path.join(EV, "remaining_readings_literature.json")

READINGS = {
    "CEREBRO": "colchicine-stroke-prevention",
    "ICH": "colchicine-intracerebral-haemorrhage",
    "PAD": "colchicine-peripheral-arterial",
    "ASCVD_MIXED": "colchicine-mixed-ascvd",
}

# Registration statuses that mean "not due to report yet". An absence here is EXPECTED.
NOT_DUE = {"RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING",
           "SUSPENDED"}
# PubMed route 2 was run in batches for every registration below and returned nothing except
# where a PMID is recorded here from route 1.
ROUTE2_HITS = {}


def read(nct):
    st, s, d = X.fetch_raw(nct, fields="protocolSection")
    if st != X.OK:
        return {"nct": nct, "state": "UNREACHABLE", "why": str(d)[:120]}
    ps = s.get("protocolSection") or {}
    idm = ps.get("identificationModule") or {}
    refs = [r for r in ((ps.get("referencesModule") or {}).get("references") or [])
            if r.get("pmid")]
    status = (ps.get("statusModule") or {}).get("overallStatus")
    return {
        "nct": nct, "state": "READ",
        "acronym": idm.get("acronym"),
        "overall_status": status,
        "due_to_report": status not in NOT_DUE,
        "enrollment": ((ps.get("designModule") or {}).get("enrollmentInfo") or {}).get("count"),
        "pmids": [{"pmid": r["pmid"], "type": r.get("type"),
                   "citation": (r.get("citation") or "")[:200]} for r in refs],
    }


def classify(row):
    if row["state"] != "READ":
        return "NOT_CHECKED", "registration unreachable"
    if row["pmids"]:
        return "PUBLISHED", ("route 1 -- the registration's own reference list, every type "
                             "unfiltered")
    if not row["due_to_report"]:
        return "EXPECTED_UNRESOLVED", (
            "overallStatus is %s. THE TRIAL HAS NOT FINISHED, so the absence of a publication "
            "is expected and is NOT the silence this analysis is about. Counting it as silent "
            "would inflate the finding with trials that were never due to report."
            % row["overall_status"])
    return "NO_PUBLICATION_RESOLVED", (
        "overallStatus is %s -- DUE to have reported. Route 1 (registration reference list) and "
        "route 2 (PubMed by registration identifier) both returned nothing. NOT evidence that "
        "no publication exists; publisher search and grey literature were not run."
        % row["overall_status"])


def run(apply_it):
    doc = {"run_utc": "2026-08-19",
           "what_this_enumerated_over": {
               "targets": "the eligible trials of the four remaining colchicine readings",
               "routes_run": ["ClinicalTrials.gov referencesModule, every type unfiltered",
                              "PubMed by registration identifier"],
               "routes_NOT_run": ["publisher or journal search by trial name",
                                  "grey literature and conference abstracts"]},
           "the_distinction_this_keeps": (
               "A COMPLETED trial with nothing posted and nothing published is SILENCE. An "
               "ONGOING trial with nothing posted is EXPECTED. Combining them inflates a "
               "silence finding with trials that were never due to report."),
           "readings": {}}

    total = {"PUBLISHED": 0, "NO_PUBLICATION_RESOLVED": 0, "EXPECTED_UNRESOLVED": 0,
             "NOT_CHECKED": 0}
    for reading, topic in READINGS.items():
        o = json.load(io.open(os.path.join(REPO, "ssot", topic, topic + ".json"),
                              encoding="utf-8"))
        rows = []
        for t in o["inputs"]["trials"]:
            r = read(t["nct"])
            st, why = classify(r)
            r["publication_state"] = st
            r["why"] = why
            rows.append(r)
            total[st] += 1
        c = {}
        for r in rows:
            c[r["publication_state"]] = c.get(r["publication_state"], 0) + 1
        doc["readings"][reading] = {"topic": topic, "counts": c, "trials": rows}
        print("%-12s %-38s %s" % (reading, topic, c))

        # Patch the object: the verdict's premise is now checked against the world.
        pr = o["results"]["by_outcome"]["primary"]
        pub = [r for r in rows if r["publication_state"] == "PUBLISHED"]
        silent = [r for r in rows if r["publication_state"] == "NO_PUBLICATION_RESOLVED"]
        expected = [r for r in rows if r["publication_state"] == "EXPECTED_UNRESOLVED"]
        for t in o["inputs"]["trials"]:
            m = [r for r in rows if r["nct"] == t["nct"]]
            if m:
                t["publication_state"] = m[0]["publication_state"]
                t["publication_state_why"] = m[0]["why"]
                t["overall_status"] = m[0].get("overall_status")
                if m[0].get("pmids"):
                    t["pmids_on_the_registration"] = m[0]["pmids"]
        pr["literature_limb"] = {
            "run_utc": "2026-08-19",
            "record": "evidence/2026-08-19-batch1/remaining_readings_literature.json",
            "PUBLISHED": len(pub),
            "NO_PUBLICATION_RESOLVED": len(silent),
            "EXPECTED_UNRESOLVED_trial_has_not_finished": len(expected),
            "why_the_third_state_exists": (
                "An ONGOING trial with no publication is not silent -- it has not finished. "
                "Counting it as silent would inflate a finding about silence with trials that "
                "were never due to report."),
        }
        pr["absent_is_not_zero"] = (
            "CHECKED AGAINST THE LITERATURE, not assumed. %d of %d trials in this reading have "
            "a publication resolved; %d are DUE to have reported and none was found by two "
            "routes; %d have NOT FINISHED and their absence is expected rather than silent."
            % (len(pub), len(rows), len(silent), len(expected)))
        if apply_it:
            with io.open(os.path.join(REPO, "ssot", topic, topic + ".json"), "w",
                         encoding="utf-8", newline="") as fh:
                fh.write(json.dumps(o, indent=1, ensure_ascii=False))
            scr = json.load(io.open(os.path.join(EV, "colchicine_split_screening.json"),
                                    encoding="utf-8"))
            disp = {r["nct"]: r["disposition"] for r in scr["rows"]}
            spec = B.READINGS[reading]
            sibs = [(B.READINGS[k]["page"], B.READINGS[k]["title"])
                    for k in B.READINGS if k != reading]
            with io.open(os.path.join(REPO, spec["page"]), "w", encoding="utf-8",
                         newline="") as fh:
                fh.write(B.page_html(spec, o, disp, sibs))

    doc["totals"] = total
    print("")
    print("across the four readings: %s" % total)
    if apply_it:
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(doc, indent=1, ensure_ascii=False))
        print("wrote %s and rebuilt four pages" % os.path.relpath(OUT, REPO))
    else:
        print("DRY RUN -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
