#!/usr/bin/env python3
"""DOES ONE PUBLICATION NAME MORE THAN ONE REGISTRATION? -- the only detector this class allows.

THE CLASS. A trial that registers its nested substudy separately appears in a registry-derived
review as TWO trials. `COLCHICINE-PCI` is the worked case: NCT02594111 (n=714) and NCT01709981
(n=280, the nested biomarker substudy), and PMID 32295417 closes its abstract "Unique
Identifiers: NCT02594111, NCT01709981."

WHY NO REGISTRY-ONLY METHOD CAN SEE IT. The duplicate detector in this project pairs
registrations on identical official title AND identical enrolment. Parent and substudy differ on
BOTH -- 280 against 714 -- so this is not a near-miss for that detector, it is out of its reach
entirely. The relationship is stated in exactly one place: THE PUBLICATION.

    A REGISTRY-DERIVED k IS AN OVERCOUNT BY AN UNKNOWN AMOUNT, and the correction is only
    available from the literature the review was avoiding.

SO THE DETECTOR IS THIS: for every publication resolved anywhere in this corpus, extract every
registration identifier appearing in its title, abstract or metadata, and flag any naming two or
more. It is a cheap extra field on work already being done and it is the only signal available.

AND A HIT IS NOT AUTOMATICALLY AN OVERCOUNT. Two shapes produce the same signal:

    PARENT_AND_SUBSTUDY   one trial, two registrations -> k IS INFLATED. (COLCHICINE-PCI)
    TWO_TRIALS_ONE_REPORT two genuinely separate trials reported together -> k is CORRECT,
                          but citing two references for them would be wrong. (SPIRE-1/SPIRE-2)

The detector cannot tell them apart and does not try. It surfaces the pair and names the
question; classification is a human read of the paper. Reporting a hit as an overcount without
that read would be the same error as reading a title match as an estimand.

USAGE
    python scripts/detect_multi_registration_publications.py [--apply]
"""
import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")
OUT = os.path.join(EV, "multi_registration_publications.json")

NCT = re.compile(r"NCT\d{8}")

# Classifications made by reading the paper. A pair not listed here is UNCLASSIFIED and is
# reported as a question, never as an overcount.
CLASSIFIED = {
    ("NCT01709981", "NCT02594111"): {
        "shape": "PARENT_AND_SUBSTUDY",
        "k_effect": "INFLATES k BY 1",
        "evidence": ("PMID 32295417: NCT01709981 (n=280, primary percent change in IL-6) is the "
                     "nested inflammatory biomarker substudy of NCT02594111 (n=714, primary "
                     "peri-procedural myocardial necrosis). One trial."),
    },
    ("NCT01975376", "NCT01975389"): {
        "shape": "TWO_TRIALS_ONE_REPORT",
        "k_effect": "k IS CORRECT -- these are two genuinely separate trials",
        "evidence": ("PMID 28304242: SPIRE-1 (n=16,784) and SPIRE-2 (n=10,564), both terminated "
                     "early and reported together. Two trials, one paper. Citing two references "
                     "for them would be wrong; counting them as one trial would also be wrong."),
    },
    ("NCT03104413", "NCT03105128"): {
        "shape": "TWO_TRIALS_ONE_REPORT",
        "k_effect": "k IS CORRECT",
        "evidence": ("PMID 35644154: ADVANCE (n=931) and MOTIVATE (n=618), two induction trials "
                     "reported in one paper."),
    },
}


