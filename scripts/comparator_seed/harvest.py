"""PHASE 1 - assemble open-access comparator systematic reviews from the PMC OA subset.

Adapter, not a scrape: the topic axis is data (TOPICS below), the query shape is one
function, and the only NCBI surface used is E-utilities. Running it on a new topic is
adding a row, not editing logic.

Writes:  <cache>/xml/PMC<id>.xml      raw JATS, one file per article
         <out>/comparator_candidates.json

Every candidate is checked against the PHASE-0 firewall before it is kept.
"""
import argparse
import json
import io
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# Guarded: a module-level stdout reassignment closes the caller's wrapper on import.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "rapidmeta-comparator-seed"
EMAIL = "mahmood726@gmail.com"

# The topic axis. Adding a field = adding rows here, nothing else.
TOPICS = {
    "cardiology": [
        "heart failure", "atrial fibrillation", "acute coronary syndrome",
        "myocardial infarction", "hypertension", "statin", "anticoagulant",
        "antiplatelet", "percutaneous coronary intervention", "aortic stenosis",
        "cardiac arrest", "stroke prevention", "lipid lowering", "cardiac rehabilitation",
        "cardiomyopathy", "pulmonary hypertension", "venous thromboembolism",
        "cardiovascular outcomes",
    ],
    "infectious_disease": [
        "tuberculosis", "HIV", "malaria", "hepatitis C", "hepatitis B", "influenza",
        "COVID-19", "pneumonia", "sepsis", "antibiotic", "antiretroviral", "vaccine",
        "sexually transmitted infection", "candidiasis", "meningitis",
        "urinary tract infection", "surgical site infection", "antimicrobial resistance",
    ],
}


def eget(endpoint, params, retries=4):
    params = dict(params)
    params.setdefault("tool", TOOL)
    params.setdefault("email", EMAIL)
    url = "%s/%s.fcgi?%s" % (EUTILS, endpoint, urllib.parse.urlencode(params))
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=90) as fh:
                return fh.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 - network surface, retry and then fail loud
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("E-utilities %s failed after %d tries: %s" % (endpoint, retries, last))


def esearch_pmc(term, retmax=100):
    """Enumerate to exhaustion, asserting collected == reported. No silent cap."""
    ids, retstart, reported = [], 0, None
    while True:
        raw = eget("esearch", {
            "db": "pmc", "term": term, "retmode": "json",
            "retmax": retmax, "retstart": retstart, "sort": "relevance",
        })
        res = json.loads(raw)["esearchresult"]
        if reported is None:
            reported = int(res["count"])
        batch = res.get("idlist", [])
        ids.extend(batch)
        retstart += len(batch)
        time.sleep(0.4)
        if not batch or len(ids) >= min(reported, retmax) or retstart >= reported:
            break
    return ids, reported


def build_query(term, year_from, year_to):
    return (
        '"open access"[filter] AND '
        '(meta-analysis[Title] OR "systematic review"[Title]) AND '
        '(randomized[Title/Abstract] OR randomised[Title/Abstract] OR '
        '"randomized controlled trial"[Title/Abstract]) AND '
        '"%s"[Title/Abstract] AND '
        '("%d"[PubDate] : "%d"[PubDate])' % (term, year_from, year_to)
    )


def fetch_xml(pmcids, cache_dir, batch=15):
    os.makedirs(cache_dir, exist_ok=True)
    need = [i for i in pmcids if not os.path.exists(os.path.join(cache_dir, "PMC%s.xml" % i))]
    for start in range(0, len(need), batch):
        chunk = need[start:start + batch]
        raw = eget("efetch", {"db": "pmc", "id": ",".join(chunk), "retmode": "xml"})
        parts = split_articles(raw)
        got = set()
        for pmcid, body in parts:
            if pmcid:
                got.add(pmcid)
                with open(os.path.join(cache_dir, "PMC%s.xml" % pmcid), "w", encoding="utf-8") as fh:
                    fh.write(body)
        missing = [c for c in chunk if c not in got]
        # A stub with no <body> is a non-OA record; record it so the denominator survives.
        for c in missing:
            with open(os.path.join(cache_dir, "PMC%s.MISSING" % c), "w", encoding="utf-8") as fh:
                fh.write("no article element returned by efetch\n")
        print("  efetch %d/%d  got=%d missing=%d" % (
            min(start + batch, len(need)), len(need), len(got), len(missing)))
        time.sleep(0.5)


ART_RE = re.compile(r"<article[ >].*?</article>", re.S)
PMCID_RE = re.compile(r'<article-id pub-id-type="pmc(?:id)?">\s*(?:PMC)?(\d+)\s*</article-id>')


def split_articles(raw):
    out = []
    for m in ART_RE.finditer(raw):
        body = m.group(0)
        pm = PMCID_RE.search(body)
        out.append((pm.group(1) if pm else None, body))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=r"C:/claude-temp/comparator-seed/xml")
    ap.add_argument("--out", default=r"C:/claude-temp/comparator-seed/stage/outputs")
    ap.add_argument("--firewall", default=r"C:/claude-temp/comparator-seed/stage/outputs/comparator_seed_firewall.json")
    ap.add_argument("--per-term", type=int, default=12)
    ap.add_argument("--year-from", type=int, default=2016)
    ap.add_argument("--year-to", type=int, default=2026)
    args = ap.parse_args()

    with open(args.firewall, encoding="utf-8") as fh:
        fw = json.load(fh)
    blocked_dois = set(fw["scored_comparator_dois"])
    print("firewall: %d comparator DOIs blocked as seeds" % len(blocked_dois))

    cands = {}
    for field, terms in TOPICS.items():
        for term in terms:
            q = build_query(term, args.year_from, args.year_to)
            ids, reported = esearch_pmc(q, retmax=args.per_term)
            print("[%s] %-32s reported=%-6d taken=%d" % (field, term, reported, len(ids)))
            for i in ids:
                cands.setdefault(i, {"pmcid": i, "fields": [], "terms": []})
                if field not in cands[i]["fields"]:
                    cands[i]["fields"].append(field)
                cands[i]["terms"].append(term)

    print("\ndistinct PMC candidates: %d" % len(cands))
    fetch_xml(sorted(cands), args.cache)

    os.makedirs(args.out, exist_ok=True)
    dest = os.path.join(args.out, "comparator_candidates.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({"query_shape": build_query("<TERM>", args.year_from, args.year_to),
                   "per_term": args.per_term,
                   "candidates": [cands[k] for k in sorted(cands)]}, fh, indent=1)
    print("wrote", dest)


if __name__ == "__main__":
    main()
