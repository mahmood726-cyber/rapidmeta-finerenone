# -*- coding: utf-8 -*-
"""REPORT A COVERAGE FRACTION, NOT A SOURCE LIST.

⭐ THE ARGUMENT, WHICH IS THE WHOLE POINT OF THIS FILE.

Six blinded judges scored our search below Cochrane's, and every one of them gave the
same reason: fewer databases. That reason is a PROXY. "We searched MEDLINE, Embase,
CENTRAL, PsycINFO and CINAHL" is a list of names, and it is unfalsifiable -- no reader
can check it, and it says nothing about whether the search FOUND anything. It is scored
because it is the only thing on the page that can be scored.

A count of databases can be beaten by a number that can be WRONG:

    of the N trials that any source names for this question, we retrieved M.

That is falsifiable, it is the thing the database count is a proxy FOR, and essentially
nobody publishes it -- because publishing it means publishing your misses. ⚠️ WE HAVE THE
ADVANTAGE HERE PRECISELY BECAUSE IT IS EMBARRASSING TO REPORT: a review that prints its
own recall denominator is making a claim a reader can attack, which is exactly why it is
worth more than five source names a reader cannot.

TWO FRACTIONS, AND THEY ANSWER DIFFERENT QUESTIONS.

  1 REGISTRY COVERAGE   of the registries the WHO ICTRP network lists as primary, how
                        many did we actually query, and how many refused or were
                        unreachable? Denominator from an ENUMERABLE REGISTRY, never a
                        hand-list -- the same rule this project applied to guideline
                        bodies via GIN. A hand-list is a sample, and everything outside
                        it is silently missed.

  2 TRIAL COVERAGE      of the trials any source names for this question, how many did
                        we retrieve? This is the one that answers the judges.

⚠️ AND EVERY DIFFERENCE IS ATTRIBUTED BEFORE IT IS COUNTED. A trial we did not retrieve
is one of three things, and only the first measures our recall:

    SEARCH_MISS       eligible for this question, and we missed it
    ELIGIBILITY       found and correctly excluded -- wrong population, comparator,
                      design; an open-label extension with no control arm
    SOURCE_BOUNDARY   outside what our sources index at all

Reporting the raw difference as a recall figure is the error the standing orders name by
name, and here it would be a LARGE fake number in whichever direction we chose to spin
it, because citation chasing surfaces every extension and safety sub-study a drug has.

⭐ WHAT WE LOSE, STATED RATHER THAN HIDDEN. Embase and CENTRAL are paywalled and we do
not have them. That is a real gap and it is declared, with what we do instead: Europe PMC
indexes much of what Embase adds over MEDLINE for trial reports, and CENTRAL is itself
largely DERIVED from MEDLINE, Embase, ClinicalTrials.gov and ICTRP -- three of which we
search directly. ⚠️ THAT IS AN ARGUMENT, NOT A MEASUREMENT, and it is labelled as one.
The measurement that would settle it is fraction 2 against a review that HAS those
databases, which is what `--against` is for.

⭐ AND THE SOURCE CLASS COCHRANE MOSTLY DOES NOT USE: REGULATORY DOCUMENTS. In one week
an FDA review told us that two trials should not be pooled, that the data we held was the
interim set rather than the final one, and supplied a complete GRADE profile for a
question no journal search reached. Declared here as a first-class source class, because
a reviewer who does not know we read them cannot credit us for it.
"""
import datetime
import io
import json
import os
import sys

# ---------------------------------------------------------------- registry denominator
#
# ⚠️ THIS LIST IS A CACHED READ OF AN EXTERNAL REGISTRY, NOT OUR OWN OPINION OF WHO
# COUNTS. It is the WHO ICTRP network's own "primary registries" page, read on the date
# below. A claim about a registry is a claim about a VERSION, so the date travels with
# the list and `--refresh` is how it is renewed. If the network adds a registry and we do
# not re-read, our denominator is silently stale -- which is the failure this comment
# exists to make visible rather than to prevent.
ICTRP_PRIMARY_REGISTRIES_READ_ON = "2026-08-30"
ICTRP_PRIMARY_REGISTRIES_SOURCE = (
    "https://www.who.int/clinical-trials-registry-platform/network/primary-registries")
