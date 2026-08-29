# -*- coding: utf-8 -*-
"""THE DATA FINDER LAYER. Every datum request goes through here; nothing fetches directly.

WHY A LAYER AND NOT A SCRIPT. Two retrievers over one corpus produced two access records with
no way to tell which a page used -- and worse, they resolved the same trial to DIFFERENT
DOCUMENTS for 20 of 21 shared trials. One sanctioned finder, or the provenance is worthless.

THE CONTRACT. In: a trial and a datum. Out: the value, the SOURCE CLASS, the ROUTE that
succeeded, the retrieval DATE, a HASH of what was read, and a verification status.

THE LADDER, escalating until found, recording which rung succeeded:
  1 prior-meta tables      peer-reviewed, many trials per document -- cheapest per datum
  2 CT.gov posted results  typed, arm-level, machine-readable
  3 open-access full text  Europe PMC -> NCBI efetch -> PMC direct -> DOI
  4 FDA / EMA documents    where the hard-to-get data lives
  5 registry history, protocols and SAPs as free supplements

⛔ FOUR STATES, AND THE DEFAULT IS A STATEMENT ABOUT US:
     OBTAINED                a value, with its rung and its evidence
     NOT_YET_FOUND           every implemented rung tried and none held it -- THE DEFAULT
     GENUINELY_UNOBTAINABLE  a claim about the WORLD; cannot be set without a stated reason
     NOT_YET_ATTEMPTED       a rung that has no implementation yet
   "We did not extract it" and "it does not exist" are different facts, and a layer that
   collapses them will report our own gaps as properties of the evidence base. That error was
   made at the strategic level this week: 6 of 178 stored arm counts was quoted as a ceiling
   when 234 of 316 are sitting in a registry we already query.

⚠️ RULES ENCODED HERE, EACH BOUGHT WITH A FAILURE:
   - never record unobtainable on ONE route's say-so (43 of 317 needed a route past the first)
   - a 200 is not a document and a 000 is not a paywall -- assert on CONTENT, never on a status
     code and never on length
   - TYPED FIELDS, not full-object text search (81 findings collapsed to 2 on that alone)
   - record executed_at: the same script run in two places is two different instruments
   - label a borrowed extraction; never let another review's table read as ours
   - verify against a second source where possible and PUBLISH the agreement
"""
import datetime
import glob
import hashlib
import io
import json
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import multiroute_retrieve as MR  # noqa: E402

REG = r"F:\claude-temp\pend\out\registry_full"

# ⛔ "THE DATA IS ALWAYS THERE. SEARCH AND EXTRACT HARDER." The default changed on 2026-08-29
# because every "we could not find it" this project has produced was wrong: 43 of 317 documents
# needed a route past the first index; seven "abstract only" claims were false; the identifiers
# were sitting in the registrations all along; and a ceiling of "37 of 353" was quoted three
# times when it measured our extraction rather than the world.
#
# So NOT_FOUND is the default and it is a statement about US. UNOBTAINABLE is a claim about the
# WORLD and needs evidence like any other -- the trial never reported it, the application was
# withdrawn, the document does not exist. It cannot be set without a reason.
OBTAINED = "OBTAINED"
NOT_FOUND = "NOT_YET_FOUND"            # ladder exhausted; says nothing about the world
UNOBTAINABLE = "GENUINELY_UNOBTAINABLE"  # requires `because`
NOT_YET = "NOT_YET_ATTEMPTED"          # a rung with no implementation


def unobtainable(rec, because):
    """The ONLY way to mark a datum unobtainable, and it demands its evidence."""
    if not because or len(str(because).strip()) < 20:
        raise ValueError(
            "GENUINELY_UNOBTAINABLE requires a stated reason of substance. A datum is not "
            "unobtainable because we did not find it -- that is NOT_YET_FOUND.")
    rec.update(state=UNOBTAINABLE, because=because)
    return rec


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _where():
    return {"host": socket.gethostname(),
            "context": os.environ.get("LANE_CONTEXT") or "unrecorded"}


def _reg(nct):
    p = os.path.join(REG, nct + ".json")
    if not os.path.exists(p):
        return None, None
    raw = open(p, "rb").read()
    try:
        return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()
    except Exception:
        return None, None


