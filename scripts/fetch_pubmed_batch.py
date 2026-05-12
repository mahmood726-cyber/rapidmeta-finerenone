"""Batch-fetch PubMed abstracts via NCBI eutils efetch.

Reads outputs/extraction_audit/pmids_to_fetch.txt; for each PMID not in
outputs/extraction_audit/pubmed_cache/<pmid>.json, fetch from NCBI efetch
and write a normalized {abstract, journal, doi, title} record.

NCBI rate limit: 3 req/sec without API key, 10/sec with. We use batches
of 50 PMIDs per efetch call (efetch supports comma-separated IDs).

Usage:
  python scripts/fetch_pubmed_batch.py [--start N] [--limit M]
"""
from __future__ import annotations
import sys, os, io, json, time, re
from pathlib import Path
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
PMIDS = HERE / "outputs" / "extraction_audit" / "pmids_to_fetch.txt"
CACHE = HERE / "outputs" / "extraction_audit" / "pubmed_cache"
CACHE.mkdir(parents=True, exist_ok=True)

EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def get_cache_path(pmid: str) -> Path:
    return CACHE / f"{pmid}.json"

def is_cached(pmid: str) -> bool:
    return get_cache_path(pmid).exists()

def parse_xml(xml_bytes: bytes) -> dict[str, dict]:
    """Return {pmid: {abstract, journal, doi, title}}"""
    out = {}
    root = ET.fromstring(xml_bytes)
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//PMID")
        if pmid_el is None: continue
        pmid = pmid_el.text.strip()
        title_el = art.find(".//ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        # Multiple AbstractText nodes (structured abstract)
        abs_pieces = []
        for at in art.findall(".//Abstract/AbstractText"):
            lab = at.get("Label", "")
            txt = "".join(at.itertext()).strip()
            if not txt: continue
            abs_pieces.append(f"{lab}: {txt}" if lab else txt)
        abstract = " ".join(abs_pieces)
        journal_el = art.find(".//Journal/ISOAbbreviation") or art.find(".//Journal/Title")
        journal = (journal_el.text or "").strip() if journal_el is not None else ""
        doi = ""
        for aid in art.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = (aid.text or "").strip()
                break
        out[pmid] = {"abstract": abstract, "journal": journal, "doi": doi, "title": title}
    return out

def fetch_batch(pmids: list[str], retries: int = 3) -> dict[str, dict]:
    if not pmids:
        return {}
    params = {"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"}
    url = EFETCH + "?" + urllib.parse.urlencode(params)
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-finerenone/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                xml_bytes = r.read()
            return parse_xml(xml_bytes)
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    print(f"  ! batch failed after {retries} retries: {last_err}")
    return {}

def main():
    pmids = PMIDS.read_text(encoding="utf-8").strip().split("\n")
    pmids = [p.strip() for p in pmids if p.strip()]
    todo = [p for p in pmids if not is_cached(p)]

    start = 0
    limit = None
    for i, a in enumerate(sys.argv):
        if a == "--start" and i+1 < len(sys.argv):
            start = int(sys.argv[i+1])
        if a == "--limit" and i+1 < len(sys.argv):
            limit = int(sys.argv[i+1])

    if limit is not None:
        todo = todo[start:start+limit]
    elif start:
        todo = todo[start:]

    print(f"Total PMIDs: {len(pmids)}")
    print(f"Already cached: {len(pmids) - sum(1 for p in pmids if not is_cached(p))}")
    print(f"To fetch this run: {len(todo)}")
    print()

    BATCH_SIZE = 50
    SLEEP = 0.4  # 2.5 req/sec
    n_done = 0
    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i+BATCH_SIZE]
        t0 = time.time()
        results = fetch_batch(batch)
        for pmid in batch:
            payload = results.get(pmid, {"abstract": "", "journal": "", "doi": "", "title": ""})
            get_cache_path(pmid).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            n_done += 1
        dt = time.time() - t0
        print(f"  batch {i//BATCH_SIZE + 1}: {len(batch)} PMIDs in {dt:.1f}s  (cum {n_done}/{len(todo)})")
        time.sleep(SLEEP)

    print(f"\nDone. Cached {n_done} PMIDs to {CACHE}")

if __name__ == "__main__":
    main()