def registry_side_pairs():
    """A PMID listed by TWO OR MORE registrations is the same signal, from the registry alone.

    THE CHEAPER ROUTE, AND A DIFFERENT ONE. Scanning 258 abstracts for registration identifiers
    answers "does this paper name two trials". Asking which PMIDs appear on more than one
    registration's reference list answers the same question from the other side, over EVERY
    trial in the corpus rather than only those whose abstracts we happened to fetch.

    ITS BLIND SPOT IS NAMED. It requires BOTH registrations to list the shared publication. Where
    only the parent lists it -- which is common, because a substudy registration is often
    abandoned after the parent reports -- the pair is invisible to this route and visible only to
    the abstract scan. NEITHER ROUTE DOMINATES; both are lower bounds and they miss different
    things.
    """
    import ctgov_transport as X
    ncts = set()
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        try:
            with io.open(p, "r", encoding="utf-8") as fh:
                o = json.load(fh)
        except Exception:
            continue
        for t in ((o.get("inputs") or {}).get("trials") or []):
            if isinstance(t, dict) and t.get("nct"):
                ncts.add(t["nct"])
        ncts |= set(NCT.findall(json.dumps(o.get("screening") or {})))
    ncts = sorted(n for n in ncts if NCT.fullmatch(n))
    by_pmid, unreachable = {}, []
    for i, n in enumerate(ncts):
        st, s, d = X.fetch_raw(n, fields="protocolSection")
        if st != X.OK:
            unreachable.append(n)
            continue
        refs = (((s.get("protocolSection") or {}).get("referencesModule") or {})
                .get("references") or [])
        for r in refs:
            if r.get("pmid"):
                by_pmid.setdefault(r["pmid"], {})[n] = r.get("type")
        if (i + 1) % 50 == 0:
            print("   ...%d/%d registrations read" % (i + 1, len(ncts)))
    return ncts, by_pmid, unreachable


def scan(records):
    """records: {pmid: {'title':..., 'abstract':..., 'ncts':[...]}}"""
    out = []
    for pmid, r in sorted(records.items()):
        ids = sorted(set(r.get("ncts") or []))
        if len(ids) < 2:
            continue
        key = tuple(sorted(ids))
        cls = CLASSIFIED.get(key)
        out.append({
            "pmid": pmid,
            "title": r.get("title"),
            "registration_identifiers_named": ids,
            "n_named": len(ids),
            "classification": cls or {
                "shape": "UNCLASSIFIED",
                "k_effect": "UNKNOWN -- requires a human read of the paper",
                "evidence": ("The detector surfaces the pair and names the question. It cannot "
                             "distinguish parent-and-substudy from two-trials-one-report and "
                             "does not try."),
            },
        })
    return out


