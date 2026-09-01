# -*- coding: utf-8 -*-
"""EXHAUST the open-access retrieval for every topic. A truncation is a LOWER BOUND.

⛔ WHY. `oa_retrieve.py` caps at 100 rows and prints `hitCount` beside it, so the cap is
visible -- but 15 of 20 topics were truncated against hitCounts up to 3,541, and their
verified rows are an arbitrary relevance-ordered WINDOW. A window judged and reported beside
a population is the reach-versus-coverage defect, so the thirteen control topics were left
unjudged. This removes the cap instead of documenting it.

⛔ THE RULE IS FROZEN. Same intervention terms, same condition terms, same
`axis_states.classify`, same `oa_frame_contract`. Only the number of rows READ changes.

⚠️ EXHAUSTION IS ASSERTED, NOT ASSUMED. Every topic reports `hitCount` beside `fetched` and
a boolean `exhausted`. A run that silently stops early would look exactly like a small
literature.

⭐ WHAT IS STORED. Not the 16,000-odd retrieved rows -- only per-topic counts, a sha256 over
the retrieved id SET, and the full text of rows that VERIFY, because a judgement about a row
that was never shown cannot be checked. Storing every abstract would put ~22 MB of
third-party text in the repo to prove a number that a hash proves.
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import norm, contains, rule_fingerprint, assert_fingerprint  # noqa: E402
from axis_states import classify, ALL_STATES, MATCHED, REFUSED_NO_TERMS      # noqa: E402
from axis_match import terms_for, sha_set, _cond_need                        # noqa: E402
from oa_frame_contract import kind_evidence, comparators                     # noqa: E402

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PUBTYPE = '(PUB_TYPE:"systematic-review" OR PUB_TYPE:"meta-analysis")'
SCOPE = 'OPEN_ACCESS:Y AND HAS_ABSTRACT:Y'
PAGE = 1000                       # Europe PMC maximum
MAX_PAGES = 25                    # 25,000 rows per topic; nothing here approaches it
CORR = "../../evidence/2026-08-31-rekey/corrected"
OUT = "../../evidence/2026-08-31-axis/oa_paged_twenty.json"


def _get(url, tries=5):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as fh:
                return json.loads(fh.read().decode("utf-8")), "OK"
        except Exception as e:                                    # noqa: BLE001
            if a == tries - 1:
                return None, "ERROR_%s" % type(e).__name__
            time.sleep(2 + 3 * a)
    return None, "ERROR"


def retrieve_all(iterms):
    """-> (rows, hit_count, exhausted, status, query, pages). cursorMark pagination."""
    if not iterms:
        return [], None, False, "NO_TERMS", "", 0
    block = " OR ".join('"%s"' % t if " " in t else t for t in iterms)
    q = "(%s) AND %s AND %s" % (block, PUBTYPE, SCOPE)
    rows, cursor, hit, pages = [], "*", None, 0
    seen = set()
    while pages < MAX_PAGES:
        url = ("%s?query=%s&format=json&pageSize=%d&resultType=core&cursorMark=%s"
               % (EPMC, urllib.parse.quote(q), PAGE, urllib.parse.quote(cursor)))
        d, st = _get(url)
        pages += 1
        if d is None:
            return rows, hit, False, st, q, pages
        if hit is None:
            hit = d.get("hitCount")
        batch = (d.get("resultList") or {}).get("result") or []
        for r in batch:
            oid = ("PMC" + r["pmcid"][3:]) if r.get("pmcid") else (
                  ("PMID:" + r["pmid"]) if r.get("pmid") else None)
            if not oid or oid in seen:
                continue
            seen.add(oid)
            abst = r.get("abstractText")
            row = {"oa_id": oid, "title": r.get("title") or "",
                   "objectives_verbatim": (abst if (abst or "").strip() else None),
                   "objectives_source": "abstract",
                   "is_open_access": r.get("isOpenAccess"), "license": r.get("license"),
                   "pub_year": r.get("pubYear"), "source": "europepmc",
                   "verification_field_kind": "abstract",
                   "provenance": "europepmc REST cursorMark resultType=core",
                   "pub_types": ((r.get("pubTypeList") or {}).get("pubType") or [])}
            row["record_kind"] = kind_evidence(row)[0]
            rows.append(row)
        nxt = d.get("nextCursorMark")
        if not batch or not nxt or nxt == cursor:
            break
        cursor = nxt
        time.sleep(0.3)
    exhausted = bool(hit is not None and len(seen) >= int(hit))
    return rows, hit, exhausted, "OK", q, pages


def score(rows, iterms, cterms):
    if not iterms or not cterms:
        st, why = classify(0, 0, 0, 0, bool(iterms), bool(cterms))
        return {"state": st, "reason": why, "axis_condition": None, "verified": None}
    for r in rows:
        r["_all"] = norm((r["title"] or "") + " " + (r["objectives_verbatim"] or ""))
        r["_obj"] = norm(r["objectives_verbatim"]) if r["objectives_verbatim"] else None
    need = _cond_need(cterms)
    ch = [r for r in rows if len([c for c in cterms if contains(r["_all"], c)]) >= need]
    ver = []
    for r in ch:
        if r["_obj"] is None:
            continue
        if (any(contains(r["_obj"], t) for t in iterms)
                and len([c for c in cterms if contains(r["_obj"], c)]) >= need):
            ver.append(r)
    st, why = classify(len(rows), len(ch), len(ch), len(ver), True, True)
    return {"state": st, "reason": why,
            "axis_condition": {"n": len(ch), "sha256": sha_set(r["oa_id"] for r in ch)},
            "verified": {"n": len(ver), "sha256": sha_set(r["oa_id"] for r in ver),
                         "rows": [{"oa_id": r["oa_id"], "title": r["title"],
                                   "objectives_verbatim": r["objectives_verbatim"],
                                   "pub_year": r["pub_year"], "license": r["license"]}
                                  for r in ver]}}


def main():
    doc = json.load(io.open(os.path.join(CORR, "twenty.json"), encoding="utf-8"))
    assert_fingerprint(doc.get("rule_fingerprint"), "twenty.json", "rekey20/oa_page_all.py")
    demand = {"etripamil-psvt", "riociguat-pah", "selexipag-pah", "sotatercept-pah",
              "mavacamten-hcm-review", "evolocumab-dyslipidemia-review",
              "evolocumab-mixed-dyslipidemia-auto-full-review"}

    print("=== REF ===")
    print("   rule        %s   FROZEN" % rule_fingerprint()[:16])
    print("   source      Europe PMC cursorMark, pageSize=%d, max %d pages/topic"
          % (PAGE, MAX_PAGES))
    print("   verify      abstract  ⛔ not comparable to a CDSR number")
    print("")
    print("   %-46s %6s %7s %7s %5s %5s %5s %s"
          % ("app_id", "hits", "fetched", "exhaust", "prot", "cond", "ver", "state"))

    out = []
    for t in sorted(doc["topics"], key=lambda x: x["app_id"]):
        dt, ct, _ = terms_for(t.get("drug") or {})
        iterms = sorted(set(dt) | set(ct))
        cterms = t.get("condition_terms") or []
        rows, hit, exhausted, st, q, pages = retrieve_all(iterms)
        eligible, kinds = (comparators(rows) if rows else
                           ([], {"n_rows": 0, "n_comparators": 0, "excluded_by_kind": {}}))
        rec = score(eligible, iterms, cterms)
        rec.update({"app_id": t["app_id"], "in_demand_list": t["app_id"] in demand,
                    "hit_count": hit, "fetched": len(rows), "pages": pages,
                    "exhausted": exhausted, "retrieval_status": st,
                    "retrieved_sha256": sha_set(r["oa_id"] for r in rows),
                    "kinds": kinds, "intervention_terms": iterms,
                    "condition_terms": cterms, "query_as_executed": q,
                    "verification_field_kind": "abstract"})
        out.append(rec)
        print("   %-46s %6s %7d %7s %5d %5s %5s %s"
              % (t["app_id"], hit if hit is not None else st, len(rows),
                 "YES" if exhausted else "NO",
                 kinds["excluded_by_kind"].get("protocol", 0),
                 "-" if rec["axis_condition"] is None else rec["axis_condition"]["n"],
                 "-" if rec["verified"] is None else rec["verified"]["n"], rec["state"]))

    print("")
    print("=== EXHAUSTION, ASSERTED ===")
    notex = [r["app_id"] for r in out
             if r["hit_count"] is not None and not r["exhausted"]]
    print("   topics exhausted        : %d / %d"
          % (sum(1 for r in out if r["exhausted"]), len(out)))
    print("   NOT exhausted (still a LOWER BOUND): %d   %s"
          % (len(notex), ", ".join(notex) if notex else "none"))
    print("   topics with no query at all (REFUSED_NO_TERMS): %d"
          % sum(1 for r in out if r["state"] == REFUSED_NO_TERMS))

    print("")
    print("=== THE FUNNEL, ALL TWENTY ===")
    fetched = sum(r["fetched"] for r in out)
    prot = sum(r["kinds"]["excluded_by_kind"].get("protocol", 0) for r in out)
    cond = sum(r["axis_condition"]["n"] for r in out if r["axis_condition"])
    ver = sum(r["verified"]["n"] for r in out if r["verified"])
    print("   fetched                          : %d" % fetched)
    print("   excluded as protocols by contract: %d" % prot)
    print("   condition axis                   : %d" % cond)
    print("   VERIFIED PAIRS                   : %d   <- the judging load" % ver)
    c = Counter(r["state"] for r in out)
    print("")
    for s in ALL_STATES:
        print("   %-24s %2d" % (s, c.get(s, 0)))
    print("   %-24s %2d   sums: %s" % ("TOTAL", sum(c.values()),
                                       "HOLDS" if sum(c.values()) == 20 else "BROKEN"))
    print("")
    print("   topics MATCHED : %d / 20   (MATCHED is NOT a counterpart -- see oa_judge)"
          % c.get(MATCHED, 0))

    json.dump({"ref": {"rule_fingerprint": rule_fingerprint(), "page_size": PAGE,
                       "verification_field_kind": "abstract"}, "topics": out},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