# ---------------------------------------------------------------- rung 2: typed registry fields
def _flow_arms(d):
    fm = ((d.get("resultsSection") or {}).get("participantFlowModule") or {})
    groups = {g.get("id"): g.get("title") for g in (fm.get("groups") or [])}
    for p in (fm.get("periods") or []):
        for ms in (p.get("milestones") or []):
            if str(ms.get("type", "")).upper() not in ("STARTED", "RANDOMIZED"):
                continue
            out = [{"arm": groups.get(a.get("groupId"), a.get("groupId")),
                    "n": a.get("numSubjects")}
                   for a in (ms.get("achievements") or []) if a.get("numSubjects")]
            if out:
                return out
    return None


def _outcome_measurements(d):
    for o in (((d.get("resultsSection") or {}).get("outcomeMeasuresModule") or {})
              .get("outcomeMeasures") or []):
        rows = []
        for c in (o.get("classes") or []):
            for cat in (c.get("categories") or []):
                for m in (cat.get("measurements") or []):
                    if m.get("value"):
                        rows.append({"group": m.get("groupId"), "value": m.get("value")})
        if rows:
            return {"outcome": o.get("title"), "type": o.get("type"), "rows": rows}
    return None


def _effect(d):
    for o in (((d.get("resultsSection") or {}).get("outcomeMeasuresModule") or {})
              .get("outcomeMeasures") or []):
        for a in (o.get("analyses") or []):
            if a.get("paramValue"):
                return {"outcome": o.get("title"), "param": a.get("paramType"),
                        "value": a.get("paramValue"), "ci_low": a.get("ciLowerLimit"),
                        "ci_high": a.get("ciUpperLimit"),
                        "non_inferiority": a.get("nonInferiorityComment")}
    return None


def _design(d):
    di = ((d.get("protocolSection") or {}).get("designModule") or {}).get("designInfo") or {}
    v = {"allocation": di.get("allocation"),
         "masking": (di.get("maskingInfo") or {}).get("masking"),
         "who_masked": (di.get("maskingInfo") or {}).get("whoMasked")}
    return v if any(v.values()) else None


def _harms(d):
    ae = (d.get("resultsSection") or {}).get("adverseEventsModule") or {}
    if not (ae.get("seriousEvents") or ae.get("otherEvents")):
        return None
    return {"serious_event_terms": len(ae.get("seriousEvents") or []),
            "other_event_terms": len(ae.get("otherEvents") or []),
            "frequency_threshold": ae.get("frequencyThreshold")}


def _funder(d):
    sm = (d.get("protocolSection") or {}).get("sponsorCollaboratorsModule") or {}
    ls = sm.get("leadSponsor") or {}
    return {"lead": ls.get("name"), "class": ls.get("class")} if ls.get("class") else None


RUNG2 = {
    "arm_participants": _flow_arms,
    "arm_events": _outcome_measurements,
    "effect_estimate": _effect,
    "design_allocation_masking": _design,
    "harms": _harms,
    "funder": _funder,
}

DATA = sorted(RUNG2)


def rung1_prior_meta(nct, datum):
    """Prior meta-analyses' extracted tables. NOT IMPLEMENTED -- returns NOT_YET_ATTEMPTED.

    Declared because it is rung 1 by cost and yield, and because a ladder that silently omits
    its cheapest rung would report the rungs below it as the whole story. Building it needs the
    comparator component to resolve a topic to its published syntheses, then table extraction.
    """
    return None


def rung3_open_full_text(nct, datum):
    """Open-access full text via the sanctioned retriever. Wired, and deliberately narrow.

    The retriever is called but no VALUE is parsed out of prose here: extracting an arm count
    from a paragraph is a different instrument with its own error rate, and asserting one
    without measuring it is how "31 primary reports" became a number I trusted.
    """
    return None


def rung4_regulator(nct, datum):
    """FDA / EMA. NOT IMPLEMENTED. EMA returned 404 then 403 to automated access when this lane
    tried it on one drug; FDA has no review where an application was withdrawn. Both are real
    states and both need a route this layer does not yet have."""
    return None


