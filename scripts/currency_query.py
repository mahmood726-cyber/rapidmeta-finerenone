#!/usr/bin/env python3
"""CURRENCY: what has appeared since the comparator's search date. A query, not an essay.

WHY THIS IS THE COMPONENT THAT GENERALISES. A published synthesis decays from the day its
search closes and cannot report anything later without redoing itself. That decay is
structural, it applies to every topic where a published comparator exists, and it is
MEASURABLE rather than asserted. Cochrane's dapivirine review is from 2021; it cannot
report EMA 16+, the WHO recommendation, or the adolescent evidence. Saying so is rhetoric.
Returning the records is a finding.

KEYED TO A DATE THE COMPARATOR ITSELF SUPPLIES, so it runs on any topic:
  1. read the comparator PMIDs already recorded in published_comparison.reviews
  2. ask PubMed for each comparator's publication date
  3. query the sources for records after the LATEST comparator's date
  4. report counts and a sample, under the three-count law

⚠ THE DATE USED IS THE COMPARATOR'S PUBLICATION DATE, NOT ITS SEARCH DATE, AND THAT
CHOICE IS DELIBERATELY CONSERVATIVE. A review's search closes BEFORE it is published,
often by 6-18 months. So records between its search date and its publication date are also
new to it and are NOT counted here. Every number this produces is therefore a LOWER BOUND
on the comparator's currency gap. It can understate our advantage; it cannot overstate it,
which is the direction an argument of ours should err in.

A CURRENCY GAP IS NOT A DEFECT IN THE COMPARATOR. A 2021 review searching to 2020 was
right in 2021. The claim here is only that it is not current now, and that the difference
is checkable.
"""
import datetime
import io
import json
import os
import sys
import time

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
UA = {"User-Agent": "rapidmeta-currency/1.0 (research use)"}
EXECUTED, EMPTY, FAILED = "EXECUTED", "EMPTY", "FAILED"


def comparators(obj):
    """PMIDs of published syntheses already recorded on the topic."""
    pc = obj.get("published_comparison")
    if not isinstance(pc, dict):
        return []
    out = []
    for r in (pc.get("reviews") or []):
        if isinstance(r, dict) and r.get("pmid"):
            out.append({"pmid": str(r["pmid"]), "title": r.get("title"),
                        "year": r.get("year")})
    return out


def pub_dates(pmids):
    """Publication dates from PubMed. The date comes from the source, not from us."""
    if not pmids:
        return {}
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                     params={"db": "pubmed", "retmode": "json", "id": ",".join(pmids)},
                     headers=UA, timeout=60)
    if r.status_code != 200:
        return {}
    res = r.json().get("result", {})
    out = {}
    for p in pmids:
        rec = res.get(p) or {}
        raw = rec.get("sortpubdate") or rec.get("pubdate") or ""
        for fmt in ("%Y/%m/%d %H:%M", "%Y/%m/%d", "%Y %b %d", "%Y %b", "%Y"):
            try:
                out[p] = datetime.datetime.strptime(raw.strip()[:len(
                    datetime.datetime.now().strftime(fmt))], fmt).date()
                break
            except ValueError:
                continue
    return out


def since_pubmed(term, since):
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                     params={"db": "pubmed", "retmode": "json", "retmax": 60,
                             "term": term, "datetype": "pdat",
                             "mindate": since.strftime("%Y/%m/%d"),
                             "maxdate": "3000/01/01"}, headers=UA, timeout=60)
    if r.status_code != 200:
        return {"source": "pubmed", "outcome": FAILED, "http": r.status_code,
                "n_records": None}
    j = r.json()["esearchresult"]
    n = int(j["count"])
    return {"source": "pubmed", "outcome": EXECUTED if n else EMPTY, "http": 200,
            "n_records": n, "ids": j.get("idlist", [])[:40]}


def since_europepmc(term, since):
    q = '%s AND (FIRST_PDATE:[%s TO 3000-01-01])' % (term, since.strftime("%Y-%m-%d"))
    r = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                     params={"query": q, "format": "json", "pageSize": 25},
                     headers=UA, timeout=60)
    if r.status_code != 200:
        return {"source": "europepmc", "outcome": FAILED, "http": r.status_code,
                "n_records": None}
    j = r.json()
    n = int(j.get("hitCount", 0))
    return {"source": "europepmc", "outcome": EXECUTED if n else EMPTY, "http": 200,
            "n_records": n,
            "sample": [x.get("title", "")[:90]
                       for x in ((j.get("resultList") or {}).get("result") or [])[:6]]}


def since_ctgov(term, since):
    """Trials whose results were POSTED after the comparator. A registration that
    reported after a review closed is evidence that review cannot contain."""
    r = requests.get("https://clinicaltrials.gov/api/v2/studies",
                     params={"query.term": term, "pageSize": 60, "countTotal": "true",
                             "filter.advanced": "AREA[ResultsFirstPostDate]RANGE[%s,MAX]"
                                                % since.strftime("%Y-%m-%d")},
                     headers=UA, timeout=60)
    if r.status_code != 200:
        return {"source": "ctgov", "outcome": FAILED, "http": r.status_code,
                "n_records": None}
    j = r.json()
    n = j.get("totalCount", 0)
    ids = []
    for st in j.get("studies", [])[:40]:
        ps = st.get("protocolSection") or {}
        ids.append(((ps.get("identificationModule") or {}).get("nctId")))
    return {"source": "ctgov", "outcome": EXECUTED if n else EMPTY, "http": 200,
            "n_records": n, "ids": ids}


