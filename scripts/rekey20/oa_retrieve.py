# -*- coding: utf-8 -*-
"""THE OPEN-ACCESS LANE. Retrieve by the FROZEN intervention terms, score the CONDITION
axis independently, classify with the FROZEN state function.

⛔ THE RULE IS NOT RETUNED. `rekey_rule`, `axis_states.classify` and the topics' term sets
are exactly what the CDSR run used. Only the material changes. That is what makes this an
experiment instead of a fitting exercise, and it is why a bad result ships as a finding.

⛔⛔ A RETRIEVED SET IS NOT A FRAME, AND TWO STATES ARE THEREFORE DEAD HERE.
CDSR is enumerable (1,216 rows); the open-access systematic-review literature is not
(131,862 and unbounded). So this lane retrieves per topic by a fixed procedure rather than
walking a slab -- and the intervention axis becomes the RETRIEVAL, which cannot also be a
measurement of itself.

    INTERVENTION_MISMATCH   axis_I == 0 AND axis_C > 0 -- IMPOSSIBLE here, because the
                            condition is scored over the retrieved rows.
    PAIR_ABSENT             both axes live and disjoint -- IMPOSSIBLE here, because the
                            condition hits are a SUBSET of the retrieved rows.

They are DECLARED, not left looking live. Printing `INTERVENTION_MISMATCH 0` in this
configuration would be a numerator fixed before a record was read.

⚠️ VERIFICATION MATERIAL IS NOT THE SAME MATERIAL. A Cochrane objectives statement is one
or two sentences; an abstract is ~250 words. Verifying against an abstract makes `MATCHED`
cheaper without changing a line of the rule, so every number here is stamped
`verification_field_kind = abstract` and MAY NOT be compared to a CDSR number.

Free source only: Europe PMC REST, no key.
"""
import hashlib, io, json, os, sys, time, urllib.parse, urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import norm, contains, rule_fingerprint, assert_fingerprint  # noqa: E402
from axis_states import (classify, ALL_STATES, MATCHED, INTERVENTION_MISMATCH,  # noqa
                         PAIR_ABSENT, REFUSED_NO_TERMS)
from axis_match import terms_for, sha_set, _cond_need                        # noqa: E402
from oa_frame_contract import kind_evidence, comparators                     # noqa: E402

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
# ⭐ DECLARED ONCE, IDENTICAL FOR EVERY TOPIC. The only per-topic part is the drug block,
# which comes from the frozen rule. Nothing here is hand-authored per topic.
PUBTYPE = '(PUB_TYPE:"systematic-review" OR PUB_TYPE:"meta-analysis")'
SCOPE = 'OPEN_ACCESS:Y AND HAS_ABSTRACT:Y'
PAGE = 100                       # cap; `hitCount` is recorded beside it so truncation shows
CORRECTED = os.path.join(HERE, "../../evidence/2026-08-31-rekey/corrected")
OUT = os.path.join(HERE, "../../evidence/2026-08-31-axis/oa_states_twenty.json")

# States that CANNOT fire in this configuration. Declared here, asserted at the end.
DEAD_HERE = (INTERVENTION_MISMATCH, PAIR_ABSENT)


def _get(url, tries=4):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as fh:
                return json.loads(fh.read().decode("utf-8")), "OK"
        except Exception as e:                                   # noqa: BLE001
            if a == tries - 1:
                return None, "ERROR %s" % type(e).__name__
            time.sleep(2 + 3 * a)
    return None, "ERROR"


def retrieve(iterms):
    """-> (rows, hitCount, status, query). Rows carry an id, title and abstract.

    ⚠️ `hitCount` is reported beside `len(rows)` ALWAYS. A capped page that reports only
    what it fetched is a reach figure with the cap invisible inside it.
    """
    if not iterms:
        return [], None, "NO_TERMS", ""
    block = " OR ".join('"%s"' % t if " " in t else t for t in iterms)
    q = "(%s) AND %s AND %s" % (block, PUBTYPE, SCOPE)
    url = ("%s?query=%s&format=json&pageSize=%d&resultType=core"
           % (EPMC, urllib.parse.quote(q), PAGE))
    d, st = _get(url)
    if d is None:
        return [], None, st, q
    rows = []
    for r in (d.get("resultList") or {}).get("result") or []:
        # The identifier is external and stable, never the title.
        oid = ("PMC" + r["pmcid"][3:]) if r.get("pmcid") else (
              ("PMID:" + r["pmid"]) if r.get("pmid") else None)
        if not oid:
            continue
        abst = r.get("abstractText")
        row = {"oa_id": oid, "title": r.get("title") or "",
               # null means UNOBTAINABLE and is never the empty string.
               "objectives_verbatim": (abst if (abst or "").strip() else None),
               "objectives_source": "abstract",
               "is_open_access": r.get("isOpenAccess"), "license": r.get("license"),
               "pub_year": r.get("pubYear"), "source": "europepmc",
               "verification_field_kind": "abstract",
               "provenance": "europepmc REST search resultType=core",
               "pub_types": ((r.get("pubTypeList") or {}).get("pubType") or [])}
        # ⛔ THE KIND IS READ FROM THE RECORD, NOT ASSERTED. This line used to be
        # `"record_kind": "systematic_review"` for every row, and four of 124 verified rows
        # were PROTOCOLS -- PMC12183782 and PMC12964950, the latter reaching three topics.
        # A protocol reports no results and cannot be a comparator; the Cochrane frame
        # contract excludes 30 of them on exactly that ground. The defect was caught by a
        # human reading the record's own words, not by any gate.
        row["record_kind"] = kind_evidence(row)[0]
        rows.append(row)
    return rows, d.get("hitCount"), "OK", q


