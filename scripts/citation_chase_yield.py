# -*- coding: utf-8 -*-
"""MEASURE what forward and backward citation chasing finds that our search does not.

THE QUESTION THIS ANSWERS, and it is Mahmood's, asked on 2026-08-29: Google Scholar is
the best free tool for citation chasing, so should we use it? The answer given here is
not an opinion about Scholar. It is a measurement of whether the FUNCTION Scholar serves
can be got from sources that are reproducible.

WHY NOT SCHOLAR. Three properties, each disqualifying on its own: no API, so any use is
scraping; results are personalised and drift, so two runs of the same query are not the
same observation; and there is no systematic export, so a result set cannot be recorded
with a hash and re-checked. ⚠️ THE AXIS WE WIN ON IS VERIFIABILITY. A source whose
results cannot be reproduced would be spent from the one account we are ahead in, to buy
coverage we can get elsewhere. `scripts/ictrp_search.py` records the same judgement about
the WHO portal for a different reason -- there, robots.txt disallows all automated access.

THE SUBSTITUTES, and what each is for.

    Europe PMC    citations and references, both directions, free, no key, and it returns
                  the NCT identifiers in the record. The workhorse.
    OpenAlex      cited_by and referenced_works over a larger, non-biomedical-limited
                  graph. Catches what is not in PubMed.
    Crossref      publisher-deposited reference lists. Weakest recall of the three
                  because deposition is optional, and named anyway so its gaps are ours
                  to report rather than to discover later.
    Semantic Scholar  ⚠️ NOT USED. It answers 429 to an unauthenticated client, so it is
                  a source we cannot currently reach rather than one we chose against.
                  Recorded as a BOUNDARY, not omitted silently.

⚠️ WHAT A DIFFERENCE MEANS, AND THE RULE THAT GOVERNS IT. A trial that citation chasing
finds and our search did not is NOT automatically a recall failure. It is one of three
things, and they are completely different findings:

    SEARCH MISS          eligible for this review's question, and our search missed it.
                         This is the only one that measures our recall.
    ELIGIBILITY          found, and correctly not included -- wrong population, wrong
                         comparator, wrong design, an extension without a control arm.
    SOURCE BOUNDARY      outside what our sources index at all.

Reporting the raw set difference as a recall figure is the error the standing orders name
explicitly, and it is the one that would flatter us here: citation chasing surfaces every
open-label extension and safety sub-study of a drug, and counting those as misses would
manufacture a large fake number in either direction depending on which way we spun it.

EVERY OBSERVATION CARRIES ITS QUERY, ITS UTC AND A HASH of the payload, for the same
reason `ictrp_search.py` does: a result set without them is a claim about no particular
moment, and this project has already been bitten once by comparing an artefact against a
version of itself that no longer existed.
"""
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
OPENALEX = "https://api.openalex.org"
CROSSREF = "https://api.crossref.org"

NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)
# Other primary-registry identifier shapes, so a non-US trial surfaced by chasing is not
# invisible just because it has no NCT. Bounded patterns, per the ReDoS rule.
OTHER_REG_RE = re.compile(
    r"\b(?:ISRCTN\d{8}|ChiCTR[-A-Za-z0-9]{4,20}|CTRI/\d{4}/\d{2,3}/\d{6}"
    r"|IRCT\d{11,20}[Nn]\d{1,3}|PACTR\d{12,20}|ACTRN\d{14}|jRCT[0-9a-z]{8,12}"
    r"|DRKS\d{8}|NTR\d{3,5}|EUCTR\d{4}-\d{6}-\d{2})\b")


