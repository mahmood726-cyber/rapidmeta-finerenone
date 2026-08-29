"""RECALL TEST against a known answer: would the five-source search have found LEAP China?

WHY THIS IS THE ONLY KIND OF TEST THAT TEACHES ANYTHING ABOUT AN INSTRUMENT. Every
coverage number this pipeline produces is a statement about its own reach. A known missing
trial, supplied by an external reader, is ground truth -- and running the search AS
SPECIFIED against it measures recall rather than reach.

THE RULE OF THIS TEST: run the query the pipeline ACTUALLY SENT, not an improved one.
    "Lefamulin moxifloxacin community-acquired bacterial"
Improving the query first would answer a different question -- "could a better search find
it" -- and quietly convert a failed recall test into a passed one.

GROUND TRUTH, supplied externally:
    LEAP China -- randomised lefamulin vs moxifloxacin in CABP, ECR ~50/83 vs 27/42
    a 2025 pooled analysis combining LEAP 1 + LEAP 2 + LEAP China
    a 2021 pooled analysis reporting 89.3% vs 90.5%, risk difference -1.1 points

The page holds two trials: NCT02559310 (LEAP 1) and NCT02813694 (LEAP 2).

WHAT COUNTS AS FOUND: the record must actually appear in what the source RETURNED for that
query. A trial that exists in a database but is not in the returned set was not found by
this search, however easy it would have been to find another way.
"""
import io
import json
import os
import re
import sys
import time

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

QUERY = "Lefamulin moxifloxacin community-acquired bacterial"
HELD = {"NCT02559310", "NCT02813694"}
UA = {"User-Agent": "rapidmeta-recall-test/1.0 (research use)"}

# Markers for the ground-truth items. Deliberately generous: if ANY of these appear the
# item counts as found, because the test must not fail on a naming quibble.
CHINA = re.compile(r"\bLEAP[\s\-]?China\b|\bChina\b|\bChinese\b", re.I)
POOLED = re.compile(r"pooled|integrated analysis|combined analysis|meta-analys", re.I)


def pubmed():
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                     params={"db": "pubmed", "retmode": "json", "retmax": 200,
                             "term": QUERY}, headers=UA, timeout=60)
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return [], 0
    time.sleep(0.4)
    s = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                     params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
                     headers=UA, timeout=60).json()["result"]
    out = []
    for i in ids:
        rec = s.get(i) or {}
        out.append({"id": i, "title": rec.get("title", ""),
                    "date": rec.get("pubdate", "")})
    return out, len(ids)


def europepmc():
    out = []
    for page in (1, 2, 3):
        r = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                         params={"query": QUERY, "format": "json", "pageSize": 100,
                                 "page": page}, headers=UA, timeout=60)
        j = r.json()
        res = (j.get("resultList") or {}).get("result") or []
        out += [{"id": x.get("id"), "title": x.get("title", ""),
                 "date": str(x.get("pubYear", ""))} for x in res]
        if len(res) < 100:
            break
        time.sleep(0.3)
    return out, len(out)


def ctgov():
    r = requests.get("https://clinicaltrials.gov/api/v2/studies",
                     params={"query.term": QUERY, "pageSize": 200, "countTotal": "true"},
                     headers=UA, timeout=60)
    j = r.json()
    out = []
    for st in j.get("studies", []):
        ps = st.get("protocolSection") or {}
        idm = ps.get("identificationModule") or {}
        loc = ps.get("contactsLocationsModule") or {}
        countries = sorted({(x.get("country") or "") for x in (loc.get("locations") or [])})
        out.append({"id": idm.get("nctId"), "title": idm.get("briefTitle", ""),
                    "countries": countries})
    return out, j.get("totalCount")


if __name__ == "__main__":
    print("RECALL TEST -- query run exactly as the pipeline sent it")
    print("  %r" % QUERY)
    print()
    findings = {}

    for name, fn in (("pubmed", pubmed), ("europepmc", europepmc), ("ctgov", ctgov)):
        try:
            recs, total = fn()
        except Exception as e:
            print("  %-11s FAILED %s" % (name, type(e).__name__))
            continue
        hits_china = [r for r in recs if CHINA.search(r.get("title", "") or "")]
        hits_pool = [r for r in recs if POOLED.search(r.get("title", "") or "")]
        findings[name] = {"n": total, "retrieved": len(recs),
                          "china": hits_china, "pooled": hits_pool, "records": recs}
        print("  %-11s total=%-6s retrieved=%-4d  china-marker=%-2d  pooled-marker=%d"
              % (name, total, len(recs), len(hits_china), len(hits_pool)))

    print()
    print("=" * 78)
    print("DID THE SEARCH RETURN LEAP CHINA?")
    print("=" * 78)
    ct = findings.get("ctgov", {})
    ncts = [r["id"] for r in ct.get("records", [])]
    print("  ClinicalTrials.gov returned %d study/studies: %s" % (len(ncts), ncts))
    print("  already held by the page: %s" % sorted(HELD))
    new = [n for n in ncts if n not in HELD]
    print("  NOT already held: %s" % (new or "none"))
    for r in ct.get("records", []):
        print("     %-14s %-58s %s" % (r["id"], r["title"][:58], r["countries"][:4]))

    print()
    print("  China-marker hits in PubMed / Europe PMC titles:")
    any_ch = False
    for src in ("pubmed", "europepmc"):
        for r in findings.get(src, {}).get("china", [])[:8]:
            any_ch = True
            print("     [%s] %s (%s)" % (src, (r.get("title") or "")[:88], r.get("date")))
    if not any_ch:
        print("     none")

    print()
    print("  Pooled/integrated-analysis hits (the 2021 and 2025 papers):")
    any_p = False
    for src in ("pubmed", "europepmc"):
        for r in findings.get(src, {}).get("pooled", [])[:10]:
            any_p = True
            print("     [%s] %s (%s)" % (src, (r.get("title") or "")[:88], r.get("date")))
    if not any_p:
        print("     none")

    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "records"}
               for k, v in findings.items()},
              open("recall_leap_china.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)