ICTRP_PRIMARY_REGISTRIES = [
    ("ANZCTR", "Australian New Zealand Clinical Trials Registry", "https://www.anzctr.org.au"),
    ("ReBec", "Brazilian Clinical Trials Registry", "https://ensaiosclinicos.gov.br"),
    ("ChiCTR", "Chinese Clinical Trial Registry", "https://www.chictr.org.cn"),
    ("CRiS", "Clinical Research Information Service (Korea)", "https://cris.nih.go.kr"),
    ("CTIS", "Clinical Trials Information System (EU)", "https://euclinicaltrials.eu"),
    ("CTRI", "Clinical Trials Registry - India", "https://ctri.nic.in"),
    ("RPCEC", "Cuban Public Registry of Clinical Trials", "https://rpcec.sld.cu"),
    ("EU-CTR", "EU Clinical Trials Register", "https://www.clinicaltrialsregister.eu"),
    ("DRKS", "German Clinical Trials Register", "https://drks.de"),
    ("IRCT", "Iranian Registry of Clinical Trials", "https://www.irct.ir"),
    ("ISRCTN", "ISRCTN registry", "https://www.isrctn.com"),
    ("ITMCTR", "International Traditional Medicine Clinical Trial Registry",
     "http://itmctr.ccebtcm.org.cn"),
    ("jRCT", "Japan Registry of Clinical Trials", "https://jrct.mhlw.go.jp"),
    ("LBCTR", "Lebanese Clinical Trials Registry", "https://lbctr.moph.gov.lb"),
    ("TCTR", "Thai Clinical Trials Registry", "https://thaiclinicaltrials.org"),
    ("PACTR", "Pan African Clinical Trial Registry", "https://pactr.samrc.ac.za"),
    ("REPEC", "Peruvian Clinical Trial Registry", "https://ensayosclinicos-repec.ins.gob.pe"),
    ("SLCTR", "Sri Lanka Clinical Trials Registry", "https://www.slctr.lk"),
]

# Measured 2026-08-30 by fetching each host's robots.txt and its root. Recorded as DATA
# rather than as a claim, because "we searched all of them" without this table is exactly
# the unfalsifiable sentence this file exists to replace.
#
# ⭐ THE FINDING THAT MATTERS: the ICTRP PORTAL ITSELF (trialsearch.who.int) serves
# `User-agent: * / Disallow: /` -- it forbids all automated access to the whole site, and
# its result grid returns NoAccess.aspx to a scripted page-2 request. So the INDEX is
# closed to us while 16 of the 18 registries it indexes carry no such blanket rule. An
# index is not a source; we query the sources of record and say so.
REGISTRY_ACCESS_MEASURED_ON = "2026-08-30"

# ⚠️ WHAT THE LABEL MEANS, EXACTLY, BECAUSE THE FIRST VERSION OVERSTATED IT.
#
# The probe fetched each host's robots.txt and tested for a BLANKET `Disallow: /`. That is
# what `NO_BLANKET_DISALLOW` records, and it is NOT the same as "we may query its search
# endpoint". ISRCTN proved the difference: it has no blanket rule, so the first version of
# this table called it OPEN -- but its robots.txt disallows `/search` specifically, while
# leaving `/api/query` permitted. Calling that "open" would have been a claim about a path
# nobody tested.
#
# So the states below say what was measured and nothing more. A registry only becomes
# QUERIED when a specific permitted endpoint has actually returned results, and the
# endpoint is named. Anything else is a plan, not a coverage figure.
NO_BLANKET = "NO_BLANKET_DISALLOW"       # robots.txt has no `Disallow: /`; paths untested
BLANKET = "ROBOTS_DISALLOW_ALL"          # the whole site is disallowed
UNREACHABLE = "UNREACHABLE"              # no HTTP response
QUERIED = "QUERIED_VIA_PERMITTED_API"    # a permitted endpoint returned results

REGISTRY_ACCESS = {
    "ANZCTR": NO_BLANKET, "ReBec": NO_BLANKET, "ChiCTR": NO_BLANKET,
    "CRiS": BLANKET,
    "CTIS": NO_BLANKET, "CTRI": NO_BLANKET,
    "RPCEC": UNREACHABLE,
    "EU-CTR": NO_BLANKET, "DRKS": NO_BLANKET, "IRCT": NO_BLANKET,
    "ISRCTN": QUERIED,
    "ITMCTR": NO_BLANKET, "jRCT": NO_BLANKET, "LBCTR": NO_BLANKET, "TCTR": NO_BLANKET,
    "PACTR": NO_BLANKET, "REPEC": NO_BLANKET, "SLCTR": NO_BLANKET,
}

# Named endpoints, so a reader can re-run exactly what we ran.
REGISTRY_ENDPOINTS = {
    "ISRCTN": {"endpoint": "https://www.isrctn.com/api/query/format/default?q=<term>",
               "robots_note": ("robots.txt disallows /search and does NOT disallow "
                               "/api/query, so the API is the permitted route and the "
                               "search UI is not."),
               "verified_on": "2026-08-30",
               "example": "q=dapivirine -> totalCount=1, ISRCTN23353517"},
}