def query_for(topic, obj):
    """The search term. Derived from the topic's own trials and slug, NOT its title --
    one title in this corpus is four registry outcome strings joined with '|'."""
    slug = " ".join(w for w in topic.split("-")
                    if w not in ("auto", "full", "review", "vs"))
    return slug


def run(topic):
    p = os.path.join(SSOT, topic, topic + ".json")
    obj = json.load(open(p, encoding="utf-8"))
    comps = comparators(obj)
    out = {"topic": topic, "comparators": comps}
    if not comps:
        out["state"] = "NO_COMPARATOR"
        out["why"] = ("No published synthesis is recorded on this topic, so there is no "
                      "search date to be current against. This is not a currency finding "
                      "either way.")
        return out
    dates = pub_dates([c["pmid"] for c in comps])
    for c in comps:
        c["published"] = str(dates.get(c["pmid"], ""))
    dated = [d for d in dates.values()]
    if not dated:
        out["state"] = "NO_DATE"
        out["why"] = "PubMed returned no usable publication date for any comparator."
        return out
    since = max(dated)
    out["anchor"] = {
        "since": str(since),
        "basis": "publication date of the most recent recorded comparator",
        "_conservative": ("A review's search closes BEFORE it is published. Records "
                          "between its search date and this date are also new to it and "
                          "are NOT counted, so every number below is a LOWER BOUND."),
    }
    term = query_for(topic, obj)
    out["query"] = term
    # PACED, AND RETRIED ON SERVER-SIDE REFUSAL. A first pass hammered Europe PMC and
    # took 502/503/504 on 12 of 22 topics. Those are MY request rate showing up as the
    # source's status, and recording them as "no new records" would be exactly the
    # FAILED-vs-EMPTY confusion this project enforces everywhere else. The source label
    # is the SOURCE, never the function name -- an earlier version wrote
    # "since_europepmc" into a record, which is a fact about my code.
    recs = []
    for label, fn in (("pubmed", since_pubmed), ("europepmc", since_europepmc),
                      ("ctgov", since_ctgov)):
        rec = None
        for attempt in range(3):
            try:
                rec = fn(term, since)
            except Exception as e:
                rec = {"source": label, "outcome": FAILED, "http": None,
                       "error": type(e).__name__}
            if rec.get("outcome") != FAILED:
                break
            time.sleep(3 * (attempt + 1))
        rec["source"] = label
        recs.append(rec)
        time.sleep(1.2)
    out["sources"] = recs
    out["three_counts"] = {k: sum(1 for r in recs if r.get("outcome") == k)
                           for k in (EXECUTED, EMPTY, FAILED)}
    out["n_new_total"] = sum((r.get("n_records") or 0) for r in recs)
    out["WHAT_THESE_COUNTS_ARE_NOT"] = (
        "These are CANDIDATE RECORDS matching the term since the comparator's publication "
        "date. They are NOT new eligible trials, and none of them has been screened. "
        "Reporting 113 new records as 113 new trials would be the same error as reporting "
        "'19 read' when 19 were retrieved and one appraised. The currency claim this "
        "supports is 'a published synthesis of date X cannot contain records that "
        "appeared after X', which is true of the records and says nothing yet about their "
        "eligibility.")
    out["state"] = "MEASURED"
    return out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    topics = sys.argv[1:]
    if not topics:
        topics = [t for t in sorted(os.listdir(SSOT))
                  if os.path.isfile(os.path.join(SSOT, t, t + ".json"))]
    results = []
    for t in topics:
        try:
            r = run(t)
        except Exception as e:
            r = {"topic": t, "state": "ERROR", "why": type(e).__name__ + ": " + str(e)[:120]}
        results.append(r)
        if r["state"] == "MEASURED":
            a = r["anchor"]["since"]
            print("%-42s since %s  new: %s" % (
                t[:42], a, " ".join("%s=%s" % (s["source"], s.get("n_records"))
                                    for s in r["sources"])))
        else:
            print("%-42s %s" % (t[:42], r["state"]))
    json.dump(results, open(os.path.join(REPO, "outputs", "currency.json"), "w",
                            encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    meas = [r for r in results if r["state"] == "MEASURED"]
    print()
    print("topics asked                     %d" % len(results))
    print("topics with a dated comparator   %d" % len(meas))
    print("topics with no comparator        %d"
          % sum(1 for r in results if r["state"] == "NO_COMPARATOR"))
    if meas:
        print()
        print("Every count is a LOWER BOUND: the comparator's search closed before it was")
        print("published, and records in that interval are new to it but not counted here.")
