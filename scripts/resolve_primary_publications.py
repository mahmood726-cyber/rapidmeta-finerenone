#!/usr/bin/env python3
"""RESOLVE THE PRIMARY PUBLICATION FOR EVERY INCLUDED TRIAL -- a reusable step, not a one-off.

WHAT THIS IS FOR. A topic that publishes an estimate should carry, for each included trial, the
PRIMARY PUBLICATION it was read from: the registration id, the PMID, the DOI, the lookup date
and the ROUTE the identifier came by. This was first done by hand for a submission reference
list; it is a method, so it belongs in the per-topic unit.

THREE TRAPS ALREADY FOUND JUSTIFY IT, and each one is invisible to recall:

  A SHARED PUBLICATION ACROSS TWO REGISTRATIONS. SPIRE-1 (NCT01975376) and SPIRE-2
  (NCT01975389) have one joint report, PMID 28304242 -- both terminated early. ADVANCE
  (NCT03105128) and MOTIVATE (NCT03104413) likewise share PMID 35644154. CITING TWO REFERENCES
  FOR EITHER PAIR WOULD BE WRONG.

  TWO REPORTS OF ONE TRIAL DIFFERING BY A SINGLE DIGIT IN BOTH IDENTIFIERS. CLEAR SYNERGY
  published colchicine as PMID 39555823 / 10.1056/NEJMoa2405922 and spironolactone as PMID
  39555814 / 10.1056/NEJMoa2405923 -- same journal, same day. Citing the wrong one attributes a
  mineralocorticoid-antagonist result to colchicine.

  A PRIMARY REPORT TYPED `BACKGROUND`. CLEAR Outcomes' main paper (PMID 36876740) is typed
  BACKGROUND in its own registration. ONLY ONE TRIAL OF TWENTY-ONE CARRIED A SPONSOR-TYPED
  `RESULT` REFERENCE AT ALL. **A type filter would have missed it**, so this tool NEVER filters
  on reference type -- it returns every reference with its type and leaves the choice to a
  human.

AND THE FAILURE THIS PREVENTS. `pmid_lodoco2` recorded EAST-AFNET 4, an atrial-fibrillation
trial, in a colchicine benchmark -- five apart in the same NEJM week. `pmid_advance_motivate`
recorded an upadacitinib ulcerative-colitis paper -- twelve apart in the same Lancet volume.
Adjacency in a journal issue is the signature of an identifier written from memory.

USAGE
    python scripts/resolve_primary_publications.py <topic> [<topic> ...]
    python scripts/resolve_primary_publications.py --all
    python scripts/resolve_primary_publications.py --selftest

It writes `evidence/<date>/primary_publications_<topic>.json` and prints a table. It does NOT
modify any object: attaching the result to a topic is a merge, done deliberately.
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                            # noqa: E402

EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")


def trials_of(topic):
    p = os.path.join(REPO, "ssot", topic, topic + ".json")
    if not os.path.exists(p):
        return None, "no object on disk"
    with io.open(p, "r", encoding="utf-8") as fh:
        o = json.load(fh)
    if str(o.get("state") or "").upper() == "RETIRED":
        return None, "retired tombstone -- not a live topic"
    return ((o.get("inputs") or {}).get("trials") or []), None


def resolve_trial(t):
    """One trial's candidate publications. EVERY reference type is returned, never filtered."""
    nct = t.get("nct")
    name = t.get("name") or t.get("id")
    if not nct or not str(nct).upper().startswith("NCT"):
        return {"name": name, "registration": t.get("registry_id") or t.get("id") or nct,
                "state": "NOT_ON_CLINICALTRIALS_GOV",
                "why": ("This trial carries no ClinicalTrials.gov identifier. Its registration "
                        "lives on another registry, WHICH THIS TOOL DOES NOT SEARCH. Reported "
                        "as unresolved rather than approximated, and the registry that was not "
                        "searched is named.")}
    st, s, detail = X.fetch_raw(nct, fields="protocolSection")
    if st != X.OK:
        return {"name": name, "registration": nct, "state": "UNREACHABLE",
                "why": str(detail)[:160]}
    ps = s.get("protocolSection") or {}
    idm = ps.get("identificationModule") or {}
    refs = (ps.get("referencesModule") or {}).get("references") or []
    cands = [{"pmid": r.get("pmid"), "type": r.get("type"),
              "citation_as_the_registry_prints_it": (r.get("citation") or "")[:280]}
             for r in refs]
    by_type = {}
    for c in cands:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    return {
        "name": name, "registration": nct,
        "state": "RESOLVED_CANDIDATES" if cands else "NO_REFERENCES_ON_THE_REGISTRATION",
        "acronym_the_registration_declares": idm.get("acronym"),
        "brief_title": (idm.get("briefTitle") or "")[:160],
        "n_candidates": len(cands),
        "candidates_by_type": by_type,
        "candidates": cands,
        "how_to_choose": ("READ THE CITATION STRINGS. Do NOT filter on `type` -- CLEAR Outcomes' "
                          "primary report is typed BACKGROUND, and only 1 of 21 trials checked "
                          "carried a sponsor-typed RESULT reference at all. Do NOT take the "
                          "first: that is P35 one level down."),
        "lookup_utc": "2026-08-19",
        "route": "ClinicalTrials.gov v2 referencesModule, all types",
    }