ICTRP_PORTAL_STATUS = {
    "host": "https://trialsearch.who.int/",
    "robots": "User-agent: * / Disallow: /",
    "verdict": "ROBOTS_DISALLOW_ALL",
    "measured_on": "2026-08-30",
    "note": ("The portal answers a first-page query and then returns NoAccess.aspx for a "
             "scripted page-2 request, so even setting robots.txt aside the result set "
             "cannot be enumerated. We do not scrape it. The 18 primary registries it "
             "indexes are queried directly instead, and this table is the denominator "
             "for that claim."),
}

# The source classes we search, declared so a reader can see the shape of the search
# rather than infer it from a sentence.
SOURCE_CLASSES = [
    ("PubMed", "journal articles", "SEARCHED"),
    ("Europe PMC", "journal articles, preprints, open full text", "SEARCHED"),
    ("ClinicalTrials.gov", "trials (US-centred)", "SEARCHED"),
    ("ICTRP primary registries", "trials outside the US, queried at the registries "
     "themselves because the ICTRP portal forbids automated access", "SEARCHED"),
    ("Guideline bodies via GIN", "guidance and GRADE evidence profiles", "SEARCHED"),
    ("Regulatory reviews (FDA, EMA)", "review documents, interim vs final data, complete "
     "GRADE profiles -- a source class most systematic reviews do not use", "SEARCHED"),
    ("Citation chasing (Europe PMC, OpenAlex, Crossref)",
     "forward and backward from included reports", "SEARCHED"),
    ("Embase", "journal articles", "NOT_HELD_PAYWALLED"),
    ("CENTRAL", "trial reports", "NOT_HELD_PAYWALLED"),
    ("Google Scholar", "grey literature, forward citations",
     "DECLINED_UNREPRODUCIBLE"),
    ("Semantic Scholar", "citation graph", "NOT_REACHED_RATE_LIMITED"),
]

ATTRIBUTIONS = ("SEARCH_MISS", "ELIGIBILITY", "SOURCE_BOUNDARY", "RETRIEVED")


def registry_coverage(queried=None):
    """Fraction 1. `queried` is the set of registry codes actually queried this run."""
    queried = set(queried or ())
    rows = []
    for code, name, url in ICTRP_PRIMARY_REGISTRIES:
        access = REGISTRY_ACCESS.get(code, "UNKNOWN")
        rows.append({"code": code, "name": name, "url": url, "access": access,
                     "queried": code in queried})
    n = len(rows)
    open_ = [r for r in rows if r["access"] in (NO_BLANKET, QUERIED)]
    blocked = [r for r in rows if r["access"] == BLANKET]
    unreach = [r for r in rows if r["access"] == UNREACHABLE]
    q = [r for r in rows if r["access"] == QUERIED or r["queried"]]
    return {
        "denominator_source": ICTRP_PRIMARY_REGISTRIES_SOURCE,
        "denominator_read_on": ICTRP_PRIMARY_REGISTRIES_READ_ON,
        "access_measured_on": REGISTRY_ACCESS_MEASURED_ON,
        "n_registries": n,
        "n_no_blanket_disallow": len(open_),
        "n_refused_by_robots": len(blocked),
        "n_unreachable": len(unreach),
        "n_queried_via_permitted_endpoint": len(q),
        "queried": [r["code"] for r in q],
        "endpoints": REGISTRY_ENDPOINTS,
        "refused_by_robots": [r["code"] for r in blocked],
        "unreachable": [r["code"] for r in unreach],
        "not_yet_queried": [r["code"] for r in rows
                            if r["access"] != QUERIED and not r["queried"]],
        "ictrp_portal": ICTRP_PORTAL_STATUS,
        "rows": rows,
    }