def score_oa(rows, iterms, cterms):
    """Condition axis scored INDEPENDENTLY over the retrieved rows. Frozen classify()."""
    if not iterms or not cterms:
        st, why = classify(0, 0, 0, 0, bool(iterms), bool(cterms))
        return {"state": st, "reason": why, "vacuous": True,
                "vacuous_axes": ([] if iterms else ["intervention"]) +
                                ([] if cterms else ["condition"]),
                "retrieved": None, "axis_condition": None, "verified": None}
    for r in rows:
        r["_all"] = norm((r["title"] or "") + " " + (r["objectives_verbatim"] or ""))
        r["_obj"] = norm(r["objectives_verbatim"]) if r["objectives_verbatim"] else None
    need = _cond_need(cterms)
    ch = [r for r in rows if len([c for c in cterms if contains(r["_all"], c)]) >= need]
    ver = []
    for r in ch:
        if r["_obj"] is None:
            continue
        oi = [t for t in iterms if contains(r["_obj"], t)]
        oc = [c for c in cterms if contains(r["_obj"], c)]
        if oi and len(oc) >= need:
            ver.append(r)
    st, why = classify(len(rows), len(ch), len(ch), len(ver), True, True)
    return {"state": st, "reason": why, "vacuous": False, "vacuous_axes": [],
            "retrieved": {"n": len(rows), "sha256": sha_set(r["oa_id"] for r in rows)},
            "axis_condition": {"n": len(ch), "sha256": sha_set(r["oa_id"] for r in ch),
                               "liveness": {c: sum(1 for r in rows if contains(r["_all"], c))
                                            for c in cterms}},
            # ⛔ NO `ver[:6]` HERE. The first version of this line stored six rows while
            # printing n=11, so the artefact was a WINDOW reported under a population's
            # count -- the reach-versus-coverage defect, committed inside the file that
            # exists to report coverage honestly. Every verified row is stored, with the
            # full text it was judged from, because a judgement about a row that was never
            # shown cannot be checked.
            "verified": {"n": len(ver), "sha256": sha_set(r["oa_id"] for r in ver),
                         "rows": [{"oa_id": r["oa_id"], "title": r["title"],
                                   "objectives_verbatim": r["objectives_verbatim"],
                                   "pub_year": r["pub_year"], "license": r["license"]}
                                  for r in ver]}}