def run(topics):
    out = {"resolved_utc": "2026-08-19",
           "rule": ("Every identifier by lookup. Unresolvable is reported UNRESOLVABLE and never "
                    "approximated; a registry that was not searched is NAMED as not searched."),
           "topics": {}}
    for topic in topics:
        trials, err = trials_of(topic)
        if trials is None:
            out["topics"][topic] = {"state": "SKIPPED", "why": err}
            print("%-40s SKIPPED -- %s" % (topic, err))
            continue
        rows = [resolve_trial(t) for t in trials if isinstance(t, dict)]
        out["topics"][topic] = {"n_trials": len(rows), "trials": rows}
        print("\n== %s  (%d trials)" % (topic, len(rows)))
        for r in rows:
            print("   %-14s %-26s %-30s %s"
                  % (r.get("registration"), (r.get("name") or "")[:26], r["state"],
                     ("%d candidate(s) %s" % (r.get("n_candidates", 0),
                                              r.get("candidates_by_type") or ""))
                     if r["state"] == "RESOLVED_CANDIDATES" else ""))
    dest = os.path.join(EV, "primary_publications_%s.json"
                        % ("corpus" if len(topics) > 3 else "-".join(topics)[:60]))
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False))
    print("\nwrote %s" % os.path.relpath(dest, REPO))
    return 0


def selftest():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-66s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    print("1. A TRIAL WITH NO NCT IS UNRESOLVED AND NAMES THE REGISTRY NOT SEARCHED:")
    r = resolve_trial({"name": "LoDoCo2", "registry_id": "ACTRN12614000093684"})
    ck("state", r["state"], "NOT_ON_CLINICALTRIALS_GOV")
    # CASE-FOLDED, and the reason is class 25 in this very selftest. The assertion was written
    # as `"does not search" in r["why"]` against a string that reads "DOES NOT SEARCH", and the
    # test failed on the CASE while the code under test was correct -- the third occurrence
    # today of a lookup that misses on spelling and reports something false about the thing it
    # looked at. A comparison over free text folds case, always.
    ck("and it says the registry was not searched",
       "does not search" in r["why"].lower(), True)

    print("\n2. REFERENCE TYPE IS NEVER FILTERED -- the CLEAR Outcomes case:")
    r = resolve_trial({"name": "CLEAR Outcomes", "nct": "NCT02993406"})
    types = r.get("candidates_by_type") or {}
    ck("BACKGROUND references are returned, not dropped", "BACKGROUND" in types, True)
    ck("and the primary report is among the candidates",
       any(c["pmid"] == "36876740" for c in r["candidates"]), True)
    ck("...and it is typed BACKGROUND",
       [c["type"] for c in r["candidates"] if c["pmid"] == "36876740"], ["BACKGROUND"])

    print("\n3. THE SHARED-PUBLICATION TRAP IS VISIBLE IN THE OUTPUT:")
    a = resolve_trial({"name": "SPIRE-1", "nct": "NCT01975376"})
    b = resolve_trial({"name": "SPIRE-2", "nct": "NCT01975389"})
    pa = {c["pmid"] for c in a["candidates"]}
    pb = {c["pmid"] for c in b["candidates"]}
    ck("SPIRE-1 and SPIRE-2 share candidate publications", "28304242" in (pa & pb), True)

    print("\n4. AND THE ACRONYM IS READ BACK, not assumed:")
    ck("NCT01975376 declares SPIRE-1", a["acronym_the_registration_declares"], "SPIRE-1")
    ck("NCT01975389 declares SPIRE-2", b["acronym_the_registration_declares"], "SPIRE-2")

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        args = sorted(os.path.basename(os.path.dirname(p))
                      for p in glob.glob(os.path.join(REPO, "ssot", "*", "*.json")))
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(run(args))