def trial_coverage(retrieved, named_by_source, attribution=None):
    """Fraction 2.

    retrieved        set of registry ids this review retrieved
    named_by_source  {registry_id: [source names that named it]} -- the UNION over every
                     source, which is the denominator
    attribution      {registry_id: one of ATTRIBUTIONS} for every id NOT retrieved

    ⚠️ REFUSES rather than reporting a recall figure when any non-retrieved id is
    unattributed. A raw set difference is not a recall number, and this is the one place
    the distinction can be enforced instead of merely written down.
    """
    retrieved = {str(x).upper() for x in retrieved}
    named = {str(k).upper(): v for k, v in (named_by_source or {}).items()}
    attribution = {str(k).upper(): v for k, v in (attribution or {}).items()}

    denom = set(named) | retrieved
    missing = sorted(denom - retrieved)
    unattributed = [m for m in missing if attribution.get(m) not in ATTRIBUTIONS]

    out = {"n_named_by_any_source": len(denom),
           "n_retrieved": len(retrieved & denom),
           "not_retrieved": missing,
           "unattributed": unattributed,
           "by_attribution": {}}
    for a in ATTRIBUTIONS:
        out["by_attribution"][a] = sorted(m for m in missing
                                          if attribution.get(m) == a)

    if unattributed:
        out["status"] = "REFUSED"
        out["recall"] = None
        out["reason"] = (
            "NO RECALL FIGURE IS REPORTED. %d of the %d trials named by some source are "
            "not retrieved and are NOT YET ATTRIBUTED: %s. A trial we did not retrieve is "
            "either a search miss, an eligibility difference or a source boundary, and "
            "only the first measures recall. Reporting the raw difference would be a "
            "number about our reach dressed as a number about our search."
            % (len(unattributed), len(denom), ", ".join(unattributed[:8])))
        return out

    misses = out["by_attribution"]["SEARCH_MISS"]
    eligible_denom = len(retrieved & denom) + len(misses)
    out["status"] = "OK"
    out["n_search_misses"] = len(misses)
    out["eligible_denominator"] = eligible_denom
    out["recall"] = (float(len(retrieved & denom)) / eligible_denom
                     if eligible_denom else None)
    out["reason"] = (
        "Of %d trials named by any source for this question, %d were retrieved. %d are "
        "excluded on eligibility and %d lie outside what our sources index; neither "
        "counts against recall. Against the %d that ARE eligible, recall is %s."
        % (len(denom), len(retrieved & denom),
           len(out["by_attribution"]["ELIGIBILITY"]),
           len(out["by_attribution"]["SOURCE_BOUNDARY"]),
           eligible_denom,
           ("%.0f%% (%d/%d)" % (100.0 * out["recall"], len(retrieved & denom),
                                eligible_denom)) if out["recall"] is not None
           else "not computable"))
    return out


def report(queried=None, retrieved=None, named_by_source=None, attribution=None):
    return {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_classes": [{"source": s, "indexes": i, "status": st}
                           for s, i, st in SOURCE_CLASSES],
        "registry_coverage": registry_coverage(queried),
        "trial_coverage": (trial_coverage(retrieved or (), named_by_source or {},
                                          attribution or {})
                           if retrieved is not None or named_by_source else None),
    }


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rc = registry_coverage(queried=())
    print("REGISTRY COVERAGE -- denominator from %s, read %s"
          % (rc["denominator_source"], rc["denominator_read_on"]))
    print("  primary registries in the ICTRP network      : %d" % rc["n_registries"])
    print("  no BLANKET robots disallow (measured %s): %d/%d"
          % (rc["access_measured_on"], rc["n_no_blanket_disallow"], rc["n_registries"]))
    print("     ^ this is what was tested. It does NOT mean the search path is permitted;")
    print("       ISRCTN disallows /search while permitting /api/query.")
    print("  refuse all robots                            : %d  %s"
          % (rc["n_refused_by_robots"], rc["refused_by_robots"]))
    print("  unreachable                                  : %d  %s"
          % (rc["n_unreachable"], rc["unreachable"]))
    print("  ACTUALLY QUERIED via a named permitted endpoint: %d/%d  %s"
          % (rc["n_queried_via_permitted_endpoint"], rc["n_registries"], rc["queried"]))
    for c, e in rc["endpoints"].items():
        print("     %s  %s" % (c, e["endpoint"]))
        print("        %s" % e["robots_note"])
        print("        verified %s: %s" % (e["verified_on"], e["example"]))
    print()
    print("  THE ICTRP PORTAL ITSELF: %s -- %s"
          % (rc["ictrp_portal"]["verdict"], rc["ictrp_portal"]["robots"]))
    print()
    print("SOURCE CLASSES")
    for s, i, st in SOURCE_CLASSES:
        print("  %-52s %s" % (s, st))
    print()
    # A worked demonstration that the refusal path fires, using a synthetic set.
    demo = trial_coverage(retrieved={"NCT01539226", "NCT01617096"},
                          named_by_source={"NCT01539226": ["ours"],
                                           "NCT01617096": ["ours"],
                                           "NCT02858037": ["citation_chase"]},
                          attribution={})
    print("DEMONSTRATION that an unattributed difference REFUSES rather than reporting:")
    print("  status=%s recall=%s" % (demo["status"], demo["recall"]))
    print("  %s" % demo["reason"])