def _get(url, tries=6, pause=4.0):
    """One GET, recorded. Returns (payload_text, status_word)."""
    for i in range(tries):
        r = subprocess.run(["curl", "-s", "--max-time", "60", "-A", UA,
                            "-w", "\n__HTTP__%{http_code}", url], capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        code = out.rsplit("__HTTP__", 1)[-1].strip() if "__HTTP__" in out else "000"
        body = out.rsplit("\n__HTTP__", 1)[0]
        if code == "200":
            return body, "OK"
        # ⚠️ RETRY 5xx, NOT ONLY 429. Europe PMC answers 503/504 intermittently under
        # load -- observed twice in one minute while writing this, with a 200 either side
        # for the identical URL. The first version of this function retried only on 429,
        # so a transient blip was recorded as FAILED and the source silently dropped out
        # of the measurement. A count that shrinks because a server hiccuped is the
        # "reach reported as coverage" defect arriving through the transport layer.
        if code == "429" or code.startswith("5"):
            if i < tries - 1:
                time.sleep(pause * (i + 2))
                continue
        if r.returncode != 0 and i < tries - 1:
            time.sleep(pause)
            continue
        return body, ("RATE_LIMITED" if code == "429" else "FAILED_HTTP_%s" % code)
    return "", "RATE_LIMITED"


def _json(url):
    body, st = _get(url)
    if st != "OK":
        return None, st
    try:
        return json.loads(body), "OK"
    except ValueError:
        return None, "FAILED_UNPARSEABLE"


def _sha(s):
    return hashlib.sha256((s or "").encode("utf-8", "replace")).hexdigest()[:16]


def _ids(text):
    """Registry identifiers in a blob, both NCT and non-NCT."""
    got = {m.group(0).upper() for m in NCT_RE.finditer(text or "")}
    got |= {m.group(0) for m in OTHER_REG_RE.finditer(text or "")}
    return got


# ------------------------------------------------------------------------ Europe PMC

def epmc_search(query, page_size=100):
    u = "%s/search?query=%s&format=json&pageSize=%d&resultType=core" % (
        EPMC, urllib.parse.quote(query), page_size)
    d, st = _json(u)
    if st != "OK":
        return [], st
    return (d.get("resultList") or {}).get("result") or [], "OK"


def epmc_linked(src, pid, direction):
    """direction is 'citations' or 'references'."""
    u = "%s/%s/%s/%s?format=json&pageSize=1000" % (EPMC, src, pid, direction)
    d, st = _json(u)
    if st != "OK":
        return [], st
    key = "citationList" if direction == "citations" else "referenceList"
    return (d.get(key) or {}).get("citation" if direction == "citations"
                                  else "reference") or [], "OK"


# --------------------------------------------------------------------------- OpenAlex

def openalex_by_pmid(pmid):
    d, st = _json("%s/works/pmid:%s" % (OPENALEX, pmid))
    return d, st


def openalex_cited_by(work_id, per_page=200):
    wid = (work_id or "").rsplit("/", 1)[-1]
    d, st = _json("%s/works?filter=cites:%s&per-page=%d" % (OPENALEX, wid, per_page))
    if st != "OK":
        return [], st
    return d.get("results") or [], "OK"


# --------------------------------------------------------------------------- Crossref

def crossref_refs(doi):
    d, st = _json("%s/works/%s" % (CROSSREF, urllib.parse.quote(doi, safe="")))
    if st != "OK":
        return [], st
    return ((d or {}).get("message") or {}).get("reference") or [], "OK"


# ------------------------------------------------------------------------------- main

def chase(seed_ncts, topic_query, label):
    """Chase from the seed trials' publications. Returns a full, hashed record."""
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rec = {"label": label, "utc": started, "seed_ncts": sorted(seed_ncts),
           "topic_query": topic_query,
           "sources": {"europe_pmc": {}, "openalex": {}, "crossref": {},
                       "semantic_scholar": {
                           "status": "NOT_REACHED",
                           "why": ("Answers HTTP 429 to an unauthenticated client. This "
                                   "is a source we could not reach, not one we chose "
                                   "against, and it is named so the gap is ours to "
                                   "report rather than to be discovered later.")}},
           "seed_papers": [], "found_ids": {}, "status_counts": {}}

    def bump(s):
        rec["status_counts"][s] = rec["status_counts"].get(s, 0) + 1

    # 1. SEEDS -- the trial reports themselves.
    seeds = []
    for nct in sorted(seed_ncts):
        res, st = epmc_search(nct)
        bump("epmc_seed_" + st)
        for r in res:
            if r.get("pmid") or r.get("doi"):
                seeds.append({"nct": nct, "epmc_id": r.get("id"),
                              "source": r.get("source"), "pmid": r.get("pmid"),
                              "doi": r.get("doi"), "title": (r.get("title") or "")[:160],
                              "citedByCount": r.get("citedByCount")})
    rec["seed_papers"] = seeds
    rec["n_seed_papers"] = len(seeds)

    found = {}   # registry id -> set of routes that surfaced it

    def add(i, route):
        found.setdefault(i.upper(), set()).add(route)

    # 2. FORWARD + BACKWARD through Europe PMC.
    for s in seeds:
        if not (s.get("epmc_id") and s.get("source")):
            continue
        for direction in ("citations", "references"):
            items, st = epmc_linked(s["source"], s["epmc_id"], direction)
            bump("epmc_%s_%s" % (direction, st))
            for it in items:
                blob = json.dumps(it)
                for i in _ids(blob):
                    add(i, "europe_pmc_" + direction)
                # A citing/cited record often names no NCT in its stub; fetch its core
                # record only when it looks like a trial report, to stay inside a
                # sensible request budget. Bounded on purpose, and the bound is reported.
                ttl = (it.get("title") or "").lower()
                if any(w in ttl for w in ("randomi", "trial", "efficacy", "phase")):
                    pid = it.get("id")
                    src = it.get("source")
                    if pid and src:
                        core, st2 = _json("%s/search?query=EXT_ID:%s%%20AND%%20SRC:%s"
                                          "&format=json&resultType=core" % (EPMC, pid, src))
                        bump("epmc_core_" + st2)
                        if core:
                            for i in _ids(json.dumps(core)):
                                add(i, "europe_pmc_" + direction + "_core")

    # 3. FORWARD through OpenAlex.
    for s in seeds:
        if not s.get("pmid"):
            continue
        w, st = openalex_by_pmid(s["pmid"])
        bump("openalex_lookup_" + st)
        if not w:
            continue
        cits, st = openalex_cited_by(w.get("id"))
        bump("openalex_cited_by_" + st)
        for c in cits:
            for i in _ids(json.dumps(c)):
                add(i, "openalex_cited_by")

    # 4. BACKWARD through Crossref.
    for s in seeds:
        if not s.get("doi"):
            continue
        refs, st = crossref_refs(s["doi"])
        bump("crossref_refs_" + st)
        for r in refs:
            for i in _ids(json.dumps(r)):
                add(i, "crossref_references")

    rec["found_ids"] = {k: sorted(v) for k, v in sorted(found.items())}
    rec["n_found"] = len(found)
    rec["payload_sha256_16"] = _sha(json.dumps(rec["found_ids"], sort_keys=True))
    return rec


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    seeds = sys.argv[1].split(",") if len(sys.argv) > 1 else \
        ["NCT01539226", "NCT01617096"]
    query = sys.argv[2] if len(sys.argv) > 2 else "dapivirine vaginal ring HIV"
    out = sys.argv[3] if len(sys.argv) > 3 else r"F:\claude-temp\rm-dapivirine-2026-08-31\rm-dapivirine-2026-08-31\citation_chase.json"
    r = chase(seeds, query, "dapivirine-ring")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, ensure_ascii=False)
    print("seed NCTs        :", ", ".join(r["seed_ncts"]))
    print("seed papers found:", r["n_seed_papers"])
    for s in r["seed_papers"]:
        print("   %s  pmid=%s  doi=%s  citedBy=%s" %
              (s["nct"], s["pmid"], s["doi"], s["citedByCount"]))
        print("      ", s["title"][:100])
    print("distinct registry ids surfaced by chasing:", r["n_found"])
    for i, routes in r["found_ids"].items():
        print("   %-24s %s" % (i, ", ".join(routes)))
    print("status counts    :", json.dumps(r["status_counts"], indent=1))
    print("written to", out, os.path.getsize(out), "bytes")
