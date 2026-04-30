"""Task D: published-manuscript comparator.

For each of the 22 v0.2 HF P3 trials, find the primary publication via
PubMed search using NCT cross-reference, pull the abstract, and save
side-by-side with the current registered primary outcome for manual
diff against the registry.

Flagship-journal filter (NEJM > Lancet > JAMA > Circulation > JACC > others)
to disambiguate when multiple papers cite the same NCT.
"""
from __future__ import annotations
import json
import sys
import time
import io
import urllib.request
import urllib.parse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
RAW = OUT_DIR / "hf_outcomes_raw.json"
PUB_OUT = OUT_DIR / "hf_publications_22.json"

# NCBI E-utilities (PubMed) -- direct REST since the MCP tool returns
# truncated payloads for >1 article batch.
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

FLAGSHIP_JOURNALS = [
    # ranked by reach for HF-cardiology pivotal-trial reporting
    "N Engl J Med",
    "Lancet",
    "JAMA",
    "Circulation",
    "J Am Coll Cardiol",
    "Eur Heart J",
    "JAMA Cardiol",
    "Nat Med",
]

EXCLUDE = {"NCT03473223", "NCT02809131", "NCT04415658"}  # non-HF


def esearch_pmids(nct: str, max_results: int = 10) -> list[str]:
    """Return PMIDs for the given NCT, sorted by relevance."""
    params = {
        "db": "pubmed",
        "term": f"{nct}[All Fields]",
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
    }
    url = ESEARCH + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    return data.get("esearchresult", {}).get("idlist", [])


def esummary(pmids: list[str]) -> list[dict]:
    """Lightweight metadata for ranking (title + journal)."""
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    url = ESUMMARY + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    out = []
    for pmid in pmids:
        rec = data.get("result", {}).get(pmid, {})
        out.append({
            "pmid": pmid,
            "title": rec.get("title", ""),
            "journal": rec.get("source", ""),
            "pubdate": rec.get("pubdate", ""),
            "authors": [a.get("name") for a in (rec.get("authors") or [])][:2],
            "publication_types": rec.get("pubtype", []),
        })
    return out


def efetch_abstract(pmid: str) -> str:
    """Fetch the abstract text via efetch."""
    params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "abstract",
        "retmode": "text",
    }
    url = EFETCH + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def pick_primary_publication(meta: list[dict]) -> dict | None:
    """Score by flagship-journal rank, exclude reviews/editorials/secondary analyses."""
    if not meta:
        return None
    # Hard exclude clearly non-primary types
    EXCLUDE_TITLE_KW = ["review", "editorial", "comment", "perspective", "commentary",
                        "rationale and design", "study design", "post hoc", "secondary",
                        "subgroup", "rationale", "protocol", "exploratory"]
    candidates = []
    for m in meta:
        title_lower = (m.get("title") or "").lower()
        if any(kw in title_lower for kw in EXCLUDE_TITLE_KW):
            continue
        # Rank by flagship index (lower = better); not in list = 99
        try:
            rank = FLAGSHIP_JOURNALS.index(m.get("journal", ""))
        except ValueError:
            rank = 99
        candidates.append((rank, m))
    if not candidates:
        return meta[0]  # fall back to top relevance
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def main() -> int:
    cur = json.load(open(RAW, "r", encoding="utf-8"))
    primary_pool = [t for t in cur["trials"] if t.get("nct_id") not in EXCLUDE]

    rows = []
    for i, t in enumerate(primary_pool, 1):
        nct = t["nct_id"]
        try:
            pmids = esearch_pmids(nct, max_results=15)
            time.sleep(0.4)
            meta = esummary(pmids)
            time.sleep(0.4)
            primary = pick_primary_publication(meta)
            if primary:
                pmid = primary["pmid"]
                abstract = efetch_abstract(pmid)
                time.sleep(0.4)
            else:
                pmid = None
                abstract = None
            row = {
                "nct_id": nct,
                "acronym": t.get("acronym"),
                "current_registered_primary": [
                    {"measure": p["measure"], "timeFrame": p["timeFrame"]}
                    for p in (t.get("registered_primary") or [])
                ],
                "n_pmids_found": len(pmids),
                "candidate_pmids": pmids,
                "primary_pmid": pmid,
                "primary_journal": primary["journal"] if primary else None,
                "primary_title": primary["title"] if primary else None,
                "primary_pubdate": primary["pubdate"] if primary else None,
                "primary_pubtypes": primary.get("publication_types") if primary else None,
                "primary_abstract": abstract,
            }
            print(f"[{i:2d}/{len(primary_pool)}] {nct} ({t.get('acronym') or '?'}): pmid={pmid} | {primary['journal'] if primary else '?'}", flush=True)
        except Exception as e:
            row = {"nct_id": nct, "error": str(e)}
            print(f"[{i:2d}/{len(primary_pool)}] {nct} FAIL {e}", flush=True)
        rows.append(row)

    json.dump({"extracted_at": "2026-04-30", "n": len(rows), "trials": rows},
              open(PUB_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print()
    print(f"Wrote {PUB_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