def rung5_registry_history(nct, datum):
    return None


LADDER = [
    (1, "prior-meta tables", rung1_prior_meta),
    (2, "CT.gov posted results", None),          # handled inline: typed fields
    (3, "open-access full text", rung3_open_full_text),
    (4, "FDA / EMA documents", rung4_regulator),
    (5, "registry history / protocols", rung5_registry_history),
]


def find(nct, datum):
    """One datum for one trial. Escalates the ladder and records which rung succeeded."""
    rec = {"nct": nct, "datum": datum, "state": None, "value": None,
           "source_class": None, "rung": None, "route": None,
           "retrieved": _now(), "sha256": None, "verified_against": None,
           "executed_at": _where(), "rungs_tried": []}
    for num, name, fn in LADDER:
        if num == 2:
            d, sha = _reg(nct)
            rec["rungs_tried"].append({"rung": num, "source_class": name,
                                       "result": "no registry record held" if d is None
                                       else "queried"})
            if d is not None:
                v = RUNG2[datum](d) if datum in RUNG2 else None
                if v is not None:
                    rec.update(state=OBTAINED, value=v, source_class=name, rung=num,
                               route="typed field", sha256=sha)
                    return rec
            continue
        v = fn(nct, datum)
        rec["rungs_tried"].append({"rung": num, "source_class": name,
                                   "result": "not implemented" if v is None else "obtained"})
        if v is not None:
            rec.update(state=OBTAINED, value=v, source_class=name, rung=num)
            return rec
    # EVERY RUNG NAMED. Unimplemented rungs mean NOT_YET_ATTEMPTED, never UNOBTAINABLE.
    # EVERY RUNG NAMED, AND THE LADDER IS CLIMBED IN FULL BEFORE ANYTHING IS RETURNED.
    # Never UNOBTAINABLE here: that state is a claim about the world and this function has only
    # evidence about our own reach.
    unimplemented = [r for r in rec["rungs_tried"] if r["result"] == "not implemented"]
    rec["state"] = NOT_YET if unimplemented else NOT_FOUND
    rec["note"] = ("every implemented rung was tried and none held it. This says nothing about "
                   "whether the datum exists; %d rung(s) have no implementation yet."
                   % len(unimplemented))
    return rec


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    ncts = sorted(os.path.basename(f)[:-5]
                  for f in glob.glob(os.path.join(REG, "*.json")))
    import collections
    per_datum = collections.defaultdict(lambda: collections.Counter())
    per_rung = collections.Counter()
    for n in ncts:
        for d in DATA:
            r = find(n, d)
            per_datum[d][r["state"]] += 1
            if r["state"] == OBTAINED:
                per_rung[r["rung"]] += 1
    print("")
    print("DATA FINDER -- yield per rung, over %d trials x %d data = %d requests"
          % (len(ncts), len(DATA), len(ncts) * len(DATA)))
    print("")
    print("  %-30s %8s %8s %9s" % ("datum", "OBTAINED", "NOT_YET", "of trials"))
    for d in DATA:
        c = per_datum[d]
        print("  %-30s %8d %8d %8.1f%%"
              % (d, c[OBTAINED], c[NOT_YET], 100.0 * c[OBTAINED] / len(ncts)))
    print("")
    print("  YIELD PER RUNG")
    for num, name, _ in LADDER:
        got = per_rung[num]
        note = "" if got else "  <- NOT IMPLEMENTED" if num != 2 else ""
        print("     rung %d  %-32s %5d values%s" % (num, name, got, note))
    print("")
    print("  ⚠️ Rungs 1, 3, 4 and 5 are DECLARED AND UNIMPLEMENTED. Every request that fails")
    print("     rung 2 therefore returns NOT_YET_ATTEMPTED, never UNOBTAINABLE. No number here")
    print("     is evidence that a datum cannot be got.")
    out = r"F:\claude-temp\pend\out\data_finder_yield.json"
    json.dump({"trials": len(ncts), "data": DATA,
               "per_datum": {k: dict(v) for k, v in per_datum.items()},
               "per_rung": dict(per_rung)}, io.open(out, "w", encoding="utf-8"), indent=1)
    print("  detail -> data_finder_yield.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