def run(apply_it):
    sys.path.insert(0, os.path.join(REPO, "ssot"))
    print("reading every registration named in an ssot object ...")
    ncts, by_pmid, unreachable = registry_side_pairs()
    print("registrations read: %d  (unreachable %d)" % (len(ncts) - len(unreachable),
                                                        len(unreachable)))
    print("distinct PMIDs on their reference lists: %d" % len(by_pmid))

    # STRATIFY BY REFERENCE TYPE, because the raw count is dominated by noise. A registration
    # citing someone else's landmark paper as BACKGROUND is not a paper reporting that trial --
    # PMID 9725923 is listed by SEVEN registrations and is plainly a shared citation. The
    # informative stratum is RESULT and DERIVED: the registration's own report.
    #
    #   AND THE TYPE FILTER IS WRONG IN THE OTHER DIRECTION TOO, which is why both strata are
    #   reported. CLEAR Outcomes' own primary is typed BACKGROUND on its own registration, so a
    #   RESULT/DERIVED restriction can miss a real self-report. Neither stratum is the answer;
    #   the RESULT/DERIVED one is the one worth a human read.
    shared = {p: v for p, v in by_pmid.items() if len(v) > 1}
    hits = []
    for pmid, byn in sorted(shared.items()):
        ids = sorted(byn)
        own = sorted(n for n, t in byn.items() if t in ("RESULT", "DERIVED"))
        # MATCH ON SUBSET, NOT ON THE EXACT TUPLE. The worked case failed an exact-tuple lookup
        # because a THIRD registration (NCT05739929) also cites PMID 32295417 -- as background.
        # A classification about two registrations must still apply when a third cites the paper.
        cls = None
        for key, val in CLASSIFIED.items():
            if set(key) <= set(ids):
                cls = dict(val)
                cls["classified_pair"] = list(key)
                if len(ids) > len(key):
                    cls["note"] = ("%d further registration(s) also cite this PMID: %s. The "
                                   "classification concerns the named pair only."
                                   % (len(ids) - len(key),
                                      ", ".join(sorted(set(ids) - set(key)))))
                break
        hits.append({
            "pmid": pmid,
            "registrations_listing_it": ids,
            "n_registrations": len(ids),
            "reference_type_per_registration": byn,
            "registrations_listing_it_as_their_OWN_report": own,
            "n_listing_it_as_their_own_report": len(own),
            "stratum": ("SELF_REPORT_BY_TWO_OR_MORE" if len(own) > 1 else
                        "SHARED_CITATION_ONLY -- at most one registration calls this its own "
                        "report; the others cite it as BACKGROUND"),
            "classification": cls or {
                "shape": "UNCLASSIFIED",
                "k_effect": "UNKNOWN -- requires a human read of the paper",
                "evidence": ("The detector surfaces the pair and names the question. It cannot "
                             "distinguish parent-and-substudy from two-trials-one-report."),
            },
        })

    informative = [h for h in hits if h["n_listing_it_as_their_own_report"] > 1]
    infl = [h for h in hits if h["classification"]["shape"] == "PARENT_AND_SUBSTUDY"]
    twot = [h for h in hits if h["classification"]["shape"] == "TWO_TRIALS_ONE_REPORT"]
    unkn = [h for h in hits if h["classification"]["shape"] == "UNCLASSIFIED"]

    doc = {
        "scanned_utc": "2026-08-19",
        "what_this_enumerated_over": {
            "route": ("ClinicalTrials.gov referencesModule for EVERY registration named in an "
                      "ssot object's included set or screening record"),
            "n_registrations_read": len(ncts) - len(unreachable),
            "n_unreachable": len(unreachable),
            "unreachable": unreachable,
            "n_distinct_pmids": len(by_pmid),
            "blind_spot_NAMED": (
                "This route requires BOTH registrations to list the shared publication. Where "
                "only the parent lists it -- common, because a substudy registration is often "
                "abandoned once the parent reports -- the pair is INVISIBLE here and visible "
                "only to an abstract scan. Neither route dominates; both are lower bounds and "
                "they miss different things."),
            "routes_NOT_run": ["abstract/full-text scan for registration identifiers across all "
                               "258 PMIDs this corpus has resolved"],
        },
        "a_hit_is_not_automatically_an_overcount": {
            "PARENT_AND_SUBSTUDY": "one trial, two registrations -> k IS INFLATED",
            "TWO_TRIALS_ONE_REPORT": "two separate trials reported together -> k is CORRECT",
            "so": ("Reporting a hit as an overcount without reading the paper would be the same "
                   "error as reading a title match as an estimand."),
        },
        "counts": {
            "publications_listed_by_more_than_one_registration": len(hits),
            "OF_WHICH_two_or_more_call_it_their_OWN_report": len(informative),
            "the_rest_are_shared_citations": len(hits) - len(informative),
            "classified_PARENT_AND_SUBSTUDY": len(infl),
            "classified_TWO_TRIALS_ONE_REPORT": len(twot),
            "UNCLASSIFIED": len(unkn),
            "k_inflation_confirmed_so_far": len(infl),
        },
        "hits_informative_stratum": informative,
        "hits_all": hits,
        "status": "LOWER BOUND -- see blind_spot_NAMED.",
    }
    print("")
    print("publications listed by MORE THAN ONE registration: %d" % len(hits))
    print("   of which TWO OR MORE call it their OWN report (RESULT/DERIVED): %d" % len(informative))
    print("   the rest are shared citations (BACKGROUND): %d" % (len(hits) - len(informative)))
    print("")
    print("THE INFORMATIVE STRATUM:")
    for h in informative:
        print("   PMID %-9s %-30s %s"
              % (h["pmid"], ",".join(h["registrations_listing_it"]),
                 h["classification"]["shape"]))
    print("")
    print("   PARENT_AND_SUBSTUDY (k inflated) : %d" % len(infl))
    print("   TWO_TRIALS_ONE_REPORT (k correct): %d" % len(twot))
    print("   UNCLASSIFIED (needs a read)      : %d" % len(unkn))

    if apply_it:
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(doc, indent=1, ensure_ascii=False))
        print("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