def main():
    doc = json.load(io.open(os.path.join(CORRECTED, "twenty.json"), encoding="utf-8"))
    assert_fingerprint(doc.get("rule_fingerprint"), "twenty.json", "rekey20/oa_retrieve.py")
    twenty = doc["topics"]

    demand = {"etripamil-psvt", "riociguat-pah", "selexipag-pah", "sotatercept-pah",
              "mavacamten-hcm-review", "evolocumab-dyslipidemia-review",
              "evolocumab-mixed-dyslipidemia-auto-full-review"}

    print("=== REF ===")
    print("   REF.rule                 %s   FROZEN, not retuned for this lane"
          % rule_fingerprint()[:16])
    print("   REF.source               Europe PMC REST (free, no key)")
    print("   REF.pubtype_filter       %s" % PUBTYPE)
    print("   REF.scope                %s" % SCOPE)
    print("   REF.page_cap             %d    hitCount reported beside every row count" % PAGE)
    print("   REF.verification_field   abstract   ⛔ NOT comparable to a CDSR number")
    print("")
    print("=== ⛔ STATES STRUCTURALLY UNREACHABLE IN THIS CONFIGURATION, DECLARED UP FRONT ===")
    for s in DEAD_HERE:
        print("   %-24s a retrieved set is not a frame: the intervention axis IS the "
              "retrieval" % s)
    print("   ⇒ their zeros below are NOT measurements and are excluded from scoring.")
    print("")

    out = []
    print("=== THE TWENTY THROUGH THE OPEN-ACCESS LANE ===")
    print("   %-46s %-6s %-22s %7s %7s %5s %5s"
          % ("app_id", "list", "state", "hitCnt", "fetched", "cond", "ver"))
    for t in sorted(twenty, key=lambda x: x["app_id"]):
        dt, ct, _ = terms_for(t.get("drug") or {})
        iterms = sorted(set(dt) | set(ct))
        cterms = t.get("condition_terms") or []
        rows, hit, st, q = retrieve(iterms)
        # ⭐ KINDS BEFORE THE NUMBER. A protocol is a THIRD kind -- not data, not a defect --
        # and `comparators` names what it removed instead of shrinking the denominator.
        eligible, kindmeta = (comparators(rows) if rows else ([], {"n_rows": 0,
                              "n_comparators": 0, "excluded_by_kind": {}}))
        rec = score_oa(eligible, iterms, cterms)
        rec["kinds"] = kindmeta
        rec.update({"app_id": t["app_id"], "title": t["title"],
                    "in_demand_list": t["app_id"] in demand,
                    "intervention_terms": iterms, "condition_terms": cterms,
                    "hit_count": hit, "fetched": len(rows), "retrieval_status": st,
                    "query_as_executed": q,
                    "truncated": bool(hit is not None and hit > len(rows)),
                    "verification_field_kind": "abstract"})
        out.append(rec)
        print("   %-46s %-6s %-22s %7s %7s %5s %5s"
              % (t["app_id"], "DEMAND" if rec["in_demand_list"] else "ctrl", rec["state"],
                 hit if hit is not None else st, len(rows),
                 "-" if rec["axis_condition"] is None else rec["axis_condition"]["n"],
                 "-" if rec["verified"] is None else rec["verified"]["n"]))
        time.sleep(0.4)

    print("")
    print("=== STATE TALLY ===")
    c = Counter(r["state"] for r in out)
    for s in ALL_STATES:
        tag = "   (UNREACHABLE HERE -- not a measurement)" if s in DEAD_HERE else ""
        print("   %-24s %2d%s" % (s, c.get(s, 0), tag))
    print("   %-24s %2d   sums to the twenty: %s"
          % ("TOTAL", sum(c.values()), "HOLDS" if sum(c.values()) == len(twenty) else "BROKEN"))
    for s in DEAD_HERE:
        if c.get(s, 0):
            print("   ⛔ %s fired %d times and was declared unreachable -- the declaration "
                  "is WRONG and must be corrected before any count here is used"
                  % (s, c[s]))

    print("")
    print("=== ⭐ THE DEMAND LIST -- the seven the CDSR frame could not reach ===")
    print("   %-46s %-22s %7s %5s %5s" % ("app_id", "state", "hitCnt", "cond", "ver"))
    reached = 0
    # ⛔ POSITIVE PROPERTY, same reason as oa_judge.py: a `if not ...: continue` skip inside
    # a corpus-wide loop shrinks the denominator invisibly. Partition, then assert the sum.
    demand_rows = [r for r in out if r["in_demand_list"]]
    control_rows = [r for r in out if r["in_demand_list"] is False]
    assert len(demand_rows) + len(control_rows) == len(out), "partition loses topics"
    for r in demand_rows:
        ok = r["state"] == MATCHED
        reached += ok
        print("   %-46s %-22s %7s %5s %5s%s"
              % (r["app_id"], r["state"], r["hit_count"],
                 "-" if r["axis_condition"] is None else r["axis_condition"]["n"],
                 "-" if r["verified"] is None else r["verified"]["n"],
                 "   <- REACHED" if ok else ""))
    print("   MATCHED on the demand list: %d / 7      (prediction A.4.2 said >= 5)" % reached)

    print("")
    print("=== THE THIRTEEN CONTROLS -- a lane that helps the seven and hurts these has not helped ===")
    cc = Counter(r["state"] for r in control_rows)
    for k, v in cc.most_common():
        print("   %-24s %2d" % (k, v))

    trunc = [r["app_id"] for r in out if r["truncated"]]
    print("")
    print("=== TRUNCATION, NAMED. A capped fetch is a LOWER BOUND, never a measurement. ===")
    print("   topics whose hitCount exceeds the %d fetched: %d" % (PAGE, len(trunc)))
    for r in out:
        if r["truncated"]:
            print("      %-46s %s of %s fetched" % (r["app_id"], r["fetched"], r["hit_count"]))
    vac = [r["app_id"] for r in out if r["state"] == REFUSED_NO_TERMS]
    print("   vacuous (REFUSED_NO_TERMS, nothing searched): %d   %s" % (len(vac), ", ".join(vac)))

    json.dump({"ref": {"rule_fingerprint": rule_fingerprint(), "source": "europepmc",
                       "pubtype": PUBTYPE, "scope": SCOPE, "page_cap": PAGE,
                       "verification_field_kind": "abstract",
                       "states_unreachable_here": list(DEAD_HERE)},
               "topics": out}, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
